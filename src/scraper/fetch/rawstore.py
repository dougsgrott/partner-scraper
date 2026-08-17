"""The raw archive: verbatim page bytes on disk, gzipped. See PLAN.md §1, §4, §6.3.

This is the layer the whole design rests on. Fetching is slow and rate-limited; parsing
is fast and will be wrong the first few times. As long as the exact bytes we received are
on disk, every extractor fix is a local re-run instead of another crawl.

So the rules here are narrow and strict:

* **Store what arrived, unaltered.** No normalisation, no re-encoding, no pretty-printing.
  The only transformation is gzip, which is lossless.
* **Mirror the URL path**, so the archive can be browsed, diffed, and grepped with
  ordinary tools rather than only through this module.
* **Never write outside the archive root.** URLs are untrusted input; a `..` segment must
  not be able to reach the filesystem.
* **Writes are atomic.** A crawl interrupted at 90 minutes must not leave a truncated
  file that later parses as a valid-but-empty page.

Path shape::

    https://docs.databricks.com/aws/en/delta/
      -> raw/databricks/docs.databricks.com/aws/en/delta/index.html.gz

    https://platform.claude.com/docs/en/build-with-claude/prompt-caching
      -> raw/anthropic/platform.claude.com/docs/en/build-with-claude/prompt-caching.md.gz

A trailing slash becomes ``index.<ext>.gz``, so ``/a/b`` and ``/a/b/`` — which are
different pages on some sites — never fight over one file. Sanitising is lossy by
necessity, so `fetch.db` keeps the authoritative URL→path mapping and
:func:`claimed_by` detects any two URLs that would land on the same file.
"""

from __future__ import annotations

import gzip
import hashlib
import logging
import os
import re
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DEFAULT_RAW_DIR = Path("raw")

_INDEX_STEM = "index"
_MAX_SEGMENT = 100          # bytes; well under every filesystem's 255 limit
_HASH_LEN = 8

# Anything outside this set is replaced. Deliberately conservative: doc-site slugs are
# ASCII, and a predictable mapping matters more than a pretty one.
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]")

# Reserved on Windows even without an extension. We are on Linux, but archives get
# copied, synced, and zipped, and a file named `con.html.gz` breaks all three.
_RESERVED = {
    "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:_HASH_LEN]


def _safe_segment(segment: str) -> str:
    """Make one path segment safe, stable, and non-empty.

    Long segments are truncated with a hash suffix so two different long URLs cannot
    collapse into the same name just because they share a prefix.
    """
    cleaned = _UNSAFE.sub("_", segment)
    cleaned = cleaned.lstrip(".")                 # no hidden files, no "." / ".."
    if not cleaned:
        cleaned = f"_{_short_hash(segment)}"
    if cleaned.split(".")[0].lower() in _RESERVED:
        cleaned = f"_{cleaned}"
    if len(cleaned.encode("utf-8")) > _MAX_SEGMENT:
        keep = cleaned[: _MAX_SEGMENT - _HASH_LEN - 1]
        cleaned = f"{keep}-{_short_hash(segment)}"
    return cleaned


def relative_path_for(url: str, company: str, *, ext: str = "html") -> Path:
    """Archive path for a URL, relative to the raw root.

    `ext` is the *content* extension (``html``/``md``); ``.gz`` is appended here so the
    stored name always states both what it is and how it is compressed.
    """
    parsed = urlparse(url)
    host = _safe_segment(parsed.netloc) if parsed.netloc else "_nohost"

    raw_segments = [s for s in parsed.path.split("/") if s]
    segments = [_safe_segment(s) for s in raw_segments]

    trailing_slash = parsed.path.endswith("/") or not raw_segments
    if trailing_slash:
        stem = _INDEX_STEM
    else:
        stem = segments.pop()

    # Query strings do not appear in doc-site sitemaps, but if one ever does it must not
    # silently overwrite the query-less page.
    if parsed.query:
        stem = f"{stem}-{_short_hash(parsed.query)}"

    ext = ext.lstrip(".")
    return Path(_safe_segment(company), host, *segments, f"{stem}.{ext}.gz")


def path_for(url: str, company: str, *, ext: str = "html", base_dir: Path | None = None) -> Path:
    """Absolute archive path for a URL, guaranteed to sit inside the raw root."""
    base = Path(base_dir or DEFAULT_RAW_DIR)
    candidate = base / relative_path_for(url, company, ext=ext)

    # Belt and braces: the sanitiser should make this impossible, but URLs are untrusted
    # and a path-traversal bug here writes attacker-chosen bytes to arbitrary locations.
    resolved = candidate.resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise ValueError(f"refusing to write outside the raw archive: {url!r} -> {resolved}")
    return candidate


def ext_for(content_type: str | None, url: str = "") -> str:
    """Pick the content extension from the Content-Type header, falling back to the URL."""
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype in ("text/markdown", "text/x-markdown"):
        return "md"
    if ctype in ("text/html", "application/xhtml+xml"):
        return "html"
    if ctype == "application/json":
        return "json"
    if ctype.startswith("text/"):
        return "txt"
    return "md" if url.endswith(".md") else "html"


def write(
    url: str,
    company: str,
    content: bytes,
    *,
    ext: str = "html",
    base_dir: Path | None = None,
) -> Path:
    """Write page bytes to the archive atomically. Returns the path written.

    gzip's mtime is zeroed so identical content produces identical files — re-fetching an
    unchanged page leaves the archive byte-for-byte unchanged, which keeps backups and
    `git status` honest about what actually moved.
    """
    path = path_for(url, company, ext=ext, base_dir=base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "wb") as fh, gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
            gz.write(content)
        os.replace(tmp, path)          # atomic on POSIX
    except BaseException:
        tmp.unlink(missing_ok=True)    # never leave a half-written archive entry
        raise

    return path


def read(path: str | Path) -> bytes:
    """Read archived bytes back, decompressed."""
    with gzip.open(Path(path), "rb") as fh:
        return fh.read()


def sha256(content: bytes) -> str:
    """Hash of the raw bytes — the change-detection key for hosts without validators."""
    return hashlib.sha256(content).hexdigest()


def claimed_by(url: str, company: str, others: dict[str, str], *, ext: str = "html") -> str | None:
    """Return a *different* URL already mapped to this URL's path, if any.

    `others` is a {path: url} mapping, normally straight out of `fetch.db`. Sanitising is
    lossy, so two URLs can in principle collapse onto one file; this makes that visible
    instead of letting the second fetch silently overwrite the first.
    """
    key = str(relative_path_for(url, company, ext=ext))
    owner = others.get(key)
    return owner if owner is not None and owner != url else None
