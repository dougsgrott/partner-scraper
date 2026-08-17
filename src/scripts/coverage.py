"""CLI for coverage / category breakdown. Read-only, no tokens. See docs/coverage.md.

Examples:
    uv run python scripts/coverage.py --overview
    uv run python scripts/coverage.py --company databricks --sort pending
    uv run python scripts/coverage.py --raw
    uv run python scripts/coverage.py --json
"""

from __future__ import annotations

import argparse
import json

from scraper.config import load_config
from scraper.coverage import CompanyCoverage, compute

_SORT_KEYS = {
    "pending": lambda c: -c.pending,
    "total": lambda c: -c.total,
    "scraped": lambda c: -c.scraped,
}


def _print_company(cov: CompanyCoverage, *, by_category: bool, sort: str) -> None:
    print(
        f"\n{cov.company}   scraped {cov.scraped}/{cov.total} ({cov.pct:.1f}%)   "
        f"errored {cov.errored}   pending {cov.pending}"
    )
    if not by_category:
        return
    print(f"  {'category':<28} {'total':>6} {'scraped':>7} {'errored':>7} {'pending':>7}   prefix")
    for c in sorted(cov.categories, key=_SORT_KEYS[sort]):
        print(
            f"  {c.category:<28} {c.total:>6} {c.scraped:>7} {c.errored:>7} {c.pending:>7}   {c.prefix}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape coverage + sitemap category breakdown.")
    parser.add_argument("--config", default="config/sources.yaml")
    parser.add_argument("--company", help="focus one company")
    parser.add_argument("--overview", action="store_true", help="per-company totals only")
    parser.add_argument("--sort", choices=list(_SORT_KEYS), default="pending")
    parser.add_argument("--raw", action="store_true", help="ignore include/exclude filters")
    parser.add_argument("--depth", type=int, default=1, help="category segment depth")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    args = parser.parse_args()

    cfg = load_config(args.config)
    companies = [args.company] if args.company else None
    coverage = compute(
        cfg, companies=companies, use_filters=not args.raw, depth=args.depth
    )

    if args.json:
        print(json.dumps([c.to_dict() for c in coverage], indent=2))
        return

    for cov in coverage:
        _print_company(cov, by_category=not args.overview, sort=args.sort)


if __name__ == "__main__":
    main()
