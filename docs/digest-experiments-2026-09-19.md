# Digest accuracy experiments — four A/B arms on one stored pair (2026-09-19)

> Written to stand alone: the reader is assumed to know nothing about this project.
> Conclusions a reviewer should attack are marked *(challenge)*. Everything here traces
> to files in this repository (§9) and to the verdict ledger in `state/changes.db`,
> which answers `uv run python scripts/digest.py accuracy` at any time.

## 0. Context in one page

This project keeps a local corpus of two vendors' documentation (Anthropic's
platform.claude.com and docs.databricks.com, ~6,700 pages), snapshots it weekly, diffs
snapshots, and pays one LLM session (~$3–4, `claude-opus-5`, Claude Agent SDK) per week
to write a *digest*: findings about what changed, for engineers who build on both
vendors. The digest is useful and wrong in recurring ways; an earlier review decomposed
the errors into twelve issues (`issue/accuracy/`), and the days before this experiment
built the instruments: a **verdict ledger** that persists human grades per finding
(selection: seeded `draw` vs `targeted`; method: `full-page` vs `excerpt`; stratum
weights), a **mechanical audit** (false-newness check, quoted-past-claim verification),
and an **absence scan** (added restriction lines naming things that existed before —
the class of finding the digest historically failed to write at all).

Three accuracy interventions were built but *gated*: each changes what the model reads,
and the house rule requires one graded A/B on a stored pair before any input change
becomes default. This document records those A/Bs — three single arms plus the
combination — all on the stored snapshot pair **#5 → #6** (a launch week: Claude Fable
5.1 / Mythos 5.1 shipped, 1,072 changes, ~88k-token prompt), against a baseline graded
the same way. Total spend: **$15.26**.

The recurring characters:

- **The type specimen.** The supported-models page added, for the *existing* Claude
  Fable 5, the sentence "Customers who opt out of data retention cannot use Claude
  Fable 5." — a restriction on something people already relied on, verified new in this
  window (absent from #5, present in #6), missed by every previous digest of the pair.
- **The Grok/GLM cluster.** The same page's rewritten tables made the pre-existing
  models Grok 4.6 and GLM-5.3 reappear on `+` lines; earlier digests called them
  "added". The mechanical newness check now catches this class.
- **The `breaking` label.** Prompt v1 over-used it (12 of 48 findings); v2's rules cut
  it to 4 of 63 with one still wrong.

## 1. Method

Every arm: one full digest run over the same pair, findings recorded under a distinct
`prompt_version` so the ledger never pools arms. Grading per arm, all free after the
run:

1. **Seeded draw, full-page** — `draw(findings, n=10, seed=1)`, every drawn finding
   checked against the stored page bodies (blobs), imported into the ledger with
   stratum weights. Same seed and method for every arm and the baseline.
2. **Mechanical audit over all findings** — false-newness flags, quoted-past-claim
   verification, unverifiable notes.
3. **Cluster checks** — the type specimen, Grok/GLM, the `breaking` group read in
   full, needle-page citation (5 verified anchor changes at feed ranks 1–744), absence
   coverage (of 117 scan candidates, how many sit on cited pages).

The baseline first: prompt v2's own seeded draw had never been graded full-page (its
earlier grades were targeted at known errors, which the ledger refuses to call a rate).

## 2. Baseline: prompt v2 grades 70%, and grading found a new false finding

**v2 draw: 7 true / 1 partly / 2 false (70%, weighted 70%).** Both falses are invented
newness. One was known (`code_execution_20260120` "now supported" — the release note
was in #5). One was new to us: finding 172 reported that cache-invalidation
documentation was added ("the prompt-caching table gains an 'Effort setting' row"; "the
thinking page adds 'Configuration changes invalidate caching'") — **both existed in #5
verbatim**, and the third claimed addition isn't on the after page at all. The partly
is a mild invented contrast ("no longer shortens retention" where the page states a
minimum, not a change). For calibration: prompt v1's identically-graded draw is 50%.

## 3. The three single arms

| arm | mechanism | findings | cost | draw | true flags | coverage |
|---|---|---|---|---|---|---|
| `2+r` boost | restriction-first, clause-windowed excerpts (the 280-char excerpt had cut the retention sentence at the word `cannot` — character 140 of the line, `EXCERPT_LINE` = 140) | 79 | $3.79 | **10/10** | **0** | 74/117 |
| `2+q` quote rule | prompt rule 10: assert what the old text said only with a verbatim quote, or "absent before"; quotes verified mechanically | 62 | $3.47 | 9/1/0 | ≥1 | 72/117 |
| `2+inj` injection | the absence scan's 117 candidates appended to the prompt, grouped per page, "record a finding or it's uncovered" | 64 | $3.87 | 9/1/0 | ≥2 | **87/117** |

**Boost (`2+r`) — everything moved together.** 10/10 on the draw; zero mechanical
flags across all 79 findings; all needle pages cited. The graded error clusters
resolved at the source: the new-models finding names only the three genuinely new
models (no Grok/GLM), the CMEK story carries `behavioural` (v2 had mislabelled it
`breaking`), and the 5.1 retention restriction became its own finding — because the
boosted excerpt put exactly that clause on screen. The Fable 5 twin stayed unreported:
it is the page's *third* restriction line and the excerpt has two slots, precisely as
the pre-spend measurement predicted.

**Quote rule (`2+q`) — works on its class, only its class.** The model obeys: findings
quote the old text and the quotes verify verbatim (the ZDR finding quotes the old
Covered-Models sentence exactly; the change-data-feed finding quotes both requirement
texts). But the Grok/GLM false newness returned in full (caught by the audit) — quoting
discipline does not touch the newness class. The one partly presented an
already-deprecated field as newly deprecated: also outside the rule's reach. Side
effect: the induced quoting volume exposed three parsing limits in the verifier
(escaped quotes inside quotes; sentence-splitting inside quoted text; "now read *Y*"
not classified as present-side) — its flags are not trustworthy at this volume until
hardened.

**Injection (`2+inj`) — the predicted anchoring materialised, on the type specimen
itself.** Coverage rose to 87/117, `breaking` to 7, and the model *did* read the Fable
5 sentence from the appendix — then wrote it as "the same condition **already
documented** for Claude Fable 5", a false past-claim that neutralises exactly the news
the injection exists to surface, buried inside the additive models finding against the
prompt's own rule 6. The candidate list also re-anchored the GLM-5.3 false newness.

## 4. The combined arm: 10/10 on the draw, and worse where the draw doesn't look

`2+r+q+inj`: 73 findings, $4.13. Its seeded draw also grades **10/10**, and the drawn
findings are the strongest any run produced (the ABAC GA finding quotes its removed
limitations verbatim and verified; the Batches finding quotes the old and new
unsupported-parameter lists exactly). The interactions:

- **Composed well:** boost × quote rule. Windowed excerpts hand the model real old
  text; it quotes it accurately. The Grok/GLM fix held.
- **Interfered:** `breaking` ballooned to **15 of 73**, with 3–4 over-labels — a C#
  *example* change; the CMEK doc-widening that v2 was already graded down for; and a
  verified *relaxation* (job-metrics prerequisites, correctly reported as loosened by
  the injection arm) framed as a new requirement. The injection's "record restrictions"
  pressure plus the quote rule's old-text gravity pushed labels the boost alone never
  pushed. *(challenge: 3–4 of 15 is my reading of the group; the list is in
  `reports/changefeed/digest-0005..0006-2rqinj.md` for re-adjudication)*
- **Cancelled out:** absence coverage fell to **68/117 — below baseline**. The
  injection's headline gain vanished in combination.
- **Reproduced:** finding 547 repeats the neutralisation *verbatim* — the 5.1
  restriction quoted exactly, then "the same note already existed for Claude Fable 5."
  False, in **both** runs that injected, independently. Injecting candidates reliably
  provokes the model into inventing a past for them. *(challenge: n=2; but the exact
  phrasing recurrence across independent sessions is hard to read as chance)*

## 5. The type specimen across five runs

| run | the Fable 5 restriction |
|---|---|
| v2 baseline | absent; the models finding inverts the rule ("an opt-out path") |
| `2+r` | the **5.1** twin becomes its own finding (the excerpt showed that clause); the Fable 5 line — third restriction line, two excerpt slots — still absent |
| `2+q` | absent; only the Anthropic-side ZDR story (correct, well-quoted) |
| `2+inj` | present in a detail — as "already documented for Claude Fable 5" (false) |
| combined | its own `breaking` finding, 5.1 quoted verbatim — Fable 5 half still "already existed" (false) |

No arm produced the correct finding: *existing* Fable 5 users who opted out lose the
model. The failure mechanism is now precise: the model cannot reliably distinguish a
newly added line from background it assumes was always there, and *telling* it (the
injection appendix says "these are ADDED lines") demonstrably does not stick. The
deterministic fix on deck is issue 07 — mark edited/reappearing lines in the diffs and
excerpts themselves, so the input carries the distinction instead of the instructions.
*(challenge: an alternative reading is that the model treats "the 5.1 sentence is the
news" as licensing "the 5 sentence is background"; issue 07 would test exactly this)*

## 6. Methodological findings — as valuable as the arms

1. **A 10-finding draw rate and the cluster checks disagree, and the clusters are
   right.** Two arms grade 10/10 while differing sharply on `breaking` discipline,
   coverage, and the type specimen — all outside the draw. A sample rate is evidence;
   targeted checks on known error classes carry the verdict. Neither substitutes for
   the other, which is why the ledger stores selection per verdict.
2. **Raw flag counts stop being comparable once the quote rule enters.** Quoting volume
   drives artifact flags (the three parser limits above); the combined arm's 10 raw
   flags are mostly artifacts while its one real error (the invented past in 547) is a
   paraphrase the checker cannot see. Harden `audit.quoted_claims` before trusting its
   flag counts at quoting volume.
3. **The baseline was flattered by its own prose history.** The session record's
   impression of v2 ("improved but did not recover") sat on targeted grading; the
   unbiased draw both confirmed the improvement (50% → 70%) and surfaced a false
   finding nobody had noticed (172). Instruments beat impressions.

## 7. Conclusions and recommendation

- **Adopt the boost alone as default** *(challenge — this is the one operational
  decision in this document)*: 100% draw with clean clusters, zero flags, no
  interference terms, +$0.30/run. n=10 on one launch-week pair is not statistical
  proof; the recommendation rests on the convergence of draw rate, zero flags over all
  79 findings, and the named clusters resolving at the source. A confirming boost run
  on the stored #6 → #7 pair (~$5 + a grade cycle) is the cheap way to be surer.
  Adoption mechanics: flip the flag default and fold `+r` into the next PROMPT_VERSION.
- **Do not adopt the quote rule as default.** Keep the *verifier* (it runs on all
  findings regardless); the rule adds verifiability, not accuracy, and in combination
  helps push labels the wrong way.
- **Do not adopt the injection**, singly or combined. Its scan stays valuable as the
  post-run net (`digest.py absence`, uncited-pages-first).
- **Issue 07 (edited-line marking) is now the highest-leverage open item**: it attacks
  the one mechanism every arm failed on, deterministically and free.

## 8. Costs and integrity

$15.26 total (R $3.79, Q $3.47, inj $3.87, combined $4.13). All five runs' findings are
preserved in `state/changes.db` under their `prompt_version`s; prompt v2 was restored
as the *current* set for the pair and renders byte-identical to the committed digest.
Grading: one grader (the session of 2026-09-19), same seed, same method, notes per
verdict in the worksheets. Known bias: the grader built the arms. *(challenge: re-grade
any worksheet from the blobs; every verdict names its evidence)*

## 9. Where the data lives

| artifact | path |
|---|---|
| the ledger and all runs | `state/changes.db` (`findings`, `verdicts`); `scripts/digest.py accuracy` |
| worksheets (per-verdict notes) | `reports/changefeed/verdicts-0005..0006-{v1,v2,v2-draw,2r,2q,2inj,2rqinj}.yaml` |
| arm digests | `reports/changefeed/digest-0005..0006-{2r,2q,2inj,2rqinj}.md` |
| the A/B records | `issue/accuracy/02,04,05` + `docs/changefeed-phase-2.md` ("The three A/B arms") |
| the instruments | `src/changefeed/digest/{verdicts,audit,absence}.py`; arm flags in `session.py` / `scripts/digest.py run --help` |
| needle ground truth | `docs/changefeed-needles-0005..0006.yaml` |
| the prior session record | `docs/session-2026-09-18-lessons.md` |


---

## Addendum (later on 2026-09-19): the issue-07 arms close the type-specimen story

Two further arms, run after this document was first written, on the boost base
(`2+r`, the presumptive default), one input change each. Full record:
`issue/accuracy/07-reappearing-lines.md`.

| arm | mechanism | findings | cost | draw | the type specimen |
|---|---|---|---|---|---|
| `2+r+p` marking | shown diff lines with a close variant on the other side are tagged `~` ("edited, not added or removed whole"), threshold 0.7 measured against the blobs | 63 | $3.39 | 8/1/0 | **written, correctly, for the first time in any run**: "[breaking] Claude Fable 5 on Databricks now carries the added condition that customers who opt out of data retention cannot use it… previously did not include the sentence…" |
| `2+r+e` slots | up to four excerpt slots on restriction-heavy pages — the Fable 5 clause itself lands on screen | 92 | $3.66 | 10/10 | clause visible, then neutralised: "…cannot use Claude Fable 5.1 **(as already stated for Fable 5)**" |

Which answers §5's open question and sharpens §6's lesson:

1. **The invented-past signature is now 3-for-3 against visibility without
   provenance** (both injection arms, then the slots arm — no injection involved) and
   **0-for-1 with provenance marking**. Showing the model the added line does not
   work; telling it in an appendix does not work; a per-line tag carried by the diff
   itself, with a one-rule legend, worked on first trial. One trial per arm, as
   always — but the mechanism is now isolated, not conjectured.
2. The marking arm's pathway is worth knowing: the specimen line was NOT in its
   excerpt. The tagged sibling plus the legend sent the model to `get_diff`, and the
   aligned diff showed the insertion. Provenance's effect was to make the model
   check, and the check produced the finding.
3. The draws inverted the clusters again (10/10 for the arm that failed the
   endpoint, 8/1/0 for the arm that delivered it) — §6.1 stands.
4. What marking does not fix: name-level false newness (the GLM claim returned under
   marking and was caught by the audit) and the `breaking` over-label class.

Cumulative experiment spend including these arms and the issue-06 probes: ~$37.8.

---

## Addendum 2 (2026-09-19, issue 13): the confirm, and the flip

The prescription in §7 was executed: a fresh n=18 full-page seeded baseline for the
stored #6 → #7 v2 findings (**15/3/0; pooled full-page draw row 79%, 76% weighted** —
the earlier "1 of 4" was the suspicion-selected subset, as §6.1 predicted), then one
boost run on that pair (`2+r`, $4.85, 62 findings): **17/1/0 = 94%** (re-graded
2026-09-20 to **15/3/0 = 83%** — Addendum 3), the original partly
being the DENY plain-noun false-newness class on both pairs — outside every mechanism
the boost touches. Pooled boost draws across both pairs: 27/28 true, against the
baseline's 22/29.

**Adopted: PROMPT_VERSION 3 = the v2 text plus boosted input, now the default**, with
the version semantics written beside the constant (rule-10 explicitly excluded;
`CLASSIFY_VERSION` 1 → 2 in the same change; `--no-boost-restrictions` records `3-r`).
Honest residuals, on the record: the confirm wrote 62 findings vs the baseline's 79 and
left two needle pages uncited (including the verified-true Kimi-retirement control) —
variance vs mechanism unresolved at n=1, watched by the standing needle checks; and the
`breaking` sample-swap over-label recurred once (prompt-side class). The 547-signature
census (issue 04's follow-up): false "already documented/stated/existed" claims occur
only under the three unadopted visibility-without-provenance arms, zero under v2, the
boost, the quote rule, and marking. The second-grader check remains open for Doug
(suggested rows are in issue 13). Cumulative experiment spend: **~$42.7**.

## Addendum 3 (2026-09-20): the second-grader pass, and what it cost the headline

Doug delegated the re-grade back; it ran as a targeted second pass by the **same
model after context compaction** — each of the six suggested rows re-verified from
the blobs *before* the recorded verdict was read. Blind-ish, not independent; the
grader-built-the-arms bias is mitigated, not discharged.

| row | arm | recorded | re-grade | note |
|---|---|---|---|---|
| 333 | 5→6 `2+r` | true | **confirmed** | the 18-LTS→19 requirement line is a verbatim before/after |
| 351 | 5→6 `2+r` | true | **confirmed** | all three models absent at #5; limits row verbatim |
| 305 | 5→6 `2+r` | true | **confirmed** | `clear_at` genuinely new; cache/thinking mechanics are the page's own words |
| 763 | 6→7 `2+r` | partly | **confirmed** | same split: metastore half true, DENY false-newness |
| 736 | 6→7 `2+r` | true | **DOWNGRADED partly** | the after page itself keeps `Needed: [...]` on delete endpoints — the universal claim is over-broad |
| 785 | 6→7 `2+r` | true | **DOWNGRADED partly** | USE CONNECTION clause verbatim pre-existing at #6; folded in without the 'restate' marker the finding uses elsewhere |

Both downgrades share one shape — the first pass verified the quoted change and
stopped, missing contradicting material on the same page — which is exactly the
failure the box was designed to catch. Ledger updated (notes carry both passes):
the confirm arm reads **15/3/0 = 83%**, and the adoption headline "94% vs 79%"
is retired in favour of **83% vs 79%**. Two caveats, cutting opposite ways: the
six rows were suspicion-selected (worst-first — the downgrades don't extrapolate
to the arm), and the baseline's 19 grades were *not* re-graded (its 79% carries
the same first-pass leniency risk). The adoption stands on the replicated
direction and consistent error clusters, not on the headline. Spend: $0.