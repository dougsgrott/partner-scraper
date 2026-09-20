"""Keep every scraping session's raw bytes. See plans/raw-archive-plan.md.

`raw/` holds one version of each page and a refresh overwrites it, so without this the only
record of what a vendor served on a given date is the date of the last crawl. This archives
each session's bytes as a **generation**, so "what did Databricks publish on 2026-08-29?" has
an answer, and so a fixed extractor can be re-run over historical input.

**A generation is hard-linked, not copied**, and that rests on a property `rawstore` already
guarantees: `write` builds a temp file and calls `os.replace`. It never writes in place, so a
later fetch swaps the directory entry and leaves the archived link pointing at the old inode.
Archiving therefore costs inodes, not data blocks — a generation occupies real space only for
the files that later diverge. A plain copy would duplicate the whole 55 MiB archive on every
run regardless of what changed.

Whole generations are kept even though ~80% of the byte churn is three rotating asset-hash
tokens per Databricks page. Storing only the pages whose *content* moved would be five times
cheaper, and is the intended next step — but it can only be designed against several real
generations, and pages it discards cannot be recovered. Keeping everything is what makes that
decision reversible.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from . import rawstore

if TYPE_CHECKING:
    from .runner import RunSummary

DEFAULT_ARCHIVE_DIR = Path("raw-archive")
MANIFEST = "manifest.json"


@dataclass(frozen=True)
class Generation:
    """One archived scraping session."""

    label: str
    path: Path
    taken_at: str
    files: int
    bytes: int
    run: str | None = None

    def render(self) -> str:
        return (f"  {self.label:24} {self.files:>6} files  "
                f"{self.bytes / 1_048_576:>7.1f} MiB  {self.taken_at}")


def _label_now() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S")


def archive(
    *,
    label: str | None = None,
    raw_dir: str | Path | None = None,
    archive_dir: str | Path | None = None,
    run: str | None = None,
) -> Generation:
    """Snapshot `raw/` as a generation. Returns what was captured.

    Refuses an existing label rather than merging into it: two sessions sharing a directory
    would silently produce a generation that never existed, mixing bytes from different days
    under one date — the archive's whole purpose is that a generation is a moment.
    """
    source = Path(raw_dir or rawstore.DEFAULT_RAW_DIR)
    base = Path(archive_dir or DEFAULT_ARCHIVE_DIR)
    label = label or _label_now()
    target = base / label

    if not source.exists():
        raise FileNotFoundError(f"nothing to archive: {source} does not exist")
    if target.exists():
        raise FileExistsError(
            f"generation {label!r} already exists at {target}; archiving into it would mix "
            f"two sessions under one date")

    target.mkdir(parents=True)
    files = total = 0
    for entry in sorted(source.rglob("*.gz")):
        relative = entry.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(entry, destination)
        except OSError:
            # A different filesystem, or a limit on link count. Copying is slower and costs
            # real blocks, but a generation that exists beats one that failed to.
            shutil.copy2(entry, destination)
        files += 1
        total += entry.stat().st_size

    generation = Generation(label=label, path=target,
                            taken_at=datetime.now(UTC).isoformat(timespec="seconds"),
                            files=files, bytes=total, run=run)
    (target / MANIFEST).write_text(
        json.dumps({"label": generation.label, "taken_at": generation.taken_at,
                    "files": generation.files, "bytes": generation.bytes,
                    "run": generation.run, "source": str(source)}, indent=2),
        encoding="utf-8")
    return generation


def archive_after(
    summary: RunSummary,
    *,
    label: str | None = None,
    raw_dir: str | Path | None = None,
    archive_dir: str | Path | None = None,
) -> Generation | None:
    """Archive what a fetch run left in `raw/` — the shared retention decision.

    Every in-repo entry point that fetches routes its "does this run get archived?"
    through here (issue/accuracy/09). `scripts/fetch.py` and `changes.py run --fetch`
    used to answer that question separately — one archived, one silently did not, and
    a generation nobody archived is unrecoverable once the next refresh overwrites
    `raw/`. A future caller of `run_fetch` should call this next, not re-decide.

    Returns None — archiving nothing — only when there is nothing new to lose: a dry
    run touched no bytes, and a run with zero `ok` fetches left `raw/` exactly as the
    last archived generation saw it (every page answered 304, or every request failed).
    """
    if summary.dry_run or not summary.ok:
        return None
    return archive(label=label, run=summary.started_at,
                   raw_dir=raw_dir, archive_dir=archive_dir)


def generations(archive_dir: str | Path | None = None) -> list[Generation]:
    """Every archived session, oldest first."""
    base = Path(archive_dir or DEFAULT_ARCHIVE_DIR)
    if not base.exists():
        return []

    found = []
    for entry in sorted(base.iterdir()):
        manifest = entry / MANIFEST
        if not entry.is_dir() or not manifest.exists():
            continue
        data = json.loads(manifest.read_text(encoding="utf-8"))
        found.append(Generation(label=data.get("label", entry.name), path=entry,
                                taken_at=data.get("taken_at", ""), files=data.get("files", 0),
                                bytes=data.get("bytes", 0), run=data.get("run")))
    return found


def verify(generation: Generation) -> tuple[int, int]:
    """`(files found, files the manifest claims)`.

    A generation is only worth keeping if it still holds what it says it does, and a hard
    link is easy to break by moving or copying the tree with the wrong tool.
    """
    found = sum(1 for _ in generation.path.rglob("*.gz"))
    return found, generation.files
