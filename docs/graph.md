# The corpus graph

> Built 2026-08-30 against the corpus as it stood that day — 6,564 files, 6,541 live
> pages. Every number here came out of `scripts/graph.py`, so re-run it rather than
> quoting these; the commands are below and take about fifteen seconds.
>
> Design and rationale: [`graph-plan.md`](graph-plan.md). What it is an application *of*:
> family D of [`kb-application.md`](kb-application.md), items 20, 21, 23 and 25.

## Quick start

```bash
uv run python scripts/graph.py build --label baseline   # ~15 s, no network, no model
uv run python scripts/graph.py rank --top 20            # hubs, honestly counted
uv run python scripts/graph.py rank --top 20 --by in_refs   # …and the way it was counted before
uv run python scripts/graph.py page <url>               # one page, and what others call it
uv run python scripts/graph.py taxonomy --kind breadcrumb
uv run python scripts/graph.py stats --by category
uv run python scripts/graph.py report --write           # reports/graph/NNNN.{md,json}
```

Nothing here fetches and nothing calls a model. A build is a pure function of `data/` and
`state/index.db`, so it can be re-run at any time and thrown away as freely.

## What it corrects

`kb-application.md` said the corpus "names its own hot spots" and ranked them by inbound
link count. That count was **link occurrences**, and the conclusion drawn from it — "where
the questions concentrate before anyone has asked one" — does not survive being measured a
second way.

| Page | occurrences | distinct linking pages | ratio | PageRank |
|---|---|---|---|---|
| `error-messages/error-classes` | 7,069 | 210 | 33.7× | **#7** |
| `error-messages/sqlstates` | 4,123 | 406 | 10.2× | **#1** |
| `machine-learning/…/supported-models` | 2,563 | 53 | 48.4× | **#214** |
| `data-governance/unity-catalog/securable-objects` | 437 | 20 | 21.9× | **#408** |
| `pyspark/reference/classes/geography` | 161 | 40 | 4.0× | **#771** |
| `release-notes/release-types` | 1,215 | 941 | 1.3× | **#2** |

`supported-models` is third by occurrences because 53 pages link it about 48 times each —
a table row repeated down a page. `securable-objects` is 20 pages linking it 22 times
apiece. Neither is a centre of gravity, and a build order taken from that list would have
started in the wrong place.

Only **24 of the top 50 pages agree** between the two rankings. Switching from occurrences
to distinct linking pages alone recovers 39 of 50; PageRank moves a further 15. The
occurrence count is not deleted — it is a genuine signal about templates — but it is never
the number a report leads with.

## The graph

| Property | Value |
|---|---|
| Pages (nodes) | 6,541 — 5,758 Databricks, 783 Anthropic |
| Edges — distinct `(source, target)` pairs | **39,872** |
| Link occurrences behind them | 75,925 (1.9× the edges) |
| Edges naming a `#section` | 26,833 |
| Edges carrying anchor text | 39,872 — all of them |
| Pages with no internal outlink (dangling) | 1,243 (19%) |
| Pages nothing links to (orphans) | 560 (8.6%) |
| Pages no path from an entry page reaches | 606 (9.3%) |
| Build time, whole corpus | ~15 s |

**The published figure of 73,519 edges was counting something else.** It counted
occurrences, not pairs, over a slightly older corpus, and it counted image embeds as
links. The comparable number today is 75,925 occurrences over 39,872 edges.

### Where the other links went

Every link instance is accounted for; the build refuses to write if they do not add up.

| | link instances |
|---|---|
| seen by the scanner | 98,860 |
| → internal edges | 75,925 |
| → out of scope (other sites) | 17,854 |
| → image embeds, skipped | 2,327 |
| → self-links, skipped | 1,264 |
| → linked but not archived (the coverage gap) | 991 |
| → notebook exports | 248 |
| → assets (PDF, PNG, `.py`…) | 186 |
| → other hosts inside our scope | 65 |

The 991 is `link_gap.py`'s number, reached independently and by the same classifier, which
is the point of reusing `coverage.classify_links` instead of writing a second one.

## What the anchor text turned out to be worth

Every edge carries the text the linking page used, and **66% of the 63,487 named link
instances differ from the title of the page they point at**. That is an alias vocabulary
for the whole corpus, derived from a regex pass rather than a model. `graph page` shows it:

```
cast function
https://docs.databricks.com/aws/en/sql/language-manual/functions/cast

  linked by        63 pages (88 occurrences)
  pagerank         0.002579  (#11)

  called, by other pages:
      71×  `cast` function
       7×  cast
       4×  cast(expr AS type)
       2×  cast function
       1×  CAST expression
       1×  casting
```

17,052 distinct anchors survive across the corpus. This is the input phase 2 of the plan
needs, and it is why entity extraction there is a *naming and typing* problem rather than a
span-mining one — the names are already on disk.

## Vocabularies mined

| Kind | Distinct terms | Note |
|---|---|---|
| `breadcrumb` | 5,893 | trail nodes with parents; Databricks only |
| `anchor` | 17,052 | what other pages call a page |
| `external_host` | 646 | where the docs send you away |
| `code_language` | 63 | across both vendors |
| `category` | 122 | 119 distinct names, a few shared across companies |
| `author` | 40 | cookbook only |
| `tag` | 14 | cookbook only |

`graph taxonomy --kind breadcrumb` walks the hierarchy: `SQL language reference` covers
1,140 pages, and six levels down `Alphabetical list of built-in functions` still covers
771 of them.

## Content strategy

`graph stats` puts size beside centrality, because neither alone says anything:

| group | pages | median chars | share of rank | orphans |
|---|---|---|---|---|
| `databricks/sql` | 1,183 | 2,115 | 24.8% | 0 |
| `databricks/pyspark` | 1,124 | 1,361 | 3.7% | 8 |
| `databricks/ingestion` | 500 | 4,507 | 3.7% | 18 |
| `anthropic/api` | 456 | 5,306 | 1.9% | **335** |
| `databricks/error-messages` | 412 | 708 | 12.7% | 18 |
| `databricks/release-notes` | 238 | 10,160 | 6.1% | 1 |

`sql` and `error-messages` are short pages holding a third of the corpus's centrality
between them — a reference index that everything points into. `release-notes` is the
opposite: long prose, moderately central. Those are different content-strategy situations
and a page count cannot distinguish them.

### 335 of Anthropic's 456 API pages are orphans

The single most actionable thing this build surfaced, and it was not on anyone's list. 60%
of `anthropic/api` is linked by nothing else in the corpus. Two candidate explanations,
and they need different responses:

- The vendor reaches those pages only through a rendered sidebar, which the Markdown twin
  does not carry — in which case the graph is correct and simply cannot see that structure
  on this half of the corpus.
- Our extractor is dropping links on those pages — in which case it is a defect.

Not resolved here. It is recorded because `lessons-learned.md` §16 is explicit that a
discovery signal needs classifying before it is believed, and an unexplained 335 is a
finding, not a conclusion.

## Two defects this found in its own regex

Both were caught by the same mechanism and neither by any count looking wrong, which is
the case for the reconciliation gate existing at all.

**5,406 links, lost silently.** The first build used a flat `[^\[\]]*` for anchor text.
Databricks writes its SQL function index as `[first(expr [, ignoreNull])](url)`, so every
entry in it failed to match. The build reported 39,491 edges and looked entirely
plausible.

**102 more, from nesting twice.** Allowing one level of nested brackets left
`[lag(expr [, offset [, default]])](url)`, and then eight more from
`[aes_encrypt(expr, key[, mode[, padding[, iv]]])](url)`. The depth is now generated
rather than typed, and the gate says whether it is deep enough.

The check that caught both is containment, not equality: every link `coverage.MD_LINK`
finds must fall inside a span the wider pattern matched. A wider pattern that is not a
superset is not wider — it is different, and the difference is invisible.

**A third, in the report.** Rendering a build over a small corpus slice produced tables
with a header, a separator, and no rows — which GitHub renders as broken, not empty. Found
by reading the output rather than the counts (`lessons-learned.md` §1) and now covered by
the test that found it.

## Pictures

```bash
uv run python scripts/graph.py image --all                      # three views, ~1 s
uv run python scripts/graph.py image --kind ego --url <url>     # one page's neighbourhood
uv run python scripts/graph.py image --kind hubs --theme dark
```

Writes `reports/graph/0001-<view>.svg`. SVG, not PNG: nothing rasterises without a new
dependency, and a vector file scales into a deck without going soft. Keynote, PowerPoint
and any browser open them directly; for PNG, `rsvg-convert -w 2800 in.svg -o out.png` or
a browser screenshot.

| View | What it answers | Default size |
|---|---|---|
| `hubs` | what the corpus revolves around | top 70 by PageRank |
| `ego` | what depends on this page, and what it depends on | 14 each way |
| `correction` | rank by occurrences → rank by PageRank | 28 most-linked |
| `categories` | dense, or load-bearing? | 45 largest |

Four defaults rather than one, because the views fail differently as they grow: the hub
map turns into a hairball, the dumbbell's rows collide, the scatter overplots.

The colours come from the `dataviz` skill's reference palette and were checked with its
validator rather than by eye — three categorical slots, which is that palette's
documented all-pairs cap, in separately-stepped light and dark sets. Light-mode aqua
falls below 3:1 on the surface, so the one view that uses it direct-labels every mark.

**`hubs` is the picture people expect and the one worth explaining.** It does not draw
the graph — 39,872 edges render as a texture, not a picture. It draws the top pages that
link to *each other*, which turns out to be two clusters: the SQL language reference, and
the platform/dev-tools/governance mass, joined by a thin bridge through
`sql-ref-identifiers` and Unity Catalog. That structure is a claim about the corpus that
the tables do not make.

### Four things that went wrong on the way, all found by looking

Rendering and reading the output is a step, not a formality (`lessons-learned.md` §1):

1. **One disconnected page crushed the whole graph into a corner.** `sql/…/functions/cos`
   ranks in the top 55 and links to nothing else in it; any force layout pushes such a
   node to the frame edge, and fitting the layout to its extremes then shrinks everything
   real. Isolates are now dropped and counted in the footer.
2. **Labels dodged each other and sat on top of the data.** Collision avoidance that
   treats only other labels as obstacles is half a solution.
3. **The scatter's reference line was simply wrong.** "Proportional share" is a straight
   line only in log-log space; drawn straight on a log-linear plot it stated a
   relationship that does not hold. Both axes are now log, which also unsquashed four
   orders of magnitude of share onto a readable range.
4. **Sixty dumbbell rows in a fixed frame collided.** The canvas grows with the row count
   now — a chart that cannot be read is not a smaller chart, it is a wrong one.

A fifth was caught by the tests rather than the eye: a corpus slice whose categories all
hold the same share divides by zero on a log axis.

## Where it lives

`state/graph.db` — `builds`, `edges`, `nodes`, `terms`. Every build row carries the
`formula` that produced its scores and a `corpus_stamp` over the corpus it described, so
two builds are never compared across a damping change or a re-extraction without that
being visible.

The database is **derived and disposable**: `graph build` reconstructs all of it in
fifteen seconds. There is no backup command, unlike `state/changes.db`, because there is
nothing here that cannot be rebuilt. `graph gc --keep N` drops old builds.

## Verification

- 46 tests in `tests/test_corpusgraph.py`, run by `uv run pytest`.
- PageRank is checked against graphs whose answers can be worked out on paper — a cycle
  (uniform), a star, a chain, and three shapes of dangling node where the vector must
  still sum to one. `lessons-learned.md` §19: a scorer that has only ever succeeded has
  not been tested.
- The containment check is handed a known-bad input and must refuse.
- Two builds of the unchanged real corpus produce byte-identical JSON but for the build id
  and timestamps.
- Every view is parsed as XML in both themes, label boxes are asserted not to overlap
  each other *or* their marks, node radius is asserted proportional to area rather than
  to value, and the layout is asserted identical across runs — two exports of one build
  must not look like two different datasets.

## Not built

- **Item 22**, gap analysis against our own product surface: blocked on an input the repo
  does not have.
- **Item 24 and the concept layer** (items 20 and 24 in `graph-plan.md`'s phase 2): the
  deterministic half above is what makes them affordable, and it is now in place.
- **Section-level nodes.** 26,833 edges name a `#fragment`, so the graph is there for the
  taking; the count is stored on every edge so it stays a decision rather than a rebuild.
- **Wiring into consumers** — the BM25 re-rank experiment, and replacing the digest's
  `inbound_links` tool, which today reports occurrences under a name that promises pages.

## See also

- [`graph-plan.md`](graph-plan.md) — the design, and what planning got wrong
- [`kb-application.md`](kb-application.md) — family D, corrected in place
- [`changefeed.md`](changefeed.md) — the other application built on this corpus
- [`lessons-learned.md`](lessons-learned.md) — §16, §18 and §19 shaped this one
