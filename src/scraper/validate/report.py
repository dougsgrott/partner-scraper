"""The shape of a validation result. See docs/validation-plan.md.

Every check returns a `Check` rather than printing one, so the same code backs the
report, the JSON artifact, and the tests. A check that cannot run (missing dependency,
missing input) is `SKIPPED` and says why — never silently passing, which is the failure
mode a validator must not have.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

PASSED, FAILED, WARNED, SKIPPED = "passed", "failed", "warned", "skipped"


@dataclass
class Check:
    """One question asked of the corpus, and what the answer was."""

    name: str
    status: str
    summary: str
    count: int = 0                     # how many items tripped it (0 when clean)
    total: int = 0                     # how many were examined
    samples: list[str] = field(default_factory=list)
    detail: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status in (PASSED, SKIPPED, WARNED)

    def render(self) -> str:
        mark = {PASSED: "ok  ", FAILED: "FAIL", WARNED: "warn", SKIPPED: "skip"}[self.status]
        head = f"  [{mark}] {self.name:<34} {self.summary}"
        return "\n".join([head, *(f"           - {s}" for s in self.samples[:5])])


def passed(name: str, summary: str, *, total: int = 0, detail: dict | None = None) -> Check:
    return Check(name, PASSED, summary, total=total, detail=detail or {})


def failed(name: str, summary: str, *, count: int = 0, total: int = 0,
           samples: list[str] | None = None, detail: dict | None = None) -> Check:
    return Check(name, FAILED, summary, count=count, total=total,
                 samples=samples or [], detail=detail or {})


def warned(name: str, summary: str, *, count: int = 0, total: int = 0,
           samples: list[str] | None = None, detail: dict | None = None) -> Check:
    return Check(name, WARNED, summary, count=count, total=total,
                 samples=samples or [], detail=detail or {})


def skipped(name: str, why: str) -> Check:
    return Check(name, SKIPPED, why)


@dataclass
class Report:
    """A full validation pass."""

    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds"))
    sections: dict[str, list[Check]] = field(default_factory=dict)
    elapsed_s: float = 0.0

    def add(self, section: str, *checks: Check) -> None:
        self.sections.setdefault(section, []).extend(checks)

    @property
    def checks(self) -> list[Check]:
        return [c for checks in self.sections.values() for c in checks]

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if c.status == FAILED]

    @property
    def ok(self) -> bool:
        return not self.failures

    def render(self) -> str:
        lines = [f"validate {self.started_at}"]
        for section, checks in self.sections.items():
            lines.append(f"\n{section}")
            lines.extend(c.render() for c in checks)
        counts = {s: sum(1 for c in self.checks if c.status == s)
                  for s in (PASSED, WARNED, FAILED, SKIPPED)}
        lines.append(
            f"\n{counts[PASSED]} passed · {counts[WARNED]} warned · "
            f"{counts[FAILED]} failed · {counts[SKIPPED]} skipped   ({self.elapsed_s:.1f}s)"
        )
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at,
            "elapsed_s": self.elapsed_s,
            "ok": self.ok,
            "sections": {s: [asdict(c) for c in checks] for s, checks in self.sections.items()},
        }

    def write(self, directory: str | Path = "state/validation") -> Path:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.started_at.replace(':', '').replace('-', '')}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path
