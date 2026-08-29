"""Does each file faithfully represent its source? See docs/validation-plan.md §2.

Three sources of truth, in descending order of strength:

1. **Anthropic docs** — the archive holds the Markdown the site itself served, so the
   comparison is exact and covers the whole population, not a sample. The corpus body is
   inverted back through the two documented transforms (an added title heading, rooted
   links absolutised) and must then equal what was served, byte for byte.
2. **The cookbook** — each page names the `.ipynb` it was generated from, so the code
   cells of the real notebook are ground truth for the extractor's hardest job.
3. **Databricks** — no ground truth exists, so a second, independently-written extractor
   reads the same archived bytes and the two results are compared for recall. Agreement
   is not proof; disagreement is where to look.

The inverse transforms here are written independently of `extract/` on purpose. Verifying
the pipeline by calling the pipeline proves only that it is self-consistent.
"""

from __future__ import annotations

import re
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from ..fetch import rawstore
from ..store import writer
from .report import Check, failed, passed, skipped

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_COMPONENT = re.compile(r"<([A-Z][A-Za-z0-9]*)\b")
_COMPONENT_TAG = re.compile(r"</?[A-Z][A-Za-z0-9]*\b[^>]*>", re.DOTALL)
_ATTRIBUTE = re.compile(r"""[A-Za-z][\w-]*\s*=\s*(?:"[^"]*"|'[^']*'|\{[^}]*\})""")
_HREF = re.compile(r'href="([^"]+)"')
_WORD = re.compile(r"[a-z0-9]+")
_BLANKS = re.compile(r"\n{3,}")


@dataclass
class Comparison:
    """One page checked against its source."""

    url: str
    ok: bool
    reason: str = ""
    detail: dict = field(default_factory=dict)


def normalise(text: str) -> str:
    """Whitespace normalisation applied to both sides before comparing."""
    return _BLANKS.sub("\n\n", "\n".join(line.rstrip() for line in text.splitlines())).strip()


def served_body(raw: bytes) -> str:
    """The body of a served `.md`, with the site's own frontmatter removed."""
    text = raw.decode("utf-8", "replace")
    match = _FRONTMATTER.match(text)
    return text[match.end():] if match else text


def canonicalise_links(text: str, origin: str) -> str:
    """Put every in-site link in one form, so both sides can be compared directly.

    Rewriting *our* absolute links back to rooted paths does not work: the served
    Markdown already contains a mix of both, so the inverse is not injective and 320 of
    566 pages "differed" purely because a link had been absolute all along. Normalising
    both sides forwards has no such ambiguity.
    """
    return re.sub(r"\]\((/(?!/)[^)\s]*)\)", rf"]({origin}\1)", text)


def drop_added_title(body: str, title: str) -> str:
    """Remove the `# title` heading the corpus prepends, if this page has one."""
    if not title:
        return body
    first, _, rest = body.partition("\n")
    return rest.lstrip("\n") if first.strip() == f"# {title}" else body


def align(body: str, *, title: str, canonical: str) -> str:
    """Reduce a body to the form both sides are compared in."""
    origin = f"{urlsplit(canonical).scheme}://{urlsplit(canonical).netloc}"
    return normalise(canonicalise_links(drop_added_title(body, title), origin))


def align_pair(ours: str, theirs: str, *, title: str, canonical: str) -> tuple[str, str]:
    """Align a corpus body and its served original for comparison.

    The title heading can only be judged by looking at both: `…/api/models` is served
    *with* `# Models` already at the top, so stripping it from our side unconditionally
    made the corpus look like it had dropped content. It is removed from ours only when
    the source did not have it — which is exactly when we added it.
    """
    origin = f"{urlsplit(canonical).scheme}://{urlsplit(canonical).netloc}"
    theirs_aligned = normalise(canonicalise_links(theirs, origin))
    ours_aligned = normalise(canonicalise_links(ours, origin))

    lead = f"# {title}".strip()
    if title and ours_aligned.startswith(lead) and not theirs_aligned.startswith(lead):
        ours_aligned = normalise(drop_added_title(ours_aligned, title))
    return ours_aligned, theirs_aligned


def source_has_components(served: str) -> bool:
    """Whether the served Markdown carries MDX the extractor is expected to convert."""
    from ..extract import mdx

    return bool({m for m in _COMPONENT.findall(mdx.strip_code(served))} & mdx.KNOWN)


def content_preserved(ours: str, theirs: str) -> tuple[bool, str]:
    """Everything the source said still present, after a conversion that is not invertible.

    Two assertions: every link target survives, and every prose word survives. Attribute
    noise the conversion deliberately drops (`icon="lock"`, `cols={3}`) is excluded, as
    are the component names themselves.
    """
    from ..extract import mdx

    missing_links = [href for href in set(_HREF.findall(theirs)) if href not in ours]
    if missing_links:
        return False, f"{len(missing_links)} link(s) lost, e.g. {missing_links[0]}"

    prose = _ATTRIBUTE.sub(" ", _COMPONENT_TAG.sub(" ", theirs))
    theirs_words = Counter(_WORD.findall(prose.lower()))
    ours_words = Counter(_WORD.findall(ours.lower()))
    for name in mdx.KNOWN:                       # tag names are markup, not content
        theirs_words.pop(name.lower(), None)
    lost = {w: n - ours_words.get(w, 0) for w, n in theirs_words.items()
            if ours_words.get(w, 0) < n}
    if lost:
        worst = sorted(lost.items(), key=lambda kv: -kv[1])[:3]
        return False, f"{sum(lost.values())} word(s) lost, e.g. {worst}"
    return True, ""


def compare_served_markdown(fetch_db_path: str | Path = "state/fetch.db",
                            data_dir: str | Path = "data",
                            source_id: str = "anthropic-docs") -> list[Comparison]:
    """Every corpus page for a source, against the Markdown its site served.

    Pages whose source is plain Markdown must match **exactly**. Pages carrying MDX are
    converted (PLAN.md §7.1), and conversion is not invertible, so those are held to
    content preservation instead: every link and every word still present.
    """
    conn = sqlite3.connect(fetch_db_path)
    conn.row_factory = sqlite3.Row
    archived = {r["url"]: r["raw_path"] for r in conn.execute(
        "SELECT url, raw_path FROM fetches WHERE source_id = ? AND raw_path IS NOT NULL",
        (source_id,))}
    conn.close()

    results = []
    for path in Path(data_dir).rglob("*.md"):
        front, body = writer.parse(path)
        if front.get("source_id") != source_id:
            continue
        raw_path = archived.get(front.get("source_url"))
        if raw_path is None or not Path(raw_path).exists():
            results.append(Comparison(front.get("source_url", str(path)), False, "no archived bytes"))
            continue

        canonical = str(front.get("canonical_url", ""))
        served = served_body(rawstore.read(raw_path))
        ours, theirs = align_pair(body, served, title=str(front.get("title", "")),
                                  canonical=canonical)
        converted = source_has_components(served)

        if not converted:
            ok, reason = (ours == theirs), _describe(ours, theirs) if ours != theirs else ""
        else:
            ok, reason = content_preserved(ours, theirs)
        results.append(Comparison(front["source_url"], ok, reason,
                                  detail={"converted": converted}))
    return results


def _describe(ours: str, theirs: str) -> str:
    """Where the two first diverge, in a form that points at the cause."""
    if theirs in ours:
        return f"we added {len(ours) - len(theirs)} chars beyond what was served"
    if ours in theirs:
        return f"we dropped {len(theirs) - len(ours)} chars that were served"
    for i, (a, b) in enumerate(zip(ours, theirs, strict=False)):
        if a != b:
            return f"diverges at char {i}: ours {ours[i:i+40]!r} vs served {theirs[i:i+40]!r}"
    return f"length differs: ours {len(ours)}, served {len(theirs)}"


def check_served_markdown(fetch_db_path: str | Path = "state/fetch.db",
                          data_dir: str | Path = "data",
                          source_id: str = "anthropic-docs") -> Check:
    results = compare_served_markdown(fetch_db_path, data_dir, source_id)
    if not results:
        return skipped(f"fidelity_{source_id}", "no pages for this source")

    exact = [r for r in results if not r.detail.get("converted")]
    converted = [r for r in results if r.detail.get("converted")]
    bad = [r for r in results if not r.ok]
    summary = (f"{len(exact)} plain page(s) byte-exact against the served Markdown; "
               f"{len(converted)} MDX page(s) content-preserved")
    if bad:
        return failed(f"fidelity_{source_id}", summary + f" — {len(bad)} failing",
                      count=len(bad), total=len(results),
                      samples=[f"{r.url}: {r.reason}" for r in bad[:5]])
    return passed(f"fidelity_{source_id}", summary, total=len(results),
                  detail={"exact": len(exact), "content_preserved": len(converted)})


# --- notebooks -------------------------------------------------------------

def raw_github_url(blob_url: str) -> str:
    """`github.com/o/r/blob/main/x.ipynb` → the raw file."""
    return (blob_url
            .replace("https://github.com/", "https://raw.githubusercontent.com/", 1)
            .replace("/blob/", "/", 1))


def notebook_cells(notebook: dict) -> tuple[list[str], list[str]]:
    """`(code_sources, markdown_sources)` for a parsed `.ipynb`."""
    code, markdown = [], []
    for cell in notebook.get("cells", []):
        source = "".join(cell.get("source", []))
        if not source.strip():
            continue
        (code if cell.get("cell_type") == "code" else markdown).append(source)
    return code, markdown


# Fences vary in length: a block quoting Markdown opens with ````. Pairing them by
# assuming exactly three backticks is the same mistake the extraction quality gate made
# in step 5, repeated here — it hid 6 code cells that were present and correctly fenced.
_FENCED = re.compile(r"^(?P<f>`{3,}|~{3,})[^\n]*\n(?P<code>.*?)^(?P=f)`*[ \t]*$",
                     re.MULTILINE | re.DOTALL)


def fenced_text(body: str) -> str:
    """Everything inside fenced code blocks, whatever fence length they use."""
    return "\n".join(m.group("code") for m in _FENCED.finditer(body))


def compare_notebook(body: str, notebook: dict) -> Comparison:
    """How much of the real notebook survived into the corpus page."""
    code, markdown = notebook_cells(notebook)
    fenced = fenced_text(body)

    def present(text: str, haystack: str) -> bool:
        lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
        if not lines:
            return True
        hits = sum(1 for ln in lines if ln in haystack)
        return hits / len(lines) >= 0.9        # tolerate a trailing-whitespace difference

    code_hits = sum(1 for cell in code if present(cell, fenced))
    prose_hits = sum(1 for cell in markdown if present(_plain(cell), body))
    ok = code_hits == len(code)
    detail = {"code_cells": len(code), "code_matched": code_hits,
              "markdown_cells": len(markdown), "markdown_matched": prose_hits}
    reason = "" if ok else f"{len(code) - code_hits} of {len(code)} code cells not found in fences"
    return Comparison("", ok, reason, detail=detail)


def _plain(markdown_cell: str) -> str:
    """Notebook markdown minus the syntax our converter re-renders differently."""
    return re.sub(r"[*_`#>\[\]()]", "", markdown_cell)
