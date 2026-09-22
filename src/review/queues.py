"""Everything is a review queue: items, evidence, a validated write path.

One abstraction carries the tool (docs/review-tool-plan.md). A queue is a row in
`review_queues` — kind, title, params — and its **items are re-derived from params at
open time**: `audit.draw` is seeded and the absence scan is deterministic, so
materialization is reproducible and resumability is nothing more than "mark done where
a verdict or label row already exists, jump to the first pending". No item-state table
to drift out of sync.

The ledger's integrity rules are defaults here, not habits:

* full-page method unless the submit says otherwise;
* **blind mode** — prior verdicts are withheld until after submit, then revealed
  (the 2026-09-20 re-grade protocol, enforced by code);
* selection, seed, and stratum weights sealed into params at queue creation;
* grader identity on every row.

Adding future functionality (absence-candidate review, decision records, arm launching)
means adding a queue or action kind to `REGISTRY`, not a new tool.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from changefeed import classify
from changefeed.db import ChangeDB
from changefeed.diff import MODIFIED, DiffResult
from changefeed.digest import absence, audit, findings, verdicts
from changefeed.digest.findings import Finding

from . import evidence, store

GRADING = "grading"
LABELING = "labeling"

# Pre-labeler v1: the deterministic lexicon. The schema is agnostic — an LLM pre-labeler
# later just fills `pre_label` and names itself in `pre_labeler`.
PRE_LABELER_V1 = "classify.RESTRICTION"

LABEL_SOURCES = ("absence", "stratified")


class ReviewError(ValueError):
    """A request the queue cannot honour. The app maps it to a 400, not a traceback."""


@dataclass
class Context:
    """What a queue needs from the app: the database, the blob store, and a (cached)
    diff of a snapshot pair — computing one is seconds, so the app memoises it."""

    db: ChangeDB
    blob_dir: Path | None
    diff: Callable[[int, int], DiffResult]


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class GradingQueue:
    """Findings to grade, through the verdict ledger's own semantics.

    Params: `before`/`after`; either a seeded draw (`selection: draw`, `seed`, `n`,
    optionally `prompt_version` to draw from a shelved arm) or an explicit
    `finding_ids` list (`selection: targeted`); `method` default full-page; `grader`.
    `strata` is sealed in at creation — the draw's sampling record.
    """

    kind = GRADING

    def __init__(self, queue_id: int, params: dict):
        self.id = queue_id
        self.params = params

    @property
    def pair(self) -> tuple[int, int]:
        return int(self.params["before"]), int(self.params["after"])

    @property
    def method(self) -> str:
        return self.params.get("method") or "full-page"

    @property
    def selection(self) -> str:
        return "targeted" if self.params.get("finding_ids") else "draw"

    # -- materialization ---------------------------------------------------

    def _materialize(self, ctx: Context) -> tuple[list[Finding], list[Finding]]:
        """`(population, drawn)`, re-derived deterministically from params."""
        before, after = self.pair
        pv = self.params.get("prompt_version")
        ids = self.params.get("finding_ids")
        if ids:
            # Targeted sets may reach shelved or superseded rows — grades attach to
            # the finding row, so an arm's findings are gradeable without promotion.
            drawn = findings.by_ids(ctx.db, before, after, [int(i) for i in ids])
            return drawn, drawn
        if pv:
            stored = findings.arm_run(ctx.db, before, after, pv)
        else:
            stored = findings.for_pair(ctx.db, before, after)
        if not stored:
            raise ReviewError(f"no findings for pair #{before} -> #{after}"
                              + (f" (prompt version {pv})" if pv else ""))
        drawn = audit.draw(stored, int(self.params.get("n") or 10),
                           int(self.params.get("seed") or 1))
        return stored, drawn

    def seal(self, ctx: Context) -> None:
        """Validate params and record the sampling facts, at creation time only.

        The strata block is the one thing that must be captured *now*: it describes
        the population at draw time, and re-runs over the pair may change it later.
        """
        stored, drawn = self._materialize(ctx)
        self.params["selection"] = self.selection
        self.params["method"] = self.method
        self.params["item_count"] = len(drawn)
        if self.selection == "draw":
            self.params["strata"] = verdicts.stratum_weights(stored, drawn)

    def _drawn(self, ctx: Context) -> list[Finding]:
        return self._materialize(ctx)[1]

    def _done_map(self, ctx: Context, drawn: list[Finding]) -> dict[int, verdicts.Verdict]:
        """This queue's method only: an excerpt grade elsewhere must not mark a
        full-page item done — and must not leak through the done flag either."""
        wanted = {f.id for f in drawn}
        return {v.finding_id: v
                for v in verdicts.for_pair(ctx.db, *self.pair)
                if v.method == self.method and v.finding_id in wanted}

    def items(self, ctx: Context) -> list[dict]:
        drawn = self._drawn(ctx)
        done = self._done_map(ctx, drawn)
        out = []
        for f in drawn:
            item = {"id": f.id, "impact": f.impact, "kind": f.kind,
                    "summary": f.headline, "cited": len(f.urls),
                    "done": f.id in done}
            if f.id in done:  # post-reveal: its own grade may show
                item["verdict"] = done[f.id].verdict
            out.append(item)
        return out

    def progress(self, ctx: Context) -> dict:
        drawn = self._drawn(ctx)
        return {"done": len(self._done_map(ctx, drawn)), "total": len(drawn)}

    # -- evidence and writes -------------------------------------------------

    def _finding(self, ctx: Context, item_id: str) -> Finding:
        try:
            fid = int(item_id)
        except ValueError:
            raise ReviewError(f"not a finding id: {item_id!r}") from None
        f = next((f for f in self._drawn(ctx) if f.id == fid), None)
        if f is None:
            raise ReviewError(f"finding {fid} is not an item of queue {self.id}")
        return f

    def evidence(self, ctx: Context, item_id: str) -> dict:
        f = self._finding(ctx, item_id)
        result = ctx.diff(*self.pair)
        by_url = {c.url: c for c in result.changes}
        bundle = evidence.grading_bundle(f, by_url, blob_dir=ctx.blob_dir)
        bundle["done"] = f.id in self._done_map(ctx, [f])
        if bundle["done"]:  # already revealed at submit time; a revisit may see them
            bundle["prior"] = self._verdicts_for(ctx, f.id)
        return bundle

    def _verdicts_for(self, ctx: Context, fid: int) -> list[dict]:
        from dataclasses import asdict

        return [asdict(v) for v in verdicts.for_pair(ctx.db, *self.pair)
                if v.finding_id == fid]

    def submit(self, ctx: Context, item_id: str, payload: dict) -> dict:
        """Build a `verdicts.Verdict` and store it — replacement per (finding, method),
        exactly the ledger's semantics, so correcting a done item just works. Returns
        the prior verdicts (as they stood before this write): the blind-mode reveal."""
        f = self._finding(ctx, item_id)
        verdict = payload.get("verdict")
        if verdict not in verdicts.VERDICTS:
            raise ReviewError(f"verdict {verdict!r} is not one of {verdicts.VERDICTS}")
        method = payload.get("method") or self.method
        if method not in verdicts.METHODS:
            raise ReviewError(f"method {method!r} is not one of {verdicts.METHODS}")
        prior = self._verdicts_for(ctx, f.id)

        weight = None
        if self.selection == "draw":
            weight = ((self.params.get("strata") or {}).get(f.impact) or {}).get("weight")
        v = verdicts.Verdict(
            finding_id=f.id, verdict=verdict, method=method, graded_at=_now(),
            selection=self.selection, stratum=f.impact, stratum_weight=weight,
            notes=(payload.get("notes") or None),
            source=f"review:queue-{self.id}",
            grader=(payload.get("grader") or self.params.get("grader")))
        verdicts.store(ctx.db, [v])
        from dataclasses import asdict

        return {"stored": asdict(v), "prior": prior}

    def export(self, ctx: Context, out: Path | None = None) -> tuple[Path, int]:
        """A filled worksheet in the exact existing format — and it must round-trip
        through `verdicts.parse`, checked here at write time, so the "worksheet is the
        rebuildable provenance" promise survives the UI rather than being assumed."""
        stored, drawn = self._materialize(ctx)
        filled = self._done_map(ctx, drawn)
        if not filled:
            raise ReviewError("no grades in this queue yet — nothing to export")
        before, after = self.pair
        text = verdicts.worksheet(
            self.pair, stored, drawn,
            seed=self.params.get("seed") if self.selection == "draw" else None,
            requested=self.params.get("n") if self.selection == "draw" else None,
            graded_at=datetime.now(UTC).date().isoformat(),
            selection=self.selection, grader=self.params.get("grader"), filled=filled)
        out = out or Path(
            f"reports/changefeed/verdicts-{before:04d}..{after:04d}-q{self.id}.yaml")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        parsed = verdicts.parse(out, ctx.db)  # raises WorksheetError on format drift
        if len(parsed) != len(filled):
            raise RuntimeError(f"export round-trip mismatch: wrote {len(filled)} "
                               f"grades, parse returned {len(parsed)}")
        return out, len(parsed)


class LabelingQueue:
    """Changed lines to label — the dataset of docs/accuracy-enrichment-plan.md §3.1.

    Params: `before`/`after`; `source` (`absence` = the scan's candidates, `stratified`
    = a seeded sample of the pair's added lines split lexicon-hit / no-hit, `n`+`seed`);
    `labeler`. Creation makes a `label_sessions` row carrying taxonomy version and
    pre-labeler identity; items key on `store.line_hash`.
    """

    kind = LABELING

    def __init__(self, queue_id: int, params: dict):
        self.id = queue_id
        self.params = params

    @property
    def pair(self) -> tuple[int, int]:
        return int(self.params["before"]), int(self.params["after"])

    @property
    def source(self) -> str:
        return self.params.get("source") or "absence"

    # -- materialization ---------------------------------------------------

    def _raw_items(self, ctx: Context) -> list[dict]:
        """Deterministic: the scan iterates the diff's sorted changes, the stratified
        sample is seeded, and dedup keys on normalised text — a re-open re-derives
        exactly this list."""
        if self.source not in LABEL_SOURCES:
            raise ReviewError(f"source {self.source!r} is not one of {LABEL_SOURCES}")
        result = ctx.diff(*self.pair)
        if self.source == "absence":
            cands = absence.scan(result, blob_dir=ctx.blob_dir)
            raw = [{"url": c.url, "line": c.line, "stratum": "absence"} for c in cands]
        else:
            raw = self._stratified(ctx, result)
        for item in raw:
            item["id"] = store.line_hash(item["url"], item["line"])
            item["pre_label"] = ("restriction"
                                 if classify.RESTRICTION.search(item["line"]) else None)
        return raw

    def _stratified(self, ctx: Context, result: DiffResult) -> list[dict]:
        """A seeded sample of added lines, half lexicon-hit, half no-hit — the no-hit
        stratum is where the enrichment plan's held-out evaluation needs labels most."""
        from changefeed import blobs

        hit: list[dict] = []
        nohit: list[dict] = []
        seen: set[str] = set()
        for change in result.changes:
            if change.kind != MODIFIED or change.cause != classify.CONTENT:
                continue
            before_body = blobs.read_or_none(
                (change.before or {}).get("content_hash"), ctx.blob_dir)
            after_body = blobs.read_or_none(
                (change.after or {}).get("content_hash"), ctx.blob_dir)
            if before_body is None or after_body is None:
                continue
            _, added = classify.changed_sides(before_body, after_body)
            for line in added:
                key = " ".join(line.split())
                if not key or key in seen:
                    continue
                seen.add(key)
                bucket = hit if classify.RESTRICTION.search(line) else nohit
                bucket.append({"url": change.url, "line": line.strip()})
        n = int(self.params.get("n") or 100)
        rng = random.Random(int(self.params.get("seed") or 1))
        take_hit = min(max(1, n // 2), len(hit))
        take_nohit = min(n - take_hit, len(nohit))
        take_hit = min(len(hit), n - take_nohit)  # top up when a stratum runs short
        drawn = ([{**d, "stratum": "lexicon-hit"} for d in rng.sample(hit, take_hit)]
                 + [{**d, "stratum": "no-hit"} for d in rng.sample(nohit, take_nohit)])
        return drawn

    def seal(self, ctx: Context) -> None:
        raw = self._raw_items(ctx)
        if not raw:
            raise ReviewError(f"no candidate lines for pair "
                              f"#{self.pair[0]} -> #{self.pair[1]} ({self.source})")
        self.params["source"] = self.source
        self.params["pre_labeler"] = PRE_LABELER_V1
        self.params["taxonomy_version"] = store.TAXONOMY_VERSION
        self.params["item_count"] = len(raw)

    def _session(self, ctx: Context) -> dict:
        session = store.session_for_queue(ctx.db, self.id)
        if session is None:
            raise ReviewError(f"queue {self.id} has no label session")
        return session

    def _labels(self, ctx: Context) -> dict[str, dict]:
        session = self._session(ctx)
        return {r["line_hash"]: r
                for r in store.labels_for_session(ctx.db, session["id"])}

    def items(self, ctx: Context) -> list[dict]:
        labels = self._labels(ctx)
        out = []
        for item in self._raw_items(ctx):
            done = item["id"] in labels
            row = {"id": item["id"], "url": item["url"],
                   "slug": evidence._slug(item["url"]), "line": item["line"],
                   "stratum": item["stratum"], "pre_label": item["pre_label"],
                   "done": done}
            if done:
                row["label"] = labels[item["id"]]["label"]
            out.append(row)
        return out

    def progress(self, ctx: Context) -> dict:
        session = store.session_for_queue(ctx.db, self.id)
        done = 0
        if session:
            done = ctx.db.conn.execute(
                "SELECT COUNT(*) FROM line_labels WHERE session_id = ?",
                (session["id"],)).fetchone()[0]
        return {"done": done, "total": int(self.params.get("item_count") or 0)}

    # -- evidence and writes -------------------------------------------------

    def _item(self, ctx: Context, item_id: str) -> dict:
        item = next((i for i in self._raw_items(ctx) if i["id"] == item_id), None)
        if item is None:
            raise ReviewError(f"line {item_id} is not an item of queue {self.id}")
        return item

    def evidence(self, ctx: Context, item_id: str) -> dict:
        item = self._item(ctx, item_id)
        removed, added = evidence.signed_context(
            ctx.db, self.pair, item["url"], blob_dir=ctx.blob_dir)
        labels = self._labels(ctx)
        return {
            "line": item["line"], "url": item["url"],
            "slug": evidence._slug(item["url"]), "stratum": item["stratum"],
            "pre_label": item["pre_label"], "pre_labeler": self.params.get("pre_labeler"),
            "context_removed": removed, "context_added": added,
            "taxonomy": list(store.TAXONOMY), "skip": store.SKIP,
            "done": item_id in labels,
            "label": (labels.get(item_id) or {}).get("label"),
        }

    def submit(self, ctx: Context, item_id: str, payload: dict) -> dict:
        label = payload.get("label")
        if label not in (*store.TAXONOMY, store.SKIP):
            raise ReviewError(
                f"label {label!r} is not one of {(*store.TAXONOMY, store.SKIP)}")
        item = self._item(ctx, item_id)
        session = self._session(ctx)
        removed, added = evidence.signed_context(
            ctx.db, self.pair, item["url"], blob_dir=ctx.blob_dir)
        before, after = self.pair
        store.store_label(ctx.db, {
            "session_id": session["id"], "before_snapshot": before,
            "after_snapshot": after, "url": item["url"], "line_hash": item["id"],
            "line_text": item["line"],
            "context_before": "\n".join(removed) or None,
            "context_after": "\n".join(added) or None,
            "pre_label": item["pre_label"], "label": label,
            "labeler": payload.get("labeler") or self.params.get("labeler"),
            "labeled_at": _now(), "notes": payload.get("notes") or None,
        })
        rows = store.labels_for_session(ctx.db, session["id"])
        return {"stored": {"line_hash": item["id"], "label": label},
                "flips": store.flip_summary(rows)}

    def export(self, ctx: Context, out: Path | None = None) -> tuple[Path, int]:
        """A needle-file-style YAML under reports/labels/. Skip rows are provenance,
        not data: they are counted in the header and excluded from `lines`, so nothing
        unsure can enter a training export (the `unverified` precedent)."""
        import json

        session = self._session(ctx)
        rows = store.labels_for_session(ctx.db, session["id"])
        if not rows:
            raise ReviewError("no labels in this session yet — nothing to export")
        summary = store.flip_summary(rows)
        before, after = self.pair

        def q(text) -> str:
            return json.dumps(text if text is not None else "", ensure_ascii=False)

        lines = [
            f"# Labeled changed lines — #{before} -> #{after}, session {session['id']}.",
            "# See docs/accuracy-enrichment-plan.md §3.1. Lines are verbatim; `pre_label`",
            "# names what the pre-labeler suggested and `label` what a person approved —",
            "# a difference is a flip, the measure of pre-labeler bias. Skipped lines are",
            "# counted below but excluded here: nothing unsure enters training data.",
            f"pair: {{before: {before}, after: {after}}}",
            f"session: {session['id']}",
            f"queue: {self.id}",
            f"taxonomy_version: {q(session['taxonomy_version'])}",
            f"pre_labeler: {q(session['pre_labeler'])}",
            f"exported_at: {q(_now())}",
            f"labeled: {summary['labeled']}",
            f"skipped: {summary['skipped']}",
            f"flips: {summary['flips']}",
            f"flip_rate: {summary['flip_rate'] if summary['flip_rate'] is not None else 'null'}",
            "lines:",
        ]
        kept = 0
        for r in rows:
            if r["label"] == store.SKIP:
                continue
            kept += 1
            lines += [
                f"  - url: {q(r['url'])}",
                f"    line: {q(r['line_text'])}",
                f"    pre_label: {q(r['pre_label']) if r['pre_label'] else 'null'}",
                f"    label: {q(r['label'])}",
                f"    labeler: {q(r['labeler']) if r['labeler'] else 'null'}",
                f"    labeled_at: {q(r['labeled_at'])}",
            ]
            if r["notes"]:
                lines.append(f"    notes: {q(r['notes'])}")
        out = out or Path(f"reports/labels/labels-{before:04d}..{after:04d}"
                          f"-s{session['id']}.yaml")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out, kept


# The queue registry: new review functionality is a new kind here, not a new tool.
REGISTRY: dict[str, type] = {GRADING: GradingQueue, LABELING: LabelingQueue}


def load(kind: str, queue_id: int, params: dict):
    cls = REGISTRY.get(kind)
    if cls is None:
        raise ReviewError(f"unknown queue kind {kind!r}; one of {tuple(REGISTRY)}")
    return cls(queue_id, params)
