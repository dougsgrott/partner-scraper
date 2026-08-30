"""What the digest session produced, and how it renders.

Findings are stored rather than streamed to a file for the reason the whole report layer
works this way: rendering is separate from computing, so a digest can be re-rendered —
shorter, grouped differently, for a different audience — without re-running the model.

**A finding is a story, not a page.** Measurement on the first run showed 44 items returned
by the model carried only about 25 distinct stories: ten pages saying the `ai_*` functions
now require Databricks Runtime 15.4, four saying `pipelines.channel` is unsupported. A
digest that repeats one story ten times is a worse digest, so `urls` is a list.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

from ..db import ChangeDB

# What a change does to someone building on the vendor. A small closed set, because an open
# one drifts into synonyms across runs and stops being groupable. `kind` is free text for
# the same reason in reverse: the *sort* of change is too varied to enumerate honestly.
IMPACTS = ("breaking", "behavioural", "additive", "editorial")


@dataclass(frozen=True)
class Finding:
    """One story from a run."""

    impact: str
    summary: str
    urls: list[str] = field(default_factory=list)
    kind: str | None = None
    detail: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    id: int | None = None

    @property
    def headline(self) -> str:
        """The summary as a heading: single line, no inner emphasis.

        The model writes summaries containing their own `**bold**`, and wrapping those in
        bold again produces nested markers that render as literal asterisks. Headings do
        not need emphasis, so it is stripped rather than escaped.
        """
        return " ".join(self.summary.replace("**", "").split())

    def render(self, *, max_pages: int = 6) -> str:
        """One finding, sized to be read rather than scanned past.

        Citations are capped. A finding covering 26 pages is a good finding and a terrible
        26-line list; the full set stays in `changes.db` and in the JSON report, and the
        count is always stated so nothing looks smaller than it is.
        """
        meta = " · ".join(x for x in (f"`{self.impact}`", self.kind,
                                      f"{len(self.urls)} page" + ("s" if len(self.urls) != 1 else "")) if x)
        lines = [f"### {self.headline}", "", meta, ""]
        if self.detail:
            lines += [" ".join(self.detail.split()), ""]
        for url in self.urls[:max_pages]:
            lines.append(f"- [{_slug(url)}]({url})")
        if len(self.urls) > max_pages:
            lines.append(f"- …and {len(self.urls) - max_pages} more")
        lines.append("")
        return "\n".join(lines)


def _slug(url: str) -> str:
    """The readable tail of a URL — the shared prefix is noise in a list of ten."""
    for marker in ("/en/", "/docs/", "://"):
        if marker in url:
            return url.split(marker, 1)[1]
    return url


def record(db: ChangeDB, before: int, after: int, finding: Finding) -> int:
    """Store one finding. Returns its id."""
    cur = db.conn.execute(
        "INSERT INTO findings (before_snapshot, after_snapshot, recorded_at, impact, "
        "kind, summary, detail, urls, model, prompt_version) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (before, after, datetime.now(UTC).isoformat(timespec="seconds"), finding.impact,
         finding.kind, finding.summary, finding.detail, json.dumps(finding.urls),
         finding.model, finding.prompt_version),
    )
    db.conn.commit()
    return int(cur.lastrowid)


def for_pair(db: ChangeDB, before: int, after: int, *,
             superseded: bool = False) -> list[Finding]:
    """Findings for a snapshot pair, most severe impact first.

    Current ones by default. `superseded=True` returns the replaced rows instead, which is
    how two runs over the same pair get compared — the only available check on whether the
    digest is stable.
    """
    clause = "IS NOT NULL" if superseded else "IS NULL"
    rows = db.conn.execute(
        f"SELECT * FROM findings WHERE before_snapshot = ? AND after_snapshot = ? "
        f"AND superseded_at {clause} ORDER BY id", (before, after)).fetchall()
    findings = [
        Finding(impact=r["impact"], summary=r["summary"], urls=json.loads(r["urls"]),
                kind=r["kind"], detail=r["detail"], model=r["model"],
                prompt_version=r["prompt_version"], id=r["id"])
        for r in rows
    ]
    order = {impact: i for i, impact in enumerate(IMPACTS)}
    return sorted(findings, key=lambda f: (order.get(f.impact, len(IMPACTS)), -len(f.urls)))


def supersede(db: ChangeDB, before: int, after: int) -> int:
    """Retire the current findings for a pair without destroying them.

    A re-run replaces rather than accumulates, so a report shows one run's work — but the
    old rows are marked, not deleted. Deleting them made the first run-to-run stability
    comparison impossible, and that comparison is the only evidence there is about whether
    a digest is reproducible.
    """
    cur = db.conn.execute(
        "UPDATE findings SET superseded_at = ? WHERE before_snapshot = ? "
        "AND after_snapshot = ? AND superseded_at IS NULL",
        (datetime.now(UTC).isoformat(timespec="seconds"), before, after))
    db.conn.commit()
    return cur.rowcount


def render(findings: list[Finding], *, before: str, after: str, changes: int) -> str:
    """The digest: a skimmable summary first, then the detail, grouped by impact."""
    stamp = datetime.now(UTC).isoformat(timespec="seconds")
    out = [
        "# Change digest",
        "",
        f"> {before} → {after} · {changes:,} changes · rendered {stamp}",
        "",
    ]
    if not findings:
        out += ["No findings recorded for this pair.", ""]
        return "\n".join(out)

    covered = len({url for f in findings for url in f.urls})
    tally = ", ".join(f"**{len([f for f in findings if f.impact == i])}** {i}"
                      for i in IMPACTS if any(f.impact == i for f in findings))
    out += [
        "## At a glance",
        "",
        (f"{len(findings)} findings — {tally} — covering {covered:,} of {changes:,} "
         f"changed pages. Anything not here is in the full feed report beside this file."),
        "",
    ]

    # The part a reader who has two minutes actually reads.
    urgent = [f for f in findings if f.impact == "breaking"]
    if urgent:
        out += ["**If you read nothing else:**", ""]
        out += [f"{i}. {f.headline}" for i, f in enumerate(urgent, 1)]
        out += [""]

    out += ["---", ""]

    for impact in IMPACTS:
        group = [f for f in findings if f.impact == impact]
        if not group:
            continue
        out += [f"## {impact.title()} — {len(group)}", ""]
        out += [f.render() for f in group]

    other = [f for f in findings if f.impact not in IMPACTS]
    if other:
        out += [f"## Unclassified — {len(other)}", "", *(f.render() for f in other)]
    return "\n".join(out)
