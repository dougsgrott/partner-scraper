# 02 — Rework change weighting against real ground truth

**Status:** done (2026-08-29) · **Kind:** code + measurement · **Effort:** ~4 h
**Depends on:** nothing · **Blocks:** [03](03-rediff-and-evaluate.md)

> **Revised mid-flight.** The premise below was wrong, and measuring said so. The original
> claim — "the heuristic ranks 97% substantive, so it filters nothing and is broken" — turned
> out to be mostly a misreading of the corpus, not a defect in the classifier. What follows
> is the corrected problem statement and what was actually built. The original framing is
> preserved in [What the premise got wrong](#what-the-premise-got-wrong) because the mistake
> is the useful part.

## Problem (as revised)

The weight heuristic marked 1,084 of 1,116 modifications (97.1%) `substantive`. Three real
defects sat behind that number, and one imagined one.

1. **The feed was ordered alphabetically.** `DiffResult.feed()` sorted by
   `(company, category, url)`. With ~680 substantive changes in a run, that buries a
   deprecation among hundreds of routine edits. **This was the real problem.**
2. **The strongest available signal was not being used.** `classify.SIGNAL` tested for
   links, numbers, headings and code. It had no notion of *status and policy language* —
   deprecated, no longer, not supported, beta, generally available — which is what
   separates "this property is no longer supported" from a reworded paragraph.
3. **Weighing was ~130× slower than necessary.** `changed_text` ran `difflib` over every
   modification, and this corpus holds pages of 6.0 MB. `difflib` is superlinear.

## What the premise got wrong

The original issue assumed 97% substantive meant the classifier was broken. Measuring the
1,116 real modifications says the corpus really does change that heavily:

| | |
|---|---|
| move a link, heading, code block, or number | **84%** |
| median change as a share of its page | **19%** |
| median changed characters | 1,285 |

Then a stratified sample of 64 was read by hand. Among the cases that *looked* least
significant — no structural signal at all — were:

- a SQL property that is **"no longer supported"** (`pipelines.channel`)
- a function leaving **Beta** (`ip_network`)
- an availability list narrowing (`vector_search`)
- **Claude Sonnet 5 dropped** from a supported-model table

Five of eight were genuinely worth reading; only two were editorial. **No honest threshold
reduces ~680 substantive changes to a readable handful, because most of them really are
substantive.** Reduction beyond ordering has to come from clustering or a model pass —
which is [05](05-decide-phase-2-architecture.md)'s problem, not this one.

The acceptance criterion the original issue set — *recall ≥ 0.95 on a labelled sample* — was
also badly chosen. Recall of the worth-reading class is trivially maximised by calling
everything substantive, which is exactly what the old classifier did. It measures nothing
when the classifier is permissive. **Ordering quality is the criterion that matters**, and it
is checked by reading the top of the feed.

## What was built

**A `status` signal.** Status and policy language in the changed lines. On the read sample it
fired on every change worth reading — including the two with no structural signal — and on
neither editorial change. It fires on 55% of all modifications.

**A `severity` score, by density rather than volume.** Each signal counts as the share of
changed lines carrying it, capped at one. This was the decisive design choice and it took two
attempts:

| scored by | what reached the top of the feed |
|---|---|
| volume (`log1p` of raw counts) | regenerated API reference pages — one had **11,181** status-matching lines purely because it is enormous |
| **density** (share of changed lines) | a swapped beta header; a region's supported models changing `databricks-gpt-5-5-pro` → `databricks-grok-4-6`; **the Python tool runner losing automatic compaction** |

Size is not a term at any point. The largest change in the run rewrote 4.2 MB of a
machine-generated dump; letting size in put it above every deprecation in the corpus.

**The feed is ordered by severity**, and each entry shows its evidence — `severity 6.0
(status ×2, numbers ×1, links ×2)` — because a ranked feed a reader cannot interrogate is one
they will not trust.

**`difflib` is out of the ranking path.** `changed_lines` uses a line multiset symmetric
difference instead: O(n), and a moved line is correctly ignored because its count is
unchanged in both multisets. `changed_text` still uses `difflib`, because rendering a diff
for a human genuinely needs the alignment.

**Rendering is guarded too.** Above 400,000 characters `render_diff` falls back to an
unaligned changed-lines listing that states what it is and carries no `@@` hunk headers, so
it cannot be mistaken for a diff.

## Outcome

Over the 1,116 modifications:

| | before | after |
|---|---|---|
| full diff of 1,116 changes | ~10 min | **17 s** |
| feed order | alphabetical | **severity, most urgent first** |
| `substantive` | 1,084 | **1,021** |
| `low` | 29 | **92** |
| `noise` | 3 | 3 |

The substantive share moved less than the original premise expected — from 97.1% to 91.5% —
and that is the honest result: it was roughly right all along, because the corpus really does
change that heavily. Ranking down did roughly triple, which is a real improvement, but it is
not the change that matters. What matters is that the top of the feed is now worth reading.

Of the 522 modifications attributed to a vendor, 519 rank `substantive` and 3 `low`. The
other 594 are `unknown`-attributed and so appear in neither the feed nor the ranked-down
list — see the note under Verification.

**Known false negative, deliberately accepted.** `manage-claude/access-transparency` renames
"Anthropic Workbench" to "Playground (Claude Console)" with no status word, number, link,
code or heading change — invisible to every signal here. It ranks `low`. It is still counted
and still listed by URL, so the rank-never-filter rule holds; catching it would need a
proper-noun or table-row signal, which is speculative on one example.

## Verification

```bash
uv run pytest -q            # 313 passed
uv run ruff check .
uv run python scripts/changes.py diff 1 2 --write
```

Then read the top of `reports/changefeed/0001..0002.md` and confirm the leading entries are
changes you would want in a weekly digest.

Note that this pair's feed is Anthropic-only: all 593 Databricks modifications are
`unknown`-attributed because both snapshots predate `body_fingerprint`
([01](01-split-body-fingerprint.md)). From snapshot #3 onward both vendors appear.

## Tests added

- status language outranks a larger prose edit
- severity is scale-invariant — a sharp 2-line deprecation beats 200 status lines spread
  over 20,000
- the feed is ordered by severity, not alphabetically
- a page too large to align falls back to an unaligned listing and says so
