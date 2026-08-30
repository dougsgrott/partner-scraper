"""The tools a digest session can call. See docs/changefeed-phase-2.md.

Every handler here is a plain async function taking a dict and returning a dict, which is
the point: **the tool layer is fully testable with no model, no SDK and no network.** Only
the thin `create_sdk_mcp_server` wrapper at the bottom touches `claude-agent-sdk`, and it
imports it lazily.

The session already has every change in its prompt, so these are not for discovery — they
are for *checking*. A 280-character excerpt is enough to rank a change and not always enough
to describe it, so the agent opens the full diff for the handful it intends to write about.

`record_finding` is the output channel. Its URL argument is validated against the run's
change set, because a schema can guarantee a finding is well-formed but only a membership
test shows it is about something that actually changed.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scraper.store import writer

from ..db import ChangeDB
from ..diff import DiffResult, PageChange, render_diff
from .findings import IMPACTS, Finding, record

# Cap what a tool can return. The prompt is already ~105k tokens; a 6 MB page pasted into
# the conversation would blow the budget for one page's worth of context.
MAX_DIFF_CHARS = 12_000
MAX_PAGE_CHARS = 20_000


def _slug(url: str) -> str:
    """The path a compressed record shows — what the model sees, and so what it answers."""
    for marker in ("/en/", "/docs/", "://"):
        if marker in url:
            return url.split(marker, 1)[1]
    return url


def _text(payload: str, *, is_error: bool = False) -> dict:
    result: dict[str, Any] = {"content": [{"type": "text", "text": payload}]}
    if is_error:
        result["is_error"] = True
    return result


@dataclass
class DigestContext:
    """Everything the tools need, resolved once per session."""

    result: DiffResult
    db: ChangeDB
    blob_dir: str | None = None
    data_root: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    recorded: list[Finding] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    # How the model chose to record. Turns are what a session costs, so a drift back to
    # one finding per call is a cost regression — and nothing but the bill would show it.
    calls: Counter = field(default_factory=Counter)
    _by_url: dict[str, PageChange] = field(default_factory=dict)
    _by_slug: dict[str, PageChange] = field(default_factory=dict)
    _inbound: dict[str, int] | None = None

    def __post_init__(self) -> None:
        self._by_url = {c.url: c for c in self.result.changes}
        self._by_slug = {_slug(c.url): c for c in self.result.changes}

    def find(self, url: str) -> PageChange | None:
        """Resolve a path the model supplied, in order of decreasing confidence.

        1. the full URL, 2. the slug shown in the prompt, 3. a unique suffix.

        **Step 2 is load-bearing.** The prompt shows slugs, so that is what the model
        answers with, and a first version that went straight from exact URL to fuzzy
        matching rejected 194 of 1,334 legitimate slugs — every short one, because
        `ai-gateway/` is a substring of `ai-gateway/query-model-services` and the
        uniqueness check then found several matches and gave up. A real digest run showed
        69 rejected citations that looked like the model inventing pages and were this
        instead.

        Ambiguity still resolves to nothing rather than to a guess; it is simply no longer
        manufactured.
        """
        if url in self._by_url:
            return self._by_url[url]
        candidate = _slug(url)
        if candidate in self._by_slug:
            return self._by_slug[candidate]
        matches = [c for u, c in self._by_url.items() if u.endswith(url)]
        return matches[0] if len(matches) == 1 else None

    def inbound(self) -> dict[str, int]:
        """How many corpus pages link to each URL. Computed once; it scans the corpus."""
        if self._inbound is None:
            from scraper.validate.coverage import corpus_links
            data = self.data_root or "data"
            self._inbound = {url: n for url, n in corpus_links(data).items()}
        return self._inbound


def make_handlers(ctx: DigestContext) -> dict[str, Any]:
    """The four handlers, closed over one session's context."""

    async def get_diff(args: dict) -> dict:
        change = ctx.find(str(args.get("url", "")))
        if change is None:
            return _text(f"no change in this run matches {args.get('url')!r}", is_error=True)
        body = render_diff(change, blob_dir=ctx.blob_dir, max_chars=MAX_DIFF_CHARS)
        return _text(body or "the stored body for this change is unavailable")

    async def read_page(args: dict) -> dict:
        change = ctx.find(str(args.get("url", "")))
        if change is None:
            return _text(f"no change in this run matches {args.get('url')!r}", is_error=True)
        path = (change.after or change.before or {}).get("file_path")
        if not path or not Path(path).exists():
            return _text("this page has no file on disk (it was removed)", is_error=True)
        _, body = writer.parse(path)
        return _text(body[:MAX_PAGE_CHARS])

    async def inbound_links(args: dict) -> dict:
        change = ctx.find(str(args.get("url", "")))
        if change is None:
            return _text(f"no change in this run matches {args.get('url')!r}", is_error=True)
        count = ctx.inbound().get(change.url, 0)
        return _text(f"{count} corpus pages link to {change.url}")

    async def record_finding(args: dict) -> dict:
        ctx.calls["record calls"] += 1
        impact = str(args.get("impact", "")).strip().lower()
        summary = str(args.get("summary", "")).strip()
        urls = args.get("urls") or []
        if isinstance(urls, str):
            urls = [urls]

        if impact not in IMPACTS:
            return _text(f"impact must be one of {', '.join(IMPACTS)}", is_error=True)
        if not summary:
            return _text("summary is required", is_error=True)

        # The membership test. A finding citing a page nobody touched is worse than a
        # missing finding: it is confidently wrong, and nothing downstream would catch it.
        resolved, unknown = [], []
        for url in urls:
            change = ctx.find(str(url))
            (resolved.append(change.url) if change else unknown.append(str(url)))
        if unknown:
            ctx.rejected.extend(unknown)
            return _text(
                f"these are not changes in this run: {', '.join(unknown[:5])}. "
                "Cite only paths that appear in the list you were given.",
                is_error=True)
        if not resolved:
            return _text("a finding must cite at least one changed page", is_error=True)

        ctx.calls["findings recorded"] += 1
        finding = Finding(impact=impact, summary=summary, urls=resolved,
                          kind=(str(args.get("kind")) or None), detail=args.get("detail"),
                          model=ctx.model, prompt_version=ctx.prompt_version)
        record(ctx.db, ctx.result.before.id, ctx.result.after.id, finding)
        ctx.recorded.append(finding)
        return _text(f"recorded ({len(resolved)} page(s)) — {summary[:80]}")

    async def record_findings(args: dict) -> dict:
        """Several findings in one call.

        Turns, not tokens, are what a digest session costs: every tool call re-sends the
        ~105k-token change list. Recording twenty findings one at a time cost more than
        the whole rest of the run, so batching is the primary lever and the prompt asks
        for it. Each entry is validated independently and a bad one does not discard the
        rest.
        """
        ctx.calls["batch calls"] += 1
        entries = args.get("findings") or []
        if not isinstance(entries, list) or not entries:
            return _text("findings must be a non-empty list", is_error=True)

        stored, problems = 0, []
        for i, entry in enumerate(entries):
            outcome = await record_finding(entry if isinstance(entry, dict) else {})
            if outcome.get("is_error"):
                problems.append(f"[{i}] {outcome['content'][0]['text']}")
            else:
                stored += 1
        note = f"recorded {stored} of {len(entries)} findings"
        if problems:
            return _text(note + ". Rejected:\n" + "\n".join(problems[:5]), is_error=True)
        return _text(note)

    return {"get_diff": get_diff, "read_page": read_page,
            "inbound_links": inbound_links, "record_finding": record_finding,
            "record_findings": record_findings}


SERVER_NAME = "digest"

# Fully qualified names, as the model sees them.
ALLOWED = [f"mcp__{SERVER_NAME}__{name}"
           for name in ("get_diff", "read_page", "inbound_links",
                        "record_finding", "record_findings")]


def build_server(ctx: DigestContext):
    """Wrap the handlers in an in-process MCP server. Imports the SDK lazily."""
    from claude_agent_sdk import ToolAnnotations, create_sdk_mcp_server, tool

    handlers = make_handlers(ctx)
    read_only = ToolAnnotations(readOnlyHint=True)

    wrapped = [
        tool("get_diff", "The full unified diff for one changed page. Use it before "
             "writing about a change whose excerpt is ambiguous.",
             {"url": str}, annotations=read_only)(handlers["get_diff"]),
        tool("read_page", "The current body of a changed page, for context the diff "
             "alone does not give.", {"url": str}, annotations=read_only)(handlers["read_page"]),
        tool("inbound_links", "How many corpus pages link to this one — a proxy for how "
             "much depends on it.", {"url": str}, annotations=read_only)(handlers["inbound_links"]),
        tool("record_finding",
             "Record one finding. A finding is a STORY, not a page: if ten pages changed "
             "for the same reason, record one finding citing all ten. `urls` is a list of "
             "paths exactly as they appear in the change list. `impact` is one of "
             f"{', '.join(IMPACTS)}. `kind` is a short free-text label such as "
             "'deprecation' or 'availability'.",
             {"type": "object",
              "properties": {
                  "urls": {"type": "array", "items": {"type": "string"},
                           "description": "paths from the change list this finding covers"},
                  "impact": {"type": "string", "enum": list(IMPACTS)},
                  "kind": {"type": "string"},
                  "summary": {"type": "string",
                              "description": "one sentence a reader can act on"},
                  "detail": {"type": "string"},
              },
              "required": ["urls", "impact", "summary"]})(handlers["record_finding"]),
        tool("record_findings",
             "Record SEVERAL findings in one call. Prefer this: every tool call re-sends "
             "the whole change list, so batching ten or more findings per call is much "
             "cheaper than one call each. Each entry has the same shape as record_finding.",
             {"type": "object",
              "properties": {
                  "findings": {"type": "array", "items": {"type": "object",
              "properties": {
                  "urls": {"type": "array", "items": {"type": "string"},
                           "description": "paths from the change list this finding covers"},
                  "impact": {"type": "string", "enum": list(IMPACTS)},
                  "kind": {"type": "string"},
                  "summary": {"type": "string",
                              "description": "one sentence a reader can act on"},
                  "detail": {"type": "string"},
              },
              "required": ["urls", "impact", "summary"]}},
              },
              "required": ["findings"]})(handlers["record_findings"]),
    ]
    return create_sdk_mcp_server(name=SERVER_NAME, version="1.0.0", tools=wrapped)
