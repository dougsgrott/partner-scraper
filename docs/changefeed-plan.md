# Change intelligence, phase 1: the deterministic layer

> Written 2026-08-29. The churn figures in [What is already known](#what-is-already-known-about-churn)
> are measured from the corpus as of the 2026-08-18 crawl, not estimated. Re-measure before
> quoting them elsewhere.

## Context

[`kb-application.md`](kb-application.md) §C argues that the two-stage architecture makes the
corpus a time series rather than a snapshot, and that item 14 — the documentation diff feed
— is the capability no competing approach has. This is the first application built on the
corpus, in a monorepo alongside the scraper.

**Planning it turned up a gap between that document and the code.** Item 19 claims `raw/`
accumulates a versioned history once a scheduled run exists. It does not:
`rawstore.write()` writes each URL to a fixed path, `fetch.db` and `index.db` both upsert
by URL, and `raw/`, `data/` and `state/` are all gitignored. Every refresh overwrites the
prior state with no trace. **The corpus has no time dimension at all.** The architecture
*enables* change intelligence; nothing currently retains the "before" that it needs.

So phase 1 builds the instrument, not the report.

## Why this phase stops short of the Agent SDK

The agent design — one session per ~25 changed pages, versus one per page, versus a
two-pass cheap-filter-then-deep-agent — turns entirely on how many pages actually change
per run. Nobody knows, because nothing has ever retained a before-state. Choosing now would
be guessing.

Everything in this plan is required by **every** one of those options: snapshot, version
store, diff, cause attribution, noise classification. None of it is contingent on the agent
decision, so building it is not a bet — it is the instrument that produces the number that
decides. Phase 2 gets planned once a real run has reported actual churn.

## What is already known about churn

| | pages/week | % of 5,742 |
|---|---|---|
| median week (20 weeks) | 144 | 2.5% |
| recent 8 weeks | 250–450 | 4–8% |
| worst week (wk23) | 1,045 | 18.2% |

482 pages — 8.4% — carry an `updated_date` within 7 days of the crawl.

`updated_date` is read from `.theme-last-updated`, which Docusaurus renders from the source
file's commit date (`src/scraper/extract/docusaurus.py:59`). 225 distinct values spread
across three years confirm it is a per-page content signal and not a build stamp. Three
caveats shape the design:

1. **It is an upper bound on *content* churn.** Week 23's 1,045 is almost certainly a bulk
   restructure — 999 of those pages share a single date — not 999 genuine edits.
2. **Anthropic is entirely unmeasured.** 0 of 661 pages carry `updated_date`; 0 have an
   ETag or `Last-Modified`. There is no existing signal for that half of the corpus.
3. **HTTP validators cannot serve as a content signal.** Every sampled Databricks
   `Last-Modified` is the same timestamp — `Mon, 17 Aug 2026 23:21:51 GMT` — across
   unrelated pages. It is the deploy time. This is the same effect that made a rebuild
   change all 5,743 pages' bytes while leaving their content alone
   ([`lessons-learned.md`](lessons-learned.md)).

## The trap this design exists to avoid

A `content_hash` move does **not** mean the vendor changed the page. The MDX conversion
rewrote all 566 Anthropic pages. `index.db`'s `output_fingerprint` is exactly the signal
that separates "they changed it" from "we changed the parser", and this project has already
been bitten three times by an under-scoped fingerprint.

Attribution is therefore a first-class field on every change rather than an afterthought,
and it gets a dedicated regression test.

## Layout

`src/changefeed/`, a sibling package to `src/scraper/`. It imports `scraper`; `scraper`
never imports it. That line keeps the corpus builder testable offline and dependency-free,
and sets the pattern for applications 2..N (MCP server, error lookup, retrieval benchmark).

```
src/changefeed/
  __init__.py
  db.py          ChangeDB over state/changes.db
  blobs.py       content-addressed body store
  snapshot.py    capture the corpus as of now
  diff.py        compare two snapshots -> PageChange records
  classify.py    cause attribution + noise bucketing
  report.py      Markdown and JSON rendering
scripts/changefeed.py
```

**Phase 1 adds zero dependencies** — `gzip`, `sqlite3`, `difflib` and `hashlib` are all
stdlib. `claude-agent-sdk` arrives in phase 2 as an optional extra, so building the corpus
never requires it.

## Storage

### `state/changes.db`

```sql
CREATE TABLE snapshots (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    taken_at   TEXT NOT NULL,
    label      TEXT,
    page_count INTEGER NOT NULL,
    note       TEXT
);

CREATE TABLE page_versions (
    snapshot_id        INTEGER NOT NULL REFERENCES snapshots(id),
    url                TEXT NOT NULL,
    company            TEXT,
    source_id          TEXT,
    category           TEXT,
    title              TEXT,
    description        TEXT,
    updated_date       TEXT,
    content_hash       TEXT NOT NULL,
    output_fingerprint TEXT,
    extractor          TEXT,
    body_chars         INTEGER,
    file_path          TEXT,
    PRIMARY KEY (snapshot_id, url)
);
```

Built on `scraper.db.connect`, which is already WAL-enabled, rather than a second
connection helper.

### The version store

**The blob address is the corpus's own `content_hash`.** `writer.content_hash` is
`sha256(markdown.strip())` and `writer.render` writes exactly `markdown.strip()`
(`src/scraper/store/writer.py:40-48`, `:87-95`), so a body read back off disk hashes to the
value already sitting in its frontmatter. No second hashing scheme, deduplication falls out
for free, and every stored blob is verifiable against the file it came from.

```
state/changes/blobs/<hash[:2]>/<hash>.gz
```

`blobs.py` mirrors the `rawstore.py` idioms deliberately: gzip with `mtime=0` so identical
content yields identical files, atomic `os.replace`, and a guard rejecting anything that is
not 64 hex characters before it is used to build a path.

Storage cost: the first snapshot writes ~6,400 bodies — roughly 20 MB gzipped from 79.5 MB
of text. Subsequent snapshots write only what moved, so at the median 144 pages/week a run
adds a few hundred KB.

## Components

### `snapshot.py`

```python
take(label=None, *, index_db, data_dir, changes_db, blobs_dir) -> SnapshotResult
```

Reads every `ok` row from `index.db`, parses each file with `writer.parse`, stores the body
if its hash is not already present, and writes one `page_versions` row.

**The snapshot is self-verifying.** It recomputes `writer.content_hash(body)` and compares
it against the frontmatter's own value, reporting any mismatch as a warning. A file that
changed underneath the index is exactly the drift that would otherwise corrupt a diff
silently, and the check is free because the body is already in hand.

### `diff.py`

```python
@dataclass(frozen=True)
class PageChange:
    url: str
    kind: str       # added | removed | modified | moved | metadata
    cause: str      # content | pipeline | unknown
    weight: str     # substantive | low | noise
    before: dict | None
    after: dict | None
```

| kind | rule |
|---|---|
| `added` | url in B, not in A |
| `removed` | url in A, not in B |
| `moved` | same `content_hash`, different `file_path` (category or date bucket rolled) |
| `modified` | different `content_hash` |
| `metadata` | same `content_hash`, but title, description or `updated_date` moved |

**Cause attribution, applied to `modified`:**

- `output_fingerprint` differs between A and B → `cause="pipeline"`. We changed the
  extractor, so the change cannot be attributed to the vendor. Reported in its own section,
  never in the feed.
- fingerprints match → `cause="content"`. A real upstream change.

Unified diffs come from `difflib.unified_diff` over the two stored bodies. Ten pages exceed
500 KB (the largest is 4.77 MB), so diffs truncate at a line and character cap and the
output states when truncation happened rather than quietly eliding.

### `classify.py`

Weights `cause="content"` modifications as `substantive`, `low`, or `noise`.

**Nothing is ever silently dropped.** A feed that under-reports is worse than one that
over-reports, so the low and noise buckets are counted in the summary and listed by URL in
an appendix — merely not expanded. Whitespace-only diffs are `noise`; small deltas touching
no link, code fence or number are `low`; everything else is `substantive`.

### `report.py`

Writes `reports/changefeed/<A>..<B>.md` plus a `--json` form, which becomes phase 2's agent
input:

- snapshot identities, dates, page counts
- summary table by kind and company
- the `pipeline` section, separated and captioned as *our* changes rather than theirs
- substantive changes grouped by company then category, with truncated diffs
- an appendix listing the low and noise URLs

Table rendering gets a test asserting no blank line follows the separator row — the exact
bug that broke [`validation-scorecard.md`](validation-scorecard.md).

### `scripts/changefeed.py`

```
snapshot [--label L] [--note N]   capture corpus state now
list                              snapshots taken so far
diff [A B] [--json] [--all]       compare two snapshots (default: the last two)
run [--fetch] [--label L]         snapshot -> [fetch] -> extract -> snapshot -> diff -> report
log URL                           version history for one page
show URL [--snapshot N]           a stored body out of the version store
gc [--keep N]                     drop blobs no snapshot references
```

`run` is the single manual command that stands in for the deferred cron. **`--fetch` is
opt-in**: the default reuses what is already in `raw/`, so the whole feed is exercisable in
seconds without putting load on partner servers. With `--fetch` it calls
`run_fetch(mode="refresh")` at the configured 1 req/s. The code stays scheduler-ready — one
command, an exit code, and a JSON summary written to `state/runs/` in the existing shape —
but nothing schedules it.

## Reuse

| Need | Existing code |
|---|---|
| parse a corpus file | `scraper.store.writer.parse` |
| body hash | `scraper.store.writer.content_hash` |
| the manifest, incl. `output_fingerprint` | `scraper.store.index.Index` |
| WAL sqlite connection | `scraper.db.connect` |
| atomic gzip write idiom | `scraper.fetch.rawstore` (mirrored, not imported) |
| orchestration | `scraper.config.load_config`, `fetch.runner.run_fetch`, `extract.run_extract` |

## Tests — `tests/test_changefeed.py`

- blob round-trip; re-writing the same hash adds no bytes; a non-hex sha is rejected before
  the filesystem is touched
- a snapshot captures N pages; re-snapshotting an unchanged corpus creates **zero** new blobs
- each `kind` classified correctly, including `moved` (same hash, new path)
- **the fingerprint regression test**: a corpus where every page's `content_hash` *and*
  `output_fingerprint` moved yields 0 `content` changes and N `pipeline` changes. This is
  the test that would have caught 566 false Anthropic changes.
- whitespace-only diff → `noise`; a changed link → `substantive`
- a >500 KB diff truncates and says so
- the report table renders with no blank line after the separator

## Verification

```bash
uv run pytest -q
uv run ruff check .

uv run python scripts/changefeed.py snapshot --label baseline
uv run python scripts/changefeed.py list                    # one snapshot, ~6,403 pages
uv run python scripts/changefeed.py snapshot --label same   # expect 0 new blobs
uv run python scripts/changefeed.py diff                    # expect an empty feed
```

An empty diff between two snapshots of an untouched corpus is the strongest available smoke
test: it proves the store, the hashing and the classifier all agree that nothing happened.

Then the measurement run this phase exists for:

```bash
uv run python scripts/fetch.py --refresh    # ~2h, 1 req/s, polite
uv run python scripts/extract.py
uv run python scripts/changefeed.py run --label after-refresh
```

Expected output: exact content churn since the 2026-08-18 crawl, split by vendor —
**including the 661 Anthropic pages, for which no other signal exists** — plus the ratio
between `updated_date` churn and real `content_hash` churn. Those two numbers decide the
phase 2 agent design.

## Effort

| Task | Estimate |
|---|---|
| `db.py` + `blobs.py` | 1 h |
| `snapshot.py` | 1 h |
| `diff.py` + `classify.py` | 2 h |
| `report.py` | 1.5 h |
| CLI + `run` orchestrator | 1 h |
| Tests | 2 h |
| Docs | 45 min |
| **Total** | **≈ 9–10 h**, no new dependencies, no network beyond the opt-in refresh |

## Not in this phase

The Claude Agent SDK triage layer, the `record_finding` tool surface, batching strategy and
cost controls. All of it gets planned against real churn numbers once the measurement run
above has produced them.

## See also

- [`kb-application.md`](kb-application.md) — the catalogue this application comes from
- [`lessons-learned.md`](lessons-learned.md) — why the fingerprint trap gets its own test
- [`validation.md`](validation.md) — what the corpus has been proven to contain
