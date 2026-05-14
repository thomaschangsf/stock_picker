import argparse
import json
import sys

from stock_picker.load_env import load_repo_dotenv


def main() -> None:
    load_repo_dotenv()
    parser = argparse.ArgumentParser(prog="stock-picker")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    sub = parser.add_subparsers(dest="cmd")

    doc_p = sub.add_parser(
        "doctor",
        help="Step checklist: Verify LangGraph (poc1) vs Market/SEC/Analysis (phase2 adhoc).",
    )
    doc_p.add_argument(
        "--for",
        dest="doctor_for",
        choices=("poc1", "phase2-adhoc"),
        default=None,
        metavar="PROFILE",
        help="Limit output to poc1 or phase2-adhoc (default: show both).",
    )
    doc_p.add_argument(
        "--symbol",
        default=None,
        metavar="TICKER",
        help="Ticker to check for datasets/market_data/{SYMBOL}.parquet (e.g. AAPL).",
    )
    doc_p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any shown profile has FAIL (for scripts/CI).",
    )

    poc1 = sub.add_parser("poc1", help="Phase 0 Triton POC (specs/poc-1.md)")
    poc1_sub = poc1.add_subparsers(dest="poc1_cmd", required=True)
    run_p = poc1_sub.add_parser("run", help="Run LangGraph once (Manager calls OpenAI)")
    run_p.add_argument(
        "--prompt",
        required=True,
        help="User prompt (include tickers like AAPL in uppercase for best extraction).",
    )
    run_p.add_argument(
        "--max-seconds",
        type=float,
        default=120.0,
        help="run_budget.max_seconds (default: 120).",
    )
    run_p.add_argument(
        "--max-spend-usd",
        type=float,
        default=2.0,
        help="run_budget.max_spend_usd LLM estimate cap (default: 2).",
    )

    ph1 = sub.add_parser("phase1", help="Phase 1 Docker + Obsidian helpers (specs/poc-1.md)")
    ph1_sub = ph1.add_subparsers(dest="phase1_cmd", required=True)
    ph1_sub.add_parser("up", help="docker compose up -d --build")
    ph1_sub.add_parser("down", help="docker compose down")
    ph1_sub.add_parser("ps", help="docker compose ps")
    ph1_sub.add_parser("verify", help="docker compose config (validate compose file)")

    ph2 = sub.add_parser(
        "phase2",
        help="Phase 2 utilities (specs/poc-1.md): ad-hoc reads from datasets/market_data/",
    )
    ph2_sub = ph2.add_subparsers(dest="phase2_cmd", required=True)
    fetch_p = ph2_sub.add_parser(
        "fetch",
        help="Summarize datasets/market_data/{SYMBOL}.parquet (DuckDB read_parquet)",
    )
    fetch_p.add_argument("symbol", help="Ticker symbol (e.g. AAPL, BRK-B, BF.B)")
    import_p = ph2_sub.add_parser(
        "import-csv",
        help="Import a CSV file and write datasets/market_data/{SYMBOL}.parquet",
    )
    import_p.add_argument("symbol", help="Ticker symbol (e.g. AAPL, BRK-B, BF.B)")
    import_p.add_argument("--csv", required=True, help="Path to CSV to import.")
    adhoc_p = ph2_sub.add_parser(
        "adhoc",
        help="Fetch 3 data sets (market parquet + SEC + optional Finnhub) and print JSON",
    )
    adhoc_p.add_argument("symbol", help="Ticker symbol (e.g. AAPL, BRK-B, BF.B)")

    args = parser.parse_args()

    if args.cmd == "doctor":
        from stock_picker.doctor import run_doctor

        code = run_doctor(
            for_profile=args.doctor_for,
            symbol=args.symbol,
            strict=args.strict,
        )
        raise SystemExit(code)

    if args.version:
        from stock_picker import __version__

        print(__version__)
        return

    if args.cmd == "poc1":
        if args.poc1_cmd == "run":
            from stock_picker.poc1.budget import RunBudget
            from stock_picker.poc1.graph import run_triton_poc

            budget = RunBudget(max_seconds=args.max_seconds, max_spend_usd=args.max_spend_usd)
            try:
                out = run_triton_poc(user_prompt=args.prompt, budget=budget)
            except Exception as e:
                print(f"error: {e}", file=sys.stderr)
                raise SystemExit(1) from e
            print(json.dumps(out, indent=2))
            return

    if args.cmd == "phase1":
        from stock_picker.phase1.compose import run_compose

        mapping = {
            "up": ["up", "-d", "--build"],
            "down": ["down"],
            "ps": ["ps"],
            "verify": ["config"],
        }
        extra = mapping.get(args.phase1_cmd)
        if extra is None:
            raise SystemExit(f"unknown phase1 command: {args.phase1_cmd!r}")
        raise SystemExit(run_compose(extra))

    if args.cmd == "phase2":
        if args.phase2_cmd == "adhoc":
            from stock_picker.phase2.adhoc import run_phase2_adhoc

            try:
                out = run_phase2_adhoc(args.symbol)
            except Exception as e:
                print(f"error: {e}", file=sys.stderr)
                raise SystemExit(1) from e

            print(json.dumps(out.to_json_dict(), indent=2))
            return

        # Backwards-compatible utilities (kept for now).
        if args.phase2_cmd == "fetch":
            from stock_picker.phase2.scout import summarize_parquet

            try:
                summary = summarize_parquet(args.symbol)
            except FileNotFoundError:
                print(
                    json.dumps(
                        {
                            "error": "missing_market_data",
                            "expected_path": (
                                f"datasets/market_data/{args.symbol.strip().upper()}.parquet"
                            ),
                        },
                        indent=2,
                    ),
                    file=sys.stderr,
                )
                raise SystemExit(2)
            except Exception as e:
                print(f"error: {e}", file=sys.stderr)
                raise SystemExit(1) from e

            print(json.dumps(summary.to_json_dict(), indent=2))
            return

        if args.phase2_cmd == "import-csv":
            from pathlib import Path

            from stock_picker.phase2.scout import import_csv_to_parquet

            try:
                summary = import_csv_to_parquet(args.symbol, csv_path=Path(args.csv))
            except FileNotFoundError as e:
                print(
                    json.dumps(
                        {
                            "error": "missing_file",
                            "path": str(e),
                        },
                        indent=2,
                    ),
                    file=sys.stderr,
                )
                raise SystemExit(2)
            except ValueError as e:
                print(
                    json.dumps({"error": "invalid_csv_input", "detail": str(e)}, indent=2),
                    file=sys.stderr,
                )
                raise SystemExit(2) from e
            except Exception as e:
                print(f"error: {e}", file=sys.stderr)
                raise SystemExit(1) from e

            print(json.dumps(summary.to_json_dict(), indent=2))
            return

    parser.print_help()


if __name__ == "__main__":
    main()

