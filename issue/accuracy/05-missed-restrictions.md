# 05 — An absence detector for restrictions

**Status:** open (2026-09-18) · **Kind:** code + measurement · **Effort:** ~4 h
**Depends on:** [02](02-restriction-lexicon.md) (the RESTRICTION lexicon);
[03](03-newness-coverage.md) option C strengthens it · **Blocks:** nothing

## Problem

The worst error class is the finding that was never written. The Fable 5 case is the
type specimen: a page announcing Fable 5.1 also added, for the *existing* Fable 5, the
sentence "Customers who opt out of data retention cannot use…" — a restriction on
something people already relied on, missed under prompt v1 **and** under v2, which
carried a rule written for exactly this. The session record is precise about why no
audit helps: *"no audit can flag a finding that was never written."*

The idea recorded in `docs/changefeed-phase-2.md` — a deterministic pass for added
sentences with restriction language that name something already present before — is the
right shape and remains unbuilt and unmeasured. This issue builds and measures it. What
makes it plausible rather than hopeful: the failure signature is mechanical. The missed
sentence contains `cannot` (a RESTRICTION word once [02](02-restriction-lexicon.md)
lands) on a `+` line, and names a thing present in the before text (checkable via the
before-index of [03](03-newness-coverage.md), or crudely via the cited page's own before
blob).

## Design common to all options

The scan: for each modification, take added lines matching the RESTRICTION lexicon,
keep those whose subject terms appear in the before text (page-local first;
corpus-wide when 03 C exists), emit candidates ranked by restriction-word density.
Deterministic, free, runs on stored pairs today.

## Options — what to do with the candidates

**A — post-run coverage check.** After a digest, candidates on pages **not cited by any
finding** are appended to the audit output: "possible missed restrictions: N, listed."
A human reads them.

- *Pro:* no prompt change, no model-behaviour risk, works retroactively on stored runs.
- *Con:* catches the miss after the digest shipped, and only if the human reads the
  appendix. It is a net, not a fix.

**B — inject the candidates into the session prompt.** An appendix: "a deterministic
scan found these N added restriction sentences concerning things that existed before;
record a finding for each or state why not."

- *Pro:* the finding gets *written*, which is the actual failure; zero extra sessions;
  cost is N × ~1 line of prompt.
- *Con:* `PROMPT_VERSION` bump; anchoring risk — a model handed a checklist may
  rubber-stamp it and slacken elsewhere. Only a graded A/B ([01](01-verdict-ledger.md))
  and the needle sets can show whether overall quality held.

**C — both.** The scan is one function; A audits what B injected, and the injection list
gives the coverage check its denominator.

- *Pro:* B fixes, A verifies B; the pairing is cheap once the scan exists.
- *Con:* none beyond B's, if B survives its A/B.

## The number to get first

**Candidate count per run, at each lexicon strictness.** This number decides everything:
at dozens per run, B is viable and A is readable; at hundreds, B dies (prompt bloat and
rubber-stamping) and A degenerates into a second feed nobody reads — the issue then
reduces to tightening the lexicon or the subject test until the count is workable, or
accepting A-only with sampling. Runs on stored pairs for free before any design
argument. The plan's "what would change this plan" section already commits to this.

## Acceptance criteria

- [ ] The scan, run on the stored #5 → #6 pair, surfaces the Fable 5 retention sentence —
      the motivating case, from the real blobs; this is the test that gates everything
      else
- [ ] Candidate counts per stored run recorded here, per lexicon variant
- [ ] The A/B/C decision made on those counts and recorded here
- [ ] If B: one graded re-run comparing digest-with-appendix against the stored
      digest-without, including needle-set recall and overall grade — not just "did it
      find the planted case"
- [ ] False-candidate rate stated: what fraction of candidates a reader judges to be
      restrictions worth a finding

## Tests

- the Fable 5 sentence (real text, real before-body) is a candidate
- a GA announcement ("generally available") is not a candidate despite status language,
  if the RESTRICTION lexicon of [02](02-restriction-lexicon.md) excludes it — the
  breaking-vs-GA distinction the prompt already draws
- a restriction sentence about a *genuinely new* thing (subject absent before) is not a
  candidate
