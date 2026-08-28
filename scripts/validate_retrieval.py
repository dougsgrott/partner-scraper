"""Can the corpus answer the questions it exists to answer? See docs/validation-plan.md §4.

Structural checks say the files are well formed; this says whether the material is
actually *there*. Retrieval is plain BM25 over the corpus — no model, no tokens — so the
result is reproducible, free, and measures the corpus rather than an embedding stack.

A miss is a finding either way: a weak retrieval hit means the page exists but is hard to
surface; no hit at all usually means a genuine coverage gap.

Examples:
    uv run python scripts/validate_retrieval.py
    uv run python scripts/validate_retrieval.py --k 10 --show-misses
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

from scraper.store import writer
from scraper.validate.report import Report, failed, passed, warned

TOKEN = re.compile(r"[a-z0-9]+")
# Indexing the whole body is unnecessary for a smoke test and slow; a page's identity
# lives in its title, headings, and opening prose.
INDEX_CHARS = 4000


def tokenise(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


class BM25:
    """Textbook BM25 over the corpus. Small enough to keep in memory, simple enough to trust."""

    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = docs
        self.freqs = [Counter(doc) for doc in docs]
        self.lengths = [len(doc) for doc in docs]
        self.avg_len = sum(self.lengths) / len(docs) if docs else 0.0
        self.df: Counter = Counter()
        for freq in self.freqs:
            self.df.update(freq.keys())
        self.n = len(docs)

    def idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def top(self, query: str, k: int) -> list[tuple[float, int]]:
        terms = tokenise(query)
        scores = []
        for i, freq in enumerate(self.freqs):
            score = 0.0
            for term in terms:
                tf = freq.get(term, 0)
                if not tf:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * self.lengths[i] / self.avg_len)
                score += self.idf(term) * tf * (self.k1 + 1) / denom
            if score:
                scores.append((score, i))
        return sorted(scores, reverse=True)[:k]


def build(data_dir: str) -> tuple[BM25, list[dict]]:
    docs, meta = [], []
    for path in sorted(Path(data_dir).rglob("*.md")):
        front, body = writer.parse(path)
        headings = " ".join(re.findall(r"^#{1,3} (.+)$", body, re.MULTILINE))
        text = " ".join([str(front.get("title", "")), str(front.get("description") or ""),
                         headings, body[:INDEX_CHARS]])
        docs.append(tokenise(text))
        meta.append({"url": str(front.get("source_url")), "title": front.get("title"),
                     "path": str(path)})
    return BM25(docs), meta


def main() -> None:
    ap = argparse.ArgumentParser(description="Retrieval smoke test over the corpus.")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--questions", default="docs/validation-questions.yaml")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--show-misses", action="store_true")
    ap.add_argument("--report-dir", default="state/validation")
    args = ap.parse_args()

    questions = yaml.safe_load(Path(args.questions).read_text(encoding="utf-8"))["questions"]
    index, meta = build(args.data_dir)

    hits_at_1 = hits_at_k = 0
    misses, weak = [], []
    for item in questions:
        results = index.top(item["q"], args.k)
        urls = [meta[i]["url"] for _, i in results]
        matched = [rank for rank, url in enumerate(urls)
                   if any(exp in url for exp in item["expects"])]
        if matched and matched[0] == 0:
            hits_at_1 += 1
            hits_at_k += 1
        elif matched:
            hits_at_k += 1
            weak.append(f"{item['q']}  -> rank {matched[0] + 1}: {urls[matched[0]]}")
        else:
            misses.append(f"{item['q']}  -> best: {urls[0] if urls else '(nothing)'}")

    total = len(questions)
    report = Report()
    check = passed if not misses else warned if len(misses) <= total * 0.25 else failed
    report.add("usefulness", check(
        "retrieval_question_set",
        f"hit@1 {hits_at_1}/{total} ({hits_at_1 / total:.0%}), "
        f"hit@{args.k} {hits_at_k}/{total} ({hits_at_k / total:.0%})",
        count=len(misses), total=total, samples=misses[:8],
        detail={"hit_at_1": hits_at_1, f"hit_at_{args.k}": hits_at_k, "questions": total},
    ))

    sizes = sorted(len(" ".join(doc)) for doc in index.docs)
    over = sum(1 for path in Path(args.data_dir).rglob("*.md")
               if path.stat().st_size > 200_000)
    report.add("usefulness", passed(
        "chunking_profile",
        f"median indexed page {sizes[len(sizes) // 2]:,} chars; "
        f"{over} file(s) over 200 KB will need splitting before embedding",
        total=len(sizes), detail={"over_200kb": over}))

    print(report.render())
    if args.show_misses and weak:
        print("\nfound, but not first:")
        for line in weak:
            print("   " + line)
    path = report.write(args.report_dir)
    print(f"\nreport: {path}")
    sys.exit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
