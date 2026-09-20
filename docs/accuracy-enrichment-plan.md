# Enrichment: more information per change, and the volume question

> Written 2026-09-20, after the accuracy arc (issues 01–13) closed. This plans the
> *next* horizon: raising digest accuracy by giving the pipeline more information —
> ad-hoc rules, trained text classifiers, LLM annotators (Jev, Haiku) — and by
> settling whether the sheer number of diffs is degrading accuracy more than the
> current instruments measure. Options carry pros and cons and each item names the
> number to get first; nothing here is a commitment to build. Figures trace to the
> ledger (`digest.py accuracy`), the issue records under `issue/accuracy/`, and
> `docs/digest-experiments-2026-09-19.md`.
>
> Decisions already taken (2026-09-20, Doug): Jev is a **hosted API**, so per-change
> use is a standing cost. Standing cost is **acceptable if measured** — a graded A/B
> must show a paid component beats the free deterministic baseline by a margin worth
> the cost, and deterministic baselines come first. Labels for ML are produced by
> **model-assisted pre-labeling with every label human-approved in dedicated
> sessions**.

## 0. Frame

### Where information can enter

The pipeline has six injection points, and every idea below lands in one of them:

1. **Compressed-record annotations** — what each of the ~1,000–6,300 one-line
   records carries (today: kind, severity, signals, cause, excerpt).
2. **Excerpt selection** — which lines of a change the model sees (today:
   RESTRICTION-boosted, clause-windowed; the v3 default).
3. **The digest prompt** — rules and appendices (today: the v2 text; the injection
   appendix was measured and rejected).
4. **Session tools** — what the model can look up (`get_diff`, `read_page`,
   `inbound_links`, `list_changes`).
5. **Post-hoc audit** — checks on findings after they exist (newness, quotes,
   mirror dedup).
6. **Absence-candidate generation** — what the scan surfaces as possibly missed.

### Laws inherited from the arc, now proven rather than assumed

- **One input change per arm**, each under its own version stamp, graded through the
  ledger. The combined arm's interference terms are the standing evidence.
- **Annotate, never filter.** A classifier that drops changes reopens the silent
  false-negative path that killed phase-2 option B. Every enrichment *adds* a label
  or a line; nothing removes a change from the model's reach.
- **The deterministic baseline gate.** Any learned or paid component must beat the
  free lexicon/rule it would replace *on the same held-out labeled data* before an
  arm is spent on it. The arc rejected three plausible designs this way for
  CPU-seconds each; the gate is the cheapest filter we own.
- **Annotator output is information, never ground truth.** Labels an LLM emits pass
  the human-approval gate before entering training data or the record.

## 1. The volume question — first, because it bounds everything else

Enrichment adds tokens to a prompt that already measured **305k real tokens** on
#6 → #7 (6,329 records; the estimator hid this until issue 06). If volume itself
degrades synthesis recall, enrichment can net-harm. The honest state of evidence:

- **For "volume is fine":** locate-recall 3/3 at the real 305k; digest-mode top-30
  identical between full and collapsed renderings; graded-true findings cite pages
  at ranks 874 and 948 (issue 08 — the model reads the whole feed).
- **Against, and unmeasured:** locate is the *easy* test, by the probe's own
  docstring — being told what to find is not noticing it unprompted. Every draw
  rate in the ledger is a **precision** measure; volume-driven *recall* loss is
  structurally invisible to the headline metric. And the boost confirm's narrowing —
  **62 findings vs the baseline's 79, two needle pages uncited including a
  verified-true control** — is exactly what volume-degraded synthesis would look
  like, unresolved at n=1.

Doug's suspicion is therefore legitimate and partially uninstrumented. Measurements,
cheapest first:

| measurement | cost | what it answers |
|---|---|---|
| **Citation-rate by feed-position decile**, all nine stored runs, within severity tie-blocks | free | does position in the long list gate the *rate* of finding-writing? (08 established existence at the bottom, not rate) |
| **Standing per-run metrics** in the run report: finding count, needle citations, absence coverage | free | the narrowing watch, formalized — n grows by one per week without anyone remembering to check |
| **Volume-recall curve**: the same pair digested at 2–3 rendered sizes (full / full+collapse / top-N-only-as-probe), needle recall graded per size | ~$10–15 | the direct answer. The queued collapse A/B (`+c`/`+m`, −55% tokens, built, ungraded) **is arm one of this curve** — design them as one experiment, not two |

**Decision rule:** if the curve shows recall rising as volume falls, the collapse
becomes an *accuracy* adoption and every §2–4 annotation must justify its token
cost; if flat, annotations are cheap and the narrowing gets attributed to the boost
mechanism instead. Either result reshapes the rest of this plan — which is why §1 is
first.

## 2. Deterministic enrichment — free, and first in line

Ranked by expected leverage on the *open* error classes (plain-noun newness;
invented past on rewrites; over-broad quantifiers; `breaking` over-labels).

### 2.1 Structural table/list diffing

Parse markdown tables and lists in changed regions; diff **rows, cells, and items**
instead of lines. One mechanism, three consumers:

- *Excerpts:* "row `DENY` added to existing enum" / "cell changed: `10,000` →
  `25,000`" — the DENY class (plain-noun newness, identical on both pairs, no
  deterministic handle found in issue 03) becomes mechanically stated, because "item
  added to an existing list" is exactly the granularity the line diff destroys.
- *Marking:* issue 07's `~+` pairing currently approximates a revised row with
  Jaccard overlap (known length-sensitivity: the real pair scores 0.88, an
  abbreviated one 0.58). A cell-level diff *is* the provenance, no threshold dial.
- *Audit:* "the finding claims X is new; the structural diff says X's row existed
  and one cell changed" — the Grok/GLM check without identifier extraction.

- *Pro:* targets both open error classes at their shared root (tables rewritten
  whole); deterministic; feeds three existing consumers without new prompt text.
- *Con:* markdown table parsing on vendor-generated pages is messier than it looks
  (ragged rows, inline HTML); a wrong structural diff is more confidently wrong
  than a line diff. Scope it to well-formed tables first, fall back to lines.

**The number first:** how many graded errors and needles trace to table/list
regions — countable from the stored blobs against the ~280 graded findings. If it
is most of them (the Grok, DENY, USE CONNECTION, and Unsloth cases all suggest so),
this is the highest-leverage build in the plan.

### 2.2 Churn priors per page

From snapshot history (free SQL over `page_versions`): annotate each record with
`churn:9/10` — changed in nine of the last ten windows. The model currently
re-derives "this is API-reference regeneration" every week from shape alone; a
prior states it, and its inverse — a *rarely-changing* page changing — is a signal
nothing currently carries.

- *Pro:* free, tiny (≈9 characters/record), uses data already stored; helps both
  discounting (regen) and attention (unusual movers).
- *Con:* needs ≥5 snapshots of history to mean anything (we have 8); it is a prior,
  and the injection arms proved the model over-trusts context it is handed — the
  arm must check that high-churn annotation doesn't suppress *true* findings on
  regen pages (the API-reference share of graded-true findings is the check).

### 2.3 Cross-run finding memory

Annotate pages whose previous window produced a graded-true finding ("last window:
retention restriction, graded true"). The ledger becomes an information *source*,
not only a metric.

- *Pro:* continuity is exactly what a weekly reader wants ("the restriction
  announced last week was widened"); bounded — a handful of pages per run.
- *Con:* it feeds the model assertions about the past, which is the invented-past
  error's food. Mitigation is the provenance lesson: the annotation quotes the
  *finding id and verdict*, not a paraphrase of history.

### 2.4 Error-signature registry

Generalize the 547-signature census into a registry of known model-error regexes
run post-hoc over every finding — the `noise.py` pattern, applied to findings:
named signatures, each with an admission record and a test from the real text that
motivated it. Seeds: "already documented/stated/existed" (fires only under
visibility-without-provenance arms — a canary for provenance regressions);
over-broad quantifiers ("only", "all", "every" in headlines — both re-grade
downgrades were this shape); grab-bag conjunction chains.

- *Pro:* each signature is a one-line regex with measured precision; the registry
  shape is proven twice (noise patterns, needle files).
- *Con:* signatures are shaped like past incidents — the arc's own recorded
  limitation. They catch recurrences, not novelty; that is their honest job.

## 3. Trained classifiers (ML)

The binding constraint is **labels, not architecture**. Everything here is gated on
the dataset, so the dataset comes first.

### 3.1 The labeled-line dataset

Per Doug's decision: **model-assisted pre-labeling, every label human-approved in
dedicated sessions.** Mechanics in the house style:

- Stored like needles: verbatim real changed lines, label, source page and pair,
  pre-labeler identity, approver, session date. One YAML per labeling session,
  imported to a table the way verdicts are (worksheet → validate → store).
- **Taxonomy mirrors what downstream consumes**: `restriction` /
  `behavioural-change` / `addition` / `editorial` / `regeneration` — aligned with
  `IMPACTS` so classifier output is comparable with finding labels directly.
- **Record the flip rate** (pre-label vs human approval) per session — it is the
  measure of the pre-labeler's bias leaking into ground truth, and it is the number
  that decides whether pre-labeling is helping or steering.
- Seeds already on disk: the 50 hand-read scan candidates (~55–60% restriction
  precision), the 64-diff stratified read, and ~280 graded findings (weak
  line-level labels via cited pages). Target for session one: **300–500 lines**,
  stratified by company and by lexicon-hit/no-hit (the no-hit stratum is where a
  classifier could actually add something).

### 3.2 The capability ladder

| rung | what | cost | gate |
|---|---|---|---|
| 1 | TF-IDF + logistic regression / gradient boosting on changed lines (scikit-learn, CPU) | free inference | beat the RESTRICTION lexicon on held-out labels — precision *and* the no-hit-stratum recall, or it does not ship |
| 2 | local sentence embeddings: upgrade 07's Jaccard pairing; semantic restriction scoring; pre-digest story *clustering as annotation* ("story:17" tags — phase-2 rejected exact-match clustering; embeddings retry the idea without the brittleness, and without filtering) | free inference, one-time model download | pairing: fewer over/under-pairs than Jaccard on the recorded real cases; clustering: the Admin-mirror and re-date groups recovered without exact-match rules |
| 3 | fine-tuned transformer | GPU + thousands of labels | deferred until rungs 1–2 plateau on a dataset 5–10× today's; revisit then, not before |

- *Pro (the ladder as a whole):* free at inference forever, so it never fights the
  standing-cost constraint; interpretable at rung 1 (coefficients are a lexicon the
  data wrote).
- *Con:* the lexicons already encode most of the obvious signal — the honest prior
  is that rung 1 ties the regex on lexicon-hit lines and earns its keep only on the
  no-hit stratum. That is exactly what the held-out split must measure, which is
  why the dataset is stratified that way.

## 4. LLM annotators — Jev and Haiku

Jev is a hosted classification API (post-cutoff release; capabilities, pricing,
rate limits, and context size are **unknown facts to gather, not assume** — that
evaluation is step one and produces a short recorded profile). The protocol keeps
standing cost at $0 until something earns it:

1. **Offline benchmark, $0 standing.** Jev, Haiku, the RESTRICTION lexicon, and
   rung-1 ML, all on the same held-out labeled set from §3.1. Report
   precision/recall per class, cost per 1k changes, latency, and failure modes.
   One table, in this document, when it exists.
2. **Adoption path, only for a winner with a worthwhile margin:** per-change labels
   appended to compressed records (annotate-never-filter), ~6,300 changes/run
   batched. The annotator gets a **version stamp** recorded with the run (the
   PROMPT_VERSION lesson applies to annotators: a silently updated hosted model
   changes the output and nothing else records it — and a hosted API *will* update
   under us, which is a standing comparability risk the profile must state).
   Ships as its own arm, graded, against the projected standing cost.
3. **The scoped variant, cheaper and probably first:** annotate only the absence
   scan's ~117 candidates and the ambiguous no-lexicon-hit records — dozens of
   calls, not thousands — where a classifier's marginal value is highest and the
   cost is cents. If scoped annotation moves nothing in a graded arm, full-feed
   annotation will not either.

- *Pro:* an LLM classifier handles paraphrase and context the regexes structurally
  cannot; the benchmark is cheap and reusable for every future candidate model.
- *Con:* a hosted dependency in a pipeline that is otherwise reproducible offline
  from blobs; per-run cost scales with the vendor-event tail (a re-date week means
  6,300 calls unless the terse kinds are excluded — they should be); and the
  injection arms proved the model over-weights labels it is handed, so annotator
  *errors* propagate with authority. The arm's cluster checks must include the
  known anchoring signatures.

## 5. Guard rails — what this plan deliberately does not build

- **No classifier-as-filter**, however good the benchmark looks. Annotation only.
- **No corpus-wide existence semantics** — measured and rejected in issue 03 (one
  early cookbook page would have flagged nine true launch findings).
- **No ranking-formula coupling** — issue 08's guard stands; enrichment feeds
  excerpts, annotations, and audits, not `severity`.
- **Annotations compete for the token budget §1 interrogates.** No §2–4 arm ships
  before §1's free measurements exist; if the volume-recall curve shows recall
  falling with size, every annotation pays its way in tokens too.
- **No LLM output enters training data unapproved** — the flip-rate-measured human
  gate is the boundary between information and ground truth.

## 6. Sequencing and cost

| phase | items | new standing cost |
|---|---|---|
| P0 (free, next) | §1 position/citation-rate analysis · standing per-run metrics · churn-prior prototype (annotation built, off by default) | $0 |
| P1 | structural table/list diff (build + arm) · volume-recall curve **with** the queued collapse A/B | $0 standing; ~$10–15 experiments |
| P2 | labeling session one (300–500 lines, pre-label + approval) · benchmark harness · Jev profile | $0 standing; cents–few $ for pre-labeling and benchmark calls |
| P3 | benchmark winner as a scoped annotator arm (if it beat the baseline) · error-signature registry · cross-run memory arm | $0 until a winner earns adoption |

Every arm follows the arc's grading protocol (seeded full-page draw, needles,
coverage, cluster checks) and the choreography fix (`run --no-replace` + current-set
pointer) should land before the first new arm campaign — the manual
supersede/restore dance already produced one silent failure.

## 7. What would change this plan

- **§1's curve showing recall falls with volume** promotes the collapse to an
  accuracy adoption and demotes every token-adding annotation until re-measured at
  the smaller size.
- **The structural-diff count coming back small** (few graded errors in table/list
  regions) demotes §2.1 from first build to opportunistic.
- **Rung 1 failing its gate** (no lift over the lexicon on the no-hit stratum) puts
  the whole ML ladder on ice and makes the scoped LLM annotator the only live
  classifier candidate — the benchmark decides, not the enthusiasm.
- **The next natural windows resolving the narrowing** (finding counts and needle
  citations recovering under v3) removes the recall alarm that motivates half of
  §1; the curve is then optional calibration rather than a gating question.
