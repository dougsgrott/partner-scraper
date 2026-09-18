"""The verdict ledger — issue/accuracy/01-verdict-ledger.md.

The claim under test: a human grade, once given, survives everything that later happens
to the finding it judges — re-runs, supersession, re-imports — and never gets pooled
with grades that were made a different way. The first three grade sets in this project's
history evaporated into prose; these tests are the contract that stops the fourth.
"""

from __future__ import annotations

import pytest

from changefeed.db import ChangeDB
from changefeed.digest import audit, findings, verdicts
from changefeed.digest.findings import Finding


def build_pair(tmp_path, *, impacts=("breaking", "behavioural", "additive", "additive")):
    """A ChangeDB with one snapshot pair and one finding per impact given."""
    db = ChangeDB(tmp_path / "changes.db")
    before = db.create_snapshot(label="before")
    after = db.create_snapshot(label="after")
    ids = [
        findings.record(db, before, after, Finding(
            impact=impact, summary=f"Story {i} about {impact}",
            urls=[f"https://docs.databricks.com/aws/en/page-{i}"],
            model="claude-opus-5", prompt_version="2"))
        for i, impact in enumerate(impacts)
    ]
    return db, before, after, ids


def worksheet_for(db, before, after, n=10, seed=1) -> str:
    stored = findings.for_pair(db, before, after)
    drawn = audit.draw(stored, n, seed)
    return verdicts.worksheet((before, after), stored, drawn,
                              seed=seed, requested=n, graded_at="2026-09-18")


def fill(text: str, grades: dict[int, tuple[str, str]]) -> str:
    """Fill a worksheet the way an editor would: verdict and method per id."""
    out, current = [], None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- id:"):
            current = int(stripped.split(":")[1])
        if current in grades:
            verdict, method = grades[current]
            if stripped == "verdict:":
                line = line.replace("verdict:", f"verdict: {verdict}")
            elif stripped == "method:":
                line = line.replace("method:", f"method: {method}")
        out.append(line)
    return "\n".join(out)


def test_import_rejects_a_verdict_for_a_finding_not_in_the_pair(tmp_path):
    """A verdict must attach to a finding of the pair the file names — a typo'd id or a
    finding from another pair would silently grade the wrong thing forever."""
    db, before, after, _ids = build_pair(tmp_path)
    other_before = db.create_snapshot()
    other_after = db.create_snapshot()
    foreign = findings.record(db, other_before, other_after,
                              Finding(impact="additive", summary="other pair", urls=[]))
    sheet = tmp_path / "v.yaml"
    sheet.write_text(
        f"pair: {{before: {before}, after: {after}}}\n"
        f'graded_at: "2026-09-18"\n'
        f"verdicts:\n"
        f"  - id: {foreign}\n    verdict: true\n    method: full-page\n"
        f"  - id: 99999\n    verdict: true\n    method: full-page\n",
        encoding="utf-8")
    with pytest.raises(verdicts.WorksheetError) as err:
        verdicts.parse(sheet, db)
    assert str(foreign) in str(err.value) and "99999" in str(err.value)
    assert verdicts.for_pair(db, before, after) == []
    db.close()


def test_a_superseded_finding_keeps_its_verdict(tmp_path):
    """Grades attach to the finding row, not to "current": superseding a run is exactly
    when its grades become the baseline the new run gets compared against."""
    db, before, after, ids = build_pair(tmp_path)
    verdicts.store(db, [verdicts.Verdict(
        finding_id=ids[0], verdict="partly", method="full-page",
        graded_at="2026-09-18", selection="draw")])
    findings.supersede(db, before, after)
    findings.record(db, before, after, Finding(
        impact="breaking", summary="the v3 rewrite", urls=[], prompt_version="3"))

    kept = verdicts.for_pair(db, before, after)
    assert [(v.finding_id, v.verdict) for v in kept] == [(ids[0], "partly")]
    rows = verdicts.accuracy(db)
    assert any(r["prompt_version"] == "2" and r["partly"] == 1 for r in rows)
    db.close()


def test_full_page_accuracy_excludes_excerpt_grades(tmp_path):
    """An excerpt grade judges claim-vs-lines-shown, not truth. Asking for full-page
    accuracy must not let the flattering excerpt numbers leak in."""
    db, _before, _after, ids = build_pair(tmp_path)
    verdicts.store(db, [
        verdicts.Verdict(ids[0], "true", "excerpt", "2026-09-18", selection="draw"),
        verdicts.Verdict(ids[1], "true", "excerpt", "2026-09-18", selection="draw"),
        verdicts.Verdict(ids[2], "false", "full-page", "2026-09-18", selection="draw"),
    ])
    rows = verdicts.accuracy(db, method="full-page")
    assert len(rows) == 1
    assert rows[0]["method"] == "full-page"
    assert (rows[0]["true"], rows[0]["false"]) == (0, 1)
    assert rows[0]["rate"] == 0.0
    db.close()


def test_draw_and_targeted_grades_are_never_pooled(tmp_path):
    """A targeted set was picked because something looked wrong; pooling it with a
    seeded draw poisons the rate in whichever direction the picker was biased."""
    db, _before, _after, ids = build_pair(tmp_path)
    verdicts.store(db, [
        verdicts.Verdict(ids[0], "true", "full-page", "2026-09-18", selection="draw"),
        verdicts.Verdict(ids[1], "false", "full-page", "2026-09-18", selection="targeted"),
    ])
    rows = verdicts.accuracy(db)
    selections = {r["selection"] for r in rows}
    assert selections == {"draw", "targeted"}
    draw_row = next(r for r in rows if r["selection"] == "draw")
    assert draw_row["false"] == 0
    db.close()


def test_worksheet_round_trip_stores_stratum_weights(tmp_path):
    """The emit records the draw's sampling record and the import attaches each weight
    to its verdict — without them a stratified sample cannot be extrapolated later."""
    db, before, after, _ids = build_pair(
        tmp_path, impacts=("breaking", "additive", "additive", "additive", "additive"))
    text = worksheet_for(db, before, after, n=2, seed=1)
    assert "strata:" in text and "weight" in text

    stored = findings.for_pair(db, before, after)
    drawn = audit.draw(stored, 2, 1)
    filled = fill(text, {f.id: ("true", "full-page") for f in drawn})
    sheet = tmp_path / "verdicts.yaml"
    sheet.write_text(filled, encoding="utf-8")
    rows = verdicts.parse(sheet, db)
    verdicts.store(db, rows)

    weights = {v.stratum: v.stratum_weight for v in verdicts.for_pair(db, before, after)}
    # One breaking finding of one is drawn (weight 1); the additive stratum of four
    # contributes per its own sampling fraction.
    assert weights["breaking"] == 1.0
    assert weights["additive"] == 4.0
    db.close()


def test_a_blank_verdict_is_skipped_and_a_bad_one_fails_the_whole_file(tmp_path):
    """Half-graded worksheets import (grading is incremental); vocabulary mistakes fail
    the file atomically, because a partial import leaves table and file disagreeing."""
    db, before, after, ids = build_pair(tmp_path)
    text = worksheet_for(db, before, after)
    filled = fill(text, {ids[0]: ("true", "full-page")})  # others stay blank
    sheet = tmp_path / "ok.yaml"
    sheet.write_text(filled, encoding="utf-8")
    assert len(verdicts.parse(sheet, db)) == 1

    bad = fill(text, {ids[0]: ("mostly-right", "full-page"),
                      ids[1]: ("true", "vibes")})
    sheet_bad = tmp_path / "bad.yaml"
    sheet_bad.write_text(bad, encoding="utf-8")
    with pytest.raises(verdicts.WorksheetError) as err:
        verdicts.parse(sheet_bad, db)
    assert "mostly-right" in str(err.value) and "vibes" in str(err.value)
    db.close()


def test_a_bare_yaml_true_is_the_verdict_true(tmp_path):
    """`verdict: true` is the single likeliest thing a grader types, and YAML hands it
    to us as a boolean. It must mean the verdict, not a type error."""
    db, before, after, ids = build_pair(tmp_path)
    sheet = tmp_path / "v.yaml"
    sheet.write_text(
        f"pair: {{before: {before}, after: {after}}}\n"
        f'graded_at: "2026-09-18"\n'
        f"verdicts:\n"
        f"  - id: {ids[0]}\n    verdict: true\n    method: full-page\n"
        f"  - id: {ids[1]}\n    verdict: false\n    method: excerpt\n",
        encoding="utf-8")
    rows = verdicts.parse(sheet, db)
    assert [(v.finding_id, v.verdict) for v in rows] == [
        (ids[0], "true"), (ids[1], "false")]
    db.close()


def test_regrading_a_method_replaces_but_another_method_coexists(tmp_path):
    """One row per (finding, method): correcting an excerpt grade replaces it, while a
    later full-page check of the same finding sits beside it — the upgrade path the
    method distinction exists for."""
    db, before, after, ids = build_pair(tmp_path)
    v = verdicts.Verdict(ids[0], "true", "excerpt", "2026-09-18")
    verdicts.store(db, [v])
    verdicts.store(db, [verdicts.Verdict(ids[0], "partly", "excerpt", "2026-09-19")])
    verdicts.store(db, [verdicts.Verdict(ids[0], "false", "full-page", "2026-09-19")])
    got = {(x.method, x.verdict) for x in verdicts.for_pair(db, before, after)}
    assert got == {("excerpt", "partly"), ("full-page", "false")}
    db.close()
