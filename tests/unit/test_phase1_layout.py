from pathlib import Path

from stock_picker.phase1.compose import compose_file, repo_root


def test_repo_root_contains_src() -> None:
    root = repo_root()
    assert (root / "src" / "stock_picker").is_dir()


def test_phase1_compose_and_readmes_exist() -> None:
    root = repo_root()
    assert compose_file().is_file()
    assert (root / "infra" / "phase1" / "README.md").is_file()
    assert (root / "infra" / "phase1" / "squid-fundamental" / "squid.conf").is_file()
    assert (root / "scripts" / "phase1" / "obsidian-sync.sh").is_file()
