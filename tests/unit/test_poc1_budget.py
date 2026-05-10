import pytest

from stock_picker.poc1.budget import RunBudget
from stock_picker.poc1.exceptions import RunBudgetExceeded


def test_run_budget_exceeds_spend() -> None:
    b = RunBudget(max_seconds=3600.0, max_spend_usd=1e-9)
    b.reset_clock()
    with pytest.raises(RunBudgetExceeded):
        b.add_llm_usage(prompt_tokens=1_000_000, completion_tokens=0)


def test_run_budget_exceeds_time(monkeypatch: pytest.MonkeyPatch) -> None:
    b = RunBudget(max_seconds=0.05, max_spend_usd=1e6)
    t = {"v": 0.0}

    def fake_monotonic() -> float:
        t["v"] += 0.1
        return t["v"]

    monkeypatch.setattr("stock_picker.poc1.budget.time.monotonic", fake_monotonic)
    b.reset_clock()
    with pytest.raises(RunBudgetExceeded):
        b.check_time()
