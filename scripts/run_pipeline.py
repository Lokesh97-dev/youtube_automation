#!/usr/bin/env python3
"""CLI entrypoint invoked by the GitHub Actions workflow (and usable
locally for testing): generates one day's video end-to-end.

Usage:
    python scripts/run_pipeline.py [--date YYYY-MM-DD]
"""
import argparse
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.orchestrator import run_pipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date to generate (YYYY-MM-DD). Defaults to today (UTC).",
    )
    args = parser.parse_args()

    run_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else date.today()

    try:
        result = run_pipeline(run_date)
    except Exception as exc:
        print(f"Pipeline failed for {run_date.isoformat()}: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Done: {result}")


if __name__ == "__main__":
    main()
