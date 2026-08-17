"""Filter a discovered URL work-list. Deterministic, offline. See PLAN.md §5.

Filters applied, in order:
  1. path include (keep only URLs whose path matches an include prefix, if any)
  2. path exclude (drop URLs matching an exclude prefix; wins over include)
  3. date window against the sitemap ``lastmod`` (URLs with unknown lastmod are kept —
     in practice that is nearly all of them, see PLAN.md §2e)

``max_pages`` is deliberately *not* applied here. It is applied last, by
``worklist.build``, after the robots check — capping first would spend the budget on
URLs that are then dropped, so `--limit 50` could yield far fewer than 50 pages.
"""

from __future__ import annotations

from urllib.parse import urlparse

from ..config import Filters, SourceConfig
from .sitemap import DiscoveredURL


def _path_matches(path: str, prefixes: list[str]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def in_scope(url: str, source: SourceConfig) -> bool:
    """Whether a URL's path passes this source's include/exclude prefixes."""
    path = urlparse(url).path
    if source.include_paths and not _path_matches(path, source.include_paths):
        return False
    return not (source.exclude_paths and _path_matches(path, source.exclude_paths))


def apply(
    urls: list[DiscoveredURL],
    source: SourceConfig,
    filters: Filters,
) -> list[DiscoveredURL]:
    """Return the filtered work-list, preserving each URL's lastmod."""
    result: list[DiscoveredURL] = []

    for item in urls:
        if not in_scope(item.url, source):
            continue

        # Date window: only judge URLs that actually carry a lastmod. Unknown -> keep.
        if item.lastmod is not None:
            if filters.published_after and item.lastmod < filters.published_after:
                continue
            if filters.published_before and item.lastmod > filters.published_before:
                continue

        result.append(item)

    return result
