## Multi-Agent Equity Analysis Framework

This architecture leverages the **Model Context Protocol (MCP)** to transform Claude from a chatbot into an orchestration layer for financial analysis. By using a "team" of agents, we can mitigate the inherent biases of any single investment philosophy.

---

### 1. Overview of the Three Plugin Families

Financial MCP servers generally fall into three distinct architectural and logical "families." Each family provides the LLM with a different "sensory organ" for the market.

| Family | Primary Data Source | Core Objective | Typical Tools |
| --- | --- | --- | --- |
| **Technical / Momentum** | Exchange Price Feeds | Identifying price patterns, trend strength, and entry/exit timing. | `yfinance-mcp`, `alpaca-mcp`, `tradingview-mcp` |
| **Fundamental / Value** | SEC Filings, Balance Sheets | Determining "intrinsic value" and financial health. | `sec-mcp`, `edgar-mcp`, `capital-iq-mcp` |
| **Sentiment / Macro** | News Aggregators, Social, Fed Data | Gauging market "mood" and identifying qualitative tailwinds. | `newsapi-mcp`, `lseg-mcp`, `browser-use` |

---

### 2. Comparative Analysis: Pros & Cons

#### **Technical / Momentum**

* **Pros:** Highly objective; excellent for short-term timing; easy to automate with mathematical triggers (RSI, Moving Averages).
* **Cons:** Prone to "whipsaws" (false signals); ignores why a stock is moving; high competition from HFT (High-Frequency Trading) bots.

#### **Fundamental / Value**

* **Pros:** High margin of safety; aligns with long-term wealth building (REITs/BDCs); less affected by daily market volatility.
* **Cons:** Data is "lagging" (quarterly reports); a "cheap" stock can stay cheap forever (value traps); requires deep accounting knowledge to vet properly.

#### **Sentiment / Macro**

* **Pros:** Captures "the why" behind a move; identifies emerging tech trends (like Agentic AI) before they hit the balance sheet.
* **Cons:** High noise-to-signal ratio; subjective; sentiment can flip instantly based on a single tweet or news headline.

---

### 3. Implementation Plan: The "Triton" Agent Team

To build this, you can use a framework like **LangGraph** or **CrewAI** to manage the state and handoffs between specialized nodes.

#### **Phase 1: Environment & Hardening**

* **Containerization:** Deploy each MCP server in a separate **Docker** container.
* **Egress Filtering:** Configure your network to ensure the "Fundamental Agent" can only talk to SEC.gov/EDGAR, preventing data leakage.
* **Obsidian Sync:** Set up a local Git hook to push agent outputs directly into your Obsidian vault as daily markdown notes.

#### **Phase 2: The Agent Workflow (The "Consensus" Model)**

1. **The Scout (Technical):** Scans the top 500 tickers.
* *Trigger:* "Find all tickers where the 50-day MA has crossed the 200-day MA and RSI is < 60."

2. **The Auditor (Fundamental):** Receives the Scout's list.
* *Filter:* "Of these tickers, keep only those with a Debt/Equity < 1.0 and a Dividend Yield > 3%."

3. **The Analyst (Sentiment):** Performs a deep search on the remaining candidates.
* *Search:* "Analyze the last 3 transcript calls for [Ticker]. Are there mentions of supply chain risks or management changes?"

4. **The Manager (Aggregator):** Compiles the final report.
* *Output:* A Markdown table in your Obsidian vault with a "Unified Confidence Score" (0–100).

#### **Phase 3: Backtesting & Refinement**

* Integrate the agent's "High Confidence" picks into your **Monte Carlo simulation** software.
* Compare the agent's picks against historical regime changes to see how the "Consensus" model would have performed during the 2022 rate hikes or the 2024 AI surge.

