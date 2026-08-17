"""Windowed, usage-limit-aware batch runner for the Claude Code (Agent SDK) path.

One invocation ingests a bounded batch of pages, persists each to the store, and stops
cleanly when: the batch size is reached, the work-list is exhausted, or the Claude Code
usage window is (nearly) exhausted — then exits. Stateless/resumable across runs: the
work-list is recomputed each run from discovery + the index, so the corpus fills in
incrementally over many runs. Drive cadence externally (cron, or the /loop skill).

See the plan: `.claude/plans/nicely-done-now-i-reflective-lecun.md`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse

from .config import AppConfig
from .discovery import filters as flt
from .discovery import sitemap as sm
from .discovery.sitemap import DiscoveredURL
from .ingest.fetch_enrich_cc import fetch_enrich_cc_observed
from .store import writer
from .store.index import Index

logger = logging.getLogger(__name__)

Work = tuple[str, DiscoveredURL]  # (company, discovered url)


@dataclass
class RunSummary:
    """Outcome of one batch run."""

    processed: int = 0
    ingested: int = 0
    errored: int = 0
    remaining: int = 0  # work-list items left un-processed this run
    stopped_reason: str = "exhausted"  # batch_size | exhausted | rate_limited | dry_run
    resets_at: int | None = None

    def __str__(self) -> str:
        line = (
            f"processed={self.processed} ingested={self.ingested} errored={self.errored} "
            f"remaining={self.remaining} stopped={self.stopped_reason}"
        )
        if self.resets_at:
            secs = self.resets_at / 1000 if self.resets_at > 1_000_000_000_000 else self.resets_at
            when = datetime.fromtimestamp(secs, tz=UTC).isoformat()
            line += f" resets_at={self.resets_at} ({when})"
        return line


def _priority_rank(url: str, priorities: list[str]) -> int:
    """Index of the first matching priority prefix (lower = higher priority)."""
    path = urlparse(url).path
    for i, prefix in enumerate(priorities):
        if path.startswith(prefix):
            return i
    return len(priorities)


def _order(work: list[Work], companies: list[str], priorities: list[str]) -> list[Work]:
    """Sort by (priority rank asc, round-robin position across companies, company, url)."""
    comp_order = {c: i for i, c in enumerate(companies)}
    by_company: dict[str, list[Work]] = {}
    for item in work:
        by_company.setdefault(item[0], []).append(item)
    for items in by_company.values():
        items.sort(key=lambda w: w[1].url)

    keyed: list[tuple[tuple[int, int, int, str], Work]] = []
    for company, items in by_company.items():
        for position, item in enumerate(items):
            rank = _priority_rank(item[1].url, priorities)
            keyed.append(((rank, position, comp_order.get(company, 999), item[1].url), item))
    keyed.sort(key=lambda kv: kv[0])
    return [item for _, item in keyed]


def _select(cfg: AppConfig, companies: list[str], only: str | None, index: Index) -> list[Work]:
    """Discover candidates, keep those needing ingest, order by priority."""
    candidates: list[Work] = []
    for company in companies:
        src = cfg.sources[company]
        for du in flt.apply(sm.collect(src), src, cfg.filters):
            if only and not urlparse(du.url).path.startswith(only):
                continue
            candidates.append((company, du))

    work = [
        (company, du)
        for company, du in candidates
        if index.should_ingest(du.url, du.lastmod, cfg.batch.max_attempts)
    ]
    return _order(work, companies, cfg.batch.priorities)


def run_batch(
    config: AppConfig,
    *,
    companies: list[str] | None = None,
    batch_size: int | None = None,
    only: str | None = None,
    dry_run: bool = False,
    index: Index | None = None,
) -> RunSummary:
    """Ingest up to `batch_size` pages via the CC path, stopping on the usage window."""
    batch = config.batch
    size = batch_size or batch.size
    companies = companies or batch.companies or list(config.sources)

    own_index = index is None
    index = index or Index()
    try:
        work = _select(config, companies, only, index)
        summary = RunSummary(remaining=len(work))

        if dry_run:
            summary.stopped_reason = "dry_run"
            print(f"[dry-run] {len(work)} pages need ingest; showing first {size}:")
            for company, du in work[:size]:
                rank = _priority_rank(du.url, config.batch.priorities)
                print(f"  p{rank} {company:10} {du.url}")
            return summary

        stop_reason: str | None = None
        for company, du in work:
            if summary.processed >= size:
                stop_reason = "batch_size"
                break

            result, snap = fetch_enrich_cc_observed(
                du.url,
                company=company,
                allowed_themes=config.themes_for(company),
                model=config.model,
                max_content_tokens=config.max_content_tokens,
            )
            summary.processed += 1

            if result.status == "ok" and result.record:
                path = writer.write(result.record, du.url)
                index.upsert(
                    du.url, result.record, path,
                    writer.content_hash(result.record.markdown), lastmod=du.lastmod,
                )
                summary.ingested += 1
            else:
                index.record_error(
                    du.url, company, result.status, result.error or "", lastmod=du.lastmod,
                )
                summary.errored += 1
            logger.info("%s %s", result.status, du.url)

            # Usage guard: hard stop on rejection; proactive stop when approaching the cap.
            if snap and (
                snap.status == "rejected"
                or snap.status == "allowed_warning"
                or (snap.utilization is not None and snap.utilization >= batch.stop_utilization)
            ):
                stop_reason = "rate_limited"
                summary.resets_at = snap.resets_at
                break

        summary.stopped_reason = stop_reason or "exhausted"
        summary.remaining = len(work) - summary.processed
        return summary
    finally:
        if own_index:
            index.close()
