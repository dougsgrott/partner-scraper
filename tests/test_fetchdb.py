"""fetch.db bookkeeping: validators, state transitions, and what a 304 must not destroy."""

from __future__ import annotations

import pytest

from scraper.fetch import FetchDB

URL = "https://docs.databricks.com/aws/en/delta/"


@pytest.fixture
def db(tmp_path):
    with FetchDB(tmp_path / "fetch.db") as fdb:
        yield fdb


@pytest.fixture
def archived(tmp_path, db):
    """A URL already fetched once, with its archive file actually on disk."""
    raw = tmp_path / "delta.html.gz"
    raw.write_bytes(b"gzipped-ish")
    db.record_ok(
        URL, "databricks-docs",
        raw_path=raw, raw_sha256="abc123", tier="http",
        content_type="text/html", etag='"v1"', last_modified="Fri, 14 Aug 2026 21:30:20 GMT",
    )
    return raw


def test_record_and_get(db, archived):
    row = db.get(URL)
    assert row["state"] == "ok"
    assert row["source_id"] == "databricks-docs"
    assert row["etag"] == '"v1"'
    assert row["final_url"] == URL
    assert row["attempts"] == 1


def test_unknown_url_is_none(db):
    assert db.get("https://nope.example/") is None


def test_validators_returned_for_conditional_get(db, archived):
    assert db.validators(URL) == ('"v1"', "Fri, 14 Aug 2026 21:30:20 GMT")


def test_no_validators_when_archive_file_is_missing(db, archived):
    """Revalidating against a file we no longer hold would turn a 304 into a gap."""
    archived.unlink()
    assert db.validators(URL) == (None, None)


def test_no_validators_for_unknown_url(db):
    assert db.validators("https://nope.example/") == (None, None)


def test_304_keeps_the_archive_pointer(db, archived):
    """A 304 says the stored body is still current — it must not orphan it."""
    db.record_not_modified(URL, etag='"v1"')
    row = db.get(URL)
    assert row["state"] == "not_modified"
    assert row["status_code"] == 304
    assert row["raw_path"] == str(archived)      # still points at the body
    assert row["raw_sha256"] == "abc123"
    assert row["attempts"] == 2


def test_304_can_refresh_validators(db, archived):
    db.record_not_modified(URL, etag='"v2"')
    assert db.get(URL)["etag"] == '"v2"'


def test_304_without_prior_fetch_is_a_bug(db):
    with pytest.raises(KeyError):
        db.record_not_modified("https://never-fetched.example/")


def test_error_preserves_previous_archive(db, archived):
    """A failed refresh must not discard a good copy we already have."""
    db.record_error(URL, "databricks-docs", error="timeout", tier="http")
    row = db.get(URL)
    assert row["state"] == "fetch_error"
    assert row["error"] == "timeout"
    assert row["raw_path"] == str(archived)
    assert row["etag"] == '"v1"'


def test_attempts_accumulate_across_failures(db):
    for _ in range(3):
        db.record_error(URL, "s", error="boom")
    assert db.get(URL)["attempts"] == 3


def test_recovery_after_error(db):
    db.record_error(URL, "s", error="boom")
    db.record_ok(URL, "s", raw_path="p", raw_sha256="h", tier="http")
    row = db.get(URL)
    assert row["state"] == "ok"
    assert row["error"] is None


def test_skipped_is_recorded_without_an_archive(db):
    db.record_skipped(URL, "s", reason="robots")
    row = db.get(URL)
    assert row["state"] == "skipped"
    assert row["error"] == "robots"
    assert row["raw_path"] is None


def test_counts_cover_every_state(db):
    db.record_ok("https://x/1", "s", raw_path="a", raw_sha256="h", tier="http")
    db.record_error("https://x/2", "s", error="boom")
    db.record_skipped("https://x/3", "s", reason="robots")
    assert db.counts() == {"ok": 1, "not_modified": 0, "fetch_error": 1, "skipped": 1}


def test_counts_filter_by_source(db):
    db.record_ok("https://x/1", "a", raw_path="p", raw_sha256="h", tier="http")
    db.record_ok("https://x/2", "b", raw_path="q", raw_sha256="h", tier="http")
    assert db.counts(source_id="a")["ok"] == 1


def test_urls_filtered_by_state_and_source(db):
    db.record_ok("https://x/1", "a", raw_path="p", raw_sha256="h", tier="http")
    db.record_error("https://x/2", "a", error="boom")
    assert db.urls(source_id="a", state="ok") == ["https://x/1"]
    assert db.urls(source_id="b") == []


def test_raw_path_owners_feeds_collision_detection(db, archived):
    assert db.raw_path_owners() == {str(archived): URL}


def test_final_url_records_redirect_target(db):
    db.record_ok(
        "https://x.com/a", "s", raw_path="p", raw_sha256="h", tier="http",
        final_url="https://x.com/b",
    )
    assert db.get("https://x.com/a")["final_url"] == "https://x.com/b"


def test_reopening_the_db_keeps_rows(tmp_path):
    path = tmp_path / "fetch.db"
    with FetchDB(path) as first:
        first.record_ok(URL, "s", raw_path="p", raw_sha256="h", tier="http")
    with FetchDB(path) as second:
        assert second.get(URL)["state"] == "ok"
