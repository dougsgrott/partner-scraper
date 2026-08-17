"""SQLite manifest over the corpus: dedup, incremental gating, and querying.

The index is a denormalized copy of each file's frontmatter plus a content hash and the
sitemap lastmod. The Markdown files are the source of truth — the index can be rebuilt
from them at any time (``rebuild``). See PLAN.md §5.3.

Deviation from the PLAN.md sketch (documented on purpose):
  * added `lastmod` — the sitemap lastmod at last ingest, so the pre-fetch dedup hint
    compares like-for-like instead of against Claude-extracted dates.
  * added `error` and relaxed some NOT NULLs — so fetch/parse failures can be recorded
    as rows (status = fetch_error | parse_error) alongside successful pages.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Self

from ..ingest.schema import PageRecord
from . import writer

DEFAULT_DB_PATH = Path("state/index.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    url            TEXT PRIMARY KEY,
    company        TEXT NOT NULL,
    theme          TEXT,
    content_type   TEXT,
    title          TEXT,
    summary        TEXT,
    published_date TEXT,
    updated_date   TEXT,
    lastmod        TEXT,
    content_hash   TEXT,
    file_path      TEXT,
    fetched_at     TEXT NOT NULL,
    status         TEXT NOT NULL,
    error          TEXT,
    attempts       INTEGER NOT NULL DEFAULT 0
);
"""

_COLUMNS = [
    "url", "company", "theme", "content_type", "title", "summary",
    "published_date", "updated_date", "lastmod", "content_hash",
    "file_path", "fetched_at", "status", "error", "attempts",
]


def _iso(value: date | None) -> str | None:
    return value.isoformat() if value else None


class Index:
    """Thin wrapper over a SQLite `pages` table."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(_SCHEMA)
        self._migrate()
        self.conn.commit()

    def _migrate(self) -> None:
        """Additive migrations for pre-existing DBs (CREATE TABLE IF NOT EXISTS is a no-op
        once the table exists, so new columns must be added explicitly)."""
        cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(pages)")}
        if "attempts" not in cols:
            self.conn.execute("ALTER TABLE pages ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0")

    # -- context manager -------------------------------------------------
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self.conn.close()

    # -- writes ----------------------------------------------------------
    def _next_attempts(self, url: str) -> int:
        """One more than the stored attempt count (0 if the URL is new)."""
        row = self.get(url)
        prev = row["attempts"] if row and row["attempts"] is not None else 0
        return prev + 1

    def _upsert(self, row: dict) -> None:
        row = {col: row.get(col) for col in _COLUMNS}
        if row["attempts"] is None:  # NOT NULL column; rebuild() doesn't set it
            row["attempts"] = 0
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
        url: str,
        record: PageRecord,
        file_path: str | Path,
        content_hash: str,
        *,
        lastmod: date | None = None,
        fetched_at: datetime | None = None,
    ) -> None:
        """Record a successfully-ingested page."""
        fetched_at = fetched_at or datetime.now(UTC)
        self._upsert({
            "url": url,
            "company": record.company,
            "theme": record.theme,
            "content_type": record.content_type,
            "title": record.title,
            "summary": record.summary,
            "published_date": _iso(record.published_date),
            "updated_date": _iso(record.updated_date),
            "lastmod": _iso(lastmod),
            "content_hash": content_hash,
            "file_path": str(file_path),
            "fetched_at": fetched_at.isoformat(),
            "status": "ok",
            "error": None,
            "attempts": self._next_attempts(url),
        })

    def record_error(
        self,
        url: str,
        company: str,
        status: str,
        error: str,
        *,
        lastmod: date | None = None,
        fetched_at: datetime | None = None,
    ) -> None:
        """Record a fetch_error / parse_error so the run has an auditable trail."""
        fetched_at = fetched_at or datetime.now(UTC)
        self._upsert({
            "url": url,
            "company": company,
            "lastmod": _iso(lastmod),
            "fetched_at": fetched_at.isoformat(),
            "status": status,
            "error": error,
            "attempts": self._next_attempts(url),
        })

    # -- reads -----------------------------------------------------------
    def get(self, url: str) -> dict | None:
        cur = self.conn.execute("SELECT * FROM pages WHERE url = ?", (url,))
        row = cur.fetchone()
        return dict(row) if row else None

    def needs_refresh(
        self,
        url: str,
        lastmod: date | None = None,
        new_hash: str | None = None,
    ) -> bool:
        """Decide whether a URL should be (re)ingested.

        * unknown URL -> True (never seen)
        * new_hash given (post-fetch) -> True iff it differs from the stored hash
        * else lastmod given (pre-fetch hint) -> True iff sitemap lastmod is newer than
          what we stored at last ingest
        * otherwise (seen, no newer signal) -> False
        """
        row = self.get(url)
        if row is None:
            return True
        if new_hash is not None:
            return new_hash != row["content_hash"]
        if lastmod is not None and row["lastmod"]:
            return lastmod.isoformat() > row["lastmod"]
        return False

    def should_ingest(self, url: str, lastmod: date | None, max_attempts: int) -> bool:
        """Work-selection gate for the batch runner.

        * never seen -> True
        * last ingest ok -> True only if the page changed (needs_refresh)
        * last attempt errored -> True while attempts remain under the cap
          (needs_refresh alone would skip error rows forever)
        """
        row = self.get(url)
        if row is None:
            return True
        if row["status"] == "ok":
            return self.needs_refresh(url, lastmod)
        return (row["attempts"] or 0) < max_attempts

    def query(
        self,
        *,
        company: str | None = None,
        theme: str | None = None,
        content_type: str | None = None,
        status: str | None = None,
        updated_after: date | None = None,
        updated_before: date | None = None,
    ) -> list[dict]:
        """Filtered query over the manifest. ISO date strings compare lexically."""
        clauses: list[str] = []
        params: list[object] = []
        for col, val in (
            ("company", company),
            ("theme", theme),
            ("content_type", content_type),
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

    # -- maintenance -----------------------------------------------------
    def rebuild(self, data_dir: str | Path = "data") -> int:
        """Repopulate the index from the Markdown files. Returns rows written."""
        self.conn.execute("DELETE FROM pages")
        count = 0
        for md in sorted(Path(data_dir).rglob("*.md")):
            fm, _ = writer.parse(md)
            if not fm.get("source_url"):
                continue
            self._upsert({
                "url": fm["source_url"],
                "company": fm.get("company"),
                "theme": fm.get("theme"),
                "content_type": fm.get("content_type"),
                "title": fm.get("title"),
                "summary": fm.get("summary"),
                "published_date": _date_str(fm.get("published_date")),
                "updated_date": _date_str(fm.get("updated_date")),
                "lastmod": None,  # not persisted in frontmatter; re-learned on next run
                "content_hash": fm.get("content_hash"),
                "file_path": str(md),
                "fetched_at": fm.get("fetched_at") or datetime.now(UTC).isoformat(),
                "status": "ok",
                "error": None,
            })
            count += 1
        self.conn.commit()
        return count


def _date_str(value) -> str | None:
    """Frontmatter dates load as date objects (yaml) or strings; normalize to ISO str."""
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return str(value)
