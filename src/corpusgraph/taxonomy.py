"""Taxonomy mining — item 23, and the alias vocabulary item 20 needs.

`kb-application.md:123-125` calls the corpus's metadata "a ready controlled vocabulary."
Five of the six vocabularies are simply read off frontmatter, and only one of those is in
`state/index.db`: `breadcrumbs`, `tags`, `authors` and `code_languages` exist nowhere but
the Markdown files, which is why everything here reads `data/` rather than the manifest.

The sixth is the one nothing in this repo produces. 72% of the corpus's 75,000 internal
links use anchor text that differs from the title of the page they point at — `[cast]`,
`[CAST_OVERFLOW]`, `[casting rules]` all resolving to one page. That is an alias list for
every page in the corpus, obtained from a regex pass rather than from a model, and it is
what makes *what is this thing called elsewhere?* answerable offline.

One deliberate asymmetry, and it limits what this can claim: breadcrumbs exist on 5,776
Databricks pages and on none of Anthropic's 788, so hierarchy mining covers one vendor.
`rank.depth` is the substitute on the other, and the report says so rather than presenting
a half-covered tree as if it were the whole corpus.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from .edges import Edge

# Frontmatter list fields that are already controlled vocabularies, and the `kind` each
# becomes in the `terms` table. `breadcrumbs` is absent because it is a *trail*, not a
# set: its terms carry a parent.
LIST_FIELDS = {
    "tags": "tag",
    "authors": "author",
    "code_languages": "code_language",
}

# An anchor this common across many targets is punctuation, not a name: "here", "this
# page", "documentation". Kept in the table — dropping data is not this module's job —
# but the report ranks by how *specific* an anchor is, not by how often it appears.
GENERIC_ANCHOR_TARGETS = 25


def build_terms(nodes: dict[str, dict], edges: list[Edge],
                external_hosts: Counter | None = None,
                external_pages: dict[str, set] | None = None) -> list[dict]:
    """Every vocabulary the corpus already contains, as `terms` rows.

    `pages` is how many pages carry the term; `refs` is how many link occurrences point
    at those pages. Both are needed for the same reason the node table keeps two inbound
    counts: a category with many pages nobody links to and a category with few pages
    everybody links to are different situations that one number hides.
    """
    _, in_refs, _ = _inbound(edges)
    rows: list[dict] = []

    # -- categories ------------------------------------------------------
    cat_pages: Counter = Counter()
    cat_refs: Counter = Counter()
    for url, node in nodes.items():
        key = (node.get("company") or "?", node.get("category") or "?")
        cat_pages[key] += 1
        cat_refs[key] += in_refs.get(url, 0)
    rows += [
        {"kind": "category", "term": category, "parent": "", "company": company,
         "pages": count, "refs": cat_refs[(company, category)]}
        for (company, category), count in cat_pages.items()
    ]

    # -- breadcrumb trails -----------------------------------------------
    # Every prefix of a trail is a node in the hierarchy, so `Data engineering` counts
    # every page beneath it, not only pages whose trail ends there.
    crumb_pages: Counter = Counter()
    crumb_refs: Counter = Counter()
    for url, node in nodes.items():
        company = node.get("company") or "?"
        trail = node.get("breadcrumbs") or []
        for i in range(1, len(trail) + 1):
            key = (company, " > ".join(trail[: i - 1]), trail[i - 1])
            crumb_pages[key] += 1
            crumb_refs[key] += in_refs.get(url, 0)
    rows += [
        {"kind": "breadcrumb", "term": term, "parent": parent, "company": company,
         "pages": count, "refs": crumb_refs[(company, parent, term)]}
        for (company, parent, term), count in crumb_pages.items()
    ]

    # -- plain list fields -----------------------------------------------
    for field_name, kind in LIST_FIELDS.items():
        pages: Counter = Counter()
        refs: Counter = Counter()
        for url, node in nodes.items():
            company = node.get("company") or "?"
            for value in node.get(field_name) or []:
                pages[(company, str(value))] += 1
                refs[(company, str(value))] += in_refs.get(url, 0)
        rows += [
            {"kind": kind, "term": term, "parent": "", "company": company,
             "pages": count, "refs": refs[(company, term)]}
            for (company, term), count in pages.items()
        ]

    # -- the anchor vocabulary -------------------------------------------
    # `pages` counts distinct pages the anchor names, which is what separates a name
    # ("cast function", 1 page) from a connective ("here", hundreds).
    anchor_targets: dict[tuple[str, str], set[str]] = defaultdict(set)
    anchor_refs: Counter = Counter()
    for edge in edges:
        company = (nodes.get(edge.dst) or {}).get("company") or "?"
        for anchor, count in edge.anchors.items():
            if not anchor:
                continue
            anchor_targets[(company, anchor)].add(edge.dst)
            anchor_refs[(company, anchor)] += count
    rows += [
        {"kind": "anchor", "term": anchor, "parent": "", "company": company,
         "pages": len(targets), "refs": anchor_refs[(company, anchor)]}
        for (company, anchor), targets in anchor_targets.items()
    ]

    # -- external hosts --------------------------------------------------
    # Item 25's "where does the documentation send you when it sends you away?" — 7,908
    # links into the Apache JIRA is a fact about Databricks' SQL reference, not noise.
    for host, refs in (external_hosts or Counter()).items():
        rows.append({"kind": "external_host", "term": host, "parent": "", "company": "*",
                     "pages": len((external_pages or {}).get(host, ())), "refs": refs})
    return rows


def aliases(edges: list[Edge], nodes: dict[str, dict], *,
            min_count: int = 1) -> dict[str, list[tuple[str, int]]]:
    """`{page: [(name others use for it, times)]}`, commonest first.

    The page's own title is not removed: whether the corpus calls a page what it calls
    itself is exactly the interesting comparison, and removing the match would hide it.
    """
    merged: dict[str, Counter] = defaultdict(Counter)
    for edge in edges:
        for anchor, count in edge.anchors.items():
            if anchor:
                merged[edge.dst][anchor] += count
    return {
        url: [(a, n) for a, n in counter.most_common() if n >= min_count]
        for url, counter in merged.items() if url in nodes
    }


def alias_divergence(edges: list[Edge], nodes: dict[str, dict]) -> tuple[int, int]:
    """`(occurrences whose anchor differs from the target's title, total with anchors)`.

    Measured at 72% on 2026-08-30. It is quoted in the report because it is the number
    that says whether the alias vocabulary is worth anything: were it near zero, every
    anchor would just be repeating the title and this whole pass would be redundant.
    """
    differing = total = 0
    for edge in edges:
        title = ((nodes.get(edge.dst) or {}).get("title") or "").strip().lower()
        for anchor, count in edge.anchors.items():
            if not anchor:
                continue
            total += count
            if anchor.strip().lower() != title:
                differing += count
    return differing, total


def _inbound(edges: list[Edge]) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    from .rank import in_degrees
    return in_degrees(edges)
