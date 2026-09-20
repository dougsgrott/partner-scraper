# Layout migration: removing the date from corpus paths

> Adopted 2026-09-19 (issue/accuracy/12, option A). Owner's decision, recorded verbatim:
> early stage, migrations are not a concern; browse-by-month is not necessary; temporal
> browsing via the frontmatter dates suffices. Executed the same day — the *Executed*
> section at the bottom records what actually happened.

## What changes

    data/{company}/{category}/{YYYY-MM|undated}/{slug}.md    (before)
    data/{company}/{category}/{slug}.md                      (after)

A file's identity no longer includes `updated_date` — the field the 2026-09-11 event
proved a vendor can rewrite site-wide with no content change, relocating 71% of the
corpus. After this, `moved` means a page's *place* changed (category or slug), and a
re-date changes exactly one frontmatter line. Temporal queries use the frontmatter
(`updated_date:` / `published_date:`), which `writer.parse` round-trips and `index.db`
carries as columns.

## Why it is safe (the issue-12 inventory, condensed)

- The path shape lives in **one function**, `store/layout.py path_for`; everything
  else either walks the tree (`rglob("*.md")` — validation, corpusgraph, sample
  review, index rebuild) or holds paths in a rebuildable store.
- **Collision check, run before adopting:** flattening the current 6,774 indexed
  paths produces exactly 2 collisions, both the known trailing-slash duplicate-URL
  pairs that already share one file today (`status=duplicate` in the index). The
  flattened namespace is otherwise collision-free, because slugs are URL-derived.
- `data/` and `state/` are **gitignored** — the move is invisible to version control.

## The migration, step by step

1. **Code:** drop the date segment in `layout.path_for` (keep `date_bucket` — the
   frontmatter/index still want the value); classify a same-body move whose paths
   differ *only by the presence of a date segment* as `moved` with cause
   `pipeline` — the flattening is our churn, not the vendor's, so it must be
   excluded from the feed and the digest prompt like all pipeline churn
   (`CLASSIFY_VERSION` 3 covers both of today's classifier rules).
2. **Move the files through the pipeline, not by hand:**
   `uv run python scripts/extract.py --force --prune` — the writer lands every page
   at its new path, `_drop_stale_copy` removes each old dated copy,
   `writer.remove` prunes the emptied month directories, and `index.db` is updated
   row by row in the same pass. No `mv`, no separate index rebuild.
3. **Rebuild the graph** (derived store): `uv run python scripts/graph.py build`.
4. **Validate:** `uv run python scripts/validate.py` (integrity: `data/` and
   `index.db` agree; no orphans).
5. **Snapshot and verify the diff:** the #7 → #8 diff must read ~0 `modified`
   (bodies untouched), everything relocated as `moved`/`pipeline`, 0
   `content`-attributed moves. This is the migration's acceptance test.

## Standing consequences

- `state/changes.db` history keeps the old dated paths in `page_versions.file_path`
  for snapshots ≤ #7 — historical records are records; nothing rewrites them. The
  pipeline-cause rule above is permanent, so re-diffing any old pair against a new
  one classifies the flattening correctly.
- The raw archive, fetch state and blobs are untouched — this is a corpus-layout
  change only.
- If a future change reintroduces a path segment, the same playbook applies: layout
  edit, forced extract, graph rebuild, and a classifier rule making our churn
  attributable to us.

## Executed (2026-09-19/20)

- `extract --force --prune`: **6,771 written · 6,771 moved (stale copies removed) ·
  0 errors · 0 quality failures**, 608 s, 2 duplicate URLs merged, 87.4 M chars.
- One straggler, handled by hand: a `gone` page (404 upstream, file kept as the
  last-known copy) is skipped by re-extraction, so its file and index row still
  carried the dated path. Moved and re-pointed manually; 0 dated paths remain in
  `data/` or `index.db`.
- Graph rebuilt in 15.2 s. `validate.py`: 22 ok · 5 warn (pre-existing) · 0 failed;
  corpus_completeness: all 6,773 extractable pages accounted for.
- Snapshot **#8 `layout-flattened`** taken: 6,771 pages, **0 new bodies** — the
  migration changed no content, byte-for-byte.
- Verification diff #7 → #8: `moved 6771`, **feed: 0 substantive vendor changes,
  “our own churn 6771 (extractor changed, not the vendor)”** — the
  `moved`/`pipeline` rule classified the entire migration as ours, and the digest
  prompt would carry none of it.
- Surprises: only the `gone`-page straggler above, and the forced pass taking ~10
  minutes rather than the module docstring's "seconds" (quality checks over 87 M
  chars).
