"""Two judgements about a changed page: *who* changed it, and *how much it matters*.

Both are deliberately deterministic. A model will eventually read these diffs, but it
should be handed a set that has already been attributed and ranked — otherwise it spends
its attention re-deriving facts that a string comparison settles.

## Attribution: did they change it, or did we?

The question this whole package exists to answer honestly. A `content_hash` move does
**not** mean the vendor edited the page — re-running a revised extractor moves the hash of
every page it touches. The MDX conversion rewrote all 566 Anthropic pages in one pass; a
feed without attribution would have reported 566 vendor changes that never happened.

`output_fingerprint` (see `scraper.extract.registry`) is the signal: it hashes the
extractor, its imports, the writer, and the layout, so it moves exactly when our output
pipeline moves. This project has widened that fingerprint three times after it silently
under-reported, which is the reason the ladder below falls back rather than assuming.

## Weight: is this worth a human's attention?

A ranking, never a filter. Nothing is dropped on the strength of these heuristics — a
change feed that silently under-reports is worse than one that over-reports, because the
reader has no way to notice the omission. `low` and `noise` are still counted and still
listed by URL; they are simply not expanded.
"""

from __future__ import annotations

import difflib
import re

# --- attribution ----------------------------------------------------------

CONTENT = "content"     # the vendor changed the page
PIPELINE = "pipeline"   # we changed the extractor; not attributable to the vendor
UNKNOWN = "unknown"     # cannot tell — see `attribute`

CAUSES = (CONTENT, PIPELINE, UNKNOWN)


def attribute(before: dict, after: dict) -> str:
    """Who is responsible for a `content_hash` move.

    The ladder, strongest signal first:

    1. **Both fingerprints known.** Equal means our pipeline is unchanged, so the page
       itself moved: `content`. Different means we did: `pipeline`.
    2. **A fingerprint is missing** — `output_fingerprint` lives only in `index.db`, not
       in the frontmatter, so a rebuilt index has none. Fall back to the `name@version`
       string, which does survive in the file.
    3. **Neither is usable.** `unknown`, reported in its own bucket. Not folded into
       `content`: presenting our own churn as vendor churn is the specific failure this
       function exists to prevent, and a smaller honest feed beats a larger wrong one.
    """
    fp_before, fp_after = before.get("output_fingerprint"), after.get("output_fingerprint")
    if fp_before and fp_after:
        return CONTENT if fp_before == fp_after else PIPELINE

    ex_before, ex_after = before.get("extractor"), after.get("extractor")
    if ex_before and ex_after and ex_before != ex_after:
        return PIPELINE

    # A same-named extractor whose VERSION was not bumped is indistinguishable from an
    # unchanged one — the first trap this project ever hit. Say so rather than guess.
    return UNKNOWN


# --- weight ---------------------------------------------------------------

SUBSTANTIVE = "substantive"
LOW = "low"
NOISE = "noise"

WEIGHTS = (SUBSTANTIVE, LOW, NOISE)

# Below this many changed characters, a diff carrying none of the signals below is
# treated as editorial. Tuned to be forgiving: a sentence rewritten is ~100 chars.
LOW_DELTA_CHARS = 160

# Things whose change is almost never merely editorial: a link target, a URL, a heading,
# a code fence, an inline code span, or a version-shaped number.
SIGNAL = re.compile(
    r"""\]\(              # a Markdown link target
      | https?://         # a bare URL
      | ^\s{0,3}\#{1,6}\s # a heading
      | ^\s*`{3,}         # a fence
      | `[^`\n]+`         # an inline code span
      | \b\d+\.\d+        # a version or a decimal
      | \b\d{3,}\b        # a limit, a size, a status code
    """,
    re.VERBOSE | re.MULTILINE,
)

_WS = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Collapse whitespace so reflowed prose is not mistaken for an edit."""
    return _WS.sub(" ", text).strip()


def weigh(before: str | None, after: str | None) -> str:
    """Rank one page's change. Missing bodies rank `substantive` — never assume harmless.

    A body the store cannot supply means the diff could not be inspected, which is a
    reason to look, not a reason to skip.
    """
    if before is None or after is None:
        return SUBSTANTIVE
    if normalise(before) == normalise(after):
        return NOISE

    changed = changed_text(before, after)
    if SIGNAL.search(changed):
        return SUBSTANTIVE
    return LOW if len(changed) < LOW_DELTA_CHARS else SUBSTANTIVE


def changed_text(before: str, after: str) -> str:
    """The added and removed lines only, without context — what `weigh` inspects."""
    lines = difflib.unified_diff(
        before.splitlines(), after.splitlines(), lineterm="", n=0)
    return "\n".join(
        line[1:] for line in lines
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    )
