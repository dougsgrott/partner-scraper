"""Dump parsing, scope filtering, and the worklist funnel."""

from __future__ import annotations

from datetime import date

import pytest

from scraper.config import Filters, SourceConfig
from scraper.worklist import build, dumps
from scraper.worklist import filters as flt
from scraper.worklist.sitemap import DiscoveredURL

DUMP = """\
2024-05-19  https://example.com/docs/en/a
----------  https://example.com/docs/en/b
2026-08-13  https://example.com/cookbook/c
----------  https://example.com/docs/es/localized
"""


@pytest.fixture
def dump_file(tmp_path):
    p = tmp_path / "urls.txt"
    p.write_text(DUMP, encoding="utf-8")
    return p


def source(**kw) -> SourceConfig:
    base = {
        "company": "example",
        "seeds": [{"type": "dump", "path": "unused.txt"}],
        "include_paths": ["/docs/en/"],
    }
    return SourceConfig.model_validate({**base, **kw})


# --- dump parsing ---------------------------------------------------------

def test_parse_dated_and_undated_lines():
    assert dumps.parse_line("2024-05-19  https://x.com/a") == DiscoveredURL("https://x.com/a", date(2024, 5, 19))
    assert dumps.parse_line("----------  https://x.com/b") == DiscoveredURL("https://x.com/b", None)


def test_parse_skips_junk():
    assert dumps.parse_line("") is None
    assert dumps.parse_line("   ") is None
    assert dumps.parse_line("# comment") is None
    assert dumps.parse_line("2024-01-01  not-a-url") is None


def test_parse_bare_url_without_lastmod_column():
    assert dumps.parse_line("https://x.com/a") == DiscoveredURL("https://x.com/a", None)


def test_read_dedupes_and_preserves_order(dump_file):
    dump_file.write_text(DUMP + "----------  https://example.com/docs/en/a\n", encoding="utf-8")
    items = dumps.read(dump_file)
    assert [i.url for i in items] == [
        "https://example.com/docs/en/a",
        "https://example.com/docs/en/b",
        "https://example.com/cookbook/c",
        "https://example.com/docs/es/localized",
    ]
    # first occurrence wins, so the date survives
    assert items[0].lastmod == date(2024, 5, 19)


def test_read_missing_dump_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        dumps.read(tmp_path / "nope.txt")


# --- scope filters --------------------------------------------------------

def test_include_and_exclude():
    urls = [DiscoveredURL(f"https://x.com{p}", None) for p in ("/docs/en/a", "/docs/es/a", "/docs/en/archive/b")]
    src = source(exclude_paths=["/docs/en/archive/"])
    assert [u.url for u in flt.apply(urls, src, Filters())] == ["https://x.com/docs/en/a"]


def test_date_window_keeps_undated():
    urls = [
        DiscoveredURL("https://x.com/docs/en/old", date(2020, 1, 1)),
        DiscoveredURL("https://x.com/docs/en/new", date(2026, 1, 1)),
        DiscoveredURL("https://x.com/docs/en/undated", None),
    ]
    kept = flt.apply(urls, source(), Filters(published_after=date(2025, 1, 1)))
    assert {u.url for u in kept} == {"https://x.com/docs/en/new", "https://x.com/docs/en/undated"}


def test_apply_does_not_cap():
    """max_pages belongs to build(), after robots — see filters.py docstring."""
    urls = [DiscoveredURL(f"https://x.com/docs/en/{i}", None) for i in range(10)]
    assert len(flt.apply(urls, source(), Filters(max_pages=3))) == 10


# --- the funnel -----------------------------------------------------------

def test_build_offline_counts(dump_file):
    src = source(seeds=[{"type": "dump", "path": str(dump_file)}])
    wl = build("s", src, use_sitemaps=False)
    assert wl.counts.seeded == 4
    assert wl.counts.in_scope == 2          # the /cookbook/ and /docs/es/ URLs drop out
    assert wl.counts.out_of_scope == 2
    assert wl.counts.final == 2


def test_build_applies_cap_after_robots(dump_file):
    class BlockOne:
        def allows(self, url: str) -> bool:
            return not url.endswith("/a")

    src = source(seeds=[{"type": "dump", "path": str(dump_file)}])
    wl = build("s", src, Filters(max_pages=1), robots=BlockOne(), use_sitemaps=False)

    assert wl.counts.in_scope == 2
    assert wl.counts.robots_blocked == 1
    # The cap is spent on a URL we are actually allowed to fetch, not on the blocked one.
    assert wl.counts.final == 1
    assert wl.urls[0].url.endswith("/b")


def test_build_respects_disabled_robots(dump_file):
    class BlockAll:
        def allows(self, url: str) -> bool:
            return False

    src = source(seeds=[{"type": "dump", "path": str(dump_file)}])
    wl = build("s", src, robots=BlockAll(), respect_robots=False, use_sitemaps=False)
    assert wl.counts.robots_blocked == 0
    assert wl.counts.final == 2
