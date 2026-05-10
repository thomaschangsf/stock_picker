# stock_picker

Your job in this repo is to produce **reviewable artifacts** that support correct agent-driven coding:

- specs and decisions in `docs/` and `specs/`
- deterministic checks via `uv run check ...`
- small, auditable patches

## Mandatory workflow

1. Start from the user request and relevant docs (`README.md`, `ARCHITECTURE.md`, `docs/index.md`).
2. Write/update a spec in `specs/` if scope is non-trivial.
3. Implement in small steps with runnable entrypoints.
4. Prefer deterministic validation (ruff/pytest) over narrative assurance.

## Output contract

- If implementing: summarize changes + how to run + validation results.
- If blocked: ask only the minimum blocking questions.

