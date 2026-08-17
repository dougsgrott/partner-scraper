"""Coverage computation: how much of each company/category is scraped.

Pure, read-only, token-free. Cross-references the discovery candidate set (the sitemap,
optionally filtered to the configured scope) against the local index. Returns structured
data; `scripts/coverage.py` formats it and a future UI can consume it directly. See
`docs/coverage.md`.

`category` here is a URL-path section (e.g. `agents-and-tools`) with its path-prefix — the
thing `batch.priorities` matches on — NOT the content `theme` used for `data/` folders.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from .config import AppConfig, SourceConfig
from .discovery import filters as flt
from .discovery import sitemap as sm
from .store.index import Index


def category_for(url: str, source: SourceConfig, depth: int = 1) -> tuple[str, str]:
    """Return (label, prefix) for a URL's category.

    Strips the longest matching include_path prefix, then takes the next `depth` path
    segments as the label; prefix is the full path-prefix (paste-ready for priorities).
    """
    path = urlparse(url).path
    matched = ""
    for prefix in sorted(source.include_paths, key=len, reverse=True):
        if path.startswith(prefix):
            matched = prefix
            break

    remainder = [s for s in path[len(matched):].split("/") if s]
    if not remainder:
        # URL is exactly the prefix (e.g. /cookbook/) — label from the prefix's last segment.
        base = [s for s in matched.split("/") if s]
        return (base[-1] if base else "(root)"), (matched or "/")

    take = remainder[:depth]
    label = "/".join(take)
    prefix = f"{matched}{label}/" if matched else f"/{label}/"
    return label, prefix


@dataclass
class CategoryStat:
    category: str
    prefix: str
    total: int = 0
    scraped: int = 0
    errored: int = 0

    @property
    def pending(self) -> int:
        return self.total - self.scraped - self.errored

    @property
    def pct(self) -> float:
        return 100.0 * self.scraped / self.total if self.total else 0.0

    def to_dict(self) -> dict:
        return {
            "category": self.category, "prefix": self.prefix, "total": self.total,
            "scraped": self.scraped, "errored": self.errored, "pending": self.pending,
            "pct": round(self.pct, 1),
        }


@dataclass
class CompanyCoverage:
    company: str
    categories: list[CategoryStat] = field(default_factory=list)

    @property
    def total(self) -> int:
        return sum(c.total for c in self.categories)

    @property
    def scraped(self) -> int:
        return sum(c.scraped for c in self.categories)

    @property
    def errored(self) -> int:
        return sum(c.errored for c in self.categories)

    @property
    def pending(self) -> int:
        return self.total - self.scraped - self.errored

    @property
    def pct(self) -> float:
        return 100.0 * self.scraped / self.total if self.total else 0.0

    def to_dict(self) -> dict:
        return {
            "company": self.company, "total": self.total, "scraped": self.scraped,
            "errored": self.errored, "pending": self.pending, "pct": round(self.pct, 1),
            "categories": [c.to_dict() for c in self.categories],
        }


def compute(
    cfg: AppConfig,
    *,
    companies: list[str] | None = None,
    use_filters: bool = True,
    depth: int = 1,
    index: Index | None = None,
) -> list[CompanyCoverage]:
    """Per-company, per-category coverage. `use_filters=False` uses the raw sitemap."""
    companies = companies or list(cfg.sources)
    own_index = index is None
    index = index or Index()
    try:
        status_by_url = {r["url"]: r["status"] for r in index.query()}

        results: list[CompanyCoverage] = []
        for company in companies:
            src = cfg.sources[company]
            urls = sm.collect(src)
            if use_filters:
                urls = flt.apply(urls, src, cfg.filters)

            cats: dict[str, CategoryStat] = {}
            for du in urls:
                label, prefix = category_for(du.url, src, depth)
                stat = cats.get(label)
                if stat is None:
                    stat = cats[label] = CategoryStat(label, prefix)
                stat.total += 1
                status = status_by_url.get(du.url)
                if status == "ok":
                    stat.scraped += 1
                elif status is not None:
                    stat.errored += 1

            results.append(CompanyCoverage(company, list(cats.values())))
        return results
    finally:
        if own_index:
            index.close()
