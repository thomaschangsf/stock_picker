# Architecture

This repo uses an **orchestrator-style** layout so an agent can separate:

- **app/**: presentation layer (CLI/UI)
- **orchestrator/**: workflow state machine / multi-step pipeline
- **tools/**: pure utilities and side-effect boundaries
- **data/**: data loading, schemas, local storage (e.g., DuckDB)

Imports should flow “down” toward simpler layers; avoid circular dependencies.

Run checks with `uv run check code`.

