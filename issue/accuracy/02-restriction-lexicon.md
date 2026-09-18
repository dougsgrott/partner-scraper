# 02 — The status lexicon cannot see "cannot"

**Status:** open (2026-09-18) · **Kind:** code + measurement · **Effort:** ~2–3 h
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

- [ ] Candidate words measured (count + sampled precision) on a stored run before any is
      admitted; the numbers recorded here
- [ ] The Fable 5.1 retention sentence fires the (new) restriction signal — the test is
      built from that exact sentence, per the standing rule
- [ ] Re-ranked top-100 diff read and summarised; regressions named or ruled out
- [ ] A lexicon/classifier version stamp appears in run reports
- [ ] A/B on model input order (if any word is admitted): one re-run of a stored pair,
      graded via [01](01-verdict-ledger.md), before the new lexicon becomes default

## Tests

- each admitted word: a test from the real changed line that motivated it
- each rejected candidate: its rejection reason recorded here, not silently dropped
- `must.` / `must,` end-of-clause forms match if and only if `must` is admitted
