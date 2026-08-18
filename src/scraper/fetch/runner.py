"""Drive a fetch run: worklist → fetch → raw archive → fetch.db. See PLAN.md §6, §10.

Selection is the part worth reading. A run over 6,381 pages takes ~1h45m at the
configured rate, so what a re-run *doesn't* do matters as much as what it does:

* **default** — fetch URLs that are new or previously errored; skip anything already
  archived. This makes an interrupted run resumable for free: restart it and the pages
  already on disk cost nothing.
* **`--refresh`** — revalidate archived URLs with a conditional GET. On Databricks that
  is a `304` with an empty body (PLAN.md §8), so a full refresh is cheap; on Anthropic,
  which sends `no-store`, it is a real re-fetch compared by content hash.
* **`--force`** — unconditional re-fetch, ignoring both state and validators. The escape
  hatch for "the archive is wrong", not a routine mode.

Every URL's outcome is written to `fetch.db` as it happens, so a run killed at minute 90
loses at most the requests in flight.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import httpx

from ..config import AppConfig
from ..worklist import Worklist, build_all
from . import rawstore
from .db import FetchDB
from .http import FetchResult, HttpFetcher
from .markdown_endpoint import MarkdownEndpointFetcher
from .politeness import Politeness

logger = logging.getLogger(__name__)

DEFAULT_RUNS_DIR = Path("state/runs")

# Fetch tiers implemented so far. A source asking for anything else is skipped rather
# than quietly fetched with the wrong tier: archiving 566 HTML pages for a source whose
# `.md` twin we will fetch in step 4 would burn 566 requests on someone else's server
# and leave an archive that has to be thrown away.
IMPLEMENTED_TIERS = frozenset({"http", "markdown_endpoint"})


@dataclass
class Job:
    """One URL to fetch, with the context needed to file the result."""

    url: str
    source_id: str
    company: str
    tier: str = "http"
    etag: str | None = None
    last_modified: str | None = None


@dataclass
class RunSummary:
    """What a run did — printed, and written to `state/runs/{ts}.json` (PLAN.md §10)."""

    started_at: str
    mode: str
    dry_run: bool = False
    sources: list[str] = field(default_factory=list)
    deferred_sources: dict[str, str] = field(default_factory=dict)
    selected: int = 0
    skipped_existing: int = 0
    skipped_exhausted: int = 0
    ok: int = 0
    unchanged: int = 0          # re-fetched, but byte-identical to the archived copy
    not_modified: int = 0
    errors: int = 0
    bytes_fetched: int = 0
    elapsed_s: float = 0.0
    status_codes: dict[str, int] = field(default_factory=dict)
    tiers: dict[str, int] = field(default_factory=dict)
    redirected: int = 0
    hosts: dict[str, dict] = field(default_factory=dict)
    error_samples: list[dict] = field(default_factory=list)

    @property
    def attempted(self) -> int:
        return self.ok + self.not_modified + self.errors

    @property
    def rate(self) -> float:
        return self.attempted / self.elapsed_s if self.elapsed_s else 0.0

    def to_dict(self) -> dict:
        return {
            **self.__dict__,
            "attempted": self.attempted,
            "requests_per_second": round(self.rate, 3),
        }

    def write(self, runs_dir: Path | None = None) -> Path:
        runs_dir = Path(runs_dir or DEFAULT_RUNS_DIR)
        runs_dir.mkdir(parents=True, exist_ok=True)
        stamp = self.started_at.replace(":", "").replace("-", "").replace(".", "")[:15]
        path = runs_dir / f"{stamp}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path

    def render(self) -> str:
        lines = [
            f"run {self.started_at}  mode={self.mode}{'  DRY RUN' if self.dry_run else ''}",
            f"  sources        {', '.join(self.sources) or '-'}",
            *(
                [f"  deferred       {sid} ({why})" for sid, why in self.deferred_sources.items()]
            ),
            (
                f"  selected       {self.selected}"
                f"   (skipped: {self.skipped_existing} archived,"
                f" {self.skipped_exhausted} exhausted)"
            ),
            f"  ok             {self.ok}"
            + (f"   ({self.unchanged} byte-identical)" if self.unchanged else ""),
            f"  not modified   {self.not_modified}",
            f"  errors         {self.errors}",
            f"  fetched        {self.bytes_fetched / 1_048_576:.1f} MiB",
            f"  elapsed        {self.elapsed_s:.1f}s  ({self.rate:.2f} req/s overall)",
        ]
        if self.status_codes:
            codes = "  ".join(f"{k}:{v}" for k, v in sorted(self.status_codes.items()))
            lines.append(f"  status codes   {codes}")
        if self.tiers:
            tiers = "  ".join(f"{k}:{v}" for k, v in sorted(self.tiers.items()))
            lines.append(f"  tiers          {tiers}")
        if self.redirected:
            lines.append(f"  redirected     {self.redirected}")
        for host, info in self.hosts.items():
            note = f"  ({info['penalties']} penalties)" if info["penalties"] else ""
            lines.append(f"  host {host}  {info['requests_per_second']} req/s{note}")
        for sample in self.error_samples[:10]:
            lines.append(f"  ! {sample['status'] or '-'}  {sample['url']}  {sample['error']}")
        return "\n".join(lines)


def select_jobs(
    worklists: list[Worklist],
    db: FetchDB,
    *,
    mode: str = "new",
    max_attempts: int = 3,
    tiers: dict[str, str] | None = None,
) -> tuple[list[Job], int, int]:
    """Decide which URLs this run will request.

    Returns `(jobs, skipped_existing, skipped_exhausted)`.
    """
    jobs: list[Job] = []
    skipped_existing = skipped_exhausted = 0

    for wl in worklists:
        for du in wl.urls:
            row = db.get(du.url)

            exhausted = (
                row is not None
                and row["state"] == "fetch_error"
                and (row["attempts"] or 0) >= max_attempts
            )
            if exhausted:
                skipped_exhausted += 1
                continue

            archived = row is not None and row["state"] in ("ok", "not_modified")
            if archived and mode == "new":
                skipped_existing += 1
                continue

            etag = last_modified = None
            if mode == "refresh" and archived:
                etag, last_modified = db.validators(du.url)

            jobs.append(
                Job(
                    du.url,
                    wl.source_id,
                    wl.company,
                    (tiers or {}).get(wl.source_id, "http"),
                    etag,
                    last_modified,
                )
            )

    return jobs, skipped_existing, skipped_exhausted


class FetchRunner:
    """Runs a set of jobs politely, archiving each result as it lands."""

    def __init__(
        self,
        cfg: AppConfig,
        db: FetchDB,
        *,
        raw_dir: Path | None = None,
        dry_run: bool = False,
        progress_every: int = 25,
    ):
        self.cfg = cfg
        self.db = db
        self.raw_dir = Path(raw_dir or rawstore.DEFAULT_RAW_DIR)
        self.dry_run = dry_run
        self.progress_every = progress_every
        self.politeness = Politeness(
            requests_per_second=cfg.defaults.requests_per_second,
            concurrency=cfg.defaults.concurrency,
            jitter_s=cfg.defaults.jitter_s,
        )
        self._done = 0
        self._total = 0
        self._started = 0.0

    async def run(self, jobs: list[Job], summary: RunSummary) -> RunSummary:
        self._total = len(jobs)
        self._done = 0
        self._started = time.monotonic()

        if self.dry_run or not jobs:
            summary.elapsed_s = 0.0
            summary.hosts = self.politeness.report()
            return summary

        limits = httpx.Limits(max_connections=16, max_keepalive_connections=8)
        async with httpx.AsyncClient(
            http2=True,
            timeout=self.cfg.defaults.timeout_s,
            follow_redirects=True,
            headers={"User-Agent": self.cfg.defaults.user_agent},
            limits=limits,
        ) as client:
            http = HttpFetcher(
                client,
                retries=self.cfg.defaults.retries,
                backoff_max_s=self.cfg.defaults.backoff_max_s,
            )
            fetchers = {
                "http": http,
                "markdown_endpoint": MarkdownEndpointFetcher(http),
            }
            queue: asyncio.Queue[Job] = asyncio.Queue()
            for job in jobs:
                queue.put_nowait(job)

            host_count = max(1, len({Politeness.host_of(j.url) for j in jobs}))
            workers = min(len(jobs), self.cfg.defaults.concurrency * host_count)
            tasks = [
                asyncio.create_task(self._worker(queue, fetchers, summary))
                for _ in range(workers)
            ]
            try:
                await queue.join()
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)

        summary.elapsed_s = time.monotonic() - self._started
        summary.hosts = self.politeness.report()
        return summary

    async def _worker(self, queue: asyncio.Queue, fetchers: dict, summary: RunSummary) -> None:
        while True:
            job = await queue.get()
            try:
                fetcher = fetchers[job.tier]
                async with self.politeness.slot(job.url):
                    result = await fetcher.fetch(
                        job.url, etag=job.etag, last_modified=job.last_modified
                    )
                if result.penalised:
                    self.politeness.penalise(job.url, f"HTTP {result.status_code}")
                self._file(job, result, summary)
                self._progress()
            except asyncio.CancelledError:
                raise
            except Exception as exc:                      # never let one URL kill the run
                logger.exception("unhandled error fetching %s", job.url)
                self.db.record_error(job.url, job.source_id, error=f"{type(exc).__name__}: {exc}")
                summary.errors += 1
            finally:
                queue.task_done()

    def _file(self, job: Job, result: FetchResult, summary: RunSummary) -> None:
        """Archive the bytes (if any) and record the outcome."""
        if result.status_code is not None:
            key = str(result.status_code)
            summary.status_codes[key] = summary.status_codes.get(key, 0) + 1
        summary.tiers[result.tier] = summary.tiers.get(result.tier, 0) + 1
        if result.final_url and result.final_url not in (job.url, job.url + ".md"):
            summary.redirected += 1

        if result.state == "ok" and result.content is not None:
            digest = rawstore.sha256(result.content)
            # Hosts that send no validators (Anthropic sends `no-store` and no ETag) can
            # only be diffed after the fact. Report it so a refresh run says how much
            # actually moved, rather than implying 566 pages changed. PLAN.md §8.
            prior = self.db.get(job.url)
            if prior is not None and prior["raw_sha256"] == digest:
                summary.unchanged += 1

            ext = rawstore.ext_for(result.content_type, job.url)
            path = rawstore.write(job.url, job.company, result.content, ext=ext, base_dir=self.raw_dir)
            self.db.record_ok(
                job.url,
                job.source_id,
                raw_path=path,
                raw_sha256=digest,
                tier=result.tier,
                status_code=result.status_code or 200,
                final_url=result.final_url,
                content_type=result.content_type,
                etag=result.etag,
                last_modified=result.last_modified,
            )
            summary.ok += 1
            summary.bytes_fetched += len(result.content)

        elif result.state == "not_modified":
            self.db.record_not_modified(
                job.url, etag=result.etag, last_modified=result.last_modified
            )
            summary.not_modified += 1

        else:
            self.db.record_error(
                job.url,
                job.source_id,
                error=result.error or "unknown error",
                status_code=result.status_code,
                tier=result.tier,
            )
            summary.errors += 1
            if len(summary.error_samples) < 25:
                summary.error_samples.append(
                    {"url": job.url, "status": result.status_code, "error": result.error}
                )

    def _progress(self) -> None:
        self._done += 1
        if self.progress_every and self._done % self.progress_every == 0:
            elapsed = time.monotonic() - self._started
            rate = self._done / elapsed if elapsed else 0
            remaining = (self._total - self._done) / rate if rate else 0
            logger.warning(
                "  %d/%d  %.2f req/s  eta %s",
                self._done,
                self._total,
                rate,
                _humanise(remaining),
            )


def _humanise(seconds: float) -> str:
    seconds = int(seconds)
    if seconds < 90:
        return f"{seconds}s"
    if seconds < 5400:
        return f"{seconds // 60}m"
    return f"{seconds // 3600}h{(seconds % 3600) // 60:02d}m"


def run_fetch(
    cfg: AppConfig,
    *,
    source_ids: list[str] | None = None,
    mode: str = "new",
    limit: int | None = None,
    dry_run: bool = False,
    db_path: Path | None = None,
    raw_dir: Path | None = None,
    use_sitemaps: bool = True,
    runs_dir: Path | None = None,
) -> RunSummary:
    """Build the worklist, select jobs, fetch them, and return the run summary."""
    summary = RunSummary(
        started_at=datetime.now(UTC).isoformat(timespec="seconds"),
        mode="force" if mode == "force" else mode,
        dry_run=dry_run,
    )

    worklists = build_all(cfg, source_ids=source_ids, use_sitemaps=use_sitemaps)

    runnable = []
    for wl in worklists:
        tier = cfg.sources[wl.source_id].fetcher
        if tier in IMPLEMENTED_TIERS:
            runnable.append(wl)
        else:
            summary.deferred_sources[wl.source_id] = f"fetcher '{tier}' not implemented yet"
            logger.warning(
                "skipping %s: its fetcher is '%s', which is not implemented yet — "
                "fetching it with the HTTP tier would archive the wrong bytes",
                wl.source_id,
                tier,
            )
    worklists = runnable
    summary.sources = [wl.source_id for wl in worklists]

    with FetchDB(db_path or "state/fetch.db") as db:
        jobs, skipped_existing, skipped_exhausted = select_jobs(
            worklists,
            db,
            mode=mode,
            max_attempts=cfg.defaults.max_attempts,
            tiers={sid: cfg.sources[sid].fetcher for sid in cfg.sources},
        )
        if limit is not None:
            jobs = jobs[:limit]

        summary.selected = len(jobs)
        summary.skipped_existing = skipped_existing
        summary.skipped_exhausted = skipped_exhausted

        runner = FetchRunner(cfg, db, raw_dir=raw_dir, dry_run=dry_run)
        try:
            asyncio.run(runner.run(jobs, summary))
        except KeyboardInterrupt:
            logger.warning("interrupted — %d URLs already recorded in fetch.db", summary.attempted)
            summary.mode += "+interrupted"

    if not dry_run:
        summary.write(runs_dir)
    return summary
