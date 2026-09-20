# 07 — Mark reappearing lines in diffs and excerpts

**Status:** done (2026-09-19/20), uncommitted — built, measured, three arms run and
graded. **The provenance bet answered yes; the v4 candidacy declined on the
second-pair confirm** (mechanism endpoints held — 0 invented-past, 4/4 needles —
but the rate came in a tier below the unmarked sibling arm); see *The bet,
answered* and *The second-pair confirm* ·
**Kind:** code + measurement · **Effort:** ~3 h build + two graded arms
**Depends on:** [01](01-verdict-ledger.md) (the ledger, live); the baseline of
[13](13-boost-adoption.md) if arms run on #6 → #7 · **Blocks:** nothing

> **Revised after the A/B arms** (`docs/digest-experiments-2026-09-19.md`). The arms
> elevated this issue — and narrowed what it can claim. The type specimen failed through
> **two distinct mechanisms**, and marking addresses only the second:
>
> 1. **Slot exhaustion** (the boost arm): the Fable 5 line is the page's *third*
>    restriction line on a two-slot excerpt. Shown clauses became findings — the 5.1
>    twin did — and unshown ones did not. No marking scheme fixes what is not on
>    screen; option E below is the companion fix for this path.
> 2. **Invented past** (both injection arms): the model read the added line and wrote
>    "already documented for Claude Fable 5" — near-verbatim across two independent
>    sessions, *after* an appendix stating in words that these were ADDED lines. This
>    issue's central bet is therefore now explicit and falsifiable: **per-line
>    provenance carried by the diff itself sticks where instruction-level provenance
>    demonstrably did not.** A hypothesis to test, not a fix to bank — the A/B design
>    below is built around it.

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

**E — adaptive excerpt slots (companion arm — not a marking option).** Scale the
excerpt's line count with the page's RESTRICTION-line count (2 up to 3–4, capped; a few
hundred prompt tokens per run). Not provenance at all, but the boost arm's own
mechanics predict it delivers the type specimen: shown clause → written finding held
for the 5.1 twin, and E puts the Fable 5 clause on screen. **Run it as its own arm,
never combined with a marking arm** — the combined-arm interference result is the
standing reason one input change per arm is now a rule.

- *Pro:* the cheapest plausible path to the one finding no arm produced;
  deterministic; measurable on the stored pair.
- *Con:* more excerpt tokens on restriction-heavy pages, and it hands the model more
  lines *without* provenance — if the invented-past mechanism dominates, E alone could
  reproduce the injection's neutralisation. That is not only a risk but the
  experiment's value: E-alone vs marking-alone separates the two mechanisms cleanly.

## The number to get first

On the stored runs: how many shown `-`/`+` pairs exceed candidate thresholds, and a
hand-read of a sample at each — the over/under-pairing rates. Then the motivating case:
the actual Grok table diff from #5 → #6 must produce the tag, and a diff with a
genuinely new table row must not.

## The A/B design (fixed by the 2026-09-19 arms)

Separate arms on #5 → #6 — marking (A or B) and slots (E) each under their own
`prompt_version` — graded by the same seeded full-page draw as the four existing arms,
so the ledger compares them directly. **Primary endpoint: the type specimen produced as
its own correct finding** — *existing* Fable 5 users who opted out lose the model — the
finding no run has ever written. Secondary: the standing cluster checks (Grok/GLM,
`breaking` discipline, needle-page citation) and no draw regression against the boost
arm's 10/10. If arms run on #6 → #7 instead, [13](13-boost-adoption.md)'s fresh
baseline grade comes first.

## Acceptance criteria

- [x] The real Grok/GLM table diff renders the revised rows as revised — the region rows
      pair at 0.93 against the blobs; tests carry the real Fable retention pair (0.88)
      and a same-shape row (the 11k-char real rows cannot live in a test file; the
      full-row verification is in *Measured*)
- [x] A real diff with a genuinely new row shows it untagged — the real GLM-5.3
      description scores ≤0.1 and stays a bare `+`
- [x] Pairing runs only on rendered lines; `changed_sides` and the ranking path
      unchanged (tested: severity and signals identical under the flag); a full run's
      shown lines pair in **1.0–1.8 s**
- [x] Threshold **0.7**, chosen against measurement: true revisions score 0.84–0.97,
      genuinely new prose ≤0.1, and a read sample of shown lines at ≥0.7 was all
      genuine revisions (58%/43% of shown lines tag — most shown lines ARE revisions;
      the signal is the tag's absence). One measured, accepted boundary: a genuinely
      new line pairs with its TEMPLATE SIBLING (the 5.1 retention line at 0.84 against
      the old Fable 5 line), which is why the tag claims only "a close variant
      existed", never "not new". Under-pairing boundary: an appended clause on a SHORT
      line scores low (0.58 on an abbreviated fixture vs 0.88 on the real line) —
      score is length-sensitive.
- [x] Marking (`2+r+p`, $3.39, 63 findings) and slots (`2+r+e`, $3.66, 92 findings)
      run and graded as separate arms on the boost base, seeded full-page draws,
      the type specimen the named primary endpoint of each — see *The arms*
- [x] The provenance bet answered in writing — see *The bet, answered*

## Tests

- revised-row pairing on the real motivating diff
- new-row non-pairing on a real diff
- a moved line (identical text both sides) is already absent from `changed_sides` output
  and stays absent — no regression on the multiset behaviour


## The arms (2026-09-19)

| arm | findings | cost | draw grade | specimen | flags |
|---|---|---|---|---|---|
| `2+r+p` marking | 63 | $3.39 | 8/1/0 (89%; the partly is a sample-swap labelled `breaking`) | **DELIVERED** — finding 615 | 4 (GLM returned in 614, caught; 2 context FPs; 1 soft-true) |
| `2+r+e` slots | 92 | $3.66 | 10/10 (100%) | **NOT delivered** — the clause was on screen and 684 neutralised it | 7 (2 misquote catches incl. the recurring "BASIC reports only"; 1 new checker artifact: "X is retitled \"Y\"") |

The marking arm's finding 615 is the finding no previous run ever wrote:
*"[breaking] Claude Fable 5 on Databricks now carries the added condition that
customers who opt out of data retention cannot use it"*, detail: *"The 30-day
trust-and-safety retention callout for Claude Fable 5 **previously did not include
the sentence** 'Customers who opt out of data retention cannot use Claude Fable 5.'"*
— the past-claim in the right direction, the clause quoted verbatim. The pathway is
worth recording: the Fable 5 line was NOT in the marked arm's two-slot excerpt; the
5.1 sibling was, tagged `~+`, and the legend ("edited, not added — get_diff shows the
pair") sent the model to the diff, where the aligned view showed the insertion.

The slots arm put the Fable 5 clause itself on screen (third slot) with no
provenance — and finding 684 wrote *"customers who opt out of data retention cannot
use Claude Fable 5.1 **(as already stated for Fable 5)**"*. The invented past, third
independent reproduction (both injection arms, now E), first time with no injection.
E was otherwise excellent: 10/10 draw, best absence coverage of any arm (98/117),
92 findings including the cleanest versions yet of several stories, and its models
finding avoided the GLM false newness in its summary.

## The bet, answered

**Yes: per-line provenance carried by the diff sticks where instruction-level
provenance did not — and where mere visibility actively misleads.** The evidence now
spans four arms: shown-without-provenance produced the "already stated/documented"
neutralisation three times independently (2+inj, combined, 2+r+e); marked provenance
produced the correct edited-line reading and the specimen finding once (2+r+p). The
mechanism isolated by E-alone vs P-alone: when the model sees a restriction clause
about X beside a near-identical clause about X's sibling, it defaults to "the X
version already existed" unless the input carries evidence otherwise. One trial per
arm — the standing caveat — but the signature count is 3-for-3 against visibility
and 0-for-1 against marking. What marking does NOT fix, measured: name-level false
newness (GLM returned under `2+r+p`; a name existing elsewhere is the corpus question
issue 03 measured and rejected) and the `breaking` over-label class (the sample-swap
finding). Adoption question now on the table for [13](13-boost-adoption.md)'s
process: `+p` beat nothing but its draw is one finding below `+r`'s 10/10 while
delivering the specimen — a confirming marked run on #6 → #7 rides along with the
boost confirm if Doug wants both.

## The second-pair confirm (2026-09-20): v4 candidacy declined for now

The `3+p` confirm ran on #6 → #7 ($5.23, 68 findings, shelved via the new
`--no-replace`; worksheet `verdicts-0006..0007-3p.yaml`, graded at the strict
post-re-grade standard).

**The mechanism endpoints held, cleanly.** Invented-past signature: **0 of 68** —
now 0-for-2 pairs under marking (and 0-for-72 in the same-day `3+c` arm; the
signature appears dead under every boost-era prompt, which weakens the claim that
marking specifically kills it). **4 of 4 needles cited — the only arm on any pair
ever to do that**, including the Kimi-retirement control and `token-counting` that
the `2+r` confirm missed, which resolves 13's narrowing watch-item in this arm's
favour. Twelve findings describe changes *as revisions*; two were verbatim-verified
in the draw (800: the `thinking_delta` rewording with the old phrasing quoted; 804:
the 1M-context platform list with the previous list stated exactly).

**The rate did not hold.** 13/5/0 = **72%** — the lowest graded arm on this pair at
the strict standard, against `3+c`'s same-day, same-grader, same-standard **89%**.
All five partlys are one class: pre-existing content conjoined into a change claim
(the DENY and 403 twins of 763/736, plus `workspace_id` deprecation, drop-protection,
and "gained offset"). Marking demonstrably did not fix that class even when the
evidence was marked: the `offset` row *was* a `~` revision and the model still wrote
"gained offset". Meanwhile the unmarked `3+c` arm produced finding 863 — a
verbatim-true past-claim from plain two-sided excerpt visibility.

**Verdict: `+p` is not the v4 candidate on this evidence.** Its unique, replicated
value is needle coverage (4/4) and revision framing; its cost is a rate a full tier
below its unmarked sibling, with the invented-past kill no longer uniquely its.
Standing caveats: one graded pair per comparison, strict-vs-mixed standard across
older arms, CLASSIFY_VERSION 3 input on both new arms. If a future pair shows the
invented-past signature returning under an unmarked prompt, this confirm should be
re-read — that is the one result that would reopen `+p`.