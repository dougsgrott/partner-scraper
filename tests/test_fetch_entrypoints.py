"""Every fetch entry point archives — issue/accuracy/09.

The invariant under test: it is impossible to fetch through an in-repo entry point
without a generation landing in `raw-archive/`, other than by an explicit
`--no-archive`. A missed archive is the one unrecoverable failure in the pipeline —
`raw/` is overwritten in place by the next fetch — and it used to depend on which
script someone typed: `fetch.py` archived, `changes.py run --fetch` silently did not.

The decision now lives once, in `generations.archive_after`; the policy is tested
against real directories, and then each caller's wiring with `run_fetch` replaced by
a stub, because the question is what happens *after* a fetch, not the fetch itself.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from scraper.fetch import generations, rawstore
from scraper.fetch.runner import RunSummary

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def raw(tmp_path):
    root = tmp_path / "raw"
    rawstore.write("https://docs.databricks.com/aws/en/a", "databricks",
                   b"<html>bytes</html>", ext="html", base_dir=root)
    return root


def summary(**kw) -> RunSummary:
    return RunSummary(started_at="2026-09-19T12:00:00+00:00", mode="refresh", **kw)


# -- the shared policy -----------------------------------------------------

def test_a_successful_fetch_archives_a_generation(raw, tmp_path):
    gen = generations.archive_after(summary(ok=1), raw_dir=raw,
                                    archive_dir=tmp_path / "archive")

    assert gen is not None
    assert (gen.path / "manifest.json").exists()
    assert gen.run == "2026-09-19T12:00:00+00:00"


def test_a_dry_run_archives_nothing(raw, tmp_path):
    gen = generations.archive_after(summary(ok=3, dry_run=True), raw_dir=raw,
                                    archive_dir=tmp_path / "archive")

    assert gen is None
    assert not (tmp_path / "archive").exists()


def test_a_fetch_that_wrote_nothing_archives_nothing(raw, tmp_path):
    """An all-304 refresh or an all-error run leaves raw/ as the last generation saw it."""
    gen = generations.archive_after(summary(ok=0, not_modified=5, errors=2), raw_dir=raw,
                                    archive_dir=tmp_path / "archive")

    assert gen is None
    assert not (tmp_path / "archive").exists()


# -- caller wiring ---------------------------------------------------------

@pytest.fixture
def default_dirs(monkeypatch, raw, tmp_path):
    """Point the module-level default directories at tmp space.

    Both entry points call `archive_after` without path arguments, so `archive` falls
    back to these module constants — which it reads at call time, making them safe to
    patch here and dangerous to cache anywhere else.
    """
    monkeypatch.setattr(rawstore, "DEFAULT_RAW_DIR", raw)
    monkeypatch.setattr(generations, "DEFAULT_ARCHIVE_DIR", tmp_path / "archive")
    return tmp_path / "archive"


def test_changes_run_fetch_archives(default_dirs, monkeypatch, capsys):
    """The path that used to lose data: `changes.py run --fetch` now archives."""
    from changefeed import cli

    monkeypatch.setattr("scraper.fetch.runner.run_fetch", lambda cfg, **kw: summary(ok=1))
    cli._fetch_and_archive(None)

    gens = generations.generations(default_dirs)
    assert len(gens) == 1
    assert (gens[0].path / "manifest.json").exists()
    assert "archived generation" in capsys.readouterr().out


def test_changes_run_fetch_no_archive_opts_out(default_dirs, monkeypatch):
    from changefeed import cli

    monkeypatch.setattr("scraper.fetch.runner.run_fetch", lambda cfg, **kw: summary(ok=1))
    cli._fetch_and_archive(None, archive=False)

    assert generations.generations(default_dirs) == []


def _load_fetch_script():
    spec = importlib.util.spec_from_file_location("fetch_script", ROOT / "scripts" / "fetch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fetch_script_archives_by_default(default_dirs, monkeypatch, capsys):
    script = _load_fetch_script()
    monkeypatch.setattr(script, "run_fetch", lambda cfg, **kw: summary(ok=1))
    monkeypatch.setattr(script, "load_config", lambda path: None)
    monkeypatch.setattr(sys, "argv", ["fetch.py"])

    script.main()

    assert len(generations.generations(default_dirs)) == 1
    assert "archived generation" in capsys.readouterr().out


def test_fetch_script_no_archive_opts_out(default_dirs, monkeypatch):
    script = _load_fetch_script()
    monkeypatch.setattr(script, "run_fetch", lambda cfg, **kw: summary(ok=1))
    monkeypatch.setattr(script, "load_config", lambda path: None)
    monkeypatch.setattr(sys, "argv", ["fetch.py", "--no-archive"])

    script.main()

    assert generations.generations(default_dirs) == []
