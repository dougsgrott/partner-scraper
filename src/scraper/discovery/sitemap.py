"""Sitemap discovery: robots.txt -> sitemap.xml -> URL list.

Fully deterministic and token-free. This is the only place we fetch over HTTP ourselves
(robots.txt + sitemap XML) — page *content* is fetched by Claude's web_fetch tool in the
ingest layer. See PLAN.md §5.1.
"""

from __future__ import annotations

import gzip
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import NamedTuple
from urllib.parse import urlparse

import httpx

from ..config import SourceConfig

logger = logging.getLogger(__name__)

_USER_AGENT = "claude-scraper/0.1 (+https://github.com/; docs sync)"
_DEFAULT_TIMEOUT = 30.0


class DiscoveredURL(NamedTuple):
    """A URL discovered from a sitemap, with its optional last-modified date."""

    url: str
    lastmod: date | None


def _maybe_gunzip(content: bytes) -> bytes:
    """Transparently decompress gzip-encoded sitemaps (.xml.gz)."""
    if content[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(content)
        except OSError as exc:  # pragma: no cover - corrupt gzip
            logger.warning("gzip decode failed: %s", exc)
    return content


def _parse_lastmod(text: str | None) -> date | None:
    """Parse a sitemap <lastmod> value (ISO date or datetime) into a date."""
    if not text:
        return None
    text = text.strip()
    try:
        return date.fromisoformat(text)
    except ValueError:
        pass
    try:
        # fromisoformat (3.11+) handles both "…+00:00" and the trailing-Z form.
        return datetime.fromisoformat(text).date()
    except ValueError:
        logger.debug("unrecognized lastmod value: %r", text)
        return None


def _localname(tag: str) -> str:
    """Strip an XML namespace, returning the bare tag name."""
    return tag.rsplit("}", 1)[-1]


def _parse_sitemap(content: bytes) -> tuple[list[str], list[DiscoveredURL]]:
    """Parse a sitemap document.

    Returns (child_sitemap_urls, discovered_urls). A <sitemapindex> yields child sitemap
    URLs; a <urlset> yields DiscoveredURLs. Malformed XML yields ([], []).
    """
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        logger.warning("sitemap parse error: %s", exc)
        return [], []

    children: list[str] = []
    urls: list[DiscoveredURL] = []
    for entry in root:
        kind = _localname(entry.tag)
        loc: str | None = None
        lastmod: date | None = None
        for field in entry:
            name = _localname(field.tag)
            if name == "loc":
                loc = (field.text or "").strip()
            elif name == "lastmod":
                lastmod = _parse_lastmod(field.text)
        if not loc:
            continue
        if kind == "sitemap":
            children.append(loc)
        elif kind == "url":
            urls.append(DiscoveredURL(loc, lastmod))
    return children, urls


def _get(client: httpx.Client, url: str) -> bytes | None:
    """Fetch a URL, returning decompressed bytes or None on any error."""
    try:
        resp = client.get(url)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("fetch failed for %s: %s", url, exc)
        return None
    return _maybe_gunzip(resp.content)


def _sitemaps_from_robots(client: httpx.Client, sitemap_urls: list[str]) -> list[str]:
    """Discover extra sitemap URLs from each host's robots.txt (Sitemap: directives)."""
    robots_urls: list[str] = []
    for raw in sitemap_urls:
        parsed = urlparse(raw)
        if parsed.scheme and parsed.netloc:
            robots_urls.append(f"{parsed.scheme}://{parsed.netloc}/robots.txt")

    found: list[str] = []
    for robots_url in dict.fromkeys(robots_urls):
        content = _get(client, robots_url)
        if not content:
            continue
        for line in content.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if line.lower().startswith("sitemap:"):
                found.append(line.split(":", 1)[1].strip())
    return found


def collect(
    source: SourceConfig,
    *,
    client: httpx.Client | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
) -> list[DiscoveredURL]:
    """Collect all URLs for a source from its sitemaps (+ robots.txt-declared ones).

    Follows sitemap-index files exactly one level deep. Deduplicates by URL. Never
    raises for network/parse errors on individual documents — it logs and skips.
    """
    own_client = client is None
    if client is None:
        client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        )

    try:
        seeds = list(dict.fromkeys(source.sitemaps + _sitemaps_from_robots(client, source.sitemaps)))
        results: dict[str, DiscoveredURL] = {}

        for seed in seeds:
            content = _get(client, seed)
            if content is None:
                continue
            child_sitemaps, urls = _parse_sitemap(content)
            for found in urls:
                results[found.url] = found

            # Follow index entries one level only.
            for child in child_sitemaps:
                child_content = _get(client, child)
                if child_content is None:
                    continue
                grandchildren, child_urls = _parse_sitemap(child_content)
                for found in child_urls:
                    results[found.url] = found
                if grandchildren:
                    logger.warning(
                        "sitemap %s nests %d further index entries; not following beyond one level",
                        child,
                        len(grandchildren),
                    )

        return list(results.values())
    finally:
        if own_client:
            client.close()
