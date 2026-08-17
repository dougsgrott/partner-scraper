# claude-scraper — Project Plan

An on-demand tool that discovers pages on partner sites (Anthropic, Databricks, …),
fetches and enriches each page through a single Claude API call, and stores the result
as theme- and date-organized Markdown with a queryable index.

Purpose: keep an always-current local corpus of partner product, technical, and
documentation material without doing it by hand.

---

## 1. Principles & scope

- **Anthropic SDK, not terminal Claude Code.** Everything runs as an importable Python
  program using the `anthropic` package (the Messages API client). No Claude Code CLI,
  no Claude Agent SDK in the core path.
- **Claude does the fetching.** We use the server-side `web_fetch` tool rather than a
  hand-rolled HTTP client, for a standardized, low-error ingestion path.
- **One Claude call per page.** Fetching and enrichment happen in a *single* request:
  Claude fetches the URL, cleans the body, and returns structured metadata together.
- **Deterministic orchestration.** Discovery, filtering, storage, and dedup are ordinary
  Python — no LLM in the loop where it isn't needed.
- **On-demand only.** No scheduler. The pipeline is invoked when the user runs it.
  Incremental re-runs are cheap because of content-hash dedup.

Out of scope (for now): scheduling/cron, JS rendering of client-only pages, RAG/search
over the corpus (the store is designed so this can be added later).

---

## 2. Architecture & data flow

```
 ┌─────────────┐   ┌──────────────────────────┐   ┌──────────────┐   ┌───────────┐
 │  DISCOVER   │──▶│      FETCH + ENRICH       │──▶│   ORGANIZE   │──▶│   STORE   │
 │ sitemap.xml │   │  ONE Claude call:         │   │ theme + date │   │ .md files │
 │ + filters   │   │  web_fetch tool +         │   │ path builder │   │ + SQLite  │
 │             │   │  structured output        │   │              │   │  index    │
 └─────────────┘   └──────────────────────────┘   └──────────────┘   └───────────┘
        │                                                                    ▲
        └──────────── SQLite index: content-hash dedup, skip-if-unchanged ───┘
```

Each page produces **one Markdown file**: enriched metadata as YAML frontmatter,
cleaned page body as the Markdown content. The SQLite index is a denormalized copy of
the frontmatter (plus a content hash) so the whole corpus is queryable without opening
files. **The files are the source of truth; the index is rebuildable from them.**

---

## 3. Project structure

```
claude-scraper/
├── pyproject.toml
├── PLAN.md                      # this file
├── config/
│   └── sources.yaml             # per-company config + theme taxonomy + filters
├── src/scraper/
│   ├── __init__.py
│   ├── config.py                # load + validate config (pydantic-settings)
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── sitemap.py           # robots.txt → sitemap.xml → URL list
│   │   └── filters.py           # URL/path/date filtering ("optional filters")
│   ├── ingest/                  # fetch + enrich, a single Claude call
│   │   ├── __init__.py
│   │   ├── schema.py            # Pydantic PageRecord (metadata + body)
│   │   ├── fetch_enrich.py      # web_fetch tool + structured output, one page
│   │   └── batch.py             # same call via Batch API for bulk (50% cost)
│   ├── store/
│   │   ├── __init__.py
│   │   ├── layout.py            # data/{company}/{theme}/{YYYY-MM}/{slug}.md
│   │   ├── index.py             # SQLite manifest: url, hash, dates, theme, status
│   │   └── writer.py            # write .md with YAML frontmatter
│   ├── pipeline.py              # orchestrates discover → ingest → organize → store
│   └── cli.py                   # importable entry point + thin CLI
├── data/                        # OUTPUT, organized by theme + date
│   └── anthropic/prompt-caching/2026-02/prompt-caching-guide.md
└── state/
    └── index.db                 # SQLite (dedup, incremental, query)
```

---

## 4. Configuration — `config/sources.yaml`

Config drives everything: which sites, which paths to include/exclude, the date window,
and the **fixed theme taxonomy** (a closed set so folder names stay stable over time).

```yaml
# Model tier used for ingestion. Bulk classification runs fine on a cheaper tier;
# raise to claude-opus-4-8 if extraction quality needs it.
model: claude-sonnet-4-6
max_content_tokens: 30000        # cap per-page fetched content (cost control)

sources:
  anthropic:
    sitemaps:
      - https://docs.claude.com/sitemap.xml
    include_paths:               # keep only URLs whose path matches one of these
      - /docs/
      - /release-notes/
    exclude_paths:
      - /docs/es/                # skip localized duplicates
    themes:                      # the closed taxonomy Claude must classify into
      - prompt-caching
      - tool-use
      - agents
      - models-and-pricing
      - streaming
      - other

  databricks:
    sitemaps:
      - https://docs.databricks.com/sitemap.xml
    include_paths:
      - /en/
    exclude_paths: []
    themes:
      - delta-lake
      - unity-catalog
      - mlflow
      - workflows
      - sql-warehouse
      - other

filters:                         # global, overridable per run
  published_after: null          # e.g. "2025-01-01" to ingest only recent material
  published_before: null
  max_pages: null                # cap per run for testing
```

---

## 5. Component detail

### 5.1 Discovery — `discovery/`

**`sitemap.py`** — deterministic, no Claude.
1. Fetch `robots.txt`, read `Sitemap:` lines (fall back to the configured sitemap URLs).
2. Fetch each `sitemap.xml`; follow sitemap-index files one level.
3. Yield `(url, lastmod)` tuples. `lastmod` (when present) is a cheap pre-filter and a
   dedup hint before spending any tokens.

**`filters.py`** — the "optional filters" surface.
- Path include/exclude (from config).
- Date window against sitemap `lastmod` (skip clearly-stale or out-of-window URLs).
- `max_pages` cap for test runs.
- Returns the final work-list of URLs to ingest.

Output of this layer: a list of URLs. Nothing has been fetched yet.

### 5.2 Ingest — `ingest/` (the heart of it)

**`schema.py`** — the contract for every page.

```python
from datetime import date
from typing import Literal
from pydantic import BaseModel, Field

class PageRecord(BaseModel):
    title: str
    company: str
    content_type: Literal["docs", "blog", "changelog", "pricing", "reference", "other"]
    theme: str = Field(description="Must be one of the taxonomy themes for this company")
    published_date: date | None = None
    updated_date: date | None = None
    summary: str = Field(description="2-3 sentence summary of the page")
    key_entities: list[str] = Field(default_factory=list)
    markdown: str = Field(description="The cleaned page body as Markdown")
```

`theme` is validated against the per-company taxonomy after the call (and the allowed
values are injected into the prompt), so folders never drift.

**`fetch_enrich.py`** — one page, one Claude call. Claude fetches via `web_fetch`,
reads, cleans, and returns `PageRecord`-shaped JSON via structured output.

```python
import anthropic
from .schema import PageRecord

client = anthropic.Anthropic()

SYSTEM = """You extract partner documentation into a structured record.
Fetch the given URL, then return:
- a cleaned Markdown body (drop nav/footer/ads; keep headings, code, tables),
- the publish and last-updated dates if present on the page,
- a 2-3 sentence summary,
- exactly one theme from the allowed list.
"""

def fetch_enrich(url: str, company: str, allowed_themes: list[str],
                 model: str, max_content_tokens: int) -> PageRecord:
    resp = client.messages.create(
        model=model,
        max_tokens=16000,
        system=[{
            "type": "text",
            "text": SYSTEM + f"\nCompany: {company}\nAllowed themes: {allowed_themes}",
            "cache_control": {"type": "ephemeral"},   # cache instructions + taxonomy
        }],
        tools=[{
            "type": "web_fetch_20260209",
            "name": "web_fetch",
            "max_uses": 3,
            "max_content_tokens": max_content_tokens,
        }],
        output_config={"format": {
            "type": "json_schema",
            "schema": PageRecord.model_json_schema(),
        }},
        messages=[{"role": "user", "content": f"Fetch and extract: {url}"}],
    )

    # web_fetch is a SERVER tool: the loop runs server-side. If it hits the
    # iteration cap, stop_reason == "pause_turn" — re-send to continue.
    while resp.stop_reason == "pause_turn":
        resp = client.messages.create(
            model=model, max_tokens=16000, system=..., tools=..., output_config=...,
            messages=[
                {"role": "user", "content": f"Fetch and extract: {url}"},
                {"role": "assistant", "content": resp.content},
            ],
        )

    text = next(b.text for b in resp.content if b.type == "text")
    return PageRecord.model_validate_json(text)
```

Key facts this relies on:
- **`web_fetch` only fetches URLs already in the conversation** — we pass exactly the
  URL we want, so it can't wander.
- **Structured output and citations are mutually exclusive.** We keep structured output
  and record provenance via the source URL (already known from discovery) instead of
  citation blocks.
- **`max_content_tokens`** caps the fetched page size — the main per-page cost lever.
- **`pause_turn`** is the server-tool continuation signal; handle it as above.

> ⚠️ Smoke-test the `web_fetch` + `output_config.format` combination on ~5 pages before
> a bulk run, and confirm it behaves the same inside the Batch API.

**`batch.py`** — for volume. The same request submitted through the Batch API at **50%
cost**; results are asynchronous and **unordered — key results by `custom_id` (the URL),
never by position.** Prompt caching on the system block gives ~0.1× on the shared
instructions + taxonomy across the batch.

### 5.3 Store — `store/`

**`layout.py`** — deterministic path from the record:
```
data/{company}/{theme}/{YYYY-MM}/{slug}.md
```
`YYYY-MM` comes from `updated_date or published_date` (fallback: an `undated/` bucket).
`slug` is derived from the URL path. Same URL → same path across runs (idempotent writes).

**`writer.py`** — one file per page: enriched metadata as YAML frontmatter, cleaned body
below.

```markdown
---
title: Prompt caching guide
company: anthropic
theme: prompt-caching
content_type: docs
published_date: 2026-02-11
updated_date: 2026-02-11
summary: How prefix-match caching works, breakpoint placement, and cost math.
source_url: https://docs.claude.com/…/prompt-caching
key_entities: [cache_control, ephemeral, TTL]
content_hash: 9f2c…            # sha256 of the body; drives dedup
fetched_at: 2026-08-14T12:00:00Z
---

# Prompt caching

Caching is a prefix match. Any byte change anywhere in the prefix…
(full cleaned body continues)
```

**`index.py`** — SQLite manifest, one row per page (denormalized frontmatter + hash):

```sql
CREATE TABLE IF NOT EXISTS pages (
    url            TEXT PRIMARY KEY,
    company        TEXT NOT NULL,
    theme          TEXT NOT NULL,
    content_type   TEXT,
    title          TEXT,
    summary        TEXT,
    published_date TEXT,
    updated_date   TEXT,
    content_hash   TEXT NOT NULL,   -- skip re-ingest when unchanged
    file_path      TEXT NOT NULL,
    fetched_at     TEXT NOT NULL,
    status         TEXT NOT NULL    -- ok | fetch_error | parse_error
);
```

The index is what makes incremental cheap: before ingesting a URL, compare against the
last known `content_hash`/`lastmod`; skip unchanged pages so no tokens are spent.

### 5.4 Pipeline — `pipeline.py`

```
for each source in config:
    urls = discovery.sitemap.collect(source)
    urls = discovery.filters.apply(urls, config.filters)
    urls = [u for u in urls if index.needs_refresh(u)]   # incremental
    records = ingest.batch.run(urls)     # or fetch_enrich per URL for small runs
    for record in records:
        path = store.layout.path_for(record)
        store.writer.write(path, record)
        index.upsert(record, path)
```

Fully deterministic; the only LLM step is `ingest`.

### 5.5 Entry point — `cli.py`

Importable (`run(config_path, **overrides)`) so it can be called from other Python code,
plus a thin CLI wrapper: `python -m scraper --source anthropic --max-pages 5`.

---

## 6. How the two artifacts relate ("enriched vs fetched md")

They are not competing artifacts — they are **one file with two parts**:

- **Cleaned Markdown body** → what you *read* / consume as reference material. If a
  RAG/search layer is added later, this is what gets chunked and embedded.
- **Enriched metadata (frontmatter)** → what you *query and organize by*. Theme + date
  decide the folder; summary + tags let you (and the SQLite index) filter and scan
  without opening files.

Both come out of the same single Claude call. The metadata is *about* the body; it never
replaces it.

---

## 7. Cost & performance levers

- **Batch API** — 50% off for bulk ingestion (not latency-sensitive).
- **Prompt caching** — the system block (instructions + taxonomy) is identical across
  pages; cache it (~0.1× after first call).
- **`max_content_tokens`** — cap fetched page size; the biggest per-page cost knob.
- **Model tiering** — `claude-sonnet-4-6` or `claude-haiku-4-5` for bulk extraction;
  reserve `claude-opus-4-8` for hard pages or an optional later synthesis pass.
- **Content-hash dedup** — re-runs only spend tokens on changed pages.

Cost tradeoff of the web_fetch approach: letting Claude fetch standardizes ingestion and
minimizes our code, but we pay input tokens for each fetched page (vs. near-zero for
self-fetching). `max_content_tokens` + Batch keep this in check.

---

## 8. Build sequence

1. `config.py` + `sources.yaml` + `ingest/schema.py` — the contracts.
2. `discovery/` — sitemap + filters (verify the URL work-list looks right, no tokens yet).
3. `ingest/fetch_enrich.py` — the single Claude call; smoke-test on ~5 URLs.
4. `store/` — layout, writer, index; confirm files + index rows land correctly.
5. `pipeline.py` + `cli.py` — wire it together for a full small run.
6. `ingest/batch.py` — switch to Batch once the single-call path is proven.

---

## 9. Open decisions (defaults chosen, change if needed)

- **Theme taxonomy: fixed enum** (stable folders) — recommended over free-form themes.
- **Provenance: source URL in frontmatter** (not citation blocks) — required because
  citations are incompatible with structured output.
- **Default model: `claude-sonnet-4-6`** for bulk — raise to Opus if quality needs it.
