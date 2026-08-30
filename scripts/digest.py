"""Entry point for the change digest — phase 2. See docs/changefeed-phase-2.md.

`compress` is deterministic and free: no model, no API key, no network. It is worth running
on its own before a digest, to see exactly what a session would be given and how large it is.

Named `digest.py` rather than a name matching the package, for the reason `changes.py`
documents: a script whose name matches an installed package shadows it on `sys.path`.

Examples:
    uv run python scripts/digest.py compress                 # size the latest run
    uv run python scripts/digest.py compress --out run.txt   # what a session would read
    uv run python scripts/digest.py compress 1 2 --head 20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from changefeed import diff
from changefeed.db import ChangeDB
from changefeed.digest import compress_run


def cmd_compress(args) -> int:
    with ChangeDB(args.changes_db) if args.changes_db else ChangeDB() as db:
        if args.before and args.after:
            before, after = db.resolve(args.before), db.resolve(args.after)
            if before is None or after is None:
                print("no such snapshot", file=sys.stderr)
                return 1
        else:
            pair = db.last_two()
            if pair is None:
                print("need at least two snapshots", file=sys.stderr)
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

    args = ap.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
