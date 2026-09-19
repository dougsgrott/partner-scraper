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

    def populate(self, records, *, fingerprint: str | None = "fp1",
                 body_fingerprint: str | None = "bf1") -> None:
        """Write records to disk and rebuild the manifest to match, as extract does.

        The two fingerprints move independently on purpose: `fingerprint`
        (`output_fingerprint`) also covers the writer and layout, so it can move when
        nothing about the body did. Attribution must follow `body_fingerprint` alone.
        """
        index = Index(self.index_db)
        index.conn.execute("DELETE FROM pages")
        index.conn.commit()
        for rec in records:
            result = writer.write(rec, self.data)
            index.upsert(rec, result.path,
                         content_hash=writer.content_hash(rec.markdown),
                         fingerprint=fingerprint,
                         body_fingerprint=body_fingerprint)
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
    happened. Every page here moves its content hash *and* its body fingerprint, which
    is exactly the signature of a re-extraction.
    """
    corpus.populate([record("a"), record("b"), record("c")],
                    fingerprint="fp1", body_fingerprint="bf1")
    corpus.snap()
    corpus.populate(
        [record(s, markdown=f"# Page {s}\n\nConverted by a new extractor. " * 5)
         for s in ("a", "b", "c")],
        fingerprint="fp2", body_fingerprint="bf2",
    )
    corpus.snap()

    result = corpus.diff_last_two()

    assert len(result.by_kind(diff.MODIFIED)) == 3
    assert len(result.by_cause(classify.PIPELINE)) == 3
    assert result.by_cause(classify.CONTENT) == []
    assert result.feed() == []


def test_a_missing_fingerprint_is_unattributed_rather_than_assumed(corpus):
    """A rebuilt index carries no fingerprint — say so instead of blaming the vendor."""
    corpus.populate([record("a")], fingerprint=None, body_fingerprint=None)
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n\nDifferent. " * 5)],
                    fingerprint=None, body_fingerprint=None)
    corpus.snap()

    result = corpus.diff_last_two()

    assert len(result.by_cause(classify.UNKNOWN)) == 1
    assert result.feed() == []


def test_a_version_bump_without_a_fingerprint_still_reads_as_pipeline(corpus):
    corpus.populate([record("a")], fingerprint=None, body_fingerprint=None)
    corpus.snap()
    corpus.populate(
        [record("a", markdown="# Page a\n\nDifferent. " * 5, extractor_version="5")],
        fingerprint=None, body_fingerprint=None,
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
    corpus.populate([record("a")], fingerprint="fp1", body_fingerprint="bf1")
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n\nRe-extracted. " * 5)],
                    fingerprint="fp2", body_fingerprint="bf2")
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
    # The lexicon that ranked these changes — without it, reports produced by different
    # classifiers compare as if they were the same instrument (issue/accuracy/02).
    assert payload["classify_version"] == classify.CLASSIFY_VERSION


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


def test_a_writer_only_change_is_still_the_vendors_change(corpus):
    """The regression for the bug that cost this feature its first real measurement.

    `output_fingerprint` covers the writer and the layout, neither of which can alter a
    word of a page's body. When a one-line `writer.py` edit moved it — alongside a change
    to the fingerprint formula itself — 594 genuine Databricks changes were reported as
    our own churn. Here `output_fingerprint` moves and `body_fingerprint` does not, which
    is exactly that shape.
    """
    corpus.populate([record("a")], fingerprint="fp1", body_fingerprint="bf1")
    corpus.snap()
    corpus.populate(
        # A real vendor edit, not a reword: the limit moved, so it must reach the feed.
        [record("a", markdown="# Page a\n\nThe cap is 5000 rows. " * 5)],
        fingerprint="fp2", body_fingerprint="bf1")
    corpus.snap()

    result = corpus.diff_last_two()

    assert [c.cause for c in result.by_kind(diff.MODIFIED)] == [classify.CONTENT]
    assert result.by_cause(classify.PIPELINE) == []
    assert len(result.feed()) == 1


def test_attribution_ignores_output_fingerprint_entirely():
    """Even with `output_fingerprint` disagreeing, the body hash decides."""
    before = {"body_fingerprint": "bf1", "output_fingerprint": "fp1", "extractor": "d@7"}
    after = {"body_fingerprint": "bf1", "output_fingerprint": "fp2", "extractor": "d@7"}

    assert classify.attribute(before, after) == classify.CONTENT
    assert classify.attribute(before, {**after, "body_fingerprint": "bf2"}) \
        == classify.PIPELINE


def test_a_snapshot_predating_body_fingerprint_is_unattributed():
    """Snapshots taken before the column existed must say `unknown`, not guess.

    Reporting them as `content` would be a guess in the vendor's favour; reporting them as
    `pipeline` is the wrong answer this split exists to stop giving.
    """
    old = {"body_fingerprint": None, "output_fingerprint": "fp1", "extractor": "d@7"}
    new = {"body_fingerprint": "bf1", "output_fingerprint": "fp2", "extractor": "d@7"}

    assert classify.attribute(old, new) == classify.UNKNOWN


def test_the_history_database_gains_a_column_without_losing_a_row(tmp_path):
    """`changes.db` is the only copy of the corpus's past — migrating must be additive.

    `index.db` can drop its table and rebuild from `data/`; there is nothing to rebuild
    this from, so the migration is tested against an already-populated database rather
    than only a fresh one.
    """
    import sqlite3

    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        "CREATE TABLE snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, taken_at TEXT NOT NULL,"
        " label TEXT, page_count INTEGER NOT NULL DEFAULT 0, note TEXT);"
        "CREATE TABLE page_versions (snapshot_id INTEGER NOT NULL, url TEXT NOT NULL,"
        " company TEXT, source_id TEXT, category TEXT, title TEXT, description TEXT,"
        " updated_date TEXT, content_hash TEXT NOT NULL, output_fingerprint TEXT,"
        " extractor TEXT, body_chars INTEGER, file_path TEXT,"
        " PRIMARY KEY (snapshot_id, url));"
        "INSERT INTO snapshots (taken_at, label, page_count) VALUES ('2026-08-29', 'old', 1);"
        "INSERT INTO page_versions (snapshot_id, url, content_hash, extractor)"
        " VALUES (1, 'https://x.test/a', 'deadbeef', 'docusaurus@7');"
    )
    conn.commit()
    conn.close()

    with ChangeDB(path) as db:
        cols = {r["name"] for r in db.conn.execute("PRAGMA table_info(page_versions)")}
        assert "body_fingerprint" in cols

        versions = db.versions(1)
        assert versions["https://x.test/a"]["content_hash"] == "deadbeef"
        assert versions["https://x.test/a"]["body_fingerprint"] is None
        assert db.snapshot(1).label == "old"


def test_an_unchanged_wider_fingerprint_clears_a_page():
    """`output_fingerprint` covers a superset of `body_fingerprint`.

    An unchanged superset proves the subset is unchanged, so a page with no
    `body_fingerprint` on either side is still safely the vendor's. This is what keeps
    snapshots taken before the column existed useful instead of wholly unattributed.
    """
    before = {"body_fingerprint": None, "output_fingerprint": "fp1", "extractor": "d@7"}
    after = {"body_fingerprint": None, "output_fingerprint": "fp1", "extractor": "d@7"}

    assert classify.attribute(before, after) == classify.CONTENT


def test_a_changed_wider_fingerprint_convicts_nobody():
    """A moved `output_fingerprint` may be entirely writer or layout — it proves nothing.

    This is the 594-page case: reporting it as `pipeline` was the bug, and reporting it as
    `content` would be the opposite guess. Neither is supportable, so say so.
    """
    before = {"body_fingerprint": None, "output_fingerprint": "fp1", "extractor": "d@7"}
    after = {"body_fingerprint": None, "output_fingerprint": "fp2", "extractor": "d@7"}

    assert classify.attribute(before, after) == classify.UNKNOWN


# --- severity ranking -----------------------------------------------------

def test_status_language_outranks_a_larger_prose_edit():
    """The signal reading proved most valuable, and the one the first version missed.

    A one-line "no longer supported" matters more than a paragraph rewritten around it,
    and neither a structural comparison nor a size comparison can tell them apart.
    """
    before = "The `pipelines.channel` property selects a runtime channel."
    after = "The `pipelines.channel` property is no longer supported."
    deprecation = classify.severity(classify.signals(before, after))

    prose_before = "This page explains the feature in practice. " * 20
    prose_after = "This page describes the behaviour in practice. " * 20
    reword = classify.severity(classify.signals(prose_before, prose_after))

    assert deprecation > reword


def test_severity_is_scale_invariant():
    """A regenerated reference page must not outrank a sharp deprecation.

    Scoring by raw volume put a page with 11,181 status-matching lines at the top of the
    feed purely because it is enormous. Density fixes that: the same evidence spread over
    a hundred times more lines is not a hundred times more urgent.
    """
    sharp = {"status": 2, "changed_lines": 2}
    bulky = {"status": 200, "changed_lines": 20_000}

    assert classify.severity(sharp) > classify.severity(bulky)


def test_the_feed_is_ordered_by_severity_not_alphabetically(corpus):
    """With ~680 substantive changes in a run, ordering is the only reduction on offer."""
    corpus.populate([record("aaa"), record("zzz")])
    corpus.snap()
    corpus.populate([
        # Alphabetically first, but merely reworded at length.
        record("aaa", markdown="# Page aaa\n\n" + "Reworded prose here. " * 60),
        # Alphabetically last, but a deprecation.
        record("zzz", markdown="# Page zzz\n\nThis parameter is no longer supported."),
    ])
    corpus.snap()

    feed = corpus.diff_last_two().feed()

    assert [c.url.rsplit("/", 1)[-1] for c in feed] == ["zzz", "aaa"]


def test_a_huge_page_falls_back_to_an_unaligned_listing(corpus):
    """`difflib` is superlinear and this corpus holds 6 MB pages; aligning them took
    minutes. The fallback must be honest about what it is rather than look like a diff."""
    big = "# Page a\n" + "".join(f"line {i} of the reference\n" for i in range(30_000))
    corpus.populate([record("a", markdown=big)])
    corpus.snap()
    corpus.populate([record("a", markdown=big.replace("reference", "manual"))])
    corpus.snap()

    change = corpus.diff_last_two().by_kind(diff.MODIFIED)[0]
    rendered = diff.render_diff(change, blob_dir=corpus.blob_dir)

    assert "too large to align" in rendered
    assert "@@" not in rendered


# --- pages that disappear upstream ----------------------------------------

def test_a_page_gone_upstream_leaves_the_snapshot_and_reports_removed(corpus):
    """A 404 upstream must surface as a change; before this it surfaced as nothing.

    `FetchDB.record_error` preserves the previous archive entry, so a deleted page kept
    its last-known body, kept its `ok` index row, and reported as unchanged forever — the
    exact opposite of what the deprecation and link-rot watches need.
    """
    corpus.populate([record("a"), record("b")])
    corpus.snap()

    index = Index(corpus.index_db)
    assert index.mark_gone(record("b").source_url, status_code=404) is True
    index.close()
    corpus.snap()

    result = corpus.diff_last_two()

    assert [c.url for c in result.by_kind(diff.REMOVED)] == [record("b").source_url]


def test_a_gone_page_keeps_its_file_and_is_not_an_orphan(corpus):
    """Deleting on the strength of one HTTP response is destructive inference.

    The row still claims the file, so `--prune` leaves it alone and the integrity check
    does not start failing the moment a vendor removes a page.
    """
    corpus.populate([record("a")])
    path = next(corpus.data.rglob("*.md"))

    index = Index(corpus.index_db)
    index.mark_gone(record("a").source_url, status_code=410)
    orphans = index.orphans(corpus.data)
    row = index.get(record("a").source_url)
    index.close()

    assert path.exists()
    assert orphans == []
    assert row["status"] == "gone" and "410" in row["error"]


def test_marking_gone_is_idempotent_and_refuses_to_resurrect(corpus):
    corpus.populate([record("a")])
    index = Index(corpus.index_db)

    assert index.mark_gone(record("a").source_url, status_code=404) is True
    assert index.mark_gone(record("a").source_url, status_code=404) is False
    assert index.mark_gone("https://docs.databricks.com/aws/en/never-seen") is False
    index.close()


def test_the_history_can_be_backed_up_and_is_incremental(tmp_path, corpus):
    """`changes.db` is the only artifact here that cannot be rebuilt from anything else.

    The blob store is content-addressed and append-only, so a second backup copies only
    what is new — which is what makes backing up after every run affordable.
    """
    from changefeed import db as db_module

    corpus.populate([record("a"), record("b")])
    corpus.snap()

    out = tmp_path / "backup"
    first_bytes, first_blobs = db_module.backup(
        out, db_path=corpus.changes_db, blob_dir=corpus.blob_dir)

    assert first_blobs == 2
    assert (out / "changes.db").exists()

    second_bytes, second_blobs = db_module.backup(
        out, db_path=corpus.changes_db, blob_dir=corpus.blob_dir)

    assert second_blobs == 0                    # nothing new to copy
    assert second_bytes < first_bytes


def test_a_backed_up_history_is_readable(tmp_path, corpus):
    corpus.populate([record("a")])
    corpus.snap("baseline")

    from changefeed import db as db_module
    out = tmp_path / "backup"
    db_module.backup(out, db_path=corpus.changes_db, blob_dir=corpus.blob_dir)

    with ChangeDB(out / "changes.db") as restored:
        assert [s.label for s in restored.snapshots()] == ["baseline"]
        assert len(restored.versions(1)) == 1
