from stock_picker.load_env import load_repo_dotenv


def test_load_repo_dotenv_runs_without_error() -> None:
    """Smoke: must not raise when optional files are absent."""
    load_repo_dotenv()
