# stock_picker

Agent-oriented Python repo structure (modeled after `modelAgent`) so artifacts and code are easy to review:

- `AGENTS.md`: agent operating rules
- `ARCHITECTURE.md`: layering + dependency intent
- `docs/`: decisions, generated docs, doc index
- `specs/`: build plans/specs for planned work
- `src/stock_picker/`: Python source
- `tests/`: tests

## How to run locally

### Prerequisites

- **[uv](https://docs.astral.sh/uv/)** installed
- **Python 3.11+** (uv will download a matching interpreter if needed)

### Clone and install

From the directory that contains this repo (or after `git clone`):

```bash
cd stock_picker
uv sync --all-extras
```

That creates `.venv/` and installs runtime + dev dependencies (`pytest`, `ruff`, etc.).

### Checks

```bash
uv run check code
```

### CLI overview

```bash
uv run stock-picker --help
```

### Phase 0 Triton POC (`specs/poc-1.md`)

Runs **LangGraph** Scout → Auditor → Analyst → **Manager (OpenAI)** with **Pydantic** handoffs and **`run_budget`**.

1. Set your OpenAI API key (required for the Manager node):

```bash
export OPENAI_API_KEY="your-key-here"
```

2. Run one full graph pass:

```bash
uv run stock-picker poc1 run --prompt "Quick read on Nvidia and Brk-b"
```

Use **uppercase tickers** in the prompt for best extraction (e.g. `AAPL`); if none are found, the stub Scout uses **`SPY`**.

**What is “real” in Phase 0?** Only the **Manager** step calls **OpenAI**. Scout / Auditor / Analyst use **in-repo stubs** (regex tickers from your text, pass-through list, placeholder sentiment). There is **no** Stooq, Alpha Vantage, SEC/EDGAR, FRED, or MCP market-data fetch in Phase 0—so you are **not** yet pulling OHLCV, filings, or headlines from vendors through this pipeline.

**When do real sources enter?** See `specs/poc-1.md` for the full roadmap. In short:

- **Phase 1 — Environment & hardening:** Dockerized MCP servers, egress policy, Obsidian sync hooks. This **prepares** safe outbound access; it does not by itself define the research screen.
- **Phase 2 — Consensus workflow:** The spec’s Scout / Auditor / Analyst behavior assumes **real tools/APIs** (e.g. market data, SEC/EDGAR, news) behind MCP, typically **after** Phase 1’s execution layer exists.

Until Phase 2 (plus real MCP implementations), treat outputs as **orchestration and LLM synthesis demos**, not verified data-backed screens.

**Optional environment variables**

- `STOCK_PICKER_OPENAI_MODEL` — default `gpt-4o-mini`
- `STOCK_PICKER_PRICE_INPUT_PER_1M` / `STOCK_PICKER_PRICE_OUTPUT_PER_1M` — USD per 1M tokens for **`run_budget`** spend estimates (defaults approximate public list pricing; change if your model differs)

**Tune run limits**

```bash
uv run stock-picker poc1 run --prompt "SOFI" --max-seconds 60 --max-spend-usd 1.0
```

