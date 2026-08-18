"""Map a source's configured `extractor` name to the function that implements it.

Unimplemented extractors are *absent* rather than silently aliased to a fallback: writing
a Docusaurus page through the wrong parser produces a plausible-looking file, and a
plausible-looking wrong file is the failure mode this pipeline is built to avoid.
"""

from __future__ import annotations

from collections.abc import Callable

from . import docusaurus, passthrough_md
from .base import Extracted, RawPayload

Extractor = Callable[[RawPayload], Extracted]

EXTRACTORS: dict[str, Extractor] = {
    docusaurus.NAME: docusaurus.extract,
    passthrough_md.NAME: passthrough_md.extract,
}

VERSIONS: dict[str, str] = {
    docusaurus.NAME: docusaurus.VERSION,
    passthrough_md.NAME: passthrough_md.VERSION,
}


def get(name: str) -> Extractor | None:
    return EXTRACTORS.get(name)


def version(name: str) -> str:
    """Bumping an extractor's version forces re-extraction from `raw/` (PLAN.md §8)."""
    return VERSIONS.get(name, "0")


def implemented() -> frozenset[str]:
    return frozenset(EXTRACTORS)
