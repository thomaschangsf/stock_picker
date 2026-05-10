# stock_picker

Agent-oriented Python repo structure (modeled after `modelAgent`) so artifacts and code are easy to review:

- `AGENTS.md`: agent operating rules
- `ARCHITECTURE.md`: layering + dependency intent
- `docs/`: decisions, generated docs, doc index
- `specs/`: build plans/specs for planned work
- `src/stock_picker/`: Python source
- `tests/`: tests

## Quickstart

```bash
# Install (dev tools included)
uv sync --all-extras

# Run checks
uv run check code
```

## Commands

```bash
uv run stock-picker --help
```

