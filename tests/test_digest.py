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


def test_an_arm_run_is_shelved_and_never_pools_with_current(corpus):
    """Issue 13's choreography fix: `run --no-replace` leaves the current set alone,
    and the arm's rows never join it — pooling arms is what the ledger forbids."""
    from changefeed.digest.findings import Finding, arm_run, for_pair, shelve_new
    from changefeed.digest.findings import record as store

    _changed(corpus)
    _, db = _ctx(corpus)
    try:
        current = Finding(impact="breaking", summary="current story",
                          urls=[record("a").source_url], prompt_version="3")
        store(db, 1, 2, current)
        floor = db.conn.execute("SELECT MAX(id) FROM findings").fetchone()[0]

        arm = Finding(impact="additive", summary="arm story",
                      urls=[record("a").source_url], prompt_version="3+p")
        store(db, 1, 2, arm)
        shelved, _stamp = shelve_new(db, 1, 2, above_id=floor)

        assert shelved == 1
        assert [f.summary for f in for_pair(db, 1, 2)] == ["current story"]
        assert [f.summary for f in arm_run(db, 1, 2, "3+p")] == ["arm story"]
    finally:
        db.close()


def test_promote_points_current_at_a_shelved_arm(corpus):
    from changefeed.digest.findings import Finding, for_pair, promote, shelve_new
    from changefeed.digest.findings import record as store

    _changed(corpus)
    _, db = _ctx(corpus)
    try:
        store(db, 1, 2, Finding(impact="breaking", summary="old current",
                                urls=[record("a").source_url], prompt_version="3"))
        floor = db.conn.execute("SELECT MAX(id) FROM findings").fetchone()[0]
        store(db, 1, 2, Finding(impact="additive", summary="the winning arm",
                                urls=[record("a").source_url], prompt_version="3+p"))
        shelve_new(db, 1, 2, above_id=floor)

        retired, promoted = promote(db, 1, 2, "3+p")

        assert (retired, promoted) == (1, 1)
        assert [f.summary for f in for_pair(db, 1, 2)] == ["the winning arm"]
        # the old current set is retired, not destroyed
        assert "old current" in {f.summary for f in for_pair(db, 1, 2, superseded=True)}
    finally:
        db.close()


def test_promote_of_an_unknown_arm_is_refused(corpus):
    import pytest

    from changefeed.digest.findings import promote

    _changed(corpus)
    _, db = _ctx(corpus)
    try:
        with pytest.raises(ValueError, match="no shelved or superseded run"):
            promote(db, 1, 2, "9+nope")
    finally:
        db.close()


def test_arm_run_reads_the_latest_run_of_a_version(corpus):
    """Two shelved runs of one version: the newer stamp group wins, whole."""
    from changefeed.digest.findings import Finding, arm_run, shelve_new
    from changefeed.digest.findings import record as store

    _changed(corpus)
    _, db = _ctx(corpus)
    try:
        for run_no in (1, 2):
            floor = db.conn.execute(
                "SELECT COALESCE(MAX(id), 0) FROM findings").fetchone()[0]
            store(db, 1, 2, Finding(impact="additive", summary=f"run {run_no}",
                                    urls=[record("a").source_url], prompt_version="3+p"))
            _, stamp = shelve_new(db, 1, 2, above_id=floor)
            # distinct stamps even inside one second
            db.conn.execute("UPDATE findings SET superseded_at = ? "
                            "WHERE superseded_at = ?", (f"{stamp}-{run_no}", stamp))
            db.conn.commit()

        assert [f.summary for f in arm_run(db, 1, 2, "3+p")] == ["run 2"]
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


# --- the audit ------------------------------------------------------------

def _two_sided(corpus, before_md: str, after_md: str):
    corpus.populate([record("a", markdown=before_md)])
    corpus.snap()
    corpus.populate([record("a", markdown=after_md)])
    corpus.snap()
    with ChangeDB(corpus.changes_db) as db:
        b, a = db.last_two()
        result = diff.compare(b, a, db=db, blob_dir=corpus.blob_dir)
    return {c.url: c for c in result.changes}


def test_the_audit_flags_a_new_claim_about_something_already_there(corpus):
    """The failure the #5 -> #6 audit found by hand: Grok 4.6 reported as newly added when
    the models table had simply been rewritten whole and the old entry reappeared on a `+`
    line. A scorer is only tested once it has returned a failure (lessons-learned §19)."""
    from changefeed.digest.audit import audit_finding
    from changefeed.digest.findings import Finding

    by_url = _two_sided(
        corpus,
        "# Models\n\n| model |\n|---|\n| `databricks-grok-4-6` |\n",
        "# Models\n\n| model | notes |\n|---|---|\n| `databricks-grok-4-6` | hosted |\n"
        "| `databricks-gpt-6-astra` | hosted |\n")
    # Prose names, as the real finding wrote them — an id-only first version missed this.
    finding = Finding(impact="additive",
                      summary="Databricks added GPT 6 Astra and Grok 4.6 as hosted models",
                      urls=list(by_url))

    result = audit_finding(finding, by_url, blob_dir=corpus.blob_dir)

    assert "Grok 4.6" in result.already_present
    assert not any("6" in x and "Astra" in x for x in result.already_present)


def test_context_in_the_detail_is_not_mistaken_for_a_newness_claim(corpus):
    """"Previously documented only for us-east-1" names something that existed before, on
    purpose. Checking the detail flagged exactly that, and every such flag was noise."""
    from changefeed.digest.audit import audit_finding
    from changefeed.digest.findings import Finding

    by_url = _two_sided(corpus, "# X\n\nAvailable in us-east-1 on version 2.1.\n",
                        "# X\n\nAvailable in all regions on version 2.1.\n")
    finding = Finding(impact="additive", summary="HIPAA support added",
                      detail="Previously documented only for us-east-1 on version 2.1.",
                      urls=list(by_url))

    assert audit_finding(finding, by_url, blob_dir=corpus.blob_dir).already_present == []


def test_the_audit_does_not_flag_a_deprecation_naming_something_that_existed(corpus):
    """Something deprecated necessarily existed before. Flagging it would train the reader
    to ignore the warning, which is worse than having none."""
    from changefeed.digest.audit import audit_finding
    from changefeed.digest.findings import Finding

    by_url = _two_sided(corpus,
                        "# Tools\n\nUse `legacy-tool-api` for this.\n",
                        "# Tools\n\n`legacy-tool-api` is deprecated and removed on 2026-12-01.\n")
    finding = Finding(impact="breaking",
                      summary="`legacy-tool-api` is deprecated, removal on 2026-12-01",
                      urls=list(by_url))

    assert audit_finding(finding, by_url, blob_dir=corpus.blob_dir).already_present == []


def test_evidence_lines_are_ranked_by_the_claim_not_by_position():
    """Taking lines in order showed blank lines and boilerplate that proved nothing."""
    from changefeed.digest.audit import rank_lines

    lines = [("+", "> **Note:**"), ("+", ""),
             ("+", "Customers who opt out of data retention cannot use Claude Fable 5.")]
    terms = {"opt", "retention", "fable"}

    assert "cannot use Claude Fable 5" in rank_lines(lines, terms)[0][1]
    assert all(text.strip() for _, text in rank_lines(lines, terms))


def test_a_finding_citing_far_more_than_is_shown_says_so(corpus):
    """Judging a 25-page finding from three of its pages as if that were the whole case is
    how the first audit came out too generous."""
    from changefeed.digest.audit import Audit, render
    from changefeed.digest.findings import Finding

    finding = Finding(impact="additive", summary="x",
                      urls=[f"https://x.test/en/p{i}" for i in range(25)])

    text = render(Audit(finding=finding, shown_pages=3), 1)

    assert "only 12% of the evidence is shown" in text


def test_a_replaced_name_is_not_flagged(corpus):
    """"Now pins claude-opus-4-8 instead of claude-opus-4-1" names the old model on purpose;
    it is the one that went away, so it must not be flagged as falsely new."""
    from changefeed.digest.audit import audit_finding
    from changefeed.digest.findings import Finding

    by_url = _two_sided(corpus, "# X\n\nmodel = claude-opus-4-1\n",
                        "# X\n\nmodel = claude-opus-4-8\n")
    finding = Finding(impact="editorial",
                      summary="Examples now pin `claude-opus-4-8` instead of `claude-opus-4-1`",
                      urls=list(by_url))

    assert audit_finding(finding, by_url, blob_dir=corpus.blob_dir).already_present == []


def test_newness_check_reads_the_v2_phrasing():
    """The v2 run wrote "add ... GLM-5.3 and grok-4-6": the bare verb and a hyphen-then-dot
    name both slipped past the check the first time."""
    from changefeed.digest.audit import claims_newness, identifiers
    from changefeed.digest.findings import Finding

    finding = Finding(impact="additive", urls=[],
                      summary="Databricks Foundation Model APIs add Gemini 3.8 Flash, GLM-5.3 "
                              "and grok-4-6, with region and rate-limit entries for each.")

    assert claims_newness(finding)
    assert {"GLM-5.3", "grok-4-6", "Gemini 3.8 Flash"} <= identifiers(finding)


# --- issue/accuracy/02: restriction language and the boosted excerpt ------

# The exact sentence the digest missed under both prompt versions — the standing rule:
# a check's test is built from the real text that motivated it. `cannot` begins at
# character 140 of the real changed line, which is also EXCERPT_LINE: head truncation
# cut the excerpt at the word itself.
_FABLE_LINE = (
    "> For Claude Fable 5, prompts and responses are retained for 30 days for trust "
    "and safety purposes. Customers who opt out of data retention cannot use Claude "
    "Fable 5. This data is processed by automated safety systems and may in certain "
    "instances be reviewed."
)


def test_the_fable_retention_sentence_fires_restriction():
    assert classify.RESTRICTION.search(_FABLE_LINE)
    # And deliberately NOT the ranking lexicon: extending STATUS was measured on both
    # stored runs and rejected (rank 538 -> 499; Admin-API boilerplate into the top-100).
    # If this assertion ever fails, someone widened STATUS without re-measuring.
    assert not classify.STATUS.search(_FABLE_LINE)


def test_admitted_restriction_words_fire_on_their_motivating_lines():
    """One real changed line per admitted word, from the samples read on 2026-09-18."""
    for line in (
        "> This example requires the Databricks AI environment version 5 or above.",
        "Archived rules are rejected with 400. OAuth callers may only manage rules",
        ("(**Behavior change**) Metric views now reject window measures that reference "
         "other window measures."),
        ("- You cannot share a metric view that references tables with row filters or "
         "column masks."),
        ("In organizations that use customer-managed encryption keys, local session "
         "transcripts are unavailable."),
    ):
        assert classify.RESTRICTION.search(line), line


def test_must_at_end_of_clause_is_restriction_but_not_status():
    """The iff from the issue: end-of-clause `must` matches exactly where `must` was
    admitted — RESTRICTION (`must\\b`) — and not in STATUS, whose v1 `must ` (trailing
    space) is frozen by the measured rejection."""
    for line in ("Before November 30, 2026, you must:", "The `upsertkey` columns must:"):
        assert classify.RESTRICTION.search(line), line
        assert not classify.STATUS.search(line), line
    # STATUS v1 behaviour unchanged where it did match:
    assert classify.STATUS.search("you must provide a name for the resource")


def test_boosted_excerpt_windows_the_restriction_clause():
    """Off (the default), the retention line is selected but head truncation hides the
    clause — the measured failure. On, the excerpt windows to the sentence holding the
    match, so 'cannot use Claude Fable 5' is on screen."""
    import tempfile

    from changefeed import blobs

    filler = "Filler table row that is long and unremarkable in every way. " * 3
    before = "# Models\n\n" + filler
    after = "# Models\n\n" + filler + "\n" + _FABLE_LINE

    change = diff.PageChange(
        "https://x.test/en/supported-models", diff.MODIFIED, classify.CONTENT,
        classify.SUBSTANTIVE, {"content_hash": "1" * 64}, {"content_hash": "2" * 64})
    with tempfile.TemporaryDirectory() as d:
        blobs.write("1" * 64, before, d)
        blobs.write("2" * 64, after, d)
        plain = compress(change, blob_dir=d)
        boosted = compress(change, blob_dir=d, boost_restrictions=True)

    assert "For Claude Fable 5" in plain.excerpt        # the line IS selected…
    assert "cannot use Claude Fable 5" not in plain.excerpt   # …but the clause is cut
    assert "cannot use Claude Fable 5" in boosted.excerpt
    assert len(boosted.excerpt) <= 280


def test_the_window_never_rewinds_the_match_off_screen():
    """A sentence boundary can sit far before the match; rewinding there re-hides the
    clause the window exists to show. The window must always contain the match."""
    from changefeed.digest.compress import EXCERPT_LINE, _clip

    line = ("The section opens here. " + "An unremarkable clause drones on and on, "
            "never ending a sentence, going through commas, " * 4
            + "until finally the feature cannot be used with serverless compute.")
    clipped = _clip(line, boost=True)
    assert "cannot" in clipped
    assert len(clipped) <= EXCERPT_LINE + 1  # the ellipsis


# --- issue/accuracy/03: what the newness check may and may not see --------


def test_a_region_in_the_headline_is_not_an_identifier():
    """From real finding 192, the standing false positive: "…rather than us-east-1 only"
    names the region as the old state. A region is where something became available,
    never the thing that became available, so "did it exist before" cannot answer the
    claim. Finding 91 was the same shape a run earlier and went unrecorded."""
    from changefeed.digest.audit import identifiers
    from changefeed.digest.findings import Finding

    finding = Finding(impact="additive", urls=[],
                      summary="Lakebase adds HIPAA support — enablement, audit logging and "
                              "shared-responsibility pages — and PCI-DSS and HITRUST now "
                              "cover all AWS regions where Lakebase is available rather "
                              "than us-east-1 only.")
    assert "us-east-1" not in identifiers(finding)
    # The exclusion is shape-based, not a blocklist of one:
    finding2 = Finding(impact="additive", urls=[],
                       summary="Feature X added in eu-west-1 and us-gov-west-1")
    assert not identifiers(finding2) & {"eu-west-1", "us-gov-west-1"}


def test_a_region_on_both_sides_no_longer_flags(corpus):
    """End to end: the finding-192 shape, with the region present in before and after
    text of the cited page, produces no already_present flag."""
    from changefeed.digest.audit import audit_finding
    from changefeed.digest.findings import Finding

    by_url = _two_sided(
        corpus,
        "# Lakebase\n\nPCI-DSS applies in us-east-1.\n",
        "# Lakebase\n\nPCI-DSS and HITRUST apply in all regions, was us-east-1.\n")
    finding = Finding(impact="additive", urls=list(by_url),
                      summary="Lakebase adds HIPAA; PCI-DSS now covers all AWS regions "
                              "rather than us-east-1 only")
    assert audit_finding(finding, by_url, blob_dir=corpus.blob_dir).already_present == []


def test_an_all_added_finding_says_the_newness_check_could_not_run(corpus):
    """A finding whose cited pages are all new has no before text; the check used to
    skip in silence, and silence reads as a pass. Four stored findings sit in this
    state today. The audit must say the check could not run."""
    from changefeed.digest import audit as A
    from changefeed.digest.findings import Finding

    corpus.populate([record("old")])
    corpus.snap()
    corpus.populate([record("old"), record("brand-new-page",
                                           markdown="# New\n\nA new API, `frobnicate_20261001`.")])
    corpus.snap()
    with ChangeDB(corpus.changes_db) as db:
        b, a = db.last_two()
        result = diff.compare(b, a, db=db, blob_dir=corpus.blob_dir)
    by_url = {c.url: c for c in result.changes}
    added_urls = [u for u, c in by_url.items() if c.kind == "added"]

    finding = Finding(impact="additive", urls=added_urls,
                      summary="A new `frobnicate_20261001` API is added")
    out = A.audit_finding(finding, by_url, blob_dir=corpus.blob_dir)
    assert out.newness_unverifiable
    assert out.already_present == []
    assert "could NOT run" in A.render(out, 1)

    # And a finding with ordinary modified pages does not carry the note.
    by_url2 = _two_sided(corpus, "# P\n\nold text\n", "# P\n\nnew text, adds `thing_v2_0`\n")
    finding2 = Finding(impact="additive", urls=list(by_url2), summary="adds `thing_v2_0`")
    assert not A.audit_finding(finding2, by_url2, blob_dir=corpus.blob_dir).newness_unverifiable


# --- issue/accuracy/04: quoted claims about the past are verified ---------


def test_a_fabricated_quote_of_the_old_text_flags(corpus):
    """Graded finding 237, the motivating case: the detail attributes to the old page a
    sentence — "supports client tools and the advisor tool" — that exists only on the
    NEW page. The flag must say both halves: absent from before, present in after."""
    from changefeed.digest import audit as A
    from changefeed.digest.findings import Finding

    by_url = _two_sided(
        corpus,
        "# Token counting\n\nCount tokens before sending a request.\n",
        "# Token counting\n\n> Token counting supports client tools and the "
        "[advisor tool](https://x.test/advisor), but returns an `invalid_request_error` "
        "for server tools.\n")
    finding = Finding(
        impact="behavioural", urls=list(by_url),
        summary="Token counting now documents that it returns an `invalid_request_error` "
                "for a few inputs the Messages API accepts, including server tools.",
        detail='The page previously framed this as a support note ("supports client '
               'tools and the advisor tool") rather than naming the error.')
    out = A.audit_finding(finding, by_url, blob_dir=corpus.blob_dir)
    assert [(q, other) for q, other in out.misquoted_before] == \
        [("supports client tools and the advisor tool", True)]
    assert "likely quoting the new page as the old" in A.render(out, 1)


def test_a_true_from_to_quote_pair_does_not_flag(corpus):
    """Graded finding 160 quotes both sides of the CMEK change verbatim and truly. The
    from-quote checks against the before text, the to-quote against the after — the
    to-side must never be flagged for being absent from the before text, which is what
    the first measurement pass got wrong on three findings."""
    from changefeed.digest import audit as A
    from changefeed.digest.findings import Finding

    by_url = _two_sided(
        corpus,
        "# CMEK\n\n| feature | note |\n|---|---|\n| structured outputs | not available "
        "for Claude Fable 5 or Claude Mythos models in CMEK organizations |\n",
        "# CMEK\n\n| feature | note |\n|---|---|\n| structured outputs | not available "
        "for Claude Fable or Claude Mythos models in CMEK organizations |\n")
    finding = Finding(
        impact="breaking", urls=list(by_url),
        summary="The CMEK page now says structured outputs are unavailable for Claude "
                "Fable and Claude Mythos models generally, where it previously named "
                "only Claude Fable 5 and Claude Mythos models.",
        detail='The table entry changed from "not available for Claude Fable 5 or '
               'Claude Mythos models in CMEK organizations" to "not available for '
               'Claude Fable or Claude Mythos models in CMEK organizations".')
    out = A.audit_finding(finding, by_url, blob_dir=corpus.blob_dir)
    assert out.misquoted_before == []
    assert out.misquoted_after == []


def test_a_paraphrase_presented_as_a_quote_flags(corpus):
    """Graded finding 202: the old page says "The connector only supports ingestion of
    BASIC reports." — the finding quotes it as "BASIC reports only". Right substance,
    fabricated quotation; the check flags the quotation."""
    from changefeed.digest import audit as A
    from changefeed.digest.findings import Finding

    by_url = _two_sided(
        corpus,
        "# TikTok Ads\n\n- The connector only supports ingestion of BASIC reports.\n",
        "# TikTok Ads\n\n- Report data is only supported for reports with fewer than "
        "20,000 ads.\n")
    finding = Finding(
        impact="behavioural", urls=list(by_url),
        summary='The TikTok Ads connector limit changed from "BASIC reports only" to '
                '"report data is only supported for reports with fewer than 20,000 ads".')
    out = A.audit_finding(finding, by_url, blob_dir=corpus.blob_dir)
    assert [q for q, _ in out.misquoted_before] == ["BASIC reports only"]
    assert out.misquoted_after == []


def test_emphasis_tokens_and_elided_quotes_are_not_claims():
    """From real findings 226 and 179: a single quoted token is emphasis, and an elided
    template ("For how X…") is unverifiable by construction. Neither is checked."""
    from changefeed.digest.audit import quoted_claims
    from changefeed.digest.findings import Finding

    finding = Finding(
        impact="editorial", urls=[],
        summary='The endpoints now document an optional "anthropic-workspace-id" header '
                'that was previously undocumented.',
        detail='A phrasing sweep rewrites cross-reference sentences from "For how X…" '
               'to "To learn how X…".')
    past, present = quoted_claims(finding)
    assert past == []
    assert present == []


def test_quantifier_falsity_is_a_recorded_miss(corpus):
    """Graded finding 158's falsity lives in the word "only" — every named term of its
    past-claim IS in the old text (which also excluded Opus 5 and Sonnet 5). Term
    presence cannot see that, and A-terms measured ~90% false on other grounds, so this
    stays a documented boundary of the deterministic check, not a silent one."""
    from changefeed.digest import audit as A
    from changefeed.digest.findings import Finding

    by_url = _two_sided(
        corpus,
        "# Service tiers\n\nPriority Tier is supported on all available Claude models "
        "except Claude Mythos 5, Claude Mythos Preview, Claude Opus 5, and Claude "
        "Sonnet 5.\n",
        "# Service tiers\n\nPriority Tier is supported on all available Claude models "
        "except Claude Fable 5.1, Claude Mythos 5.1, Claude Mythos 5, Claude Mythos "
        "Preview, Claude Opus 5, and Claude Sonnet 5.\n")
    finding = Finding(
        impact="additive", urls=list(by_url),
        summary="Priority Tier now lists Claude Fable 5.1 and Claude Mythos 5.1 among "
                "the models it does not support, alongside Claude Mythos 5 and Claude "
                "Mythos Preview.",
        detail="The page previously excluded only Claude Mythos 5 and Claude Mythos "
               "Preview from Priority Tier; the new sentence adds the two 5.1 models.")
    out = A.audit_finding(finding, by_url, blob_dir=corpus.blob_dir)
    assert out.misquoted_before == []   # no quote to check — the boundary, on purpose


def test_a_preposition_to_is_not_a_rename_to(corpus):
    """Real finding 199, a true finding: `pages that linked to "Enrich data using AI
    Functions" now use the new title`. "linked to" is a preposition — the quote names
    the OLD title correctly and must not be checked as the new text. Caught by reading
    the real audit output, not by a test."""
    from changefeed.digest import audit as A
    from changefeed.digest.findings import Finding

    by_url = _two_sided(
        corpus,
        "# AI Functions\n\nSee [Enrich data using AI Functions](https://x.test/ai).\n",
        "# AI Functions\n\nSee [Transform unstructured data using AI Functions]"
        "(https://x.test/ai).\n")
    finding = Finding(
        impact="additive", urls=list(by_url),
        summary='A new `ai_enrich` SQL function (Beta) generates new columns for each '
                'row, and the AI Functions guide is retitled "Transform unstructured '
                'data using AI Functions".',
        detail='The many pages that linked to "Enrich data using AI Functions" now use '
               'the new title.')
    out = A.audit_finding(finding, by_url, blob_dir=corpus.blob_dir)
    assert out.misquoted_after == []
    assert out.misquoted_before == []


# --- issue/accuracy/05: the absence detector --------------------------------


def _diff_result(corpus, before_md: str, after_md: str, extra=None):
    """Like _two_sided, but returns the DiffResult the absence scan consumes."""
    corpus.populate([record("a", markdown=before_md)] + (extra or []))
    corpus.snap()
    corpus.populate([record("a", markdown=after_md)] + (extra or []))
    corpus.snap()
    with ChangeDB(corpus.changes_db) as db:
        b, a = db.last_two()
        return diff.compare(b, a, db=db, blob_dir=corpus.blob_dir)


def test_the_fable_sentence_is_a_candidate(corpus):
    """The gate for the whole issue: the real missed sentence, on a page whose before
    text already names Claude Fable 5, must surface — this is the only check in the
    project that can see a finding that was never written."""
    from changefeed.digest import absence

    result = _diff_result(
        corpus,
        "# Supported models\n\n| model |\n|---|\n| Claude Fable 5 (`claude-fable-5`) |\n",
        "# Supported models\n\n| model |\n|---|\n| Claude Fable 5 (`claude-fable-5`) |\n\n"
        "> For Claude Fable 5, prompts and responses are retained for 30 days for trust "
        "and safety purposes. Customers who opt out of data retention cannot use Claude "
        "Fable 5. This data is processed by automated safety systems.\n")
    candidates = absence.scan(result, blob_dir=corpus.blob_dir)
    hits = [c for c in candidates if "cannot use Claude Fable 5" in c.line]
    assert hits
    assert any("Claude Fable 5" in s for s in hits[0].subjects)


def test_a_ga_announcement_is_not_a_candidate(corpus):
    """GA is never a restriction — the lexicon draws the breaking-vs-GA line the prompt
    rules already draw, so "generally available" must not surface here."""
    from changefeed.digest import absence

    result = _diff_result(
        corpus,
        "# ABAC\n\nABAC GRANT policies are in Beta for Unity Catalog.\n",
        "# ABAC\n\nABAC GRANT policies are generally available for Unity Catalog.\n")
    assert absence.scan(result, blob_dir=corpus.blob_dir) == []


def test_a_restriction_on_a_genuinely_new_thing_is_not_a_candidate(corpus):
    """A restriction shipping with a brand-new thing is part of the launch, not news
    about something people relied on. Subject absent from the before text -> filtered.
    (The subject test is a heuristic: a new version whose FAMILY name existed before —
    the Fable 5.1 twin — does pass, an accepted cost recorded in the module docstring.)"""
    from changefeed.digest import absence

    result = _diff_result(
        corpus,
        "# Tools\n\nExisting content about other tools.\n",
        "# Tools\n\nExisting content about other tools.\n\n"
        "`frobnicate_20261001` is not available on Bedrock.\n")
    assert absence.scan(result, blob_dir=corpus.blob_dir) == []


def test_duplicate_restriction_lines_appear_once(corpus):
    """One vendor sentence stamped across hundreds of mirror pages is one candidate —
    the #6 -> #7 pair carries a tool-safety sentence on ~290 API-reference mirrors."""
    from changefeed.digest import absence

    sentence = ("The Unity Catalog API cannot modify groups provisioned by an identity "
                "provider.")
    corpus.populate([record("a", markdown="# A\n\nUnity Catalog API docs.\n"),
                     record("b", markdown="# B\n\nUnity Catalog API docs.\n")])
    corpus.snap()
    corpus.populate([record("a", markdown=f"# A\n\nUnity Catalog API docs.\n\n{sentence}\n"),
                     record("b", markdown=f"# B\n\nUnity Catalog API docs.\n\n{sentence}\n")])
    corpus.snap()
    with ChangeDB(corpus.changes_db) as db:
        b, a = db.last_two()
        result = diff.compare(b, a, db=db, blob_dir=corpus.blob_dir)
    candidates = absence.scan(result, blob_dir=corpus.blob_dir)
    assert len([c for c in candidates if sentence in c.line]) == 1


def test_cited_means_a_finding_looked_not_that_it_reported(corpus):
    """Page-level marking, stated honestly: the Fable page WAS cited — by the finding
    that inverted its retention rule — so 'cited' can never be read as 'covered'."""
    from changefeed.digest import absence
    from changefeed.digest.findings import Finding

    result = _diff_result(
        corpus,
        "# M\n\nClaude Fable 5 is hosted.\n",
        "# M\n\nClaude Fable 5 is hosted.\n\nClaude Fable 5 is not available for "
        "opted-out customers.\n")
    candidates = absence.scan(result, blob_dir=corpus.blob_dir)
    assert candidates
    url = candidates[0].url
    absence.mark_cited(candidates, [Finding(impact="additive", urls=[url],
                                            summary="something about this page")])
    assert candidates[0].cited is True
    absence.mark_cited(candidates, [Finding(impact="additive", urls=["https://x.test/en/z"],
                                            summary="elsewhere")])
    assert candidates[0].cited is False
    assert "UNCITED" in absence.render(candidates, before="#1", after="#2")


@pytest.mark.asyncio
async def test_the_experiment_arms_change_the_prompt_and_the_version(corpus, monkeypatch):
    """Each A/B flag must actually reach the prompt AND stamp the arm into
    prompt_version — an arm that ran without its marker would poison the ledger."""
    import claude_agent_sdk

    from changefeed.digest import session as session_mod

    seen = {}

    async def fake_query(*, prompt, options, **_):
        seen["prompt"] = prompt
        return
        yield  # pragma: no cover

    monkeypatch.setattr(claude_agent_sdk, "query", fake_query)
    _changed(corpus)
    with ChangeDB(corpus.changes_db) as db:
        before, after = db.last_two()
        result = diff.compare(before, after, db=db, blob_dir=corpus.blob_dir)

        await session_mod.run_digest(result, db=db, blob_dir=str(corpus.blob_dir))
        base = seen["prompt"]
        assert "10. **When you assert" not in base
        assert "{extra_rules}" not in base          # the placeholder formatted away

        await session_mod.run_digest(result, db=db, blob_dir=str(corpus.blob_dir),
                                     quote_evidence=True)
        assert "10. **When you assert" in seen["prompt"]

        await session_mod.run_digest(result, db=db, blob_dir=str(corpus.blob_dir),
                                     inject_restrictions=True)
        # This tiny corpus has no restriction candidates, so the appendix is empty —
        # the flag must not break the prompt; the version marker still applies.
        assert seen["prompt"].startswith(base[:200])


# --- issue/accuracy/06: collapse, merge, and the amended promise ----------


def _many_moved(corpus, n=12):
    """A corpus where n pages move category (site re-date shape) and one page edits."""
    corpus.populate([record(f"p{i}", category="delta") for i in range(n)]
                    + [record("edited", markdown="# E\n\nOld text about the feature.\n")])
    corpus.snap()
    corpus.populate([record(f"p{i}", category="delta", updated_date="2026-09-11")
                     for i in range(n)]
                    + [record("edited", markdown="# E\n\nNew text: the feature is no "
                                                 "longer supported.\n")])
    corpus.snap()
    with ChangeDB(corpus.changes_db) as db:
        b, a = db.last_two()
        return diff.compare(b, a, db=db, blob_dir=corpus.blob_dir)


def test_collapsed_terse_groups_sum_and_stay_enumerable(corpus):
    """The amended promise: every change is a line or enumerable through a tool. The
    header's change count must still equal the real total, and the grouped pages must
    all be present in the group lines' population."""
    from changefeed.digest.compress import TERSE_KINDS

    result = _many_moved(corpus)
    plain = compress_run(result, blob_dir=corpus.blob_dir)
    collapsed = compress_run(result, blob_dir=corpus.blob_dir, collapse_terse=True)

    n_terse = sum(1 for r in plain.records if r.kind in TERSE_KINDS)
    assert n_terse >= 12
    assert sum(len(g.slugs) for g in collapsed.terse_groups) == n_terse
    assert not any(r.kind in TERSE_KINDS for r in collapsed.records)
    # The header states the true total, and the rendering says how to enumerate.
    assert f"# {len(plain.records)} changes:" in collapsed.header()
    assert "list_changes" in collapsed.render()


@pytest.mark.asyncio
async def test_list_changes_enumerates_exactly_the_collapsed_set(corpus):
    """The tool half of the promise: what the grouped lines hide, the tool returns —
    all of it, and nothing else."""
    from changefeed.digest.tools import DigestContext, make_handlers

    result = _many_moved(corpus)
    with ChangeDB(corpus.changes_db) as db:
        ctx = DigestContext(result=result, db=db, blob_dir=str(corpus.blob_dir))
        handlers = make_handlers(ctx)
        out = await handlers["list_changes"]({"kind": "metadata"})
        text = out["content"][0]["text"]
        expected = {c.url.split("/en/")[-1] for c in result.changes if c.kind == "metadata"}
        listed = set(text.splitlines()[1:])
        assert listed == expected

        missing = await handlers["list_changes"]({"kind": "removed"})
        assert missing.get("is_error")


def test_identical_changed_lines_merge_to_one_record_and_stay_citable(corpus):
    """The #5 -> #6 run carries one beta-header edit stamped across 115 API-reference
    mirrors. One story, one record — and every mirror path still resolves, because
    `find()` works on the diff, not the rendering."""
    from changefeed.digest.tools import DigestContext

    shared_before = "# API\n\nHeader list: `beta-a` or `beta-b` or 38 more.\n"
    shared_after = "# API\n\nHeader list: `beta-a` or `beta-b`.\n"
    corpus.populate([record("mirror-one", markdown=shared_before),
                     record("mirror-two", markdown=shared_before),
                     record("unrelated", markdown="# U\n\nSomething else entirely.\n")])
    corpus.snap()
    corpus.populate([record("mirror-one", markdown=shared_after),
                     record("mirror-two", markdown=shared_after),
                     record("unrelated", markdown="# U\n\nSomething else changed here.\n")])
    corpus.snap()
    with ChangeDB(corpus.changes_db) as db:
        b, a = db.last_two()
        result = diff.compare(b, a, db=db, blob_dir=corpus.blob_dir)

        merged = compress_run(result, blob_dir=corpus.blob_dir, merge_duplicates=True)
        mirror_records = [r for r in merged.records if "mirror" in r.slug]
        assert len(mirror_records) == 1
        assert len(mirror_records[0].mirrors) == 1
        assert "identical change" in mirror_records[0].render()
        # the unrelated page is untouched by the merge
        assert any("unrelated" in r.slug for r in merged.records)

        ctx = DigestContext(result=result, db=db)
        for slug in ("mirror-one", "mirror-two"):
            hits = [u for u in ctx._by_slug if slug in u]
            assert hits and ctx.find(hits[0]) is not None


def test_quiet_runs_render_identically_with_flags_off(corpus):
    """Both features are A/B arms: with the flags off the rendering must stay
    byte-identical to what every graded run read."""
    result = _many_moved(corpus)
    a = compress_run(result, blob_dir=corpus.blob_dir).render()
    b = compress_run(result, blob_dir=corpus.blob_dir,
                     collapse_terse=False, merge_duplicates=False).render()
    assert a == b


def test_audit_evidence_counts_a_mirror_pair_once(corpus):
    """A finding citing two pages with byte-identical changed lines gets ONE evidence
    block and a note for the mirror — one story must not arrive as two confirmations."""
    from changefeed.digest import audit as A
    from changefeed.digest.findings import Finding

    shared_before = "# API\n\nThe endpoint accepts `beta-a` or `beta-b` or 38 more.\n"
    shared_after = "# API\n\nThe endpoint accepts `beta-a` or `beta-b`.\n"
    corpus.populate([record("twin-a", markdown=shared_before),
                     record("twin-b", markdown=shared_before)])
    corpus.snap()
    corpus.populate([record("twin-a", markdown=shared_after),
                     record("twin-b", markdown=shared_after)])
    corpus.snap()
    with ChangeDB(corpus.changes_db) as db:
        b, a = db.last_two()
        result = diff.compare(b, a, db=db, blob_dir=corpus.blob_dir)
    by_url = {c.url: c for c in result.changes}
    finding = Finding(impact="editorial", urls=sorted(by_url),
                      summary="The beta header enumeration was shortened on two pages")
    out = A.audit_finding(finding, by_url, blob_dir=corpus.blob_dir)
    with_lines = [e for e in out.evidence if e.lines]
    noted = [e for e in out.evidence if "identical change to" in e.note]
    assert len(with_lines) == 1
    assert len(noted) == 1


# --- issue/accuracy/07: revision marking and adaptive slots ---------------

# The real lines from the #5 -> #6 supported-models diff — the type specimen. The old
# retention note, the new one with the opt-out clause INSERTED (a revision, 0.88
# Jaccard), the genuinely new 5.1 twin (which pairs with its template sibling — the
# measured over-pairing boundary), and the genuinely new GLM prose (no pair).
_FABLE5_OLD = ("> For Claude Fable 5, prompts and responses are retained for 30 days for "
               "trust and safety purposes. This data is processed by automated safety "
               "systems and may in certain instances be flagged for human review. The "
               "data is deleted automatically after 30 days, except in the event of a "
               "safety investigation, or legal requirements to retain the data beyond 30 "
               "days. Anthropic is a limited subprocessor for this safety retention "
               "purpose.")
_FABLE5_NEW = _FABLE5_OLD.replace(
    "purposes. This data",
    "purposes. Customers who opt out of data retention cannot use Claude Fable 5. "
    "This data")
_FABLE51_NEW = _FABLE5_NEW.replace("Claude Fable 5,", "Claude Fable 5.1,").replace(
    "cannot use Claude Fable 5.", "cannot use Claude Fable 5.1.")
_GLM_NEW_PROSE = ("GLM-5.3 is a text-only mixture of experts (MoE) language model "
                  "developed by Zhipu AI for coding and agentic tool use. It supports "
                  "function calling, parallel tool calls, structured output, and long "
                  "context.")
# Same shape as the real 11k-char region rows (verified against the blobs at 0.93 in
# the issue's measurement; a row that long cannot live in a test file): a model list
# where one entry swaps.
_ROW_OLD = ("| `ap-northeast-1` | The following models are supported:   "
            "- [`databricks-grok-4-6`](https://docs.databricks.com/aws/en/machine-"
            "learning/foundation-model-apis/supported-models#grok) "
            "- [`databricks-gpt-5-5-pro`](https://docs.databricks.com/aws/en/machine-"
            "learning/foundation-model-apis/supported-models#gpt) |")
_ROW_NEW = _ROW_OLD.replace("databricks-gpt-5-5-pro", "databricks-gpt-6-astra")


def test_revised_lines_pair_and_new_prose_does_not():
    """The founding incident's two shapes, from the real texts: a rewritten row (Grok
    reappearing on `+`) and the type specimen's inserted clause both pair; the
    genuinely new GLM description does not."""
    from changefeed.classify import is_revision, token_set

    old_side = [token_set(_ROW_OLD), token_set(_FABLE5_OLD)]
    assert is_revision(_ROW_NEW, old_side)
    assert is_revision(_FABLE5_NEW, old_side)
    assert not is_revision(_GLM_NEW_PROSE, old_side)


def test_template_sibling_overpairing_is_the_documented_boundary():
    """The Fable 5.1 twin is genuinely NEW but pairs with its template sibling —
    measured at 0.84+, not fixable by threshold. The tag's wording therefore claims
    only 'a close variant existed', never 'not new'."""
    from changefeed.classify import is_revision, token_set

    assert is_revision(_FABLE51_NEW, [token_set(_FABLE5_OLD)])


def test_marked_excerpt_tags_revisions_and_flags_off_stay_identical(corpus):
    """`~` on the shown revised lines; with the flag off the excerpt is byte-identical
    to what every graded run read, and the ranking path never sees the flag."""
    before = f"# Models\n\n{_FABLE5_OLD}\n\nOther prose.\n"
    after = f"# Models\n\n{_FABLE5_NEW}\n\n{_GLM_NEW_PROSE}\n\nOther prose.\n"
    change = next(iter(_two_sided(corpus, before, after).values()))

    plain = compress(change, blob_dir=corpus.blob_dir)
    marked = compress(change, blob_dir=corpus.blob_dir, mark_revisions=True)
    assert "~" in marked.excerpt
    assert "~" not in plain.excerpt
    # The tag spends budget characters, so the marked excerpt truncates slightly
    # earlier; content-wise it is the same excerpt.
    stripped = marked.excerpt.replace("~", "")
    assert stripped == plain.excerpt[:len(stripped)]
    assert marked.severity == plain.severity and marked.signals == plain.signals


def test_adaptive_slots_show_the_third_restriction_line(corpus):
    """The type specimen was the page's third restriction line on a two-slot excerpt.
    With 3+ restriction lines the excerpt grows (to at most four slots); pages under
    the threshold and runs without the flag are unchanged."""
    restr = [
        "Feature Alpha is not supported on serverless compute in any region at all.",
        "Feature Beta cannot be used together with customer-managed keys on AWS today.",
        "Feature Gamma is unavailable for workspaces with the compliance profile on.",
    ]
    before = "# Limits\n\nIntro prose.\n"
    after = "# Limits\n\nIntro prose.\n\n" + "\n\n".join(restr) + "\n"
    change = next(iter(_two_sided(corpus, before, after).values()))

    plain = compress(change, blob_dir=corpus.blob_dir)
    wide = compress(change, blob_dir=corpus.blob_dir, adaptive_slots=True)
    assert plain.excerpt.count(" | ") == 1          # two slots
    assert wide.excerpt.count(" | ") == 2           # three slots for three restrictions
    assert "Gamma" in wide.excerpt or "Alpha" in wide.excerpt

    # A page with fewer restriction lines is untouched by the flag.
    calm = next(iter(_two_sided(
        corpus, "# P\n\nOld words here.\n", "# P\n\nNew words here, quite different.\n").values()))
    assert compress(calm, blob_dir=corpus.blob_dir, adaptive_slots=True).excerpt == \
        compress(calm, blob_dir=corpus.blob_dir).excerpt


def test_unaligned_diff_marks_revisions_only_under_the_flag(corpus):
    """get_diff's unaligned fallback is the other place pairing information dies; the
    tag appears there under the arm's flag and nowhere without it."""
    from changefeed.diff import render_diff

    filler = ("A very long filler paragraph that repeats to push the page over the "
              "alignment limit. " * 6000)
    before = f"# Big\n\n{filler}\n{_FABLE5_OLD}\n"
    after = f"# Big\n\n{filler}\n{_FABLE5_NEW}\n{_GLM_NEW_PROSE}\n"
    change = next(iter(_two_sided(corpus, before, after).values()))

    plain = render_diff(change, blob_dir=corpus.blob_dir)
    marked = render_diff(change, blob_dir=corpus.blob_dir, mark_revisions=True)
    assert "too large to align" in plain and "~" not in plain
    assert "~+" in marked and f"+{_GLM_NEW_PROSE[:30]}" in marked


def test_a_moved_line_stays_invisible_to_changed_sides():
    """Regression guard on the multiset behaviour marking depends on: a line identical
    on both sides is not a change and must never surface for pairing at all."""
    from changefeed.classify import changed_sides

    before = "# T\n\nA stable line.\nAn old line.\n"
    after = "An old line.\n# T\n\nA stable line.\n"
    removed, added = changed_sides(before, after)
    assert removed == [] and added == []


@pytest.mark.asyncio
async def test_the_issue_07_arms_wire_their_legend_and_versions(corpus, monkeypatch):
    """The marking arm must carry its `~` legend into the prompt and both arms must
    stamp their prompt_version suffix — an unmarked arm would poison the ledger."""
    import claude_agent_sdk

    from changefeed.digest import session as session_mod

    seen = {}

    async def fake_query(*, prompt, options, **_):
        seen["prompt"] = prompt
        return
        yield  # pragma: no cover

    monkeypatch.setattr(claude_agent_sdk, "query", fake_query)
    _changed(corpus)
    with ChangeDB(corpus.changes_db) as db:
        before, after = db.last_two()
        result = diff.compare(before, after, db=db, blob_dir=corpus.blob_dir)

        out = await session_mod.run_digest(result, db=db, blob_dir=str(corpus.blob_dir),
                                           boost_restrictions=True, mark_revisions=True)
        assert "**A `~` sign marks a revised line.**" in seen["prompt"]
        assert out.findings == []  # stub session records nothing

        await session_mod.run_digest(result, db=db, blob_dir=str(corpus.blob_dir),
                                     boost_restrictions=True, adaptive_slots=True)
        assert "`~` sign" not in seen["prompt"]


@pytest.mark.asyncio
async def test_v4_collapses_terse_kinds_by_default(corpus, monkeypatch):
    """The prompt-v4 adoption (issue/accuracy/06): a default session reads grouped
    terse lines, and opting out is the marked deviation — an unmarked deviation
    would poison the ledger."""
    import claude_agent_sdk

    from changefeed.digest import session as session_mod

    seen = {}

    async def fake_query(*, prompt, options, **_):
        seen["prompt"] = prompt
        return
        yield  # pragma: no cover

    monkeypatch.setattr(claude_agent_sdk, "query", fake_query)
    result = _many_moved(corpus)
    with ChangeDB(corpus.changes_db) as db:
        await session_mod.run_digest(result, db=db, blob_dir=str(corpus.blob_dir))
        assert "METADATA x12" in seen["prompt"]          # the TerseGroup header line

        await session_mod.run_digest(result, db=db, blob_dir=str(corpus.blob_dir),
                                     collapse_terse=False)
        assert "METADATA x12" not in seen["prompt"]

    assert session_mod.PROMPT_VERSION == "4"
