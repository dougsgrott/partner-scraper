# The review tool: a local UI for grading, labeling, and future human review

> Written 2026-09-20; **built 2026-09-20** — see Build status at the end. Decisions taken
> (Doug): **FastAPI + plain HTML/JS** local web app, no build step; **v1 scope =
> finding grading + line labeling + dashboard**. Figures and module references trace
> to `issue/accuracy/01`, `docs/accuracy-enrichment-plan.md` §3, and the code named
> below, all as of the era boundary (snapshot #8).

## Context

Human-reviewed outputs are the project's scarce resource. Every accuracy decision
runs through hand grades in the verdict ledger; the ML roadmap needs human-approved
line labels; the second-grader criterion of issue 13 is still open. The current
workflow — emit a YAML worksheet, edit it in an editor, import it — works but is
unfriendly and easy to do wrong: method discipline and blind-mode discipline are
manual, and the choreography around experiment arms already produced one silently
empty worksheet.

The tool is a **user-friendly, resumable** local UI with a backend, designed as the
**centralization point** for future human-review functionality. Two design keys make
it survive the weekly code churn:

- **Everything is a review queue.** One abstraction — items, an evidence renderer, a
  verdict schema, a validated write path. New future functionality (absence-candidate
  review, decision records, arm launching) is a new queue or action kind, not a new
  tool.
- **The tool is a thin skin over existing modules.** It renders and writes through
  `verdicts.py`, `audit.py`, `diff.py`, `blobs.py`, `classify.py`, `absence.py`; it
  owns no grading or labeling semantics of its own. When the pipeline refactors, the
  tool moves with the modules it imports rather than duplicating them.

A third principle: **the ledger's integrity rules become UI defaults.** Full-page
method by default; blind mode (prior verdicts hidden until after submit — the
2026-09-20 re-grade protocol, enforced by code instead of discipline); selection,
seed, and stratum weights recorded at queue creation; grader identity on every row.

## Architecture

```
scripts/review.py serve [--port 8765]        # launches uvicorn, prints the URL
src/review/
  app.py        FastAPI app: JSON API + serves static/
  queues.py     Queue protocol + registry; GradingQueue, LabelingQueue
  evidence.py   evidence bundles for one finding / one line (all reuse)
  store.py      additive tables (review_queues, label_sessions, line_labels)
  static/       index.html, app.js, style.css — vanilla, no build step, no npm
tests/test_review.py
```

Dependencies as an optional extra, following the `digest` extra's pattern exactly:
`review = ["fastapi>=0.115", "uvicorn>=0.30"]`. The core pipeline stays free of it;
`scripts/review.py` fails with an install hint when the extra is missing.

## Data model — all additive, no existing row touched

The established patterns in `src/changefeed/db.py` (`CREATE TABLE IF NOT EXISTS`,
`_ADDED_FINDING_COLUMNS`) carry everything:

- **`review_queues`** — id, kind (`grading` | `labeling`), title, params_json,
  created_at, note. **Items are re-derived from params at open time**: a grading
  queue's params are (pair, prompt_version or current, seed, n, selection, or an
  explicit id list for targeted queues), and `audit.draw` is seeded, so
  materialization is deterministic. Resumability = derive items, mark done where a
  verdict/label row already exists, jump to the first pending one. No item-state
  table to drift out of sync.
- **`verdicts` gains one additive column, `grader`** (TEXT, nullable), via the
  existing column-migration helper. Issue 13's independence question makes grader a
  first-class dimension; `verdicts.Verdict` gains the optional field and
  `store`/`for_pair`/`accuracy` pass it through.
- **`label_sessions`** — id, queue_id, taxonomy_version, pre_labeler, created_at.
- **`line_labels`** — session_id, pair, url, line_hash, line_text (verbatim, per the
  fixture rule), context_before/after, pre_label, label, labeler, labeled_at,
  notes. Flip rate = `pre_label != label`, summarised per session — the measure of
  pre-labeler bias the enrichment plan requires. Taxonomy v1 (its §3.1):
  `restriction | behavioural-change | addition | editorial | regeneration`, plus
  `skip/unsure`, which enters no training export (the `unverified` precedent).

## Backend

Minimal JSON API: list/create queues; open a queue (items + progress); fetch one
item's evidence bundle; submit; fetch full page bodies lazily; export provenance;
`GET /api/accuracy` serving `verdicts.accuracy` for the dashboard.

**Grading evidence bundle** (per finding): the finding's fields
(`findings.for_pair`, superseded rows included when a queue targets an arm); per
cited page the ranked changed lines (`audit.audit_finding`), a capped full unified
diff (`diff.render_diff`), the mechanical audit flags (newness and quote checks —
machine evidence, shown), and the full before/after body on demand from the blobs.
**Prior verdicts by other graders or methods are withheld until after submit**, then
revealed for comparison — blind mode as the default, not a habit.

**Labeling evidence bundle** (per line): the verbatim changed line, its `-`/`+`
context from `classify.changed_sides` over the pair's blobs, the page slug, and the
pre-label with its producer named. Session sources: `absence.scan` candidates, and
stratified samples of a pair's changed lines split by lexicon-hit / no-hit — the
stratification the enrichment plan's held-out evaluation needs. Pre-labeler v1 is
the `classify.RESTRICTION` lexicon; the schema is agnostic, so an LLM pre-labeler
later just fills `pre_label` + `pre_labeler`.

**Writes.** Grading submit builds a `verdicts.Verdict` (method defaults to
`full-page`; selection/stratum/weight from queue params; grader; source =
`review:queue-{id}`) and goes through `verdicts.store` — replacement per
(finding, method), exactly the existing semantics, so re-opening a done item to
correct it just works. Labeling submit is insert-or-replace on
(session, line_hash).

**Provenance export.** A completed (or partial) grading queue exports a filled
worksheet in the exact existing format to `reports/changefeed/verdicts-*.yaml`, and
the export must round-trip through `verdicts.parse` — the "worksheet is the
rebuildable provenance" promise survives the UI. Labeling sessions export a
needle-file-style YAML to `reports/labels/`.

## Frontend

One static page, three hash-routed views. **Dashboard**: the accuracy table, queue
cards with progress bars and Resume buttons, a create-queue form. **Grading**:
finding header, evidence panel with coloured diff lines (`-` red, `+` green, `~`
amber — the marking convention), verdict buttons, notes, blind-mode reveal after
submit. **Labeling**: line + context, taxonomy buttons, the pre-label with its
producer, a running flip counter. Keyboard-first throughout: `j`/`k` previous/next
pending, `1–5` verdict or label, `f` full page, `n` notes, `Enter` submit and
advance. Progress in the header; every submit is durable, so closing the tab loses
nothing.

## Tests

FastAPI TestClient against tmp databases, the `test_verdicts.py` pattern:
deterministic queue materialization and resume; grading submit lands the correct
`Verdict` row (weight, grader, method) and re-submit replaces per (finding, method);
blind mode excludes prior verdicts before submit and includes them after; labeling
flip-rate summary and the skip/unsure exclusion; worksheet export round-trips
through `verdicts.parse`; the `grader` column migration leaves existing rows and old
code paths untouched.

## Non-goals for v1, recorded so they are decisions rather than gaps

No auth (localhost only); no multi-user concurrency; no editing findings; no
running digests or arms from the UI — a natural future action kind, wanted only
after the `run --no-replace` choreography fix exists; no LLM pre-labeler (the tool
consumes `pre_label`, whoever produces it). Absence-candidate review is the
designed-for third queue kind, not built in v1.

## Verification, when built

1. `uv sync --extra review`; full test suite green; ruff clean.
2. Serve against the real `changes.db` (writes only new verdict/label rows): a
   targeted grading queue over two or three already-graded findings under a scratch
   grader name — grade blind, confirm the reveal matches the stored verdicts,
   confirm `digest.py accuracy` still reads.
3. A small labeling session from `absence.scan` on a stored pair — labels land,
   flips count, the export parses.
4. Docs: a usage section beside the ledger write-up in `docs/changefeed-phase-2.md`;
   issue 13's second-grader criterion pointed at the tool as its vehicle.

## Sequencing note

The tool's first real use is exactly the queue already waiting: Doug's human
spot-grade of the `2+r` and combined-arm rows (issue 13), then the marking-confirm
and collapse-A/B grade cycles. Building it before that arm campaign turns three
manual worksheet dances into three Resume buttons.

## Build status (2026-09-20)

Built as specified: `src/review/` (`app.py`, `queues.py`, `evidence.py`, `store.py`,
`static/`), `scripts/review.py serve`, the `review` extra, `tests/test_review.py`
(7 tests), and the additive `grader` column with `Verdict`/`store`/`for_pair`/
`accuracy`/`parse` passing it through — `accuracy` groups by grader now, NULL-grader
rows grouping together so every existing number is unchanged. Two deviations worth a
line: `verdicts.worksheet` gained optional `selection`/`grader`/`filled` parameters so
the UI's export *is* the existing format rather than an imitation of it (the export
re-parses itself through `verdicts.parse` before returning); and `scripts/review.py`
strips its own directory from `sys.path`, because the script deliberately shares the
package's name — the shadowing trap `scripts/changes.py` documents.

Verified against a scratch copy of the real `changes.db`: the dashboard reads all 15
accuracy rows; a seeded grading queue over #6 → #7 materialized in 50 ms with the
strata sealed (5/31/33 populations), marked the already-graded finding 264 done on
open — resume for free — and served evidence in ~10 s cold (the pair diff, then
cached: 25 ms warm); an absence labeling queue materialized the expected ~117
candidates. Full suite green (495), ruff clean. Not yet done, deliberately: the plan's
verification steps 2–3 (scratch-grader blind grade, a real labeling session) are
Doug's to run — a scratch re-grade of an already-graded finding *replaces* its
full-page row per the ledger's (finding, method) semantics, which is not a write to
make unasked.
