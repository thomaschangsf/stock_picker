"""Human-readable environment check after dotenv load."""

from __future__ import annotations

import os
import sys
from typing import TextIO

# Doctor UI label for `phase2 adhoc` (CLI name unchanged).
_PH2_HEADING = "Fetch Market, SEC, and Analysis Data"


def _mask_secret(raw: str, *, keep_start: int = 4, keep_end: int = 4) -> str:
    s = raw.strip()
    if len(s) <= keep_start + keep_end + 3:
        return "(set, hidden)"
    return f"{s[:keep_start]}…{s[-keep_end:]}"


def run_doctor(
    *,
    for_profile: str | None,
    symbol: str | None,
    stream: TextIO | None = None,
    strict: bool = False,
) -> int:
    """
    Print short step checklists for ``poc1 run`` (Verify LangGraph) and
    ``phase2 adhoc`` (Fetch Market, SEC, and Analysis Data).

    ``for_profile``: ``None`` (both), ``"poc1"``, or ``"phase2-adhoc"``.
    ``symbol``: ticker for Parquet check (``phase2-adhoc`` only).

    Returns ``1`` if ``strict`` and any shown profile has FAIL; else ``0``.
    """
    out = stream or sys.stdout
    from stock_picker.phase2.adhoc import DEFAULT_SEC_USER_AGENT
    from stock_picker.phase2.scout import market_data_path, normalize_symbol

    out.write("doctor (dotenv already loaded)\n\n")

    show_poc1 = for_profile in (None, "poc1")
    show_ph2 = for_profile in (None, "phase2-adhoc")

    poc1_ok = True
    ph2_status = "OK"
    ph2_detail = ""
    any_fail = False

    if show_poc1:
        out.write("Verify LangGraph — do this:\n")
        out.write(
            "  why: LangGraph once on your prompt; Scout/Auditor/Analyst are stubs; "
            "Manager is the only node that calls OpenAI.\n"
        )
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if key:
            out.write(f"  1. OPENAI_API_KEY → OK ({_mask_secret(key)})\n")
        else:
            out.write("  1. OPENAI_API_KEY → FAIL (unset; required)\n")
            poc1_ok = False
        out.write("  2. Run: uv run stock-picker poc1 run --prompt \"…\"\n")
        out.write(f"  → Verify LangGraph: {'OK' if poc1_ok else 'FAIL'}\n\n")
        if not poc1_ok:
            any_fail = True

    if show_ph2:
        sym_label = "SYMBOL"
        if symbol:
            try:
                sym_label = normalize_symbol(symbol)
            except ValueError:
                sym_label = "SYMBOL"

        out.write(f"{_PH2_HEADING} — do this:\n")
        out.write(
            "  why: One JSON from `phase2 adhoc SYMBOL` — three slices: market, SEC, analyst.\n"
        )
        out.write("\n")
        out.write("  what:\n")
        out.write(
            "      • Market (Scout) = OHLCV (O,H,L,C,V): CSV → import-csv → Parquet.\n"
        )
        out.write(
            "      • SEC (Auditor) = filings Atom from SEC (Atom XML; RSS-like), "
            f"cached for {sym_label}.\n"
        )
        out.write(
            "      • Analyst = SEC-only stub lines in JSON + optional Finnhub if key set.\n"
        )
        out.write("\n")
        ua_custom = bool(os.environ.get("STOCK_PICKER_SEC_USER_AGENT", "").strip())
        if ua_custom:
            ua = os.environ.get("STOCK_PICKER_SEC_USER_AGENT", "").strip()
            preview = ua[:40] + ("…" if len(ua) > 40 else "")
            out.write(f"  1. STOCK_PICKER_SEC_USER_AGENT → OK ({preview})\n")
        else:
            out.write("  1. STOCK_PICKER_SEC_USER_AGENT → WARN (unset; SEC may 403)\n")
            out.write(f"      default is: {DEFAULT_SEC_USER_AGENT}\n")

        sym: str | None = None
        parquet_ok = False
        if symbol:
            try:
                sym = normalize_symbol(symbol)
            except ValueError as e:
                out.write(f"  2. --symbol {symbol!r} → FAIL ({e})\n")
                ph2_status = "FAIL"
                ph2_detail = str(e)
            else:
                p = market_data_path(sym)
                if p.is_file():
                    out.write(f"  2. market Parquet → OK ({p.name})\n")
                    parquet_ok = True
                else:
                    out.write("  2. market Parquet → WARN (file missing)\n")
                    cmd = (
                        f"uv run stock-picker phase2 import-csv {sym} "
                        f"--csv datasets/samples/aapl_ohlcv_sample.csv"
                    )
                    out.write(f"      try: {cmd}\n")
        else:
            out.write("  2. market Parquet → skip (add --symbol AAPL to check)\n")

        fh = os.environ.get("FINNHUB_API_KEY", "").strip()
        out.write(
            f"  3. FINNHUB_API_KEY → {'on (optional quote)' if fh else 'off (optional)'}\n"
        )

        if ph2_status != "FAIL":
            warns: list[str] = []
            if not symbol:
                warns.append("no --symbol")
            elif sym is not None and not parquet_ok:
                warns.append("missing Parquet")
            if not ua_custom:
                warns.append("default SEC User-Agent")
            if warns:
                ph2_status = "WARN"
                ph2_detail = ", ".join(warns)
            else:
                ph2_status = "OK"
                ph2_detail = "ready" if sym else "add --symbol for Parquet check"

        out.write(f"  → {_PH2_HEADING}: {ph2_status}")
        if ph2_detail and ph2_status != "OK":
            out.write(f" ({ph2_detail})")
        out.write("\n\n")

        if ph2_status == "FAIL":
            any_fail = True

    if show_poc1 and show_ph2:
        out.write(
            "overall: "
            f"{'LangGraph OK' if poc1_ok else 'LangGraph FAIL'}; "
            f"{_PH2_HEADING} {ph2_status}\n\n"
        )

    out.write("more: docs/env.md\n")

    if strict and any_fail:
        return 1
    return 0
