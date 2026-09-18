# 11 — Detect a new noise pattern before an event does

**Status:** open (2026-09-18) · **Kind:** code + measurement · **Effort:** ~3–4 h
**Depends on:** [10](10-standing-instruments.md) (the raw-churn instrument)
**Blocks:** nothing

## Problem

The session record, marked *(challenge)*: *"a noise-pattern list only learns a pattern
is missing when a vendor event exposes it. No mechanism detects a new noise pattern
before it swamps a run."* Both known patterns were found reactively — the CSS-module
suffixes only after the asset-hash hypothesis measured 0, the `dateModified` re-date
only after it made 4,966 pages look changed.

The detection signal already exists in the pipeline, unexploited: **a page whose raw
bytes changed while its extracted body stayed identical is, by construction, a noise
candidate.** The extract layer computes exactly this (the "identical" count). What is
missing is the step from "many such pages" to "here is the byte pattern they share."

Scope honesty: this protects the *raw-churn numbers* and the unbuilt
normalised-content-addressing idea from `docs/raw-archive.md` — not the change feed,
which already absorbed the re-date at the extract layer (the damage there was the
date-keyed paths, [12](12-date-keyed-paths.md), and the terse flood,
[06](06-prompt-size.md)).

## Options

**A — cluster the residue.** Per generation pair, for byte-changed/body-identical
pages: strip the *known* normalisations, then diff the raw text of a sample and cluster
the most common changed substrings or line-shapes across files. Report top clusters
with counts; a cluster above a threshold is a candidate new pattern, named by its
commonest exemplar.

- *Pro:* answers "what is the pattern", not just "something happened"; deterministic;
  runs offline on archived generations, which exist precisely to make this possible.
- *Con:* clustering raw HTML diffs is heuristic; quality unknown until validated —
  which is cheap, see below.

**B — threshold-only alarm.** If byte-changed-with-identical-body exceeds X% of a
host's pages in a pair, print a loud line telling a human to investigate.

- *Pro:* ~10 lines on top of counts the pipeline already has.
- *Con:* says something happened, not what; the investigation it triggers is the manual
  work A automates.

**C — B always-on, A on demand.** The alarm runs with every refresh; the clusterer is
an instrument subcommand ([10](10-standing-instruments.md)) pointed at the flagged
pair.

- *Pro:* the cheap part is ambient, the heuristic part runs only when summoned, on
  archived data, with a human reading its output.
- *Con:* none beyond its parts. Likely the right shape.

## The number to get first

**Run A retroactively on the stored generations.** gen1 → gen2 must surface the
CSS-module suffix pattern (`_Dt63`-style) and gen2 → gen3 must surface
`<time … itemprop=dateModified>` — *without being told about either*. Both events are
fully archived; if the clusterer re-derives both known patterns blind, it works; if it
cannot find patterns that are already known, it cannot be trusted with unknown ones and
the issue falls back to B. The alarm threshold X also comes from stored data: the three
generations give the observed base rates for quiet and event pairs.

## Acceptance criteria

- [ ] The clusterer, run blind on stored pairs, re-derives both known noise patterns —
      this is the gating test, from real archived bytes
- [ ] Threshold X chosen from the measured base rates, recorded here
- [ ] The alarm line appears in refresh output when tripped, naming the pair and count
- [ ] A tripped alarm's investigation path documented: one command against the archive
- [ ] False-alarm behaviour stated: what a legitimate mass content change (a real
      site-wide edit, bodies *not* identical) does — nothing, by construction — and a
      test saying so

## Tests

- both known patterns re-derived from archived bytes
- a synthetic pair with no shared byte pattern yields no cluster above threshold
- body-changed pages never enter the candidate set
