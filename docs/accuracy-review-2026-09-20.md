# External review of the accuracy arc — and the watchlist for the next scrape

> Written 2026-09-20 by the reviewing session (the one that opened `issue/accuracy/`
> on 2026-09-18), after issues 01–13 closed. This is the *reviewer's* read of the
> results — what holds, what is genuinely open, and what to check on the next real
> run — complementing `docs/accuracy-retrospective-2026-09-19.md` (the builder's
> process record) and `docs/digest-experiments-2026-09-19.md` (the experiment data).
> Everything here was verified against the working tree on 2026-09-20 unless marked
> otherwise. Come back to §1 on the next scrape; §3 ranks the open decisions.

## 0. Verified end state (2026-09-20)

- 483 tests pass; `PROMPT_VERSION = "3"` (v2 text + boosted excerpts) and
  `CLASSIFY_VERSION = 3` are the shipped defaults.
- The corpus is flat (`data/<company>/<category>/<slug>.md`); the migration's
  verification diff (#7 → #8) attributed all 6,771 moves to `pipeline`, 0 vendor
  changes — the `page_versions` history problem was solved by the permanent
  pipeline-cause rule, not by rewriting records.
- The ledger answers thirteen run/version rows from `digest.py accuracy`; the
  numbers cited below all reproduce from it.
- Honest headline after the re-grade: **boost 83% vs baseline 79% on #6 → #7**,
  direction replicated on two pairs (pooled draws 27/28 vs 22/29 — but see §3.2:
  that is a precision-only comparison). The retired "94% vs 79%" should not be
  quoted.

## 1. The next refresh is the integration test — read it, don't just run it

*(Added 2026-09-20: snapshot #8 is now the declared era boundary — trends,
volume figures, and churn priors start there; the comparison rules are in
`docs/changefeed.md` § "The era boundary: snapshot #8". The next refresh produces
the first all-modern pair, #8 → #9.)*

The next `changes.py run --fetch` exercises, in one pass, nearly everything this arc
built: archive convergence (09), the cross-check reconciliation block (10), the
canary (11), flat-layout diffing (12), and v3 as the default digest input (02/13).
It is also the first *natural* window — post-migration, post-adoption, no experiment
scaffolding. Specifically check:

- [ ] **A generation landed in `raw-archive/`** for the run (issue 09's whole point;
      the failure mode is silent and unrecoverable).
- [ ] **The reconciliation block prints and balances** (exit 1 means a pipeline bug,
      by design — do not shrug it off as instrument noise).
- [ ] **The canary line**: quiet base rate was 6–8%; the threshold is 20%. A trip
      means a new noise pattern — `measure.py residue` is the investigation command.
      Also decide the pending admission of the cookbook chunk-name pattern
      (`chunk-XXXXXXXX.js`, 8 letters not hex) the canary already surfaced; the
      issue-10 bar applies (verify zero collapsed real changes first).
- [ ] **`moved` should be ~0** on a re-date-free window now that date-only moves
      classify as `metadata`; a nonzero `moved` is a real vendor relocation and worth
      reading.
- [ ] **The narrowing question (§3.2), first natural data point**: finding count vs
      the v2 era (baseline wrote 79 on #6 → #7, the boost confirm 62), and the
      needle-style spot check — did the digest cite the pages carrying the window's
      known-important changes? Two uncited needle pages (one a verified-true
      control) is the pattern to watch for.
- [ ] **The `breaking` sample-swap over-label** (a code example's model swap labelled
      breaking) recurred once under the boost — count it; it is the known prompt-side
      residual class.
- [ ] If a digest grade cycle happens: seeded full-page draw, import to the ledger,
      and note that **prompt v3 rows and v2 rows are now different input shapes** —
      the accuracy table's version column is the comparison boundary.

## 2. What holds up, in the reviewer's judgment

1. **The provenance mechanism (issue 07) is the arc's most valuable result, earned
   properly.** Restriction content shown *without* provenance produced the invented
   past ("already stated/documented for Fable 5") 3-for-3 across independent
   sessions (both injection arms, then the slots arm with no injection at all);
   per-line `~+` marking produced 0-for-1 and delivered finding 615 — the
   type-specimen finding no run had ever written. The pathway is the convincing
   part: the Fable 5 line was *not* in the marked arm's excerpt; the legend sent the
   model to `get_diff`, where the aligned pair showed the insertion. Marking worked
   through its intended channel. Caveat that stands: one trial per arm.
2. **Issue 08 refuted its own premise with graded ground truth.** Half of everything
   the digest verifiably reported true rides changes of ≤100 characters — "tiny"
   and "trivial" do not coincide, so damping/banding would bury confirmed-true
   material for no gain at either end of the density pathology. Option D (no formula
   change) is the right call, and the tie-block reading rule (ranks meaningful only
   ± their severity tie block; blocks run to 172 pages wide) should be remembered
   whenever a rank is quoted.
3. **The negative results are load-bearing and guarded.** Newness-extractor
   broadenings (03): every variant multiplied false flags, caught neither real
   graded error; the dotted-version gate is load-bearing. STATUS extension (02):
   could not deliver its motivating case (rank 538 → 499) while flooding the top-100
   with boilerplate. Term-overlap past-claim checking (04): ~90% false. Each
   rejection has its numbers in a code comment where the next "obvious fix" will
   look. These comments are part of the accuracy system now — do not clean them up.
4. **The instruments compounded.** The token estimator was 35% optimistic ("198k"
   was 305k real; historic figures need a ×1.5 reading); locate recall at the real
   305k measured 3/3, retiring the long-context worry at true size; the canary
   blind-rederived both known noise patterns from the archive and found a third on
   its first quiet run; every recorded figure the instruments could reproduce, they
   reproduced.
5. **The record self-corrects, which is why its numbers can be trusted.** The 94%
   headline was retired by the re-grade; the type specimen's definition was
   sharpened mid-stream (the *clause* is new, the shorter Fable 5 note was not —
   the earlier "fabricated from nothing" grade was too strong); the "1 of 4"
   #6 → #7 baseline turned out to be a suspicion-selected subset, replaced by an
   honest n=18 at 79%.

## 3. Open decisions, ranked by consequence

1. **The adopted default does not produce the type specimen.** The single most
   important open fact. v3 (the boost) fixed clusters and lifted the rate, but the
   Fable 5 restriction — the miss that started this arc — is delivered only by the
   *unadopted* marking arm (`+p`). The marking confirm on #6 → #7 (~$5 + a grade
   cycle) is the highest-value spend in the project; until `+p` is confirmed and
   adopted or declined, the headline miss is fixed only in an experiment. Marking's
   known non-fixes, for the adoption reading: name-level false newness (GLM
   returned under `+p`, audit caught it) and the `breaking` over-label class.
2. **Precision vs recall on the boost is unresolved, and the draw metric cannot see
   it.** The confirm wrote 62 findings against the baseline's 79 and left two
   needle pages uncited, including a verified-true control. All draw-based rates
   are precision measures; if the boost narrows coverage, the ledger's headline
   number will not show it. The watch is §1's needle/coverage checks across the
   next few natural windows — treat a repeat of "fewer findings + uncited controls"
   as the mechanism answer, not variance.
3. **No human has graded anything.** The "second grader" was the same model after
   context compaction — mitigated, not independent, and both its downgrades share
   one shape (verified-the-quote-and-stopped) while the baseline's 19 grades were
   never re-checked. Five rows of genuine human spot-grading (worksheets name their
   evidence; blobs are on disk) remains the cheapest real independence available
   and the one issue-13 criterion still effectively open.
4. **Choreography debt before the next arm campaign.** `supersede` was designed for
   re-runs, not seven arms on one pair: hand-written SQL restores, one silently
   empty worksheet. The marking confirm and the collapse A/B are both queued —
   build `run --no-replace` plus an explicit current-set pointer (and worksheet
   emit for superseded sets) *first*; it is an hour against a repeat of a failure
   mode that already fired once.
5. **Smaller residuals, all recorded in their issues:** the collapse/merge digest
   A/B (−55% tokens built behind `+c`/`+m`, ungraded — sequenced after the marking
   decision so arms stay attributable); plain-noun newness (DENY, identical on both
   pairs, no cheap deterministic handle measured — honestly open); the
   quote-verifier hardening precondition (its flags are not comparable at induced
   quoting volume until the four parser limits are fixed); the 547-signature
   census result worth remembering — false "already documented" claims occurred
   *only* under visibility-without-provenance arms, zero under v2, boost, quote
   rule, and marking.

## 4. Reviewer's errors, on the record

Symmetry demands it (the arms were checked against the reviewer's predictions too):

- **Adaptive slots as "the cheapest path to the type specimen" — wrong.** The slots
  arm put the clause on screen and the model neutralised it; visibility without
  provenance is actively harmful, exactly as the option's own recorded con allowed.
  The separate-arms design is what made the refutation clean.
- **Taking the token estimate at face value, twice.** First "at the context edge"
  (wrong direction), then "no overflow cliff at 198k" (conclusion survived only
  because 305k is still under 1M). The estimator is now measured; the lesson —
  never reason from an unvalidated constant — is the same one the project already
  knew.
- The original issue-08 framing implied the one-line head was clutter; the ledger
  showed it is half the signal.

## 5. Cost and constraints, closed out

~$43 total experiment spend across nine graded runs; zero standing model calls
added; the weekly pipeline still costs one session ($3.4–4.9), with a measured −55%
token reduction banked pending its A/B. The plan's three bets — instrument first,
measure before build, one input change per arm — all cashed; the third should be
treated as permanent law for anything that touches model input.

## 6. Where everything lives

| what | where |
|---|---|
| the ledger (13 rows) | `state/changes.db` · `uv run python scripts/digest.py accuracy` |
| experiment data + addenda | `docs/digest-experiments-2026-09-19.md` |
| builder's process record | `docs/accuracy-retrospective-2026-09-19.md` |
| per-issue outcomes | `issue/accuracy/01–13` (each carries Measured/Done/rejections) |
| migration record | `docs/layout-migration-plan.md` |
| instruments | `scripts/measure.py`, `src/changefeed/measure.py`, `src/scraper/fetch/noise.py` |
| worksheets (per-verdict evidence) | `reports/changefeed/verdicts-*.yaml` |
| needle ground truth + tie-block rule | `docs/changefeed-needles-000{5..6,6..7}.yaml` |
