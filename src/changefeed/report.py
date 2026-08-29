"""Render a diff as Markdown, and as JSON for whatever reads it next.

Rendering is separated from computing so a report can be regenerated — with different
truncation, or a different audience — without recomputing the diff or, later, without
re-running a model over it. The JSON form is the same data with nothing dropped; it is
what phase 2's triage layer will consume.

Two rules the layout follows:

* **The vendor's changes and our own are never mixed.** `pipeline` churn gets its own
  section, captioned as ours. A reader who skims must not come away believing we watched
  Anthropic rewrite 566 pages on a day when all that happened was an extractor release.
* **Suppressed changes are listed, not hidden.** `low` and `noise` entries appear by URL
  with their counts. The reader can always see the size of what was ranked down, which is
  the only defence against a heuristic that is quietly wrong.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from . import classify
from .diff import KINDS, DiffResult, PageChange, render_diff

DEFAULT_REPORT_DIR = Path("reports/changefeed")


def _plural(n: int, word: str, suffix: str = "s") -> str:
    """`1 change` / `2 changes` — reports get shared, and "1 changes" reads as a bug."""
    return f"{n} {word}" if n == 1 else f"{n} {word}{suffix}"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    """A GitHub-flavoured table as one string, with no trailing newline.

    The trailing newline matters: joining a header block that already ends in "\\n" with
    rows joined by "\\n" puts a blank line after the separator, which ends the table and
    renders the body as paragraph text. That is exactly how `validation-scorecard.md`
    broke, so the invariant has a test.
    """
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
        *("| " + " | ".join(row) + " |" for row in rows),
    ]
    return "\n".join(lines)


def _summary_table(result: DiffResult) -> str:
    companies = sorted({c.company for c in result.changes})
    headers = ["kind", *companies, "total"]
    rows = []
    for kind in KINDS:
        changes = result.by_kind(kind)
        if not changes:
            continue
        per = Counter(c.company for c in changes)
        rows.append([kind, *(str(per.get(co, 0)) for co in companies), str(len(changes))])
    if not rows:
        return "_No differences between these snapshots._"
    return _table(headers, rows)


def _attribution_table(result: DiffResult) -> str:
    modified = result.by_kind("modified")
    if not modified:
        return ""
    per = Counter(c.cause for c in modified)
    rows = [
        [cause, str(per.get(cause, 0)), _CAUSE_BLURB[cause]]
        for cause in classify.CAUSES if per.get(cause)
    ]
    return _table(["cause", "pages", "meaning"], rows)


_CAUSE_BLURB = {
    classify.CONTENT: "the vendor changed the page",
    classify.PIPELINE: "**we** changed the extractor — not a vendor change",
    classify.UNKNOWN: "no fingerprint on one side; cause not established",
}


def _entry(change: PageChange, *, blob_dir: Path | None, context: int) -> str:
    url = (change.after or change.before or {}).get("url") or change.url
    delta = f"{change.delta_chars:+,} chars" if change.delta_chars else "same length"
    lines = [f"#### {change.title}", "", f"`{change.kind}` · {delta} · <{url}>"]

    if change.kind == "modified":
        body = render_diff(change, blob_dir=blob_dir, context=context)
        if body:
            lines += ["", "```diff", body, "```"]
        else:
            lines += ["", "_Stored body unavailable; diff could not be rendered._"]
    elif change.kind == "moved":
        lines += ["", (f"Moved from `{(change.before or {}).get('file_path')}` "
                       f"to `{(change.after or {}).get('file_path')}`.")]
    elif change.kind == "metadata":
        before, after = change.before or {}, change.after or {}
        moved = [f"- `{f}`: {before.get(f)!r} → {after.get(f)!r}"
                 for f in ("title", "description", "updated_date", "category")
                 if before.get(f) != after.get(f)]
        lines += ["", *moved]
    return "\n".join(lines)


def render(
    result: DiffResult,
    *,
    blob_dir: str | Path | None = None,
    context: int = 3,
    expand: int | None = None,
) -> str:
    """The full Markdown report. `expand` caps how many diffs are shown in full."""
    blob_dir = Path(blob_dir) if blob_dir else None
    feed = result.feed()
    shown = feed if expand is None else feed[:expand]

    out = [
        "# Documentation change feed",
        "",
        (f"> {result.before.name} · {result.before.taken_at} · "
         f"{result.before.page_count:,} pages"),
        (f"> {result.after.name} · {result.after.taken_at} · "
         f"{result.after.page_count:,} pages"),
        f"> Rendered {datetime.now(UTC).isoformat(timespec='seconds')}",
        "",
    ]

    if result.is_empty:
        out += ["Nothing changed between these two snapshots.", ""]
        return "\n".join(out)

    out += ["## Summary", "", _summary_table(result), ""]

    attribution = _attribution_table(result)
    if attribution:
        out += ["## Attribution", "", attribution, ""]

    pipeline = result.by_cause(classify.PIPELINE)
    unknown = result.by_cause(classify.UNKNOWN)
    if pipeline or unknown:
        out += [
            ("> **Read the attribution before the feed.** Pages attributed to `pipeline` "
             "moved because our extractor changed, not because the vendor edited anything. "
             "They are listed at the end of this report and excluded from the feed below."),
            "",
        ]

    out += [f"## Feed — {_plural(len(feed), 'substantive vendor change')}", ""]
    if not feed:
        out += ["_No substantive vendor changes in this window._", ""]

    grouped: dict[tuple[str, str], list[PageChange]] = defaultdict(list)
    for change in shown:
        grouped[(change.company, change.category)].append(change)

    for (company, category), changes in grouped.items():
        out += [f"### {company} · {category}", ""]
        for change in changes:
            out += [_entry(change, blob_dir=blob_dir, context=context), ""]

    if expand is not None and len(feed) > expand:
        out += [(f"_{len(feed) - expand} further substantive changes not expanded; "
                 f"see the JSON report for the full set._"), ""]

    suppressed = result.suppressed()
    if suppressed:
        per = Counter(c.weight for c in suppressed)
        out += [
            f"## Ranked down — {_plural(len(suppressed), 'change')}",
            "",
            (f"Real vendor changes ranked `low` ({per.get(classify.LOW, 0)}) or "
             f"`noise` ({per.get(classify.NOISE, 0)}). Listed rather than dropped: the "
             "ranking is a heuristic, and a feed that hides what it discarded cannot be "
             "audited."),
            "",
            *(f"- `{c.weight}` [{c.title}]({c.url})" for c in suppressed),
            "",
        ]

    if pipeline:
        out += [
            f"## Our own churn — {_plural(len(pipeline), 'page')}",
            "",
            ("These pages differ because the extractor that produced them changed "
             "(`output_fingerprint` moved). **The vendor did not edit them.**"),
            "",
            *(f"- [{c.title}]({c.url})" for c in pipeline[:50]),
            "",
        ]
        if len(pipeline) > 50:
            out += [f"_...and {len(pipeline) - 50} more._", ""]

    if unknown:
        out += [
            f"## Unattributed — {_plural(len(unknown), 'page')}",
            "",
            ("The content hash moved but no `output_fingerprint` was recorded on one side, "
             "usually because the index was rebuilt from `data/` (the fingerprint is not "
             "stated in the frontmatter). Cause not established either way."),
            "",
            *(f"- [{c.title}]({c.url})" for c in unknown[:50]),
            "",
        ]

    if result.unreadable:
        out += [
            f"## Unreadable bodies — {len(result.unreadable)}",
            "",
            ("Stored bodies these pages need are missing from the version store, so their "
             "changes were ranked `substantive` without inspection."),
            "",
            *(f"- {url}" for url in result.unreadable[:20]),
            "",
        ]

    return "\n".join(out)


def to_json(result: DiffResult) -> dict:
    """The whole diff as data, with nothing ranked away. Phase 2's input."""
    return {
        "before": {"id": result.before.id, "label": result.before.label,
                   "taken_at": result.before.taken_at, "pages": result.before.page_count},
        "after": {"id": result.after.id, "label": result.after.label,
                  "taken_at": result.after.taken_at, "pages": result.after.page_count},
        "counts": result.counts(),
        "causes": dict(Counter(c.cause for c in result.by_kind("modified"))),
        "weights": dict(Counter(c.weight for c in result.changes)),
        "unreadable": result.unreadable,
        "changes": [
            {
                "url": c.url,
                "kind": c.kind,
                "cause": c.cause,
                "weight": c.weight,
                "company": c.company,
                "category": c.category,
                "title": c.title,
                "delta_chars": c.delta_chars,
                "before": c.before,
                "after": c.after,
            }
            for c in result.changes
        ],
    }


def write(
    result: DiffResult,
    *,
    report_dir: str | Path | None = None,
    blob_dir: str | Path | None = None,
    expand: int | None = None,
) -> tuple[Path, Path]:
    """Write the Markdown and JSON reports. Returns both paths."""
    base = Path(report_dir or DEFAULT_REPORT_DIR)
    base.mkdir(parents=True, exist_ok=True)
    stem = f"{result.before.id:04d}..{result.after.id:04d}"

    md_path = base / f"{stem}.md"
    md_path.write_text(render(result, blob_dir=blob_dir, expand=expand), encoding="utf-8")

    json_path = base / f"{stem}.json"
    json_path.write_text(json.dumps(to_json(result), indent=2), encoding="utf-8")
    return md_path, json_path


def summarise(result: DiffResult) -> str:
    """A few lines for the terminal — what a run prints when it finishes."""
    counts = result.counts()
    feed = result.feed()
    pipeline = result.by_cause(classify.PIPELINE)
    # `+` binds tighter than `or`, so building this inline made the fallback unreachable
    # and printed a blank line for an empty diff. Named, so the intent is checkable.
    tally = "  ".join(f"{k} {v}" for k, v in counts.items() if v)
    lines = [
        f"diff {result.before.name} -> {result.after.name}",
        f"  {tally}" if tally else "  no differences",
        f"  feed             {_plural(len(feed), 'substantive vendor change')}",
        f"  ranked down      {len(result.suppressed())}",
    ]
    if pipeline:
        lines.append(f"  our own churn    {len(pipeline)} (extractor changed, not the vendor)")
    if result.by_cause(classify.UNKNOWN):
        lines.append(f"  unattributed     {len(result.by_cause(classify.UNKNOWN))}")
    if result.unreadable:
        lines.append(f"  unreadable       {len(result.unreadable)}")
    return "\n".join(lines)
