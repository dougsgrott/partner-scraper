"""Write a PageRecord as a Markdown file: YAML frontmatter (metadata) + body.

The metadata is *about* the body, never a replacement for it (PLAN.md §6). One file per
page; writes are idempotent. Frontmatter round-trips via `parse` so the SQLite index can
be rebuilt from the files alone.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import yaml

from ..ingest.schema import PageRecord


def content_hash(markdown: str) -> str:
    """sha256 of the body — the change-detection key used for dedup."""
    return hashlib.sha256(markdown.encode("utf-8")).hexdigest()


def build_frontmatter(record: PageRecord, url: str, fetched_at: datetime) -> dict:
    """The ordered metadata block written above the body.

    Dates are stored as native date objects so YAML emits them unquoted (2026-02-11)
    and they round-trip back to date on parse.
    """
    return {
        "title": record.title,
        "company": record.company,
        "theme": record.theme,
        "content_type": record.content_type,
        "published_date": record.published_date,
        "updated_date": record.updated_date,
        "summary": record.summary,
        "source_url": url,
        "key_entities": list(record.key_entities),
        "content_hash": content_hash(record.markdown),
        "fetched_at": fetched_at.isoformat(),
    }


def render(record: PageRecord, url: str, fetched_at: datetime) -> str:
    """Serialize to the frontmatter + body text form."""
    fm = build_frontmatter(record, url, fetched_at)
    front = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True)
    return f"---\n{front}---\n\n{record.markdown.rstrip()}\n"


def write(
    record: PageRecord,
    url: str,
    base_dir: Path | None = None,
    *,
    fetched_at: datetime | None = None,
) -> Path:
    """Write the page to its computed path. Returns the path written."""
    from . import layout  # local import avoids a module-load cycle

    fetched_at = fetched_at or datetime.now(UTC)
    path = layout.path_for(record, url, base_dir or layout.DEFAULT_DATA_DIR)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(record, url, fetched_at), encoding="utf-8")
    return path


def parse(path: Path) -> tuple[dict, str]:
    """Split a stored file into (frontmatter dict, body). Returns ({}, text) if no front."""
    text = Path(path).read_text(encoding="utf-8")
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) == 3:
            _, front_text, body = parts
            return (yaml.safe_load(front_text) or {}), body.lstrip("\n")
    return {}, text
