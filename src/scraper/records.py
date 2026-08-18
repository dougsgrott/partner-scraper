"""Shared record types. See PLAN.md §7.1.

These live outside both `extract` and `store` because both need them: extraction produces
an `Extracted`, storage consumes one. Putting the contract in either package would make
the two import each other in a cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from pydantic import BaseModel, Field


@dataclass
class RawPayload:
    """One archived response, handed to an extractor."""

    url: str
    company: str
    source_id: str
    content: bytes
    content_type: str | None = None
    final_url: str | None = None
    include_paths: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", "replace")

    @property
    def canonical_url(self) -> str:
        """The URL the content really lives at, after redirects."""
        return self.final_url or self.url


class Extracted(BaseModel):
    """The cleaned result of parsing one archived page."""

    title: str
    markdown: str
    canonical_url: str
    source_url: str
    company: str
    source_id: str
    category: str
    description: str | None = None
    published_date: date | None = None
    updated_date: date | None = None
    breadcrumbs: list[str] = Field(default_factory=list)
    code_languages: list[str] = Field(default_factory=list)
    extractor: str = "unknown"
    extractor_version: str = "0"

    @property
    def body_chars(self) -> int:
        return len(self.markdown.strip())
