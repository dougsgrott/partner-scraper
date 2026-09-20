# 08 — Severity density and the one-line change

**Status:** done (2026-09-19), uncommitted — **option D, decided by measurement**: the
graded ledger shows the "one-line clutter" and the graded-true material are the same
population, so A and B would bury what the digest verifiably gets right. No formula
change; the rejection numbers are recorded here and in a guard comment on
`classify.severity`. See *Measured* and *Decision* · **Kind:** decision
**Effort:** ~2 h once the graded data exists
**Depends on:** [01](01-verdict-ledger.md) (done), [02](02-restriction-lexicon.md)
(done — its measurement is now an *input* here, see the revision note)

> **Revised 2026-09-19.** Issue [02](02-restriction-lexicon.md)'s measurement handed
> this issue its sharpest input: the density pathology has **two ends, and they are the
> same formula**. One-line changes saturate to the cap (63 of the top 100 at ≤100
> characters), while a 62-line page with five restriction lines is capped at a few
> tenths of severity — rank ~500 *no matter which words fire*. That second end is why
> the lexicon extension could not deliver its own motivating case and was rejected at
> the ranking layer. Any option evaluated here must be scored against **both** ends,
> and 02's re-rank instrumentation (top-100 churn tables, graded-page rank moves, the
> Fable 5 page at 538 → 499) is the ready-made instrument for doing it.

> **Revised again 2026-09-19, at execution.** Two later results changed what this
> decision is *for*. [06](06-prompt-size.md) measured model recall at the true prompt
> size (locate 3/3 at 305k tokens), and the ledger now holds full-page grades on both
> pairs ([13](13-boost-adoption.md)) — so whether ranking gates the *model* is no
> longer a conjecture to protect against; it can be read off the graded findings'
> cited-page ranks directly. That reading is the *Measured* section below.

## Problem

Density scoring was chosen deliberately and for a measured reason — volume scoring put
11,181-line regenerated dumps on top. But density saturates on tiny changes: a one-line
curl edit (`-H 'anthropic-version: 2023-06-01'`) scores 5.0, an anchor fix scores 5.0,
and **63 of the top 100 in #6 → #7 are changes of 100 characters or less**, tied with or
above genuine breaking changes. Three consumers feel it:

1. the report head a human reads first;
2. the order the digest session reads changes in (`compress_run` sorts by severity);
3. any recall-against-ranking metric — already declared invalid in the session record,
   *because* the digest correctly skips the one-liners the ranking promotes.

What keeps this a decision rather than a bug-fix: the harm to the digest is **unproven**.
The model demonstrably skips the one-liners, so the measurable damage so far is to the
human-facing head and to metric validity. Re-tuning the ranking blind would repeat the
exact mistake issue 02 of the readiness set documents — the acceptance criterion must
come from graded ground truth, which is what [01](01-verdict-ledger.md) provides.

## Options

**A — corroboration damping.** Multiply the density score by a saturating function of
volume — `min(1, changed_lines / L0)` or a log ramp — so a one-line change needs company
to reach the top.

- *Pro:* one factor, keeps density's character, tunable against graded data.
- *Con:* `L0` is a fitted constant; fitting needs [01](01-verdict-ledger.md)'s "where did
  graded-true findings' pages rank" data, and risks re-burying small sharp changes — the
  precise thing density was built to surface. The Fable 5.1 retention sentence is itself
  a small change; the fit must check it does not sink.

**B — a tiny-change band.** Below N changed characters, changes rank within their own
`minor` band, listed after the main feed in the report.

- *Pro:* fixes the human-facing head without touching relative order among real changes;
  N is legible in a way a damping curve is not.
- *Con:* a hard band is a filter-shaped object, and the house position is ranking-never-
  filter; the band must remain fully listed. Boundary cases land arbitrarily.

**C — leave scores; change presentation.** Two heads: sharpest by density, largest by
volume. The model input order can stay density-sorted or interleave.

- *Pro:* destroys no information, no constants to fit.
- *Con:* two lists to read; does nothing for metric validity.

**D — do nothing to ranking; fix only the metric.** Declare ranking a model-input
ordering, drop recall-vs-ranking for digest quality (already done in prose), and let
[01](01-verdict-ledger.md)'s graded recall replace it.

- *Pro:* zero risk; honest about where the demonstrated harm is.
- *Con:* the report head stays cluttered for the human reader.

## The number to get first

From the graded ledger — now live, with five graded arms on #5 → #6 to draw from: the
rank distribution of pages cited by graded-true findings vs the rest, and where the
known-miss needle pages ranked (the Fable 5 page sits at 538 of 986; the needle files
record ranks for exactly this). If graded-true pages already concentrate high despite
the one-liners, D or C suffice; if they are buried under one-liners — or pinned to the
middle by the density cap, the second end of the pathology — A or B earn their risk.
Any adopted change: re-rank the stored pairs, diff the top-100, read what moved — and
bump `CLASSIFY_VERSION` (shipped by [02](02-restriction-lexicon.md)) in the same
change.

## Measured (2026-09-19)

All free and deterministic: the run-report JSONs carry per-page severity/signals, the
ledger carries every full-page verdict with the finding's cited URLs. Rank universe =
content-cause modifications ordered by the `compress_run` key `(-severity, company,
url)` — 986 for #5 → #6, 1,156 for #6 → #7. Sanity: the untied needle ranks reproduce
exactly (538, 32, 105, 142); every recorded rank that doesn't sits inside its severity
tie block (see *rank instability* below).

**Where graded-true findings' pages actually rank** (best-cited page per finding,
method full-page, all arms pooled):

| | #5 → #6 | #6 → #7 |
|---|---|---|
| graded `true` with a ranked page | 66 | 31 |
| best-cited rank min / q25 / med / q75 / max | 1 / 46 / **178** / 428 / 874 | 2 / 48 / **94** / 459 / 948 |
| in top-100 / top-300 | 31 / 45 | 16 / 20 |
| ≤100-char pages **above** the median true rank | 124 of 177 | 74 of 93 |

Graded-true pages do **not** concentrate in the head — half sit past rank 178 (of 986)
and 94 (of 1,156), under a blanket of one-liners. By the issue's own framing that
should mean "A or B earn their risk". It doesn't, because of the next number.

**The burial check: the one-liners are the material.** For each graded `true`/`partly`
finding, the size of its best-cited page:

| best-cited page is… | #5 → #6 (n=76) | #6 → #7 (n=36) |
|---|---|---|
| ≤100 changed chars | **34 (45%)** | **18 (50%)** |
| ≤3 changed lines | 23 | 15 |

Half of everything the digest verifiably reported true rides exactly the changes A
would damp and B would band. The head's "63 of 100 at ≤100 chars" is not clutter
around the signal; to a first approximation it *is* the signal. The premise that tiny
and trivial coincide is refuted by the ledger.

**Option A simulated** (`severity × min(1, changed_lines/L0)`, re-ranked, both pairs):

| L0 | top-100 ≤100ch (5→6 / 6→7) | pooled true+partly median (5→6: 89 / 6→7: 94) | graded pages sunk >100 ranks | supported-models 538 → | token-counting 638 → |
|---|---|---|---|---|---|
| 3 | 52 / 67 | 116 / 117 | 5 / 6 | 529 | 635 |
| 5 | 44 / 59 | 286 / 381 | 20 / 15 | 420 | 613 |
| 10 | 27 / 31 | 522 / 522 | 32 / 20 | 339 | 723 |

Even the gentlest damping sinks graded-true pages by hundreds of ranks (a rank-20 page
falls to 431 at L0=3), and the second end of the pathology barely moves: the
density-capped restriction pages crawl from ~540 to ~420–530. A pays in confirmed
recall material for almost nothing at either end.

**Option B simulated**: a ≤100-char band captures the best-cited page of 34/76 graded
true+partly findings on #5 → #6 and 18/36 on #6 → #7; at ≤200 chars, 41/76 and 23/36.
B's *pro* ("fixes the head without touching real changes") is false on the data — the
band is where half the real changes live.

**Rank instability inside tie blocks** (a finding about the metric, not the formula):
the top-100 is dominated by exact severity ties — 5.0 ×21 and 4.0 ×19 on #5 → #6,
5.0 ×42 and 4.0 ×23 on #6 → #7 — and mid-feed blocks run to 172 pages wide (sev 2.0,
ranks 302–473) and 90 wide (sev 1.0, ranks 631–720). Within a block, rank is the
`(company, url)` tiebreak: alphabetical, meaningless. This retroactively explains every
needle-file rank that doesn't reproduce (321 vs 459, 717 vs 638, 53 vs 40 — each pair
inside one block). **Reading rule: a rank is only meaningful ± its tie block**; the
needle files now say so.

**Model recall is not gated by rank.** Graded-true findings cite pages at ranks 874 and
948 — the model reads the whole feed and finds true material at the bottom, consistent
with [06](06-prompt-size.md)'s locate 3/3 at the real 305k tokens. Reordering model
input is a lever with no measured target.

## Decision (2026-09-19): option D

No change to `severity`; `CLASSIFY_VERSION` stays 2. The reasons, in order of weight:

1. **A and B are rejected by graded ground truth** — both bury the pages behind
   one-third to one-half of confirmed-true findings, for no measurable gain at either
   end of the pathology. This is the same shape as 02's option-A rejection: the obvious
   fix cannot deliver its motivating case and demotes real pages in exchange.
2. **The density-cap end already has its answer at a different layer.** Ranking could
   not surface the Fable 5 restriction (538 of 986 under every re-weighting tried);
   boosted excerpts ([02](02-restriction-lexicon.md), default since
   [13](13-boost-adoption.md)) and the absence detector
   ([05](05-missed-restrictions.md)) deliver that content regardless of rank.
3. **The metric harm is already fixed** — the ledger's graded recall replaced
   recall-vs-ranking ([01](01-verdict-ledger.md)), which was D's substance.
4. **The human head is more legible than the problem statement assumed**: the report
   prints size and per-signal counts on every entry (`+37 chars · severity 5.0
   (status ×2)`), and the graded data says the tiny entries at the top are half
   true-material, not noise.

**C** is declined with A and B: the graded-true pages spread across the *entire* rank
range (1–948) under density, and a volume head would simply be the dump-ordering that
density was built to escape — no second scalar ordering concentrates a population this
flat. **Considered and declined, option E** (restriction-aware tiebreak within equal
severity — cannot bury anything across blocks): the pages it would lift sit in blocks
around rank 300–500, so within-block movement never reaches the head; excerpt boosting
already shows the model the restriction clause; and it would still reorder model input,
costing a graded arm to validate a change with no measured target. If a future graded
pair shows rank-gated misses, E is the cheapest candidate to revisit.

What shipped: this measurement, a guard comment on `classify.severity` carrying the
rejection numbers (so density is not "fixed" in passing — the STATUS pattern), and the
tie-block reading rule in both needle files' headers. Nothing that changes model input;
no A/B owed.

## Acceptance criteria

- [x] The rank-distribution measurement done and recorded here before any formula
      changes — see *Measured*; no formula change followed
- [x] Whichever option wins: the Fable 5.1 retention page's rank stated before/after —
      `foundation-model-apis/supported-models` (carries both the 5.1 and Fable 5
      retention lines): **538 of 986 before, 538 after** (D changes nothing); under
      the rejected A it would have reached only 529/420/339 at L0=3/5/10
- [x] No change ships without one graded A/B on a stored pair — satisfied by shipping
      no change that reorders model input
- [x] The report renders whatever bands/heads exist with everything still listed — no
      bands or heads were introduced; the feed is unchanged
