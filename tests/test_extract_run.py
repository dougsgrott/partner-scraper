"""`run_extract` end to end over a fake archive — PLAN.md §12 step 6.

The unit tests in `test_store.py` prove the writer and index behave; these prove the
extract loop actually *uses* them, which is where step 6's second defect lived.
"""

from __future__ import annotations

import pytest

from scraper.config import AppConfig, DumpSeed, SourceConfig
from scraper.extract import run_extract
from scraper.fetch import FetchDB, rawstore
from scraper.store.index import Index

URL = "https://docs.databricks.com/aws/en/delta/tutorial"

PAGE = """
<html><head>
<meta property="og:title" content="Delta tutorial | Databricks on AWS"/>
<meta property="og:url" content="%(url)s"/>
</head><body><article>
  <div class="theme-last-updated">Last updated on %(updated)s</div>
  <div class="theme-doc-markdown markdown">
    <h1>Delta tutorial</h1>
    <p>%(body)s</p>
  </div>
</article></body></html>
"""


def page(updated="Jul 10, 2026", body="Body text that is comfortably long enough. " * 8) -> bytes:
    return (PAGE % {"url": URL, "updated": updated, "body": body}).encode()


@pytest.fixture
def env(tmp_path):
    """A one-source config plus the four paths run_extract needs."""
    cfg = AppConfig(sources={"databricks-docs": SourceConfig(
        company="databricks",
        seeds=[DumpSeed(type="dump", path=tmp_path / "dump.txt")],
        include_paths=["/aws/en/"],
        extractor="docusaurus",
    )})
    (tmp_path / "dump.txt").write_text("")
    return {
        "cfg": cfg,
        "raw": tmp_path / "raw",
        "data": tmp_path / "data",
        "fetch_db": tmp_path / "fetch.db",
        "index_db": tmp_path / "index.db",
    }


def archive(env, content: bytes, url: str = URL) -> None:
    """Put bytes in the archive and tell fetch.db about them, as a fetch run would."""
    path = rawstore.write(url, "databricks", content, ext="html", base_dir=env["raw"])
    with FetchDB(env["fetch_db"]) as db:
        db.record_ok(url, "databricks-docs", raw_path=path,
                     raw_sha256=rawstore.sha256(content), tier="http",
                     content_type="text/html", final_url=url)


def extract(env, **kw):
    return run_extract(env["cfg"], fetch_db_path=env["fetch_db"],
                       index_db_path=env["index_db"], data_dir=env["data"], **kw)


def corpus(env) -> list[str]:
    return sorted(str(p.relative_to(env["data"])) for p in env["data"].rglob("*.md"))


def test_a_page_is_extracted_and_indexed(env):
    archive(env, page())
    summary = extract(env)
    assert (summary.written, summary.errors, summary.quality_failed) == (1, 0, 0)
    assert corpus(env) == ["databricks/delta/2026-07/aws-en-delta-tutorial.md"]

    with Index(env["index_db"]) as index:
        assert index.get(URL)["status"] == "ok"


def test_rerunning_skips_unchanged_pages(env):
    archive(env, page())
    extract(env)
    summary = extract(env)
    assert (summary.written, summary.skipped_unchanged) == (0, 1)


def test_forcing_rewrites_nothing_when_nothing_changed(env):
    archive(env, page())
    path = env["data"] / "databricks/delta/2026-07/aws-en-delta-tutorial.md"
    extract(env)
    before = path.read_bytes(), path.stat().st_mtime_ns

    summary = extract(env, force=True)
    assert (summary.written, summary.unchanged_files) == (1, 1)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


def test_a_page_that_moves_leaves_no_stale_copy(env):
    """REGRESSION: the date bucket comes from `updated_date`, so an edited doc changes path.

    Before this, the previous month's file stayed in `data/` forever: unreferenced by the
    index, invisible in every summary, and indistinguishable from a live page to anything
    that reads the corpus off disk.
    """
    archive(env, page(updated="Jul 10, 2026"))
    extract(env)

    archive(env, page(updated="Aug 3, 2026"))          # the site edited the doc
    summary = extract(env)

    assert corpus(env) == ["databricks/delta/2026-08/aws-en-delta-tutorial.md"]
    assert summary.moved == 1
    with Index(env["index_db"]) as index:
        assert index.orphans(env["data"]) == []


def test_prune_removes_files_the_index_no_longer_claims(env):
    archive(env, page())
    extract(env)
    stray = env["data"] / "databricks/delta/2024-01/aws-en-delta-old.md"
    stray.parent.mkdir(parents=True)
    stray.write_text("left over from an older layout")

    summary = extract(env, prune=True)
    assert summary.pruned == 1
    assert not stray.exists()
    assert not stray.parent.exists(), "the empty date bucket should go too"


def test_prune_is_opt_in(env):
    archive(env, page())
    extract(env)
    stray = env["data"] / "databricks/delta/2024-01/x.md"
    stray.parent.mkdir(parents=True)
    stray.write_text("still here")
    assert extract(env).pruned == 0
    assert stray.exists()


def test_two_urls_for_one_document_keep_one_file(env):
    archive(env, page())
    archive(env, page(), url=URL + "/")
    summary = extract(env)
    assert summary.duplicates == 1
    assert len(corpus(env)) == 1

    with Index(env["index_db"]) as index:
        assert index.counts()["duplicate"] == 1
        assert index.orphans(env["data"]) == []

    # Settled, not pending: a second pass must not keep re-resolving it.
    assert extract(env).duplicates == 0


def test_a_failed_page_leaves_no_file_and_stays_visible(env):
    archive(env, page(body="tiny"))
    summary = extract(env)
    assert (summary.quality_failed, summary.written) == (1, 0)
    assert corpus(env) == []

    with Index(env["index_db"]) as index:
        row = index.get(URL)
        assert row["status"] == "quality_failed" and "too short" in row["error"]
