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
from urllib.parse import urljoin

import yaml

from ..category import category_for
from .base import Extracted, RawPayload, collapse_blank_lines, parse_date

NAME = "passthrough_md"
VERSION = "3"   # v2: category from the page URL; v3: absolute links + a title heading

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_FENCE_LANG = re.compile(r"^```([\w+-]+)", re.MULTILINE)
_FIRST_HEADING = re.compile(r"^#{1,3}\s+(.+)$", re.MULTILINE)
_FENCED_BLOCK = re.compile(r"^(?P<fence>`{3,}|~{3,}).*?(?:^(?P=fence)`*\s*$|\Z)", re.MULTILINE | re.DOTALL)
# `](/docs/en/…)` and `[ref]: /docs/en/…` — site-rooted, so meaningless once the file
# leaves the site. Only rooted paths are touched: a bare `foo.md` may be prose, and
# `[string]()` (which the API reference emits) has no target at all.
_ROOTED_LINK = re.compile(r"(?P<open>\]\(|^\[[^\]]+\]:\s+)(?P<path>/(?!/)[^\s)]*)", re.MULTILINE)


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


def absolutise_links(markdown: str, base_url: str) -> str:
    """Resolve site-rooted Markdown links against the page URL, leaving code alone."""
    def fix(match: re.Match) -> str:
        return match.group("open") + urljoin(base_url, match.group("path"))

    out: list[str] = []
    cursor = 0
    for block in _FENCED_BLOCK.finditer(markdown):
        out.append(_ROOTED_LINK.sub(fix, markdown[cursor:block.start()]))
        out.append(block.group(0))            # fenced code passes through untouched
        cursor = block.end()
    out.append(_ROOTED_LINK.sub(fix, markdown[cursor:]))
    return "".join(out)


def with_title_heading(markdown: str, title: str) -> str:
    """Open the document with its own title unless it already does.

    The served `.md` keeps the title in frontmatter only, so the body starts at the first
    `##`. Every other page in the corpus opens with an `# H1`, and a chunk of a document
    that never names it is much harder to use downstream.
    """
    first = next((line for line in markdown.splitlines() if line.strip()), "")
    heading = first.lstrip("#").strip() if first.startswith("#") else None
    if not title or first.startswith("# ") or (heading and heading.casefold() == title.casefold()):
        return markdown            # already named — never state the title twice
    return f"# {title}\n\n{markdown.lstrip()}"


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

    body = with_title_heading(absolutise_links(body, canonical), title)

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
