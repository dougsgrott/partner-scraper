"""Graph and metadata analysis over the corpus — docs/graph-plan.md.

Family D of `docs/kb-application.md`: the link graph as a graph, hub and authority
ranking, taxonomy mining, and content statistics.

Like `changefeed`, this is an application built *on* the corpus, not part of building it.
It imports `scraper`; `scraper` never imports it. It is a pure function of `data/` plus
`state/index.db`, touches no network, and adds no dependencies.
"""
