from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from stock_picker.phase1.compose import repo_root


def test_phase2_import_csv_writes_parquet_and_reports_path(tmp_path: Path) -> None:
    root = repo_root()
    csv_path = tmp_path / "aapl.csv"
    csv_path.write_text("date,close\n2026-01-01,100.0\n2026-01-02,101.5\n")

    out_parquet = root / "datasets" / "market_data" / "AAPL.parquet"
    if out_parquet.exists():
        out_parquet.unlink()

    try:
        cmd = [
            sys.executable,
            "-m",
            "stock_picker.cli",
            "phase2",
            "import-csv",
            "AAPL",
            "--csv",
            str(csv_path),
        ]
        out = subprocess.check_output(cmd, text=True)
        payload = json.loads(out)
        assert payload["symbol"] == "AAPL"
        assert payload["artifacts"]["market_data_parquet"].endswith("/datasets/market_data/AAPL.parquet")
        assert out_parquet.is_file()
        assert any("imported CSV" in m for m in payload["messages"])
        assert payload["rows"] == 2
    finally:
        if out_parquet.exists():
            out_parquet.unlink()


def test_phase2_import_csv_bundled_sample_smoke() -> None:
    """Repo ships datasets/samples/aapl_ohlcv_sample.csv for a copy-pasteable path."""
    root = repo_root()
    sample = root / "datasets" / "samples" / "aapl_ohlcv_sample.csv"
    assert sample.is_file(), f"missing bundled sample: {sample}"

    out_parquet = root / "datasets" / "market_data" / "AAPL.parquet"
    if out_parquet.exists():
        out_parquet.unlink()

    try:
        cmd = [
            sys.executable,
            "-m",
            "stock_picker.cli",
            "phase2",
            "import-csv",
            "AAPL",
            "--csv",
            str(sample),
        ]
        out = subprocess.check_output(cmd, text=True, cwd=str(root))
        payload = json.loads(out)
        assert payload["symbol"] == "AAPL"
        assert payload["rows"] == 3
        assert out_parquet.is_file()
    finally:
        if out_parquet.exists():
            out_parquet.unlink()


def test_phase2_import_csv_rejects_parquet_as_input(tmp_path: Path) -> None:
    from stock_picker.phase2.scout import import_csv_to_parquet

    pq = tmp_path / "fake.parquet"
    pq.write_bytes(b"PAR1")
    with pytest.raises(ValueError, match="CSV"):
        import_csv_to_parquet("AAPL", csv_path=pq, root=tmp_path)

