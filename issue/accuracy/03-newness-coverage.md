# 03 — Newness check: invisible identifiers, cited-page scope

**Status:** measured (2026-09-18), uncommitted — the broadenings were **rejected by the
numbers**; what survived is implemented. See *Measured* and *Done* below ·
**Kind:** code + measurement · **Effort:** ~3 h
**Depends on:** nothing to build; [01](01-verdict-ledger.md) to measure FP rates properly
**Blocks:** nothing hard; option C feeds [05](05-missed-restrictions.md)

## Problem

The audit's mechanical newness check is the one accuracy device that has worked — and it
is shaped like the incident that created it. Verified on 2026-09-18 by running
`audit.identifiers()` on realistic headlines:

| headline | identifiers found |
|---|---|
| "Grok 4.6 added to the supported model list" | `Grok 4.6` |
| "GLM-5.3 is now available in eu-west-1" | `GLM-5.3`, `eu-west-1` |
| "Databricks adds a **DBR 18** requirement …" | **none** |
| "A new restriction on **Claude Fable 5** data retention" | **none** |
| "The **AI v6** environment adds Unsloth support" | **none** |
| "New **DENY** policy type added …" | **none** |
| "code_execution_20260120 tool is new" (un-backticked) | **none** |

`_VERSIONED_NAME` and `_VERSIONED_ID` both require a *dotted* version
(`\d+(?:\.\d+)+`). The session record attributes the DENY miss to "no version number" and
stops there — but **DBR 18 has a version number and is still invisible, and so is
"Fable 5" itself**, the name at the centre of the worst miss. The real gap is "anything
without two dotted components": DBR releases, environment versions (`v6`), major-only
model names, underscore ids unless the model happens to backtick them. Both of the
audit's recent misses fall in this class. Note also the `eu-west-1` row: regions match
`_HYPHEN_ID`, which is exactly the known `us-east-1` false positive.

Separately, **scope**: prompt rule 4 tells the model "check that it does not appear
*anywhere in the old text*", but `audit_finding` checks only the BEFORE blobs of the
pages the finding itself cites. A thing announced on page A but previously documented on
uncited page B passes. And when every cited page is `added`, `befores` is empty and the
check skips **silently** — a finding about a new page is precisely where a false "first
time" claim is cheapest to make.

## Options

Independent; measure each, admit what earns it.

**A — broaden the identifier patterns.** Single-number versioned names
(`[A-Z][A-Za-z]*(\s[A-Z][A-Za-z]*)?\s\d+\b`), `v\d+` forms, underscore ids.

- *Pro:* directly covers DBR 18 / Fable 5 / AI v6; trivial to write.
- *Con:* false-flag surface grows — "Chapter 5", "top 10", bare years. The FP rate is
  measurable for free on the ~190 stored findings (both prompt versions, superseded rows
  included) before enabling anything.

**B — drop the any-digit gate for backticked terms.** Backticks are the model marking
something as an exact identifier; `` `DENY` `` is checkable at low FP cost even without a
digit.

- *Pro:* covers the plain-noun class partially, using a signal the model already emits.
- *Con:* only fires when the model backticks; pairs naturally with a one-line prompt nudge
  ("backtick exact identifiers"), which costs a `PROMPT_VERSION` bump.

**C — a corpus-wide before-index.** One pass over the before-snapshot's blobs builds a
normalised identifier set (the blob store is content-addressed, so the index is
incremental and cacheable per snapshot). "New" then means what the prompt says it means,
and the all-cited-pages-`added` case stops skipping.

- *Pro:* closes the scope hole entirely; deterministic; also the machinery
  [05](05-missed-restrictions.md) wants for "names something that existed before".
- *Con:* a term can exist elsewhere in an unrelated sense ("DENY" as an English word
  somewhere in 6,700 pages). Mitigations to test: restrict the corpus-wide check to
  versioned/backticked identifiers only, or scope it per company.

**D — a region blocklist or context rule** for the `us-east-1` FP class (regions are
named as *context* far more often than as *the new thing*).

- *Pro:* kills the one known standing FP.
- *Con:* a blocklist is a lexicon to maintain; alternatively "identifier preceded by
  in/from/to is context" is a rule with its own FP surface. Cheap to measure both.

## The number to get first

For each broadened pattern: identifiers-per-finding and flag rate over all stored
findings, hand-checking every new flag. The check is only trusted because it is quiet;
an option that triples its flag rate with noise is worse than the gap.

## Acceptance criteria

- [ ] ~~DBR 18, Claude Fable 5, and AI v6 headlines each extract an identifier~~ —
      **invalidated by measurement**: extracting that class produced flags on 6 of 6
      affected findings, every one false (see *Measured*), and would not have caught
      either real graded error. The criterion assumed broader extraction helps; the
      numbers say the dotted-version gate was load-bearing.
- [x] The all-cited-pages-`added` case no longer skips silently: it either checks against
      the corpus-wide index (option C) or renders an explicit "newness unverifiable —
      no before text" note — *the note; option C was measured and rejected as a flag
      source*
- [x] FP rates per admitted option measured on stored findings and recorded here
- [x] The `us-east-1` false positive resolved or explicitly accepted with its rate stated
      — *resolved by shape exclusion; measurement found a second unrecorded instance
      (finding 91, pair #1 → #2) and zero true region flags ever*

## Tests

- ~~real DBR 18 and Fable 5 finding texts flag against real before-bodies~~ (rejected
  with option A)
- a genuinely new dotted-version name still flags nothing (no regression on the working case)
- ~~option C: an identifier present only on an *uncited* page of the before snapshot
  flags~~ (rejected — that behaviour would have flagged nine true launch findings)
- real finding 192's headline extracts no region; the all-added case renders its note

## Measured (2026-09-18)

Extraction variants over all **231 stored findings** (four sets: #1 → #2, #5 → #6 v1 and
v2, #6 → #7), then flag deltas under the audit's real containment semantics against the
stored blobs, every new flag hand-checked:

| option | new identifiers | new flags | verdict on the flags |
|---|---|---|---|
| A — single-number names, `v\d`, underscore ids (months and leading "The" already excluded) | 40 across 28 findings | 10 flags on 6 findings | **6/6 findings false.** "Mythos 5", "Claude Fable 5", "DBR 18" appear in headlines as *context* — the old floor, the existing family, the list being joined. Established things carry bare numbers; newly-versioned things carry dotted ones. The gate encoded that. |
| B — backticked terms without digits | 159 across 87 findings | flags on **25 findings** | ~24/25 noise: SQL-keyword and common-word collisions (`FILE`, `ALTER TABLE`, `auto`, `effort`, `INSERT`). One plausible true positive (`MLFLOW_TRACING_SQL_WAREHOUSE_ID`). The check is trusted because it is quiet; this quintuples it with noise. |
| B′ — B, but the term must appear *backticked* in the old text | — | flags on 19 findings | same classes, barely better. Rejected. |
| C — corpus-wide before-index (current extractor, 2.5–6.7 s to scan a full snapshot) | — | 14 flags on 12 findings | effectively all false, and instructively so: **one cookbook page mentioned Claude Fable 5.1 before the launch**, which would have flagged nine true launch findings of that week at once. Per-company scoping would not have helped (same company). Prompt rule 4's letter — "anywhere in the old text" — is the wrong semantics for real findings. |
| D — exclude cloud-region shapes | −2 identifiers | −2 flags | both standing FPs (findings 91 and 192, the same "…beyond us-east-1" shape) gone; **zero true region flags exist in any stored set.** Admitted. |

**The decisive negative:** none of A/B/B′/C catches either real graded error. Finding 253
(the DBR 18 mislabel) asserts contrast **without a newness verb**, so the newness check
never runs on it under any extractor — that error class belongs to
[04](04-invented-contrast.md). Finding 252's "DENY" is invisible to every extractor
measured — plain-noun newness has no deterministic handle here and its systematic answer
is [05](05-missed-restrictions.md)'s corpus-existence semantics, where "did this exist
anywhere before" *is* the right question.

**Silent skips:** exactly 4 newness findings across all sets cite only added pages, and
none of them extracts a checkable identifier — so option C would have verified nothing
for them either. The explicit note is the honest fix.

**Known residual FP (accepted, rate stated):** one flag in #6 → #7 (an editorial finding
whose subject is "Fable 5.1" and whose *detail* contains instructional "add …", which
trips `claims_newness`). 1 false of 3 standing flags; predates this issue's changes.
Narrowing `claims_newness` is its own measurement and is not attempted here.

## Done (2026-09-18)

- `audit.identifiers()` excludes cloud-region shapes (`_REGION`, covers `-gov-` forms);
  the extractor is otherwise **unchanged on purpose**, and its docstring now carries the
  rejection numbers so the next reader does not re-broaden it in passing.
- `audit_finding` sets `newness_unverifiable` when a newness-claiming finding has no
  before text; `render` prints "the newness check could NOT run; verify by hand".
  Re-running the stored audits surfaces the note on all 4 affected findings.
- Verified on the real pairs: finding 192's flag is gone, the true flags
  (`code_execution_20260120`; `GLM-5.3`/`grok-4-6`) are intact.
- Tests from real texts: finding 192's headline (region excluded, end to end), the
  shape-not-blocklist property, the all-added note, and the no-regression case.
