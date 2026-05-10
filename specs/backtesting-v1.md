# Backtesting v1 — specification

## Purpose

Support **experimenting with trading strategies** against **historical daily market data** for **multi-symbol portfolios**, with **realistic execution**, **long-only** positions, **explicit per-symbol weights**, **optional cash**, **ETF expense ratio drag**, and a **configurable risk-free rate** for cash (default: **Fed series**, with **constant override**).

## Non-goals (v1)

- Short selling, leverage, margin, options
- Intraday bars, limit/stop orders, order book / microstructure
- Per-trade commissions and slippage (treated as **third-order**; deferred)
- Sophisticated **rebalancing / churn thresholds** (deferred; see [Future work](#future-work))

## Data layout

### Per-symbol market history (local, append-friendly)

- **Path:** `datasets/market_data/{SYMBOL}.parquet` (one growing file per symbol).
- **Format:** Parquet.
- **Bar:** one row per **trading day** (daily bars).
- **Required columns (v1):**
  - `date` (or index): trading calendar date, **no duplicates**, ascending.
  - `open`, `high`, `low`, `close` — **all required** (no `open` fallback) so “next day open” execution stays honest.
  - `volume` — recommended; required if we use volume-based filters later (v1: **recommended**, validate if present).
- **Metadata columns (stored with the data, repeated per row is acceptable v1):**
  - `asset_type`: e.g. `stock` | `etf`
  - `expense_ratio`: annual fraction (e.g. `0.0003` for 0.03% / year). Use **`0.0` for stocks** unless we later model ongoing stock-level fees.

### Historical truth / reproducibility

- Adjusted vs raw: document the provider’s convention in the ingest step; prefer **stability** (treat each download append as extending a canonical local series).
- Past prices can be **revised** by vendors for adjusted series; local Parquet is still the **project’s SSOT** for backtests once written.

## Data acquisition

- **Default fetcher:** **Stooq** (no API key; suitable for bulk history).
- **Optional fetcher:** **Alpha Vantage** (API key; strict daily limits — use sparingly, e.g. gap-fill or spot checks).
- Ingestion writes/merges into `datasets/market_data/{SYMBOL}.parquet` (dedupe by date on append).

## Strategy interface (v1)

- Strategies are evaluated **daily** using information available through each day’s bar (close of day *t* for signal is acceptable **only if** trades execute **next** day at open — see Execution).
- Output: **target portfolio weights** per symbol for “as of” end of day *t*:
  - Long-only: each weight \(\ge 0\).
  - **Cash allowed:** weights sum to **≤ 1.0**; remainder is cash.
  - Symbols with weight `0` are not held.

## Execution model (v1)

- **Signal timing:** computed from data through day *t* (after that day’s close is known — classic “signal at close”).
- **Trade timing:** portfolio transitions toward the new target weights at **day *t+1* open** prices (next trading session).
- **Multi-symbol:** execute trades at each symbol’s next-day open; **corporate actions** not modeled beyond what’s in the price series.

## Costs (v1)

- **No** per-trade commission or slippage in v1.
- **ETF expense ratio:** apply a **small daily drag** on the **marked-to-market value** of each ETF position while held, using `expense_ratio` from the data (annual → daily conversion documented in implementation; e.g. \((1+r)^{1/252}-1\) on trading days unless we choose ACT/365 — pick one and document).

## Cash yield (risk-free)

- **Default:** fetch a **Fed-linked policy rate** series (implementation detail: e.g. **FRED** — exact series ID TBD) aligned to backtest calendar; convert to **daily** accrual on cash balance.
- **Override:** CLI flag **constant annual rate** (e.g. `--risk-free 0.045`) bypasses fetch for reproducibility or offline runs.

## Backtest outputs

- **Console:** summary metrics (TBD list: total return, CAGR, volatility, max drawdown, etc.).
- **Artifact:** Markdown report under **`docs/generated/backtests/`** (timestamped filename). Local `docs/generated/` may remain gitignored except placeholders; reports are for **local review** unless policy changes.

## Minimal v1 rebalancing (until “future TODO” lands)

Until we add **threshold-based / event-based** rebalancing rules:

- Whenever the strategy’s **target weights** change from the previous trading day’s targets, **rebalance at the next open** toward the new targets (subject to execution model above).

## Future work (explicit TODOs)

- **Rebalancing policy:** e.g. rebalance only when \(\|w - w_{prev}\|_1\) or per-name delta exceeds a threshold; calendar-based (monthly); or band-based.
- **Per-trade costs:** optional bps slippage / spread model; SEC fee on sells; commission schedules.
- **Corporate actions:** explicit splits/dividends if using raw prices.
- **Borrow / short / margin.**
- **Multi-currency.**

## Acceptance criteria (v1 implementation)

- Deterministic unit tests on **toy daily** OHLCV + known weights + known Fed override.
- Integration test: **two symbols** + cash + one ETF with non-zero `expense_ratio` produces stable equity path shape (no lookahead: signal day *t* cannot move capital at *t* open before signal exists).
- `uv run check code` passes after implementation.
