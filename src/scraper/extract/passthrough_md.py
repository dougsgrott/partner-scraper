"""Extractor for pages fetched as native Markdown. See PLAN.md §2a, §7.1.

Anthropic's `.md` twins arrive already clean, with YAML frontmatter the site itself
maintains::

    ---
    title: Glossary
    url: https://platform.claude.com/docs/en/about-claude/glossary
    description: These concepts are not unique to Claude…
    ---

    ## Context window
    …

So this extractor does almost nothing, and that is the point: no DOM, no selectors, no
conversion, and therefore no class of conversion bug. It splits the frontmatter, keeps the
body verbatim, and records which fence languages appear.
"""

from __future__ import annotations

import re

import yaml

from ..category import category_for
from .base import Extracted, RawPayload, collapse_blank_lines, parse_date

NAME = "passthrough_md"
VERSION = "2"   # v2: category derived from the page URL, not the `.md` fetch URL

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_FENCE_LANG = re.compile(r"^```([\w+-]+)", re.MULTILINE)
_FIRST_HEADING = re.compile(r"^#{1,3}\s+(.+)$", re.MULTILINE)


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Split leading YAML frontmatter from the body. Returns `({}, text)` if absent."""
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}, text
    if not isinstance(meta, dict):
        return {}, text
    return meta, text[match.end():]


def extract(payload: RawPayload) -> Extracted:
    meta, body = split_frontmatter(payload.text)
    body = collapse_blank_lines(body)

    title = str(meta.get("title") or "").strip()
    if not title:
        # No frontmatter title — fall back to the first heading, then the URL slug.
        heading = _FIRST_HEADING.search(body)
        title = heading.group(1).strip() if heading else _title_from_url(payload.canonical_url)

    # The fetched URL ends in `.md`; the *page* does not. Deriving the category from the
    # fetch URL produced categories like "get-started.md" — and therefore corpus
    # directories named after a file extension.
    canonical = str(meta.get("url") or "").strip() or _strip_md(payload.canonical_url)
    category, _ = category_for(canonical, payload.include_paths)

    return Extracted(
        title=title,
        markdown=body,
        canonical_url=canonical,
        source_url=payload.url,
        company=payload.company,
        source_id=payload.source_id,
        category=category,
        description=(str(meta["description"]).strip() if meta.get("description") else None),
        published_date=parse_date(_as_text(meta.get("published"))),
        updated_date=parse_date(_as_text(meta.get("updated") or meta.get("last_updated"))),
        code_languages=sorted({m.group(1) for m in _FENCE_LANG.finditer(body)}),
        extractor=NAME,
        extractor_version=VERSION,
    )


def _strip_md(url: str) -> str:
    return url.removesuffix(".md")


def _as_text(value) -> str | None:
    return None if value is None else str(value)


def _title_from_url(url: str) -> str:
    from urllib.parse import urlparse

    leaf = [s for s in urlparse(url).path.split("/") if s]
    return leaf[-1].replace("-", " ").title() if leaf else "Untitled"
