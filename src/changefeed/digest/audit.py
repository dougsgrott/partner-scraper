"""Check that findings are TRUE, not merely well-formed. See docs/changefeed-phase-2.md.

URL validation proves a cited page changed; nothing proves the sentence about it is right.
This lays each finding beside its evidence so a person can decide — and does the one check
a person reliably misses at a glance.

Two lessons from the #5 -> #6 audit shaped it:

* **Showing the first three pages is not showing the evidence.** Findings there cited 13 to
  25 pages, and the first three were often not where the claim came from. Lines are now
  ranked by overlap with the claim itself, pages by their best line, and a finding that
  cites far more than is shown says so.
* **"New" is the claim most often wrong, and the easiest to check mechanically.** The
  digest reported Grok 4.6 and GLM 5.3 as newly added when both were already present —
  the tables had been rewritten whole, so the old entries reappeared on `+` lines. Any
  identifier a finding names is now checked against the *before* text of its cited pages.
"""

from __future__ import annotations

import random
import re
from collections import defaultdict
from dataclasses import dataclass, field

from .. import blobs, classify
from ..diff import PageChange
from .findings import IMPACTS, Finding

# Words that make up the claim. Short and common words carry no evidence.
_WORD = re.compile(r"[a-z0-9][a-z0-9._-]{2,}")
_STOP = frozenset(["the", "and", "for", "with", "that", "this", "from", "are", "was", "were", "now", "has", "have", "not", "but", "its", "into", "than", "then", "also", "only", "when", "what", "which", "will", "can", "may", "more", "most", "each", "other", "been", "being", "their", "there", "they", "them", "you", "your", "our", "all", "any", "new", "page", "pages", "docs", "document", "documentation"])

# Identifiers worth checking for prior existence — only *versioned* ones, because that is
# where "new" was wrong in practice (models and releases), and restricting to them keeps the
# check from flagging every region or product name mentioned in passing.
#
#   prose names:  Grok 4.6, GLM 5.3, Gemini 3.8 Flash, Claude Fable 5.1
#   id forms:     databricks-grok-4-6, claude-fable-5-1
#
# Prose matters: the first version matched only id forms, and the real finding that motivated
# the check wrote "Grok 4.6". Its synthetic test used an id and passed; the real case did not.
#
# The dotted-version requirement looks like an accident of that incident. It is not — it was
# re-derived by measurement (issue/accuracy/03, 2026-09-18). Every broadening tried against
# all 231 stored findings multiplied false flags without catching a single real graded error:
# single-number names ("Mythos 5", "DBR 18") flag as context on 6 of 6 findings, because
# established things are named with bare numbers and newly-versioned things with dotted ones;
# backticked terms without digits flag ~25 findings of SQL-keyword and common-word collisions
# ("FILE", "auto", "effort"); and checking the whole before corpus instead of cited pages
# would have flagged nine true launch findings at once, because one cookbook page mentioned
# Claude Fable 5.1 early. The graded errors these were meant to catch are out of reach on a
# different axis: finding 253 asserts contrast with no newness verb (issue/accuracy/04), and
# 252's "DENY" is invisible to every extractor measured (issue/accuracy/05's territory).
_VERSIONED_NAME = re.compile(
    r"\b[A-Z][A-Za-z]*(?:\s[A-Z][A-Za-z]*)?\s\d+(?:\.\d+)+(?:\s[A-Z][a-z]+)?\b")
_VERSIONED_ID = re.compile(r"\b[A-Za-z][A-Za-z]*-\d+(?:\.\d+)+\b")      # GLM-5.3
_BACKTICK = re.compile(r"`([^`\n]{3,60})`")
_HYPHEN_ID = re.compile(r"\b[a-z][a-z0-9]*(?:-[a-z0-9]+){2,}\b")
_SEPARATORS = re.compile(r"[\s._-]+")

# Cloud regions match _HYPHEN_ID and carry a digit, but a region in a headline is where
# something became available, not the thing that became available — "did this region exist
# before" can never answer the claim. Both standing false positives were this shape
# (finding 91: "…extended beyond us-east-1"; finding 192: "…rather than us-east-1 only"),
# and no true flag has ever been a region.
_REGION = re.compile(r"^(?:us|eu|ap|ca|sa|me|af|il|cn)(?:-gov)?-[a-z]+-\d$")

# A finding that says one of these is claiming something did not exist before.
_NEWNESS = re.compile(r"\b(new|add|added|adds|introduc\w*|launch\w*|now available|debut\w*)\b",
                      re.IGNORECASE)

# --- claims about the past (issue/accuracy/04) -----------------------------
#
# The graded runs' most common error is invented contrast: asserting what the old text
# said without checking. Term overlap cannot verify a paraphrase — measured on all
# stored findings, ~90% of its hits were the *new* side of rename claims and passive
# "was/were" noise — but a QUOTE carries direction and wording, and the model quotes
# often: `changed from "X" to "Y"`, `previously framed this as ("…")`. So exactly the
# quoted spans are verified: a from-/past-context quote must appear in the BEFORE text
# of the cited pages, a to-quote in the AFTER text. On the stored findings this flags
# two and only two claims, both genuine: finding 237's "support note" quote (which
# exists only on the NEW page) and finding 202's `"BASIC reports only"` (the old page
# says "The connector only supports ingestion of BASIC reports" — right substance,
# fabricated quotation). Known, accepted misses: falsity carried by a quantifier
# ("previously excluded only …", finding 158) and contrast asserted with no trigger at
# all (finding 253) — those need issue/accuracy/07's edited-line pairing, not this.
_PAST_CONTEXT = re.compile(
    r"\b(previously|used to|until (?:now|then)|formerly|earlier|was|were|had)\b",
    re.IGNORECASE)
# Verbs whose "to" introduces the new text ("renamed to", "changed to"); any other
# "to" before a quote is a preposition. From the phrasings in stored findings.
_RENAME_VERBS = frozenset(
    ["renamed", "changed", "moved", "switched", "retitled", "updated", "went",
     "rewritten", "rewrites"])
_QUOTE_SPAN = re.compile(r"[\"“]([^\"“”]{1,240})[\"”]")
_SENTENCES = re.compile(r"(?<=[.!?;])\s+")
_MARKUP = re.compile(r"[*_`\[\]()|>#\"“”]")


def _loose(text: str) -> str:
    """Case- and markup-insensitive form for matching quoted prose against a body.

    `_normalise` is for identifiers; a quoted sentence has to survive the body's links
    and emphasis — "client tools and the [advisor tool](url)" must contain
    "client tools and the advisor tool".
    """
    return re.sub(r"\s+", " ", _MARKUP.sub(" ", text.lower())).strip()


def quoted_claims(finding: Finding) -> tuple[list[str], list[str]]:
    """Quoted spans asserting text: `(about the old text, about the new text)`.

    A span right after "from" is the old text, right after "to" the new; any other
    quote in a past-context sentence is the old. Only spans of at least three words
    are claims — a single quoted token is emphasis, not quotation — and an elided
    quote ("For how X…") is an abbreviation by construction, unverifiable verbatim.
    """
    text = f"{finding.summary} {finding.detail or ''}"
    past: list[str] = []
    present: list[str] = []
    for sent in _SENTENCES.split(text):
        has_past = bool(_PAST_CONTEXT.search(sent))
        saw_from_quote = False
        for m in _QUOTE_SPAN.finditer(sent):
            quote = m.group(1).strip()
            if len(quote) < 12 or len(quote.split()) < 3 or "…" in quote or "..." in quote:
                continue
            words = sent[:m.start()].lower().split()
            last = words[-1] if words else ""
            prev = words[-2] if len(words) > 1 else ""
            if last in ("from", "(from"):
                past.append(quote)
                saw_from_quote = True
            elif last in ("to", "into") and (saw_from_quote or prev in _RENAME_VERBS):
                # Only a rename's to-side is a claim about the new text. A bare
                # preposition is not: real finding 199 writes `pages that linked to
                # "Enrich data using AI Functions"` — a true statement about the OLD
                # title, which the first version of this rule flagged as a misquote
                # of the new text.
                present.append(quote)
            elif has_past:
                past.append(quote)
    return past, present


@dataclass
class Evidence:
    """What the audit shows for one cited page."""

    url: str
    kind: str
    lines: list[tuple[str, str]] = field(default_factory=list)   # (sign, text)
    score: int = 0
    note: str = ""


@dataclass
class Audit:
    """One finding and everything needed to judge it."""

    finding: Finding
    evidence: list[Evidence] = field(default_factory=list)
    shown_pages: int = 0
    already_present: list[str] = field(default_factory=list)
    # The newness check needs before text, and a finding whose cited pages are all new
    # has none. That used to skip in silence — and a finding about a brand-new page is
    # precisely where a false "first time" claim is cheapest to make, so the reader must
    # be told the check could not run rather than left to assume it passed.
    newness_unverifiable: bool = False
    # Quoted assertions about the old or new text that the text does not contain —
    # (quote, found_on_the_other_side). See `quoted_claims`.
    misquoted_before: list[tuple[str, bool]] = field(default_factory=list)
    misquoted_after: list[tuple[str, bool]] = field(default_factory=list)


def claim_terms(finding: Finding) -> set[str]:
    text = f"{finding.summary} {finding.detail or ''}".lower()
    return {w for w in _WORD.findall(text) if w not in _STOP}


def identifiers(finding: Finding) -> set[str]:
    """Versioned names the finding's *headline* asserts something about.

    Summary only. The detail routinely mentions things that existed before as context —
    "previously documented only for us-east-1" — and checking those produced flags that were
    all noise on the first real run. The headline is where "X was added" lives.
    """
    text = finding.summary
    found = set(_VERSIONED_NAME.findall(text)) | set(_VERSIONED_ID.findall(text))
    found |= {m.strip() for m in _BACKTICK.findall(text)}
    found |= set(_HYPHEN_ID.findall(text.lower()))
    return {f for f in found
            if len(f) >= 4 and any(ch.isdigit() for ch in f) and not _REGION.fullmatch(f)}


def _normalise(text: str) -> str:
    """`Grok 4.6`, `grok-4-6` and `databricks-grok-4-6` must all match each other."""
    return _SEPARATORS.sub("-", text.lower())


def claims_newness(finding: Finding) -> bool:
    return bool(_NEWNESS.search(f"{finding.summary} {finding.detail or ''}"))


def _score(line: str, terms: set[str]) -> int:
    return len(terms & set(_WORD.findall(line.lower())))


def rank_lines(lines: list[tuple[str, str]], terms: set[str]) -> list[tuple[str, str]]:
    """Most claim-relevant first; status language breaks ties, then length.

    Taking lines in document or multiset order showed blank lines and `> **Note:**`
    boilerplate that could neither confirm nor refute anything.
    """
    real = [(sign, text) for sign, text in lines if text.strip()]
    return sorted(real, key=lambda pair: (-_score(pair[1], terms),
                                          0 if classify.STATUS.search(pair[1]) else 1,
                                          -len(pair[1])))


def audit_finding(finding: Finding, by_url: dict[str, PageChange], *, blob_dir=None,
                  pages: int = 3, lines: int = 4) -> Audit:
    """Gather the evidence for one finding, best-matching pages and lines first."""
    terms = claim_terms(finding)
    out = Audit(finding=finding)
    befores: list[str] = []
    afters: list[str] = []
    candidates: list[Evidence] = []

    seen_signatures: dict[tuple, str] = {}
    for url in finding.urls:
        change = by_url.get(url)
        if change is None:
            candidates.append(Evidence(url, "?", note="not in this diff"))
            continue
        if change.kind in ("added", "removed"):
            size = (change.current.get("body_chars") or 0)
            candidates.append(Evidence(url, change.kind, note=f"{change.kind} page — {size:,} chars"))
            continue
        before = blobs.read_or_none((change.before or {}).get("content_hash"), blob_dir)
        after = blobs.read_or_none((change.after or {}).get("content_hash"), blob_dir)
        if before is None or after is None:
            candidates.append(Evidence(url, change.kind, note="stored body unavailable"))
            continue
        befores.append(before)
        afters.append(after)
        removed, added = classify.changed_sides(before, after)
        # A mirror pair is one piece of evidence, not two. The Admin API republication
        # stamped one edit across up to 115 reference pages, and an audit that shows
        # the same changed lines twice lets one story count as two confirmations.
        signature = (tuple(sorted(removed)), tuple(sorted(added)))
        if (removed or added) and signature in seen_signatures:
            first = seen_signatures[signature].split("/en/")[-1]
            candidates.append(Evidence(url, change.kind,
                                       note=f"identical change to {first}"))
            continue
        seen_signatures[signature] = url
        ranked = rank_lines([("-", ln) for ln in removed] + [("+", ln) for ln in added], terms)
        candidates.append(Evidence(url, change.kind, lines=ranked[:lines],
                                   score=_score(" ".join(t for _, t in ranked[:lines]), terms)))

    # Pages whose changed lines best match the claim first. Pages with only a note (added,
    # removed) keep their place after the scored ones — they are evidence of existence only.
    candidates.sort(key=lambda e: (-e.score, bool(e.note)))
    out.evidence = candidates[:pages]
    out.shown_pages = len(out.evidence)

    # The mechanical check. Only meaningful when the finding claims something is new: a
    # deprecation will name things that existed before, correctly. A name must also survive
    # into the AFTER text: "now pins claude-opus-4-8 instead of claude-opus-4-1" names the old
    # one on purpose, and it is the thing that disappeared.
    past_quotes, present_quotes = quoted_claims(finding)
    if befores:
        if claims_newness(finding):
            old_text = _normalise("\n".join(befores))
            new_text = _normalise("\n".join(afters))
            out.already_present = sorted(i for i in identifiers(finding)
                                         if _normalise(i) in old_text and _normalise(i) in new_text)
        # The mirror check: a quoted assertion about the old text must be in the before
        # text, one about the new text in the after text. Whether the missing quote
        # appears on the *other* side is reported too — "quoted the new page as the old"
        # is the exact mistake of graded finding 237.
        old_loose = _loose("\n".join(befores))
        new_loose = _loose("\n".join(afters))
        out.misquoted_before = [(q, _loose(q) in new_loose) for q in past_quotes
                                if _loose(q) not in old_loose]
        out.misquoted_after = [(q, _loose(q) in old_loose) for q in present_quotes
                               if _loose(q) not in new_loose]
    elif claims_newness(finding) or past_quotes or present_quotes:
        out.newness_unverifiable = True
    return out


def draw(findings: list[Finding], n: int, seed: int) -> list[Finding]:
    """A seeded sample stratified by impact, so a re-draw gives the same findings."""
    by_impact = defaultdict(list)
    for f in findings:
        by_impact[f.impact].append(f)
    rng = random.Random(seed)
    drawn: list[Finding] = []
    for impact in IMPACTS:
        group = by_impact.get(impact, [])
        if group:
            quota = max(1, round(n * len(group) / len(findings)))
            drawn.extend(rng.sample(group, min(quota, len(group))))
    return drawn[:n]


def render(audit: Audit, index: int) -> str:
    f = audit.finding
    out = [f"\n{'=' * 78}\n{index}. [{f.impact}] {f.headline}"]
    if f.detail:
        out.append(f"\n   {' '.join(f.detail.split())[:500]}")
    cited = len(f.urls)
    head = f"\n   cites {cited} page(s); showing the {audit.shown_pages} that best match the claim"
    if cited > audit.shown_pages * 2:
        # Most of the claim's support is not on screen. Say so, rather than let a reader
        # judge a 25-page finding from three of its pages as if that were the whole case.
        head += f"  ! only {audit.shown_pages / cited:.0%} of the evidence is shown"
    out.append(head + ":")
    if audit.already_present:
        out.append("   ! claims something is new, but these already appeared in the BEFORE "
                   "text of its cited pages: " + ", ".join(audit.already_present[:8]))
    if audit.newness_unverifiable:
        out.append("   ! claims newness or contrast with the past, but no before text exists "
                   "for its cited pages (all new or unreadable) — the check could NOT run; "
                   "verify by hand")
    for quote, on_other_side in audit.misquoted_before[:4]:
        line = (f'   ! quotes the old text as saying "{quote[:120]}" — not found in the '
                f"BEFORE text of its cited pages")
        if on_other_side:
            line += " (it IS in the AFTER text: likely quoting the new page as the old)"
        out.append(line)
    for quote, on_other_side in audit.misquoted_after[:4]:
        line = (f'   ! quotes the new text as saying "{quote[:120]}" — not found in the '
                f"AFTER text of its cited pages")
        if on_other_side:
            line += " (it IS in the BEFORE text: likely quoting the old page as the new)"
        out.append(line)
    for ev in audit.evidence:
        out.append(f"\n   --- {ev.url.split('/en/')[-1]}")
        if ev.note:
            out.append(f"       ({ev.note})")
        for sign, text in ev.lines:
            out.append(f"       {sign} {text.strip()[:170]}")
    return "\n".join(out)
