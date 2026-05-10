from __future__ import annotations

import re
from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from stock_picker.poc1.budget import RunBudget
from stock_picker.poc1.llm_manager import synthesize_manager
from stock_picker.poc1.models import AnalystOutput, AuditorOutput, ScoutOutput


class TritonState(TypedDict, total=False):
    user_prompt: str
    scout: dict[str, Any]
    auditor: dict[str, Any]
    analyst: dict[str, Any]
    manager: dict[str, Any]


def _budget_from_config(config: RunnableConfig) -> RunBudget:
    b = config.get("configurable", {}).get("budget")
    if not isinstance(b, RunBudget):
        raise TypeError("config['configurable']['budget'] must be a RunBudget instance")
    return b


def _tickers_from_prompt(text: str) -> list[str]:
    hits = re.findall(r"\b([A-Z]{1,5})\b", text.upper())
    # de-dupe preserving order
    out: list[str] = []
    for h in hits:
        if h not in out:
            out.append(h)
    return out or ["SPY"]


def node_scout(state: TritonState, config: RunnableConfig) -> dict[str, Any]:
    budget = _budget_from_config(config)
    budget.check_time()
    tickers = _tickers_from_prompt(state.get("user_prompt", ""))
    raw = ScoutOutput(
        universe=tickers[:20],
        rationale="Phase 0 stub: universe from uppercase tokens in prompt, else SPY.",
    ).model_dump()
    ScoutOutput.model_validate(raw)
    return {"scout": raw}


def node_auditor(state: TritonState, config: RunnableConfig) -> dict[str, Any]:
    budget = _budget_from_config(config)
    budget.check_time()
    scout = state.get("scout") or {}
    ScoutOutput.model_validate(scout)
    uni = scout["universe"]
    raw = AuditorOutput(
        passed_tickers=uni,
        rejected=[],
    ).model_dump()
    AuditorOutput.model_validate(raw)
    return {"auditor": raw}


def node_analyst(state: TritonState, config: RunnableConfig) -> dict[str, Any]:
    budget = _budget_from_config(config)
    budget.check_time()
    auditor = state.get("auditor") or {}
    AuditorOutput.model_validate(auditor)
    notes = {t: "stub sentiment: neutral" for t in auditor["passed_tickers"]}
    raw = AnalystOutput(
        per_ticker_notes=notes,
        sentiment_summary="Phase 0 stub: neutral across passed names.",
    ).model_dump()
    AnalystOutput.model_validate(raw)
    return {"analyst": raw}


def node_manager(state: TritonState, config: RunnableConfig) -> dict[str, Any]:
    budget = _budget_from_config(config)
    budget.check_time()
    scout = state.get("scout") or {}
    auditor = state.get("auditor") or {}
    analyst = state.get("analyst") or {}
    ScoutOutput.model_validate(scout)
    AuditorOutput.model_validate(auditor)
    AnalystOutput.model_validate(analyst)
    out = synthesize_manager(
        user_prompt=state.get("user_prompt", ""),
        scout=scout,
        auditor=auditor,
        analyst=analyst,
        budget=budget,
    )
    return {"manager": out.model_dump()}


def build_triton_graph() -> StateGraph:
    g: StateGraph = StateGraph(TritonState)
    g.add_node("scout", node_scout)
    g.add_node("auditor", node_auditor)
    g.add_node("analyst", node_analyst)
    g.add_node("manager", node_manager)
    g.add_edge(START, "scout")
    g.add_edge("scout", "auditor")
    g.add_edge("auditor", "analyst")
    g.add_edge("analyst", "manager")
    g.add_edge("manager", END)
    return g


def run_triton_poc(*, user_prompt: str, budget: RunBudget) -> TritonState:
    """Compile and invoke the Phase 0 graph once."""
    budget.reset_clock()
    app = build_triton_graph().compile()
    cfg: RunnableConfig = {"configurable": {"budget": budget}}
    result = app.invoke({"user_prompt": user_prompt}, config=cfg)
    if not isinstance(result, dict):
        raise TypeError("unexpected graph result type")
    return result  # type: ignore[return-value]


__all__ = ["TritonState", "build_triton_graph", "run_triton_poc"]
