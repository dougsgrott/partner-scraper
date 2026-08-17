"""CLI for inspecting the fetch work-list. Fetches sitemaps + robots.txt only — never a page.

Examples:
    uv run python scripts/worklist.py                       # every enabled source
    uv run python scripts/worklist.py --offline             # dumps only, no network
    uv run python scripts/worklist.py --source databricks-docs --sample 5
    uv run python scripts/worklist.py --json
"""

from __future__ import annotations

import argparse
import json
import logging

from scraper.config import load_config
from scraper.worklist import Worklist, build_all


def _print(wl: Worklist, *, sample: int) -> None:
    c = wl.counts
    print(f"{wl.source_id}  ({wl.company})")
    print(
        f"  seeded {c.seeded:>6}"
        f"   -out-of-scope {c.out_of_scope:>6}"
        f"   -robots {c.robots_blocked:>4}"
        f"   -capped {c.capped:>5}"
        f"   => {c.final:>6}"
    )
    for du in wl.urls[:sample]:
        print(f"    {du.lastmod or '----------'}  {du.url}")
    if sample and len(wl.urls) > sample:
        print(f"    … {len(wl.urls) - sample} more")
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="Build and inspect the fetch work-list.")
    ap.add_argument("--config", default="config/sources.yaml")
    ap.add_argument("--source", action="append", dest="sources", help="source id (repeatable)")
    ap.add_argument("--offline", action="store_true", help="dumps only; skip sitemaps + robots")
    ap.add_argument("--include-disabled", action="store_true")
    ap.add_argument("--sample", type=int, default=0, help="print N example URLs per source")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    cfg = load_config(args.config)
    worklists = build_all(
        cfg,
        source_ids=args.sources,
        include_disabled=args.include_disabled,
        use_sitemaps=not args.offline,
    )

    if args.json:
        print(json.dumps(
            [
                {"source_id": w.source_id, "company": w.company, **w.counts.to_dict()}
                for w in worklists
            ],
            indent=2,
        ))
        return

    for wl in worklists:
        _print(wl, sample=args.sample)

    total = sum(len(w) for w in worklists)
    print(f"TOTAL to fetch: {total}")


if __name__ == "__main__":
    main()
