"""Build the on-disk path for a corpus page. See PLAN.md §7.3.

    data/{company}/{category}/{YYYY-MM}/{slug}.md

`category` comes from the URL path (`scraper.category`), not from a model's judgement, so
the same page lands in the same place on every run — re-extraction overwrites in place
instead of accumulating near-duplicates under drifting folder names.
"""

from __future__ import annotations

from pathlib import Path

from ..category import slug_for
from ..records import Extracted

DEFAULT_DATA_DIR = Path("data")
UNDATED = "undated"


def date_bucket(record: Extracted) -> str:
    """`YYYY-MM` from the updated date, else the published date, else `undated`."""
    when = record.updated_date or record.published_date
    return when.strftime("%Y-%m") if when else UNDATED


def path_for(record: Extracted, base_dir: Path | None = None) -> Path:
    """Full destination path for an extracted page."""
    base = Path(base_dir or DEFAULT_DATA_DIR)
    return (
        base
        / _safe(record.company)
        / _safe(record.category)
        / date_bucket(record)
        / f"{slug_for(record.source_url)}.md"
    )


def _safe(segment: str) -> str:
    """Category labels come from URLs, so keep them to one safe path segment.

    A URL path segment can be anything the site publishes, including `..` — which would
    otherwise walk the corpus root. `fetch/rawstore.py` guards its own paths the same
    way, and for the same reason.
    """
    cleaned = segment.strip().strip("/").replace("/", "-").replace("\\", "-")
    if set(cleaned) <= {"."}:                     # "", ".", ".." — no usable name
        return "other"
    return cleaned
