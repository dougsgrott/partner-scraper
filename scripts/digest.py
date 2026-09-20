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
    uv run python scripts/digest.py audit 6 7 --n 10         # sample findings + evidence

Grading a run is one emit -> edit -> import cycle (see `changefeed.digest.verdicts`):
    uv run python scripts/digest.py grade 6 7                # emit the worksheet
    $EDITOR reports/changefeed/verdicts-0006..0007.yaml      # fill verdict + method
    uv run python scripts/digest.py grade --import reports/changefeed/verdicts-0006..0007.yaml
    uv run python scripts/digest.py accuracy                 # rates by prompt version
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

    run = compress_run(result, blob_dir=args.blob_dir,
                       boost_restrictions=args.boost_restrictions,
                       collapse_terse=args.collapse_terse,
                       merge_duplicates=args.merge_duplicates,
                       mark_revisions=args.mark_revisions,
                       adaptive_slots=args.adaptive_slots)
    text = run.render()

    print(f"compressed {before.name} -> {after.name}")
    print(f"  changes          {len(run.records)}")
    print(f"  size             {run.chars:,} chars  (~{run.approx_tokens // 1000}k tokens, approx)")
    print(f"  mean record      {run.chars // max(len(run.records), 1)} chars")
    if run.approx_tokens > 500_000:
        print("  ! over half a context window — see docs/changefeed-phase-2.md, "
              "'What would change this decision'")

    if args.count_tokens:
        # The free count-tokens endpoint, so the estimate above stops being the only
        # number. Needs the `anthropic` SDK (the `enrich` extra) and credentials —
        # an API key or an `ant auth login` profile; degrades to a hint without them.
        try:
            import anthropic

            from changefeed.digest.session import MODEL
            n = anthropic.Anthropic().messages.count_tokens(
                model=MODEL, messages=[{"role": "user", "content": text}])
            drift = (run.approx_tokens - n.input_tokens) / n.input_tokens
            print(f"  actual tokens    {n.input_tokens:,}  "
                  f"(estimate off by {drift:+.0%})")
        except ModuleNotFoundError:
            print("  actual tokens    unavailable — install the anthropic SDK "
                  "(uv sync --extra enrich)", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001 — credentials/network; the hint matters
            print(f"  actual tokens    unavailable — {type(exc).__name__}: needs "
                  f"ANTHROPIC_API_KEY or an `ant auth login` profile", file=sys.stderr)
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
            max_budget_usd=None if args.no_budget else args.max_budget,
            boost_restrictions=args.boost_restrictions,
            quote_evidence=args.quote_evidence,
            inject_restrictions=args.inject_restrictions,
            collapse_terse=args.collapse_terse,
            merge_duplicates=args.merge_duplicates,
            mark_revisions=args.mark_revisions,
            adaptive_slots=args.adaptive_slots))
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

    from changefeed.digest import verdicts

    by_url = {c.url: c for c in result.changes}
    drawn = audit.draw(stored, args.n, args.seed)
    audits = [audit.audit_finding(f, by_url, blob_dir=args.blob_dir,
                                  pages=args.pages, lines=args.lines) for f in drawn]

    version = stored[0].prompt_version or "?"
    print(f"# Finding audit — {before.name} -> {after.name}  (prompt v{version})")
    print(f"\n{len(drawn)} of {len(stored)} findings, seed {args.seed}. For each: the claim, "
          f"then the changed lines that best match it. Mark each TRUE, PARTLY, or FALSE.")
    # The sampling record. The draw gives every impact at least one slot, so rare
    # impacts are oversampled; a grade set without these weights cannot be extrapolated.
    strata = verdicts.stratum_weights(stored, drawn)
    print("strata: " + "  ".join(
        f"{impact} {s['drawn']}/{s['population']} (weight {s['weight']})"
        for impact, s in strata.items()))
    flagged = sum(1 for a in audits
                  if a.already_present or a.misquoted_before or a.misquoted_after)
    if flagged:
        print(f"\n! {flagged} finding(s) claim something about the old or new text that "
              f"the stored text does not support — check those first.")
    for i, a in enumerate(audits, 1):
        print(audit.render(a, i))
    # The audit can only check findings that exist. The absence scan is the other half.
    print(f"\nFor restrictions no finding reports at all, run: "
          f"uv run python scripts/digest.py absence {before.id} {after.id}")
    return 0


def cmd_absence(args) -> int:
    """Restrictions the digest may have missed. See `changefeed.digest.absence`.

    No model and no cost. Scans the pair's added lines for restriction language naming
    things that were already on the page, and lists the candidates — pages no finding
    cites first. This is the only check that can surface a finding that was never
    written; everything in `audit` starts from one that was.
    """
    from changefeed.digest import absence

    with ChangeDB(args.changes_db) if args.changes_db else ChangeDB() as db:
        pair = _pair(db, args)
        if pair is None:
            return 1
        before, after = pair
        result = diff.compare(before, after, db=db, blob_dir=args.blob_dir)
        stored = findings.for_pair(db, before.id, after.id)

    candidates = absence.scan(result, blob_dir=args.blob_dir)
    if stored:
        absence.mark_cited(candidates, stored)
    print(absence.render(candidates, before=before.name, after=after.name,
                         limit=args.limit))
    return 0


def cmd_grade(args) -> int:
    """Emit a verdict worksheet for a pair, or import a filled one.

    The emit draws the same seeded sample as `audit` (same `--n`, same `--seed`), so the
    worksheet lists exactly the findings whose evidence the audit printed. The import is
    all-or-nothing: any invalid entry fails the file with every problem listed.
    """
    from datetime import UTC, datetime

    from changefeed.digest import audit, verdicts

    with ChangeDB(args.changes_db) if args.changes_db else ChangeDB() as db:
        if getattr(args, "import_file", None):
            try:
                rows = verdicts.parse(args.import_file, db)
            except verdicts.WorksheetError as err:
                print(err, file=sys.stderr)
                return 1
            verdicts.store(db, rows)
            methods = {v.method for v in rows}
            print(f"stored {len(rows)} verdict(s) from {args.import_file} "
                  f"({', '.join(sorted(methods))})")
            return 0

        pair = _pair(db, args)
        if pair is None:
            return 1
        before, after = pair
        stored = findings.for_pair(db, before.id, after.id)
        if not stored:
            print("no findings for this pair", file=sys.stderr)
            return 1
        drawn = audit.draw(stored, args.n, args.seed)
        text = verdicts.worksheet(
            (before.id, after.id), stored, drawn, seed=args.seed, requested=args.n,
            graded_at=datetime.now(UTC).date().isoformat())
        out = Path(args.out or
                   f"reports/changefeed/verdicts-{before.id:04d}..{after.id:04d}.yaml")
        if out.exists() and not args.force:
            print(f"{out} already exists — it may hold grades not yet imported. "
                  f"Use --out for a new file or --force to overwrite.", file=sys.stderr)
            return 1
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"worksheet for {len(drawn)} of {len(stored)} findings: {out}")
        print("fill `verdict` and `method`, then: "
              f"uv run python scripts/digest.py grade --import {out}")
        return 0


def cmd_accuracy(args) -> int:
    """Accuracy by prompt version, from the verdict ledger. No model, no cost.

    One row per (pair, prompt version, selection, method) — never merged across method
    or selection, because an excerpt grade and a full-page grade are different
    measurements, and a targeted set (findings picked because something looked wrong)
    is not a rate at all.
    """
    from changefeed.digest import verdicts

    with ChangeDB(args.changes_db) if args.changes_db else ChangeDB() as db:
        rows = verdicts.accuracy(db, method=args.method)
    if not rows:
        print("no verdicts stored" + (f" for method {args.method}" if args.method else "")
              + "; run `digest.py grade` first", file=sys.stderr)
        return 1
    print(f"{'pair':>8}  {'prompt':>6}  {'selection':>9}  {'method':>9}  "
          f"{'true':>4} {'partly':>6} {'false':>5} {'unver':>5}   rate  weighted")
    for r in rows:
        rate = f"{r['rate']:.0%}" if r["rate"] is not None else "—"
        weighted = f"{r['weighted']:.0%}" if r["weighted"] is not None else "—"
        note = "  (targeted — not a rate)" if r["selection"] == "targeted" else ""
        print(f"  #{r['before']}->#{r['after']}  {('v' + (r['prompt_version'] or '?')):>6}  "
              f"{(r['selection'] or '?'):>9}  {r['method']:>9}  "
              f"{r['true']:>4} {r['partly']:>6} {r['false']:>5} {r['unverified']:>5}   "
              f"{rate:>4}  {weighted:>8}{note}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a digest from a run of changes.")
    sub = ap.add_subparsers(dest="command", required=True)

    boost_help = ("restriction-first, clause-windowed excerpts — THE DEFAULT since "
                  "prompt v3 (issue/accuracy/13, two graded confirms); "
                  "--no-boost-restrictions disables it and findings record '3-r'")
    collapse_help = ("A/B arm (issue 06): group moved/metadata pages one line per "
                     "kind+category (saved ~55%% of the event-pair prompt); "
                     "list_changes enumerates them; findings record '+c'")
    merge_help = ("A/B arm (issue 06): pages with byte-identical changed lines render "
                  "as one record naming the group; findings record '+m'")
    mark_help = ("A/B arm (issue 07): tag shown lines that are close revisions of the "
                 "other side with '~' in excerpts and unaligned diffs; findings "
                 "record '+p'")
    slots_help = ("A/B arm (issue 07 E): pages with 3+ restriction lines get up to 4 "
                  "excerpt slots; findings record '+e'")

    p = sub.add_parser("compress", help="deterministic stage: size what a session would read")
    p.add_argument("before", nargs="?")
    p.add_argument("after", nargs="?")
    p.add_argument("--changes-db")
    p.add_argument("--blob-dir")
    p.add_argument("--out", help="write the full compressed run to a file")
    p.add_argument("--head", type=int, help="print the first N lines")
    p.add_argument("--boost-restrictions", action=argparse.BooleanOptionalAction,
                   default=True, help=boost_help)
    p.add_argument("--collapse-terse", action="store_true", help=collapse_help)
    p.add_argument("--merge-duplicates", action="store_true", help=merge_help)
    p.add_argument("--mark-revisions", action="store_true", help=mark_help)
    p.add_argument("--adaptive-slots", action="store_true", help=slots_help)
    p.add_argument("--count-tokens", action="store_true",
                   help="also count the session prompt for real via the free count-tokens "
                        "endpoint (needs the anthropic SDK and credentials)")
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
    p.add_argument("--boost-restrictions", action=argparse.BooleanOptionalAction,
                   default=True, help=boost_help)
    p.add_argument("--quote-evidence", action="store_true",
                   help="A/B arm (issue 04): prompt rule to quote the exact old text; "
                        "findings record prompt_version '+q'")
    p.add_argument("--inject-restrictions", action="store_true",
                   help="A/B arm (issue 05): append the absence scan's candidates to "
                        "the prompt; findings record prompt_version '+inj'")
    p.add_argument("--collapse-terse", action="store_true", help=collapse_help)
    p.add_argument("--merge-duplicates", action="store_true", help=merge_help)
    p.add_argument("--mark-revisions", action="store_true", help=mark_help)
    p.add_argument("--adaptive-slots", action="store_true", help=slots_help)
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

    p = sub.add_parser("absence", help="restrictions the digest may have missed entirely")
    p.add_argument("before", nargs="?")
    p.add_argument("after", nargs="?")
    p.add_argument("--limit", type=int, default=200, help="candidates to show")
    p.add_argument("--changes-db")
    p.add_argument("--blob-dir")
    p.set_defaults(func=cmd_absence)

    p = sub.add_parser("grade", help="emit a verdict worksheet, or --import a filled one")
    p.add_argument("before", nargs="?")
    p.add_argument("after", nargs="?")
    p.add_argument("--n", type=int, default=10, help="findings to draw (match the audit)")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--out", help="where to write the worksheet")
    p.add_argument("--force", action="store_true", help="overwrite an existing worksheet")
    p.add_argument("--import", dest="import_file", metavar="FILE",
                   help="validate FILE and store its verdicts; nothing else happens")
    p.add_argument("--changes-db")
    p.set_defaults(func=cmd_grade)

    p = sub.add_parser("accuracy", help="grade counts by prompt version, from the ledger")
    p.add_argument("--method", choices=("excerpt", "full-page"),
                   help="only grades made this way (full-page is the trustworthy one)")
    p.add_argument("--changes-db")
    p.set_defaults(func=cmd_accuracy)

    args = ap.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
