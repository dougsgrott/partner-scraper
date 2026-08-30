# 03 — Re-diff #1 → #2 and evaluate

**Status:** done (2026-08-29) · **Kind:** evaluation · **Effort:** ~1 h
**Depends on:** [01](01-split-body-fingerprint.md), [02](02-rework-change-weighting.md)
**Blocks:** [05](05-decide-phase-2-architecture.md)

> **Revised.** Most of this issue was executed inside 01 and 02 — each fix was re-run
> against the real 1,116 diffs as it landed, because neither could be trusted otherwise.
> Two things in the original text were wrong and are corrected below. What genuinely
> remained was the preservation step, and that is now the point of this issue.

## Problem

Issues 01 and 02 were hypotheses. This project's record on that is unambiguous: every real
defect it has had was found by reading actual output, and a validator once needed six
corrections to the corpus's one (`docs/lessons-learned.md` §1, §11).

## Corrections to the original issue

**A synthetic change was listed as a real finding.** The original text asked to confirm
"the token-lifetime limit moving 730 → 1460 days" appears in the feed. That change is not
real — it was *injected* into a scratch copy of the corpus during the phase-1 end-to-end
test, to exercise the number-change path. It appears **zero** times in the real report, and
correctly so. Writing it into an issue as a known-good vendor change let a test fixture
contaminate a findings list; the check would have failed for the right reason and been
"fixed" for the wrong one.

**"Costs nothing" was wrong, then became right.** Re-diffing took ~10 minutes when this
issue was written, because `difflib` ran over every modification including 6 MB pages. Issue
02 moved ranking to a line-multiset difference and guarded rendering above 400,000
characters. It now takes **17 seconds**. The original claim was wrong when made and is true
now for a different reason than it assumed.

## What was checked

**1. Attribution moved from wrong to honest.**

| | before | after |
|---|---|---|
| `content` | 522 | **522** |
| `pipeline` | 594 — all false | **0** |
| `unknown` | 0 | **594** |

The 522 correct attributions were preserved by the superset rung added in 01: an *unchanged*
`output_fingerprint` proves the body pipeline did not move, while a *changed* one proves
nothing. Without it all 1,116 fell to `unknown` — which a first pass actually produced.

**2. The ranking became usable.** Over the 1,116 modifications, `substantive` went
1,084 → 1,021, `low` 29 → 92, `noise` 3 → 3. The share moved less than expected, which is
[02](02-rework-change-weighting.md)'s central finding: the corpus really does change that
heavily. The feed is now ordered by severity rather than alphabetically, which is the change
that made it readable.

**3. The top of the feed is right.** Read and confirmed:

| severity | change |
|---|---|
| 8.3 | `api/beta-headers` — `files-api-2025-04-14` → `context-management-2025-06-27` |
| 6.0 | `tool-use/tool-runner` — **Python dropped** from the runtimes with automatic compaction |
| 5.5 | `about-claude/model-deprecations` — the deprecations page itself |
| 5.3 | `build-with-claude/fast-mode` — availability |
| — | `foundation-model-overview` — a region's models change `databricks-gpt-5-5-pro` → `databricks-grok-4-6` |

**4. Nothing regressed.** Kind counts unchanged: 161 added, 1,116 modified, 49 moved,
8 metadata, 0 removed.

**5. The known false negative is visible, not hidden.**
`manage-claude/access-transparency` renames "Anthropic Workbench" to "Playground (Claude
Console)" with no signal any heuristic here can see. It ranks `low`, so its diff is not
expanded — but it appears in the report's *Ranked down* section as
``- `low` [Access Transparency](…) — prose only``. The rank-never-filter rule holds.

## The preservation step — what actually remained

**After 01, the tool no longer prints the churn number.** The 594 Databricks modifications
report as `unknown`, so the feed shows 161. The measured figure of 1,277 body changes rests
on evidence the tool cannot restate:

- reading a sample of the 594 diffs and finding unambiguous vendor content — new Genie Agent
  audit events, a budget-tracking behaviour change, a moved link target, a new section;
- `git show --stat 8b3f999`, confirming that commit touched only `registry.py` and one line
  of `writer.py`, neither of which can alter a page body.

Recorded in `docs/changefeed.md` under **Measured churn**, with that provenance stated, so
the most expensive measurement this project has made is not lost to a later reader who sees
only `unknown`.

## Verification

```bash
uv run python scripts/changes.py diff 1 2 --write     # ~17 s
head -40 reports/changefeed/0001..0002.md
```

Note this pair's feed is Anthropic-only: every Databricks modification is
`unknown`-attributed because both snapshots predate `body_fingerprint`. From snapshot #3
onward both vendors appear. That is a property of the historical pair, not a defect.
