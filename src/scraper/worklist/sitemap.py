"""Sitemap collection: sitemap.xml (+ sitemap-index) -> URL list. See PLAN.md §5.

Deterministic and side-effect free apart from the fetches themselves. Sitemap documents
are metadata, not page content — the page fetchers in `scraper.fetch` are rate-limited
separately (PLAN.md §6.2).
"""

from __future__ import annotations

import gzip
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import TYPE_CHECKING, NamedTuple

import httpx

if TYPE_CHECKING:
    from .robots import RobotsCache

logger = logging.getLogger(__name__)

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


def _get(client: httpx.Client, url: str) -> tuple[bytes, str] | None:
    """Fetch a URL, returning (decompressed bytes, final URL) or None on any error.

    The final URL matters: `docs.databricks.com/sitemap.xml` 301s to
    `/aws/en/sitemap.xml`, which robots.txt *also* declares — without comparing
    post-redirect URLs we would request the same document twice every run.
    """
    try:
        resp = client.get(url)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("fetch failed for %s: %s", url, exc)
        return None
    return _maybe_gunzip(resp.content), str(resp.url)


def collect(
    sitemap_urls: list[str],
    *,
    client: httpx.Client | None = None,
    robots: RobotsCache | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    user_agent: str = "claude-scraper",
) -> list[DiscoveredURL]:
    """Collect URLs from the given sitemaps, plus any the hosts' robots.txt declares.

    Follows sitemap-index files exactly one level deep. Deduplicates by URL. Never
    raises for network/parse errors on individual documents — it logs and skips, so one
    unreachable sitemap cannot take down a multi-source run.
    """
    if not sitemap_urls:
        return []

    own_client = client is None
    if client is None:
        client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": user_agent},
        )

    try:
        declared: list[str] = []
        if robots is not None:
            # robots.txt is already being fetched for its rules; reuse it rather than
            # asking the same host for the same file twice.
            for url in sitemap_urls:
                declared.extend(robots.sitemaps_for(url))

        results: dict[str, DiscoveredURL] = {}
        seen: set[str] = set()

        def fetch_once(url: str) -> bytes | None:
            """Fetch a sitemap unless we already have it, before or after redirects."""
            if url in seen:
                return None
            seen.add(url)
            got = _get(client, url)
            if got is None:
                return None
            content, final_url = got
            if final_url != url and final_url in seen:
                logger.debug("%s redirects to already-fetched %s", url, final_url)
                return None
            seen.add(final_url)
            return content

        for seed in dict.fromkeys(sitemap_urls + declared):
            content = fetch_once(seed)
            if content is None:
                continue
            child_sitemaps, urls = _parse_sitemap(content)
            for found in urls:
                results[found.url] = found

            # Follow index entries one level only.
            for child in child_sitemaps:
                child_content = fetch_once(child)
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
