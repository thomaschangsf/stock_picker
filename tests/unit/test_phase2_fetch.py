from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import duckdb

from stock_picker.phase1.compose import repo_root


def _write_parquet(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(
        """
        create table t as
        select * from (values
          ('2026-01-01'::date, 100.0),
          ('2026-01-02'::date, 101.5)
        ) as v(date, close)
        """
    )
    con.execute("copy t to ? (format parquet)", [str(path)])
    con.close()


def test_phase2_fetch_summarizes_parquet(tmp_path: Path) -> None:
    # Write into the repo's expected datasets/ location so the CLI finds it.
    root = repo_root()
    p = root / "datasets" / "market_data" / "AAPL.parquet"
    _write_parquet(p)

    try:
        cmd = [sys.executable, "-m", "stock_picker.cli", "phase2", "fetch", "AAPL"]
        out = subprocess.check_output(cmd, text=True)
        payload = json.loads(out)
        assert payload["symbol"] == "AAPL"
        assert payload["artifacts"]["market_data_parquet"].endswith("/datasets/market_data/AAPL.parquet")
        assert payload["rows"] == 2
        assert "date" in payload["columns"]
        assert payload["date_min"] == "2026-01-01"
        assert payload["date_max"] == "2026-01-02"
        assert payload["messages"]
    finally:
        # Keep repo clean after test.
        if p.exists():
            p.unlink()

