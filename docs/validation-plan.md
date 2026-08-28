# Validating the phase-1 corpus — plan

> **Executed.** Results, including where this plan's own
> estimates turned out wrong, are in [validation.md](validation.md).

The plan of record for the validation effort. Results land in
[validation.md](validation.md); the habits behind it are in
[lessons-learned.md](lessons-learned.md).

## Context

Phase 1 produced 6,403 Markdown files (80.4 MiB) from 6,404 archived pages, with 0
extraction errors and 0 quality failures. Those numbers say the pipeline ran; they do not
say the corpus is **complete**, **faithful**, or **useful** — and every defect this project
has had passed exactly those counts (`docs/lessons-learned.md` §1).

This work builds the evidence, because the corpus is about to be judged as a proof of
concept. Three questions, answered independently:

1. **Completeness** — is every page that should be here, here?
2. **Fidelity** — does each file faithfully represent its source page?
3. **Usefulness** — can the corpus answer the questions the team will actually ask it?

Read-only probing while planning already produced findings that shape the work:

| Probe | Result |
|---|---|
| Live sitemap ↔ archive (exact URL match) | 5,758 in-scope, **5,738 archived** — the 20 absent were published in the hours since the refresh began. **No pipeline bug.** |
| Corpus link graph ↔ archive | 8,705 distinct internal link targets; after removing assets and out-of-scope, **370 linked pages we do not have** |
| HEAD spot-check of 5 missing targets | 3 live `200`s, 1 `307` to a page we hold, 1 genuine `404` |
| `/aws/en/agents/agent-evaluation`, `/release-notes/runtime/eos` | live, in scope, linked — **not listed in the sitemap at all** |

**Root cause of the coverage gap: sitemap-driven discovery has a ceiling.** The sitemap is
an incomplete index of the site, not a stale one, and no amount of refreshing dumps fixes
that. The link graph already in the corpus exceeds it.

---

## Deliverables

### 1. `scraper.validate` package + `scripts/validate.py` — the automated audit

Repeatable, no network, exits non-zero on hard failures. Report to
`state/validation/<timestamp>.json` plus a rendered summary.

- **`integrity.py`** — the store is self-consistent: index ↔ disk (no orphans, none
  missing), archive ↔ index, each file's `content_hash` matches its body, extraction is
  idempotent (a second pass writes nothing), and `Index.rebuild()` into a temp DB
  reproduces every `ok` row. Reuse `Index.orphans()`, `Index.file_paths()`,
  `writer.content_hash`, `writer.parse`.
- **`invariants.py`** — the ad-hoc greps from steps 5–8, as named checks with thresholds:
  markup leakage (`<div`, `class="`), site-rooted links, `data:` URIs, missing leading
  `#`, unbalanced fences (reuse `extract.base._unclosed_fence`), private-use glyphs,
  screen-reader text, bodies under `MIN_BODY_CHARS`, per-source frontmatter completeness,
  duplicate `content_hash` across URLs, size outliers, category distribution.
- **`coverage.py`** — scope reconciliation in both directions (worklist ↔ archive ↔
  corpus, per source) and **link-graph closure**: classify every internal link target as
  archived / asset / out-of-scope / excluded-by-config / candidate-gap.

Every check returns a structured result (name, status, count, sample) rather than
printing — so the same code backs the report, the tests, and any future CI.

### 2. `scripts/validate_fidelity.py` — comparison against ground truth

Three sources of truth, in descending order of strength:

- **Anthropic docs — complete, offline, zero cost.** The archive holds the `.md` the site
  served. The corpus body must equal it modulo exactly two known transforms: the added
  `# title` (`extract.base.with_title_heading`) and rooted-link absolutisation
  (`passthrough_md.absolutise_links`). Invert both and assert byte equality across **all
  566 pages**. This is a full-population fidelity proof for a third of the corpus.
- **Cookbook — sampled, network.** Each page's frontmatter carries `source_file_url`, the
  `.ipynb` on GitHub. Fetch N=15, parse the notebook JSON, and check every code cell's
  source appears verbatim inside a fence, and markdown-cell prose appears in the body.
  This validates the hardest extractor (`promote_code_blocks`) against true source.
- **Databricks — sampled, offline, second opinion.** No ground truth exists, so compare
  against an independent extractor: run `trafilatura` over the same archived bytes for
  N=100 and measure sentence-level recall in both directions. Flag pages where our output
  captures materially less — the signature of a dropped section, which no invariant
  catches. Adds `trafilatura` as a dev dependency (already anticipated in PLAN.md §11 for
  the `generic` extractor).

### 3. `scripts/sample_review.py` + `docs/validation-rubric.md` — the human pass

Stratified sample of 50 pages (company × category × size decile, seeded RNG so the sample
is reproducible and re-drawable). Emits a Markdown scorecard with one row per page, its
path, its live URL, and columns for the rubric: **title correct · body complete vs the
live page · code blocks intact · links resolve · metadata right · verdict**. A companion
`--score` mode summarises a filled scorecard into pass rates per dimension.

50 gives roughly ±14% at 95% confidence on a pass rate — stated explicitly in the write-up
so the number is not over-claimed.

### 4. `scripts/validate_retrieval.py` + `docs/validation-questions.yaml` — usefulness

~20 questions a partner-facing engineer would actually ask ("how do I enable Unity Catalog
lineage?", "what's the prompt-caching TTL?"), each with expected source URL(s). Score
hit@1 / hit@5 using simple BM25 over the corpus bodies — no model, no tokens, so it is
repeatable and free. Report questions with no answering page: those are coverage gaps
expressed in the language of the actual use case.

Also report chunking statistics (page size distribution, count above a chunk budget), so
the embedding step downstream is predictable — the 4.77 MB API pages matter here.

### 5. Closing the discovery ceiling — `worklist/linkgraph.py`

Diagnosis is settled; the fix is a new seed type. A `type: links` seed reads internal link
targets out of the corpus, filters by `filters.in_scope` and robots, subtracts the
archive, and emits candidates. HEAD-probe them first (1 req/s) to drop redirects and 404s
— of 5 sampled, 2 were exactly that — then feed the survivors through the normal fetch
path. ~370 candidates ≈ 7 minutes of fetching.

Ship it as **discovery + report** in this work; the decision to run the fetch is yours,
and the report will say how many of the 370 are real.

### 6. `tests/test_validate.py` — tests for the validators

Per `docs/lessons-learned.md` §3 and §10: a validator nobody has audited is a source of
false assurance. Build synthetic corpora that reproduce each historical defect — welded
code lines, base64 images, rooted links, missing H1, stale orphan file, `.md`-suffixed
category — and assert the corresponding check fires. Also assert the checks do **not**
fire on the known false positives: pages documenting `404 Not Found`, `<div>` inside code
fences, `[string]()` unlinked type names.

### 7. `docs/validation.md` — the write-up

Methodology, how to re-run each part, what every number means, the results table, and the
confidence caveats. This is the artifact that justifies the PoC.

---

## Critical files

| Path | Role |
|---|---|
| `src/scraper/validate/{__init__,integrity,invariants,coverage,fidelity}.py` | new package |
| `scripts/validate.py`, `scripts/validate_fidelity.py`, `scripts/sample_review.py`, `scripts/validate_retrieval.py` | entry points |
| `src/scraper/worklist/linkgraph.py`, `src/scraper/config.py` | new `links` seed type |
| `src/scraper/store/index.py`, `src/scraper/store/writer.py` | reuse `orphans`, `file_paths`, `parse`, `content_hash` — no changes expected |
| `src/scraper/extract/base.py`, `extract/passthrough_md.py` | reuse `with_title_heading`, `absolutise_links`, `_unclosed_fence` for the inverse-transform diff |
| `docs/validation.md`, `docs/validation-rubric.md`, `docs/validation-questions.yaml` | outputs |
| `tests/test_validate.py` | tests for the checkers |

## Sequencing

1. **Offline audit** — package, `scripts/validate.py`, tests. Establishes the baseline.
2. **Anthropic full-population fidelity diff** — cheapest strong evidence; expect zero
   unexplained differences across 566 pages, and treat any non-zero as a real finding.
3. **Link-graph coverage + HEAD probe** of the 370 candidates → the real gap number.
4. **Cookbook ground truth** (15 notebooks) and **Databricks second opinion** (100 pages).
5. **Retrieval question set.**
6. **Draw the 50-page sample**, review by hand, score it.
7. **Write `docs/validation.md`**; decide on the link-graph fetch with real numbers.

Network total: ~400 requests (370 HEADs + 15 notebooks + a handful of live checks), at the
configured 1 req/s.

## Verification

- `uv run pytest` — the new checker tests pass, including the "must not fire" cases.
- `uv run python scripts/validate.py` — exits 0 on the current corpus; deliberately break
  a file (add a rooted link, delete a title) and confirm it exits non-zero and names the
  file.
- `uv run python scripts/validate_fidelity.py --source anthropic-docs` — 566/566 match.
- `uv run python scripts/validate_retrieval.py` — prints hit@k and unanswerable questions.
- `uv run python scripts/sample_review.py --n 50` — produces a scorecard; `--score` on the
  filled file summarises it.
- Re-run `scripts/validate.py` twice — identical report, no writes to `data/`.

## Out of scope

Fetching the 370 candidate pages (reported, not run), the browser tier for `/api/**`, and
LLM-based enrichment or judging. Retrieval scoring stays keyword-based so validation costs
nothing and does not depend on model availability.
