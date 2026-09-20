"""Named noise normalisations for raw HTML — issue/accuracy/10.

The raw archive's byte churn is ~80% build noise: tokens a site generator rotates on
every rebuild while the prose stands still. These patterns collapse that noise so a
churn measurement counts what a vendor *changed*, not what its bundler re-emitted.
They were one-off analysis regexes before; each is now a named, tested instrument,
because a redone instrument measures slightly differently and nothing shows it —
cross-window comparisons silently become comparisons between instruments.

The registry is append-only in spirit: every pattern was admitted by a measured
collapse on real archived generations, and the admission is recorded on the pattern.
The safety standard is the 2026-09-09 verification — all 5,255 pages collapsed by the
first two patterns were extracted on both sides and compared: **zero** pages whose
extracted content actually changed were collapsed. A new pattern must clear the same
bar before joining (`scripts/measure.py raw-churn` reports what it would collapse).

A pattern list like this only learns it is *missing* something when a vendor event
exposes it (the 2026-09-11 site-wide re-date looked like 4,966 changed pages until
`date-modified` was added). Detecting that before it swamps a run is
issue/accuracy/11, which consumes this registry.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class NoisePattern:
    """One rotation a site build performs that carries no information."""

    name: str
    pattern: re.Pattern[bytes]
    replacement: bytes
    admitted: str  # when it entered, what it collapsed, how safety was verified


PATTERNS: tuple[NoisePattern, ...] = (
    NoisePattern(
        name="asset-hash",
        pattern=re.compile(rb"\.[0-9a-f]{8}\.(css|js)\b"),
        replacement=rb".HASH.\1",
        admitted=("2026-09-09 — the first hypothesis, and alone it collapsed 0 pages "
                  "(every page also carries css-module churn); gen2->gen3 it collapsed "
                  "188 pages on its own when the bundles rotated without a suffix "
                  "rebuild. Kept first so the attribution stays comparable."),
    ),
    NoisePattern(
        name="css-module-suffix",
        # A Docusaurus CSS-module class: an identifier plus a per-build 4-char
        # suffix (`anchorTargetStickyNavbar_Dt63` -> `_e1Nq`). The suffix can be
        # all-lowercase (`navbarSearchContainer_xryr`), so no character-class
        # narrowing — the 4-char length and identifier head are the whole shape.
        pattern=re.compile(rb"([A-Za-z][A-Za-z0-9]*)_[A-Za-z0-9]{4}\b"),
        replacement=rb"\1_HASH",
        admitted=("2026-09-09 — the real cause of the 80% churn: collapsed 5,255 of "
                  "6,339 changed pages gen1->gen2; all 5,255 extracted on both sides, "
                  "0 real changes collapsed (docs/raw-archive.md)."),
    ),
    NoisePattern(
        name="date-modified",
        pattern=re.compile(rb"<time datetime=[^ >]+ itemprop=dateModified>[^<]*"),
        replacement=rb"<time itemprop=dateModified>DATE",
        admitted=("2026-09-18 — the site-wide re-date to 2026-09-11 made 4,966 "
                  "unchanged pages look modified gen2->gen3; all 609 change-feed "
                  "modifications of that window are among the survivors, so 0 real "
                  "changes collapsed."),
    ),
)


def normalise(body: bytes, patterns: tuple[NoisePattern, ...] = PATTERNS) -> bytes:
    """`body` with every registered rotation replaced by a stable token."""
    for p in patterns:
        body = p.pattern.sub(p.replacement, body)
    return body


def collapse(before: bytes, after: bytes,
             patterns: tuple[NoisePattern, ...] = PATTERNS) -> str | None:
    """The name of the pattern whose addition makes the two bodies equal, else None.

    Patterns apply cumulatively in registry order, so the attribution is "the first
    pattern at which nothing real remains" — the same convention as the recorded
    churn tables, which keeps this week's numbers comparable with 2026-09-09's.
    None means the difference survives every pattern: a real change, or a noise
    pattern nobody has named yet.
    """
    if before == after:
        return None
    for p in patterns:
        before, after = p.pattern.sub(p.replacement, before), p.pattern.sub(p.replacement, after)
        if before == after:
            return p.name
    return None
