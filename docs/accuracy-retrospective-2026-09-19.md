# Accuracy work retrospective — issues 01–07 and 13 (2026-09-18/19)

> The technical record of *how* the work went, complementing
> `docs/digest-experiments-2026-09-19.md` (which records *what the experiments found*).
> Both faces are here: what worked as designed, and what broke, misled, or had to be
> corrected mid-stream. Everything traces to the issue files under `issue/accuracy/`,
> the worksheets under `reports/changefeed/verdicts-*.yaml`, and the ledger in
> `state/changes.db`.

## Scope

Eight issues executed over two days: the verdict ledger (01), the restriction lexicon
and boosted excerpts (02), newness-check coverage (03), past-claim verification (04),
the absence detector (05), prompt size and real token counts (06), revision marking
and adaptive slots (07), and the boost confirmation and adoption (13). Nine graded
digest runs, ~$43 of model spend, 450 tests at the end, prompt v2 → v3 with the
adoption reasoning in the code.

---

## What went right

**1. Instrument before intervention.** Issue 01 (the ledger) was built first, and every
later conclusion leaned on it. Grades stopped evaporating into prose; `digest.py
accuracy` now answers eleven run/version combinations from one query. The
selection/method columns did exactly the work they were designed for — twice they
prevented wrong conclusions: the "0% targeted" row was never mistaken for a rate, and
the mixed-method #6 → #7 grade decomposed into a flattering excerpt half and a
suspicion-biased full-page half, neither of which was the truth (the honest n=18 rate
turned out to be 79%).

**2. Measure-before-build killed three plausible designs for a few CPU-seconds each.**
Extending STATUS with restriction words (the fix issue 02 was *named for*): rejected —
the target page moved rank 538 → 499 while Admin-API boilerplate flooded the top-100.
Broadening the newness extractor (03): every variant multiplied false flags without
catching either real graded error; the corpus-wide check would have flagged nine true
launch findings over one early cookbook page. Term-overlap past-claim checking (04):
~90% false, all direction confusion. Each rejection is recorded with its numbers where
the next person will look, including comments in the code guarding the "obvious fixes".

**3. The one-input-change-per-arm rule, learned once and then enforced.** The combined
arm proved interference is real (breaking labels ballooned; the injection's coverage
gain vanished), and every arm after it was single-change with its own
`prompt_version`. That discipline is what made the issue-07 result attributable: four
arms cleanly separated visibility from provenance.

**4. The mechanism finding.** The invented-past signature ("already documented for
Claude Fable 5") reproduced 3-for-3 in arms that showed restriction content without
provenance, and 0-for-1 with per-line `~` marking — which also produced the type
specimen finding no run had ever written. Instructions do not carry provenance;
the data must. This came from experiment design, not intuition, and it redirects
future effort (marking is the v4 candidate; more prompt rules are not).

**5. Free measurements were repeatedly available where paid ones seemed needed.** The
token-count calibration rode on a probe run's `usage` field (no API key exists on
this box); the 547-signature census, absence coverage, needle checks, re-rank
experiments, and every grading pass cost nothing but time. The one recurring paid
unit — a digest run — stayed $3.4–4.9.

**6. Reading real output as a verification step.** At least six defects that tests
missed were caught by eyeballing what an instrument actually produced on the stored
pairs: the excerpt window rewind bug, the preposition-"to" false flag, the quote
pairing artifacts, the empty worksheet, the census false positive, and the collapse
group-line formatting. The house rule ("a check's test is built from the exact text
that got past the previous version") kept converting these into regression tests.

---

## What went wrong

**1. The quote verifier's parser broke four different ways on real text — after
shipping with measured 2/2 precision.** Escaped quotes inside quotes; sentence
splitting *inside* quoted spans re-pairing quote marks across fragments; "now read
\"Y\"" and "is retitled \"Y\"" not classified as present-side; and the original
length-filter-before-pairing artifact. Organic volume (~6 quote-claims/run) hid all of
this; the quote-rule arm's induced volume exposed it. Lesson: a text-parsing check
validated at one volume is not validated at another, and its flag counts stop being
comparable across conditions that change the input distribution. The hardening is a
recorded precondition before those flags are trusted again.

**2. I violated the project's own fixture rule and the tests caught me.** The issue-07
pairing tests were first written with *abbreviated* versions of the real lines; the
Jaccard score is length-sensitive (the real appended-clause pair scores 0.88, my
shortened fixture 0.58) and three tests failed for a reason that looked like a code
bug and was a fixture bug. The standing rule — real text, verbatim — exists precisely
because paraphrases change the measured property.

**3. My own grading needed a correction mid-stream.** I graded the injection arms'
"the same condition already documented for Claude Fable 5" as flatly false. The
issue-07 measurement then showed the before page *did* carry a shorter Fable 5
retention note — the cannot-use clause was appended to it. The restriction is still
new (the claim is still wrong in the direction that matters), but "fabricated from
nothing" was too strong, and the specimen's precise definition had to be sharpened:
the *clause* is new, the *note* is not. A grader who also built the arms is the
recorded bias; this is what it looks like in practice. (The reverse also happened:
finding 245's "(was 10,000)" looked like an invented past and the blobs proved it
verbatim-true.)

**4. The experiment machinery fought the schema's assumptions.** `supersede` was
designed for re-runs, not for seven experiment arms on one pair: every arm run
overwrote "current", graded sets had to be restored by hand-written
`UPDATE … SET superseded_at = NULL`, and one worksheet was silently emitted *empty*
because a background run's supersede fired between a restore and a draw (the
draw read zero current findings). The ledger absorbed all of it — grades attach to
rows — but the choreography was manual and error-prone. If arm-running becomes
routine, `run --no-replace` plus an explicit "current set" pointer is the missing
schema feature. *(Built 2026-09-20 — `run --no-replace` shelves an arm at birth,
`grade --prompt-version` draws from it, `promote` is the pointer; the 2026-09-20
two-arm campaign ran on it without a single manual UPDATE.)*

**5. Process-management slips.** One arm was launched with a shell `&` instead of the
background mechanism, losing its completion notification (recovered by polling); one
confirm attempt burned zero dollars but a full supersede/restore cycle when the
Claude Code session limit hit mid-read. Neither cost data; both cost cleanup.

**6. Instrument gaps found in use.** `grade` can only emit worksheets for the
*current* finding set, so every superseded arm's worksheet was hand-built; the census
regex matched a technical phrase ("history already present") as a past-claim; the
`--count-tokens` instrument cannot run on this machine at all (no `ant` CLI, no API
key) and survives only as a graceful hint plus the probe-side measurement.

**7. Inherited findings that predate this work but shaped it.** The token estimator
had been 35% optimistic since the beginning — the "198k" prompt was 305k real, the
size-warning threshold was unreachable, and every historic figure needs a ×1.5
reading. And the newness check's digit gate, twice nearly "fixed", turned out to be
load-bearing — its one true blind spot (plain nouns: DENY) appeared identically on
both pairs and remains open, honestly, with no cheap deterministic fix measured.

**8. Two questions the data cannot yet answer.** The boost confirm wrote 62 findings
against the baseline's 79 and left two needle pages uncited (including a
verified-true control); run variance and mechanism are indistinguishable at n=1. And
the draw metric inverted the qualitative verdicts three separate times (10/10 arms
failing the primary endpoint) — the sample rate and the cluster checks are both
necessary and neither is sufficient, which is now a documented reading rule for the
`accuracy` table, not just a caveat.

---

## The one-line versions

- Right: instruments first; measure before building; one change per arm; real text in
  tests; read what the instrument produces.
- Wrong: parsers validated at one volume; abbreviated fixtures; grader bias surfacing
  as an over-strong verdict; experiment choreography on a schema built for re-runs;
  and two honest unknowns left standing (confirm-run narrowing, plain-noun newness).

## Standing state after this arc

Prompt v3 (= v2 text + boosted excerpts) and CLASSIFY_VERSION 2 are the defaults;
quote rule, injection, marking, slots, collapse, and merge are flagged arms with their
results recorded; the ledger holds 11 graded run/version rows; the second-grader check
(issue 13) is open for Doug; issues 08–12 are untouched. All of it uncommitted.

*(Post-script, 2026-09-20: the second-grader pass ran — delegated back to the same
model, blind-ish after compaction — and vindicated §3's worry concretely: 2 of the 6
suspicion-selected rows downgraded true → partly, both the verified-the-quote-and-
stopped shape; the confirm headline is now 83%, not 94%. Issues 08–12 were executed
after this document; CLASSIFY_VERSION is 3 and the corpus layout is flat. See the
issue files and `docs/digest-experiments-2026-09-19.md` Addendum 3.)*
