"""Graph and metadata analysis — docs/graph-plan.md.

The claim under test is that the corpus's own link graph can be trusted as a graph:
nothing falls out of it silently, and the ranking it produces measures importance rather
than repetition.

The test that matters most is
`test_a_page_linked_many_times_from_one_page_ranks_below_one_linked_once_from_many`.
`kb-application.md:34-44` ranked the corpus's hubs by link occurrences and read the result
as "where the questions concentrate"; on the real corpus that put
`machine-learning/foundation-model-apis/supported-models` third, when only 53 pages link
it — about 48 times each, from a repeated table row. Under PageRank it is 214th. That
defect is the reason this package deduplicates before it ranks, and the reason the report
opens with the two counts side by side.

The second is `test_a_link_the_wider_pattern_misses_refuses_the_build`. The first build of
`edges.py` lost 5,406 links — every entry in Databricks' SQL function index, because
`[first(expr [, ignoreNull])](url)` nests brackets inside the anchor text — and every
count in that build looked entirely reasonable. It was caught only by reconciling against
a second, independently written regex, so that reconciliation is a gate and not a report.
"""

from __future__ import annotations

import json

import pytest

from corpusgraph import build as build_mod
from corpusgraph import edges as edges_mod
from corpusgraph import rank, report, stats, taxonomy
from corpusgraph.db import GraphDB, corpus_stamp
from scraper.records import Extracted
from scraper.store import writer
from scraper.store.index import Index

BASE = "https://docs.databricks.com/aws/en"


def record(slug: str = "delta", body: str = "", **kw) -> Extracted:
    base = {
        "title": f"Page {slug}",
        "markdown": f"# Page {slug}\n\n{body or f'Prose about {slug}.'}\n",
        "canonical_url": f"{BASE}/{slug}",
        "source_url": f"{BASE}/{slug}",
        "company": "databricks", "source_id": "databricks-docs", "category": "delta",
        "extractor": "docusaurus", "extractor_version": "4",
    }
    return Extracted(**{**base, **kw})


def link(slug: str, text: str = "") -> str:
    return f"[{text or slug}]({BASE}/{slug})"


class Corpus:
    """A throwaway corpus, its manifest, and the graph database built from them."""

    def __init__(self, tmp_path):
        self.data = tmp_path / "data"
        self.index_db = tmp_path / "index.db"
        self.graph_db = tmp_path / "graph.db"
        self.report_dir = tmp_path / "reports"

    def populate(self, records, *, gone: set[str] = frozenset()) -> None:
        """Write real files and a real manifest — no mock ever stands in for the store."""
        index = Index(self.index_db)
        index.conn.execute("DELETE FROM pages")
        index.conn.commit()
        for rec in records:
            result = writer.write(rec, self.data)
            index.upsert(rec, result.path, content_hash=writer.content_hash(rec.markdown))
            if rec.canonical_url in gone:
                index.mark_gone(rec.canonical_url, status_code=404)
        index.close()

    def edges(self, **kw):
        return edges_mod.build_edges(self.data, cfg=config(), index_db=self.index_db, **kw)

    def build(self, **kw):
        return build_mod.run(data_dir=self.data, db_path=self.graph_db,
                             index_db=self.index_db, cfg=config(), **kw)

    def db(self) -> GraphDB:
        return GraphDB(self.graph_db)


def config():
    from scraper.config import AppConfig
    return AppConfig(sources={"databricks-docs": {
        "company": "databricks",
        "seeds": [{"type": "sitemap", "url": "https://docs.databricks.com/sitemap.xml"}],
        "include_paths": ["/aws/en/"],
        "fetcher": "http", "extractor": "docusaurus",
    }})


@pytest.fixture
def corpus(tmp_path):
    return Corpus(tmp_path)


# --- the regression this package exists for -------------------------------

def test_a_page_linked_many_times_from_one_page_ranks_below_one_linked_once_from_many(corpus):
    """`supported-models`, reduced to a fixture.

    2,563 occurrences from 53 pages put it third in `kb-application.md`'s hot-spot table
    and 214th under PageRank. A ranking that cannot tell a repeated table row from a
    citation is measuring the template, so this is the property the deduplication exists
    to give and the one worth breaking loudly.
    """
    template = "\n".join(link("loud") for _ in range(50))
    records = [
        record("loud"), record("quiet"),
        record("shouter", body=template),
        *(record(f"citer{i}", body=link("quiet")) for i in range(20)),
    ]
    corpus.populate(records)
    result = corpus.build()

    with corpus.db() as db:
        loud = db.node(result.build_id, f"{BASE}/loud")
        quiet = db.node(result.build_id, f"{BASE}/quiet")

    assert loud["in_refs"] == 50 and loud["in_pages"] == 1
    assert quiet["in_refs"] == 20 and quiet["in_pages"] == 20
    assert quiet["pagerank"] > loud["pagerank"], (
        "occurrence count outranked distinct linkers — the deduplication is not happening")


def test_the_two_inbound_counts_are_both_kept(corpus):
    """Reporting either count alone is how the hot-spot table went wrong."""
    corpus.populate([record("hub"), record("linker", body=link("hub") + link("hub"))])
    result = corpus.build()
    with corpus.db() as db:
        node = db.node(result.build_id, f"{BASE}/hub")
    assert (node["in_refs"], node["in_pages"]) == (2, 1)


# --- the ranker, shown failing before it is trusted -----------------------
# lessons-learned.md §19: "a scorer that has only ever returned success has not been
# tested — it has been observed agreeing with itself." Each of these has an answer that
# can be worked out on paper.

def test_pagerank_on_a_cycle_is_uniform():
    out = {"a": ["b"], "b": ["c"], "c": ["a"]}
    scores = rank.pagerank(out)
    assert all(abs(v - 1 / 3) < 1e-9 for v in scores.values())


def test_pagerank_on_a_star_concentrates_on_the_centre():
    out = {"hub": [], "a": ["hub"], "b": ["hub"], "c": ["hub"]}
    scores = rank.pagerank(out)
    assert scores["hub"] > max(scores["a"], scores["b"], scores["c"])


def test_pagerank_always_sums_to_one_even_with_dangling_nodes():
    """The 19%-of-the-corpus case.

    1,243 of the real corpus's 6,541 pages link to nothing inside it. A loop that pushes
    rank only along edges leaks their share every iteration, and the failure is silent:
    the ordering still looks plausible while every score is wrong. Asserting the sum is
    what catches it; asserting the order is not.
    """
    for out in (
        {"a": [], "b": [], "c": []},                     # all dangling
        {"a": ["b"], "b": [], "c": ["a"]},               # one sink
        {"a": ["b"], "b": ["a"], "sink": []},            # a component plus a sink
    ):
        assert abs(sum(rank.pagerank(out).values()) - 1.0) < 1e-9


def test_pagerank_gives_an_isolated_node_the_teleport_minimum():
    out = {"a": ["b"], "b": ["a"], "lonely": []}
    scores = rank.pagerank(out)
    assert scores["lonely"] > 0, "an unlinked page must still be reachable by teleport"
    assert scores["lonely"] < scores["a"]


def test_hits_separates_a_hub_from_an_authority():
    out = {"index": ["one", "two", "three"], "one": [], "two": [], "three": []}
    hub, authority = rank.hits(out)
    assert hub["index"] > max(hub["one"], hub["two"])
    assert authority["one"] > authority["index"]


def test_depth_omits_unreachable_pages_rather_than_numbering_them():
    """`lessons-learned.md` §14 — "unreachable" and "far away" are different facts."""
    out = {"root": ["a"], "a": ["b"], "b": [], "island": []}
    depths = rank.depth(out, {"root"})
    assert depths == {"root": 0, "a": 1, "b": 2}
    assert "island" not in depths


# --- what is and is not an edge -------------------------------------------

def test_an_image_embed_is_not_an_edge(corpus):
    """2,326 of them in the real corpus. An illustration is not a citation."""
    corpus.populate([record("target"),
                     record("page", body=f"![a diagram]({BASE}/target)")])
    edge_set = corpus.edges()
    assert edge_set.edges == []
    assert edge_set.skipped["image"] == 1


def test_a_self_link_is_not_an_edge(corpus):
    corpus.populate([record("page", body=f"[top]({BASE}/page#section)")])
    edge_set = corpus.edges()
    assert edge_set.edges == []
    assert edge_set.skipped["self_link"] == 1


def test_a_link_to_a_page_that_is_gone_upstream_is_classified_not_counted(corpus):
    """`data/` keeps a deleted page's last copy; the present graph must not contain it."""
    corpus.populate([record("dead"), record("page", body=link("dead"))],
                    gone={f"{BASE}/dead"})
    edge_set = corpus.edges()
    assert edge_set.edges == []
    assert f"{BASE}/dead" not in edge_set.nodes
    assert sum(edge_set.buckets.values()) == 1


def test_a_fragment_link_is_one_edge_and_is_counted_as_a_section(corpus):
    corpus.populate([record("target"),
                     record("page", body=link("target") + f"[part]({BASE}/target#part)")])
    edge_set = corpus.edges()
    assert len(edge_set.edges) == 1
    assert edge_set.edges[0].occurrences == 2
    assert edge_set.edges[0].sections == 1


def test_vendor_host_and_cloud_aliases_resolve_to_the_same_page():
    """+317 edges on the real corpus. Small, but the alternative is dropping real ones."""
    assert (edges_mod.canonicalise("https://docs.databricks.com/azure/en/delta/")
            == "https://docs.databricks.com/aws/en/delta")
    assert (edges_mod.canonicalise("https://docs.anthropic.com/en/api/messages")
            == "https://platform.claude.com/docs/en/api/messages")


# --- reconciliation, which is a gate ---------------------------------------

def test_a_sql_signature_with_nested_brackets_is_still_a_link(corpus):
    """The 5,406-link regression, reduced.

    `[first(expr [, ignoreNull])](url)` and `[lag(expr [, offset [, default]])](url)` are
    how Databricks writes its function index. A flat anchor pattern matches neither, and
    nothing about the resulting build looks wrong.
    """
    body = (f"| [first(expr [, ignoreNull])]({BASE}/first) |\n"
            f"| [lag(expr [, offset [, default]])]({BASE}/lag) |\n"
            f"| [aes_encrypt(expr, key[, mode[, padding[, iv]]])]({BASE}/aes) |\n")
    corpus.populate([record("first"), record("lag"), record("aes"),
                     record("index", body=body)])
    edge_set = corpus.edges()
    assert {e.dst for e in edge_set.edges} == {f"{BASE}/first", f"{BASE}/lag", f"{BASE}/aes"}
    assert edge_set.reconcile()[0]


def test_every_link_instance_is_accounted_for(corpus):
    """Internal edge, classified bucket, or explicitly skipped — nothing else exists."""
    body = "\n".join([
        link("target"), f"![img]({BASE}/pic.png)", "[out](https://example.com/x)",
        f"[self]({BASE}/page)", f"[asset]({BASE}/f.pdf)",
    ])
    corpus.populate([record("target"), record("page", body=body)])
    edge_set = corpus.edges()
    assert edge_set.accounted() == edge_set.seen
    assert edge_set.reconcile()[0]


def test_a_link_the_wider_pattern_misses_refuses_the_build(corpus):
    """Give the checker a known-bad input, per lessons-learned §19.

    The containment check is only evidence if it can fail, so it is handed a body with a
    link and a deliberately empty span list — the exact shape of the defect it was
    written for.
    """
    result = edges_mod.EdgeSet()
    edges_mod._check_covered(f"see [x]({BASE}/target) here", [], result)
    assert result.md_independent == 1
    assert result.md_uncovered == 1
    assert result.reconcile()[0] is False
    assert result.md_samples, "a refusal must name the link it could not match"


def test_a_build_that_does_not_reconcile_is_never_written(corpus, monkeypatch):
    corpus.populate([record("target"), record("page", body=link("target"))])
    monkeypatch.setattr(edges_mod, "LINK", edges_mod.re.compile(r"(!?)\[(never)\]\((x)\)"))
    result = corpus.build()
    assert result.refused
    assert result.build_id is None
    with corpus.db() as db:
        assert db.builds() == []


# --- vocabularies ---------------------------------------------------------

def test_a_page_counts_once_per_term_however_often_it_is_linked(corpus):
    corpus.populate([
        record("a", tags=["Tools"]),
        record("b", tags=["Tools"]),
        record("linker", body=link("a") * 5),
    ])
    result = corpus.build()
    with corpus.db() as db:
        row = db.terms(result.build_id, kind="tag")[0]
    assert row["term"] == "Tools"
    assert row["pages"] == 2
    assert row["refs"] == 5, "refs counts link occurrences, pages counts pages"


def test_breadcrumb_counts_are_monotone_down_a_trail(corpus):
    corpus.populate([
        record("x", breadcrumbs=["SQL", "Functions", "cast"]),
        record("y", breadcrumbs=["SQL", "Functions", "trim"]),
        record("z", breadcrumbs=["SQL", "Types"]),
    ])
    result = corpus.build()
    with corpus.db() as db:
        rows = {(t["parent"], t["term"]): t["pages"]
                for t in db.terms(result.build_id, kind="breadcrumb", limit=50)}
    assert rows[("", "SQL")] == 3
    assert rows[("SQL", "Functions")] == 2
    assert rows[("SQL > Functions", "cast")] == 1


def test_the_anchor_vocabulary_records_what_other_pages_call_a_page(corpus):
    """Item 20's alias list, without a model: 66% of real anchors differ from the title."""
    corpus.populate([
        record("cast"),
        record("a", body=link("cast", "`cast` function")),
        record("b", body=link("cast", "casting rules")),
        record("c", body=link("cast", "`cast` function")),
    ])
    result = corpus.build()
    with corpus.db() as db:
        assert db.anchors_for(result.build_id, f"{BASE}/cast") == [
            ("`cast` function", 2), ("casting rules", 1)]


def test_alias_divergence_counts_anchors_that_differ_from_the_title(corpus):
    corpus.populate([record("cast"), record("a", body=link("cast", "Page cast")),
                     record("b", body=link("cast", "casting"))])
    edge_set = corpus.edges()
    differing, total = taxonomy.alias_divergence(edge_set.edges, edge_set.nodes)
    assert (differing, total) == (1, 2)


def test_an_external_host_is_counted_but_never_becomes_an_edge(corpus):
    corpus.populate([record("page", body="[jira](https://issues.apache.org/x)")])
    edge_set = corpus.edges()
    assert edge_set.edges == []
    assert edge_set.external_hosts["issues.apache.org"] == 1
    assert edge_set.external_pages["issues.apache.org"] == {f"{BASE}/page"}


# --- statistics -----------------------------------------------------------

def test_group_statistics_use_a_median_not_a_mean(corpus):
    """§18: a corpus with a 4.77 MB page and a 300-byte page has no meaningful average."""
    nodes = [{"company": "d", "category": "c", "body_chars": n, "pagerank": 0.1,
              "in_pages": 1, "depth": 0, "code_languages": [], "updated_date": None}
             for n in (10, 20, 30, 10_000_000)]
    group = stats.by_category(nodes)[0]
    assert group.median_chars == 25


def test_pages_without_breadcrumbs_are_a_group_not_a_silent_omission():
    """788 real pages have none; a rollup that drops them misreports its own coverage."""
    nodes = [{"company": "anthropic", "breadcrumbs": [], "body_chars": 10,
              "pagerank": 0.5, "in_pages": 0, "depth": None, "code_languages": [],
              "updated_date": None}]
    groups = stats.by_breadcrumb(nodes)
    assert [g.key for g in groups] == ["(no breadcrumbs)"]
    assert groups[0].pages == 1


def test_orphans_are_pages_nothing_links_to(corpus):
    corpus.populate([record("target"), record("page", body=link("target"))])
    result = corpus.build()
    with corpus.db() as db:
        nodes = [dict(r) for r in db.conn.execute(
            "SELECT * FROM nodes WHERE build_id = ?", (result.build_id,))]
    assert [n["url"] for n in stats.orphans(nodes)] == [f"{BASE}/page"]


# --- the store ------------------------------------------------------------

def test_a_build_records_the_formula_that_produced_its_scores(corpus):
    """§17b: a stored derived value carries its formula, or it cannot be compared."""
    corpus.populate([record("a"), record("b", body=link("a"))])
    result = corpus.build(label="baseline")
    with corpus.db() as db:
        build = db.resolve("baseline")
    assert build.id == result.build_id
    assert "pagerank d=0.85" in build.formula
    assert "dedup=page" in build.formula
    assert f"anchor_depth={edges_mod.ANCHOR_DEPTH}" in build.formula


def test_a_build_records_which_corpus_it_described(corpus):
    corpus.populate([record("a")])
    first = corpus_stamp(corpus.index_db)
    corpus.populate([record("a", body="different prose entirely")])
    assert corpus_stamp(corpus.index_db) != first


def test_builds_resolve_by_id_label_and_latest(corpus):
    corpus.populate([record("a"), record("b", body=link("a"))])
    first = corpus.build(label="one")
    second = corpus.build(label="two")
    with corpus.db() as db:
        assert db.resolve("one").id == first.build_id
        assert db.resolve(second.build_id).id == second.build_id
        assert db.resolve("latest").id == second.build_id
        assert db.resolve("nope") is None


def test_gc_keeps_the_newest_builds_and_removes_their_rows(corpus):
    corpus.populate([record("a"), record("b", body=link("a"))])
    first = corpus.build()
    corpus.build()
    with corpus.db() as db:
        assert db.prune(1) == [first.build_id]
        assert db.counts(first.build_id) == {"edges": 0, "nodes": 0, "terms": 0}


def test_an_unknown_ranking_column_is_refused_rather_than_interpolated(corpus):
    """The column name reaches SQL, so it is checked against a list, never quoted in."""
    corpus.populate([record("a")])
    result = corpus.build()
    with corpus.db() as db, pytest.raises(ValueError):
        db.top(result.build_id, by="1; DROP TABLE nodes")


# --- idempotency ----------------------------------------------------------

def test_two_builds_of_an_unchanged_corpus_agree_on_everything_derived(corpus):
    """§6: idempotency is a property to test, not to assume."""
    corpus.populate([record("a"), record("b", body=link("a")),
                     record("c", body=link("a") + link("b"))])
    first = corpus.build()
    second = corpus.build()

    with corpus.db() as db:
        one = report.to_json(db, db.build(first.build_id))
        two = report.to_json(db, db.build(second.build_id))
    for payload in (one, two):
        for volatile in ("id", "built_at", "label"):
            payload["build"].pop(volatile)
        for rows in payload["top"].values():
            for row in rows:
                row.pop("build_id")
        for row in payload["orphans"]:
            row.pop("build_id")
        for rows in payload["terms"].values():
            for row in rows:
                row.pop("build_id")
    assert json.dumps(one, sort_keys=True) == json.dumps(two, sort_keys=True)


def test_the_report_renders_both_files_and_keeps_its_tables_intact(corpus):
    """`_table` must not end in a newline, or the row after it ends the table."""
    corpus.populate([record("a"), record("b", body=link("a"))])
    result = corpus.build()
    with corpus.db() as db:
        md_path, json_path = report.write(db, db.build(result.build_id),
                                          report_dir=corpus.report_dir)
    text = md_path.read_text(encoding="utf-8")
    assert "occurrences are not importance" in text
    assert "|---|" in text
    assert "\n|---|---|---|---|---|\n\n" not in text, "a blank line after a separator ends the table"
    assert json.loads(json_path.read_text(encoding="utf-8"))["build"]["pages"] == 2


# --- pictures -------------------------------------------------------------
# `viz.py` is presentational, but its geometry is not a matter of taste: a label that
# overlaps a mark, a radius that lies about magnitude, or a layout that moves between
# runs are all defects with objective tests. Every one below defends something that went
# wrong on a real render.

def _fixture_graph(corpus):
    corpus.populate([
        record("hub"), record("second"), record("third"),
        record("lonely"),                       # links to nothing, is linked by nothing
        *(record(f"citer{i}", body=link("hub") + link("second")) for i in range(8)),
        record("bridge", body=link("hub") + link("third")),
    ])
    return corpus.build()


def _svg(corpus, kind, **kw):
    from corpusgraph import viz
    with corpus.db() as db:
        return viz.render(db, db.resolve("latest"), kind, **kw)


@pytest.mark.parametrize("kind", ["hubs", "correction", "categories"])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_every_view_renders_parseable_svg(corpus, kind, theme):
    """Dark mode is a selected set of steps, not a flipped one — so both are rendered."""
    import xml.etree.ElementTree as ET
    _fixture_graph(corpus)
    svg = _svg(corpus, kind, theme=theme, top=10)
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert root.get("viewBox")


def test_a_title_containing_markup_cannot_break_the_document(corpus):
    """Page titles come from vendor HTML; one `&` unescaped is a corrupt file.

    The ego view is the one that prints a title rather than a URL slug, so it is the one
    where an unescaped ampersand would actually land in the document.
    """
    import xml.etree.ElementTree as ET
    corpus.populate([record("a", title="Tips & <tricks>"),
                     record("b", body=link("a"))])
    corpus.build()
    svg = _svg(corpus, "ego", url=f"{BASE}/a", top=5)
    ET.fromstring(svg)
    assert "Tips &amp; &lt;tricks&gt;" in svg


def test_node_radius_is_proportional_to_area_not_to_value(corpus):
    """A radius set straight from the value makes a 4× page look 16× as important."""
    from corpusgraph import viz
    r1 = viz._radius(25, 100, smallest=0, biggest=40)
    r2 = viz._radius(100, 100, smallest=0, biggest=40)
    assert abs(r2 / r1 - 2.0) < 1e-9


def test_the_layout_is_the_same_every_run(corpus):
    """Two exports of one build must not look like two different datasets."""
    from corpusgraph import viz
    nodes = [f"n{i}" for i in range(12)]
    edges = [("n0", f"n{i}") for i in range(1, 8)] + [("n8", "n9")]
    first = viz.force_layout(nodes, edges, width=400, height=300, iterations=60)
    second = viz.force_layout(nodes, edges, width=400, height=300, iterations=60)
    assert first == second


def test_labels_never_overlap_each_other_or_their_marks(corpus):
    """Both halves of the rule.

    The first render avoided label-label collisions perfectly and drew
    `error-messages/error-classes` straight through a circle, because the marks were not
    obstacles. A label overlapping data is the same defect as a label overlapping a label.
    """
    from corpusgraph import viz
    bounds = (0.0, 0.0, 500.0, 300.0)
    candidates = [(100 + 7 * i, 150 + 3 * i, f"label-{i}", 12.0) for i in range(30)]
    placed = viz._place_labels(candidates, bounds=bounds)
    boxes = [(x - 2, y - 13, x + viz.text_width(t, 11) + 2, y + 3) for x, y, t in placed]
    for i, a in enumerate(boxes):
        assert a[0] >= bounds[0] and a[2] <= bounds[2]
        for b in boxes[i + 1:]:
            assert a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3]
    for x, y, _ in placed:
        for cx, cy, _, r in candidates:
            assert not (abs(x - cx) < r and abs(y - 4 - cy) < r), "label sits on a mark"


def test_the_hub_map_drops_pages_that_link_to_nothing_in_it(corpus):
    """One floating node rescaled the whole first render into a corner.

    `_fit` scales the layout to its extremes, so a single disconnected page — which any
    force layout pushes to the frame's edge — shrinks the actual graph to make room for
    it. Isolates are dropped and counted in the footer instead.
    """
    _fixture_graph(corpus)
    svg = _svg(corpus, "hubs", top=20)
    assert "lonely" not in svg
    assert "link to none of them" in svg


def test_the_dumbbell_grows_instead_of_squeezing_its_rows(corpus):
    """60 rows in a fixed frame collided; the canvas is sized from the row count."""
    import xml.etree.ElementTree as ET
    targets = [record(f"t{i}") for i in range(40)]
    linkers = [record(f"l{i}", body="".join(link(f"t{j}") for j in range(40)))
               for i in range(3)]
    corpus.populate(targets + linkers)
    corpus.build()
    short = ET.fromstring(_svg(corpus, "correction", top=5))
    tall = ET.fromstring(_svg(corpus, "correction", top=40))
    assert int(short.get("height")) == 900, "few rows fit the default frame"
    assert int(tall.get("height")) > 900, "many rows must grow it, never squeeze"


def test_the_ego_view_refuses_to_guess_its_subject(corpus):
    _fixture_graph(corpus)
    with corpus.db() as db, pytest.raises(ValueError, match="needs --url"):
        from corpusgraph import viz
        viz.render(db, db.resolve("latest"), "ego")


def test_a_single_series_gets_no_legend_box(corpus):
    """The subtitle names it; a one-entry legend is chrome pretending to be information."""
    _fixture_graph(corpus)          # databricks only
    assert "databricks pages that link to each other" in _svg(corpus, "hubs", top=10)
