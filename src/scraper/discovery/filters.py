"""Filter a discovered URL work-list. Deterministic, token-free. See PLAN.md §5.1.

Filters applied, in order:
  1. path include (keep only URLs whose path matches an include prefix, if any)
  2. path exclude (drop URLs matching an exclude prefix; wins over include)
  3. date window against the sitemap ``lastmod`` (URLs with unknown lastmod are kept —
     the real date is resolved later during ingest)
  4. ``max_pages`` cap
"""

from __future__ import annotations

from urllib.parse import urlparse

from ..config import Filters, SourceConfig
from .sitemap import DiscoveredURL


def _path_matches(path: str, prefixes: list[str]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def apply(
    urls: list[DiscoveredURL],
    source: SourceConfig,
    filters: Filters,
) -> list[DiscoveredURL]:
    """Return the filtered work-list, preserving each URL's lastmod."""
    result: list[DiscoveredURL] = []

    for item in urls:
        path = urlparse(item.url).path

        if source.include_paths and not _path_matches(path, source.include_paths):
            continue
        if source.exclude_paths and _path_matches(path, source.exclude_paths):
            continue

        # Date window: only judge URLs that actually carry a lastmod. Unknown -> keep.
        if item.lastmod is not None:
            if filters.published_after and item.lastmod < filters.published_after:
                continue
            if filters.published_before and item.lastmod > filters.published_before:
                continue

        result.append(item)

    if filters.max_pages is not None:
        result = result[: filters.max_pages]

    return result
