"""The version store: page bodies on disk, gzipped, addressed by content hash.

This is what gives the corpus a past tense. `data/` holds one version of each page —
the current one — and a refresh overwrites it, so without this store a diff has nothing
on the left-hand side.

**The address is the corpus's own `content_hash`.** `writer.content_hash` is
`sha256(markdown.strip())` and `writer.render` writes exactly `markdown.strip()`, so a
body read back off disk hashes to the value already sitting in its own frontmatter. That
buys three things for free:

* deduplication — a page that did not change between snapshots stores no new bytes, which
  is the whole reason a weekly history is affordable;
* verification — any stored blob can be checked against the file it came from, with no
  second hashing scheme to keep in step;
* identity — two snapshots agree a page is unchanged precisely when they name the same
  blob, so the diff's cheapest question is answered by a string comparison.

The write rules are lifted from `scraper.fetch.rawstore` deliberately, and for the same
reasons: gzip with `mtime=0` so identical content produces identical files, atomic
`os.replace` so an interrupted run leaves no truncated blob, and a hard guard on the
address so an untrusted string can never escape the store.
"""

from __future__ import annotations

import gzip
import os
import re
from pathlib import Path

DEFAULT_BLOB_DIR = Path("state/changes/blobs")

# sha256, lowercase hex. Anything else is a bug or an attack, and either way must not be
# turned into a filesystem path.
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

# Two hex characters — 256 buckets — keeps directory sizes sane at corpus scale without
# nesting deeply enough to be annoying to browse.
_FANOUT = 2


def _validate(sha: str) -> str:
    if not _SHA256.match(sha):
        raise ValueError(f"not a sha256 content hash: {sha!r}")
    return sha


def path_for(sha: str, base_dir: Path | None = None) -> Path:
    """Where the body with this content hash lives."""
    sha = _validate(sha)
    return Path(base_dir or DEFAULT_BLOB_DIR) / sha[:_FANOUT] / f"{sha}.gz"


def exists(sha: str, base_dir: Path | None = None) -> bool:
    return path_for(sha, base_dir).exists()


def write(sha: str, text: str, base_dir: Path | None = None) -> bool:
    """Store a body under its content hash. Returns True if it was newly written.

    A hash already present is left alone rather than rewritten: the content is identical
    by definition, and skipping the write is what makes the second snapshot of an
    unchanged corpus cost nothing.
    """
    path = path_for(sha, base_dir)
    if path.exists():
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "wb") as fh, gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
            gz.write(text.encode("utf-8"))
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return True


def read(sha: str, base_dir: Path | None = None) -> str:
    """Read a stored body back. Raises `FileNotFoundError` if it was never stored."""
    with gzip.open(path_for(sha, base_dir), "rb") as fh:
        return fh.read().decode("utf-8")


def read_or_none(sha: str | None, base_dir: Path | None = None) -> str | None:
    """`read`, but tolerant — a missing or malformed hash yields None instead of raising.

    The diff asks for bodies that a `gc` may have collected or an older snapshot may
    predate. A missing left-hand side degrades the report; it should not end the run.
    """
    if not sha:
        return None
    try:
        return read(sha, base_dir)
    except (FileNotFoundError, OSError, ValueError):
        return None


def prune(keep: set[str], base_dir: Path | None = None) -> tuple[int, int]:
    """Delete blobs no snapshot references. Returns `(files removed, bytes reclaimed)`.

    `keep` must be every hash still named by `page_versions`; passing an incomplete set
    silently destroys history, so the caller computes it in one query rather than
    incrementally.
    """
    base = Path(base_dir or DEFAULT_BLOB_DIR)
    removed = reclaimed = 0
    if not base.exists():
        return (0, 0)

    for path in base.rglob("*.gz"):
        if path.stem in keep:
            continue
        reclaimed += path.stat().st_size
        path.unlink()
        removed += 1

    for bucket in sorted(base.iterdir()):
        if bucket.is_dir() and not any(bucket.iterdir()):
            bucket.rmdir()
    return (removed, reclaimed)


def total_bytes(base_dir: Path | None = None) -> int:
    base = Path(base_dir or DEFAULT_BLOB_DIR)
    return sum(p.stat().st_size for p in base.rglob("*.gz")) if base.exists() else 0
