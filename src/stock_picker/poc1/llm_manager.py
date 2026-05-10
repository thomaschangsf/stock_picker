from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from stock_picker.poc1.budget import RunBudget
from stock_picker.poc1.exceptions import HandoffValidationError
from stock_picker.poc1.models import AnalystOutput, AuditorOutput, ManagerOutput, ScoutOutput


def _model() -> str:
    return os.environ.get("STOCK_PICKER_OPENAI_MODEL", "gpt-4o-mini")


def synthesize_manager(
    *,
    user_prompt: str,
    scout: dict[str, Any],
    auditor: dict[str, Any],
    analyst: dict[str, Any],
    budget: RunBudget,
) -> ManagerOutput:
    """
    Single real LLM call (Phase 0). Expects OPENAI_API_KEY in the environment.
    One bounded JSON repair retry if Pydantic validation fails.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set; required for Phase 0 Manager (real LLM integration)."
        )

    client = OpenAI(api_key=api_key)
    schema = ManagerOutput.model_json_schema()
    prior = {
        "user_prompt": user_prompt,
        "scout": scout,
        "auditor": auditor,
        "analyst": analyst,
    }
    system = (
        "You are the Manager (Aggregator) for a multi-agent equity research pipeline. "
        "Return a single JSON object that conforms to this JSON Schema (no markdown fences):\n"
        f"{json.dumps(schema, indent=2)}\n"
        "Use evidence_refs for short strings (e.g. 'stub:scout', 'stub:auditor'). "
        "Recommendation must be one of: Buy, Hold, Avoid."
    )
    user = json.dumps(prior, indent=2)

    def _call(extra: str | None = None) -> ManagerOutput:
        messages = [
            {"role": "system", "content": system + (f"\n\n{extra}" if extra else "")},
            {"role": "user", "content": user},
        ]
        completion = client.chat.completions.create(
            model=_model(),
            response_format={"type": "json_object"},
            messages=messages,
        )
        usage = completion.usage
        if usage is not None:
            budget.add_llm_usage(
                prompt_tokens=usage.prompt_tokens or 0,
                completion_tokens=usage.completion_tokens or 0,
            )
        raw = completion.choices[0].message.content or "{}"
        data = json.loads(raw)
        # Cross-check upstream payloads still validate (fail-fast on corrupted state).
        ScoutOutput.model_validate(scout)
        AuditorOutput.model_validate(auditor)
        AnalystOutput.model_validate(analyst)
        return ManagerOutput.model_validate(data)

    try:
        return _call()
    except (json.JSONDecodeError, ValueError) as first:
        try:
            return _call(
                extra=(
                    "Your previous reply was invalid JSON or did not match the schema. "
                    f"Error: {first!r}. Reply with JSON only."
                )
            )
        except (json.JSONDecodeError, ValueError) as second:
            raise HandoffValidationError(str(second)) from second
