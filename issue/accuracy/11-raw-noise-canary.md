# 11 — Detect a new noise pattern before an event does

**Status:** done (2026-09-19), uncommitted — **option C**, and the gating test passed:
the clusterer, run blind on both stored events, re-derived both known patterns; the
canary separates quiet (6–8%) from event (81–84%) with ~2.5× margin each way. See
*Done* and *Measured* · **Kind:** code + measurement · **Effort:** ~3–4 h
**Depends on:** [10](10-standing-instruments.md) (the raw-churn instrument)
**Blocks:** nothing

> **Revised 2026-09-19, at execution.** One premise correction: the issue pointed at
> the extract layer's "identical" count as the unexploited signal. Measured, that
> signal cannot carry an alarm — the CSS-suffix churn keeps the raw-changed-but-
> body-identical rate at ~83% in *every* window, so the re-date event is invisible
> inside it. The signal that separates is one normalisation deeper: **churn survivors**
> (known noise already stripped) whose content did not change. That set is 6–8% of
> survivors in a quiet window and 81–84% when a pattern is missing — the alarm rides
> the cross-check's churn leg ([10](10-standing-instruments.md)), which
> [09](09-fetch-path-convergence.md) conveniently guarantees data for: every fetched
> run archives a generation, so every fetched run can churn the newest pair.

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

## Measured (2026-09-19)

**The gating test, blind, on the real archive** (`measure.py residue GEN1 GEN2 --pair
B A --ignore-pattern …` replays an event with the registry as it stood before it):

| replay | canary | top clusters (files/sampled) | re-derived? |
|---|---|---|---|
| gen1→gen2, registry = asset-hash only | **5,353 of 6,339 (84%) — tripped** | `letters len 4 after '_'` 39/40 (3,023 occ) and `alnum len 4 after '_'` 39/40 (2,411 occ); exemplars `iconExternalLink_cOCV → _SOoC`, `anchorTargetStickyNavbar_Dt63 → _e1Nq` | **yes** — the suffix pattern, verbatim |
| gen2→gen3, registry without date-modified | **5,043 of 6,199 (81%) — tripped** | top four clusters 37–38/40, every exemplar showing `<time datetime=… itemprop=dateModified>` | **yes** — the re-date element, verbatim |

**Quiet base rates, full registry** (the same command, nothing ignored):

| pair | candidates / survivors | rate | alarm |
|---|---|---|---|
| gen1→gen2 | 85 / 1,071 | 8% | quiet |
| gen2→gen3 | 77 / 1,233 | 6% | quiet |

**Threshold X = 20% of survivors, minimum 50 candidates** — recorded as
`measure.CANARY_THRESHOLD` / `CANARY_MIN` with this justification in a comment: quiet
runs 6–8%, events 81–84%, so the threshold has ~2.5× headroom below and ~4× above;
the minimum count keeps a tiny survivor set (where a handful of residual pages is
100%) from alarming on nothing.

**A bonus catch, first run out:** the quiet gen1→gen2 residue clusters surfaced a
real unnamed noise pattern — the Anthropic cookbook's chunk names
(`chunk-BrrRHzDK.js → chunk-BcPgHWXd.js`, `letters len 8 after '-'`, 35/40 files),
which the `asset-hash` pattern misses because those hashes are 8 *letters*, not 8 hex
digits. At 8% total the canary correctly stays quiet; the cluster is exactly the
"candidate new pattern, named by its commonest exemplar" the design promised. Admission
into the registry is a separate, measured decision (the issue-10 bar: verify zero
collapsed real changes first) — deliberately not done in passing here.

## Done (2026-09-19)

**Option C.** The alarm is `measure.Canary` (candidates = churn survivors minus the
window's content modifications, mapped through `rawstore.relative_path_for`), computed
inside `measure.reconcile` whenever the churn leg and the modified list are present —
which now includes **every `changes.py run --fetch`**: the run archives a generation
(issue 09), churns the newest pair (~70 s), and prints the canary line in its
reconciliation block. Tripped, the line names the count, rate, and the one
investigation command; a tripped canary is a loud warning, never a run failure — the
investigation is a human's.

The clusterer is `measure.cluster_residue` (CLI: `measure.py residue`): known noise is
normalised away first, then the word-multiset difference of each sampled pair is
clustered by shape — (length, character class, preceding byte) — with verbatim byte
context kept as exemplars. It names no regex; it shows a human the recurring shape and
its surroundings, which is what the gating test proves sufficient. `--ignore-pattern`
(also on `raw-churn`) replays history blind.

**The investigation path, one command against the archive:**

    uv run python scripts/measure.py residue GEN1 GEN2 --pair BEFORE AFTER

**False-alarm behaviour, stated:** a legitimate mass content change — a real site-wide
edit, bodies *not* identical — does nothing, by construction: its pages are content
modifications, so they are subtracted from the candidate set before the rate is taken
(`test_a_mass_real_edit_does_not_trip_the_canary`).

Tests (7, in `tests/test_measure.py`): quiet at the measured base rate; tripped at
event scale; the minimum-count guard; the mass-edit false-alarm case; the canary
carried (as warning, not failure) through `reconcile`; the gating test in miniature —
real archived byte lines, empty registry, the `after '_'` cluster with the
`anchorTargetStickyNavbar` exemplar on top; and disjoint changes yielding no cluster
above the candidate flag. The full-corpus replays are recorded above and rerun via
the CLI.

## Acceptance criteria

- [x] The clusterer, run blind on stored pairs, re-derives both known noise patterns —
      both events, table above, from real archived bytes
- [x] Threshold X chosen from the measured base rates, recorded here (20% / min 50;
      quiet 6–8%, events 81–84%)
- [x] The alarm line appears in refresh output when tripped, naming the pair and count
      — the reconciliation block of `changes.py run --fetch`, which churns the
      generation pair the run just completed
- [x] A tripped alarm's investigation path documented: one command against the archive
- [x] False-alarm behaviour stated: what a legitimate mass content change (a real
      site-wide edit, bodies *not* identical) does — nothing, by construction — and a
      test saying so

## Tests

- both known patterns re-derived from archived bytes — full-corpus via CLI (recorded
  above); in miniature in the suite from verbatim archived lines
- a synthetic pair with no shared byte pattern yields no cluster above threshold —
  `test_disjoint_changes_yield_no_shared_cluster`
- body-changed pages never enter the candidate set —
  `test_a_mass_real_edit_does_not_trip_the_canary`
