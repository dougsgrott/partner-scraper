"""Per-host rate limiting. See PLAN.md §6.2.

This module exists to make it *hard* to be rude by accident. Three properties:

* **Limits are keyed on host, not source.** `anthropic-docs` and `anthropic-cookbook`
  are the same server; without this they would together hit it at twice the configured
  rate, and nothing in the config would say so.
* **Backing off is one-way within a run.** A `429` or `503` halves the host's rate for
  the remainder of the run and never restores it. A server that pushes back should not
  have to push back twice.
* **Jitter by default.** A perfectly periodic request stream is both easy to mistake for
  an attack and unnecessarily bursty at the far end.

The limiter is the binding constraint on run time — at 1 req/s the request timer, not
latency, sets the pace — so it is also the thing to reach for when a run must be gentler.
Lower the rate; never work around the limiter.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import random
from collections.abc import AsyncIterator
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class HostLimiter:
    """Token-bucket pacing plus a concurrency cap, for one host."""

    def __init__(
        self,
        host: str,
        *,
        requests_per_second: float,
        concurrency: int,
        jitter_s: float = 0.0,
    ):
        self.host = host
        self._interval = 1.0 / requests_per_second
        self._jitter = jitter_s
        self._sem = asyncio.Semaphore(concurrency)
        self._lock = asyncio.Lock()
        self._next_at = 0.0
        self.penalties = 0

    @property
    def requests_per_second(self) -> float:
        return 1.0 / self._interval

    async def _reserve(self) -> float:
        """Claim the next slot, returning how long the caller must wait for it."""
        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            start_at = max(now, self._next_at)
            self._next_at = start_at + self._interval + random.uniform(0, self._jitter)
            return start_at - now

    @contextlib.asynccontextmanager
    async def slot(self) -> AsyncIterator[None]:
        """Wait for this host's next permitted request slot."""
        await self._sem.acquire()
        try:
            # Reserve under the lock, sleep outside it, so waiting requests do not
            # serialise behind each other's sleeps.
            delay = await self._reserve()
            if delay > 0:
                await asyncio.sleep(delay)
            yield
        finally:
            self._sem.release()

    def penalise(self, reason: str) -> None:
        """Halve this host's rate for the rest of the run. Never reversed."""
        self._interval *= 2
        self.penalties += 1
        logger.warning(
            "%s pushed back (%s) — halving rate to %.2f req/s for the rest of this run",
            self.host,
            reason,
            self.requests_per_second,
        )


class Politeness:
    """A `HostLimiter` per host, created on demand."""

    def __init__(
        self,
        *,
        requests_per_second: float = 1.0,
        concurrency: int = 2,
        jitter_s: float = 0.3,
    ):
        self._rps = requests_per_second
        self._concurrency = concurrency
        self._jitter = jitter_s
        self._limiters: dict[str, HostLimiter] = {}

    @staticmethod
    def host_of(url: str) -> str:
        return urlparse(url).netloc.lower()

    def limiter(self, url: str) -> HostLimiter:
        host = self.host_of(url)
        limiter = self._limiters.get(host)
        if limiter is None:
            limiter = self._limiters[host] = HostLimiter(
                host,
                requests_per_second=self._rps,
                concurrency=self._concurrency,
                jitter_s=self._jitter,
            )
        return limiter

    def slot(self, url: str):
        return self.limiter(url).slot()

    def penalise(self, url: str, reason: str) -> None:
        self.limiter(url).penalise(reason)

    @property
    def hosts(self) -> dict[str, HostLimiter]:
        return dict(self._limiters)

    def report(self) -> dict[str, dict]:
        """Per-host end-of-run state — surfaces any host that pushed back."""
        return {
            host: {
                "requests_per_second": round(lim.requests_per_second, 3),
                "penalties": lim.penalties,
            }
            for host, lim in self._limiters.items()
        }
