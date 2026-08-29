"""Extractor for the Claude Cookbook (`platform.claude.com/cookbook/**`). See PLAN.md §7.1.

The cookbook is a Next.js app rendering notebooks converted to HTML, and it differs from
the other two sources in one way that matters: **the page states its own metadata in an
embedded JSON payload**. Title, description, publication date, authors, topic tags, and a
link to the source notebook on GitHub all come from there rather than being scraped out of
the DOM or guessed.

The body still has to come from the DOM, and it needs one repair the other extractors do
not: code blocks are not `<pre>` elements at all. Each line is its own `<div>`, so left
alone they convert to prose — no fence, no line breaks (see `promote_code_blocks`).
"""

from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from ..category import category_for
from .base import (
    Extracted,
    RawPayload,
    collapse_blank_lines,
    parse_date,
    with_title_heading,
)
from .html import (
    absolutise_urls,
    meta_content,
    promote_code_blocks,
    soupify,
    strip_chrome,
    to_markdown,
)

NAME = "nextjs_article"
VERSION = "2"   # v2: display names for authors, not GitHub handles

CONTENT_SELECTORS = ("article", "main")
CODE_BLOCK_SELECTOR = ".code-scroll-region"
CODE_LINE_SELECTOR = "div.whitespace-pre-wrap"

_TITLE_SUFFIX = re.compile(r"\s*\|\s*Claude Cookbook\s*$", re.IGNORECASE)
_FENCE_LANG = re.compile(r"^```([\w+-]+)", re.MULTILINE)
# The design system draws its icons from a private-use font, so the copy/anchor controls
# carry characters like U+E09A as *text*. They are never content.
_PRIVATE_USE = re.compile("[\ue000-\uf8ff]")


def page_metadata(soup: BeautifulSoup) -> dict:
    """The `data.cookbook` block the page embeds, or `{}` (the index page has none)."""
    for script in soup.find_all("script", attrs={"type": "application/json"}):
        try:
            payload = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(payload, dict):
            cookbook = (payload.get("data") or {}).get("cookbook")
            if isinstance(cookbook, dict):
                return cookbook
    return {}


def extract(payload: RawPayload) -> Extracted:
    soup = soupify(payload.content)
    meta = page_metadata(soup)

    canonical = meta_content(soup, "meta[property='og:url']") or payload.canonical_url
    title = str(meta.get("title") or "").strip() or _title_from_head(soup)
    description = str(meta.get("description") or "").strip() or meta_content(
        soup, "meta[name='description']", "meta[property='og:description']"
    )

    names, handles = author_names(meta)

    content = next((node for sel in CONTENT_SELECTORS if (node := soup.select_one(sel))), None)
    if content is None:
        markdown = ""
    else:
        # Rebuild the code blocks *before* stripping chrome: the copy button sits inside
        # the block, and the line divs are what carry the source.
        promote_code_blocks(content, CODE_BLOCK_SELECTOR, line=CODE_LINE_SELECTOR)
        strip_chrome(content)
        absolutise_urls(content, canonical)
        markdown = collapse_blank_lines(_PRIVATE_USE.sub("", to_markdown(content)))

    markdown = with_title_heading(markdown, title)

    return Extracted(
        title=title,
        markdown=markdown,
        canonical_url=canonical,
        source_url=payload.url,
        company=payload.company,
        source_id=payload.source_id,
        category=_category(meta, payload),
        description=description or None,
        published_date=parse_date(str(meta["date"])) if meta.get("date") else None,
        tags=[str(t) for t in (meta.get("categories") or [])],
        authors=names,
        author_handles=handles,
        source_file_url=str(meta.get("github_url") or "") or None,
        code_languages=sorted({m.group(1) for m in _FENCE_LANG.finditer(markdown)}),
        extractor=NAME,
        extractor_version=VERSION,
    )


def author_names(meta: dict) -> tuple[list[str], list[str]]:
    """`(display names, handles)` for a page's authors.

    The `authors` array holds GitHub handles — `Briiick` — while `author_details` holds
    the name the site actually shows beside them — `Alexander Bricken`. Reading the
    handle put an informal identifier on 77 of 94 cookbook pages; the human review pass
    found it on the third page read.

    The two lists stay index-aligned, so `authors[i]` is always the person behind
    `author_handles[i]`. Falling back to the handle matters only if the site stops
    publishing a name: all 105 records currently have one.
    """
    handles = [str(a) for a in (meta.get("authors") or [])]
    names = {str(d.get("username")): str(d.get("name") or "").strip()
             for d in (meta.get("author_details") or [])}
    return [names.get(handle) or handle for handle in handles], handles


def _category(meta: dict, payload: RawPayload) -> str:
    """Group by the notebook's own directory in the cookbook repository.

    The URL is flat — every page would be its own category, which is no taxonomy at all.
    The declared `categories` are tags: multi-valued, so picking "the first" is arbitrary.
    The notebook's path (`tool_use/…`, `multimodal/…`) is single-valued, stated by the
    site, and the grouping the cookbook's own authors maintain.
    """
    path = str(meta.get("path") or "")
    top = path.split("/")[0].strip() if "/" in path else ""
    if top:
        return top.replace("_", "-")
    return category_for(payload.canonical_url, payload.include_paths)[0]


def _title_from_head(soup: BeautifulSoup) -> str:
    for value in (meta_content(soup, "meta[property='og:title']"),
                  soup.title.get_text(strip=True) if soup.title else None):
        if value:
            return _TITLE_SUFFIX.sub("", value).strip()
    return ""
