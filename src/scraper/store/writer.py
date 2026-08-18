"""Write an `Extracted` page as Markdown: YAML frontmatter + body. See PLAN.md §7.

One file per page. The frontmatter is what you query and organise by; the body is what you
read, and `parse` round-trips the frontmatter so the index can be rebuilt from the files
alone.

**Writes are idempotent at the byte level.** Re-extracting a page whose content has not
changed leaves the file untouched — same bytes, same mtime. That matters because
re-extraction is the normal way to fix an extractor (§8): a `--force` pass over the whole
corpus must not present 6,000 modified files to git, rsync, or an embedding pipeline when
nothing was actually said differently. The only volatile field, `extracted_at`, is
therefore carried over from the existing file rather than restamped.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml

from ..records import Extracted

# Written to the file but ignored when deciding whether the file changed.
VOLATILE_KEYS = ("extracted_at",)


@dataclass(frozen=True)
class WriteResult:
    """What `write` did. `extracted_at` is the stamp now *in the file*."""

    path: Path
    changed: bool
    extracted_at: datetime


def content_hash(markdown: str) -> str:
    """sha256 of the body — drives change detection for the corpus (PLAN.md §8)."""
    return hashlib.sha256(markdown.encode("utf-8")).hexdigest()


def build_frontmatter(record: Extracted, extracted_at: datetime) -> dict:
    """The ordered metadata block written above the body.

    Dates stay as `date` objects so YAML emits them unquoted and they round-trip.
    `raw_sha256` names the archived bytes this file was parsed from, which makes the
    file self-describing: `Index.rebuild` can restore the change-detection state from
    `data/` alone, without consulting `fetch.db`.
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
        "raw_sha256": record.raw_sha256,
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


def unchanged_stamp(path: Path, record: Extracted) -> datetime | None:
    """The existing file's `extracted_at` if it already holds exactly this page.

    Returns `None` when the file is absent, unreadable, or differs in any field that is
    not volatile — i.e. when it genuinely needs rewriting.
    """
    if not path.exists():
        return None
    try:
        front, body = parse(path)
        stamp = datetime.fromisoformat(str(front.get("extracted_at")))
    except (OSError, ValueError, yaml.YAMLError):
        return None

    if body.strip() != record.markdown.strip():
        return None
    candidate = build_frontmatter(record, stamp)
    return stamp if _stable(front) == _stable(candidate) else None


def _stable(front: dict) -> dict:
    return {k: v for k, v in front.items() if k not in VOLATILE_KEYS}


def write(
    record: Extracted,
    base_dir: Path | None = None,
    *,
    extracted_at: datetime | None = None,
) -> WriteResult:
    """Write the page to its computed path, atomically, unless it is already there."""
    from . import layout

    path = layout.path_for(record, base_dir)

    kept = unchanged_stamp(path, record)
    if kept is not None:
        return WriteResult(path, changed=False, extracted_at=kept)

    # Second precision, matching what the file stores, so the returned stamp is exactly
    # what a reader will parse back out of it.
    stamp = (extracted_at or datetime.now(UTC)).replace(microsecond=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(render(record, stamp), encoding="utf-8")
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return WriteResult(path, changed=True, extracted_at=stamp)


def remove(path: str | Path, base_dir: Path | None = None) -> None:
    """Delete a corpus file and any directories it leaves empty behind it."""
    from . import layout

    path = Path(path)
    base = Path(base_dir or layout.DEFAULT_DATA_DIR).resolve()
    path.unlink(missing_ok=True)

    parent = path.resolve().parent
    while parent != base and base in parent.parents:
        if any(parent.iterdir()):
            break
        parent.rmdir()
        parent = parent.parent


def parse(path: str | Path) -> tuple[dict, str]:
    """Split a stored file into `(frontmatter, body)`. Returns `({}, text)` if absent."""
    text = Path(path).read_text(encoding="utf-8")
    if text.startswith("---\n"):
        parts = text.split("---\n", 2)
        if len(parts) == 3:
            _, front_text, body = parts
            return (yaml.safe_load(front_text) or {}), body.lstrip("\n")
    return {}, text
