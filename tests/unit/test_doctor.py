from __future__ import annotations

import os
from io import StringIO

import pytest

from stock_picker.doctor import run_doctor


def test_doctor_poc1_reports_missing_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    buf = StringIO()
    assert run_doctor(for_profile="poc1", symbol=None, stream=buf, strict=False) == 0
    out = buf.getvalue()
    assert "Verify LangGraph — do this:" in out
    assert "why: LangGraph" in out
    assert "1. OPENAI_API_KEY → FAIL" in out
    assert "→ Verify LangGraph: FAIL" in out
    assert "Fetch Market, SEC, and Analysis Data" not in out


def test_doctor_poc1_strict_exits_when_openai_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    buf = StringIO()
    assert run_doctor(for_profile="poc1", symbol=None, stream=buf, strict=True) == 1
    assert "FAIL" in buf.getvalue()


def test_doctor_phase2_reports_builtin_sec_ua_when_unset(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("stock_picker.phase2.scout.repo_root", lambda: tmp_path)
    (tmp_path / "datasets" / "market_data").mkdir(parents=True)
    monkeypatch.delenv("STOCK_PICKER_SEC_USER_AGENT", raising=False)
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)
    buf = StringIO()
    assert run_doctor(for_profile="phase2-adhoc", symbol="AAPL", stream=buf) == 0
    out = buf.getvalue()
    assert "Fetch Market, SEC, and Analysis Data — do this:" in out
    assert "what:" in out
    assert "• Market (Scout)" in out
    assert "• SEC (Auditor)" in out
    assert "• Analyst" in out
    assert "why: One JSON" in out and "three slices" in out
    assert "1. STOCK_PICKER_SEC_USER_AGENT → WARN" in out
    assert "2. market Parquet → WARN" in out
    assert "3. FINNHUB_API_KEY → off" in out
    assert "→ Fetch Market, SEC, and Analysis Data: WARN" in out


def test_doctor_masks_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-abcdefghijklmnop")
    buf = StringIO()
    assert run_doctor(for_profile="poc1", symbol=None, stream=buf) == 0
    out = buf.getvalue()
    assert "sk-te…mnop" in out or "OK" in out
    assert "abcdefghijklmnop" not in out
    assert "→ Verify LangGraph: OK" in out


def test_doctor_parquet_present(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from stock_picker.phase2.scout import market_data_path, normalize_symbol

    sym = normalize_symbol("ZZDOC")
    p = market_data_path(sym, root=tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"not-real-parquet-but-file")

    monkeypatch.setattr("stock_picker.phase2.scout.repo_root", lambda: tmp_path)
    monkeypatch.setenv("STOCK_PICKER_SEC_USER_AGENT", "Doctor Test doctor-test@example.com")
    monkeypatch.delenv("FINNHUB_API_KEY", raising=False)

    buf = StringIO()
    assert run_doctor(for_profile="phase2-adhoc", symbol="ZZDOC", stream=buf) == 0
    out = buf.getvalue()
    assert "• Market (Scout)" in out
    assert "cached for ZZDOC" in out
    assert "2. market Parquet → OK" in out
    assert "→ Fetch Market, SEC, and Analysis Data: OK" in out


def test_doctor_both_shows_overall_summary(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("stock_picker.phase2.scout.repo_root", lambda: tmp_path)
    (tmp_path / "datasets" / "market_data").mkdir(parents=True)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-abcdefghijklmnop")
    monkeypatch.delenv("STOCK_PICKER_SEC_USER_AGENT", raising=False)
    buf = StringIO()
    assert run_doctor(for_profile=None, symbol="AAPL", stream=buf) == 0
    out = buf.getvalue()
    assert "overall:" in out
    assert "LangGraph OK" in out
    assert "Fetch Market, SEC, and Analysis Data WARN" in out


def test_doctor_phase2_fail_invalid_symbol() -> None:
    buf = StringIO()
    assert run_doctor(for_profile="phase2-adhoc", symbol="A*B", stream=buf) == 0
    out = buf.getvalue()
    assert "2. --symbol" in out and "FAIL" in out
    assert "→ Fetch Market, SEC, and Analysis Data: FAIL" in out


def test_doctor_phase2_strict_fail_invalid_symbol() -> None:
    buf = StringIO()
    assert run_doctor(for_profile="phase2-adhoc", symbol="A*B", stream=buf, strict=True) == 1
