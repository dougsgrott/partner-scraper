"""Find (and optionally probe) pages the corpus links to but does not contain.

Sitemap-driven discovery has a ceiling: `/aws/en/agents/agent-evaluation` is live, in
scope, and linked from pages we hold — and listed in no sitemap the site publishes. The
corpus's own link graph is the only index that knows about such pages.

`--probe` sends one HEAD per candidate at the fetcher's rate, because a link may also
point at something renamed or deleted. Nothing here fetches a page body.

Examples:
    uv run python scripts/link_gap.py                       # list candidates, no network
    uv run python scripts/link_gap.py --probe               # HEAD each one, classify
    uv run python scripts/link_gap.py --probe --write-dump sitemap-dumps/link-gap.txt
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from scraper.config import load_config
from scraper.worklist import dumps, linkgraph


def main() -> None:
    ap = argparse.ArgumentParser(description="Pages the corpus links to but lacks.")
    ap.add_argument("--config", default="config/sources.yaml")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--fetch-db", default="state/fetch.db")
    ap.add_argument("--probe", action="store_true", help="HEAD each candidate (1 req/s)")
    ap.add_argument("--limit", type=int, help="probe only the N most-referenced")
    ap.add_argument("--write-dump", metavar="PATH",
                    help="write live candidates as a dump the worklist can seed from")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cfg = load_config(args.config)
    candidates = linkgraph.discover(cfg, data_dir=args.data_dir, fetch_db_path=args.fetch_db)
    print(f"{len(candidates)} in-scope page(s) linked by the corpus but not archived")

    if args.probe:
        probed = linkgraph.probe(candidates, user_agent=cfg.defaults.user_agent,
                                 requests_per_second=cfg.defaults.requests_per_second,
                                 limit=args.limit)
        verdicts = Counter(c.verdict for c in probed)
        print("\nprobe results:")
        for verdict, n in verdicts.most_common():
            print(f"   {n:>4}  {verdict}")
        live = [c for c in probed if c.fetchable]
        print("\nmost-referenced live pages missing from the corpus:")
        for c in live[:10]:
            print(f"   {c.references:>4}×  {c.url}")

        if args.write_dump and live:
            path = Path(args.write_dump)
            count = dumps.write(path, linkgraph.as_dump(probed))
            print(f"\nwrote {count} live URLs to {path}")
        if args.json:
            print(json.dumps([{"url": c.url, "references": c.references,
                               "status": c.status, "verdict": c.verdict} for c in probed],
                             indent=2))
    elif args.json:
        print(json.dumps([{"url": c.url, "references": c.references} for c in candidates],
                         indent=2))


if __name__ == "__main__":
    main()
