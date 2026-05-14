# Analyst (Phase 2a) — coverage and options

This document matches **`specs/poc-1.md`**: Phase 2a Analyst is a **hybrid**—**SEC-only baseline**, plus an **optional Finnhub** path (strict **1–2** API calls per daily batch on the **free** tier). Update this file when behavior or limits change.

## Baseline (always on): SEC analysis

**Covered (intent for Phase 2a implementation):**

- **SEC RSS / Atom** and other **SEC family** HTTP targets already allowed via **`infra/phase1/squid-fundamental/squid.conf`** (maintained in-repo; PR-reviewed additions).
- **Narrative / “sentiment”** derived from **regulator-issuer** artifacts (e.g. press releases, filings pointers) that the **Auditor** and **Scout** subgraph already surfaced—**not** open-web social listening.

**Not covered by baseline:**

- Broad **social** sentiment (Reddit/X/StockTwits).
- **Per-ticker issuer IR RSS** at **S&P scale** (high curation cost; see **Future TODOs**).
- **Paid** “general news” APIs (e.g. NewsAPI Business tier) unless explicitly added later.

## Optional: Finnhub (free tier, strict call budget)

**When enabled** (e.g. env flag + `FINNHUB_API_KEY`):

- **At most 1–2 Finnhub HTTP requests per daily batch run** (design for **batch** queries, not per-ticker spam).
- **Domains:** allowlist **`finnhub.io`** (and any **documented** subdomains/CDNs Finnhub requires) in Squid **only** when this option is on—same PR discipline as other non-SEC domains.

**When disabled (default for $0 incremental news):**

- Analyst output is **SEC baseline only**; the graph must still validate and complete.

**Operational note:** Finnhub’s **free tier limits and commercial terms change**—before production reliance, re-read [Finnhub API documentation](https://finnhub.io/docs/api) and your account dashboard; reflect actual limits in code and in this doc.

## What “hybrid” means here

| Layer | Source | Cost posture |
| --- | --- | --- |
| Baseline | SEC family (+ graph context from Scout/Auditor) | No third-party news subscription required |
| Optional | Finnhub (1–2 calls / daily batch) | Uses **free** tier only in Phase 2a design |

This is **not** “NewsAPI + full web search” hybrid.

## Future TODOs (not Phase 2a unless pulled in explicitly)

1. **Issuer IR RSS / Atom** for a **small watchlist** (tens of names), with explicit feed URLs or a curated `datasets/ir_feeds.csv`—not S&P-wide by default.
2. **Transcripts** (vendor TBD; licensing + allowlist work).
3. **Additional bounded providers** (≤4 total per `specs/poc-1.md`) with Squid domain PRs—e.g. a paid news API **if budget allows**.
4. **Social / forum** sources only with explicit **legal/ToS** review and a **separate** threat model (likely not Squid-only).
5. **Finnhub**: promote beyond “1–2 calls” only after measuring quota + cost + value; consider **paid** Finnhub only if free tier is insufficient.

## Related specs

- [specs/poc-1.md](../specs/poc-1.md) — Phase 2 locks (transport, orchestrator, Scout, Auditor, Analyst).
- [specs/backtesting-v1.md](../specs/backtesting-v1.md) — Parquet / market data conventions (Scout side).
