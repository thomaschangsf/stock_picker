from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from stock_picker.phase1.compose import repo_root

_SYMBOL_RE = re.compile(r"^[A-Z0-9.\-]{1,15}$")


def redact_url_secrets(url: str) -> str:
    out = re.sub(r"([?&]apikey=)[^&]+", r"\1REDACTED", url, flags=re.IGNORECASE)
    out = re.sub(r"([?&]token=)[^&]+", r"\1REDACTED", out, flags=re.IGNORECASE)
    return out


def _quote_ident(ident: str) -> str:
    return '"' + ident.replace('"', '""') + '"'


@dataclass(frozen=True)
class MarketDataSummary:
    symbol: str
    path: str
    rows: int
    columns: list[str]
    date_min: str | None
    date_max: str | None
    messages: list[str]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "artifacts": {"market_data_parquet": self.path},
            "rows": self.rows,
            "columns": self.columns,
            "date_min": self.date_min,
            "date_max": self.date_max,
            "messages": self.messages,
        }


def market_data_path(symbol: str, *, root: Path | None = None) -> Path:
    sym = normalize_symbol(symbol)
    base = root if root is not None else repo_root()
    return base / "datasets" / "market_data" / f"{sym}.parquet"


def normalize_symbol(symbol: str) -> str:
    sym = symbol.strip().upper()
    if not _SYMBOL_RE.match(sym):
        raise ValueError(f"invalid symbol {symbol!r} (expected e.g. AAPL, BRK-B, BF.B)")
    return sym


def summarize_parquet(symbol: str, *, path: Path | None = None) -> MarketDataSummary:
    p = path if path is not None else market_data_path(symbol)
    if not p.is_file():
        raise FileNotFoundError(str(p))

    # Use DuckDB so we don't require pyarrow just for ad-hoc reads.
    rel = duckdb.sql("select * from read_parquet(?)", params=[str(p)])
    cols = [c[0] for c in rel.description]
    rows = int(
        duckdb.sql("select count(*) as n from read_parquet(?)", params=[str(p)])
        .fetchone()[0]
    )

    # Try to infer a date-ish column for min/max reporting.
    date_col = None
    for candidate in ("date", "Date", "datetime", "timestamp", "time"):
        if candidate in cols:
            date_col = candidate
            break

    date_min = date_max = None
    if date_col is not None:
        quoted = _quote_ident(date_col)
        q = f"select min({quoted}) as mn, max({quoted}) as mx from read_parquet(?)"
        mn, mx = duckdb.sql(q, params=[str(p)]).fetchone()
        date_min = None if mn is None else str(mn)
        date_max = None if mx is None else str(mx)

    return MarketDataSummary(
        symbol=normalize_symbol(symbol),
        path=str(p),
        rows=rows,
        columns=cols,
        date_min=date_min,
        date_max=date_max,
        messages=[f"loaded existing market data from {p}"],
    )


def import_csv_to_parquet(
    symbol: str,
    *,
    csv_path: Path,
    root: Path | None = None,
) -> MarketDataSummary:
    sym = normalize_symbol(symbol)
    out_path = market_data_path(sym, root=root)
    if not csv_path.is_file():
        raise FileNotFoundError(str(csv_path))

    suf = csv_path.suffix.lower()
    if suf in (".parquet", ".pq"):
        raise ValueError(
            f"--csv must point to a CSV file, not {csv_path.suffix!r}. "
            "This command reads CSV and writes Parquet under datasets/market_data/. "
            f"If you already have Parquet, place it at datasets/market_data/{sym}.parquet "
            "(no import). Ticker spelling: Apple is AAPL, not APPL."
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # DuckDB can infer types and write Parquet without bringing in pyarrow/pandas.
    # DuckDB doesn't reliably support parameterized file paths for COPY targets,
    # so we quote/escape the paths and embed them.
    csv_sql = str(csv_path).replace("'", "''")
    out_sql = str(out_path).replace("'", "''")
    duckdb.sql(
        f"copy (select * from read_csv_auto('{csv_sql}', header=true)) "
        f"to '{out_sql}' (format parquet)"
    )
    summary = summarize_parquet(sym, path=out_path)
    return MarketDataSummary(
        symbol=summary.symbol,
        path=summary.path,
        rows=summary.rows,
        columns=summary.columns,
        date_min=summary.date_min,
        date_max=summary.date_max,
        messages=[
            f"imported CSV {csv_path} to {out_path}",
            *summary.messages,
        ],
    )
