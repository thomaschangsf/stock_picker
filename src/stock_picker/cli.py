import argparse


def main() -> None:
    parser = argparse.ArgumentParser(prog="stock-picker")
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    args = parser.parse_args()

    if args.version:
        from stock_picker import __version__

        print(__version__)
        return

    parser.print_help()


if __name__ == "__main__":
    main()

