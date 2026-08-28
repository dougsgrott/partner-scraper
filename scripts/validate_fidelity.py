"""CLI for fidelity checks: does each corpus file match its source? See docs/validation-plan.md.

The Anthropic comparison is exact, offline, and covers every page. The cookbook comparison
fetches the real notebooks from GitHub (small, rate-limited). Databricks has no ground
truth, so `--second-opinion` runs an independently-written extractor over the same bytes.

Examples:
    uv run python scripts/validate_fidelity.py                    # served-Markdown, all pages
    uv run python scripts/validate_fidelity.py --notebooks 15     # cookbook vs GitHub
    uv run python scripts/validate_fidelity.py --second-opinion 100
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time

from scraper.config import load_config
from scraper.validate import fidelity
from scraper.validate.report import Report, failed, passed, skipped, warned

logger = logging.getLogger("validate_fidelity")


def notebook_check(data_dir: str, sample: int, delay: float = 1.0):
    """Compare a sample of cookbook pages against the notebooks they were generated from."""
    import httpx

    from scraper.store import writer

    pages = []
    for path in sorted(__import__("pathlib").Path(data_dir).rglob("*.md")):
        front, body = writer.parse(path)
        if front.get("source_id") == "anthropic-cookbook" and front.get("source_file_url"):
            pages.append((front, body))
    if not pages:
        return skipped("fidelity_notebooks", "no cookbook pages with a source_file_url")

    picked = random.Random(0).sample(pages, min(sample, len(pages)))
    results, errors = [], []
    with httpx.Client(follow_redirects=True, timeout=30,
                      headers={"User-Agent": "indicium-docs-scraper/0.2"}) as client:
        for front, body in picked:
            url = fidelity.raw_github_url(str(front["source_file_url"]))
            try:
                response = client.get(url)
                response.raise_for_status()
                notebook = response.json()
            except (httpx.HTTPError, ValueError) as exc:  # a missing notebook is not our defect
                errors.append(f"{url}: {type(exc).__name__}")
                time.sleep(delay)
                continue
            comparison = fidelity.compare_notebook(body, notebook)
            comparison.url = str(front["source_url"])
            results.append(comparison)
            time.sleep(delay)

    if not results:
        return skipped("fidelity_notebooks", f"no notebooks fetched ({len(errors)} errors)")
    bad = [r for r in results if not r.ok]
    cells = sum(r.detail["code_cells"] for r in results)
    matched = sum(r.detail["code_matched"] for r in results)
    summary = (f"{matched}/{cells} code cells recovered across {len(results)} notebooks"
               + (f"; {len(errors)} unfetchable" if errors else ""))
    if bad:
        return failed("fidelity_notebooks", summary, count=len(bad), total=len(results),
                      samples=[f"{r.url}: {r.reason}" for r in bad[:5]])
    return passed("fidelity_notebooks", summary, total=len(results))


def second_opinion(data_dir: str, fetch_db: str, sample: int, threshold: float = 0.8):
    """Independent extraction of the same bytes; disagreement marks where to look."""
    try:
        import trafilatura
    except ImportError:
        return skipped("fidelity_second_opinion", "trafilatura not installed (uv add --dev trafilatura)")

    import pathlib
    import sqlite3

    from scraper.fetch import rawstore
    from scraper.store import writer

    conn = sqlite3.connect(fetch_db)
    conn.row_factory = sqlite3.Row
    archived = {r["url"]: r["raw_path"] for r in conn.execute(
        "SELECT url, raw_path FROM fetches WHERE source_id = 'databricks-docs'")}
    conn.close()

    pages = []
    for path in sorted(pathlib.Path(data_dir).rglob("*.md")):
        front, body = writer.parse(path)
        if front.get("source_id") == "databricks-docs" and front.get("source_url") in archived:
            pages.append((front, body))
    if not pages:
        return skipped("fidelity_second_opinion", "no databricks pages to compare")

    # Word-level, not line-level. The two extractors disagree about *formatting* by
    # design — trafilatura returns `/pyspark/reference/functions/user` as a single
    # run-on line with the code welded together, which no line of ours can match even
    # though our page contains every word of it, better structured. Only missing *words*
    # indicate dropped content.
    import re
    from collections import Counter

    word = re.compile(r"[a-z0-9]+")
    picked = random.Random(0).sample(pages, min(sample, len(pages)))
    thin = []
    for front, body in picked:
        html = rawstore.read(archived[front["source_url"]]).decode("utf-8", "replace")
        theirs = trafilatura.extract(html, include_tables=True, include_links=False) or ""
        their_words = Counter(word.findall(theirs.lower()))
        if sum(their_words.values()) < 50:
            continue
        our_words = Counter(word.findall(body.lower()))
        covered = sum(min(n, our_words.get(w, 0)) for w, n in their_words.items())
        recall = covered / sum(their_words.values())
        if recall < threshold:
            thin.append(f"{front['source_url']}: {recall:.0%} of the independent text's words present")

    summary = f"{len(picked)} pages compared against an independent extractor"
    if thin:
        return warned("fidelity_second_opinion",
                      f"{len(thin)} page(s) below {threshold:.0%} recall — inspect these",
                      count=len(thin), total=len(picked), samples=thin[:5])
    return passed("fidelity_second_opinion", summary + ", none below threshold", total=len(picked))


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare the corpus against its sources.")
    ap.add_argument("--config", default="config/sources.yaml")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--fetch-db", default="state/fetch.db")
    ap.add_argument("--source", default="anthropic-docs",
                    help="source whose served Markdown is the ground truth")
    ap.add_argument("--notebooks", type=int, default=0, metavar="N",
                    help="also compare N cookbook pages against their GitHub notebooks")
    ap.add_argument("--second-opinion", type=int, default=0, metavar="N",
                    help="also re-extract N databricks pages with trafilatura and compare")
    ap.add_argument("--report-dir", default="state/validation")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    load_config(args.config)

    started = time.monotonic()
    report = Report()
    report.add("fidelity", fidelity.check_served_markdown(args.fetch_db, args.data_dir, args.source))
    if args.notebooks:
        report.add("fidelity", notebook_check(args.data_dir, args.notebooks))
    if args.second_opinion:
        report.add("fidelity", second_opinion(args.data_dir, args.fetch_db, args.second_opinion))
    report.elapsed_s = time.monotonic() - started

    print(json.dumps(report.to_dict(), indent=2) if args.json else report.render())
    path = report.write(args.report_dir)
    if not args.json:
        print(f"\nreport: {path}")
    sys.exit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
