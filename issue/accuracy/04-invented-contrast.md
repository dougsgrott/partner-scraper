# 04 — Verify claims about the past, not only claims of newness

**Status:** done (2026-09-19), uncommitted — the quote check ships; option B's A/B run
and graded (90%, rule followed but other error classes untouched; not adopted) ·
**Kind:** code + measurement · **Effort:** ~3–4 h
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

- [x] The "previously framed as a support note" case — the real recorded text — is a test:
      unflagged by the current audit, flagged by the new check
- [x] Contrast-claim frequency per run measured and recorded here
- [x] A's precision on graded findings measured; the A/B/C decision made on those numbers
      and recorded here
- [x] B's A/B: **run and graded 2026-09-19** (`prompt_version` `2+q`, $3.47, 62
      findings). Seeded-draw full-page grade **9/1/0 (90%)** vs baseline 70%. The rule
      is visibly followed — findings quote the old text and the quotes verify (the ZDR
      finding quotes the old Covered-Models sentence verbatim; the CDF finding quotes
      both requirement texts) — but it does not touch the other error classes: the
      Grok/GLM false newness recurred in full (caught by the audit), and the one
      `partly` was a stale deprecation presented as news, not a contrast claim. The
      induced quote volume also exposed three parsing limits in the verifier (escaped
      quotes inside quotes, sentence-splitting inside quoted text, and "now read
      \"Y\"" not classified present-side) — harden `quoted_claims` before trusting
      its flags at this volume. Not adopted as default; arm R measured better on the
      same pair

## Tests

- the motivating real finding text flags against the real before-body
- a *correct* contrast claim from a graded-true finding does not flag
- trigger lexicon: past-tense phrasing variants from stored findings, not invented ones

## Measured (2026-09-19)

**Frequency** (all 231 stored findings, summary + detail): "previously" appears in 2–10
findings per run; all past-triggers together mark ~25–35 findings per run. Quoted spans
in past context: **26 across the four runs (~6 per run)**; past-trigger sentences
*without* a quote: 115 (~29 per run). Small enough that C — a standing verifier call —
is absurd, as the issue predicted.

**A-terms (term overlap on no-quote past-sentences): rejected, ~90% false.** Of 27
sentence-level hits, nearly all were the *new* side of rename claims ("renamed
`BUNDLE_ROOT` → `DATABRICKS_BUNDLE_ROOT`" flags the new name as absent-from-before —
of course it is), passive-voice "was/were" noise ("examples were rewritten to …"), or
labels the model coined itself ("the earlier yaml-on-stdin idiom"). The direction
problem that bit the excerpts and the model bites naive term checking identically.

**A-quote (verify quoted spans, sided): admitted — final precision 2/2, recall on the
graded cases 1/3, boundaries recorded.** The raw pass flagged 9 of 26 quotes; reading
every one reshaped the check three times, each from a real text:

- three flags were the **to-side** of `changed from "X" to "Y"` checked against the
  before text — a to-quote asserts the *new* text and must check the after text;
- `" was renamed to "` was a quote-pairing artifact (length-filtering before pairing
  let the regex pair a closing quote with the next opening one);
- `"anthropic-workspace-id"` is emphasis, not quotation (now: ≥3 words), and
  `"For how X…"` is an elided template (now: no ellipsis);
- after those fixes the first real run produced one **new** false positive: finding
  199's true statement `pages that linked to "Enrich data using AI Functions"` — a
  prepositional "to", not a rename's to-side. The to-rule now requires a preceding
  from-quote or a rename verb. Caught by reading the real audit output.

Final state on the real pairs: **two flags, both genuine** — finding 237's "support
note" quote (absent from the before text, present in the AFTER text: the model quoted
the new page as the old — the motivating case) and finding 202's `"BASIC reports only"`
(the old page says "The connector only supports ingestion of BASIC reports": right
substance, fabricated quotation). Zero flags on #1 → #2. Known, accepted misses:
quantifier falsity (finding 158's "previously excluded **only** …" — every named term
IS in the old text) and contrast asserted with no trigger at all (finding 253) — the
latter is [07](07-reappearing-lines.md)'s territory (the −/+ pair of the edited
sentence), not a text-side check's.

## Done (2026-09-19)

`audit.quoted_claims()` extracts sided quote-claims; `audit_finding` verifies past-side
quotes against the before text and to-side quotes against the after text of the cited
pages (markup-insensitive), reporting whether a missing quote appears on the *other*
side — "likely quoting the new page as the old" is finding 237's exact mistake. The
all-added unverifiable note now also covers contrast claims. Six tests, every one from
a real recorded finding text (237, 160, 202, 226+179, 158, 199), including the two
honest-boundary tests that assert a known miss stays unflagged.

**Option B, drafted for adoption (PROMPT_VERSION 3, gated on one graded ~$3–5 re-run):**
add to the prompt rules — *"When you assert what the old text said or lacked
('previously …', 'was …', 'renamed from …'), quote the exact old line in double quotes,
or write 'absent before'. Quoted lines are verified verbatim against the stored before
text."* B composes with the shipped check: every quote the rule induces lands in the
verifier, converting the paraphrase class (the check's main blind spot) into the quote
class (where measured precision is 2/2). **C is rejected**: ~6 quote-claims per run do
not justify a standing model call, and the remaining paraphrase misses are bounded and
recorded rather than silent.
