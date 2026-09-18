# 09 — One fetch path, always archived

**Status:** open (2026-09-18) · **Kind:** code · **Effort:** ~1 h
**Depends on:** nothing · **Blocks:** nothing — but see urgency below

## Problem

Two entry points perform the same fetch and disagree about archiving.
`scripts/fetch.py` archives a generation by default after every successful non-dry run;
`changes.py run --fetch` (the `--fetch` path in `src/changefeed/cli.py`) refreshes
through `run_fetch` directly and **does not archive**. The documented workflow routes
around it — run `fetch.py --refresh`, then `changes.py run` without `--fetch` — which
means the invariant "every generation is archived" is held up by everyone remembering a
doc.

Why this is first in the whole set despite being the smallest: **a missed archive is the
one unrecoverable failure here.** `raw/` is overwritten in place by the next fetch;
bytes that were never hard-linked into `raw-archive/` are gone, and with them the
regression data the raw archive exists to accumulate — the owner's stated reason for
choosing option A over the cheaper scheme. Every other issue in this set can wait a
window; this one loses data per occurrence. Nothing to measure, either — the standing
measure-first rule applies to design choices that hinge on a number, and this hinges on
none.

## Options

**A — archive in the `--fetch` path of `changes.py run`**, with the same default and
flags (`--no-archive`, `--label`) as `fetch.py`.

- *Pro:* both entry points converge on the same behaviour; smallest diff.
- *Con:* the default-and-flags logic now exists twice unless extracted; a third caller
  tomorrow re-opens the hole.

**B — archive inside `run_fetch` itself**, so every present and future caller gets it.

- *Pro:* single choke point; the invariant becomes structural instead of per-caller.
- *Con:* `run_fetch` is fetch-layer and archiving is retention policy — the layering
  argument against is real, and tests that exercise `run_fetch` would all need archive
  expectations or an off-switch, which reintroduces a smaller version of the same knob.

**C — remove `--fetch` from `changes.py run`.** The documented workflow is already two
commands; delete the trap instead of fixing it.

- *Pro:* the smallest possible surface — no second path exists to diverge.
- *Con:* breaks a documented invocation and the readiness-issue snippets that use it;
  loses the one-command convenience for a supervised run.

Any of the three is acceptable; what is not acceptable is the status quo, where the
safe behaviour is a matter of which script someone typed. Leaning A with the shared
logic extracted — C is cleaner but reaches into documented workflow for a convenience
question the owner may want to keep.

## Acceptance criteria

- [ ] It is impossible to fetch through any in-repo entry point without archiving, other
      than by passing an explicit `--no-archive`
- [ ] The trap note in `docs/session-2026-09-18-lessons.md` §2 and the workflow note in
      `docs/raw-archive.md` updated to describe the converged behaviour
- [ ] A test per surviving entry point: successful fetch ⇒ a new generation exists with
      a manifest; `--no-archive` ⇒ it does not

## Tests

- `changes.py run --fetch` (if it survives) leaves a generation in `raw-archive/`
- a dry run archives nothing
- a failed fetch archives nothing (the existing `fetch.py` semantics, preserved)
