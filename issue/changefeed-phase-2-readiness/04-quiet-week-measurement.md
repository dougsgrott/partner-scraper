# 04 — Second measurement in a quiet week

**Status:** partially done (2026-08-29) — code complete, measurement calendar-gated
**Kind:** operational + code · **Depends on:** nothing
**Blocks:** [05](05-decide-phase-2-architecture.md)

> **Revised.** This issue bundled three things: a measurement that can only be taken after
> waiting a week, a code gap around deleted pages, and an open question about what `added`
> means. The two that did not need a calendar are now done. The measurement is the only
> thing still outstanding in this whole issue set.

## Part 1 — the measurement (still outstanding)

Anthropic's measured churn was **650 of 661 pages (98.3%) in 11 days**. Real — the diffs are
genuine content edits — but the window contained a model launch and a docs reorganisation:
new `/docs/en/models/opus-5`, `/models/sonnet-5`, `/models/fable-5` paths, 127 new pages,
`api/beta/*` promoted to `api/*`, and version bumps across examples (CLI 1.22.1 → 1.27.0,
Go 1.22 → 1.25, Python 3.9 → 3.10).

Only **2%** of Anthropic pages changed purely by link rewriting, so this is a genuine
site-wide refresh rather than one mechanical event. Either way it is an event week, and
**Anthropic's steady-state rate remains unknown.**

That matters because Anthropic is the vendor with **no `updated_date` and no usable HTTP
validator** — every sampled Databricks `Last-Modified` is the deploy timestamp, and Anthropic
sends none at all. A snapshot diff is the only instrument that can measure it.

Databricks needs no second measurement: 399/week measured against the 250–450/week
`updated_date` estimate confirms the proxy works there.

### How to take it

Wait for a week with no obvious Anthropic release, then:

```bash
uv run python scripts/changes.py snapshot --label quiet-start
# ... wait ...
uv run python scripts/fetch.py --refresh        # ~2 h at 1 req/s
uv run python scripts/extract.py
uv run python scripts/changes.py run --label quiet-end
```

**Do not change an extractor inside the window.** A moved fingerprint attributes every
co-occurring vendor change to us — the failure that corrupted the first run. Finish and
re-extract *before* `quiet-start`, never between the two snapshots.

Judging "quiet" is a matter of checking whether Anthropic shipped a model or restructured
paths in the window; the release notes and the appearance of new top-level path segments in
the added-pages list both show it.

Compare the result against **~414/week** from the launch window. A large gap is the expected
and useful outcome — it says the feed's volume is event-driven, which is itself an input to
[05](05-decide-phase-2-architecture.md).

### Measured (2026-09-18)

Pair #6 → #7, 9.06 days, no model launch, no extractor change (0 `pipeline`, 0 `unknown`).
Anthropic: **610 changes, ~471/week**, against ~414/week in the launch window. **The expected
large gap did not appear.** 82% of modified pages are API reference. Hand-written pages ran
~79/week. Figures and caveats are in `docs/changefeed.md`. The window is not fully quiet:
61 of the 63 added pages are the Admin API republished under `api/beta/organization/*`.

## Part 2 — deleted pages are now visible (done)

The refresh hit one 404:

```
! 404  https://docs.databricks.com/aws/en/oltp/instances/query/notebook
```

**The feed said nothing about it, and would have said nothing forever.**
`FetchDB.record_error` preserves the last good archive entry — correctly, so one bad minute
on a vendor's server cannot destroy a page — but the index row was preserved with it, and the
extract loop skipped the URL before it was even counted as a candidate. The page kept its
`ok` row, kept reporting as unchanged, and silently missed every pipeline update including
`body_fingerprint` five days later.

**Implemented:**

- `gone` is now an index status, set by the next extract pass when a fetch *reached* the
  server and was told 404 or 410. A timeout, a reset or a 5xx changes nothing — the status
  code is the only thing separating "the vendor removed this" from "the network was unhappy".
- Snapshots capture `ok` rows, so a gone page leaves the next snapshot and the change feed
  reports it as **`removed`** — the signal the deprecation and link-rot watches need
  (`docs/kb-application.md` items 16 and 18).
- **The corpus file is kept**, and the `gone` row still claims it, so `--prune` leaves it
  alone and the integrity check does not start failing when a vendor deletes a page.
  Deleting on the strength of one HTTP response is destructive inference. The trade-off is
  recorded in `docs/changefeed.md`: anything globbing `data/` without consulting the index
  will serve a deleted page as current.

**Verified on the real corpus:** `extract.py` reported `gone 1`; snapshot #4 came back with
6,563 pages instead of 6,564; `diff 3 4` reported `removed 1`. The file is still on disk and
`orphans` is 0.

The original issue offered an N-consecutive-404 rule as the most conservative option. It was
not built: it needs a counter `fetch.db` does not have, and keeping the file already removes
the destructive part of the risk. A single spurious 404 costs one wrong `removed` line in one
report, and the next successful fetch restores the page to `ok`.

## Part 3 — what `added` means (resolved, no code needed)

`added` conflated two different things: a page new upstream, and a page that was always there
but only just entered our worklist. The run selected 6,566 URLs against 6,404 before, so the
question was live.

**Resolved from data already held.** All 34 Databricks additions carry an `updated_date`
between **2026-08-18 and 2026-08-28** — after the previous crawl. The vendor published them
inside the window; none is an old page we just noticed.

The 127 Anthropic additions cannot be settled this way, because that source publishes no
`updated_date`. Their paths (`/models/opus-5`, `/models/sonnet-5`, `/models/fable-5`) place
them in the launch, which is strong but circumstantial. Separating the two cases properly
would need a first-seen column in `fetch.db` — `fetched_at` is overwritten on every fetch —
and that has not been worth a schema change to the one database a crawl costs two hours to
rebuild.

## Acceptance criteria

- [ ] A snapshot pair covering a window with no Anthropic release
- [ ] Anthropic steady-state churn recorded in `docs/changefeed.md` beside the launch-week
      figure, clearly labelled as two different regimes
- [ ] No extractor change inside the measurement window
- [x] 404 handling decided, implemented, and tested
- [x] The `added` ambiguity resolved, or its limits stated

## Tests added

- a page gone upstream leaves the snapshot and reports as `removed`
- a gone page keeps its file and is not an orphan
- marking gone is idempotent and will not resurrect an unknown URL
- only a real 404/410 counts — a 503 or a bare connection error does not
