"""Hub and authority ranking — item 21, which is the correction to item 20.

`kb-application.md:34-44` ranks the corpus's hubs by how many times they are linked and
concludes the distribution "says where the questions concentrate." Measured both ways on
2026-08-30:

    error-messages/error-classes        7,069 occurrences from   210 pages   33.7x
    machine-learning/…/supported-models 2,563 occurrences from    53 pages   48.4x
    release-notes/release-types         1,212 occurrences from   941 pages    1.3x

`supported-models` is third on that list because 53 pages link it about 48 times each — a
repeated table row, not a centre of gravity. Only 39 of the top 50 survive the switch to
distinct linking pages. That is `lessons-learned.md` §18's "volume is not severity" in a
new place, so every function here takes the deduplicated adjacency and never a weight.

No `networkx`, no `numpy`: neither is in `uv.lock`, the whole corpus ranks in about three
seconds, and `scripts/validate_retrieval.py`'s hand-rolled BM25 set the precedent for
keeping something this size legible instead of importing it.
"""

from __future__ import annotations

from collections import deque

# Standard damping. Named because it is stored in `builds.formula`: a score whose formula
# is not recorded cannot be compared with a score from another build (lessons-learned §17b).
DAMPING = 0.85
TOLERANCE = 1e-10
MAX_ITER = 100
HITS_ITERATIONS = 50


def pagerank(out: dict[str, list[str]], *, damping: float = DAMPING,
             tolerance: float = TOLERANCE, max_iter: int = MAX_ITER) -> dict[str, float]:
    """PageRank over a deduplicated adjacency map. Sums to 1.

    **Dangling nodes are the detail that decides whether this is right.** 1,247 of the
    corpus's 6,543 pages — 19% — link to nothing inside the corpus. A loop that only
    pushes rank along edges leaks their share on every iteration, and the result is a
    vector that no longer sums to one and is quietly wrong for every page, not just the
    dangling ones. Their mass is collected each pass and redistributed uniformly, which
    is the standard formulation and the one the tests assert against.
    """
    nodes = list(out)
    n = len(nodes)
    if not n:
        return {}
    dangling = [u for u in nodes if not out[u]]
    rank = dict.fromkeys(nodes, 1.0 / n)
    leaked = (1.0 - damping) / n

    for _ in range(max_iter):
        spilled = damping * sum(rank[u] for u in dangling) / n
        nxt = dict.fromkeys(nodes, leaked + spilled)
        for src, targets in out.items():
            if not targets:
                continue
            share = damping * rank[src] / len(targets)
            for dst in targets:
                nxt[dst] += share
        delta = sum(abs(nxt[u] - rank[u]) for u in nodes)
        rank = nxt
        if delta < tolerance:
            break
    return rank


def hits(out: dict[str, list[str]], *,
         iterations: int = HITS_ITERATIONS) -> tuple[dict[str, float], dict[str, float]]:
    """Kleinberg's HITS. Returns `(hub, authority)`, each normalised to unit sum.

    Complementary to PageRank rather than a second opinion on it: a good *hub* is a page
    that points at many good authorities — an index, a tutorial, a release-note roundup —
    which PageRank has no way to express and which is exactly what item 26's
    dependency-ordered curriculum needs.
    """
    nodes = list(out)
    if not nodes:
        return {}, {}
    incoming: dict[str, list[str]] = {u: [] for u in nodes}
    for src, targets in out.items():
        for dst in targets:
            incoming[dst].append(src)

    hub = dict.fromkeys(nodes, 1.0)
    auth = dict.fromkeys(nodes, 1.0)
    for _ in range(iterations):
        auth = {u: sum(hub[s] for s in incoming[u]) for u in nodes}
        auth = _normalise(auth)
        hub = {u: sum(auth[d] for d in out[u]) for u in nodes}
        hub = _normalise(hub)
    return hub, auth


def _normalise(scores: dict[str, float]) -> dict[str, float]:
    total = sum(scores.values())
    if not total:
        return scores
    return {u: v / total for u, v in scores.items()}


def depth(out: dict[str, list[str]], roots: set[str]) -> dict[str, int]:
    """Hops from the nearest root, by breadth-first search. Unreachable pages are absent.

    Absent, not `-1` or `999`: "unreachable" and "far away" are different facts and
    `lessons-learned.md` §14 is explicit that they must not share a code path. The caller
    stores `NULL`, and a report that wants to count them counts the gap.

    Anthropic's 788 pages carry no breadcrumbs, so on that half of the corpus this is the
    only hierarchy signal there is.
    """
    seen: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque()
    for root in roots:
        if root in out and root not in seen:
            seen[root] = 0
            queue.append((root, 0))
    while queue:
        url, d = queue.popleft()
        for dst in out.get(url, ()):
            if dst not in seen:
                seen[dst] = d + 1
                queue.append((dst, d + 1))
    return seen


def in_degrees(edges) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    """`(in_pages, in_refs, out_pages)` — the two inbound counts, side by side.

    They are returned together deliberately. Reporting either one alone is how the
    hot-spot table went wrong, and the divergence between them is itself the signal:
    a high ratio means a template, not an authority.
    """
    in_pages: dict[str, int] = {}
    in_refs: dict[str, int] = {}
    out_pages: dict[str, int] = {}
    for edge in edges:
        in_pages[edge.dst] = in_pages.get(edge.dst, 0) + 1
        in_refs[edge.dst] = in_refs.get(edge.dst, 0) + edge.occurrences
        out_pages[edge.src] = out_pages.get(edge.src, 0) + 1
    return in_pages, in_refs, out_pages
