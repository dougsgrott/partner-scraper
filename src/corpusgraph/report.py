"""The Markdown and JSON a build produces — `reports/graph/<NNNN>.{md,json}`.

**The report opens with the correction, not with the totals.** `kb-application.md`'s
hot-spot table ranks the corpus's hubs by link occurrences and reads that as "where the
questions concentrate"; measured against the same corpus, `supported-models` is third by
occurrences and 214th by PageRank, because 53 pages link it about 48 times each. A reader
who stops after the first table should come away with the corrected picture, so the first
table *is* the comparison.

Table and pluralisation helpers are imported from `changefeed.report` rather than copied:
`_table`'s missing trailing newline is load-bearing — a blank line after the separator row
ends a GitHub table and renders the body as paragraph text, which is how
`validation-scorecard.md` broke — and one copy with one regression test is the only way
that stays true.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from changefeed.report import _table

from . import stats
from .db import Build, GraphDB

DEFAULT_REPORT_DIR = Path("reports/graph")

TOP_N = 25
SAMPLE_N = 12


def _short(url: str, width: int = 58) -> str:
    for marker in ("/aws/en/", "/docs/en/", "/cookbook/"):
        if marker in url:
            url = url.split(marker, 1)[1]
            break
    return url if len(url) <= width else url[: width - 1] + "…"


def _pct(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "n/a"


def _table_or(headers: list[str], rows: list[list[str]], empty: str) -> str:
    """A table, or a sentence when there is nothing to put in it.

    A header and a separator with no rows under them render as a broken table, not as an
    empty one — which is how a build over a corpus slice with no cookbook tags produced a
    report with three dangling separators. Found by reading the output, per
    `lessons-learned.md` §1, and kept honest by the test that found it.
    """
    return _table(headers, rows) if rows else f"_{empty}_"


def divergence_table(db: GraphDB, build: Build, *, limit: int = TOP_N) -> str:
    """The two rankings side by side — the whole reason this subsystem exists."""
    by_refs = db.top(build.id, by="in_refs", limit=limit)
    rows = []
    for entry in by_refs:
        position = db.rank_of(build.id, entry["url"], by="pagerank")
        ratio = entry["in_refs"] / entry["in_pages"] if entry["in_pages"] else 0.0
        rows.append([
            f"`{_short(entry['url'], 46)}`",
            f"{entry['in_refs']:,}",
            f"{entry['in_pages']:,}",
            f"{ratio:.1f}×",
            str(position) if position else "—",
        ])
    return _table_or(["page", "occurrences", "linking pages", "ratio", "PageRank #"], rows,
                     "no page in this build is linked more than once")


def hubs_table(db: GraphDB, build: Build, *, by: str = "pagerank",
               limit: int = TOP_N) -> str:
    rows = [
        [f"{i}", f"`{_short(entry['url'], 50)}`", entry["company"] or "?",
         f"{entry['in_pages']:,}", f"{entry['in_refs']:,}",
         f"{entry[by]:.5f}" if isinstance(entry.get(by), float) else str(entry.get(by))]
        for i, entry in enumerate(db.top(build.id, by=by, limit=limit), 1)
    ]
    return _table_or(["#", "page", "company", "linking pages", "occurrences", by], rows,
                     f"no page in this build has a {by} score")


def stats_table(groups: list[stats.GroupStat], *, limit: int = TOP_N) -> str:
    rows = [
        [f"`{g.key}`", g.company, f"{g.pages:,}", f"{g.median_chars:,}",
         f"{100 * g.share_of_rank:.2f}%", f"{g.orphans:,}", g.stale_months or "—",
         ", ".join(g.languages) or "—"]
        for g in groups[:limit]
    ]
    return _table_or(["group", "company", "pages", "median chars", "share of rank",
                      "orphans", "newest update", "languages"], rows, "no groups")


def terms_table(db: GraphDB, build: Build, kind: str, *, limit: int = TOP_N) -> str:
    rows = [
        [f"`{t['term']}`", t["parent"] or "—", t["company"], f"{t['pages']:,}",
         f"{t['refs']:,}"]
        for t in db.terms(build.id, kind=kind, limit=limit)
    ]
    return _table_or(["term", "parent", "company", "pages", "inbound refs"], rows,
                     f"this corpus carries no {kind.replace('_', ' ')} terms")


def render(db: GraphDB, build: Build) -> str:
    nodes = [dict(r) for r in db.conn.execute(
        "SELECT * FROM nodes WHERE build_id = ?", (build.id,))]
    for node in nodes:
        node["breadcrumbs"] = json.loads(node["breadcrumbs"] or "[]")
        node["code_languages"] = json.loads(node["code_languages"] or "[]")

    profile = stats.size_profile(nodes)
    orphaned = [n for n in nodes if not n["in_pages"]]
    unreachable = [n for n in nodes if n["depth"] is None]
    by_category = stats.by_category(nodes)

    parts = [
        "# Corpus graph and metadata",
        "",
        (f"> {build.name} · {build.built_at} · {build.pages:,} pages · "
         f"{build.edges:,} edges · corpus `{build.corpus_stamp}`"),
        f"> Formula: `{build.formula}`",
        f"> Rendered {datetime.now(UTC).isoformat(timespec='seconds')}",
        "",
        "## Read this first: occurrences are not importance",
        "",
        "The corpus's hubs ranked the way `kb-application.md` ranked them — by how many",
        "times a page is linked — beside the number of *distinct pages* that link it and",
        "the page's position under PageRank. Where the ratio is high, the count is",
        "measuring a repeated template on a handful of pages, not a centre of gravity.",
        "",
        divergence_table(db, build),
        "",
        "## Hubs by PageRank",
        "",
        hubs_table(db, build, by="pagerank"),
        "",
        "## Authorities by HITS",
        "",
        hubs_table(db, build, by="authority"),
        "",
        "## Shape of the graph",
        "",
        _table(["property", "value", "note"], [
            ["pages", f"{build.pages:,}", "nodes in the graph"],
            ["edges", f"{build.edges:,}", "distinct (source, target) pairs"],
            ["occurrences", f"{build.occurrences:,}",
             f"link instances — {build.occurrences / max(build.edges, 1):.1f}× the edges"],
            ["orphaned", f"{len(orphaned):,} ({_pct(len(orphaned), len(nodes))})",
             "nothing in the corpus links to them"],
            ["unreachable", f"{len(unreachable):,} ({_pct(len(unreachable), len(nodes))})",
             "no path from any entry page"],
        ]),
        "",
        "### Largest orphans",
        "",
        "Not a defect list: a vendor may only reach these from a sidebar the Markdown does",
        "not carry. A *large* orphan is worth a look — it is either a real gap in the",
        "vendor's navigation or a page whose links our extractor dropped.",
        "",
        _table_or(["page", "chars", "category"], [
            [f"`{_short(n['url'])}`", f"{n['body_chars']:,}", n["category"] or "—"]
            for n in stats.orphans(nodes, limit=SAMPLE_N)
        ], "every page in this build is linked from somewhere"),
        "",
        "## Content strategy",
        "",
        "Density and centrality together. A group with many pages and a small share of",
        "rank is bulk reference; few pages with a large share is a load-bearing hub.",
        "",
        stats_table(by_category),
        "",
        "### Page sizes",
        "",
        _table(["median", "p90", "p99", "max", "over 500 KB"], [[
            f"{profile.get('median', 0):,}", f"{profile.get('p90', 0):,}",
            f"{profile.get('p99', 0):,}", f"{profile.get('max', 0):,}",
            f"{profile.get('over_500kb', 0):,}",
        ]]),
        "",
        "### Recency",
        "",
        _table_or(["month", "pages"], [[m, f"{n:,}"] for m, n in stats.recency(nodes)[:12]],
                  "no page carries an updated_date"),
        "",
        "## Vocabularies",
        "",
        "### Categories",
        "",
        terms_table(db, build, "category"),
        "",
        "### Breadcrumb hierarchy",
        "",
        "Databricks only — Anthropic's pages carry no breadcrumbs, so hop distance from an",
        "entry page is the only hierarchy signal on that half of the corpus.",
        "",
        terms_table(db, build, "breadcrumb"),
        "",
        "### Code languages",
        "",
        terms_table(db, build, "code_language", limit=SAMPLE_N),
        "",
        "### Cookbook tags",
        "",
        terms_table(db, build, "tag", limit=SAMPLE_N),
        "",
        "### Where the docs send you away",
        "",
        terms_table(db, build, "external_host", limit=SAMPLE_N),
        "",
        "## What was not an edge",
        "",
        _table_or(["bucket", "link instances"],
                  [[k, f"{v:,}"] for k, v in sorted(build.buckets.items())],
                  "every link in this build resolved to a corpus page"),
        "",
    ]
    return "\n".join(parts)


def to_json(db: GraphDB, build: Build) -> dict:
    nodes = [dict(r) for r in db.conn.execute(
        "SELECT * FROM nodes WHERE build_id = ?", (build.id,))]
    for node in nodes:
        node["breadcrumbs"] = json.loads(node["breadcrumbs"] or "[]")
        node["code_languages"] = json.loads(node["code_languages"] or "[]")
    return {
        "build": {
            "id": build.id, "built_at": build.built_at, "label": build.label,
            "pages": build.pages, "edges": build.edges,
            "occurrences": build.occurrences, "formula": build.formula,
            "corpus_stamp": build.corpus_stamp, "buckets": build.buckets,
        },
        "size_profile": stats.size_profile(nodes),
        "recency": stats.recency(nodes),
        "top": {
            by: db.top(build.id, by=by, limit=100)
            for by in ("pagerank", "authority", "hub", "in_pages", "in_refs")
        },
        "categories": [vars(g) for g in stats.by_category(nodes)],
        "breadcrumbs": [vars(g) for g in stats.by_breadcrumb(nodes)],
        "orphans": stats.orphans(nodes, limit=200),
        "terms": {kind: db.terms(build.id, kind=kind, limit=500)
                  for kind in ("category", "tag", "code_language", "author",
                               "external_host")},
    }


def write(db: GraphDB, build: Build, *, report_dir: str | Path | None = None,
          ) -> tuple[Path, Path]:
    """Write both reports. Returns their paths."""
    base = Path(report_dir or DEFAULT_REPORT_DIR)
    base.mkdir(parents=True, exist_ok=True)
    stem = f"{build.id:04d}"

    md_path = base / f"{stem}.md"
    md_path.write_text(render(db, build), encoding="utf-8")
    json_path = base / f"{stem}.json"
    json_path.write_text(json.dumps(to_json(db, build), indent=2, sort_keys=True),
                         encoding="utf-8")
    return md_path, json_path


def summarise(db: GraphDB, build: Build) -> str:
    """A few aligned lines for the terminal."""
    counts = db.counts(build.id)
    top = db.top(build.id, by="pagerank", limit=3)
    return "\n".join([
        f"{build.name} · {build.built_at}",
        f"  pages            {build.pages:,}",
        f"  edges            {build.edges:,}  ({build.occurrences:,} occurrences)",
        f"  terms            {counts['terms']:,}",
        "  top by pagerank  " + ", ".join(_short(t["url"], 28) for t in top),
    ])
