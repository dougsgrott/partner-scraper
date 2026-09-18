# 03 — Newness check: invisible identifiers, cited-page scope

**Status:** open (2026-09-18) · **Kind:** code + measurement · **Effort:** ~3 h
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

- [ ] DBR 18, Claude Fable 5, and AI v6 headlines each extract an identifier, with tests
      built from the real recorded findings, not synthetic ones (the standing rule — the
      first version of this check failed exactly by testing on a synthetic id)
- [ ] The all-cited-pages-`added` case no longer skips silently: it either checks against
      the corpus-wide index (option C) or renders an explicit "newness unverifiable —
      no before text" note
- [ ] FP rates per admitted option measured on stored findings and recorded here
- [ ] The `us-east-1` false positive resolved or explicitly accepted with its rate stated

## Tests

- real DBR 18 and Fable 5 finding texts flag against real before-bodies
- a genuinely new dotted-version name still flags nothing (no regression on the working case)
- option C: an identifier present only on an *uncited* page of the before snapshot flags
