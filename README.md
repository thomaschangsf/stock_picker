# stock_picker

Agent-oriented Python repo (after `modelAgent`): `AGENTS.md`, `ARCHITECTURE.md`, `docs/`, `specs/`, `src/stock_picker/`, `tests/`.

## How to run locally

### Prerequisites

- **[uv](https://docs.astral.sh/uv/)**
- **Python 3.11+** (uv can fetch a matching interpreter)

### Clone and install

From the directory that contains this repo (or after `git clone`):

```bash
cd stock_picker
uv sync --all-extras
```

### Quick start (env + `phase2 adhoc`)

From repo root. Set secrets first — **[docs/env.md](docs/env.md)** (copy `config/secrets.env.example` → `config/secrets.env`).

```bash
uv run stock-picker doctor --symbol AAPL
# optional: add --strict  →  exit 1 if any FAIL

# Optional: demo OHLCV Parquet (tiny sample; real CSV paths → docs/env.md § Market CSV)
uv run stock-picker phase2 import-csv AAPL --csv datasets/samples/aapl_ohlcv_sample.csv

uv run stock-picker phase2 adhoc AAPL
```

Missing `datasets/market_data/{SYMBOL}.parquet` is a **WARN** in `doctor` and yields `missing_market_data` in JSON; **SEC (and optional Finnhub) still run**.

### Checks

```bash
uv run check code
```

### API keys and environment variables

**Do not commit** real secrets. `.env` and `config/secrets.env` are gitignored.

- Template: **`config/secrets.env.example`** → `config/secrets.env` or repo-root `.env`.
- Full variable list, SEC User-Agent, HTTP debug fields: **[docs/env.md](docs/env.md)**.

```bash
cp config/secrets.env.example config/secrets.env
# edit — see docs/env.md
```

### CLI overview

```bash
uv run stock-picker --help
uv run stock-picker doctor --help
```

### Phase 0 — Triton POC (`specs/poc-1.md`)

**LangGraph** Scout → Auditor → Analyst → **Manager (OpenAI)** with Pydantic + `run_budget`.

1. Set **`OPENAI_API_KEY`** in **`config/secrets.env`** / **`.env`** (see **[API keys and environment variables](#api-keys-and-environment-variables)** above) or in the shell:

```bash
export OPENAI_API_KEY="your-key-here"
```

2. Run:

```bash
uv run stock-picker poc1 run --prompt "Quick read on Nvidia and Brk-b"
```

Use **uppercase tickers** in the prompt when you can; if none match, the stub Scout uses **`SPY`**.

**Reality check:** only **Manager** calls **OpenAI**; other nodes are **stubs** (no live market/SEC/MCP fetches in Phase 0). Roadmap and “when do real sources land?” → **`specs/poc-1.md`**.

### Phase 1 — Docker + egress + Obsidian (`specs/poc-1.md`)

**Squid** ([squid-cache.org](http://www.squid-cache.org/)) is the HTTP(S) forward proxy in **`infra/phase1/squid-fundamental/`** (here: **`.sec.gov` only**). Placeholder MCP containers + **`squid-fundamental`** are in **`infra/phase1/docker-compose.yml`**; outbound from the fundamental container is meant to go via **`HTTP_PROXY` / `HTTPS_PROXY`**.

```bash
uv run stock-picker phase1 verify
uv run stock-picker phase1 up
uv run stock-picker phase1 ps
uv run stock-picker phase1 down
```

Details, smoke tests, **403** notes: **`infra/phase1/README.md`**. Optional Obsidian hooks: **`scripts/phase1/README.md`**.

Optional: `STOCK_PICKER_OPENAI_MODEL`, `STOCK_PICKER_PRICE_INPUT_PER_1M` / `STOCK_PICKER_PRICE_OUTPUT_PER_1M` for `run_budget` hints.

```bash
uv run stock-picker poc1 run --prompt "SOFI" --max-seconds 60 --max-spend-usd 1.0
```

### Phase 2 — `phase2 adhoc` (market + SEC + analyst JSON)

**Status:** specified / partial; see **`specs/poc-1.md`**, **`docs/analyst-coverage.md`**.

`uv run stock-picker phase2 adhoc SYMBOL` prints **one JSON** with:

| Key | Source |
| --- | --- |
| `scout_market` | Reads **`datasets/market_data/{SYMBOL}.parquet`** (OHLCV). No host OHLCV vendor fetch — build with **`phase2 import-csv`** or your own Parquet. If missing → `missing_market_data`; other slices still run. |
| `auditor_sec` | SEC ticker map + filings **Atom** (cached under **`datasets/sec/`**). |
| `analyst` | SEC-only stub lines + **optional** one Finnhub quote if **`FINNHUB_API_KEY`** is set. |

Env + SEC User-Agent + Parquet checks: **`uv run stock-picker doctor --symbol SYMBOL`**; details **[docs/env.md](docs/env.md)**.

On HTTP errors, JSON may include **`http_debug`**, **`request_user_agent`**, etc. — see **docs/env.md**.

Example import (demo CSV) then adhoc:

```bash
uv run stock-picker phase2 import-csv AAPL --csv datasets/samples/aapl_ohlcv_sample.csv
uv run stock-picker phase2 adhoc AAPL
```

Real CSV path example: `uv run stock-picker phase2 import-csv AAPL --csv "$HOME/Downloads/your_aapl.csv"` — more in **docs/env.md** § *Market CSV for import-csv*.

Live Scout MCP (e.g. Alpha Vantage) without host Parquet is **not** wired yet — **`specs/poc-1.md`**.
