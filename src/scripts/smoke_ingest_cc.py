"""Live smoke test for the Claude Agent SDK ingestion path (mirror of smoke_ingest.py).

Run:  env -u ANTHROPIC_API_KEY uv run python scripts/smoke_ingest_cc.py
Auth: uses the ambient Claude Code login (no ANTHROPIC_API_KEY needed / wanted).
Prints the same fields as scripts/smoke_ingest.py so results compare line-for-line.
"""

from __future__ import annotations

from scraper.config import load_config
from scraper.discovery import filters as flt
from scraper.discovery import sitemap as sm
from scraper.ingest.fetch_enrich_cc import fetch_enrich_cc


def pick(urls, n, *, hint=None):
    """Take up to n URLs, preferring ones whose path contains `hint` (e.g. a changelog)."""
    if hint:
        hinted = [u for u in urls if hint in u.url]
        rest = [u for u in urls if hint not in u.url]
        urls = hinted + rest
    return urls[:n]


def main() -> None:
    cfg = load_config("config/sources.yaml")

    a = flt.apply(sm.collect(cfg.sources["anthropic"]), cfg.sources["anthropic"], cfg.filters)
    d = flt.apply(sm.collect(cfg.sources["databricks"]), cfg.sources["databricks"], cfg.filters)

    targets = (
        [("anthropic", u) for u in pick(a, 2)]
        + [("anthropic", u) for u in pick(a, 1, hint="release-notes")]
        + [("databricks", u) for u in pick(d, 2)]
    )

    for company, du in targets:
        res = fetch_enrich_cc(
            du.url,
            company=company,
            allowed_themes=cfg.themes_for(company),
            model=cfg.model,
            max_content_tokens=cfg.max_content_tokens,
        )
        print(f"\n{res.status.upper():11} {du.url}")
        if res.record:
            r = res.record
            print(f"   theme={r.theme}  type={r.content_type}  "
                  f"pub={r.published_date}  upd={r.updated_date}")
            print(f"   title={r.title!r}")
            print(f"   summary={r.summary[:120]}")
            print(f"   body_chars={len(r.markdown)}  entities={r.key_entities[:5]}")
        else:
            print(f"   error={res.error}")


if __name__ == "__main__":
    main()
