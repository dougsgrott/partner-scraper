"""Command line for the corpus graph — `docs/graph-plan.md`.

Every command is offline and reads only `data/`, `state/index.db` and `state/graph.db`.
Nothing here fetches, and nothing here calls a model.

Examples:

    uv run python scripts/graph.py build --label first
    uv run python scripts/graph.py rank --top 20
    uv run python scripts/graph.py rank --top 20 --by in_refs      # the old ranking
    uv run python scripts/graph.py page <url>
    uv run python scripts/graph.py taxonomy --kind breadcrumb
    uv run python scripts/graph.py stats --by category
    uv run python scripts/graph.py report --write
    uv run python scripts/graph.py image --all           # SVGs for a deck
    uv run python scripts/graph.py image --kind ego --url <url>
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from . import build as build_mod
from . import report as report_mod
from . import stats as stats_mod
from . import viz as viz_mod
from .db import DEFAULT_DB_PATH, RANK_COLUMNS, TERM_KINDS, GraphDB
from .edges import canonicalise

logger = logging.getLogger(__name__)


def _add_store_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--graph-db", help="graph database (default state/graph.db)")
    parser.add_argument("--index-db", help="corpus manifest (default state/index.db)")
    parser.add_argument("--data-dir", help="corpus root (default data)")
    parser.add_argument("--report-dir", help="where reports are written")


def _db(args) -> GraphDB:
    return GraphDB(args.graph_db or DEFAULT_DB_PATH)


def _resolve(db: GraphDB, args):
    build = db.resolve(getattr(args, "build", None))
    if build is None:
        print("no builds yet — run `graph build` first", file=sys.stderr)
    return build


def _emit(args, payload) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str)
          if getattr(args, "json", False) else payload)


def cmd_build(args) -> int:
    result = build_mod.run(
        data_dir=args.data_dir or "data",
        db_path=args.graph_db or DEFAULT_DB_PATH,
        index_db=args.index_db,
        config=args.config,
        label=args.label,
        note=args.note,
    )
    print(result.render())
    if args.reconcile or result.refused:
        print("\nreconciliation:\n" + result.reconciliation)
    return 1 if result.refused else 0


def cmd_list(args) -> int:
    with _db(args) as db:
        builds = db.builds()
        if not builds:
            print("no builds yet")
            return 0
        for b in builds:
            print(f"{b.name:<22} {b.built_at}  {b.pages:>6,} pages  {b.edges:>7,} edges"
                  f"  corpus {b.corpus_stamp}")
    return 0


def cmd_rank(args) -> int:
    with _db(args) as db:
        build = _resolve(db, args)
        if build is None:
            return 1
        rows = db.top(build.id, by=args.by, limit=args.top, company=args.company,
                      category=args.category)
        if args.json:
            _emit(args, rows)
            return 0
        print(f"{build.name} — top {len(rows)} by {args.by}")
        print(f"{'#':>4} {'pages':>7} {'refs':>7} {args.by:>10}  page")
        for i, row in enumerate(rows, 1):
            score = row[args.by]
            shown = f"{score:.5f}" if isinstance(score, float) else f"{score:,}"
            print(f"{i:>4} {row['in_pages']:>7,} {row['in_refs']:>7,} {shown:>10}  "
                  f"{report_mod._short(row['url'], 60)}")
    return 0


def cmd_page(args) -> int:
    with _db(args) as db:
        build = _resolve(db, args)
        if build is None:
            return 1
        url = canonicalise(args.url)
        node = db.node(build.id, url)
        if node is None:
            print(f"not in build {build.name}: {url}", file=sys.stderr)
            return 1
        if args.json:
            _emit(args, {"node": node, "inbound": db.inbound(build.id, url, limit=args.top),
                         "outbound": db.outbound(build.id, url, limit=args.top),
                         "aliases": db.anchors_for(build.id, url)})
            return 0
        print(f"{node['title']}\n{url}\n")
        print(f"  company/category {node['company']} / {node['category']}")
        print(f"  size             {node['body_chars']:,} chars")
        print(f"  linked by        {node['in_pages']:,} pages "
              f"({node['in_refs']:,} occurrences)")
        print(f"  links out to     {node['out_pages']:,} pages")
        print(f"  pagerank         {node['pagerank']:.6f}  "
              f"(#{db.rank_of(build.id, url)})")
        print(f"  authority / hub  {node['authority']:.6f} / {node['hub']:.6f}")
        print(f"  depth            {node['depth'] if node['depth'] is not None else 'unreachable'}")
        aliases = db.anchors_for(build.id, url)
        if aliases:
            print("\n  called, by other pages:")
            for anchor, count in aliases[:args.top]:
                print(f"    {count:>5}×  {anchor[:70]}")
        inbound = db.inbound(build.id, url, limit=args.top)
        if inbound:
            print("\n  linked from (by pagerank):")
            for row in inbound:
                print(f"    {row['occurrences']:>4}×  {report_mod._short(row['url'], 60)}")
    return 0


def cmd_taxonomy(args) -> int:
    with _db(args) as db:
        build = _resolve(db, args)
        if build is None:
            return 1
        rows = db.terms(build.id, kind=args.kind, company=args.company,
                        parent=args.parent, limit=args.top)
        if args.json:
            _emit(args, rows)
            return 0
        print(f"{build.name} — {args.kind or 'all kinds'}"
              + (f" under {args.parent!r}" if args.parent else ""))
        print(f"{'pages':>7} {'refs':>8}  term")
        for row in rows:
            parent = f"  [{row['parent']}]" if row["parent"] else ""
            print(f"{row['pages']:>7,} {row['refs']:>8,}  {row['term']}{parent}")
    return 0


def cmd_stats(args) -> int:
    with _db(args) as db:
        build = _resolve(db, args)
        if build is None:
            return 1
        nodes = [dict(r) for r in db.conn.execute(
            "SELECT * FROM nodes WHERE build_id = ?", (build.id,))]
        for node in nodes:
            node["breadcrumbs"] = json.loads(node["breadcrumbs"] or "[]")
            node["code_languages"] = json.loads(node["code_languages"] or "[]")
        groups = (stats_mod.by_breadcrumb(nodes, depth=args.depth)
                  if args.by == "breadcrumb" else stats_mod.by_category(nodes))
        if args.json:
            _emit(args, {"groups": [vars(g) for g in groups],
                         "size_profile": stats_mod.size_profile(nodes),
                         "recency": stats_mod.recency(nodes)})
            return 0
        print(f"{build.name} — by {args.by}")
        print(f"{'pages':>7} {'median':>8} {'rank%':>7} {'orph':>5}  group")
        for group in groups[:args.top]:
            print(f"{group.pages:>7,} {group.median_chars:>8,} "
                  f"{100 * group.share_of_rank:>6.2f}% {group.orphans:>5,}  "
                  f"{group.company}/{group.key}")
        profile = stats_mod.size_profile(nodes)
        print(f"\nsizes  median {profile['median']:,}  p90 {profile['p90']:,}  "
              f"max {profile['max']:,}  over 500 KB: {profile['over_500kb']}")
    return 0


def cmd_report(args) -> int:
    with _db(args) as db:
        build = _resolve(db, args)
        if build is None:
            return 1
        if args.write:
            md_path, json_path = report_mod.write(db, build, report_dir=args.report_dir)
            print(f"wrote {md_path}\nwrote {json_path}")
            print()
            print(report_mod.summarise(db, build))
        else:
            print(report_mod.render(db, build))
    return 0


def cmd_image(args) -> int:
    with _db(args) as db:
        build = _resolve(db, args)
        if build is None:
            return 1
        base = Path(args.report_dir or report_mod.DEFAULT_REPORT_DIR)
        base.mkdir(parents=True, exist_ok=True)
        kinds = sorted(viz_mod.VIEWS) if args.all else [args.kind]
        for kind in kinds:
            if kind == "ego" and not args.url:
                if args.all:
                    # The ego view needs a subject, and picking one silently would make
                    # `--all` quietly mean something different every build.
                    print("skipping ego: pass --url to draw one page's neighbourhood",
                          file=sys.stderr)
                    continue
                print("the ego view needs --url", file=sys.stderr)
                return 1
            try:
                top = args.top or viz_mod.DEFAULT_TOP[kind]
                svg = viz_mod.render(db, build, kind, theme=args.theme, top=top,
                                     url=args.url, width=args.width, height=args.height)
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1
            suffix = "" if args.theme == "light" else f"-{args.theme}"
            out = (Path(args.out) if args.out and not args.all
                   else base / f"{build.id:04d}-{kind}{suffix}.svg")
            out.write_text(svg, encoding="utf-8")
            print(f"wrote {out}  ({len(svg):,} bytes)")
    return 0


def cmd_gc(args) -> int:
    with _db(args) as db:
        removed = db.prune(args.keep)
        print(f"removed {len(removed)} build(s)" + (f": {removed}" if removed else ""))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Graph and metadata analysis over the corpus.")
    ap.add_argument("--config", default="config/sources.yaml")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("build", help="scan data/, classify links, rank, store")
    p.add_argument("--label", help="a name you will recognise later, e.g. baseline")
    p.add_argument("--note")
    p.add_argument("--reconcile", action="store_true",
                   help="always print the link accounting, not only on refusal")
    _add_store_args(p)
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("list", help="builds so far")
    _add_store_args(p)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("rank", help="hubs and authorities")
    p.add_argument("--build", help="id, label, or 'latest'")
    p.add_argument("--by", default="pagerank", choices=RANK_COLUMNS)
    p.add_argument("--top", type=int, default=20)
    p.add_argument("--company")
    p.add_argument("--category")
    p.add_argument("--json", action="store_true")
    _add_store_args(p)
    p.set_defaults(func=cmd_rank)

    p = sub.add_parser("page", help="one page: rank, neighbours, and what it is called")
    p.add_argument("url")
    p.add_argument("--build")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--json", action="store_true")
    _add_store_args(p)
    p.set_defaults(func=cmd_page)

    p = sub.add_parser("taxonomy", help="the vocabularies the corpus already contains")
    p.add_argument("--build")
    p.add_argument("--kind", choices=TERM_KINDS)
    p.add_argument("--company")
    p.add_argument("--parent", help="breadcrumb trail to list beneath")
    p.add_argument("--top", type=int, default=30)
    p.add_argument("--json", action="store_true")
    _add_store_args(p)
    p.set_defaults(func=cmd_taxonomy)

    p = sub.add_parser("stats", help="density, thinness, orphans and recency")
    p.add_argument("--build")
    p.add_argument("--by", default="category", choices=("category", "breadcrumb"))
    p.add_argument("--depth", type=int, default=1, help="breadcrumb depth to group at")
    p.add_argument("--top", type=int, default=25)
    p.add_argument("--json", action="store_true")
    _add_store_args(p)
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("report", help="the full Markdown report")
    p.add_argument("--build")
    p.add_argument("--write", action="store_true", help="also write reports/graph/")
    _add_store_args(p)
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("image", help="SVG views of the graph, for slides")
    p.add_argument("--build")
    p.add_argument("--kind", default="hubs", choices=sorted(viz_mod.VIEWS))
    p.add_argument("--all", action="store_true", help="every view except ego")
    p.add_argument("--url", help="the subject page, for --kind ego")
    p.add_argument("--top", type=int, help="how many nodes or rows to draw "
                   "(default: per view — 70 hubs, 28 correction, 14 ego, 45 categories)")
    p.add_argument("--theme", default="light", choices=("light", "dark"))
    p.add_argument("--width", type=int, default=1400)
    p.add_argument("--height", type=int, default=900)
    p.add_argument("--out", help="output path (single --kind only)")
    _add_store_args(p)
    p.set_defaults(func=cmd_image)

    p = sub.add_parser("gc", help="drop all but the newest builds")
    p.add_argument("--keep", type=int, default=3)
    _add_store_args(p)
    p.set_defaults(func=cmd_gc)

    args = ap.parse_args()
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    raise SystemExit(args.func(args))
