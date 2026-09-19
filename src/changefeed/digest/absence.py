"""Restrictions the digest may have missed — the finding that was never written.

See issue/accuracy/05-missed-restrictions.md. The worst error class has no audit: a
restriction on something people already rely on, arriving inside a launch, produces no
finding to check. The type specimen is the Fable 5 retention sentence — added for the
*existing* model on a page announcing the new one, missed under both prompt versions.

The failure signature is mechanical, so the detector is deterministic: an **added** line
carrying restriction language, naming something that was **already in the page's before
text**. Presence-in-before is a *filter* here, not a flag — the inverse of the audit's
newness check — which is why the broad name classes rejected there (issue/accuracy/03)
are safe here.

Measured on the stored pairs (2026-09-19): ~117 deduplicated candidates per run on
~60 pages, of which ~50 sit on pages no finding cites; a read sample judged ~55-60%
restrictions worth a reader's attention, the rest troubleshooting prose and
reference-table semantics. The full RESTRICTION lexicon (adding `requires`, `must`,
`reject*`) raises that to 254-303 per run, mostly requirement boilerplate — so the scan
uses the loss-words subset below. One accepted candidate class: a restriction shipping
with a *new* version whose family already exists (the Fable **5.1** twin sentence
passes the subject test through "Claude Fable"); it costs about a line per launch and
sits next to the twin that matters.

This is option A of the issue — a net, not a fix: it runs after the digest and a person
reads it. Option B (injecting the candidates into the session prompt) is drafted in the
issue and gated on a graded A/B.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .. import blobs, classify
from ..diff import DiffResult
from . import audit
from .findings import Finding

# The loss-words subset of classify.RESTRICTION: something stops being possible,
# supported, or available. The requirement words (`requires`, `must`, `reject*`)
# measured at +137-186 candidates per run of mostly boilerplate ("Requires an OAuth
# access token…") and are deliberately excluded — counts in the issue file.
LEXICON = re.compile(
    r"\b(cannot|not (?:supported|available)|unsupported|unavailable|no longer"
    r"|deprecat\w*|removed|discontinu\w*)",
    re.IGNORECASE,
)

# Name-like spans a restriction sentence can be *about*. Broader than the audit's
# newness classes on purpose: "Claude Fable 5" and "Databricks Runtime" must count.
_CAPRUN = re.compile(r"\b[A-Z][A-Za-z0-9]*(?:\s[A-Z][A-Za-z0-9.]*)+\b")
_SINGLE_VERSION = re.compile(r"\b[A-Z][A-Za-z]*(?:\s[A-Z][A-Za-z]*)?\s\d+\b")


@dataclass
class Candidate:
    """One added restriction line naming something that existed before."""

    url: str
    line: str
    subjects: list[str]                  # the names found in the before text
    severity: float = 0.0                # the page's rank evidence, for ordering
    cited: bool | None = None            # None until judged against a finding set


def _subjects(line: str) -> set[str]:
    found = set(audit._BACKTICK.findall(line))
    found |= set(audit._VERSIONED_NAME.findall(line)) | set(audit._VERSIONED_ID.findall(line))
    found |= set(audit._HYPHEN_ID.findall(line.lower()))
    found |= set(_CAPRUN.findall(line)) | set(_SINGLE_VERSION.findall(line))
    # A sentence-initial article welds itself onto the name ("The Unity Catalog API")
    # and then never matches the before text, which names things without it.
    found |= {s.split(" ", 1)[1] for s in found
              if s.split(" ", 1)[0] in ("The", "A", "An") and " " in s}
    return {s.strip() for s in found if len(s.strip()) >= 4}


def scan(result: DiffResult, *, blob_dir=None) -> list[Candidate]:
    """Every added restriction line whose subject was already on the page.

    Deduplicated by whitespace-normalised text across the whole run: the #6 -> #7 pair
    carries one tool-safety sentence on ~290 API-reference mirrors, and a reader needs
    it once. Deterministic and model-free, so it can run on stored pairs.
    """
    seen: set[str] = set()
    out: list[Candidate] = []
    for change in result.changes:
        if change.kind != "modified" or change.cause != classify.CONTENT:
            continue
        before = blobs.read_or_none((change.before or {}).get("content_hash"), blob_dir)
        after = blobs.read_or_none((change.after or {}).get("content_hash"), blob_dir)
        if before is None or after is None:
            continue
        _, added = classify.changed_sides(before, after)
        norm_before = audit._normalise(before)
        for line in added:
            if not LEXICON.search(line):
                continue
            key = " ".join(line.split())
            if not key or key in seen:
                continue
            named = sorted(s for s in _subjects(line)
                           if audit._normalise(s) in norm_before)
            if not named:
                continue
            seen.add(key)
            out.append(Candidate(url=change.url, line=line.strip(), subjects=named,
                                 severity=change.severity))
    return out


def mark_cited(candidates: list[Candidate], findings: list[Finding]) -> None:
    """Say which candidates sit on a page some finding at least cites.

    Page-level only, and that is a known limit worth stating: the Fable 5 page *was*
    cited — by the finding that got its retention rule backwards — so "cited" means
    "a finding looked here", never "this line was reported".
    """
    cited_urls = {u.rstrip("/") for f in findings for u in f.urls}
    for c in candidates:
        c.cited = c.url.rstrip("/") in cited_urls


def injection(candidates: list[Candidate]) -> str:
    """The option-B appendix: the candidates, grouped per page, for the session prompt.

    Grouped by page (~60 groups) rather than one line each, per the issue: at ~100
    candidates a flat list invites rubber-stamping. The instruction asks for coverage,
    not for sixty justifications — a model forced to explain every non-restriction
    would pad the run with noise. This block only enters the prompt under
    `digest.py run --inject-restrictions`, and findings then carry `prompt_version`
    `+inj`, so the ledger keeps the arm separate.
    """
    if not candidates:
        return ""
    by_page: dict[str, list[Candidate]] = {}
    for c in candidates:
        by_page.setdefault(c.url, []).append(c)
    lines = [
        "",
        "---",
        "",
        "A deterministic scan found these ADDED lines that use restriction language and",
        "name something already present in the page's old text. They are candidates from",
        "a lexicon, not verdicts — some are troubleshooting prose or table semantics.",
        "Go through this list before you finish: any line that restricts something that",
        "already existed and is not covered by one of your findings deserves its own",
        "finding (rules 5 and 6). Do not duplicate findings you already recorded.",
        "",
    ]
    for url, group in sorted(by_page.items(), key=lambda kv: -max(c.severity for c in kv[1])):
        slug = url.split("/en/")[-1] if "/en/" in url else url
        lines.append(f"{slug}")
        for c in group:
            lines.append(f"    + {c.line[:200]}")
    return "\n".join(lines)


def render(candidates: list[Candidate], *, before: str, after: str,
           limit: int = 200) -> str:
    """Uncited pages first — where a miss is likeliest — then by page severity."""
    ordered = sorted(candidates,
                     key=lambda c: (c.cited is not False, -c.severity, c.url))
    uncited = sum(1 for c in candidates if c.cited is False)
    pages = len({c.url for c in candidates})
    out = [
        f"# Possible missed restrictions — {before} -> {after}",
        "",
        (f"{len(candidates)} added restriction line(s) naming things that existed "
         f"before, on {pages} page(s)"
         + (f"; {uncited} on pages no finding cites (shown first)"
            if any(c.cited is not None for c in candidates) else "")
         + f". Showing {min(limit, len(candidates))}."),
        ("A candidate is evidence, not a verdict: on the read sample ~55-60% were "
         "restrictions worth a reader's attention. 'cited' means a finding looked at "
         "the page, not that it reported the line."),
    ]
    for c in ordered[:limit]:
        slug = c.url.split("/en/")[-1] if "/en/" in c.url else c.url
        tag = {False: "UNCITED", True: "cited  ", None: "       "}[c.cited]
        out.append(f"\n{tag} sev {c.severity:>4.1f}  {slug}")
        out.append(f"    + {c.line[:220]}")
        out.append(f"      names: {', '.join(c.subjects[:5])}")
    if len(candidates) > limit:
        out.append(f"\n…and {len(candidates) - limit} more — raise --limit to see them.")
    return "\n".join(out)
