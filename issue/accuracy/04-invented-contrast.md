# 04 — Verify claims about the past, not only claims of newness

**Status:** open (2026-09-18) · **Kind:** code + measurement · **Effort:** ~3–4 h
**Depends on:** [01](01-verdict-ledger.md) for FP measurement · **Blocks:** nothing

## Problem

The session record's own cross-run conclusion: *"the model's most common error is
invented contrast with the past. It asserts what the old text said or lacked, without
checking."* Real instances: "previously framed as a support note" (the old text had no
such note); a DBR 18 requirement presented as new when only DENY was added to an existing
sentence; "where AI v5 bundled it with its dependencies"-style framings whose before-half
is unverified.

The audit machinery checks exactly one direction: a **newness** claim is tested for the
identifier's *absence* from the before text. Nothing tests the mirror image — a
**previously/was/used-to** claim for the asserted content's *presence* in the before
text. The most common error pattern is the one with no detector, while the machinery it
needs already exists inverted.

## Options

**A — the deterministic mirror check.** Trigger lexicon
(`previously|used to|was\b|had\b|no longer|until now|before this change`) → extract the
distinctive terms of the past-tense clause (reuse `claim_terms`, or prefer
quoted/backticked spans when present) → require them in the BEFORE blobs of the cited
pages; flag "asserts the old text said X; X's terms are absent from it". Unlike the
newness check, this one should read the **detail** too — that is where contrast framing
lives — which is exactly the choice that produced noise for newness, so the FP rate
decides, not the analogy.

- *Pro:* zero model cost; same machinery inverted; targets the top error class directly.
- *Con:* term overlap is a weak proxy for a paraphrased assertion — "framed as a support
  note" shares few content words with any actual old sentence. Expect real FN and some
  FP; measure both on the graded ledger before trusting it.

**B — make the model quote its evidence, then check the quote exactly.** A prompt rule:
any claim about what the old text said must include the exact `-` line (or state "absent
before"). The audit then verifies by whitespace-normalised substring — near-zero FP, and
the fabrication is prevented at writing time rather than caught after.

- *Pro:* verification becomes trivial and strong; the strongest option on principle,
  because it converts an unverifiable paraphrase into a checkable citation.
- *Con:* `PROMPT_VERSION` bump and a ~$5 graded re-run to know what it did; findings get
  longer; the model may quote loosely (normalisation handles some of this) or may simply
  stop making contrast claims — which is itself a win for accuracy but a loss of useful
  framing, and only the graded A/B will show which happened.

**C — a scoped verifier call.** Batch every contrast claim from a run into **one** small
model call (Haiku-class) with the relevant before-texts; true/false per claim.

- *Pro:* handles paraphrase, which A cannot.
- *Con:* the plan's only standing-call exception — one bounded call per run, but still a
  second model whose own errors need auditing. Enters only if A and B measure
  insufficient, per the standing constraints.

A and B compose: B for new runs, A as the audit-side check that also works on stored
findings from before the prompt change.

## The number to get first

Free and immediate: the trigger-lexicon hit rate over all stored findings — how many
contrast claims does a typical run even make? If it is five, option A's FP tolerance is
generous and C is absurd; if it is fifty, precision dominates the choice. Then A's
flag/FP/FN rates against the graded ledger, using the known real cases as the FN probes.

## Acceptance criteria

- [ ] The "previously framed as a support note" case — the real recorded text — is a test:
      unflagged by the current audit, flagged by the new check
- [ ] Contrast-claim frequency per run measured and recorded here
- [ ] A's precision on graded findings measured; the A/B/C decision made on those numbers
      and recorded here
- [ ] If B is adopted: `PROMPT_VERSION` bumped, one stored-pair re-run graded through
      [01](01-verdict-ledger.md) before default

## Tests

- the motivating real finding text flags against the real before-body
- a *correct* contrast claim from a graded-true finding does not flag
- trigger lexicon: past-tense phrasing variants from stored findings, not invented ones
