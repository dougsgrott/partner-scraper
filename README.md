# claude-scraper

Keeps a local, always-current corpus of partner documentation — Anthropic, Databricks,
and more to come — as clean Markdown with YAML frontmatter, so it can be read, grepped,
diffed, and later embedded without anyone doing it by hand.

The full design and its rationale live in [PLAN.md](PLAN.md). What the pipeline got wrong
on the way there — and what now stops it recurring — is in
[docs/lessons-learned.md](docs/lessons-learned.md); read that one before writing a new
extractor. Evidence that the corpus is complete, faithful, and useful is in
[docs/validation.md](docs/validation.md).

## How it works

```
WORKLIST  ──▶  FETCH  ──▶  RAW STORE  ──▶  EXTRACT  ──▶  CORPUS
sitemaps +     tiered      verbatim        per-site      data/*.md
dumps          fetchers    .html/.md.gz    parsers       + index.db
                                ▲                │
                                └── re-parse without re-fetching
```

Where a site offers a Markdown twin of each page — Anthropic's docs serve
`…/prompt-caching.md` — it is fetched directly and **no HTML parsing happens at all**.

The one idea everything follows from: **acquisition and parsing are separate stages.**
Fetching is slow, rate-limited, and someone else's resource; parsing is free, local, and
will be wrong the first few times. Because the exact bytes we received are archived under
`raw/`, fixing an extractor is a local re-run over the archive — not another crawl.

Two consequences worth knowing before changing anything:

- The fetcher never parses. It records bytes, status, headers, and the final URL.
- The extractor never fetches. It is a pure function of `raw/` → corpus.

## Being a good citizen

The scraper is deliberately slower than the target sites would allow: **1 request/second
per host, 2 concurrent, with jitter**. Rate limits are keyed on *host*, not source, so two
sources sharing a host don't double the load. `robots.txt` is fetched once per host and
enforced, and any `429`/`503` halves that host's rate for the rest of the run.

If you need a run to finish sooner, prefer starting it earlier over raising the rate.
There is no CLI flag to go faster — the limits live in `config/sources.yaml`.

A source whose fetch tier isn't implemented yet is **deferred, not fetched with a
different tier** — fetching a browser-tier source over plain HTTP would archive an empty
SPA shell and record it as a success.

## Setup

```bash
uv sync                    # Python 3.12+
uv run pytest              # 395 tests, no network
```

## Usage

### Inspect before you fetch

```bash
uv run python scripts/worklist.py                      # what would we fetch?
uv run python scripts/worklist.py --offline            # dumps only, no network at all
uv run python scripts/worklist.py --source databricks-docs --sample 5
uv run python scripts/worklist.py --refresh-dumps      # merge live sitemaps into the dumps
uv run python scripts/coverage.py --overview           # how much is already in the corpus?
uv run python scripts/link_gap.py                      # pages we link to but never fetched
```

`worklist.py` prints the funnel, so an unexpectedly small result says which stage caused it:

```
databricks-docs  (databricks)
  seeded  37712   -out-of-scope  31969   -robots    0   -capped     0   =>   5743
```

`sitemap-dumps/` is what makes `--offline` possible, and it drifts as the sites publish.
`--refresh-dumps` merges the live sitemaps back in; it only ever **adds** URLs, because
the dumps cover every locale and cloud while the configured seed advertises one tree.

### Extract

Reads `raw/`, writes `data/`. Never touches the network, so re-run it as often as you like.

```bash
uv run python scripts/extract.py                        # extract what's new or changed
uv run python scripts/extract.py --force                # re-extract everything (~8 min)
uv run python scripts/extract.py --only-failed          # retry past failures
uv run python scripts/extract.py --source databricks-docs --limit 20
uv run python scripts/extract.py --prune                # also delete orphaned files
```

Re-extraction is automatic when anything that shapes the output changes — bump an
extractor's `VERSION`, or just edit it, since the index stores a fingerprint of the
extractor, the writer, and the layout, and re-extracts when it moves. Fixing a parser bug
means editing it and re-running. No refetching, ever.

Three extractors, one per source shape: `passthrough_md` (Anthropic docs — served as
Markdown, so no HTML is parsed at all, though the MDX components a third of those pages
carry are converted to real Markdown), `docusaurus` (Databricks), and `nextjs_article`
(the Claude Cookbook, whose pages state their own metadata in an embedded JSON block).

Each page becomes one Markdown file with YAML frontmatter:

```yaml
---
title: What is Delta Lake in Databricks?
company: databricks
category: delta
description: Delta Lake is the default open-source storage format…
updated_date: 2026-07-10
source_url: https://docs.databricks.com/aws/en/delta/
breadcrumbs: [Tables, Table formats, Delta Lake]
extractor: docusaurus@7
content_hash: 385f9eb4…
extracted_at: '2026-08-18T16:23:47+00:00'
---
```

Cookbook pages add what their JSON states — `tags`, `authors` (display names, with the
GitHub `author_handles` beside them), and `source_file_url` pointing at the notebook.

What is deliberately absent is a hash of the archived bytes. A static site republishes
byte-different HTML on every build, so recording that here would rewrite every file in
the corpus each time Databricks rebuilds — for a change no reader would see. It lives in
`state/index.db` instead.

`category` comes from the URL path, not from a model — the docs' own taxonomy, for free.
(The cookbook is the exception: its URLs are flat, so pages are grouped by the notebook's
directory in the cookbook repo instead.)

**Re-extracting an unchanged page rewrites nothing** — same bytes, same mtime — so a
`--force` pass leaves the corpus untouched where nothing was actually said differently.
When a page *does* move (its `updated_date` rolls into a new month, or a revised extractor
files it under a different category), the file it used to occupy is deleted rather than
left behind as a stale twin. `--prune` sweeps anything the index no longer claims.

Pages that fail the quality gate get an index row with a reason and **no file**, so a
silent extraction failure can't masquerade as a real document. Their raw bytes stay on
disk; fix the extractor and re-run.

### Fetch

Always start with `--dry-run`, and prefer a `--limit` trial before a full run.

```bash
uv run python scripts/fetch.py --dry-run                        # select, request nothing
uv run python scripts/fetch.py --source databricks-docs --limit 50
uv run python scripts/fetch.py                                  # fetch what's new / resume
uv run python scripts/fetch.py --refresh                        # revalidate the archive
```

Three selection modes, because on a ~1h45m run what a re-run *doesn't* do matters most:

| Mode | Does | Use when |
|---|---|---|
| default | fetches new + previously-errored URLs; skips what is archived | first run, or resuming an interrupted one |
| `--refresh` | revalidates archived URLs with a conditional GET | keeping the corpus current |
| `--force` | re-fetches unconditionally, ignoring state and validators | the archive is wrong |

Because outcomes are written to `fetch.db` per URL, an interrupted run loses at most the
requests in flight — restart it and the archived pages cost nothing.

Every run prints a summary and writes it to `state/runs/{timestamp}.json`:

```
run 2026-08-17T17:54:23+00:00  mode=refresh
  sources        databricks-docs
  selected       50   (skipped: 0 archived, 0 exhausted)
  ok             0
  not modified   50
  errors         0
  fetched        0.0 MiB
  elapsed        56.0s  (0.89 req/s overall)
  status codes   304:50
  host docs.databricks.com  1.0 req/s
```

That run is the design working: 50 pages revalidated, **zero bytes transferred**, because
Databricks answers `If-None-Match` with a `304`. Anthropic sends `no-store`, so a refresh
there is a real re-fetch compared by content hash instead.

### Validate

Checks the corpus rather than the pipeline: is it complete, faithful, and useful?
Read-only, and non-zero exit on failure so it can gate a release.

```bash
uv run python scripts/validate.py                      # 26 structural + integrity checks
uv run python scripts/validate_fidelity.py             # every page vs the source it came from
uv run python scripts/validate_retrieval.py            # 20 questions, BM25, no tokens
uv run python scripts/sample_review.py --n 50          # draw a sample for human review
```

Results and what they mean: [docs/validation.md](docs/validation.md).

### Track what changed

The first application built on the corpus. Records where the corpus stands, then reports
what moved between two points — and, critically, whether *the vendor* moved it or *we* did.

```bash
uv run python scripts/changes.py snapshot --label baseline   # ~18 s, no network
uv run python scripts/changes.py run                         # over what is already in raw/
uv run python scripts/changes.py run --fetch                 # refresh first (~2 h)
uv run python scripts/changes.py log <url>                   # one page's history
```

A content hash moving does not mean the vendor edited anything — re-running a revised
extractor moves every page it touches. `body_fingerprint` separates the two, and pages
attributed to our own pipeline never enter the feed. The feed itself is ordered by severity,
weighted toward status and policy language (*deprecated*, *no longer supported*, *beta*), so
the top of a 680-change run is the part worth reading.

Full guide: [docs/changefeed.md](docs/changefeed.md).

### Ask the corpus what matters

The second application. The corpus's 39,872 internal links are a graph, and the graph
knows which pages everything else depends on — plus, from the anchor text on every edge,
what other pages *call* each one.

```bash
uv run python scripts/graph.py build --label baseline   # ~15 s, no network, no model
uv run python scripts/graph.py rank --top 20            # hubs, by PageRank
uv run python scripts/graph.py page <url>               # rank, neighbours, aliases
uv run python scripts/graph.py stats --by category      # dense, thin, orphaned, stale
uv run python scripts/graph.py report --write
uv run python scripts/graph.py image --all              # SVG views for a deck
```

**Count links, not link occurrences.** One Databricks page links `supported-models` 48
times from a repeated table row; ranking by raw count put that page 3rd in the corpus when
only 53 pages reference it at all — it is 214th under PageRank. `rank` reports both counts
side by side, and every build refuses to write unless every link instance in the corpus is
accounted for.

`image` writes `reports/graph/*.svg` — a map of what the corpus revolves around, one
page's neighbourhood, the occurrence-vs-PageRank correction, and category density against
centrality. Vector, so they scale into slides; no plotting dependency.

Full guide: [docs/graph.md](docs/graph.md).

## Configuration

[`config/sources.yaml`](config/sources.yaml) drives everything. A **source** is a tier
unit, not a company: one company needs two when parts of its site are served differently.
Anthropic is exactly that case — `/docs/en/` serves native Markdown (no HTML parsing at
all), while `/cookbook/` is HTML only.

```yaml
sources:
  anthropic-docs:
    company: anthropic
    seeds:
      - {type: dump, path: sitemap-dumps/anthropic_all_urls.txt}
      - {type: sitemap, url: https://platform.claude.com/sitemap.xml}
    include_paths: [/docs/en/]
    fetcher: markdown_endpoint
    extractor: passthrough_md
```

Add a partner site by adding a source. If no bespoke extractor fits it yet, `generic`
(trafilatura) gives something usable on day one.

## Layout

| Path | What it is |
|---|---|
| `config/sources.yaml` | sources, scope filters, politeness defaults |
| `sitemap-dumps/` | committed URL dumps; let the worklist run fully offline |
| `src/scraper/worklist/` | seeds → filters → robots → the list of URLs to fetch |
| `src/scraper/fetch/` | rate limiting, the HTTP fetcher, the raw archive, and `fetch.db` |
| `src/scraper/store/` | corpus writer (idempotent) + `index.db` manifest |
| `src/scraper/validate/` | the corpus audit: integrity, invariants, coverage, fidelity |
| `src/changefeed/` | **application 1** — what changed between runs, and who changed it |
| `src/corpusgraph/` | **application 2** — the link graph, its rankings, and the corpus's vocabularies |
| `raw/` | **archive** — verbatim page bytes, gzipped. Gitignored, never hand-edited |
| `data/` | **corpus** — the Markdown output. Gitignored; rebuildable from `raw/` |
| `state/fetch.db` | what we asked for, what came back, HTTP validators |
| `state/runs/` | one JSON summary per fetch run |
| `state/index.db` | corpus manifest; rebuildable from `data/` |
| `state/changes.db` | **the corpus's history** — snapshots and page versions |
| `state/changes/blobs/` | past page bodies, gzipped, addressed by content hash |
| `state/graph.db` | the link graph, rankings and mined terms; rebuilt in ~15 s |
| `reports/changefeed/` | rendered change feeds |
| `reports/graph/` | rendered graph reports and SVG views |

`raw/` is the expensive artifact — it costs a crawl to recreate. `data/` and
`state/index.db` are cheap: both can be regenerated from `raw/` with no network.
`state/changes.db` is the exception in the other direction: it is **not** rebuildable from
anything, because the past exists nowhere else.

A full refresh is ~2 hours and ~294 MiB at the configured rate. Re-extracting the whole
corpus from `raw/` is ~7 minutes and no requests at all.

## Status

| Step | State |
|---|---|
| 0 · repo layout | ✅ done |
| 1 · worklist (dumps, filters, robots) | ✅ done — 566 / 95 / 5,743 = **6,404** URLs in scope |
| 2 · raw store + `fetch.db` | ✅ done — 0 collisions over 40,618 URLs; 304 revalidation confirmed live |
| 3 · tier-1 HTTP fetcher + politeness | ✅ done — 50 live pages, then 50 × `304` on refresh |
| 4 · tier-0 `.md` fetcher | ✅ done — Anthropic docs fetched as native Markdown |
| 5 · extractors + corpus | ✅ done — **6,301 pages, 77.9 MiB**, 1 quality failure |
| 6 · corpus writer + index | ✅ done — a second `--force` pass rewrote **0 of 6,301** files; index rebuilds from `data/` exactly |
| 7 · full phase-1 run + review | ✅ done — live refresh of all **6,404** pages in 2 h 03 m, 0 errors |
| 8 · cookbook extractor (`nextjs_article`) | ✅ done — **95 pages**, metadata from the page's own JSON |
| validation · audit, fidelity, retrieval | ✅ done — **566/566** pages match their served source; 0 failing checks |
| app 1 · change feed, phase 1 | ✅ done — 6,403-page snapshot in 18 s / 16.8 MiB; a re-snapshot of an unchanged corpus stores **0 bytes** |
| app 1 · first measurement | ✅ done — **1,277 pages changed body in 11 days** (Databricks ~399/week, matching the `updated_date` estimate; Anthropic launch-inflated) |
| app 1 · attribution + ranking fixes | ✅ done — 594 false "our own churn" attributions eliminated; feed ordered by severity; full diff 10 min → **17 s** |
| app 1 · deleted pages | ✅ done — a page that 404s upstream is marked `gone` and reported as `removed`; it was previously invisible forever |
| app 1 · change feed, phase 2 (Agent SDK digest) | stage 1 built; recall measured — a run compresses to **~105k tokens** and every needle is reachable, including one at rank 1113/1116 ([decision record](docs/changefeed-phase-2.md)) |
| app 2 · corpus graph, phase 1 | ✅ done — **39,872 edges** persisted, PageRank/HITS/depth, 23,830 mined terms, whole build in **15 s**; reconciliation caught 5,406 links its own first regex had silently dropped ([docs/graph.md](docs/graph.md)) |
| app 2 · corpus graph, phase 2 (concept layer) | not started — deterministic half is the input it needs |
| 9–10 · enrichment, browser tier | next |

**Corpus today: 6,403 pages, 80.4 MiB, 121 categories — 0 extraction errors, 0 quality
failures, 0 orphaned files.** The archive behind it is 54.1 MiB of gzipped originals.

A full refresh of phase 1 is ~2 hours at the configured rate. Re-extracting the entire
corpus from `raw/` takes ~7 minutes and **no requests at all** — which is the property the
whole design is built around.
