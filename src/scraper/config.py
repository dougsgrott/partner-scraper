"""Configuration schema and loader for claude-scraper.

The config (``config/sources.yaml``) drives which sites are scraped and which paths are
kept. See PLAN.md §5.

Still to come (PLAN.md §5): per-source ``fetcher``/``extractor`` selection, seed
declarations, and the politeness defaults. ``themes`` is a leftover of the retired
LLM-classification path and disappears once the corpus is laid out by URL-derived
``category`` instead (PLAN.md §7.3).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class SourceConfig(BaseModel):
    """Per-company scraping configuration."""

    model_config = ConfigDict(extra="forbid")

    sitemaps: list[str] = Field(min_length=1, description="Sitemap URLs to collect from")
    include_paths: list[str] = Field(
        default_factory=list, description="Keep only URLs whose path matches one of these prefixes"
    )
    exclude_paths: list[str] = Field(
        default_factory=list, description="Drop URLs matching any of these (wins over include)"
    )
    themes: list[str] = Field(
        min_length=1, description="Closed taxonomy Claude must classify pages into"
    )


class Filters(BaseModel):
    """Global filters applied to the discovered URL work-list."""

    model_config = ConfigDict(extra="forbid")

    published_after: date | None = None
    published_before: date | None = None
    max_pages: int | None = Field(default=None, ge=1)


class AppConfig(BaseModel):
    """Top-level application configuration."""

    model_config = ConfigDict(extra="forbid")

    sources: dict[str, SourceConfig] = Field(min_length=1)
    filters: Filters = Field(default_factory=Filters)

    def themes_for(self, company: str) -> list[str]:
        """Allowed theme values for a company. Raises KeyError if the company is unknown."""
        return self.sources[company].themes


def load_config(path: str | Path) -> AppConfig:
    """Load and validate a sources.yaml file into an AppConfig.

    Raises pydantic.ValidationError on unknown keys, empty sitemaps, or empty themes,
    and FileNotFoundError if the path does not exist.
    """
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path}: expected a mapping at the top level, got {type(raw).__name__}")
    return AppConfig.model_validate(raw)
