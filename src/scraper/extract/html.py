"""Shared HTML → Markdown machinery for the site-specific extractors.

Two things here are load-bearing and were found by reading real archived pages rather
than by reasoning about HTML in the abstract:

**Comments must be stripped before any text extraction.** React/Docusaurus pages are full
of `<!-- -->` hydration markers *between text nodes*. BeautifulSoup treats them as node
boundaries, so `get_text(strip=True)` on
`<h1>What is <!-- -->Delta Lake<!-- --> in <!-- -->Databricks<!-- -->?</h1>` yields
`"What isDelta LakeinDatabricks?"`. Joining with a space instead gives
`"What is Delta Lake in Databricks ?"` — wrong in a different way. Removing the comments
first is the only variant that produces the real title, and the same corruption applies to
every paragraph in the body.

**Code blocks are one `<span class="token-line">` per line, and those spans carry no
newline of their own.** So `pre.get_text()` returns
`"import rayfrom ray.util.spark import setup_ray_cluster…"` — every line in every code
example silently run together. The lines have to be rejoined explicitly. This corrupts
quietly: the Markdown still looks like a code block, so nothing downstream notices that
the code in it no longer runs.

**Code language lives on the `<pre>`, not the `<code>`.** Docusaurus emits
`<pre class="prism-code language-sql">` wrapping `<code class="codeBlockLines_…">`.
Reading the language off `<code>` finds nothing.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Comment, Tag
from markdownify import MarkdownConverter

# Chrome that is never page content, whatever the site.
STRIP_SELECTORS = (
    "script", "style", "noscript", "svg", "template",
    "nav", "header", "footer",
    "[aria-hidden='true']",
    ".theme-doc-toc-desktop", ".theme-doc-toc-mobile", ".tocCollapsible",
    ".theme-doc-breadcrumbs", ".pagination-nav", ".theme-doc-footer-edit-meta-row",
    ".theme-last-updated", ".hash-link", "button",
)

_LANG_CLASS = re.compile(r"(?:^|\s)language-([\w+-]+)")


def soupify(html: str | bytes) -> BeautifulSoup:
    """Parse HTML and remove comments, which otherwise corrupt every text run."""
    soup = BeautifulSoup(html, "lxml")
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()
    return soup


def strip_chrome(node: Tag, selectors: tuple[str, ...] = STRIP_SELECTORS) -> Tag:
    """Remove navigation, TOC, and other non-content elements in place."""
    for selector in selectors:
        for element in node.select(selector):
            element.decompose()
    return node


def code_language(pre: Tag) -> str:
    """Read a fence language from the `<pre>`'s classes, falling back to `<code>`'s."""
    for element in (pre, pre.find("code")):
        if element is None:
            continue
        match = _LANG_CLASS.search(" ".join(element.get("class") or []))
        if match:
            lang = match.group(1)
            return "" if lang in ("text", "none", "plaintext") else lang
    return ""


def code_text(pre: Tag) -> str:
    """Recover a code block's source, restoring the newlines the markup omits.

    Docusaurus splits each line into `<span class="token-line">` with no newline between
    them, so the lines must be rejoined here or every multi-line example comes out as one
    unbroken line.
    """
    lines = pre.select(".token-line")
    if lines:
        return "\n".join(line.get_text() for line in lines)
    return pre.get_text()


def absolutise_urls(node: Tag, base_url: str) -> None:
    """Rewrite relative `href`/`src` against the page's own URL.

    A corpus read outside the site is the whole point, and `](/aws/en/lakehouse/acid)`
    resolves nowhere once the file is on disk or in a retrieval index.
    """
    for element, attr in ((a, "href") for a in node.select("a[href]")):
        value = element.get(attr, "")
        if value and not value.startswith(("http://", "https://", "#", "mailto:", "data:")):
            element[attr] = urljoin(base_url, value)
    for img in node.select("img[src]"):
        src = img.get("src", "")
        if src and not src.startswith(("http://", "https://", "data:")):
            img["src"] = urljoin(base_url, src)


class DocsConverter(MarkdownConverter):
    """MarkdownConverter tuned for documentation pages."""

    def convert_img(self, el, text, parent_tags):
        """Keep the alt text, drop inline base64 payloads.

        Databricks marks feature availability with small `data:image/png;base64,…` icons.
        Inlined verbatim they accounted for 13% of the whole corpus — 11 MiB of base64
        that no reader wants and no retrieval index should ever embed.
        """
        src = el.attrs.get("src", "")
        if src.startswith("data:"):
            alt = el.attrs.get("alt", "").strip()
            return f"({alt})" if alt else ""
        return super().convert_img(el, text, parent_tags)

    def convert_pre(self, el, text, parent_tags):
        code = code_text(el)
        if not code.strip():
            return ""
        lang = code_language(el)
        fence = "```"
        while fence in code:                  # a block quoting Markdown needs a longer fence
            fence += "`"
        return f"\n\n{fence}{lang}\n{code.rstrip()}\n{fence}\n\n"


def to_markdown(node: Tag, **options) -> str:
    """Convert a cleaned element subtree to Markdown."""
    opts = {
        "heading_style": "ATX",
        "bullets": "-",
        "strip": ["a"] if options.pop("drop_links", False) else None,
        "escape_underscores": False,
        "escape_asterisks": False,
        **options,
    }
    opts = {k: v for k, v in opts.items() if v is not None}
    return DocsConverter(**opts).convert_soup(node)


def promote_admonitions(node: Tag) -> None:
    """Turn Docusaurus admonition boxes into blockquotes.

    Left alone they flatten into an unlabelled paragraph, so a `warning` reads as ordinary
    prose — a meaningful loss on reference documentation.
    """
    for box in node.select(".theme-admonition, .admonition"):
        # Docusaurus renders the label in its own heading div. Take the text from there
        # and remove it — leaving it in place duplicates the label in the blockquote.
        heading = box.select_one("[class*='admonitionHeading']")
        if heading is not None:
            label = heading.get_text(" ", strip=True).capitalize()
            heading.decompose()
        else:
            classes = " ".join(box.get("class") or [])
            match = re.search(r"admonition-(\w+)", classes) or re.search(r"alert--(\w+)", classes)
            label = (match.group(1) if match else "note").capitalize()

        quote = node.new_tag("blockquote") if hasattr(node, "new_tag") else None
        if quote is None:                      # detached tree; fall back to a soup handle
            quote = BeautifulSoup("<blockquote></blockquote>", "lxml").blockquote

        strong = BeautifulSoup(f"<p><strong>{label}:</strong></p>", "lxml").p
        quote.append(strong)
        for child in list(box.children):
            quote.append(child.extract() if isinstance(child, Tag) else child)
        box.replace_with(quote)


def first_text(node: Tag, *selectors: str) -> str | None:
    """Text of the first matching selector, whitespace-normalised."""
    for selector in selectors:
        found = node.select_one(selector)
        if found:
            text = re.sub(r"\s+", " ", found.get_text()).strip()
            if text:
                return text
    return None


def meta_content(soup: BeautifulSoup, *queries: str) -> str | None:
    for query in queries:
        tag = soup.select_one(query)
        if tag and tag.get("content"):
            return tag["content"].strip()
    return None
