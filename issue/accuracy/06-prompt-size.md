# 06 — The 198k-token prompt: collapse, count, re-probe

**Status:** done (2026-09-19/20), uncommitted — counted, re-probed, collapse and
merge built behind flags; the collapse A/B graded 89% at −55% input tokens and
**adopted as PROMPT_VERSION 4** (see *The collapse A/B*); merge stays a flagged,
ungraded arm; see *Measured* and *Done* below. The
headline: **the "198k-token" prompt was really 305k** — the estimator was off by 35% —
**and recall is intact even there** (locate 3/3), so collapse is a cost fix, not an
accuracy fix, exactly the branch the plan pre-registered ·
**Kind:** code + measurement · **Effort:** ~4–6 h
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
   is exactly the shape the probe was built to distrust. *(Revised 2026-09-19: the
   blocker is gone — the probe's needles were pinned to #1 → #2 until
   [01](01-verdict-ledger.md) produced per-pair needle files, and
   `probe_recall.py --needles docs/changefeed-needles-0006..0007.yaml` now runs
   digest-mode at the real #6 → #7 size. The assertion is testable and simply
   untested.)* The 60%-of-top-25 citation figure for #6 → #7 is
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

**E — re-probe recall at real size.** The per-pair needle files exist
(`docs/changefeed-needles-0006..0007.yaml`, built by [01](01-verdict-ledger.md)); run
`digest`-mode at the #6 → #7 size, and again post-collapse. This is the number that
says whether A is an accuracy fix or only a cost fix.

## The number to get first

E, and C's estimate-vs-actual delta. Both are cheap (one probe run ~$5; the count is
free). A's token saving is measurable for free today via `digest.py compress` on the
stored pair with a prototype collapse.

## Sequencing (added 2026-09-19, after the A/B arms)

The arms turned "one input change per arm" from a preference into a rule — the
combined arm's interference terms are the evidence. Consequences here:

- [13](13-boost-adoption.md)'s boost confirm on #6 → #7 runs against **current**
  compress (no collapse), and this issue's collapse A/B runs as its own arm afterward —
  never folded into the confirm, or neither result attributes.
- 13's fresh full-page baseline draw of the stored v2 #6 → #7 findings doubles as this
  issue's baseline; do not grade it twice.

## Acceptance criteria

- [x] Actual token count printed beside the estimate for every compress; the constant's
      observed error recorded here — *`--count-tokens` on `digest.py compress` (free
      endpoint, graceful without credentials), and the probe now prints actuals from
      `ResultMessage.usage`. Observed error of `CHARS_PER_TOKEN = 3.5`: **−35%**
      (693,238 chars billed as 305,337 input tokens = 2.27 chars/token). The constant
      is now 2.3; the collapsed probe's estimate landed within 0.1% of actual.*
- [x] Probe recall at real size measured and recorded — *at **305k actual tokens**
      (not 198k): digest-mode 1/4, but locate-mode **3/3** on the misses, so the
      digest misses were top-30 ranking choices, not retrieval failures. The
      "no long-context failure" conclusion re-dates to 2026-09-19 at 305k. A second
      digest-mode probe on the collapsed+merged rendering (137,786 actual tokens)
      returned the identical hit pattern and 30/30 valid paths — the reformat neither
      helps nor hurts selection, and grouped lines parse cleanly.*
- [ ] Collapse (A or B) behind a flag; one graded A/B re-run on the stored event pair
      before it becomes default — *built behind `--collapse-terse`; the **graded digest
      A/B is gated behind [13](13-boost-adoption.md)'s confirm per the sequencing
      section, and is now a pure cost decision* (~$2/run on event weeks)*
- [x] The `compress.py` docstring's promise updated in the same change that alters its
      truth — *"every change is a line, **or enumerable through a tool**", amended in
      the open with the reasoning in place*
- [x] Duplicate-group merge measured and audit evidence deduplicated — *262 redundant
      records on #5 → #6 (largest group: 115 API-reference mirrors losing one
      beta-header line), 246 on #6 → #7; `--merge-duplicates` renders each group as one
      record naming the mirrors; `audit_finding` now shows a mirror pair as one
      evidence block plus an "identical change to …" note (default on — the audit is
      human-facing, not model input)*

## Tests

- a run with 5,000 moved pages renders them as grouped lines whose counts sum correctly
- `list_changes` enumerates exactly the collapsed set, nothing else
- a mirror pair (identical changed-line multiset, two paths) compresses to one record
  citing both, and `find()` resolves either path to it
- flags off ⇒ rendering byte-identical to what every graded run read
- audit evidence counts a mirror pair once

## Measured (2026-09-19)

Probe spend ~$7.50 (one digest-mode at full size, three locate calls, one digest-mode
at collapsed size), against Claude Code CLI credentials.

| number | value |
|---|---|
| real tokens, #6 → #7 rendered prompt | **305,337** (est. was 198k; ratio 2.27 chars/token) |
| real tokens, #5 → #6 | ~135k by the corrected estimator (recorded as "88k") |
| locate recall at 305k | **3/3** — no long-context retrieval failure |
| digest-mode top-30, full vs collapsed rendering | identical (1/4 needles chosen, 0 invented paths, both) |
| collapse+merge, #6 → #7 | 693,238 → 316,132 chars ≈ **301k → 137k tokens (−55%)**; 6,329 → 1,072 records + 137 group lines |
| collapse+merge, #5 → #6 (quiet pair) | 311k → 248k chars (−21%, all from the merge; collapse is a no-op at 17 terse records) |
| duplicate records removed by merge | 262 (#5 → #6) / 246 (#6 → #7) |

**Consequences worth stating.** Every historical prompt-size figure in the docs was
understated ~1.5×: the runs graded in `docs/digest-experiments-2026-09-19.md` read
~135k-token prompts, and the #6 → #7 digest read ~300k. The 500k warning threshold,
under the old constant, would not have fired until ~1.5M real tokens — past the 1M
window; under the corrected constant it means what it says. Cost scales with real
tokens, which is most of why #6 → #7 cost $4.68 against #5 → #6's $2.81.

## Done (2026-09-19)

`compress_run(collapse_terse=, merge_duplicates=)` + `TerseGroup` + `mirrors` on
records; the `list_changes` session tool (kind, optional category, paginated) in
`tools.py`; flags on `digest.py compress|run` (findings record `+c` / `+m`) and on
`probe_recall.py`; `--count-tokens` on compress; `CHARS_PER_TOKEN` corrected with the
measurement in its comment; audit mirror-evidence dedup; five new tests. The digest
A/B for `+c`/`+m` remains the one open box, sequenced after
[13](13-boost-adoption.md)'s boost confirm so the arms stay attributable.

## The collapse A/B (2026-09-20): graded, and it costs nothing

Run as `3+c` on #6 → #7 in the two-arm campaign ($4.26, 72 findings, shelved via the
new `--no-replace`; worksheet `verdicts-0006..0007-3c.yaml`). **The first point of the
volume-recall curve says collapse is free**: input 1,295 records (the 5,034 terse
lines grouped) at **−55% input tokens and −19% cost**, and the digest got *better*,
not worse — **16/2/0 = 89% full-page** (the highest graded arm on the pair, at the
strict post-re-grade standard), 72 findings against the baseline's 79 (no narrowing),
zero invented-past claims in all 72, and 3 of 4 needles cited. The uncited needle is
`token-counting` (rank ~638) — the same page the `2+r` confirm missed, now looking
like a recurring low-rank variance case rather than an arm effect. Bonus datum:
finding 863 (AWS tier-advancement) is a verbatim-true *past-claim* produced without
marking — visibility of both diff sides in the excerpt sufficed. Caveats recorded in
the experiment record's Addendum 4: strict-vs-mixed grading standards across arms,
and CLASSIFY_VERSION 3 input (moved→metadata relabels) on the new arms only.
**Adopted 2026-09-20 (Doug's call, same day): PROMPT_VERSION 4 = the v3 prompt text
plus collapsed terse input as the default.** The adoption comment in `session.py`
carries the numbers and the exclusions; `--no-collapse-terse` records `-c`, the same
deviation convention as the boost's `-r`. `merge_duplicates` (`+m`) remains built and
ungraded.
