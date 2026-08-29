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
    extractor          TEXT,
    body_chars         INTEGER,
    file_path          TEXT,
    PRIMARY KEY (snapshot_id, url)
);
CREATE INDEX IF NOT EXISTS idx_pv_url  ON page_versions(url);
CREATE INDEX IF NOT EXISTS idx_pv_hash ON page_versions(content_hash);
"""

# Every column of `page_versions` except the snapshot id, in insert order. A page version
# is passed around as a plain dict keyed by these.
VERSION_COLUMNS = [
    "url", "company", "source_id", "category", "title", "description", "updated_date",
    "content_hash", "output_fingerprint", "extractor", "body_chars", "file_path",
]


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
