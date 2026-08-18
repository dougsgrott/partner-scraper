"""Extraction: archived bytes → clean Markdown corpus. See PLAN.md §7, §12 step 5.

**Nothing in this package touches the network.** It reads `raw/`, writes `data/`, and
updates `state/index.db`. That is the whole point of the two-stage design: extraction can
be re-run as often as it takes to get right, and re-running it costs nothing but local CPU
(`--force` over 6,398 pages takes seconds).

Pages that fail extraction or the quality gate are recorded in the index with a reason and
*no corpus file*. Their raw bytes stay on disk, so fixing the extractor and re-running is
the entire remedy — there is never a reason to re-fetch to recover from a parsing bug.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from ..config import AppConfig
from ..fetch import rawstore
from ..fetch.db import FetchDB
from ..records import Extracted, RawPayload
from ..store import writer
from ..store.index import Index
from . import registry
from .base import QualityReport, check_quality

logger = logging.getLogger(__name__)

__all__ = [
    "ExtractSummary",
    "Extracted",
    "RawPayload",
    "check_quality",
    "extract_payload",
    "registry",
    "run_extract",
]


@dataclass
class ExtractSummary:
    """What an extraction pass did (PLAN.md §10)."""

    started_at: str
    sources: list[str] = field(default_factory=list)
    deferred_sources: dict[str, str] = field(default_factory=dict)
    candidates: int = 0
    skipped_unchanged: int = 0
    written: int = 0
    unchanged_files: int = 0
    moved: int = 0
    pruned: int = 0
    duplicates: int = 0
    quality_failed: int = 0
    errors: int = 0
    missing_raw: int = 0
    elapsed_s: float = 0.0
    categories: dict[str, int] = field(default_factory=dict)
    corpus_chars: int = 0
    largest: list[dict] = field(default_factory=list)
    issue_counts: dict[str, int] = field(default_factory=dict)
    samples: list[dict] = field(default_factory=list)

    @property
    def processed(self) -> int:
        return self.written + self.quality_failed + self.errors

    def to_dict(self) -> dict:
        return {**self.__dict__, "processed": self.processed}

    def render(self) -> str:
        lines = [
            f"extract {self.started_at}",
            f"  sources          {', '.join(self.sources) or '-'}",
            *[f"  deferred         {sid} ({why})" for sid, why in self.deferred_sources.items()],
            f"  candidates       {self.candidates}  (skipped {self.skipped_unchanged} unchanged)",
            f"  written          {self.written}"
            + (f"   ({self.unchanged_files} byte-identical)" if self.unchanged_files else "")
            + (f"   ({self.duplicates} duplicate URLs merged)" if self.duplicates else ""),
            *([f"  moved            {self.moved}  (stale copies removed)"] if self.moved else []),
            *([f"  pruned           {self.pruned}  (orphaned files removed)"] if self.pruned else []),
            f"  quality failed   {self.quality_failed}",
            f"  extract errors   {self.errors}",
            f"  missing raw      {self.missing_raw}",
            f"  elapsed          {self.elapsed_s:.1f}s",
        ]
        if self.issue_counts:
            lines.append("  issues:")
            for issue, n in sorted(self.issue_counts.items(), key=lambda kv: -kv[1])[:10]:
                lines.append(f"    {n:>5}  {issue}")
        if self.corpus_chars:
            lines.append(f"  written chars    {self.corpus_chars:,}")
        for page in self.largest[:3]:
            lines.append(f"    largest        {page['body_chars']:>9,}  {page['url']}")
        if self.categories:
            top = sorted(self.categories.items(), key=lambda kv: -kv[1])[:8]
            lines.append("  top categories:  " + ", ".join(f"{k} ({v})" for k, v in top))
        for sample in self.samples[:10]:
            lines.append(f"  ! {sample['url']}  {sample['reason']}")
        return "\n".join(lines)


def extract_payload(payload: RawPayload, extractor_name: str) -> tuple[Extracted, QualityReport]:
    """Run one extractor over one payload and score the result."""
    extractor = registry.get(extractor_name)
    if extractor is None:
        raise KeyError(f"no extractor named {extractor_name!r}")
    record = extractor(payload)
    return record, check_quality(record)


def run_extract(
    cfg: AppConfig,
    *,
    source_ids: list[str] | None = None,
    force: bool = False,
    only_failed: bool = False,
    limit: int | None = None,
    prune: bool = False,
    fetch_db_path: Path | None = None,
    index_db_path: Path | None = None,
    data_dir: Path | None = None,
) -> ExtractSummary:
    """Extract every archived page for the selected sources into the corpus."""
    import time

    summary = ExtractSummary(started_at=datetime.now(UTC).isoformat(timespec="seconds"))
    started = time.monotonic()

    selected = {
        sid: src
        for sid, src in (cfg.sources if source_ids is None else
                         {s: cfg.sources[s] for s in source_ids}).items()
        if source_ids is not None or src.enabled
    }

    runnable = {}
    for sid, src in selected.items():
        if src.extractor in registry.implemented():
            runnable[sid] = src
        else:
            summary.deferred_sources[sid] = f"extractor '{src.extractor}' not implemented yet"
    summary.sources = list(runnable)

    # Two sitemap URLs can name one document — `/ldp/best-practices` and
    # `/ldp/best-practices/` both exist, and a redirect can land two URLs on one page
    # (PLAN.md §2a). The archive keeps them apart on purpose; the corpus should not.
    written_paths: dict[str, str] = {}

    with FetchDB(fetch_db_path or "state/fetch.db") as fetch_db, \
            Index(index_db_path or "state/index.db") as index:

        for sid, src in runnable.items():
            version = registry.version(src.extractor)
            for url in fetch_db.urls(source_id=sid):
                row = fetch_db.get(url)
                if not row or not row["raw_path"] or row["state"] not in ("ok", "not_modified"):
                    continue

                summary.candidates += 1
                if limit is not None and summary.processed >= limit:
                    break

                if not force:
                    existing = index.get(url)
                    already_ok = existing is not None and existing["status"] == "ok"
                    stale = index.needs_extract(
                        url, raw_sha256=row["raw_sha256"], extractor_version=version
                    )
                    if already_ok if only_failed else not stale:
                        summary.skipped_unchanged += 1
                        continue

                raw_path = Path(row["raw_path"])
                if not raw_path.exists():
                    summary.missing_raw += 1
                    logger.warning("archive file missing for %s: %s", url, raw_path)
                    continue

                try:
                    payload = RawPayload(
                        url=url,
                        company=src.company,
                        source_id=sid,
                        content=rawstore.read(raw_path),
                        content_type=row["content_type"],
                        final_url=row["final_url"],
                        include_paths=list(src.include_paths),
                    )
                    record, quality = extract_payload(payload, src.extractor)
                except Exception as exc:                      # one bad page must not stop 6,000
                    summary.errors += 1
                    index.record_failure(url, src.company, source_id=sid,
                                         status="extract_error",
                                         error=f"{type(exc).__name__}: {exc}")
                    _sample(summary, url, f"{type(exc).__name__}: {exc}")
                    logger.exception("extract failed for %s", url)
                    continue

                if not quality.ok:
                    summary.quality_failed += 1
                    for issue in quality.issues:
                        key = issue.split("(")[0].strip()
                        summary.issue_counts[key] = summary.issue_counts.get(key, 0) + 1
                    index.record_failure(url, src.company, source_id=sid,
                                         status="quality_failed", error=str(quality))
                    _sample(summary, url, str(quality))
                    continue

                record = record.model_copy(update={"raw_sha256": row["raw_sha256"]})
                path = writer.path_for_record(record, data_dir)
                # In-run map catches duplicates in a full pass; the index catches them
                # across incremental runs, where the first URL was written long ago.
                previous = index.get(url)
                first_url = written_paths.get(str(path)) or index.owner_of(path)
                if first_url is not None and first_url != url:
                    summary.duplicates += 1
                    index.record_duplicate(url, src.company, file_path=path,
                                           duplicate_of=first_url, source_id=sid,
                                           extractor_version=version,
                                           raw_sha256=row["raw_sha256"])
                    # It may have owned a file of its own before it became a duplicate.
                    _drop_stale_copy(previous, path, url, index, data_dir, summary)
                    logger.info("%s duplicates %s — one corpus file kept", url, first_url)
                    continue
                written_paths[str(path)] = url

                result = writer.write(record, data_dir)
                index.upsert(
                    record,
                    result.path,
                    content_hash=writer.content_hash(record.markdown),
                    raw_sha256=row["raw_sha256"],
                    extracted_at=result.extracted_at,
                )
                _drop_stale_copy(previous, result.path, url, index, data_dir, summary)
                summary.written += 1
                summary.unchanged_files += 0 if result.changed else 1
                summary.corpus_chars += record.body_chars
                summary.categories[record.category] = summary.categories.get(record.category, 0) + 1

        summary.largest = index.largest()

        if prune:
            for orphan in index.orphans(data_dir or "data"):
                writer.remove(orphan, data_dir)
                summary.pruned += 1
                logger.info("pruned orphaned corpus file %s", orphan)

    summary.elapsed_s = time.monotonic() - started
    return summary


def _drop_stale_copy(previous: dict | None, path: Path, url: str, index: Index,
                     data_dir: Path | None, summary: ExtractSummary) -> None:
    """Remove the file this page used to occupy, if it moved.

    A page moves when its `updated_date` rolls into a new month bucket or a revised
    extractor puts it in another category. Without this the old copy stays in `data/`
    forever, unreferenced by the index and indistinguishable from a live page to anything
    that reads the corpus off disk.
    """
    if not previous or previous["status"] != "ok" or not previous["file_path"]:
        return
    stale = Path(previous["file_path"])
    if stale == path or not stale.exists():
        return
    # Only if nothing else has since claimed it — two URLs can trade paths within a run.
    if index.owner_of(stale) is not None:
        return
    writer.remove(stale, data_dir)
    summary.moved += 1
    logger.info("%s moved to %s — removed stale %s", url, path, stale)


def _sample(summary: ExtractSummary, url: str, reason: str) -> None:
    if len(summary.samples) < 25:
        summary.samples.append({"url": url, "reason": reason})
