# 10 — Promote one-off measurements into instruments

**Status:** open (2026-09-18) · **Kind:** code · **Effort:** ~4–6 h
**Depends on:** nothing · **Blocks:** [11](11-raw-noise-canary.md)

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

## Acceptance criteria

- [ ] The three analyses runnable against stored data, reproducing the recorded figures
      (or the discrepancy documented)
- [ ] Each noise normalisation is a named, tested pattern; its test uses real archived
      bytes
- [ ] The cross-check reconciliation runs with (or in) every `changes.py run` and its
      block appears in the report
- [ ] `docs/session-2026-09-18-lessons.md` §7.5's challenge answered with a pointer here
