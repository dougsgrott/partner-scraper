"""CLI for the extract stage: raw archive → Markdown corpus. See PLAN.md §7, §9.

Touches no network. Re-running it is free, which is the point — iterate on an extractor
and re-run over `raw/` as often as needed.

Examples:
    uv run python scripts/extract.py                        # extract what's new/changed
    uv run python scripts/extract.py --force                # re-extract everything
    uv run python scripts/extract.py --only-failed          # retry past failures
    uv run python scripts/extract.py --source databricks-docs --limit 20
    uv run python scripts/extract.py --prune                # also delete orphaned files
"""

from __future__ import annotations

import argparse
import logging

from scraper.config import load_config
from scraper.extract import run_extract


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract archived pages into the corpus.")
    ap.add_argument("--config", default="config/sources.yaml")
    ap.add_argument("--source", action="append", dest="sources", help="source id (repeatable)")
    ap.add_argument("--limit", type=int, help="stop after N pages (for a trial run)")
    ap.add_argument("--force", action="store_true", help="re-extract even if unchanged")
    ap.add_argument("--only-failed", action="store_true", help="retry pages that failed before")
    ap.add_argument("--prune", action="store_true",
                    help="delete corpus files no longer claimed by the index")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    cfg = load_config(args.config)
    summary = run_extract(
        cfg,
        source_ids=args.sources,
        force=args.force,
        only_failed=args.only_failed,
        limit=args.limit,
        prune=args.prune,
    )
    print(summary.render())


if __name__ == "__main__":
    main()
