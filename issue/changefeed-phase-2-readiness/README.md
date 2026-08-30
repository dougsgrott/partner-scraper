# Change feed: phase-2 readiness

> Opened 2026-08-29, after the first real measurement run (snapshots #1 -> #2).
> Every figure below traces to `reports/changefeed/0001..0002.json`.

## Why this set exists

Phase 1 of the change feed ([`docs/changefeed.md`](../../docs/changefeed.md)) shipped and
did its job: it produced churn numbers that had never existed, because nothing had ever
retained a before-state. It also produced two defects that make its output untrustworthy —
in opposite directions.

**It over-reports our own churn.** 594 pages were attributed to `pipeline` — "we changed
the extractor" — in a run where no code changed at all. Reading the diffs showed they are
genuine vendor changes.

**It under-ranks nothing.** 1,084 of 1,116 modifications (97.1%) came back `substantive`.
The ranking that was supposed to make a thousand-page feed readable filters nothing.

Neither is a small bug. The first makes the feed lie about who changed what, which is the
one thing the package was built to get right. The second makes the phase-2 architecture
decision unanswerable, because the volume reaching a model depends entirely on how much the
deterministic layer removes first.

## What the run measured

**1,277 pages changed body in 11 days** — 19.9% of the corpus, ~813/week.

| | changed | of | rate |
|---|---|---|---|
| Databricks | 627 (593 modified + 34 added) | 5,742 | 10.9% / 11d -> ~399/week |
| Anthropic | 650 (523 modified + 127 added) | 661 | 98.3% / 11d |

Databricks validates the `updated_date` proxy — 399/week measured against 250-450/week
estimated. Anthropic's 98.3% is real but reflects a model launch plus a docs
reorganisation (new `/docs/en/models/opus-5`, `/models/sonnet-5`, `/models/fable-5` paths,
127 new pages, `api/beta/*` promoted to `api/*`). Its steady-state rate is still unknown,
which is what issue 04 exists to get.

## The issues

| # | Issue | Status | Kind |
|---|---|---|---|
| [01](01-split-body-fingerprint.md) | Split `body_fingerprint` from `output_fingerprint` | **done** | code |
| [02](02-rework-change-weighting.md) | Rework change weighting against real ground truth | **done** | code + measurement |
| [03](03-rediff-and-evaluate.md) | Re-diff #1 -> #2 and evaluate both fixes | **done** | evaluation |
| [04](04-quiet-week-measurement.md) | Second measurement in a quiet week | **code done**, measurement calendar-gated | operational + code |
| [05](05-decide-phase-2-architecture.md) | Decide the phase-2 architecture | **done** | decision record |

### Where it stands (2026-08-30)

**Phase 2 stage 1 is built and the recall risk is measured.** A run compresses to ~105k
tokens; asked to find each of ten needles verified by reading, the model found **4/4** of the
ones a top-30 digest had passed over — including one at rank **1113 of 1,116** that the
deterministic ranking scores 0.00. There is no long-context failure to design around, so the
hierarchical fallback stays unbuilt. Details in
[`docs/changefeed-phase-2.md`](../../docs/changefeed-phase-2.md).

### Where the issue set stands (2026-08-29)

01-03 are complete. Attribution no longer reports our own churn as the vendor's — the 594
false `pipeline` attributions are gone and the 522 correct ones survived. The feed is ordered
by severity instead of alphabetically, and a full diff of 1,116 changes runs in **17 seconds**
rather than ten minutes. The measured churn is recorded in
[`docs/changefeed.md`](../../docs/changefeed.md) § Measured churn, with its provenance,
because the tool itself can no longer restate it for that snapshot pair.

Two premises in this set turned out to be wrong, and both are documented in place rather
than quietly edited away:

- **02** assumed the ranking was broken because it marked 97% of changes substantive.
  Measurement said the corpus genuinely changes that heavily; the real defects were an
  alphabetical feed, a missing status-language signal, and a `difflib` bottleneck.
- **03** listed a change that was never real — a token-lifetime limit moving 730 → 1460 days,
  which had been *injected* into a scratch corpus during an end-to-end test. A test fixture
  had leaked into a findings list.

**05 is decided** — [`docs/changefeed-phase-2.md`](../../docs/changefeed-phase-2.md). None of
its three candidate architectures was chosen: a run compresses to 92k tokens, so it fits in
one context window and the batching, pre-filtering and clustering options were all working
around a limit that does not exist. That also unblocked 05 from 04, since the design holds
across the whole plausible volume range.

**04** turned out to bundle three things. Its two code parts are done: pages deleted upstream
now surface as `removed` (they were invisible — a 404 left the index row untouched and the
page reported as unchanged forever), and the `added` ambiguity is resolved for Databricks
from data already held. Only the measurement itself remains, and it is waiting on a quiet
week rather than on work.

## Dependency order

```
01 --+
     +--> 03 --+
02 --+         +--> 05
           04 -+
```

- **01 and 02 are independent** and can be done in either order or in parallel.
- **03 needs both.** It is the cheap proof that the two fixes actually work, run against
  1,116 real diffs that are already stored — no network, no re-fetch.
- **04 is independent of everything** and is gated by the calendar, not by work. Start the
  waiting period early.
- **05 needs 03 and 04.** Deciding before then repeats the mistake this whole sequence was
  created to avoid: choosing an architecture on a number nobody has measured.

## Standing rule that came out of this run

**Never bundle an extractor change with a refresh.** When the fingerprint moves, every
vendor change that happened in the same window is attributed to us. That is precisely what
corrupted the first measurement. Snapshot first, change code separately, re-extract, and
only then refresh.
