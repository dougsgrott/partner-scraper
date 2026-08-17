"""The per-page contract produced by the fetch+enrich Claude call.

A PageRecord carries both the enriched metadata (what you query/organize by) and the
cleaned Markdown body (what you read). See PLAN.md §5.2 and §6.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

ContentType = Literal["docs", "blog", "changelog", "pricing", "reference", "other"]


class PageRecord(BaseModel):
    """Structured result of fetching and enriching a single page."""

    title: str
    company: str
    content_type: ContentType
    theme: str = Field(description="Must be one of the company's taxonomy themes")
    published_date: date | None = None
    updated_date: date | None = None
    summary: str = Field(description="2-3 sentence summary of the page")
    key_entities: list[str] = Field(default_factory=list)
    markdown: str = Field(description="The cleaned page body as Markdown")

    def theme_is_valid(self, allowed_themes: list[str]) -> bool:
        """Whether this record's theme is within the company's taxonomy."""
        return self.theme in allowed_themes


def validate_theme(theme: str, allowed_themes: list[str]) -> None:
    """Raise ValueError if a theme is outside the allowed taxonomy.

    The taxonomy is per-company, so this is checked at runtime rather than via a
    Literal on the model. Ingestion (issue 03) coerces unknown themes to "other";
    this helper is for callers that want a hard failure instead.
    """
    if theme not in allowed_themes:
        raise ValueError(f"theme {theme!r} not in allowed taxonomy {allowed_themes}")
