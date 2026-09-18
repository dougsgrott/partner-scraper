"""The verdict ledger: human grades of digest findings, persisted and queryable.

See issue/accuracy/01-verdict-ledger.md. The project graded findings by hand three times
in one day and all three sets of verdicts existed only as prose in session documents —
so prompt v3 could not be scored against v2 without redoing an entire manual audit.
This module is the instrument that stops grades evaporating.

The shape is worksheet-in, table-out. `scripts/digest.py grade` emits a YAML worksheet
pre-filled from the audit sample; a person fills in `verdict` and `method` in an editor;
`grade --import` validates it and stores rows in the `verdicts` table of `changes.db`.
The worksheet file stays in `reports/changefeed/` as provenance — the one part of
`changes.db` that *is* rebuildable, by re-importing.

Three distinctions the ledger refuses to blur, because blurring them is how the first
three grade sets became incomparable:

* **method** — what the grader read. `excerpt` grades judge whether a claim matches the
  ranked lines shown; only `full-page` grades judge whether it is true. The 2026-08-30
  audit scored 9/1/0 from excerpts and full-page checking later found errors everywhere.
* **selection** — how the findings were chosen. A seeded `draw` supports a rate; a
  `targeted` set (findings picked because v1 got them wrong) does not, and reporting one
  as accuracy would be wrong in the flattering direction.
* **stratum weight** — `audit.draw` stratifies by impact with a per-stratum minimum of
  one, so small impact groups are oversampled and an unweighted "7 of 10 true" cannot be
  extrapolated. The weight (stratum population / drawn) is recorded with every draw.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from ..db import ChangeDB
from .findings import Finding

VERDICTS = ("true", "partly", "false", "unverified")
METHODS = ("excerpt", "full-page")
SELECTIONS = ("draw", "targeted")


@dataclass(frozen=True)
class Verdict:
    """One human grade of one finding, by one method."""

    finding_id: int
    verdict: str
    method: str
    graded_at: str
    selection: str | None = None
    stratum: str | None = None
    stratum_weight: float | None = None
    notes: str | None = None
    source: str | None = None


def stratum_weights(findings: list[Finding], drawn: list[Finding]) -> dict[str, dict]:
    """`{impact: {population, drawn, weight}}` for one draw.

    `weight` is population / drawn — the inverse sampling fraction. `audit.draw` gives
    every non-empty impact group at least one slot, so a group of 2 in a run of 79 is
    sampled at 25x the rate of a group of 50; without these numbers a sample's true-rate
    silently over-represents the rare impacts.
    """
    population: dict[str, int] = {}
    for f in findings:
        population[f.impact] = population.get(f.impact, 0) + 1
    counts: dict[str, int] = {}
    for f in drawn:
        counts[f.impact] = counts.get(f.impact, 0) + 1
    return {
        impact: {"population": population.get(impact, 0), "drawn": n,
                 "weight": round(population.get(impact, n) / n, 4)}
        for impact, n in sorted(counts.items())
    }


def store(db: ChangeDB, verdicts: list[Verdict]) -> int:
    """Write grades. One row per (finding, method); re-grading a method replaces it.

    Replacement rather than append, deliberately: the worksheet is the provenance, and a
    corrected worksheet re-imported should leave the table matching the file, not holding
    both readings. An excerpt grade later upgraded by a full-page check keeps both rows,
    which is the distinction that matters.
    """
    db.conn.executemany(
        "INSERT OR REPLACE INTO verdicts (finding_id, method, verdict, graded_at, "
        "selection, stratum, stratum_weight, notes, source) VALUES (?,?,?,?,?,?,?,?,?)",
        [(v.finding_id, v.method, v.verdict, v.graded_at, v.selection, v.stratum,
          v.stratum_weight, v.notes, v.source) for v in verdicts],
    )
    db.conn.commit()
    return len(verdicts)


def for_pair(db: ChangeDB, before: int, after: int) -> list[Verdict]:
    """Every grade attached to any finding of a pair — superseded runs included.

    Grades attach to the finding row, not to "current": a superseded run's grades are
    exactly what a new run gets compared against.
    """
    rows = db.conn.execute(
        "SELECT v.* FROM verdicts v JOIN findings f ON f.id = v.finding_id "
        "WHERE f.before_snapshot = ? AND f.after_snapshot = ? ORDER BY v.finding_id",
        (before, after)).fetchall()
    return [Verdict(r["finding_id"], r["verdict"], r["method"], r["graded_at"],
                    r["selection"], r["stratum"], r["stratum_weight"], r["notes"],
                    r["source"]) for r in rows]


def accuracy(db: ChangeDB, *, method: str | None = None) -> list[dict]:
    """Grade counts per (pair, prompt version, selection, method) — the comparison the
    schema was built for.

    One row per group, never merged across `method` or `selection`: an excerpt grade and
    a full-page grade of the same prompt are different measurements, and a targeted
    group's rate is not an accuracy estimate at all (the findings were picked because
    something was wrong with them). `rate` is true / (true + partly + false); `weighted`
    is the stratum-weighted version, present only when every graded row in the group
    carries a weight; `unverified` rows count in neither.
    """
    clause, params = "", []
    if method:
        clause, params = "WHERE v.method = ?", [method]
    rows = db.conn.execute(
        f"SELECT f.before_snapshot b, f.after_snapshot a, f.prompt_version pv, "
        f"v.selection sel, v.method m, v.verdict, v.stratum_weight w "
        f"FROM verdicts v JOIN findings f ON f.id = v.finding_id {clause} "
        f"ORDER BY f.before_snapshot, f.after_snapshot, f.prompt_version", params).fetchall()

    groups: dict[tuple, list] = {}
    for r in rows:
        groups.setdefault((r["b"], r["a"], r["pv"], r["sel"], r["m"]), []).append(r)

    out = []
    for (b, a, pv, sel, m), rs in groups.items():
        counts = {v: sum(1 for r in rs if r["verdict"] == v) for v in VERDICTS}
        graded = [r for r in rs if r["verdict"] != "unverified"]
        row = {"before": b, "after": a, "prompt_version": pv, "selection": sel,
               "method": m, **counts, "n": len(rs),
               "rate": (counts["true"] / len(graded)) if graded else None}
        if graded and all(r["w"] is not None for r in graded):
            total = sum(r["w"] for r in graded)
            row["weighted"] = sum(r["w"] for r in graded if r["verdict"] == "true") / total
        else:
            row["weighted"] = None
        out.append(row)
    return out


# -- the worksheet -------------------------------------------------------


def _yaml_str(text: str) -> str:
    """A string as a safe double-quoted YAML scalar."""
    import json

    return json.dumps(text, ensure_ascii=False)


def worksheet(pair: tuple[int, int], all_findings: list[Finding],
              drawn: list[Finding], *, seed: int, requested: int,
              graded_at: str) -> str:
    """The file a grader edits: one entry per drawn finding, verdict left blank.

    Summaries are included for reading convenience only — the import keys on `id` and
    re-reads everything else from the database, so editing a summary here changes
    nothing. The strata block is the draw's sampling record; without it the sample
    cannot be extrapolated later.
    """
    pv = next((f.prompt_version for f in drawn if f.prompt_version), None)
    strata = stratum_weights(all_findings, drawn)
    lines = [
        f"# Verdict worksheet — findings from #{pair[0]} -> #{pair[1]}"
        + (f", prompt v{pv}." if pv else "."),
        "# Fill `verdict` (true | partly | false | unverified) and `method`",
        "# (excerpt = judged from the audit's ranked lines; full-page = checked against",
        "# the stored page text). A blank verdict skips the entry. Then:",
        "#     uv run python scripts/digest.py grade --import <this file>",
        f"pair: {{before: {pair[0]}, after: {pair[1]}}}",
        f"prompt_version: {_yaml_str(pv) if pv else 'null'}",
        "selection: draw",
        f"seed: {seed}",
        f"requested: {requested}",
        f"graded_at: {_yaml_str(graded_at)}",
        "strata:  # population and quota per impact at draw time; weight = population/drawn",
    ]
    for impact, s in strata.items():
        lines.append(f"  {impact}: {{population: {s['population']}, "
                     f"drawn: {s['drawn']}, weight: {s['weight']}}}")
    lines.append("verdicts:")
    for f in drawn:
        lines += [
            f"  - id: {f.id}",
            f"    impact: {f.impact}",
            f"    summary: {_yaml_str(f.summary[:160])}",
            "    verdict:",
            "    method:",
            '    notes: ""',
        ]
    return "\n".join(lines) + "\n"


class WorksheetError(ValueError):
    """The worksheet cannot be imported as it stands. Nothing was stored."""


def parse(path: str | Path, db: ChangeDB) -> list[Verdict]:
    """Read a worksheet and validate every entry against the database.

    All-or-nothing: any bad entry fails the whole file with every problem listed, and
    nothing is stored by the caller. A partial import would leave the table and the
    worksheet silently disagreeing, which is the failure mode this module exists to end.
    """
    path = Path(path)
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    problems: list[str] = []

    pair = spec.get("pair") or {}
    before, after = pair.get("before"), pair.get("after")
    if not isinstance(before, int) or not isinstance(after, int):
        raise WorksheetError(f"{path}: `pair` must give integer before/after snapshots")

    selection = spec.get("selection")
    if selection is not None and selection not in SELECTIONS:
        problems.append(f"selection {selection!r} is not one of {SELECTIONS}")
    strata = spec.get("strata") or {}
    default_graded_at = spec.get("graded_at")
    default_source = spec.get("source") or str(path)

    known = {
        r["id"]: r["impact"]
        for r in db.conn.execute(
            "SELECT id, impact FROM findings WHERE before_snapshot = ? "
            "AND after_snapshot = ?", (before, after))
    }

    out: list[Verdict] = []
    for entry in spec.get("verdicts") or []:
        fid = entry.get("id")
        verdict = entry.get("verdict")
        # YAML reads a bare `true` or `false` as a boolean before this module ever sees
        # it, and those are the two words a grader types most. Map them back.
        if isinstance(verdict, bool):
            verdict = "true" if verdict else "false"
        if verdict in (None, ""):
            continue  # not graded yet — a worksheet may be imported half-filled
        where = f"finding {fid}"
        if not isinstance(fid, int) or fid not in known:
            problems.append(f"{where}: no such finding for pair "
                            f"#{before} -> #{after}")
            continue
        if verdict not in VERDICTS:
            problems.append(f"{where}: verdict {verdict!r} is not one of {VERDICTS}")
        entry_method = entry.get("method")
        if entry_method not in METHODS:
            problems.append(f"{where}: method {entry_method!r} is not one of {METHODS}")
        graded_at = entry.get("graded_at") or default_graded_at
        if not graded_at:
            problems.append(f"{where}: no graded_at on the entry or the header")
        impact = known.get(fid)
        weight = (strata.get(impact) or {}).get("weight") if selection == "draw" else None
        out.append(Verdict(
            finding_id=fid, verdict=str(verdict), method=str(entry_method),
            graded_at=str(graded_at), selection=selection, stratum=impact,
            stratum_weight=weight, notes=(entry.get("notes") or None),
            source=default_source))

    if problems:
        raise WorksheetError(f"{path}:\n  " + "\n  ".join(problems))
    if not out:
        raise WorksheetError(f"{path}: no filled-in verdicts to import")
    return out
