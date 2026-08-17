"""Tier 0: fetch a page's native Markdown twin. See PLAN.md §2a, §6.1.

Anthropic's docs serve `…/prompt-caching.md` alongside `…/prompt-caching`, returning
`text/markdown` with YAML frontmatter that already carries `title`, `url`, and
`description`. For those 566 pages there is **no HTML parsing at all** — which removes an
entire class of extractor bugs rather than making them cheaper to fix.

The tier is deliberately distrustful of its own premise. A `.md` twin is a convention, not
a guarantee, so anything that is not clearly Markdown escalates to tier 1 rather than
being archived as if it were:

* `404`/`410`/`415` — no twin exists here (`/cookbook/**` behaves this way);
* a `2xx` whose `Content-Type` is not Markdown — the endpoint answered, but not with what
  the tier exists to collect.

Redirects are followed and the destination recorded. `/docs/en/release-notes/api.md`
`307`s to `…/overview.md`, so two worklist URLs can legitimately resolve to one document;
`final_url` is what lets the corpus notice that later instead of storing it twice.
"""

from __future__ import annotations

import logging

from .http import FetchResult, HttpFetcher

logger = logging.getLogger(__name__)

MARKDOWN_SUFFIX = ".md"

# Content types accepted as "this really is the Markdown twin".
_MARKDOWN_TYPES = frozenset({"text/markdown", "text/x-markdown", "text/plain"})

# The twin is absent — not an error, just a page without one.
_ABSENT_STATUSES = frozenset({404, 410, 415})


def markdown_url_for(url: str) -> str:
    """`…/prompt-caching` → `…/prompt-caching.md`, leaving an existing suffix alone."""
    if url.endswith(MARKDOWN_SUFFIX):
        return url
    base, sep, query = url.partition("?")
    return f"{base.rstrip('/')}{MARKDOWN_SUFFIX}{sep}{query}"


def is_markdown(content_type: str | None) -> bool:
    return (content_type or "").split(";")[0].strip().lower() in _MARKDOWN_TYPES


class MarkdownEndpointFetcher:
    """Fetches `{url}.md`, falling back to the plain page when there is no twin."""

    tier = "markdown_endpoint"

    def __init__(self, http: HttpFetcher):
        self._http = http

    async def fetch(
        self,
        url: str,
        *,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> FetchResult:
        md_url = markdown_url_for(url)
        result = await self._http.fetch(md_url, etag=etag, last_modified=last_modified)
        result.tier = self.tier

        if result.state == "not_modified":
            return result

        if result.state == "ok" and is_markdown(result.content_type):
            return result

        # Everything below is an escalation: the twin is missing, or answered with
        # something this tier has no business archiving as Markdown.
        if result.state == "ok":
            reason = f"content-type {result.content_type!r}"
        elif result.status_code in _ABSENT_STATUSES:
            reason = f"HTTP {result.status_code}"
        else:
            # A timeout or 5xx is a transient failure of tier 0, not evidence that the
            # twin is absent. Report it as-is so the URL is retried next run rather than
            # permanently downgraded to HTML.
            return result

        logger.info("%s: no usable .md twin (%s) — falling back to the page itself", url, reason)
        fallback = await self._http.fetch(url)
        fallback.tier = f"{self.tier}->{self._http.tier}"
        return fallback
