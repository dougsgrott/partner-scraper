# The raw archive: keeping every scraping session

> Design and costings: [`../plans/raw-archive-plan.md`](../plans/raw-archive-plan.md).

`raw/` holds **one** version of each page, and a refresh overwrites it. Without an archive,
the only record of what a vendor served is the date of the last crawl — and a page that
changed twice since then has left no trace of the middle state.

A **generation** is one scraping session's bytes, kept whole:

```
raw-archive/
  20260829T181157/
    manifest.json
    anthropic/platform.claude.com/docs/en/….md.gz
    databricks/docs.databricks.com/aws/en/….html.gz
```

## Usage

```bash
uv run python scripts/fetch.py --refresh              # archives automatically
uv run python scripts/fetch.py --archive-now          # capture raw/ without fetching
uv run python scripts/fetch.py --refresh --no-archive # opt out, deliberately
```

**Archiving is on by default.** An opt-in archive is one forgotten flag away from a lost
generation, and nothing can recover it: the next fetch has already overwritten the bytes.

## Why hard links, and why that is safe

A generation is hard-linked rather than copied. Measured on the first real capture: **6,566
files, 54.8 MiB apparent, 2.4 MB of actual disk**, in 2.3 seconds. A copy would have cost the
full 54.8 MiB every run regardless of what changed.

This works because of a property `rawstore` already guarantees. `rawstore.write` builds a temp
file and calls `os.replace` — it **never writes in place**. A later fetch therefore swaps the
directory entry and leaves the archived link pointing at the old inode:

```
raw/…/index.html.gz              inode 602482, 2 links   <- before a refresh
raw-archive/2026…/index.html.gz  inode 602482, 2 links
                                 ↓ refresh replaces the live entry
raw/…/index.html.gz              inode 998113            <- new bytes
raw-archive/2026…/index.html.gz  inode 602482            <- old bytes, intact
```

If `rawstore` ever wrote in place, every archived generation would silently change under it.
`tests/test_generations.py` asserts the surviving-overwrite property directly, so that
regression fails loudly.

**One consequence worth knowing:** copying or moving `raw-archive/` with a tool that does not
preserve hard links (`cp` without `-a`, some sync tools, most archive formats) will expand it
to full size — potentially gigabytes. Use `cp -a`, `rsync -aH`, or `tar` with `--hard-dereference`
off. `generations.verify()` checks a generation still holds the file count its manifest claims.

## What it costs

| | |
|---|---|
| one generation | 54.8 MiB apparent, ~2.4 MB real when nothing has changed yet |
| new bytes per refresh | ~54.4 MiB — 6,521 of 6,565 files change |
| weekly cadence | ~2.9 GB/year, ~339,000 files/year |

About **80% of that churn carries no information**: every Databricks page embeds three
content-hashed asset references (`.04d7f009.css`, `.d13ea689.js`, `.f2fd70e4.js`) that rotate
on every site rebuild, so all 5,778 pages look different while the prose is untouched.
Anthropic's Markdown endpoint has none — which is why the 2026-08-18 refresh reported exactly
661 byte-identical pages, the Anthropic page count at the time.

It is kept anyway. Storing only the pages whose *content* moved would be roughly five times
cheaper and is the intended next step, but that scheme can only be designed against several
real generations, and the pages it discards cannot be recovered. Keeping everything is what
makes that decision reversible.

## Backups

`raw-archive/` is gitignored for size, **not because it is disposable**. Unlike `raw/`, which
can be re-fetched at the cost of a two-hour crawl, a generation records what a vendor served
on one particular day. That day is gone. Treat it like `state/changes.db`: back it up, with a
tool that preserves hard links.

## Measured: what actually churns (2026-09-09)

Two generations, 11 days apart, compared exhaustively — not sampled.

| | of 6,566 pages in both |
|---|---|
| bytes identical | 227 (3.5%) |
| bytes differ | **6,339 (96.5%)** |
| differ **only** in build identifiers | **5,255 (80.0%)** |
| differ beyond them | 1,084 (16.5%) |

**The asset-hash hypothesis was wrong.** Normalising the three `.hash.js` / `.hash.css`
bundle names collapsed **zero** pages. The real cause is Docusaurus CSS-module class names,
which carry a per-build suffix and appear on every styled element — dozens per page:

```
anchorTargetStickyNavbar_Dt63  ->  anchorTargetStickyNavbar_e1Nq
admonition_l747   admonitionHeading_ba9f   admonitionIcon_cPPe
```

Normalising both — bundle names and CSS-module suffixes — reduces churn **5.8×**, from 6,339
pages to 1,084.

### It is safe, and that was verified exhaustively

Every one of the 5,255 collapsed pages was extracted through its real extractor on both
sides and the output compared:

| | |
|---|---|
| collapsed pages whose extracted content actually changed | **0 of 5,255** |
| survivors whose extracted content actually changed | 986 of 1,084 (91%) |

**Zero false negatives.** A page whose content moved was never collapsed. The 98 remaining
false positives are residual noise that costs a little wasted work and hides nothing.

Real content churn in the window: **986 modified + 69 new = 1,055 pages in 11 days.** Not a
quiet week either — the new pages include `models/fable-5-1/migration-guide` and
`prompting-claude-fable-5-1`.

## Open

- **Normalised content-addressing** now looks better than the option-C plan it was meant to
  inform. Storing bytes verbatim while *addressing* them by a normalised hash would cut new
  blobs per run from ~6,477 to ~1,153 — the same ~5.6× saving as option C — **without
  discarding any page**. C drops pages whose content did not change; this keeps every
  content version and drops only build-identifier noise, which is exactly the distinction
  the audit purpose cares about. It would also make `raw_sha256` a usable signal in
  `Index.needs_extract`, which today re-extracts ~6,400 pages to write ~5,300 identical files.
- **Archive only content-changed pages (option C)** — superseded by the above unless
  byte-exactness per date is ever required.
- **Replay**: re-run a fixed extractor over a historical generation. The reason for collecting
  this, and untestable until there are two generations.
- **Retention.** None yet, on purpose: the point right now is to accumulate.
