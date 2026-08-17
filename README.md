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

## Setup

```bash
uv sync                    # Python 3.12+
uv run pytest              # 68 tests, no network
```

## Usage

Nothing below fetches a page yet — the tier fetchers land in step 3 (see PLAN.md §12).

```bash
# What would we fetch, and what did each filter stage remove?
uv run python scripts/worklist.py
uv run python scripts/worklist.py --offline            # dumps only, no network at all
uv run python scripts/worklist.py --source databricks-docs --sample 5
uv run python scripts/worklist.py --json

# How much of each company/category is already in the corpus?
uv run python scripts/coverage.py --overview
uv run python scripts/coverage.py --company databricks --sort pending
```

`worklist.py` prints the funnel, so an unexpectedly small result says which stage caused it:

```
databricks-docs  (databricks)
  seeded  37689   -out-of-scope  31969   -robots    0   -capped     0   =>   5720
```

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
| `src/scraper/fetch/` | the raw archive (`rawstore`) and its bookkeeping (`db`) |
| `src/scraper/store/` | corpus writer + `index.db` manifest |
| `raw/` | **archive** — verbatim page bytes, gzipped. Gitignored, never hand-edited |
| `data/` | **corpus** — the Markdown output. Gitignored; rebuildable from `raw/` |
| `state/fetch.db` | what we asked for, what came back, HTTP validators |
| `state/index.db` | corpus manifest; rebuildable from `data/` |

`raw/` is the expensive artifact — it costs a crawl to recreate. `data/` and
`state/index.db` are cheap: both can be regenerated from `raw/` with no network.

## Status

| Step | State |
|---|---|
| 0 · repo layout | ✅ done |
| 1 · worklist (dumps, filters, robots) | ✅ done — 566 / 95 / 5,720 = **6,381** URLs in scope |
| 2 · raw store + `fetch.db` | ✅ done — 0 collisions over 40,618 URLs; 304 revalidation confirmed live |
| 3 · tier-1 HTTP fetcher | next |
| 4–7 · tier-0 fetcher, extractors, corpus writer, full run | planned |
| 8–10 · cookbook extractor, enrichment, browser tier | planned |

A full cold crawl of phase 1 is ~1 h 45 m at the configured rate; re-extracting the whole
corpus from `raw/` takes seconds and no requests.
