"""Two judgements about a changed page: *who* changed it, and *how much it matters*.

Both are deliberately deterministic. A model will eventually read these diffs, but it
should be handed a set that has already been attributed and ranked — otherwise it spends
its attention re-deriving facts that a string comparison settles.

## Attribution: did they change it, or did we?

The question this whole package exists to answer honestly. A `content_hash` move does
**not** mean the vendor edited the page — re-running a revised extractor moves the hash of
every page it touches. The MDX conversion rewrote all 566 Anthropic pages in one pass; a
feed without attribution would have reported 566 vendor changes that never happened.

`body_fingerprint` (see `scraper.extract.registry`) is the signal: it hashes the extractor
and the modules it is built from, so it moves exactly when the code that decides a page's
*body* moves.

It is deliberately **not** `output_fingerprint`, which also covers the writer and the
layout. That was the first version of this check, and it failed in the opposite direction
from every earlier fingerprint bug: a one-line `writer.py` edit — which can only change the
frontmatter — together with a widening of the fingerprint formula itself made 594 genuine
Databricks changes report as our own churn. Because the value is stored per page at extract
time, changing how it is computed silently invalidated every stored comparison at once.
That is also why the ladder below falls back rather than assuming.

## Weight and severity: what should a reader look at first?

A ranking, never a filter. Nothing is dropped on the strength of these heuristics — a
change feed that silently under-reports is worse than one that over-reports, because the
reader has no way to notice the omission. `low` and `noise` are still counted and still
listed by URL; they are simply not expanded.

**Ordering matters more than bucketing here, and that was a surprise.** The first version
of this module assumed its 97%-substantive verdict meant the heuristic was broken. Measuring
the 1,116 real modifications in the first run said otherwise: 84% genuinely move a link, a
heading, a code block, or a number, and the median change rewrites 19% of its page. Reading a
stratified sample of 64 confirmed it — among the cases that *looked* least significant were a
SQL property that is "no longer supported", a function leaving Beta, a narrowed availability
list, and a model quietly dropped from a supported-model table. Only a minority were genuine
editorial churn.

So the bucket distribution was roughly right, and no honest threshold reduces ~680
substantive changes to a readable handful. What a reader needs from a feed this size is the
*most important thirty*, which is why `severity` exists and why the feed is sorted by it.
Reduction beyond that has to come from clustering or a model pass, not from ranking.

The strongest single signal turned out to be one the first version had no notion of:
**status and policy language** in the changed lines — deprecated, no longer, not supported,
beta, generally available, required. On the read sample it fired on every change worth
reading, including two with no structural signal at all, and on neither editorial change.
"""

from __future__ import annotations

import difflib
import re
from collections import Counter

# --- attribution ----------------------------------------------------------

CONTENT = "content"     # the vendor changed the page
PIPELINE = "pipeline"   # we changed the extractor; not attributable to the vendor
UNKNOWN = "unknown"     # cannot tell — see `attribute`

CAUSES = (CONTENT, PIPELINE, UNKNOWN)


def attribute(before: dict, after: dict) -> str:
    """Who is responsible for a `content_hash` move.

    The ladder, strongest signal first:

    1. **Both `body_fingerprint`s known.** Equal means the code that produces the body is
       unchanged, so the page itself moved: `content`. Different means we did: `pipeline`.
    2. **A `body_fingerprint` is missing** — it lives only in `index.db`, not in the
       frontmatter, so a rebuilt index has none, and so does any snapshot taken before the
       column existed. Fall back to the `name@version` string, which does survive in the
       file.
    3. **Neither is usable.** `unknown`, reported in its own bucket. Not folded into
       `content`: presenting our own churn as vendor churn is the specific failure this
       function exists to prevent, and a smaller honest feed beats a larger wrong one.

    `output_fingerprint` is consulted only in one direction, at rung 1b. It covers a
    *superset* of what `body_fingerprint` covers, so an **unchanged** superset proves the
    subset is unchanged too — the body pipeline cannot have moved, and the page is the
    vendor's doing. A **changed** superset proves nothing either way: the difference may
    lie entirely in the writer or the layout, neither of which can alter a word of the
    body. So it can clear a page but never convict one.

    That asymmetry is what makes snapshots taken before `body_fingerprint` existed still
    useful: without it, every modification in such a pair falls to `unknown` and 522
    correct attributions are lost along with the 594 wrong ones.
    """
    fp_before, fp_after = before.get("body_fingerprint"), after.get("body_fingerprint")
    if fp_before and fp_after:
        return CONTENT if fp_before == fp_after else PIPELINE

    out_before, out_after = before.get("output_fingerprint"), after.get("output_fingerprint")
    if out_before and out_after and out_before == out_after:
        return CONTENT

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

# With no signal at all, a change this small is editorial: a typo, a reflow, a reworded
# clause. Above it, a large prose rewrite is worth seeing even with nothing structural in it.
LOW_DELTA_CHARS = 900

# Bumped when STATUS, RESTRICTION, or how their consumers order the model's input changes
# behaviour. Stamped into run reports for the PROMPT_VERSION reason: a changed lexicon
# changes severity, excerpts, and the digest's reading order, and without a stamp two runs
# from different lexicons are silently incomparable.
CLASSIFY_VERSION = 1

# Status and policy language. Empirically the highest-value signal in the corpus: it is
# what distinguishes "this function left Beta" and "this property is no longer supported"
# from a paragraph being reworded, and neither is visible to a structural comparison.
#
# Deliberately NOT extended with the restriction words below, although it looks like an
# oversight (`required` but not `requires`, `must ` but not `must.`). Extending it was
# measured on both stored runs (issue/accuracy/02, 2026-09-18): the Fable 5 retention
# page — the miss the extension was meant to rescue — moved rank 538 -> 499 of 986,
# nowhere near the top, while ten Admin-API reference pages rode "Requires an OAuth
# access token…" boilerplate into the #5 -> #6 top-100 and pushed real docs pages out.
# Density arithmetic is the wrong delivery vehicle for restriction language; RESTRICTION
# below feeds the channels that work. Do not add words here without re-running that
# measurement and a graded A/B (docs/accuracy-plan.md, standing constraints).
STATUS = re.compile(
    r"\b(deprecat\w*|no longer|removed|discontinu\w*|end[- ]of[- ]\w+|sunset\w*"
    r"|breaking|beta|preview|generally available|now available|GA\b"
    r"|not (?:supported|available)|unsupported|required|must )",
    re.IGNORECASE,
)

# Restriction language: something you cannot do, lose, or now need. The signature of the
# change class the digest misses ("Customers who opt out of data retention cannot use
# Claude Fable 5" carried no signal at all — issue/accuracy/02 has the measurements).
# Split from STATUS because the consumers' error costs differ: this one feeds the
# restriction-boosted excerpt (`compress._excerpt`) and the absence detector of
# issue/accuracy/05, both of which want precision, while STATUS feeds ranking density,
# which the measured words made worse, not better.
#
# Word-by-word decisions, from reading seeded samples of marginal hits on both stored
# runs (counts in the issue file): `cannot`, `requires`, `reject(s|ed)`, `must` at end of
# clause — admitted, hits overwhelmingly state real constraints. `unavailable` — admitted
# HERE but kept out of STATUS: its ranking effect measured ~zero and its #6 -> #7 hits
# were 83% Admin-API null-semantics boilerplate ("null when the account is unavailable"),
# but as restriction *language* it is exactly what the absence detector must see. The
# withdrawal words (`no longer`, `not supported/available`, `unsupported`, `deprecat*`,
# `removed`, `discontinu*`) carry over from STATUS's original calibration — a restriction
# scan that missed "no longer supported" would be absurd — not from new measurement.
RESTRICTION = re.compile(
    r"\b(cannot|not (?:supported|available)|unsupported|unavailable"
    r"|no longer|require[sd]\b|must\b|reject(?:s|ed)?\b"
    r"|deprecat\w*|removed|discontinu\w*)",
    re.IGNORECASE,
)

LINK = re.compile(r"\]\(([^)\s]+)")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$", re.MULTILINE)
FENCE = re.compile(r"^(`{3,}|~{3,}).*?^\1`*\s*$", re.MULTILINE | re.DOTALL)
NUMBER = re.compile(r"\b\d[\d.,]*\b")

# How much each signal counts toward severity, applied to its *density* — see `severity`.
# Judgement, calibrated by reading a stratified sample of 64 diffs and then the top of the
# resulting feed. Not fitted, and not a probability: the ordering is the product, and the
# absolute values mean nothing on their own.
SIGNAL_WEIGHTS = {"status": 4.0, "code": 3.0, "headings": 2.0, "numbers": 2.0, "links": 1.0}

_WS = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Collapse whitespace so reflowed prose is not mistaken for an edit."""
    return _WS.sub(" ", text).strip()


def changed_lines(before: str, after: str) -> list[str]:
    """Lines that appear a different number of times in the two bodies.

    A multiset difference rather than a `difflib` alignment, and that is a deliberate
    trade. `difflib` is superlinear, and this corpus holds pages of 6.0 MB — weighing all
    1,116 modifications of the first run took ten minutes through `difflib` and **4.6
    seconds** this way. For ranking, an unaligned symmetric difference carries the same
    information: a moved line is unchanged in both multisets and correctly ignored.

    `changed_text` still uses `difflib`, because rendering a diff for a human does need
    the alignment.
    """
    removed, added = changed_sides(before, after)
    return removed + added


def changed_sides(before: str, after: str) -> tuple[list[str], list[str]]:
    """`(removed, added)` — the same multiset difference, keeping which side each came from.

    Direction is not decoration. "the TypeScript and Ruby tool runners support automatic
    compaction" means the opposite thing depending on whether it is the old line or the new
    one, and an excerpt that shows both without marking them is worse than showing neither.
    """
    before_lines = Counter(before.splitlines())
    after_lines = Counter(after.splitlines())
    return (list((before_lines - after_lines).elements()),
            list((after_lines - before_lines).elements()))


def _multiset_delta(before: str, after: str, pattern: re.Pattern, group: int = 0) -> int:
    """How many extracted items differ between the two bodies."""
    def found(text: str) -> Counter:
        return Counter(m.group(group).strip() for m in pattern.finditer(text))

    b, a = found(before), found(after)
    return sum(((b - a) + (a - b)).values())


def signals(before: str, after: str) -> dict[str, int]:
    """The raw evidence behind a severity score, per signal.

    Returned rather than folded away so a report can say *why* something ranked where it
    did, and so the weighting can be re-tuned without re-deriving the features.
    """
    lines = changed_lines(before, after)
    return {
        "status": sum(1 for line in lines if STATUS.search(line)),
        "code": _multiset_delta(before, after, FENCE),
        "headings": _multiset_delta(before, after, HEADING, 1),
        "numbers": _multiset_delta(before, after, NUMBER),
        "links": _multiset_delta(before, after, LINK, 1),
        "changed_lines": len(lines),
        "changed_chars": sum(len(line) for line in lines),
    }


def severity(counts: dict[str, int]) -> float:
    """How far up the feed this change belongs. Higher is more urgent.

    **Density, not volume.** Each signal counts as the share of changed lines carrying it,
    capped at one, so the score says *how concentrated* the evidence is rather than how
    much of it there is.

    That distinction decided the ranking. Scoring by volume — `log1p` of each raw count —
    filled the top of the feed with regenerated API reference pages: one had 11,181 lines
    matching the status pattern simply because it is enormous. Under density the same run
    surfaces a swapped beta header, a region's supported-model list changing from
    `databricks-gpt-5-5-pro` to `databricks-grok-4-6`, and the Python tool runner quietly
    losing automatic compaction — small, sharp changes a reader must not miss.

    Size is not a term here at all, for the same reason it is not one in `weigh` beyond the
    floor: the largest change in the first run rewrote 4.2 MB of a machine-generated dump.
    """
    lines = max(counts.get("changed_lines", 0), 1)
    return sum(weight * min(1.0, counts.get(name, 0) / lines)
               for name, weight in SIGNAL_WEIGHTS.items())


def weigh(before: str | None, after: str | None) -> str:
    """Rank one page's change. Missing bodies rank `substantive` — never assume harmless.

    A body the store cannot supply means the diff could not be inspected, which is a
    reason to look, not a reason to skip.
    """
    if before is None or after is None:
        return SUBSTANTIVE
    if normalise(before) == normalise(after):
        return NOISE

    counts = signals(before, after)
    if severity(counts) > 0:
        return SUBSTANTIVE
    return LOW if counts["changed_chars"] < LOW_DELTA_CHARS else SUBSTANTIVE


def changed_text(before: str, after: str) -> str:
    """The added and removed lines only, without context, aligned by `difflib`.

    Used for rendering, not for ranking — see `changed_lines` for why.
    """
    lines = difflib.unified_diff(
        before.splitlines(), after.splitlines(), lineterm="", n=0)
    return "\n".join(
        line[1:] for line in lines
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    )
