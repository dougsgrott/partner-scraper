# Accuracy: the post-review issue set

> Opened 2026-09-18, from the external review of
> [`docs/session-2026-09-18-lessons.md`](../../docs/session-2026-09-18-lessons.md). The
> plan these issues implement is [`docs/accuracy-plan.md`](../../docs/accuracy-plan.md);
> read that first — it carries the standing constraints (no new standing model calls;
> ad-hoc checks welcome but validated on real text; measure before deciding; version
> anything that changes the model's input).

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
| [02](02-restriction-lexicon.md) | The status lexicon cannot see "cannot" | open | code + measurement |
| [03](03-newness-coverage.md) | Newness check: invisible identifiers, cited-page scope | open | code + measurement |
| [04](04-invented-contrast.md) | Verify claims about the past | open | code + measurement |
| [05](05-missed-restrictions.md) | An absence detector for restrictions | open | code + measurement |
| [06](06-prompt-size.md) | The 198k-token prompt: collapse, count, re-probe | open | code + measurement |
| [07](07-reappearing-lines.md) | Mark reappearing lines in diffs and excerpts | open | code |
| [08](08-tiny-change-severity.md) | Severity density and the one-line change | open | decision, gated on 01 |
| [09](09-fetch-path-convergence.md) | One fetch path, always archived | open | code |
| [10](10-standing-instruments.md) | Promote one-off measurements into instruments | open | code |
| [11](11-raw-noise-canary.md) | Detect a new noise pattern before an event does | open | code + measurement |
| [12](12-date-keyed-paths.md) | Corpus paths keyed on a vendor-controlled date | open | decision |

## Dependency order

```
09 first — it is insurance, not measurement, and each missed archive is unrecoverable.

01 --------+----------------------------+
02 --------+--> 05                      +--> 08
03 (opt C) +                            |
04, 06, 07: built independently, measured against 01's graded ledger

10 --> 11        12 independent (small option C; large option A gated on inventory)
```

Issues deliberately offer **multiple options with trade-offs rather than one design**,
because most of the choices hinge on numbers nobody has measured yet — candidate counts,
false-positive rates, recall at 198k tokens. Each issue names the number to get first.
