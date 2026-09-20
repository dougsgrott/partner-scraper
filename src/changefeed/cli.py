"""CLI for the change feed: what moved in the corpus, and who moved it.

See docs/changefeed-plan.md. Phase 1 is deterministic — no model, no tokens — and touches
the network only when `run` is given `--fetch`.

`run` is the single manual command standing in for the scheduled cadence that PLAN.md
defers. It is deliberately not wired to a scheduler, but it behaves like something that
could be: one command, one exit code, a JSON summary on disk.

The argument parsing lives here rather than in `scripts/` because a module named
`changefeed.py` sitting in `scripts/` shadows this package: Python puts the script's own
directory first on `sys.path`, so `import changefeed` finds the script and the import
fails. `scripts/changes.py` is a thin entry point onto `main` below.

Examples:
    uv run python scripts/changes.py snapshot --label baseline
    uv run python scripts/changes.py list
    uv run python scripts/changes.py run              # reuse raw/, no network
    uv run python scripts/changes.py run --fetch      # ~2h refresh at 1 req/s first
    uv run python scripts/changes.py diff baseline latest --json
    uv run python scripts/changes.py log https://docs.databricks.com/aws/en/delta/
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from scraper.config import load_config

from . import blobs, diff, report, snapshot
from .db import ChangeDB


def _add_store_args(parser: argparse.ArgumentParser) -> None:
    """Path overrides, so a run can read a corpus that lives somewhere else.

    Useful for operating on the main checkout's corpus from a worktree, and for tests.
    """
    parser.add_argument("--index-db", help="corpus manifest (default state/index.db)")
    parser.add_argument("--changes-db", help="history database (default state/changes.db)")
    parser.add_argument("--blob-dir", help="version store (default state/changes/blobs)")
    parser.add_argument("--report-dir", help="where reports are written")
    parser.add_argument("--data-root",
                        help="prefix for the relative file paths the index stores, when "
                             "the corpus lives outside the current directory")


def _db(args) -> ChangeDB:
    return ChangeDB(args.changes_db) if args.changes_db else ChangeDB()


def _resolve_pair(db: ChangeDB, args) -> tuple | None:
    """The two snapshots to compare: explicit refs, or the last two taken."""
    if args.before and args.after:
        before, after = db.resolve(args.before), db.resolve(args.after)
        if before is None:
            print(f"no such snapshot: {args.before}", file=sys.stderr)
            return None
        if after is None:
            print(f"no such snapshot: {args.after}", file=sys.stderr)
            return None
        return before, after

    pair = db.last_two()
    if pair is None:
        print("need at least two snapshots to diff; run `snapshot` first", file=sys.stderr)
        return None
    return pair


# -- commands --------------------------------------------------------------

def cmd_snapshot(args) -> int:
    result = snapshot.take(
        label=args.label,
        note=args.note,
        index_db=args.index_db,
        changes_db=args.changes_db,
        blob_dir=args.blob_dir,
        data_root=args.data_root,
    )
    print(result.render())
    return 0


def cmd_list(args) -> int:
    with _db(args) as db:
        snaps = db.snapshots()
        if not snaps:
            print("no snapshots yet")
            return 0
        blob_bytes = blobs.total_bytes(Path(args.blob_dir) if args.blob_dir else None)
        for snap in snaps:
            label = f"  {snap.label}" if snap.label else ""
            print(f"  #{snap.id:<4} {snap.taken_at}  {snap.page_count:>6} pages{label}")
        print(f"\n  {len(snaps)} snapshots · version store {blob_bytes / 1_048_576:.1f} MiB")
    return 0


def cmd_diff(args) -> int:
    with _db(args) as db:
        pair = _resolve_pair(db, args)
        if pair is None:
            return 1
        before, after = pair
        result = diff.compare(before, after, db=db, blob_dir=args.blob_dir)

        if args.json:
            print(json.dumps(report.to_json(result), indent=2))
            return 0

        print(report.summarise(result))
        if args.write:
            md, js = report.write(
                result, report_dir=args.report_dir, blob_dir=args.blob_dir,
                expand=args.expand)
            print(f"\n  report           {md}\n  json             {js}")
    return 0


def _fetch_and_archive(cfg, *, archive: bool = True) -> None:
    """Refresh through the fetch layer, then archive the generation it left in `raw/`.

    Archiving here matches `scripts/fetch.py` (issue/accuracy/09): this used to be the
    one fetch path that did not archive, and bytes never hard-linked into
    `raw-archive/` are gone the moment the next refresh overwrites `raw/`. The
    decision of *whether* a run gets archived is `generations.archive_after`, shared
    with `fetch.py`; only the printing differs.
    """
    from scraper.fetch import generations
    from scraper.fetch.runner import run_fetch

    print("\nfetching (conditional refresh, 1 req/s per host — this takes hours)\n")
    summary = run_fetch(cfg, mode="refresh")
    print(summary.render())

    if not archive:
        return
    generation = generations.archive_after(summary)
    if generation is None:
        print("\n  nothing fetched — no generation archived")
    else:
        print(f"\narchived generation {generation.label}")
        print(generation.render())


def cmd_run(args) -> int:
    """Snapshot, optionally refresh, extract, snapshot again, diff, report."""
    with _db(args) as db:
        existing = db.snapshots()
        before = existing[-1] if existing else None

    if before is None:
        print("no baseline snapshot yet — taking one first")
        baseline = snapshot.take(
            label="baseline", index_db=args.index_db, changes_db=args.changes_db,
            blob_dir=args.blob_dir, data_root=args.data_root)
        print(baseline.render())
        with _db(args) as db:
            before = db.snapshot(baseline.snapshot_id)

    cfg = load_config(args.config)

    if args.fetch:
        # The one command in this repo that puts sustained load on someone else's
        # servers. Rate limits live in config/sources.yaml; there is no flag here.
        _fetch_and_archive(cfg, archive=not args.no_archive)

    from scraper.extract import run_extract
    print("\nextracting\n")
    extract_summary = run_extract(cfg, prune=not args.no_prune)
    print(extract_summary.render())

    after_result = snapshot.take(
        label=args.label, index_db=args.index_db, changes_db=args.changes_db,
        blob_dir=args.blob_dir, data_root=args.data_root)
    print()
    print(after_result.render())

    with _db(args) as db:
        after = db.snapshot(after_result.snapshot_id)
        result = diff.compare(before, after, db=db, blob_dir=args.blob_dir)
        print()
        print(report.summarise(result))
        md, js = report.write(
            result, report_dir=args.report_dir, blob_dir=args.blob_dir, expand=args.expand)
        print(f"\n  report           {md}\n  json             {js}")

        # The cross-check invariant (issue/accuracy/10): the change feed and the
        # extract pass just measured the same window two ways, and a diff missing
        # pages or an extractor double-writing shows up here at the run that
        # introduces it, not at the next manual audit. The block lands in the report,
        # and a hard mismatch fails the run.
        from collections import Counter

        from . import measure
        causes = dict(Counter(c.cause for c in result.by_kind("modified")))

        # With a fresh generation just archived (issue/accuracy/09 guarantees one per
        # fetched run), the raw leg and its noise canary (issue/accuracy/11) come for
        # ~70s: churn the last two generations and hand the reconciliation the
        # window's real changes.
        churn = modified = None
        if args.fetch and not args.no_archive:
            from scraper.fetch import generations
            gens = generations.generations()
            if len(gens) >= 2:
                print("\ncomparing the two newest generations for the noise canary\n")
                churn = measure.raw_churn(gens[-2].path, gens[-1].path)
                modified = [{"url": c.url, "company": c.company}
                            for c in result.by_kind("modified")
                            if c.cause == "content"]

        rec = measure.reconcile(result.counts(), causes,
                                extract=extract_summary.to_dict(),
                                churn=churn, modified=modified)
        print()
        print(rec.render())
        with md.open("a", encoding="utf-8") as fh:
            fh.write("\n" + rec.render() + "\n")
    return 0 if rec.ok else 1


def cmd_log(args) -> int:
    with _db(args) as db:
        history = db.history(args.url)
        if not history:
            print(f"no recorded versions of {args.url}")
            return 1
        seen: str | None = None
        for row in history:
            marker = " " if row["content_hash"] == seen else "*"
            label = f"  ({row['label']})" if row["label"] else ""
            print(f"  {marker} #{row['snapshot_id']:<4} {row['taken_at']}  "
                  f"{row['content_hash'][:12]}  {row['body_chars']:>7} chars{label}")
            seen = row["content_hash"]
        print("\n  * marks a snapshot where the content differed from the one before it")
    return 0


def cmd_show(args) -> int:
    with _db(args) as db:
        history = db.history(args.url)
        if not history:
            print(f"no recorded versions of {args.url}", file=sys.stderr)
            return 1
        row = history[-1]
        if args.snapshot is not None:
            match = [r for r in history if r["snapshot_id"] == args.snapshot]
            if not match:
                print(f"{args.url} was not in snapshot #{args.snapshot}", file=sys.stderr)
                return 1
            row = match[0]
        body = blobs.read_or_none(
            row["content_hash"], Path(args.blob_dir) if args.blob_dir else None)
        if body is None:
            print("stored body is missing from the version store", file=sys.stderr)
            return 1
        print(body)
    return 0


def cmd_backup(args) -> int:
    """Copy the history somewhere else. The one thing here that cannot be rebuilt."""
    from . import db as db_module

    blob_dir = args.blob_dir or str(blobs.DEFAULT_BLOB_DIR)
    copied, new = db_module.backup(args.destination,
                                   db_path=args.changes_db or db_module.DEFAULT_DB_PATH,
                                   blob_dir=blob_dir)
    print(f"  backed up        {args.destination}")
    print(f"  copied           {copied / 1_048_576:.1f} MiB  ({new} new bodies)")
    return 0


def cmd_gc(args) -> int:
    with _db(args) as db:
        snaps = db.snapshots()
        if args.keep and len(snaps) > args.keep:
            for snap in snaps[: len(snaps) - args.keep]:
                print(f"  dropping snapshot #{snap.id} ({snap.taken_at})")
                db.delete_snapshot(snap.id)
        keep = db.referenced_hashes()

    removed, reclaimed = blobs.prune(keep, Path(args.blob_dir) if args.blob_dir else None)
    print(f"  removed {removed} unreferenced bodies, reclaimed "
          f"{reclaimed / 1_048_576:.1f} MiB")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Change intelligence over the corpus.")
    ap.add_argument("--config", default="config/sources.yaml")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("snapshot", help="record the corpus as it stands now")
    p.add_argument("--label", help="a name you will recognise later, e.g. baseline")
    p.add_argument("--note")
    _add_store_args(p)
    p.set_defaults(func=cmd_snapshot)

    p = sub.add_parser("list", help="snapshots taken so far")
    _add_store_args(p)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("diff", help="compare two snapshots")
    p.add_argument("before", nargs="?", help="id, label, or 'previous'")
    p.add_argument("after", nargs="?", help="id, label, or 'latest'")
    p.add_argument("--json", action="store_true", help="print the full diff as JSON")
    p.add_argument("--write", action="store_true", help="also write the report files")
    p.add_argument("--expand", type=int, default=100,
                   help="cap how many diffs are shown in full (default 100)")
    _add_store_args(p)
    p.set_defaults(func=cmd_diff)

    p = sub.add_parser("run", help="snapshot, [fetch], extract, snapshot, diff, report")
    p.add_argument("--fetch", action="store_true",
                   help="refresh the archive first (~2h at 1 req/s; off by default)")
    p.add_argument("--no-archive", action="store_true",
                   help="with --fetch: do not archive this run's bytes into raw-archive/ "
                        "(they become unrecoverable once the next fetch overwrites raw/)")
    p.add_argument("--label", help="label for the snapshot this run takes")
    p.add_argument("--no-prune", action="store_true",
                   help="keep corpus files the index no longer claims")
    p.add_argument("--expand", type=int, default=100)
    _add_store_args(p)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("log", help="version history of one page")
    p.add_argument("url")
    _add_store_args(p)
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("show", help="print a stored body from the version store")
    p.add_argument("url")
    p.add_argument("--snapshot", type=int, help="which snapshot (default: the newest)")
    _add_store_args(p)
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("backup", help="copy the history — it cannot be rebuilt")
    p.add_argument("destination")
    _add_store_args(p)
    p.set_defaults(func=cmd_backup)

    p = sub.add_parser("gc", help="drop old snapshots and unreferenced bodies")
    p.add_argument("--keep", type=int, help="keep only the N most recent snapshots")
    _add_store_args(p)
    p.set_defaults(func=cmd_gc)

    args = ap.parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    raise SystemExit(args.func(args))
