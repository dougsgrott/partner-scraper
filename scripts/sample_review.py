"""Draw a stratified sample for human review, and score the filled scorecard.

The automated checks in `scripts/validate.py` prove the corpus is *structurally* sound.
They cannot tell you it reads correctly — and every defect this project has had was found
by a person reading a page (docs/lessons-learned.md §1). This draws a reproducible sample
and gives it to you as a checklist.

Examples:
    uv run python scripts/sample_review.py --n 50            # write the scorecard
    uv run python scripts/sample_review.py --score docs/validation-scorecard.md
"""

from __future__ import annotations

import argparse
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from scraper.store import writer

DIMENSIONS = ("title", "complete", "code", "links", "metadata")
DEFAULT_OUT = Path("docs/validation-scorecard.md")

HEADER = """# Corpus review scorecard

{n} pages drawn from {total} by `scripts/sample_review.py --n {n} --seed {seed}`, stratified
by company, category, and size decile. Re-drawing with the same seed gives the same sample.

**How to score.** Open the corpus file and its live URL side by side, then mark each
column `y` / `n` / `?`:

| Column | Question |
|---|---|
| `title` | Is the title right, and does the page open by naming itself? |
| `complete` | Is the whole page here — no section silently missing, nothing added? |
| `code` | Are code blocks intact: fenced, line breaks preserved, runnable as shown? |
| `links` | Do links point somewhere real, and are they absolute? |
| `metadata` | Are category, dates, description, and tags right for this page? |

Leave `notes` for anything a column cannot capture. A single `n` anywhere is worth
investigating — this project's worst defects were corpus-wide and looked fine in aggregate.

Score it with: `uv run python scripts/sample_review.py --score {out}`

| # | page | url | title | complete | code | links | metadata | notes |
|---|---|---|---|---|---|---|---|---|
"""


def strata(pages: list[tuple[Path, dict, int]]) -> dict[tuple, list]:
    """Group by company, category, and size decile."""
    sizes = sorted(size for _, _, size in pages)
    cuts = [sizes[min(len(sizes) - 1, int(len(sizes) * i / 10))] for i in range(1, 10)]

    def decile(size: int) -> int:
        return sum(1 for cut in cuts if size > cut)

    grouped = defaultdict(list)
    for path, front, size in pages:
        grouped[(front.get("company"), front.get("category"), decile(size))].append((path, front))
    return grouped


def draw(data_dir: str, n: int, seed: int) -> list[tuple[Path, dict]]:
    """A stratified sample: proportional by stratum, at least one from each company."""
    pages = []
    for path in sorted(Path(data_dir).rglob("*.md")):
        front, body = writer.parse(path)
        pages.append((path, front, len(body)))
    if not pages:
        return []

    grouped = strata(pages)
    rng = random.Random(seed)
    quota = {key: max(1, math.floor(n * len(rows) / len(pages))) for key, rows in grouped.items()}

    picked: list[tuple[Path, dict]] = []
    for key in sorted(grouped, key=lambda k: (-len(grouped[k]), str(k))):
        rows = grouped[key]
        picked.extend(rng.sample(rows, min(quota[key], len(rows))))
    rng.shuffle(picked)

    if len(picked) > n:                       # trim, but keep every company represented
        seen: Counter = Counter()
        trimmed = []
        for path, front in picked:
            company = front.get("company")
            if len(trimmed) < n or seen[company] == 0:
                trimmed.append((path, front))
                seen[company] += 1
        picked = trimmed[:n]
    return picked


def write_scorecard(rows: list[tuple[Path, dict]], out: Path, total: int, seed: int) -> None:
    # `rstrip` matters: the header template ends with the separator row and a newline, and
    # joining on "\n" would insert a blank line after it — which closes the table, leaving
    # every data row to render as one run-on paragraph.
    lines = [HEADER.format(n=len(rows), total=total, seed=seed, out=out).rstrip("\n")]
    for i, (path, front) in enumerate(rows, 1):
        lines.append(f"| {i} | `{path}` | {front.get('source_url')} |  |  |  |  |  |  |")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


ROW = re.compile(r"^\|\s*(\d+)\s*\|(.+)\|\s*$")


def score(path: Path) -> int:
    """Summarise a filled scorecard. Returns a process exit code."""
    marks = {dim: Counter() for dim in DIMENSIONS}
    rows = failures = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ROW.match(line)
        if not match:
            continue
        cells = [c.strip().lower() for c in match.group(2).split("|")]
        if len(cells) < 2 + len(DIMENSIONS):
            continue
        rows += 1
        verdicts = cells[2:2 + len(DIMENSIONS)]
        for dim, verdict in zip(DIMENSIONS, verdicts, strict=False):
            marks[dim][verdict or "unscored"] += 1
        if "n" in verdicts:
            failures += 1

    if not rows:
        print(f"no scored rows found in {path}")
        return 1

    print(f"{rows} pages reviewed\n")
    for dim in DIMENSIONS:
        counts = marks[dim]
        scored = counts["y"] + counts["n"] + counts["?"]
        rate = f"{counts['y'] / scored:.0%}" if scored else "—"
        print(f"  {dim:<10} pass {counts['y']:>3}   fail {counts['n']:>3}   "
              f"unsure {counts['?']:>3}   unscored {counts['unscored']:>3}   ({rate})")

    clean = rows - failures
    margin = 1.96 * math.sqrt((clean / rows) * (1 - clean / rows) / rows) if rows else 0
    print(f"\n  pages with no failure: {clean}/{rows} = {clean / rows:.0%} "
          f"(95% CI ±{margin:.0%})")
    if marks[DIMENSIONS[0]]["unscored"]:
        print("  note: unscored rows are excluded from the rates above")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Stratified sample for human corpus review.")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--score", type=Path, metavar="SCORECARD",
                    help="summarise a filled-in scorecard instead of drawing a new sample")
    args = ap.parse_args()

    if args.score:
        raise SystemExit(score(args.score))

    total = sum(1 for _ in Path(args.data_dir).rglob("*.md"))
    rows = draw(args.data_dir, args.n, args.seed)
    write_scorecard(rows, args.out, total, args.seed)
    companies = Counter(front.get("company") for _, front in rows)
    print(f"{len(rows)} pages sampled from {total} -> {args.out}")
    print("  by company: " + ", ".join(f"{c} {n}" for c, n in companies.most_common()))


if __name__ == "__main__":
    main()
