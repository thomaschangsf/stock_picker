from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ScoutOutput(BaseModel):
    """Technical scout: candidate universe (stub data in Phase 0)."""

    universe: list[str] = Field(min_length=1, description="Ticker symbols to pass downstream")
    rationale: str = ""


class AuditorOutput(BaseModel):
    """Fundamental screen (stub pass-through in Phase 0)."""

    passed_tickers: list[str] = Field(min_length=1)
    rejected: list[tuple[str, str]] = Field(default_factory=list)


class AnalystOutput(BaseModel):
    """Sentiment / qualitative notes (stub in Phase 0)."""

    per_ticker_notes: dict[str, str] = Field(default_factory=dict)
    sentiment_summary: str = ""


class ManagerOutput(BaseModel):
    """Final synthesis; evidence_refs satisfy Phase 0 'slots' as plain strings."""

    recommendation: Literal["Buy", "Hold", "Avoid"]
    rationale: str
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="Opaque evidence handles (URLs, tool run ids, etc.)",
    )
