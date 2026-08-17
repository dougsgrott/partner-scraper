# Coverage & category breakdown

A read-only tool to (a) **monitor how much of the corpus is scraped** and (b) **see the
sitemap's categories with counts** so you can choose `batch.priorities`. It spends **no
tokens** — it only reads sitemaps (discovery) and the local index.

## Why both jobs are one tool

Both answers come from the same data: per-company, per-**category** page counts
cross-referenced against the index (what's already `ok` / `errored` / still pending). So a
single command shows progress *and* the pickable categories.

## Category vs. theme (important)

- **category** — derived from the URL *path* (the sitemap section), e.g.
  `agents-and-tools` → prefix `/docs/en/agents-and-tools/`. This is what
  `batch.priorities` matches on (path-prefixes), so the tool groups by category and prints
  each category's prefix ready to paste into config.
- **theme** — Claude's *content* classification (`prompt-caching`, `agents`, …), used only
  to lay out the `data/` folder. Not used here.

You pick priorities by category, not theme.

## Design: reusable compute + thin CLI

- `src/scraper/coverage.py` — pure computation returning structured data
  (`CategoryStat`, `CompanyCoverage`, `compute(...)`). No printing. A future
  visual/interactive dashboard consumes this directly (or the `--json` output) unchanged.
- `scripts/coverage.py` — a thin formatter/CLI over `compute(...)`.

Reuses existing primitives: `discovery.sitemap.collect` + `discovery.filters.apply` (the
in-scope candidate set = coverage denominator), `store.index.Index.query()` (all rows),
and `config.SourceConfig.include_paths` (to strip the prefix when deriving a category).

## CLI

```
uv run python scripts/coverage.py [flags]
```

| Flag | Meaning |
|---|---|
| `--config PATH` | config file (default `config/sources.yaml`) |
| `--company X` | focus one company |
| `--overview` | per-company totals + % only (the "how much scraped" monitor) |
| `--by-category` | per-category table (default view) |
| `--sort {pending,total,scraped}` | category sort key (default `pending`) |
| `--raw` | ignore include/exclude filters → show the *full* sitemap's categories (for deciding what to add to `include_paths`) |
| `--depth N` | category granularity (default 1; `2` splits into subsections) |
| `--json` | emit structured data for machines / the future UI |

`total = scraped + errored + pending`. `pending` = an in-scope page with no index row yet.

## Examples

Monitor overall progress:
```
uv run python scripts/coverage.py --overview
```

Pick priorities — biggest, least-done sections first, with copy-paste prefixes:
```
uv run python scripts/coverage.py --company databricks --sort pending
```
Copy a row's `prefix` (e.g. `/aws/en/mlflow3/`) into `config/sources.yaml`:
```yaml
batch:
  priorities:
    - /aws/en/mlflow3/
```

Discover sections currently outside scope (to widen `include_paths`):
```
uv run python scripts/coverage.py --company databricks --raw
```

Machine-readable (future dashboard):
```
uv run python scripts/coverage.py --json
```

## Sample output

```
anthropic   scraped 4/661 (0.6%)   errored 0   pending 657
  category              total  scraped  errored  pending   prefix
  api                     368        0        0      368   /docs/en/api/
  cookbook                 95        0        0       95   /cookbook/
  agents-and-tools         41        4        0       37   /docs/en/agents-and-tools/
  ...
```

## Notes

- Runs discovery each invocation (fetches sitemaps over HTTP) — a few seconds, no tokens.
- The index is authoritative for "scraped"; deleting `state/index.db` and rebuilding from
  `data/` (`Index.rebuild`) keeps coverage accurate.
- Out of scope here: the later visual/interactive dashboard — it will reuse
  `coverage.compute(...)` / `--json`.
