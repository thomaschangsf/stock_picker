from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    """Repository root (directory that contains ``src/``)."""
    # compose.py -> phase1/ -> stock_picker/ -> src/ -> repo root
    return Path(__file__).resolve().parents[3]


def compose_file() -> Path:
    return repo_root() / "infra" / "phase1" / "docker-compose.yml"


def run_compose(args: list[str]) -> int:
    """Run ``docker compose -f <compose> …``; returns process exit code."""
    cf = compose_file()
    if not cf.is_file():
        print(f"error: missing compose file {cf}", file=sys.stderr)
        return 1
    cmd = ["docker", "compose", "-f", str(cf), *args]
    return subprocess.call(cmd)
