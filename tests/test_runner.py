"""Job selection: what a re-run does *not* do matters as much as what it does."""

from __future__ import annotations

import pytest

from scraper.config import load_config
from scraper.fetch import FetchDB
from scraper.fetch.runner import IMPLEMENTED_TIERS, RunSummary, run_fetch, select_jobs
from scraper.worklist import Worklist, WorklistCounts
from scraper.worklist.sitemap import DiscoveredURL

URLS = [f"https://x.com/p{i}" for i in range(4)]


def worklist(urls=None) -> Worklist:
    urls = urls or URLS
    return Worklist(
        source_id="s",
        company="c",
        urls=[DiscoveredURL(u, None) for u in urls],
        counts=WorklistCounts(seeded=len(urls), in_scope=len(urls), final=len(urls)),
    )


@pytest.fixture
def db(tmp_path):
    with FetchDB(tmp_path / "fetch.db") as fdb:
        yield fdb


def archive(db, url, tmp_path, *, etag='"v1"'):
    raw = tmp_path / f"{url.rsplit('/', 1)[-1]}.gz"
    raw.write_bytes(b"body")
    db.record_ok(url, "s", raw_path=raw, raw_sha256="h", tier="http", etag=etag)


def test_everything_is_new_on_a_first_run(db):
    jobs, existing, exhausted = select_jobs([worklist()], db)
    assert [j.url for j in jobs] == URLS
    assert (existing, exhausted) == (0, 0)


def test_default_mode_skips_archived_urls(db, tmp_path):
    """This is what makes an interrupted run resumable for free."""
    archive(db, URLS[0], tmp_path)
    archive(db, URLS[1], tmp_path)
    jobs, existing, _ = select_jobs([worklist()], db, mode="new")
    assert [j.url for j in jobs] == URLS[2:]
    assert existing == 2


def test_refresh_mode_revalidates_with_stored_validators(db, tmp_path):
    archive(db, URLS[0], tmp_path, etag='"abc"')
    jobs, existing, _ = select_jobs([worklist()], db, mode="refresh")
    assert len(jobs) == 4
    assert existing == 0
    assert jobs[0].etag == '"abc"'
    assert jobs[1].etag is None, "URLs never fetched have nothing to revalidate against"


def test_force_mode_ignores_validators(db, tmp_path):
    archive(db, URLS[0], tmp_path, etag='"abc"')
    jobs, _, _ = select_jobs([worklist()], db, mode="force")
    assert len(jobs) == 4
    assert jobs[0].etag is None, "force means unconditional — do not send If-None-Match"


def test_errored_urls_are_retried_by_default(db):
    db.record_error(URLS[0], "s", error="timeout")
    jobs, _, exhausted = select_jobs([worklist()], db, mode="new")
    assert URLS[0] in [j.url for j in jobs]
    assert exhausted == 0


def test_urls_are_abandoned_after_max_attempts(db):
    for _ in range(3):
        db.record_error(URLS[0], "s", error="timeout")
    jobs, _, exhausted = select_jobs([worklist()], db, mode="new", max_attempts=3)
    assert URLS[0] not in [j.url for j in jobs]
    assert exhausted == 1


def test_max_attempts_is_configurable(db):
    for _ in range(3):
        db.record_error(URLS[0], "s", error="timeout")
    jobs, _, exhausted = select_jobs([worklist()], db, mode="new", max_attempts=5)
    assert URLS[0] in [j.url for j in jobs]
    assert exhausted == 0


def test_not_modified_counts_as_archived(db, tmp_path):
    archive(db, URLS[0], tmp_path)
    db.record_not_modified(URLS[0])
    jobs, existing, _ = select_jobs([worklist()], db, mode="new")
    assert URLS[0] not in [j.url for j in jobs]
    assert existing == 1


def test_jobs_carry_source_and_company(db):
    jobs, _, _ = select_jobs([worklist()], db)
    assert jobs[0].source_id == "s"
    assert jobs[0].company == "c"


def test_skipped_urls_are_still_retried(db):
    """A robots skip from a previous config should not permanently exclude a URL."""
    db.record_skipped(URLS[0], "s", reason="robots")
    jobs, existing, _ = select_jobs([worklist()], db, mode="new")
    assert URLS[0] in [j.url for j in jobs]
    assert existing == 0


# --- summary ---------------------------------------------------------------

def test_summary_counts_and_render():
    s = RunSummary(started_at="2026-08-17T12:00:00+00:00", mode="new")
    s.ok, s.not_modified, s.errors = 10, 5, 2
    s.elapsed_s = 17.0
    assert s.attempted == 17
    assert s.rate == pytest.approx(1.0)
    out = s.render()
    assert "ok             10" in out
    assert "1.00 req/s" in out


# --- tier guard ------------------------------------------------------------

def test_unimplemented_tiers_are_deferred_not_misfetched(tmp_path):
    """A source whose fetcher does not exist yet must be skipped, not fetched wrongly.

    Fetching a `browser`-tier source through the HTTP tier would archive an empty SPA
    shell and record it as a success — 3,526 wasted requests and a corrupt archive.
    """
    cfg = load_config("config/sources.yaml")
    cfg.sources["databricks-api"].enabled = True        # browser tier, not implemented

    summary = run_fetch(
        cfg,
        mode="new",
        dry_run=True,
        use_sitemaps=False,
        db_path=tmp_path / "fetch.db",
        raw_dir=tmp_path / "raw",
        runs_dir=tmp_path / "runs",
    )
    assert "databricks-api" in summary.deferred_sources
    assert "browser" in summary.deferred_sources["databricks-api"]
    assert "databricks-api" not in summary.sources
    assert "databricks-docs" in summary.sources


def test_implemented_tiers_are_the_ones_with_fetchers():
    assert IMPLEMENTED_TIERS == {"http", "markdown_endpoint"}


def test_jobs_carry_their_source_tier(db):
    jobs, _, _ = select_jobs(
        [worklist()], db, tiers={"s": "markdown_endpoint"}
    )
    assert all(j.tier == "markdown_endpoint" for j in jobs)


def test_jobs_default_to_the_http_tier(db):
    jobs, _, _ = select_jobs([worklist()], db)
    assert all(j.tier == "http" for j in jobs)


def test_summary_is_written_as_json(tmp_path):
    s = RunSummary(started_at="2026-08-17T12:00:00+00:00", mode="new")
    s.ok = 3
    path = s.write(tmp_path)
    assert path.exists()
    import json
    data = json.loads(path.read_text())
    assert data["ok"] == 3
    assert data["attempted"] == 3


# --- content-hash change detection (PLAN.md §8) -----------------------------

def test_unchanged_bytes_are_reported_on_refresh(tmp_path):
    """Anthropic sends no validators, so 'did it change?' is answerable only after the
    fetch. A refresh must not imply every page moved."""
    import asyncio

    from scraper.config import AppConfig
    from scraper.fetch.runner import FetchRunner, Job

    cfg = AppConfig.model_validate({
        "sources": {"s": {"company": "c", "seeds": [{"type": "dump", "path": "x.txt"}]}}
    })
    body = b"# unchanged content"

    class Stub:
        tier = "http"

        async def fetch(self, url, **kw):
            from scraper.fetch.http import FetchResult
            return FetchResult(url=url, state="ok", status_code=200, content=body,
                               content_type="text/markdown", final_url=url)

    with FetchDB(tmp_path / "f.db") as db:
        runner = FetchRunner(cfg, db, raw_dir=tmp_path / "raw")
        job = Job("https://x.com/p", "s", "c")

        first = RunSummary(started_at="t", mode="new")
        asyncio.run(_file_once(runner, job, Stub(), first))
        assert (first.ok, first.unchanged) == (1, 0)

        second = RunSummary(started_at="t", mode="refresh")
        asyncio.run(_file_once(runner, job, Stub(), second))
        assert (second.ok, second.unchanged) == (1, 1)


async def _file_once(runner, job, fetcher, summary):
    result = await fetcher.fetch(job.url)
    result.tier = fetcher.tier
    runner._file(job, result, summary)
