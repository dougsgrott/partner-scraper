"""Discovery beyond the sitemap. See docs/validation-plan.md §5.

Sitemap-driven discovery has a ceiling, and phase 1 hit it: `/aws/en/agents/agent-evaluation`
and `/release-notes/runtime/eos` are live, in scope, and linked from pages we already
hold — and appear in no sitemap the site publishes. The corpus's own link graph is the
only index that knows about them.

This module turns that graph into candidate URLs. It never fetches pages; the optional
probe is a `HEAD` per candidate, because a link can also point at something that has since
been renamed or deleted (2 of the first 5 sampled were exactly that).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from ..config import AppConfig
from ..validate.coverage import archived_urls, classify_links, corpus_links
from .robots import RobotsCache
from .sitemap import DiscoveredURL

logger = logging.getLogger(__name__)


@dataclass
class Candidate:
    """A URL the corpus links to but does not contain."""

    url: str
    references: int
    status: int | None = None
    location: str | None = None

    @property
    def fetchable(self) -> bool:
        return self.status == 200

    @property
    def verdict(self) -> str:
        if self.status is None:
            return "unprobed"
        if self.status == 200:
            return "live"
        if self.status in (301, 302, 307, 308):
            return "redirect"
        if self.status in (404, 410):
            return "gone"
        return f"http {self.status}"


def discover(cfg: AppConfig, *, data_dir: str | Path = "data",
             fetch_db_path: str | Path = "state/fetch.db",
             respect_robots: bool = True) -> list[Candidate]:
    """In-scope pages the corpus links to but never archived, most-referenced first."""
    buckets = classify_links(cfg, corpus_links(data_dir), archived_urls(fetch_db_path))
    candidates = [Candidate(url, hits) for hits, url in buckets["candidate"]]

    if respect_robots and candidates:
        with httpx.Client(timeout=20, follow_redirects=True,
                          headers={"User-Agent": cfg.defaults.user_agent}) as client:
            robots = RobotsCache(client, user_agent=cfg.defaults.user_agent)
            allowed = [c for c in candidates if robots.allows(c.url)]
        if len(allowed) != len(candidates):
            logger.info("robots.txt disallows %d candidate(s)", len(candidates) - len(allowed))
        candidates = allowed
    return candidates


def probe(candidates: list[Candidate], *, user_agent: str, requests_per_second: float = 1.0,
          limit: int | None = None, timeout: float = 20.0) -> list[Candidate]:
    """`HEAD` each candidate to separate live pages from redirects and dead links.

    One request per candidate at the configured rate — the same politeness the fetcher
    uses, because this is the same servers.
    """
    interval = 1.0 / requests_per_second if requests_per_second else 0.0
    selected = candidates[:limit] if limit else candidates

    with httpx.Client(http2=True, follow_redirects=False, timeout=timeout,
                      headers={"User-Agent": user_agent}) as client:
        for candidate in selected:
            started = time.monotonic()
            try:
                response = client.head(candidate.url)
                candidate.status = response.status_code
                candidate.location = response.headers.get("location")
            except httpx.HTTPError as exc:
                logger.warning("probe failed for %s: %s", candidate.url, type(exc).__name__)
            elapsed = time.monotonic() - started
            if interval > elapsed:
                time.sleep(interval - elapsed)
    return selected


def as_dump(candidates: list[Candidate], *, only_live: bool = True) -> list[DiscoveredURL]:
    """Candidates as work-list entries, ready to write with `dumps.write`."""
    chosen = [c for c in candidates if c.fetchable] if only_live else candidates
    return [DiscoveredURL(c.url, None) for c in chosen]
