# 12 — Corpus paths keyed on a vendor-controlled date

**Status:** open (2026-09-18) · **Kind:** decision (option C is small code)
**Effort:** C ~2 h; A is the largest item in this set
**Depends on:** an inventory (below) before the big option · **Blocks:** nothing

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

## The number to get first

**The consumer inventory, before A is even sized:** everything that parses, stores, or
globs a `data/` path — index, snapshot columns, graph build, validation, coverage,
scripts. A grep-and-read, an afternoon, and it converts A from "the largest item" to a
known list of touch points. Second: how often the vendor re-dates without content —
one event observed so far; a second occurrence inside a few months is itself the
strongest argument for A. [10](10-standing-instruments.md)'s instruments will show it
when it happens.

## Acceptance criteria

- [ ] The consumer inventory recorded here
- [ ] C implemented and tested against the stored re-date pair: the 4,805 date-only
      moves classify as `metadata` when re-diffed
- [ ] A decided — adopted with a migration plan in `docs/`, or explicitly declined with
      the browse-by-month value named as the reason — after the inventory and, ideally,
      a second observed re-date event
- [ ] `docs/changefeed.md`'s `updated_date`-proxy caveat updated to point at whatever
      this issue concludes
