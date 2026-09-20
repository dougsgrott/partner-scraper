"""Can a model find the needles in a whole run? See docs/changefeed-phase-2.md.

The phase-2 decision rests on one empirical claim: a run of ~1,300 changes compresses to
~105k tokens, so it can go to a single session instead of being batched or pre-filtered.
The risk that buys is **recall** — a long, flat list of broadly similar lines is exactly the
shape where a model drops things, and this feed's value depends on not dropping the one
deprecation that matters.

This probe measures that risk directly, before any agent code exists, so a bad result
changes the architecture instead of being discovered after it is built.

Two modes, deliberately not the same test:

* ``locate`` — ask for each needle by description. Measures raw retrieval from the
  haystack. **This is the easy test**: being told what to look for is much easier than
  noticing it unprompted, so a pass here does not mean the digest will work. A *failure*
  here, though, is decisive — it means no prompt will fix it and the hierarchical fallback
  is mandatory.
* ``digest`` — ask for the most important changes, with no hint, then check which needles
  appear. The test that counts, and the one closest to what phase 2 actually does.

**This spends real money and runs against the Claude Code CLI's credentials.** `--dry-run`
shows exactly what would be sent, and its size, without calling anything.

Needle files are per pair: the default describes #1 -> #2, and each graded pair since has
its own (`docs/changefeed-needles-<BBBB>..<AAAA>.yaml`, seeded from the graded misses —
see issue/accuracy/01-verdict-ledger.md). Passing one runs against its own pair
automatically; pointing it at any other pair is refused rather than reported as misses.

Examples:
    uv run python scripts/probe_recall.py --dry-run
    uv run python scripts/probe_recall.py --mode locate
    uv run python scripts/probe_recall.py --mode digest --top 30
    uv run python scripts/probe_recall.py --needles docs/changefeed-needles-0005..0006.yaml --mode locate
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from changefeed import diff
from changefeed.db import ChangeDB
from changefeed.digest import compress_run
from changefeed.digest.compress import CHARS_PER_TOKEN

MODEL = "claude-opus-5"
DEFAULT_NEEDLES = Path("docs/changefeed-needles.yaml")

LOCATE_PROMPT = """Below is a list of documentation changes, one per line.

Find the single change that matches this description:

    {what}

Reply with only the path, exactly as it appears in the list. If nothing matches, reply NONE.

{run}"""

DIGEST_PROMPT = """Below is a list of documentation changes from two vendors, one per line,
ordered by a heuristic severity score.

You are writing a weekly digest for engineers who build on both vendors. Identify the {top}
changes most likely to break something, remove a capability, or change what is supported.

Reply with one path per line, exactly as it appears in the list, and nothing else.

{run}"""


def load_run(args, expected: dict | None) -> str:
    """The compressed run the needles were written against.

    Defaults to the pair named in the needle file rather than the newest snapshots. A
    needle set is only meaningful for the run it was read from; pointed at any other pair
    it reports every needle missing, which looks like total failure and is not.
    """
    before_ref = args.before or (expected or {}).get("before")
    after_ref = args.after or (expected or {}).get("after")

    with ChangeDB(args.changes_db) if args.changes_db else ChangeDB() as db:
        pair = ((db.resolve(before_ref), db.resolve(after_ref)) if before_ref
                else db.last_two())
        if not pair or pair[0] is None or pair[1] is None:
            print("need two snapshots to compare", file=sys.stderr)
            raise SystemExit(1)
        if expected and (pair[0].id, pair[1].id) != (expected["before"], expected["after"]):
            print(f"refusing to run: these needles describe snapshots "
                  f"#{expected['before']} -> #{expected['after']}, not "
                  f"#{pair[0].id} -> #{pair[1].id}. A needle set is only meaningful for "
                  f"the run it was read from.", file=sys.stderr)
            raise SystemExit(2)
        result = diff.compare(pair[0], pair[1], db=db, blob_dir=args.blob_dir)
    return compress_run(result, blob_dir=args.blob_dir,
                        collapse_terse=args.collapse_terse,
                        merge_duplicates=args.merge_duplicates).render()


async def ask(prompt: str) -> str:
    """One stateless question. No tools — this measures reading, not agency.

    Text is taken from `ResultMessage.result` first and only falls back to walking
    `AssistantMessage` blocks. Both paths use `isinstance`, not duck-typing: `TextBlock` in
    claude-agent-sdk 0.2.148 carries **no** `type` attribute, so an earlier
    ``getattr(block, "type", None) == "text"`` check silently matched nothing and discarded
    a perfectly good answer — a 105k-token call that returned zero lines and looked like a
    model failure.
    """
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    options = ClaudeAgentOptions(
        model=MODEL,
        # No built-in tools and no inherited settings: the probe must measure the model's
        # reading of the prompt, not its ability to go and look something up.
        tools=[],
        setting_sources=[],
    )
    blocks: list[str] = []
    result: str | None = None
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            blocks += [b.text for b in message.content if isinstance(b, TextBlock)]
        elif isinstance(message, ResultMessage) and message.subtype == "success":
            result = message.result
            # The only free source of REAL token counts this project has: the estimator
            # (`CHARS_PER_TOKEN = 3.5`) had never been checked against an actual count
            # until issue/accuracy/06 read it off a probe run here. Includes the
            # harness's own overhead, so it upper-bounds the payload.
            if message.usage:
                u = message.usage
                actual = (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                          + u.get("cache_read_input_tokens", 0))
                print(f"  actual input tokens {actual:,} "
                      f"(fresh {u.get('input_tokens', 0):,}, cache-write "
                      f"{u.get('cache_creation_input_tokens', 0):,}, cache-read "
                      f"{u.get('cache_read_input_tokens', 0):,}) vs estimate "
                      f"~{int(len(prompt) / CHARS_PER_TOKEN):,}", file=sys.stderr)
    answer = result or "\n".join(blocks)
    if not answer.strip():
        print("  ! the model returned no text — this is a probe failure, not a recall "
              "result", file=sys.stderr)
    return answer


def known_paths(run_text: str) -> set[str]:
    """Every path the run actually contains — the set a valid answer must draw from."""
    paths = set()
    for line in run_text.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[1].isupper():
            paths.add(parts[2])
    return paths


def validate_paths(answer: str, known: set[str]) -> tuple[list[str], list[str]]:
    """Split an answer's paths into `(real, invented)`.

    A schema can guarantee a finding is well-formed; only a membership test against the
    input can show it is about something that actually changed. Nothing upstream of this
    stops a model naming a plausible path that was never in the run, and a digest that
    quietly cites a page nobody touched is worse than one that omits it.
    """
    real, invented = [], []
    for line in answer.splitlines():
        if not line.strip():
            continue
        # Containment, not token equality. A model asked for "the path" may reasonably
        # answer `api/beta-headers`, `anthropic/api/beta-headers`, or echo the whole
        # record prefix — all three name the same real page. An exact first-token match
        # called every one of those a hallucination and reported 0 real of 50, which was
        # the parser being wrong about a correct answer, not the model inventing pages.
        hits = [path for path in known if path in line]
        if hits:
            real.append(max(hits, key=len))
        else:
            invented.append(line.strip()[:80])
    return real, invented


def accepts(needle: dict) -> list[str]:
    """The substrings that count as finding this needle.

    A list, because a change can legitimately be named at more than one level. Asked which
    change said the IP address functions left Beta, the model named the *overview* page
    rather than one of the six function pages — a better answer than the needle expected,
    and scored a miss by a single-substring match.
    """
    value = needle["url_contains"]
    return [value] if isinstance(value, str) else list(value)


def matched(answer: str, needle: dict) -> bool:
    lowered = answer.lower()
    return any(option.lower() in lowered for option in accepts(needle))


def score(answer: str, needles: list[dict]) -> list[tuple[dict, bool]]:
    return [(n, matched(answer, n)) for n in needles]


def report(rows: list[tuple[dict, bool]]) -> int:
    hits = sum(1 for _, ok in rows if ok)
    print(f"\n  recall {hits}/{len(rows)}")
    for needle, ok in sorted(rows, key=lambda r: r[0]["rank"]):
        print(f"   {'HIT ' if ok else 'MISS'} rank {needle['rank']:>5}  "
              f"{accepts(needle)[0]}")
        if not ok:
            print(f"          {needle['what']}")
    return 0 if hits == len(rows) else 1


def interpret(rows: list[tuple[dict, bool]], mode: str) -> None:
    """Say what a miss does and does not prove. The two modes cannot be read alike.

    In `digest` mode the model is asked for a fixed number of the most important changes,
    so a miss is ambiguous: it may not have seen the change, or it may have seen it and
    judged others more important. Reporting that as a recall failure would be wrong.
    Only `locate`, which names the change and asks the model to find it, isolates recall.
    """
    missed = [n for n, ok in rows if not ok]
    if not missed:
        return
    if mode == "digest":
        print("\n  A miss here is not yet a recall failure: the model was asked for a "
              "fixed number of changes, so it may have seen these and ranked others "
              "above them. Re-run the misses in `locate` mode to tell the two apart:")
        print(f"    uv run python scripts/probe_recall.py --mode locate --rank "
              f"{','.join(str(n['rank']) for n in missed)}")
    else:
        top = [n for n in missed if n["rank"] <= 10]
        if top:
            print("\n  ! a needle in the top 10 by severity was not found when the model "
                  "was told exactly what to look for. That is a decisive long-context "
                  "failure, not a tuning problem — see the fallback in "
                  "docs/changefeed-phase-2.md.")


async def run(args) -> int:
    spec = yaml.safe_load(Path(args.needles).read_text(encoding="utf-8"))
    needles = spec["needles"]
    if args.rank:
        wanted = {int(r) for r in args.rank.split(",")}
        needles = [n for n in needles if n["rank"] in wanted]
        if not needles:
            print(f"no needles with rank in {sorted(wanted)}", file=sys.stderr)
            return 1
    run_text = load_run(args, spec.get("snapshots"))
    print(f"run: {len(run_text.splitlines())} lines, {len(run_text):,} chars "
          f"(~{int(len(run_text) / CHARS_PER_TOKEN) // 1000}k tokens, approx)")
    print(f"needles: {len(needles)}  ranks {sorted(n['rank'] for n in needles)}")

    if args.dry_run:
        calls = len(needles) if args.mode == "locate" else 1
        print(f"\ndry run — would make {calls} call(s) to {MODEL}, "
              f"~{calls * int(len(run_text) / CHARS_PER_TOKEN) // 1000}k input tokens total. Nothing sent.")
        return 0

    if args.mode == "locate":
        rows = []
        for needle in needles:
            answer = await ask(LOCATE_PROMPT.format(what=needle["what"], run=run_text))
            found = matched(answer, needle)
            rows.append((needle, found))
            print(f"  {'HIT ' if found else 'MISS'} {accepts(needle)[0]}")
            if not found:
                # Print what came back. A miss that is never read is a guess about why.
                print(f"       model said: {answer.strip()[:200]!r}")
        code = report(rows)
        interpret(rows, args.mode)
        return code

    answer = await ask(DIGEST_PROMPT.format(top=args.top, run=run_text))
    print(f"\n--- model returned {len(answer.splitlines())} lines ---")

    real, invented = validate_paths(answer, known_paths(run_text))
    print(f"  paths: {len(real)} real, {len(invented)} not in the run")
    for path in invented[:5]:
        print(f"    ! invented: {path}")
    if len(set(real)) != len(real):
        print(f"    ! {len(real) - len(set(real))} duplicate path(s) returned")

    if args.save:
        out = Path(args.save)
        out.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        (out / f"digest-{stamp}.txt").write_text(answer, encoding="utf-8")
        print(f"  saved  {out / f'digest-{stamp}.txt'}")
    rows = score(answer, needles)
    code = report(rows)
    interpret(rows, args.mode)
    return code


def main() -> None:
    ap = argparse.ArgumentParser(description="Measure digest recall over a whole run.")
    ap.add_argument("--mode", choices=("locate", "digest"), default="digest")
    ap.add_argument("--top", type=int, default=30, help="digest mode: how many to ask for")
    ap.add_argument("--needles", default=str(DEFAULT_NEEDLES))
    ap.add_argument("--rank", help="only these needle ranks, comma-separated — for "
                                   "re-testing digest-mode misses in locate mode")
    ap.add_argument("before", nargs="?")
    ap.add_argument("after", nargs="?")
    ap.add_argument("--changes-db")
    ap.add_argument("--blob-dir")
    ap.add_argument("--save", help="directory to write the raw answer to (use a scratch "
                                   "dir; these are experiment artifacts, not results)")
    ap.add_argument("--collapse-terse", action="store_true",
                    help="probe the collapsed rendering (issue 06)")
    ap.add_argument("--merge-duplicates", action="store_true",
                    help="probe the duplicate-merged rendering (issue 06)")
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would be sent, and its size, without calling anything")
    args = ap.parse_args()
    raise SystemExit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
