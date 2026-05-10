# Phase 1 — Environment & hardening

Implements **`specs/poc-1.md` Phase 1** in this repo:

1. **Containerization** — three placeholder MCP services (`mcp-quant`, `mcp-fundamental`, `mcp-sentiment`) plus a **Squid** forward-proxy for the fundamental role.
2. **Egress filtering (Fundamental)** — `mcp-fundamental` is attached **only** to `mcp_internal` (no direct `mcp_wan`). It must use `HTTP_PROXY` / `HTTPS_PROXY` pointing at **`squid-fundamental`**, whose `squid.conf` allowlists **SEC / EDGAR–related** hostnames. Extend `squid-fundamental/squid.conf` if tools need additional domains.
3. **Obsidian sync** — optional git hook; see `scripts/phase1/`.

## Bring the stack up

From the **repository root**:

```bash
docker compose -f infra/phase1/docker-compose.yml up -d --build
docker compose -f infra/phase1/docker-compose.yml ps
```

Or:

```bash
uv run stock-picker phase1 up
uv run stock-picker phase1 ps
```

Tear down:

```bash
uv run stock-picker phase1 down
```

## Verify Squid allowlist (optional)

With the stack running:

```bash
docker compose -f infra/phase1/docker-compose.yml exec mcp-fundamental \
  curl -fsS -x http://squid-fundamental:3128 https://www.sec.gov/robots.txt | head
```

**Squid ACL:** only **`dstdomain .sec.gov`** is allowlisted (Squid 6 rejects listing both `.sec.gov` and `sec.gov` in the same ACL).

**SEC edge behavior:** you may see **HTTP 403** from `www.sec.gov` for scripted or data-center traffic even when CONNECT succeeded—use `curl -v` to confirm the response is from SEC, not a Squid deny.

A request to a non-allowlisted host through the same proxy should **fail** (confirming the proxy is in path). Direct `curl https://example.com` **without** proxy from `mcp-fundamental` should fail (no route / connection refused) because that container has **no** `mcp_wan` network.

## Replace placeholders

Swap `alpine` + `sleep infinity` images for real MCP server images or bind-mounted builds in **Phase 2**, keeping the same service names and networks where possible.
