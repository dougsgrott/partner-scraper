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

from changefeed import diff
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
    """Check that findings are TRUE, not merely well-formed. See `changefeed.digest.audit`.

    No model and no cost. Prints each sampled finding beside the changed lines that best
    match its claim, and flags the claim most often wrong: calling something new that was
    already in the old text.
    """
    from changefeed.digest import audit

    with ChangeDB(args.changes_db) if args.changes_db else ChangeDB() as db:
        pair = _pair(db, args)
        if pair is None:
            return 1
        before, after = pair
        stored = findings.for_pair(db, before.id, after.id)
        if not stored:
            print("no findings for this pair", file=sys.stderr)
            return 1
        result = diff.compare(before, after, db=db, blob_dir=args.blob_dir)

    by_url = {c.url: c for c in result.changes}
    drawn = audit.draw(stored, args.n, args.seed)
    audits = [audit.audit_finding(f, by_url, blob_dir=args.blob_dir,
                                  pages=args.pages, lines=args.lines) for f in drawn]

    version = stored[0].prompt_version or "?"
    print(f"# Finding audit — {before.name} -> {after.name}  (prompt v{version})")
    print(f"\n{len(drawn)} of {len(stored)} findings, seed {args.seed}. For each: the claim, "
          f"then the changed lines that best match it. Mark each TRUE, PARTLY, or FALSE.")
    flagged = sum(1 for a in audits if a.already_present)
    if flagged:
        print(f"\n! {flagged} finding(s) claim something is new that already existed before "
              f"— check those first.")
    for i, a in enumerate(audits, 1):
        print(audit.render(a, i))
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
