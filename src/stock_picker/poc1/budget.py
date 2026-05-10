from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

from stock_picker.poc1.exceptions import RunBudgetExceeded


def _env_float(name: str, default: str) -> float:
    return float(os.environ.get(name, default))


@dataclass
class RunBudget:
    """
    Single run budget: abort when max_seconds OR max_estimated_spend_usd is exceeded.

    LLM cost is best-effort: input and completion tokens priced per 1M using env defaults.
    """

    max_seconds: float
    max_spend_usd: float
    input_usd_per_1m_tokens: float = field(
        default_factory=lambda: _env_float("STOCK_PICKER_PRICE_INPUT_PER_1M", "0.15")
    )
    output_usd_per_1m_tokens: float = field(
        default_factory=lambda: _env_float("STOCK_PICKER_PRICE_OUTPUT_PER_1M", "0.60")
    )
    _t0: float = field(default_factory=time.monotonic)
    _estimated_spend_usd: float = 0.0

    def reset_clock(self) -> None:
        self._t0 = time.monotonic()

    def elapsed_seconds(self) -> float:
        return time.monotonic() - self._t0

    def check_time(self) -> None:
        if self.elapsed_seconds() > self.max_seconds:
            msg = (
                f"run_budget: exceeded max_seconds={self.max_seconds!r} "
                f"(elapsed={self.elapsed_seconds():.3f}s)"
            )
            raise RunBudgetExceeded(msg)

    def add_llm_usage(self, *, prompt_tokens: int, completion_tokens: int) -> None:
        spend = (prompt_tokens / 1_000_000.0) * self.input_usd_per_1m_tokens
        spend += (completion_tokens / 1_000_000.0) * self.output_usd_per_1m_tokens
        self._estimated_spend_usd += spend
        if self._estimated_spend_usd > self.max_spend_usd:
            msg = (
                f"run_budget: exceeded max_spend_usd={self.max_spend_usd!r} "
                f"(estimated={self._estimated_spend_usd:.6f} USD)"
            )
            raise RunBudgetExceeded(msg)

    @property
    def estimated_spend_usd(self) -> float:
        return self._estimated_spend_usd
