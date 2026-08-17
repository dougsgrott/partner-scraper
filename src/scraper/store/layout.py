"""Build the on-disk path for a page: data/{company}/{theme}/{YYYY-MM}/{slug}.md.

Deterministic and idempotent — the same URL always maps to the same path, so re-runs
overwrite in place rather than accumulating duplicates. See PLAN.md §5.3.

Note: the slug is derived from the URL (not carried on PageRecord, which is the LLM
contract), so path_for takes the url explicitly.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from ..ingest.schema import PageRecord

DEFAULT_DATA_DIR = Path("data")
_UNDATED = "undated"


def _slugify(text: str) -> str:
    """Lowercase, collapse non-alphanumerics to single hyphens, trim. Empty -> 'index'."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "index"


def slug_for(url: str) -> str:
    """Stable slug from a URL's path (query/fragment dropped)."""
    return _slugify(urlparse(url).path.strip("/"))


def date_bucket(record: PageRecord) -> str:
    """'YYYY-MM' from updated_date (preferred) or published_date; else 'undated'."""
    d = record.updated_date or record.published_date
    return d.strftime("%Y-%m") if d else _UNDATED


def path_for(record: PageRecord, url: str, base_dir: Path = DEFAULT_DATA_DIR) -> Path:
    """Full destination path for a page."""
    return Path(base_dir) / record.company / record.theme / date_bucket(record) / f"{slug_for(url)}.md"
