"""CLI for the corpus audit: is it complete, faithful, and self-consistent?

Read-only and offline by default — it never writes to `data/`, `raw/`, or the databases.
Exits non-zero if any check fails, so it can gate a release of the corpus.

Examples:
    uv run python scripts/validate.py                       # full offline audit
    uv run python scripts/validate.py --no-idempotency      # skip the re-extract pass
    uv run python scripts/validate.py --scope               # also reconcile against sitemaps
    uv run python scripts/validate.py --write-candidates out.txt   # link-gap work list
    uv run python scripts/validate.py --json                # machine-readable report
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from scraper.config import load_config
from scraper.validate import run_validation


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate the extracted corpus.")
    ap.add_argument("--config", default="config/sources.yaml")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--fetch-db", default="state/fetch.db")
    ap.add_argument("--index-db", default="state/index.db")
    ap.add_argument("--scope", action="store_true",
                    help="reconcile against the worklist (fetches sitemaps + robots.txt)")
    ap.add_argument("--offline", action="store_true",
                    help="with --scope, build the worklist from dumps only")
    ap.add_argument("--no-idempotency", action="store_true",
                    help="skip the repeat-extraction check (the slow one, ~2 min)")
    ap.add_argument("--write-candidates", metavar="PATH",
                    help="write link-gap candidates for a follow-up fetch")
    ap.add_argument("--report-dir", default="state/validation")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")
    cfg = load_config(args.config)

    worklists = None
    if args.scope:
        from scraper.worklist import build_all
        worklists = build_all(cfg, use_sitemaps=not args.offline)

    report, candidates = run_validation(
        cfg,
        data_dir=args.data_dir,
        fetch_db_path=args.fetch_db,
        index_db_path=args.index_db,
        worklists=worklists,
        idempotency=not args.no_idempotency,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.render())

    path = report.write(args.report_dir)
    if not args.json:
        print(f"\nreport: {path}")

    if args.write_candidates and candidates:
        out = Path(args.write_candidates)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(f"{'-' * 10}  {url}" for _, url in candidates) + "\n",
                       encoding="utf-8")
        if not args.json:
            print(f"link-gap candidates ({len(candidates)}): {out}")

    sys.exit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
