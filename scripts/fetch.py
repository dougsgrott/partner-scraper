"""CLI for the fetch stage: archive page bytes under raw/. See PLAN.md §6, §9.

This is the one command that puts sustained load on someone else's servers. It is
deliberately rate-limited (1 req/s per host by default) and the limits live in
config/sources.yaml, not here — there is no flag to make it go faster.

Examples:
    uv run python scripts/fetch.py --dry-run                    # what would it fetch?
    uv run python scripts/fetch.py --source databricks-docs --limit 50
    uv run python scripts/fetch.py --refresh                    # revalidate the archive
    uv run python scripts/fetch.py                              # resume / fetch what's new
"""

from __future__ import annotations

import argparse
import logging

from scraper.config import load_config
from scraper.fetch.runner import run_fetch


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch pages into the raw archive.")
    ap.add_argument("--config", default="config/sources.yaml")
    ap.add_argument("--source", action="append", dest="sources", help="source id (repeatable)")
    ap.add_argument("--limit", type=int, help="cap URLs this run (use for a trial run first)")
    ap.add_argument(
        "--refresh",
        action="store_true",
        help="revalidate already-archived URLs with a conditional GET",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="re-fetch unconditionally, ignoring state and validators",
    )
    ap.add_argument("--dry-run", action="store_true", help="select jobs but make no requests")
    ap.add_argument("--offline", action="store_true", help="build the worklist from dumps only")
    ap.add_argument("-q", "--quiet", action="store_true", help="suppress progress lines")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.ERROR if args.quiet else logging.WARNING,
        format="%(message)s",
    )

    mode = "force" if args.force else "refresh" if args.refresh else "new"
    cfg = load_config(args.config)

    summary = run_fetch(
        cfg,
        source_ids=args.sources,
        mode=mode,
        limit=args.limit,
        dry_run=args.dry_run,
        use_sitemaps=not args.offline,
    )
    print(summary.render())


if __name__ == "__main__":
    main()
