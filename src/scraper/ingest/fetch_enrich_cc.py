"""Claude Agent SDK ingestion path — a parallel to `fetch_enrich.py`.

Same contract (`fetch_enrich_cc(...) -> IngestResult`) as the API path, but instead of the
API's server-side `web_fetch` + `messages.parse`, this:

  1. fetches the raw HTML ourselves with httpx (full fidelity, our control), then
  2. hands it to a **tool-less, harness-stripped** Claude Agent SDK `query()` whose only
     job is to clean + extract into the PageRecord schema via native structured output.

Auth: runs on the ambient Claude Code login when ANTHROPIC_API_KEY is unset (verified).
See the plan: `.claude/plans/nicely-done-now-i-reflective-lecun.md`.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass

import httpx
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKError,
    RateLimitEvent,
    ResultMessage,
    query,
)
from pydantic import ValidationError

from .fetch_enrich import IngestResult  # reuse the exact same result contract
from .schema import PageRecord

logger = logging.getLogger(__name__)


@dataclass
class RateLimitSnapshot:
    """The latest Claude Code usage-window state seen during a query (for the runner)."""

    status: str  # 'allowed' | 'allowed_warning' | 'rejected'
    utilization: float | None = None  # fraction of the active window consumed, 0..1
    resets_at: int | None = None  # unix ts when the window resets
    rate_limit_type: str | None = None  # five_hour | seven_day | seven_day_* | overage

_FALLBACK_THEME = "other"
_CHARS_PER_TOKEN = 4  # rough budget: char cap ≈ max_content_tokens * 4
_USER_AGENT = "claude-scraper/0.1 (+https://github.com/; docs sync)"
_HTTP_TIMEOUT = 30.0
_MAX_TURNS = 6  # room for the SDK's structured-output re-prompts

_SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _strip_html(html: str) -> str:
    """Drop <script>/<style>/comments to cut tokens; leave the rest for the model."""
    html = _SCRIPT_STYLE_RE.sub(" ", html)
    return _COMMENT_RE.sub(" ", html)


def _fetch_raw_html(url: str, max_chars: int) -> str:
    """GET the page (following redirects), strip noise, truncate to a char budget."""
    with httpx.Client(
        follow_redirects=True,
        timeout=_HTTP_TIMEOUT,
        headers={"User-Agent": _USER_AGENT},
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
    return _strip_html(resp.text)[:max_chars]


def _system_prompt(company: str, allowed_themes: list[str]) -> str:
    themes = ", ".join(allowed_themes)
    return (
        "You are given the raw HTML of a partner-documentation page. Produce a single "
        "structured record via the required output format. Fields:\n"
        "- markdown: the cleaned page body as Markdown. Drop nav, sidebars, footers, "
        "cookie banners, and ads; keep headings, prose, code blocks, and tables.\n"
        "- title: the page's main title.\n"
        "- content_type: one of docs, blog, changelog, pricing, reference, other.\n"
        "- published_date / updated_date: from page metadata (JSON-LD, <meta>, <time>, or "
        "a visible 'Updated' line) as YYYY-MM-DD. Use null when absent — do not guess.\n"
        "- summary: 2-3 sentences on what the page covers.\n"
        "- key_entities: notable product names, APIs, or concepts.\n"
        f"- theme: choose EXACTLY ONE from this fixed list: {themes}. "
        f"If nothing fits, use '{_FALLBACK_THEME}'.\n"
        "Do not use any tools; the HTML is provided inline."
    )


async def _extract(
    url: str,
    html: str,
    company: str,
    allowed_themes: list[str],
    model: str,
) -> tuple[IngestResult, RateLimitSnapshot | None]:
    options = ClaudeAgentOptions(
        system_prompt=_system_prompt(company, allowed_themes),
        allowed_tools=[],           # no tools — the model only reads the provided HTML
        setting_sources=[],         # no CLAUDE.md / settings.json / .mcp.json
        permission_mode="bypassPermissions",
        max_turns=_MAX_TURNS,
        model=model,
        output_format={"type": "json_schema", "schema": PageRecord.model_json_schema()},
    )
    prompt = f"Extract this page.\nURL: {url}\n\nRAW HTML:\n{html}"

    result: ResultMessage | None = None
    snapshot: RateLimitSnapshot | None = None
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, RateLimitEvent):
                info = message.rate_limit_info
                snapshot = RateLimitSnapshot(
                    status=info.status,
                    utilization=info.utilization,
                    resets_at=info.resets_at,
                    rate_limit_type=info.rate_limit_type,
                )
            elif isinstance(message, ResultMessage):
                result = message
    except ClaudeSDKError as exc:
        # Connection/process/CLI errors, or the raise-after-error-result. If we already
        # captured a result message, fall through and map it; otherwise it's a fetch-side
        # (transport/auth) failure.
        if result is None:
            logger.warning("Agent SDK error ingesting %s: %s", url, exc)
            return IngestResult(url, "fetch_error", error=f"{type(exc).__name__}: {exc}"), snapshot

    # Defense in depth: a 429 result implies a limit rejection even if no event arrived.
    if result is not None and result.api_error_status == 429 and (
        snapshot is None or snapshot.status != "rejected"
    ):
        snapshot = RateLimitSnapshot(status="rejected")

    if result is None:
        return IngestResult(url, "fetch_error", error="no result message from agent"), snapshot
    if result.subtype != "success" or not result.structured_output:
        return IngestResult(
            url, "parse_error",
            error=f"subtype={result.subtype} errors={result.errors}",
        ), snapshot

    try:
        record = PageRecord.model_validate(result.structured_output)
    except ValidationError as exc:
        return IngestResult(url, "parse_error", error=f"schema validation: {exc}"), snapshot

    # Coerce out-of-taxonomy theme; force the known company (mirrors the API path).
    theme = record.theme if record.theme in allowed_themes else _FALLBACK_THEME
    if theme != record.theme:
        logger.info("coerced theme %r -> %r for %s", record.theme, theme, url)
    record = record.model_copy(update={"company": company, "theme": theme})
    return IngestResult(url, "ok", record=record), snapshot


def _fetch_and_extract(
    url: str,
    company: str,
    allowed_themes: list[str],
    model: str,
    max_content_tokens: int,
) -> tuple[IngestResult, RateLimitSnapshot | None]:
    try:
        html = _fetch_raw_html(url, max_content_tokens * _CHARS_PER_TOKEN)
    except httpx.HTTPError as exc:
        return IngestResult(url, "fetch_error", error=f"{type(exc).__name__}: {exc}"), None
    if not html.strip():
        return IngestResult(url, "fetch_error", error="empty page content"), None
    return asyncio.run(_extract(url, html, company, allowed_themes, model))


def fetch_enrich_cc_observed(
    url: str,
    company: str,
    allowed_themes: list[str],
    model: str,
    max_content_tokens: int,
) -> tuple[IngestResult, RateLimitSnapshot | None]:
    """Like fetch_enrich_cc but also returns the latest usage-window snapshot (runner)."""
    return _fetch_and_extract(url, company, allowed_themes, model, max_content_tokens)


def fetch_enrich_cc(
    url: str,
    company: str,
    allowed_themes: list[str],
    model: str,
    max_content_tokens: int,
) -> IngestResult:
    """Fetch + enrich one URL via the Claude Agent SDK. Never raises for one bad page."""
    result, _snapshot = _fetch_and_extract(url, company, allowed_themes, model, max_content_tokens)
    return result
