# 08 — Severity density and the one-line change

**Status:** open (2026-09-18), **gated on [01](01-verdict-ledger.md)** · **Kind:** decision
**Effort:** ~2 h once the graded data exists
**Depends on:** [01](01-verdict-ledger.md), [02](02-restriction-lexicon.md) (a lexicon
change re-ranks everything and should land first or be measured jointly)

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

From the graded ledger: the rank distribution of pages cited by graded-true findings vs
the rest, and where the known-miss needle pages ranked. If graded-true pages already
concentrate high despite the one-liners, D or C suffice; if they are buried under
one-liners, A or B earn their risk. Any adopted change: re-rank the stored pairs, diff
the top-100, read what moved — and stamp the version
([02](02-restriction-lexicon.md) option C).

## Acceptance criteria

- [ ] The rank-distribution measurement done and recorded here before any formula changes
- [ ] Whichever option wins: the Fable 5.1 retention page's rank stated before/after
- [ ] No change ships without one graded A/B on a stored pair (it reorders model input)
- [ ] The report renders whatever bands/heads exist with everything still listed —
      ranking, never a filter
