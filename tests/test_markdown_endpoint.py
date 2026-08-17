"""Tier 0: the `.md` twin, and the cases where it must refuse to trust itself."""

from __future__ import annotations

import httpx
import pytest

from scraper.fetch.http import HttpFetcher
from scraper.fetch.markdown_endpoint import (
    MarkdownEndpointFetcher,
    is_markdown,
    markdown_url_for,
)

PAGE = "https://platform.claude.com/docs/en/build-with-claude/prompt-caching"
MD = PAGE + ".md"


def fetcher_over(handler, **kw):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)
    return MarkdownEndpointFetcher(HttpFetcher(client, backoff_max_s=0.01, **kw)), client


def markdown(body=b"# Title\n\ntext"):
    return httpx.Response(200, content=body, headers={"content-type": "text/markdown; charset=utf-8"})


# --- URL construction -----------------------------------------------------

def test_markdown_url_construction():
    assert markdown_url_for(PAGE) == MD
    assert markdown_url_for(PAGE + "/") == MD          # trailing slash dropped
    assert markdown_url_for(MD) == MD                  # already suffixed
    assert markdown_url_for("https://x.com/a?b=1") == "https://x.com/a.md?b=1"


def test_is_markdown():
    assert is_markdown("text/markdown; charset=utf-8")
    assert is_markdown("text/plain")
    assert not is_markdown("text/html; charset=utf-8")
    assert not is_markdown(None)


# --- the happy path -------------------------------------------------------

@pytest.mark.asyncio
async def test_fetches_the_md_twin():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return markdown()

    f, client = fetcher_over(handler)
    async with client:
        r = await f.fetch(PAGE)
    assert seen == [MD], "tier 0 must request the .md twin, not the page"
    assert r.ok
    assert r.tier == "markdown_endpoint"
    assert r.content == b"# Title\n\ntext"


@pytest.mark.asyncio
async def test_conditional_get_targets_the_md_url():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["inm"] = request.headers.get("if-none-match")
        return httpx.Response(304)

    f, client = fetcher_over(handler)
    async with client:
        r = await f.fetch(PAGE, etag='"v1"')
    assert seen["url"] == MD
    assert seen["inm"] == '"v1"'
    assert r.state == "not_modified"
    assert r.tier == "markdown_endpoint"


@pytest.mark.asyncio
async def test_redirect_to_another_md_page_is_followed_and_recorded():
    """`/release-notes/api.md` 307s to `…/overview.md` — two URLs, one document."""
    def handler(request):
        if request.url.path.endswith("api.md"):
            return httpx.Response(307, headers={"location": "/docs/en/release-notes/overview.md"})
        return markdown(b"# Overview")

    f, client = fetcher_over(handler)
    async with client:
        r = await f.fetch("https://platform.claude.com/docs/en/release-notes/api")
    assert r.ok
    assert r.final_url.endswith("/overview.md")
    assert r.content == b"# Overview"


# --- escalation -----------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_twin_falls_back_to_the_page():
    """`/cookbook/**` has no `.md` twin; the page itself is the right answer."""
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if str(request.url).endswith(".md"):
            return httpx.Response(404)
        return httpx.Response(200, content=b"<html>page</html>",
                              headers={"content-type": "text/html"})

    f, client = fetcher_over(handler)
    async with client:
        r = await f.fetch(PAGE)
    assert seen == [MD, PAGE]
    assert r.ok
    assert r.content == b"<html>page</html>"
    assert r.tier == "markdown_endpoint->http", "the escalation must be visible in the record"


@pytest.mark.asyncio
async def test_html_from_the_md_url_also_escalates():
    """A 200 that isn't Markdown means the twin isn't real — don't archive it as one."""
    def handler(request):
        if str(request.url).endswith(".md"):
            return httpx.Response(200, content=b"<html>not markdown</html>",
                                  headers={"content-type": "text/html"})
        return httpx.Response(200, content=b"<html>page</html>",
                              headers={"content-type": "text/html"})

    f, client = fetcher_over(handler)
    async with client:
        r = await f.fetch(PAGE)
    assert r.tier == "markdown_endpoint->http"
    assert r.content == b"<html>page</html>"


@pytest.mark.parametrize("status", [404, 410, 415])
@pytest.mark.asyncio
async def test_absence_statuses_escalate(status):
    def handler(request):
        if str(request.url).endswith(".md"):
            return httpx.Response(status)
        return markdown(b"ok")

    f, client = fetcher_over(handler, retries=0)
    async with client:
        r = await f.fetch(PAGE)
    assert r.ok
    assert r.tier == "markdown_endpoint->http"


@pytest.mark.asyncio
async def test_transient_failure_does_not_escalate():
    """A 500 on the .md URL is tier 0 failing, not evidence the twin is absent.

    Escalating here would permanently downgrade the page to HTML because of one bad
    minute on the server. Report the failure and let the next run retry.
    """
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(500)

    f, client = fetcher_over(handler, retries=0)
    async with client:
        r = await f.fetch(PAGE)
    assert r.state == "fetch_error"
    assert r.tier == "markdown_endpoint"
    assert calls == [MD], "must not fall back to the HTML page on a transient error"


@pytest.mark.asyncio
async def test_timeout_does_not_escalate():
    def handler(request):
        raise httpx.ConnectTimeout("slow")

    f, client = fetcher_over(handler, retries=0)
    async with client:
        r = await f.fetch(PAGE)
    assert r.state == "fetch_error"
    assert r.tier == "markdown_endpoint"
