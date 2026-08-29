"""The cookbook extractor — PLAN.md §7.1, §12 step 8.

The cookbook is the third source and the first that states its own metadata in the page,
so the tests split cleanly: what the JSON payload gives us, and what the DOM still has to
be repaired to give us.
"""

from __future__ import annotations

import json
from datetime import date

import pytest

from scraper.extract import extract_payload
from scraper.extract.html import promote_code_blocks, soupify
from scraper.extract.nextjs_article import page_metadata
from scraper.records import RawPayload

META = {
    "title": "Enhancing RAG with contextual retrieval",
    "description": "Improve RAG accuracy by adding context to chunks.",
    "path": "capabilities/contextual-embeddings/guide.ipynb",
    "authors": ["Briiick"],
    "date": "2024-09-13",
    "categories": ["RAG & Retrieval", "Tools"],
    "slug": "capabilities-contextual-embeddings-guide",
    "github_url": "https://github.com/anthropics/claude-cookbooks/blob/main/x/guide.ipynb",
    "author_details": [{"username": "Briiick", "name": "Alexander Bricken",
                        "website": "https://github.com/Briiick"}],
}

PAGE = """
<html><head>
<title>Enhancing RAG with contextual retrieval | Claude Cookbook</title>
<meta property="og:url" content="https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide"/>
<script type="application/json">{payload}</script>
</head><body><main><article>
  <h1><button aria-label="Copy link"></button>Enhancing RAG with Contextual Retrieval</h1>
  <p>{body}</p>
  <p>See the <a href="/cookbook/misc-read-web-pages">reader guide<span class="sr-only">(opens in new tab)</span></a>.</p>
  <div class="group relative rounded-lg">
    <button aria-label="Copy code"></button>
    <div class="code-scroll-region" tabindex="0">
      <div class="font-mono">
        <div class="min-h-[1lh] whitespace-pre-wrap">import os</div>
        <div class="min-h-[1lh] whitespace-pre-wrap"></div>
        <div class="min-h-[1lh] whitespace-pre-wrap">client = anthropic.Anthropic()</div>
      </div>
    </div>
  </div>
  <pre class="whitespace-pre overflow-x-auto font-mono">Processing chunks: 100%
Done.</pre>
</article></main></body></html>
""".format(payload=json.dumps({"data": {"cookbook": META}}),
           body="Body text long enough to pass. " * 8)

URL = "https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide"


def payload(content: str = PAGE, url: str = URL) -> RawPayload:
    return RawPayload(url=url, company="anthropic", source_id="anthropic-cookbook",
                      content=content.encode(), content_type="text/html", final_url=url,
                      include_paths=["/cookbook/"])


@pytest.fixture
def cookbook():
    return extract_payload(payload(), "nextjs_article")


# --- metadata the page states about itself ---------------------------------

def test_extraction_passes_quality(cookbook):
    assert cookbook[1].ok, cookbook[1]


def test_metadata_comes_from_the_embedded_json(cookbook):
    record = cookbook[0]
    assert record.title == META["title"]
    assert record.description == META["description"]
    assert record.published_date == date(2024, 9, 13)
    assert record.tags == ["RAG & Retrieval", "Tools"]
    assert record.authors == ["Alexander Bricken"]
    assert record.author_handles == ["Briiick"]
    assert record.source_file_url == META["github_url"]


def test_the_display_name_is_preferred_over_the_handle(cookbook):
    """REGRESSION: `authors` holds GitHub handles, so 77 of 94 pages credited `Briiick`
    rather than Alexander Bricken. Found by the human review pass, on page three."""
    record = cookbook[0]
    assert record.authors == ["Alexander Bricken"]
    assert record.author_handles == ["Briiick"]


def test_a_handle_without_a_display_name_is_kept_as_is():
    meta = {**META, "author_details": [{"username": "Briiick", "name": ""}]}
    page = PAGE.replace(json.dumps({"data": {"cookbook": META}}),
                        json.dumps({"data": {"cookbook": meta}}))
    record, _ = extract_payload(payload(page), "nextjs_article")
    assert record.authors == ["Briiick"] and record.author_handles == ["Briiick"]


def test_missing_author_details_falls_back_to_handles():
    meta = {k: v for k, v in META.items() if k != "author_details"}
    page = PAGE.replace(json.dumps({"data": {"cookbook": META}}),
                        json.dumps({"data": {"cookbook": meta}}))
    record, _ = extract_payload(payload(page), "nextjs_article")
    assert record.authors == ["Briiick"]


def test_multiple_authors_stay_index_aligned():
    """10 real pages have two authors; a name and handle that drift apart would be worse
    than either on its own."""
    meta = {**META,
            "authors": ["rodrigo-olivares", "JiriDeJonghe"],
            "author_details": [{"username": "JiriDeJonghe", "name": "Jiri De Jonghe"},
                               {"username": "rodrigo-olivares", "name": "Rodrigo Olivares"}]}
    page = PAGE.replace(json.dumps({"data": {"cookbook": META}}),
                        json.dumps({"data": {"cookbook": meta}}))
    record, _ = extract_payload(payload(page), "nextjs_article")
    assert record.author_handles == ["rodrigo-olivares", "JiriDeJonghe"]
    assert record.authors == ["Rodrigo Olivares", "Jiri De Jonghe"]


def test_category_groups_by_notebook_directory(cookbook):
    """The URL is flat — every page would otherwise be a category of one."""
    assert cookbook[0].category == "capabilities"


def test_underscored_directories_become_hyphenated():
    meta = {**META, "path": "tool_use/memory/cookbook.ipynb"}
    page = PAGE.replace(json.dumps({"data": {"cookbook": META}}),
                        json.dumps({"data": {"cookbook": meta}}))
    record, _ = extract_payload(payload(page), "nextjs_article")
    assert record.category == "tool-use"


def test_a_page_without_the_payload_still_extracts():
    """The cookbook index is the one page with no `data.cookbook` block."""
    page = PAGE.replace(json.dumps({"data": {"cookbook": META}}), "{}")
    record, quality = extract_payload(
        payload(page, url="https://platform.claude.com/cookbook/"), "nextjs_article")
    assert quality.ok
    assert record.title == "Enhancing RAG with contextual retrieval"   # from <title>
    assert record.category == "index"          # falls back to the URL rule (§7.3)
    assert record.tags == [] and record.published_date is None


def test_malformed_json_is_not_fatal():
    page = PAGE.replace(json.dumps({"data": {"cookbook": META}}), "{not json")
    assert extract_payload(payload(page), "nextjs_article")[1].ok


def test_page_metadata_ignores_unrelated_json_blocks():
    soup = soupify('<script type="application/json">{"other": 1}</script>'
                   '<script type="application/json">{"data": {"cookbook": {"title": "x"}}}</script>')
    assert page_metadata(soup) == {"title": "x"}


# --- the DOM repairs -------------------------------------------------------

def test_code_blocks_become_real_fences(cookbook):
    """REGRESSION: each code line is its own `<div>` and there is no `<pre>` at all.

    Left alone the block converts to prose — no fence, and every line run together.
    """
    body = cookbook[0].markdown
    assert "```\nimport os\n\nclient = anthropic.Anthropic()\n```" in body


def test_notebook_output_is_kept(cookbook):
    assert "Processing chunks: 100%\nDone." in cookbook[0].markdown


def test_promote_code_blocks_reports_what_it_rebuilt():
    soup = soupify('<div class="code-scroll-region">'
                   '<div class="whitespace-pre-wrap">a = 1</div>'
                   '<div class="whitespace-pre-wrap">b = 2</div></div>')
    assert promote_code_blocks(soup, ".code-scroll-region", line="div.whitespace-pre-wrap") == 1
    assert soup.pre.code.get_text() == "a = 1\nb = 2"


def test_icon_font_characters_are_removed(cookbook):
    """The design system draws icons with private-use glyphs, which are text to a parser."""
    assert "" not in cookbook[0].markdown
    assert "" not in cookbook[0].markdown


def test_screen_reader_only_text_is_not_link_text(cookbook):
    """REGRESSION: `[reader guide(opens in new tab)](…)` — 389 of these across 95 pages."""
    assert "opens in new tab" not in cookbook[0].markdown
    assert "[reader guide](https://platform.claude.com/cookbook/misc-read-web-pages)" \
        in cookbook[0].markdown


def test_the_document_opens_with_its_title(cookbook):
    assert cookbook[0].markdown.startswith("# Enhancing RAG with Contextual Retrieval")


def test_a_page_that_opens_on_a_code_cell_gets_its_title():
    page = PAGE.replace(
        '<h1><button aria-label="Copy link"></button>'
        'Enhancing RAG with Contextual Retrieval</h1>', "")
    record, _ = extract_payload(payload(page), "nextjs_article")
    assert record.markdown.startswith(f"# {META['title']}\n")
