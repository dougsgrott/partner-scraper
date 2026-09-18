# 01 — Persist audit verdicts; make grading cumulative

**Status:** implemented (2026-09-18), uncommitted — see *Done* below · **Kind:** code + process · **Effort:** ~3–4 h
**Depends on:** nothing · **Blocks:** the *measured* acceptance criteria of
[02](02-restriction-lexicon.md), [04](04-invented-contrast.md),
[05](05-missed-restrictions.md), [06](06-prompt-size.md), [07](07-reappearing-lines.md);
all of [08](08-tiny-change-severity.md)

## Problem

The project has graded digest findings by hand three times — #5 → #6 under prompt v1,
#5 → #6 under v2, #6 → #7 under v2 — and **all three sets of verdicts exist only as prose
in session documents.** The `findings` table carries `model` and `prompt_version`
specifically so runs can be compared, and nothing compares them: v3 of the prompt cannot
be scored against v2 without redoing an entire manual audit, and the audits already done
cannot be queried at all.

Three subsidiary defects ride along:

1. **The grades are not method-comparable.** The #5 → #6 v1 grade came from full-page
   checking; the #6 → #7 grade ("7 true, 3 partly, 0 false") checked only 4 of 10 findings
   against full text — the other six were judged from ranked excerpts, the method §4 of
   the session record itself declared invalid ("the excerpt audit judges whether a claim
   matches the lines shown, not whether it is true"). The apparent stability across runs
   is partly a change in instrument.
2. **The sample cannot be extrapolated.** `audit.draw()` stratifies by impact with a
   per-stratum minimum of one, so small impact groups are oversampled. A "7 of 10 true"
   sample gives no unbiased overall rate unless the stratum weights are recorded with the
   verdicts.
3. **Misses have no home.** The known missed findings — the Fable 5 retention restriction
   above all — are the project's most valuable ground truth, and they live in prose. The
   repo already has the right mechanism: `docs/changefeed-needles.yaml`, needles with
   ranks, pinned to pair #1 → #2. Nothing extends it to later pairs.

## Options

**A — a `verdicts` table in `changes.db`.** Keyed by finding id: `verdict`
(true / partly / false), `method` (excerpt / full-page), `graded_at`, `notes`, and the
stratum weight of the draw it came from. The migration machinery exists
(`_ADDED_FINDING_COLUMNS` pattern in `src/changefeed/db.py`). Accuracy per
`prompt_version` becomes a join.

- *Pro:* cumulative, queryable, lives beside the findings it judges, survives re-renders.
- *Con:* schema change on the one database that is not rebuildable; grading happens in an
  editor, so a write path is needed anyway.

**B — flat verdict files**, `reports/changefeed/verdicts-NNNN..MMMM.yaml`, one entry per
finding id, no schema change.

- *Pro:* zero risk to `changes.db`; hand-editable; the natural editing surface.
- *Con:* joins by hand; two sources of truth if A ever happens; nothing enforces that ids
  exist.

**C — B as the editing surface, imported into A** (`scripts/digest.py grade` emits a
worksheet pre-filled from the audit sample; `grade --import` validates ids and stores).
The file remains as provenance.

- *Pro:* the editing ergonomics of B with the queryability of A.
- *Con:* the most code of the three. Probably still the right call: the worksheet emit is
  nearly free given `audit.draw()` exists, and validation-on-import is where id mistakes
  get caught.

**Misses, whichever option wins:** extend the needles mechanism rather than inventing a
parallel one — a needle set per graded pair (the #5 → #6 set starts with the Fable 5
sentence, the invented "support note", the DBR 18 mislabel), each with the real text that
defines it. `probe_recall.py` currently refuses any pair but #1 → #2; teaching it to take
a per-pair needle file turns every graded miss into a standing recall check for free.

## The number to get first

None — this issue *is* the instrument. But it has a deadline of sorts: the three existing
grade sets are reconstructible from `docs/session-2026-09-18-lessons.md` §4 and the
grader's memory **now**, and only approximately later. Importing them is the first act
after the mechanism exists.

## Acceptance criteria

- [x] Verdicts for all three existing run/prompt combinations stored, each carrying its
      `method`, with the mixed-method #6 → #7 grade labelled as such
- [x] One query (or one `digest.py` subcommand) answers "accuracy by prompt_version",
      counting only method-comparable grades
- [x] Stratum weights recorded with every draw from now on
- [x] A per-pair needle file for #5 → #6 seeded with the known misses, runnable through
      `probe_recall.py` (or a successor) against any future digest of that pair
- [x] Grading a fresh run is one emit → edit → import cycle, documented in the script's
      docstring

## Tests

- import rejects a verdict whose finding id does not exist for the pair
- a superseded finding keeps its verdict (grades attach to the row, not to "current")
- the accuracy query excludes excerpt-method grades when asked for full-page accuracy

## Done (2026-09-18)

**Option C**, as the issue leaned: `verdicts` table in `changes.db`
(`src/changefeed/db.py`, additive `CREATE TABLE IF NOT EXISTS` — no existing row touched),
worksheet emit / validate-on-import / accuracy query in `src/changefeed/digest/verdicts.py`,
CLI as `digest.py grade [--import]` and `digest.py accuracy`, eight tests in
`tests/test_verdicts.py` (the three above plus atomic-failure, blank-skip, YAML-boolean,
never-pool-selections, re-grade-replaces-per-method). The write-up with the first ledger
table is in [`docs/changefeed-phase-2.md`](../../docs/changefeed-phase-2.md) ("The verdict
ledger").

Deviations from the sketch, both in the honest direction:

- The vocabulary gained **`unverified`** — the v1 grab-bag finding was actually graded
  "unverified", and forcing it into true/partly/false would have falsified the record.
  `unverified` counts in no rate's numerator or denominator.
- A **`selection`** column (`draw` | `targeted`) beyond the issue's method split: the
  v2 #5 → #6 grades were picked to chase v1's errors, so labelling only their method
  would still have let a meaningless "rate" be computed. `accuracy` prints targeted
  rows with "not a rate". Consequence now visible: **no unbiased full-page figure for
  prompt v2 exists yet** — producing one is a single grade cycle on pair 5 6.

The three subsidiary defects: (1) method-comparability — labelled per row, split in every
query; (2) extrapolation — weights recorded by the audit header, the worksheet, and the
table; (3) misses — per-pair needle files `docs/changefeed-needles-0005..0006.yaml`
(the Fable 5 sentence, rank 538 of 986, plus four verified anchors) and
`-0006..0007.yaml` (the three invented-contrast pages and a verified-true control).
`probe_recall.py` needed no change: `--needles` plus its own wrong-pair guard already do
the per-pair routing; needle 1 of the #5 → #6 set is meaningful in `locate` mode only,
as both files' headers explain.
