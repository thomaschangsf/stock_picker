#!/usr/bin/env bash
# Copy generated backtest markdown into an Obsidian vault directory.
# Usage (from repo root): OBSIDIAN_VAULT_PATH=/path/to/vault ./scripts/phase1/obsidian-sync.sh
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

VAULT="${OBSIDIAN_VAULT_PATH:-}"
if [[ -z "$VAULT" ]]; then
  echo "error: set OBSIDIAN_VAULT_PATH to your Obsidian vault root" >&2
  exit 1
fi

DEST="$VAULT/StockPicker/backtests"
mkdir -p "$DEST"

shopt -s nullglob
files=(docs/generated/backtests/*.md)
if ((${#files[@]} == 0)); then
  echo "no docs/generated/backtests/*.md to copy"
  exit 0
fi

cp -v "${files[@]}" "$DEST/"
echo "synced ${#files[@]} file(s) -> $DEST"
