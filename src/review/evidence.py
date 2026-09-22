"""Evidence bundles: everything the UI shows for one finding or one line.

All reuse. The grading bundle is `audit.audit_finding` (ranked lines, the newness and
quote checks) plus `diff.render_diff` (the capped unified diff); the labeling context is
`classify.changed_sides` over the pair's blobs. This module arranges those outputs into
JSON-shaped dicts and adds nothing of its own — when the audit gains a check, the UI
shows it without a change here beyond passing it through.

What is deliberately absent: prior verdicts. Blind mode is the default, so the bundle
never carries them — the submit path reveals them (`queues.GradingQueue.submit`), which
makes "peeked before grading" structurally impossible rather than a discipline.
"""

from __future__ import annotations

from pathlib import Path

from changefeed import blobs, classify
from changefeed.db import ChangeDB
from changefeed.diff import MODIFIED, PageChange, render_diff
from changefeed.digest import audit
from changefeed.digest.findings import Finding

# Enough signed context to judge a line without drowning it. The absence read sample was
# judged from about this much surrounding change.
CONTEXT_LINES = 30


def _slug(url: str) -> str:
    return url.split("/en/")[-1] if "/en/" in url else url


def grading_bundle(finding: Finding, by_url: dict[str, PageChange], *,
                   blob_dir: Path | None = None, pages: int = 3,
                   lines: int = 6) -> dict:
    """One finding beside its evidence: the audit's ranked lines and mechanical flags,
    plus a capped unified diff per shown modified page. Machine evidence only."""
    a = audit.audit_finding(finding, by_url, blob_dir=blob_dir, pages=pages, lines=lines)
    evidence = []
    for ev in a.evidence:
        change = by_url.get(ev.url)
        diff_text = ""
        if change is not None and change.kind == MODIFIED:
            diff_text = render_diff(change, blob_dir=blob_dir, mark_revisions=True)
        evidence.append({
            "url": ev.url, "slug": _slug(ev.url), "kind": ev.kind, "note": ev.note,
            "score": ev.score, "lines": [[sign, text] for sign, text in ev.lines],
            "diff": diff_text,
        })
    return {
        "finding": {
            "id": finding.id, "impact": finding.impact, "kind": finding.kind,
            "summary": finding.headline, "detail": finding.detail,
            "urls": finding.urls, "model": finding.model,
            "prompt_version": finding.prompt_version,
        },
        "cited": len(finding.urls),
        "shown": a.shown_pages,
        "flags": {
            "already_present": a.already_present,
            "newness_unverifiable": a.newness_unverifiable,
            "misquoted_before": a.misquoted_before,
            "misquoted_after": a.misquoted_after,
        },
        "evidence": evidence,
    }


def _hash_for(db: ChangeDB, snapshot_id: int, url: str) -> str | None:
    row = db.conn.execute(
        "SELECT content_hash FROM page_versions WHERE snapshot_id = ? AND url = ?",
        (snapshot_id, url)).fetchone()
    return row["content_hash"] if row else None


def page_bodies(db: ChangeDB, pair: tuple[int, int], url: str, *,
                blob_dir: Path | None = None) -> dict:
    """Both sides of one page, on demand — the full-page method's raw material.

    Either side may be None: an added page has no before, a `gc` may have collected a
    blob. The UI says which rather than showing an empty pane as if the page were empty.
    """
    before, after = pair
    return {
        "url": url,
        "before": blobs.read_or_none(_hash_for(db, before, url), blob_dir),
        "after": blobs.read_or_none(_hash_for(db, after, url), blob_dir),
    }


def signed_context(db: ChangeDB, pair: tuple[int, int], url: str, *,
                   blob_dir: Path | None = None,
                   cap: int = CONTEXT_LINES) -> tuple[list[str], list[str]]:
    """`(removed, added)` for one page — the `-`/`+` context a line is judged in.

    From `classify.changed_sides` over the pair's blobs, direction preserved: the same
    sentence means the opposite thing on the other side. Capped and de-blanked; empty
    lists when either body is unavailable.
    """
    before_body = blobs.read_or_none(_hash_for(db, pair[0], url), blob_dir)
    after_body = blobs.read_or_none(_hash_for(db, pair[1], url), blob_dir)
    if before_body is None or after_body is None:
        return [], []
    removed, added = classify.changed_sides(before_body, after_body)
    return ([ln for ln in removed if ln.strip()][:cap],
            [ln for ln in added if ln.strip()][:cap])
