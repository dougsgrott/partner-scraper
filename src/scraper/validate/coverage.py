"""Did we get everything we should have? See docs/validation-plan.md §1, §5.

Two independent measurements, because they fail differently:

**Scope reconciliation** trusts the sitemap and asks whether the pipeline honoured it —
it catches filters that drop too much and runs that stopped early.

**Link-graph closure** does not trust the sitemap at all. Every internal link the corpus
itself contains is a claim that a page exists; any in-scope target we never archived is a
page the sitemap did not advertise. That is the only check here that can find pages the
site never told us about, and on the phase-1 corpus it found 370.
"""

from __future__ import annotations

import re
import sqlite3
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from ..config import AppConfig
from ..store import writer
from ..worklist import filters as flt
from .report import Check, failed, passed, warned

# Files the pipeline deliberately never fetches: they are not documentation pages.
# The sample-code suffixes are here because Databricks links downloadable `.py`, `.sh`,
# `.sql` and `.tdc` files out of `/assets/files/`, and counting those as missing pages
# overstated the coverage gap by a fifth.
ASSET_SUFFIXES = re.compile(
    r"\.(?:pdf|png|jpe?g|gif|svg|webp|ico|zip|tar|gz|csv|xlsx?|whl|jar|ipynb|txt|xml|json"
    r"|py|sh|sql|tdc|ya?ml|toml|scala|r|dbc|tf|properties|conf)$",
    re.IGNORECASE,
)
# Notebook exports served as standalone `.html` under `/notebooks/source/`. Real content,
# but notebook source rather than documentation — a separate decision from closing a gap.
NOTEBOOK_EXPORT = re.compile(r"/notebooks/source/.*\.html$|\.html$", re.IGNORECASE)
MD_LINK = re.compile(r"\]\((https?://[^)\s]+)\)")


def normalise(url: str) -> str:
    """Drop the fragment and query, and the trailing slash — one document, one key."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/") or "/", "", ""))


def archived_urls(fetch_db_path: str | Path = "state/fetch.db") -> set[str]:
    conn = sqlite3.connect(fetch_db_path)
    urls = {normalise(u) for (u,) in conn.execute("SELECT url FROM fetches")}
    conn.close()
    return urls


def corpus_links(data_dir: str | Path = "data") -> Counter:
    """Every absolute link the corpus contains, counted by how often it is referenced."""
    targets: Counter = Counter()
    for path in Path(data_dir).rglob("*.md"):
        _, body = writer.parse(path)
        for match in MD_LINK.finditer(body):
            targets[normalise(match.group(1))] += 1
    return targets


def hosts_of(urls: set[str]) -> set[str]:
    """The hosts we actually archive — a candidate on any other host is a different site."""
    return {urlsplit(u).netloc for u in urls if u}


def classify_links(cfg: AppConfig, targets: Counter, archived: set[str]) -> dict[str, list]:
    """Split link targets into what they actually are.

    `filters.in_scope` matches on *path* alone, which is right where a URL already came
    from a source's own seeds and wrong here, where the input is every link in the corpus:
    `code.claude.com/docs/en/overview` and `nlp.johnsnowlabs.com/docs/en/…` both match
    `/docs/en/` while belonging to entirely different sites. Hence the host check.
    """
    known = hosts_of(archived)
    buckets: dict[str, list] = {"archived": [], "asset": [], "notebook_export": [],
                                "foreign_host": [], "out_of_scope": [], "candidate": []}
    for url, hits in targets.items():
        source = next((s for s in cfg.enabled_sources().values() if flt.in_scope(url, s)), None)
        if source is None:
            buckets["out_of_scope"].append((hits, url))
        elif url in archived:
            buckets["archived"].append((hits, url))
        elif known and urlsplit(url).netloc not in known:
            buckets["foreign_host"].append((hits, url))
        elif ASSET_SUFFIXES.search(url):
            buckets["asset"].append((hits, url))
        elif NOTEBOOK_EXPORT.search(url):
            buckets["notebook_export"].append((hits, url))
        else:
            buckets["candidate"].append((hits, url))
    for entries in buckets.values():
        entries.sort(reverse=True)
    return buckets


def check_link_closure(cfg: AppConfig, *, data_dir: str | Path = "data",
                       fetch_db_path: str | Path = "state/fetch.db") -> tuple[Check, list]:
    """Pages the corpus links to but does not contain.

    Reported as a warning, not a failure: a link can point at a page that has since been
    removed or renamed, and only a live probe can tell those apart from a real gap. The
    candidate list is the input to that probe.
    """
    targets = corpus_links(data_dir)
    buckets = classify_links(cfg, targets, archived_urls(fetch_db_path))
    candidates = buckets["candidate"]
    detail = {k: len(v) for k, v in buckets.items()} | {"distinct_targets": len(targets)}

    summary = (f"{len(candidates)} documentation page(s) linked but not archived "
               f"({detail['archived']} archived, {detail['asset']} assets, "
               f"{detail['notebook_export']} notebook exports, "
               f"{detail['foreign_host']} on other hosts, "
               f"{detail['out_of_scope']} out of scope)")
    check = (passed("link_graph_closure", "every in-scope link target is archived",
                    total=len(targets), detail=detail)
             if not candidates else
             warned("link_graph_closure", summary, count=len(candidates), total=len(targets),
                    samples=[f"{n:>4}×  {u}" for n, u in candidates[:5]], detail=detail))
    return check, candidates


def check_scope_reconciliation(cfg: AppConfig, worklists, *,
                               fetch_db_path: str | Path = "state/fetch.db") -> list[Check]:
    """Worklist ↔ archive, both directions, per source."""
    archived_by_source: dict[str, set[str]] = {}
    conn = sqlite3.connect(fetch_db_path)
    for url, source_id in conn.execute("SELECT url, source_id FROM fetches"):
        archived_by_source.setdefault(source_id, set()).add(normalise(url))
    conn.close()

    checks = []
    for worklist in worklists:
        wanted = {normalise(du.url) for du in worklist.urls}
        have = archived_by_source.get(worklist.source_id, set())
        unfetched, stale = sorted(wanted - have), sorted(have - wanted)
        name = f"scope_{worklist.source_id}"

        if unfetched:
            checks.append(failed(name, f"{len(unfetched)} in-scope URL(s) never fetched",
                                 count=len(unfetched), total=len(wanted), samples=unfetched[:5],
                                 detail={"in_scope": len(wanted), "archived": len(have)}))
        elif stale:
            checks.append(warned(name,
                                 f"{len(wanted)} in scope, all archived; "
                                 f"{len(stale)} archived URL(s) no longer in scope",
                                 count=len(stale), total=len(wanted), samples=stale[:5]))
        else:
            checks.append(passed(name, f"{len(wanted)} in scope, all archived", total=len(wanted)))
    return checks


def check_corpus_completeness(cfg: AppConfig, *, data_dir: str | Path = "data",
                              fetch_db_path: str | Path = "state/fetch.db",
                              index_db_path: str | Path = "state/index.db") -> Check:
    """Every archived page should end up in the corpus, deferred, or explained."""
    from ..extract import registry
    from ..store.index import Index

    conn = sqlite3.connect(fetch_db_path)
    conn.row_factory = sqlite3.Row
    archived = [dict(r) for r in conn.execute(
        "SELECT url, source_id FROM fetches WHERE state IN ('ok', 'not_modified')")]
    conn.close()

    deferred_sources = {sid for sid, src in cfg.sources.items()
                        if src.extractor not in registry.implemented()}
    with Index(index_db_path) as index:
        accounted = {row["url"] for row in index.query()}

    expected = [r for r in archived if r["source_id"] not in deferred_sources]
    unaccounted = sorted(r["url"] for r in expected if r["url"] not in accounted)
    deferred = [r for r in archived if r["source_id"] in deferred_sources]

    detail = {"archived": len(archived), "expected": len(expected),
              "deferred": len(deferred), "unaccounted": len(unaccounted)}
    if unaccounted:
        return failed("corpus_completeness",
                      f"{len(unaccounted)} archived page(s) never reached the corpus",
                      count=len(unaccounted), total=len(expected), samples=unaccounted[:5],
                      detail=detail)
    note = f" ({len(deferred)} deferred)" if deferred else ""
    return passed("corpus_completeness",
                  f"all {len(expected)} extractable pages accounted for{note}",
                  total=len(expected), detail=detail)
