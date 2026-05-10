from __future__ import annotations

import argparse
import subprocess
import sys


def _run(cmd: list[str]) -> int:
    try:
        return subprocess.call(cmd)
    except FileNotFoundError:
        print(f"Missing command: {cmd[0]}", file=sys.stderr)
        return 127


def check(argv: list[str] | None = None) -> None:
    """
    `uv run check code` style entrypoint.
    """
    parser = argparse.ArgumentParser(prog="check")
    sub = parser.add_subparsers(dest="target", required=True)
    sub.add_parser("code", help="Run ruff + pytest (if installed).")
    args = parser.parse_args(argv)

    if args.target == "code":
        ruff_rc = _run(["ruff", "check", "src/"])
        pytest_rc = _run(["pytest", "tests/"])

        # pytest returns 5 when no tests are collected; treat that as success.
        if pytest_rc == 5:
            pytest_rc = 0

        raise SystemExit(ruff_rc or pytest_rc)


if __name__ == "__main__":
    check()

