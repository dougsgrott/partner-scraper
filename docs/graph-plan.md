# Graph and metadata analysis, phase 1: the deterministic layer

> Written 2026-08-30. Every figure below is measured from the corpus at that date —
> 6,564 files, 6,563 `ok` pages — not estimated. Re-measure before quoting them
> elsewhere; the corpus has already moved since [`kb-application.md`](kb-application.md)
> was written on 2026-08-29.
>
> **Phase 1 was built the same day. What it measured, and the three defects building it
> exposed, are in [`graph.md`](graph.md); corrections to this plan are marked in place
> below.** Phase 2 is not started.

## Context

[`kb-application.md`](kb-application.md) §D lists six applications built on the corpus's
link graph and metadata. Planning them turned up the same kind of gap between that
catalogue and the code that [`changefeed-plan.md`](changefeed-plan.md) found.

**None of family D's numbers are reproducible.** `kb-application.md:232-238` describes the
method in prose — "resolving every Markdown link in every body against the set of
`canonical_url` values" — but no committed script does it. The 73,519 edges, the 5,822
pages with inbound links, and the hot-spot table all came from an ad-hoc script that was
never kept. [`lessons-learned.md`](lessons-learned.md) §9 and `changefeed.md:244` both
argue that is a defect, not a shortcut.

**The one graph primitive that exists cannot produce a graph.**
`scraper.validate.coverage.corpus_links()` (`src/scraper/validate/coverage.py:55`) returns
`Counter[target_url]` and discards the source page. It is an occurrence-weighted in-degree,
not an edge list, and PageRank cannot be computed from it. It is also the input to the
digest's `inbound_links` tool (`src/changefeed/digest/tools.py:98`), whose description
promises "how many corpus pages link to this one" — which is not what it returns.

## The trap this design exists to avoid

**Ranking by link occurrences measures templates, not importance.**
`kb-application.md:34-44` ranks the corpus's hubs by occurrence count and concludes the
distribution "says where the questions concentrate before anyone has asked one." Measured
both ways:

| Page | occurrences | distinct linking pages | ratio |
|---|---|---|---|
| `error-messages/error-classes` | 7,069 | 210 | 33.7× |
| `error-messages/sqlstates` | 4,123 | 406 | 10.2× |
| `machine-learning/…/supported-models` | 2,563 | **53** | 48.4× |
| `release-notes/release-types` | 1,212 | 941 | 1.3× |

`supported-models` sits third on that list because 53 pages each link it about 48 times —
a table template repeated down a page, not a centre of gravity. Only 39 of the top 50
survive the switch to distinct linking pages, and PageRank over the deduplicated graph
moves `error-classes` from first to seventh.

This is `lessons-learned.md` §18's "volume is not severity" in a new place, and §17b's "one
derived value cannot answer two questions." So **item 21 is not an enhancement on top of
item 20; it is the correction to it.** Both counts are therefore first-class columns on
every node, the report shows them side by side, and the disagreement gets a dedicated
regression test.

## What is already known

Measured on 2026-08-30 by direct scripts over `data/` and `state/index.db`.

| Fact | Value | Consequence for the design |
|---|---|---|
| Whole-corpus parse, 6,564 files | **~1.0 s** | no cache, no incremental build, no new `index.db` columns |
| Full PageRank, pure stdlib, including the parse | **~3.1 s**, 40 iterations to 7e-5 | no graph library; power iteration is about thirty lines |
| Internal link occurrences | **76,882** | the 73,519 figure is both stale and unreproducible |
| Distinct internal `(src, dst)` pairs | **39,876** | the graph is half the size the headline implies |
| Pages with inbound links | 5,983 / 6,543 | |
| Dangling nodes, no internal outlink | **1,247 (19%)** | dangling mass must be redistributed or rank leaks |
| Internal edges carrying anchor text | **75,719** | a naming vocabulary, for free |
| …whose anchor differs from the target's title | **54,753 (72%)** | an alias vocabulary, deterministically |
| Internal edges naming a `#section` | 27,702 | store the fragment; keep a section graph reachable |
| Link instances missed by `MD_LINK`'s shape | ~194 (0.2%) | the pattern is effectively complete for this corpus |
| ~~…so a wider pattern is a marginal gain~~ | **wrong** | a *flat* wider pattern lost **5,406** links to nested brackets in SQL signatures. See [`graph.md`](graph.md) § Two defects |
| Image embeds inside `MD_LINK`'s matches | **2,326** | `corpus_links()` counts these as links today |
| Gain from alias normalisation (`docs.anthropic.com`→`platform.claude.com`, `{azure,gcp}`→`aws`) | **+317 edges** | worth doing; not worth much. Do it and say so |
| Frontmatter-only metadata, absent from `index.db` | `breadcrumbs` 5,776 · `code_languages` 4,200 · `tags`/`authors` 94 · `canonical_url` all | items 23 and 25 must read `data/**/*.md` |
| Distinct breadcrumb trail nodes | 5,898, depth 0–7 | a real hierarchy — Databricks only; 788 Anthropic pages sit at depth 0 |
| Category overlap across vendors | **4 of 119** (`api`, `index`, `release-notes`, `resources`) | item 24 cannot use categories; it needs a concept layer |

Three caveats attach to those numbers:

1. `MD_LINK` (`src/scraper/validate/coverage.py:39`) matches `](url)`, which also matches
   image embeds. The 2,326 of them are mostly assets and land in the `asset` bucket, so
   coverage's conclusions are unaffected — but an edge builder that keeps them would be
   asserting that an illustration is a citation.
2. The MDX `<Card href=…>` links that `lessons-learned.md:33-38` records are a property of
   the *extractor's input*, not of the corpus: there are zero in `data/`. Verified, because
   the fear was reasonable and would have justified a second parser.
3. `src/scraper/coverage.py:23` and `src/scraper/category.py:22` are two implementations of
   `category_for` that disagree on section front pages (`"index"` versus the prefix's last
   segment). Taxonomy work uses `category.py`'s, the one the extractors actually call.

## Why the model comes second

Item 24 (cross-vendor concept alignment) is naively 788 × 5,776 = 4.5M page pairs. The
dependency-free half was prototyped — TF-IDF over title, description and headings through
an inverted index, 1.4 s — and its top matches are `Archive Session` ↔ `ADD ARCHIVE`,
`Reduce prompt leak` ↔ `reduce function`, `Get User` ↔ `user function`. It matches
vocabulary, not concepts. Shipping it alone would be a scorer agreeing with itself
(`lessons-learned.md` §19).

It is, however, an excellent *candidate generator*. Deterministic recall, model precision:
4.5M pairs become roughly 4,000 judgements. That is the shape `changefeed/digest/compress.py`
already proved, turning 6.1M tokens of diff into 92k. Phase 2 below builds it; phase 1 must
run fully without it.

**Item 22 — gap analysis against our own product surface — is not in either phase.** The
repo holds no representation of what Indicium supports, and inventing a proxy would be
§7's "do not infer." It is blocked on an input, not on engineering.

## Layout

```
src/corpusgraph/
    __init__.py     docstring only; states the import direction
    db.py           GraphDB over state/graph.db — schema, additive migrations
    edges.py        build_edges() — the edge list that does not exist today
    rank.py         pagerank(), hits(), depth() — stdlib power iteration
    taxonomy.py     categories, breadcrumb trails, tags, code languages, anchor aliases
    stats.py        density, thinness and recency rollups (item 25)
    build.py        run() — scan, rank, mine, store; the whole pipeline as one call
    report.py       render() / to_json() / write() -> reports/graph/
    viz.py          SVG views of the graph, for slides — stdlib, no plotting library
    cli.py          argparse: build, rank, taxonomy, stats, page, report
scripts/graph.py    an 11-line shim -> corpusgraph.cli:main
```

(This plan listed eight modules; the build has ten — `viz.py` was added afterwards, when
the graph needed to be shown to people rather than queried. Orchestration went into `build.py`
rather than `cli.py` so the whole pipeline stays callable as a function that prints
nothing — the `coverage.md:24-33` shape — which `cli.py` could not have offered.)

`corpusgraph` imports `scraper`; `scraper` never imports it — the rule `pyproject.toml:44-46`
states for `changefeed`. `"src/corpusgraph"` joins
`[tool.hatch.build.targets.wheel] packages` or the package stays invisible to the installed
environment.

The script is `scripts/graph.py`, not `scripts/corpusgraph.py`: `scripts/changes.py`'s
docstring records why a script must never share a package's name.

**Phase 1 adds zero dependencies and touches no network.** It is a pure function of `data/`
plus `state/index.db`, re-runnable in seconds.

## Storage

### `state/graph.db`

Built on `scraper.db.connect`, which is already WAL-enabled, rather than a second
connection helper. Rebuildable from `data/` in seconds, so unlike `state/changes.db` it is
disposable and needs no backup command.

```sql
-- One row per build. Every derived score carries the formula that produced it
-- (lessons-learned §17b) and the corpus it described, so two builds are never
-- silently compared across a formula change or a re-extraction.
CREATE TABLE IF NOT EXISTS builds (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    built_at     TEXT NOT NULL,
    label        TEXT,
    pages        INTEGER NOT NULL,
    edges        INTEGER NOT NULL,      -- distinct internal (src, dst) pairs
    occurrences  INTEGER NOT NULL,      -- link instances behind them
    formula      TEXT NOT NULL,         -- "pagerank d=0.85 tol=1e-10 dedup=page; hits it=50"
    corpus_stamp TEXT NOT NULL,         -- sha256 over sorted (url, content_hash) from index.db
    buckets      TEXT NOT NULL,         -- JSON: classify_links() counts, for reconciliation
    note         TEXT
);

-- The graph. One row per (src, dst) pair, never per occurrence: occurrence counts are
-- template artifacts — one page links supported-models 48 times — so every algorithm
-- reads the row, and `occurrences` is kept only to explain the difference.
CREATE TABLE IF NOT EXISTS edges (
    build_id    INTEGER NOT NULL,
    src         TEXT NOT NULL,          -- canonical_url of the linking page
    dst         TEXT NOT NULL,          -- normalise()d target, another corpus page
    occurrences INTEGER NOT NULL,
    sections    INTEGER NOT NULL,       -- how many of them named a #fragment
    anchors     TEXT,                   -- JSON {anchor_text: count}, top 8 by count
    PRIMARY KEY (build_id, src, dst)
);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(build_id, dst);

CREATE TABLE IF NOT EXISTS nodes (
    build_id       INTEGER NOT NULL,
    url            TEXT NOT NULL,
    company        TEXT, category TEXT, title TEXT,
    body_chars     INTEGER, updated_date TEXT,
    breadcrumbs    TEXT,                -- JSON list, from frontmatter
    code_languages TEXT,                -- JSON list, from frontmatter
    in_pages       INTEGER NOT NULL,    -- distinct linking pages  <- the honest hub signal
    in_refs        INTEGER NOT NULL,    -- link occurrences        <- what the old table ranked
    out_pages      INTEGER NOT NULL,
    pagerank       REAL, authority REAL, hub REAL,
    depth          INTEGER,             -- hops from the company's index pages; NULL if unreachable
    PRIMARY KEY (build_id, url)
);
CREATE INDEX IF NOT EXISTS idx_nodes_rank ON nodes(build_id, pagerank DESC);

-- Item 23. One vocabulary table discriminated by `kind`, because the vocabularies differ
-- only in where they come from. `parent` is '' rather than NULL: it is in the primary key.
CREATE TABLE IF NOT EXISTS terms (
    build_id INTEGER NOT NULL,
    kind     TEXT NOT NULL,   -- category|breadcrumb|tag|code_language|author|anchor|external_host
    term     TEXT NOT NULL,
    parent   TEXT NOT NULL,
    company  TEXT NOT NULL,
    pages    INTEGER NOT NULL,
    refs     INTEGER NOT NULL,
    PRIMARY KEY (build_id, kind, company, parent, term)
);
```

Non-internal link targets — assets, notebook exports, foreign hosts, out-of-scope URLs —
are **counted and reconciled but never stored as edges**. That is `link_gap.py`'s job, and
duplicating it would give two answers to one question. Their bucket counts go on
`builds.buckets`; external hosts roll up into `terms(kind='external_host')`, which is where
item 25's "7,908 links to `issues.apache.org`" lives.

Migrations are additive-and-nullable only, the `changefeed/db.py:132-145` pattern — never
`index.py`'s drop-and-rebuild, because no other pipeline stage reconstructs this database.

## Components

### `edges.py`

```python
@dataclass(frozen=True)
class Edge:
    src: str; dst: str; occurrences: int; sections: int; anchors: Counter

@dataclass
class EdgeSet:
    edges: list[Edge]; nodes: dict[str, dict]       # url -> frontmatter
    buckets: dict[str, int]; skipped: dict[str, int]
    def render(self) -> str

def build_edges(data_dir: str | Path = "data", *, cfg: AppConfig | None = None) -> EdgeSet
```

One streaming pass over `sorted(Path(data_dir).rglob("*.md"))` through
`scraper.store.writer.parse` — the same loop as `coverage.corpus_links`, but keeping the
source page. Streaming rather than `validate.invariants.load()`, which materialises all
80 MB of bodies at once.

Four rules a naive builder gets wrong, each one measured above:

| Rule | Why |
|---|---|
| Match `(!?)\[…\](…)` and drop the `!` form | 2,326 image embeds; an illustration is not a citation |
| Allow `<url>` wrappers and `"title"` suffixes, and capture anchor text in the same match | recovers the 0.2% `MD_LINK` misses and yields the alias vocabulary in one pass |
| Normalise aliases before resolving | +317 edges; the alternative is silently dropping real ones |
| Resolve against `canonical_url` from frontmatter, not against `fetch.db` | `classify_links` resolves against the *archive*; a graph must resolve against the *corpus*, and they differ by the `duplicate` and `gone` rows |

Everything else is reused verbatim: `coverage.normalise`, `coverage.ASSET_SUFFIXES`,
`coverage.NOTEBOOK_EXPORT`, `coverage.hosts_of`, `worklist.filters.in_scope`. Those
exclusion lists are hard-won — §16 records that the first link-gap run claimed 398 missing
pages when the truth was 69 — and rewriting them would relearn the same lesson.

**Nothing is silently dropped.** Every link instance lands in exactly one of: an internal
edge, one of `classify_links`'s five buckets, or `EdgeSet.skipped` (image embed, self-link,
unparseable). A build refuses to write when those totals do not reconcile.

(Corrected during implementation: the second check is *containment*, not a total. Comparing
sums against `corpus_links()` cannot work — the two patterns legitimately match different
things — so the gate is that every link `coverage.MD_LINK` finds falls inside a span the
wider pattern matched. Equality would have been unimplementable; containment caught two
real defects on the first two runs.)

### `rank.py`

```python
def pagerank(out: dict[str, list[str]], *, damping: float = 0.85,
             tolerance: float = 1e-10, max_iter: int = 100) -> dict[str, float]
def hits(out: dict[str, list[str]], *, iterations: int = 50) -> tuple[dict, dict]
def depth(out: dict[str, list[str]], roots: set[str]) -> dict[str, int]
```

Plain dicts and stdlib, the precedent `scripts/validate_retrieval.py:39` set with BM25
("small enough to keep in memory, simple enough to trust"). Neither `networkx` nor `numpy`
is in `uv.lock`, and 3.1 s end to end does not justify making one of them this project's
first graph dependency.

Two details are load-bearing at this corpus's shape. **Dangling mass**: 1,247 nodes have no
internal outlink, so their rank must be redistributed every iteration rather than dropped —
otherwise the vector stops summing to one and every score is quietly wrong by a fifth.
**Deduplication**: ranking the occurrence-weighted multigraph reproduces exactly the
artifact this subsystem exists to correct.

`depth` roots at each company's `category == 'index'` pages. Anthropic has no breadcrumbs,
so hop distance is the only hierarchy signal available on that half of the corpus.

### `taxonomy.py` and `stats.py`

`taxonomy.py` fills the `terms` table: the 119 emergent categories — derived from URL paths
by `scraper.category.category_for`, never an enumerated vocabulary — 5,898 breadcrumb trail
nodes with their parents, 14 cookbook tags, 40 authors, 48 code languages, and the anchor
vocabulary that nothing else in the repo produces: for each target page, the distinct texts
other pages use to refer to it.

`stats.py` rolls up per `(company, category)` and per breadcrumb subtree: page count,
median and total `body_chars`, recency from `updated_date`, code-language mix, with the
graph columns joined in so that "dense but peripheral" and "thin but central" are both
visible. It reuses `Index.query()` and `Index.counts()` rather than re-reading frontmatter
for fields `index.db` already holds.

### `report.py`

`reports/graph/<NNNN>.md` and `<NNNN>.json` through `write() -> tuple[Path, Path]`,
mirroring `changefeed/report.py:275`, and reusing its `_table()` and `_plural()` — including
the no-trailing-newline behaviour that already has a regression test.

**The report opens with the correction, not the totals**: hubs by PageRank beside hubs by
occurrence, with the divergence named. Then taxonomy, then content statistics, then the
reconciliation block. A reader who stops after the first table should come away with the
right idea rather than the old one.

### `scripts/graph.py`

```
graph build     [--label L]        parse data/, classify links, rank, write a build row
graph rank      [--top N] [--by pagerank|authority|in_pages|in_refs]
graph taxonomy  [--kind K] [--company C]
graph stats     [--by category|breadcrumb]
graph page      <url>              one page: rank, neighbours, the anchors used to cite it
graph report    [--build N] [--write]
```

`--json` on every read command, and the computation lives in `src/` returning dataclasses
with no printing — the shape `coverage.md:24-33` argues for, so a later dashboard or MCP
tool consumes the same functions unchanged.

## Phase 2 — the concept layer (items 20 and 24)

An optional extra, `graph = ["claude-agent-sdk>=0.1"]`, alongside `digest`. Phase 1 stays
fully runnable without it.

```
src/corpusgraph/concepts/
    __init__.py     re-exports the deterministic half only, with __all__
    compress.py     node cards and alignment candidates — the cost lever
    records.py      Concept / Alignment dataclasses and persistence (mirrors digest/findings.py)
    tools.py        async handlers over a context dataclass; the SDK imported lazily
    session.py      MODEL, PROMPT, PROMPT_VERSION, run_concepts()
scripts/concepts.py argparse in the script, the scripts/digest.py pattern
```

**Item 20 is entity extraction as typing the nodes, not mining spans.** The catalogue asks
for "products, APIs, config flags" so that *what depends on Unity Catalog?* becomes
answerable. With 39,876 edges already on disk, the cheap reading is the right one: the
pages are the entities, so name and type them. Mining new spans out of 20M tokens would
cost orders of magnitude more and produce a second graph needing reconciliation with the
first. A deterministic pre-pass assigns a provisional type from URL, category and
breadcrumb shape (`error-messages/*` → `error`, `sql/language-manual/functions/*` →
`function`, `dev-tools/cli/*` → `tool`), and the session adjudicates only what the rules
leave ambiguous, drawing candidate names and aliases from the anchor vocabulary.

**Item 24 is deterministic recall and model precision.** `compress.py` generates candidates
with the TF-IDF prototype; the session judges each pair `equivalent | overlapping |
unrelated` with a one-line reason.

Cost discipline, all of it learned from `changefeed-phase-2.md:301` ("cost was 5–10× the
estimate, and the estimate measured the wrong thing"):

- `scripts/concepts.py compress` prints the candidate count and token estimate and spends
  nothing — the free sizing step `scripts/digest.py compress` established.
- **Turns dominate, not tokens.** `record_concepts` and `record_alignments` take arrays,
  and `ctx.calls` telemetry warns when results-per-call falls below a threshold.
- `--budget` passes `max_budget_usd`; `--no-budget` must be given explicitly.
- Results persist as each call lands, so `render` is free and a crashed session loses
  nothing.

Two additive tables, `concepts` and `alignments`, both carrying `model` and
`prompt_version` so runs stay comparable — as `findings` does.

## Reuse

| Need | Existing code |
|---|---|
| Frontmatter and body of a corpus file | `scraper.store.writer.parse` (`store/writer.py:174`) |
| URL to one key | `scraper.validate.coverage.normalise` (`validate/coverage.py:42`) |
| Which link targets are not pages | `coverage.ASSET_SUFFIXES`, `NOTEBOOK_EXPORT`, `hosts_of`, `classify_links` |
| Is this URL ours | `scraper.worklist.filters.in_scope` |
| SQLite policy — WAL, busy timeout, `Row` | `scraper.db.connect` (`db.py:19`) |
| Corpus manifest queries | `scraper.store.index.Index.query/counts/largest` |
| Category derivation | `scraper.category.category_for` (`category.py:22`) |
| Markdown tables, pluralisation, report writing | `changefeed.report._table/_plural/write` |
| CLI shape, DB class shape, migrations | `changefeed.cli`, `changefeed.db` |
| MCP tool, session and budget shape | `changefeed.digest.tools`, `.session` |
| Stratified sampling for hand-validation | `scripts/sample_review.py:71` |

## Tests — `tests/test_corpusgraph.py`, `tests/test_concepts.py`

Flat, no `conftest.py`, with a local `Corpus`-style `tmp_path` helper that writes **real**
files through the real `writer` and a real `Index` — the `tests/test_changefeed.py:20-72`
pattern. Sentence-named tests whose docstrings cite the defect they defend.

- **`test_a_page_linked_many_times_from_one_page_ranks_below_one_linked_once_from_many`** —
  the regression this subsystem exists for. It is the `supported-models` case (2,563
  references from 53 pages) reduced to a fixture, and it is the graph's equivalent of the
  change feed's attribution test.
- **The ranker is shown failing before it is trusted** (§19: "a scorer that has only ever
  returned success has not been tested"). Analytic fixtures with known answers — a
  three-cycle giving uniform rank, a star, a chain, and a rank sink whose dangling mass, if
  dropped, stops the vector summing to one. Assert the sum, not only the order.
- An image embed produces no edge; a self-link produces no edge; a link to a `duplicate` or
  `gone` page is classified rather than silently counted as internal.
- Reconciliation in both directions: internal edges plus buckets plus skipped equals an
  independent `corpus_links()` total (§9).
- Idempotency: two builds over an unchanged corpus give byte-identical JSON but for the
  build id and timestamp (§6 — tested, not assumed).
- `terms` counts a page once per distinct term, and breadcrumb parent counts are monotone
  down a trail.
- Phase 2: handlers exercised through `make_handlers(ctx)` with no SDK; wiring asserted by
  monkeypatching `claude_agent_sdk.query` (`tests/test_digest.py:513`); and an
  **adversarial judge test** — twenty randomly paired cross-vendor pages mixed with known
  matches, which fails a judge that never answers `unrelated`.

## Verification

Phase 1, no network and no spend:

```bash
uv run pytest tests/test_corpusgraph.py                # unit and analytic ranker fixtures
uv run python scripts/graph.py build --label first     # ~5 s, ~6,543 nodes, ~39,900 edges
uv run python scripts/graph.py build                   # again: JSON identical but for id/timestamp
uv run python scripts/graph.py rank --top 20 --by pagerank
uv run python scripts/graph.py rank --top 20 --by in_refs      # the two lists must differ
uv run python scripts/graph.py page https://docs.databricks.com/aws/en/error-messages/error-classes
uv run python scripts/graph.py report --write          # reports/graph/0001.{md,json}
```

The build is believed only once its reconciliation block balances *and* the two `rank`
listings visibly disagree. If they agree, the deduplication is not happening.

Then the part no assertion covers (§1 — read the output, not the summary): hand-read the
top fifty by PageRank and ask whether they are pages an engineer would actually be sent to;
read twenty random anchor-alias sets and check they are names rather than sentence
fragments; cross-check three pages' inbound sets against `grep -rl` over `data/`.

Finally, re-derive `kb-application.md` §D's numbers from the committed script and correct
that document in place — the `**Corrected 2026-08-29:**` style item 19 already uses — with
the hot-spot table replaced by the two-column form and a note on why the old one misled.

Phase 2:

```bash
uv run python scripts/concepts.py compress             # candidates and token estimate, free
uv run python scripts/concepts.py run --budget 8
uv run python scripts/concepts.py render               # re-render from SQLite, no model
```

Judge the output as `changefeed-phase-2.md:328` judged the digest's: sample the
`equivalent` verdicts and confirm they are equivalent, sample the `unrelated` ones and
confirm the candidate generator was wrong rather than the judge.

## Effort

| Task | Estimate |
|---|---|
| `edges.py` and reconciliation | 3 h |
| `rank.py` and the analytic fixtures | 3 h |
| `db.py`, `taxonomy.py`, `stats.py` | 5 h |
| `report.py`, `cli.py`, `scripts/graph.py` | 5 h |
| Tests, hand-validation, `docs/graph.md`, the `kb-application.md` correction | 6 h |
| **Phase 1 total** | **~22 h** — no new dependencies, no network |
| *Actual, 2026-08-30* | *built and verified in one session; 32 tests, no new dependencies* |
| `compress.py` — candidates and node cards | 4 h |
| `tools.py`, `session.py`, `records.py` | 6 h |
| Tests including the adversarial judge, one real run, write-up | 6 h |
| **Phase 2 total** | **~16 h** — one optional extra, one paid run |

## Not in this phase

- **Item 22**, gap analysis against our own product surface. Blocked on an input the repo
  does not have: a list of what Indicium supports, joined on the concept layer phase 2
  builds. Recorded, not attempted.
- **Section-level nodes.** 27,702 edges name a `#fragment` and the corpus holds 62,861 H2+
  headings, so a section graph is real and reachable — but it multiplies the node set
  tenfold for a use case, chunk-level retrieval, that nothing consumes yet. The fragment
  count is stored on every edge so this stays a later decision rather than a rebuild.
- **Wiring the graph into consumers.** Re-ranking BM25 by a PageRank prior against
  `validation-questions.yaml`, and replacing the digest's `inbound_links` tool with real
  metrics. Both are small once `state/graph.db` exists; both are separate changes, per the
  standing rule against bundling. Note that twenty questions at 50% hit@1 can demonstrate a
  large regression but cannot prove a small win.
- **Embeddings.** Item 24's candidate generation would be better with them, and that is a
  measurement phase 2 produces: if the model rejects most lexical candidates, the honest
  next step is an embedding arm, not a better regex.

## See also

- [`kb-application.md`](kb-application.md) — family D, the catalogue this plan implements and corrects
- [`changefeed-plan.md`](changefeed-plan.md) — the subsystem whose shape this one copies
- [`lessons-learned.md`](lessons-learned.md) — §16, §17b, §18 and §19 are the ones that shaped this design
- [`validation.md`](validation.md) — what the corpus has been proven to contain
