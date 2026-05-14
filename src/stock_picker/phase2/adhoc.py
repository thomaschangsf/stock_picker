from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from stock_picker.phase1.compose import repo_root
from stock_picker.phase2.scout import (
    MarketDataSummary,
    normalize_symbol,
    redact_url_secrets,
    summarize_parquet,
)


@dataclass(frozen=True)
class AdhocResult:
    symbol: str
    scout_market: dict[str, Any]
    auditor_sec: dict[str, Any]
    analyst: dict[str, Any]
    artifacts: dict[str, Any]
    messages: list[str]
    estimated_cost: dict[str, Any]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "scout_market": self.scout_market,
            "auditor_sec": self.auditor_sec,
            "analyst": self.analyst,
            "artifacts": self.artifacts,
            "messages": self.messages,
            "estimated_cost": self.estimated_cost,
        }


def _http_status_error_debug(e: httpx.HTTPStatusError) -> dict[str, Any]:
    """Subset of request/response for JSON (no secrets in URLs we control)."""
    resp = e.response
    headers = resp.headers
    picked = {
        k: headers.get(k)
        for k in ("server", "content-type", "content-length", "date", "retry-after", "location")
        if headers.get(k)
    }
    body = (resp.text or "")[:1200].replace("\n", "\\n")
    return {
        "request_method": e.request.method,
        "request_url": str(e.request.url),
        "response_status_code": resp.status_code,
        "response_headers": picked,
        "response_body_preview": body,
    }


DEFAULT_SEC_USER_AGENT = "stock-picker/0.1 (https://github.com/thomaschangsf/stock_picker)"


def effective_sec_user_agent() -> str:
    """User-Agent sent to www.sec.gov (env override or built-in default)."""
    raw = os.environ.get("STOCK_PICKER_SEC_USER_AGENT", DEFAULT_SEC_USER_AGENT)
    stripped = raw.strip()
    return stripped if stripped else DEFAULT_SEC_USER_AGENT


def _sec_headers() -> dict[str, str]:
    # SEC fair access: descriptive User-Agent with contact. Do not set Host manually.
    ua = effective_sec_user_agent()
    return {
        "User-Agent": ua,
        "Accept-Encoding": "gzip, deflate",
        "Accept": "application/json, text/xml, application/atom+xml, */*",
    }


def _datasets_dir() -> Path:
    return repo_root() / "datasets"


def _sec_cache_dir() -> Path:
    return _datasets_dir() / "sec"


def _load_or_fetch_company_tickers(*, client: httpx.Client) -> tuple[Path, dict[str, Any], bool]:
    """
    Returns: (path, parsed_json, did_write)
    """
    cache_dir = _sec_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "company_tickers.json"

    did_write = False
    if cache_path.is_file():
        data = json.loads(cache_path.read_text())
        return cache_path, data, did_write

    url = "https://www.sec.gov/files/company_tickers.json"
    r = client.get(url, headers=_sec_headers(), timeout=30.0)
    r.raise_for_status()
    cache_path.write_text(r.text)
    did_write = True
    return cache_path, r.json(), did_write


def _symbol_to_cik(symbol: str, company_tickers: dict[str, Any]) -> str | None:
    # company_tickers.json is keyed by integer-ish strings like:
    # {"0": {"cik_str": ..., "ticker": ...}}
    sym = normalize_symbol(symbol)
    for _, rec in company_tickers.items():
        if isinstance(rec, dict) and rec.get("ticker", "").upper() == sym:
            cik = rec.get("cik_str")
            if cik is None:
                return None
            return str(cik).zfill(10)
    return None


def _fetch_sec_atom(*, client: httpx.Client, cik10: str, count: int = 10) -> tuple[str, str]:
    params = {
        "action": "getcompany",
        "CIK": cik10,
        "owner": "exclude",
        "count": str(count),
        "output": "atom",
    }
    url = "https://www.sec.gov/cgi-bin/browse-edgar?" + urlencode(params)
    r = client.get(url, headers=_sec_headers(), timeout=30.0)
    r.raise_for_status()
    return url, r.text


def _save_text(path: Path, text: str) -> bool:
    if path.is_file():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return True


def run_phase2_adhoc(symbol: str) -> AdhocResult:
    """
    Consolidated Phase 2 ad-hoc fetch.

    Three sets of data:
    - scout_market: Parquet at ``datasets/market_data/{SYMBOL}.parquet`` (required for this
      command; use ``phase2 import-csv`` to create it)
    - auditor_sec: SEC company ticker mapping + recent filings Atom feed (saved to datasets/sec/)
    - analyst: SEC-baseline narrative (no LLM) + optional Finnhub (1 call) if FINNHUB_API_KEY is set
    """
    sym = normalize_symbol(symbol)
    started = time.monotonic()

    messages: list[str] = []
    artifacts: dict[str, Any] = {
        "market_data_parquet": str(
            repo_root() / "datasets" / "market_data" / f"{sym}.parquet"
        )
    }
    http_calls = {"sec": 0, "finnhub": 0}

    # 1) Scout market data (on-disk Parquet only — no live vendor fetch in host adhoc)
    try:
        md: MarketDataSummary = summarize_parquet(sym)
        scout_market = md.to_json_dict()
        messages.extend(md.messages)
    except FileNotFoundError:
        p = repo_root() / "datasets" / "market_data" / f"{sym}.parquet"
        sample_csv = "datasets/samples/aapl_ohlcv_sample.csv"
        hint_cmd = f"uv run stock-picker phase2 import-csv {sym} --csv {sample_csv}"
        scout_market = {
            "symbol": sym,
            "error": "missing_market_data",
            "detail": f"No Parquet at {p}.",
            "hint": hint_cmd,
            "hint_note": (
                "The path after --csv must be a real CSV file on disk (absolute or relative to "
                "where you run the command). The repo includes a tiny demo at datasets/samples/ "
                "for smoke tests; for production use your own OHLCV export. See docs/env.md."
            ),
            "artifacts": {"market_data_parquet": str(p)},
            "messages": [
                f"No Parquet at {p}. Example: {hint_cmd}",
                "See docs/env.md (Market CSV) for where to get real data and how to pick the path.",
            ],
        }
        messages.extend(scout_market["messages"])

    # 2) Auditor SEC data (mapping + Atom feed)
    auditor_sec: dict[str, Any]
    try:
        with httpx.Client() as client:
            tickers_path, tickers_json, wrote_tickers = _load_or_fetch_company_tickers(
                client=client
            )
            http_calls["sec"] += 0 if not wrote_tickers else 1
            artifacts["sec_company_tickers_json"] = str(tickers_path)
            if wrote_tickers:
                messages.append(f"saved SEC company tickers map to {tickers_path}")
            else:
                messages.append(f"loaded cached SEC company tickers map from {tickers_path}")

            cik10 = _symbol_to_cik(sym, tickers_json)
            if cik10 is None:
                auditor_sec = {
                    "symbol": sym,
                    "error": "cik_not_found",
                }
                messages.append(f"SEC CIK not found for symbol {sym}")
            else:
                atom_target_url = "https://www.sec.gov/cgi-bin/browse-edgar?" + urlencode(
                    {
                        "action": "getcompany",
                        "CIK": cik10,
                        "owner": "exclude",
                        "count": str(10),
                        "output": "atom",
                    }
                )
                try:
                    sec_url, atom_xml = _fetch_sec_atom(client=client, cik10=cik10, count=10)
                    http_calls["sec"] += 1
                    atom_path = _sec_cache_dir() / "atom" / sym / f"{cik10}.atom.xml"
                    wrote_atom = _save_text(atom_path, atom_xml)
                    artifacts["sec_atom_xml"] = str(atom_path)
                    if wrote_atom:
                        messages.append(f"saved SEC Atom feed to {atom_path}")
                    else:
                        messages.append(f"SEC Atom feed already present at {atom_path}")

                    auditor_sec = {
                        "symbol": sym,
                        "cik10": cik10,
                        "sec_atom_url": sec_url,
                        "artifacts": {"sec_atom_xml": str(atom_path)},
                    }
                except httpx.HTTPStatusError as e:
                    code = e.response.status_code
                    auditor_sec = {
                        "symbol": sym,
                        "cik10": cik10,
                        "error": "sec_atom_http_error",
                        "status_code": code,
                        "url": str(e.request.url),
                        "request_user_agent": _sec_headers().get("User-Agent"),
                        "http_debug": _http_status_error_debug(e),
                        "hint": (
                            "SEC often returns 403 without a proper User-Agent. Set "
                            "STOCK_PICKER_SEC_USER_AGENT to a string that identifies you "
                            "(include contact)."
                        ),
                    }
                    messages.append(
                        f"SEC Atom request failed with HTTP {code} for {e.request.url}"
                    )
                except httpx.RequestError as e:
                    auditor_sec = {
                        "symbol": sym,
                        "cik10": cik10,
                        "error": "sec_atom_network_error",
                        "detail": str(e),
                        "request_url": atom_target_url,
                    }
                    messages.append(f"SEC Atom request failed (network): {e}")
                except OSError as e:
                    auditor_sec = {
                        "symbol": sym,
                        "cik10": cik10,
                        "error": "sec_atom_io_error",
                        "detail": str(e),
                    }
                    messages.append(f"SEC Atom save failed: {e}")
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        auditor_sec = {
            "symbol": sym,
            "error": "sec_http_error",
            "status_code": code,
            "url": str(e.request.url),
            "request_user_agent": _sec_headers().get("User-Agent"),
            "http_debug": _http_status_error_debug(e),
            "hint": (
                "SEC often returns 403 without a proper User-Agent. Set "
                "STOCK_PICKER_SEC_USER_AGENT to a string that identifies you (include contact)."
            ),
        }
        messages.append(f"SEC request failed with HTTP {code} for {e.request.url}")
    except httpx.RequestError as e:
        auditor_sec = {
            "symbol": sym,
            "error": "sec_network_error",
            "detail": str(e),
        }
        messages.append(f"SEC request failed (network): {e}")
    except (OSError, json.JSONDecodeError, ValueError) as e:
        auditor_sec = {
            "symbol": sym,
            "error": "sec_parse_or_io_error",
            "detail": str(e),
        }
        messages.append(f"SEC data handling failed: {e}")

    # 3) Analyst (SEC baseline + optional Finnhub, no LLM in this command)
    analyst: dict[str, Any] = {
        "baseline": "SEC-only (no paid news API; no LLM in adhoc)",
        "notes": [
            "This command does not run the LangGraph Phase 2 pipeline yet.",
            (
                "It produces a deterministic bundle: local market parquet + SEC filings "
                "feed (+ optional Finnhub)."
            ),
        ],
        "finnhub": {"enabled": False},
    }

    finnhub_key = os.environ.get("FINNHUB_API_KEY")
    if finnhub_key:
        # Keep this deliberately to a single call.
        fh_url = f"https://finnhub.io/api/v1/quote?symbol={sym}&token={finnhub_key}"
        try:
            r = httpx.get(
                fh_url,
                timeout=20.0,
                headers={
                    "User-Agent": "stock-picker/0.1 (https://github.com/thomaschangsf/stock_picker)"
                },
            )
            r.raise_for_status()
            http_calls["finnhub"] += 1
            analyst["finnhub"] = {
                "enabled": True,
                "request_url": redact_url_secrets(str(r.request.url)),
                "quote": r.json(),
            }
        except httpx.HTTPStatusError as e:
            analyst["finnhub"] = {
                "enabled": True,
                "request_url": redact_url_secrets(str(e.request.url)),
                "error": str(e),
                "http_debug": _http_status_error_debug(e),
            }
        except httpx.RequestError as e:
            analyst["finnhub"] = {
                "enabled": True,
                "request_url": redact_url_secrets(fh_url),
                "error": str(e),
                "error_type": type(e).__name__,
            }
        except Exception as e:
            analyst["finnhub"] = {
                "enabled": True,
                "request_url": redact_url_secrets(fh_url),
                "error": str(e),
                "error_type": type(e).__name__,
            }

    elapsed_s = time.monotonic() - started
    estimated_cost = {
        "estimated_llm_usd": 0.0,
        "http_calls": http_calls,
        "elapsed_seconds": round(elapsed_s, 3),
        "note": "Adhoc Phase 2 fetch does not call an LLM; estimated_llm_usd is always 0.0.",
    }

    return AdhocResult(
        symbol=sym,
        scout_market=scout_market,
        auditor_sec=auditor_sec,
        analyst=analyst,
        artifacts=artifacts,
        messages=messages,
        estimated_cost=estimated_cost,
    )

