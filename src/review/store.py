"""The review tool's own tables — all additive, no existing row touched.

Three tables beside the ledger in `changes.db`, created with the same
`CREATE TABLE IF NOT EXISTS` pattern as `changefeed.db._SCHEMA`:

* **review_queues** — what a queue *is*: kind, title, and the parameters its items are
  re-derived from at open time. Deliberately no item-state table: `audit.draw` is
  seeded and the absence scan is deterministic, so materialization is reproducible,
  and "done" is simply "a verdict or label row already exists". Nothing to drift.
* **label_sessions** — one per labeling queue: taxonomy version and pre-labeler
  identity, so a session's labels are forever attributable to what suggested them.
* **line_labels** — the labeled-line dataset of docs/accuracy-enrichment-plan.md §3.1.
  `line_text` is verbatim (the fixture rule); `pre_label` vs `label` per row is the
  flip — the measure of pre-labeler bias leaking into ground truth.

Grades themselves live in the existing `verdicts` table; this module never writes one.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from changefeed.db import ChangeDB

# Taxonomy v1, docs/accuracy-enrichment-plan.md §3.1 — mirrors what downstream consumes,
# aligned with findings.IMPACTS so classifier output is comparable with finding labels.
TAXONOMY_VERSION = "1"
TAXONOMY = ("restriction", "behavioural-change", "addition", "editorial", "regeneration")
# The unsure verdict. Stored (a skipped line is session provenance) but excluded from
# the flip rate and from every training export — the `unverified` precedent.
SKIP = "skip"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS review_queues (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kind        TEXT NOT NULL,      -- grading | labeling (queues.REGISTRY)
    title       TEXT NOT NULL,
    params_json TEXT NOT NULL,      -- everything materialization needs, sealed at creation
    created_at  TEXT NOT NULL,
    note        TEXT
);

CREATE TABLE IF NOT EXISTS label_sessions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    queue_id         INTEGER NOT NULL REFERENCES review_queues(id),
    taxonomy_version TEXT NOT NULL,
    pre_labeler      TEXT,
    created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS line_labels (
    session_id      INTEGER NOT NULL REFERENCES label_sessions(id),
    before_snapshot INTEGER NOT NULL,
    after_snapshot  INTEGER NOT NULL,
    url             TEXT NOT NULL,
    line_hash       TEXT NOT NULL,
    line_text       TEXT NOT NULL,  -- verbatim, per the fixture rule
    context_before  TEXT,           -- the page's `-` lines (changed_sides, capped)
    context_after   TEXT,           -- the page's `+` lines
    pre_label       TEXT,
    label           TEXT NOT NULL,
    labeler         TEXT,
    labeled_at      TEXT NOT NULL,
    notes           TEXT,
    PRIMARY KEY (session_id, line_hash)
);
"""


def ensure_schema(db: ChangeDB) -> None:
    """Create the review tables if missing. Safe to run on every open."""
    db.conn.executescript(_SCHEMA)
    db.conn.commit()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def line_hash(url: str, line: str) -> str:
    """A line's identity within a queue: page + whitespace-normalised text.

    Whitespace-normalised so a reflow between materializations does not orphan a label,
    while `line_text` stays verbatim in the row.
    """
    key = f"{url}\n{' '.join(line.split())}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# -- queues ----------------------------------------------------------------


def create_queue(db: ChangeDB, *, kind: str, title: str, params: dict,
                 note: str | None = None) -> int:
    cur = db.conn.execute(
        "INSERT INTO review_queues (kind, title, params_json, created_at, note) "
        "VALUES (?, ?, ?, ?, ?)",
        (kind, title, json.dumps(params), _now(), note))
    db.conn.commit()
    return int(cur.lastrowid)


def _queue_row(r) -> dict:
    return {"id": r["id"], "kind": r["kind"], "title": r["title"],
            "params": json.loads(r["params_json"]), "created_at": r["created_at"],
            "note": r["note"]}


def queues(db: ChangeDB) -> list[dict]:
    rows = db.conn.execute("SELECT * FROM review_queues ORDER BY id DESC").fetchall()
    return [_queue_row(r) for r in rows]


def queue(db: ChangeDB, queue_id: int) -> dict | None:
    r = db.conn.execute(
        "SELECT * FROM review_queues WHERE id = ?", (queue_id,)).fetchone()
    return _queue_row(r) if r else None


# -- labeling sessions -------------------------------------------------------


def create_session(db: ChangeDB, *, queue_id: int, taxonomy_version: str = TAXONOMY_VERSION,
                   pre_labeler: str | None = None) -> int:
    cur = db.conn.execute(
        "INSERT INTO label_sessions (queue_id, taxonomy_version, pre_labeler, created_at) "
        "VALUES (?, ?, ?, ?)", (queue_id, taxonomy_version, pre_labeler, _now()))
    db.conn.commit()
    return int(cur.lastrowid)


def session_for_queue(db: ChangeDB, queue_id: int) -> dict | None:
    r = db.conn.execute(
        "SELECT * FROM label_sessions WHERE queue_id = ? ORDER BY id LIMIT 1",
        (queue_id,)).fetchone()
    return dict(r) if r else None


def store_label(db: ChangeDB, row: dict) -> None:
    """Insert-or-replace on (session, line_hash) — correcting a label just works."""
    db.conn.execute(
        "INSERT OR REPLACE INTO line_labels (session_id, before_snapshot, after_snapshot, "
        "url, line_hash, line_text, context_before, context_after, pre_label, label, "
        "labeler, labeled_at, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (row["session_id"], row["before_snapshot"], row["after_snapshot"], row["url"],
         row["line_hash"], row["line_text"], row.get("context_before"),
         row.get("context_after"), row.get("pre_label"), row["label"],
         row.get("labeler"), row.get("labeled_at") or _now(), row.get("notes")))
    db.conn.commit()


def labels_for_session(db: ChangeDB, session_id: int) -> list[dict]:
    rows = db.conn.execute(
        "SELECT * FROM line_labels WHERE session_id = ? ORDER BY url, line_hash",
        (session_id,)).fetchall()
    return [dict(r) for r in rows]


def flip_summary(labels: list[dict]) -> dict:
    """Per-session flip rate — the measure of pre-labeler bias the enrichment plan
    requires. A flip is `pre_label != label`; skips and rows with no pre-label count
    in neither numerator nor denominator."""
    skipped = sum(1 for r in labels if r["label"] == SKIP)
    counted = [r for r in labels if r["label"] != SKIP and r["pre_label"]]
    flips = sum(1 for r in counted if r["label"] != r["pre_label"])
    return {
        "labeled": len(labels) - skipped,
        "skipped": skipped,
        "with_pre_label": len(counted),
        "flips": flips,
        "flip_rate": round(flips / len(counted), 4) if counted else None,
    }
