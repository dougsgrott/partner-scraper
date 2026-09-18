# 06 — The 198k-token prompt: collapse, count, re-probe

**Status:** open (2026-09-18) · **Kind:** code + measurement · **Effort:** ~4–6 h
**Depends on:** [01](01-verdict-ledger.md) for graded A/B; needle sets from 01 for the
re-probe · **Blocks:** nothing

## Problem

The phase-2 recall risk was measured once, well, and at half the size the system now
runs at. The probe (`scripts/probe_recall.py`, needles at ranks 1 through 1113) settled
"no long-context failure" on the #1 → #2 run at **~105k tokens**. The #6 → #7 digest read
**~198k tokens, ~97k of them one-liners for pages that only re-dated** — the Databricks
re-date event flowed straight through `compress`, whose `TERSE_KINDS` lines are not
collapsed. Three distinct exposures:

1. **Recall at 198k is asserted, not measured.** A long flat list of near-identical lines
   is exactly the shape the probe was built to distrust, and the probe refuses to run on
   any pair but #1 → #2 (correctly — its needles are pair-specific), so the assertion
   cannot currently be tested at all. The 60%-of-top-25 citation figure for #6 → #7 is
   confounded by the ranking's own defects ([08](08-tiny-change-severity.md)) and says
   nothing clean about recall.
2. **Token counts are estimated, roughly, and nothing branches on them.**
   `CHARS_PER_TOKEN = 3.5`, labelled "for a size warning, not a decision"; the warning
   threshold (500k, "over half a context window") assumes the 1M window. The estimate has
   never been checked against a real count, and cost scales linearly with the error.
3. **The terse flood is pure dilution.** A `MOVED`/`METADATA` line carries only
   `company/category KIND path` — no excerpt, near-zero information each — and a vendor
   event mints 5,000 of them. They cost ~$2 of input and an unmeasured amount of the
   model's attention.

To be explicit about what this is *not*: there is no window-overflow cliff at 198k
against a 1M window. The exposure is recall degradation and cost, plus the untested
estimator — not a hard limit.

## Options

**A — collapse `TERSE_KINDS` into grouped lines.** One line per (kind, company,
category): count, a few sample paths, and the detected cause where the pipeline knows it
("site-wide re-date"). Pair it with a `list_changes(kind, category)` session tool so
every collapsed change stays enumerable on demand.

- *Pro:* −~97k tokens on event runs; removes the dilution; the information lost per line
  was already near zero.
- *Con:* this **amends the "nothing is dropped" promise** — from "every change is a line"
  to "every change is a line or enumerable through a tool". That is a deliberate wording
  change in `compress.py`'s contract, to be made in the open, not slipped in. The model
  also loses the ability to eyeball the full terse list unprompted; what it could get
  from pathnames alone is the question the A/B answers.

**B — threshold collapse.** Flat list as today until a kind exceeds N lines in a run,
grouped beyond that.

- *Pro:* quiet runs unchanged; only events pay the format shift.
- *Con:* two rendering regimes means run-to-run format instability for the model, and a
  threshold to justify. Weaker than A unless the A/B shows the flat terse list earns its
  tokens on quiet runs.

**C — count tokens for real.** The count-tokens endpoint is free: count the rendered
prompt, print actual beside estimate, branch the size warning on the actual. Do this
regardless of A/B — it converts an untested constant into a measurement at zero cost.

**D — merge duplicate change groups.** The Admin API mirror made 132 of 175
duplicate-body groups; identical changed-line sets can compress to one record citing
both paths. Also stops the mirror double-counting evidence in audits — one story
currently arrives as two records and can be cited as two confirmations.

**E — re-probe recall at real size.** Needle sets per pair
([01](01-verdict-ledger.md)) un-pin the probe from #1 → #2; run `digest`-mode at the
#6 → #7 size, and again post-collapse. This is the number that says whether A is an
accuracy fix or only a cost fix.

## The number to get first

E, and C's estimate-vs-actual delta. Both are cheap (one probe run ~$5; the count is
free). A's token saving is measurable for free today via `digest.py compress` on the
stored pair with a prototype collapse.

## Acceptance criteria

- [ ] Actual token count printed beside the estimate for every compress; the constant's
      observed error recorded here
- [ ] Probe recall at ~198k measured and recorded; the "no long-context failure"
      conclusion re-dated with its new evidence, or revised
- [ ] Collapse (A or B) behind a flag; one graded A/B re-run on the stored event pair
      before it becomes default
- [ ] The `compress.py` docstring's promise updated in the same change that alters its
      truth, with the amendment called out in the change description
- [ ] Duplicate-group merge measured: how many records it removes on #6 → #7, and audit
      evidence no longer counts a mirror pair as two pages

## Tests

- a run with 5,000 moved pages renders them as grouped lines whose counts sum correctly
- `list_changes` enumerates exactly the collapsed set, nothing else
- a mirror pair (identical changed-line multiset, two paths) compresses to one record
  citing both, and `find()` resolves either path to it
