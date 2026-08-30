"""SVG pictures of the graph — for slides, not for the terminal.

SVG rather than PNG, and hand-written rather than plotted, for the same reason
`rank.py` implements PageRank instead of importing it: neither `matplotlib` nor
`networkx` is in `uv.lock`, the whole job is a few hundred lines of arithmetic, and a
vector file scales into a deck without going soft. Every renderer here is stdlib.

Four views, because "draw the graph" is four different questions:

- `hubs`       what the corpus revolves around — the top pages and the links among them
- `ego`        what one page depends on, and what depends on it
- `correction` the finding: rank by link occurrences → rank by PageRank
- `categories` where the corpus is dense, and where that density is load-bearing

**A 39,872-edge hairball is not a picture, it is a texture.** Drawing every node
produces something that looks impressive and says nothing, which is the failure this
module is built to avoid: each view draws a deliberately small subgraph and says in its
own subtitle which one.

Colour follows the reference palette in the `dataviz` skill and was validated with its
checker rather than by eye — three categorical slots (blue, orange, aqua), which is the
documented all-pairs cap, in both light and dark steps. Aqua sits below 3:1 on the light
surface, so the one view that uses it direct-labels every mark.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from html import escape

# --- palette ---------------------------------------------------------------
# The `dataviz` reference instance. Two selected sets, not one flipped.


@dataclass(frozen=True)
class Theme:
    name: str
    surface: str
    ink: str
    ink_secondary: str
    ink_muted: str
    grid: str
    axis: str
    series: tuple[str, ...]      # categorical slots 1-3
    pale: str                    # sequential step 250
    strong: str                  # sequential step 450/550


LIGHT = Theme("light", "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7",
              ("#2a78d6", "#eb6834", "#1baf7a"), "#86b6ef", "#1c5cab")
DARK = Theme("dark", "#1a1a19", "#ffffff", "#c3c2b7", "#898781", "#2c2c2a", "#383835",
             ("#3987e5", "#d95926", "#199e70"), "#86b6ef", "#3987e5")
THEMES = {"light": LIGHT, "dark": DARK}

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
# system-ui at weight 400, mixed case. Only ever used to keep labels from colliding, so
# a slight overestimate is the safe direction.
CHAR_WIDTH = 0.55


def text_width(text: str, size: float) -> float:
    return len(text) * size * CHAR_WIDTH


# --- svg primitives --------------------------------------------------------


class Canvas:
    """An SVG document. Elements are appended in paint order — no z-index."""

    def __init__(self, width: int, height: int, theme: Theme, *, adaptive: bool = True):
        self.width, self.height, self.theme = width, height, theme
        self.adaptive = adaptive
        self.parts: list[str] = []

    def add(self, markup: str) -> None:
        self.parts.append("  " + markup)

    def line(self, x1, y1, x2, y2, *, stroke, width=1.0, opacity=1.0, cap="round") -> None:
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{stroke}" stroke-width="{width}" stroke-opacity="{opacity:.3f}" '
                 f'stroke-linecap="{cap}"/>')

    def circle(self, cx, cy, r, *, fill, stroke=None, width=2.0, opacity=1.0) -> None:
        ring = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
        self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.2f}" fill="{fill}"'
                 f' fill-opacity="{opacity:.3f}"{ring}/>')

    def rect(self, x, y, w, h, *, fill, rx=0, opacity=1.0) -> None:
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                 f'rx="{rx}" fill="{fill}" fill-opacity="{opacity:.3f}"/>')

    def text(self, x, y, content, *, size=12, fill=None, anchor="start", weight=400,
             mono=False) -> None:
        fill = fill or self.theme.ink
        extra = ' font-variant-numeric="tabular-nums"' if mono else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
                 f'fill="{fill}" text-anchor="{anchor}"{extra}>{escape(content)}</text>')

    def curve(self, x1, y1, x2, y2, *, stroke, width=1.0, opacity=1.0) -> None:
        """A gentle arc — straight lines between many nodes read as a mesh."""
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        cx, cy = mx - dy * 0.12, my + dx * 0.12
        self.add(f'<path d="M{x1:.1f},{y1:.1f} Q{cx:.1f},{cy:.1f} {x2:.1f},{y2:.1f}" '
                 f'fill="none" stroke="{stroke}" stroke-width="{width}" '
                 f'stroke-opacity="{opacity:.3f}"/>')

    def render(self) -> str:
        # The theme's values are the defaults; a browser in dark mode swaps them. A deck
        # that rasterises the file gets the selected theme it was generated with.
        style = ""
        if self.adaptive and self.theme is LIGHT:
            style = (
                "\n  <style>\n"
                "    @media (prefers-color-scheme: dark) {\n"
                f"      .surface {{ fill: {DARK.surface}; }}\n"
                f"      text {{ fill: {DARK.ink}; }}\n"
                f"      .ink-secondary {{ fill: {DARK.ink_secondary}; }}\n"
                f"      .ink-muted {{ fill: {DARK.ink_muted}; }}\n"
                "    }\n"
                "  </style>")
        return "\n".join([
            (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
             f'height="{self.height}" viewBox="0 0 {self.width} {self.height}" '
             f'font-family=\'{FONT}\'>{style}'),
            (f'  <rect class="surface" width="{self.width}" height="{self.height}" '
             f'fill="{self.theme.surface}"/>'),
            *self.parts,
            "</svg>",
        ])


def _heading(canvas: Canvas, title: str, subtitle: str, *, x: int = 40, y: int = 46) -> None:
    canvas.text(x, y, title, size=22, weight=600)
    for i, line in enumerate(subtitle.split("\n")):
        canvas.text(x, y + 24 + i * 17, line, size=13, fill=canvas.theme.ink_secondary)


def _legend(canvas: Canvas, entries: list[tuple[str, str]], x: float, y: float) -> None:
    """Always present for two or more series — identity is never colour alone."""
    for label, colour in entries:
        canvas.circle(x + 6, y - 4, 6, fill=colour, stroke=canvas.theme.surface, width=2)
        canvas.text(x + 18, y, label, size=12, fill=canvas.theme.ink_secondary)
        x += 18 + text_width(label, 12) + 22


def _footer(canvas: Canvas, note: str) -> None:
    canvas.text(40, canvas.height - 18, note, size=11, fill=canvas.theme.ink_muted)


def _short(url: str, width: int = 40) -> str:
    for marker in ("/aws/en/", "/docs/en/", "/cookbook/"):
        if marker in url:
            url = url.split(marker, 1)[1]
            break
    return url if len(url) <= width else url[: width - 1] + "…"


def _place_labels(candidates: list[tuple[float, float, str, float]], *,
                  bounds: tuple[float, float, float, float],
                  avoid_marks: bool = True) -> list[tuple[float, float, str]]:
    """Greedy non-overlapping label placement, most important first.

    A label on every node is chaos and goes unread, so this takes them in priority order
    and drops any whose box would collide with something already on the canvas or leave
    the frame. Dropping is the point: the alternative is an unreadable picture.

    The marks themselves are obstacles, not only the other labels. Leaving them out is
    what put `error-messages/error-classes` half-behind a circle on the first render — the
    labels missed each other perfectly and collided with the data.
    """
    x0, y0, x1, y1 = bounds
    placed: list[tuple[float, float, float, float]] = []
    if avoid_marks:
        placed += [(cx - r, cy - r, cx + r, cy + r) for cx, cy, _, r in candidates]
    out: list[tuple[float, float, str]] = []
    for cx, cy, label, radius in candidates:
        w, h = text_width(label, 11), 13
        # Try right of the mark, then left; a label is never drawn over its own node.
        for lx in (cx + radius + 6, cx - radius - 6 - w):
            box = (lx - 2, cy - h + 4, lx + w + 2, cy + 7)
            if box[0] < x0 or box[2] > x1 or box[1] < y0 or box[3] > y1:
                continue
            if any(not (box[2] < p[0] or box[0] > p[2] or box[3] < p[1] or box[1] > p[3])
                   for p in placed):
                continue
            placed.append(box)
            out.append((lx, cy + 4, label))
            break
    return out


# --- layout ----------------------------------------------------------------


def force_layout(nodes: list[str], edges: list[tuple[str, str]], *, width: float,
                 height: float, iterations: int = 400, seed: int = 7) -> dict[str, list[float]]:
    """Fruchterman–Reingold, seeded so the same build always draws the same picture.

    Deterministic on purpose: a layout that moves between runs makes two exports of the
    same data look like different data, and the change feed already taught this project
    what an unstable artifact costs.
    """
    rng = random.Random(seed)
    area = width * height
    k = math.sqrt(area / max(len(nodes), 1)) * 0.85
    # Start on a ring rather than at random: a random start on a graph this sparse
    # settles into a different local minimum every time the node set changes slightly.
    pos = {}
    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / max(len(nodes), 1)
        jitter = rng.uniform(0.92, 1.08)
        pos[node] = [width / 2 + math.cos(angle) * width * 0.32 * jitter,
                     height / 2 + math.sin(angle) * height * 0.32 * jitter]

    index = {n: i for i, n in enumerate(nodes)}
    pairs = [(index[a], index[b]) for a, b in edges if a in index and b in index]
    temperature = width * 0.1

    for _ in range(iterations):
        disp = [[0.0, 0.0] for _ in nodes]
        for i in range(len(nodes)):
            xi, yi = pos[nodes[i]]
            for j in range(i + 1, len(nodes)):
                xj, yj = pos[nodes[j]]
                dx, dy = xi - xj, yi - yj
                dist = math.hypot(dx, dy) or 0.01
                force = k * k / dist
                fx, fy = dx / dist * force, dy / dist * force
                disp[i][0] += fx
                disp[i][1] += fy
                disp[j][0] -= fx
                disp[j][1] -= fy
        for a, b in pairs:
            dx = pos[nodes[a]][0] - pos[nodes[b]][0]
            dy = pos[nodes[a]][1] - pos[nodes[b]][1]
            dist = math.hypot(dx, dy) or 0.01
            force = dist * dist / k
            fx, fy = dx / dist * force, dy / dist * force
            disp[a][0] -= fx
            disp[a][1] -= fy
            disp[b][0] += fx
            disp[b][1] += fy
        for i, node in enumerate(nodes):
            # Gravity, or disconnected nodes drift off the canvas and the interesting
            # part of the picture shrinks to fit them.
            gx = (width / 2 - pos[node][0]) * 0.012
            gy = (height / 2 - pos[node][1]) * 0.012
            dx, dy = disp[i][0] + gx, disp[i][1] + gy
            dist = math.hypot(dx, dy) or 0.01
            step = min(dist, temperature)
            pos[node][0] += dx / dist * step
            pos[node][1] += dy / dist * step
        temperature = max(temperature * 0.97, 0.6)
    return pos


def _fit(pos: dict[str, list[float]], radii: dict[str, float],
         box: tuple[float, float, float, float]) -> None:
    """Scale a layout into the frame, leaving room for the largest node."""
    x0, y0, x1, y1 = box
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    if not xs:
        return
    pad = max(radii.values(), default=6) + 4
    span_x = (max(xs) - min(xs)) or 1
    span_y = (max(ys) - min(ys)) or 1
    scale = min((x1 - x0 - 2 * pad) / span_x, (y1 - y0 - 2 * pad) / span_y)
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    for point in pos.values():
        point[0] = mx + (point[0] - cx) * scale
        point[1] = my + (point[1] - cy) * scale


def _radius(value: float, largest: float, *, smallest: float = 3.0,
            biggest: float = 30.0) -> float:
    """Area proportional to value — radius is the square root, or big nodes lie."""
    if largest <= 0:
        return smallest
    return smallest + (biggest - smallest) * math.sqrt(max(value, 0) / largest)


# --- views -----------------------------------------------------------------


@dataclass
class ViewData:
    """What a renderer needs, so the drawing code never touches SQL."""

    build_name: str = ""
    corpus: str = ""
    rows: list[dict] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


def hub_map(data: ViewData, theme: Theme, *, width: int = 1400, height: int = 900,
            adaptive: bool = True) -> str:
    """The corpus's centre of gravity: top pages by PageRank, and the links among them.

    Node area is PageRank; hue is the vendor. Size and colour carry different variables
    on purpose — a ramp that repeats what size already says spends the only free channel
    on nothing.
    """
    canvas = Canvas(width, height, theme, adaptive=adaptive)
    rows = data.rows
    # **Drop nodes with no edge inside this subgraph.** A single disconnected page floats
    # to the frame's edge under any force layout, and `_fit` then scales the whole picture
    # down to include it — the first render crushed the actual graph into one corner to
    # make room for `sql/.../functions/cos`, which links to nothing else in the top 55.
    present = {r["url"] for r in rows}
    edges = [(a, b) for a, b in data.edges if a in present and b in present and a != b]
    linked = {u for edge in edges for u in edge}
    isolated = len(rows) - len(linked)
    rows = [r for r in rows if r["url"] in linked]
    data = ViewData(data.build_name, data.corpus, rows, edges, data.extra)
    if not rows:
        rows = data.rows = list(present and [])
    top_rank = max((r["pagerank"] or 0) for r in rows) if rows else 0
    radii = {r["url"]: _radius(r["pagerank"] or 0, top_rank) for r in rows}
    urls = [r["url"] for r in rows]
    box = (40.0, 150.0, width - 40.0, height - 60.0)

    pos = force_layout(urls, data.edges, width=box[2] - box[0], height=box[3] - box[1])
    _fit(pos, radii, box)

    companies = sorted({r["company"] or "?" for r in rows})
    colour = {c: theme.series[i % 3] for i, c in enumerate(companies)}

    for src, dst in data.edges:
        if src in pos and dst in pos:
            canvas.curve(*pos[src], *pos[dst], stroke=theme.axis, width=1, opacity=0.5)
    for row in sorted(rows, key=lambda r: r["pagerank"] or 0):
        url = row["url"]
        canvas.circle(pos[url][0], pos[url][1], radii[url],
                      fill=colour[row["company"] or "?"],
                      stroke=theme.surface, width=2, opacity=0.92)

    ranked = sorted(rows, key=lambda r: -(r["pagerank"] or 0))
    labels = _place_labels(
        [(pos[r["url"]][0], pos[r["url"]][1], _short(r["url"], 34), radii[r["url"]])
         for r in ranked],
        bounds=box)
    for lx, ly, label in labels:
        canvas.text(lx, ly, label, size=11, fill=theme.ink_secondary)

    vendors = " and ".join(companies)
    _heading(canvas, "What the corpus revolves around",
             f"The highest-ranked {vendors} pages that link to each other — {len(rows)} "
             f"pages, {len(data.edges)} links. Node area is PageRank."
             f"\n{data.build_name} · corpus {data.corpus}")
    # One series needs no legend box: the subtitle names it.
    if len(companies) > 1:
        _legend(canvas, [(c, colour[c]) for c in companies], width - 360, 46)
    note = f"{len(labels)} of {len(rows)} nodes labelled — the rest would collide."
    if isolated:
        note += (f" {isolated} more rank in the top {len(rows) + isolated} but link to "
                 f"none of them, so they are not drawn.")
    _footer(canvas, note)
    return canvas.render()


def ego_map(data: ViewData, theme: Theme, *, width: int = 1400, height: int = 900,
            adaptive: bool = True) -> str:
    """One page, what links to it, and what it links to.

    A fixed two-column layout rather than a force layout: the question is directional,
    and a physics simulation hides direction behind whatever shape it settles into.
    """
    canvas = Canvas(width, height, theme, adaptive=adaptive)
    centre = data.extra["centre"]
    inbound, outbound = data.extra["inbound"], data.extra["outbound"]
    in_colour, out_colour = theme.series[1], theme.series[2]

    cx, cy = width / 2, height / 2 + 40
    # Sized by how *heavily* each neighbour links, not by its own rank: on one page's
    # neighbourhood the neighbours' PageRanks are all similar, so that channel showed
    # nothing. Occurrences vary, and are the thing the reader came to compare.
    top = max([r["occurrences"] for r in inbound + outbound] or [0])

    def column(rows, x, colour, align):
        drawn = []
        if not rows:
            return drawn
        span = min(height - 300, 46 * max(len(rows) - 1, 1))
        y0 = cy - span / 2
        for i, row in enumerate(rows):
            y = y0 + (span / max(len(rows) - 1, 1)) * i
            r = _radius(row["occurrences"], top, smallest=5, biggest=17)
            canvas.curve(x, y, cx, cy, stroke=colour, width=1.4, opacity=0.45)
            drawn.append((x, y, r, row, colour, align))
        return drawn

    marks = column(inbound, 300, in_colour, "end") + column(outbound, width - 300,
                                                            out_colour, "start")
    for x, y, r, row, colour, align in marks:
        canvas.circle(x, y, r, fill=colour, stroke=theme.surface, width=2)
        offset = -(r + 8) if align == "end" else (r + 8)
        # Every mark is direct-labelled: aqua is below 3:1 on the light surface, and the
        # palette's relief rule makes visible labels the mitigation, not an option.
        canvas.text(x + offset, y + 4, _short(row["url"], 44), size=11,
                    fill=theme.ink_secondary, anchor=align)

    canvas.circle(cx, cy, 34, fill=theme.series[0], stroke=theme.surface, width=3)
    canvas.text(cx, cy + 66, _short(centre["url"], 52), size=13, weight=600, anchor="middle")

    _heading(canvas, centre["title"] or _short(centre["url"]),
             f"{centre['in_pages']:,} pages link here · links out to "
             f"{centre['out_pages']:,} · PageRank #{data.extra.get('rank', '?')}\n"
             f"{data.build_name} · corpus {data.corpus}")
    _legend(canvas, [("links to it", in_colour), ("it links to", out_colour)],
            width - 360, 46)
    _footer(canvas, f"The {len(inbound)} highest-ranked inbound and {len(outbound)} "
                    f"outbound neighbours. Node area is how many times the link is made.")
    return canvas.render()


def rank_correction(data: ViewData, theme: Theme, *, width: int = 1400, height: int = 900,
                    adaptive: bool = True) -> str:
    """Rank by link occurrences → rank by PageRank, one row per page.

    A dumbbell, because the job is before-and-after for each item: one hue, two shades,
    the pair joined so the move is the mark rather than something the reader computes.

    The rank axis is logarithmic — the moves span #1 to #917 and a linear axis would
    flatten every one of them against the left edge. The canvas grows with the row count
    instead of squeezing rows together: 60 rows in a fixed frame collided, and a chart
    that cannot be read is not a smaller chart, it is a wrong one.
    """
    rows = data.rows
    height = max(height, 320 + 26 * len(rows))
    canvas = Canvas(width, height, theme, adaptive=adaptive)
    left, right = 430.0, width - 190.0
    top, bottom = 200.0, height - 90.0
    worst = max(max(r["rank_refs"], r["rank_pagerank"]) for r in rows)
    upper = 10 ** math.ceil(math.log10(max(worst, 10)))

    def x_of(rank: int) -> float:
        return left + (right - left) * math.log10(max(rank, 1)) / math.log10(upper)

    tick = 1
    while tick <= upper:
        x = x_of(tick)
        canvas.line(x, top - 14, x, bottom, stroke=theme.grid, width=1)
        # Axis chrome is muted by the palette, but these are read off a projector at the
        # back of a room; secondary ink is the deliberate step up.
        canvas.text(x, top - 22, f"#{tick:,}", size=11, fill=theme.ink_secondary,
                    anchor="middle", mono=True)
        tick *= 10
    canvas.text(left, top - 44, "position in the corpus, log scale", size=11,
                fill=theme.ink_muted)

    step = (bottom - top) / max(len(rows), 1)
    for i, row in enumerate(rows):
        y = top + step * (i + 0.5)
        x_before, x_after = x_of(row["rank_refs"]), x_of(row["rank_pagerank"])
        moved = row["rank_pagerank"] - row["rank_refs"]
        canvas.line(x_before, y, x_after, y, stroke=theme.pale, width=2)
        canvas.circle(x_before, y, 5, fill=theme.pale, stroke=theme.surface, width=2)
        canvas.circle(x_after, y, 5.5, fill=theme.strong, stroke=theme.surface, width=2)
        canvas.text(left - 18, y + 4, _short(row["url"], 44), size=12,
                    fill=theme.ink_secondary, anchor="end")
        # Direct-label only the movers worth naming; a number on every row is chaos.
        # "+211" is ambiguous about which way is worse, so the arrow does the talking.
        if abs(moved) >= 25:
            arrow = "↓" if moved > 0 else "↑"
            canvas.text(max(x_before, x_after) + 12, y + 4,
                        f"{arrow} {abs(moved):,} places", size=11, fill=theme.ink_muted,
                        mono=True)

    _heading(canvas, "Counting links, not link occurrences",
             "Each page ranked by raw link occurrences, and by PageRank over the "
             "deduplicated graph.\nA long bar is a page whose apparent importance was a "
             f"repeated template.\n{data.build_name} · corpus {data.corpus}")
    _legend(canvas, [("by occurrences", theme.pale), ("by PageRank", theme.strong)],
            width - 400, 46)
    _footer(canvas, f"The {len(rows)} most-linked pages. Only moves of 25+ places are "
                    f"labelled; ↓ means the occurrence count flattered it.")
    return canvas.render()


def category_scatter(data: ViewData, theme: Theme, *, width: int = 1400, height: int = 900,
                     adaptive: bool = True) -> str:
    """Pages against share of PageRank: is a big area actually load-bearing?

    **Both axes are logarithmic, and that is what makes the reference line honest.**
    Share of rank spans four orders of magnitude, so a linear y flattened all but three
    categories onto the axis; worse, "proportional share" is a straight line only in
    log-log space, and the first version of this chart drew it straight on a log-linear
    plot — a reference line that was simply wrong. On log-log it is the true diagonal:
    above it, a category the corpus points into more than its size warrants.
    """
    canvas = Canvas(width, height, theme, adaptive=adaptive)
    rows = [r for r in data.rows if r["pages"] > 0 and r["share_of_rank"] > 0]
    limit = data.extra.get("limit")
    shown = sorted(rows, key=lambda r: -r["pages"])[:limit] if limit else rows
    left, right = 130.0, width - 60.0
    top, bottom = 210.0, height - 100.0
    total_pages = sum(r["pages"] for r in data.rows) or 1

    # A log axis needs a decade to span. One category, or a set that all hold the same
    # share, collapses `hi` onto `lo` and divides by zero — which is what happens on any
    # small corpus slice, so the floor is not hypothetical.
    page_hi = max(10 ** math.ceil(math.log10(max(r["pages"] for r in shown))), 10)
    share_lo = 10 ** math.floor(math.log10(min(r["share_of_rank"] for r in shown)))
    share_hi = 10 ** math.ceil(math.log10(max(r["share_of_rank"] for r in shown)))
    share_hi = max(share_hi, share_lo * 10)

    def x_of(pages: float) -> float:
        return left + (right - left) * math.log10(max(pages, 1)) / math.log10(page_hi)

    def y_of(share: float) -> float:
        span = math.log10(share_hi) - math.log10(share_lo)
        return bottom - (bottom - top) * (math.log10(max(share, share_lo))
                                          - math.log10(share_lo)) / span

    tick = 1
    while tick <= page_hi:
        x = x_of(tick)
        canvas.line(x, top, x, bottom, stroke=theme.grid, width=1)
        canvas.text(x, bottom + 24, f"{tick:,}", size=11, fill=theme.ink_secondary,
                    anchor="middle", mono=True)
        tick *= 10
    tick = share_lo
    while tick <= share_hi * 1.001:
        y = y_of(tick)
        canvas.line(left, y, right, y, stroke=theme.grid, width=1)
        label = f"{100 * tick:g}%" if tick >= 0.0001 else f"{100 * tick:.2g}%"
        canvas.text(left - 12, y + 4, label, size=11, fill=theme.ink_secondary,
                    anchor="end", mono=True)
        tick *= 10

    canvas.line(x_of(1), y_of(1 / total_pages), x_of(page_hi), y_of(page_hi / total_pages),
                stroke=theme.axis, width=1.5, opacity=0.9)
    canvas.text(x_of(page_hi) - 6, y_of(page_hi / total_pages) - 12,
                "its proportional share", size=11, fill=theme.ink_muted, anchor="end")

    companies = sorted({r["company"] for r in shown})
    colour = {c: theme.series[i % 3] for i, c in enumerate(companies)}
    biggest = max((r["median_chars"] for r in shown), default=1)
    marks = []
    for row in sorted(shown, key=lambda r: -r["pages"]):
        x, y = x_of(row["pages"]), y_of(row["share_of_rank"])
        r = _radius(row["median_chars"], biggest, smallest=5, biggest=20)
        canvas.circle(x, y, r, fill=colour[row["company"]], stroke=theme.surface,
                      width=2, opacity=0.85)
        marks.append((x, y, row["key"], r))
    labels = _place_labels(marks, bounds=(left, top, right, bottom))
    for lx, ly, label in labels:
        canvas.text(lx, ly, label, size=11, fill=theme.ink_secondary)

    canvas.text((left + right) / 2, height - 52, "pages in the category, log scale",
                size=12, fill=theme.ink_secondary, anchor="middle")
    _heading(canvas, "Dense, or load-bearing?",
             "Every category: how many pages it holds against how much of the corpus's "
             "PageRank sits in it — both axes log.\nBubble area is the category's median "
             f"page length. Above the diagonal, the corpus leans on it.\n{data.build_name}"
             f" · corpus {data.corpus}")
    _legend(canvas, [(c, colour[c]) for c in companies], width - 360, 46)
    note = f"{len(labels)} of {len(shown)} categories labelled."
    if limit and len(rows) > len(shown):
        note += f" Showing the {len(shown)} largest of {len(rows)}."
    _footer(canvas, note)
    return canvas.render()


# How much of each view is worth drawing. These are not one number because the views fail
# differently as they grow: the hub map turns into a hairball, the dumbbell's rows collide,
# and the scatter overplots. Measured by rendering them and looking.
DEFAULT_TOP = {"hubs": 70, "ego": 14, "correction": 28, "categories": 45}

VIEWS = {
    "hubs": hub_map,
    "ego": ego_map,
    "correction": rank_correction,
    "categories": category_scatter,
}


# --- data assembly ---------------------------------------------------------
# Kept below the renderers and separate from them: every function above takes a
# `ViewData` and knows nothing about SQLite, so a view can be drawn from a fixture in a
# test without a database anywhere near it.


def collect(db, build, kind: str, *, top: int = 60, url: str | None = None) -> ViewData:
    """Pull one view's worth of rows out of `state/graph.db`."""
    data = ViewData(build_name=build.name, corpus=build.corpus_stamp)

    if kind == "hubs":
        data.rows = db.top(build.id, by="pagerank", limit=top)
        urls = [r["url"] for r in data.rows]
        marks = ",".join("?" * len(urls))
        data.edges = [(r["src"], r["dst"]) for r in db.conn.execute(
            f"SELECT src, dst FROM edges WHERE build_id = ? AND src IN ({marks}) "
            f"AND dst IN ({marks})", [build.id, *urls, *urls])]

    elif kind == "ego":
        if not url:
            raise ValueError("the ego view needs --url")
        centre = db.node(build.id, url)
        if centre is None:
            raise ValueError(f"not in {build.name}: {url}")
        data.extra = {
            "centre": centre,
            "inbound": db.inbound(build.id, url, limit=top),
            "outbound": db.outbound(build.id, url, limit=top),
            "rank": db.rank_of(build.id, url),
        }

    elif kind == "correction":
        rows = db.top(build.id, by="in_refs", limit=top)
        data.rows = [
            {**row, "rank_refs": i, "rank_pagerank": db.rank_of(build.id, row["url"])}
            for i, row in enumerate(rows, 1)
        ]

    elif kind == "categories":
        import json as _json
        data.extra["limit"] = top

        from . import stats
        nodes = [dict(r) for r in db.conn.execute(
            "SELECT * FROM nodes WHERE build_id = ?", (build.id,))]
        for node in nodes:
            node["breadcrumbs"] = _json.loads(node["breadcrumbs"] or "[]")
            node["code_languages"] = _json.loads(node["code_languages"] or "[]")
        data.rows = [vars(g) for g in stats.by_category(nodes)]

    else:
        raise ValueError(f"unknown view {kind!r}; expected one of {sorted(VIEWS)}")
    return data


def render(db, build, kind: str, *, theme: str = "light", top: int = 60,
           url: str | None = None, width: int = 1400, height: int = 900,
           adaptive: bool = True) -> str:
    """Assemble and draw one view. Returns SVG text."""
    data = collect(db, build, kind, top=top, url=url)
    return VIEWS[kind](data, THEMES[theme], width=width, height=height, adaptive=adaptive)
