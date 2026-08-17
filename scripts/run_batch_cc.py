"""CLI for the windowed CC batch runner.

Run key-free (uses the Claude Code login):
    env -u ANTHROPIC_API_KEY uv run python scripts/run_batch_cc.py --batch-size 5
Preview the work-list without spending tokens:
    uv run python scripts/run_batch_cc.py --dry-run
Drive periodicity externally, e.g. cron or the /loop skill:
    /loop 6h scripts/run_batch_cc.py
"""

from __future__ import annotations

import argparse
import logging

from scraper.cc_runner import run_batch
from scraper.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Windowed CC batch scraper (resumable).")
    parser.add_argument("--config", default="config/sources.yaml")
    parser.add_argument("--source", help="restrict to one company (default: config/all)")
    parser.add_argument("--batch-size", type=int, help="override batch.size for this run")
    parser.add_argument("--only", help="restrict this run to URLs whose path starts with this")
    parser.add_argument("--dry-run", action="store_true", help="print the work-list; spend no tokens")
    parser.add_argument("--verbose", action="store_true", help="log each page result")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    cfg = load_config(args.config)
    companies = [args.source] if args.source else None
    summary = run_batch(
        cfg,
        companies=companies,
        batch_size=args.batch_size,
        only=args.only,
        dry_run=args.dry_run,
    )
    print(summary)


if __name__ == "__main__":
    main()
