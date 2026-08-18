"""`state/fetch.db` — acquisition bookkeeping, one row per URL. See PLAN.md §6.3, §8.

Separate from `state/index.db` (the *corpus* manifest) on purpose. They answer different
questions and have different lifetimes:

* `fetch.db` — what we asked for, what came back, and what is on disk. Deleting it means
  re-crawling, which is expensive.
* `index.db` — what the corpus contains. Rebuildable from the Markdown files at any time.

The columns that matter most are the HTTP validators. Databricks answers `If-None-Match`
with `304` and an empty body, so a refresh run over 5,720 pages is nearly free — but only
if the ETag from last time was kept. Anthropic sends `no-store`, so there the fallback is
comparing `raw_sha256` after re-fetching (PLAN.md §8).
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

from ..db import connect

DEFAULT_DB_PATH = Path("state/fetch.db")

# ok            — fetched, body archived
# not_modified  — server said 304; the archived copy is still current
# fetch_error   — network failure, timeout, or non-retryable HTTP status
# skipped       — deliberately not fetched (robots, disabled source, dry run)
STATES = ("ok", "not_modified", "fetch_error", "skipped")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS fetches (
    url            TEXT PRIMARY KEY,
    source_id      TEXT NOT NULL,
    final_url      TEXT,
    raw_path       TEXT,
    content_type   TEXT,
    status_code    INTEGER,
    etag           TEXT,
    last_modified  TEXT,
    raw_sha256     TEXT,
    tier           TEXT,
    fetched_at     TEXT NOT NULL,
    state          TEXT NOT NULL,
    error          TEXT,
    attempts       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_fetches_state     ON fetches(state);
CREATE INDEX IF NOT EXISTS idx_fetches_source    ON fetches(source_id);
CREATE INDEX IF NOT EXISTS idx_fetches_raw_path  ON fetches(raw_path);
"""

_COLUMNS = [
    "url", "source_id", "final_url", "raw_path", "content_type", "status_code",
    "etag", "last_modified", "raw_sha256", "tier", "fetched_at", "state",
    "error", "attempts",
]


def _now() -> str:
    return datetime.now(UTC).isoformat()


class FetchDB:
    """Thin wrapper over the `fetches` table."""

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
    def _upsert(self, row: dict) -> None:
        row = {col: row.get(col) for col in _COLUMNS}
        row["attempts"] = row["attempts"] or 0
        placeholders = ", ".join(f":{c}" for c in _COLUMNS)
        updates = ", ".join(f"{c}=excluded.{c}" for c in _COLUMNS if c != "url")
        self.conn.execute(
            f"INSERT INTO fetches ({', '.join(_COLUMNS)}) VALUES ({placeholders}) "
            f"ON CONFLICT(url) DO UPDATE SET {updates}",
            row,
        )
        self.conn.commit()

    def _next_attempts(self, url: str) -> int:
        row = self.get(url)
        return ((row["attempts"] or 0) if row else 0) + 1

    def record_ok(
        self,
        url: str,
        source_id: str,
        *,
        raw_path: str | Path,
        raw_sha256: str,
        tier: str,
        status_code: int = 200,
        final_url: str | None = None,
        content_type: str | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> None:
        """Record a successful fetch whose body is now archived."""
        self._upsert({
            "url": url,
            "source_id": source_id,
            "final_url": final_url or url,
            "raw_path": str(raw_path),
            "content_type": content_type,
            "status_code": status_code,
            "etag": etag,
            "last_modified": last_modified,
            "raw_sha256": raw_sha256,
            "tier": tier,
            "fetched_at": _now(),
            "state": "ok",
            "error": None,
            "attempts": self._next_attempts(url),
        })

    def record_not_modified(self, url: str, *, etag: str | None = None,
                            last_modified: str | None = None) -> None:
        """Record a 304: the archived copy stands, so keep every column describing it.

        Only the freshness fields move. Overwriting `raw_path`/`raw_sha256` here would
        orphan a perfectly good archive entry.
        """
        row = self.get(url)
        if row is None:
            raise KeyError(f"304 for a URL that was never fetched: {url!r}")
        merged = dict(row)
        merged.update({
            "state": "not_modified",
            "status_code": 304,
            "fetched_at": _now(),
            "error": None,
            "attempts": self._next_attempts(url),
            "etag": etag or row["etag"],
            "last_modified": last_modified or row["last_modified"],
        })
        self._upsert(merged)

    def record_error(self, url: str, source_id: str, *, error: str,
                     status_code: int | None = None, tier: str | None = None) -> None:
        """Record a failed fetch, preserving any archived copy from an earlier success."""
        row = self.get(url)
        self._upsert({
            "url": url,
            "source_id": source_id,
            "raw_path": row["raw_path"] if row else None,
            "raw_sha256": row["raw_sha256"] if row else None,
            "etag": row["etag"] if row else None,
            "last_modified": row["last_modified"] if row else None,
            "status_code": status_code,
            "tier": tier,
            "fetched_at": _now(),
            "state": "fetch_error",
            "error": error,
            "attempts": self._next_attempts(url),
        })

    def record_skipped(self, url: str, source_id: str, *, reason: str) -> None:
        """Record a URL we deliberately did not request (robots, dry run, cap).

        `attempts` is left alone — we never asked the server for anything.
        """
        row = self.get(url)
        self._upsert({
            "url": url,
            "source_id": source_id,
            "fetched_at": _now(),
            "state": "skipped",
            "error": reason,
            "attempts": (row["attempts"] if row else 0),
        })

    # -- reads -----------------------------------------------------------
    def get(self, url: str) -> dict | None:
        cur = self.conn.execute("SELECT * FROM fetches WHERE url = ?", (url,))
        row = cur.fetchone()
        return dict(row) if row else None

    def validators(self, url: str) -> tuple[str | None, str | None]:
        """`(etag, last_modified)` for a conditional GET, or `(None, None)`.

        Only offered when the archived body is actually still on disk — revalidating
        against a file we no longer have would turn a 304 into a permanent gap.
        """
        row = self.get(url)
        if row is None or not row["raw_path"] or not Path(row["raw_path"]).exists():
            return None, None
        return row["etag"], row["last_modified"]

    def raw_path_owners(self, source_id: str | None = None) -> dict[str, str]:
        """{raw_path: url} — the collision check's input (see rawstore.claimed_by)."""
        sql = "SELECT url, raw_path FROM fetches WHERE raw_path IS NOT NULL"
        params: tuple = ()
        if source_id is not None:
            sql += " AND source_id = ?"
            params = (source_id,)
        return {r["raw_path"]: r["url"] for r in self.conn.execute(sql, params)}

    def urls(self, *, source_id: str | None = None, state: str | None = None) -> list[str]:
        clauses, params = [], []
        if source_id is not None:
            clauses.append("source_id = ?")
            params.append(source_id)
        if state is not None:
            clauses.append("state = ?")
            params.append(state)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        return [r["url"] for r in self.conn.execute(f"SELECT url FROM fetches{where} ORDER BY url", params)]

    def counts(self, *, source_id: str | None = None) -> dict[str, int]:
        """Rows per state — the backbone of the per-run summary (PLAN.md §10)."""
        sql = "SELECT state, COUNT(*) AS n FROM fetches"
        params: tuple = ()
        if source_id is not None:
            sql += " WHERE source_id = ?"
            params = (source_id,)
        sql += " GROUP BY state"
        counts = Counter({state: 0 for state in STATES})
        for row in self.conn.execute(sql, params):
            counts[row["state"]] = row["n"]
        return dict(counts)

    def archived_bytes(self) -> int:
        """Total on-disk size of the archive entries this DB knows about."""
        total = 0
        for row in self.conn.execute("SELECT raw_path FROM fetches WHERE raw_path IS NOT NULL"):
            path = Path(row["raw_path"])
            if path.exists():
                total += path.stat().st_size
        return total
