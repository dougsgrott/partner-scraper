"""One build: scan the corpus, rank it, mine its vocabularies, write `state/graph.db`.

Kept out of `cli.py` so the whole pipeline is callable as a function — the shape
`docs/coverage.md:24-33` argues for, where the computation returns dataclasses and prints
nothing, so a later MCP tool or dashboard consumes exactly what the CLI consumes.

**A build that does not reconcile is not written.** `EdgeSet.reconcile()` has already
caught two real defects in this module's own regex; refusing the write is what turns that
check from a diagnostic into a gate.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import edges as edges_mod
from . import rank, taxonomy
from .db import DEFAULT_DB_PATH, GraphDB, corpus_stamp

logger = logging.getLogger(__name__)

DEFAULT_INDEX_DB = "state/index.db"


def formula() -> str:
    """The string stored on the build row. Change a constant, change this — that is the point."""
    return (f"pagerank d={rank.DAMPING} tol={rank.TOLERANCE} max_iter={rank.MAX_ITER} "
            f"dedup=page; hits it={rank.HITS_ITERATIONS}; "
            f"anchor_depth={edges_mod.ANCHOR_DEPTH}")


@dataclass
class BuildResult:
    build_id: int | None = None
    label: str | None = None
    pages: int = 0
    edges: int = 0
    occurrences: int = 0
    terms: int = 0
    dangling: int = 0
    unreachable: int = 0
    orphans: int = 0
    alias_divergence: tuple[int, int] = (0, 0)
    elapsed_s: float = 0.0
    reconciled: bool = False
    reconciliation: str = ""
    refused: str | None = None
    buckets: dict = field(default_factory=dict)

    def render(self) -> str:
        if self.refused:
            return f"build refused — {self.refused}\n{self.reconciliation}"
        differing, total = self.alias_divergence
        share = f"{100 * differing / total:.0f}%" if total else "n/a"
        return "\n".join([
            f"build #{self.build_id}" + (f" ({self.label})" if self.label else ""),
            f"  pages            {self.pages:,}",
            f"  edges            {self.edges:,}  ({self.occurrences:,} occurrences)",
            f"  terms            {self.terms:,}",
            f"  dangling         {self.dangling:,}  (no internal outlink)",
            f"  orphaned         {self.orphans:,}  (nothing links to them)",
            f"  unreachable      {self.unreachable:,}  (no path from an entry page)",
            f"  anchor != title  {share}  ({differing:,} of {total:,} named links)",
            f"  elapsed          {self.elapsed_s:.1f}s",
        ])


def run(*, data_dir: str | Path = "data", db_path: str | Path = DEFAULT_DB_PATH,
        index_db: str | Path | None = None, config: str | None = None,
        label: str | None = None, note: str | None = None,
        cfg=None) -> BuildResult:
    """Scan, rank, mine and store. Returns without writing if reconciliation fails."""
    started = time.monotonic()
    if cfg is None and config:
        from scraper.config import load_config
        cfg = load_config(config)

    index = str(index_db) if index_db else DEFAULT_INDEX_DB
    edge_set = edges_mod.build_edges(data_dir, cfg=cfg, index_db=index)
    ok, detail = edge_set.reconcile()
    result = BuildResult(label=label, pages=len(edge_set.nodes), edges=len(edge_set.edges),
                         occurrences=edge_set.occurrences, reconciled=ok,
                         reconciliation=detail, buckets=edge_set.buckets)
    if not ok:
        result.refused = "link accounting does not reconcile"
        result.elapsed_s = time.monotonic() - started
        return result

    adjacency = edge_set.adjacency()
    pageranks = rank.pagerank(adjacency)
    hubs, authorities = rank.hits(adjacency)
    in_pages, in_refs, out_pages = rank.in_degrees(edge_set.edges)
    depths = rank.depth(adjacency, edges_mod.entry_pages(edge_set.nodes))
    term_rows = taxonomy.build_terms(edge_set.nodes, edge_set.edges,
                                     edge_set.external_hosts, edge_set.external_pages)

    result.dangling = sum(1 for targets in adjacency.values() if not targets)
    result.unreachable = len(adjacency) - len(depths)
    result.orphans = sum(1 for url in edge_set.nodes if not in_pages.get(url))
    result.terms = len(term_rows)
    result.alias_divergence = taxonomy.alias_divergence(edge_set.edges, edge_set.nodes)

    with GraphDB(db_path) as db:
        build_id = db.create_build(
            pages=result.pages, edges=result.edges, occurrences=result.occurrences,
            formula=formula(), stamp=corpus_stamp(index), buckets=dict(edge_set.buckets),
            label=label, note=note)
        db.add_edges([
            {"build_id": build_id, "src": e.src, "dst": e.dst,
             "occurrences": e.occurrences, "sections": e.sections,
             "anchors": json.dumps(dict(e.top_anchors), sort_keys=True) or None}
            for e in edge_set.edges
        ])
        db.add_nodes([
            {"build_id": build_id, "url": url,
             "company": node.get("company"), "category": node.get("category"),
             "title": node.get("title"), "body_chars": node.get("body_chars"),
             "updated_date": node.get("updated_date"),
             "breadcrumbs": json.dumps(node.get("breadcrumbs") or []),
             "code_languages": json.dumps(node.get("code_languages") or []),
             "in_pages": in_pages.get(url, 0), "in_refs": in_refs.get(url, 0),
             "out_pages": out_pages.get(url, 0),
             "pagerank": pageranks.get(url), "authority": authorities.get(url),
             "hub": hubs.get(url), "depth": depths.get(url)}
            for url, node in edge_set.nodes.items()
        ])
        db.add_terms([{"build_id": build_id, **row} for row in term_rows])

    result.build_id = build_id
    result.elapsed_s = time.monotonic() - started
    logger.info("build #%d: %d pages, %d edges, %.1fs", build_id, result.pages,
                result.edges, result.elapsed_s)
    return result
