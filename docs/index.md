# Documentation Index

Folder conventions:

- **specs/** -- Build plans for planned work. Consumed during implementation, then archived.
- **decisions/** -- Architecture decision records. Append-only, numbered chronologically.
- **generated/** -- Auto-generated from code. Do not edit directly.

## Generated

`docs/generated/` is intentionally checked in only with placeholders (e.g. `.gitkeep`) until generators exist.

Planned backtest run reports (v1): `docs/generated/backtests/` — see [specs/backtesting-v1.md](../specs/backtesting-v1.md).

## Decisions

- [decisions/001-backtesting-v1-scope.md](decisions/001-backtesting-v1-scope.md)

## Environment

- [env.md](env.md) — dotenv load order, variable table, SEC User-Agent setup, `stock-picker doctor`.

## Phase 2 — Analyst coverage

- [analyst-coverage.md](analyst-coverage.md) — SEC baseline vs optional Finnhub; what is covered; future TODOs.

