import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(prog="stock-picker")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    sub = parser.add_subparsers(dest="cmd")

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

    args = parser.parse_args()

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

    parser.print_help()


if __name__ == "__main__":
    main()

