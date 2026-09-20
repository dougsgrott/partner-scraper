"""Compare two snapshots. See docs/changefeed-plan.md.

The output is a list of `PageChange` records, each carrying three orthogonal facts: *what*
happened to the page (`kind`), *who* caused it (`cause`, from `classify.attribute`), and
*how much it matters* (`weight`, from `classify.weigh`). Keeping them separate is what lets
the report say "412 pages moved, but 400 of those were our own extractor" instead of
reporting 412 vendor changes.

Bodies are read from the version store on demand rather than held on the change records. A
pipeline-wide re-extraction moves every page in the corpus, and holding both sides of 6,400
diffs in memory is a few hundred megabytes for a report that will expand a few dozen of
them.
"""

from __future__ import annotations

import difflib
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from . import blobs, classify
from .db import ChangeDB, Snapshot

ADDED = "added"
REMOVED = "removed"
MODIFIED = "modified"
MOVED = "moved"
METADATA = "metadata"

KINDS = (ADDED, REMOVED, MODIFIED, MOVED, METADATA)

# Fields whose change, with the body untouched, counts as a metadata-only change.
METADATA_FIELDS = ("title", "description", "updated_date", "category")

# The date segment of a corpus path: data/<company>/<category>/<YYYY-MM|undated>/<file>.
_DATE_SEGMENT = re.compile(r"^(\d{4}-\d{2}|undated)$")


def _date_only_move(old_path: str | None, new_path: str | None) -> bool:
    """True when two corpus paths differ only in the layout's date segment.

    The layout keys that segment on the vendor's `updated_date`, a field the vendor can
    rewrite site-wide with no content change — the 2026-09-11 re-date relocated 4,805
    byte-identical pages this way (issue/accuracy/12). Under this layout's semantics
    such a move *is* a metadata change, so `_classify_page` files it as one; `moved`
    stays reserved for a page whose place in the tree genuinely changed.
    """
    if not old_path or not new_path:
        return False
    a, b = old_path.split("/"), new_path.split("/")
    if len(a) != len(b) or len(a) < 2 or a[:-2] != b[:-2] or a[-1] != b[-1]:
        return False
    return bool(_DATE_SEGMENT.match(a[-2]) and _DATE_SEGMENT.match(b[-2]))


def _date_segment_dropped(old_path: str | None, new_path: str | None) -> bool:
    """True when the paths differ only by a date segment present on one side.

    The signature of the 2026-09-19 layout migration (docs/layout-migration-plan.md):
    `data/c/cat/2026-09/slug.md` -> `data/c/cat/slug.md`. That relocation is *our*
    churn — the vendor changed nothing — so `_classify_page` attributes it `pipeline`,
    which keeps it out of the feed and the digest prompt like all pipeline churn.
    Symmetric on purpose: a rollback would be our churn too.
    """
    if not old_path or not new_path:
        return False
    a, b = old_path.split("/"), new_path.split("/")
    if len(a) == len(b) + 1:
        longer, shorter = a, b
    elif len(b) == len(a) + 1:
        longer, shorter = b, a
    else:
        return False
    return (len(longer) >= 2
            and bool(_DATE_SEGMENT.match(longer[-2]))
            and longer[:-2] + longer[-1:] == shorter)

# A 4.77 MB page exists in this corpus. Diffs are truncated, and the truncation is always
# announced — quietly eliding half a diff is how a reader is misled.
MAX_DIFF_LINES = 400
MAX_DIFF_CHARS = 40_000

# Above this, `difflib` stops being viable: it is superlinear, and aligning two 6 MB
# machine-generated API pages takes minutes for a diff nobody will read line by line.
# Past it the report falls back to an unaligned changed-lines listing, and says so.
MAX_ALIGNED_CHARS = 400_000


@dataclass(frozen=True)
class PageChange:
    """One page's difference between two snapshots."""

    url: str
    kind: str
    cause: str
    weight: str
    before: dict | None = None
    after: dict | None = None
    # Why it ranked where it did, and how far up the feed it belongs. Empty for kinds
    # with no two bodies to compare (added, removed, moved, metadata).
    signals: dict = field(default_factory=dict)
    severity: float = 0.0

    @property
    def current(self) -> dict:
        """Whichever side exists — a removed page has no `after`."""
        return self.after or self.before or {}

    @property
    def title(self) -> str:
        return self.current.get("title") or self.url

    @property
    def company(self) -> str:
        return self.current.get("company") or "unknown"

    @property
    def category(self) -> str:
        return self.current.get("category") or "uncategorised"

    @property
    def delta_chars(self) -> int:
        after = (self.after or {}).get("body_chars") or 0
        before = (self.before or {}).get("body_chars") or 0
        return after - before

    @property
    def is_feed_worthy(self) -> bool:
        """A real upstream change a reader should see, as opposed to our own churn."""
        return self.cause == classify.CONTENT and self.weight == classify.SUBSTANTIVE


@dataclass
class DiffResult:
    """Every difference between two snapshots, plus the counts a summary needs."""

    before: Snapshot
    after: Snapshot
    changes: list[PageChange] = field(default_factory=list)
    unreadable: list[str] = field(default_factory=list)

    def by_kind(self, kind: str) -> list[PageChange]:
        return [c for c in self.changes if c.kind == kind]

    def by_cause(self, cause: str) -> list[PageChange]:
        return [c for c in self.changes if c.cause == cause]

    def counts(self) -> dict[str, int]:
        return {kind: len(self.by_kind(kind)) for kind in KINDS}

    def feed(self) -> list[PageChange]:
        """What a human should actually read, most urgent first.

        Ordered by severity, not alphabetically. With ~680 substantive changes in a single
        run this is the only reduction the deterministic layer can honestly offer: no
        threshold turns that into a readable handful, because measurement showed most of
        them really are substantive. What it can do is put the deprecations and the
        changed limits above the reworded paragraphs. The url tiebreak keeps the order
        reproducible between runs.
        """
        return sorted(
            (c for c in self.changes if c.is_feed_worthy),
            key=lambda c: (-c.severity, c.company, c.url),
        )

    def suppressed(self) -> list[PageChange]:
        """Real vendor changes ranked `low` or `noise` — listed, never expanded."""
        return sorted(
            (c for c in self.changes
             if c.cause == classify.CONTENT and c.weight != classify.SUBSTANTIVE),
            key=lambda c: (-c.severity, c.company, c.url),
        )

    @property
    def is_empty(self) -> bool:
        return not self.changes


def compare(
    before: Snapshot,
    after: Snapshot,
    *,
    changes_db: str | Path | None = None,
    blob_dir: str | Path | None = None,
    db: ChangeDB | None = None,
) -> DiffResult:
    """Diff two snapshots. Opens its own `ChangeDB` unless one is supplied."""
    owned = db is None
    db = db or (ChangeDB(changes_db) if changes_db else ChangeDB())
    blob_dir = Path(blob_dir) if blob_dir else None

    try:
        old = db.versions(before.id)
        new = db.versions(after.id)
        result = DiffResult(before=before, after=after)

        for url in sorted(old.keys() | new.keys()):
            change = _classify_page(url, old.get(url), new.get(url), blob_dir, result)
            if change is not None:
                result.changes.append(change)
        return result
    finally:
        if owned:
            db.close()


def _classify_page(
    url: str,
    old: dict | None,
    new: dict | None,
    blob_dir: Path | None,
    result: DiffResult,
) -> PageChange | None:
    """Decide what happened to one page, or None if nothing did."""
    if old is None:
        # A page appearing is a corpus change worth reporting, though the cause is not
        # purely the vendor's: a widened worklist or a newly enabled source lands here too.
        return PageChange(url, ADDED, classify.CONTENT, classify.SUBSTANTIVE, None, new)
    if new is None:
        return PageChange(url, REMOVED, classify.CONTENT, classify.SUBSTANTIVE, old, None)

    if old["content_hash"] != new["content_hash"]:
        cause = classify.attribute(old, new)
        weight, counts = _weigh_bodies(url, old, new, blob_dir, result)
        return PageChange(url, MODIFIED, cause, weight, old, new,
                          signals=counts, severity=classify.severity(counts))

    # Same body from here on: the page did not change, its filing or its metadata did.
    path_moved = old.get("file_path") != new.get("file_path")
    if path_moved and not _date_only_move(old.get("file_path"), new.get("file_path")):
        cause = (classify.PIPELINE
                 if _date_segment_dropped(old.get("file_path"), new.get("file_path"))
                 else classify.CONTENT)
        return PageChange(url, MOVED, cause, classify.LOW, old, new)

    # A date-only move falls through to here: its cause is the `updated_date` edit
    # itself, so it is filed with the metadata change that produced it.
    moved_fields = [f for f in METADATA_FIELDS if old.get(f) != new.get(f)]
    if moved_fields or path_moved:
        # A retitled page is worth seeing; a redescribed one usually is not.
        weight = classify.SUBSTANTIVE if "title" in moved_fields else classify.LOW
        return PageChange(url, METADATA, classify.CONTENT, weight, old, new)

    return None


def _weigh_bodies(
    url: str,
    old: dict,
    new: dict,
    blob_dir: Path | None,
    result: DiffResult,
) -> tuple[str, dict]:
    """Rank a modification and return the evidence, recording unreadable bodies."""
    before_body = blobs.read_or_none(old["content_hash"], blob_dir)
    after_body = blobs.read_or_none(new["content_hash"], blob_dir)
    if before_body is None or after_body is None:
        result.unreadable.append(url)
        return classify.SUBSTANTIVE, {}
    return classify.weigh(before_body, after_body), classify.signals(before_body, after_body)


def render_diff(
    change: PageChange,
    *,
    blob_dir: str | Path | None = None,
    context: int = 3,
    max_lines: int = MAX_DIFF_LINES,
    max_chars: int = MAX_DIFF_CHARS,
    mark_revisions: bool = False,
) -> str:
    """A unified diff for one change, truncated with an explicit notice.

    Returns an empty string when either body is unavailable, so a collected blob degrades
    one entry in the report rather than ending the run.
    """
    blob_dir = Path(blob_dir) if blob_dir else None
    before = blobs.read_or_none((change.before or {}).get("content_hash"), blob_dir)
    after = blobs.read_or_none((change.after or {}).get("content_hash"), blob_dir)
    if before is None or after is None:
        return ""

    if max(len(before), len(after)) > MAX_ALIGNED_CHARS:
        return _unaligned(change, before, after, max_lines, mark=mark_revisions)

    lines = list(difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile=f"{change.url} @ before",
        tofile=f"{change.url} @ after",
        lineterm="",
        n=context,
    ))

    total = len(lines)
    if total > max_lines:
        lines = lines[:max_lines]
        lines.append(f"... diff truncated: {total - max_lines} of {total} lines not shown")

    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n... diff truncated at {max_chars} characters"
    return text


def _unaligned(change: PageChange, before: str, after: str, max_lines: int,
               mark: bool = False) -> str:
    """A changed-lines listing for pages too large to align.

    Not a unified diff and shaped so it cannot be mistaken for one: no hunk headers, and a
    leading note. The lines are real and correctly attributed to added or removed. An
    aligned diff shows an edited row as an adjacent -/+ pair; that pairing is exactly what
    this path loses, so revised lines are tagged instead (`~-`/`~+`,
    issue/accuracy/07) — this output is read by the model mid-session, and an untagged
    `+` here is where "Grok 4.6 added" came from.
    """
    removed = Counter(before.splitlines()) - Counter(after.splitlines())
    added = Counter(after.splitlines()) - Counter(before.splitlines())
    budget = max(2, max_lines // 2)
    rem_shown = list(removed.elements())[:budget]
    add_shown = list(added.elements())[:budget]
    out = [
        f"# {change.url}",
        (f"# {len(before):,} -> {len(after):,} characters — too large to align, so these "
         f"are changed lines without context, not a diff."),
        f"# {sum(removed.values()):,} removed, {sum(added.values()):,} added."
        + (" A ~ sign marks a line with a close variant on the other side: edited, "
           "not added or removed whole." if mark else ""),
    ]
    if mark:
        rem_tokens = [classify.token_set(x) for x in removed]
        add_tokens = [classify.token_set(x) for x in added]
        out += [("~-" if classify.is_revision(line, add_tokens) else "-") + line
                for line in rem_shown]
        out += [("~+" if classify.is_revision(line, rem_tokens) else "+") + line
                for line in add_shown]
    else:
        out += [f"-{line}" for line in rem_shown]
        out += [f"+{line}" for line in add_shown]
    return "\n".join(out)
