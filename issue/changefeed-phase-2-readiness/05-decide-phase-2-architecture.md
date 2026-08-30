# 05 — Decide the phase-2 architecture

**Status:** done (2026-08-29) · **Kind:** decision record · **Effort:** ~2 h
**Depends on:** [03](03-rediff-and-evaluate.md) · **Blocks:** building phase 2

> **Decided.** The record is [`docs/changefeed-phase-2.md`](../../docs/changefeed-phase-2.md).
> **None of the three options below was chosen**, and [04](04-quiet-week-measurement.md)
> turned out not to block the decision — see [Outcome](#outcome).

## Problem

Phase 2 is the Claude Agent SDK layer: semantic summaries of what changed, impact
classification, and a digest a person actually reads. It was deliberately not built,
because its shape depends on how many changes reach it per run — a number that did not
exist until phase 1 produced it.

That number now exists, and it rules one option out immediately:

**~813 body changes per week** (1,277 in 11 days). One agent session per changed page is
1,277 sessions per run. Dead on arrival — not only on cost, but because 1,277 independent
paragraphs cannot see that six of them describe one deprecation.

Batching at ~25 pages per session is ~51 sessions, which is affordable. But it would emit a
report with over a thousand entries, and **nobody reads that.** So:

> The binding constraint is **reduction**, not cost.

And reduction is the deterministic layer's job — the layer that, before
[02](02-rework-change-weighting.md), ranked 97.1% of changes as worth reading. That is why
this decision waits on 03: the volume that actually reaches a model is unknown until the
ranking works.

## What to decide

Write a decision record naming the post-fix volume, then choose among:

**A. Batched triage.** One session per ~25 substantive changes, batched by company and
category so a themed rollout lands in one session rather than scattered across four. Gives
cross-page synthesis; depth is rationed.

**B. Two-pass.** A cheap classification pass drops editorial changes, then a deep agent
session runs only on survivors. Better cost/quality at volume; introduces a silent
false-negative path, which needs a standing sampling audit to trust.

**C. Deterministic clustering first.** Group related changes with no model at all — a shared
before/after substitution across many pages, a common path move, a shared new section
heading — then hand the model one item per cluster.

### Evidence already gathered on C

C looked compelling when the Anthropic URL restructure appeared to explain the 98% churn.
**It does not.** Only 9 of 523 modified Anthropic pages (2%) changed *purely* by link
rewriting, and the largest single path move touched 29 pages:

```
/docs/en/about-claude/models -> /docs/en/models            x29
/docs/en/about-claude/models -> /docs/en/models/opus-5     x16
/docs/en/about-claude/models -> /docs/en/models/sonnet-5   x12
/docs/en/about-claude/models -> /docs/en/models/fable-5    x11
/docs/en/api/beta/files      -> /docs/en/api/files          x4
```

So mechanical clustering collapses maybe 70-80 of 1,277 changes. Real, worth having, and
far less than it first promised. Record this so the option is not re-litigated on the
intuition that "surely most of it is one event."

A and C are complementary rather than exclusive: clustering is a pre-pass, batched triage is
what consumes the result.

## Inputs required before deciding

| input | from |
|---|---|
| substantive changes per run, post-ranking | [03](03-rediff-and-evaluate.md) |
| Anthropic steady-state vs launch-week rate | [04](04-quiet-week-measurement.md) |
| whether ranking recall holds at >= 0.95 | [02](02-rework-change-weighting.md) |

If the post-fix substantive count lands in the low hundreds per week, A alone is likely
enough. If it stays near a thousand, B or C becomes necessary rather than optional.

## Agent SDK facts already established

Recorded here so they are not re-derived:

- The package is **`claude-agent-sdk`** (Python), a different product from the Anthropic API
  SDK. The bundled `claude-api` skill explicitly does not cover it; its docs are at
  `code.claude.com/docs/en/agent-sdk`.
- It **authenticates through the installed Claude Code CLI** (v2.1.251 here), so no
  `ANTHROPIC_API_KEY` is needed — relevant, because none is set in this environment.
- Custom tools go through `@tool` + `create_sdk_mcp_server`, running in-process. Tool names
  reach the model as `mcp__{server}__{tool}`.
- **Have the agent report through a tool call, not prose.** A `record_finding(url, impact,
  kind, summary)` tool writes structured rows, so the report stays deterministically
  rendered and re-renderable without re-running the model. Note the Python `@tool` decorator
  forwards only `content` and `is_error` — `structuredContent` is TypeScript-only — so the
  tool handler must do the writing itself.
- The tools are plain async functions returning dicts, so **the tool layer is testable with
  no model involved.**
- `ClaudeAgentOptions` supports `max_budget_usd` and `max_turns` per session, and
  `setting_sources=[]` keeps the app from inheriting local Claude Code settings.
- `reports/changefeed/*.json` is already the intended input: it carries every change with
  nothing ranked away.

## Acceptance criteria

- [ ] A decision record in `docs/` naming the chosen architecture and the volume figure it
      rests on.
- [ ] The rejected options recorded with their reasons, so they are not revisited on
      intuition.
- [ ] If B is chosen, the sampling audit for pass-1 false negatives is specified as part of
      the design, not deferred.
- [ ] A cost estimate per run, derived from the measured volume rather than assumed.

---

## Outcome

**Chosen: deterministic compression, then one synthesis session.** Not A, B or C.

One measurement decided it. All three options exist to process a run piecemeal, because a run
was assumed too large for the model to see at once:

| representation | size |
|---|---|
| every diff sent whole | 6.1M tokens · ~$30/run |
| **each change compressed to one line** | **92k tokens · ~$0.50/run** |

**The whole run fits in one context window.** A, B and C were solving a problem that does not
exist, and each pays for it: A's 25-item batches cannot see that 452 of 1,182 changes are one
API-reference regeneration; B adds a silent false-negative path for no benefit; C collapses
only ~5% of a run (measured directly: 87 pages in 24 exact-duplicate groups, largest 15).

**This issue's own decision rule was falsified.** It said "if it stays near a thousand, B or C
becomes necessary rather than optional." It stayed near a thousand — 1,182 per run — and
neither is necessary. The rule assumed volume forces piecemeal processing; compression breaks
that link.

**Severity ranking cannot substitute for synthesis either.** The distribution is flat — the
top 25 carries 8.4% of total severity, the top 100 carries 26.6% — so there is no small head
to truncate to.

**04 stopped being a blocker.** The design is volume-insensitive across the plausible range:
a quiet Anthropic week gives ~450 changes (~35k tokens), a launch week twice the observed one
gives ~2,400 (~185k). Both are one session. The steady-state number is still worth having,
but the architecture does not hinge on it.

### Acceptance criteria

- [x] A decision record in `docs/` naming the architecture and the volume it rests on
- [x] The rejected options recorded with their reasons
- [x] B's sampling audit — not applicable, B rejected
- [x] A cost estimate derived from measured volume, not assumed

### Carried forward into the build

The real risk is **synthesis recall over a long flat list**, not cost or context limits. Six
changes already verified by reading are named in the decision record as a seeded recall test,
with a hierarchical reduce over the 26 categories carrying ≥10 changes as the fallback — to
be built only if measurement shows it is needed.
