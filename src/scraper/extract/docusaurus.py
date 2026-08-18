"""Extractor for Docusaurus documentation sites (docs.databricks.com). See PLAN.md §7.1.

Content lives in `.theme-doc-markdown`, **not** in `<article>` — the article element also
wraps the mobile TOC, the edit-meta row, and a layout wrapper, all of which would
otherwise land in the corpus as body text.

Metadata is taken from the places the site states it explicitly (`og:title`,
`meta[name=description]`, the visible "Last updated on …") rather than inferred from the
body, so a change in page layout degrades one field instead of silently corrupting the
document.
"""

from __future__ import annotations

import re

from ..category import category_for
from .base import Extracted, RawPayload, collapse_blank_lines, parse_date
from .html import (
    STRIP_SELECTORS,
    absolutise_urls,
    first_text,
    meta_content,
    promote_admonitions,
    soupify,
    strip_chrome,
    to_markdown,
)

NAME = "docusaurus"
VERSION = "5"   # v2 admonition labels; v3 code newlines; v4 absolute links; v5 keep the h1

CONTENT_SELECTORS = (".theme-doc-markdown", "article", "main")

# Docusaurus wraps the page's `<h1>` in a `<header>` *inside* `.theme-doc-markdown`, so
# the generic "strip every header" rule deleted the title from the body of every page.
# The site chrome is outside the content root, so nothing here needs that rule.
CONTENT_STRIP_SELECTORS = tuple(s for s in STRIP_SELECTORS if s != "header")

# og:title carries the site name: "What is Delta Lake in Databricks? | Databricks on AWS".
_TITLE_SUFFIX = re.compile(r"\s*\|\s*Databricks(?:\s+on\s+\w+)?\s*$", re.IGNORECASE)
_FENCE_LANG = re.compile(r"^```([\w+-]+)", re.MULTILINE)


def extract(payload: RawPayload) -> Extracted:
    soup = soupify(payload.content)

    breadcrumbs = [
        text
        for crumb in soup.select("nav.theme-doc-breadcrumbs a, .breadcrumbs__link")
        if (text := crumb.get_text(" ", strip=True))
    ]
    updated = parse_date(first_text(soup, ".theme-last-updated"))
    description = meta_content(soup, "meta[name='description']", "meta[property='og:description']")
    title = _title(soup)

    canonical = meta_content(soup, "meta[property='og:url']") or payload.canonical_url

    content = None
    for selector in CONTENT_SELECTORS:
        content = soup.select_one(selector)
        if content is not None:
            break

    if content is None:
        markdown = ""
    else:
        # Order matters: promote admonitions to blockquotes *before* stripping chrome,
        # since the stripper removes the buttons and hash-links inside them.
        promote_admonitions(content)
        strip_chrome(content, CONTENT_STRIP_SELECTORS)
        absolutise_urls(content, canonical)
        markdown = collapse_blank_lines(to_markdown(content))

    category, _ = category_for(payload.canonical_url, payload.include_paths)

    return Extracted(
        title=title,
        markdown=markdown,
        canonical_url=canonical,
        source_url=payload.url,
        company=payload.company,
        source_id=payload.source_id,
        category=category,
        description=description,
        updated_date=updated,
        breadcrumbs=breadcrumbs,
        code_languages=sorted({m.group(1) for m in _FENCE_LANG.finditer(markdown)}),
        extractor=NAME,
        extractor_version=VERSION,
    )


def _title(soup) -> str:
    """Prefer `og:title` — the `<h1>` is fragmented by hydration markers."""
    og = meta_content(soup, "meta[property='og:title']")
    if og:
        return _TITLE_SUFFIX.sub("", og).strip()

    heading = first_text(soup, ".theme-doc-markdown h1", "article h1", "h1")
    if heading:
        return heading

    title_tag = soup.find("title")
    return _TITLE_SUFFIX.sub("", title_tag.get_text(strip=True)).strip() if title_tag else ""
