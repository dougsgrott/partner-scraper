# Persist every scraping session's raw bytes

> Written 2026-09-09. Figures are measured from the archive as it stood that day, not
> estimated. Re-measure before quoting them elsewhere.

## Context

Each scraping session should keep its inputs, for auditing what the vendors published and for
regression-testing extractors against real pages rather than synthetic strings.

Three options were costed. **Option A — keep every generation whole — is chosen**, over the
cheaper option C (archive only pages whose content changed), for a reason that outweighs the
storage difference:

> Scraping happens every few days to weekly, so generations accumulate slowly. Designing the
> cheaper scheme now would tune it against a single observed refresh, and build regression
> machinery with no regression data to test it on.

**A is a superset of C.** With whole generations kept, what C would have retained can be
computed and pruned at any time. The reverse is impossible — pages C discards are gone. The
storage difference buys optionality, and the transition to C stays open.

## What it costs

| | |
|---|---|
| one generation | **54.8 MiB**, 6,566 files |
| new bytes per refresh | ~54.4 MiB — 6,521 of 6,565 files change |
| weekly cadence | **~2.9 GB/year**, ~339,000 files/year |

Real headroom is **~55 GB**, not the 877 GB `df` reports inside WSL2: that is the nominal size
of a sparse virtual disk backed by the Windows host, which shows 475 GB total / 421 GB used at
`/usr/lib/wsl/drivers`. So roughly **5% of remaining space per year**, on a host already 89%
full. Worth watching; not a reason to compress the design now.

About **80% of that churn carries no information.** Every Databricks page embeds three
content-hashed asset references — `.04d7f009.css`, `.d13ea689.js`, `.f2fd70e4.js` — which
rotate on every site rebuild, so all 5,778 pages look different while the prose is untouched.
Anthropic's Markdown endpoint has none, which is why the 2026-08-18 refresh reported exactly
661 byte-identical pages: the Anthropic page count at the time. Against 1,277 real content
changes in the same window, ~5,244 pages changed bytes and said nothing new.

Keeping it anyway is the price of not guessing which 20% mattered.

## Design: hard-linked generations, pipeline untouched

`raw/` stays exactly as it is — the working copy the fetcher writes and the extractor reads.
Nothing in `rawstore.py`, `fetch/db.py`, `runner.py` or `extract/` changes. Those hold the two
most expensive pieces of state to rebuild, and the fetch path is the one stage that costs two
hours of someone else's bandwidth to redo. They stay out of it.

A generation is a **hard-linked snapshot** of `raw/`:

```
raw-archive/
  2026-08-29T181157/
    manifest.json
    anthropic/platform.claude.com/docs/en/….md.gz      <- same inode as raw/…
    databricks/docs.databricks.com/aws/en/….html.gz
```

Hard links are safe because of a property `rawstore` already guarantees: `write` builds a temp
file and calls `os.replace`. It **never writes in place**, so a later fetch swaps the directory
entry and leaves the archived link pointing at the old inode. Archiving therefore costs inodes,
not data blocks, and a generation occupies real space only for the files that later diverge.

That is also why this cannot be a plain `cp`: copying would duplicate 54.8 MiB every run
regardless of what changed.

`manifest.json` records what the generation contains, in the shape `state/runs/*.json` already
uses: taken-at, file count, byte total, and the fetch run it corresponds to.

## Files

| file | change |
|---|---|
| `src/scraper/fetch/generations.py` | **new** — `archive()`, `generations()`, `verify()` |
| `scripts/fetch.py` | `--archive` (default **on**) after a successful run; `--no-archive` to skip; `--archive-now` for a standalone capture |
| `.gitignore` | `raw-archive/` beside `raw/` |
| `tests/test_generations.py` | **new** |
| `docs/raw-archive.md` | what a generation is, why hard links are safe, and the open transition to option C |

Archiving is **on by default**: an opt-in archive is one forgotten flag away from a lost
generation, and a generation cannot be recovered after the next fetch overwrites it.

## The one-time capture, first

The generation now in `raw/` — fetched 2026-08-29 — has never been archived, and `rawstore`
overwrites in place. **The next refresh destroys it.**

```bash
uv run python scripts/fetch.py --archive-now --label 2026-08-29T181157
```

That capture is also what makes the asset-hash hypothesis testable. With two generations, a
diff shows whether those three tokens are the *only* volatile bytes. If they are, normalising
them before hashing would collapse churn from 6,521 to ~1,300 per run, make `raw_sha256` usable
in `Index.needs_extract` — which today re-extracts ~6,500 pages to write ~4,800 byte-identical
files — and bring option A's cost down to option C's while giving nothing up.

## Tests

- an archived generation survives a later overwrite of `raw/`: the archived file still holds
  the **old** bytes after `rawstore.write` replaces the live one. The property the scheme rests on
- archiving costs no data blocks — disk usage is unchanged after archiving an untouched `raw/`
- `raw/` is not mutated: same file count, same hashes, before and after
- archiving twice under one label is refused rather than silently merging
- the manifest's counts match what the generation actually holds

## Verification

```bash
uv run pytest -q
uv run ruff check .

uv run python scripts/fetch.py --archive-now --label 2026-08-29T181157
ls raw-archive/
du -sh raw raw-archive        # the archive adds ~0 real bytes
cat raw-archive/*/manifest.json
```

Then the weekly ingest, which produces the second generation and makes the churn measurement
possible.

## Outcome (2026-09-09)

Built, and the 2026-08-29 generation captured before the refresh that would have destroyed it
(6,566 files, 54.8 MiB apparent, **2.4 MB of real disk**, 2.3 s — hard links verified by inode
identity). A second generation followed the refresh, and the measurement the archive existed
to make possible now exists — see `docs/raw-archive.md` § Measured.

Two things it changed:

- **The asset-hash hypothesis in this plan was wrong.** Normalising the three bundle names
  collapses zero pages. The churn is Docusaurus CSS-module class suffixes, dozens per page.
  Normalising both gives a 5.8x reduction with **zero false negatives across all 5,255
  collapsed pages**, verified by extracting both sides.
- **Option C is superseded.** Normalised content-addressing achieves the same ~5.6x saving
  without discarding any page, which fits the stated audit purpose better than C did.

Keeping whole generations was the right call for a reason beyond the one given: the analysis
that produced these numbers is only possible because both generations were kept intact. C
would have thrown away the 5,255 pages that turned out to be the evidence.

## Deferred, deliberately

- **Option C** — archive only content-changed pages. Revisit once several generations exist and
  the churn shape is known rather than inferred from one refresh.
- **Replay** (`extract --from-generation <gen>`), the payoff for regression testing. It cannot
  be tested with one generation; build it when there are two.
- **Retention and `gc`.** The point right now is to accumulate. Add pruning when there is
  something worth pruning, and let the measurement say what.
