# 10 — Promote one-off measurements into instruments

**Status:** done (2026-09-19), uncommitted — **A + C as forecast**: `scripts/measure.py`
carries the three analyses, the cross-check runs inside `changes.py run`, and every
recorded figure reproduced (three documented refinements, no contradictions). See
*Done* and *Validated* · **Kind:** code · **Effort:** ~4–6 h
**Depends on:** nothing · **Blocks:** [11](11-raw-noise-canary.md)

> **Revised 2026-09-19, at execution.** Three things changed since this was written.
> The ledger ([01](01-verdict-ledger.md)) made "recall-vs-ranking overlap" obsolete as
> a quality metric and [08](08-tiny-change-severity.md) measured what replaced it —
> so `ranking-overlap` ships as an *ordering watch* (for classifier bumps), with a
> `--graded` mode that reproduces 08's population. Second, a gap found in use: extract
> summaries were printed and lost, so the cross-check had nothing to reconcile against
> after the fact — they now persist to `state/extracts/` like fetch summaries do.
> Third, the noise patterns live fetch-side (`scraper/fetch/noise.py`), not in the
> instrument, because [11](11-raw-noise-canary.md)'s canary is a fetch-time consumer.

## Problem

The session record's own §7.5, marked *(challenge)*: the key measurements — raw churn
with noise normalisation, the duplicate-body breakdown, recall-vs-ranking overlap — were
carried by one-off analysis scripts that no longer exist as runnable artifacts. Two
costs, and the second is the accuracy one:

1. The next window redoes the work.
2. **A redone instrument measures slightly differently, and nothing shows it.** The
   cross-window comparisons this project's questions live on — is this week quiet, did
   the noise rate move, did the ranking improve — silently become comparisons between
   instruments, not between weeks. The house has already met this failure shape once:
   changing how `output_fingerprint` was computed invalidated every stored comparison at
   once. Instruments drift the same way code fingerprints do.

There is also one measurement that was done by hand exactly once and is really an
**invariant**: the §3 cross-validation — change-feed modified count = raw-analysis real
changes = extract written − identical. It held for #5 → #6. Nothing checks it on any
other run, and it is precisely the kind of three-way reconciliation that catches a whole
class of pipeline bugs (a diff missing pages, an extractor double-writing) the moment
they happen instead of at the next manual audit.

## Options

**A — `scripts/measure.py`** with subcommands: `raw-churn GEN1 GEN2` (byte churn, then
survivors under each registered noise normalisation), `duplicates PAIR` (duplicate-body
groups with the mirror breakdown), `ranking-overlap PAIR` (digest citations vs top-N),
`cross-check PAIR` (the reconciliation). Outputs land in `reports/` beside the run
reports they describe.

- *Pro:* one home; instruments are versioned, tested, and diffable like everything else;
  the noise-normalisation list becomes code with a test per pattern built from the real
  bytes that motivated it, per the standing rule.
- *Con:* a maintenance surface that must move when the pipeline moves — the price of
  having instruments at all.

**B — fold each measurement into the tool it measures** (churn into fetch, duplicates
into validate, overlap into digest).

- *Pro:* no new script; measurements run where their data lives.
- *Con:* scatters the instrument set across four tools; churn analysis is not a fetch
  concern, and the point of instruments is finding them next window. Weaker than A
  except for the one case below.

**C — the cross-check invariant runs inside `changes.py run`** and prints its
reconciliation block with every report, failing loud on mismatch.

- *Pro:* always-on, catches pipeline bugs at the run that introduces them; this is the
  one measurement that belongs in the tool rather than beside it, because it is a check,
  not an analysis.
- *Con:* couples the run to the extract summary's availability; needs a clean way to
  say "no extract data for this window" instead of failing.

A + C together, most likely: A for the analyses, C for the invariant.

## The number to get first

None to decide the issue — but the validation *is* a set of numbers: each instrument,
run against the stored generations and pairs, must reproduce the session record's
published figures. gen1 → gen2: 0 collapsed by asset-hash normalisation, 5,255 by
CSS-module suffixes, 1,084 survivors, 986 real. gen2 → gen3: 188 survivors after
suffixes, +4,966 from `dateModified`, 680 survivors, 609 real, 0 missed.
**Reproduction of known results is the acceptance test.** Where a figure cannot be
reproduced, that is a finding about either the instrument or the record, and both are
worth having.

## Done (2026-09-19)

**A + C.** The analyses live in `src/changefeed/measure.py` (CLI:
`scripts/measure.py`, outputs to `reports/measure/`); the noise patterns in
`src/scraper/fetch/noise.py` as a registry of named `NoisePattern`s, each carrying its
admission record — when it entered, what it collapsed, how safety was verified.
Attribution follows the recorded tables' convention: patterns apply cumulatively in
registry order, and a page is attributed to the first pattern at which nothing remains.

- `raw-churn GEN1 GEN2` — exhaustive byte comparison, per-pattern attribution,
  per-company survivor counts, survivor list in the written report (~70 s a pair).
- `duplicates SNAPSHOT` — duplicate-body groups, group-size histogram, the Admin-API
  mirror count (membership rule: a group holding both an `/api/admin/` and an
  `/api/beta/organization` member — the pairing includes renames, so a rewrite rule
  undercounts: 107 vs the true 132), and non-mirror samples.
- `ranking-overlap BEFORE AFTER [--graded]` — best-cited severity rank per finding,
  quantiles, top-N counts, with 08's tie-block reading rule printed on every output.
- `cross-check BEFORE AFTER [--extract F] [--generations G1 G2]` — the reconciliation.
  `measure.reconcile` degrades by leg: feed counts always; extract leg when a summary
  exists ("no extract data for this window" otherwise — summaries persist to
  `state/extracts/` as of today, the same pattern as `state/runs/`); raw leg when
  generations are named, which enables the **per-page** form of the record's "0 missed"
  figure: every content modification's raw file must be a churn survivor, and a
  collapsed one is a hard failure (a noise pattern ate a real change).

**C wiring:** `changes.py run` reconciles its diff against the extract summary it just
produced, prints the block, appends it to the Markdown report, and **returns exit 1 on
a hard mismatch** (feed changed+added pages exceeding extract's changed outputs, or a
collapsed real change). A nonzero residue is printed, never fatal — next window's
reader should see the same ~2% the record saw, not a mystery. `pipeline`/`unknown`
attribution warns without failing: extractor changes are legitimate and known-noisy.

Tests (`tests/test_measure.py`, 17): each noise pattern against the verbatim archived
bytes that motivated it — including the all-lowercase suffix (`navbarSearchContainer_xryr`)
that broke the first, narrower regex draft — the Fable 5.1 retention clause surviving
every pattern (alone and mixed with suffix churn), attribution order, the duplicates
grouping and mirror rule, best-cited-rank selection with superseded findings excluded,
and every `reconcile` verdict path. `cmd_run`'s wiring is by-inspection plus the fully
tested `reconcile`; `cmd_run` end-to-end remains untested like the rest of that command.

## Validated (2026-09-19): every recorded figure reproduced

| figure | recorded | instrument | note |
|---|---|---|---|
| gen1→gen2 identical / differ | 227 / 6,339 | 227 / 6,339 | exact |
| collapsed by asset-hash | 0 | 0 | exact |
| collapsed by CSS-module suffixes | 5,255 | 5,255 | exact |
| survivors | 1,084 | 1,071 + 13 | **refinement 1**: the `date-modified` pattern postdates the 2026-09-09 study; it collapses 13 of the recorded survivors. 1,071 + 13 = 1,084 exactly |
| gen2→gen3 collapsed "by the 09-09 normaliser" | 188 | 188, all by asset-hash | **refinement 2**: this window the bundles rotated without a suffix rebuild — the record's combined label decomposes to asset-hash alone |
| collapsed by `dateModified` | 4,966 | 4,966 | exact |
| Databricks survivors / Anthropic changed | 680 / 553 | 680 / 553 | exact |
| duplicate-body groups in #7 / mirrors | 175 / 132 | 175 / 132 | exact |
| 08's pooled best-cited medians | 89 / 94 | 89 / 93 | **refinement 3**: quantile-index convention (`int(p·(n−1))`) differs by ≤1 from 08's `n//2` on even n |
| "0 missed real changes" | 0 of 609 (Databricks) | **0 of 1,156** (both companies, per-page) | the standing check is stronger than the recorded one |

The suffix regex itself was re-derived and is *broader* than the first draft: the
per-build suffix can be four lowercase letters, so the pattern is length-4-alnum with
an identifier head, no character-class narrowing — the figures above are what admit it.

## Acceptance criteria

- [x] The three analyses runnable against stored data, reproducing the recorded figures
      (or the discrepancy documented) — see *Validated*; three refinements, zero
      contradictions
- [x] Each noise normalisation is a named, tested pattern; its test uses real archived
      bytes — `scraper/fetch/noise.py` + `tests/test_measure.py`
- [x] The cross-check reconciliation runs with (or in) every `changes.py run` and its
      block appears in the report — appended to the run's Markdown report; hard
      mismatch fails the run
- [x] `docs/session-2026-09-18-lessons.md` §7.5's challenge answered with a pointer here
