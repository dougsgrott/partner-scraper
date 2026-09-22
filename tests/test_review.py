"""The review tool — docs/review-tool-plan.md.

The claims under test are the integrity rules the UI turns from discipline into code:
queue materialization is deterministic (resume = re-derive and skip the done); a grading
submit goes through the ledger's own semantics (one row per finding × method, weights and
grader attached); blind mode structurally withholds prior verdicts until after submit;
skip/unsure labels enter no flip rate and no export; the exported worksheet round-trips
through `verdicts.parse`; and the `grader` column arrives without disturbing a single
existing row.
"""

from __future__ import annotations

import hashlib
import sqlite3

import pytest
import yaml

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from changefeed import blobs
from changefeed.db import ChangeDB
from changefeed.digest import findings, verdicts
from changefeed.digest.findings import Finding
from review.app import create_app


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


PAGES = {
    # url-slug: (before body, after body). Each after adds one restriction line whose
    # subject is already in the before text — an absence candidate by construction.
    "widget-api": (
        ("# Widget API\n\nClaude Fable 5 is available in all regions.\n"
         "The Widget API supports batch mode.\nA prose line that stays.\n"),
        ("# Widget API\n\nClaude Fable 5 is available in all regions.\n"
         "Claude Fable 5 is no longer available for customers who opt out.\n"
         "The Widget API supports batch mode in most regions.\nA prose line that stays.\n"),
    ),
    "export-guide": (
        "# Export Guide\n\nThe Widget API exports CSV and JSON.\nAnother stable line.\n",
        ("# Export Guide\n\nThe Widget API exports JSON.\n"
         "The Widget API cannot export CSV files.\nAnother stable line.\n"),
    ),
    "quota-page": (
        "# Quotas\n\nBatch Mode quotas apply per workspace.\nFiller here.\n",
        ("# Quotas\n\nBatch Mode quotas apply per account.\n"
         "Batch Mode is unsupported for trial accounts.\nFiller here.\n"),
    ),
}


def _url(slug: str) -> str:
    return f"https://docs.acme.com/en/{slug}"


def _version(slug: str, body: str) -> dict:
    return {"url": _url(slug), "company": "acme", "source_id": "acme-docs",
            "category": "docs", "title": slug, "description": None, "updated_date": None,
            "content_hash": _sha(body), "output_fingerprint": "of1",
            "body_fingerprint": "bf1", "extractor": "x@1", "body_chars": len(body),
            "file_path": f"data/acme/docs/{slug}.md"}


@pytest.fixture
def corpus(tmp_path):
    """A pair of snapshots with real blobs, plus one finding per impact."""
    db_path = tmp_path / "changes.db"
    blob_dir = tmp_path / "blobs"
    db = ChangeDB(db_path)
    before = db.create_snapshot(label="before")
    after = db.create_snapshot(label="after")
    for snap_id, side in ((before, 0), (after, 1)):
        rows = []
        for slug, bodies in PAGES.items():
            blobs.write(_sha(bodies[side]), bodies[side], blob_dir)
            rows.append(_version(slug, bodies[side]))
        db.add_versions(snap_id, rows)
        db.finish_snapshot(snap_id)
    ids = [
        findings.record(db, before, after, Finding(
            impact=impact, summary=f"Story {i}: the Widget API changed ({impact})",
            urls=[_url("widget-api")], model="claude-opus-5", prompt_version="3"))
        for i, impact in enumerate(("breaking", "behavioural", "additive", "additive"))
    ]
    yield {"db_path": db_path, "blob_dir": blob_dir, "db": db,
           "before": before, "after": after, "finding_ids": ids}
    db.close()


@pytest.fixture
def client(corpus):
    app = create_app(changes_db=corpus["db_path"], blob_dir=corpus["blob_dir"])
    return TestClient(app)


def make_grading_queue(client, corpus, **extra) -> dict:
    params = {"before": corpus["before"], "after": corpus["after"],
              "n": 3, "seed": 1, "grader": "scratch", **extra}
    res = client.post("/api/queues", json={
        "kind": "grading", "title": "spot grade", "params": params})
    assert res.status_code == 200, res.text
    return res.json()


def make_labeling_queue(client, corpus, **extra) -> dict:
    params = {"before": corpus["before"], "after": corpus["after"],
              "source": "absence", "labeler": "scratch", **extra}
    res = client.post("/api/queues", json={
        "kind": "labeling", "title": "label lines", "params": params})
    assert res.status_code == 200, res.text
    return res.json()


def test_grading_queue_materializes_deterministically_and_resumes(client, corpus):
    """Items are re-derived from sealed params, so two opens agree — and resume is
    nothing but a done flag where a verdict row already exists."""
    q = make_grading_queue(client, corpus)
    assert q["params"]["item_count"] == 3
    assert q["params"]["selection"] == "draw"
    assert "strata" in q["params"]  # the sampling record, sealed at creation

    first = client.get(f"/api/queues/{q['id']}").json()
    second = client.get(f"/api/queues/{q['id']}").json()
    assert [i["id"] for i in first["items"]] == [i["id"] for i in second["items"]]
    assert all(not i["done"] for i in first["items"])

    target = first["items"][0]["id"]
    res = client.post(f"/api/queues/{q['id']}/items/{target}",
                      json={"verdict": "true"})
    assert res.status_code == 200, res.text

    reopened = client.get(f"/api/queues/{q['id']}").json()
    done_flags = {i["id"]: i["done"] for i in reopened["items"]}
    assert done_flags[target] is True
    assert sum(done_flags.values()) == 1
    assert reopened["progress"] == {"done": 1, "total": 3}


def test_grading_submit_lands_the_ledger_row_and_resubmit_replaces(client, corpus):
    """The write path is `verdicts.store`: method, grader, stratum weight, and source
    on the row; a second submit replaces per (finding, method), never appends."""
    q = make_grading_queue(client, corpus)
    items = client.get(f"/api/queues/{q['id']}").json()["items"]
    target = items[0]
    client.post(f"/api/queues/{q['id']}/items/{target['id']}",
                json={"verdict": "true", "notes": "checked the diff"})

    with ChangeDB(corpus["db_path"]) as db:
        rows = [v for v in verdicts.for_pair(db, corpus["before"], corpus["after"])
                if v.finding_id == target["id"]]
    assert len(rows) == 1
    v = rows[0]
    assert (v.verdict, v.method, v.grader) == ("true", "full-page", "scratch")
    assert v.selection == "draw"
    assert v.stratum == target["impact"]
    assert v.stratum_weight == q["params"]["strata"][target["impact"]]["weight"]
    assert v.source == f"review:queue-{q['id']}"
    assert v.notes == "checked the diff"

    client.post(f"/api/queues/{q['id']}/items/{target['id']}",
                json={"verdict": "partly"})
    with ChangeDB(corpus["db_path"]) as db:
        rows = [v for v in verdicts.for_pair(db, corpus["before"], corpus["after"])
                if v.finding_id == target["id"]]
    assert [(r.verdict, r.method) for r in rows] == [("partly", "full-page")]

    res = client.post(f"/api/queues/{q['id']}/items/{target['id']}",
                      json={"verdict": "vibes"})
    assert res.status_code == 400  # vocabulary is validated, not trusted


def test_blind_mode_withholds_prior_verdicts_until_after_submit(client, corpus):
    """The evidence bundle structurally cannot leak an earlier grade; the submit
    response is the reveal — the re-grade protocol as code, not discipline."""
    q = make_grading_queue(client, corpus)
    target = client.get(f"/api/queues/{q['id']}").json()["items"][0]
    with ChangeDB(corpus["db_path"]) as db:
        verdicts.store(db, [verdicts.Verdict(
            finding_id=target["id"], verdict="false", method="excerpt",
            graded_at="2026-09-19", selection="draw", grader="doug")])

    bundle = client.get(f"/api/queues/{q['id']}/items/{target['id']}").json()
    assert bundle["done"] is False  # an excerpt grade is not this queue's method
    assert "prior" not in bundle
    assert "false" not in str(bundle.get("finding"))  # nothing smuggled through fields

    reveal = client.post(f"/api/queues/{q['id']}/items/{target['id']}",
                         json={"verdict": "true"}).json()
    prior = {(p["method"], p["verdict"], p["grader"]) for p in reveal["prior"]}
    assert ("excerpt", "false", "doug") in prior

    revisit = client.get(f"/api/queues/{q['id']}/items/{target['id']}").json()
    assert revisit["done"] is True
    assert {p["method"] for p in revisit["prior"]} == {"excerpt", "full-page"}


def test_labeling_flip_rate_and_the_skip_exclusion(client, corpus, tmp_path,
                                                   monkeypatch):
    """Flip rate counts pre-labeled, non-skip rows only; a skip is provenance in the
    table but enters no training export — the `unverified` precedent."""
    monkeypatch.chdir(tmp_path)  # exports write under reports/
    q = make_labeling_queue(client, corpus)
    detail = client.get(f"/api/queues/{q['id']}").json()
    items = detail["items"]
    assert len(items) == 3  # one absence candidate per page, deduplicated
    assert all(i["pre_label"] == "restriction" for i in items)

    def submit(item, label):
        res = client.post(f"/api/queues/{q['id']}/items/{item['id']}",
                          json={"label": label})
        assert res.status_code == 200, res.text
        return res.json()

    submit(items[0], "restriction")            # agrees with the pre-label
    submit(items[1], "behavioural-change")     # a flip
    result = submit(items[2], "skip")          # unsure — excluded everywhere
    assert result["flips"] == {"labeled": 2, "skipped": 1, "with_pre_label": 2,
                               "flips": 1, "flip_rate": 0.5}

    export = client.post(f"/api/queues/{q['id']}/export").json()
    assert export["count"] == 2
    spec = yaml.safe_load((tmp_path / export["path"]).read_text(encoding="utf-8"))
    assert spec["flip_rate"] == 0.5
    assert spec["skipped"] == 1
    assert len(spec["lines"]) == 2
    labels = {(ln["line"], ln["label"]) for ln in spec["lines"]}
    assert (items[1]["line"], "behavioural-change") in labels
    assert not any(ln["label"] == "skip" for ln in spec["lines"])
    # verbatim, per the fixture rule
    assert all(any(ln["line"] in body for bodies in PAGES.values() for body in bodies)
               for ln in spec["lines"])

    res = client.post(f"/api/queues/{q['id']}/items/{items[0]['id']}",
                      json={"label": "made-up"})
    assert res.status_code == 400


def test_worksheet_export_round_trips_through_parse(client, corpus, tmp_path,
                                                    monkeypatch):
    """The exported worksheet is the exact provenance format: `verdicts.parse` reads it
    back into the same rows — verdicts, weights, and grader included."""
    monkeypatch.chdir(tmp_path)
    q = make_grading_queue(client, corpus)
    items = client.get(f"/api/queues/{q['id']}").json()["items"]
    client.post(f"/api/queues/{q['id']}/items/{items[0]['id']}",
                json={"verdict": "true"})
    client.post(f"/api/queues/{q['id']}/items/{items[1]['id']}",
                json={"verdict": "partly", "notes": "half of it moved"})

    export = client.post(f"/api/queues/{q['id']}/export").json()
    path = tmp_path / export["path"]
    assert export["count"] == 2 and path.exists()

    with ChangeDB(corpus["db_path"]) as db:
        parsed = verdicts.parse(path, db)
        stored = {v.finding_id: v
                  for v in verdicts.for_pair(db, corpus["before"], corpus["after"])}
    assert len(parsed) == 2
    for p in parsed:
        s = stored[p.finding_id]
        assert (p.verdict, p.method, p.grader) == (s.verdict, s.method, "scratch")
        assert p.stratum_weight == s.stratum_weight
        assert p.selection == "draw"

    # Re-importing the export leaves the table exactly as the UI wrote it — the
    # "worksheet is the rebuildable provenance" promise, exercised.
    with ChangeDB(corpus["db_path"]) as db:
        verdicts.store(db, parsed)
        after = {v.finding_id: v.verdict
                 for v in verdicts.for_pair(db, corpus["before"], corpus["after"])}
    assert after == {items[0]["id"]: "true", items[1]["id"]: "partly"}


def test_export_with_no_grades_is_refused(client, corpus):
    q = make_grading_queue(client, corpus)
    res = client.post(f"/api/queues/{q['id']}/export")
    assert res.status_code == 400
    assert "nothing to export" in res.json()["detail"]


def test_grader_migration_leaves_existing_rows_and_old_paths_untouched(tmp_path):
    """A database from before the column opens cleanly: the row keeps its values,
    `grader` reads as NULL, and grader-less writes still work."""
    db_path = tmp_path / "old.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE verdicts (
        finding_id INTEGER NOT NULL, method TEXT NOT NULL, verdict TEXT NOT NULL,
        graded_at TEXT NOT NULL, selection TEXT, stratum TEXT, stratum_weight REAL,
        notes TEXT, source TEXT, PRIMARY KEY (finding_id, method))""")
    conn.execute("INSERT INTO verdicts VALUES (1, 'full-page', 'true', '2026-09-18', "
                 "'draw', 'breaking', 1.0, 'old note', 'old.yaml')")
    conn.commit()
    conn.close()

    db = ChangeDB(db_path)  # migrates: ALTER TABLE ... ADD COLUMN grader
    before = db.create_snapshot(label="b")
    after = db.create_snapshot(label="a")
    fid = findings.record(db, before, after, Finding(
        impact="breaking", summary="s", urls=[], prompt_version="2"))
    assert fid == 1  # the old verdict row now joins cleanly

    old = verdicts.for_pair(db, before, after)
    assert [(v.verdict, v.stratum_weight, v.grader)
            for v in old] == [("true", 1.0, None)]

    # The pre-UI write path — no grader anywhere — still works beside graded rows.
    verdicts.store(db, [verdicts.Verdict(
        finding_id=fid, verdict="partly", method="excerpt", graded_at="2026-09-20",
        selection="draw")])
    rows = verdicts.accuracy(db)
    assert {r["grader"] for r in rows} == {None}
    assert sum(r["n"] for r in rows) == 2
    db.close()


def test_concurrent_first_opens_migrate_without_error(tmp_path):
    """The app opens a ChangeDB per request and the dashboard fires several requests at
    once, so the first launch against an old database migrates concurrently. Two
    connections racing PRAGMA-then-ALTER must both come up, not die on
    'duplicate column name' — the failure Doug's first `serve` hit."""
    import threading

    db_path = tmp_path / "old.db"
    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE verdicts (
        finding_id INTEGER NOT NULL, method TEXT NOT NULL, verdict TEXT NOT NULL,
        graded_at TEXT NOT NULL, selection TEXT, stratum TEXT, stratum_weight REAL,
        notes TEXT, source TEXT, PRIMARY KEY (finding_id, method))""")
    conn.commit()
    conn.close()

    workers = 8
    barrier = threading.Barrier(workers)
    errors: list[Exception] = []

    def open_close():
        try:
            barrier.wait()
            ChangeDB(db_path).close()
        except Exception as err:  # noqa: BLE001 — the assertion is "no error at all"
            errors.append(err)

    threads = [threading.Thread(target=open_close) for _ in range(workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []

    with ChangeDB(db_path) as db:
        cols = {r["name"] for r in db.conn.execute("PRAGMA table_info(verdicts)")}
    assert "grader" in cols
