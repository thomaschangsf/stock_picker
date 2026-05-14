# ADR 001: Backtesting v1 scope and realism defaults

## Status

Accepted (planning).

## Context

We want a **realistic but simple** backtester for **long-hold** portfolios: daily evaluation, multi-symbol weights, optional cash, ETF expense drag, and a **Fed-linked** cash yield, without over-modeling trading friction.

## Decision

1. **Positions:** long-only; strategies output **explicit weights** per symbol; **cash allowed** (weights sum \(\le 1\)).
2. **Bars:** **daily**; local canonical store: **`datasets/market_data/{SYMBOL}.parquet`** (append new dates).
3. **Execution:** signal after day *t* data; **trade at next day open**; **`open` required** (no cheating with close-as-open).
4. **Costs v1:** **ETF `expense_ratio` daily drag** from data; **no** per-trade slippage/commissions (deferred as third-order).
5. **Metadata in price data:** include **`asset_type`** and **`expense_ratio`** alongside OHLCV.
6. **Rates:** default **fetch Fed-linked series**; **`--risk-free`** constant annual override for offline/reproducible runs.
7. **Fetchers:** **Parquet / user ingest primary**; **Alpha Vantage optional** (key + strict limits) for documented API pulls.
8. **Reports:** write Markdown under **`docs/generated/backtests/`**.
9. **Rebalancing sophistication:** deferred; v1 uses **“rebalance next open whenever targets change”** until threshold/calendar rules exist.

## Consequences

- **Pros:** clear semantics, minimal moving parts, reproducible local data, aligns with long-hold mental model.
- **Cons:** ignores spread/slips and rich rebalance policies until later ADRs.

## Alternatives considered

- Same-day close execution — rejected (lookahead / optimism).
- Close-only data with synthetic open — rejected (explicitly “don’t cheat”).
- Alpha Vantage as default — rejected (25 requests/day free tier is too small for routine bulk ingest).
