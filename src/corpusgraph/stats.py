"""Content-strategy statistics — item 25: which areas are dense, thin, stale, or orphaned.

The catalogue asks "which areas are dense, which are thin, and where differentiated
partner content would land." Page counts alone cannot answer that, and this is where
`lessons-learned.md` §18's warning bites hardest: a corpus holding a 4.77 MB page and a
300-byte page has no meaningful average anything. So every rollup carries a median rather
than a mean, and pairs its size with its centrality — `sql` has 1,183 pages at a median of
2,115 characters, which is a reference index, while `release-notes` has 238 at 10,160,
which is prose. Those are opposite content-strategy situations and one column cannot tell
them apart.

The rollups are computed from the node table a build already wrote, so they cost nothing
and cannot disagree with the ranking they sit beside.
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field


@dataclass
class GroupStat:
    """One `(company, category)` or one breadcrumb subtree."""

    company: str
    key: str
    pages: int = 0
    median_chars: int = 0
    total_chars: int = 0
    median_pagerank: float = 0.0
    share_of_rank: float = 0.0        # what fraction of the corpus's PageRank it holds
    orphans: int = 0                  # pages nothing links to
    unreachable: int = 0              # pages no path from an entry page reaches
    stale_months: str | None = None   # newest `updated_date` in the group
    languages: list[str] = field(default_factory=list)

    @property
    def rank_per_page(self) -> float:
        """Centrality density. High means every page here matters; low means bulk."""
        return self.share_of_rank / self.pages if self.pages else 0.0


def by_category(nodes: list[dict]) -> list[GroupStat]:
    """Per `(company, category)`, densest first."""
    return _rollup(nodes, lambda n: [(n.get("company") or "?", n.get("category") or "?")])


def by_breadcrumb(nodes: list[dict], *, depth: int = 1) -> list[GroupStat]:
    """Per breadcrumb subtree at `depth`. Databricks only — Anthropic has no trails.

    Pages without breadcrumbs are grouped under `(no breadcrumbs)` rather than dropped:
    `lessons-learned.md` §14 — absent is a fact, and a rollup that silently omits 788
    pages is a rollup that lies about its own coverage.
    """
    def key(node):
        trail = node.get("breadcrumbs") or []
        company = node.get("company") or "?"
        if not trail:
            return [(company, "(no breadcrumbs)")]
        return [(company, " > ".join(trail[:depth]))]
    return _rollup(nodes, key)


def _rollup(nodes: list[dict], key_fn) -> list[GroupStat]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for node in nodes:
        for key in key_fn(node):
            groups[key].append(node)
    total_rank = sum(n.get("pagerank") or 0.0 for n in nodes) or 1.0

    out = []
    for (company, key), members in groups.items():
        sizes = sorted(n.get("body_chars") or 0 for n in members)
        ranks = sorted(n.get("pagerank") or 0.0 for n in members)
        languages: Counter = Counter()
        for node in members:
            for language in node.get("code_languages") or []:
                languages[language] += 1
        dates = [n["updated_date"] for n in members if n.get("updated_date")]
        out.append(GroupStat(
            company=company,
            key=key,
            pages=len(members),
            median_chars=int(statistics.median(sizes)) if sizes else 0,
            total_chars=sum(sizes),
            median_pagerank=statistics.median(ranks) if ranks else 0.0,
            share_of_rank=sum(n.get("pagerank") or 0.0 for n in members) / total_rank,
            orphans=sum(1 for n in members if not n.get("in_pages")),
            unreachable=sum(1 for n in members if n.get("depth") is None),
            stale_months=max(dates)[:7] if dates else None,
            languages=[lang for lang, _ in languages.most_common(4)],
        ))
    return sorted(out, key=lambda g: -g.pages)


def size_profile(nodes: list[dict]) -> dict[str, int]:
    """Median, p90 and the tail that a naive chunker chokes on.

    `kb-application.md` flags ten pages over 500 KB as a retrieval hazard; this keeps that
    number current instead of quoting a measurement whose date nobody remembers.
    """
    sizes = sorted(n.get("body_chars") or 0 for n in nodes)
    if not sizes:
        return {"pages": 0}
    return {
        "pages": len(sizes),
        "median": sizes[len(sizes) // 2],
        "p90": sizes[int(0.9 * (len(sizes) - 1))],
        "p99": sizes[int(0.99 * (len(sizes) - 1))],
        "max": sizes[-1],
        "over_500kb": sum(1 for s in sizes if s > 500_000),
    }


def recency(nodes: list[dict]) -> list[tuple[str, int]]:
    """Pages per `updated_date` month, newest first. `unknown` is a bucket, not a gap."""
    months: Counter = Counter(
        (n["updated_date"][:7] if n.get("updated_date") else "unknown") for n in nodes)
    known = sorted((m for m in months if m != "unknown"), reverse=True)
    return [(m, months[m]) for m in known] + (
        [("unknown", months["unknown"])] if "unknown" in months else [])


def orphans(nodes: list[dict], *, limit: int = 20) -> list[dict]:
    """Pages nothing in the corpus links to, largest first.

    Not a defect list. A page can be orphaned because the vendor only reaches it from a
    sidebar the Markdown does not carry — but a *large* orphan is either a real gap in the
    vendor's own navigation or a page our extractor stripped the links out of, and both
    are worth someone looking at.
    """
    return sorted((n for n in nodes if not n.get("in_pages")),
                  key=lambda n: -(n.get("body_chars") or 0))[:limit]
