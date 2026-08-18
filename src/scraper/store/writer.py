"""Write an `Extracted` page as Markdown: YAML frontmatter + body. See PLAN.md §7.

One file per page. The frontmatter is what you query and organise by; the body is what you
read. Writes are idempotent — the same page always lands at the same path with the same
bytes — and `parse` round-trips the frontmatter so the index can be rebuilt from the
files alone.
"""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path

import yaml

from ..records import Extracted


def content_hash(markdown: str) -> str:
    """sha256 of the body — drives change detection for the corpus (PLAN.md §8)."""
    return hashlib.sha256(markdown.encode("utf-8")).hexdigest()


def build_frontmatter(record: Extracted, extracted_at: datetime) -> dict:
    """The ordered metadata block written above the body.

    Dates stay as `date` objects so YAML emits them unquoted and they round-trip.
    """
    front = {
        "title": record.title,
        "company": record.company,
        "source_id": record.source_id,
        "category": record.category,
        "description": record.description,
        "published_date": record.published_date,
        "updated_date": record.updated_date,
        "source_url": record.source_url,
        "canonical_url": record.canonical_url,
        "breadcrumbs": list(record.breadcrumbs),
        "code_languages": list(record.code_languages),
        "extractor": f"{record.extractor}@{record.extractor_version}",
        "content_hash": content_hash(record.markdown),
        "extracted_at": extracted_at.isoformat(timespec="seconds"),
    }
    return {k: v for k, v in front.items() if v not in (None, [], "")}


def render(record: Extracted, extracted_at: datetime | None = None) -> str:
    extracted_at = extracted_at or datetime.now(UTC)
    front = yaml.safe_dump(
        build_frontmatter(record, extracted_at),
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )
    return f"---\n{front}---\n\n{record.markdown.strip()}\n"


def path_for_record(record: Extracted, base_dir: Path | None = None) -> Path:
    """Where this record *would* be written — used to spot two URLs claiming one file."""
    from . import layout

    return layout.path_for(record, base_dir)


def write(
    record: Extracted,
    base_dir: Path | None = None,
    *,
    extracted_at: datetime | None = None,
) -> Path:
    """Write the page to its computed path, atomically. Returns the path written."""
    from . import layout

    path = layout.path_for(record, base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(render(record, extracted_at), encoding="utf-8")
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return path


def parse(path: str | Path) -> tuple[dict, str]:
    """Split a stored file into `(frontmatter, body)`. Returns `({}, text)` if absent."""
    text = Path(path).read_text(encoding="utf-8")
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) == 3:
            _, front_text, body = parts
            return (yaml.safe_load(front_text) or {}), body.lstrip("\n")
    return {}, text
