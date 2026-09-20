"""Standing instruments for the measurements the accuracy work kept redoing.

Issue/accuracy/10. Three analyses and one invariant, promoted from one-off scripts
that no longer existed as runnable artifacts:

* ``raw_churn`` — byte churn between two archived generations, attributed to the
  named noise patterns of `scraper.fetch.noise`, survivors listed.
* ``duplicate_bodies`` — duplicate-body groups within one snapshot, with the known
  Admin-API mirror breakdown.
* ``ranking_overlap`` — where the digest's cited pages sit in the severity ranking
  (the issue/accuracy/08 measurement, kept runnable).
* ``reconcile`` — the three-way cross-check (change feed = extract output churn ≈ raw
  survivors) that held for #5 → #6 and was checked exactly once, by hand. It runs
  with every `changes.py run` and post-hoc via `scripts/measure.py cross-check`.

Every instrument is validated by reproducing the figures published in
`docs/session-2026-09-18-lessons.md` and `docs/raw-archive.md` against the stored
generations and pairs — reproduction of known results is the acceptance test, and a
figure that stops reproducing is a finding about the instrument or the record.
"""

from __future__ import annotations

import gzip
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from scraper.fetch import noise, rawstore

DEFAULT_MEASURE_DIR = Path("reports/measure")

# A duplicate-body group is "the known mirror" when it spans the Admin API and its
# beta republication — the pairing includes renames (`federation_rules` ->
# `federation/rules`), so membership, not a rewrite rule, is the measured criterion
# (132 of 175 groups in #7).
MIRROR_MARKERS = ("/api/admin/", "/api/beta/organization")


# -- raw churn --------------------------------------------------------------

@dataclass
class RawChurn:
    """Byte churn between two generations, attributed to named noise patterns."""

    gen1: str
    gen2: str
    in_both: int = 0
    identical: int = 0
    collapsed: dict[str, int] = field(default_factory=dict)
    survivors: list[str] = field(default_factory=list)
    by_company: dict[str, dict[str, int]] = field(default_factory=dict)
    collapsed_paths: set[str] = field(default_factory=set)

    @property
    def differ(self) -> int:
        return self.in_both - self.identical

    def render(self) -> str:
        lines = [
            f"raw churn {self.gen1} -> {self.gen2}",
            f"  files in both      {self.in_both}",
            f"  bytes identical    {self.identical}",
            f"  bytes differ       {self.differ}",
        ]
        for p in noise.PATTERNS:
            lines.append(f"  collapsed by {p.name:18s} {self.collapsed.get(p.name, 0)}")
        lines.append(f"  survivors          {len(self.survivors)}")
        for company, row in sorted(self.by_company.items()):
            lines.append(f"    {company:12s} collapsed {row.get('collapsed', 0)}, "
                         f"survivors {row.get('survivors', 0)}")
        return "\n".join(lines)


def raw_churn(gen1_dir: str | Path, gen2_dir: str | Path,
              patterns: tuple[noise.NoisePattern, ...] = noise.PATTERNS) -> RawChurn:
    """Compare two generations exhaustively — not sampled — like the 2026-09-09 study.

    `patterns` narrows the registry, which is how the canary's gating test re-runs a
    historical event blind: the registry as it stood before the pattern existed.
    """
    g1, g2 = Path(gen1_dir), Path(gen2_dir)
    files1 = {p.relative_to(g1) for p in g1.rglob("*.gz")}
    files2 = {p.relative_to(g2) for p in g2.rglob("*.gz")}
    both = sorted(files1 & files2)

    out = RawChurn(gen1=g1.name, gen2=g2.name, in_both=len(both))
    for rel in both:
        before = gzip.decompress((g1 / rel).read_bytes())
        after = gzip.decompress((g2 / rel).read_bytes())
        if before == after:
            out.identical += 1
            continue
        company = rel.parts[0]
        row = out.by_company.setdefault(company, {"collapsed": 0, "survivors": 0})
        name = noise.collapse(before, after, patterns)
        if name:
            out.collapsed[name] = out.collapsed.get(name, 0) + 1
            out.collapsed_paths.add(str(rel))
            row["collapsed"] += 1
        else:
            out.survivors.append(str(rel))
            row["survivors"] += 1
    return out


# -- duplicate bodies -------------------------------------------------------

@dataclass
class Duplicates:
    snapshot: int
    groups: int = 0
    mirror_groups: int = 0
    pages_in_groups: int = 0
    sizes: dict[int, int] = field(default_factory=dict)
    non_mirror_samples: list[list[str]] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            f"duplicate bodies in snapshot #{self.snapshot}",
            f"  groups             {self.groups}",
            f"  admin=beta mirrors {self.mirror_groups}",
            f"  pages involved     {self.pages_in_groups}",
            "  group sizes        " + ", ".join(
                f"{n}x{c}" for n, c in sorted(self.sizes.items())),
        ]
        for urls in self.non_mirror_samples[:8]:
            lines.append("    non-mirror: " + "  =  ".join(urls))
        return "\n".join(lines)


def duplicate_bodies(db, snapshot_id: int) -> Duplicates:
    """Groups of pages sharing one body within a snapshot.

    The digest reads every member as a separate change, so a group is doubled (or
    octupled) evidence for one fact — the mirror count says how much of that is the
    one known, structural cause rather than something new worth reading.
    """
    rows = db.conn.execute(
        """SELECT content_hash, COUNT(*) AS n, GROUP_CONCAT(url, ' ') AS urls
           FROM page_versions WHERE snapshot_id = ? GROUP BY content_hash
           HAVING n > 1 ORDER BY n DESC, urls""", (snapshot_id,)).fetchall()
    out = Duplicates(snapshot=snapshot_id, groups=len(rows))
    for _hash, n, urls in rows:
        out.pages_in_groups += n
        out.sizes[n] = out.sizes.get(n, 0) + 1
        if MIRROR_MARKERS[0] in urls and MIRROR_MARKERS[1] in urls:
            out.mirror_groups += 1
        elif len(out.non_mirror_samples) < 8:
            out.non_mirror_samples.append(urls.split(" "))
    return out


# -- ranking overlap --------------------------------------------------------

@dataclass
class RankingOverlap:
    pair: tuple[int, int]
    universe: int = 0
    findings: int = 0
    ranked: list[int] = field(default_factory=list)  # best-cited rank per finding
    unranked: int = 0

    def _q(self, p: float) -> int:
        return sorted(self.ranked)[int(p * (len(self.ranked) - 1))]

    def render(self) -> str:
        if not self.ranked:
            return (f"ranking overlap #{self.pair[0]} -> #{self.pair[1]}: "
                    f"no findings with a ranked page")
        r = sorted(self.ranked)
        top = {n: sum(1 for v in r if v <= n) for n in (30, 100, 300)}
        return "\n".join([
            f"ranking overlap #{self.pair[0]} -> #{self.pair[1]}",
            f"  findings           {self.findings}  ({self.unranked} citing no ranked page)",
            f"  rank universe      {self.universe} modifications",
            (f"  best-cited rank    min {r[0]}  q25 {self._q(.25)}  med {self._q(.5)}  "
             f"q75 {self._q(.75)}  max {r[-1]}"),
            "  in top-N           " + "  ".join(f"top-{n}: {c}/{len(r)}"
                                                for n, c in top.items()),
            ("  (ranks inside an exact-severity tie block are tiebreak order — read them "
             "+/- the block; issue/accuracy/08)"),
        ])


def ranking_overlap(db, pair: tuple[int, int], report_json: str | Path,
                    *, graded: bool = False) -> RankingOverlap:
    """Where the digest's citations sit in the severity order the model read.

    Default: the pair's current findings. ``graded=True`` pools every full-page-graded
    finding across arms instead — the population issue/accuracy/08 measured, kept
    reproducible here. Not a quality metric either way: graded recall replaced
    recall-vs-ranking (issue/accuracy/01), and 08 showed the model cites true material
    at rank 948. This instrument watches the *ordering*, e.g. after a classifier bump.
    """
    report = json.loads(Path(report_json).read_text(encoding="utf-8"))
    mods = [c for c in report["changes"]
            if c["kind"] == "modified" and c["cause"] == "content"]
    mods.sort(key=lambda c: (-c["severity"], c["company"], c["url"]))
    rank = {c["url"]: i for i, c in enumerate(mods, 1)}

    if graded:
        rows = db.conn.execute(
            """SELECT f.urls FROM findings f
               JOIN verdicts v ON v.finding_id = f.id AND v.method = 'full-page'
               WHERE f.before_snapshot = ? AND f.after_snapshot = ?
                 AND v.verdict IN ('true', 'partly')""", pair).fetchall()
    else:
        rows = db.conn.execute(
            """SELECT urls FROM findings
               WHERE before_snapshot = ? AND after_snapshot = ?
                 AND superseded_at IS NULL""", pair).fetchall()

    out = RankingOverlap(pair=pair, universe=len(mods), findings=len(rows))
    for (urls,) in rows:
        ranks = [rank[u] for u in json.loads(urls) if u in rank]
        if ranks:
            out.ranked.append(min(ranks))
        else:
            out.unranked += 1
    return out


# -- the cross-check invariant ----------------------------------------------

# -- the noise canary (issue/accuracy/11) -----------------------------------

# Measured base rates over the stored generations (recorded in the issue file):
# quiet pairs run ~6-8% unknown noise among survivors; the two known events, replayed
# with the registry as it stood before each pattern, ran 81-84%. The threshold sits
# between with ~2.5x margin each way; the minimum count keeps a tiny survivor set
# (where a handful of residual pages is 100%) from alarming on nothing.
CANARY_THRESHOLD = 0.20
CANARY_MIN = 50


def _modified_paths(modified: list[dict]) -> set[str]:
    """Raw-archive paths a window's content modifications can live at."""
    return {
        str(rawstore.relative_path_for(m["url"], m["company"], ext=ext))
        for m in modified for ext in ("html", "md")}


@dataclass
class Canary:
    """Survivors whose bytes changed while the corpus saw no content change.

    By construction these are noise the registry does not know — the signal that
    existed unexploited when the 2026-09-11 re-date made 4,966 pages look changed.
    A mass *real* edit does not trip this: its pages are content modifications, so
    they are subtracted before the rate is taken.
    """

    candidates: list[str]
    survivors: int

    @property
    def rate(self) -> float:
        return len(self.candidates) / self.survivors if self.survivors else 0.0

    @property
    def tripped(self) -> bool:
        return len(self.candidates) >= CANARY_MIN and self.rate > CANARY_THRESHOLD

    def render(self, gen1: str = "GEN1", gen2: str = "GEN2") -> str:
        line = (f"canary: {len(self.candidates)} of {self.survivors} churn survivors "
                f"changed bytes but not content ({self.rate:.0%})")
        if not self.tripped:
            return f"- {line} — quiet (threshold {CANARY_THRESHOLD:.0%}, min {CANARY_MIN})"
        return (f"- **!! CANARY: {line} — a noise pattern the registry does not know. "
                f"Investigate:** `uv run python scripts/measure.py residue "
                f"{gen1} {gen2} --pair BEFORE AFTER`")


def unknown_noise(churn: RawChurn, modified: list[dict]) -> Canary:
    """The canary's candidate set: churn survivors minus the window's real changes."""
    real = _modified_paths(modified)
    return Canary(candidates=[s for s in churn.survivors if s not in real],
                  survivors=len(churn.survivors))


@dataclass
class Cluster:
    """One shared byte-change shape across the candidate files."""

    shape: str
    files: int
    occurrences: int
    exemplars: list[tuple[str, str]] = field(default_factory=list)  # (old ctx, new ctx)

    def render(self, sampled: int) -> str:
        flag = "  <- candidate pattern" if self.files >= sampled / 2 else ""
        lines = [(f"  {self.shape:28s} files {self.files}/{sampled}  "
                  f"occurrences {self.occurrences}{flag}")]
        for old, new in self.exemplars[:2]:
            lines.append(f"      - …{old}…")
            lines.append(f"      + …{new}…")
        return "\n".join(lines)


_WORD = re.compile(rb"[A-Za-z0-9]+")


def _word_class(w: bytes) -> str:
    if w.isdigit():
        return "digits"
    if w.isalpha():
        return "letters"
    return "alnum"


def _context(body: bytes, start: int, end: int, width: int = 55) -> str:
    return body[max(0, start - width):end + width].decode("utf-8", "replace")


def cluster_residue(gen1_dir: str | Path, gen2_dir: str | Path,
                    candidates: list[str],
                    patterns: tuple[noise.NoisePattern, ...] = noise.PATTERNS,
                    *, sample_files: int = 40, top: int = 8,
                    max_words: int = 400) -> tuple[list[Cluster], int]:
    """Option A of issue/accuracy/11: name the byte pattern the candidates share.

    For each sampled candidate pair, known noise is normalised away first, then the
    *word multiset difference* between the sides is clustered by shape — (length,
    character class, preceding byte) — with real byte context kept as exemplars. The
    output does not name a regex; it shows a human the recurring shape and its
    surroundings, which is what turned `_Dt63` and `<time …dateModified>` from
    mysteries into patterns. Returns `(clusters, files_sampled)`.
    """
    g1, g2 = Path(gen1_dir), Path(gen2_dir)
    sample = candidates[::max(1, len(candidates) // sample_files)][:sample_files]
    grouped: dict[tuple, Cluster] = {}

    def keyed(body: bytes, words) -> dict[tuple, tuple[str, int]]:
        """Cluster one side's differing words by (length, class, preceding byte)."""
        found: dict[tuple, list] = {}
        for w, n in words.most_common(max_words):
            i = body.find(w)
            if i < 0:  # pragma: no cover - a multiset word always exists in its body
                continue
            prev = chr(body[i - 1]) if i > 0 else "^"
            entry = found.setdefault((len(w), _word_class(w), prev), [None, 0])
            entry[1] += n
            if entry[0] is None:
                entry[0] = _context(body, i, i + len(w))
        return {k: (ctx, count) for k, (ctx, count) in found.items()}

    for rel in sample:
        before = noise.normalise(gzip.decompress((g1 / rel).read_bytes()), patterns)
        after = noise.normalise(gzip.decompress((g2 / rel).read_bytes()), patterns)
        w1 = Counter(m.group(0) for m in _WORD.finditer(before))
        w2 = Counter(m.group(0) for m in _WORD.finditer(after))
        removed, added = w1 - w2, w2 - w1

        old_side = keyed(before, removed)
        new_side = keyed(after, added)
        for key in set(old_side) | set(new_side):
            length, wclass, prev = key
            cluster = grouped.setdefault(key, Cluster(
                shape=f"{wclass} len {length} after {prev!r}", files=0, occurrences=0))
            cluster.files += 1
            cluster.occurrences += (old_side.get(key, ("", 0))[1]
                                    + new_side.get(key, ("", 0))[1])
            if len(cluster.exemplars) < 3 and key in old_side and key in new_side:
                cluster.exemplars.append((old_side[key][0], new_side[key][0]))

    ranked = sorted(grouped.values(), key=lambda c: (-c.files, -c.occurrences))
    return ranked[:top], len(sample)


# -- the cross-check invariant ----------------------------------------------

@dataclass
class Reconciliation:
    """The three-way identity, with the legs it could and could not check.

    ``ok`` is False only on a *hard* mismatch — one no healthy pipeline produces:
    the feed reporting more changed/new pages than extraction wrote non-identical
    output files for, or (given generations) a content modification whose raw bytes
    the noise patterns collapsed, which would mean a real change was eaten as noise.
    A nonzero residue is not a failure; it is printed, because next window's reader
    should see the same ~2% the record saw, not a mystery.
    """

    feed: dict[str, int]
    causes: dict[str, int]
    extract: dict | None = None
    churn: RawChurn | None = None
    canary: Canary | None = None
    missed_real: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        if self.missed_real:
            return False
        return self.extract is None or self.feed_changed <= self.extract_changed

    @property
    def feed_changed(self) -> int:
        """Pages the feed says have new output: content modifications plus additions."""
        return self.causes.get("content", 0) + self.feed.get("added", 0)

    @property
    def extract_changed(self) -> int:
        assert self.extract is not None
        return self.extract.get("written", 0) - self.extract.get("unchanged_files", 0)

    def render(self) -> str:
        lines = ["## Reconciliation", ""]
        f = self.feed
        lines.append(f"- change feed: {self.causes.get('content', 0)} content-modified · "
                     f"{f.get('added', 0)} added · {f.get('metadata', 0)} metadata-only · "
                     f"{f.get('moved', 0)} moved")
        for cause in ("pipeline", "unknown"):
            if self.causes.get(cause):
                lines.append(f"- WARNING: {self.causes[cause]} changes attributed "
                             f"`{cause}` — read them before trusting this window")
        if self.extract is None:
            lines.append("- extract: no summary for this window (persisted to "
                         "state/extracts/ since 2026-09-19)")
        else:
            lines.append(f"- extract: wrote {self.extract.get('written', 0)}, "
                         f"{self.extract.get('unchanged_files', 0)} byte-identical -> "
                         f"{self.extract_changed} changed outputs")
            residue = self.extract_changed - self.feed_changed
            lines.append(f"- residue: {residue} changed outputs beyond feed-changed "
                         f"pages (frontmatter/metadata churn; ~2% is normal)")
        if self.churn is not None:
            lines.append(f"- raw churn: {self.churn.differ} changed files, "
                         f"{len(self.churn.survivors)} survive noise normalisation")
            lines.append(f"- content modifications collapsed as noise: "
                         f"{len(self.missed_real)} (must be 0)")
            for url in self.missed_real[:10]:
                lines.append(f"    !! {url}")
        if self.canary is not None and self.churn is not None:
            lines.append(self.canary.render(self.churn.gen1, self.churn.gen2))
        lines.extend(f"- {n}" for n in self.notes)
        checked = []
        if self.extract is not None:
            checked.append("feed changes within extract's changed outputs")
        if self.churn is not None:
            checked.append("no real change collapsed as noise")
        if self.ok:
            verdict = ("ok — " + " · ".join(checked) if checked
                       else "nothing to check — no extract summary or generations "
                            "for this window")
        else:
            verdict = ("!! MISMATCH — a leg disagrees; a diff missing pages, an "
                       "extractor double-writing, or a noise pattern eating a real "
                       "change. Do not trust this window until explained.")
        lines.append(f"- **{verdict}**")
        return "\n".join(lines)


def reconcile(feed_counts: dict[str, int], feed_causes: dict[str, int],
              *, extract: dict | None = None, churn: RawChurn | None = None,
              modified: list[dict] | None = None) -> Reconciliation:
    """Cross-check one window's legs. Any leg may be absent; checks degrade to fewer.

    ``modified`` (url/company dicts for content modifications) enables the per-page
    third leg against ``churn``: every content modification's raw file must be a
    churn survivor. That is the "0 missed real changes" figure of the record, as a
    standing check instead of a one-time verification.
    """
    rec = Reconciliation(feed=dict(feed_counts), causes=dict(feed_causes),
                         extract=extract, churn=churn)
    if churn is not None and modified:
        known = churn.collapsed_paths | set(churn.survivors)
        mapped = 0
        for m in modified:
            candidates = {
                str(rawstore.relative_path_for(m["url"], m["company"], ext=ext))
                for ext in ("html", "md")}
            if candidates & churn.collapsed_paths:
                rec.missed_real.append(m["url"])
            if candidates & known:
                mapped += 1
        if not mapped:
            rec.notes.append("no modified URL mapped onto the generation files — "
                             "wrong generation pair for this snapshot window?")
        else:
            # The noise canary (issue/accuracy/11): a tripped canary is a loud
            # warning, never a failure — the investigation is a human's.
            rec.canary = unknown_noise(churn, modified)
    return rec
