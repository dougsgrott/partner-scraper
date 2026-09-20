# Accuracy: the post-review issue set

> Opened 2026-09-18, from the external review of
> [`docs/session-2026-09-18-lessons.md`](../../docs/session-2026-09-18-lessons.md). The
> plan these issues implement is [`docs/accuracy-plan.md`](../../docs/accuracy-plan.md);
> read that first — it carries the standing constraints (no new standing model calls;
> ad-hoc checks welcome but validated on real text; measure before deciding; version
> anything that changes the model's input).
>
> **Revised 2026-09-19.** The A/B arms are recorded in
> [`docs/digest-experiments-2026-09-19.md`](../../docs/digest-experiments-2026-09-19.md):
> issues 02–05 carry their outcomes, 06–09 carry their implications as revision notes,
> and [13](13-boost-adoption.md) carries the adoption decision they opened. One rule the
> arms hardened for every remaining A/B: **one input change per arm** — the combined
> arm's interference terms are the evidence.

## Why this set exists

The digest's accuracy history has a shape: every check was built from a real failure, and
every check is shaped like *that failure* rather than the failure class. Dotted-version
regexes for a "names asserted new" problem; cited-page scope for an "anywhere in the old
text" rule; newness-only checks for a "contrast with the past" pattern. The session record
states the principle that predicts this — *a synthetic test written by the author of the
check shares the author's blind spot* — and the same holds for checks written from single
incidents.

Two of the gaps were verified by running code on 2026-09-18, not by reading it: the STATUS
lexicon does not match `cannot`/`requires`/`rejected` (so the pair's most consequential
sentence carried no status signal), and the newness identifier extraction returns nothing
for single-number versions ("DBR 18", "Claude Fable 5", "AI v6") — the class both recent
misses fall into.

The other structural fact: **manual audit verdicts are not persisted anywhere**, so no
prompt or ranking change can be scored against the last one. `PROMPT_VERSION` exists so
runs can be compared; nothing compares them. Issue 01 fixes that and gates the "measured"
acceptance criteria of most of the rest.

## The issues

| # | Issue | Status | Kind |
|---|---|---|---|
| [01](01-verdict-ledger.md) | Persist audit verdicts; make grading cumulative | implemented 2026-09-18 | code + process |
| [02](02-restriction-lexicon.md) | The status lexicon cannot see "cannot" | done 2026-09-19 — A/B graded 100% vs 70%; boost recommended for default | code + measurement |
| [03](03-newness-coverage.md) | Newness check: invisible identifiers, cited-page scope | measured 2026-09-18 — broadenings rejected; region FP + silent skip fixed | code + measurement |
| [04](04-invented-contrast.md) | Verify claims about the past | done 2026-09-19 — quote check ships; rule A/B graded 90%, not adopted | code + measurement |
| [05](05-missed-restrictions.md) | An absence detector for restrictions | done 2026-09-19 — scan ships; injection A/B graded 90% but anchoring confirmed, not adopted | code + measurement |
| [06](06-prompt-size.md) | The 198k-token prompt: collapse, count, re-probe | done 2026-09-20 — collapse A/B graded 89% at −55% input tokens and **adopted: PROMPT_VERSION 4** (`--no-collapse-terse` records `-c`); `+m` ungraded | code + measurement |
| [07](07-reappearing-lines.md) | Mark reappearing lines in diffs and excerpts | done 2026-09-20 — second-pair confirm: mechanism endpoints held (0 invented-past, 4/4 needles) but 72% vs sibling 89%; v4 candidacy declined | code + measurement |
| [08](08-tiny-change-severity.md) | Severity density and the one-line change | done 2026-09-19 — option D by measurement: the head's one-liners are half the graded-true material; A and B bury it | decision |
| [09](09-fetch-path-convergence.md) | One fetch path, always archived | done 2026-09-19 — both entry points route through `generations.archive_after`; landed before the next refresh | code |
| [10](10-standing-instruments.md) | Promote one-off measurements into instruments | done 2026-09-19 — `measure.py` + noise registry + in-run cross-check; all recorded figures reproduced | code |
| [11](11-raw-noise-canary.md) | Detect a new noise pattern before an event does | done 2026-09-19 — canary in every fetched run (quiet 6–8% vs event 81–84%); clusterer re-derived both known patterns blind | code + measurement |
| [12](12-date-keyed-paths.md) | Corpus paths keyed on a vendor-controlled date | done 2026-09-19 — C shipped, then A adopted by Doug and executed: tree flattened, 6,771 moves all `pipeline`-attributed, snapshot #8 | decision |
| [13](13-boost-adoption.md) | Confirm and adopt the boost: baseline, sample, version axes | done 2026-09-20 — 83% vs 79% on #6→#7 after the second-grader pass (2 of 6 rows downgraded); PROMPT_VERSION 3 default stands | measurement + decision |

## Dependency order (revised 2026-09-19; 01–05 done)

```
09 first — insurance, not measurement, and the next weekly refresh is due within days.

13 next — the missing #6 → #7 full-page baseline (free), then the boost confirm run;
          decides the default flip and hands 06 and 07 their baseline on that pair.

07 — marking arm and slots arm (E), SEPARATE arms, type specimen the primary endpoint.
06 — re-probe now unblocked (per-pair needle files); collapse A/B its own arm, after 13.
08 — gate satisfied (ledger live); 02's density-cap measurement is its sharpest input.

10 --> 11        12 independent (small option C; large option A gated on inventory)
```

Issues deliberately offer **multiple options with trade-offs rather than one design**,
because most of the choices hinge on numbers nobody has measured yet — over/under-pairing
rates, recall at 198k tokens, the rank distribution of graded-true pages. Each issue
names the number to get first, and every arm that changes the model's input runs alone.
