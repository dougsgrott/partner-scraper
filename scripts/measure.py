"""Standing instruments — issue/accuracy/10. See `changefeed.measure`.

The analyses the accuracy work kept redoing as one-off scripts, runnable and versioned:

    uv run python scripts/measure.py raw-churn 20260829T181157 20260909T172623
    uv run python scripts/measure.py duplicates 7
    uv run python scripts/measure.py ranking-overlap 6 7 --graded
    uv run python scripts/measure.py cross-check 6 7 --generations 20260909T172623 20260918T184955

Outputs land in `reports/measure/` beside a printed copy. Each instrument was
validated by reproducing the figures in `docs/session-2026-09-18-lessons.md` and
`docs/raw-archive.md`; the validation numbers are recorded in
`issue/accuracy/10-standing-instruments.md`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from changefeed import measure
from changefeed.db import ChangeDB
from scraper.fetch import noise

ARCHIVE_DIR = Path("raw-archive")
REPORT_DIR = Path("reports/changefeed")


def _patterns(args) -> tuple:
    """The noise registry, minus any `--ignore-pattern` — the blind-replay switch."""
    ignored = set(getattr(args, "ignore_pattern", None) or [])
    unknown = ignored - {p.name for p in noise.PATTERNS}
    if unknown:
        print(f"no such noise pattern: {', '.join(sorted(unknown))} "
              f"(registry: {', '.join(p.name for p in noise.PATTERNS)})",
              file=sys.stderr)
        raise SystemExit(1)
    return tuple(p for p in noise.PATTERNS if p.name not in ignored)


def _modified(before: int, after: int) -> list[dict]:
    report = json.loads(_report_json(before, after).read_text(encoding="utf-8"))
    return [{"url": c["url"], "company": c["company"]}
            for c in report["changes"]
            if c["kind"] == "modified" and c["cause"] == "content"]


def _gen(ref: str) -> Path:
    """A generation label under raw-archive/, or an explicit path."""
    candidate = ARCHIVE_DIR / ref
    if candidate.is_dir():
        return candidate
    if Path(ref).is_dir():
        return Path(ref)
    print(f"no such generation: {ref} (looked in {ARCHIVE_DIR}/)", file=sys.stderr)
    raise SystemExit(1)


def _out(args, name: str, text: str) -> None:
    base = Path(args.out_dir)
    base.mkdir(parents=True, exist_ok=True)
    path = base / name
    path.write_text(text + "\n", encoding="utf-8")
    print(f"\n  written          {path}")


def _report_json(before: int, after: int) -> Path:
    path = REPORT_DIR / f"{before:04d}..{after:04d}.json"
    if not path.exists():
        print(f"no run report at {path} — run `changes.py diff {before} {after} --write` "
              f"first", file=sys.stderr)
        raise SystemExit(1)
    return path


def cmd_raw_churn(args) -> int:
    churn = measure.raw_churn(_gen(args.gen1), _gen(args.gen2), _patterns(args))
    text = churn.render()
    if churn.survivors:
        text += "\n\nsurvivors:\n" + "\n".join(f"  {s}" for s in churn.survivors)
    print(churn.render())
    _out(args, f"raw-churn-{churn.gen1}..{churn.gen2}.md", text)
    return 0


def cmd_duplicates(args) -> int:
    with ChangeDB(args.changes_db) if args.changes_db else ChangeDB() as db:
        dup = measure.duplicate_bodies(db, args.snapshot)
    print(dup.render())
    _out(args, f"duplicates-{args.snapshot:04d}.md", dup.render())
    return 0


def cmd_ranking_overlap(args) -> int:
    pair = (args.before, args.after)
    with ChangeDB(args.changes_db) if args.changes_db else ChangeDB() as db:
        overlap = measure.ranking_overlap(db, pair, _report_json(*pair),
                                          graded=args.graded)
    print(overlap.render())
    suffix = "-graded" if args.graded else ""
    _out(args, f"ranking-overlap-{pair[0]:04d}..{pair[1]:04d}{suffix}.md",
         overlap.render())
    return 0


def cmd_residue(args) -> int:
    """The tripped-canary investigation path: one command against the archive."""
    patterns = _patterns(args)
    g1, g2 = _gen(args.gen1), _gen(args.gen2)
    churn = measure.raw_churn(g1, g2, patterns)
    canary = measure.unknown_noise(churn, _modified(*args.pair))
    print(canary.render(g1.name, g2.name).lstrip("- "))
    if not canary.candidates:
        return 0

    clusters, sampled = measure.cluster_residue(g1, g2, canary.candidates, patterns)
    body = "\n".join([(f"residue clusters {g1.name} -> {g2.name} "
                       f"({sampled} files sampled of {len(canary.candidates)} candidates):"),
                      *[c.render(sampled) for c in clusters]])
    print(body)
    _out(args, f"residue-{g1.name}..{g2.name}.md",
         canary.render(g1.name, g2.name) + "\n\n" + body)
    return 0


def cmd_cross_check(args) -> int:
    pair = (args.before, args.after)
    report = json.loads(_report_json(*pair).read_text(encoding="utf-8"))
    counts = report["counts"]
    causes = report["causes"]
    modified = [{"url": c["url"], "company": c["company"]}
                for c in report["changes"]
                if c["kind"] == "modified" and c["cause"] == "content"]

    extract = None
    if args.extract:
        extract = json.loads(Path(args.extract).read_text(encoding="utf-8"))
    else:
        window = (report["before"]["taken_at"], report["after"]["taken_at"])
        for path in sorted(Path("state/extracts").glob("*.json"), reverse=True):
            data = json.loads(path.read_text(encoding="utf-8"))
            if window[0] <= data.get("started_at", "") <= window[1]:
                extract = data
                print(f"  extract summary  {path}")
                break

    churn = None
    if args.generations:
        churn = measure.raw_churn(_gen(args.generations[0]), _gen(args.generations[1]))

    rec = measure.reconcile(counts, causes, extract=extract, churn=churn,
                            modified=modified)
    print(rec.render())
    _out(args, f"cross-check-{pair[0]:04d}..{pair[1]:04d}.md", rec.render())
    return 0 if rec.ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="Standing measurement instruments.")
    ap.add_argument("--out-dir", default=str(measure.DEFAULT_MEASURE_DIR))
    ap.add_argument("--changes-db", help="history database (default state/changes.db)")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("raw-churn", help="byte churn between two generations, "
                                         "attributed to named noise patterns")
    p.add_argument("gen1")
    p.add_argument("gen2")
    p.add_argument("--ignore-pattern", action="append", metavar="NAME",
                   help="drop a noise pattern from the registry (replay an event "
                        "blind); repeatable")
    p.set_defaults(func=cmd_raw_churn)

    p = sub.add_parser("residue", help="cluster the byte changes of survivors whose "
                                       "content did not change — the tripped-canary "
                                       "investigation (issue/accuracy/11)")
    p.add_argument("gen1")
    p.add_argument("gen2")
    p.add_argument("--pair", nargs=2, type=int, required=True,
                   metavar=("BEFORE", "AFTER"),
                   help="the snapshot pair whose content modifications define what "
                        "was a real change")
    p.add_argument("--ignore-pattern", action="append", metavar="NAME",
                   help="drop a noise pattern from the registry (replay an event "
                        "blind); repeatable")
    p.set_defaults(func=cmd_residue)

    p = sub.add_parser("duplicates", help="duplicate-body groups within one snapshot")
    p.add_argument("snapshot", type=int)
    p.set_defaults(func=cmd_duplicates)

    p = sub.add_parser("ranking-overlap", help="where digest citations sit in the "
                                               "severity ranking")
    p.add_argument("before", type=int)
    p.add_argument("after", type=int)
    p.add_argument("--graded", action="store_true",
                   help="pool full-page-graded findings across arms instead of the "
                        "current finding set (the issue/accuracy/08 population)")
    p.set_defaults(func=cmd_ranking_overlap)

    p = sub.add_parser("cross-check", help="three-way reconciliation: feed = extract "
                                           "output churn ~ raw survivors")
    p.add_argument("before", type=int)
    p.add_argument("after", type=int)
    p.add_argument("--extract", help="an extract summary JSON (default: newest in "
                                     "state/extracts/ inside the window)")
    p.add_argument("--generations", nargs=2, metavar=("GEN1", "GEN2"),
                   help="also run raw churn and the per-page missed-real-change check")
    p.set_defaults(func=cmd_cross_check)

    args = ap.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
