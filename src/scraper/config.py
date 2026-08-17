"""Configuration schema and loader for claude-scraper.

The config (``config/sources.yaml``) drives which sites are scraped, which paths are
kept, the date window, and the fixed per-company theme taxonomy. See PLAN.md §4.
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


class BatchConfig(BaseModel):
    """Controls the windowed (usage-limit-aware) batch runner. See PLAN / cc_runner.py."""

    model_config = ConfigDict(extra="forbid")

    size: int = Field(default=100, ge=1, description="Max pages ingested per run")
    max_attempts: int = Field(default=3, ge=1, description="Retry cap for errored URLs")
    stop_utilization: float = Field(
        default=0.9, ge=0.0, le=1.0,
        description="Stop the run once the active usage window is this full",
    )
    companies: list[str] | None = Field(
        default=None, description="Restrict runs to these companies (None = all)"
    )
    priorities: list[str] = Field(
        default_factory=list,
        description="Ordered path-prefix patterns; earlier = scraped first",
    )


class AppConfig(BaseModel):
    """Top-level application configuration."""

    model_config = ConfigDict(extra="forbid")

    model: str = "claude-sonnet-4-6"
    max_content_tokens: int = Field(default=30000, ge=1)
    sources: dict[str, SourceConfig] = Field(min_length=1)
    filters: Filters = Field(default_factory=Filters)
    batch: BatchConfig = Field(default_factory=BatchConfig)

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
