# 12 — Corpus paths keyed on a vendor-controlled date

**Status:** done (2026-09-19), uncommitted — **C shipped, then A adopted by the owner
and executed the same day**: C is verified against the stored re-date (4,805 `moved` →
0, all `metadata`, CLASSIFY_VERSION 3); A flattened the corpus to
`data/<company>/<category>/<slug>.md` via `extract --force --prune` (6,771 moved, 0
content changes, snapshot #8, diff #7→#8 fully `pipeline`-attributed — see
`docs/layout-migration-plan.md`). See *Done*, *Inventory*, *The A decision* ·
**Kind:** decision (option C is small code)
**Effort:** C ~2 h; A re-sized below · **Depends on:** the inventory (done) ·
**Blocks:** nothing

## Problem

Corpus files live at `data/<company>/<category>/<YYYY-MM|undated>/`, keyed on the
vendor's `updated_date`. The session record marks the consequence *(challenge)*: the
Databricks site-wide re-date moved `updated_date` to 2026-09-11 across 4,805
byte-identical-body pages, so **71% of the corpus relocated** (extract: "moved 5273"),
the feed carried ~5,000 `moved`/`metadata` records into the digest prompt, and
`docs/changefeed.md`'s validated use of `updated_date` as a change-volume proxy broke.

The underlying defect: **a file's identity includes a field the vendor can rewrite
site-wide at will, with no content change.** Any downstream consumer holding a
`file_path` — the index, snapshots' `file_path` columns, the graph, inbound-link
counts, anything globbing `data/` — churns with it.

Separable harms, because the options address different ones:

1. feed/digest noise (5,034 records; the token cost is [06](06-prompt-size.md)'s);
2. on-disk churn and `file_path` invalidation across state databases;
3. the loss of the `updated_date` proxy for Databricks volume (not repairable by
   layout — the proxy is simply now known to be vendor-fragile, which is itself a
   finding to keep).

## Options

**A — remove the date from the path.** `data/<company>/<category>/<slug>`; the date
lives in frontmatter and `index.db` only. Identity becomes stable; a `moved` record
becomes a real vendor path move again.

- *Pro:* kills harms 1 and 2 at the root; `moved` regains meaning.
- *Con:* the largest migration in this set — extractor path logic, every stored
  `file_path` (index, snapshots), graph edges, validation, plus one final mass-move
  event as the tree flattens. Loses the browse-by-month property of the tree, which may
  or may not be load-bearing for the owner's workflow — worth asking, not assuming.

**B — key on first-seen date** (immutable per page) instead of `updated_date`.

- *Pro:* keeps a dated tree, stable thereafter.
- *Con:* first-seen does not exist — `fetched_at` is overwritten per fetch, and the
  readiness set (issue 04, part 3) already judged that column not worth a schema change
  to the two-hour-rebuild database. The semantics are also odd: a page's month becomes
  "when we noticed it". Weakest option; listed because it keeps the tree dated.

**C — keep the layout; reclassify date-only moves.** In the diff layer: a `moved` whose
only path difference is the date segment, with identical body, classifies as
`metadata`. Combined with [06](06-prompt-size.md)'s terse collapse, a future re-date
costs one grouped line instead of 5,000.

- *Pro:* small, immediate, addresses the measured harm (feed/digest noise) without
  touching layout; correct regardless — a date-segment move *is* metadata under this
  layout's semantics.
- *Con:* disk churn and `file_path` invalidation remain; extract still physically moves
  thousands of files on the next event.

**D — C now, A later.** C's classifier stays correct during and after any migration.

## Done (2026-09-19): option C

`diff._date_only_move`: two corpus paths that agree everywhere except the layout's
date segment (`YYYY-MM` or `undated` on both sides, same file name, same tree above).
A same-body change matching it falls through to the metadata classification — its
cause is the `updated_date` edit itself, so it is filed with the field change that
produced it, keeping the title-weight rule (`SUBSTANTIVE` on retitle) intact. `moved`
is now reserved for a page whose place in the tree genuinely changed (category or
slug), which the pre-existing filing-change test still asserts.

**Verified against both stored pairs, re-diffed in memory** (the committed reports
were left untouched — they are v2-classifier artifacts):

| pair | before | after |
|---|---|---|
| #6 → #7 (the re-date) | 4,805 moved · 229 metadata | **0 moved · 5,034 metadata**, all weight `low` |
| #5 → #6 | 12 moved · 5 metadata | 0 moved · 17 metadata — the 12 were ordinary single-page re-dates, correctly absorbed |

`CLASSIFY_VERSION` bumped 2 → 3 (kind labels in the prompt and the summary table
change on re-date windows, so historic reports will not re-render byte-identically on
such pairs; the version comment records this). `TERSE_KINDS` already treats `moved`
and `metadata` alike, so [06](06-prompt-size.md)'s collapse arm is unaffected. Tests:
the real re-date paths verbatim (positive, `undated`, category-change, rename, and a
non-date segment as negatives) plus a corpus-level test that a vendor re-date is
`metadata`, not `moved`.

`docs/changefeed.md`'s proxy caveat now points here, with the standing advice: treat
`updated_date` volume as vendor-fragile; use content-attributed counts.

## Inventory (2026-09-19): every consumer of a `data/` path

Grep-and-read of `file_path` / `data/` across `src` and `scripts`. The decisive
finding: **most consumers walk the tree (`rglob("*.md")`) and never parse the path**,
so option A leaves them untouched.

- **Path shape is defined in exactly one place:** `store/layout.py`
  (`data/{company}/{category}/{YYYY-MM}/{slug}.md`). `store/writer.py` writes what
  layout says. A is an edit to one function plus migration.
- **Layout-agnostic (unaffected by A):** `validate/fidelity`, `validate/invariants`,
  `corpusgraph/edges` + `taxonomy` (walk `data/`), `store/index.rebuild`/`orphans`,
  `scripts/sample_review`, `scripts/validate_retrieval`.
- **Literal-path holders:**
  - `state/index.db` `pages.file_path` — **rebuildable from `data/` by design**; one
    rebuild after the move.
  - `state/graph.db` — derived; `graph build` rebuilds it in ~15 s.
  - `state/changes.db` `page_versions.file_path` — **not rebuildable**; historic rows
    keep old paths forever. The first post-migration diff would show every page as a
    real `moved` (a *removed* segment changes path length, so `_date_only_move`
    correctly does not absorb it) — migration day needs a companion: either a one-off
    classifier allowance for "date segment removed", or accepting one loud, final,
    honestly-labelled mass-move report.
  - `scraper/extract` stale-copy pruning reads the index's previous `file_path` —
    already move-aware (it exists to clean up relocations).
  - `changefeed/report.py` prints moved paths (display only);
    `digest/tools.get_source` reads current records only.

**Re-sized: A is an afternoon** — one layout function, an `extract --force`-style
rewrite pass (or a scripted `mv`), an index rebuild, a graph rebuild, and the
migration-day diff decision. Not "the largest item in this set" once the inventory
exists; the README's dependency note said exactly this would happen.

## The A decision — decided by the owner, 2026-09-19

- [x] **Adopted.** Doug: early stage, migrations are not a concern on the assumption
      they bear fruit soon; browse-by-month is not necessary — some temporal browsing
      is useful, and the frontmatter dates provide it. (They do: `updated_date`/
      `published_date` round-trip through the frontmatter and sit as `index.db`
      columns; only the *path* stopped carrying them.)

Executed immediately — plan and full run record in `docs/layout-migration-plan.md`:
`layout.path_for` dropped the segment (`date_bucket` deleted with it, no callers
left); the migration ran through the pipeline (`extract --force --prune`: 6,771
written, 6,771 stale dated copies removed, 0 errors; one `gone`-page straggler moved
by hand); graph rebuilt; validation 0 failed; snapshot #8 `layout-flattened`; the
#7 → #8 diff reads **6,771 moved, all "our own churn", feed empty** — the companion
classifier rule (`_date_segment_dropped` → `moved`/`pipeline`, inside
CLASSIFY_VERSION 3) attributed the whole event to us and kept it out of the digest.
The recommendation to wait for a second re-date was overruled by the owner's
early-stage argument, which is the stronger one at this maturity.

## Acceptance criteria

- [x] The consumer inventory recorded here
- [x] C implemented and tested against the stored re-date pair: the 4,805 date-only
      moves classify as `metadata` when re-diffed
- [x] A decided — **adopted** with the migration plan in
      `docs/layout-migration-plan.md`, and executed: the tree is flat, identity is
      date-free, and the migration diff is `pipeline`-attributed
- [x] `docs/changefeed.md`'s `updated_date`-proxy caveat updated to point at whatever
      this issue concludes
