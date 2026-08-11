"""CLI entrypoint for on-demand report generation."""

from __future__ import annotations

import argparse
import json
import sys

from app.core.logging import setup_logging
from app.reports.generator import generate_reports


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="Generate AWS FinOps cost reports")
    parser.add_argument(
        "--period",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="Report period",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print summary as JSON to stdout",
    )
    args = parser.parse_args()

    result = generate_reports(period=args.period)
    print(f"CSV : {result['csv']}")
    print(f"HTML: {result['html']}")
    print(f"PDF : {result['pdf']}")

    if args.json:
        summary = result.get("summary")
        if summary:
            # make serializable
            print(json.dumps(summary, default=str, indent=2))

    sys.exit(0)


if __name__ == "__main__":
    main()
