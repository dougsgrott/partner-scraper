"""Capture the corpus as it stands right now. See docs/changefeed-plan.md.

A snapshot is one row in `snapshots` plus one `page_versions` row per corpus page, with
each page's body filed in the content-addressed store. Taking one touches no network and
rewrites nothing in `data/`.

**The snapshot verifies as it captures.** Every body is re-hashed and compared against the
`content_hash` its own frontmatter states. That check is free — the body is already in
hand — and it catches the one failure that would otherwise corrupt a diff silently: a file
edited underneath the index, so that the corpus and the manifest disagree about what a page
says. A diff built on a mismatched pair reports a change that never happened, or misses one
that did.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from scraper.store import writer
from scraper.store.index import Index

from . import blobs
from .db import ChangeDB

logger = logging.getLogger(__name__)


@dataclass
class SnapshotResult:
    """What `take` recorded."""

    snapshot_id: int
    label: str | None
    pages: int = 0
    new_blobs: int = 0
    bytes_added: int = 0
    missing_files: list[str] = field(default_factory=list)
    hash_mismatches: list[str] = field(default_factory=list)

    def render(self) -> str:
        name = f"#{self.snapshot_id}" + (f" ({self.label})" if self.label else "")
        lines = [
            f"snapshot {name}",
            f"  pages            {self.pages}",
            f"  new bodies       {self.new_blobs}  ({self.bytes_added / 1024:.0f} KiB added)",
        ]
        if self.missing_files:
            lines.append(f"  missing files    {len(self.missing_files)}  "
                         f"(indexed but not on disk; first: {self.missing_files[0]})")
        if self.hash_mismatches:
            lines.append(f"  hash mismatches  {len(self.hash_mismatches)}  "
                         f"(file disagrees with its frontmatter; first: {self.hash_mismatches[0]})")
        if not self.new_blobs and self.pages:
            lines.append("  nothing changed since the last snapshot")
        return "\n".join(lines)


def take(
    *,
    label: str | None = None,
    note: str | None = None,
    index_db: str | Path | None = None,
    changes_db: str | Path | None = None,
    blob_dir: str | Path | None = None,
    data_root: str | Path | None = None,
) -> SnapshotResult:
    """Record the current corpus state and return what was captured.

    `data_root` prefixes the relative `file_path` values the index stores, which are
    relative to whatever directory `extract` ran in. Supply it to snapshot a corpus that
    lives somewhere other than the current working directory.
    """
    index = Index(index_db) if index_db else Index()
    changes = ChangeDB(changes_db) if changes_db else ChangeDB()
    blob_dir = Path(blob_dir) if blob_dir else None
    data_root = Path(data_root) if data_root else None

    try:
        snapshot_id = changes.create_snapshot(label=label, note=note)
        result = SnapshotResult(snapshot_id=snapshot_id, label=label)
        rows: list[dict] = []

        for page in index.query(status="ok"):
            captured = _capture(page, blob_dir, data_root, result)
            if captured is not None:
                rows.append(captured)

        changes.add_versions(snapshot_id, rows)
        result.pages = changes.finish_snapshot(snapshot_id)
        return result
    finally:
        index.close()
        changes.close()


def _capture(
    page: dict,
    blob_dir: Path | None,
    data_root: Path | None,
    result: SnapshotResult,
) -> dict | None:
    """Store one page's body and build its `page_versions` row, or None if unreadable."""
    path = Path(page["file_path"] or "")
    if data_root is not None and not path.is_absolute():
        path = data_root / path
    if not path.exists():
        # The index points at a file that is gone — a `--prune` that did not run, or a
        # half-finished extract. Recorded rather than raised: one stale row must not
        # cost the whole snapshot.
        result.missing_files.append(str(path))
        return None

    try:
        front, body = writer.parse(path)
    except (OSError, ValueError) as exc:
        logger.warning("cannot read %s: %s", path, exc)
        result.missing_files.append(str(path))
        return None

    # The file is the source of truth, so the body's own hash is the address we store it
    # under — never the index's copy, which may be stale.
    content_hash = writer.content_hash(body)
    if front.get("content_hash") and front["content_hash"] != content_hash:
        result.hash_mismatches.append(str(path))

    if blobs.write(content_hash, body.strip(), blob_dir):
        result.new_blobs += 1
        result.bytes_added += blobs.path_for(content_hash, blob_dir).stat().st_size

    return {
        "url": page["url"],
        "company": page["company"],
        "source_id": page["source_id"],
        "category": page["category"],
        "title": page["title"],
        "description": page["description"],
        "updated_date": page["updated_date"],
        "content_hash": content_hash,
        # Not stated in the frontmatter — it lives only in the index. A rebuilt index
        # therefore has none, which `classify.attribute` handles explicitly rather than
        # guessing.
        "output_fingerprint": page["output_fingerprint"],
        "extractor": _extractor(page, front),
        "body_chars": len(body.strip()),
        "file_path": str(path),
    }


def _extractor(page: dict, front: dict) -> str | None:
    """`name@version`, preferring the index but falling back to the frontmatter.

    Worth the fallback: this is the only pipeline-identity signal that survives an index
    rebuild, and attribution degrades to guessing without it.
    """
    name, version = page.get("extractor"), page.get("extractor_version")
    if name and version:
        return f"{name}@{version}"
    return str(front.get("extractor")) if front.get("extractor") else None
