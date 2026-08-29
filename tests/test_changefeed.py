"""The change feed — docs/changefeed-plan.md.

The claim under test is that the corpus now has a past tense that can be trusted: a
snapshot of an unchanged corpus costs nothing, a diff of two identical snapshots is empty,
and — the one that matters most — **our own extractor churn is never reported as a vendor
change**. That last test is the reason this package has an attribution step at all.
"""

from __future__ import annotations

import pytest

from changefeed import blobs, classify, diff, report, snapshot
from changefeed.db import ChangeDB
from scraper.records import Extracted
from scraper.store import writer
from scraper.store.index import Index


def record(slug: str = "delta", **kw) -> Extracted:
    base = {
        "title": f"Page {slug}",
        "markdown": f"# Page {slug}\n\nSome prose about {slug}. " * 5,
        "canonical_url": f"https://docs.databricks.com/aws/en/{slug}",
        "source_url": f"https://docs.databricks.com/aws/en/{slug}",
        "company": "databricks", "source_id": "databricks-docs", "category": "delta",
        "extractor": "docusaurus", "extractor_version": "4",
    }
    return Extracted(**{**base, **kw})


class Corpus:
    """A throwaway corpus plus the three stores the change feed reads and writes."""

    def __init__(self, tmp_path):
        self.data = tmp_path / "data"
        self.index_db = tmp_path / "index.db"
        self.changes_db = tmp_path / "changes.db"
        self.blob_dir = tmp_path / "blobs"

    def populate(self, records, *, fingerprint: str | None = "fp1") -> None:
        """Write records to disk and rebuild the manifest to match, as extract does."""
        index = Index(self.index_db)
        index.conn.execute("DELETE FROM pages")
        index.conn.commit()
        for rec in records:
            result = writer.write(rec, self.data)
            index.upsert(rec, result.path,
                         content_hash=writer.content_hash(rec.markdown),
                         fingerprint=fingerprint)
        index.close()

    def snap(self, label: str | None = None):
        return snapshot.take(label=label, index_db=self.index_db,
                             changes_db=self.changes_db, blob_dir=self.blob_dir)

    def diff_last_two(self) -> diff.DiffResult:
        with ChangeDB(self.changes_db) as db:
            before, after = db.last_two()
            return diff.compare(before, after, db=db, blob_dir=self.blob_dir)


@pytest.fixture
def corpus(tmp_path):
    return Corpus(tmp_path)


# --- the version store ----------------------------------------------------

SHA = "a" * 64


def test_blob_round_trips(tmp_path):
    assert blobs.write(SHA, "hello world", tmp_path) is True
    assert blobs.read(SHA, tmp_path) == "hello world"


def test_second_write_of_the_same_hash_adds_nothing(tmp_path):
    blobs.write(SHA, "hello world", tmp_path)
    before = blobs.total_bytes(tmp_path)

    assert blobs.write(SHA, "hello world", tmp_path) is False
    assert blobs.total_bytes(tmp_path) == before


def test_identical_content_produces_identical_files(tmp_path):
    """gzip mtime is zeroed, so a rewritten archive does not churn backups."""
    blobs.write(SHA, "same", tmp_path / "one")
    blobs.write(SHA, "same", tmp_path / "two")
    assert (blobs.path_for(SHA, tmp_path / "one").read_bytes()
            == blobs.path_for(SHA, tmp_path / "two").read_bytes())


@pytest.mark.parametrize("bad", ["../../etc/passwd", "", "xyz", "A" * 64, "a" * 63])
def test_a_bad_address_never_reaches_the_filesystem(tmp_path, bad):
    with pytest.raises(ValueError):
        blobs.path_for(bad, tmp_path)


def test_prune_removes_only_unreferenced_bodies(tmp_path):
    keep, drop = "b" * 64, "c" * 64
    blobs.write(keep, "keep me", tmp_path)
    blobs.write(drop, "drop me", tmp_path)

    removed, reclaimed = blobs.prune({keep}, tmp_path)

    assert removed == 1 and reclaimed > 0
    assert blobs.exists(keep, tmp_path)
    assert not blobs.exists(drop, tmp_path)


def test_read_or_none_tolerates_a_collected_body(tmp_path):
    assert blobs.read_or_none("d" * 64, tmp_path) is None
    assert blobs.read_or_none(None, tmp_path) is None


# --- snapshots ------------------------------------------------------------

def test_snapshot_captures_every_indexed_page(corpus):
    corpus.populate([record("a"), record("b"), record("c")])

    result = corpus.snap("baseline")

    assert result.pages == 3
    assert result.new_blobs == 3
    assert not result.hash_mismatches


def test_resnapshotting_an_unchanged_corpus_stores_no_new_bodies(corpus):
    """The property that makes a weekly history affordable."""
    corpus.populate([record("a"), record("b")])
    corpus.snap("first")

    second = corpus.snap("second")

    assert second.pages == 2
    assert second.new_blobs == 0
    assert second.bytes_added == 0


def test_snapshot_notices_a_file_that_disagrees_with_its_frontmatter(corpus):
    corpus.populate([record("a")])
    path = next(corpus.data.rglob("*.md"))
    path.write_text(path.read_text().replace("Some prose", "Tampered prose"), encoding="utf-8")

    result = corpus.snap()

    assert len(result.hash_mismatches) == 1


def test_snapshot_survives_an_index_pointing_at_a_missing_file(corpus):
    corpus.populate([record("a"), record("b")])
    next(corpus.data.rglob("*.md")).unlink()

    result = corpus.snap()

    assert result.pages == 1
    assert len(result.missing_files) == 1


# --- diff kinds -----------------------------------------------------------

def test_two_snapshots_of_an_untouched_corpus_differ_in_nothing(corpus):
    corpus.populate([record("a"), record("b")])
    corpus.snap()
    corpus.snap()

    assert corpus.diff_last_two().is_empty


def test_added_and_removed_pages(corpus):
    corpus.populate([record("a")])
    corpus.snap()
    corpus.populate([record("b")])
    corpus.snap()

    result = corpus.diff_last_two()

    assert [c.url for c in result.by_kind(diff.ADDED)] == [record("b").source_url]
    assert [c.url for c in result.by_kind(diff.REMOVED)] == [record("a").source_url]


def test_a_changed_body_is_a_modification_attributed_to_the_vendor(corpus):
    corpus.populate([record("a")])
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n\nRewritten entirely, at length. " * 5)])
    corpus.snap()

    changes = corpus.diff_last_two().by_kind(diff.MODIFIED)

    assert len(changes) == 1
    assert changes[0].cause == classify.CONTENT


def test_a_page_that_only_changes_filing_is_moved_not_modified(corpus):
    corpus.populate([record("a")])
    corpus.snap()
    corpus.populate([record("a", category="streaming")])
    corpus.snap()

    result = corpus.diff_last_two()

    assert len(result.by_kind(diff.MOVED)) == 1
    assert not result.by_kind(diff.MODIFIED)


def test_a_page_that_only_changes_description_is_metadata(corpus):
    corpus.populate([record("a")])
    corpus.snap()
    corpus.populate([record("a", description="Now described.")])
    corpus.snap()

    result = corpus.diff_last_two()

    assert len(result.by_kind(diff.METADATA)) == 1
    assert not result.by_kind(diff.MODIFIED)


# --- attribution: the regression this package exists for ------------------

def test_our_own_extractor_churn_is_never_reported_as_vendor_change(corpus):
    """The MDX conversion rewrote all 566 Anthropic pages in one pass.

    Without attribution that run would have reported 566 upstream changes that never
    happened. Every page here moves its content hash *and* its output fingerprint, which
    is exactly the signature of a re-extraction.
    """
    corpus.populate([record("a"), record("b"), record("c")], fingerprint="fp1")
    corpus.snap()
    corpus.populate(
        [record(s, markdown=f"# Page {s}\n\nConverted by a new extractor. " * 5)
         for s in ("a", "b", "c")],
        fingerprint="fp2",
    )
    corpus.snap()

    result = corpus.diff_last_two()

    assert len(result.by_kind(diff.MODIFIED)) == 3
    assert len(result.by_cause(classify.PIPELINE)) == 3
    assert result.by_cause(classify.CONTENT) == []
    assert result.feed() == []


def test_a_missing_fingerprint_is_unattributed_rather_than_assumed(corpus):
    """A rebuilt index carries no fingerprint — say so instead of blaming the vendor."""
    corpus.populate([record("a")], fingerprint=None)
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n\nDifferent. " * 5)], fingerprint=None)
    corpus.snap()

    result = corpus.diff_last_two()

    assert len(result.by_cause(classify.UNKNOWN)) == 1
    assert result.feed() == []


def test_a_version_bump_without_a_fingerprint_still_reads_as_pipeline(corpus):
    corpus.populate([record("a")], fingerprint=None)
    corpus.snap()
    corpus.populate(
        [record("a", markdown="# Page a\n\nDifferent. " * 5, extractor_version="5")],
        fingerprint=None,
    )
    corpus.snap()

    assert len(corpus.diff_last_two().by_cause(classify.PIPELINE)) == 1


# --- weighting ------------------------------------------------------------

def test_reflowed_whitespace_is_noise():
    assert classify.weigh("one two three", "one   two\nthree") == classify.NOISE


def test_a_changed_link_is_substantive():
    before = "See the [guide](https://example.com/a) for details."
    after = "See the [guide](https://example.com/b) for details."
    assert classify.weigh(before, after) == classify.SUBSTANTIVE


def test_a_changed_limit_is_substantive():
    assert classify.weigh("The cap is 1000 rows.", "The cap is 5000 rows.") \
        == classify.SUBSTANTIVE


def test_a_small_prose_rewording_ranks_low():
    before = "This page explains how the feature works in practice."
    after = "This page describes how the feature behaves in practice."
    assert classify.weigh(before, after) == classify.LOW


def test_an_unreadable_body_is_never_assumed_harmless():
    assert classify.weigh(None, "anything") == classify.SUBSTANTIVE


def test_ranked_down_changes_are_listed_not_dropped(corpus):
    corpus.populate([record("a", markdown="# Page a\n\nThe feature works well here.")])
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n\nThe feature behaves well here.")])
    corpus.snap()

    result = corpus.diff_last_two()

    assert result.feed() == []
    assert len(result.suppressed()) == 1


# --- rendering ------------------------------------------------------------

def test_tables_have_no_blank_line_after_the_separator():
    """`validation-scorecard.md` shipped broken exactly this way."""
    table = report._table(["a", "b"], [["1", "2"], ["3", "4"]])
    lines = table.split("\n")

    assert lines[1].startswith("|---")
    assert lines[2] == "| 1 | 2 |"
    assert "" not in lines


def test_report_of_an_empty_diff_says_so(corpus):
    corpus.populate([record("a")])
    corpus.snap()
    corpus.snap()

    text = report.render(corpus.diff_last_two(), blob_dir=corpus.blob_dir)

    assert "Nothing changed" in text


def test_report_separates_our_churn_from_the_vendor_feed(corpus):
    corpus.populate([record("a")], fingerprint="fp1")
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n\nRe-extracted. " * 5)],
                    fingerprint="fp2")
    corpus.snap()

    text = report.render(corpus.diff_last_two(), blob_dir=corpus.blob_dir)

    assert "Our own churn" in text
    assert "The vendor did not edit them" in text
    assert "No substantive vendor changes" in text


def test_a_huge_diff_is_truncated_and_says_so(corpus):
    corpus.populate([record("a", markdown="# Page a\n" + "original line\n" * 2000)])
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n" + "rewritten line\n" * 2000)])
    corpus.snap()

    change = corpus.diff_last_two().by_kind(diff.MODIFIED)[0]
    rendered = diff.render_diff(change, blob_dir=corpus.blob_dir, max_lines=50)

    assert "diff truncated" in rendered
    assert len(rendered.splitlines()) <= 51


def test_json_report_keeps_every_change_including_ranked_down_ones(corpus):
    corpus.populate([record("a"), record("b")])
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n\nThe feature behaves well.")])
    corpus.snap()

    payload = report.to_json(corpus.diff_last_two())

    assert payload["counts"]["removed"] == 1
    assert len(payload["changes"]) == len(corpus.diff_last_two().changes)


# --- history --------------------------------------------------------------

def test_history_records_every_version_of_a_page(corpus):
    corpus.populate([record("a")])
    corpus.snap("one")
    corpus.populate([record("a", markdown="# Page a\n\nSecond version. " * 5)])
    corpus.snap("two")

    with ChangeDB(corpus.changes_db) as db:
        history = db.history(record("a").source_url)

    assert len(history) == 2
    assert history[0]["content_hash"] != history[1]["content_hash"]
    assert blobs.read(history[0]["content_hash"], corpus.blob_dir).startswith("# Page a")


def test_snapshots_resolve_by_label_and_by_position(corpus):
    corpus.populate([record("a")])
    corpus.snap("baseline")
    corpus.snap("after")

    with ChangeDB(corpus.changes_db) as db:
        assert db.resolve("baseline").label == "baseline"
        assert db.resolve("latest").label == "after"
        assert db.resolve("previous").label == "baseline"
        assert db.resolve("#1").id == 1
        assert db.resolve("nope") is None


def test_the_terminal_summary_names_an_empty_diff(corpus):
    """Built inline, `"  " + join(...) or "no differences"` never reached the fallback."""
    corpus.populate([record("a")])
    corpus.snap()
    corpus.snap()

    lines = report.summarise(corpus.diff_last_two()).splitlines()

    assert "no differences" in lines[1]
    assert not any(line.strip() == "" for line in lines)


def test_headings_do_not_say_one_changes(corpus):
    """Reports get shared; "Ranked down - 1 changes" reads as a bug in the tool."""
    corpus.populate([record("a")])
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n\nSee [docs](https://x.test/b).")])
    corpus.snap()

    text = report.render(corpus.diff_last_two(), blob_dir=corpus.blob_dir)

    assert "1 substantive vendor change" in text
    assert "1 changes" not in text
