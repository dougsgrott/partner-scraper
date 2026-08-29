"""Structural checks over the corpus files. See docs/validation-plan.md §1.

These are the ad-hoc greps from steps 5–8 turned into named, repeatable checks. Each one
corresponds to a defect that actually reached the corpus, so a regression announces itself
instead of waiting to be noticed by a reader.

Equally important is what these must **not** flag. Pages that document `404 Not Found`,
code fences containing `<div>`, and `[string]()` type names in the API reference are all
correct, and earlier versions of these rules rejected every one of them.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from ..extract import mdx
from ..extract.base import MIN_BODY_CHARS, _unclosed_fence
from ..store import writer
from .report import Check, failed, passed, skipped, warned

# One entry per historical defect. `outside_code` rules ignore code, because a docs page
# may legitimately *show* the very markup we are looking for — and several do.
LEAKS: tuple[tuple[str, str, bool], ...] = (
    ("html_markup",        r"<(?:div|span|section|nav|header|footer)\b", True),
    ("html_attributes",    r'\sclass="',                                 True),
    ("data_uri_images",    r"\]\(data:",                                 False),
    ("private_use_glyphs", "[\ue000-\uf8ff]",                            False),
    ("screen_reader_text", r"\(opens in new tab\)",                      False),
)

# One definition of "this is code", shared with the extractor that has to respect it.
# Both halves are load-bearing: `/aws/en/sql/user-alerts-create` lists the HTML tags an
# alert may contain as `` `<div>` ``, and `/internal/directives` documents a `:::div`
# directive the same way. Matching those is a false positive of exactly the kind that made
# the extraction quality gate reject real pages (docs/lessons-learned.md §3).
strip_code = mdx.strip_code


def load(data_dir: str | Path = "data") -> list[tuple[Path, dict, str]]:
    """Every corpus file as `(path, frontmatter, body)`."""
    pages = []
    for path in sorted(Path(data_dir).rglob("*.md")):
        front, body = writer.parse(path)
        pages.append((path, front, body))
    return pages


def check_leaks(pages: list[tuple[Path, dict, str]]) -> list[Check]:
    checks = []
    for name, pattern, outside_code in LEAKS:
        rx = re.compile(pattern)
        hits = [str(p) for p, _, body in pages
                if rx.search(strip_code(body) if outside_code else body)]
        checks.append(
            passed(name, f"clean across {len(pages)} files", total=len(pages))
            if not hits else
            failed(name, f"{len(hits)} file(s) contain {pattern}",
                   count=len(hits), total=len(pages), samples=hits)
        )
    return checks


def check_rooted_links(pages: list[tuple[Path, dict, str]], cfg=None) -> Check:
    """Site-rooted links that should have been absolutised.

    Only paths that point into a configured source count. `/Workspace/absolute/path/to/
    image.png` in a notebook page is an example path in prose, not a broken link — the
    naive rule flagged it, which would have taught everyone to ignore this check.
    """
    prefixes = tuple(sorted({p for src in (cfg.enabled_sources().values() if cfg else [])
                             for p in src.include_paths}))
    if not prefixes:
        return skipped("rooted_links", "no include_paths configured to judge against")

    rx = re.compile(r"\]\((/(?!/)[^)\s]*)\)")
    hits = []
    for path, _, body in pages:
        targets = [m.group(1) for m in rx.finditer(strip_code(body))
                   if m.group(1).startswith(prefixes)]
        if targets:
            hits.append(f"{path}  ({targets[0]})")
    if hits:
        return failed("rooted_links", f"{len(hits)} file(s) link into a source by bare path",
                      count=len(hits), total=len(pages), samples=hits)
    return passed("rooted_links", f"no unresolved in-site links across {len(pages)} files",
                  total=len(pages))


_COMPONENT = re.compile(r"<([A-Z][A-Za-z0-9]*)\b")


def check_mdx_converted(pages: list[tuple[Path, dict, str]]) -> Check:
    """No structural MDX component may survive into the corpus.

    Anthropic publishes MDX, so `<Card href=…>` reaches us holding links no Markdown
    parser can see — 562 of them, across a third of that source. `extract/mdx.py`
    converts the families the site uses; this catches the day it starts using a shape the
    converter does not handle, or a page where conversion silently failed.
    """
    hits = []
    for path, _, body in pages:
        names = set(_COMPONENT.findall(strip_code(body))) & mdx.KNOWN
        if names:
            hits.append(f"{path}  ({', '.join(sorted(names))})")
    if hits:
        return failed("mdx_converted", f"{len(hits)} file(s) still carry MDX components",
                      count=len(hits), total=len(pages), samples=hits)
    return passed("mdx_converted", f"no unconverted components across {len(pages)} files",
                  total=len(pages))


def check_titles(pages: list[tuple[Path, dict, str]]) -> Check:
    """Every document opens with a heading naming it (§7.3)."""
    bad = [str(p) for p, front, body in pages
           if not (body.lstrip().startswith("# ")
                   or _opens_with_own_name(body, str(front.get("title", ""))))]
    if bad:
        return failed("opens_with_its_title", f"{len(bad)} file(s) start unnamed",
                      count=len(bad), total=len(pages), samples=bad)
    return passed("opens_with_its_title", f"all {len(pages)} files name themselves first",
                  total=len(pages))


def _opens_with_own_name(body: str, title: str) -> bool:
    first = next((line for line in body.splitlines() if line.strip()), "")
    return bool(title) and first.startswith("#") and \
        first.lstrip("#").strip().casefold() == title.strip().casefold()


def check_fences(pages: list[tuple[Path, dict, str]]) -> Check:
    bad = [str(p) for p, _, body in pages if _unclosed_fence(body)]
    if bad:
        return failed("code_fences_closed", f"{len(bad)} file(s) have an unclosed fence",
                      count=len(bad), total=len(pages), samples=bad)
    return passed("code_fences_closed", f"balanced in {len(pages)} files", total=len(pages))


def check_body_length(pages: list[tuple[Path, dict, str]]) -> Check:
    short = [(len(body.strip()), str(p)) for p, _, body in pages
             if len(body.strip()) < MIN_BODY_CHARS]
    if short:
        return failed("body_length", f"{len(short)} file(s) below {MIN_BODY_CHARS} chars",
                      count=len(short), total=len(pages),
                      samples=[f"{n} chars  {p}" for n, p in sorted(short)])
    return passed("body_length", f"all bodies ≥ {MIN_BODY_CHARS} chars", total=len(pages))


# Fields every page must carry, and fields a source is expected to supply.
REQUIRED = ("title", "company", "source_id", "category", "source_url", "extractor",
            "content_hash", "extracted_at")
EXPECTED_BY_SOURCE = {
    "databricks-docs": ("description", "updated_date", "breadcrumbs"),
    "anthropic-cookbook": ("description", "published_date", "source_file_url", "authors"),
}


def check_frontmatter(pages: list[tuple[Path, dict, str]]) -> list[Check]:
    missing = [f"{p} (no {f})" for p, front, _ in pages for f in REQUIRED if not front.get(f)]
    checks = [
        passed("frontmatter_required", f"all {len(REQUIRED)} required fields present",
               total=len(pages))
        if not missing else
        failed("frontmatter_required", f"{len(missing)} missing required field(s)",
               count=len(missing), total=len(pages), samples=missing)
    ]

    for source, fields in EXPECTED_BY_SOURCE.items():
        subset = [(p, front) for p, front, _ in pages if front.get("source_id") == source]
        if not subset:
            continue
        gaps = {f: sum(1 for _, front in subset if not front.get(f)) for f in fields}
        thin = {f: n for f, n in gaps.items() if n}
        checks.append(
            passed(f"frontmatter_{source}", f"{len(subset)} pages carry {', '.join(fields)}",
                   total=len(subset))
            if not thin else
            warned(f"frontmatter_{source}",
                   "incomplete: " + ", ".join(f"{f} missing on {n}" for f, n in thin.items()),
                   count=sum(thin.values()), total=len(subset), detail=gaps)
        )
    return checks


def check_duplicate_bodies(pages: list[tuple[Path, dict, str]]) -> Check:
    """Identical bodies under different URLs — real on doc sites (aliases), worth knowing."""
    groups: dict[str, list[str]] = {}
    for _, front, _ in pages:
        groups.setdefault(str(front.get("content_hash")), []).append(str(front.get("source_url")))
    dupes = {h: urls for h, urls in groups.items() if len(urls) > 1}
    if not dupes:
        return passed("duplicate_bodies", "every page body is distinct", total=len(pages))
    return warned("duplicate_bodies",
                  f"{len(dupes)} group(s) of identical bodies under different URLs",
                  count=sum(len(u) for u in dupes.values()), total=len(pages),
                  samples=[" = ".join(u[:2]) for u in list(dupes.values())[:5]])


def check_size_distribution(pages: list[tuple[Path, dict, str]], *,
                            outlier_chars: int = 500_000) -> Check:
    """Outliers are not defects, but anything that chunks the corpus needs to know."""
    sizes = sorted((len(body), str(p)) for p, _, body in pages)
    if not sizes:
        return failed("size_distribution", "no pages found")
    big = [(n, p) for n, p in sizes if n >= outlier_chars]
    median = sizes[len(sizes) // 2][0]
    detail = {"median_chars": median, "max_chars": sizes[-1][0],
              "over_threshold": len(big), "threshold": outlier_chars}
    summary = f"median {median:,} chars, largest {sizes[-1][0]:,}, {len(big)} over {outlier_chars:,}"
    return warned("size_distribution", summary, count=len(big), total=len(pages),
                  samples=[f"{n:,} chars  {p}" for n, p in reversed(big[-5:])], detail=detail) \
        if big else passed("size_distribution", summary, total=len(pages), detail=detail)


def check_categories(pages: list[tuple[Path, dict, str]]) -> Check:
    """All singletons or one giant bucket means the category rule is wrong for a site."""
    per_company: dict[str, Counter] = {}
    for _, front, _ in pages:
        per_company.setdefault(str(front.get("company")), Counter())[str(front.get("category"))] += 1

    detail, suspicious = {}, []
    for company, counts in per_company.items():
        singletons = sum(1 for n in counts.values() if n == 1)
        biggest, biggest_n = counts.most_common(1)[0]
        share = biggest_n / sum(counts.values())
        detail[company] = {"categories": len(counts), "singletons": singletons,
                           "largest": biggest, "largest_share": round(share, 3)}
        if len(counts) > 1 and singletons / len(counts) > 0.8:
            suspicious.append(f"{company}: {singletons}/{len(counts)} categories hold one page")
        if share > 0.9 and len(counts) > 1:
            suspicious.append(f"{company}: {share:.0%} of pages in '{biggest}'")

    summary = ", ".join(f"{c} {d['categories']} categories" for c, d in detail.items())
    return warned("category_distribution", "; ".join(suspicious), count=len(suspicious),
                  detail=detail) if suspicious else \
        passed("category_distribution", summary, total=len(pages), detail=detail)


def run(data_dir: str | Path = "data", cfg=None) -> list[Check]:
    pages = load(data_dir)
    if not pages:
        return [failed("corpus_present", f"no Markdown files under {data_dir}")]
    return [
        passed("corpus_present", f"{len(pages)} files", total=len(pages)),
        *check_leaks(pages),
        check_rooted_links(pages, cfg),
        check_mdx_converted(pages),
        check_titles(pages),
        check_fences(pages),
        check_body_length(pages),
        *check_frontmatter(pages),
        check_duplicate_bodies(pages),
        check_size_distribution(pages),
        check_categories(pages),
    ]
