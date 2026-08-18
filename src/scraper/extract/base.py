"""The extractor contract and the quality gate. See PLAN.md §7.1, §7.2.

An extractor is a **pure function of archived bytes**. It never fetches, never writes, and
never reaches for anything outside its `RawPayload`. That is what makes iterating on
extraction free: run it over `raw/` as many times as it takes, at no cost to anyone else's
server.

The quality gate exists because a silent extraction failure is worse than a loud one. A
page that yields an empty body, or a nav-only shell, or the site's 404 template, will
happily write a valid-looking Markdown file that nobody notices is wrong until it turns up
in a search result. Every extraction is scored, and failures are recorded with a reason
while the raw bytes stay on disk for a retry after the extractor is fixed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

from ..records import Extracted, RawPayload

__all__ = [
    "MIN_BODY_CHARS",
    "Extracted",
    "QualityReport",
    "RawPayload",
    "check_quality",
    "collapse_blank_lines",
    "parse_date",
]

# Below this, whatever we extracted is not a document. Calibrated against the real
# corpus: the Databricks SPA shell yields 31 characters, while genuine reference stubs
# (an error-condition page with a one-line description) run to ~120. Set between them.
MIN_BODY_CHARS = 100

# Markers that mean "this is not the page you asked for" — matched against the TITLE only.
#
# Matching the body was a mistake worth recording: docs.databricks.com documents error
# conditions, so `/error-messages/hdfs-http-error-error-class` legitimately contains the
# phrase "404 Not Found", and a page on Kinesis permissions legitimately contains "access
# denied". Body matching rejected both. A real error page announces itself in its title.
_ERROR_MARKERS = (
    "page not found",
    "404 not found",
    "this page could not be found",
    "just a moment...",          # Cloudflare interstitial
    "enable javascript and cookies to continue",
    "access denied",
)


@dataclass
class QualityReport:
    """Why an extraction was accepted or rejected."""

    issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues

    def __str__(self) -> str:
        return "; ".join(self.issues) or "ok"


def check_quality(extracted: Extracted, *, min_chars: int = MIN_BODY_CHARS) -> QualityReport:
    """Score an extraction. An empty issue list means it is fit for the corpus."""
    issues: list[str] = []
    body = extracted.markdown.strip()

    if len(body) < min_chars:
        issues.append(f"body too short ({len(body)} < {min_chars} chars)")

    if not extracted.title.strip():
        issues.append("missing title")

    title = extracted.title.lower()
    for marker in _ERROR_MARKERS:
        if marker in title:
            issues.append(f"error-page title: {marker!r}")
            break

    if _unclosed_fence(body):
        issues.append("unbalanced code fence")

    if _looks_like_markup(body):
        issues.append("output still contains HTML markup")

    return QualityReport(issues)


_FENCE_LINE = re.compile(r"^(`{3,})(.*)$")
_FENCED = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def _unclosed_fence(body: str) -> bool:
    """Whether a code fence is left open.

    Counting ``` occurrences is not enough: a block quoting Markdown is opened with a
    *longer* fence and legitimately contains ``` inside it, which makes a naive count odd
    on a perfectly well-formed document. Track the open fence and require the closer to be
    at least as long, as CommonMark specifies.
    """
    open_fence: str | None = None
    for line in body.splitlines():
        match = _FENCE_LINE.match(line)
        if not match:
            continue
        ticks, info = match.group(1), match.group(2).strip()
        if open_fence is None:
            open_fence = ticks
        elif len(ticks) >= len(open_fence) and not info:
            open_fence = None
    return open_fence is not None


def _looks_like_markup(body: str) -> bool:
    """Catch conversions that left raw HTML behind.

    Fenced code is excluded first: documentation legitimately *contains* markup as example
    code — a page on collecting user feedback ships a React component — and counting that
    rejected perfectly good pages. A few stray tags in prose are normal (`<br>`, inline
    `<sup>`); a wall of them means the converter did not do its job.
    """
    prose = _FENCED.sub("", body)
    tags = len(re.findall(r"<(?:div|span|section|article|nav|script|style)\b", prose))
    return tags > 5


_DATE_FORMATS = (
    "%b %d, %Y",      # Jul 10, 2026   (Docusaurus "Last updated on")
    "%B %d, %Y",      # July 10, 2026
    "%Y-%m-%d",
)


def parse_date(value: str | None) -> date | None:
    """Parse the date formats the target sites actually publish."""
    if not value:
        return None
    text = re.sub(r"^\s*last updated (?:on)?\s*", "", value.strip(), flags=re.IGNORECASE).strip()
    text = text.rstrip(".")
    for fmt in _DATE_FORMATS:
        try:
            # These are calendar dates printed on a page, not instants — no tz applies.
            return datetime.strptime(text, fmt).date()  # noqa: DTZ007
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


def collapse_blank_lines(markdown: str) -> str:
    """Normalise the ragged whitespace HTML-to-Markdown conversion leaves behind."""
    text = re.sub(r"[ \t]+\n", "\n", markdown)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"
