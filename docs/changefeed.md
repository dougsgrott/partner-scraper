# The change feed

> The first application built on the corpus — item 14 of
> [`kb-application.md`](kb-application.md). Design and rationale:
> [`changefeed-plan.md`](changefeed-plan.md).

The scraper answers *what do the vendors' docs say?* This answers *what did they change?*

Phase 1 is deterministic end to end: no model, no tokens, and no network unless you ask
for a refresh. It exists to make the corpus a time series, and to measure how much of it
actually moves between runs — a number nobody has ever had, because until now nothing
retained a before-state.

## Quick start

```bash
# 1. Record where the corpus stands today. ~18 s, no network.
uv run python scripts/changes.py snapshot --label baseline

# 2. Later — get fresh bytes, re-extract, snapshot again, diff, report.
uv run python scripts/changes.py run --fetch

# Or, without touching the vendors' servers, over whatever is already in raw/:
uv run python scripts/changes.py run
```

`run` is the single manual command that stands in for the scheduled cadence PLAN.md
defers. **`--fetch` is opt-in** — without it nothing hits the network, so the feed can be
re-run and the report reshaped in seconds. With it, the refresh is the usual ~2 hours at
1 req/s; the rate lives in `config/sources.yaml` and there is no flag here to raise it.

## What a change actually is

Three orthogonal facts are recorded about every page that differs.

**`kind` — what happened**

| | |
|---|---|
| `added` | the page is new to the corpus |
| `removed` | it is gone — either deleted upstream, or dropped from the worklist |
| `modified` | its body changed |
| `moved` | identical body, different file (its category or date bucket rolled over) |
| `metadata` | identical body, but the title, description, category or `updated_date` moved |

### Pages that disappear upstream

A page that 404s is marked `gone` in `index.db` by the next extract pass, drops out of the
next snapshot, and reports as `removed`. Only a fetch that *reached* the server and was told
404 or 410 counts; a timeout, a reset or a 5xx changes nothing.

This did not work before 2026-08-29 and the failure was silent. `FetchDB.record_error`
preserves the last good archive entry — correctly, so one bad minute on a vendor's server
cannot destroy a page — but the index row was preserved with it, so a deleted page kept
reporting as **unchanged forever**. The first measurement run had exactly one such page and
the feed said nothing.

**The corpus file is kept on disk**, and the `gone` row still claims it, so `--prune` leaves
it alone and the integrity check does not start failing when a vendor removes a page.
Deleting on the strength of one HTTP response is destructive inference. The cost of that
choice: anything that globs `data/` without consulting the index will serve a deleted page as
current, so consumers that care should read `status` from `index.db`.

**`cause` — who did it.** The distinction the whole package exists for.

| | |
|---|---|
| `content` | the vendor changed the page |
| `pipeline` | **we** changed the extractor; not a vendor change |
| `unknown` | no `body_fingerprint` on one side, so the cause is not established |

A content hash moving does not mean anyone upstream edited anything. Re-running a revised
extractor moves the hash of every page it touches — the MDX conversion rewrote all 566
Anthropic pages in a single pass. **`body_fingerprint`** covers the extractor and the
modules it is built from, so it moves exactly when the code that decides a page's *body*
moves. Pages attributed to `pipeline` are reported in their own section and never appear in
the feed.

### Why there are two fingerprints

`index.db` stores both, and they answer different questions:

| | covers | answers |
|---|---|---|
| `output_fingerprint` | extractor + imports + writer + layout | should this page be re-extracted? |
| `body_fingerprint` | extractor + imports | did *we* change what this page says? |

Attribution uses the second and ignores the first. The first version of this check used
`output_fingerprint` for both, and the first real measurement run showed why that is wrong:
a one-line `writer.py` edit — which can only touch the frontmatter — together with a
widening of the fingerprint *formula* made **594 genuine Databricks changes report as our
own churn**. Because the value is stored per page at extract time, changing how it is
computed silently invalidated every stored comparison at once.

The rule that falls out: **anything added to `body_fingerprint` must be able to change the
body.** The writer decides the frontmatter and layout decides the path; neither qualifies.

`unknown` shows up when the index was rebuilt from `data/`, or for snapshots taken before
`body_fingerprint` existed, because neither fingerprint is stated in the frontmatter. It is
deliberately not folded into `content`: presenting our own churn as the vendor's is the
specific failure being guarded against, and a smaller honest feed beats a larger wrong one.

**`weight` — whether it is worth reading.** `substantive`, `low`, or `noise`. A change with
any signal at all is substantive; one with none is ranked by size, so a reflow is `noise`
and a reworded sentence is `low`.

**`severity` — how far up the feed it belongs.** The number that actually matters, because
in a typical run ~680 changes are substantive and no threshold honestly reduces that to a
readable handful. Measurement is blunt about this: 84% of changes move a link, heading, code
block or number, and the median change rewrites 19% of its page. The corpus really does
change that much. So the feed is **ordered by severity**, and the top thirty is what a person
reads.

Five signals feed the score, each counted as the *share of changed lines carrying it*:

| signal | weight | why |
|---|---|---|
| `status` | 4 | deprecated, no longer, not supported, beta, generally available |
| `code` | 3 | examples are what people copy |
| `headings` | 2 | sections appearing or disappearing |
| `numbers` | 2 | limits, versions, sizes |
| `links` | 1 | a moved destination, often a restructure |

`status` was added after reading a stratified sample of 64 real diffs. It was the only signal
that caught a SQL property becoming "no longer supported", a function leaving Beta, and a
model quietly dropped from a supported-model table — and it fired on neither of the two
genuinely editorial changes in the sample.

**Density, not volume, and never size.** Scoring by raw counts filled the top of the feed with
regenerated API reference pages: one matched the status pattern on 11,181 lines simply
because it is enormous. Density surfaces the small sharp changes instead — a swapped beta
header, a region's supported models changing, the Python tool runner losing automatic
compaction. Size is not a term in the score at all; the largest change in the first run
rewrote 4.2 MB of a machine-generated dump.

Each feed entry shows its evidence — `severity 6.0 (status ×2, numbers ×1, links ×2)` —
because a ranked feed a reader cannot interrogate is one they will not trust.

**Weight ranks; it never filters.** Ranked-down changes are still counted and still listed
by URL — just not expanded. A feed that silently drops things cannot be audited, and a
reader has no way to notice an omission.

## Commands

| | |
|---|---|
| `snapshot [--label L]` | record the corpus as it stands now |
| `list` | snapshots taken so far, and the size of the version store |
| `diff [A B] [--json] [--write]` | compare two snapshots; defaults to the last two |
| `run [--fetch]` | snapshot → [fetch] → extract → snapshot → diff → report |
| `log URL` | every recorded version of one page |
| `show URL [--snapshot N]` | print a stored body out of the version store |
| `gc [--keep N]` | drop old snapshots and the bodies nothing references |

`A` and `B` accept a snapshot id (`3`, `#3`), a label (`baseline`), or a position
(`latest`, `previous`).

Every command takes `--index-db`, `--changes-db`, `--blob-dir`, `--report-dir` and
`--data-root`, so a feed can be computed over a corpus that lives elsewhere — the index
stores paths relative to wherever `extract` ran, and `--data-root` supplies that prefix.

## Where the history lives

```
state/changes.db              snapshots + one page_versions row per page per snapshot
state/changes/blobs/ab/ab….gz page bodies, gzipped, addressed by content hash
reports/changefeed/0001..0002.md   the rendered feed (and .json beside it)
```

**Bodies are addressed by the corpus's own `content_hash`.** `writer.content_hash` is
`sha256(markdown.strip())` and that is exactly what `writer.render` writes, so a body read
back off disk hashes to the value already in its frontmatter. Deduplication falls out for
free: a page that did not change stores no new bytes.

Measured on the real corpus:

| | |
|---|---|
| full diff of 1,116 changes | **17 s** (10 min before `difflib` left the ranking path) |
| first snapshot | 6,403 pages · 6,401 bodies · **16.8 MiB** · 18 s |
| second snapshot, corpus untouched | 6,403 pages · **0 new bodies** · 0 bytes |
| second snapshot, 6 pages changed | 6,403 pages · **4 new bodies** · 9 KiB |

(6,401 bodies for 6,403 pages because two pairs of pages share identical content.)

**`state/changes.db` is the one database here that is not rebuildable.** `data/` holds a
single version of each page and `index.db` is derived from it, but the history exists
nowhere else — losing it loses the past. Worth backing up in a way the other two are not.

## Measured churn

The first real measurement, snapshots #1 → #2, covering **2026-08-18 → 2026-08-29** (11 days).

**1,277 pages changed body** — 19.9% of the corpus, ~813/week.

| | changed | of | rate |
|---|---|---|---|
| Databricks | 627 (593 modified + 34 added) | 5,742 | 10.9% / 11d → **~399/week** |
| Anthropic | 650 (523 modified + 127 added) | 661 | 98.3% / 11d |
| **total** | **1,277** | 6,403 | **~813/week** |

Also in the window: 49 pages moved file, 8 changed metadata only, 0 removed.

**The 161 additions are new to the corpus — which is not quite the same as new upstream.**
All 34 Databricks additions carry an `updated_date` between 2026-08-18 and 2026-08-28, after
the previous crawl, so the vendor published them inside the window. The 127 Anthropic
additions cannot be settled the same way (no `updated_date` on that source), though their
paths (`/models/opus-5`, `/models/sonnet-5`, `/models/fable-5`) place them squarely in the
launch.

**Five of those 127 are not new content at all.** Anthropic kept both URL trees live through
the restructure, and both are in the sitemap, so the corpus holds the same bytes twice:

```
about-claude/models/overview          =  models/overview
about-claude/models/whats-new-opus-5  =  models/opus-5/whats-new-opus-5
release-notes/system-prompts          =  release-notes/system-prompts/overview
```

`validate.py`'s `duplicate_bodies` check reports 21 such groups corpus-wide. The existing
`duplicate` status cannot catch them: it detects two URLs resolving to the same *file path*,
and these resolve to different paths. The effect on the churn figure is within rounding — 5
of 1,277 — but `added` means "new to the corpus", and this window is where that distinction
stopped being theoretical.

Separating new-upstream from newly-discovered for Anthropic would need a first-seen column in
`fetch.db`, which does not exist and has not been worth adding.

**0 removed is real, but only because nothing was deleted in this window that we could see.**
The one page that did 404 (`oltp/instances/query/notebook`) was invisible to the feed until
`gone` handling landed; it now reports as `removed` in the #3 → #4 diff.

**Databricks validates the `updated_date` proxy.** 399/week measured against 250–450/week
estimated from the `.theme-last-updated` stamp. That estimate can be trusted going forward,
which matters because it is available without a snapshot diff.

**Anthropic's 98.3% is an event week, not a baseline.** The window contained a model launch
and a docs reorganisation: new `/docs/en/models/opus-5`, `/models/sonnet-5`,
`/models/fable-5` paths, 127 new pages, and `api/beta/*` promoted to `api/*`. Only 2% of
Anthropic pages changed *purely* by link rewriting, so this is a genuine site-wide refresh
rather than one mechanical event. Its steady-state rate is still unknown — see
`issue/changefeed-phase-2-readiness/04-quiet-week-measurement.md`.

**Measured without a launch (2026-09-18), and it is not lower.** Pair #6 → #7 is 9.06
days, fetch to fetch. No model shipped. The release notes carry five feature entries
(compact-on-demand, Managed Agents `auto` permissions, `ant` CLI 1.32.0, per-message effort on
Google Cloud, Compliance API Chrome transcripts).

| Anthropic | launch window (#1 → #2) | no-launch window (#6 → #7) |
|---|---|---|
| changes | 650 in 11 days | 610 in 9.06 days (547 modified, 63 added) |
| per week | ~414 | **~471** |
| API reference share of modified | — | 447 of 547 (82%) |
| hand-written pages | — | 100 modified + 2 added, ~79/week |

**Volume is not event-driven. The API reference is.** It is regenerated continuously, and it
drives Anthropic churn whether or not anything launched. The 61 new pages are one event: the
Admin API republished under `api/beta/organization/*`, which also produces 132 of the
corpus's 175 duplicate-body groups (`admin/analytics/cost` = `beta/organization/analytics/cost`).

It isn't a textbook quiet week, because that republication is a new path segment. But the
hand-written count (~79/week) is the steady-state figure issue 04 asked for, and it is small.

**Databricks re-dated the whole site.** 4,805 pages moved file (all byte-identical bodies) and
229 more changed only metadata. All of them are `updated_date` jumping to 2026-09-11.
`data/databricks/<category>/<YYYY-MM>/` is keyed on that date, so one vendor rebuild relocates
71% of the corpus. Content changes were 609 modified + 76 added, ~529/week, against 399/week
before. **The `updated_date` proxy validated above is broken by this event.** It stamped
5,034 pages whose content did not change.

### Why this is written down rather than re-derivable

**The tool no longer reports these numbers.** Of the 1,116 modifications, 594 are
`unknown`-attributed, because both snapshots predate `body_fingerprint` and the wider
`output_fingerprint` moved between them. The feed for that pair therefore shows 161 changes,
not 1,277.

The figure rests on two pieces of evidence gathered by hand:

1. **Reading a sample of the 594.** All were unambiguous vendor content — new Genie Agent
   audit events, a budget-tracking behaviour change, a moved link target, a removed passkey
   restriction, an entire new section.
2. **`git show --stat 8b3f999`**, confirming that commit touched only
   `extract/registry.py` and one line of `store/writer.py`. Neither can alter a page body,
   so the extractor that produced those pages was unchanged and the vendor is responsible.

Snapshots taken from #3 onward carry `body_fingerprint` and attribute automatically; this
caveat applies only to the #1 → #2 pair.

## What a report contains

1. **Summary** — counts by kind and company.
2. **Attribution** — the `content` / `pipeline` / `unknown` split, with a banner if any
   page is not the vendor's doing.
3. **Feed** — substantive vendor changes, **ordered by severity**, each with a unified diff
   and the evidence behind its rank. Diffs truncate and say so; above 400,000 characters
   they fall back to an unaligned changed-lines listing, because aligning two 6 MB pages
   with `difflib` takes minutes for something nobody reads line by line.
4. **Ranked down** — the `low` and `noise` changes, listed by URL.
5. **Our own churn** — `pipeline` pages, captioned as ours.
6. **Unattributed**, and any pages whose stored bodies could not be read.

The `.json` beside it carries every change with nothing ranked away. That is what the
phase 2 triage layer will read.

## Phase 2

The Claude Agent SDK layer — semantic summaries, impact classification, a digest — is
**designed but not yet built**. The decision record is
[`changefeed-phase-2.md`](changefeed-phase-2.md).

Short version: every change compresses to a one-line record, the whole run is **92k tokens**,
and it goes to **one** session rather than being batched, pre-filtered, or clustered. The
session gets read-only tools to open the full diff for anything it wants to inspect, and
reports through a tool call so the digest renders from structured rows.

That decision waited on a real measurement, and the measurement is what settled it: at 1,182
changes per run the three obvious architectures — batched triage, a cheap pre-filter, and
deterministic clustering — all exist to work around a context limit that compression removes.

The phase-1 layer above is what produced the numbers, and is required by any of those designs,
so none of it was a bet.

## See also

- [`changefeed-plan.md`](changefeed-plan.md) — why it is built this way, with the churn
  figures measured from the corpus
- [`changefeed-phase-2.md`](changefeed-phase-2.md) — the digest architecture, decided
- [`kb-application.md`](kb-application.md) — the catalogue of applications this comes from
- [`lessons-learned.md`](lessons-learned.md) — §17, the fingerprint trap this guards
