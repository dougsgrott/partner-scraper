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
| `removed` | it is gone |
| `modified` | its body changed |
| `moved` | identical body, different file (its category or date bucket rolled over) |
| `metadata` | identical body, but the title, description, category or `updated_date` moved |

**`cause` — who did it.** The distinction the whole package exists for.

| | |
|---|---|
| `content` | the vendor changed the page |
| `pipeline` | **we** changed the extractor; not a vendor change |
| `unknown` | no `output_fingerprint` on one side, so the cause is not established |

A content hash moving does not mean anyone upstream edited anything. Re-running a revised
extractor moves the hash of every page it touches — the MDX conversion rewrote all 566
Anthropic pages in a single pass. `output_fingerprint` covers the extractor, its imports,
the writer and the layout, so it moves exactly when our output pipeline moves. Pages
attributed to `pipeline` are reported in their own section and never appear in the feed.

`unknown` shows up when the index was rebuilt from `data/`, because the fingerprint lives
only in `index.db` and is not stated in the frontmatter. It is deliberately not folded into
`content`: presenting our own churn as the vendor's is the specific failure being guarded
against, and a smaller honest feed beats a larger wrong one.

**`weight` — whether it is worth reading.** `substantive`, `low`, or `noise`, from
heuristics over the changed lines: a moved link, a changed limit, a heading or a code fence
reads as substantive; reflowed whitespace is noise.

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
| first snapshot | 6,403 pages · 6,401 bodies · **16.8 MiB** · 18 s |
| second snapshot, corpus untouched | 6,403 pages · **0 new bodies** · 0 bytes |
| second snapshot, 6 pages changed | 6,403 pages · **4 new bodies** · 9 KiB |

(6,401 bodies for 6,403 pages because two pairs of pages share identical content.)

**`state/changes.db` is the one database here that is not rebuildable.** `data/` holds a
single version of each page and `index.db` is derived from it, but the history exists
nowhere else — losing it loses the past. Worth backing up in a way the other two are not.

## What a report contains

1. **Summary** — counts by kind and company.
2. **Attribution** — the `content` / `pipeline` / `unknown` split, with a banner if any
   page is not the vendor's doing.
3. **Feed** — substantive vendor changes grouped by company and category, each with a
   unified diff. Diffs truncate (a 4.77 MB page exists in this corpus) and say so.
4. **Ranked down** — the `low` and `noise` changes, listed by URL.
5. **Our own churn** — `pipeline` pages, captioned as ours.
6. **Unattributed**, and any pages whose stored bodies could not be read.

The `.json` beside it carries every change with nothing ranked away. That is what the
phase 2 triage layer will read.

## Phase 2

The Claude Agent SDK layer — semantic summaries, impact classification, a digest — is
deliberately not built yet. Its shape (one session per batch of changes, versus one per
page, versus a cheap filter feeding a deep pass) depends entirely on how many pages really
change per run, and that number did not exist until this layer produced it.

Everything above is required by all three of those designs, so none of it is a bet. Run
the measurement first:

```bash
uv run python scripts/changes.py snapshot --label baseline
uv run python scripts/fetch.py --refresh
uv run python scripts/extract.py
uv run python scripts/changes.py run --label after-refresh
```

The resulting report gives content churn per vendor — including the 661 Anthropic pages,
for which no `updated_date` and no HTTP validator exists — and the ratio between pages the
vendor stamps as updated and pages whose content actually moved.

## See also

- [`changefeed-plan.md`](changefeed-plan.md) — why it is built this way, with the churn
  figures measured from the corpus
- [`kb-application.md`](kb-application.md) — the catalogue of applications this comes from
- [`lessons-learned.md`](lessons-learned.md) — §17, the fingerprint trap this guards
