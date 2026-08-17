"""Configuration schema and loader for claude-scraper.

``config/sources.yaml`` declares *sources*. A source is a *tier unit*, not a company: one
company can need two of them when parts of its site are served differently (Anthropic's
`/docs/en/` is native Markdown, its `/cookbook/` is HTML). Each source names the company
it belongs to, where its URLs come from (`seeds`), which paths are in scope, and which
fetcher/extractor pair handles it. See PLAN.md §5.

`fetcher` and `extractor` are validated here but not yet honoured — the fetch tiers land
in step 3 and the extractors in step 5 (PLAN.md §12).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

Fetcher = Literal["markdown_endpoint", "http", "browser"]
Extractor = Literal["passthrough_md", "docusaurus", "nextjs_article", "generic"]


class DumpSeed(BaseModel):
    """URLs from a committed sitemap dump file (offline)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["dump"]
    path: Path


class SitemapSeed(BaseModel):
    """URLs from a live sitemap.xml (network)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["sitemap"]
    url: str


Seed = Annotated[DumpSeed | SitemapSeed, Field(discriminator="type")]


class Defaults(BaseModel):
    """Global fetch defaults.

    The rate settings are a floor on politeness, not a tuning knob — see PLAN.md §6.2.
    They are deliberately below what the target sites would tolerate.
    """

    model_config = ConfigDict(extra="forbid")

    user_agent: str = Field(
        default="indicium-docs-scraper/0.2 (+doug.sgrott@gmail.com)",
        description="Sent on every request. Identify honestly and leave a contact.",
    )
    timeout_s: float = Field(default=30.0, gt=0)
    respect_robots: bool = Field(
        default=True, description="Drop robots.txt-disallowed URLs from the worklist"
    )

    concurrency: int = Field(
        default=2, ge=1, le=8, description="Simultaneous in-flight requests per host"
    )
    requests_per_second: float = Field(
        default=1.0, gt=0, le=10,
        description="Per-host request rate — the binding constraint on run time",
    )
    jitter_s: float = Field(
        default=0.3, ge=0, description="Random extra delay, so we never look like a metronome"
    )
    retries: int = Field(default=3, ge=0, description="Retry attempts for transient failures")
    backoff_max_s: float = Field(default=120.0, gt=0, description="Ceiling on retry backoff")
    max_attempts: int = Field(
        default=3, ge=1, description="Give up on a URL after this many failed runs"
    )


class SourceConfig(BaseModel):
    """One fetch/extract unit: a set of URLs handled by a single tier pair."""

    model_config = ConfigDict(extra="forbid")

    company: str = Field(description="Owning company; groups sources in the corpus + reports")
    seeds: list[Seed] = Field(min_length=1, description="Where this source's URLs come from")
    include_paths: list[str] = Field(
        default_factory=list, description="Keep only URLs whose path matches one of these prefixes"
    )
    exclude_paths: list[str] = Field(
        default_factory=list, description="Drop URLs matching any of these (wins over include)"
    )
    fetcher: Fetcher = "http"
    extractor: Extractor = "generic"
    enabled: bool = Field(default=True, description="Set false to park a source without deleting it")

    def sitemap_urls(self) -> list[str]:
        return [s.url for s in self.seeds if isinstance(s, SitemapSeed)]

    def dump_paths(self) -> list[Path]:
        return [s.path for s in self.seeds if isinstance(s, DumpSeed)]


class Filters(BaseModel):
    """Global filters applied to the discovered URL work-list."""

    model_config = ConfigDict(extra="forbid")

    published_after: date | None = None
    published_before: date | None = None
    max_pages: int | None = Field(default=None, ge=1)


class AppConfig(BaseModel):
    """Top-level application configuration."""

    model_config = ConfigDict(extra="forbid")

    defaults: Defaults = Field(default_factory=Defaults)
    sources: dict[str, SourceConfig] = Field(min_length=1)
    filters: Filters = Field(default_factory=Filters)

    def enabled_sources(self) -> dict[str, SourceConfig]:
        """Sources not parked via `enabled: false`."""
        return {sid: src for sid, src in self.sources.items() if src.enabled}

    def sources_for(self, company: str) -> dict[str, SourceConfig]:
        """Every source belonging to one company."""
        return {sid: src for sid, src in self.sources.items() if src.company == company}

    @property
    def companies(self) -> list[str]:
        """Distinct companies, in config order."""
        return list(dict.fromkeys(src.company for src in self.sources.values()))


def load_config(path: str | Path) -> AppConfig:
    """Load and validate a sources.yaml file into an AppConfig.

    Raises pydantic.ValidationError on unknown keys, empty seeds, or an unknown
    fetcher/extractor name, and FileNotFoundError if the path does not exist.
    """
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"{path}: expected a mapping at the top level, got {type(raw).__name__}")
    return AppConfig.model_validate(raw)
