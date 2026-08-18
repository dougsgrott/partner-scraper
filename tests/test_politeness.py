"""Rate limiting: the code that makes it hard to be rude by accident."""

from __future__ import annotations

import asyncio
import time

import pytest

from scraper.fetch.politeness import HostLimiter, Politeness


async def _drain(limiter: HostLimiter, n: int) -> float:
    start = time.monotonic()
    await asyncio.gather(*( _one(limiter) for _ in range(n) ))
    return time.monotonic() - start


async def _one(limiter: HostLimiter) -> None:
    async with limiter.slot():
        pass


@pytest.mark.asyncio
async def test_requests_are_paced():
    """5 requests at 20/s must take at least the 4 intervals between them."""
    limiter = HostLimiter("h", requests_per_second=20, concurrency=2, jitter_s=0)
    elapsed = await _drain(limiter, 5)
    assert elapsed >= 4 * 0.05 * 0.9        # allow a little scheduler slack


@pytest.mark.asyncio
async def test_concurrency_is_capped():
    """Never more than `concurrency` requests in flight at once."""
    limiter = HostLimiter("h", requests_per_second=1000, concurrency=2, jitter_s=0)
    in_flight = 0
    peak = 0

    async def work():
        nonlocal in_flight, peak
        async with limiter.slot():
            in_flight += 1
            peak = max(peak, in_flight)
            await asyncio.sleep(0.01)
            in_flight -= 1

    await asyncio.gather(*(work() for _ in range(10)))
    assert peak <= 2


@pytest.mark.asyncio
async def test_pacing_does_not_serialise_behind_sleeps():
    """Slots are reserved under the lock but waited on outside it.

    If the sleep happened while holding the lock, N concurrent callers would each wait
    for every earlier caller's sleep, and total time would grow quadratically.
    """
    limiter = HostLimiter("h", requests_per_second=50, concurrency=4, jitter_s=0)
    elapsed = await _drain(limiter, 8)
    assert elapsed < 8 * 0.02 * 2           # linear in the interval, not quadratic


def test_penalty_halves_the_rate():
    limiter = HostLimiter("h", requests_per_second=1.0, concurrency=1)
    assert limiter.requests_per_second == pytest.approx(1.0)
    limiter.penalise("HTTP 429")
    assert limiter.requests_per_second == pytest.approx(0.5)
    limiter.penalise("HTTP 503")
    assert limiter.requests_per_second == pytest.approx(0.25)
    assert limiter.penalties == 2


def test_penalty_is_never_restored():
    """A server that pushes back should not have to push back twice."""
    limiter = HostLimiter("h", requests_per_second=1.0, concurrency=1)
    limiter.penalise("HTTP 429")
    rate = limiter.requests_per_second
    assert not hasattr(limiter, "restore")
    assert limiter.requests_per_second == rate


def test_limits_are_keyed_on_host_not_source():
    """Two sources on one host must share a limiter, or they double the real load."""
    pol = Politeness(requests_per_second=1)
    docs = pol.limiter("https://platform.claude.com/docs/en/x")
    cookbook = pol.limiter("https://platform.claude.com/cookbook/y")
    other = pol.limiter("https://docs.databricks.com/aws/en/z")

    assert docs is cookbook
    assert docs is not other
    assert set(pol.hosts) == {"platform.claude.com", "docs.databricks.com"}


def test_penalty_applies_to_the_whole_host():
    pol = Politeness(requests_per_second=1)
    pol.penalise("https://platform.claude.com/docs/en/x", "HTTP 429")
    assert pol.limiter("https://platform.claude.com/cookbook/y").requests_per_second == 0.5


def test_host_matching_ignores_case():
    pol = Politeness()
    assert pol.limiter("https://Example.COM/a") is pol.limiter("https://example.com/b")


def test_report_surfaces_penalised_hosts():
    pol = Politeness(requests_per_second=2)
    pol.limiter("https://a.com/x")
    pol.penalise("https://b.com/y", "HTTP 503")
    report = pol.report()
    assert report["a.com"]["penalties"] == 0
    assert report["b.com"]["penalties"] == 1
    assert report["b.com"]["requests_per_second"] == 1.0
