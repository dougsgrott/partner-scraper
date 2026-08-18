"""CLI for inspecting the fetch work-list. Fetches sitemaps + robots.txt only — never a page.

Examples:
    uv run python scripts/worklist.py                       # every enabled source
    uv run python scripts/worklist.py --offline             # dumps only, no network
    uv run python scripts/worklist.py --source databricks-docs --sample 5
    uv run python scripts/worklist.py --json
    uv run python scripts/worklist.py --refresh-dumps        # re-dump the live sitemaps
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

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


def _refresh_dumps(cfg) -> None:
    """Merge the live sitemaps into every committed dump file.

    The dumps are what makes the work-list reproducible offline, so they only stay
    useful while they match the sites. Several sources can share one dump file (the
    Anthropic docs and cookbook do), so the sitemaps are pooled per file.

    This **adds and updates, never removes**. The committed Databricks dump holds 37,689
    URLs covering every locale and cloud, while the configured seed
    (`/aws/en/sitemap.xml`) advertises 5,835 — replacing rather than merging would throw
    away 31,877 URLs, including the whole `/api/**` tree the phase-2 source depends on.
    """
    from scraper.worklist import dumps, sitemap

    pooled: dict[Path, set[str]] = {}
    for source in cfg.sources.values():
        for path in source.dump_paths():
            pooled.setdefault(path, set()).update(source.sitemap_urls())

    for path, sitemap_urls in sorted(pooled.items()):
        existing = dumps.read(path) if path.exists() else []
        if not sitemap_urls:
            print(f"{path}: no sitemap seed to refresh from — left alone ({len(existing)} URLs)")
            continue

        merged = {du.url: du for du in existing}
        discovered = sitemap.collect(sorted(sitemap_urls), user_agent=cfg.defaults.user_agent)
        added = [du for du in discovered if du.url not in merged]
        for du in discovered:
            # A live entry wins only when it carries a date; a dateless one must not
            # erase the `lastmod` an older dump recorded.
            if du.lastmod or du.url not in merged:
                merged[du.url] = du

        after = dumps.write(path, list(merged.values()))
        print(f"{path}: {len(existing)} -> {after} URLs "
              f"(+{len(added)} new, {len(discovered)} advertised live)")
        for du in added[:5]:
            print(f"    + {du.url}")
        if len(added) > 5:
            print(f"    … {len(added) - 5} more")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build and inspect the fetch work-list.")
    ap.add_argument("--config", default="config/sources.yaml")
    ap.add_argument("--source", action="append", dest="sources", help="source id (repeatable)")
    ap.add_argument("--offline", action="store_true", help="dumps only; skip sitemaps + robots")
    ap.add_argument("--include-disabled", action="store_true")
    ap.add_argument("--sample", type=int, default=0, help="print N example URLs per source")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--refresh-dumps", action="store_true",
                    help="rewrite the committed dumps from the live sitemaps, then exit")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    cfg = load_config(args.config)

    if args.refresh_dumps:
        _refresh_dumps(cfg)
        return

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
