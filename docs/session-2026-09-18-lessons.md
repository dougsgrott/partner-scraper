# Session record: raw archive, digest accuracy, and the #6 → #7 run

> Written 2026-09-18 for a reviewer who has not seen this session. It covers the whole
> session (2026-09-09 to 2026-09-18): what was built, what was measured, what went wrong, and
> what is still open. It records facts and the author's reading of them, labelled separately.
> **Your task is to find room for improvement.** Nothing here is settled because it is written
> down, and the conclusions most worth challenging are marked *(challenge)*.

## 0. The project in one page

A local corpus of partner documentation, scraped from two vendors, plus applications built
on it. Monorepo, Python, `uv`.

| source | host | pages (2026-09-18) | format fetched |
|---|---|---|---|
| Anthropic docs + cookbook | platform.claude.com | ~830 | Markdown endpoint (767) / HTML |
| Databricks docs | docs.databricks.com | ~5,940 | HTML (Docusaurus) |

Pipeline and state:

```
fetch  (scripts/fetch.py, ~2 h, 1 req/s per host)  -> raw/            verbatim bytes, gzipped, overwritten in place
                                                    -> raw-archive/    one hard-linked generation per fetch (new, this session)
extract (scripts/extract.py)                        -> data/           Markdown corpus, frontmatter, path data/<company>/<category>/<YYYY-MM|undated>/
                                                    -> state/index.db  one row per page
change feed (scripts/changes.py run)                -> state/changes.db snapshots + history (NOT rebuildable)
                                                    -> state/changes/blobs/ content-addressed extracted bodies
                                                    -> reports/changefeed/NNNN..MMMM.{md,json}
digest (scripts/digest.py run / audit)              -> findings in changes.db, reports/changefeed/digest-NNNN..MMMM.md
```

- **Change feed phase 1** (deterministic): snapshot → diff → attribution (was a change caused
  by the vendor, or by our extractor? via `body_fingerprint` / `output_fingerprint`) →
  severity ranking → report. `src/changefeed/`.
- **Change feed phase 2** (Claude Agent SDK): compress the whole run to about one line per
  change (`digest/compress.py`), one agent session reads it all and records findings through
  tools (`get_diff`, `read_page`, `inbound_links`, `record_finding(s)`), URL membership is
  validated, findings are superseded rather than deleted, and each finding carries `model` +
  `prompt_version`. `src/changefeed/digest/`. The architecture decision is in
  `docs/changefeed-phase-2.md` and `issue/changefeed-phase-2-readiness/05-*.md`.
- House rules: the owner manages all git state (see `CLAUDE.md`). Design choices that depend
  on a number should wait until the number is measured. Plans are written into `docs/`.

## 1. Snapshot and run history

| snapshot | taken | pages | label | note |
|---|---|---|---|---|
| #1–#4 | 2026-08-29 | ~6,560 | baseline … after-gone-detection | first refresh + fixes |
| #5 | 2026-09-09 15:07 | 6,563 | 2026-09-09-before | |
| #6 | **2026-09-18 15:34** | 6,632 | 2026-09-09 | content = the 2026-09-09 fetch; snapshot taken 9 days later |
| #7 | 2026-09-18 19:44 | 6,771 | 2026-09-18 | |

Raw generations: `20260829T181157` (6,566 files), `20260909T172623` (6,635),
`20260918T184955` (6,774).

**Snapshot timestamps are not content timestamps.** A window's length has to come from the
fetch generations, not from `changes.py list`.

## 2. Raw archive (built this session)

### Decision path
1. The question was whether to keep the raw bytes from every fetch, for auditing vendor content
   and for regression testing extractors. The owner **rejected analysis that bundled two
   questions**, and required the cost to be known *before* fetching.
2. The owner corrected a storage assumption: `df` inside WSL2 showed 877 GB, but that is the
   nominal size of a sparse virtual disk. The real headroom was the Windows host's free space,
   ~55 GB on 2026-09-09 and **43 GB on 2026-09-18**. Storage may move to the cloud later.
3. Options costed: **A** keep every generation whole, **C** keep only pages whose content
   changed. **A was chosen.** Reason, in the owner's words: generations accumulate slowly, and
   designing the cheap scheme against one observed refresh risks "building things that cannot
   be tested on regression data". A is a superset of C, so C stays possible later; the reverse
   is impossible.
4. The plan is in `plans/raw-archive-plan.md`. The design and measurements are in
   `docs/raw-archive.md`.

### Design
- `src/scraper/fetch/generations.py`: `archive()` hard-links every `raw/**/*.gz` into
  `raw-archive/<label>/` and writes `manifest.json`. It falls back to copying, refuses a
  label that already exists, and provides `generations()` and `verify()`.
- **Hard links are safe only because** `rawstore.write` writes a temp file and calls
  `os.replace`. It never writes in place, so a later fetch swaps the directory entry and the
  archived link keeps the old inode. The test that matters is
  `tests/test_generations.py::…survives overwrite`.
- `scripts/fetch.py` archives by default after every successful non-dry run
  (`--no-archive`, `--archive-now`, `--label`).
- **Trap:** `scripts/changes.py run --fetch` refreshes through `run_fetch` directly and
  **does not archive**. The documented workflow therefore runs `fetch.py --refresh`, then
  `changes.py run` without `--fetch`. *(challenge: two code paths do the same job, one of them
  without archiving)*

### Measurements
| | gen1 → gen2 (11 days) | gen2 → gen3 (9 days) |
|---|---|---|
| files whose bytes changed | 6,339 of 6,566 | Databricks 5,834 of 5,835; Anthropic 553 of 800 |
| collapsed by normalising asset hashes | **0** (hypothesis falsified) | — |
| + Docusaurus CSS-module suffixes (`_Dt63`) | 5,255 (80%) | **188** |
| + `<time … itemprop=dateModified>` | — | **+4,966** |
| survivors | 1,084 | 680 (Databricks) |
| real content changes among survivors | 986 (91%) | 609 (89.6%) |
| **missed real changes (false negatives)** | **0 of 5,255 collapsed**, found by extracting both sides | **0**, all 609 change-feed modifications are among the survivors |

Disk: ~57 MiB apparent, **~72 MB real per generation** (block rounding on ~6,800 small
files). Weekly, that is ~3.7 GB/year.

### Lessons
- **The first hypothesis about the noise (asset hashes) was wrong.** Measuring it (0
  collapsed) found the real cause (CSS-module suffixes).
- **A noise-pattern list only learns a pattern is missing when a vendor event exposes it.**
  The gen2 → gen3 re-date made 4,966 pages look changed. No mechanism detects a new noise
  pattern before it swamps a run. *(challenge)*
- The open idea in `docs/raw-archive.md`: store raw bytes verbatim but *address* them by a
  normalised hash. That gets C's saving without discarding any page, and makes `raw_sha256`
  usable for skipping re-extraction. It isn't built.

## 3. Change volume, and what "quiet week" turned out to mean

Issue 04 asked for Anthropic's weekly change rate in a week without a launch, and expected it
to come out much lower than the launch week.

| Anthropic | #1 → #2 (launch) | #5 → #6 (Fable 5.1 launch) | #6 → #7 (no model launch) |
|---|---|---|---|
| changes | 650 / 11 days | — | 610 / 9.06 days |
| per week | ~414 | — | **~471** |
| API-reference share of modified | — | — | 447 / 547 (82%) |
| hand-written pages | — | — | ~79/week |

- **Change volume comes from continuous regeneration of the API reference, not from
  launches.** The expected gap did not appear.
- #6 → #7 still wasn't perfectly quiet: 61 of 63 added pages are the Admin API republished
  under `api/beta/organization/*`. As a result, 132 of the 175 duplicate-body groups are
  `admin/X` = `beta/organization/X`.
- Databricks: 609 modified + 76 added in #6 → #7 (~529/week, against 399/week earlier).

**Databricks re-date event (#6 → #7).** 4,805 pages "moved" and 229 changed only
`metadata`, all with byte-identical bodies. `updated_date` jumped to 2026-09-11 site-wide.
Consequences:
- `data/databricks/<category>/<YYYY-MM>/` is keyed on that date, so 71% of the corpus
  relocated (extract: "moved 5273"). *(challenge: a file path keyed on a date the vendor
  controls)*
- `docs/changefeed.md` had validated `updated_date` as a proxy for Databricks change volume.
  This event broke it.
- The digest prompt carried all 5,034 of these as one-liners (see §4).

Cross-validation that held for #5 → #6: change feed 986 modified = raw analysis 986 real
changes = extract written 6,406 − identical 5,323 ≈ 1,084 survivors. Attribution for #5 → #6
and #6 → #7: 0 `pipeline`, 0 `unknown`.

## 4. Digest (phase 2): accuracy

### Runs
| pair | prompt | findings | pages cited | cost | prompt size |
|---|---|---|---|---|---|
| #5 → #6 | v1 | 48 | not recorded | not recorded | ~88k tokens |
| #5 → #6 | v2 | 63 | 584 | $2.81 | ~88k tokens |
| #6 → #7 | v2 | 79 | 437 | $4.68 | **~198k tokens, ~97k of them one-liners for pages that only re-dated** |

`compress.py` keeps a "nothing is dropped" promise. Moved and metadata-only changes get a
~60-character line each, which is cheap until a vendor event produces 5,000 of them. They are
not collapsed. *(challenge)*

### Checking claims against full pages
An earlier audit (2026-08-30) scored 9 true / 1 partly / 0 false by reading **4-line
excerpts**. For #5 → #6 v1, checking against **full pages** found:

- Grok 4.6 and GLM 5.3 called "added", though both were already in #5
- Fable 5.1 retention misstated. The page says "Customers who opt out of data retention
  cannot use Claude Fable 5.1"
- **missed:** the same sentence is new for the *existing* Claude Fable 5. Opted-out customers
  lose a model they had. This was arguably the most consequential change in the pair
- consequences the docs never state: a Priority Tier "fallback", compaction "400s", Genie Code
  "breaking every deep link" (the old page still exists and the links were repointed)
- a grab-bag finding (3 unrelated stories); `breaking` on 12 of 48, several wrong

**Lesson: the excerpt audit judges whether a claim matches the lines shown, not whether it is
true.** Findings citing 13 pages show 3, and newness can't be judged without the old text.

### Changes made
1. **Prompt v2** (`src/changefeed/digest/session.py`, `PROMPT_VERSION = "2"`). The rules:
   one story per finding; say only what the page says; check with `get_diff`; "new" means
   absent from the old text (tables are rewritten whole); `breaking` = something that worked
   stops working or needs action, including a new restriction on something existing, and GA
   is never breaking; look for restrictions hidden inside additions and record them
   separately; cite only listed paths; unattributed changes are treated with caution; bulk
   regeneration is reported once.
2. **Audit tool** (`src/changefeed/digest/audit.py`, used by `scripts/digest.py audit`).
   - Evidence is ranked per claim.
   - Coverage flag: `! only 23% of the evidence is shown`.
   - Mechanical newness check. When the headline claims something is new, each versioned name
     in the **headline** is looked up in the BEFORE text of the cited pages, and must also
     appear in the AFTER text. Separators are normalised, so `Grok 4.6` = `grok-4-6` =
     `GLM-5.3`.
3. The newness check **took three iterations, each fixed after running it on real findings**:
   - v1 matched only id forms. **It missed the Grok 4.6 case it was written for.** Its
     synthetic test used an id and passed.
   - It also checked the detail text, and flagged background context (`us-east-1`,
     `system.ai`) as noise.
   - The v2 prompt's phrasing then got past it again: the bare verb "add", and `GLM-5.3`.
   - Each fix has a test built from the exact text that got past it. *(Lesson: a synthetic
     test written by the author of the check shares the author's blind spot.)*

### v1 vs v2 on #5 → #6
| v1 error | v2 |
|---|---|
| Grok/GLM "added" | still wrong. The audit now flags it |
| Fable 5.1 retention | fixed in one finding, still wrong in another's detail |
| new restriction on existing Fable 5 | **still missed**, even with a rule written for exactly this |
| unstated consequences | gone |
| Genie Code links | fixed |
| grab-bag | gone |
| `breaking` overuse | 12 → 4, one still wrong |
| new v2 errors | `code_execution_20260120` called new (it was in #5, and the audit caught it); an existing constraint presented as new; an old model list misstated |

**Verdict: accuracy improved but did not recover.** Prompt rules fixed tone and labelling,
but not the two errors that matter: false newness and missed restrictions. The first is now
caught mechanically. The second isn't, because **no audit can flag a finding that was never
written.**

### #6 → #7 (v2), 10-finding sample
7 true, 3 partly true, 0 false. Four were checked against full text. The partial findings:
- "a new DENY policy type" (the DENY page already existed). The newness check didn't fire
  because the term has no version number.
- "previously framed as a support note" (the old text had no such note).
- A DBR 18 requirement presented as new (only DENY was added to the sentence).

**Pattern across runs:** the model's most common error is **invented contrast with the past**.
It asserts what the old text said or lacked, without checking.

### Known gaps
- Newness is only checked for versioned names. Plain nouns ("DENY policy") are not checked.
- Known false positive: "rather than us-east-1 only" flags `us-east-1`.
- Absence (missed findings) has no detector. The idea recorded in `docs/changefeed-phase-2.md`:
  a deterministic pass for **added sentences with restriction language** (`cannot`,
  `not available`, `must`, `requires`, `rejected`) that name something already present
  before. It would have found the Fable 5 sentence. Not built or measured.
- The audit draws a seeded random sample and is read by a human. There is no running
  accuracy metric across runs.

## 5. Severity ranking
- Score = sum over signals (status 4, code 3, headings 2, numbers 2, links 1) of **density**
  (the share of changed lines carrying the signal, capped at 1). It was chosen deliberately
  over volume, so small sharp changes rank above regenerated dumps.
- Side effect in #6 → #7: **63 of the top 100 are changes of 100 characters or less.** One
  added `-H 'anthropic-version: 2023-06-01'` line in a curl example scores 5.0 (code + numbers
  at density 1). An anchor fix (`#drop-a-managed-table` → `#drop-managed-table`) also scores
  5.0.
- The digest cites 60% of the top 25 and 42% of the top 50. Most of the gap is the digest
  **correctly** skipping those one-line edits, so "recall against the top of the ranking" is
  not a valid digest-quality metric as the ranking stands. *(challenge)*

## 6. Validation state after #7
22 passed, 5 warnings, 0 failed. The warnings:
- `duplicate_bodies` 175 (24 before). 132 are the Admin API mirror, 38 Databricks, 5 Anthropic
  old-path/new-path pairs such as `about-claude/models/overview` = `models/overview`.
- `size_distribution`: 12 pages over 500k characters. The largest is
  `api/compliance/activities` at 6.3M.
- `link_graph_closure` 141 (69 → 106 → 148 → 141 over successive runs).
- Two frontmatter warnings, both pre-existing (`genie-agents/api`, the cookbook index).

Tests: 410 pass, ruff clean.

## 7. Process lessons (how the work went, not just what it found)
1. **Measure before designing.** Several decisions reversed once a number existed: the
   asset-hash hypothesis, the 877 GB headroom, the "quiet week is lower" expectation, and in
   an earlier session the piecemeal-digest architecture.
2. **Verify against the full source, not the evidence a tool chose to show.** The excerpt
   audit looked fine, and the full-page check contradicted it.
3. **A check must be validated on the case that motivated it, using real text.**
4. **Vendor events dominate operational numbers:** site-wide re-dates, API-reference
   regeneration, republished sections. Every volume, cost and noise figure here is
   conditional on which events fell in the window, and three windows is not a distribution.
5. **One-off analysis scripts carried the key measurements** (raw churn, duplicate breakdown,
   recall vs ranking). Nothing re-runs them, so the next window has to redo them.
   *(challenge)*
6. **Git discipline:** an earlier session created a worktree and commits without being asked,
   and the owner reversed them. The standing rule is in `CLAUDE.md`.

## 8. Open items, unranked
- Digest: missed restrictions (no absence detector); invented contrast with the past;
  newness check limited to versioned names.
- Compress: moves and metadata-only changes are not collapsed, so vendor re-dates cost ~100k
  tokens.
- Layout: corpus paths keyed on vendor-controlled `updated_date`.
- Raw archive: noise patterns are discovered reactively; normalised content-addressing is not
  built; replay of a generation through an extractor is not built; no retention policy yet.
- `changes.py run --fetch` bypasses archiving.
- Ranking density favours one-line code tweaks.
- Duplicate bodies: the Admin API mirror doubles evidence for the same change.
- Disk: 43 GB free on the host and falling from causes outside this project.
- Issue 04: measured. Whether the window counts as "quiet" is undecided.

## 9. Where to look
| topic | file |
|---|---|
| house rules | `CLAUDE.md` |
| raw archive plan / design / measurements | `plans/raw-archive-plan.md`, `docs/raw-archive.md`, `src/scraper/fetch/generations.py` |
| change feed design and volumes | `docs/changefeed.md`, `src/changefeed/{diff,classify,snapshot,report}.py` |
| digest architecture and accuracy history | `docs/changefeed-phase-2.md`, `src/changefeed/digest/{compress,session,findings,audit}.py` |
| readiness issues | `issue/changefeed-phase-2-readiness/01–05` |
| run outputs | `reports/changefeed/0005..0006.*`, `0006..0007.*`, `digest-0005..0006.md` (v2), `digest-0006..0007.md` |
| validation outputs | `state/validation/*.json` |
| tests | `tests/test_digest.py`, `tests/test_generations.py` |
