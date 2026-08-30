"""MDX components → Markdown. See docs/validation-plan.md and PLAN.md §7.1.

Anthropic publishes its docs as MDX, so the `.md` twin we fetch is only Markdown-shaped:
a third of those pages carry JSX components. Left alone they are inert — no reader
renders `<CardGroup>`, and no link parser sees the 562 `href=` attributes locked inside
`<Card>`. The human review pass found it as "the Next steps links are missing"; they were
present, just unreachable.

Conversion is deliberately conservative. Only the component families the site actually
uses are touched, anything unrecognised survives verbatim, and an unclosed tag is left
exactly as found rather than swallowing the rest of the page.
"""

from __future__ import annotations

import re

# Shared with the validator and the fidelity checks: one definition of "this is code".
FENCE_BLOCK = re.compile(r"^(?P<f>`{3,}|~{3,}).*?(?:^(?P=f)`*\s*$|\Z)", re.MULTILINE | re.DOTALL)
INLINE_CODE = re.compile(r"(?<!`)(`+)(?!`).+?(?<!`)\1(?!`)", re.DOTALL)

# `<Note>` and friends become blockquotes, matching the admonition style the Databricks
# pages already use (`extract/html.py::promote_admonitions`) so the corpus reads alike.
ADMONITIONS = {
    "Note": "Note", "Tip": "Tip", "Warning": "Warning", "Info": "Info",
    "Check": "Check", "Danger": "Danger", "Caution": "Caution", "Important": "Important",
}
# Layout only: the children are the content.
WRAPPERS = ("CardGroup", "AccordionGroup", "CodeGroup", "Columns", "Tabs")
# Labelled sections: the title becomes a bold lead-in.
LABELLED = ("Tab", "Accordion", "Expandable")

KNOWN = frozenset({*ADMONITIONS, *WRAPPERS, *LABELLED, "Card", "Steps", "Step"})

_OPEN = re.compile(r"<(?P<name>[A-Z][A-Za-z0-9]*)(?P<attrs>(?:[^>\"']|\"[^\"]*\"|'[^']*')*?)(?P<void>/?)>")
_ATTR = re.compile(r"""(?P<key>[A-Za-z][\w-]*)\s*=\s*(?:"(?P<dq>[^"]*)"|'(?P<sq>[^']*)'|\{(?P<brace>[^}]*)\})""")


_BLANKS = re.compile(r"\n{3,}")
# Cards arrive separated by blank lines, which makes a *loose* list — every item wrapped
# in its own paragraph when rendered. Consecutive items are pulled together.
_LOOSE_ITEM = re.compile(r"^(- .+)\n\n+(?=- )", re.MULTILINE)


def to_markdown(text: str) -> str:
    """Convert the MDX components the Anthropic docs use, leaving code untouched."""
    return _outside_code(text, lambda chunk: _tidy(_convert(chunk)))


def _tidy(text: str) -> str:
    """Close up the extra blank lines unwrapping leaves behind.

    Runs only outside fenced code, and only collapses runs of three or more newlines —
    which the body cannot already contain, because `collapse_blank_lines` normalised it
    before conversion. So this only ever tidies whitespace this module introduced.
    """
    return _BLANKS.sub("\n\n", text)


def _tighten(text: str) -> str:
    """Pull consecutive list items together, within one component's own output.

    Scoped deliberately. Applied to the whole page it also reformatted 55 pages that
    contain no components at all: the API reference publishes its field lists as loose
    lists on purpose, and silently restyling someone else's Markdown is not this
    converter's job.
    """
    while (tightened := _LOOSE_ITEM.sub(r"\1\n", text)) != text:
        text = tightened
    return text


def strip_code(text: str) -> str:
    """Text with fenced and inline code removed — for rules that must not fire on examples."""
    return INLINE_CODE.sub("", FENCE_BLOCK.sub("", text))


def _outside_code(text: str, transform) -> str:
    """Apply `transform` to every span that is not a fenced code block."""
    out, cursor = [], 0
    for block in FENCE_BLOCK.finditer(text):
        out.append(transform(text[cursor:block.start()]))
        out.append(block.group(0))
        cursor = block.end()
    out.append(transform(text[cursor:]))
    return "".join(out)


def _attrs(raw: str) -> dict[str, str]:
    return {m.group("key"): (m.group("dq") or m.group("sq") or m.group("brace") or "")
            for m in _ATTR.finditer(raw)}


def _find_close(text: str, name: str, start: int) -> tuple[int, int] | None:
    """Span of the matching `</name>`, honouring nesting. `None` if it never closes."""
    pattern = re.compile(rf"<{name}\b(?P<attrs>(?:[^>\"']|\"[^\"]*\"|'[^']*')*?)(?P<void>/?)>|</{name}>")
    depth, pos = 1, start
    while (match := pattern.search(text, pos)) is not None:
        pos = match.end()
        if match.group(0).startswith("</"):
            depth -= 1
            if depth == 0:
                return match.start(), match.end()
        elif not match.group("void"):
            depth += 1
    return None


def _dedent(body: str) -> str:
    """Strip the indentation MDX nesting adds.

    Load-bearing: a `<Tab>`'s content is indented four or more spaces, and left in place
    that turns a fenced example into an indented code block — or breaks the fence outright.
    """
    lines = [line for line in body.splitlines() if line.strip()]
    if not lines:
        return body.strip("\n")
    pad = min(len(line) - len(line.lstrip(" ")) for line in lines)
    return "\n".join(line[pad:] if line.strip() else "" for line in body.splitlines()).strip("\n")


def _blockquote(label: str, body: str) -> str:
    quoted = "\n".join(f"> {line}".rstrip() for line in body.splitlines())
    return f"\n> **{label}:**\n>\n{quoted}\n"


def _one_line(text: str) -> str:
    return " ".join(text.split())


def _card(attrs: dict, body: str) -> str:
    """A card is a link with a one-line blurb.

    The blurb keeps its inline code: 27 of 511 card bodies contain some, and stripping it
    silently deleted words like `` `LanguageModelSession` `` from the corpus. No card body
    in the archive contains a fenced block, so flattening to one line is safe.
    """
    title = attrs.get("title", "").strip()
    href = attrs.get("href", "").strip()
    summary = _one_line(body)
    lead = f"[{title}]({href})" if title and href else f"**{title}**" if title else ""
    if not lead:
        return f"\n- {summary}\n" if summary else ""
    return f"\n- {lead}" + (f" — {summary}" if summary else "") + "\n"


_STEP = re.compile(r"<Step\b(?P<attrs>(?:[^>\"']|\"[^\"]*\"|'[^']*')*?)>", re.DOTALL)


def _steps(body: str) -> str:
    """Number `<Step>`s within their `<Steps>`; a step's own content is converted first."""
    out, cursor, number = [], 0, 0
    while (match := _STEP.search(body, cursor)) is not None:
        close = _find_close(body, "Step", match.end())
        if close is None:
            break
        number += 1
        out.append(body[cursor:match.start()])
        title = _attrs(match.group("attrs")).get("title", "").strip()
        inner = _convert(_dedent(body[match.end():close[0]]))
        heading = f"**Step {number}: {title}**" if title else f"**Step {number}**"
        out.append(f"\n{heading}\n\n{inner}\n")
        cursor = close[1]
    out.append(body[cursor:])
    return "".join(out) if number else _dedent(body)


def _render(name: str, attrs: dict, body: str) -> str:
    if name in ADMONITIONS:
        return _blockquote(ADMONITIONS[name], body)
    if name == "Card":
        return _card(attrs, body)
    if name == "Steps":
        return f"\n{_steps(body)}\n"
    if name == "Step":                      # a step outside any <Steps> keeps its title
        title = attrs.get("title", "").strip()
        return f"\n**{title}**\n\n{body}\n" if title else f"\n{body}\n"
    if name in LABELLED:
        title = attrs.get("title", "").strip()
        return f"\n**{title}**\n\n{body}\n" if title else f"\n{body}\n"
    return f"\n{_tighten(body)}\n"           # WRAPPERS: the children are the content


def _convert(text: str) -> str:
    """Convert known components, innermost first, leaving everything else alone."""
    out, pos = [], 0
    while (match := _OPEN.search(text, pos)) is not None:
        name = match.group("name")
        if name not in KNOWN:
            out.append(text[pos:match.end()])
            pos = match.end()
            continue

        if match.group("void"):
            # `<Card title="X" href="Z" />` — a component with no body. Skipping these
            # left every link in them inert, which is the exact failure this module was
            # written to fix; the release-notes index published ten of them and the
            # `mdx_converted` invariant caught it. An empty body is a body.
            out.append(text[pos:match.start()])
            out.append(_render(name, _attrs(match.group("attrs")), ""))
            pos = match.end()
            continue

        close = _find_close(text, name, match.end())
        if close is None:                   # unclosed: never eat the rest of the page
            out.append(text[pos:match.end()])
            pos = match.end()
            continue

        out.append(text[pos:match.start()])
        body = _dedent(text[match.end():close[0]])
        inner = body if name == "Steps" else _convert(body)
        out.append(_render(name, _attrs(match.group("attrs")), inner))
        pos = close[1]
    out.append(text[pos:])
    return "".join(out)
