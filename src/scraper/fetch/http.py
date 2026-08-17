"""Tier 1: the plain HTTP fetcher. See PLAN.md §6.1.

Fetches one page and reports what happened. It does **not** parse, store, or decide what
to do next — that is the runner's job. Keeping this boundary means the awkward parts
(retry policy, validators, backoff) live in one place and are testable without a disk or
a database.

Retry policy:
  * transient — timeouts, connection errors, 408, 429, 5xx → retry with exponential
    backoff and jitter, honouring `Retry-After` when the server sends one;
  * terminal — every other 4xx → give up immediately, since retrying a 404 is just noise;
  * 429/503 additionally **penalise the host** for the rest of the run (PLAN.md §6.2).
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime

import httpx

logger = logging.getLogger(__name__)

# Retried. Everything else in 4xx is treated as a permanent answer.
_RETRY_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504, 507, 509})
# Ask the host to slow down for the rest of the run.
_PENALTY_STATUSES = frozenset({429, 503})


@dataclass
class FetchResult:
    """What one fetch attempt produced."""

    url: str
    state: str                        # ok | not_modified | fetch_error
    tier: str = "http"                # which tier produced this (may record an escalation)
    status_code: int | None = None
    content: bytes | None = None
    final_url: str | None = None
    content_type: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    error: str | None = None
    attempts: int = 0
    elapsed_s: float = 0.0
    penalised: bool = False
    retry_history: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.state == "ok"


def _retry_after_seconds(value: str | None) -> float | None:
    """Parse `Retry-After`, which is either a delta in seconds or an HTTP date."""
    if not value:
        return None
    value = value.strip()
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    from datetime import UTC, datetime

    delta = (when - datetime.now(UTC)).total_seconds()
    return max(0.0, delta)


class HttpFetcher:
    """Tier-1 fetcher over a shared `httpx.AsyncClient`."""

    tier = "http"

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        retries: int = 3,
        backoff_max_s: float = 120.0,
    ):
        self._client = client
        self._retries = retries
        self._backoff_max = backoff_max_s

    def _backoff(self, attempt: int, retry_after: float | None) -> float:
        """Exponential backoff with jitter; a server-supplied delay always wins."""
        if retry_after is not None:
            return min(retry_after, self._backoff_max)
        base = min(2.0 ** (attempt - 1), self._backoff_max)
        return base * (0.5 + random.random() / 2)      # 50–100% of base

    async def fetch(
        self,
        url: str,
        *,
        etag: str | None = None,
        last_modified: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> FetchResult:
        """Fetch one URL, revalidating with the given validators when present."""
        headers: dict[str, str] = dict(extra_headers or {})
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        result = FetchResult(url=url, state="fetch_error")
        loop = asyncio.get_running_loop()
        started = loop.time()

        for attempt in range(1, self._retries + 2):     # first try + N retries
            result.attempts = attempt
            try:
                resp = await self._client.get(url, headers=headers)
            except httpx.HTTPError as exc:
                detail = f"{type(exc).__name__}: {exc}"
                result.error = detail
                result.retry_history.append(detail)
                if attempt > self._retries:
                    break
                await asyncio.sleep(self._backoff(attempt, None))
                continue

            result.status_code = resp.status_code
            result.final_url = str(resp.url)

            if resp.status_code in _PENALTY_STATUSES:
                result.penalised = True

            if resp.status_code == 304:
                result.state = "not_modified"
                result.etag = resp.headers.get("etag") or etag
                result.last_modified = resp.headers.get("last-modified") or last_modified
                break

            if resp.is_success:
                result.state = "ok"
                result.content = resp.content
                result.content_type = resp.headers.get("content-type")
                result.etag = resp.headers.get("etag")
                result.last_modified = resp.headers.get("last-modified")
                result.error = None
                break

            detail = f"HTTP {resp.status_code}"
            result.error = detail

            if resp.status_code not in _RETRY_STATUSES or attempt > self._retries:
                break

            result.retry_history.append(detail)
            delay = self._backoff(attempt, _retry_after_seconds(resp.headers.get("retry-after")))
            logger.info("%s -> %s; retrying in %.1fs (attempt %d)", url, detail, delay, attempt)
            await asyncio.sleep(delay)

        result.elapsed_s = loop.time() - started
        return result
