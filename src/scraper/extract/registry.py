"""Map a source's configured `extractor` name to the function that implements it.

Unimplemented extractors are *absent* rather than silently aliased to a fallback: writing
a Docusaurus page through the wrong parser produces a plausible-looking file, and a
plausible-looking wrong file is the failure mode this pipeline is built to avoid.
"""

from __future__ import annotations

import hashlib
import inspect
from collections.abc import Callable

from . import docusaurus, nextjs_article, passthrough_md
from .base import Extracted, RawPayload

Extractor = Callable[[RawPayload], Extracted]

EXTRACTORS: dict[str, Extractor] = {
    docusaurus.NAME: docusaurus.extract,
    nextjs_article.NAME: nextjs_article.extract,
    passthrough_md.NAME: passthrough_md.extract,
}

VERSIONS: dict[str, str] = {
    docusaurus.NAME: docusaurus.VERSION,
    nextjs_article.NAME: nextjs_article.VERSION,
    passthrough_md.NAME: passthrough_md.VERSION,
}


def get(name: str) -> Extractor | None:
    return EXTRACTORS.get(name)


def version(name: str) -> str:
    """Bumping an extractor's version forces re-extraction from `raw/` (PLAN.md §8)."""
    return VERSIONS.get(name, "0")


def output_fingerprint(name: str) -> str | None:
    """A hash of everything that decides what a page's file looks like.

    That is the extractor itself *plus* the writer and layout modules: the extractor
    decides the content, the writer decides the frontmatter, and layout decides the path.

    `VERSION` states intent — "this output differs, re-extract" — but it is set by hand.
    Step 8 hit both halves of that: an extractor edited without a bump reported "skipped
    unchanged" and kept stale output, and then a frontmatter change did the same thing
    one layer down, where no extractor version could have caught it. Hashing the source
    catches both automatically. A false positive costs CPU and nothing else — since step
    6, rewriting an unchanged page leaves the file byte-identical.
    """
    extractor = EXTRACTORS.get(name)
    if extractor is None:
        return None
    from ..store import layout, writer

    try:
        sources = [inspect.getsource(inspect.getmodule(extractor)),
                   inspect.getsource(writer), inspect.getsource(layout)]
    except (OSError, TypeError):
        return None
    return hashlib.sha256("".join(sources).encode("utf-8")).hexdigest()[:12]


def implemented() -> frozenset[str]:
    return frozenset(EXTRACTORS)
