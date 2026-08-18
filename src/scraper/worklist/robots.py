"""robots.txt fetching, parsing, and matching. See PLAN.md §6.2.

Why not `urllib.robotparser`: the stdlib parser does not support wildcards in rule paths,
and our main target needs them — docs.databricks.com publishes `Disallow: *s=*` alongside
`Allow: /aws/en/` and `Disallow: /aws/en/archive/`. Silently mis-parsing those means
either crawling pages we were asked not to, or dropping 5,700 we were allowed.

Matching follows the de-facto standard (as documented by Google):
  * `*` matches any run of characters, `$` anchors the end of the path,
  * the **longest matching rule wins**, regardless of file order,
  * Allow beats Disallow on an exact-length tie,
  * no matching rule means allowed.

One fetch per host serves both jobs — rules *and* the `Sitemap:` lines, which are how we
discover sitemaps we were not told about.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


def _rule_to_regex(path: str) -> re.Pattern[str]:
    """Compile a robots rule path into an anchored regex.

    `*` → `.*`; a trailing `$` anchors the end; everything else is literal.
    """
    anchored_end = path.endswith("$")
    if anchored_end:
        path = path[:-1]
    body = "".join(".*" if ch == "*" else re.escape(ch) for ch in path)
    return re.compile(f"^{body}$" if anchored_end else f"^{body}")


@dataclass(frozen=True)
class _Rule:
    raw: str
    allow: bool
    pattern: re.Pattern[str]

    @property
    def specificity(self) -> int:
        """Precedence is the rule's length as written, wildcards included."""
        return len(self.raw)


@dataclass
class Robots:
    """Parsed robots.txt for one host."""

    rules: list[_Rule] = field(default_factory=list)
    sitemaps: list[str] = field(default_factory=list)
    fetched: bool = False

    def allows(self, url_or_path: str) -> bool:
        """Whether the given URL (or bare path) may be fetched.

        Rules match against path *and* query string: `Disallow: *s=*` exists precisely to
        block `?s=…` search URLs, and matching the path alone would silently permit them.
        """
        parsed = urlparse(url_or_path)
        path = (parsed.path or "/") + (f"?{parsed.query}" if parsed.query else "")
        best: _Rule | None = None
        for rule in self.rules:
            if not rule.pattern.match(path):
                continue
            if (
                best is None
                or rule.specificity > best.specificity
                # Allow wins an exact-length tie.
                or (rule.specificity == best.specificity and rule.allow and not best.allow)
            ):
                best = rule
        return best.allow if best else True


def parse(text: str, *, user_agent: str = "*") -> Robots:
    """Parse robots.txt content, selecting the group that applies to `user_agent`.

    A group naming our product token beats the catch-all `*` group; if neither is
    present, no rules apply. `Sitemap:` is global and collected regardless of group.
    """
    token = user_agent.split("/")[0].strip().lower()

    groups: dict[str, list[_Rule]] = {}
    sitemaps: list[str] = []
    current: list[str] = []          # user-agents this block applies to
    starting_new_group = True

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()

        if key == "sitemap":
            if value:
                sitemaps.append(value)
            continue

        if key == "user-agent":
            if not starting_new_group:
                current = []
                starting_new_group = True
            current.append(value.lower())
            groups.setdefault(value.lower(), [])
            continue

        if key in ("allow", "disallow") and current:
            starting_new_group = False
            # An empty `Disallow:` means "allow everything" — it constrains nothing.
            if key == "disallow" and not value:
                continue
            if not value:
                continue
            rule = _Rule(raw=value, allow=(key == "allow"), pattern=_rule_to_regex(value))
            for agent in current:
                groups[agent].append(rule)

    selected = groups.get(token) or groups.get("*") or []
    return Robots(rules=selected, sitemaps=list(dict.fromkeys(sitemaps)), fetched=True)


def origin_of(url: str) -> str:
    """`https://host` for a URL — the key robots rules are scoped to."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


class RobotsCache:
    """Fetches and caches robots.txt per origin.

    A host that cannot be reached, or answers 4xx, is treated as fully allowed — the
    conventional reading, and the same one every mainstream crawler takes. A 5xx is
    treated as fully *disallowed*: the site is up but unwell, and guessing in our own
    favour is exactly the wrong call.
    """

    def __init__(self, client: httpx.Client, *, user_agent: str = "*"):
        self._client = client
        self._user_agent = user_agent
        self._cache: dict[str, Robots] = {}

    def get(self, url: str) -> Robots:
        origin = origin_of(url)
        cached = self._cache.get(origin)
        if cached is not None:
            return cached

        robots = self._fetch(origin)
        self._cache[origin] = robots
        return robots

    def _fetch(self, origin: str) -> Robots:
        target = f"{origin}/robots.txt"
        try:
            resp = self._client.get(target)
        except httpx.HTTPError as exc:
            logger.warning("robots.txt unreachable at %s (%s) — treating host as allowed", target, exc)
            return Robots()

        if resp.status_code >= 500:
            logger.warning(
                "robots.txt at %s returned %d — treating host as DISALLOWED until it recovers",
                target,
                resp.status_code,
            )
            return Robots(rules=[_Rule(raw="/", allow=False, pattern=_rule_to_regex("/"))])

        if resp.status_code >= 400:
            logger.info("no robots.txt at %s (%d) — treating host as allowed", target, resp.status_code)
            return Robots(fetched=True)

        robots = parse(resp.text, user_agent=self._user_agent)
        logger.info(
            "robots.txt %s: %d rules, %d sitemap(s)", origin, len(robots.rules), len(robots.sitemaps)
        )
        return robots

    def allows(self, url: str) -> bool:
        return self.get(url).allows(url)

    def sitemaps_for(self, url: str) -> list[str]:
        return self.get(url).sitemaps

    @property
    def origins(self) -> list[str]:
        return list(self._cache)
