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

    def populate(self, records, *, fingerprint: str | None = "fp1",
                 body_fingerprint: str | None = "bf1") -> None:
        index = Index(self.index_db)
        index.conn.execute("DELETE FROM pages")
        index.conn.commit()
        for rec in records:
            result = writer.write(rec, self.data)
            index.upsert(rec, result.path, content_hash=writer.content_hash(rec.markdown),
                         fingerprint=fingerprint, body_fingerprint=body_fingerprint)
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


# --- the tool layer: no model, no SDK, no network -------------------------

def _ctx(corpus):
    """A DigestContext over the corpus's latest diff."""
    from changefeed.digest.tools import DigestContext
    db = ChangeDB(corpus.changes_db)
    before, after = db.last_two()
    result = diff.compare(before, after, db=db, blob_dir=corpus.blob_dir)
    return DigestContext(result=result, db=db, blob_dir=str(corpus.blob_dir)), db


def _changed(corpus):
    corpus.populate([record("a"), record("b")])
    corpus.snap()
    corpus.populate([
        record("a", markdown="# Page a\n\nThis parameter is no longer supported."),
        record("b", markdown="# Page b\n\nThis parameter is no longer supported either."),
    ])
    corpus.snap()


async def test_record_finding_stores_a_story_spanning_pages(corpus):
    """A finding is a story, not a page — ten pages changed for one reason is one row."""
    from changefeed.digest.findings import for_pair
    from changefeed.digest.tools import make_handlers

    _changed(corpus)
    ctx, db = _ctx(corpus)
    try:
        out = await make_handlers(ctx)["record_finding"]({
            "urls": [record("a").source_url, record("b").source_url],
            "impact": "breaking",
            "kind": "deprecation",
            "summary": "the parameter is no longer supported",
        })
        assert not out.get("is_error")
        stored = for_pair(db, ctx.result.before.id, ctx.result.after.id)
    finally:
        db.close()

    assert len(stored) == 1
    assert len(stored[0].urls) == 2


async def test_a_finding_citing_a_page_that_did_not_change_is_rejected(corpus):
    """The membership test. A schema proves a finding is well-formed; only this shows it
    is about something that actually happened. A confidently-wrong citation is worse than
    a missing one, and nothing downstream would catch it."""
    from changefeed.digest.tools import make_handlers

    _changed(corpus)
    ctx, db = _ctx(corpus)
    try:
        out = await make_handlers(ctx)["record_finding"]({
            "urls": ["https://docs.databricks.com/aws/en/never-touched"],
            "impact": "breaking",
            "summary": "invented",
        })
    finally:
        db.close()

    assert out["is_error"] is True
    assert "not changes in this run" in out["content"][0]["text"]
    assert ctx.rejected == ["https://docs.databricks.com/aws/en/never-touched"]


async def test_an_unknown_impact_is_rejected(corpus):
    from changefeed.digest.tools import make_handlers

    _changed(corpus)
    ctx, db = _ctx(corpus)
    try:
        out = await make_handlers(ctx)["record_finding"]({
            "urls": [record("a").source_url], "impact": "catastrophic", "summary": "x"})
    finally:
        db.close()

    assert out["is_error"] is True


async def test_a_short_path_resolves_to_the_full_url(corpus):
    """The prompt shows slugs, so the model will answer with them."""
    from changefeed.digest.tools import make_handlers

    _changed(corpus)
    ctx, db = _ctx(corpus)
    try:
        out = await make_handlers(ctx)["get_diff"]({"url": "aws/en/a"})
    finally:
        db.close()

    assert not out.get("is_error")
    assert "no longer supported" in out["content"][0]["text"]


async def test_tools_refuse_a_url_outside_the_run(corpus):
    from changefeed.digest.tools import make_handlers

    _changed(corpus)
    ctx, db = _ctx(corpus)
    try:
        handlers = make_handlers(ctx)
        for name in ("get_diff", "read_page", "inbound_links"):
            out = await handlers[name]({"url": "https://example.test/nope"})
            assert out["is_error"] is True, name
    finally:
        db.close()


def test_a_rerun_supersedes_findings_rather_than_destroying_them(corpus):
    from changefeed.digest.findings import Finding, for_pair, supersede
    from changefeed.digest.findings import record as store

    _changed(corpus)
    _, db = _ctx(corpus)
    try:
        f = Finding(impact="breaking", summary="one", urls=[record("a").source_url])
        store(db, 1, 2, f)
        store(db, 1, 2, f)
        assert len(for_pair(db, 1, 2)) == 2

        assert supersede(db, 1, 2) == 2
        assert for_pair(db, 1, 2) == []
        # Kept, not destroyed: comparing two runs is the only stability evidence there is.
        assert len(for_pair(db, 1, 2, superseded=True)) == 2
    finally:
        db.close()


def test_the_digest_renders_grouped_by_impact():
    from changefeed.digest.findings import Finding, render

    text = render(
        [Finding(impact="additive", summary="new thing", urls=["https://x.test/a"]),
         Finding(impact="breaking", summary="removed thing", urls=["https://x.test/b"])],
        before="#1", after="#2", changes=1334)

    assert text.index("## Breaking") < text.index("## Additive")
    assert "1,334 changes" in text


async def test_findings_can_be_recorded_in_one_batch(corpus):
    """Turns are what a digest costs — every tool call re-sends the whole change list."""
    from changefeed.digest.findings import for_pair
    from changefeed.digest.tools import make_handlers

    _changed(corpus)
    ctx, db = _ctx(corpus)
    try:
        out = await make_handlers(ctx)["record_findings"]({"findings": [
            {"urls": [record("a").source_url], "impact": "breaking", "summary": "one"},
            {"urls": [record("b").source_url], "impact": "additive", "summary": "two"},
        ]})
        stored = for_pair(db, ctx.result.before.id, ctx.result.after.id)
    finally:
        db.close()

    assert not out.get("is_error")
    assert len(stored) == 2


async def test_one_bad_entry_does_not_discard_the_batch(corpus):
    """A rejected finding should cost that finding, not the nineteen beside it."""
    from changefeed.digest.findings import for_pair
    from changefeed.digest.tools import make_handlers

    _changed(corpus)
    ctx, db = _ctx(corpus)
    try:
        out = await make_handlers(ctx)["record_findings"]({"findings": [
            {"urls": [record("a").source_url], "impact": "breaking", "summary": "good"},
            {"urls": ["https://x.test/never"], "impact": "breaking", "summary": "bad"},
        ]})
        stored = for_pair(db, ctx.result.before.id, ctx.result.after.id)
    finally:
        db.close()

    assert out["is_error"] is True
    assert "recorded 1 of 2" in out["content"][0]["text"]
    assert len(stored) == 1


async def test_every_slug_the_prompt_shows_resolves(corpus):
    """The prompt shows slugs, so the model answers with slugs.

    A first version matched the full URL then fell back to fuzzy containment, which
    rejected 194 of 1,334 real slugs: `ai-gateway/` is a substring of
    `ai-gateway/query-model-services`, so the uniqueness check found several and gave up.
    A live run reported 69 rejected citations that looked like invention and were this.
    """

    _changed(corpus)
    ctx, db = _ctx(corpus)
    try:
        for change in ctx.result.changes:
            slug = change.url.split("/en/", 1)[-1]
            assert ctx.find(slug) is not None, slug
    finally:
        db.close()


async def test_a_slug_that_prefixes_others_still_resolves(corpus):
    """The exact failure above, in miniature: `a` is a prefix of `ab` and `abc`."""
    from changefeed.digest.tools import make_handlers

    corpus.populate([record("a"), record("ab"), record("abc")])
    corpus.snap()
    corpus.populate([record(s, markdown=f"# {s}\n\nNo longer supported.")
                     for s in ("a", "ab", "abc")])
    corpus.snap()
    ctx, db = _ctx(corpus)
    try:
        out = await make_handlers(ctx)["record_finding"]({
            "urls": ["a", "ab", "abc"], "impact": "breaking", "summary": "all three"})
    finally:
        db.close()

    assert not out.get("is_error"), out["content"][0]["text"]


def test_a_headline_does_not_nest_bold_markers():
    """The model writes summaries containing their own **bold**; wrapping those in bold
    again renders as literal asterisks. Headings carry the emphasis instead."""
    from changefeed.digest.findings import Finding

    f = Finding(impact="breaking", summary="Every endpoint is **Deprecated**; migrate.",
                urls=["https://x.test/en/a"])

    assert "**" not in f.headline
    assert f.render().startswith("### Every endpoint is Deprecated; migrate.")


def test_long_citation_lists_are_capped_but_counted():
    """A finding covering 26 pages is a good finding and a terrible 26-line list."""
    from changefeed.digest.findings import Finding

    f = Finding(impact="breaking", summary="one story",
                urls=[f"https://x.test/en/page-{i}" for i in range(26)])

    text = f.render(max_pages=6)

    assert text.count("\n- [") == 6
    assert "…and 20 more" in text
    assert "26 pages" in text


def test_the_digest_leads_with_what_breaks():
    from changefeed.digest.findings import Finding, render

    text = render(
        [Finding(impact="additive", summary="new thing", urls=["https://x.test/en/a"]),
         Finding(impact="breaking", summary="removed thing", urls=["https://x.test/en/b"])],
        before="#1", after="#2", changes=1334)

    assert "If you read nothing else" in text
    assert text.index("removed thing") < text.index("new thing")
    assert text.index("## At a glance") < text.index("## Breaking")


# --- attribution reaches the digest ---------------------------------------

def test_our_own_churn_never_reaches_the_model(corpus):
    """The regression for the hole phase 2 opened in phase 1's work.

    Issue 01 exists to stop us reporting our own extractor churn as vendor news. The first
    version of compression iterated every change with no notion of cause, so the next run
    after an extractor change would have described our edits as Databricks news, with
    citations and an impact rating.
    """
    corpus.populate([record("a"), record("b")], fingerprint="fp1", body_fingerprint="bf1")
    corpus.snap()
    corpus.populate(
        [record("a", markdown="# Page a\n\nRe-extracted by us. " * 5),
         record("b", markdown="# Page b\n\nThe vendor rewrote this. " * 5)],
        fingerprint="fp2", body_fingerprint="bf2")
    corpus.snap()

    run = corpus.run()

    assert run.records == []
    assert run.excluded_pipeline == 2
    assert "excluded" in run.header()


def test_unattributed_changes_are_marked_not_hidden(corpus):
    """`unknown` means nobody can say whose change it is. The model must be told, so it
    describes the text rather than asserting the vendor's intent — but it must still see
    them: 594 of 1,334 changes in the first real run were unattributed."""
    corpus.populate([record("a")], fingerprint=None, body_fingerprint=None)
    corpus.snap()
    corpus.populate([record("a", markdown="# Page a\n\nNo longer supported.")],
                    fingerprint=None, body_fingerprint=None)
    corpus.snap()

    run = corpus.run()

    assert len(run.records) == 1
    assert "(unattributed)" in run.records[0].render()
    assert "describe it cautiously" in run.header()


# --- the session layer, without a model -----------------------------------

async def test_the_session_is_wired_as_intended(corpus, monkeypatch):
    """Covers what only surfaced at runtime before: option wiring and prompt formatting.

    A wrong `ClaudeAgentOptions` field or a stray `{placeholder}` used to be discoverable
    only by spending money on a session that then failed.
    """
    import claude_agent_sdk

    from changefeed.digest import session as session_mod

    seen = {}

    async def fake_query(*, prompt, options, **_):
        seen["prompt"] = prompt
        seen["options"] = options
        return
        yield  # pragma: no cover — makes this an async generator

    monkeypatch.setattr(claude_agent_sdk, "query", fake_query)
    _changed(corpus)
    with ChangeDB(corpus.changes_db) as db:
        before, after = db.last_two()
        result = diff.compare(before, after, db=db, blob_dir=corpus.blob_dir)
        out = await session_mod.run_digest(result, db=db, blob_dir=str(corpus.blob_dir))

    options = seen["options"]
    assert options.model == session_mod.MODEL
    assert options.tools == []                      # no built-in tools
    assert options.setting_sources == []            # no inherited local settings
    assert all(name.startswith("mcp__digest__") for name in options.allowed_tools)
    assert "{run}" not in seen["prompt"]            # the template actually formatted
    assert "no longer supported" in seen["prompt"]  # the run is really in there
    assert out.changes == len(result.changes)


async def test_a_budget_cap_returns_a_result_rather_than_raising(corpus, monkeypatch):
    """A cap is how a session is *meant* to end. Findings land as each call is made, so
    raising would discard real work — which is exactly what happened on the first run."""
    import claude_agent_sdk

    from changefeed.digest import session as session_mod

    async def exploding_query(*, prompt, options, **_):
        raise RuntimeError("Reached maximum budget ($5)")
        yield  # pragma: no cover

    monkeypatch.setattr(claude_agent_sdk, "query", exploding_query)
    _changed(corpus)
    with ChangeDB(corpus.changes_db) as db:
        before, after = db.last_two()
        result = diff.compare(before, after, db=db, blob_dir=corpus.blob_dir)
        out = await session_mod.run_digest(result, db=db, blob_dir=str(corpus.blob_dir))

    assert "maximum budget" in out.stopped
    assert out.findings == []


async def test_a_batching_regression_is_visible_in_the_run_output(corpus):
    """Cost lives in turns, so one-finding-per-call is a regression the bill would show
    weeks later. Counting it makes it visible when the run finishes."""
    from changefeed.digest.tools import make_handlers

    _changed(corpus)
    ctx, db = _ctx(corpus)
    try:
        handlers = make_handlers(ctx)
        await handlers["record_findings"]({"findings": [
            {"urls": [record("a").source_url], "impact": "breaking", "summary": "one"},
            {"urls": [record("b").source_url], "impact": "additive", "summary": "two"},
        ]})
    finally:
        db.close()

    assert ctx.calls["batch calls"] == 1
    assert ctx.calls["findings recorded"] == 2
