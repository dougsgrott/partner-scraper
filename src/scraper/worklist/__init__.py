"""Build the list of URLs a source should fetch. See PLAN.md §5, §12 step 1.

    seeds (dumps + sitemaps) → dedupe → path/date filters → robots → max_pages cap

Nothing here fetches a page. The only network traffic is sitemap XML and robots.txt, so
a worklist can be built and inspected before committing to a crawl — and with
`use_sitemaps=False` it is fully offline.

Every stage's drop count is reported (`WorklistCounts`) rather than silently applied: a
worklist that comes back unexpectedly small should say which stage ate it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from ..config import AppConfig, Filters, SourceConfig
from . import dumps
from . import filters as flt
from .robots import RobotsCache
from .sitemap import DiscoveredURL, collect

logger = logging.getLogger(__name__)

__all__ = ["DiscoveredURL", "Worklist", "WorklistCounts", "build", "build_all"]


@dataclass
class WorklistCounts:
    """Per-stage funnel for one source."""

    seeded: int = 0          # unique URLs across all seeds
    in_scope: int = 0        # survived include/exclude + date window
    robots_blocked: int = 0  # in scope but disallowed by robots.txt
    final: int = 0           # after the max_pages cap

    @property
    def out_of_scope(self) -> int:
        return self.seeded - self.in_scope

    @property
    def capped(self) -> int:
        return self.in_scope - self.robots_blocked - self.final

    def to_dict(self) -> dict:
        return {
            "seeded": self.seeded,
            "out_of_scope": self.out_of_scope,
            "in_scope": self.in_scope,
            "robots_blocked": self.robots_blocked,
            "capped": self.capped,
            "final": self.final,
        }


@dataclass
class Worklist:
    """The URLs one source should fetch, plus how we got to that number."""

    source_id: str
    company: str
    urls: list[DiscoveredURL]
    counts: WorklistCounts

    def __len__(self) -> int:
        return len(self.urls)


def build(
    source_id: str,
    source: SourceConfig,
    filters: Filters | None = None,
    *,
    client: httpx.Client | None = None,
    robots: RobotsCache | None = None,
    use_sitemaps: bool = True,
    respect_robots: bool = True,
    user_agent: str = "claude-scraper",
) -> Worklist:
    """Build one source's worklist.

    `use_sitemaps=False` restricts seeds to committed dumps, making the call offline
    (robots is then also skipped, since it too needs the network).
    """
    filters = filters or Filters()

    seeded: dict[str, DiscoveredURL] = {}
    for path in source.dump_paths():
        for item in dumps.read(path):
            seeded.setdefault(item.url, item)

    if use_sitemaps and source.sitemap_urls():
        for item in collect(
            source.sitemap_urls(),
            client=client,
            robots=robots,
            user_agent=user_agent,
        ):
            # A live sitemap entry wins: its lastmod is fresher than a committed dump's.
            seeded[item.url] = item

    counts = WorklistCounts(seeded=len(seeded))

    in_scope = flt.apply(list(seeded.values()), source, filters)
    counts.in_scope = len(in_scope)

    if respect_robots and robots is not None:
        allowed = [u for u in in_scope if robots.allows(u.url)]
        counts.robots_blocked = len(in_scope) - len(allowed)
        if counts.robots_blocked:
            logger.info(
                "%s: robots.txt disallows %d of %d in-scope URLs",
                source_id,
                counts.robots_blocked,
                len(in_scope),
            )
    else:
        allowed = in_scope

    if filters.max_pages is not None:
        allowed = allowed[: filters.max_pages]
    counts.final = len(allowed)

    return Worklist(source_id=source_id, company=source.company, urls=allowed, counts=counts)


def build_all(
    cfg: AppConfig,
    *,
    source_ids: list[str] | None = None,
    include_disabled: bool = False,
    use_sitemaps: bool = True,
    client: httpx.Client | None = None,
) -> list[Worklist]:
    """Build worklists for every selected source, sharing one HTTP client and robots cache.

    Sharing matters: `anthropic-docs` and `anthropic-cookbook` are the same host, and
    robots.txt should be fetched once per origin per run, not once per source.
    """
    sources = cfg.sources if include_disabled else cfg.enabled_sources()
    if source_ids:
        missing = [sid for sid in source_ids if sid not in cfg.sources]
        if missing:
            raise KeyError(f"unknown source id(s): {', '.join(missing)} — have {list(cfg.sources)}")
        sources = {sid: cfg.sources[sid] for sid in source_ids}

    own_client = client is None
    if client is None and use_sitemaps:
        client = httpx.Client(
            timeout=cfg.defaults.timeout_s,
            follow_redirects=True,
            headers={"User-Agent": cfg.defaults.user_agent},
        )

    robots = (
        RobotsCache(client, user_agent=cfg.defaults.user_agent)
        if client is not None and cfg.defaults.respect_robots
        else None
    )

    try:
        return [
            build(
                sid,
                src,
                cfg.filters,
                client=client,
                robots=robots,
                use_sitemaps=use_sitemaps,
                respect_robots=cfg.defaults.respect_robots,
                user_agent=cfg.defaults.user_agent,
            )
            for sid, src in sources.items()
        ]
    finally:
        if own_client and client is not None:
            client.close()
