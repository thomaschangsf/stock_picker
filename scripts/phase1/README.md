# Phase 1 scripts

- **`obsidian-sync.sh`** — copies `docs/generated/backtests/*.md` into `$OBSIDIAN_VAULT_PATH/StockPicker/backtests/`. Run manually from repo root, or install the hook below.
- **`install-obsidian-post-commit.sh`** — writes `.git/hooks/post-commit` to run `obsidian-sync.sh` after each commit (requires `OBSIDIAN_VAULT_PATH`).

```bash
export OBSIDIAN_VAULT_PATH="/path/to/your/ObsidianVault"
chmod +x scripts/phase1/*.sh
./scripts/phase1/install-obsidian-post-commit.sh
```
