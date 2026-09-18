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
from .findings import Finding, supersede
from .tools import ALLOWED, DigestContext, build_server

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5"

# Bump whenever PROMPT changes. Findings carry it, so a later reader can tell whether two
# runs are comparable — a reworded prompt changes the output and nothing else records it.
PROMPT_VERSION = "2"
# v2 (2026-09-18): the #5 -> #6 audit found four partly-true findings and one buried breaking
# change, all from the same cause — claims going beyond what the page says. Rules 2, 4, 5 and 6
# below each answer one observed failure; see docs/changefeed-phase-2.md.

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

Aim for the number of findings the run actually contains — perhaps 15 to 40 for a busy
week. Do not pad to a target, and do not stop early because the list is long.

Work in one pass: read the list, check the handful you are unsure of with `get_diff`, then
record everything in as few `record_findings` calls as you can. When you are done, reply
with a one-line count and stop.

{run}"""


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
) -> DigestResult:
    """Run one digest session over a whole diff."""
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    run = compress_run(result, blob_dir=blob_dir)
    logger.info("digest input: %d changes, ~%dk tokens",
                len(run.records), run.approx_tokens // 1000)

    if replace:
        # A re-run replaces rather than accumulates: two sessions over one pair should not
        # leave a report that says everything twice.
        retired = supersede(db, result.before.id, result.after.id)
        if retired:
            logger.info("superseded %d previous finding(s) for this pair", retired)

    ctx = DigestContext(result=result, db=db, blob_dir=blob_dir, data_root=data_root,
                        model=model, prompt_version=PROMPT_VERSION)
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
    try:
        async for message in query(prompt=PROMPT.format(run=run.render()), options=options):
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
    return out
