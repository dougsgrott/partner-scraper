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
    """A hash of everything that decides what a page's *file* looks like.

    That is the extractor itself *plus* the writer and layout modules: the extractor
    decides the content, the writer decides the frontmatter, and layout decides the path.

    `VERSION` states intent — "this output differs, re-extract" — but it is set by hand.
    Step 8 hit both halves of that: an extractor edited without a bump reported "skipped
    unchanged" and kept stale output, and then a frontmatter change did the same thing
    one layer down, where no extractor version could have caught it. Hashing the source
    catches both automatically. A false positive costs CPU and nothing else — since step
    6, rewriting an unchanged page leaves the file byte-identical.

    This is the *re-extraction* trigger and deliberately errs wide. It is **not** the
    right input for deciding who changed a page — see `body_fingerprint`.
    """
    extractor = _module_for(name)
    if extractor is None:
        return None
    from ..store import layout, writer

    return _hash_modules({*_project_modules(extractor), writer, layout})


def body_fingerprint(name: str) -> str | None:
    """A hash of everything that decides what a page *says*.

    The extractor and the modules it is built from — and nothing else. Notably **not**
    the writer or the layout: the writer decides the frontmatter and layout decides the
    file path, and neither can change a word of the body.

    That distinction is the whole point. `output_fingerprint` covers both, which makes it
    the right trigger for re-extraction and the wrong input for attribution: the change
    feed used it to answer "did *we* change this page, or did the vendor?", so a one-line
    `writer.py` edit made 594 genuine Databricks changes look like our own churn. Worse,
    the same commit widened the fingerprint *formula*, and because the value is stored per
    page at extract time, changing how it is computed silently invalidated every stored
    comparison at once.

    Keep this hash narrow. Anything added here must be able to change the body.
    """
    extractor = _module_for(name)
    if extractor is None:
        return None
    return _hash_modules(_project_modules(extractor))


def _module_for(name: str):
    extractor = EXTRACTORS.get(name)
    return None if extractor is None else inspect.getmodule(extractor)


def _hash_modules(modules) -> str | None:
    """Hash a set of modules by source, in a stable order.

    Sorting by `__name__` is load-bearing: a set iterates in an order that varies between
    processes, and an unstable fingerprint would report every page as ours on every run.
    """
    try:
        sources = [inspect.getsource(m) for m in sorted(modules, key=lambda m: m.__name__)]
    except (OSError, TypeError):
        return None
    return hashlib.sha256("".join(sources).encode("utf-8")).hexdigest()[:12]


def _project_modules(module) -> set:
    """A module and the project modules it draws on.

    Following imports matters: `passthrough_md` delegates its MDX conversion to
    `extract/mdx.py`, and hashing only the extractor's own file meant a rewrite of that
    converter changed every page's output while every page reported "skipped unchanged".
    That is the third time a change slipped past this hash — first an unbumped `VERSION`,
    then the writer, now an imported helper — so the rule is now "everything the
    extractor is built from", resolved from what its namespace actually holds.
    """
    if module is None:
        return set()
    found = {module}
    for value in vars(module).values():
        owner = value if inspect.ismodule(value) else inspect.getmodule(value)
        name = getattr(owner, "__name__", "")
        if owner is not None and name.startswith("scraper.") and owner not in found:
            found.add(owner)
    return found


def implemented() -> frozenset[str]:
    return frozenset(EXTRACTORS)
