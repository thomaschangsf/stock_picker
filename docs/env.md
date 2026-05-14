# Environment variables and config files

Use this page as the **full reference** for what the CLI reads from the shell and from dotenv files. **`config/secrets.env.example`** is a short copy-paste template only.

## Quick check

`doctor` prints **numbered steps** for **Verify LangGraph** (`poc1 run`) and **Fetch Market, SEC, and Analysis Data** (`phase2 adhoc` — two separate commands; there is no `poc2` CLI).

```bash
uv run stock-picker doctor --symbol AAPL
uv run stock-picker doctor --strict --symbol AAPL   # exit 1 if any FAIL
```

- **Lines `why:`** — purpose; **Fetch Market, SEC, and Analysis Data** adds a **`what:`** block (Scout / Auditor / Analyst mapping).
- **Lines `1. 2. 3.`** — each requirement and `OK` / `WARN` / `FAIL` / `skip`.
- **`→ poc1:`** / **`→ phase2 adhoc:`** — short summary for that command.
- **`overall:`** — one line when both commands are checked (default `doctor`).
- **`--strict`** — exit **1** if any **FAIL** (WARN does not fail).

**Cold start:** missing `datasets/market_data/{SYMBOL}.parquet` is **WARN** until you import a CSV or copy Parquet; see [Market CSV for `import-csv`](#market-csv-for-import-csv) below.

Limit output:

```bash
uv run stock-picker doctor --for poc1
uv run stock-picker doctor --for phase2-adhoc --symbol AAPL
```

## How dotenv is loaded

`uv run stock-picker …` calls **`python-dotenv`** before any subcommand runs. Precedence:

1. Variables **already set in the shell** are **never** overwritten by files (`override=False`).
2. Among files, the **first** file that defines a key wins on duplicates.

**Resolution order:**

1. If **`STOCK_PICKER_ENV_FILE`** is set in the **shell** (not read from other dotenv files): load **only** that file if it exists (absolute path, or path relative to the **repository root**).
2. Otherwise, if present: **`<repo>/.env`**, then **`<repo>/config/secrets.env`**.

Do **not** commit real secrets. `.env` and `config/secrets.env` are gitignored.

**Setup:**

```bash
cp config/secrets.env.example config/secrets.env
# Edit config/secrets.env (see template comments and table below)
```

## Variable reference

| Variable | Used by | Required? | Purpose |
| --- | --- | --- | --- |
| `STOCK_PICKER_ENV_FILE` | CLI startup (shell only) | No | If set, load **only** this env file (absolute or repo-relative path). |
| `OPENAI_API_KEY` | `poc1 run` (Manager) | **Yes** for real Phase 0 LLM output | OpenAI API authentication. |
| `STOCK_PICKER_OPENAI_MODEL` | `poc1 run` | No | Default `gpt-4o-mini`. |
| `STOCK_PICKER_PRICE_INPUT_PER_1M` / `STOCK_PICKER_PRICE_OUTPUT_PER_1M` | `poc1 run` (`run_budget`) | No | Token price hints for estimated spend (USD per 1M tokens). |
| `STOCK_PICKER_SEC_USER_AGENT` | `phase2 adhoc` (SEC HTTP) | **Strongly recommended** | Sent as HTTP **User-Agent** to `www.sec.gov`. A generic built-in default exists, but SEC often returns **403** without a string that identifies **you** (include contact). |
| `FINNHUB_API_KEY` | `phase2 adhoc` (analyst add-on) | No | If set, adhoc makes **one** Finnhub quote call; token is **redacted** in printed JSON. |

**Not an env var:** market OHLCV for `phase2 adhoc` comes from **`datasets/market_data/{SYMBOL}.parquet`**. Create it with `phase2 import-csv` (CSV → Parquet) or copy an existing Parquet to that path.

## Market CSV for `import-csv`

Commands like `doctor` used to show `/path/to.csv` — that only means **“replace this with the path to a CSV file that already exists on your machine.”** It is not a special folder in the repo.

### Try the bundled demo file (smoke test)

From the **repository root** (where `pyproject.toml` lives), you can run:

```bash
uv run stock-picker phase2 import-csv AAPL --csv datasets/samples/aapl_ohlcv_sample.csv
```

That file is a **few fake rows** so you can verify the import pipeline. It is **not** real market data.

### Use your own CSV

1. Obtain a daily (or intraday) **OHLCV** export as **CSV** with a **header row** (column names). This repo does **not** pick a vendor for you. Typical sources people use (subject to each site’s terms and your subscription):

   - A **broker** or portfolio app **export**
   - A **paid data API** where you save or export results as CSV
   - **Your own** script that writes OHLCV to CSV

2. Put the file somewhere on disk (e.g. macOS **Downloads**).

3. Pass **that file’s path** after `--csv`. Examples (quotes help if the path has spaces):

   ```bash
   uv run stock-picker phase2 import-csv AAPL --csv "$HOME/Downloads/aapl_daily.csv"
   uv run stock-picker phase2 import-csv AAPL --csv ./my-data/aapl.csv
   ```

`read_csv_auto` is flexible about extra columns; you usually want at least a **date** column and **price** columns (`open` / `high` / `low` / `close` / `volume` are common).

### If you already have Parquet

Do **not** use `import-csv` (that subcommand only reads **CSV**). Copy or symlink your file to **`datasets/market_data/{SYMBOL}.parquet`**.

## At a glance

- **`poc1 run`:** LangGraph once over your prompt; Scout/Auditor/Analyst are **stubs**; **Manager** is the only node that calls **OpenAI**.
- **`phase2 adhoc SYMBOL`:** Prints **one JSON** bundle: **read** `datasets/market_data/SYMBOL.parquet` (OHLCV), **fetch/cache** SEC under `datasets/sec/`, optional Finnhub quote. **No OpenAI**, not LangGraph.

## `poc1 run` checklist

1. Set **`OPENAI_API_KEY`** (shell or `config/secrets.env`).
2. Optional: `STOCK_PICKER_OPENAI_MODEL`, price hint variables.

## `phase2 adhoc` checklist

**Parquet vs SEC (common confusion):** `SYMBOL.parquet` is **only** market OHLCV you supply (e.g. via `import-csv`). **`adhoc` never appends SEC into that Parquet** — it only **reads** it. SEC responses are cached as **separate files** under `datasets/sec/` (and paths appear in the JSON). `import-csv` **replaces** `SYMBOL.parquet` from the CSV each run; cold start = create that file once, then replace when you have a fuller CSV.

1. Set **`STOCK_PICKER_SEC_USER_AGENT`** to one line of plain text (name/email or project URL). SEC does **not** issue an API key; this is policy, not vendor signup.
2. Ensure **`datasets/market_data/{SYMBOL}.parquet`** exists (`phase2 import-csv` or your own writer).
3. Optional: **`FINNHUB_API_KEY`** for one quote in the analyst section.

## SEC User-Agent (step by step)

SEC does **not** give you a key for `www.sec.gov` requests. You set **`STOCK_PICKER_SEC_USER_AGENT`** to a string sent as the HTTP **`User-Agent`** header.

**Examples of a good value:**

- `Jane Doe jane.doe@company.com`
- `stock-picker dev (https://github.com/thomaschangsf/stock_picker)`

**Option A — `config/secrets.env` (recommended)**

1. `cp config/secrets.env.example config/secrets.env` if needed.
2. Add one line (no `export` keyword in the file). Use quotes if the value contains spaces:

   ```text
   STOCK_PICKER_SEC_USER_AGENT="Jane Doe jane.doe@company.com"
   ```

3. Save. Run `uv run stock-picker …` from the repo root.

**Option B — current shell only**

```bash
export STOCK_PICKER_SEC_USER_AGENT="Jane Doe jane.doe@company.com"
```

**Verify the loader sees it:**

```bash
uv run python -c "from stock_picker.load_env import load_repo_dotenv; import os; load_repo_dotenv(); print(os.environ.get('STOCK_PICKER_SEC_USER_AGENT') or '(not set)')"
```

Official background: [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).

## Debugging `phase2 adhoc` HTTP

On SEC or Finnhub HTTP errors, JSON may include **`http_debug`** (method, URL, status, truncated body). On SEC Atom failures, **`request_user_agent`** echoes the User-Agent sent. Finnhub URLs redact `token=` as `REDACTED`.
