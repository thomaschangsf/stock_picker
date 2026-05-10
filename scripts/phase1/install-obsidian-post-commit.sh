#!/usr/bin/env bash
# Install a post-commit hook that runs obsidian-sync.sh (specs/poc-1.md Phase 1).
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
HOOK="$ROOT/.git/hooks/post-commit"
SCRIPT="$ROOT/scripts/phase1/obsidian-sync.sh"

if [[ ! -x "$SCRIPT" ]]; then
  chmod +x "$SCRIPT"
fi

cat >"$HOOK" <<'EOF'
#!/usr/bin/env bash
set -e
ROOT="$(git rev-parse --show-toplevel)"
exec "$ROOT/scripts/phase1/obsidian-sync.sh"
EOF
chmod +x "$HOOK"

echo "Installed $HOOK (runs obsidian-sync.sh after each commit)."
echo "Set OBSIDIAN_VAULT_PATH in your shell profile or export before committing."
