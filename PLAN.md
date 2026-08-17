# claude-scraper — Plan v2: direct scraping

Build a local, always-current corpus of partner documentation (Anthropic, Databricks, and
later Snowflake et al.) by fetching pages ourselves, archiving the raw payload, and
parsing it into clean Markdown offline.

Supersedes [plan v1](docs/plan-v1-claude-sdk.md), which had Claude fetch and clean each
page in a single API call. That path is retired: it paid tokens per page for work a
parser does for free, coupled fetching to model availability and usage limits, and made
every re-parse a re-fetch. The v1 discovery/storage code is largely reusable — see §11.

---

## 1. The one structural change: separate acquisition from parsing

```
 ┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌──────────┐    ┌────────────┐
 │ WORKLIST │───▶│  FETCH   │───▶│   RAW STORE  │───▶│ EXTRACT  │───▶│  CORPUS    │
 │ sitemap  │    │ tiered:  │    │ .html/.md.gz │    │ per-site │    │ .md + YAML │
 │ dumps +  │    │ md → http│    │ + fetch.db   │    │ parsers  │    │ + index.db │
 │ filters  │    │ → browser│    │ (verbatim)   │    │          │    │            │
 └──────────┘    └──────────┘    └──────────────┘    └──────────┘    └────────────┘
                                        ▲                                   │
                                        └──── re-parse without re-fetching ─┘
                                                                     ┌────────────┐
                                                                     │ ENRICH     │
                                                                     │ (optional, │
                                                                     │  LLM)      │
                                                                     └────────────┘
```

**Fetching is expensive and rate-limited; parsing is free and will be wrong the first
time.** Archiving the raw bytes verbatim means every extractor bug fix, every new field,
and every taxonomy change is a local re-run over `raw/`, not another crawl. This is the
single most important property of the design.

Corollary rules:
- The fetcher never parses. It stores bytes, status, headers, and final URL. Nothing else.
- The extractor never fetches. It is a pure function of `raw/` → corpus.
- The enrichment stage is optional and runs on already-clean text, so it can be re-run,
  skipped, or swapped without touching either of the other two.

---

## 2. What the target sites actually do (probed 2026-08-17)

These measurements drive most of the decisions below. Re-check them before a big run.

| Site | Serving | Plain `curl` | Cloudflare challenge | Content in HTML | Conditional GET |
|---|---|---|---|---|---|
| `platform.claude.com/docs/en/**` | Next.js behind Cloudflare | 200 | none seen | yes (2.3 MB page, 43 KB text) | `cache-control: no-store` |
| `platform.claude.com/cookbook/**` | Next.js behind Cloudflare | 200 | none seen | yes (148 KB page) | `no-store` |
| `docs.databricks.com/aws/en/**` | Docusaurus 3.9 static on S3/CloudFront | 200 | n/a (no CF) | yes (35 KB page, 8.7 KB text) | **ETag + Last-Modified → 304, 0 bytes** |
| `docs.databricks.com/api/**` | client-rendered SPA shell | 200 | n/a | **no — 2.3 KB, 31 chars of text** | — |

Four findings that shape the plan:

**a. Anthropic docs serve native Markdown.** `…/prompt-caching.md` returns
`text/markdown` with YAML frontmatter already containing `title`, `url`, and
`description`. Eight concurrent requests completed in 0.75 s with no throttling. For
`/docs/en/**` there is **no HTML parsing at all** — fetch, strip frontmatter, done. This
does **not** extend to `/cookbook/**` (`.md` → 404, HTML only), and some paths 307-redirect
(`/docs/en/release-notes/api.md`), so the fetcher must follow redirects, record the final
URL, and fall back to the HTML tier on 404.

**b. A headless browser is not needed for the bulk of the corpus.** Both hosts served
full content to plain `curl` with an ordinary UA. Patchright is a **fallback tier**, not
the default path — see (d) for the one place it is genuinely required.

**c. Databricks supports conditional GET; Anthropic does not.** `If-None-Match` against
`docs.databricks.com` returned `304` with a zero-byte body. That makes refresh runs over
5,814 Databricks pages nearly free. Anthropic sends `no-store`, so refresh there is a full
re-fetch gated on content hash.

**d. `docs.databricks.com/api/**` (3,526 URLs) is the browser tier.** The shell contains
31 characters of text; the REST reference renders client-side. This is out of scope for
v1 of the new pipeline (the current include filter is `/aws/en/`) but is the concrete
justification for keeping a Patchright tier in the design rather than dropping it.

**e. Sitemap `lastmod` is effectively absent** — 94 of 2,929 Anthropic URLs are dated,
**0 of 37,689** Databricks URLs are. The v1 incremental strategy (`needs_refresh(lastmod)`)
therefore cannot work. Change detection must come from HTTP validators and content
hashing instead (§8).

**Robots:** both allow the paths we want. Anthropic disallows only `/api/`. Databricks
disallows `*s=*`, `/aws/en/search-for`, and `/aws/en/archive/` — all three go into
`exclude_paths` and a robots check runs at startup regardless.

---

## 3. Scope and volume

| Source | In-scope URLs | Tier | Est. raw (gzip) |
|---|---|---|---|
| anthropic docs (`/docs/en/`) | 566 | markdown endpoint | ~10 MB |
| anthropic cookbook (`/cookbook/`) | 95 | http + HTML extract | ~3 MB |
| databricks docs (`/aws/en/`) | 5,814 | http + HTML extract | ~40 MB |
| databricks api (`/api/`) | 3,526 | **browser** (phase 2) | ~15 MB |
| **total (phase 1)** | **6,475** | | **~55 MB** |

At 5 concurrent requests and observed latencies (0.18 s Databricks, 1.15 s Anthropic
HTML, ~0.1 s Anthropic `.md`), a **full cold crawl of phase 1 is 5–15 minutes**. A
refresh run over Databricks is mostly 304s and takes ~2 minutes. This is the headline
difference from v1, where the same corpus was a multi-day, usage-limit-bounded exercise.

Locale/cloud duplicates (`/docs/zh-CN/`, `/gcp/en/`, `/aws/ja/`) are excluded by path
filter, as in v1. That is 34,000 of the 40,000 URLs in the dumps.

---

## 4. Repository layout

The current tree has the package at `src/src/scraper` while `pyproject.toml` declares
`packages = ["src/scraper"]`, and `config/`, `data/`, `state/`, `scripts/`, and
`sitemap-dumps/` all sit under `src/`. Fix that first (step 0 of §12) — it is a `git mv`,
not a rewrite.

```
claude-scraper/
├── pyproject.toml
├── PLAN.md
├── config/
│   └── sources.yaml              # per-source: seeds, filters, fetcher, extractor
├── sitemap-dumps/                # committed URL dumps (existing format)
├── src/scraper/
│   ├── config.py                 # extended (§5)
│   ├── worklist/
│   │   ├── dumps.py              # parse "lastmod<2sp>url" dump files
│   │   ├── sitemap.py            # live sitemap.xml + index (from v1)
│   │   └── filters.py            # include/exclude/limit (from v1, unchanged)
│   ├── fetch/
│   │   ├── tiers.py              # tier selection + escalation policy
│   │   ├── http.py               # httpx.AsyncClient, HTTP/2, retries, conditional GET
│   │   ├── markdown_endpoint.py  # tier 0: URL → URL.md
│   │   ├── browser.py            # tier 2: patchright persistent context
│   │   ├── politeness.py         # per-host token bucket + robots.txt
│   │   └── rawstore.py           # gz writes + fetch.db bookkeeping
│   ├── extract/
│   │   ├── registry.py           # source_id → extractor
│   │   ├── base.py               # Extracted model + quality gate
│   │   ├── passthrough_md.py     # anthropic /docs/en/ (frontmatter + body)
│   │   ├── docusaurus.py         # databricks /aws/en/
│   │   ├── nextjs_article.py     # anthropic /cookbook/
│   │   └── generic.py            # trafilatura fallback for new sites
│   ├── enrich/                   # optional LLM pass (§7)
│   ├── store/                    # layout.py, writer.py, index.py (from v1)
│   └── cli.py                    # fetch | extract | enrich | status | coverage
├── raw/                          # ARCHIVE — gitignored, never hand-edited
│   └── {company}/{host}/{path…}/index.{html,md}.gz
├── data/                         # CORPUS — {company}/{category}/{YYYY-MM}/{slug}.md
└── state/
    ├── fetch.db                  # acquisition bookkeeping
    └── index.db                  # corpus manifest (v1 schema, extended)
```

Raw files mirror the URL path so the archive is browsable and diffable; a trailing-slash
URL becomes `…/index.html.gz`. `fetch.db` holds the authoritative URL→path mapping so
path sanitization can never cause a silent collision.

---

## 5. Configuration

Sources become **per-tier units** rather than per-company, because one company can need
two different fetch/parse paths (Anthropic docs vs cookbook).

```yaml
defaults:
  user_agent: "indicium-docs-scraper/0.2 (+doug.sgrott@gmail.com)"
  concurrency: 5              # per host
  requests_per_second: 5      # per host, token bucket
  timeout_s: 30
  retries: 3
  respect_robots: true

sources:
  anthropic-docs:
    company: anthropic
    seeds:
      - {type: dump,    path: sitemap-dumps/anthropic_all_urls.txt}
      - {type: sitemap, url: https://platform.claude.com/sitemap.xml}
    include_paths: [/docs/en/]
    exclude_paths: []
    fetcher: markdown_endpoint       # tier 0; falls back to http on 404
    extractor: passthrough_md

  anthropic-cookbook:
    company: anthropic
    seeds: [{type: dump, path: sitemap-dumps/anthropic_all_urls.txt}]
    include_paths: [/cookbook/]
    fetcher: http
    extractor: nextjs_article

  databricks-docs:
    company: databricks
    seeds: [{type: dump, path: sitemap-dumps/databricks_all_urls.txt}]
    include_paths: [/aws/en/]
    exclude_paths: [/aws/en/archive/, /aws/en/search-for]   # robots-disallowed
    fetcher: http
    conditional_get: true            # ETag / Last-Modified revalidation
    extractor: docusaurus

  databricks-api:                    # phase 2 — SPA, browser required
    company: databricks
    enabled: false
    seeds: [{type: dump, path: sitemap-dumps/databricks_all_urls.txt}]
    include_paths: [/api/]
    fetcher: browser
    browser: {wait_for: "main article", wait_ms: 1500}
    extractor: docusaurus
```

The dump format (`lastmod<2 spaces>url`, `----------` for missing) is parsed as-is; no
regeneration needed to start. `lastmod` is recorded but, per §2e, is not load-bearing.

---

## 6. Stage A — acquire

### 6.1 Tiers

Escalation is explicit and recorded on every row, so `fetch.db` answers "which pages
needed a browser" without guessing.

| Tier | Mechanism | Use for | Escalate when |
|---|---|---|---|
| 0 · `markdown_endpoint` | `GET {url}.md` via httpx | Anthropic `/docs/en/` | 404/415 → tier 1 |
| 1 · `http` | `httpx.AsyncClient(http2=True)` | everything static | 403/429/503, Cloudflare challenge marker, or extracted text below the quality floor → tier 2 |
| 2 · `browser` | Patchright persistent context, real Chrome channel, page pool | SPA shells (`/api/**`), any future JS-only or Cloudflare-gated site | give up → `fetch_error` |

Tier 2 stays in the design even though phase 1 does not need it: it is the reason
`docs.databricks.com/api/**` (3,526 pages) is reachable at all, and it is the insurance
policy for the next partner site. Keep one browser context alive for a whole run and pool
pages across it — process startup dominates per-page cost otherwise.

### 6.2 Politeness and failure handling

- Per-host token bucket (`requests_per_second`) plus a concurrency semaphore. Global caps,
  not per-source, so two sources on the same host cannot double the load.
- `robots.txt` fetched once per host at startup; disallowed URLs are dropped from the
  worklist with a logged count, independent of `exclude_paths`.
- Retries on 429/5xx/timeouts with exponential backoff + jitter; honour `Retry-After`.
  4xx other than 408/429 is terminal — no retry.
- Redirects followed (≤5); the final URL is stored and the corpus keys on it, so a
  307 like `/docs/en/release-notes/api.md` lands in one place, not two.

### 6.3 What gets stored

Raw bytes go to `raw/…` gzipped, unmodified. `fetch.db`:

```sql
CREATE TABLE fetches (
    url            TEXT PRIMARY KEY,   -- requested URL
    source_id      TEXT NOT NULL,
    final_url      TEXT,               -- after redirects
    raw_path       TEXT,               -- raw/…/index.html.gz
    content_type   TEXT,
    status_code    INTEGER,
    etag           TEXT,
    last_modified  TEXT,
    raw_sha256     TEXT,               -- change detection (§8)
    tier           TEXT NOT NULL,      -- markdown_endpoint | http | browser
    fetched_at     TEXT NOT NULL,
    state          TEXT NOT NULL,      -- ok | not_modified | fetch_error | skipped
    error          TEXT,
    attempts       INTEGER NOT NULL DEFAULT 0
);
```

---

## 7. Stage B — extract, and Stage C — enrich

### 7.1 Extractor contract

```python
class Extracted(BaseModel):
    title: str
    markdown: str                    # cleaned body
    canonical_url: str
    description: str | None = None
    published_date: date | None = None
    updated_date: date | None = None
    category: str                    # from URL path, deterministic — see below
    breadcrumbs: list[str] = []
    code_languages: list[str] = []

def extract(raw: RawPayload) -> Extracted: ...   # pure; no I/O beyond raw
```

Per-site extractors, keyed by `source_id`:

- **`passthrough_md`** — split the served YAML frontmatter, keep `title`/`url`/
  `description`, body passes through untouched. No HTML involved.
- **`docusaurus`** (Databricks) — select `article.theme-doc-markdown`, drop nav/sidebar/
  footer/breadcrumb chrome, convert with `markdownify`; code fences take their language
  from `class="language-*"`; tables preserved. Metadata from `og:title`,
  `meta[name=description]`, the JSON-LD block, and the visible `Last updated on …` line.
- **`nextjs_article`** (Anthropic cookbook) — select `<article>`, same conversion path,
  plus removal of the cookie banner and search shell seen in the probe.
- **`generic`** — `trafilatura` fallback so a new partner site produces something usable
  on day one, before anyone writes a bespoke extractor for it.

Parse HTML with `lxml` (via BeautifulSoup or selectolax) — at ~6.5k documents, parser
choice is a convenience decision, not a performance one.

### 7.2 Quality gate

Every extraction is scored before it is written; failures are recorded in the index as
`extract_error` with the reason, and the raw file stays on disk for a retry after the
extractor is fixed.

- body ≥ 200 characters of visible text (this alone catches the SPA-shell case: 31 chars),
- a title exists and is not the site-wide default,
- no 404/"page not found"/challenge markers,
- text-to-markup ratio within a sane band,
- balanced code fences.

### 7.3 Category is deterministic; theme is not needed

The v1 design asked Claude to classify each page into a per-company taxonomy. That is
unnecessary here: the URL path already encodes the site's own taxonomy
(`/aws/en/delta/…` → `delta`, `/docs/en/build-with-claude/…` → `build-with-claude`), and
`src/scraper/coverage.py` already derives exactly this. **Derive `category` from the path
and use it for the folder layout.** Corpus path becomes:

```
data/{company}/{category}/{YYYY-MM}/{slug}.md
```

This removes the LLM from the critical path entirely and makes folder names stable by
construction rather than by prompt discipline.

### 7.4 Optional enrichment (Stage C)

Runs over the extracted corpus, writes additional frontmatter keys in place, and is
re-runnable without refetching or re-extracting. Worth doing for `summary`,
`key_entities`, and a cross-company semantic `theme` — none of which the URL provides.

Cost, using title + headings + first ~800 words (~1,500 input tokens/page, ~200 output),
6,500 pages via the **Batch API (50% off)** with the shared instruction block cached:

| Model | Batch input | Batch output | Total |
|---|---|---|---|
| Haiku 4.5 ($1/$5 per MTok) | ~$5 | ~$3 | **~$8** |
| Sonnet 5 ($2/$10 intro through 2026-08-31) | ~$10 | ~$7 | **~$17** |
| Opus 5 ($5/$25) | ~$25 | ~$16 | **~$41** |

Even summarizing full bodies (~8k tokens/page) keeps this in the tens of dollars. The
decision is therefore about extraction quality, not budget — pick the model on a
50-page sample, and note that the whole stage is optional. Batch results arrive unordered:
key by `custom_id` (the URL), never by position.

---

## 8. Change detection and incremental runs

Sitemap `lastmod` is unusable (§2e), so the ladder is:

1. **Conditional GET** where supported. Databricks returns `304` with an empty body —
   send stored `ETag`/`Last-Modified`, record `not_modified`, skip everything downstream.
   This makes the 5,814-page refresh nearly free.
2. **Raw content hash.** Anthropic sends `no-store`, so re-fetch and compare
   `raw_sha256`. Unchanged → skip extraction and any enrichment.
3. **Extracted content hash.** The existing `content_hash` over the cleaned body decides
   whether the corpus file and index row are rewritten, so cosmetic HTML churn (build IDs,
   nonces, CSP hashes — all present in the probes) does not produce diff noise.
4. **Extractor version.** Each extractor carries a version string; bumping it forces
   re-extraction of every page it owns, from `raw/`, with no network access at all.

A refresh run is therefore: revalidate → fetch the changed minority → re-extract only
what actually changed → optionally enrich only the new/changed rows.

---

## 9. CLI

```
scraper fetch    [--source …] [--limit N] [--force] [--tier http|browser]
scraper extract  [--source …] [--only-failed] [--force]      # never touches the network
scraper enrich   [--source …] [--model …] [--batch]          # optional
scraper status                                               # fetch.db + index.db rollup
scraper coverage                                             # existing tool, kept
```

`fetch` and `extract` being separate commands is the design in one line: you can run
`extract --force` a dozen times while iterating on a parser and never hit the network.

---

## 10. Observability

Per-run summary written to `state/runs/{ts}.json` and printed: counts by
`state`/`tier`/`status_code`, bytes fetched, wall time, per-host request rate actually
achieved, quality-gate failures grouped by reason, and the top 20 error URLs. Without
this, a silent extractor regression across 6,000 pages is invisible until someone reads
the corpus.

---

## 11. What carries over from v1

| Module | Verdict |
|---|---|
| `discovery/sitemap.py` | **keep** — live sitemap collection; add the dump-file reader beside it |
| `discovery/filters.py` | **keep as-is** — path include/exclude/limit are unchanged; the `lastmod` date-window branch becomes dead weight but harmless |
| `store/layout.py` | **keep**, swap `record.theme` → `record.category` in `path_for` |
| `store/writer.py` | **keep** — frontmatter+body render/parse round-trip is exactly what is needed |
| `store/index.py` | **keep the shape**, extend: add `source_id`, `raw_path`, `extractor_version`; keep `content_hash`; retire the `lastmod`-based `needs_refresh` path in favour of §8 |
| `coverage.py` + `docs/coverage.md` | **keep** — the category-derivation logic is directly reusable for §7.3 |
| `config.py` | **extend** — per-source fetcher/extractor selection, politeness defaults |
| `ingest/fetch_enrich*.py`, `cc_runner.py`, `scripts/run_batch_cc.py` | **retire** — replaced by fetch/extract; the windowed usage-limit runner has no purpose once fetching is free |
| `ingest/schema.py` | **retire `PageRecord`** in favour of `Extracted` + optional enrichment fields |

New dependencies: `httpx[http2]`, `beautifulsoup4`+`lxml`, `markdownify`, `trafilatura`
(fallback extractor), `patchright` (tier 2 only, optional extra), `tenacity` (retries).
`anthropic` moves to an optional extra used solely by Stage C.

---

## 12. Build sequence

Each step ends with something runnable and verifiable.

0. **Fix the layout** — `src/src/scraper` → `src/scraper`; move `config/`, `data/`,
   `state/`, `scripts/`, `sitemap-dumps/` to the repo root. Confirm `uv run scraper --help`.
1. **Worklist** — dump reader + filters + robots check. Verify: 566 / 95 / 5,814 URLs for
   the three phase-1 sources, matching §3. No network beyond `robots.txt`.
2. **Raw store + `fetch.db`** — write/read/gz round-trip, path mirroring, collision test.
3. **Tier 1 fetcher** — httpx async, politeness, retries, conditional GET. Run against
   50 Databricks URLs; confirm a second run yields 50 × `not_modified`.
4. **Tier 0 fetcher** — `.md` endpoint with 404 fallback to tier 1. Run against 50
   Anthropic docs URLs; confirm `text/markdown` and the 307 case lands correctly.
5. **Extractors** — `passthrough_md` and `docusaurus` + quality gate. Run over the ~100
   raw files from steps 3–4 and **read 10 outputs by hand**. This is the step where
   quality is actually decided; do not skim it.
6. **Corpus writer + index** — wire `store/` in, confirm idempotent paths and hashes.
7. **Full phase-1 run** — 6,475 pages. Review the run summary, then the quality-gate
   failures, then fix extractors and re-run `extract --force` (no refetch).
8. **`nextjs_article`** for the cookbook, using raw files already on disk.
9. **Optional: enrichment** — 50-page sample across models, then a Batch run.
10. **Optional: tier 2 browser** — unlocks `docs.databricks.com/api/**` (3,526 pages) and
    the next partner site.

Steps 0–7 deliver the whole phase-1 corpus with no LLM involvement and no browser.

---

## 13. Open decisions

- **Adding Snowflake and other partners.** The plan is built for it (a new source is a
  config block plus, at worst, one extractor), but no sitemap dump exists yet. Generating
  dumps for new partners is the natural first extension.
- **Databricks `/api/**` (3,526 pages).** Genuinely useful REST reference, but it doubles
  the URL count and needs the browser tier. Deferred to phase 2; enable when the phase-1
  corpus is proven.
- **Release notes and changelogs.** High-value for a partner-facing team and high-churn —
  they may warrant a shorter refresh cadence than the rest of the corpus. Currently
  treated like any other page.
- **Refresh cadence.** Everything here is on-demand, as in v1. Once a full run is ~10
  minutes and a refresh is ~2, a scheduled daily run becomes cheap enough to reconsider.
- **Keeping raw history.** Currently the raw archive holds only the latest fetch per URL.
  Keeping prior versions (hash-suffixed) would make "what changed in this doc" answerable
  — cheap in storage, but not needed for the corpus itself.
