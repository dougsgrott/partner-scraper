"""Entry point for the review tool — the local grading and labeling UI.

See docs/review-tool-plan.md. The tool is a thin skin over the existing modules
(`verdicts`, `audit`, `diff`, `blobs`, `classify`, `absence`): it renders their
evidence and writes through their validated paths, and owns no semantics of its own.

Examples:
    uv run python scripts/review.py serve                    # http://127.0.0.1:8765
    uv run python scripts/review.py serve --port 9000
    uv run python scripts/review.py serve --changes-db state/changes.db

Needs the `review` extra (FastAPI + uvicorn); the core pipeline stays free of both:
    uv sync --extra review
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# This script shares its name with the `review` package it launches, and Python puts the
# script's own directory first on sys.path — where `import review` finds this file
# instead of the package (the shadowing trap `scripts/changes.py` documents; `digest.py`
# dodged it by renaming, but the tool's command is `review.py serve` by design). Drop
# that entry: everything imported below is installed, nothing lives beside this script.
if sys.path and Path(sys.path[0]).resolve() == Path(__file__).resolve().parent:
    del sys.path[0]


def cmd_serve(args) -> int:
    try:
        import uvicorn

        from review.app import create_app
    except ModuleNotFoundError as err:
        print(f"missing dependency ({err.name}) — the review UI is an optional extra:\n"
              f"    uv sync --extra review", file=sys.stderr)
        return 1

    app = create_app(changes_db=args.changes_db, blob_dir=args.blob_dir)
    print(f"review tool: http://{args.host}:{args.port}/  (Ctrl-C stops it)")
    # Localhost by default, and no auth — binding wider than loopback is opting out of
    # the v1 threat model, which is why it takes an explicit --host.
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Local review UI: grade findings, label lines, watch accuracy.")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("serve", help="launch the web UI (uvicorn, localhost)")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--changes-db", help="default state/changes.db")
    p.add_argument("--blob-dir", help="default state/changes/blobs")
    p.set_defaults(func=cmd_serve)

    args = ap.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
