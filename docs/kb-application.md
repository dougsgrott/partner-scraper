# Applications for the corpus as a knowledge base

> Written 2026-08-29. Every figure below is measured from the corpus at that date, not
> estimated. Re-measure before quoting these numbers elsewhere — the commands that produced
> them are described in [Reproducing the measurements](#reproducing-the-measurements).

## Why this document exists

The corpus was built to validate a proof of concept and justify the work behind it. That
justification needs a concrete answer to "and then what?" — so this catalogues what can be
built on top of it, grouped by family, with each entry tied to a **measured property** of
the corpus rather than to generic retrieval advice.

It ends with the constraints that rule some options out, and a recommendation.

## What is actually in the box

| Property | Value | Why it matters downstream |
|---|---|---|
| Pages | 6,403 (661 Anthropic · 5,742 Databricks) | ~20M tokens of body text, 79.5 MB |
| Categories | 121, from `sql` (1,183) to `error-messages` (412) | a metadata filter axis, ready-made |
| Pages with code | 4,066 (63%) across 47 languages | python 1,843 · sql 1,588 · json 624 · bash 588 |
| Internal link edges | ~~**73,519**~~ → **39,872 distinct pairs**, 75,925 occurrences (2026-08-30) | a real graph, not a bag of documents — but the old figure counted occurrences and image embeds ([`graph.md`](graph.md)) |
| Pages with inbound links | 5,981 / 6,541 (91%); **560 orphans**, 606 unreachable | graph algorithms have signal to work with |
| `breadcrumbs` + `updated_date` | 5,742 pages (Databricks only) | hierarchy- and recency-aware retrieval |
| Cookbook metadata | 94 pages: `authors` (40 distinct), `tags`, `published_date`, `source_file_url` | the only human-attributed, dated slice |
| Change detection | `content_hash` + `output_fingerprint`, with history in `state/changes.db` | diffing across runs works — see the correction to item 19 |
| Databricks churn | **~399 pages/week measured** (estimate from `updated_date` was 250–450 — the proxy holds) | [`changefeed.md`](changefeed.md) § Measured churn |
| Anthropic churn | **98.3% in 11 days**, but that window held a model launch; steady state still unknown | no `updated_date` and no usable HTTP validator, so only a snapshot diff can measure it |
| Total churn | **1,277 pages / 11 days ≈ 813/week**, 19.9% of the corpus | the number every family-C application has to be sized against |
| Raw archive | `raw/` — 70 MB of verbatim gzipped bytes | re-parse history without refetching |
| Page size | median 3,730 chars · p90 19,672 · **10 pages > 500 KB** | most pages fit in context whole |

~~The graph names its own hot spots. Pages by inbound link count:~~

**Corrected 2026-08-30.** That table counted link *occurrences*, and the conclusion drawn
from it does not survive being counted a second way. Measured by
[`scripts/graph.py`](graph.md), which is now the committed source of these numbers:

| Occurrences | Linking pages | Ratio | PageRank | Page |
|---|---|---|---|---|
| 7,069 | 210 | 33.7× | **#7** | `error-messages/error-classes` |
| 4,123 | 406 | 10.2× | **#1** | `error-messages/sqlstates` |
| 2,563 | **53** | 48.4× | **#214** | `machine-learning/foundation-model-apis/supported-models` |
| 1,215 | 941 | 1.3× | **#2** | `release-notes/release-types` |
| 437 | **20** | 21.9× | **#408** | `data-governance/unity-catalog/securable-objects` |

`supported-models` ranked third because 53 pages link it about 48 times each — a table row
repeated down a page, not a centre of gravity. Only 24 of the top 50 survive the switch to
PageRank. The distribution is still a build-order signal, but the occurrence count is a
signal about *templates*; the questions concentrate where distinct pages point.

---

## A. Retrieval and question answering

1. **Grounded RAG assistant over both vendors.** The baseline. Every chunk carries
   `canonical_url`, so answers cite a live URL. The differentiator over plain web search is
   determinism: the same question hits the same pinned text, and `content_hash` names the
   exact version answered from.
2. **Hybrid retrieval.** `scripts/validate_retrieval.py` already implements BM25 over the
   corpus. Add embeddings and a reranker *beside* it rather than replacing it — the lexical
   arm is what catches exact identifiers like `SQLSTATE 42P01`.
3. **Contextual retrieval** — the technique Anthropic publishes in the cookbook that is
   itself in this corpus. Prepend `breadcrumbs` + `title` + `description` to each chunk.
   5,742 pages already carry breadcrumbs, so this is nearly free.
4. **Heading-level chunking with frontmatter as chunk metadata,** enabling filtered
   retrieval by `company`, `category`, `code_languages`, and `updated_date`.
5. **MCP server exposing the corpus as a tool** — `search_docs`, `read_page`,
   `follow_links`. This puts the corpus inside Claude Code, Claude Desktop, and any agent
   the team builds. Highest leverage per hour in this document.
6. **Claude Skills packaged from corpus slices** — a `databricks-sql` skill whose reference
   files are the 1,183 SQL pages; a `claude-api` skill from the 368 API pages.
7. **Long-context Q&A without retrieval, for narrow domains.** Median page is 3.7k chars,
   so a whole category often fits in one prompt with caching. Simpler and frequently more
   accurate than RAG when the scope is known in advance.

## B. Developer tooling

8. **Error-message lookup.** 412 Databricks error pages, and the graph proves this is the
   hot spot — 11,191 inbound links to `error-classes` and `sqlstates` combined. Paste a
   stack trace or SQLSTATE, get cause and fix.
9. **Code-example search engine.** Extract every fence from the 4,066 code-bearing pages
   into a snippet table keyed by language, page, and enclosing heading.
10. **Claude Code context packs** — per-category `CLAUDE.md` fragments, or a slash command
    that pulls the relevant doc slice into a session on demand.
11. **API surface index.** Anthropic's 368 API pages state model IDs, parameters, limits,
    and endpoints — structured enough to keep an internal SDK wrapper honest.
12. **Cross-vendor migration assistant.** Databricks `dev-tools` (353 pages) and Anthropic
    `cli-sdks-libraries` describe overlapping tasks in two dialects.
13. **Best-practice lint rules and review checklists** derived from the `security` (94) and
    `data-governance` (76) pages.

## C. Change intelligence — the family only this architecture enables

The two-stage design — verbatim `raw/` plus hashed `data/` — makes the corpus a **time
series**, not a snapshot. Nothing off the shelf does this for a vendor's documentation.

14. **Documentation diff feed.** Each run, emit the pages whose `content_hash` moved, with
    a semantic summary of what changed.
15. **Release-note digest.** 237 Databricks release-note pages plus Anthropic's, filtered
    to the categories your team actually uses.
16. **Deprecation and breaking-change watch.** Register the doc URLs your runbooks and
    products cite; alert when one changes, moves, or 404s. **The signals now exist**: the
    change feed ranks by status and policy language (*deprecated*, *no longer supported*,
    *beta*), and a page that 404s upstream is marked `gone` and reported as `removed`
    ([`changefeed.md`](changefeed.md)).
17. **Model and pricing drift tracker** over the Anthropic API pages.
18. **Link-rot monitor,** using `fetch.db` status codes plus the internal link graph.
19. **Historical archive / time machine.** ~~With a scheduled run, `raw/` accumulates a
    versioned history.~~ **Corrected 2026-08-29:** it does not. `rawstore.write()` writes
    each URL to a fixed path and both databases upsert by URL, so every refresh overwrote
    the prior state with no trace — a scheduled run would have accumulated nothing. The
    history layer built in [`changefeed-plan.md`](changefeed-plan.md) is what actually
    provides this: content-addressed page bodies in `state/changes/blobs/`, so *what did
    the guidance say in March?* is now answerable. That is an audit and compliance
    argument, not a convenience.

> This family needed a before-state, not a scheduler. Phase 1 of the change feed
> ([`changefeed.md`](changefeed.md)) supplies it; the cadence remains deferred, and `run`
> is invoked by hand.

## D. Graph and metadata analysis

20. **Knowledge graph.** ~~73,519 edges already exist.~~ **Built 2026-08-30**
    ([`graph.md`](graph.md)): 39,872 edges are now persisted in `state/graph.db`, each
    carrying the anchor text used to cite it. 66% of those anchors differ from the target
    page's title, which is an alias vocabulary for every page in the corpus — so entity
    extraction is a *naming and typing* problem, not a span-mining one. That half is
    phase 2 and is not started.
21. **Hub and authority ranking** (PageRank and HITS over the graph) to prioritise what to
    teach, test, and monitor. **Built.** It is not an enhancement on item 20 — it is the
    correction to it; see the hot-spot table above.
22. **Gap analysis against your own product surface** — where the vendor documents
    something you do not support, and where you support something they do not document.
    **Blocked on an input, not on engineering:** the repo holds no representation of what
    Indicium supports, and a proxy would be a guess.
23. **Taxonomy mining.** **Built.** 122 category terms, 5,893 breadcrumb trail nodes with
    parents, 17,052 anchor aliases, 63 code languages, 40 authors, 14 tags and 646
    external hosts, in `state/graph.db`'s `terms` table.
24. **Cross-vendor concept alignment.** Databricks Vector Search ↔ Anthropic's RAG
    cookbook. Joint answers spanning both vendors are precisely the partner value-add, and
    neither vendor publishes them. **Categories cannot do this**: only 4 of 119 category
    names are shared across the two vendors, and all four are structural (`api`, `index`,
    `release-notes`, `resources`). A lexical prototype matched vocabulary rather than
    concepts — its best pairs were *Archive Session* ↔ *ADD ARCHIVE*. It is a candidate
    generator for phase 2's model pass, not an answer ([`graph-plan.md`](graph-plan.md)).
25. **Content-strategy statistics** — which areas are dense, which are thin, and where
    differentiated partner content would land. **Built** (`graph stats`), and it
    immediately surfaced something nobody had listed: **335 of Anthropic's 456 API pages
    are orphans**, linked by nothing else in the corpus.

## E. Content generation and enablement

26. **Onboarding curriculum,** ordered by the link graph's dependency structure rather than
    by someone's recollection of what comes first.
27. **Solution-pattern library** from the 94 cookbook pages (Tools 26, Agent Patterns 24,
    RAG & Retrieval 19), re-expressed against your stack.
28. **Proposal and SOW drafting, grounded with citations** — the direct fix for claiming a
    capability that does not exist.
29. **Support macros and customer FAQs** with verifiable citations.
30. **Capability one-pagers and slides** that are current by construction.
31. **Localisation** of key pages for Portuguese-speaking customers.
32. **Positioning briefs** where the two vendors overlap (`ai-gateway`, `agents`,
    `databricks-ai`).

## F. Evaluation and model work — the corpus as data, not just as an index

33. **Eval dataset generation,** synthesising Q&A pairs where the page is ground truth.
34. **Retrieval benchmark.** Extend `docs/validation-questions.yaml` and
    `scripts/validate_retrieval.py` into a suite comparing embedding models, chunkers, and
    rerankers on *your* domain. A defensible, quantitative artifact for the POC.
35. **LLM-as-judge groundedness scoring,** with `content_hash` pinning the exact text
    judged.
36. **Claim verification.** Check an assertion in an internal doc or a customer email
    against the corpus; flag what is unsupported.
37. **Few-shot exemplar mining** — a better use of 20M tokens than fine-tuning.
38. **Reproducible regression testing for your own AI product.** A frozen corpus snapshot
    means an eval score change reflects the model, not doc drift. Without pinning, the two
    are inseparable. This is an underrated reason the hashing work pays off.
39. **A natural experiment already in the data:** 5,742 pages have breadcrumbs and 566 do
    not, so the value of contextual retrieval can be *measured* rather than assumed.

## G. Agentic systems

40. **Agent toolset:** search, read, and *follow-link*. The third is only possible because
    the graph resolves to real corpus pages.
41. **Multi-agent research** with a planner and per-vendor retrievers.
42. **Autonomous change-triage agent:** wakes on a diff (family C), judges impact on your
    product, files a ticket.
43. **Support-ticket deflection** with citations and confidence-gated escalation.
44. **PR review agent** checking changes against documented vendor best practice.

## H. Interfaces and packaging

45. **Internal search portal** — the whole corpus is 96 MB, so this can be static.
46. **Slack bot** for the team.
47. **Offline documentation bundle** for air-gapped or regulated customer environments.
48. **Browsable static site** with unified cross-vendor navigation.
49. **Notebook-embedded assistant** on the Databricks side.

---

## Constraints that should shape the choice

- **Licensing is the real gate, not engineering.** This is vendor-copyrighted material.
  Internal retrieval, analysis, and citation are ordinary use of published documentation;
  **republishing** it — items 45, 47, 48, or anything customer-facing that reproduces
  substantial text — is a legal question to settle before building, not after. It is the
  one item on this list that engineering cannot derisk.
- **Freshness decays without cadence.** 5,576 pages carry an `updated_date` in 2026, so the
  corpus is current *today*. Family C needed a retained before-state more than it needed a
  scheduler; that now exists, and `run` is invoked by hand.
- **The volume is higher than any of these entries assumed.** ~813 pages change body per
  week. Anything in family C that puts a model on each changed page costs a thousand-plus
  calls a run, and any digest a person is expected to read has to be ordered, not merely
  filtered — measurement showed ~91% of modifications are genuinely substantive, so there is
  no threshold that makes the list short.
- **The vendors' own change signals do not mean what they appear to.** Every sampled
  Databricks `Last-Modified` is the same timestamp across unrelated pages — it is the
  deploy time, and a rebuild changed all 5,743 pages' bytes while leaving their content
  alone. `updated_date` is real (Docusaurus renders it from the source file's commit date)
  but still an upper bound: one week shows 999 pages sharing a single date, which is a
  restructure rather than 999 edits. Only a content-hash diff settles it.
- **Coverage is good, not complete.** 69 pages are reachable only through the link graph
  (`sitemap-dumps/link-gap.txt`), `code.claude.com` is not configured as a source, `/api/**`
  needs the browser tier, and 244 notebook `.html` exports are unfetched. Do not claim
  completeness in a customer-facing context.
- **Metadata is asymmetric.** Breadcrumbs and `updated_date` exist for Databricks only;
  authors, tags, and publication dates for the 94 cookbook pages only. Recency filters and
  hierarchy-aware retrieval work well on one half of the corpus and degrade on the other.
- **Ten pages exceed 500 KB.** The largest, `data/anthropic/api/undated/docs-en-api-compliance.md`,
  is 4.77 MB. A naive chunker will either choke or flood the index with near-duplicate
  fragments; these need heading-level splitting or explicit exclusion.

## Recommendation

Ranked by evidence produced per hour, against the stated goal of justifying the project:

1. **MCP server (item 5).** About a day's work. Turns the corpus from a directory into
   something the team uses daily, which is the most direct available answer to "was this
   worth building?"
2. **Change feed (item 14).** The capability no competing approach has, and the one that
   makes the two-stage architecture visibly pay for itself. **Phase 1 is built** — see
   [`changefeed.md`](changefeed.md). The semantic layer waits on the churn measurement
   that phase 1 exists to produce.
3. **Retrieval benchmark (item 34).** Extends work that already exists and converts the
   POC's value from an assertion into a number.

Items 8 (error lookup) and 27 (pattern library) are the strongest candidates for a demo
with a customer in the room.

## Reproducing the measurements

The corpus statistics above come from reading `data/**/*.md` frontmatter directly; the
graph statistics come from resolving every Markdown link in every body against the set of
`canonical_url` values across all 6,403 files, counting a link as internal when it matches
another page after stripping the fragment and trailing slash. Page and category counts are
also available from `state/index.db` (`pages` table: `company`, `category`, `body_chars`).

## See also

- [`validation.md`](validation.md) — what the corpus has been proven to contain
- [`coverage.md`](coverage.md) — what it does not yet reach
- [`lessons-learned.md`](lessons-learned.md) — why it is built the way it is
- [`graph.md`](graph.md) — family D, phase 1: the graph, the rankings, and what they corrected
