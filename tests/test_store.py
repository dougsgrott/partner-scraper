"""The corpus writer, layout, and index — PLAN.md §7.3, §12 step 6.

The claim under test is that the corpus is a *function* of the archive: the same page
always lands at the same path with the same bytes, a page that moves leaves nothing
behind, and the index is fully rebuildable from the files. Each REGRESSION here is a
defect step 6 found by running the real thing, not a hypothetical.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from scraper.records import Extracted
from scraper.store import layout, writer
from scraper.store.index import Index


def record(**kw) -> Extracted:
    base = {
        "title": "Delta Lake", "markdown": "Body text. " * 20,
        "canonical_url": "https://docs.databricks.com/aws/en/delta/x",
        "source_url": "https://docs.databricks.com/aws/en/delta/x",
        "company": "databricks", "source_id": "databricks-docs", "category": "delta",
        "extractor": "docusaurus", "extractor_version": "4",
        "updated_date": date(2026, 7, 10), "raw_sha256": "abc123",
    }
    return Extracted(**{**base, **kw})


@pytest.fixture
def data_dir(tmp_path):
    return tmp_path / "data"


# --- layout ---------------------------------------------------------------

def test_path_is_company_category_month_slug(data_dir):
    path = layout.path_for(record(), data_dir)
    assert path == data_dir / "databricks/delta/2026-07/aws-en-delta-x.md"


def test_undated_pages_get_their_own_bucket(data_dir):
    path = layout.path_for(record(updated_date=None), data_dir)
    assert path.parent.name == layout.UNDATED


def test_published_date_is_the_fallback(data_dir):
    rec = record(updated_date=None, published_date=date(2024, 3, 2))
    assert layout.path_for(rec, data_dir).parent.name == "2024-03"


def test_category_cannot_escape_the_corpus_root(data_dir):
    """A category is a URL path segment, and a URL can contain `..`."""
    for hostile in ("..", "/../..", ".", ""):
        path = layout.path_for(record(category=hostile), data_dir)
        assert data_dir.resolve() in path.resolve().parents


def test_nested_category_stays_one_segment(data_dir):
    path = layout.path_for(record(category="sql/language-manual"), data_dir)
    assert path.parent.parent.name == "sql-language-manual"


# --- writer ---------------------------------------------------------------

def test_frontmatter_round_trips(data_dir):
    rec = record(description="A storage layer.", breadcrumbs=["Tables", "Delta"],
                 code_languages=["sql"])
    front, body = writer.parse(writer.write(rec, data_dir).path)
    assert front["title"] == "Delta Lake"
    assert front["updated_date"] == date(2026, 7, 10)      # a date, not a quoted string
    assert front["breadcrumbs"] == ["Tables", "Delta"]
    assert front["extractor"] == "docusaurus@4"
    assert front["raw_sha256"] == "abc123"
    assert body.strip() == rec.markdown.strip()


def test_empty_fields_are_omitted(data_dir):
    front, _ = writer.parse(writer.write(record(), data_dir).path)
    assert "description" not in front and "breadcrumbs" not in front


def test_rewriting_the_same_page_is_byte_identical(data_dir):
    """REGRESSION: `extracted_at` was restamped on every pass.

    A `--force` re-extraction is the normal way to fix an extractor, and it touched all
    6,301 files even when not one word of content differed — every downstream consumer
    (git, rsync, an embedding pipeline) saw a corpus-wide change that was pure noise.
    """
    first = writer.write(record(), data_dir)
    before = first.path.read_bytes(), first.path.stat().st_mtime_ns

    second = writer.write(record(), data_dir)
    assert second.changed is False
    assert second.extracted_at == first.extracted_at
    assert (second.path.read_bytes(), second.path.stat().st_mtime_ns) == before


def test_a_real_change_is_written(data_dir):
    writer.write(record(), data_dir)
    result = writer.write(record(markdown="Something else entirely. " * 20), data_dir)
    assert result.changed is True
    assert "Something else entirely" in result.path.read_text()


def test_metadata_only_change_is_written(data_dir):
    """The body is unchanged but the page is not: the title moved."""
    writer.write(record(), data_dir)
    assert writer.write(record(title="Delta Lake (renamed)"), data_dir).changed is True


def test_a_corrupt_existing_file_is_replaced(data_dir):
    path = writer.write(record(), data_dir).path
    path.write_text("not frontmatter at all")
    assert writer.write(record(), data_dir).changed is True


def test_remove_takes_the_empty_directories_with_it(data_dir):
    path = writer.write(record(), data_dir).path
    writer.remove(path, data_dir)
    assert not path.exists()
    assert not (data_dir / "databricks").exists()
    assert data_dir.exists(), "the corpus root itself must survive"


def test_remove_keeps_directories_that_still_hold_pages(data_dir):
    keep = writer.write(record(source_url="https://docs.databricks.com/aws/en/delta/y",
                               canonical_url="https://docs.databricks.com/aws/en/delta/y"),
                        data_dir).path
    writer.remove(writer.write(record(), data_dir).path, data_dir)
    assert keep.exists()


# --- index ----------------------------------------------------------------

@pytest.fixture
def index(tmp_path):
    with Index(tmp_path / "index.db") as idx:
        yield idx


def test_upsert_then_read_back(index, data_dir):
    rec = record()
    result = writer.write(rec, data_dir)
    index.upsert(rec, result.path, content_hash="h", raw_sha256="abc123",
                 extracted_at=result.extracted_at)
    row = index.get(rec.source_url)
    assert row["status"] == "ok" and row["category"] == "delta"
    assert index.owner_of(result.path) == rec.source_url


def test_needs_extract_covers_new_changed_and_revised(index, data_dir):
    rec = record()
    url = rec.source_url
    assert index.needs_extract(url) is True                        # never seen

    result = writer.write(rec, data_dir)
    index.upsert(rec, result.path, content_hash="h", raw_sha256="abc123")
    assert index.needs_extract(url, raw_sha256="abc123", extractor_version="4") is False
    assert index.needs_extract(url, raw_sha256="NEW", extractor_version="4") is True
    assert index.needs_extract(url, raw_sha256="abc123", extractor_version="5") is True


def test_failures_are_kept_and_retried(index):
    index.record_failure("https://x/a", "databricks", status="quality_failed", error="too short")
    assert index.get("https://x/a")["error"] == "too short"
    assert index.needs_extract("https://x/a") is True
    assert index.counts()["quality_failed"] == 1


def test_duplicate_is_settled_not_retried(index, data_dir):
    """A second URL naming one document is resolved, so re-extracting it changes nothing."""
    index.record_duplicate("https://x/a/", "databricks", file_path=data_dir / "f.md",
                           duplicate_of="https://x/a", extractor_version="4",
                           raw_sha256="abc123")
    assert index.counts()["duplicate"] == 1
    assert index.needs_extract("https://x/a/", raw_sha256="abc123",
                               extractor_version="4") is False
    assert index.owner_of(data_dir / "f.md") is None, "a duplicate row must not own the file"


def test_orphans_are_files_no_row_claims(index, data_dir):
    rec = record()
    result = writer.write(rec, data_dir)
    index.upsert(rec, result.path, content_hash="h")
    stale = data_dir / "databricks/delta/2026-06/aws-en-delta-x.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("left behind")
    assert index.orphans(data_dir) == [stale]


def test_rebuild_restores_the_index_from_the_files(index, data_dir):
    """REGRESSION: `raw_sha256` was not in the frontmatter, so a rebuilt index could not
    tell whether a page was current and re-extracted the entire corpus."""
    rec = record(description="A storage layer.")
    result = writer.write(rec, data_dir)
    index.upsert(rec, result.path, content_hash=writer.content_hash(rec.markdown),
                 raw_sha256="abc123", extracted_at=result.extracted_at)
    before = index.get(rec.source_url)

    assert index.rebuild(data_dir) == 1
    after = index.get(rec.source_url)
    assert after == before

    assert index.needs_extract(rec.source_url, raw_sha256="abc123",
                               extractor_version="4") is False


def test_readers_are_not_locked_out_by_a_writer(index, tmp_path):
    """Extraction reads `fetch.db` while a two-hour fetch writes it, so WAL is required."""
    assert index.conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_body_size_is_recorded_and_ranked(index, data_dir):
    """A handful of API-reference pages are 4 MB; the run summary should say so."""
    small, big = record(), record(
        markdown="x" * 5000,
        source_url="https://docs.databricks.com/aws/en/delta/big",
        canonical_url="https://docs.databricks.com/aws/en/delta/big")
    for rec in (small, big):
        index.upsert(rec, writer.write(rec, data_dir).path, content_hash="h")

    assert index.get(small.source_url)["body_chars"] == small.body_chars
    assert [p["url"] for p in index.largest(1)] == [big.source_url]


def test_upsert_is_keyed_on_url_not_appended(index, data_dir):
    rec = record()
    for _ in range(3):
        index.upsert(rec, writer.write(rec, data_dir).path, content_hash="h")
    assert len(index.query()) == 1


def test_extracted_at_matches_the_file(index, data_dir):
    """The index must agree with the file, or `rebuild` would not be a no-op."""
    rec = record()
    result = writer.write(rec, data_dir, extracted_at=datetime(2026, 8, 1, tzinfo=UTC))
    index.upsert(rec, result.path, content_hash="h", extracted_at=result.extracted_at)
    front, _ = writer.parse(result.path)
    assert index.get(rec.source_url)["extracted_at"] == front["extracted_at"]
