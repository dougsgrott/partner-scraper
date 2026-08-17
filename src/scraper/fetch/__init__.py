"""Acquisition: fetch pages and archive the bytes verbatim. See PLAN.md §6.

Landed so far (step 2): the raw archive (`rawstore`) and its bookkeeping (`db`).
Still to come: the tier-0/1/2 fetchers, per-host politeness, and retries (step 3+).

The invariant this package exists to protect: **the fetcher never parses.** It records
bytes, status, headers, and the final URL — nothing that requires understanding the page.
"""

from __future__ import annotations

from . import rawstore
from .db import STATES, FetchDB

__all__ = ["STATES", "FetchDB", "rawstore"]
