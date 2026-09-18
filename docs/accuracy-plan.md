# Accuracy: plan for the next round

> Written 2026-09-18, from the review of `docs/session-2026-09-18-lessons.md` and from
> checks run against the working tree that day (regex behaviour, STATUS coverage, the 410
> passing tests). Figures trace to that document, to `docs/changefeed-phase-2.md`, and to
> `reports/changefeed/0005..0006.*` / `0006..0007.*`. The work is divided into twelve
> issues in [`issue/accuracy/`](../issue/accuracy/README.md); this file is the frame they
> hang on.

## What this plan is for

The digest is useful and wrong in specific, recurring ways: it invents contrast with the
past, it calls existing things new, and it misses restrictions that arrive dressed as
announcements. The session record already knows most of this. What the review added is
that several of these model errors have **deterministic causes or deterministic detectors
upstream of the model**, and that the measurement process itself has no memory — every
manual audit evaporates into prose, so no prompt or ranking change can be scored against
the last one.

Two findings from the review are load-bearing and were verified by running code, not by
reading it:

1. **The status lexicon cannot see the sentence it most needed to see.** `classify.STATUS`
   does not match `cannot`, `requires`, or `rejected`. The Fable 5.1 retention sentence —
   "Customers who opt out of data retention **cannot** use Claude Fable 5.1", the change
   the session record calls the most consequential of its pair — carries **no status
   signal at all**, so severity never boosted it and the excerpt ranking never surfaced
   it. The digest's worst miss has a partly deterministic cause.
2. **The newness check is blind to single-number versions.** `audit.identifiers()` returns
   nothing for "DBR 18", "Claude Fable 5", "AI v6", or "DENY" — both of the audit's recent
   misses fall in this class, not only the plain-noun DENY case the session record names.
   The gap is "anything without two dotted version components", which in this corpus is a
   large class.

## Standing constraints

These bound every option in the issue set. An option that violates one is listed only to
record why it was rejected.

- **No standing model calls are added.** The pipeline's model spend stays one session per
  run. Everything proposed is deterministic except two explicitly bounded exceptions: a
  single small verifier call per run ([04](../issue/accuracy/04-invented-contrast.md),
  option C — and only if the deterministic options measure insufficient), and discrete
  A/B experiments, which are digest re-runs over **stored** pairs at ~$3–5 each. The
  `supersede` mechanism preserves the replaced findings, so re-running a pair is exactly
  the comparison the schema was built for.
- **Ad-hoc checks are welcome, under the session record's own rule (§7.3):** a check must
  be validated on the real text that motivated it, and its test is built from the exact
  text that got past the previous version. A regex that provably catches the Fable 5
  sentence beats a principled design that has not been run.
- **Measure before deciding.** Every issue names the number to get first. Options are
  listed to be tested, not to be argued; several issues deliberately end in "build the
  instrument, then choose".
- **Changes to lexicons or ranking change the model's input.** STATUS feeds severity,
  excerpt selection, *and* the order the session reads changes in. Any such change gets a
  version stamp in the run reports (the same reasoning as `PROMPT_VERSION`) and one graded
  A/B on a stored pair before it becomes the default.

## The issues

| # | Issue | Kind | Answers |
|---|---|---|---|
| [01](../issue/accuracy/01-verdict-ledger.md) | Persist audit verdicts; make grading cumulative | code + process | no running accuracy metric; grades evaporate; mixed audit methods |
| [02](../issue/accuracy/02-restriction-lexicon.md) | The status lexicon cannot see "cannot" | code + measurement | verified STATUS gaps; severity/excerpt blindness |
| [03](../issue/accuracy/03-newness-coverage.md) | Newness check: invisible identifiers, cited-page scope | code + measurement | verified regex gaps; "anywhere in the old text" checked nowhere |
| [04](../issue/accuracy/04-invented-contrast.md) | Verify claims about the past | code + measurement | the most common model error has no detector |
| [05](../issue/accuracy/05-missed-restrictions.md) | An absence detector for restrictions | code + measurement | the worst error class — findings never written |
| [06](../issue/accuracy/06-prompt-size.md) | The 198k-token prompt: collapse, count, re-probe | code + measurement | recall validated at 105k, run at 198k; terse flood |
| [07](../issue/accuracy/07-reappearing-lines.md) | Mark reappearing lines in diffs and excerpts | code | false newness prevented at the source |
| [08](../issue/accuracy/08-tiny-change-severity.md) | Severity density and the one-line change | decision, gated | 63 of the top 100 are ≤100 characters |
| [09](../issue/accuracy/09-fetch-path-convergence.md) | One fetch path, always archived | code | the `--fetch` trap; unrecoverable bytes |
| [10](../issue/accuracy/10-standing-instruments.md) | Promote one-off measurements into instruments | code | instrument drift between windows |
| [11](../issue/accuracy/11-raw-noise-canary.md) | Detect a new noise pattern before an event does | code + measurement | reactive noise-pattern discovery |
| [12](../issue/accuracy/12-date-keyed-paths.md) | Corpus paths keyed on a vendor-controlled date | decision | the re-date relocated 71% of the corpus |

## Dependency order

```
09 (insurance; no measurement needed, do first)

01 --------+----------------------------+
02 --------+--> 05                      +--> 08
03 (C) ----+                            |
04, 06, 07 are built independently but measured against 01

10 --> 11        12 independent (its option C is small; option A gated on inventory)
```

- **01 is the keystone.** Issues 02–08 can all be *built* without it — each validates on
  its motivating real case — but none can claim "accuracy improved" without it, and the
  grades for the three existing run/prompt combinations are recoverable from the session
  record **now, while they are fresh**. They decay with memory; import them first.
- **02 before 05**: the absence detector consumes the restriction lexicon, and the two
  have different precision needs, which is why the lexicon issue proposes splitting them.
- **09 stands alone and is urgent** in a way nothing else here is: a fetch that skips
  archiving destroys bytes the next fetch overwrites. Every other issue can wait a window;
  this one loses data per occurrence.
- **10 before 11**: the canary is one of the instruments.

## Cost of the whole plan

Deterministic work throughout; the only model spend is experiments. A full experimental
pass — re-running both stored pairs once per candidate change worth an A/B, call it four
re-runs — is under $25 total, against a pipeline that already spends ~$5/run weekly. The
count-tokens endpoint used by [06](../issue/accuracy/06-prompt-size.md) is free. Nothing
here scales model calls with corpus size or change volume.

## What would change this plan

- If the graded ledger ([01](../issue/accuracy/01-verdict-ledger.md)) shows v2 accuracy is
  already dominated by one error class, the issue order inverts to chase that class first;
  the sequencing above assumes the session record's ranking of error importance holds.
- If the absence-detector scan ([05](../issue/accuracy/05-missed-restrictions.md)) fires
  on hundreds of candidates per run rather than dozens, its injection option dies and the
  issue reduces to a human-review appendix — the candidate count is the first number it
  collects.
- If the re-probe ([06](../issue/accuracy/06-prompt-size.md)) shows recall intact at 198k,
  the terse collapse becomes a pure cost fix and can be deprioritised accordingly.
