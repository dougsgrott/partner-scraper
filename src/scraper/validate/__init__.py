"""Validation: is the corpus complete, faithful, and useful? See docs/validation-plan.md.

Separate from the quality gate in `extract.base`, which judges one page as it is written.
This package judges the *whole corpus* after the fact, and it exists because every defect
this project has had passed the per-page gate (docs/lessons-learned.md §1).

Nothing here writes to `data/`, `raw/`, or the databases — validation observes.
"""

from __future__ import annotations

import time
from pathlib import Path

from ..config import AppConfig
from . import coverage, integrity, invariants
from .report import Check, Report

__all__ = ["Check", "Report", "coverage", "integrity", "invariants", "run_validation"]


def run_validation(
    cfg: AppConfig,
    *,
    data_dir: str | Path = "data",
    fetch_db_path: str | Path = "state/fetch.db",
    index_db_path: str | Path = "state/index.db",
    worklists=None,
    idempotency: bool = True,
) -> tuple[Report, list]:
    """Run every offline check. Returns the report and the link-gap candidate list."""
    started = time.monotonic()
    report = Report()

    report.add("integrity", *integrity.run(cfg, data_dir=data_dir, fetch_db_path=fetch_db_path,
                                           index_db_path=index_db_path, idempotency=idempotency))
    report.add("invariants", *invariants.run(data_dir, cfg))

    closure, candidates = coverage.check_link_closure(cfg, data_dir=data_dir,
                                                      fetch_db_path=fetch_db_path)
    checks = [coverage.check_corpus_completeness(cfg, data_dir=data_dir,
                                                 fetch_db_path=fetch_db_path,
                                                 index_db_path=index_db_path)]
    if worklists is not None:
        checks.extend(coverage.check_scope_reconciliation(cfg, worklists,
                                                          fetch_db_path=fetch_db_path))
    report.add("coverage", *checks, closure)

    report.elapsed_s = time.monotonic() - started
    return report, candidates
