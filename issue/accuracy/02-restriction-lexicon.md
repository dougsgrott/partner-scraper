# 02 — The status lexicon cannot see "cannot"

**Status:** done (2026-09-19), uncommitted — implemented, and the A/B run and graded:
100% vs baseline 70%; boost recommended for default (Doug's call). See *Done* and the
A/B criterion below · **Kind:** code + measurement · **Effort:** ~2–3 h
**Depends on:** nothing to build; [01](01-verdict-ledger.md) to measure ranking effects
**Blocks:** [05](05-missed-restrictions.md) (consumes the restriction lexicon)

## Problem

`classify.STATUS` is the highest-value signal in the pipeline — it drives severity
density, excerpt selection in `compress._excerpt`, and through both, the order and
emphasis of what the digest session reads. Verified on 2026-09-18 against the real regex:

| sentence | STATUS fires? |
|---|---|
| "Customers who opt out of data retention **cannot** use Claude Fable 5.1" | **no** |
| "This feature **requires** Databricks Runtime 18 or above" | **no** |
| "Requests to this endpoint are **rejected**" | **no** |
| "Serverless compute is required" | yes |
| "This property is no longer supported" | yes |

The first row is the sentence §4 of the session record calls "arguably the most
consequential change in the pair" — the restriction the digest missed under both prompt
versions. **It carried no status signal, so severity never boosted its page and the
excerpt ranking never put it first.** The worst miss has a partly deterministic cause
upstream of the model, and the session record frames it entirely as a prompt problem.

The sharper irony: the absence-detector idea recorded in `docs/changefeed-phase-2.md`
names `cannot`, `requires`, `rejected` as its trigger words. The project identified these
words as the signature of what it misses, and its own signal lexicon does not contain
them. Mechanical gaps found by inspection: no `cannot`, no `requires` (only `required`),
no `rejected`, no bare `unavailable` (only `not available`/`unsupported`), and `must `
requires a trailing space so end-of-sentence "must." never matches.

One caution the fix must respect: **the lexicon was calibrated empirically** (the
stratified 64-diff read in issue 02 of the readiness set), and every word added shifts
severity, excerpts, and the model's reading order at once — silently, across every future
run, breaking comparability with past ones.

## Options

**A — extend STATUS directly, word by measured word.** For each candidate (`cannot`,
`requires`, `rejected`, `unavailable`, `must\b` without the space), count matches over the
stored changed lines of a real run, read a sample of the hits, admit only words whose hits
are mostly worth reading — the same protocol that admitted the original lexicon.

- *Pro:* one lexicon, one behaviour, the original calibration method reapplied.
- *Con:* the ranking's needs (recall) and the absence detector's needs (precision) pull in
  opposite directions; a word like `must` may be right for one and wrong for the other.

**B — split into two lexicons**: STATUS for ranking (broad), RESTRICTION ⊂ STATUS for the
absence detector of [05](05-missed-restrictions.md) and for excerpt boosting (strict).

- *Pro:* each tuned to its consumer's error costs; the detector can stay high-precision
  while ranking stays high-recall.
- *Con:* two lists to keep coherent; a word admitted to one and not the other needs a
  recorded reason or it looks like an oversight.

**C — version stamp, whichever else is done.** A `classify_version` written into run
report JSON (the `PROMPT_VERSION` reasoning exactly: a changed lexicon changes the output
and nothing else records it). Near-zero cost; do regardless.

## The number to get first

Per candidate word, over the stored #6 → #7 changed lines (free, deterministic — the blobs
are on disk): hit count, and precision from reading a sample of hits. Then the ranking
effect: re-rank the stored run with the admitted words, diff the top 100 against the
current top 100, and read what moved in and out. The Fable 5.1 retention page's rank
before and after is the single most interesting cell in that table.

## Acceptance criteria

- [x] Candidate words measured (count + sampled precision) on a stored run before any is
      admitted; the numbers recorded here
- [x] The Fable 5.1 retention sentence fires the (new) restriction signal — the test is
      built from that exact sentence, per the standing rule
- [x] Re-ranked top-100 diff read and summarised; regressions named or ruled out
- [x] A lexicon/classifier version stamp appears in run reports
- [x] A/B on model input order: **run and graded 2026-09-19** (`prompt_version` `2+r`,
      $3.79, 79 findings). Seeded-draw full-page grade **10/10 true (100%)** against the
      baseline v2 draw's 70%; **zero mechanical audit flags across all 79 findings**;
      all five needle pages cited. The two graded error clusters both resolved: the
      new-models finding lists only the three genuinely new models (no Grok/GLM false
      newness), and the CMEK story is labelled `behavioural`, not `breaking`. The 5.1
      retention restriction became its own finding — the boosted excerpt showed exactly
      that clause — while the Fable 5 twin (third restriction line on a two-slot
      excerpt) is still unreported, as the excerpt measurement predicted. n=10 on one
      pair is evidence, not proof; **recommended for default**, which is Doug's call
      (flip the flag default and fold `+r` into the next PROMPT_VERSION)

## Tests

- each admitted word: a test from the real changed line that motivated it
- each rejected candidate: its rejection reason recorded here, not silently dropped
- `must.` / `must,` end-of-clause forms match if and only if `must` is admitted

## Measured (2026-09-18)

Marginal hits = changed lines matching the candidate but **not** the current STATUS, over
the content-attributed modifications of both stored runs, read in seeded samples of 12:

| candidate | #5 → #6 (23,765 lines) | #6 → #7 (151,687 lines) | what the sample reads like |
|---|---|---|---|
| `cannot` | 222 lines / 60 pages | 1,297 / 68 | real constraints almost throughout (sharing limits, write-once keys); the 6 → 7 count is one duplicated tool-safety sentence across the `api/beta` mirrors |
| `requires` | 201 / 80 | 262 / 86 | mostly real ("requires the Databricks AI environment version 5"), plus Admin-API OAuth-scope boilerplate and tutorial prerequisites |
| `reject(s\|ed)` | 73 / 28 | 138 / 30 | behaviour statements ("Archived rules are rejected with 400", "Metric views now reject window measures") plus schema-field noise ("`rejected: number`") |
| `unavailable` | 6 / 3 | 174 / 18 | 6 → 7 is 83% "null when the account is unavailable" Admin-API null-semantics boilerplate |
| `must` end-of-clause | 4 / 2 | 2 / 2 | dated obligations ("Before November 30, 2026, you must:") — tiny but clean |

**Re-ranked with all four admitted** (`unavailable` measured separately: it moved nothing
by more than 4 ranks and is omitted from the rest):

| effect | #5 → #6 | #6 → #7 |
|---|---|---|
| top-100 churn | 18 in / 18 out | 10 in / 10 out |
| API-reference pages in top-100 | **1 → 11** (the `rbac_groups` family and `api/errors` ride "Requires an OAuth access token…" / "rejected." in; `salesforce-limits`, `priority-mode`, `acceptable-use-models`, release-notes pages fall out) | 35 → 35, but `whats-new-fable-5-1` falls out at #99 |
| the Fable 5 retention page | **rank 538 → 499 of 986** | — |
| graded pages | `service-tiers` 53 → 57, `compaction` 32 → 34 | `token-counting` 717 → 733, `abac/policies` 105 → 116, `create-policy` 142 → 113 |

**Decision: no candidate enters STATUS — option A is rejected by the numbers, for a
mechanism-level reason that is word-independent.** The target page's restriction lines
are 5 of its 62 changed lines; density arithmetic caps the possible boost at a few
tenths of severity, which lands it near rank 500 no matter which words fire. The
extension cannot deliver its own motivating case, and it demotes real pages in exchange.
Per-word rejection notes: `requires` and `reject*` are what carried the Admin-API
boilerplate into the 5 → 6 top-100; `unavailable` additionally measured ~zero everywhere
and is null-semantics noise in the API reference; `cannot` and `must` are clean words
whose admission still buys nothing at the ranking layer.

**Where the sentence was actually lost: excerpt truncation, not ordering.** In the real
changed lines, `cannot` begins at character 140 and 142 — and `EXCERPT_LINE` is 140. The
retention line *was selected* into the v1 excerpt and head truncation cut it at the word
`cannot`. That discovery redirected the fix.

## Done (2026-09-18)

**Option B, reshaped by the measurement.** `classify.RESTRICTION` (new): the measured
words plus STATUS's own withdrawal vocabulary; its consumers are the boosted excerpt and
the absence detector of [05](05-missed-restrictions.md). STATUS is untouched and now
carries a comment with the rejection numbers so it is not "fixed" again in passing.
`classify.CLASSIFY_VERSION` (option C) is stamped into report JSON (`classify_version`)
and the Markdown header.

The boosted excerpt (`digest.py compress|run --boost-restrictions`, off by default per
the standing A/B constraint): restriction lines outrank other status lines, and a
matched line is windowed from its clause instead of the line head. Verified on the real
#5 → #6 run: the record for `foundation-model-apis/supported-models` now reads
"…Customers who opt out of data retention cannot use Claude Fable 5.1…" where v1 showed
a truncated preamble, and on `create-policy` the excerpt pairs the old and new versions
of the edited sentence — the shape of graded finding 253's error. Limits, recorded
honestly: the excerpt has two slots, and the Fable **5** line (the actual miss) ranks
third among the page's restriction lines, so the boost surfaces the restriction *class*
on that page but not the missed sentence itself — [05](05-missed-restrictions.md)
remains the systematic answer. A first-draft bug (sentence-boundary rewind pushing the
match back off screen) was caught by reading the real output and has a test.

Tests: the Fable sentence fires RESTRICTION and not STATUS; one real motivating line per
admitted word; the `must:`-end-of-clause iff; boosted-vs-plain excerpt on the retention
line; the window-rewind bug. Findings from a boosted digest record `prompt_version`
`2+r`, so the pending A/B lands in the [01](01-verdict-ledger.md) ledger as its own arm.
