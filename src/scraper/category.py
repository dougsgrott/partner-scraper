"""Derive a page's category from its URL path. See PLAN.md §7.3.

The v1 design asked Claude to classify every page into a per-company taxonomy. That is
unnecessary: the URL path already encodes the site's own taxonomy, maintained by the
people who wrote the docs. `/aws/en/delta/…` is the Delta Lake section because Databricks
says so, not because a model guessed.

Deriving it here instead means the corpus layout is deterministic, stable across re-runs,
and free — no tokens, no drift, no prompt to keep in sync.
"""

from __future__ import annotations

from urllib.parse import urlparse

# A URL that *is* the include prefix (e.g. https://docs.databricks.com/aws/en/) is the
# section's front page. Naming it after the prefix's last segment would file it under the
# locale — category "en" — so it gets an explicit label instead.
_INDEX = "index"


def category_for(url: str, include_paths: list[str], depth: int = 1) -> tuple[str, str]:
    """Return `(label, prefix)` for a URL.

    Strips the longest matching include prefix, then takes the next `depth` path
    segments as the label. `prefix` is the full path-prefix, ready to paste into a
    config's `include_paths`/`exclude_paths`.
    """
    path = urlparse(url).path
    matched = ""
    for prefix in sorted(include_paths, key=len, reverse=True):
        if path.startswith(prefix):
            matched = prefix
            break

    remainder = [s for s in path[len(matched):].split("/") if s]
    if not remainder:
        return _INDEX, (matched or "/")

    label = "/".join(remainder[:depth])
    prefix = f"{matched}{label}/" if matched else f"/{label}/"
    return label, prefix


def slug_for(url: str) -> str:
    """A filesystem-safe leaf name for a URL, used for the corpus filename."""
    import re

    path = urlparse(url).path.strip("/")
    slug = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
    return slug or "index"
