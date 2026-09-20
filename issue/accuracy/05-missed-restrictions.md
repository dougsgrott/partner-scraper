# 05 — An absence detector for restrictions

**Status:** done (2026-09-19), uncommitted — the scan ships as `digest.py absence`;
injection's A/B run and graded (90%, coverage up, but anchoring confirmed on the type
specimen; not adopted) ·
**Kind:** code + measurement · **Effort:** ~4 h
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

- [x] The scan, run on the stored #5 → #6 pair, surfaces the Fable 5 retention sentence —
      the motivating case, from the real blobs; this is the test that gates everything
      else
- [x] Candidate counts per stored run recorded here, per lexicon variant
- [x] The A/B/C decision made on those counts and recorded here
- [x] B's A/B: **run and graded 2026-09-19** (`prompt_version` `2+inj`, $3.87, 64
      findings). Seeded-draw full-page grade **9/1/0 (90%)** vs baseline 70%; absence
      coverage rose to **87/117 candidates on cited pages** (best of any arm; baseline
      69) and `breaking` findings to 7. But the anchoring risk materialised, on the
      type specimen itself: the injection got the Fable 5 retention sentence into the
      digest — and the model wrote it as "the same condition **already documented**
      for Claude Fable 5", a false past-claim that neutralises exactly the news the
      injection exists to surface, buried in the additive models finding against rule
      6. The candidate list also re-anchored the GLM-5.3 false newness. Injection
      raises coverage but imports the candidates' framing risk; **not adopted** — the
      deeper fix for the neutralising move is [07](07-reappearing-lines.md)'s
      edited-line pairing, and the scan stays a post-run net (option A)
- [x] False-candidate rate stated: what fraction of candidates a reader judges to be
      restrictions worth a finding

## Tests

- the Fable 5 sentence (real text, real before-body) is a candidate
- a GA announcement ("generally available") is not a candidate despite status language,
  if the RESTRICTION lexicon of [02](02-restriction-lexicon.md) excludes it — the
  breaking-vs-GA distinction the prompt already draws
- a restriction sentence about a *genuinely new* thing (subject absent before) is not a
  candidate
- one vendor sentence stamped across mirror pages is one candidate, not 290
- "cited" is page-level and says a finding *looked*, never that it *reported* the line

## Measured (2026-09-19)

Candidate counts per stored run, deduplicated by line text, subject-in-before required:

| lexicon | #5 → #6 | #6 → #7 | Fable 5 sentence surfaced |
|---|---|---|---|
| loss-core (`cannot`, `not supported/available`, `unsupported`, `unavailable`, `no longer`) | 97 on 57 pages | 91 on 48 pages | **yes** |
| shipped (loss-core + `deprecat*`, `removed`, `discontinu*`) | 117 on 63 pages | 117 on 57 pages | **yes** |
| full RESTRICTION (adds `requires`, `must`, `reject*`) | 254 on 126 pages | 303 on 148 pages | yes |

**The gate passes**: the Fable 5 retention sentence surfaces from the real blobs, page
severity 1.3, on a *cited* page — which is why the "cited" tag is defined as "a finding
looked here", never coverage: the finding that cited that page is the one that inverted
the rule. About 48–52 candidates per run sit on pages no finding cites at all.

**False-candidate rate**: reading a seeded sample of 50 (25 per pair), ~55–60% are
restriction statements worth a reader's attention — platform-availability rows,
`scim`-group API constraints, "models released after Claude Opus 4.6 do not support
setting temperature", deprecation markers — and the rest troubleshooting prose,
footnotes, and schema-row semantics ("no longer members of the organization"). Two
accepted candidate classes are recorded in the module docstring: the twin restriction
shipping with a new version whose family name existed before (the Fable **5.1**
sentence — about one line per launch, next to the twin that matters), and
reference-table field semantics.

**Decision — C's shape, with B gated**: the scan is one function
(`changefeed.digest.absence.scan`); option A ships now as `digest.py absence`
(uncited-pages-first, everything shown by default — a default that truncated the type
specimen would not be a net), and the audit's footer points at it. The full RESTRICTION
lexicon is rejected for the scan (254–303/run, mostly requirement boilerplate). **B is
not adopted yet**: at ~100–117 candidates per run the issue's own threshold ("at
hundreds, B dies") is borderline, so the draft injects *per page* (57–63 groups), and
only its graded A/B can show whether findings improve without rubber-stamping —
"a deterministic scan found added restriction sentences on these pages concerning
things that existed before; for each page, record a finding or state why not." That
A/B costs ~$3–5 plus a grade cycle through [01](01-verdict-ledger.md), including the
#5 → #6 needle set.

## Done (2026-09-19)

`src/changefeed/digest/absence.py` (the scan, deterministic and model-free, runs on
stored pairs) + `digest.py absence [before] [after]` + a footer line on `digest.py
audit` ("the audit can only check findings that exist; the absence scan is the other
half"). Five tests, including the honest-limits ones. One extractor fix came from a
failing test rather than the corpus: a sentence-initial article welds onto the name
("The Unity Catalog API") and never matches the before text — leading articles are
stripped from capitalized-run subjects.

## Follow-up (2026-09-19)

A caution for readers of the arm numbers: **coverage (N/117 candidates on cited pages)
is directional, never a headline metric.** "Cited" means a finding looked at the page —
the type specimen's citing finding is the one that inverted the rule. The combined arm
made the point numerically: its coverage fell to 68/117, *below* baseline, while its
seeded draw graded 100%. Grade clusters carry verdicts; coverage only ranks where to
look next, which is exactly the job `digest.py absence` keeps.
