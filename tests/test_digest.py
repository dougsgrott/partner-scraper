"""Phase 2 compression — docs/changefeed-phase-2.md.

The claim under test is the one the architecture rests on: a whole run of changes fits in
one context window, and **nothing is dropped to make it fit**. Everything here runs with no
model, no API key, and no network, which is the point of keeping compression separate from
the session that consumes it.
"""

from __future__ import annotations

import pytest

from changefeed import classify, diff, snapshot
from changefeed.db import ChangeDB
from changefeed.digest import compress, compress_run
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
    def __init__(self, tmp_path):
        self.data = tmp_path / "data"
        self.index_db = tmp_path / "index.db"
        self.changes_db = tmp_path / "changes.db"
        self.blob_dir = tmp_path / "blobs"

    def populate(self, records) -> None:
        index = Index(self.index_db)
        index.conn.execute("DELETE FROM pages")
        index.conn.commit()
        for rec in records:
            result = writer.write(rec, self.data)
            index.upsert(rec, result.path, content_hash=writer.content_hash(rec.markdown),
                         fingerprint="fp1", body_fingerprint="bf1")
        index.close()

    def snap(self, label=None):
        return snapshot.take(label=label, index_db=self.index_db,
                             changes_db=self.changes_db, blob_dir=self.blob_dir)

    def run(self):
        with ChangeDB(self.changes_db) as db:
            before, after = db.last_two()
            result = diff.compare(before, after, db=db, blob_dir=self.blob_dir)
        return compress_run(result, blob_dir=self.blob_dir)


@pytest.fixture
def corpus(tmp_path):
    return Corpus(tmp_path)


# --- the no-filter promise ------------------------------------------------

def test_every_change_appears_in_the_compressed_run(corpus):
    """The property the architecture is sold on. A digest that silently omits things
    cannot be audited, and the reader has no way to notice the omission."""
    corpus.populate([record("a"), record("b"), record("c")])
    corpus.snap()
    corpus.populate([
        record("a", markdown="# Page a\n\nThis parameter is no longer supported."),
        record("b", category="streaming"),          # moved
        record("d"),                                # added; c removed
    ])
    corpus.snap()

    with ChangeDB(corpus.changes_db) as db:
        before, after = db.last_two()
        result = diff.compare(before, after, db=db, blob_dir=corpus.blob_dir)
    run = compress_run(result, blob_dir=corpus.blob_dir)

    assert len(run.records) == len(result.changes)
    assert {r.url for r in run.records} == {c.url for c in result.changes}


def test_low_value_kinds_are_terse_but_still_present(corpus):
    """Nothing is dropped; verbosity varies. A moved page has no prose worth quoting."""
    corpus.populate([record("a")])
    corpus.snap()
    corpus.populate([record("a", category="streaming")])
    corpus.snap()

    run = corpus.run()

    assert len(run.records) == 1
    rendered = run.records[0].render()
    assert "MOVED" in rendered
    assert "::" not in rendered          # no excerpt for a moved page


# --- the excerpt ----------------------------------------------------------

def test_status_language_leads_the_excerpt():
    """Reading a sample of 64 diffs showed status lines are what distinguish a breaking
    change from a reword, so they must survive a 280-character budget."""
    before = "# T\n\n" + "Filler prose that is long and unremarkable. " * 6 + "\nIt is supported."
    after = "# T\n\n" + "Filler prose that is long and unremarkable. " * 6 + "\nIt is no longer supported."

    change = diff.PageChange(
        "https://x.test/en/a", diff.MODIFIED, classify.CONTENT, classify.SUBSTANTIVE,
        {"content_hash": "a" * 64}, {"content_hash": "b" * 64})

    import tempfile

    from changefeed import blobs
    with tempfile.TemporaryDirectory() as d:
        blobs.write("a" * 64, before, d)
        blobs.write("b" * 64, after, d)
        rec = compress(change, blob_dir=d)

    assert "no longer supported" in rec.excerpt
    assert len(rec.excerpt) <= 280


def test_an_unreadable_body_says_so_rather_than_going_blank(corpus):
    """Silence would read as 'nothing changed'; the record must state it could not look."""
    change = diff.PageChange(
        "https://x.test/en/a", diff.MODIFIED, classify.CONTENT, classify.SUBSTANTIVE,
        {"content_hash": "c" * 64}, {"content_hash": "d" * 64})

    rec = compress(change, blob_dir="/nonexistent")

    assert "unavailable" in rec.excerpt


# --- shape and size -------------------------------------------------------

def test_records_are_ordered_by_severity(corpus):
    corpus.populate([record("aaa"), record("zzz")])
    corpus.snap()
    corpus.populate([
        record("aaa", markdown="# Page aaa\n\n" + "Reworded prose here. " * 40),
        record("zzz", markdown="# Page zzz\n\nThis parameter is no longer supported."),
    ])
    corpus.snap()

    run = corpus.run()

    assert [r.slug for r in run.records] == ["zzz", "aaa"]


def test_the_slug_drops_the_shared_url_prefix(corpus):
    """A thousand records of near-identical prefix is pure cost; tools return full URLs."""
    corpus.populate([record("a")])
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n\nNow deprecated.")])
    corpus.snap()

    assert corpus.run().records[0].slug == "a"


def test_the_header_orients_the_reader(corpus):
    corpus.populate([record("a")])
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n\nNo longer supported.")])
    corpus.snap()

    header = corpus.run().header()

    assert "modified 1" in header
    assert "s=status" in header          # the signal legend


def test_compression_is_deterministic(corpus):
    """A digest is re-run when a prompt changes; the input must not move underneath it."""
    corpus.populate([record("a"), record("b")])
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n\nDeprecated now."), record("b")])
    corpus.snap()

    assert corpus.run().render() == corpus.run().render()


def test_the_excerpt_marks_which_side_each_line_came_from():
    """Direction carries the meaning. "the TypeScript and Ruby tool runners support
    compaction" says Python was *dropped* only if you know it is the new line — the real
    case this caught, where an unmarked excerpt could be read as the exact opposite."""
    import tempfile

    from changefeed import blobs
    before = "# T\n\nPython, TypeScript and Ruby runners support compaction."
    after = "# T\n\nTypeScript and Ruby runners support compaction."

    change = diff.PageChange(
        "https://x.test/en/a", diff.MODIFIED, classify.CONTENT, classify.SUBSTANTIVE,
        {"content_hash": "e" * 64}, {"content_hash": "f" * 64})
    with tempfile.TemporaryDirectory() as d:
        blobs.write("e" * 64, before, d)
        blobs.write("f" * 64, after, d)
        rec = compress(change, blob_dir=d)

    assert "-Python, TypeScript and Ruby" in rec.excerpt
    assert "+TypeScript and Ruby" in rec.excerpt
