"""`state/graph.db` — the graph, its rankings, and the vocabularies mined alongside it.

Unlike `state/changes.db`, which holds history that cannot be reconstructed, everything
here is derived: `graph build` rebuilds the whole database from `data/` in about fifteen
seconds. It is therefore disposable, has no backup command, and old builds can be pruned
without losing anything.

**Every build records the formula that produced its scores.** `lessons-learned.md` §17b —
"a stored derived value carries its formula with it" — is not decoration here: a damping
factor or a deduplication rule changed between two builds makes their `pagerank` columns
incomparable while leaving them looking identical. The same row records a `corpus_stamp`,
so a build also knows which corpus it described and is not silently compared against one
taken after a re-extraction.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Self

from scraper.db import connect

DEFAULT_DB_PATH = Path("state/graph.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS builds (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    built_at     TEXT NOT NULL,
    label        TEXT,
    pages        INTEGER NOT NULL,
    edges        INTEGER NOT NULL,       -- distinct internal (src, dst) pairs
    occurrences  INTEGER NOT NULL,       -- link instances behind them
    formula      TEXT NOT NULL,          -- how the scores below were computed
    corpus_stamp TEXT NOT NULL,          -- which corpus they describe
    buckets      TEXT NOT NULL,          -- JSON: everything that was not an edge
    note         TEXT
);

-- One row per ordered pair, never per occurrence. `occurrences` is kept only so a report
-- can show why the two inbound counts disagree; no algorithm reads it.
CREATE TABLE IF NOT EXISTS edges (
    build_id    INTEGER NOT NULL,
    src         TEXT NOT NULL,
    dst         TEXT NOT NULL,
    occurrences INTEGER NOT NULL,
    sections    INTEGER NOT NULL,        -- how many named a #fragment
    anchors     TEXT,                    -- JSON {anchor: count}, the head of the tail
    PRIMARY KEY (build_id, src, dst)
);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(build_id, dst);

CREATE TABLE IF NOT EXISTS nodes (
    build_id       INTEGER NOT NULL,
    url            TEXT NOT NULL,
    company        TEXT,
    category       TEXT,
    title          TEXT,
    body_chars     INTEGER,
    updated_date   TEXT,
    breadcrumbs    TEXT,                 -- JSON list
    code_languages TEXT,                 -- JSON list
    in_pages       INTEGER NOT NULL,     -- distinct linking pages
    in_refs        INTEGER NOT NULL,     -- link occurrences
    out_pages      INTEGER NOT NULL,
    pagerank       REAL,
    authority      REAL,
    hub            REAL,
    depth          INTEGER,              -- NULL means unreachable, not far away
    PRIMARY KEY (build_id, url)
);
CREATE INDEX IF NOT EXISTS idx_nodes_rank ON nodes(build_id, pagerank DESC);
CREATE INDEX IF NOT EXISTS idx_nodes_cat  ON nodes(build_id, company, category);

-- One vocabulary table discriminated by `kind`: the five sources differ only in where
-- they come from. `parent` is '' rather than NULL because it is in the primary key.
CREATE TABLE IF NOT EXISTS terms (
    build_id INTEGER NOT NULL,
    kind     TEXT NOT NULL,
    term     TEXT NOT NULL,
    parent   TEXT NOT NULL,
    company  TEXT NOT NULL,
    pages    INTEGER NOT NULL,
    refs     INTEGER NOT NULL,
    PRIMARY KEY (build_id, kind, company, parent, term)
);
CREATE INDEX IF NOT EXISTS idx_terms_kind ON terms(build_id, kind, pages DESC);
"""

# Added columns must be nullable, and nothing is ever dropped — the `changefeed.db`
# pattern, not `index.py`'s replace-the-table one. No other stage rebuilds this file.
_ADDED_BUILD_COLUMNS: tuple[tuple[str, str], ...] = ()

TERM_KINDS = ("category", "breadcrumb", "tag", "code_language", "author", "anchor",
              "external_host")
RANK_COLUMNS = ("pagerank", "authority", "hub", "in_pages", "in_refs", "out_pages")

EDGE_COLUMNS = ("build_id", "src", "dst", "occurrences", "sections", "anchors")
NODE_COLUMNS = ("build_id", "url", "company", "category", "title", "body_chars",
                "updated_date", "breadcrumbs", "code_languages", "in_pages", "in_refs",
                "out_pages", "pagerank", "authority", "hub", "depth")
TERM_COLUMNS = ("build_id", "kind", "term", "parent", "company", "pages", "refs")


@dataclass(frozen=True)
class Build:
    id: int
    built_at: str
    label: str | None
    pages: int
    edges: int
    occurrences: int
    formula: str
    corpus_stamp: str
    buckets: dict
    note: str | None = None

    @property
    def name(self) -> str:
        return f"#{self.id}" + (f" ({self.label})" if self.label else "")


def corpus_stamp(index_db: str | Path = "state/index.db") -> str:
    """A fingerprint of the corpus a build described.

    Over `(url, content_hash)` rather than file mtimes, so it changes when the corpus
    changes and not when it is merely re-read — `lessons-learned.md` §8's reason for
    keeping volatile values out of anything that gets compared.
    """
    path = Path(index_db)
    if not path.exists():
        return "no-index"
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = sorted(conn.execute(
            "SELECT url, content_hash FROM pages WHERE status = 'ok'"))
    finally:
        conn.close()
    digest = hashlib.sha256()
    for url, content in rows:
        digest.update(f"{url}\t{content}\n".encode())
    return digest.hexdigest()[:16]


class GraphDB:
    """Thin wrapper over `state/graph.db`."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = connect(self.path)
        self.conn.executescript(_SCHEMA)
        self._migrate()
        self.conn.commit()

    def _migrate(self) -> None:
        cols = {r["name"] for r in self.conn.execute("PRAGMA table_info(builds)")}
        for column, ddl in _ADDED_BUILD_COLUMNS:
            if cols and column not in cols:
                self.conn.execute(f"ALTER TABLE builds ADD COLUMN {column} {ddl}")
                self.conn.commit()

    # -- context manager -------------------------------------------------
    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self.conn.close()

    # -- writes ----------------------------------------------------------
    def create_build(self, *, pages: int, edges: int, occurrences: int, formula: str,
                     stamp: str, buckets: dict, label: str | None = None,
                     note: str | None = None) -> int:
        cursor = self.conn.execute(
            "INSERT INTO builds (built_at, label, pages, edges, occurrences, formula, "
            "corpus_stamp, buckets, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (datetime.now(UTC).isoformat(timespec="seconds"), label, pages, edges,
             occurrences, formula, stamp, json.dumps(buckets, sort_keys=True), note),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def _bulk(self, table: str, columns: tuple[str, ...], rows: list[dict]) -> None:
        """One `executemany` and one commit — 40,000 separate commits is minutes."""
        if not rows:
            return
        placeholders = ", ".join(f":{c}" for c in columns)
        self.conn.executemany(
            f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            [{c: r.get(c) for c in columns} for rows_ in (rows,) for r in rows_],
        )
        self.conn.commit()

    def add_edges(self, rows: list[dict]) -> None:
        self._bulk("edges", EDGE_COLUMNS, rows)

    def add_nodes(self, rows: list[dict]) -> None:
        self._bulk("nodes", NODE_COLUMNS, rows)

    def add_terms(self, rows: list[dict]) -> None:
        self._bulk("terms", TERM_COLUMNS, rows)

    def delete_build(self, build_id: int) -> None:
        for table in ("edges", "nodes", "terms"):
            self.conn.execute(f"DELETE FROM {table} WHERE build_id = ?", (build_id,))
        self.conn.execute("DELETE FROM builds WHERE id = ?", (build_id,))
        self.conn.commit()

    def prune(self, keep: int) -> list[int]:
        """Drop all but the `keep` most recent builds. Returns the ids removed."""
        ids = [b.id for b in self.builds()][keep:]
        for build_id in ids:
            self.delete_build(build_id)
        return ids

    # -- reads -----------------------------------------------------------
    def _build(self, row) -> Build:
        data = dict(row)
        data["buckets"] = json.loads(data["buckets"])
        return Build(**data)

    def builds(self) -> list[Build]:
        """Newest first."""
        return [self._build(r) for r in
                self.conn.execute("SELECT * FROM builds ORDER BY id DESC")]

    def build(self, build_id: int) -> Build | None:
        row = self.conn.execute("SELECT * FROM builds WHERE id = ?", (build_id,)).fetchone()
        return self._build(row) if row else None

    def resolve(self, ref: str | int | None) -> Build | None:
        """`None`/`latest` -> newest; an integer -> that id; anything else -> a label."""
        if ref in (None, "latest"):
            return next(iter(self.builds()), None)
        try:
            return self.build(int(ref))
        except (TypeError, ValueError):
            pass
        row = self.conn.execute(
            "SELECT * FROM builds WHERE label = ? ORDER BY id DESC LIMIT 1", (ref,)).fetchone()
        return self._build(row) if row else None

    def top(self, build_id: int, *, by: str = "pagerank", limit: int = 20,
            company: str | None = None, category: str | None = None) -> list[dict]:
        if by not in RANK_COLUMNS:
            raise ValueError(f"unknown ranking column {by!r}; expected one of {RANK_COLUMNS}")
        sql = f"SELECT * FROM nodes WHERE build_id = ? AND {by} IS NOT NULL"
        params: list = [build_id]
        if company:
            sql += " AND company = ?"
            params.append(company)
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += f" ORDER BY {by} DESC, url LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self.conn.execute(sql, params)]

    def rank_of(self, build_id: int, url: str, *, by: str = "pagerank") -> int | None:
        """1-based position of `url` in the whole build, or None if it has no score."""
        if by not in RANK_COLUMNS:
            raise ValueError(f"unknown ranking column {by!r}")
        row = self.conn.execute(
            f"SELECT COUNT(*) + 1 AS n FROM nodes WHERE build_id = ? AND {by} > "
            f"(SELECT {by} FROM nodes WHERE build_id = ? AND url = ?)",
            (build_id, build_id, url)).fetchone()
        return int(row["n"]) if row and row["n"] is not None else None

    def node(self, build_id: int, url: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM nodes WHERE build_id = ? AND url = ?",
                                (build_id, url)).fetchone()
        return dict(row) if row else None

    def inbound(self, build_id: int, url: str, *, limit: int = 20) -> list[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT e.src AS url, e.occurrences, e.anchors, n.title, n.pagerank "
            "FROM edges e LEFT JOIN nodes n ON n.build_id = e.build_id AND n.url = e.src "
            "WHERE e.build_id = ? AND e.dst = ? ORDER BY n.pagerank DESC, e.src LIMIT ?",
            (build_id, url, limit))]

    def outbound(self, build_id: int, url: str, *, limit: int = 20) -> list[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT e.dst AS url, e.occurrences, e.anchors, n.title, n.pagerank "
            "FROM edges e LEFT JOIN nodes n ON n.build_id = e.build_id AND n.url = e.dst "
            "WHERE e.build_id = ? AND e.src = ? ORDER BY n.pagerank DESC, e.dst LIMIT ?",
            (build_id, url, limit))]

    def anchors_for(self, build_id: int, url: str) -> list[tuple[str, int]]:
        """Every distinct text the corpus uses to refer to a page, commonest first."""
        counts: dict[str, int] = {}
        for (blob,) in self.conn.execute(
                "SELECT anchors FROM edges WHERE build_id = ? AND dst = ? AND anchors IS NOT NULL",
                (build_id, url)):
            for anchor, n in json.loads(blob).items():
                counts[anchor] = counts.get(anchor, 0) + n
        return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    def terms(self, build_id: int, *, kind: str | None = None, company: str | None = None,
              parent: str | None = None, limit: int = 50) -> list[dict]:
        sql = "SELECT * FROM terms WHERE build_id = ?"
        params: list = [build_id]
        for column, value in (("kind", kind), ("company", company), ("parent", parent)):
            if value is not None:
                sql += f" AND {column} = ?"
                params.append(value)
        sql += " ORDER BY pages DESC, refs DESC, term LIMIT ?"
        params.append(limit)
        return [dict(r) for r in self.conn.execute(sql, params)]

    def counts(self, build_id: int) -> dict[str, int]:
        out = {}
        for table in ("edges", "nodes", "terms"):
            out[table] = self.conn.execute(
                f"SELECT COUNT(*) AS n FROM {table} WHERE build_id = ?",
                (build_id,)).fetchone()["n"]
        return out
