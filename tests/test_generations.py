"""Archived scraping sessions — plans/raw-archive-plan.md.

The claim under test is that a generation is a *moment*: what it holds is what the vendors
served that day, and a later fetch cannot reach back and change it. That property comes from
hard links plus `rawstore`'s atomic replace, so it is asserted directly rather than assumed.
"""

from __future__ import annotations

import pytest

from scraper.fetch import generations, rawstore


def write_page(raw_dir, url: str, body: bytes) -> None:
    rawstore.write(url, "databricks", body, ext="html", base_dir=raw_dir)


@pytest.fixture
def raw(tmp_path):
    root = tmp_path / "raw"
    write_page(root, "https://docs.databricks.com/aws/en/a", b"<html>first</html>")
    write_page(root, "https://docs.databricks.com/aws/en/b", b"<html>other</html>")
    return root


def test_a_generation_records_what_it_holds(raw, tmp_path):
    gen = generations.archive(label="g1", raw_dir=raw, archive_dir=tmp_path / "archive")

    assert gen.files == 2
    assert gen.bytes > 0
    assert (gen.path / "manifest.json").exists()
    assert generations.verify(gen) == (2, 2)


def test_an_archived_generation_survives_a_later_overwrite(raw, tmp_path):
    """The property the whole scheme rests on.

    `rawstore.write` never writes in place — it builds a temp file and calls `os.replace` —
    so a refresh swaps the directory entry and the archived hard link keeps pointing at the
    old inode. Without that, archiving would be a copy and cost 55 MiB every run.
    """
    gen = generations.archive(label="g1", raw_dir=raw, archive_dir=tmp_path / "archive")
    archived = gen.path / rawstore.relative_path_for(
        "https://docs.databricks.com/aws/en/a", "databricks")

    write_page(raw, "https://docs.databricks.com/aws/en/a", b"<html>REWRITTEN</html>")

    assert rawstore.read(archived) == b"<html>first</html>"
    live = rawstore.path_for("https://docs.databricks.com/aws/en/a", "databricks", base_dir=raw)
    assert rawstore.read(live) == b"<html>REWRITTEN</html>"


def test_archiving_costs_no_data_blocks(raw, tmp_path):
    """Hard links, not copies — asserted by inode identity rather than by `du`.

    At two files the directory overhead swamps the page bytes, so a block count cannot tell
    a link from a copy. Sharing an inode is the property itself: one set of blocks, two
    names, and 2.9 GB/year of archive instead of that plus a duplicate of everything
    unchanged.
    """
    gen = generations.archive(label="g1", raw_dir=raw, archive_dir=tmp_path / "archive")

    for archived in gen.path.rglob("*.gz"):
        live = raw / archived.relative_to(gen.path)
        assert archived.stat().st_ino == live.stat().st_ino, archived
        assert live.stat().st_nlink == 2


def test_archiving_does_not_touch_the_live_archive(raw, tmp_path):
    before = {p.relative_to(raw): p.read_bytes() for p in raw.rglob("*.gz")}

    generations.archive(label="g1", raw_dir=raw, archive_dir=tmp_path / "archive")

    after = {p.relative_to(raw): p.read_bytes() for p in raw.rglob("*.gz")}
    assert after == before


def test_reusing_a_label_is_refused(raw, tmp_path):
    """Two sessions under one date would describe a moment that never existed."""
    generations.archive(label="g1", raw_dir=raw, archive_dir=tmp_path / "archive")

    with pytest.raises(FileExistsError):
        generations.archive(label="g1", raw_dir=raw, archive_dir=tmp_path / "archive")


def test_generations_are_listed_oldest_first(raw, tmp_path):
    archive_dir = tmp_path / "archive"
    generations.archive(label="20260101T000000", raw_dir=raw, archive_dir=archive_dir)
    generations.archive(label="20260201T000000", raw_dir=raw, archive_dir=archive_dir)

    assert [g.label for g in generations.generations(archive_dir)] == [
        "20260101T000000", "20260201T000000"]


def test_an_empty_archive_lists_nothing(tmp_path):
    assert generations.generations(tmp_path / "nope") == []


def test_archiving_a_missing_raw_directory_fails_loudly(tmp_path):
    with pytest.raises(FileNotFoundError):
        generations.archive(raw_dir=tmp_path / "absent", archive_dir=tmp_path / "archive")
