"""Compress a run of changes into something one model call can read whole.

This is the step that decided the phase-2 architecture. Sending every diff in full is 6.1M
tokens for a typical run; compressing each change to a single line is **92k**, which fits
one context window with room to spare. The three obvious alternatives — batched triage, a
cheap pre-filter, deterministic clustering — all exist to work around a limit that this
removes (`docs/changefeed-phase-2.md`).

**Nothing is dropped.** Every change in the run appears, because a digest that silently
omits things cannot be audited and the reader has no way to notice. What varies is
verbosity: a substantive change gets its evidence and an excerpt, while a page that merely
moved file gets one line. Low-value entries cost ~60 characters instead of ~270, which is
how the no-filter promise is kept affordable.

The excerpt is chosen, not truncated at random: lines carrying status and policy language
come first, because reading a stratified sample showed those are what separate "this
property is no longer supported" from a paragraph being reworded.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .. import blobs, classify
from ..classify import PIPELINE, UNKNOWN
from ..diff import ADDED, METADATA, MOVED, REMOVED, DiffResult, PageChange

# Per-change excerpt budget. Two lines at 140 characters each: enough to carry a sentence
# that says what changed, short enough that 1,200 of them stay inside one context window.
EXCERPT_BUDGET = 280
EXCERPT_LINE = 140
EXCERPT_LINES = 2

# Kinds that get the short form. They are real changes and are still listed — a reader
# should see that 49 pages moved — but a moved file has no prose worth quoting.
TERSE_KINDS = (MOVED, METADATA)

# Rough, and labelled as rough. Used only to warn when a run approaches a context limit;
# nothing branches on it. Counting properly needs the API, and this does not justify a call.
CHARS_PER_TOKEN = 3.5

# Signals shown in a record, strongest first, matching the report's ordering.
_SIGNAL_ORDER = ("status", "code", "headings", "numbers", "links")


@dataclass(frozen=True)
class CompressedChange:
    """One change, small enough that a thousand of them fit in a prompt."""

    url: str
    company: str
    category: str
    kind: str
    title: str
    cause: str = ""
    severity: float = 0.0
    signals: dict = field(default_factory=dict)
    excerpt: str = ""

    @property
    def slug(self) -> str:
        """The path after the locale segment — the identity, minus the boilerplate.

        Full URLs are ~55 characters of near-identical prefix across a thousand records.
        The agent gets the whole URL back from any tool call it makes.
        """
        for marker in ("/en/", "/docs/", "://"):
            if marker in self.url:
                return self.url.split(marker, 1)[1]
        return self.url

    def render(self) -> str:
        head = f"{self.company}/{self.category} {self.kind.upper()} {self.slug}"
        if self.kind in TERSE_KINDS:
            return head
        sig = ",".join(f"{name[0]}{self.signals[name]}"
                       for name in _SIGNAL_ORDER if self.signals.get(name))
        parts = [head]
        if self.severity:
            parts.append(f"sev{self.severity:.1f}")
        if sig:
            parts.append(f"[{sig}]")
        # Only `unknown` is marked. `content` is the overwhelming majority and labelling
        # it would cost a thousand redundant tokens; `pipeline` never reaches the prompt.
        if self.cause == UNKNOWN:
            parts.append("(unattributed)")
        line = " ".join(parts)
        return f"{line} :: {self.excerpt}" if self.excerpt else line


@dataclass
class CompressedRun:
    """A whole run, ready to be handed to one session."""

    before: str
    after: str
    records: list[CompressedChange] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    # Changes withheld because our own extractor produced them. Counted, never hidden.
    excluded_pipeline: int = 0

    def render(self) -> str:
        return "\n".join([self.header(), "", *(r.render() for r in self.records)])

    def header(self) -> str:
        """Orientation for the reader: what window this is, and what is in it.

        Given before the records because a model reading a thousand near-identical lines
        benefits from knowing the shape of the set first.
        """
        tally = "  ".join(f"{kind} {n}" for kind, n in self.counts.items() if n)
        lines = [
            f"# Documentation changes, {self.before} -> {self.after}",
            f"# {len(self.records)} changes: {tally}",
            ("# One line per change: company/category KIND path sev<severity> "
             "[signal counts] :: changed lines"),
            "# Signals: s=status/policy language, c=code, h=headings, n=numbers, l=links.",
        ]
        if self.excluded_pipeline:
            lines.append(
                f"# {self.excluded_pipeline} further changes are excluded: our own "
                "extractor produced them, so they are not vendor news.")
        lines.append(
            "# A change marked (unattributed) may or may not be the vendor's — describe "
            "it cautiously and do not assert intent.")
        return "\n".join(lines)

    @property
    def chars(self) -> int:
        return len(self.render())

    @property
    def approx_tokens(self) -> int:
        """A rough estimate — see `CHARS_PER_TOKEN`. For a size warning, not a decision."""
        return int(self.chars / CHARS_PER_TOKEN)


def _clip(line: str, *, boost: bool) -> str:
    """One excerpt line, head-truncated — unless it carries restriction language.

    Head truncation buried the one sentence that mattered most: on the Fable 5 retention
    lines, `cannot` sits at character 140 and 142 of the line, and `EXCERPT_LINE` is 140 —
    the cut landed on the word itself, so the prompt showed a harmless retention preamble
    (issue/accuracy/02). With the boost on, a line matching RESTRICTION is windowed from
    the start of the sentence containing the match instead of from the head.
    """
    line = line.strip()
    if boost:
        m = classify.RESTRICTION.search(line)
        if m and m.start() >= EXCERPT_LINE - 40:
            # Rewind to the start of the match's sentence, but never so far that the
            # match falls off the end of the window again — the first draft allowed a
            # 200-character rewind into a 140-character window, which re-hid the clause
            # it existed to show.
            cut = line.rfind(". ", 0, m.start())
            start = cut + 2 if cut != -1 and m.start() - (cut + 2) <= EXCERPT_LINE - 40 \
                else max(0, m.start() - 60)
            return "…" + line[start:start + EXCERPT_LINE - 1]
    return line[:EXCERPT_LINE]


def _excerpt(change: PageChange, blob_dir=None, *, boost_restrictions: bool = False) -> str:
    """The most informative changed lines, status language first.

    `boost_restrictions` is the issue/accuracy/02 experiment, off by default because it
    changes what the model reads (docs/accuracy-plan.md: one graded A/B on a stored pair
    before any such change becomes the default). On, restriction language outranks other
    status language and matched clauses survive truncation — measured on the graded
    pages: it pairs the old and new versions of the create-policy sentence that finding
    253 misread as new, and it puts the retention clause on screen where head truncation
    had cut it at the word `cannot`.
    """
    before = blobs.read_or_none((change.before or {}).get("content_hash"), blob_dir)
    after = blobs.read_or_none((change.after or {}).get("content_hash"), blob_dir)
    if before is None or after is None:
        return "<stored body unavailable>"

    removed, added = classify.changed_sides(before, after)
    # Marked, because direction carries the meaning: "the TypeScript and Ruby tool runners
    # support compaction" says Python was dropped only if you know it is the *new* line.
    lines = [("-", line) for line in removed] + [("+", line) for line in added]
    # Status first, then longest: a long line carries more of what changed than a short
    # one, and the alternative — document order — is arbitrary with respect to importance.
    if boost_restrictions:
        lines.sort(key=lambda pair: (0 if classify.RESTRICTION.search(pair[1])
                                     else (1 if classify.STATUS.search(pair[1]) else 2),
                                     -len(pair[1])))
    else:
        lines.sort(key=lambda pair: (0 if classify.STATUS.search(pair[1]) else 1, -len(pair[1])))
    joined = " | ".join(f"{sign}{_clip(line, boost=boost_restrictions)}"
                        for sign, line in lines[:EXCERPT_LINES])
    return joined[:EXCERPT_BUDGET]


def compress(change: PageChange, *, blob_dir=None,
             boost_restrictions: bool = False) -> CompressedChange:
    """One change as a single record."""
    excerpt = ""
    if change.kind not in TERSE_KINDS:
        if change.kind in (ADDED, REMOVED):
            excerpt = (change.current.get("description") or "")[:EXCERPT_BUDGET]
        else:
            excerpt = _excerpt(change, blob_dir, boost_restrictions=boost_restrictions)

    return CompressedChange(
        url=change.url,
        company=change.company,
        category=change.category,
        kind=change.kind,
        title=change.title,
        cause=change.cause,
        severity=change.severity,
        signals={k: v for k, v in (change.signals or {}).items() if k in _SIGNAL_ORDER},
        excerpt=excerpt,
    )


def compress_run(result: DiffResult, *, blob_dir=None,
                 boost_restrictions: bool = False) -> CompressedRun:
    """Compress every change in a diff, most urgent first.

    Ordered by severity for the same reason the report is: a model reading a long flat
    list benefits from the sharpest evidence arriving early, and it makes the truncation
    that a future context limit might force cut from the least important end.
    """
    # `pipeline` changes are ours, not the vendor's, and a digest that reports them is
    # exactly the failure the attribution work in the change feed exists to prevent. They
    # are withheld from the prompt and counted in the header, never silently dropped.
    eligible = [c for c in result.changes if c.cause != PIPELINE]
    excluded = len(result.changes) - len(eligible)

    records = [compress(c, blob_dir=blob_dir, boost_restrictions=boost_restrictions)
               for c in sorted(eligible, key=lambda c: (-c.severity, c.company, c.url))]
    return CompressedRun(
        before=result.before.name,
        after=result.after.name,
        records=records,
        counts={k: sum(1 for c in eligible if c.kind == k) for k in result.counts()},
        excluded_pipeline=excluded,
    )
