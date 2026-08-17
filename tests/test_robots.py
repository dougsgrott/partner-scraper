"""robots.txt parsing and matching — the rules that decide what we may fetch."""

from __future__ import annotations

from scraper.worklist.robots import Robots, origin_of, parse

# The real docs.databricks.com file, trimmed to the rules that matter to us.
DATABRICKS = """
User-agent: *
Allow: /

# Block internal search pages and results
Disallow: *s=*

Disallow: /aws/en/search-for

# Allow crawling of language-specific directories
Allow: /aws/en/

# Hide archived docs from search indexers
Disallow: /aws/en/archive/

Sitemap: https://docs.databricks.com/sitemap.xml
"""

ANTHROPIC = """
User-Agent: *
Disallow: /api/

Sitemap: https://platform.claude.com/sitemap.xml
Sitemap: https://platform.claude.com/cookbook/sitemap.xml
"""


def test_databricks_scope_is_allowed():
    r = parse(DATABRICKS)
    assert r.allows("https://docs.databricks.com/aws/en/delta/")
    assert r.allows("https://docs.databricks.com/aws/en/mlflow3/genai/")


def test_databricks_archive_is_disallowed():
    """Longest-match-wins: /aws/en/archive/ must beat the shorter Allow: /aws/en/."""
    r = parse(DATABRICKS)
    assert not r.allows("https://docs.databricks.com/aws/en/archive/old-page")
    assert not r.allows("https://docs.databricks.com/aws/en/search-for")


def test_wildcard_patterns_match_path_and_query():
    """`*` rules are the ones urllib.robotparser silently ignores.

    Rules are matched against path *and* query — `Disallow: *s=*` exists to block `?s=`
    search URLs, so matching the path alone would silently permit every one of them.
    """
    r = parse("User-agent: *\nDisallow: *s=*\n")
    assert not r.allows("https://x.com/aws/en/foo?s=query")   # matched via the query
    assert not r.allows("https://x.com/aws/en/foos=bar")      # matched in the path
    assert r.allows("https://x.com/aws/en/some-thing")        # no literal "s="


def test_longest_match_wins_over_a_shorter_wildcard():
    """Databricks' real file: `Allow: /aws/en/` (8) outranks `Disallow: *s=*` (4).

    That is the documented precedence rule, so a `?s=` URL under /aws/en/ is technically
    crawlable. We never construct one — search URLs are not in any sitemap, and
    /aws/en/search-for is excluded outright — so conforming here costs us nothing.
    """
    assert parse(DATABRICKS).allows("https://docs.databricks.com/aws/en/foo?s=query")


def test_sitemaps_are_collected_regardless_of_group():
    assert parse(ANTHROPIC).sitemaps == [
        "https://platform.claude.com/sitemap.xml",
        "https://platform.claude.com/cookbook/sitemap.xml",
    ]


def test_anthropic_docs_allowed_api_blocked():
    r = parse(ANTHROPIC)
    assert r.allows("https://platform.claude.com/docs/en/build-with-claude/prompt-caching")
    assert r.allows("https://platform.claude.com/cookbook/tool-use-tool-choice")
    assert not r.allows("https://platform.claude.com/api/anything")


def test_end_anchor():
    r = parse("User-agent: *\nDisallow: /foo$\n")
    assert not r.allows("/foo")
    assert r.allows("/foo/bar")
    assert r.allows("/foobar")


def test_empty_disallow_means_allow_everything():
    r = parse("User-agent: *\nDisallow:\n")
    assert r.allows("/anything")


def test_allow_wins_exact_length_tie():
    r = parse("User-agent: *\nDisallow: /x/\nAllow: /x/\n")
    assert r.allows("/x/page")


def test_specific_agent_group_beats_wildcard():
    text = (
        "User-agent: *\nDisallow: /\n\n"
        "User-agent: indicium-docs-scraper\nAllow: /\n"
    )
    assert parse(text, user_agent="indicium-docs-scraper/0.2 (+x@y.z)").allows("/anything")
    assert not parse(text, user_agent="other-bot/1.0").allows("/anything")


def test_comments_and_blank_lines_ignored():
    r = parse("# hello\nUser-agent: *   # trailing\nDisallow: /private/ # why\n")
    assert not r.allows("/private/x")
    assert r.allows("/public/x")


def test_no_rules_means_allowed():
    assert Robots().allows("/anything")


def test_grouped_agents_share_rules():
    """Consecutive User-agent lines form one group; a rule line closes it."""
    r = parse("User-agent: a\nUser-agent: b\nDisallow: /x/\n\nUser-agent: *\nAllow: /\n")
    assert not parse("User-agent: a\nUser-agent: b\nDisallow: /x/\n", user_agent="b").allows("/x/y")
    assert r.allows("/x/y")  # the `*` group applies to us


def test_origin_of():
    assert origin_of("https://docs.databricks.com/aws/en/delta/") == "https://docs.databricks.com"
