"""Entry point for the change digest — phase 2. See docs/changefeed-phase-2.md.

`compress` is deterministic and free: no model, no API key, no network. It is worth running
on its own before a digest, to see exactly what a session would be given and how large it is.

Named `digest.py` rather than a name matching the package, for the reason `changes.py`
documents: a script whose name matches an installed package shadows it on `sys.path`.

Examples:
    uv run python scripts/digest.py compress                 # size the latest run, free
    uv run python scripts/digest.py compress --out run.txt   # what a session would read
    uv run python scripts/digest.py run 1 2                  # one session, spends money
    uv run python scripts/digest.py render 1 2               # re-render, no model
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from changefeed import blobs, diff
from changefeed.db import ChangeDB
from changefeed.digest import compress_run, findings

# Roughly twice a measured complete run ($4.06). A cap is the default because the first
# session ever run reached $5 in six minutes before batching existed, and an uncapped
# session bills a personal subscription with nothing to stop it.
DEFAULT_BUDGET_USD = 8.0


def _pair(db, args):
    if args.before and args.after:
        before, after = db.resolve(args.before), db.resolve(args.after)
        if before is None or after is None:
            print("no such snapshot", file=sys.stderr)
            return None
        return before, after
    pair = db.last_two()
    if pair is None:
        print("need at least two snapshots", file=sys.stderr)
    return pair


def cmd_compress(args) -> int:
    with ChangeDB(args.changes_db) if args.changes_db else ChangeDB() as db:
        pair = _pair(db, args)
        if pair is None:
            return 1
        before, after = pair
        result = diff.compare(before, after, db=db, blob_dir=args.blob_dir)

    run = compress_run(result, blob_dir=args.blob_dir)
    text = run.render()

    print(f"compressed {before.name} -> {after.name}")
    print(f"  changes          {len(run.records)}")
    print(f"  size             {run.chars:,} chars  (~{run.approx_tokens // 1000}k tokens, approx)")
    print(f"  mean record      {run.chars // max(len(run.records), 1)} chars")
    if run.approx_tokens > 500_000:
        print("  ! over half a context window — see docs/changefeed-phase-2.md, "
              "'What would change this decision'")

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"  written          {args.out}")
    if args.head:
        print()
        print("\n".join(text.splitlines()[: args.head]))
    return 0


def cmd_run(args) -> int:
    """One digest session. This is the command that spends money."""
    import asyncio

    from changefeed.digest.session import run_digest

    with ChangeDB(args.changes_db) if args.changes_db else ChangeDB() as db:
        pair = _pair(db, args)
        if pair is None:
            return 1
        before, after = pair
        result = diff.compare(before, after, db=db, blob_dir=args.blob_dir)
        outcome = asyncio.run(run_digest(
            result, db=db, blob_dir=args.blob_dir, data_root=args.data_root,
            max_budget_usd=None if args.no_budget else args.max_budget))
        print(outcome.render())
        return _write(db, before, after, len(result.changes), args)


def cmd_render(args) -> int:
    """Re-render a stored digest. No model, no cost — that is why findings are stored."""
    with ChangeDB(args.changes_db) if args.changes_db else ChangeDB() as db:
        pair = _pair(db, args)
        if pair is None:
            return 1
        before, after = pair
        result = diff.compare(before, after, db=db, blob_dir=args.blob_dir)
        return _write(db, before, after, len(result.changes), args)


def _write(db, before, after, changes: int, args) -> int:
    stored = findings.for_pair(db, before.id, after.id)
    if not stored:
        print("no findings recorded for this pair; run `digest run` first", file=sys.stderr)
        return 1
    text = findings.render(stored, before=before.name, after=after.name, changes=changes)
    out = Path(args.out or f"reports/changefeed/digest-{before.id:04d}..{after.id:04d}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"  digest           {out}")
    return 0


def cmd_audit(args) -> int:
    """Check that findings are TRUE, not merely well-formed.

    URL validation proves a cited page changed; nothing proves the sentence about it is
    right. This draws a seeded sample of findings and prints each one beside the actual
    changed lines of the pages it cites, so a person can decide. No model, no cost.

    Seeded and stratified by impact, the same way `sample_review.py` draws corpus pages,
    so a re-draw with the same seed gives the same sample.
    """
    import random
    from collections import defaultdict

    from changefeed import classify
    from changefeed.digest.findings import IMPACTS

    with ChangeDB(args.changes_db) if args.changes_db else ChangeDB() as db:
        pair = _pair(db, args)
        if pair is None:
            return 1
        before, after = pair
        stored = findings.for_pair(db, before.id, after.id)
        if not stored:
            print("no findings for this pair", file=sys.stderr)
            return 1

        by_impact = defaultdict(list)
        for f in stored:
            by_impact[f.impact].append(f)
        rng = random.Random(args.seed)
        drawn = []
        for impact in IMPACTS:
            group = by_impact.get(impact, [])
            if not group:
                continue
            quota = max(1, round(args.n * len(group) / len(stored)))
            drawn.extend(rng.sample(group, min(quota, len(group))))
        drawn = drawn[: args.n]

        result = diff.compare(before, after, db=db, blob_dir=args.blob_dir)
        by_url = {c.url: c for c in result.changes}

        print(f"# Finding audit — {before.name} -> {after.name}")
        print(f"\n{len(drawn)} of {len(stored)} findings, seed {args.seed}. For each: the "
              f"claim, then the changed lines of the pages it cites. Mark each TRUE, "
              f"PARTLY, or FALSE.\n")
        for i, f in enumerate(drawn, 1):
            print(f"\n{'=' * 78}\n{i}. [{f.impact}] {f.headline}")
            if f.detail:
                print(f"\n   {' '.join(f.detail.split())[:400]}")
            print(f"\n   cites {len(f.urls)} page(s); showing up to {args.pages}:")
            for url in f.urls[: args.pages]:
                change = by_url.get(url)
                print(f"\n   --- {url.split('/en/')[-1]}")
                if change is None:
                    print("       (not in this diff)")
                    continue
                b = blobs.read_or_none((change.before or {}).get("content_hash"), args.blob_dir)
                a = blobs.read_or_none((change.after or {}).get("content_hash"), args.blob_dir)
                if change.kind in ("added", "removed"):
                    # No two sides to diff. Saying "unavailable" implied a fault where
                    # there is none — a new page simply has no before-body.
                    print(f"       ({change.kind} page — "
                          f"{(change.current.get('body_chars') or 0):,} chars)")
                    continue
                if b is None or a is None:
                    print("       (stored body unavailable)")
                    continue
                removed, added = classify.changed_sides(b, a)
                # Same ordering the compressed excerpt uses: status language first, then
                # longest, skipping blanks. Taking lines in multiset order showed empty
                # strings and `> **Note:**` boilerplate, which cannot confirm or refute
                # anything — the audit tool needed auditing before its output was usable.
                def informative(lines: list[str]) -> list[str]:
                    real = [ln for ln in lines if ln.strip()]
                    real.sort(key=lambda ln: (0 if classify.STATUS.search(ln) else 1, -len(ln)))
                    return real[: args.lines]

                for line in informative(removed):
                    print(f"       - {line.strip()[:170]}")
                for line in informative(added):
                    print(f"       + {line.strip()[:170]}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a digest from a run of changes.")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("compress", help="deterministic stage: size what a session would read")
    p.add_argument("before", nargs="?")
    p.add_argument("after", nargs="?")
    p.add_argument("--changes-db")
    p.add_argument("--blob-dir")
    p.add_argument("--out", help="write the full compressed run to a file")
    p.add_argument("--head", type=int, help="print the first N lines")
    p.set_defaults(func=cmd_compress)

    p = sub.add_parser("run", help="one digest session over a whole run (spends money)")
    p.add_argument("before", nargs="?")
    p.add_argument("after", nargs="?")
    p.add_argument("--changes-db")
    p.add_argument("--blob-dir")
    p.add_argument("--data-root")
    p.add_argument("--out", help="where to write the digest")
    p.add_argument("--max-budget", type=float, default=DEFAULT_BUDGET_USD,
                   help=f"stop the session past this USD spend (default {DEFAULT_BUDGET_USD})")
    p.add_argument("--no-budget", action="store_true",
                   help="run without a spend cap — say so explicitly")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("render", help="re-render stored findings — no model, no cost")
    p.add_argument("before", nargs="?")
    p.add_argument("after", nargs="?")
    p.add_argument("--changes-db")
    p.add_argument("--blob-dir")
    p.add_argument("--out")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("audit", help="check findings are true, not just well-formed")
    p.add_argument("before", nargs="?")
    p.add_argument("after", nargs="?")
    p.add_argument("--n", type=int, default=10, help="findings to draw")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--pages", type=int, default=3, help="cited pages to show per finding")
    p.add_argument("--lines", type=int, default=4, help="changed lines to show per page")
    p.add_argument("--changes-db")
    p.add_argument("--blob-dir")
    p.set_defaults(func=cmd_audit)

    args = ap.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
