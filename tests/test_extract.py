"""Extraction: the contract, the quality gate, and the real defects found by reading output.

Every "regression" test here corresponds to something that actually went wrong against the
live corpus in step 5, not a hypothetical.
"""

from __future__ import annotations

from datetime import date

import pytest

from scraper.category import category_for, slug_for
from scraper.extract import RawPayload, extract_payload
from scraper.extract.base import check_quality, collapse_blank_lines, parse_date
from scraper.extract.html import code_text, soupify
from scraper.extract.passthrough_md import split_frontmatter
from scraper.records import Extracted


def payload(content: bytes, url="https://docs.databricks.com/aws/en/delta/tutorial",
            include=("/aws/en/",)) -> RawPayload:
    return RawPayload(url=url, company="databricks", source_id="databricks-docs",
                      content=content, content_type="text/html", final_url=url,
                      include_paths=list(include))


def extracted(**kw) -> Extracted:
    base = {"title": "T", "markdown": "x" * 300, "canonical_url": "u", "source_url": "u",
            "company": "c", "source_id": "s", "category": "cat"}
    return Extracted(**{**base, **kw})


# --- category (PLAN.md §7.3) ----------------------------------------------

def test_category_from_url_path():
    assert category_for("https://docs.databricks.com/aws/en/delta/x", ["/aws/en/"])[0] == "delta"
    assert category_for("https://platform.claude.com/docs/en/api/messages", ["/docs/en/"])[0] == "api"


def test_section_root_is_not_named_after_the_locale():
    """`/aws/en/` must not become category "en"."""
    assert category_for("https://docs.databricks.com/aws/en/", ["/aws/en/"])[0] == "index"
    assert category_for("https://platform.claude.com/cookbook/", ["/cookbook/"])[0] == "index"


def test_slug_is_stable_and_safe():
    assert slug_for("https://x.com/aws/en/delta/") == "aws-en-delta"
    assert slug_for("https://x.com/") == "index"


# --- quality gate (PLAN.md §7.2) ------------------------------------------

def test_short_body_is_rejected():
    assert not check_quality(extracted(markdown="tiny")).ok


def test_genuine_short_reference_page_is_accepted():
    """A 120-char error-condition stub is a real page; the SPA shell (31 chars) is not."""
    assert check_quality(extracted(markdown="x" * 120)).ok
    assert not check_quality(extracted(markdown="x" * 31)).ok


def test_error_markers_match_the_title_not_the_body():
    """REGRESSION: docs *about* errors legitimately contain error phrases.

    `/error-messages/hdfs-http-error-error-class` documents "404 Not Found", and a page on
    Kinesis permissions documents "access denied". Body matching rejected both.
    """
    assert check_quality(extracted(markdown="Status 404 Not Found. " + "x" * 300)).ok
    assert check_quality(extracted(markdown="This raises access denied. " + "x" * 300)).ok
    assert not check_quality(extracted(title="Page Not Found")).ok


def test_missing_title_is_rejected():
    assert not check_quality(extracted(title="  ")).ok


def test_unclosed_fence_is_rejected():
    assert not check_quality(extracted(markdown="```py\ncode\n" + "x" * 300)).ok


def test_longer_fence_around_nested_markdown_is_accepted():
    """REGRESSION: counting ``` is wrong — a block quoting Markdown opens with ````."""
    body = "````md\n``` shell\necho hi\n```\n````\n" + "x" * 300
    assert check_quality(extracted(markdown=body)).ok


def test_markup_check_ignores_fenced_code():
    """REGRESSION: a docs page shipping a React example is not a failed conversion."""
    jsx = "```jsx\n" + "<div><span/></div>\n" * 6 + "```\n" + "x" * 300
    assert check_quality(extracted(markdown=jsx)).ok
    assert not check_quality(extracted(markdown="<div><span><section><nav><div><span>" * 3)).ok


# --- helpers ---------------------------------------------------------------

def test_parse_date_formats():
    assert parse_date("Last updated on Jul 10, 2026") == date(2026, 7, 10)
    assert parse_date("July 10, 2026") == date(2026, 7, 10)
    assert parse_date("2026-07-10") == date(2026, 7, 10)
    assert parse_date("nonsense") is None
    assert parse_date(None) is None


def test_collapse_blank_lines():
    assert collapse_blank_lines("a\n\n\n\nb   \n") == "a\n\nb\n"


# --- HTML machinery --------------------------------------------------------

def test_comments_are_stripped_before_text_extraction():
    """REGRESSION: hydration comments split text nodes and mangle every title and paragraph."""
    html = "<h1>What is <!-- -->Delta Lake<!-- --> in <!-- -->Databricks<!-- -->?</h1>"
    assert soupify(html).h1.get_text() == "What is Delta Lake in Databricks?"


def test_code_lines_keep_their_newlines():
    """REGRESSION: Docusaurus puts each line in a span with no newline of its own."""
    html = (
        '<pre class="language-python"><code>'
        '<span class="token-line">import ray</span>'
        '<span class="token-line">import os</span>'
        "</code></pre>"
    )
    assert code_text(soupify(html).pre) == "import ray\nimport os"


# --- docusaurus extractor --------------------------------------------------

DOC_HTML = """
<html><head>
<meta property="og:title" content="What is Delta Lake? | Databricks on AWS"/>
<meta name="description" content="Delta Lake is a storage layer."/>
<meta property="og:url" content="https://docs.databricks.com/aws/en/delta/tutorial"/>
</head><body>
<nav class="theme-doc-breadcrumbs"><a>Tables</a><a>Delta Lake</a></nav>
<article>
  <div class="theme-doc-toc-mobile">ON THIS PAGE</div>
  <div class="theme-last-updated">Last updated on Jul 10, 2026</div>
  <div class="theme-doc-markdown markdown">
    <h1>What is <!-- -->Delta Lake<!-- -->?</h1>
    <p>Intro text that is long enough to pass the quality gate. %s</p>
    <p>See <a href="/aws/en/lakehouse/acid">ACID</a>.</p>
    <p><img src="data:image/png;base64,AAAA" alt="check marked yes"/> Databricks SQL</p>
    <div class="theme-admonition theme-admonition-note admonition">
      <div class="admonitionHeading_x">note</div>
      <div class="admonitionContent_y"><p>Careful here.</p></div>
    </div>
    <pre class="prism-code language-sql"><code>
      <span class="token-line">SELECT 1</span><span class="token-line">FROM t</span>
    </code></pre>
  </div>
</article></body></html>
""" % ("filler " * 40)


@pytest.fixture
def doc():
    record, quality = extract_payload(payload(DOC_HTML.encode()), "docusaurus")
    return record, quality


def test_docusaurus_extraction_passes_quality(doc):
    _record, quality = doc
    assert quality.ok, quality


def test_title_comes_from_og_title_without_the_site_suffix(doc):
    assert doc[0].title == "What is Delta Lake?"


def test_metadata_is_captured(doc):
    record = doc[0]
    assert record.description == "Delta Lake is a storage layer."
    assert record.updated_date == date(2026, 7, 10)
    assert record.breadcrumbs == ["Tables", "Delta Lake"]
    assert record.category == "delta"


def test_chrome_is_excluded_from_the_body(doc):
    body = doc[0].markdown
    assert "ON THIS PAGE" not in body
    assert "Last updated on" not in body


def test_relative_links_are_absolutised(doc):
    """REGRESSION: `](/aws/en/…)` resolves nowhere once the file is off the site."""
    assert "https://docs.databricks.com/aws/en/lakehouse/acid" in doc[0].markdown


def test_base64_images_become_alt_text(doc):
    """REGRESSION: inlined data: URIs were 13% of the whole corpus."""
    body = doc[0].markdown
    assert "data:image" not in body
    assert "(check marked yes)" in body


def test_admonition_label_is_not_duplicated(doc):
    body = doc[0].markdown
    assert "> **Note:**" in body
    assert body.count("note") <= 1, "the site's own label div must be consumed, not repeated"


def test_code_fence_carries_its_language(doc):
    assert "```sql" in doc[0].markdown
    assert "SELECT 1\nFROM t" in doc[0].markdown
    assert doc[0].code_languages == ["sql"]


# --- passthrough_md extractor ----------------------------------------------

MD = b"""---
title: Glossary
url: https://platform.claude.com/docs/en/about-claude/glossary
description: Key terms.
---

## Context window

The context window refers to the amount of text.

```python
x = 1
```
"""


def test_frontmatter_split():
    meta, body = split_frontmatter(MD.decode())
    assert meta["title"] == "Glossary"
    assert body.lstrip().startswith("## Context window")


def test_frontmatter_absent_is_not_an_error():
    assert split_frontmatter("# Just a heading") == ({}, "# Just a heading")


def test_passthrough_keeps_the_body_verbatim():
    p = RawPayload(url="https://platform.claude.com/docs/en/about-claude/glossary",
                   company="anthropic", source_id="anthropic-docs", content=MD,
                   content_type="text/markdown",
                   final_url="https://platform.claude.com/docs/en/about-claude/glossary.md",
                   include_paths=["/docs/en/"])
    record, _quality = extract_payload(p, "passthrough_md")
    assert record.title == "Glossary"
    assert record.description == "Key terms."
    assert record.code_languages == ["python"]
    assert "## Context window" in record.markdown


def test_category_ignores_the_md_fetch_suffix():
    """REGRESSION: category came from the `.md` URL, creating a dir named "get-started.md"."""
    p = RawPayload(url="https://platform.claude.com/docs/en/get-started",
                   company="anthropic", source_id="anthropic-docs",
                   content=b"# Start\n\n" + b"x" * 300, content_type="text/markdown",
                   final_url="https://platform.claude.com/docs/en/get-started.md",
                   include_paths=["/docs/en/"])
    record, _ = extract_payload(p, "passthrough_md")
    assert record.category == "get-started"
    assert not record.canonical_url.endswith(".md")


def test_unknown_extractor_raises():
    with pytest.raises(KeyError):
        extract_payload(payload(b"<html></html>"), "nope")
