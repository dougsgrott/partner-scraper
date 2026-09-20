# 09 — One fetch path, always archived

**Status:** done (2026-09-19), uncommitted — **option A with the decision extracted**:
both entry points route through `generations.archive_after`, tested per entry point.
See *Done* · **Kind:** code · **Effort:** ~1 h
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

**Timing (2026-09-19):** the cadence is weekly and the last archived generation is
`20260918T184955` — the next refresh is due within days. Land this before it runs.

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

## Done (2026-09-19)

**Option A, with the con answered by extraction.** The "does this run get archived?"
decision is now `generations.archive_after(summary, *, label, raw_dir, archive_dir)`:
archive unless the run was dry or wrote nothing (`ok == 0` — an all-304 refresh or an
all-error run leaves `raw/` exactly as the last generation saw it, so there is nothing
new to lose). Both callers delegate:

- `scripts/fetch.py` — behaviour unchanged, wiring only: `--no-archive` early-exits,
  everything else goes through `archive_after`; the "nothing fetched — no generation
  archived" message and the dry-run silence are preserved.
- `changes.py run --fetch` — the trap closed: `cmd_run`'s fetch step is now
  `_fetch_and_archive`, which runs the refresh and archives through the same policy;
  `run` grew `--no-archive` for the explicit opt-out. The docstring of `archive_after`
  tells a third caller to call it next rather than re-decide — the layering of option
  B's choke point, without putting retention policy inside the fetch layer.

**One deviation from the sketch:** `run` did not get a generation `--label`. `run
--label` already names the *snapshot*, and one flag naming two different objects on one
command is a worse trap than the one being fixed; the generation takes the timestamp
default, and `fetch.py` remains the tool for deliberately-labelled generations.

Docs: `docs/raw-archive.md` usage now shows both commands and names the shared
decision; the trap note in `docs/session-2026-09-18-lessons.md` §2 is marked closed
with the converged behaviour (and the open-items line annotated), rather than deleted —
it is a session record.

Tests (`tests/test_fetch_entrypoints.py`): the policy against real tmp directories
(success ⇒ generation with manifest and the run stamp; dry run ⇒ nothing; `ok == 0` ⇒
nothing), then each entry point's wiring with `run_fetch` stubbed — `_fetch_and_archive`
archives by default and honours `archive=False`; `scripts/fetch.py` (loaded by file
path; `scripts/` is not importable) archives by default and honours `--no-archive`.
The existing `test_generations.py` suite is untouched and green.

## Acceptance criteria

- [x] It is impossible to fetch through any in-repo entry point without archiving, other
      than by passing an explicit `--no-archive` — both entry points (the only
      `run_fetch` callers outside tests) route through `archive_after`
- [x] The trap note in `docs/session-2026-09-18-lessons.md` §2 and the workflow note in
      `docs/raw-archive.md` updated to describe the converged behaviour
- [x] A test per surviving entry point: successful fetch ⇒ a new generation exists with
      a manifest; `--no-archive` ⇒ it does not

## Tests

- `changes.py run --fetch` (if it survives) leaves a generation in `raw-archive/` —
  `test_changes_run_fetch_archives`
- a dry run archives nothing — `test_a_dry_run_archives_nothing`
- a failed fetch archives nothing (the existing `fetch.py` semantics, preserved) —
  `test_a_fetch_that_wrote_nothing_archives_nothing`
