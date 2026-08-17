"""The single fetch + enrich Claude call — the heart of the tool.

One request per page: Claude fetches the URL via the server-side ``web_fetch`` tool,
cleans the body to Markdown, and returns a ``PageRecord``-shaped structured result.
FETCH and ENRICH are deliberately one call. See PLAN.md §5.2.

Key facts this relies on:
  * web_fetch only fetches URLs already in the conversation — we pass exactly the target.
  * structured output and citations are mutually exclusive — we keep structured output;
    provenance is the source URL (known from discovery), recorded later in frontmatter.
  * max_content_tokens caps fetched page size (the main per-page cost lever).
  * a server-tool loop can end with stop_reason "pause_turn" — we continue it, bounded.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

import anthropic

from .schema import PageRecord

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None

# Non-streaming keeps us under SDK HTTP timeouts; 16k output fits typical doc pages.
# Larger pages that truncate surface as parse_error (see IngestResult.status).
_MAX_TOKENS = 16000
_MAX_CONTINUATIONS = 4  # bound the pause_turn server-tool loop
_FALLBACK_THEME = "other"

IngestStatus = Literal["ok", "fetch_error", "parse_error"]


@dataclass
class IngestResult:
    """Outcome of ingesting one URL. Maps directly to the store index `status` column."""

    url: str
    status: IngestStatus
    record: PageRecord | None = None
    error: str | None = None


def _get_client() -> anthropic.Anthropic:
    """Lazily create the shared Anthropic client (reads ANTHROPIC_API_KEY from env)."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _system_prompt(company: str, allowed_themes: list[str]) -> str:
    themes = ", ".join(allowed_themes)
    return (
        "You extract a partner-documentation page into a structured record.\n"
        "Fetch the given URL with the web_fetch tool, then return:\n"
        "- markdown: the cleaned page body as Markdown. Drop nav, sidebars, footers, "
        "cookie banners, and ads; keep headings, prose, code blocks, and tables.\n"
        "- title: the page's main title.\n"
        "- content_type: one of docs, blog, changelog, pricing, reference, other.\n"
        "- published_date / updated_date: from page metadata (JSON-LD, <meta>, <time>, "
        "or a visible 'Updated' line). Use null when the page shows no such date — do "
        "not guess.\n"
        "- summary: 2-3 sentences describing what the page covers.\n"
        "- key_entities: notable product names, APIs, or concepts on the page.\n"
        f"- theme: choose EXACTLY ONE from this fixed list: {themes}. "
        f"If nothing fits, use '{_FALLBACK_THEME}'.\n"
        f"\nThis page belongs to company '{company}'."
    )


def fetch_enrich(
    url: str,
    company: str,
    allowed_themes: list[str],
    model: str,
    max_content_tokens: int,
    *,
    client: anthropic.Anthropic | None = None,
) -> IngestResult:
    """Fetch and enrich a single URL into a PageRecord.

    Never raises for a single bad page — network/API failures return a "fetch_error"
    result and malformed output returns a "parse_error" result, so the pipeline can
    record the status and move on.
    """
    client = client or _get_client()
    system = [{
        "type": "text",
        "text": _system_prompt(company, allowed_themes),
        "cache_control": {"type": "ephemeral"},  # cache instructions+taxonomy across pages
    }]
    tools = [{
        "type": "web_fetch_20260209",
        "name": "web_fetch",
        "max_uses": 3,
        "max_content_tokens": max_content_tokens,
    }]
    messages: list[dict] = [{"role": "user", "content": f"Fetch and extract this page: {url}"}]

    resp = None
    try:
        for _ in range(_MAX_CONTINUATIONS):
            resp = client.messages.parse(
                model=model,
                max_tokens=_MAX_TOKENS,
                system=system,
                tools=tools,
                messages=messages,
                output_format=PageRecord,
            )
            if resp.stop_reason != "pause_turn":
                break
            # Server-tool loop hit its iteration cap — resume by echoing content back.
            messages.append({"role": "assistant", "content": resp.content})
        else:
            return IngestResult(url, "fetch_error", error="exceeded pause_turn continuations")
    except anthropic.APIError as exc:
        logger.warning("API error ingesting %s: %s", url, exc)
        return IngestResult(url, "fetch_error", error=f"{type(exc).__name__}: {exc}")

    if resp.stop_reason == "refusal":
        return IngestResult(url, "fetch_error", error="model refused the request")
    if resp.stop_reason == "max_tokens":
        return IngestResult(url, "parse_error", error="output truncated at max_tokens")

    record = resp.parsed_output
    if record is None:
        return IngestResult(url, "parse_error", error="no structured output returned")

    # Force the known company; coerce an out-of-taxonomy theme to the fallback.
    theme = record.theme if record.theme in allowed_themes else _FALLBACK_THEME
    if theme != record.theme:
        logger.info("coerced theme %r -> %r for %s", record.theme, theme, url)
    record = record.model_copy(update={"company": company, "theme": theme})

    return IngestResult(url, "ok", record=record)
