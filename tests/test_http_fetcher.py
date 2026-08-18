"""Tier-1 fetcher: retry policy, validators, and backoff — driven by a mock transport."""

from __future__ import annotations

import httpx
import pytest

from scraper.fetch.http import HttpFetcher, _retry_after_seconds

URL = "https://x.com/page"


def fetcher_over(handler, **kw) -> tuple[HttpFetcher, httpx.AsyncClient]:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)
    return HttpFetcher(client, backoff_max_s=0.01, **kw), client


@pytest.mark.asyncio
async def test_success_captures_body_and_validators():
    def handler(request):
        return httpx.Response(
            200, content=b"<html>hi</html>",
            headers={"content-type": "text/html", "etag": '"v1"',
                     "last-modified": "Fri, 14 Aug 2026 21:30:20 GMT"},
        )

    f, client = fetcher_over(handler)
    async with client:
        r = await f.fetch(URL)
    assert r.ok and r.state == "ok"
    assert r.content == b"<html>hi</html>"
    assert r.etag == '"v1"'
    assert r.last_modified == "Fri, 14 Aug 2026 21:30:20 GMT"
    assert r.attempts == 1


@pytest.mark.asyncio
async def test_conditional_headers_are_sent():
    seen = {}

    def handler(request):
        seen.update(request.headers)
        return httpx.Response(304)

    f, client = fetcher_over(handler)
    async with client:
        r = await f.fetch(URL, etag='"v1"', last_modified="Fri, 14 Aug 2026 21:30:20 GMT")
    assert seen["if-none-match"] == '"v1"'
    assert seen["if-modified-since"] == "Fri, 14 Aug 2026 21:30:20 GMT"
    assert r.state == "not_modified"
    assert r.content is None


@pytest.mark.asyncio
async def test_304_keeps_prior_validators_when_server_omits_them():
    f, client = fetcher_over(lambda req: httpx.Response(304))
    async with client:
        r = await f.fetch(URL, etag='"v1"')
    assert r.etag == '"v1"'


@pytest.mark.asyncio
async def test_404_is_terminal_and_not_retried():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(404)

    f, client = fetcher_over(handler, retries=3)
    async with client:
        r = await f.fetch(URL)
    assert r.state == "fetch_error"
    assert r.status_code == 404
    assert len(calls) == 1, "retrying a 404 is just noise"


@pytest.mark.asyncio
async def test_500_is_retried_then_gives_up():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(500)

    f, client = fetcher_over(handler, retries=2)
    async with client:
        r = await f.fetch(URL)
    assert len(calls) == 3          # first try + 2 retries
    assert r.state == "fetch_error"
    assert r.attempts == 3


@pytest.mark.asyncio
async def test_transient_failure_then_success():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(503)
        return httpx.Response(200, content=b"ok", headers={"content-type": "text/html"})

    f, client = fetcher_over(handler, retries=2)
    async with client:
        r = await f.fetch(URL)
    assert r.ok
    assert r.content == b"ok"
    assert r.attempts == 2
    assert r.error is None, "a recovered request must not report an error"


@pytest.mark.asyncio
async def test_429_and_503_flag_a_penalty():
    for status in (429, 503):
        f, client = fetcher_over(lambda req, s=status: httpx.Response(s), retries=0)
        async with client:
            r = await f.fetch(URL)
        assert r.penalised, f"{status} should slow the host down"


@pytest.mark.asyncio
async def test_404_does_not_flag_a_penalty():
    f, client = fetcher_over(lambda req: httpx.Response(404), retries=0)
    async with client:
        r = await f.fetch(URL)
    assert not r.penalised


@pytest.mark.asyncio
async def test_network_error_is_retried():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) < 3:
            raise httpx.ConnectError("boom")
        return httpx.Response(200, content=b"ok")

    f, client = fetcher_over(handler, retries=3)
    async with client:
        r = await f.fetch(URL)
    assert r.ok
    assert r.attempts == 3


@pytest.mark.asyncio
async def test_network_error_exhausted_reports_the_cause():
    f, client = fetcher_over(lambda req: (_ for _ in ()).throw(httpx.ConnectError("boom")), retries=1)
    async with client:
        r = await f.fetch(URL)
    assert r.state == "fetch_error"
    assert "ConnectError" in r.error


@pytest.mark.asyncio
async def test_redirect_records_the_final_url():
    def handler(request):
        if request.url.path == "/page":
            return httpx.Response(307, headers={"location": "https://x.com/final"})
        return httpx.Response(200, content=b"ok", headers={"content-type": "text/markdown"})

    f, client = fetcher_over(handler)
    async with client:
        r = await f.fetch(URL)
    assert r.ok
    assert r.final_url == "https://x.com/final"


def test_retry_after_parsing():
    assert _retry_after_seconds("5") == 5.0
    assert _retry_after_seconds(None) is None
    assert _retry_after_seconds("garbage") is None
    assert _retry_after_seconds("-3") == 0.0            # never negative
    # HTTP-date form resolves to a non-negative delta
    assert _retry_after_seconds("Wed, 21 Oct 2015 07:28:00 GMT") == 0.0


@pytest.mark.asyncio
async def test_server_retry_after_is_honoured_over_backoff(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(delay):
        slept.append(delay)

    monkeypatch.setattr("scraper.fetch.http.asyncio.sleep", fake_sleep)

    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429, headers={"retry-after": "7"})
        return httpx.Response(200, content=b"ok")

    f, client = fetcher_over(handler, retries=2)
    f._backoff_max = 60
    async with client:
        r = await f.fetch(URL)
    assert r.ok
    assert slept == [7.0], "the server's own delay must win over our backoff"
