# claude-scraper

Keeps a local, always-current corpus of partner documentation — Anthropic, Databricks,
and more to come — as clean Markdown with YAML frontmatter, so it can be read, grepped,
diffed, and later embedded without anyone doing it by hand.

The full design and its rationale live in [PLAN.md](PLAN.md).

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
uv run pytest              # 146 tests, no network
```

## Usage

### Inspect before you fetch

```bash
uv run python scripts/worklist.py                      # what would we fetch?
uv run python scripts/worklist.py --offline            # dumps only, no network at all
uv run python scripts/worklist.py --source databricks-docs --sample 5
uv run python scripts/coverage.py --overview           # how much is already in the corpus?
```

`worklist.py` prints the funnel, so an unexpectedly small result says which stage caused it:

```
databricks-docs  (databricks)
  seeded  37689   -out-of-scope  31969   -robots    0   -capped     0   =>   5720
```

### Extract

Reads `raw/`, writes `data/`. Never touches the network, so re-run it as often as you like.

```bash
uv run python scripts/extract.py                        # extract what's new or changed
uv run python scripts/extract.py --force                # re-extract everything (~8 min)
uv run python scripts/extract.py --only-failed          # retry past failures
uv run python scripts/extract.py --source databricks-docs --limit 20
```

Re-extraction is automatic when an extractor's `VERSION` is bumped — fixing a parser bug
means editing it, bumping the version, and re-running. No refetching, ever.

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
extractor: docusaurus@4
content_hash: 385f9eb4…
---
```

`category` comes from the URL path, not from a model — the docs' own taxonomy, for free.

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
| `src/scraper/store/` | corpus writer + `index.db` manifest |
| `raw/` | **archive** — verbatim page bytes, gzipped. Gitignored, never hand-edited |
| `data/` | **corpus** — the Markdown output. Gitignored; rebuildable from `raw/` |
| `state/fetch.db` | what we asked for, what came back, HTTP validators |
| `state/runs/` | one JSON summary per fetch run |
| `state/index.db` | corpus manifest; rebuildable from `data/` |

`raw/` is the expensive artifact — it costs a crawl to recreate. `data/` and
`state/index.db` are cheap: both can be regenerated from `raw/` with no network.

## Status

| Step | State |
|---|---|
| 0 · repo layout | ✅ done |
| 1 · worklist (dumps, filters, robots) | ✅ done — 566 / 95 / 5,720 = **6,381** URLs in scope |
| 2 · raw store + `fetch.db` | ✅ done — 0 collisions over 40,618 URLs; 304 revalidation confirmed live |
| 3 · tier-1 HTTP fetcher + politeness | ✅ done — 50 live pages, then 50 × `304` on refresh |
| 4 · tier-0 `.md` fetcher | ✅ done — Anthropic docs fetched as native Markdown |
| 5 · extractors + corpus | ✅ done — **6,301 pages, 77.4 MiB**, 1 quality failure |
| 6–7 · full-corpus run + review | next |
| 8 · cookbook extractor (`nextjs_article`) | planned — 95 pages currently deferred |
| 9–10 · enrichment, browser tier | planned |

A full cold crawl of phase 1 is ~1 h 45 m at the configured rate. Re-extracting the entire
corpus from `raw/` takes ~8 minutes and **no requests at all** — which is the property the
whole design is built around.
