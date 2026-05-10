from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from stock_picker.poc1.budget import RunBudget
from stock_picker.poc1.graph import run_triton_poc
from stock_picker.poc1.models import ManagerOutput


def test_triton_graph_end_to_end_stub_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake")
    fake_out = ManagerOutput(
        recommendation="Hold",
        rationale="test",
        evidence_refs=["stub:scout"],
    )

    class FakeMsg:
        content = json.dumps(fake_out.model_dump())

    class FakeChoice:
        message = FakeMsg()

    class FakeUsage:
        prompt_tokens = 100
        completion_tokens = 50

    class FakeCompletion:
        choices = [FakeChoice()]
        usage = FakeUsage()

    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = FakeCompletion()

    with patch("stock_picker.poc1.llm_manager.OpenAI", return_value=fake_client):
        budget = RunBudget(max_seconds=60.0, max_spend_usd=1.0)
        out = run_triton_poc(user_prompt="Quick read on AAPL", budget=budget)

    assert "manager" in out
    assert out["manager"]["recommendation"] == "Hold"
    fake_client.chat.completions.create.assert_called()
