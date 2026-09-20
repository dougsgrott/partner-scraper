"""Build the on-disk path for a corpus page. See PLAN.md §7.3.

    data/{company}/{category}/{slug}.md

`category` comes from the URL path (`scraper.category`), not from a model's judgement, so
the same page lands in the same place on every run — re-extraction overwrites in place
instead of accumulating near-duplicates under drifting folder names.

Until 2026-09-19 the path carried a `{YYYY-MM|undated}` segment keyed on the vendor's
`updated_date`. The 2026-09-11 Databricks re-date rewrote that field site-wide with no
content change and relocated 71% of the corpus in one event — a file's identity must not
include a field the vendor can rewrite at will (issue/accuracy/12, option A; migration:
docs/layout-migration-plan.md). The dates still live in the frontmatter and `index.db`,
which is where temporal queries belong.
"""

from __future__ import annotations

from pathlib import Path

from ..category import slug_for
from ..records import Extracted

DEFAULT_DATA_DIR = Path("data")


def path_for(record: Extracted, base_dir: Path | None = None) -> Path:
    """Full destination path for an extracted page."""
    base = Path(base_dir or DEFAULT_DATA_DIR)
    return (
        base
        / _safe(record.company)
        / _safe(record.category)
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
