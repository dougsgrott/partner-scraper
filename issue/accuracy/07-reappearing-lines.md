# 07 — Mark reappearing lines in diffs and excerpts

**Status:** open (2026-09-18) · **Kind:** code · **Effort:** ~3 h
**Depends on:** [01](01-verdict-ledger.md) only for the optional graded A/B
**Blocks:** nothing

## Problem

The Grok 4.6 / GLM 5.3 error — the audit's founding incident — originates below the
model, in what the model is shown. `classify.changed_sides` is an exact-line multiset
difference: when a vendor rewrites a table whole, a row with one edited cell surfaces as
an unrelated `-` line and `+` line, and the `+` line *reads as an addition*. Prompt rule
4 tells the model a name on a `+` line is not new if it is also on a `-` line — but the
input actively suggests otherwise, and the audit catches the resulting claim only after
it is written, only for identifiers it can extract
([03](03-newness-coverage.md)), and only for audited findings.

Prevention beats detection here: annotate the diff and excerpt so a revised row *looks*
revised. The constraint that shaped `changed_sides` still binds — the multiset diff
exists because `difflib` took ten minutes where it takes 4.6 seconds, so **the ranking
path must stay untouched**; pairing happens only at render time, on the handful of lines
actually shown.

## Options

**A — pair near-duplicate `-`/`+` lines at render time.** In `render_diff` (the
`get_diff` tool) and in `compress._excerpt`: normalise, compute token overlap between
each shown `+` line and the `-` lines (and vice versa), and above a threshold render as
`~` or suffix `(revised — a close variant existed before)`.

- *Pro:* fixes the misleading input for every finding, audited or not; deterministic.
- *Con:* the threshold is a dial with two failure directions — under-pairing leaves the
  trap, over-pairing labels a genuinely new row "revised" and *suppresses* a true
  newness signal. Both directions need real-diff validation before trusting it.

**B — annotate only in `get_diff`, not in excerpts.** The excerpt budget is 280
characters; a tag spends ~25 of them, and rule 3 already sends the model to `get_diff`
for anything it will write about.

- *Pro:* no excerpt budget cost; the annotation lands exactly where checking happens.
- *Con:* the model only sees it for changes it chose to check — the Grok claim was
  written *because* the excerpt misled, so the excerpt may be where the tag earns most.
  A bare `~` sign in excerpts (1 character) is the compromise worth trying first.

**C — cheap containment variant.** Per shown `+` line: do its alphabetic tokens (numbers
stripped) all appear in the before body? Tag "terms present before".

- *Pro:* no pairing, no threshold, trivially fast.
- *Con:* blunter — fires on reworded prose that is not a revised row; likely noisier
  than A. Worth measuring only if A's pairing proves fiddly.

## The number to get first

On the stored runs: how many shown `-`/`+` pairs exceed candidate thresholds, and a
hand-read of a sample at each — the over/under-pairing rates. Then the motivating case:
the actual Grok table diff from #5 → #6 must produce the tag, and a diff with a
genuinely new table row must not.

## Acceptance criteria

- [ ] The real Grok/GLM table diff renders the revised rows as revised — test built from
      the stored blobs, per the standing rule
- [ ] A real diff with a genuinely new row shows it untagged
- [ ] Pairing runs only on rendered lines; `changed_sides` and the ranking path
      unchanged, and the diff-time cost of a full run's renders stated
- [ ] Threshold chosen against the measured over/under-pairing rates, recorded here
- [ ] Optional, once [01](01-verdict-ledger.md) exists: one graded re-run to see whether
      false-newness claims drop

## Tests

- revised-row pairing on the real motivating diff
- new-row non-pairing on a real diff
- a moved line (identical text both sides) is already absent from `changed_sides` output
  and stays absent — no regression on the multiset behaviour
