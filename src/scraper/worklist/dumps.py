"""Read committed sitemap dump files. Offline, deterministic. See PLAN.md §5.

Dump format, one URL per line, as produced for the v1 corpus:

    2024-05-19  https://platform.claude.com/cookbook/capabilities-classification-guide
    ----------  https://platform.claude.com/cookbook/

The first column is the sitemap `lastmod`, or `----------` when the sitemap carried none.
In practice almost every line is undated — 94 of 2,929 Anthropic URLs and 0 of 37,689
Databricks URLs — which is why `lastmod` is recorded but never load-bearing (PLAN.md §2e).
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from .sitemap import DiscoveredURL

logger = logging.getLogger(__name__)

_NO_DATE = "-"


def parse_line(line: str) -> DiscoveredURL | None:
    """Parse one dump line. Returns None for blanks, comments, and malformed rows."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = line.split(None, 1)
    if len(parts) == 1:
        # Bare URL, no lastmod column.
        return DiscoveredURL(parts[0], None) if _looks_like_url(parts[0]) else None

    stamp, url = parts[0], parts[1].strip()
    if not _looks_like_url(url):
        logger.debug("skipping malformed dump line: %r", line)
        return None

    return DiscoveredURL(url, _parse_stamp(stamp))


def _looks_like_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def _parse_stamp(stamp: str) -> date | None:
    if not stamp or stamp.startswith(_NO_DATE):
        return None
    try:
        return date.fromisoformat(stamp)
    except ValueError:
        logger.debug("unrecognized dump lastmod: %r", stamp)
        return None


def read(path: str | Path) -> list[DiscoveredURL]:
    """Read a dump file into DiscoveredURLs, de-duplicated, order preserved.

    Raises FileNotFoundError if the dump is missing — a stale `seeds` path should fail
    loudly rather than silently yielding an empty worklist.
    """
    path = Path(path)
    found: dict[str, DiscoveredURL] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        item = parse_line(line)
        if item is not None:
            found.setdefault(item.url, item)
    logger.info("dump %s: %d URLs", path, len(found))
    return list(found.values())
