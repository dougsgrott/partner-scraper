"""`state/index.db` — the corpus manifest. See PLAN.md §7, §8.

A denormalised copy of each file's frontmatter, so the whole corpus is queryable without
opening 6,000 files. **The Markdown files are the source of truth**; this index is
rebuildable from them at any time (`rebuild`), and the files themselves are rebuildable
from `raw/` with no network. Losing it costs seconds.

Distinct from `state/fetch.db`, which tracks acquisition. This one answers "what is in the
corpus?"; that one answers "what did we ask for and what came back?".
"""

from __future__ import annotations

import logging
import sqlite3
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Self

from ..records import Extracted
from . import writer

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path("state/index.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    url               TEXT PRIMARY KEY,
    company           TEXT NOT NULL,
    source_id         TEXT,
    category          TEXT,
    title             TEXT,
    description       TEXT,
    published_date    TEXT,
    updated_date      TEXT,
    content_hash      TEXT,
    raw_sha256        TEXT,
    file_path         TEXT,
    extractor         TEXT,
    extractor_version TEXT,
    extracted_at      TEXT NOT NULL,
    status            TEXT NOT NULL,
    error             TEXT
);
CREATE INDEX IF NOT EXISTS idx_pages_company  ON pages(company);
CREATE INDEX IF NOT EXISTS idx_pages_category ON pages(category);
CREATE INDEX IF NOT EXISTS idx_pages_status   ON pages(status);
"""

_COLUMNS = [
    "url", "company", "source_id", "category", "title", "description",
    "published_date", "updated_date", "content_hash", "raw_sha256", "file_path",
    "extractor", "extractor_version", "extracted_at", "status", "error",
]

# "duplicate" — a second URL naming a document another URL already produced
# (`/x` and `/x/`, or a redirect). Settled, not failed: there is nothing to fix.
STATUSES = ("ok", "duplicate", "extract_error", "quality_failed")


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


class Index:
    """Thin wrapper over the `pages` table."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._migrate()
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def _migrate(self) -> None:
        """Replace a v1 index outright rather than migrating it.

        The old table keyed on a model-assigned `theme` and its rows point at files the
        retired pipeline wrote. Since the index is rebuildable from `data/` by design,
        dropping it is cheaper and safer than reconciling two schemas.
        """
        cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(pages)")}
        if cols and "theme" in cols:
            logger.warning("replacing the v1 index schema (theme → category); rebuildable from data/")
            self.conn.execute("DROP TABLE pages")
            self.conn.commit()

    # -- context manager -------------------------------------------------
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self.conn.close()

    # -- writes ----------------------------------------------------------
    def _upsert(self, row: dict) -> None:
        row = {col: row.get(col) for col in _COLUMNS}
        placeholders = ", ".join(f":{c}" for c in _COLUMNS)
        updates = ", ".join(f"{c}=excluded.{c}" for c in _COLUMNS if c != "url")
        self.conn.execute(
            f"INSERT INTO pages ({', '.join(_COLUMNS)}) VALUES ({placeholders}) "
            f"ON CONFLICT(url) DO UPDATE SET {updates}",
            row,
        )
        self.conn.commit()

    def upsert(
        self,
        record: Extracted,
        file_path: str | Path,
        *,
        content_hash: str,
        raw_sha256: str | None = None,
        extracted_at: datetime | None = None,
    ) -> None:
        self._upsert({
            "url": record.source_url,
            "company": record.company,
            "source_id": record.source_id,
            "category": record.category,
            "title": record.title,
            "description": record.description,
            "published_date": _iso(record.published_date),
            "updated_date": _iso(record.updated_date),
            "content_hash": content_hash,
            "raw_sha256": raw_sha256,
            "file_path": str(file_path),
            "extractor": record.extractor,
            "extractor_version": record.extractor_version,
            "extracted_at": (extracted_at or datetime.now(UTC)).isoformat(timespec="seconds"),
            "status": "ok",
            "error": None,
        })

    def owner_of(self, file_path: str | Path) -> str | None:
        """The URL that produced a corpus file, if any — the durable duplicate check."""
        row = self.conn.execute(
            "SELECT url FROM pages WHERE file_path = ? AND status = 'ok' LIMIT 1",
            (str(file_path),),
        ).fetchone()
        return row["url"] if row else None

    def record_duplicate(self, url: str, company: str, *, file_path: str | Path,
                         duplicate_of: str, source_id: str | None = None,
                         extractor_version: str | None = None) -> None:
        """Record that this URL names a document already in the corpus."""
        self._upsert({
            "url": url,
            "company": company,
            "source_id": source_id,
            "file_path": str(file_path),
            "extractor_version": extractor_version,
            "extracted_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "status": "duplicate",
            "error": f"same document as {duplicate_of}",
        })

    def record_failure(self, url: str, company: str, *, status: str, error: str,
                       source_id: str | None = None) -> None:
        """Record an extraction or quality failure, keeping it visible in the manifest."""
        self._upsert({
            "url": url,
            "company": company,
            "source_id": source_id,
            "extracted_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "status": status,
            "error": error,
        })

    # -- reads -----------------------------------------------------------
    def get(self, url: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM pages WHERE url = ?", (url,)).fetchone()
        return dict(row) if row else None

    def needs_extract(self, url: str, *, raw_sha256: str | None = None,
                      extractor_version: str | None = None) -> bool:
        """Whether a page should be (re-)extracted.

        Re-extract when it is new or previously failed, when the archived bytes changed
        (a refetch found new content), or when the extractor itself was revised. That
        last case is what makes fixing a parser a local re-run over `raw/` — PLAN.md §8.
        """
        row = self.get(url)
        if row is None or row["status"] not in ("ok", "duplicate"):
            return True
        if extractor_version is not None and row["extractor_version"] != extractor_version:
            return True
        return raw_sha256 is not None and row["raw_sha256"] != raw_sha256

    def query(
        self,
        *,
        company: str | None = None,
        category: str | None = None,
        source_id: str | None = None,
        status: str | None = None,
        updated_after: date | None = None,
        updated_before: date | None = None,
    ) -> list[dict]:
        clauses: list[str] = []
        params: list[object] = []
        for col, val in (
            ("company", company),
            ("category", category),
            ("source_id", source_id),
            ("status", status),
        ):
            if val is not None:
                clauses.append(f"{col} = ?")
                params.append(val)
        if updated_after is not None:
            clauses.append("updated_date >= ?")
            params.append(updated_after.isoformat())
        if updated_before is not None:
            clauses.append("updated_date <= ?")
            params.append(updated_before.isoformat())

        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        cur = self.conn.execute(f"SELECT * FROM pages{where} ORDER BY url", params)
        return [dict(r) for r in cur.fetchall()]

    def counts(self) -> dict[str, int]:
        counts = Counter({status: 0 for status in STATUSES})
        for row in self.conn.execute("SELECT status, COUNT(*) AS n FROM pages GROUP BY status"):
            counts[row["status"]] = row["n"]
        return dict(counts)

    # -- maintenance -----------------------------------------------------
    def rebuild(self, data_dir: str | Path = "data") -> int:
        """Repopulate the index from the Markdown files. Returns rows written."""
        self.conn.execute("DELETE FROM pages")
        count = 0
        for md in sorted(Path(data_dir).rglob("*.md")):
            front, _ = writer.parse(md)
            if not front.get("source_url"):
                continue
            extractor, _, version = str(front.get("extractor", "")).partition("@")
            self._upsert({
                "url": front["source_url"],
                "company": front.get("company"),
                "source_id": front.get("source_id"),
                "category": front.get("category"),
                "title": front.get("title"),
                "description": front.get("description"),
                "published_date": _date_str(front.get("published_date")),
                "updated_date": _date_str(front.get("updated_date")),
                "content_hash": front.get("content_hash"),
                "raw_sha256": front.get("raw_sha256"),
                "file_path": str(md),
                "extractor": extractor or None,
                "extractor_version": version or None,
                "extracted_at": front.get("extracted_at") or datetime.now(UTC).isoformat(),
                "status": "ok",
                "error": None,
            })
            count += 1
        self.conn.commit()
        return count


def _date_str(value) -> str | None:
    if value is None:
        return None
    return value.isoformat() if isinstance(value, date) else str(value)
