"""The one session that turns a run of changes into a digest.

See `docs/changefeed-phase-2.md`. One session, not a batch per 25 changes and not a
pre-filter: a whole run compresses to ~105k tokens, so the model can see all of it at once
and write about what connects across pages. That is the capability batching would have
destroyed.

This module is the only one in the package that touches `claude-agent-sdk`, and it imports
it inside the function, so `import changefeed` keeps working without the optional
dependency.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from ..db import ChangeDB
from ..diff import DiffResult
from .compress import compress_run
from .findings import Finding, shelve_new, supersede
from .tools import ALLOWED, DigestContext, build_server

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5"

# Bump whenever the model's INPUT changes — the prompt text or the default rendering of
# the run it reads. Findings carry it, so a later reader can tell whether two runs are
# comparable — a changed input changes the output and nothing else records it.
PROMPT_VERSION = "4"
# v4 (2026-09-20, issue/accuracy/06): **the v3 prompt TEXT, unchanged, plus terse-kind
# collapse as the default input rendering** — `compress_run(collapse_terse=True)` groups
# `moved`/`metadata` one-liners into counted TerseGroup header lines, with `list_changes`
# keeping every collapsed record enumerable (nothing is dropped). Adopted on one graded
# arm ("3+c" on #6 -> #7): 16/2/0 = 89% full-page — the pair's best — at -55% input
# tokens and -19% cost, 72 findings vs the baseline's 79, zero invented-past claims, and
# a verbatim-true past-claim (finding 863) produced by plain two-sided visibility. One
# pair, one arm is the standing caveat; the volume-recall question it answers is issue
# 06's. Explicitly NOT part of v4: revision marking (+p — its second-pair confirm graded
# 72%, candidacy declined, issue/accuracy/07), duplicate merging (+m, built, ungraded),
# and everything v3 already excluded. A run with collapse explicitly disabled records
# "4-c"; boost disabled still records "-r".
# v3 (2026-09-19, issue/accuracy/13): **the v2 prompt TEXT, unchanged, plus
# restriction-boosted input as the default** — `compress._excerpt`'s restriction-first,
# clause-windowed excerpts (issue/accuracy/02). Adopted on two graded confirms: 10/10 vs
# 7/10 on #5 -> #6, then 17/1 vs 15/4 at n=18 on #6 -> #7, with the graded error clusters
# resolving both times. CLASSIFY_VERSION moved 1 -> 2 in the same change, so both stamps
# agree on what changed. Explicitly NOT part of v3: the declined rule-10 quote draft
# (QUOTE_RULE below — issue/accuracy/04 graded it and did not adopt it), the injection
# appendix, revision marking (+p), and adaptive slots (+e) — each remains a flagged arm.
# A run with the boost explicitly disabled records "3-r".
# v2 (2026-09-18): the #5 -> #6 audit found four partly-true findings and one buried breaking
# change, all from the same cause — claims going beyond what the page says. Rules 2, 4, 5 and 6
# each answer one observed failure; see docs/changefeed-phase-2.md.

# Enough turns to read a few diffs and record a few dozen findings; low enough that a loop
# cannot run away. A session that hits this has usually misunderstood the task.
MAX_TURNS = 120

PROMPT = """You are writing this week's documentation change digest for engineers who build
on Anthropic's and Databricks' platforms.

Below is EVERY change in this run, one line each, ordered by a heuristic severity score:

    company/category KIND path sev<score> [signal counts] :: changed lines

In the excerpt, `-` is a line that was removed and `+` one that was added. Direction
matters: "the TypeScript and Ruby runners support compaction" means Python was *dropped*
only if it is the `+` line.

Your job is to tell a reader what actually happened, not to summarise every line.

Record findings with `record_findings`, which takes a LIST. **Send them in batches of ten
or more, not one per call.** Every tool call re-sends this whole list to you and is the main
cost of the run; twenty separate calls cost several times what two do.

Rules that matter:

1. **A finding is one story — no fewer pages, no more stories.** If twenty pages changed
   because one thing happened, that is ONE finding citing all twenty in `urls`. The
   converse matters as much: if a summary needs "and" to join changes with different
   causes, it is two findings. A finding that bundles a new tutorial, a version floor and a
   renamed product cannot be acted on and cannot be checked.
2. **Say only what the page says.** Do not state a consequence the text does not state —
   an error code, a fallback, a broken link, a migration someone must do. If a page says
   "not supported on X", write that; do not write that requests to X will fail, fall back,
   or return 400 unless the page says so. A plausible inference presented as fact is the
   most common way this digest has been wrong.
3. **Check before you write.** The excerpt is 280 characters and often not enough. Call
   `get_diff` on anything you intend to describe and are not certain about.
   `inbound_links` tells you how much of the corpus depends on a page.
4. **"New" means absent before.** Before calling a model, feature, field or option new,
   check that it does not appear anywhere in the old text — `get_diff` shows both sides. A
   name on a `+` line is not new if it is also on a `-` line: tables are often rewritten
   whole, so an existing entry reappears among the "added" lines. Likewise say something was removed only if the
   change is marked REMOVED or the text says so; a page whose links were repointed has not
   been deleted.
5. **`impact` has a precise meaning.**
   - `breaking`: something that worked before stops working, or now needs action to keep
     working — a capability removed, a **new restriction on something that already exists**,
     a version floor imposed on existing usage, a changed default.
   - Not breaking: a feature reaching GA, a new model that a feature does not support (it
     never did), a new option.
   A GA transition is `behavioural` or `additive`, never `breaking`.
6. **Look for restrictions hidden inside additions.** A page that mostly announces new
   models or features can also quietly restrict an existing one. Those are the changes a
   reader most needs and the easiest to miss, because the page reads as good news. Record
   them as their own `breaking` finding, not as a clause inside the announcement.
7. **Cite only paths from the list.** A finding about a page that did not change is worse
   than a missing finding. Paths are validated and invalid ones are rejected.
8. **Some changes are marked `(unattributed)`.** Our own pipeline may or may not have
   produced those. Report them if they look important, but describe what the text now says
   rather than asserting the vendor changed it deliberately.
9. **Say bulk regeneration once.** Large parts of a run can be an API reference being
   regenerated — schema shapes, casing, field-list collapsing. Record that as a single
   `editorial` finding rather than ignoring it or itemising it.
{extra_rules}
Aim for the number of findings the run actually contains — perhaps 15 to 40 for a busy
week. Do not pad to a target, and do not stop early because the list is long.

Work in one pass: read the list, check the handful you are unsure of with `get_diff`, then
record everything in as few `record_findings` calls as you can. When you are done, reply
with a one-line count and stop.

{run}"""

# Issue/accuracy/04 option B, an A/B arm until graded: converts the model's most common
# error (asserting what the old text said, unchecked) into a checkable citation. The
# audit verifies quoted past-claims verbatim (`audit.quoted_claims`), so every quote
# this rule induces lands in a verifier whose measured precision is 2/2.
QUOTE_RULE = """
10. **When you assert what the old text said or lacked** ("previously …", "was …",
    "renamed from …"), quote the exact old line or phrase in double quotes, or write
    "absent before". Quoted text is verified verbatim against the stored before text;
    a paraphrase inside quotation marks counts as a fabrication.
"""

# Issue/accuracy/07, the marking arm's legend. Numbered 10 like QUOTE_RULE: arms are one
# input change each, so the two rules never ride in the same prompt.
MARK_RULE = """
10. **A `~` sign marks a revised line.** `~-`/`~+` mean a close variant of this line
    exists on the other side of the diff: the line was EDITED, not added or removed
    whole. A name on a `~+` line is not new just for being there — but something in
    that line did change; `get_diff` shows the pair. An unmarked `+` line has no close
    variant before, and an unmarked `-` line none after.
"""


@dataclass
class DigestResult:
    """What a session produced."""

    before: int
    after: int
    changes: int
    findings: list[Finding] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    calls: dict = field(default_factory=dict)
    cost_usd: float | None = None
    turns: int = 0
    stopped: str | None = None

    def render(self) -> str:
        lines = [
            f"digest #{self.before} -> #{self.after}",
            f"  changes          {self.changes:,}",
            f"  findings         {len(self.findings)}",
            f"  pages cited      {len({u for f in self.findings for u in f.urls})}",
        ]
        if self.rejected:
            lines.append(f"  rejected urls    {len(self.rejected)}  "
                         f"(cited pages that did not change; the model was told)")
            # Samples, not just a count. A bare "69 rejected" was read as the model
            # inventing pages and was in fact a resolver bug — see DigestContext.find.
            for url in self.rejected[:5]:
                lines.append(f"    ! {url}")
        recorded = self.calls.get("findings recorded", 0)
        batches = self.calls.get("batch calls", 0)
        if recorded:
            per_call = recorded / max(batches or self.calls.get("record calls", 1), 1)
            lines.append(f"  findings per call {per_call:.1f}"
                         + ("  ! batching regressed — see docs/changefeed-phase-2.md"
                            if per_call < 3 else ""))
        if self.cost_usd is not None:
            lines.append(f"  cost             ${self.cost_usd:.2f}")
        if self.stopped:
            lines.append(f"  stopped          {self.stopped}")
        return "\n".join(lines)


async def run_digest(
    result: DiffResult,
    *,
    db: ChangeDB,
    blob_dir: str | None = None,
    data_root: str | None = None,
    model: str = MODEL,
    max_turns: int = MAX_TURNS,
    max_budget_usd: float | None = None,
    replace: bool = True,
    boost_restrictions: bool = True,
    quote_evidence: bool = False,
    inject_restrictions: bool = False,
    collapse_terse: bool = True,
    merge_duplicates: bool = False,
    mark_revisions: bool = False,
    adaptive_slots: bool = False,
) -> DigestResult:
    """Run one digest session over a whole diff.

    The three flags are A/B arms (issues 02, 04 and 05), off by default until each is
    graded. Every one changes what the model reads, so findings record
    `prompt_version` with a matching suffix (`+r`, `+q`, `+inj`) — the ledger of
    issue/accuracy/01 must never pool arms as one prompt.
    """
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    run = compress_run(result, blob_dir=blob_dir, boost_restrictions=boost_restrictions,
                       collapse_terse=collapse_terse, merge_duplicates=merge_duplicates,
                       mark_revisions=mark_revisions, adaptive_slots=adaptive_slots)
    logger.info("digest input: %d changes, ~%dk tokens",
                len(run.records), run.approx_tokens // 1000)

    appendix = ""
    if inject_restrictions:
        from . import absence

        candidates = absence.scan(result, blob_dir=blob_dir)
        appendix = absence.injection(candidates)
        logger.info("injecting %d restriction candidates", len(candidates))

    if replace:
        # A re-run replaces rather than accumulates: two sessions over one pair should not
        # leave a report that says everything twice.
        retired = supersede(db, result.before.id, result.after.id)
        if retired:
            logger.info("superseded %d previous finding(s) for this pair", retired)
    # `replace=False` is an experiment arm: the current set stays untouched, and this
    # run's rows are shelved at birth (after the loop, below) — never pooled with it.
    floor_id = db.conn.execute("SELECT COALESCE(MAX(id), 0) FROM findings").fetchone()[0]

    # v4 includes the boost and the collapse; disabling either is the marked deviation.
    version = (PROMPT_VERSION + ("" if boost_restrictions else "-r")
               + ("" if collapse_terse else "-c")
               + ("+q" if quote_evidence else "")
               + ("+inj" if inject_restrictions else "")
               + ("+m" if merge_duplicates else "")
               + ("+p" if mark_revisions else "")
               + ("+e" if adaptive_slots else ""))
    ctx = DigestContext(result=result, db=db, blob_dir=blob_dir, data_root=data_root,
                        model=model, prompt_version=version,
                        mark_revisions=mark_revisions)
    options = ClaudeAgentOptions(
        model=model,
        mcp_servers={"digest": build_server(ctx)},
        allowed_tools=ALLOWED,
        # No built-in tools: everything this session may touch is a corpus tool above, and
        # a digest has no business reading the filesystem or the web.
        tools=[],
        setting_sources=[],
        max_turns=max_turns,
        **({"max_budget_usd": max_budget_usd} if max_budget_usd else {}),
    )

    out = DigestResult(before=result.before.id, after=result.after.id,
                       changes=len(run.records))
    extra = QUOTE_RULE if quote_evidence else (MARK_RULE if mark_revisions else "")
    prompt = PROMPT.format(run=run.render(), extra_rules=extra) + appendix
    try:
        async for message in query(prompt=prompt, options=options):
            out.turns += 1
            if isinstance(message, ResultMessage):
                out.cost_usd = message.total_cost_usd
                out.stopped = getattr(message, "terminal_reason", None)
    except Exception as exc:                      # noqa: BLE001 — see below
        # A budget or turn cap is an expected way for a session to end, not a failure.
        # Findings are written as each tool call lands, so whatever the model recorded
        # before stopping is already durable; raising here would throw away real work and
        # report nothing. The reason is surfaced instead.
        out.stopped = str(exc)
        logger.warning("digest session ended early: %s", exc)

    out.findings = ctx.recorded
    out.rejected = ctx.rejected
    out.calls = dict(ctx.calls)
    if not replace:
        shelved, stamp = shelve_new(db, result.before.id, result.after.id,
                                    above_id=floor_id)
        logger.info("shelved %d arm finding(s) as %s under stamp %s — promote with "
                    "`digest.py promote`", shelved, version, stamp)
    return out
