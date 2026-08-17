"""Acquisition: fetch pages and archive the bytes verbatim. See PLAN.md §6.

Landed so far: the raw archive (`rawstore`), its bookkeeping (`db`), per-host rate
limiting (`politeness`), the tier-0 Markdown fetcher (`markdown_endpoint`), the tier-1
HTTP fetcher (`http`), and the run driver (`runner`). Still to come: tier 2 (browser,
step 10).

The invariant this package exists to protect: **the fetcher never parses.** It records
bytes, status, headers, and the final URL — nothing that requires understanding the page.
"""

from __future__ import annotations

from . import rawstore
from .db import STATES, FetchDB
from .http import FetchResult, HttpFetcher
from .markdown_endpoint import MarkdownEndpointFetcher
from .politeness import HostLimiter, Politeness
from .runner import FetchRunner, Job, RunSummary, run_fetch, select_jobs

__all__ = [
    "STATES",
    "FetchDB",
    "FetchResult",
    "FetchRunner",
    "HostLimiter",
    "HttpFetcher",
    "Job",
    "MarkdownEndpointFetcher",
    "Politeness",
    "RunSummary",
    "rawstore",
    "run_fetch",
    "select_jobs",
]
