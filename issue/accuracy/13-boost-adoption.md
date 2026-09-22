# 13 — Confirm and adopt the boost: baseline, sample, version axes

**Status:** done (2026-09-19/20), uncommitted — **confirmed and adopted:
PROMPT_VERSION 3 = v2 text + boosted input is the default**. The second-grader pass
ran 2026-09-20 (delegated back by Doug): 4/6 rows confirmed, **2 downgraded
true → partly**, both in the bias-predicted direction; the confirm arm reads
**15/3/0 = 83%** (was 94%) against the baseline's 79% — margin narrowed, direction
and adoption unchanged; see the re-grade box below · **Kind:** measurement + decision
**Effort:** two grade cycles + one ~$5 run
**Depends on:** [01](01-verdict-ledger.md) (the ledger), [02](02-restriction-lexicon.md)
(the boost, built and A/B'd on #5 → #6) · **Blocks:** flipping the
`--boost-restrictions` default

## Problem

The experiment record (`docs/digest-experiments-2026-09-19.md` §7) recommends the boost
for default and is honest about what carries the recommendation: not the 10/10 draw
alone — 10/10 vs the baseline's 7/10 is p ≈ 0.1 one-sided — but its convergence with
zero mechanical flags across all 79 findings and the named error clusters resolving at
the source. n=10, one launch-week pair, arms built by the grader. The document's own
prescription is a confirming run on the stored #6 → #7 pair. Three things stand between
that prescription and a defensible default flip:

1. **#6 → #7 has no valid baseline.** The ledger makes this legible in a way the prose
   never did: the imported v2 grade splits into excerpt-method **6/6 "true"** versus
   full-page **1 true / 3 partly** on the 4 findings actually checked against full
   text. The excerpt method did not flatter the run — it inverted the picture, on the
   same findings. The stored v2 findings for the pair need a fresh seeded full-page
   draw before any boost run on it means anything. That grade is free.
2. **The sample is the cheap half, and this draw decides a default.** Use n = 15–20,
   not 10. The run costs ~$5 either way; grading is the only added cost, and buying
   sample here is buying the decision.
3. **The version axes diverged, and the sketch conflates them.** "Fold `+r` into the
   next PROMPT_VERSION" ([02](02-restriction-lexicon.md)'s adoption parenthetical)
   merges what issue 02 just separated: the boost is an **input-shape** change
   (compress-side, `CLASSIFY_VERSION` territory) and the prompt text is untouched.
   Meanwhile [04](04-invented-contrast.md)'s Done still carries a *declined* rule-10
   draft labelled "PROMPT_VERSION 3" — mint v3 carelessly and the dead draft rides
   along in the next reader's understanding of what v3 means.

## Options — where `+r` lives

**A — bump `CLASSIFY_VERSION` 1 → 2; the prompt stays v2.**

- *Pro:* honest axes; each stamp means what it says.
- *Con:* the ledger and `digest.py accuracy` key on `prompt_version`. Boost-default
  runs would grade as plain "v2", indistinguishable from pre-boost v2 — comparability
  breaks exactly where the whole instrument lives, unless the query and the findings
  rows both learn `classify_version`, which is a schema change for bookkeeping.

**B — mint PROMPT_VERSION "3", defined as "v2 text + restriction-boosted input".**
The definition lives in the version comment beside `PROMPT_VERSION` in `session.py`,
which already carries per-version rationale; it states explicitly that the rule-10
quote draft is **not** part of v3. `CLASSIFY_VERSION` bumps in the same change, so
both stamps move together.

- *Pro:* one axis, the one the ledger already keys on; the definition survives where
  the next reader will look.
- *Con:* the name lies slightly — the prompt *text* is v2's. The comment is what keeps
  it honest, and comments are what this repo uses for exactly this.

**C — a new combined `digest_version` superseding both.**

- *Pro:* one true axis with an honest name.
- *Con:* a third version symbol, plus findings-schema and report changes, to solve a
  problem two comments solve. Overweight.

Leaning **B**: the ledger's key is the axis that must not fork.

## Also in this issue, because they share the grade cycle

- **The 547 signature, measured where it matters.** Both injection arms independently
  wrote near-verbatim "already documented for Claude Fable 5" (see
  [04](04-invented-contrast.md)'s follow-up). Count `already
  documented|existed|carried|present` past-claims in the boost arms' stored findings —
  free. If the signature is injection-specific (injection is not adopted), nothing
  needs building; if it appears under boost alone, 04 gains a narrow trigger.
- **A second grader.** The arms were built and graded by the same session — the one
  bias the ledger records (`grader`) but cannot correct. Doug re-grades a handful of
  `2+r` and combined-arm worksheet rows from the blobs; agreement or disagreement gets
  a line in the experiment record either way. **The vehicle is the review tool**
  (`scripts/review.py serve`, [docs/review-tool-plan.md](../../docs/review-tool-plan.md)):
  a targeted grading queue over those rows enforces the blind protocol in code — prior
  verdicts are withheld until after submit, then revealed for the agreement comparison —
  and stamps `grader` on every verdict. The ledger keeps one row per (finding, method),
  so the re-grade *replaces* the stored full-page row; the original stays readable in
  its worksheet provenance and in the reveal, which is where the agreement line for the
  experiment record comes from.

## The number to get first

The free one: the fresh #6 → #7 v2 full-page baseline draw. Everything else waits on it.

## Acceptance criteria

- [x] Stored v2 #6 → #7 findings graded by seeded full-page draw, n=18, imported —
      **15/3/0 among the fresh draw; the pooled full-page draw row reads 15/4/0 = 79%
      (76% weighted, 19 grades)**. The prose-era "1 of 4" full-page impression is
      resolved: that subset was suspicion-selected. All partlys sit in the two known
      classes (invented contrast ×2, Grok false newness ×1). One suspicion was
      overturned by the blobs: finding 245's "(was 10,000)" is verbatim-true.
- [x] Boost run on #6 → #7 (`2+r`, $4.85, 62 findings — first attempt burned $0 on a
      session-limit error, retried after reset), graded same seed/method, n=18:
      **17/1/0 = 94%** *(re-graded 2026-09-20: **15/3/0 = 83%** — see the
      second-grader box)*. The original partly is the DENY plain-noun false newness
      (the 252 class, invisible to the digit-gated newness check) — the boost's known
      out-of-scope class, now seen on both pairs.
- [x] Cluster checks: two of the four needle pages cited (the two invented-contrast
      SQL/ABAC pages); **the Kimi-retirement control and token-counting pages
      uncited** — recorded as the adoption's watch-item (62 findings vs baseline's
      79; variance vs mechanism indistinguishable at n=1; the needle file remains
      the standing regression check on every future run). `breaking` group: 7, six
      genuine restrictions + one sample-swap over-label — the recurring class,
      prompt-side, not boost-side.
- [x] The version decision is **in the code**: `session.py`'s `PROMPT_VERSION = "3"`
      comment defines v3 as the v2 text plus boosted input, names the two confirms,
      and **explicitly excludes the declined rule-10 quote draft**, the injection,
      marking and slots; `CLASSIFY_VERSION` moved 1 → 2 in the same change with its
      own comment (option **B** — one ledger axis, kept honest by the comments, as
      this issue leaned).
- [x] **Default flipped.** Reason: the improvement replicated on a second, larger,
      structurally different pair (launch week 70% → 100% at n=10; ordinary-week
      79% → 94% at n=18, **83% after the 2026-09-20 re-grade** — margin narrowed,
      direction intact; pooled boost draws 27/28 vs baseline 22/29), with the error
      clusters consistent both times and the residual partlys in classes the boost
      never claimed to fix. `--no-boost-restrictions` records `3-r`.
      `docs/changefeed-phase-2.md` updated.
- [x] Second-grader agreement — run 2026-09-20, delegated back by Doug. Honesty
      first: the re-grader is the **same model**, post-context-compaction — claims
      were re-verified from the blobs *before* reading the recorded verdicts, which
      is blind-ish, not independent. Results: 333, 351, 305 (the 5→6 arm) and 763
      all **confirmed** — the 100% and the partly stand. **736 and 785 downgraded
      true → partly**, both the same failure shape the box was designed to catch:
      the first pass verified the quoted change and stopped, missing contradicting
      material on the same page (736: the after page itself says delete endpoints
      keep the old `Needed: [...]` wording, so the universal claim is over-broad;
      785: the USE CONNECTION clause is verbatim pre-existing at #6, folded into
      the change finding without the "restate" marker the finding applies to its
      own sawtooth material). **Arm rate: 17/1/0 = 94% → 15/3/0 = 83%**, vs
      baseline 79% — the margin narrows from 15 to 4 points. Two caveats cut
      opposite ways and are both recorded: the six rows were suspicion-selected
      (worst-first), so the downgrades cannot be extrapolated to the arm; and the
      baseline pass was *not* re-graded, so its 79% carries the same first-pass
      leniency risk. The adoption stands on the replicated direction (70→100 and
      79→83 with consistent error clusters), not on the 94% headline, which this
      pass retires. Full per-row reasoning in the ledger notes
      (`source: … re-graded 2026-09-20`); worksheets annotated;
      `docs/digest-experiments-2026-09-19.md` Addendum 3.
- [x] 547-signature census recorded in [04](04-invented-contrast.md)'s follow-up:
      false instances only under injection/combined/slots (1 each), zero under v2,
      boost, quote rule and marking; the marking arm's one match is a verified TRUE
      use of the phrase.
