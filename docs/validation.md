# Corpus validation — results

Does the phase-1 corpus deserve to be trusted? Three questions, answered independently:
is it **complete**, is it **faithful**, is it **useful**. Method and rationale are in
[validation-plan.md](validation-plan.md); the habits behind both are in
[lessons-learned.md](lessons-learned.md).

Everything below is reproducible from the repository — no manual steps, no cherry-picked
pages — except the human review, which is a scorecard you fill in yourself.

```bash
uv run python scripts/validate.py                                  # structure + integrity
uv run python scripts/validate_fidelity.py --notebooks 15 --second-opinion 100
uv run python scripts/validate_retrieval.py --show-misses          # usefulness
uv run python scripts/link_gap.py --probe                          # coverage beyond the sitemap
uv run python scripts/sample_review.py --n 50                      # draw the human sample
```

---

## Headline

| Question | Evidence | Result |
|---|---|---|
| Faithful? | All 566 Anthropic pages vs the Markdown the site itself served | **363 byte-exact + 203 content-preserved** |
| Faithful? | 15 cookbook pages vs the real `.ipynb` on GitHub | **162/162 code cells recovered** |
| Faithful? | 100 Databricks pages vs an independently-written extractor | **100/100 above threshold** |
| Sound? | 26 structural and integrity checks over all 6,403 files | **22 passed, 4 warned, 0 failed** |
| Useful? | 20 questions written independently of the corpus | **hit@1 50%, hit@5 90%** |
| Complete? | Live sitemap ↔ archive, exact URL match | **5,738 of 5,758**; the 20 were published mid-run |
| Complete? | The corpus's own link graph, probed | **69 live documentation pages linked but absent** |

---

## 1. Fidelity — does each file match its source?

**Anthropic docs: proved, not sampled.** The archive holds the Markdown the site served,
so the comparison covers every page rather than a sample.

- **363 pages are byte-exact.** Both sides are normalised into one form — links
  canonicalised, whitespace collapsed — and the corpus body then equals the served body
  character for character.
- **203 pages are content-preserved.** Anthropic publishes MDX, so those pages carry JSX
  components that are converted to Markdown (PLAN.md §7.1). Conversion is not invertible,
  so the assertion is instead that nothing was lost: every link target in the source
  appears in the output, and every prose word survives.

This is a deliberate downgrade from the earlier 566/566 byte-exact figure, and it bought
562 links that no Markdown parser could previously see. Normalising the served side with
our own converter would be circular, so it is not offered.

**That weaker check immediately proved it was not weak enough to be useless.** On its
first run it failed 17 pages for one or two lost words — the card converter had been
running its blurb through the inline-code stripper, deleting things like
`` `LanguageModelSession` `` from the corpus. A word-level assertion caught what no
structural check would have.

**The cookbook: checked against the real notebooks.** Each page names the `.ipynb` it was
generated from, so GitHub is ground truth for the hardest extraction in the project —
cookbook code blocks are not `<pre>` elements and had to be rebuilt from per-line `<div>`s.
Across 15 sampled notebooks, **162 of 162 code cells** appear intact inside fences.

**Databricks: no ground truth exists, so a second opinion.** `trafilatura` — a different
algorithm by different authors — reads the same archived bytes, and the two results are
compared word by word. **None of 100 sampled pages** falls below 80% recall of the
independent extraction.

That comparison also produced the clearest evidence of extraction *quality* in the whole
exercise. On `/aws/en/pyspark/reference/functions/user`, trafilatura returns:

```
PySpark referenceFunctionsuserOn this pageuser Returns the current database. Syntax
Pythonfrom pyspark.sql import functions as sfsf.user() Examples …
```

— breadcrumbs welded to prose, code welded into one line. The corpus has the same page
with headings, `python` fences, and the code newlines intact. The independent tool is the
one that mangles it.

## 2. Structure and integrity

`scripts/validate.py` runs 26 checks over the whole corpus and exits non-zero on failure,
so it can gate a release. Current state: **22 passed, 4 warned, 0 failed.**

Passing: no HTML markup or attributes leaked, no `data:` URIs, no private-use glyphs, no
screen-reader text, no unresolved in-site links, every document opens by naming itself,
every code fence balanced, every body over the length floor, every required frontmatter
field present, the index and disk agree exactly (6,403 = 6,403, no orphans), every page
traces to archived bytes that still decompress and match their hash, the index rebuilds
from `data/` alone, and a repeat extraction writes nothing.

The four warnings are known and deliberate:

| Warning | Why it is not a defect |
|---|---|
| 2 pairs of identical bodies under different URLs | Real aliases on the site (`/ldp/pipeline-mode` and `/ldp/concepts/pipeline-mode`). Reported so a new one gets noticed. |
| 10 pages over 500,000 characters | Genuinely what the site serves — `/docs/en/api/compliance` is 4.77 MB. Matters for chunking, not correctness. |
| 1 cookbook page missing `published_date` / `source_file_url` | The cookbook index page, which carries no notebook metadata. |
| 398 linked-but-absent pages | Coverage, addressed below. |

## 3. Completeness

**Against the sitemap, the pipeline is correct.** 5,758 in-scope URLs are advertised;
5,738 are archived. The 20 absent were published in the hours between the refresh starting
and the check running. Nothing is dropped by our filters.

**Against the link graph, the sitemap is not enough.** The corpus contains 8,705 distinct
internal links. Classifying each one and then probing what remains:

| Bucket | Count | What it is |
|---|---|---|
| archived | 5,909 | already in the corpus |
| assets | ~2,000 | PDFs, images, and downloadable `.py`/`.sh`/`.sql` samples — never fetched by design |
| notebook exports | 244 | `/notebooks/source/*.html`, real notebook source but not documentation |
| other hosts | 23 | `code.claude.com` (Claude Code docs) and `nlp.johnsnowlabs.com` — different sites |
| out of scope | ~10,000 | other clouds, locales, external links |
| **candidates** | **108** | probed with one `HEAD` each: **69 live**, 31 redirects, 8 gone |

So the real gap is **69 live documentation pages**, concentrated in `/aws/en/agents/*`
(agent evaluation, custom agents, model serving), `/release-notes/`, and a handful of SQL
function references. `/release-notes/runtime/eos` alone is referenced 61 times by pages we
already hold.

**Root cause: sitemap-driven discovery has a ceiling.** These pages are not missing from a
stale sitemap; they are absent from the sitemap the site publishes today. Refreshing dumps
cannot find them — only the link graph can. `scripts/link_gap.py` turns that graph into a
probed, robots-respecting work list; the 69 live URLs are already written to
`sitemap-dumps/link-gap.txt`, so closing the gap is adding that dump as a seed and running
a normal fetch (~1 minute at 1 req/s).

Two adjacent findings the same analysis produced, both decisions rather than defects:

- **244 notebook exports** under `/notebooks/source/*.html` are real Databricks content
  the corpus does not hold. Whether notebook source belongs in a documentation corpus is
  a scope question.
- **`code.claude.com` — the Claude Code documentation — is a different site entirely**,
  reachable only through links. For a partner-facing team it is probably the single most
  valuable source not yet configured, and it is a new source rather than a gap.

## 4. Usefulness

20 questions written from what a partner engineer would ask — deliberately **not** derived
from the corpus, since questions drawn from it would be guaranteed hits and would measure
nothing. Scored with plain BM25, no model and no tokens, so the number is about the corpus
rather than an embedding stack: **hit@1 50%, hit@5 90%**.

Both misses were informative:

- *"How do I enable Unity Catalog lineage?"* — `/data-governance/unity-catalog/data-lineage`
  **is** in the corpus; BM25 over truncated text ranked it outside the top five. A
  retrieval-tuning finding, not a corpus one.
- *"How do I share data with Delta Sharing?"* — Databricks has **renamed Delta Sharing to
  OpenSharing**, and the corpus holds all 41 pages under the new name. The question was
  stale; the corpus was current. Worth stating plainly: the corpus was more up to date
  than the person writing the test.

Chunking profile: median indexed page 3,318 characters; **27 files exceed 200 KB** and will
need splitting before embedding.

## 5. Human review

Automation cannot tell you a page *reads* correctly, and every defect this project has had
was found by a person reading output. `scripts/sample_review.py` draws 50 pages stratified
by company, category, and size decile (seeded, so the sample is reproducible) and writes
[validation-scorecard.md](validation-scorecard.md) as a checklist: title, completeness,
code, links, metadata.

Score it with `uv run python scripts/sample_review.py --score docs/validation-scorecard.md`.
At n=50 a pass rate carries roughly **±14% at 95% confidence** — enough to catch a
systematic problem, not enough to claim a precise quality figure.

**It earned its place on page three.** The reviewer noticed that
`cookbook-capabilities-summarization-guide.md` credited `Briiick` where the site shows
**Alexander Bricken**: the extractor had read the `authors` array, which holds GitHub
handles, while `author_details` beside it holds the display name. Measured across the
archive, this affected **77 of 94 cookbook pages** and **37 of 40 distinct authors**.
Frontmatter now carries both — `authors` for reading, `author_handles` for identity.

No automated check in this suite could have found it. A handle is a perfectly well-formed
author string: present, non-empty, correctly typed, stable across runs, and identical in
the source. Only a person who knew what a byline should look like could see it was wrong.
That is the argument for the human pass in one finding.

**And page six produced a second.** On the CLI quickstart the reviewer noticed the "Next
steps" links were absent from the Markdown and the breadcrumbs were missing. Investigation
separated them: the links were *present but unreachable*, held inside MDX `<Card>`
components that no Markdown parser reads — **562 of them across 203 pages** — while the
breadcrumbs are genuinely not in what the site serves us (the `.md` twin carries only
`title`, `url`, `description`), so they were deliberately not invented. Two reports, one
real defect, one correct-as-built; the reviewer could not have known which was which, and
that is exactly what a review pass is for.

---

## What validating this actually taught

The audit found **one defect in the corpus and five in the validator**.

The corpus defect was real but small: `content_hash` covered the body *before* the writer
stripped it, so the hash in every file's frontmatter could never be recomputed from that
file — a hash that invites a verification it always fails. Fixed, and now checked on every
run.

The other five were mine, and they matter more as a warning:

| My check said | Actually |
|---|---|
| 6 files leak HTML markup | Pages documenting HTML, with `<div>` in **inline** code — I stripped fenced code but not inline |
| 1 file has an unresolved link | `](/Workspace/absolute/path/to/image.png)` is an example path in prose, not a site link |
| 320 of 566 pages differ from source | My inverse transform de-absolutised links that were **already absolute** in the source |
| 94 of 566 pages dropped content | The site serves `# Models` itself; I stripped it as "the title we added" |
| 6 of 8 notebook code cells missing | The page uses **4-backtick fences**; my three-backtick regex mis-paired them |
| 398 pages missing from coverage | Three-quarters were downloadable files, notebook exports, or *other websites* matching on path alone — the real figure is 69 |

Every one of those would have been reported as a corpus problem by a validator nobody
audited. The last is the sharpest: the extraction quality gate learned the variable-length
fence rule in step 5, and the validator repeated the identical mistake weeks later.

**A validator is a hypothesis, not an authority.** `tests/test_validate.py` therefore tests
each check twice — against a corpus carrying the real historical defect, and against the
real page an earlier version of that rule wrongly rejected.

## Open items

- **The 69-page gap** is measured but not closed. The seed dump is written; closing it is
  one fetch run of about a minute.
- **`code.claude.com`** is unconfigured and probably worth adding as a source.
- **244 notebook exports** are a scope decision, not a defect.
- **The 50-page review** is drawn but not scored; that is a human hour.
- **Retrieval indexes only the first 4,000 characters** of each page. Fine as a smoke test,
  and the Unity Catalog miss suggests full-text indexing would score better.
