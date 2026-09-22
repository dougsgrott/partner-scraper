"""`state/changes.db` — the corpus's history. See docs/changefeed-plan.md.

A third database beside `fetch.db` (what we asked for) and `index.db` (what the corpus
contains). This one answers *what the corpus contained at some earlier moment*, which
neither of the others can: both upsert by URL, so yesterday's row is gone.

It is append-only by intent. A snapshot is a fact about a moment, and rewriting one
retroactively would make every diff computed from it a lie. `gc` deletes whole snapshots
and their unreferenced blobs; nothing edits a `page_versions` row in place.

Unlike `index.db`, this is **not** rebuildable from `data/`. `data/` holds one version of
each page. Losing this database loses the history, which is the one thing here that cannot
be recomputed — so it is worth backing up in a way the other two are not.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

from scraper.db import connect

DEFAULT_DB_PATH = Path("state/changes.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    taken_at   TEXT NOT NULL,
    label      TEXT,
    page_count INTEGER NOT NULL DEFAULT 0,
    note       TEXT
);

CREATE TABLE IF NOT EXISTS page_versions (
    snapshot_id        INTEGER NOT NULL REFERENCES snapshots(id),
    url                TEXT NOT NULL,
    company            TEXT,
    source_id          TEXT,
    category           TEXT,
    title              TEXT,
    description        TEXT,
    updated_date       TEXT,
    content_hash       TEXT NOT NULL,
    output_fingerprint TEXT,
    body_fingerprint   TEXT,
    extractor          TEXT,
    body_chars         INTEGER,
    file_path          TEXT,
    PRIMARY KEY (snapshot_id, url)
);
CREATE INDEX IF NOT EXISTS idx_pv_url  ON page_versions(url);
CREATE INDEX IF NOT EXISTS idx_pv_hash ON page_versions(content_hash);

-- Phase 2 output. A finding is one *story*, which is why `urls` is a list: measurement
-- showed 44 returned items carried only ~25 distinct stories, and "the ai_* functions now
-- require DBR 15.4+" should be one row citing ten pages, not ten rows.
--
-- Stored so a digest renders deterministically and can be re-rendered — shorter, or for a
-- different audience — without paying for the model again.
CREATE TABLE IF NOT EXISTS findings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    before_snapshot INTEGER NOT NULL,
    after_snapshot  INTEGER NOT NULL,
    recorded_at     TEXT NOT NULL,
    impact          TEXT NOT NULL,
    kind            TEXT,
    summary         TEXT NOT NULL,
    detail          TEXT,
    -- JSON array. A join table would normalise it, but nothing queries findings *by* URL
    -- — they are read as a set, per snapshot pair, to render one report.
    urls            TEXT NOT NULL,
    -- Set when a later run over the same pair replaces this row. Superseded findings are
    -- kept, not deleted: comparing two runs is the only way to see whether the digest is
    -- stable, and the first attempt at that comparison failed because the re-run had
    -- destroyed its predecessor.
    superseded_at   TEXT
);
CREATE INDEX IF NOT EXISTS idx_findings_pair ON findings(before_snapshot, after_snapshot);

-- Human grades of findings, one row per (finding, grading method). Before this table,
-- every manual audit's verdicts lived only as prose in session documents — `findings`
-- carries `model` and `prompt_version` precisely so runs can be compared, and nothing
-- compared them. Grades attach to the finding row, not to "current", so superseding a
-- run keeps its grades and prompt versions stay comparable forever.
--
-- Unlike everything else in this database, these rows ARE rebuildable: each import comes
-- from a worksheet under reports/changefeed/verdicts-*.yaml, which is the provenance and
-- the backup. Vocabulary and semantics live in `changefeed.digest.verdicts`.
CREATE TABLE IF NOT EXISTS verdicts (
    finding_id     INTEGER NOT NULL REFERENCES findings(id),
    method         TEXT NOT NULL,     -- excerpt | full-page (what the grader read)
    verdict        TEXT NOT NULL,     -- true | partly | false | unverified
    graded_at      TEXT NOT NULL,
    selection      TEXT,              -- draw (seeded sample) | targeted (hand-picked)
    stratum        TEXT,              -- impact group at draw time
    stratum_weight REAL,              -- population / drawn for that stratum; NULL if targeted
    notes          TEXT,
    source         TEXT,              -- the worksheet file this row came from
    grader         TEXT,              -- who graded; NULL on rows from before the column
    PRIMARY KEY (finding_id, method)
);
"""

# Every column of `page_versions` except the snapshot id, in insert order. A page version
# is passed around as a plain dict keyed by these.
VERSION_COLUMNS = [
    "url", "company", "source_id", "category", "title", "description", "updated_date",
    "content_hash", "output_fingerprint", "body_fingerprint", "extractor", "body_chars",
    "file_path",
]

# Columns added after the first release. Every entry must be nullable and additive: this
# database is the only copy of the corpus's past, so a migration may extend a row but must
# never drop or rewrite one. `index.db` can take the shortcut of dropping its table and
# rebuilding from `data/`; there is nothing to rebuild this from.
_ADDED_COLUMNS = (("body_fingerprint", "TEXT"),)
_ADDED_FINDING_COLUMNS = (
    ("superseded_at", "TEXT"),
    # Provenance. Without it, findings from different prompts are silently incomparable —
    # a reworded prompt changes the output and nothing records which one produced what.
    ("model", "TEXT"),
    ("prompt_version", "TEXT"),
)
_ADDED_VERDICT_COLUMNS = (
    # Grader identity, issue/accuracy/13: the arms were built and graded by the same
    # session — the one bias the ledger records but could not name. Nullable, so every
    # grade imported before the column keeps meaning exactly what it meant.
    ("grader", "TEXT"),
)


@dataclass(frozen=True)
class Snapshot:
    """One recorded state of the corpus."""

    id: int
    taken_at: str
    label: str | None
    page_count: int
    note: str | None = None

    @property
    def name(self) -> str:
        """How a snapshot is named in reports: `#3 (baseline)` or just `#3`."""
        return f"#{self.id} ({self.label})" if self.label else f"#{self.id}"


class ChangeDB:
    """Thin wrapper over `snapshots` and `page_versions`."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = connect(self.path)
        self.conn.executescript(_SCHEMA)
        self._migrate()
        self.conn.commit()

    def _migrate(self) -> None:
        """Add columns a newer schema introduced. A no-op on a database just created.

        Runs after `_SCHEMA`, so a fresh database already has every column and this does
        nothing; an older one gets the additions. Deliberately the only kind of migration
        offered here — see `_ADDED_COLUMNS`.

        A "duplicate column" from the ALTER is tolerated, not raised: it means another
        connection added the column between our PRAGMA and our ALTER — the review UI
        opens a ChangeDB per request and its dashboard fires several requests at once,
        so the first launch against an old database runs this migration concurrently.
        Whoever loses that race finds exactly the schema it wanted.
        """
        import sqlite3

        for table, additions in (("page_versions", _ADDED_COLUMNS),
                                 ("findings", _ADDED_FINDING_COLUMNS),
                                 ("verdicts", _ADDED_VERDICT_COLUMNS)):
            cols = {r["name"] for r in self.conn.execute(f"PRAGMA table_info({table})")}
            for column, ddl in additions:
                if cols and column not in cols:
                    try:
                        self.conn.execute(
                            f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
                    except sqlite3.OperationalError as err:
                        if "duplicate column" not in str(err):
                            raise
                    self.conn.commit()

    # -- context manager -------------------------------------------------
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self.conn.close()

    # -- writes ----------------------------------------------------------
    def create_snapshot(self, *, label: str | None = None, note: str | None = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO snapshots (taken_at, label, note) VALUES (?, ?, ?)",
            (datetime.now(UTC).isoformat(timespec="seconds"), label, note),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def add_versions(self, snapshot_id: int, rows: list[dict]) -> None:
        """Insert page versions in one transaction — 6,400 separate commits is minutes."""
        cols = ", ".join(["snapshot_id", *VERSION_COLUMNS])
        placeholders = ", ".join(["?"] * (len(VERSION_COLUMNS) + 1))
        self.conn.executemany(
            f"INSERT OR REPLACE INTO page_versions ({cols}) VALUES ({placeholders})",
            [(snapshot_id, *(row.get(c) for c in VERSION_COLUMNS)) for row in rows],
        )
        self.conn.commit()

    def finish_snapshot(self, snapshot_id: int) -> int:
        """Stamp the snapshot with the number of pages actually recorded."""
        count = self.conn.execute(
            "SELECT COUNT(*) FROM page_versions WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchone()[0]
        self.conn.execute(
            "UPDATE snapshots SET page_count = ? WHERE id = ?", (count, snapshot_id))
        self.conn.commit()
        return int(count)

    def delete_snapshot(self, snapshot_id: int) -> None:
        """Drop a snapshot and its versions. Blob cleanup is `blobs.prune`'s job."""
        self.conn.execute("DELETE FROM page_versions WHERE snapshot_id = ?", (snapshot_id,))
        self.conn.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))
        self.conn.commit()

    # -- reads -----------------------------------------------------------
    def snapshots(self) -> list[Snapshot]:
        return [
            Snapshot(r["id"], r["taken_at"], r["label"], r["page_count"], r["note"])
            for r in self.conn.execute("SELECT * FROM snapshots ORDER BY id")
        ]

    def snapshot(self, snapshot_id: int) -> Snapshot | None:
        row = self.conn.execute(
            "SELECT * FROM snapshots WHERE id = ?", (snapshot_id,)).fetchone()
        if row is None:
            return None
        return Snapshot(row["id"], row["taken_at"], row["label"], row["page_count"], row["note"])

    def resolve(self, ref: str | int) -> Snapshot | None:
        """Find a snapshot by id, by label, or by `latest` / `previous`.

        Labels are what a human actually remembers (`baseline`, `after-refresh`), so the
        CLI accepts either. A label is matched newest-first, since re-using one is a
        reasonable thing to do across runs.
        """
        snaps = self.snapshots()
        if not snaps:
            return None
        text = str(ref).strip()
        if text in ("latest", "last", "-1"):
            return snaps[-1]
        if text in ("previous", "prev", "-2"):
            return snaps[-2] if len(snaps) > 1 else None
        if text.lstrip("#").isdigit():
            return self.snapshot(int(text.lstrip("#")))
        return next((s for s in reversed(snaps) if s.label == text), None)

    def last_two(self) -> tuple[Snapshot, Snapshot] | None:
        snaps = self.snapshots()
        return (snaps[-2], snaps[-1]) if len(snaps) > 1 else None

    def versions(self, snapshot_id: int) -> dict[str, dict]:
        """`{url: version}` for one snapshot — the diff's input on each side."""
        cur = self.conn.execute(
            "SELECT * FROM page_versions WHERE snapshot_id = ?", (snapshot_id,))
        return {r["url"]: {c: r[c] for c in VERSION_COLUMNS} for r in cur}

    def history(self, url: str) -> list[dict]:
        """Every recorded version of one page, oldest first — the time machine."""
        cur = self.conn.execute(
            "SELECT pv.*, s.taken_at, s.label FROM page_versions pv "
            "JOIN snapshots s ON s.id = pv.snapshot_id "
            "WHERE pv.url = ? ORDER BY pv.snapshot_id", (url,))
        return [dict(r) for r in cur]

    def referenced_hashes(self) -> set[str]:
        """Every content hash any snapshot still points at — `gc`'s keep-set."""
        return {r[0] for r in self.conn.execute("SELECT DISTINCT content_hash FROM page_versions")}


def backup(destination: str | Path, *, db_path: str | Path = DEFAULT_DB_PATH,
           blob_dir: str | Path = "state/changes/blobs") -> tuple[int, int]:
    """Copy the history to a second location. Returns `(bytes copied, blobs copied)`.

    **This is the only artifact in the project that cannot be rebuilt.** `raw/` costs a
    crawl, `data/` and `index.db` regenerate from it for free, but the corpus's past exists
    nowhere else — and it is gitignored, so nothing else is protecting it.

    A file copy, deliberately: the blob store is content-addressed and append-only, so
    copying it is safe while a run is in progress and re-copying skips what is already
    there. The database is copied through SQLite's own backup API rather than as a file,
    because a plain copy of a WAL database mid-write is not guaranteed to be consistent.
    """
    import shutil
    import sqlite3

    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)

    source = connect(db_path)
    try:
        target = sqlite3.connect(destination / Path(db_path).name)
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()
    copied = (destination / Path(db_path).name).stat().st_size

    blobs_out = destination / "blobs"
    new_blobs = 0
    for blob in Path(blob_dir).rglob("*.gz"):
        target_path = blobs_out / blob.parent.name / blob.name
        if target_path.exists():
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(blob, target_path)
        copied += blob.stat().st_size
        new_blobs += 1
    return copied, new_blobs
