# Phase 2: the change digest — decision record

> Decided 2026-08-29, against measurements from `reports/changefeed/0001..0002.json`
> (snapshots #1 → #2, 11 days). Re-measure before re-litigating; the numbers are what the
> decision rests on, and they are cheap to recompute.

## Decision

**Compress every change deterministically, then hand the whole run to one Claude Agent SDK
session.** No batching, no pre-filter, no clustering pass.

The session receives all ~1,200 compressed change records at once, plus read-only tools to
open the full diff for anything it wants to inspect, and reports through a `record_finding`
tool so the digest is rendered from structured rows rather than parsed out of prose.

## The numbers it rests on

| | measured |
|---|---|
| changes reaching a model per run | **1,182** (11 days) ≈ 752/week |
| every diff sent whole | 6.1M tokens · ~$30/run input |
| **each change compressed to one line** | **92k tokens · ~$0.50/run input** |
| mean compressed record | 273 characters |
| categories spanned | 78, of which 26 carry ≥10 changes |
| exact-duplicate change groups | 87 pages in 24 groups, largest 15 |
| severity carried by the top 25 / 100 | 8.4% / 26.6% |

A compressed record looks like this — identity, evidence, and the two most informative
changed lines, preferring lines that carry status language:

```
databricks/admin MOD sev1.4 [s1,h2,n4,l3] admin/account-settings/custom-url ::
  - Your account must not use [Chrome-managed passkeys](…) | + ## What changes when you use a custom URL
```

**The whole run fits in one context window with room to spare.** That single fact decided
everything below.

## Why not the three options this replaced

The original framing assumed the model had to process a run piecemeal, because a run was too
big to see at once. It is not. Each rejected option was designed around a constraint that
does not exist, and each pays a real cost for it.

### A — batched triage (~25 changes per session)

**Rejected: batching destroys the capability it was chosen for.** A existed for cross-page
synthesis, but a 25-item batch cannot see that 452 of 1,182 changes are one API-reference
regeneration, or that `api/beta/files` and `api/beta/skills` moving to `api/*` are one story
about promoting APIs out of beta. Whole-run context can.

It also costs ~47 sessions per run instead of one, and its batches are arbitrary slices of a
long tail — see the severity note below.

### B — two-pass, cheap filter then deep agent

**Rejected: it opens a silent false-negative path for no benefit.** B's premise was that
volume made a pre-filter necessary. At 92k tokens it is not. What it would add is a
classification pass that can drop a breaking change before any careful reader sees it —
invisible under-reporting, the one failure mode a change feed cannot recover from, requiring
a standing sampling audit to trust. Paying that price to solve a solved problem is a bad
trade.

### C — deterministic clustering before the model

**Rejected as a primary mechanism; the evidence got firmer, not weaker.** Measured directly:
only **87 pages across 24 groups** share an identical changed-line set, largest group 15. That
collapses about 5% of a run. Earlier link-move analysis agreed — the largest single path move
(`/docs/en/about-claude/models` → `/docs/en/models`) touched 29 pages, and only 2% of
Anthropic pages changed *purely* by link rewriting.

Clustering by exact match is brittle in the way that matters: it groups pages that changed
*identically*, not pages that changed *for the same reason*. Reading across the run is what
finds the latter, and that is what the model is for.

### And why not "just show the top 30"

Severity ordering ([issue 02](../issue/changefeed-phase-2-readiness/02-rework-change-weighting.md))
made the feed readable, but it cannot substitute for synthesis. The distribution is flat: the
top 25 carries 8.4% of total severity and the top 100 carries 26.6%. There is no small head
holding most of the value, so truncation discards real content rather than noise.

## The design

**Stage 1 — compression (no model).** Every change becomes one record: company, category,
kind, severity, signal counts, path, and a bounded excerpt of the changed lines, ordered to
put status language first. Nothing is filtered. The false-negative path never opens, because
every change is present in the prompt.

**Stage 2 — one session (Claude Agent SDK).** Input is the full compressed run. Tools, all
read-only:

| tool | purpose |
|---|---|
| `get_diff(url)` | the full unified diff for one change |
| `read_page(url)` | the current body from `data/` |
| `inbound_links(url)` | who points at this page — the impact signal |
| `record_finding(urls, ...)` | the agent's **output channel**: structured rows, not prose. Takes a **list** of URLs so one finding covers a story spanning many pages — measurement showed 44 returned items carried only ~25 distinct stories |

This is where the Agent SDK earns its place over a single API call. The model sees everything
cheaply, then *chooses* the twenty diffs worth opening in full. That is a tool loop, not a
prompt.

**Output.** `record_finding` rows render deterministically into the digest, so a report can be
re-rendered — different audience, different length — without re-running the model. Note the
Python `@tool` decorator forwards only `content` and `is_error`; `structuredContent` is
TypeScript-only, so the handler writes the row itself.

**Validate tool arguments against the run.** A schema can guarantee a finding is well-formed;
only a membership test shows it is about something that actually changed. The handler should
reject any URL not in the run's change set and return `is_error: True`, so the model sees the
rejection and corrects itself rather than silently citing a page nobody touched. Three runs
produced zero invented paths, so this is a guard rail rather than an observed problem — but
it costs nothing and turns a silent corruption into a visible, self-correcting failure. Do
**not** enum the URLs in the schema: 1,300 of them would add tens of thousands of tokens to
every turn and duplicate the input.

## Cost

~105k input tokens per run, plus drill-down tool calls and output. **Measured at $4.06 for a
complete run** — see the stage 2 result below; the earlier $0.50 estimate priced a single
call and a digest is an agentic loop. Weekly cadence puts it around $20 a month. Cost is not
a design constraint at that level, but it is not free either, and `--max-budget` should
always be set.

For contrast, sending full diffs would be ~6.1M input tokens (~$30/run), and option A's ~47
sessions would exceed that while seeing less.

## Build status (2026-08-30)

**Stage 1 is built and verified against real data. The recall risk is measured and does not
materialise.** Stage 2 — the session that consumes the compressed run — is not built.

```
src/changefeed/digest/
  compress.py          deterministic — no model, no SDK, no network
scripts/digest.py      `compress` subcommand: size what a session would read
scripts/probe_recall.py  the recall probe — run; result below
docs/changefeed-needles.yaml   ground truth: 10 needles verified by reading
```

Measured by the real code rather than a prototype, on snapshots #1 → #2:

| | |
|---|---|
| changes compressed | **1,334** — every change, nothing dropped |
| size | 370,872 chars ≈ **105k tokens** |
| mean record | 278 characters |
| time | ~14 s |

105k rather than the 92k first estimated, because this includes the `moved`, `metadata`,
`low` and `noise` entries too. Those get the short form — one line, no excerpt — so the
no-filter promise costs about 13k tokens. Worth it.

**A defect that reading the output caught.** The first excerpts showed the removed and added
lines with no marker of which was which, so `tool-runner`'s record read *"the TypeScript and
Ruby tool runners support automatic compaction"* next to the same sentence including Python —
and nothing said which was current. A model could have drawn the opposite conclusion. Lines
are now prefixed `-` and `+`, with a test.

## The risk, and how it gets tested

**Not cost, and not context limits — synthesis recall over a long flat list.** 92k tokens is
modest for a 1M-context model, but a list of 1,182 broadly similar items is exactly the shape
where things get dropped, and this feed's value depends on not dropping the one deprecation
that matters.

Test it rather than assume it. These changes are already verified by reading and should each
appear in a digest of the #1 → #2 run:

| | |
|---|---|
| `api/beta-headers` | `files-api-2025-04-14` → `context-management-2025-06-27` |
| `tool-use/tool-runner` | **Python dropped** from the runtimes with automatic compaction |
| `foundation-model-overview` | a region's models change `databricks-gpt-5-5-pro` → `databricks-grok-4-6` |
| `about-claude/model-deprecations` | the deprecations page itself |
| `sql-ref-syntax-ddl-create-streaming-table` | `pipelines.channel` **no longer supported** |
| `sql/.../ip_network` | the function left Beta |

The needles live in [`changefeed-needles.yaml`](changefeed-needles.yaml) with their rank in
the run, because a recall figure that does not say *where* the needles were is meaningless.
They are well spread — ranks **1, 2, 3, 5, 6, 36, 67, 82, 153 and 1113 of 1,116**. The last
is `access-transparency`, the known false negative from issue 02: a product rename with no
status word, number, link, code or heading change, which severity scores 0.00 and puts near
the bottom of the run. If the digest finds that, the long-context worry is settled.

`scripts/probe_recall.py` runs it, in two modes that are deliberately not the same test:

- **`locate`** asks for each needle by description. The *easy* test — being told what to look
  for is far easier than noticing it unprompted, so passing proves little. Failing is
  decisive: no prompt fixes it, and the fallback becomes mandatory.
- **`digest`** asks for the most important changes with no hint, then checks needle coverage.
  The test that counts.

`--dry-run` shows what would be sent and its size without calling anything. The probe refuses
to run against any snapshot pair other than the one the needles were read from — pointed
elsewhere it would report ten misses that look like catastrophic failure and are not.

### Result (2026-08-30): no long-context failure

Measured, not assumed. Roughly nine calls, ~$5.

| mode | result | what it means |
|---|---|---|
| `digest` — asked for the top 30, no hint | **6/10** | agreement with a human's top-30, not recall |
| `locate` — asked to find each of the four `digest` misses | **4/4** | **recall** |

**Every needle is reachable, including rank 1113 of 1,116** — `access-transparency`, the
product rename with no structural signal that severity scores 0.00 and puts near the bottom
of the run. The model found it in a 105k-token prompt. The "lost in the middle" worry does
not apply here, and the hierarchical fallback below is not needed.

The four `digest` misses are judgement disagreements, and two are defensible: a function
*leaving* Beta is good news rather than something "likely to break", and a product rename is
not a breaking change. The other two — a region swapping `databricks-gpt-5-5-pro` for
`databricks-grok-4-6`, and `vector_search` narrowing its availability — are prompt-tuning
work, not architecture.

**Three apparent failures were defects in the test, none in the model.** Worth recording,
because the first reading of each was "the model got it wrong":

1. A `TextBlock` in claude-agent-sdk 0.2.148 has no `type` attribute, so duck-typed
   extraction discarded a correct answer and reported zero lines. Use `isinstance`.
2. The `ip_network` needle asked for "the single change" when **18 pages** in the run had a
   Beta admonition removed, six of them byte-identical. Any answer was correct.
3. Broadened to the function pages, it still missed — because the model named the IP
   functions *overview* page, a better answer than the needle anticipated. `url_contains`
   now accepts a list.

A fourth bug made this worse: the probe's own recall counter summed every row instead of the
matching ones, so a total failure printed `recall 10/10` and exited 0.

### Precision and stability (2026-08-30): three runs at top-50

Recall against "every important change" is **structurally impossible**, and measuring it was
the wrong goal. A labelled sample of 50 changes drawn at random from the 1,151 eligible found
**14 genuinely important (28%)**, which extrapolates to ~322 in the run. A digest of 50 can
cover at most 16% of that by construction. So the question is not how many important changes
it finds — it is whether the 50 it picks are the right ones.

Three runs, `--top 50`, on the identical input:

| | result |
|---|---|
| stability (Jaccard across 3 runs) | **0.81** — 44 of 54 items in all three |
| hallucinated paths | **0** of 147 returned |
| duplicate paths | **0** |
| precision, judging the 44 stable items by hand | **44/44** |

Every one of the 44 is a genuine capability, availability, deprecation, or requirement
change: the Supervisor API reaching end of life on 2026-09-30, legacy stable IPs
decommissioned, `output_format` moving to `output_config.format`, ten `ai_*` functions
gaining a Databricks Runtime floor, `pipelines.channel` no longer supported. **Not one is
schema regeneration, casing, or boilerplate** — in a population where 72% is exactly that.
Random selection would score ~28%.

**The weakness is redundancy, not accuracy.** Those 44 slots carry only about **25 distinct
stories**. Ten went to the same runtime-version requirement across `ai_*` functions; four to
`pipelines.channel`; three to the Supervisor API deprecation; two each to the legacy-IP
decommission and the AI Gateway entitlement change.

That is an artifact of the probe's output format, not of the approach: it asked for a list of
paths, which forces one line per page. It has a direct consequence for the design —
**`record_finding` must accept a list of URLs, not one**, so a single finding can say "the
`ai_*` functions now require DBR 15.4+" and cite ten pages. Without that, a third of the
digest is repetition.

**Fallback if recall is poor:** a hierarchical reduce — synthesize per category, then across
the summaries. Only 26 categories carry ≥10 changes, so that is a cheap second stage rather
than a redesign. Do not build it pre-emptively.

## Stage 2 result (2026-08-30): built and run

```
src/changefeed/digest/
  findings.py   the findings table in changes.db + deterministic rendering
  tools.py      four read-only tools + record_finding(s); handlers are model-free
  session.py    the one session; the only module importing claude-agent-sdk
scripts/digest.py   compress | run | render
```

First full run over snapshots #1 → #2:

| | |
|---|---|
| findings | **45** — 9 breaking, 18 behavioural, 11 additive, 7 editorial |
| pages cited | 403 of 1,334 |
| citations per finding | median 7, max 26 |
| cost | **$4.06** |
| wall clock | 9 min |

**Story-level grouping works, which was the open question.** One finding covers the
Foundation Model Fine-tuning end of life across ten pages; another covers the Admin API
being republished under `api/beta/organization/*` across 36. The redundancy that made the
path-list probe return ~25 stories in 44 slots is gone.

It also found a breaking change that hand-labelling missed: `BUNDLE_ROOT` renamed to
`DATABRICKS_BUNDLE_ROOT` across seven CI/CD pages, which the 50-change labelled sample had
marked *not important*.

### Cost was 5–10× the estimate, and the estimate measured the wrong thing

The figure below — ~$0.50 per run — was derived from a single 105k-token call. A digest is
an **agentic loop**: every tool call re-sends the whole change list, so turns, not tokens,
are what it costs. The first attempt recorded twenty findings one call at a time and hit a
$5 budget cap without finishing.

The fix was a `record_findings` batch tool and a prompt that asks for batches of ten or
more. Same run, complete, **$4.06**. Budget for **$4–6 per weekly run**, not $0.50, and keep
`--max-budget` set: a cap is now handled as an outcome rather than an exception, because
findings are written as each call lands and are durable even when a session stops early.

### Validation: 69 rejections, and they were ours

The run reported 69 citations rejected as pages that did not change. That looked like the
membership test catching hallucination. It was not: `DigestContext.find` matched the full
URL and then fell back to fuzzy containment, which rejected **194 of 1,334 legitimate
slugs** — every short one, because `ai-gateway/` is a substring of
`ai-gateway/query-model-services` and the uniqueness check then found several and gave up.
The prompt shows slugs, so slugs are what the model answers with.

Fixed by resolving exact URL → exact slug → unique suffix; all 1,334 now resolve, with a
test. The observed hallucination rate is therefore **unmeasured, and probably near zero** —
the earlier path-list probe returned zero invented paths across 147. The report now prints
sample rejected URLs rather than a bare count, because a count alone was read as a model
failure twice.

### Are the findings *true*? (2026-08-30)

Everything above measures whether the digest picks the right changes. Nothing measured
whether what it *says* about them is correct — the claims are prose generated from a
280-character excerpt, and URL validation proves only that a cited page changed.

Audited by hand: ten findings drawn seeded and stratified by impact, each read against the
actual changed lines of the pages it cites (`scripts/digest.py audit`).

| | |
|---|---|
| true | **9** |
| partly true | 1 |
| false | **0** |

Verified precisely, including details: `Python, TypeScript, and Ruby` → `TypeScript and
Ruby` on the tool runner; Foundation Model Fine-tuning moving from "scheduled for removal
2026-08-14" to "reached end of life"; AI Functions replacing a serverless requirement with a
DBR 15.4 floor *and* dropping Pro SQL warehouses from the exclusion list; row tracking
corrected from 14.1 to 14.0; the workspace-isolation warning added to Files and Skills.

The one partial: a finding said Lakeflow links were rewritten to "Choose a standard
connector" where the diff shows "Lakeflow Connect connector concepts". The reframing is real,
that detail is not. Imprecision in a supporting clause, not a fabricated claim.

**This is now standing practice.** `scripts/digest.py audit --n 10` draws a seeded sample and
prints each finding beside its evidence; it costs nothing and should run after every digest.

Two defects in the audit tool itself, both found by reading its output — which is the same
lesson as §11b, one layer up:

- it selected changed lines in multiset order, which surfaced blank lines and `> **Note:**`
  boilerplate that could neither confirm nor refute a claim. It now orders by status language
  then length, as the compressed excerpt does.
- an `added` page reported "(stored body unavailable)", implying a fault where a new page
  simply has no before-side.

### Second run, after the fixes (2026-08-30)

The first digest predated the slug-resolver repair and the attribution exclusion. Re-run
clean:

| | run 1 | run 2 |
|---|---|---|
| findings | 45 | **41** |
| pages cited | 403 | **544** |
| rejected citations | 69 (all a resolver bug) | **0** |
| findings per tool call | ~1 | **20.5** |
| cost | $4.06 | **$3.25** |
| wall clock | 9 min | **6 min** |

**Stability, as a spot-check rather than a figure:** 7 of run 1's 9 breaking headlines recur
in run 2. Two dropped (an Admin API tunnel deprecation, a container `acl` requirement), one
new appeared (`ant` CLI now needs Go 1.25). Two runs is not a distribution — this says the
digest is broadly reproducible at the top, not that it is deterministic.

That comparison was nearly impossible to make: the re-run **deleted** run 1's findings, and
only the headlines that happened to be in terminal scrollback survived. Findings are now
*superseded* rather than removed, so the next comparison has both sides.

### Guards added after the first run

- **`--max-budget` defaults to $8** (~2× a measured run). Uncapped requires `--no-budget`.
  The first session ever run reached $5 in six minutes.
- **Batching is now observable.** `DigestResult` reports findings-per-call and flags a
  regression below 3, because the cost fix depends on the model choosing to batch and
  nothing else would show a drift back to one-per-call except the invoice.
- **The session layer has tests.** A stubbed `query` asserts option wiring, prompt
  formatting, and that a budget exception yields a result rather than propagating.
- **Findings carry `model` and `prompt_version`.** `PROMPT_VERSION` bumps whenever the
  prompt changes, so runs from different prompts are not silently compared.
- **`changes.py backup DIR`** copies the history — the only artifact here that cannot be
  rebuilt. The database goes through SQLite's backup API (a file copy of a WAL database
  mid-write is not guaranteed consistent); the content-addressed blob store copies
  incrementally, so a second backup moves only what is new.
- **Digests are tracked in git**; the 700 KB feed report and 2.5 MB JSON beside them are not.

### Third pair, #5 → #6: the excerpt audit was too lenient (2026-09-18)

The first pair with a model launch in it (Claude Fable 5.1 / Mythos 5.1, plus five new
Databricks-hosted models). Checked against **full pages** instead of the audit's four-line
excerpts, the prompt-v1 digest (48 findings) had errors the 9/1/0 audit above would not have
caught:

- Grok 4.6 and GLM 5.3 called "added" — both were already listed in #5
- Fable 5.1 retention misstated. The page says *"Customers who opt out of data retention
  cannot use Claude Fable 5.1"*
- **missed:** that same sentence is new for the **existing** Claude Fable 5, so opted-out
  customers lose a model they already had. The most consequential change in the pair, and it
  was not in the digest
- consequences the docs never state: a Priority Tier "fallback", compaction "400s", Genie Code
  "breaking every deep link" (the old page still exists and the links were repointed)
- one grab-bag finding with three unrelated stories; `breaking` on 12 of 48
  findings, several of them wrong

**The excerpt audit judges whether a claim matches the lines shown, not whether it is true.**
A finding citing 13 pages gets three shown, and a newness claim can't be checked without the
old text.

Three changes followed:

1. **Prompt v2.** Say only what the page says. Check the old text before calling something
   new. `breaking` means something that worked stops working or needs action, including a new
   restriction on something that already exists. Look for restrictions hidden inside additions
   and record each as its own finding. One story per finding.
2. **The audit checks newness mechanically.** For a finding whose headline claims something
   new, every versioned name in the headline (`Grok 4.6`, `GLM-5.3`, `grok-4-6`, backticked
   ids) is looked up in the BEFORE text of its cited pages, with separators normalised so
   prose and id forms match each other. It also has to survive into the AFTER text, so "pins
   X instead of Y" doesn't flag Y. The audit also says when it shows less than half the
   evidence (`! only 23% of the evidence is shown`).
3. The check took three tries, each fixed by running it on real findings. v1 matched only id
   forms and **missed the Grok 4.6 case it was written for**; its synthetic test used an id
   and passed. It also checked the detail text and flagged context (`us-east-1`). After those
   fixes, v2's phrasing slipped past it: the bare verb "add" and `GLM-5.3`. Each has a test
   built from the exact text that got past it.

**Prompt v2 on the same pair:** 63 findings, 584 pages cited, $2.81, 63 findings per call.

| v1 error | v2 |
|---|---|
| Grok 4.6 / GLM 5.3 "added" | **still wrong** (#54). Now flagged by the audit |
| Fable 5.1 retention misstated | fixed in #10; **still wrong** in #54's detail ("an opt-out path") |
| new restriction on existing Fable 5 | **still missed**, even with a rule written for exactly this |
| Priority Tier "fallback" | gone. But #45 misstates the old list, which also excluded Opus 5 and Sonnet 5 |
| compaction "400s" | gone |
| Genie Code "breaking every deep link" | fixed: "links were repointed" (#62) |
| grab-bag finding | gone. Stories split: ABAC GA and DENY are now two findings |
| `breaking` overused | 12 → 4. One is still wrong: CMEK "Fable 5" → "Fable" widens the exclusion to a model that is new this week (#2) |

New errors in v2: #40 calls `code_execution_20260120` SDK support new. That release note was
already in #5, and only its availability tail changed. The audit flagged it. #50 presents a
placement constraint that existed before as new; it was actually narrowed.

**Verdict: accuracy improved but did not recover.** Unstated consequences and mislabelled
impact mostly went away. The two errors that matter most did not: false newness and a missed
restriction on an existing model. Prompt rules didn't fix either. The first is now caught
mechanically. The second is not, because nothing checks for **absence**: no audit can flag a
finding that was never written.

Known audit false positive: #38 ("PCI-DSS now covers all regions rather than us-east-1 only")
flags `us-east-1`, which the headline names as the old state on purpose. *Resolved
(2026-09-18): regions are excluded from identifier extraction by shape — a region is where
something became available, never the thing that became available — and the measurement
found the same false positive one run earlier, unrecorded (finding 91). Broadening the
extractor in the other direction was measured on all 231 stored findings and rejected;
[issue/accuracy/03](../issue/accuracy/03-newness-coverage.md) has the numbers, including
why a corpus-wide check would have flagged nine true launch findings over one early
cookbook page.*

**Open: detecting new restrictions on existing things.** It could be a deterministic pass: a
sentence added on the + side that contains restriction language (`cannot`, `not available`,
`must`, `requires`, `rejected`) and names a model or feature that was already in the BEFORE
text. That pass would have found the Fable 5 sentence. Measure its hit rate on #5 → #6 before
deciding whether it feeds the session or the audit.

*Update (2026-09-18):* those trigger words were measured against the severity lexicon in
[issue/accuracy/02](../issue/accuracy/02-restriction-lexicon.md), and the result reframes
this miss. Admitting them to STATUS moves the retention page only from rank 538 to 499 —
density arithmetic cannot rescue a five-line restriction inside a 62-line rewrite — while
pulling Admin-API boilerplate into the top-100, so STATUS stays as it is. The sentence was
actually lost to **excerpt truncation**: `cannot` begins at character 140 of the changed
line and `EXCERPT_LINE` is 140. A `RESTRICTION` lexicon now exists (`classify.py`), a
restriction-boosted, clause-windowed excerpt sits behind `digest.py run
--boost-restrictions` pending its graded A/B (findings record `prompt_version` `2+r`), and
run reports carry a `classify_version` stamp. The detector sketched above is still open as
issue/accuracy/05, and remains the only channel that can surface the Fable 5 line itself.

*Update (2026-09-19):* the audit also verifies **claims about the past** now — the graded
runs' most common error class. A quote attributed to the old text must appear in the
before text of the cited pages; a rename's to-quote in the after text. On all 231 stored
findings this flags exactly two claims, both real fabrications: the "support note" quote
of finding 237 (it exists only on the new page — the model quoted the new page as the
old) and finding 202's `"BASIC reports only"` (a paraphrase presented as a quotation).
Term-overlap checking of unquoted past-claims measured ~90% false and was rejected; the
prompt rule that would make the paraphrase class checkable is drafted and gated in
[issue/accuracy/04](../issue/accuracy/04-invented-contrast.md).

### The verdict ledger (2026-09-18): grades stop evaporating

Every accuracy statement above came from a manual audit whose verdicts lived only in prose —
`prompt_version` existed so runs could be compared, and nothing compared them. Built per
[issue/accuracy/01](../issue/accuracy/01-verdict-ledger.md): a `verdicts` table in
`changes.db` (one row per finding × grading method; grades attach to the finding row, so a
superseded run keeps its grades), YAML worksheets in `reports/changefeed/verdicts-*.yaml` as
the editing surface and the provenance — the one part of `changes.db` that *is* rebuildable,
by re-importing. The cycle is `digest.py grade` → edit → `grade --import` → `digest.py
accuracy`; the audit and the worksheet both record stratum weights, because `draw()`
guarantees each impact one slot and an unweighted sample rate over-represents rare impacts.

The ledger refuses to pool three things the prose blurred: **method** (`excerpt` grades
judge claim-vs-lines-shown; only `full-page` grades judge truth), **selection** (`draw`
supports a rate; a `targeted` set picked to chase known errors does not), and the weights.
The three existing grade sets are imported, and separating them changes what the history
says:

| pair | prompt | selection | method | true | partly | false | unverified | rate |
|---|---|---|---|---|---|---|---|---|
| #5 → #6 | v1 | draw | full-page | 4 | 4 | 0 | 1 | 50% (49% weighted) |
| #5 → #6 | v2 | targeted | full-page + excerpt | 3 | 4 | 1 | 0 | not a rate |
| #6 → #7 | v2 | draw | excerpt (6) | 6 | 0 | 0 | 0 | 100% |
| #6 → #7 | v2 | draw | full-page (4) | 1 | 3 | 0 | 0 | — see below |

Two things the table shows that the prose hid. **There is no unbiased full-page accuracy
figure for prompt v2 at all** — the v2 #5 → #6 grades were targeted at v1's error classes,
and #6 → #7's four full-page checks went to the findings that looked suspicious, so the
1-of-4 row inherits that targeting and is not a rate either. The honest v1-to-v2 comparison
still does not exist; producing one is now a single grade cycle (`digest.py grade 5 6`, grade
all rows full-page). And the #6 → #7 "7 true / 3 partly" from the session record is a
**mixed-method** number: 100% of excerpt grades agreed with their excerpts while 3 of 4
full-page checks found errors — which is the 2026-08-30 lesson again, as a measurement.

The graded misses have a standing home too: per-pair needle files
(`docs/changefeed-needles-0005..0006.yaml`, `-0006..0007.yaml`), same genre as the
original, runnable through `probe_recall.py --needles <file>`. The #5 → #6 set leads with
the Fable 5 retention sentence — rank 538 of 986 because `cannot` carries no status signal
([issue/accuracy/02](../issue/accuracy/02-restriction-lexicon.md)); for that needle a
digest-mode URL hit is necessary but not sufficient, since both graded runs cited the page
and still missed the restriction, so `locate` mode is the meaningful automated test.

## What would change this decision

- **A run an order of magnitude larger.** ~12,000 changes would be ~900k compressed tokens
  and the single-session design stops fitting. The observed range does not approach this: a
  quiet Anthropic week drops a run to ~450 changes (~35k tokens), and a launch week twice as
  heavy as the one measured gives ~2,400 (~185k). Both are one session, which is why
  [issue 04](../issue/changefeed-phase-2-readiness/04-quiet-week-measurement.md) no longer
  blocks this decision.
- **Measured recall failure** on the seeded changes above, unfixed by hierarchical reduce.
- **A need for per-page depth** rather than a digest — a different product, and it would
  revive A.

## What phase 2 does not do

It does not decide what is important *to this team*. The digest reports what the vendors
changed; mapping that onto your product surface is
[`kb-application.md`](kb-application.md) item 22, and needs an input this corpus does not
contain.

One thing the digest should say once rather than 452 times: **the Anthropic API reference was
regenerated.** That category is 38% of the run at middling severity and appears nowhere in the
top 100 — the ranking already handles it correctly, but a reader should be told it happened
and then left alone about it.

## See also

- [`changefeed.md`](changefeed.md) — what phase 1 built, and the measured churn
- [`kb-application.md`](kb-application.md) — the catalogue this application comes from
- [`../issue/changefeed-phase-2-readiness/`](../issue/changefeed-phase-2-readiness/README.md)
  — the issue set that produced these numbers
