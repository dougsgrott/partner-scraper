"""The internal link graph — the edge list the corpus never kept.

`scraper.validate.coverage.corpus_links()` counts link *targets* and throws the source
page away, which is all a coverage check needs and is why no graph algorithm can run on
it. This module keeps both ends.

Four things a naive edge builder gets wrong here, each one measured on 2026-08-30 against
the 6,564-file corpus, which yields 6,541 live pages and 39,872 edges (docs/graph.md):

1. **Image embeds are not citations.** `coverage.MD_LINK` matches `](url)`, which also
   matches the `![alt](url)` form. There are 2,327 of them. Counting an illustration as
   an edge inflates every hub that happens to carry screenshots.
2. **Anchor text is free and is thrown away.** Every one of the 39,872 edges carries some,
   and 66% of the 63,487 named link instances use a text that differs from the target
   page's own title — an alias vocabulary nothing else in this repo produces, obtained in
   the same regex pass.
3. **A link is not one link.** One page links `supported-models` 48 times; counting
   occurrences instead of pairs is what put that page third in the hot-spot table of
   `kb-application.md` when only 53 pages in the whole corpus reference it — it is 214th
   under PageRank. Both counts are kept, and `rank.py` uses the pair.
4. **The corpus is not the archive.** `classify_links` resolves against `fetch.db`, which
   holds URLs whose pages were never written (`duplicate`) or have since been deleted
   upstream (`gone`). A graph must resolve against pages that exist.

Nothing is silently dropped: every link instance the scanner sees lands in exactly one of
an internal edge, a `classify_links` bucket, or `skipped`, and `EdgeSet.reconcile()`
re-derives the total with a second, independent regex before a build is written.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from bisect import bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from scraper.config import AppConfig, load_config
from scraper.store import writer
from scraper.validate import coverage

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = "config/sources.yaml"
DEFAULT_INDEX_DB = Path("state/index.db")

# Deliberately wider than `coverage.MD_LINK`, which is `\]\((https?://[^)\s]+)\)`:
#
#   group 1  the "!" of an image embed, so it can be excluded rather than counted
#   group 2  anchor text — the alias vocabulary
#   group 3  the URL, optionally wrapped in <> and optionally followed by a "title"
#
# The wider shape recovers link instances `MD_LINK` cannot match at all: `<url>` autolink
# form and `(url "title")`. That is a rounding error on coverage's conclusions and was
# left alone there for good reason; it is not a rounding error on an alias vocabulary,
# where each miss is a name.
#
# **The anchor group must tolerate nested brackets.** A flat `[^\[\]]*` silently lost
# 5,406 links on the first build — every entry in Databricks' SQL function index, because
# an optional-argument signature reads `[first(expr [, ignoreNull])](url)`. One level of
# nesting still lost 102, because some signatures nest twice:
# `[lag(expr [, offset [, default]])](url)`. Both were caught by the containment check in
# `EdgeSet.reconcile`, which is the entire argument for reconciling against a second regex
# rather than trusting one.
#
# So the depth is generated rather than typed, and the check is what says whether it is
# deep enough. If a future corpus nests three levels, the build refuses and names the link
# it could not match — it does not quietly return a smaller graph.
ANCHOR_DEPTH = 6


def _bracketed(depth: int) -> str:
    """A regex fragment matching one anchor-text character, brackets nested `depth` deep.

    The two alternatives are disjoint on their first character, so this stays linear —
    it is not the classic nested-quantifier backtracking trap.
    """
    inner = r"[^\[\]]"
    if depth == 0:
        return inner
    return rf"(?:{inner}|\[(?:{_bracketed(depth - 1)})*\])"


LINK = re.compile(
    rf"""(!?)\[((?:{_bracketed(ANCHOR_DEPTH)})*)\]\(\s*<?(https?://[^\s)>]+?)>?\s*(?:"[^"]*")?\)""")

# Two hostname shifts the vendors made without rewriting their own links. Worth +317
# edges — small, but the alternative is dropping edges that resolve perfectly well.
_ALIASES: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"^https://docs\.anthropic\.com/en/"), "https://platform.claude.com/docs/en/"),
    (re.compile(r"^https://docs\.anthropic\.com/"), "https://platform.claude.com/docs/"),
    (re.compile(r"^https://docs\.databricks\.com/(?:azure|gcp)/en/"),
     "https://docs.databricks.com/aws/en/"),
)

# How many distinct anchor texts to keep per edge. The long tail is one-offs and full
# sentences; the head is the name.
MAX_ANCHORS = 8


def canonicalise(url: str) -> str:
    """`coverage.normalise` plus the vendors' own host and cloud aliases."""
    for pattern, replacement in _ALIASES:
        if pattern.match(url):
            url = pattern.sub(replacement, url)
            break
    return coverage.normalise(url)


@dataclass(frozen=True)
class Edge:
    """One ordered pair of corpus pages, however many times they are linked."""

    src: str
    dst: str
    occurrences: int
    sections: int          # how many of those occurrences named a #fragment
    anchors: Counter = field(default_factory=Counter)

    @property
    def top_anchors(self) -> list[tuple[str, int]]:
        return self.anchors.most_common(MAX_ANCHORS)


@dataclass
class EdgeSet:
    """The graph, its nodes' frontmatter, and a full account of everything else."""

    edges: list[Edge] = field(default_factory=list)
    nodes: dict[str, dict] = field(default_factory=dict)
    buckets: dict[str, int] = field(default_factory=dict)
    skipped: dict[str, int] = field(default_factory=dict)
    external_hosts: Counter = field(default_factory=Counter)          # host -> link occurrences
    external_pages: dict[str, set] = field(default_factory=dict)      # host -> pages linking there
    seen: int = 0            # link instances matched, images included
    md_independent: int = 0  # what `coverage.MD_LINK` found over the same bodies
    md_uncovered: int = 0    # …of which this module's pattern did not span. Must be 0.
    md_samples: list[str] = field(default_factory=list)

    @property
    def occurrences(self) -> int:
        return sum(e.occurrences for e in self.edges)

    def accounted(self) -> int:
        return self.occurrences + sum(self.buckets.values()) + sum(self.skipped.values())

    def reconcile(self) -> tuple[bool, str]:
        """Two checks, both of which have to hold before a build is written.

        The first is an accounting identity over one regex: every instance seen is an
        internal edge, a classified non-page target, or explicitly skipped. It catches the
        failure that matters — a link quietly falling out of the graph.

        The second is containment against a *different* regex written for a different
        purpose: every link `coverage.MD_LINK` finds must fall inside a span this module
        matched. A wider pattern that is not a superset is not wider, it is different, and
        the difference is silent — which is how the first build of this module lost every
        SQL function-index link without any count looking wrong.
        """
        identity = self.accounted() == self.seen
        covered = self.md_uncovered == 0
        lines = [
            f"  seen             {self.seen:>7,}",
            f"  internal edges   {len(self.edges):>7,}  ({self.occurrences:,} occurrences)",
            *(f"  {name:<15}  {count:>7,}" for name, count in sorted(self.buckets.items())),
            *(f"  skipped/{name:<7}  {count:>7,}" for name, count in sorted(self.skipped.items())),
            f"  accounted        {self.accounted():>7,}  {'OK' if identity else 'MISMATCH'}",
            (f"  MD_LINK found    {self.md_independent:>7,}, "
             f"uncovered {self.md_uncovered:,}  {'OK' if covered else 'MISMATCH'}"),
            *(f"    missed: {s}" for s in self.md_samples[:5]),
        ]
        return identity and covered, "\n".join(lines)

    def adjacency(self) -> dict[str, list[str]]:
        """`{page: [pages it links to]}` — deduplicated, every node present."""
        out: dict[str, list[str]] = {url: [] for url in self.nodes}
        for edge in self.edges:
            out[edge.src].append(edge.dst)
        return out

    def render(self) -> str:
        ok, detail = self.reconcile()
        return "\n".join([
            f"corpus     {len(self.nodes):,} pages",
            f"graph      {len(self.edges):,} edges, {self.occurrences:,} occurrences",
            f"reconciled {'yes' if ok else 'NO — build refused'}",
            detail,
        ])


def entry_pages(nodes: dict[str, dict]) -> set[str]:
    """Where a reader plausibly enters each source — the roots `rank.depth` measures from.

    `category == 'index'` finds only two pages in the whole corpus (`/aws/en` and
    `/cookbook`), because `scraper.category.category_for` only assigns it to a URL that
    *is* a source's include prefix. Measuring hop distance from two pages makes `depth` a
    fact about those two pages rather than about the corpus, so the shallowest pages of
    every source join them.
    """
    shallowest: dict[str, int] = {}
    depths: dict[str, int] = {}
    for url, node in nodes.items():
        source = node.get("source_id") or node.get("company") or "?"
        segments = len([s for s in urlsplit(url).path.split("/") if s])
        depths[url] = segments
        if segments < shallowest.get(source, 1 << 30):
            shallowest[source] = segments
    roots = {u for u, n in nodes.items() if n.get("category") == "index"}
    for url, node in nodes.items():
        source = node.get("source_id") or node.get("company") or "?"
        if depths[url] == shallowest[source]:
            roots.add(url)
    return roots


def _check_covered(body: str, spans: list[tuple[int, int]], result: EdgeSet) -> None:
    """Record any `coverage.MD_LINK` hit that this module's pattern did not span."""
    starts = [s for s, _ in spans]
    for match in coverage.MD_LINK.finditer(body):
        result.md_independent += 1
        start, end = match.span()
        i = bisect_right(starts, start) - 1
        if 0 <= i < len(spans) and spans[i][0] <= start and end <= spans[i][1]:
            continue
        result.md_uncovered += 1
        if len(result.md_samples) < 20:
            result.md_samples.append(body[max(0, start - 60):end].replace("\n", " "))


def _corpus_pages(index_db: str | Path | None) -> set[str] | None:
    """Canonical URLs of pages that actually exist, or None if there is no index.

    `data/` also holds the last known copy of a page that has since 404'd upstream
    (`status='gone'`, which keeps its file). A link to one of those is a fact about the
    corpus's past, not an edge in its present graph.
    """
    path = Path(index_db) if index_db else DEFAULT_INDEX_DB
    if not path.exists():
        logger.info("no index at %s; treating every corpus file as a live page", path)
        return None
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return {canonicalise(u) for (u,) in conn.execute(
            "SELECT url FROM pages WHERE status = 'ok'")}
    finally:
        conn.close()


def build_edges(data_dir: str | Path = "data", *, cfg: AppConfig | None = None,
                index_db: str | Path | None = None) -> EdgeSet:
    """Scan the corpus once and resolve every link against it."""
    cfg = cfg or load_config(DEFAULT_CONFIG)
    live = _corpus_pages(index_db)
    result = EdgeSet()

    # Pass 1 collects; nothing can be resolved until every canonical URL is known.
    # Bodies are read and released one at a time — `validate.invariants.load()` would
    # hold all 80 MB at once, and this loop only needs the links out of each.
    raw: list[tuple[str, str, str, bool]] = []   # src, anchor, target, fragment
    for path in sorted(Path(data_dir).rglob("*.md")):
        front, body = writer.parse(path)
        url = front.get("canonical_url")
        if not url:
            result.skipped["no_canonical_url"] = result.skipped.get("no_canonical_url", 0) + 1
            continue
        url = canonicalise(url)
        if live is not None and url not in live:
            continue
        result.nodes[url] = {
            "url": url,
            "company": front.get("company"),
            "source_id": front.get("source_id"),
            "category": front.get("category"),
            "title": front.get("title"),
            "description": front.get("description"),
            "updated_date": str(front["updated_date"]) if front.get("updated_date") else None,
            "breadcrumbs": front.get("breadcrumbs") or [],
            "code_languages": front.get("code_languages") or [],
            "tags": front.get("tags") or [],
            "authors": front.get("authors") or [],
            "body_chars": len(body.strip()),
        }
        spans: list[tuple[int, int]] = []
        for match in LINK.finditer(body):
            bang, anchor, target = match.group(1), match.group(2), match.group(3)
            spans.append(match.span())
            result.seen += 1
            if bang:
                result.skipped["image"] = result.skipped.get("image", 0) + 1
                continue
            raw.append((url, anchor.strip(), target, "#" in target))
        _check_covered(body, spans, result)

    # Pass 2 resolves. A target inside the corpus is an edge; everything else goes to the
    # classifier that `link_gap.py` already trusts, so the two never disagree.
    pairs: dict[tuple[str, str], list] = defaultdict(lambda: [0, 0, Counter()])
    unresolved: Counter = Counter()
    corpus_hosts = coverage.hosts_of(set(result.nodes))
    for src, anchor, target, fragment in raw:
        dst = canonicalise(target)
        if dst == src:
            result.skipped["self_link"] = result.skipped.get("self_link", 0) + 1
            continue
        if dst in result.nodes:
            slot = pairs[(src, dst)]
            slot[0] += 1
            slot[1] += int(fragment)
            if anchor:
                slot[2][anchor] += 1
            continue
        unresolved[dst] += 1
        host = urlsplit(dst).netloc
        if host and host not in corpus_hosts:
            result.external_hosts[host] += 1
            result.external_pages.setdefault(host, set()).add(src)

    result.edges = [
        Edge(src=src, dst=dst, occurrences=n, sections=sections,
             anchors=Counter(dict(anchors.most_common(MAX_ANCHORS))))
        for (src, dst), (n, sections, anchors) in sorted(pairs.items())
    ]

    buckets = coverage.classify_links(cfg, unresolved, set(result.nodes))
    result.buckets = {name: sum(hits for hits, _ in entries) for name, entries in buckets.items()}
    # `archived` cannot occur: the "archive" passed in *is* the node set, so anything in
    # it resolved to an edge above. Keeping the key at zero would suggest otherwise.
    result.buckets.pop("archived", None)
    return result
