# 01 — Split `body_fingerprint` from `output_fingerprint`

**Status:** done (2026-08-29) · **Kind:** code · **Effort:** ~1 h, plus a re-extract pass
**Depends on:** nothing · **Blocks:** [03](03-rediff-and-evaluate.md)

## Problem

The first measurement run reported **594 pages as `pipeline`** — our own extractor churn —
in a run where no code changed at all. Verified false by reading the diffs: new Genie Agent
audit events, a budget-tracking behaviour change, a moved link target, a removed passkey
restriction, an entire new section. All vendor.

### Root cause

`registry.output_fingerprint` (`src/scraper/extract/registry.py:41`) hashes the extractor,
its `scraper.*` imports, **and** `store/writer.py` + `store/layout.py`:

```python
modules = {*_project_modules(inspect.getmodule(extractor)), writer, layout}   # :59
sources = [inspect.getsource(m) for m in sorted(modules, key=lambda m: m.__name__)]  # :61
```

`writer` decides the frontmatter and `layout` decides the file path. **Neither can change a
page's body.** So a frontmatter-only edit moves the fingerprint and looks identical to an
extractor change.

Commit `8b3f999` did exactly that — and worse. It changed one line of `writer.py` (the
`content_hash` strip fix) *and* widened `_project_modules` itself, which changed the
**formula**. Databricks and cookbook pages were last extracted before that commit, so their
stored fingerprints were computed under the old formula:

```
docusaurus@7      37e8f2e8ee -> 41802dcfd8    x593
nextjs_article@2  397e21c699 -> 039345f2f8    x1
```

Same extractor version on both sides. `passthrough_md` was unaffected because those pages
were re-extracted after the commit, so both snapshots agree at `967984dbbf4d`.

The general failure: **the fingerprint is a stored value, so any change to how it is
computed silently invalidates every stored comparison.** This is the fingerprint's fourth
bite, and the first in the over-reporting direction — the three previous ones all
under-reported.

## Proposed change

Add a second, narrower fingerprint used **only** for attribution.

`registry.body_fingerprint(name)` — the extractor module plus its `scraper.*` imports, and
nothing else. Reuse the existing `_project_modules` walk (`registry.py:67`) and keep the
same `sorted(..., key=__name__)` determinism; factor the shared hashing out of
`output_fingerprint` rather than duplicating it.

**Leave `output_fingerprint` exactly as it is.** It drives `Index.needs_extract`, and a
writer or layout change *must* still force re-extraction — that behaviour was correct and is
what makes a frontmatter fix propagate. The two fingerprints answer different questions:

| | covers | answers |
|---|---|---|
| `output_fingerprint` | extractor + imports + writer + layout | should this page be re-extracted? |
| `body_fingerprint` | extractor + imports | did *we* change what this page says? |

### Plumbing

| file | change |
|---|---|
| `src/scraper/extract/registry.py` | new `body_fingerprint`; extract the common hashing helper |
| `src/scraper/extract/__init__.py:157` | compute both alongside `version`; pass both through `index.upsert` (~:239) and `index.record_duplicate` (~:226) |
| `src/scraper/store/index.py` | `body_fingerprint` column; additive migration in the existing `_migrate` loop at `:102`, which already handles `body_chars` and `output_fingerprint` |
| `src/changefeed/db.py:36` | `body_fingerprint` in the `page_versions` schema and in `VERSION_COLUMNS` (`:58`) |
| `src/changefeed/snapshot.py` | capture it in `_capture`, next to `output_fingerprint` |
| `src/changefeed/classify.py:41` | `attribute` prefers `body_fingerprint`; `output_fingerprint` stops being an attribution input |

### A gap this exposes

`src/changefeed/db.py` builds its schema with `CREATE TABLE IF NOT EXISTS` (`:87`) and has
**no migration path at all**, unlike `index.py::_migrate`.

This is the first schema change to a database that is **not rebuildable** — `index.db` can
be regenerated from `data/`, but the history exists nowhere else. So `index.py`'s "drop the
table and rebuild" shortcut is unavailable. The migration must be additive
(`ALTER TABLE ... ADD COLUMN`), guarded by a `PRAGMA table_info` check, and must never drop
or rewrite a `page_versions` row.

### The attribution ladder becomes

1. Both `body_fingerprint`s present — equal means `content`, different means `pipeline`.
2. Either missing — fall back to the `name@version` string; a difference means `pipeline`.
3. Neither usable — `unknown`.

Snapshots #1 and #2 predate the column, so they will fall to step 2, match on
`docusaurus@7`, and report **`unknown`**. That is an honest downgrade from a confident wrong
answer, and it is the expected outcome of [03](03-rediff-and-evaluate.md).

## Acceptance criteria

- [ ] `test_our_own_extractor_churn_is_never_reported_as_vendor_change` still passes — a
      genuine extractor change must still be caught.
- [ ] New test: a page whose **writer or layout** hash moved while the extractor did not is
      attributed `content`, not `pipeline`. This is the regression for the bug above.
- [ ] New test: `body_fingerprint` is deterministic across processes (the current
      `output_fingerprint` is, via the `sorted()`, and the new one must not lose that).
- [ ] `changefeed.db` migrates an existing populated `changes.db` without losing a row —
      test against a database built by an older schema, not only a fresh one.
- [ ] A re-extract populates `body_fingerprint` for all 6,564 pages and rewrites **0**
      files (`written N (N byte-identical)`). This needs `--force`: `needs_extract` keys on
      `output_fingerprint`, which does not move when a column is added, so a plain
      `extract.py` skips every page and leaves the new column empty.

## Verification

```bash
uv run pytest -q
uv run ruff check .

# populates body_fingerprint; expect every file byte-identical.
# --force is required — see the acceptance criterion above.
uv run python scripts/extract.py --force

# the history database must survive the column addition
uv run python scripts/changes.py list          # still 2 snapshots, same page counts
uv run python scripts/changes.py log https://docs.databricks.com/aws/en/
```

Then confirm the new fingerprint is narrower than the old one, and that both are stable:

```bash
uv run python -c "
from scraper.extract import registry
for n in ('docusaurus','nextjs_article','passthrough_md'):
    print(n, registry.body_fingerprint(n), registry.output_fingerprint(n))"
```

## Notes

Do this **before** any refresh. Per the standing rule in the [README](README.md), an
extractor-side change bundled with a fetch attributes every co-occurring vendor change to
us — the exact failure being fixed here.

---

## Outcome (2026-08-29)

Implemented. `uv run pytest -q` -> **309 passed**, ruff clean.

**A rung was added that this issue did not anticipate.** As written, both existing
snapshots lack `body_fingerprint`, so the ladder fell straight through to the
`name@version` comparison and reported **all 1,116** modifications as `unknown` — losing
the 522 correct `content` attributions along with the 594 wrong ones.

`output_fingerprint` covers a *superset* of `body_fingerprint`, so an **unchanged**
superset proves the subset is unchanged too. A **changed** superset proves nothing, because
the difference may lie entirely in the writer or layout. It can clear a page but never
convict one, and adding that asymmetric rung recovers the correct attributions:

| | before the fix | after |
|---|---|---|
| `content` | 522 | **522** |
| `pipeline` | 594 (all false) | **0** |
| `unknown` | 0 | **594** |

**Verified against the real corpus:**

- `extract.py --force` -> `written 6563 (6563 byte-identical)`. Every file unchanged.
- `body_fingerprint` populated for 6,563 of 6,564 pages.
- `changes.db` migrated in place: column added, all 12,967 existing rows preserved,
  snapshot #3 stored **0 new bodies**.
- `diff 2 3` (same corpus, both with the new column) -> no differences.

**One page has no `body_fingerprint`:**
`https://docs.databricks.com/aws/en/oltp/instances/query/notebook`. It 404s upstream, so its
`fetch.db` state is `fetch_error` and the extract loop skips it before it becomes a
candidate — even under `--force`. Its index row has been stale since 2026-08-24. This is a
second symptom of the gap in [04](04-quiet-week-measurement.md): a page that disappears
upstream not only fails to report as `removed`, it silently stops receiving pipeline
metadata as well.

Docs updated: `docs/changefeed.md` (a "Why there are two fingerprints" section) and
`docs/lessons-learned.md` §17b, rewritten as "One hash cannot answer two questions".
