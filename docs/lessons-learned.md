# Lessons learned

What this pipeline got wrong on the way to a working corpus, why each mistake was hard to
see, and what now stops it recurring. Written after phase 1 (6,403 pages, 80.4 MiB) so
that the next source, the next extractor, and the next person do not have to rediscover
any of it.

[PLAN.md](../PLAN.md) says what the system does and why it is shaped that way. This file
says what it felt like to be wrong about it.

---

## 1. The one rule: read the output, not the summary

Nearly every extraction defect this project has had passed every count. The run summary
said `0 errors, 0 quality failures` while the corpus contained text like
`"What isDelta LakeinDatabricks?"`. The one defect that did trip a check tripped it on a
*single page* while corrupting thousands. Counts measure what you thought to count; the
page is the artifact.

What summaries missed, and only reading found:

| Defect | What the summary said | What the page said |
|---|---|---|
| React hydration comments split text nodes | `0 errors` | `What isDelta LakeinDatabricks?` |
| Docusaurus code lines are `<span>`s with no newline | `0 errors` | every multi-line example on one line |
| `data:` image URIs inlined verbatim | `0 errors` | 11 MiB of base64 — 13% of the corpus, 28% of files |
| Links left relative | `0 errors` | 95,560 links resolving nowhere off-site |
| Category taken from the `.md` fetch URL | `0 errors` | corpus directories named `get-started.md` |
| Docusaurus `<h1>` wrapped in a `<header>` inside the content root | `0 errors` | 5,735 pages beginning mid-sentence |
| Cookbook code blocks are not `<pre>` at all | `0 errors` | 1,671 code blocks rendered as prose |

Content can also be *present and unreachable*. A third of the Anthropic docs pages ship
MDX components, so 562 links sat in the corpus inside `<Card href=…>` where no Markdown
parser could see them — every structural check passed, because JSX is not malformed
Markdown, it is simply not Markdown. A human reading the page said "the Next steps links
are missing"; they were not missing, they were inert. **"Present" and "usable" are
different claims, and only one of them is easy to test.**

The same holds for metadata, and there the automation is blinder still. Cookbook pages
credited `Briiick` instead of Alexander Bricken for 77 of 94 pages, because the extractor
read the GitHub-handle array rather than the display names sitting beside it. Every
automated check passed: the field was present, non-empty, correctly typed, stable across
runs, and matched the source exactly. **A well-formed value is not a correct one**, and
only a reader who knows what a byline should look like can tell the difference.

**The practice that works:** after any extractor change, open five real pages end to end —
a long one, a short one, one with tables, one with code, one from each category shape.
Then grep the whole corpus for things that should never appear (`<div`, `class="`,
`](/`, `data:image`, `Skip to main content`, private-use glyphs) and things that should
always appear (a leading `# `, balanced fences).

---

## 2. Silent corruption is the failure mode that matters

Rank defects by whether anything downstream would ever notice.

The code-newline bug is the reference case. Databricks wraps each line of a code sample in
`<span class="token-line">` with no newline of its own, so `pre.get_text()` returned
`"import rayfrom ray.util.spark import…"`. The Markdown still had a valid fence, still
had a language tag, still looked like code. Nothing failed. The only symptom was that the
code no longer ran, and only a human reading it would ever know.

Compare that with a page that fails extraction outright: it lands in the index as
`extract_error` with a reason, and it is fixed the same day. **The loud failure is the
cheap one.** Design so that wrongness is loud:

- extractors that are missing are *absent* from the registry, never aliased to a fallback
  (`extract/registry.py`) — a Docusaurus page parsed by the wrong extractor produces a
  plausible file, and plausible-but-wrong is the outcome this pipeline exists to avoid;
- sources whose tier or extractor is not implemented are **deferred and reported**, not
  processed with the nearest available thing;
- quality failures are recorded in the index with a reason and **no corpus file**, so a
  silent failure cannot masquerade as a real document.

---

## 3. Your quality gate will reject good pages — read the rejects

The gate was wrong more often than the extractors were, and always in the same direction:
it rejected real documentation.

- **Error markers matched the body.** `/error-messages/hdfs-http-error-error-class` is a
  page whose entire job is documenting `404 Not Found`, and a Kinesis page documents
  `access denied`. Both were thrown out as failed fetches. Markers now match the
  **title** only.
- **Fence balance counted ``` and took it modulo 2.** A block that quotes Markdown
  legitimately opens with a longer ```` fence, so a correctly-formed page counted as
  unbalanced. Now CommonMark rules.
- **The markup-ratio check counted JSX inside code fences**, rejecting a docs page whose
  subject was a React example. Fences are stripped before the ratio is taken.
- **The minimum body length was simply too high.** Reading the rejects showed genuine
  120–190-character reference stubs. Lowered 200 → 100; the SPA shell that motivated the
  check is 31 characters, so the floor still sits between them.

The inverse is just as important. Several things that *looked* like defects were correct
and were left alone: six pages containing raw `<div>` markup are documentation *about*
HTML, and `[string]()` in the API reference is an unlinked type name, not a broken link.

**Read a sample of what your validator rejected before you trust it, and read what it
flagged before you "fix" it.** A gate you have not audited is a source of silent data
loss with a reassuring green summary.

---

## 4. Probe the site before designing for it

Every significant design decision here came from a measurement, and several contradicted
the obvious assumption:

- **Anthropic serves a Markdown twin of every docs page.** `…/prompt-caching.md` returns
  `text/markdown` with usable frontmatter. That deleted an entire extractor's worth of
  HTML parsing — tier 0 exists because of a five-minute probe.
- **Anthropic sends no validators at all** — 0 of 50 responses carried an `ETag` or
  `Last-Modified`. Conditional GET is impossible there, which is why change detection has
  a content-hash rung and not just an HTTP rung.
- **Sitemap `lastmod` is unusable.** 0 of 37,689 Databricks URLs carried one.
- **`docs.databricks.com/api/**` is a real SPA** — 2.3 KB of HTML, 31 characters of text.
  No extractor can fix that; it needs a browser. Knowing this early stopped a lot of
  wasted parser work.

The corollary is that measurements expire. See §9.

---

## 5. Hand-maintained metadata rots; derive it instead

Twice in one afternoon, an extractor changed and the pipeline reported
`skipped … unchanged` — the corpus silently kept its old output. Both times the cause was
the same: `VERSION` is a number a human is supposed to remember to bump.

The first time it was the extractor itself. The second time it was the *writer* — a
frontmatter change, one layer below anything an extractor version could ever describe.

The fix is to hash the source of everything that decides what a file contains and where it
goes: extractor + writer + layout (`extract/registry.py::output_fingerprint`, stored in
`index.db`). `VERSION` still exists to state intent in the version history; the fingerprint
is what actually protects the corpus.

**The general lesson: if correctness depends on someone remembering, it is already
broken.** A false positive costs one free re-extraction pass — and since writes are
byte-identical when nothing changed (§6), the corpus does not even churn.

The same principle drove `category` (derived from the URL path or the notebook's own
directory, never assigned by a model or by hand) and the deterministic corpus layout.

---

## 6. Idempotency is a property to test, not to assume

The writer's docstring claimed "the same page always lands at the same path with the same
bytes". Measured: **0 of 25 re-extracted files were byte-identical**, because
`extracted_at` was restamped on every write. Re-extraction is the *normal* way to fix an
extractor, so every fix presented the whole corpus as modified to git, rsync, and anything
downstream — thousands of files of pure noise.

Two related failures shared the shape:

- **Pages that move leave stale copies.** The path embeds `updated_date`, so a doc edited
  into a new month lands in a new folder — and the old file just stays there,
  unreferenced by the index and indistinguishable from a live page to anything that reads
  `data/` off disk. It cannot appear until the *second* fetch of an edited page, which is
  why it survived the entire build phase.
- **Duplicate URLs.** `/ldp/best-practices` and `/ldp/best-practices/` are one document.
  The first fix deduplicated within a run, which silently regressed on the next
  incremental pass, when the first URL had been written hours earlier. Durable state
  belongs in the index, not in a variable that dies with the process.

Safeguards now: `store/writer.py::unchanged_stamp` compares the rendered page against
what is on disk and skips the write entirely; `run_extract` deletes the file a page
vacated; `extract --prune` sweeps anything the index no longer claims;
`Index.orphans()` reports them. Tested in `tests/test_store.py` and
`tests/test_extract_run.py`.

**Test for it directly:** run the thing twice and compare bytes *and* mtimes. "It looks
the same" is not the same claim.

---

## 7. Do not state what the site does not, and do not discard what it does

Two symmetrical temptations, both resisted, both worth resisting again:

- **Do not infer.** Cookbook code fences carry no language, because the site states none
  anywhere in its markup and the notebooks mix Python with shell magics. A guessed
  `python` tag would be right most of the time, which is exactly what makes it dangerous.
- **Do not discard.** The cookbook states more about itself than any DOM scrape would
  yield — publication date, authors, topic tags, and the GitHub URL of the source
  notebook, all in an embedded JSON block. `Extracted` grew `tags`, `authors`, and
  `source_file_url` to keep it.

The middle ground is *derivation from what the site states*: `category` comes from the URL
path for the docs sites, and from the notebook's own directory for the cookbook — because
cookbook URLs are flat and the URL rule would have produced 95 categories of one page
each. Same principle, different evidence.

---

## 8. Provenance in a file's bytes is provenance you will diff

Step 6 added `raw_sha256` to the frontmatter so the corpus would be self-describing and
the index rebuildable from `data/` alone. Defensible, and wrong.

The first real refresh showed why: Databricks republishes byte-different HTML on every
site build, so **all 5,743 pages got a new archive hash while their content stood still**
(only 33 pages' `updated_date` moved to a new month). Every file in the corpus was
rewritten for a one-line hash change — precisely the diff noise that change-detection rung
exists to prevent.

Provenance now lives in `index.db` only. A rebuilt index re-derives it in one free pass
that rewrites nothing.

**The lesson is about the class of field, not the field.** Anything upstream-volatile —
build IDs, archive hashes, fetch timestamps — must stay out of artifacts that people diff.
The corpus should change when a reader would notice, and not otherwise.

**The meta-lesson:** this was a deliberate decision, taken with reasons, reversed two
steps later on evidence that did not exist when it was made. That is the system working.
Record the reasoning, not just the conclusion, so the reversal is cheap.

---

## 9. Measurements expire, and stale inputs are silent

Step 1 established that the live sitemaps contributed no URLs the committed dumps lacked.
True on the day. By step 7 the live sitemap was **23 pages ahead**, six of which had never
been fetched — and nothing in the pipeline would ever have said so, because the dumps are
an input, and an input that is quietly out of date looks exactly like an input that is
correct.

Reconciliation is now an explicit act: diff scope against the archive in both directions
(in-scope-but-unfetched, and archived-but-out-of-scope), and `worklist --refresh-dumps` to
merge live sitemaps back in.

The site behaviours in PLAN.md §2 carry a probe date for the same reason. **Re-probe
before a big run.**

---

## 10. "Refresh" must never mean "replace"

The first version of `--refresh-dumps` rewrote each dump from its configured sitemap. It
cut the Databricks dump from **37,689 URLs to 5,835** — because the seed is
`/aws/en/sitemap.xml` while the dump covers every locale and cloud, including the entire
`/api/**` tree phase 2 depends on.

It was caught in seconds because the file is committed to git. That is the only reason.

Two habits generalise:

- when an artifact is a **superset** of the source you are refreshing it from, merge —
  never replace (the command now adds and updates, and never removes);
- **destructive operations belong behind version control or a dry run.** `raw/` is
  gitignored because it is 54 MiB of binary, which makes it the one artifact with no
  undo — treat it as write-once and never hand-edit it.

---

## 11. A passing test is not evidence if the test is wrong

Several defects lived in the tests, not the code:

- a collision test that used a **non-colliding** pair, so it could never have failed;
- an assertion of the form `assert … or True`;
- a robots.txt expectation asserting a precedence that the standard does not specify —
  tracing the actual rule showed `Allow: /aws/en/` legitimately outranks `Disallow: *s=*`
  under longest-match-wins, so the code was right and my expectation was wrong;
- a cookbook test asserting a URL-derived category of `index` for a *deep* URL, when that
  rule only ever yields `index` for a section root.

When a test and the code disagree, the test is a hypothesis too. Trace the actual
behaviour to a specification or a real page before "fixing" either.

Every regression test in `tests/` is tied to a defect that actually occurred against live
data — that is what keeps them honest. When you fix something, write the test that
would have caught it, and say in the docstring what went wrong.

---

## 12. What the two-stage design actually bought

Every extractor defect above was fixed by a local re-run over `raw/`. **Across the whole
project: zero pages were re-fetched to fix a parsing bug.** The docusaurus extractor went
v1 → v7; each pass re-processed thousands of pages in minutes and cost nothing but CPU.

That is the property to protect above all others when extending this system:

- the fetcher never parses — it stores bytes, status, headers, and the final URL;
- the extractor never fetches — it is a pure function of `raw/` → corpus;
- anything expensive and someone else's resource happens once, and is archived verbatim.

The corollary showed up in step 7: a full refresh took 2 h 03 m and 294 MiB, and the
*archive* absorbed all of it. The corpus rebuild afterwards took seven minutes.

---

## 13. Politeness is structural, not configurable

1 request/second per host, 2 concurrent, jitter, one-way backoff on `429`/`503`, robots
enforced. There is deliberately **no flag to go faster** — the limits live in
`config/sources.yaml`, and the correct response to "this run is slow" is to start it
earlier.

A related measurement, worth knowing before optimising anything: conditional GET saved
**nothing** across a Databricks site rebuild (all 5,743 pages returned `200`, all with
different bytes), while Anthropic — which sends no validators at all and must be
re-downloaded in full — came back **661 of 661 byte-identical**. Validators there are
per-*build*, not per-page. The host that supports revalidation saved nothing; the host
that cannot be revalidated had not changed. Politeness and patience are load-bearing;
cleverness about HTTP caching is not.

---

## 14. Distinguish "absent" from "failed"

Tier 0 fetches a Markdown twin (`…/page.md`) and falls back to HTML when there isn't one.
The tempting implementation escalates on *any* non-success. That is wrong, and expensively
so: a timeout or a `503` would permanently downgrade a page to HTML parsing because of one
bad minute on someone's server.

Escalation is therefore narrow by design — only a genuine absence (`404`, `410`, `415`) or
a non-Markdown `2xx` falls back. A transient failure is reported as a tier-0 failure and
retried on the next run, when the twin will still be there.

The same distinction runs through the rest of the state machine: `not_modified` preserves
the archive pointer rather than overwriting it, a `fetch_error` never destroys the last
good copy, and a `duplicate` is recorded as *settled* rather than failed, because there is
nothing to retry. **"I could not get it" and "it does not exist" must never share a code
path.**

---

## 15. Running it teaches things building it cannot

Both of these only appeared once the pipeline was doing real work for hours at a time:

- **SQLite defaults lock readers out.** Extraction reads `fetch.db` while a two-hour fetch
  writes it, and with the default rollback journal a writer blocks readers for the whole
  file. Both databases now open in WAL with a busy timeout (`src/scraper/db.py`). This is
  invisible in tests, where nothing runs concurrently.
- **Long jobs need to be interruptible and resumable, and then they need to actually be
  interrupted.** Two extraction passes were once started concurrently by operator error
  (mine). Nothing corrupted — writes are atomic via tmp-file rename, and the databases are
  WAL — and the restart resumed exactly where it left off because selection is driven by
  state, not by position in a list. Design every long run so that killing it is a
  non-event, then verify that by killing it.

---

## 16. Your index of the world is not the world

The work-list is built from sitemaps, and for phase 1 that was treated as equivalent to
"every page on the site". Validation showed it is not: `/aws/en/agents/agent-evaluation`
and `/release-notes/runtime/eos` are live, in scope, referenced 22 and 61 times by pages
already in the corpus — and listed in no sitemap Databricks publishes. Sixty-nine such
pages exist. Refreshing the dumps cannot find them, because the dumps are faithful copies
of an index that is itself incomplete.

The corpus's own link graph is a second, independent index, and it is free: every internal
link is a claim that a page exists. Comparing that claim against the archive
(`scripts/link_gap.py`) is the only check here that can discover what nobody told us about.

**But a discovery signal needs classifying before it is believed.** The first run of that
check reported 398 missing pages. Three-quarters of them were not missing pages at all:

- downloadable `.py`, `.sh`, `.sql` and `.tdc` samples under `/assets/files/`;
- 244 notebook exports served as standalone `.html`;
- 23 pages on **entirely different websites** — `code.claude.com`, `nlp.johnsnowlabs.com` —
  which matched because `filters.in_scope` compares *paths* and both sites use `/docs/en/`.

That last one is worth remembering on its own: a predicate is only correct for the inputs
it was written for. `in_scope` was written for URLs that already came from a source's own
sitemap, where the host is a given. Feeding it arbitrary links from the open web silently
changed its meaning.

---

## 17. A design that "enables" something has not built it

`kb-application.md` argued — correctly — that the two-stage architecture makes the corpus a
time series rather than a snapshot, and listed a whole family of applications resting on
that. One entry said `raw/` would accumulate a versioned history once a scheduled run
existed.

It would not have. `rawstore.write()` writes each URL to a fixed path, and both `fetch.db`
and `index.db` upsert by URL. Every refresh overwrote the prior state with no trace, and
adding a scheduler would have produced a very regular way of destroying history. **The
corpus had no time dimension at all** — a fact that survived a full validation pass, a
50-page human review, and a document specifically about what could be built on top, because
nothing ever asked it to produce a "before".

The architecture genuinely did enable the feature: acquisition and parsing were already
separate, `content_hash` was already computed, `output_fingerprint` already distinguished
our changes from theirs. Those are the hard parts, and they were right. But *enabling* and
*having* are different claims, and prose slides between them easily. The retention layer
had to be written.

Two habits fall out:

- **When a document claims a capability, check the code path that would deliver it.** The
  cost here was one hour of reading; the cost of finding out during the first scheduled run
  would have been the belief that a history existed.
- **Ask what a feature would need to be *false*.** "We can diff across runs" needs two
  states. Only one was ever kept.

The same section also asserted that change detection worked via "ETag/Last-Modified in
`fetch.db`". Those columns are populated, but every sampled Databricks `Last-Modified` is
the same timestamp across unrelated pages — it is the deploy time, which is why a rebuild
changed all 5,743 pages' bytes while leaving their content alone (§10). A validator that is
present is not a validator that means what you want.

### 17b. The fingerprint trap now has a consumer

`output_fingerprint` has been widened three times after silently under-reporting: an
unbumped `VERSION`, then the writer, then imported modules. The change feed is the first
thing that *depends* on it being right, and it fails loudly rather than quietly — a page
whose fingerprint moved is reported as our churn, not the vendor's, and if the fingerprint
is missing entirely the change is `unknown` rather than being folded into the feed.

The regression test is the MDX pass itself: three pages whose content hash and fingerprint
both move must yield zero vendor changes. Without attribution, the run that converted MDX
would have reported 566 upstream edits that never happened.

---

## Checklist: adding a source or an extractor

1. **Probe the live site first.** Content type, validators, whether the HTML contains the
   text, whether a `.md` twin exists, what robots says. Record the date.
2. **Check for embedded metadata** before scraping the DOM — a `<script type="application/json">`
   block may state the title, date, authors, and taxonomy already.
3. **Fetch a small `--limit` sample.** Confirm the archive round-trips.
4. **Write the extractor, then read five real pages end to end.** Long, short, tables,
   code, and one section root.
5. **Grep the whole output** for markup leakage, relative links, `data:` URIs, missing
   leading `#`, unbalanced fences, private-use glyphs, and screen-reader-only text.
6. **Check the category distribution.** All singletons or one giant bucket means the rule
   is wrong for this site.
7. **Look at the size distribution.** The largest page here is 4.77 MB — genuinely served,
   and worth knowing before it reaches a chunker.
8. **Run twice.** The second run must write nothing.
9. **Write the regression test** for anything you fixed, naming the real defect.
10. **Update PLAN.md and this file** if the site taught you something new.

---

## Open risks

- **`generic` (trafilatura) fallback is unwritten.** A new source with no bespoke
  extractor currently has no path at all — deliberate, but it means adding a partner is
  not yet a config-only change.
- **The 4.77 MB pages** pass every check and will need a chunking strategy before the
  corpus is embedded.
- **Only the latest fetch of each URL is archived.** "What changed in this doc?" is not
  answerable today; keeping hash-suffixed prior versions would fix it cheaply.
- **`/api/**` (3,526 pages) still needs the browser tier**, and browser fetching is the
  one part of this design that has never been exercised against a live site.
- **69 documentation pages are known-missing** and discoverable only via the link graph;
  the seed dump exists (`sitemap-dumps/link-gap.txt`) but has not been fetched.
- **`code.claude.com` is not configured as a source**, and for a partner-facing team it
  is likely the most valuable site currently absent.
