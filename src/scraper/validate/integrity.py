"""Is the store self-consistent? See docs/validation-plan.md §1.

`data/` and `state/index.db` are two views of the same thing, and `raw/` is the source
both derive from. These checks assert the three agree — that nothing was written the
index does not know about, nothing is claimed that is not there, and the corpus is
reproducible from the archive rather than merely present.
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from ..fetch import rawstore
from ..store import writer
from ..store.index import FILE_OWNING_STATUSES, Index
from .report import Check, failed, passed, warned


def check_index_matches_disk(index: Index, data_dir: str | Path = "data") -> list[Check]:
    owned = index.file_paths()
    on_disk = {str(p) for p in Path(data_dir).rglob("*.md")}
    orphans = index.orphans(data_dir)
    missing = sorted(owned - {str(Path(p)) for p in on_disk})

    checks = [
        passed("index_orphans", f"every one of {len(on_disk)} files is claimed by the index",
               total=len(on_disk))
        if not orphans else
        failed("index_orphans", f"{len(orphans)} file(s) no index row claims",
               count=len(orphans), total=len(on_disk), samples=[str(p) for p in orphans]),

        passed("index_files_exist", f"all {len(owned)} indexed files are on disk", total=len(owned))
        if not missing else
        failed("index_files_exist", f"{len(missing)} indexed file(s) are absent",
               count=len(missing), total=len(owned), samples=missing),
    ]
    return checks


def check_content_hashes(index: Index, data_dir: str | Path = "data") -> Check:
    """The recorded hash must match the body actually on disk."""
    mismatched, checked = [], 0
    for row in index.query(status="ok"):
        path = Path(row["file_path"])
        if not path.exists():
            continue
        checked += 1
        front, body = writer.parse(path)
        if writer.content_hash(body.strip()) != front.get("content_hash"):
            mismatched.append(str(path))
    if mismatched:
        return failed("content_hash_matches_body", f"{len(mismatched)} file(s) disagree",
                      count=len(mismatched), total=checked, samples=mismatched)
    return passed("content_hash_matches_body", f"{checked} files hash to their frontmatter",
                  total=checked)


def check_archive_backs_corpus(index: Index, fetch_db_path: str | Path = "state/fetch.db") -> Check:
    """Every corpus page must trace back to an archived response still on disk."""
    conn = sqlite3.connect(fetch_db_path)
    conn.row_factory = sqlite3.Row
    archived = {r["url"]: r["raw_path"] for r in
                conn.execute("SELECT url, raw_path FROM fetches WHERE raw_path IS NOT NULL")}
    conn.close()

    unbacked, gone, rows = [], [], index.query(status="ok")
    for row in rows:
        raw_path = archived.get(row["url"])
        if raw_path is None:
            unbacked.append(row["url"])
        elif not Path(raw_path).exists():
            gone.append(raw_path)

    if unbacked or gone:
        return failed("archive_backs_corpus",
                      f"{len(unbacked)} page(s) with no archive row, {len(gone)} with a missing file",
                      count=len(unbacked) + len(gone), total=len(rows),
                      samples=[*unbacked[:3], *gone[:2]])
    return passed("archive_backs_corpus", f"all {len(rows)} pages trace to archived bytes",
                  total=len(rows))


def check_archive_readable(fetch_db_path: str | Path = "state/fetch.db",
                           sample: int = 25) -> Check:
    """Spot-check that archived files still decompress — silent bit-rot would be invisible."""
    import random

    conn = sqlite3.connect(fetch_db_path)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        "SELECT url, raw_path, raw_sha256 FROM fetches WHERE raw_path IS NOT NULL")]
    conn.close()
    if not rows:
        return failed("archive_readable", "no archived responses recorded")

    picked = random.Random(0).sample(rows, min(sample, len(rows)))
    bad = []
    for row in picked:
        try:
            content = rawstore.read(row["raw_path"])
        except OSError as exc:
            bad.append(f"{row['url']}: {type(exc).__name__}")
            continue
        if row["raw_sha256"] and rawstore.sha256(content) != row["raw_sha256"]:
            bad.append(f"{row['url']}: sha256 mismatch")
    if bad:
        return failed("archive_readable", f"{len(bad)} of {len(picked)} sampled files are bad",
                      count=len(bad), total=len(picked), samples=bad)
    return passed("archive_readable", f"{len(picked)} sampled archives decompress and match",
                  total=len(picked))


def check_rebuildable(index: Index, data_dir: str | Path = "data") -> Check:
    """`index.db` must be reproducible from `data/` — it is the cheap half of the pair.

    "Reproducible" means the rows a rebuild *can* derive. Three kinds of state live only in
    the index because the frontmatter deliberately does not carry them, and each comes back
    on the next extract pass, which rewrites no files:

    * `raw_sha256` — provenance, kept out of the frontmatter so a vendor rebuild that
      changes bytes without changing content does not diff every file (PLAN.md §8);
    * `output_fingerprint` and `body_fingerprint` — pipeline identity, meaningless in a file;
    * `status` — a page marked `gone` (404 upstream) keeps its last-known file on disk, so a
      rebuild from `data/` alone sees an ordinary page and marks it `ok`.

    That last one is why `live` spans the file-owning statuses rather than just `ok`: the
    file exists, the rebuild will find it, and counting only `ok` rows made this check fail
    the moment upstream deletions became visible.
    """
    live = {row["url"]: row
            for status in FILE_OWNING_STATUSES
            for row in index.query(status=status)}
    volatile = {"raw_sha256", "output_fingerprint", "body_fingerprint", "body_chars",
                "status", "error", "extracted_at"}

    with tempfile.TemporaryDirectory() as tmp, Index(Path(tmp) / "rebuilt.db") as rebuilt:
        count = rebuilt.rebuild(data_dir)
        copy = {row["url"]: row for row in rebuilt.query(status="ok")}

    if count != len(live):
        return failed("index_rebuildable", f"rebuild produced {count} rows, index has {len(live)}",
                      count=abs(count - len(live)), total=len(live))
    differing = [url for url, row in live.items()
                 if {k: v for k, v in row.items() if k not in volatile}
                 != {k: v for k, v in copy.get(url, {}).items() if k not in volatile}]
    if differing:
        return failed("index_rebuildable", f"{len(differing)} row(s) differ after rebuild",
                      count=len(differing), total=len(live), samples=differing)
    return passed("index_rebuildable", f"{count} rows reproduced from data/ alone", total=count)


def check_idempotent(cfg, *, data_dir: str | Path = "data",
                     fetch_db_path: str | Path = "state/fetch.db",
                     index_db_path: str | Path = "state/index.db") -> Check:
    """A second extraction pass must write nothing. Re-runs are how extractors get fixed."""
    from ..extract import run_extract

    summary = run_extract(cfg, fetch_db_path=Path(fetch_db_path),
                          index_db_path=Path(index_db_path), data_dir=Path(data_dir))
    if summary.written or summary.moved or summary.pruned:
        return failed("extraction_idempotent",
                      f"a repeat pass wrote {summary.written}, moved {summary.moved}, "
                      f"pruned {summary.pruned}",
                      count=summary.written, total=summary.candidates)
    if summary.errors:
        return failed("extraction_idempotent", f"{summary.errors} extraction error(s)",
                      count=summary.errors, total=summary.candidates)
    return passed("extraction_idempotent",
                  f"{summary.skipped_unchanged} pages already current, nothing written",
                  total=summary.candidates)


def check_statuses(index: Index) -> Check:
    counts = index.counts()
    broken = counts.get("extract_error", 0) + counts.get("quality_failed", 0)
    summary = ", ".join(f"{k} {v}" for k, v in counts.items() if v)
    if broken:
        return warned("index_statuses", summary, count=broken, detail=counts)
    return passed("index_statuses", summary, detail=counts)


def run(cfg, *, data_dir: str | Path = "data", fetch_db_path: str | Path = "state/fetch.db",
        index_db_path: str | Path = "state/index.db", idempotency: bool = True) -> list[Check]:
    with Index(index_db_path) as index:
        checks = [
            *check_index_matches_disk(index, data_dir),
            check_statuses(index),
            check_content_hashes(index, data_dir),
            check_archive_backs_corpus(index, fetch_db_path),
            check_archive_readable(fetch_db_path),
            check_rebuildable(index, data_dir),
        ]
    if idempotency:
        checks.append(check_idempotent(cfg, data_dir=data_dir, fetch_db_path=fetch_db_path,
                                       index_db_path=index_db_path))
    return checks
