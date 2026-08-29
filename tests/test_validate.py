"""Tests for the validators. See docs/validation-plan.md §6.

A validator nobody has audited is worse than no validator: it converts "we did not look"
into "it passed". So each check is tested twice — once against a corpus carrying the real
historical defect, and once against the real page that earlier versions of that rule
wrongly rejected (docs/lessons-learned.md §3, §10).
"""

from __future__ import annotations

import pytest

from scraper.config import AppConfig, DumpSeed, SourceConfig
from scraper.records import Extracted
from scraper.store import writer
from scraper.validate import coverage, invariants
from scraper.validate.fidelity import (
    align,
    align_pair,
    compare_notebook,
    drop_added_title,
    fenced_text,
    served_body,
)
from scraper.validate.report import FAILED, PASSED, WARNED, Report, failed, passed

BODY = "Real documentation body. " * 20


def page(**kw) -> Extracted:
    base = {
        "title": "Delta Lake", "markdown": f"# Delta Lake\n\n{BODY}",
        "canonical_url": "https://docs.databricks.com/aws/en/delta/x",
        "source_url": "https://docs.databricks.com/aws/en/delta/x",
        "company": "databricks", "source_id": "databricks-docs", "category": "delta",
        "description": "d", "extractor": "docusaurus", "extractor_version": "7",
        "breadcrumbs": ["Tables"],
    }
    from datetime import date
    base["updated_date"] = date(2026, 7, 10)
    return Extracted(**{**base, **kw})


@pytest.fixture
def corpus(tmp_path):
    """A small, clean corpus plus a factory for adding pages to it."""
    data = tmp_path / "data"

    def add(**kw):
        writer.write(page(**kw), data)
        return data

    add()
    return data, add


@pytest.fixture
def cfg(tmp_path):
    (tmp_path / "dump.txt").write_text("")
    return AppConfig(sources={"databricks-docs": SourceConfig(
        company="databricks", seeds=[DumpSeed(type="dump", path=tmp_path / "dump.txt")],
        include_paths=["/aws/en/"], extractor="docusaurus")})


def status_of(checks, name):
    return next(c.status for c in checks if c.name == name)


# --- the report ------------------------------------------------------------

def test_report_fails_when_any_check_fails():
    report = Report()
    report.add("s", passed("a", "fine"), failed("b", "broken"))
    assert report.ok is False
    assert [c.name for c in report.failures] == ["b"]


def test_report_round_trips_to_json(tmp_path):
    import json

    report = Report()
    report.add("s", passed("a", "fine"))
    path = report.write(tmp_path)
    assert json.loads(path.read_text())["sections"]["s"][0]["name"] == "a"


# --- invariants catch the real defects -------------------------------------

def test_welded_markup_is_caught(corpus):
    data, add = corpus
    add(markdown=f"# T\n\n<div class=\"x\">leaked</div>\n\n{BODY}",
        source_url="https://docs.databricks.com/aws/en/delta/leak",
        canonical_url="https://docs.databricks.com/aws/en/delta/leak")
    assert status_of(invariants.run(data), "html_markup") == FAILED


def test_base64_images_are_caught(corpus):
    data, add = corpus
    add(markdown=f"# T\n\n![i](data:image/png;base64,AAAA)\n\n{BODY}",
        source_url="https://docs.databricks.com/aws/en/delta/img",
        canonical_url="https://docs.databricks.com/aws/en/delta/img")
    assert status_of(invariants.run(data), "data_uri_images") == FAILED


def test_rooted_links_are_caught(corpus, cfg):
    data, add = corpus
    add(markdown=f"# T\n\nSee [acid](/aws/en/lakehouse/acid).\n\n{BODY}",
        source_url="https://docs.databricks.com/aws/en/delta/rel",
        canonical_url="https://docs.databricks.com/aws/en/delta/rel")
    assert status_of(invariants.run(data, cfg), "rooted_links") == FAILED


def test_unconverted_mdx_is_caught(corpus):
    """REGRESSION: `<Card href=…>` hides links from every Markdown parser."""
    data, add = corpus
    add(markdown=('# T\n\n<CardGroup>\n  <Card title="X" href="https://x/y">b</Card>\n'
                  "</CardGroup>\n\n" + BODY),
        source_url="https://docs.databricks.com/aws/en/delta/mdx",
        canonical_url="https://docs.databricks.com/aws/en/delta/mdx")
    assert status_of(invariants.run(data), "mdx_converted") == FAILED


def test_a_component_shown_inside_code_is_not_flagged(corpus):
    """A page documenting MDX legitimately contains `<Card>` in an example."""
    data, add = corpus
    add(markdown=("# T\n\nExample:\n\n```mdx\n<Card title=\"X\">b</Card>\n```\n\n" + BODY),
        source_url="https://docs.databricks.com/aws/en/delta/mdxdoc",
        canonical_url="https://docs.databricks.com/aws/en/delta/mdxdoc")
    assert status_of(invariants.run(data), "mdx_converted") == PASSED


def test_untitled_page_is_caught(corpus):
    data, add = corpus
    add(markdown=BODY, source_url="https://docs.databricks.com/aws/en/delta/untitled",
        canonical_url="https://docs.databricks.com/aws/en/delta/untitled")
    assert status_of(invariants.run(data), "opens_with_its_title") == FAILED


def test_unclosed_fence_is_caught(corpus):
    data, add = corpus
    add(markdown=f"# T\n\n```py\nx = 1\n\n{BODY}",
        source_url="https://docs.databricks.com/aws/en/delta/fence",
        canonical_url="https://docs.databricks.com/aws/en/delta/fence")
    assert status_of(invariants.run(data), "code_fences_closed") == FAILED


def test_private_use_glyphs_are_caught(corpus):
    data, add = corpus
    add(markdown=f"# T\n\n icon leaked\n\n{BODY}",
        source_url="https://docs.databricks.com/aws/en/delta/glyph",
        canonical_url="https://docs.databricks.com/aws/en/delta/glyph")
    assert status_of(invariants.run(data), "private_use_glyphs") == FAILED


def test_a_clean_corpus_passes(corpus, cfg):
    data, _ = corpus
    checks = invariants.run(data, cfg)
    assert [c.name for c in checks if c.status == FAILED] == []


# --- and must NOT fire on the pages that are actually correct ---------------

def test_html_inside_code_is_not_a_leak(corpus, cfg):
    """REGRESSION: `/sql/user-alerts-create` lists allowed tags as `<div>` in inline code,
    and `/internal/directives` documents a `:::div` directive. Both are real pages."""
    data, add = corpus
    add(markdown=("# T\n\nAllowed tags: `<div>`, `<span>`.\n\n"
                  "```html\n<div class=\"x\">example</div>\n```\n\n" + BODY),
        source_url="https://docs.databricks.com/aws/en/sql/alerts",
        canonical_url="https://docs.databricks.com/aws/en/sql/alerts")
    checks = invariants.run(data, cfg)
    assert status_of(checks, "html_markup") == PASSED
    assert status_of(checks, "html_attributes") == PASSED


def test_example_paths_are_not_rooted_links(corpus, cfg):
    """REGRESSION: `](/Workspace/absolute/path/to/image.png)` is prose about a file path,
    not a site link — flagging it teaches everyone to ignore the check."""
    data, add = corpus
    add(markdown=f"# T\n\nUse [the image](/Workspace/absolute/path/to/image.png).\n\n{BODY}",
        source_url="https://docs.databricks.com/aws/en/notebooks/media",
        canonical_url="https://docs.databricks.com/aws/en/notebooks/media")
    assert status_of(invariants.run(data, cfg), "rooted_links") == PASSED


def test_a_page_documenting_an_error_is_not_a_failure(corpus, cfg):
    data, add = corpus
    add(title="404 Not Found error condition",
        markdown=f"# 404 Not Found error condition\n\nThe server returned 404. {BODY}",
        source_url="https://docs.databricks.com/aws/en/error-messages/http-404",
        canonical_url="https://docs.databricks.com/aws/en/error-messages/http-404")
    assert [c.name for c in invariants.run(data, cfg) if c.status == FAILED] == []


def test_reference_stub_passes_the_length_floor(corpus):
    data, add = corpus
    add(markdown="# clearTags\n\n" + "x" * 120,
        source_url="https://docs.databricks.com/aws/en/pyspark/clearTags",
        canonical_url="https://docs.databricks.com/aws/en/pyspark/clearTags")
    assert status_of(invariants.run(data), "body_length") == PASSED


# --- signals that are warnings, not failures -------------------------------

def test_identical_bodies_are_reported_without_failing(corpus):
    data, add = corpus
    add(source_url="https://docs.databricks.com/aws/en/delta/x-alias",
        canonical_url="https://docs.databricks.com/aws/en/delta/x-alias")
    assert status_of(invariants.run(data), "duplicate_bodies") == WARNED


def test_singleton_categories_are_flagged(tmp_path):
    """A flat URL space would give every page its own category — the cookbook's shape."""
    data = tmp_path / "flat"
    for i in range(6):
        writer.write(page(category=f"only-{i}",
                          source_url=f"https://docs.databricks.com/aws/en/x{i}",
                          canonical_url=f"https://docs.databricks.com/aws/en/x{i}"), data)
    assert status_of(invariants.run(data), "category_distribution") == WARNED


# --- coverage --------------------------------------------------------------

def test_link_closure_finds_pages_we_link_to_but_lack(corpus, cfg, tmp_path, monkeypatch):
    data, add = corpus
    add(markdown=("# T\n\nSee [next](https://docs.databricks.com/aws/en/delta/missing).\n\n"
                  + BODY),
        source_url="https://docs.databricks.com/aws/en/delta/y",
        canonical_url="https://docs.databricks.com/aws/en/delta/y")
    monkeypatch.setattr(coverage, "archived_urls", lambda *a, **kw: set())

    check, candidates = coverage.check_link_closure(cfg, data_dir=data, fetch_db_path="unused")
    assert check.status == WARNED
    assert "https://docs.databricks.com/aws/en/delta/missing" in [u for _, u in candidates]


def test_link_closure_ignores_assets_and_other_hosts(corpus, cfg, monkeypatch):
    """REGRESSION: `in_scope` matches on path alone, so `code.claude.com/docs/en/x` and
    downloadable `.py`/`.sql` samples counted as missing documentation pages. They are a
    different site and a set of files respectively — together they inflated the reported
    gap from 108 to 398."""
    data, add = corpus
    add(markdown=("# T\n\n[pdf](https://docs.databricks.com/aws/en/assets/x.pdf), "
                  "[script](https://docs.databricks.com/aws/en/assets/files/deploy.sh), "
                  "[export](https://docs.databricks.com/aws/en/notebooks/source/demo.html), "
                  "[elsewhere](https://code.databricks.com/aws/en/other) and "
                  "[away](https://example.com/page).\n\n" + BODY),
        source_url="https://docs.databricks.com/aws/en/delta/z",
        canonical_url="https://docs.databricks.com/aws/en/delta/z")
    monkeypatch.setattr(coverage, "archived_urls",
                        lambda *a, **kw: {"https://docs.databricks.com/aws/en/delta/x"})

    _, candidates = coverage.check_link_closure(cfg, data_dir=data, fetch_db_path="unused")
    urls = [u for _, u in candidates]
    assert not any(u.endswith((".pdf", ".sh", ".html")) for u in urls), urls
    assert not any("code.databricks.com" in u or "example.com" in u for u in urls), urls


def test_link_closure_still_reports_a_real_missing_page(corpus, cfg, monkeypatch):
    data, add = corpus
    add(markdown=("# T\n\n[real](https://docs.databricks.com/aws/en/agents/agent-evaluation)."
                  "\n\n" + BODY),
        source_url="https://docs.databricks.com/aws/en/delta/w",
        canonical_url="https://docs.databricks.com/aws/en/delta/w")
    monkeypatch.setattr(coverage, "archived_urls",
                        lambda *a, **kw: {"https://docs.databricks.com/aws/en/delta/x"})

    _, candidates = coverage.check_link_closure(cfg, data_dir=data, fetch_db_path="unused")
    assert "https://docs.databricks.com/aws/en/agents/agent-evaluation" in [u for _, u in candidates]


def test_normalise_url_collapses_fragment_query_and_slash():
    assert coverage.normalise("https://x.com/a/b/?q=1#frag") == "https://x.com/a/b"


# --- fidelity inverse transforms -------------------------------------------

def test_served_body_drops_the_sites_own_frontmatter():
    raw = b"---\ntitle: Glossary\nurl: https://x/y\n---\n\n## Context window\n\nText."
    assert served_body(raw).lstrip().startswith("## Context window")


def test_aligning_both_sides_matches_what_was_served():
    canonical = "https://platform.claude.com/docs/en/glossary"
    served = "## Context\n\nSee [caching](/docs/en/build-with-claude/prompt-caching)."
    ours = ("# Glossary\n\n## Context\n\nSee "
            "[caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).")
    assert align(ours, title="Glossary", canonical=canonical) == \
           align(served, title="", canonical=canonical)


def test_a_link_absolute_in_the_source_is_not_a_difference():
    """REGRESSION: de-absolutising *our* links made 320 of 566 pages look wrong, because
    the served Markdown already mixes rooted and absolute links."""
    canonical = "https://platform.claude.com/docs/en/x"
    served = "Body [a](https://platform.claude.com/docs/en/api/overview) and [b](/docs/en/y)."
    ours = ("Body [a](https://platform.claude.com/docs/en/api/overview) and "
            "[b](https://platform.claude.com/docs/en/y).")
    assert align(ours, title="", canonical=canonical) == align(served, title="", canonical=canonical)


def test_a_title_the_site_itself_served_is_not_treated_as_added():
    """REGRESSION: `/docs/en/api/models` is served with `# Models` already at the top.
    Stripping it from our side made 94 pages look like they had dropped content."""
    canonical = "https://platform.claude.com/docs/en/api/models"
    served = "# Models\n\n## List Models\n\nBody."
    ours = "# Models\n\n## List Models\n\nBody."
    mine, theirs = align_pair(ours, served, title="Models", canonical=canonical)
    assert mine == theirs


def test_a_title_we_added_is_removed_before_comparing():
    canonical = "https://platform.claude.com/docs/en/about-claude/glossary"
    served = "## Context window\n\nBody."
    ours = "# Glossary\n\n## Context window\n\nBody."
    mine, theirs = align_pair(ours, served, title="Glossary", canonical=canonical)
    assert mine == theirs


def test_dropping_the_title_leaves_a_page_that_already_had_one():
    assert drop_added_title("# Real Heading\n\nBody.", "Different Title") == \
        "# Real Heading\n\nBody."


# --- notebook comparison ---------------------------------------------------

def test_fenced_text_handles_longer_fences():
    """REGRESSION: a page quoting Markdown opens with ````, and a three-backtick regex
    mis-pairs it — hiding 6 code cells that were present and correctly fenced."""
    body = ("````md\n``` shell\necho hi\n```\n````\n\n"
            "```\nasync def demo():\n    pass\n```\n")
    text = fenced_text(body)
    assert "async def demo():" in text
    assert "echo hi" in text


def test_notebook_comparison_matches_code_cells():
    notebook = {"cells": [
        {"cell_type": "code", "source": ["import os\n", "x = 1\n"]},
        {"cell_type": "markdown", "source": ["## Setup\n"]},
    ]}
    body = "# T\n\n## Setup\n\n```python\nimport os\nx = 1\n```\n"
    result = compare_notebook(body, notebook)
    assert result.ok and result.detail["code_matched"] == 1


def test_notebook_comparison_notices_missing_code():
    notebook = {"cells": [{"cell_type": "code", "source": ["import pandas as pd\n"]}]}
    result = compare_notebook("# T\n\nNo code here at all.\n", notebook)
    assert not result.ok and "not found in fences" in result.reason


# --- the review scorecard --------------------------------------------------

def test_scorecard_is_a_well_formed_markdown_table(tmp_path, corpus):
    """REGRESSION: a blank line between the separator and the first row closes the table,
    and every page renders as one run-on paragraph instead."""
    import runpy
    import sys

    data, add = corpus
    for i in range(3):
        add(source_url=f"https://docs.databricks.com/aws/en/delta/p{i}",
            canonical_url=f"https://docs.databricks.com/aws/en/delta/p{i}")

    out = tmp_path / "scorecard.md"
    argv = ["sample_review.py", "--data-dir", str(data), "--n", "4", "--out", str(out)]
    old = sys.argv
    sys.argv = argv
    try:
        runpy.run_path("scripts/sample_review.py", run_name="__main__")
    finally:
        sys.argv = old

    lines = out.read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| # |"))
    table = lines[start:]
    assert table[1].startswith("|---")
    body = [line for line in table[2:] if line.strip()]
    assert body, "the table has no rows"
    assert "" not in table[2:2 + len(body)], "a blank line inside the table closes it"

    widths = {line.count("|") for line in table[:2] + body}
    assert len(widths) == 1, f"ragged table: {widths}"


def test_scorecard_scoring_reads_marks_back(tmp_path, capsys):
    """A filled scorecard must summarise; an empty one must say so rather than claim 100%."""
    import runpy
    import sys

    card = tmp_path / "filled.md"
    card.write_text(
        "| # | page | url | title | complete | code | links | metadata | notes |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
        "| 1 | `a.md` | https://x/a | y | y | y | y | y |  |\n"
        "| 2 | `b.md` | https://x/b | y | n | y | y | y | lost a section |\n",
        encoding="utf-8")

    old = sys.argv
    sys.argv = ["sample_review.py", "--score", str(card)]
    try:
        with pytest.raises(SystemExit) as exit_info:
            runpy.run_path("scripts/sample_review.py", run_name="__main__")
    finally:
        sys.argv = old

    assert exit_info.value.code == 0
    out = capsys.readouterr().out
    assert "2 pages reviewed" in out
    assert "1/2 = 50%" in out          # one page carries a failing dimension


# --- fidelity: exact for plain pages, content-preserving for converted ones ---

def test_content_preservation_accepts_a_faithful_conversion():
    from scraper.validate.fidelity import content_preserved

    served = ('<CardGroup>\n  <Card title="Auth" href="https://x/auth">API keys and '
              '`profiles`</Card>\n</CardGroup>')
    ours = "- [Auth](https://x/auth) — API keys and `profiles`"
    ok, reason = content_preserved(ours, served)
    assert ok, reason


def test_content_preservation_notices_a_lost_link():
    from scraper.validate.fidelity import content_preserved

    served = '<Card title="Auth" href="https://x/auth">API keys</Card>'
    ok, reason = content_preserved("- **Auth** — API keys", served)
    assert not ok and "link" in reason


def test_content_preservation_notices_lost_words():
    """REGRESSION: the card blurb was run through `strip_code`, deleting inline code from
    17 pages. This is the check that found it."""
    from scraper.validate.fidelity import content_preserved

    served = '<Card title="Apple" href="https://x/a">Swift package for `LanguageModelSession`</Card>'
    ok, reason = content_preserved("- [Apple](https://x/a) — Swift package for", served)
    assert not ok and "word" in reason
