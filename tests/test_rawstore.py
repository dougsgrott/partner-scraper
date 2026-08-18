"""The raw archive: path mirroring, safety, and the gz round-trip."""

from __future__ import annotations

import gzip

import pytest

from scraper.fetch import rawstore

DBX = "https://docs.databricks.com/aws/en/delta/"
ANT = "https://platform.claude.com/docs/en/build-with-claude/prompt-caching"


def rel(url: str, company: str = "x", **kw) -> str:
    return str(rawstore.relative_path_for(url, company, **kw))


# --- path mirroring -------------------------------------------------------

def test_trailing_slash_becomes_index():
    assert rel(DBX, "databricks") == "databricks/docs.databricks.com/aws/en/delta/index.html.gz"


def test_leaf_url_keeps_its_name():
    assert rel(ANT, "anthropic", ext="md") == (
        "anthropic/platform.claude.com/docs/en/build-with-claude/prompt-caching.md.gz"
    )


def test_bare_host_becomes_index():
    assert rel("https://x.com", "c") == "c/x.com/index.html.gz"
    assert rel("https://x.com/", "c") == "c/x.com/index.html.gz"


def test_page_and_directory_of_same_name_do_not_collide():
    """`/a/b` and `/a/b/` are different pages on some sites; they must be different files."""
    assert rel("https://x.com/a/b", "c") != rel("https://x.com/a/b/", "c")
    assert rel("https://x.com/a/b", "c") == "c/x.com/a/b.html.gz"
    assert rel("https://x.com/a/b/", "c") == "c/x.com/a/b/index.html.gz"


def test_sibling_page_and_child_page_coexist():
    """`a/b.html.gz` (file) and `a/b/c.html.gz` (dir) can both exist — no name clash."""
    assert rel("https://x.com/a/b", "c") == "c/x.com/a/b.html.gz"
    assert rel("https://x.com/a/b/c", "c") == "c/x.com/a/b/c.html.gz"


def test_query_string_does_not_overwrite_the_plain_page():
    assert rel("https://x.com/p") != rel("https://x.com/p?v=2")
    assert rel("https://x.com/p?v=2") != rel("https://x.com/p?v=3")


def test_extension_reflects_content():
    assert rel(ANT, "a", ext="md").endswith(".md.gz")
    assert rel(ANT, "a", ext=".md").endswith(".md.gz")     # leading dot tolerated
    assert rel(ANT, "a", ext="html").endswith(".html.gz")


# --- safety ---------------------------------------------------------------

@pytest.mark.parametrize("url", [
    "https://x.com/../../etc/passwd",
    "https://x.com/a/../../../../etc/passwd",
    "https://x.com/./.././sneaky",
])
def test_traversal_segments_are_neutralised(url, tmp_path):
    path = rawstore.path_for(url, "c", base_dir=tmp_path)
    assert path.resolve().is_relative_to(tmp_path.resolve())
    assert ".." not in path.parts


def test_dotfiles_are_not_created(tmp_path):
    path = rawstore.path_for("https://x.com/.env", "c", base_dir=tmp_path)
    assert not path.name.startswith(".")


def test_windows_reserved_names_are_escaped():
    """Archives get zipped and synced to other platforms; `con.html.gz` breaks that."""
    assert rel("https://x.com/con") == "x/x.com/_con.html.gz"
    assert rel("https://x.com/COM1") == "x/x.com/_COM1.html.gz"
    assert rel("https://x.com/console") == "x/x.com/console.html.gz"   # only exact names


def test_long_segments_are_truncated_but_stay_distinct():
    a = rel("https://x.com/" + "a" * 300)
    b = rel("https://x.com/" + "a" * 299 + "b")
    assert a != b                                   # hash suffix keeps them apart
    assert all(len(part) <= 110 for part in a.split("/"))


def test_unsafe_characters_are_replaced():
    assert "%" not in rel("https://x.com/a%20b")
    assert " " not in rel("https://x.com/a b")


def test_same_url_always_maps_to_the_same_path():
    assert rel(DBX, "databricks") == rel(DBX, "databricks")


# --- round-trip -----------------------------------------------------------

def test_write_read_round_trip(tmp_path):
    body = b"<html><body>caf\xc3\xa9 \x00 binary-ish</body></html>"
    path = rawstore.write(DBX, "databricks", body, base_dir=tmp_path)
    assert rawstore.read(path) == body


def test_written_file_is_real_gzip(tmp_path):
    path = rawstore.write(DBX, "databricks", b"hello", base_dir=tmp_path)
    assert path.read_bytes()[:2] == b"\x1f\x8b"
    with gzip.open(path, "rb") as fh:
        assert fh.read() == b"hello"


def test_identical_content_produces_identical_bytes(tmp_path):
    """mtime is zeroed, so an unchanged page leaves the archive untouched."""
    first = rawstore.write(DBX, "d", b"same", base_dir=tmp_path).read_bytes()
    second = rawstore.write(DBX, "d", b"same", base_dir=tmp_path).read_bytes()
    assert first == second


def test_rewrite_replaces_content(tmp_path):
    rawstore.write(DBX, "d", b"old", base_dir=tmp_path)
    path = rawstore.write(DBX, "d", b"new", base_dir=tmp_path)
    assert rawstore.read(path) == b"new"


def test_no_temp_files_left_behind(tmp_path):
    rawstore.write(DBX, "d", b"x", base_dir=tmp_path)
    assert list(tmp_path.rglob("*.tmp")) == []


def test_empty_body_round_trips(tmp_path):
    path = rawstore.write(DBX, "d", b"", base_dir=tmp_path)
    assert rawstore.read(path) == b""


# --- helpers --------------------------------------------------------------

def test_ext_for_content_type():
    assert rawstore.ext_for("text/markdown; charset=utf-8") == "md"
    assert rawstore.ext_for("text/html; charset=utf-8") == "html"
    assert rawstore.ext_for(None) == "html"
    assert rawstore.ext_for(None, "https://x.com/a.md") == "md"
    assert rawstore.ext_for("application/json") == "json"


def test_sha256_is_content_addressed():
    assert rawstore.sha256(b"a") == rawstore.sha256(b"a")
    assert rawstore.sha256(b"a") != rawstore.sha256(b"b")


def test_percent_encoding_does_not_collide_with_its_decoded_form():
    """`%` is replaced rather than decoded, so `/a b` and `/a%20b` stay distinct."""
    assert rel("https://x.com/a b") == "x/x.com/a_b.html.gz"
    assert rel("https://x.com/a%20b") == "x/x.com/a_20b.html.gz"


def test_claimed_by_detects_collisions():
    """Sanitising is lossy, so two URLs *can* land on one file. That must be visible."""
    a, b = "https://x.com/a b", "https://x.com/a_b"
    assert rel(a, "c") == rel(b, "c")                        # a genuine collision
    owners = {rel(a, "c"): a}
    assert rawstore.claimed_by(b, "c", owners) == a          # reported
    assert rawstore.claimed_by(a, "c", owners) is None       # same URL is not a collision
    assert rawstore.claimed_by("https://x.com/other", "c", owners) is None
