"""Load KEY=value config files into the process environment."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from stock_picker.phase1.compose import repo_root


def load_repo_dotenv() -> None:
    """
    Load env vars from optional repo config files.

    **Precedence:** variables already set in the shell (or process) are **not**
    replaced (``override=False``). Among files, the **first** file wins on duplicate keys.

    **Resolution:**

    1. If ``STOCK_PICKER_ENV_FILE`` is set: load that path only if it exists (absolute path,
       or path relative to the repository root).
    2. Otherwise load, in order, if present: ``<repo>/.env`` then ``<repo>/config/secrets.env``.
    """
    root = repo_root()
    explicit = os.environ.get("STOCK_PICKER_ENV_FILE", "").strip()
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            alt = root / explicit
            path = alt if alt.is_file() else path
        if path.is_file():
            load_dotenv(path, override=False)
        return

    for rel in (Path(".env"), Path("config") / "secrets.env"):
        p = root / rel
        if p.is_file():
            load_dotenv(p, override=False)
