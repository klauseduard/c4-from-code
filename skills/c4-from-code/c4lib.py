"""c4lib - C4 diagram helper. Standard library only; emits SVG.

Blueprint style: paper with a faint grid, an engineering-style title block with
breadcrumbs, an automatic legend, carded boxes with a coloured header band and a
soft shadow, orthogonal (elbow) connectors, and drill-down links so a C4 set can
be navigated: click a system to open its containers, a container to open its
components. No external deps, no Mermaid/PlantUML, no rendering services.

Shapes return a Box, so connectors are expressed as `connect(a, b, "label")`
and routed automatically between box edges.

Run this file directly to emit a self-test diagram to stdout.
"""
from __future__ import annotations

from html import escape as _esc

SANS = "-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
MONO = "'SFMono-Regular',Menlo,Consolas,'Liberation Mono',monospace"

PAPER, GRID = "#f7f9fc", "#e4e9f1"
INK, INK2, INK3, LINE = "#1f2937", "#4b5563", "#6b7280", "#374151"

# kind -> (band, body, border, legend label)
KINDS = {
    "container": ("#2f5fd1", "#eef3fd", "#2f5fd1", "Container"),
    "component": ("#3b8ac4", "#ecf5fb", "#3b8ac4", "Component"),
    "datastore": ("#1d8a6a", "#e9f6f1", "#1d8a6a", "Data store"),
    "external": ("#6b7280", "#f1f3f5", "#6b7280", "External system"),
    "person": ("#6d4fc2", "#f1edfb", "#6d4fc2", "Person"),
    "poc": ("#2f5fd1", "#ffffff", "#2f5fd1", "Proof of concept"),
    "planned": ("#9aa3b2", "#ffffff", "#9aa3b2", "Planned"),
}
DASHED = {"poc", "planned"}


def esc(s):
    return _esc(str(s), quote=True)


def _wrap(text, max_chars):
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= max_chars or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def _rounded_path(pts, r=9):
    pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
    if len(pts) < 3:
        return " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
    d = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for i in range(1, len(pts) - 1):
        p0, p1, p2 = pts[i - 1], pts[i], pts[i + 1]
        v1 = (p1[0] - p0[0], p1[1] - p0[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1 = max(1e-6, (v1[0] ** 2 + v1[1] ** 2) ** 0.5)
        l2 = max(1e-6, (v2[0] ** 2 + v2[1] ** 2) ** 0.5)
        rr = min(r, l1 / 2, l2 / 2)
        a = (p1[0] - v1[0] / l1 * rr, p1[1] - v1[1] / l1 * rr)
        b = (p1[0] + v2[0] / l2 * rr, p1[1] + v2[1] / l2 * rr)
        d.append(f"L{a[0]:.1f},{a[1]:.1f} Q{p1[0]:.1f},{p1[1]:.1f} {b[0]:.1f},{b[1]:.1f}")
    d.append(f"L{pts[-1][0]:.1f},{pts[-1][1]:.1f}")
    return " ".join(d)


class Box:
    """Geometry of a placed shape; `port(side, t)` is a point on an edge."""

    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2

    def port(self, side, t=0.5):
        if side == "left":
            return (self.x, self.y + self.h * t)
        if side == "right":
            return (self.x + self.w, self.y + self.h * t)
        if side == "top":
            return (self.x + self.w * t, self.y)
        return (self.x + self.w * t, self.y + self.h)


class Diagram:
    def __init__(self, width, height, title, subtitle="", crumbs=None):
        self.width, self.height = width, height
        self.title, self.subtitle = title, subtitle
        self.crumbs = crumbs or []   # [(label, href-or-None)], last = current diagram
        self.back, self.parts = [], []
        self.used = []

    # ---------- text ----------
    def _text(self, x, y, s, size=12, color=INK, weight="normal", anchor="middle",
              family=SANS, style="normal"):
        return (f"<text x='{x:.1f}' y='{y:.1f}' font-size='{size}' fill='{color}' "
                f"font-weight='{weight}' font-style='{style}' text-anchor='{anchor}' "
                f"font-family=\"{family}\">{esc(s)}</text>")

    def _block(self, cx, cy, lines):
        # lines: (text, size, color, weight, family)
        lh = 1.35
        total = sum(sz * lh for (_t, sz, _c, _w, _f) in lines)
        y = cy - total / 2
        out = []
        for (t, sz, color, weight, fam) in lines:
            y += sz
            out.append(self._text(cx, y, t, size=sz, color=color, weight=weight, family=fam))
            y += sz * (lh - 1)
        return "".join(out)

    def _label(self, x, y, text):
        if not text:
            return ""
        w = len(str(text)) * 6.3 + 12
        return (f"<rect x='{x - w / 2:.1f}' y='{y - 9.5:.1f}' width='{w:.1f}' height='19' rx='4' "
                f"fill='#ffffff' stroke='#d1d5db'/>"
                + self._text(x, y + 3.5, text, size=11, color=INK2))

    def _use(self, kind):
        if kind not in self.used:
            self.used.append(kind)

    # ---------- shapes ----------
    def box(self, x, y, w, h, name, type_line="", desc=None, kind="container",
            href=None, hint=None):
        desc = desc or []
        band, body, border, _ = KINDS[kind]
        self._use(kind)
        dash = " stroke-dasharray='7 5'" if kind in DASHED else ""
        name_lines = _wrap(name, max(8, int(w / 7.4)))
        band_h = 26 + 14 * (len(name_lines) - 1)
        g = [f"<rect class='card' x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='{body}' "
             f"stroke='{border}' stroke-width='1.4'{dash} filter='url(#shadow)'/>",
             f"<path d='M{x},{y + 8} Q{x},{y} {x + 8},{y} L{x + w - 8},{y} Q{x + w},{y} "
             f"{x + w},{y + 8} L{x + w},{y + band_h} L{x},{y + band_h} Z' fill='{band}'/>"]
        ny = y + 17.5
        for ln in name_lines:
            g.append(self._text(x + w / 2, ny, ln, size=13, color="#ffffff", weight="bold"))
            ny += 14
        lines = []
        if type_line:
            lines += [(s, 11, INK2, "normal", MONO) for s in _wrap(type_line, max(10, int(w / 6.6)))]
        for d in desc:
            lines += [(s, 11, INK, "normal", SANS) for s in _wrap(d, max(10, int(w / 6.4)))]
        if lines:
            g.append(self._block(x + w / 2, y + band_h + (h - band_h) / 2, lines))
        if href:
            zx, zy = x + w - 14, y + band_h / 2
            g.append(f"<g class='zoom'><circle cx='{zx - 1}' cy='{zy - 1}' r='4.2' fill='none' "
                     f"stroke='#ffffff' stroke-width='1.6'/><line x1='{zx + 2}' y1='{zy + 2}' "
                     f"x2='{zx + 5.5}' y2='{zy + 5.5}' stroke='#ffffff' stroke-width='1.8' "
                     f"stroke-linecap='round'/></g>")
            tip = hint or f"Open {href}"
            self.parts.append(f"<a class='drill' href='{esc(href)}'><title>{esc(tip)}</title>"
                              + "".join(g) + "</a>")
        else:
            self.parts.append("".join(g))
        return Box(x, y, w, h)

    def datastore(self, x, y, w, h, name, type_line="", desc=None, kind="datastore"):
        desc = desc or []
        band, body, border, _ = KINDS[kind]
        self._use(kind)
        ry = 11
        self.parts.append(
            f"<path d='M{x},{y + ry} A{w / 2},{ry} 0 0 1 {x + w},{y + ry} L{x + w},{y + h - ry} "
            f"A{w / 2},{ry} 0 0 1 {x},{y + h - ry} Z' fill='{body}' stroke='{border}' "
            f"stroke-width='1.4' filter='url(#shadow)'/>"
            f"<ellipse cx='{x + w / 2}' cy='{y + ry}' rx='{w / 2}' ry='{ry}' fill='{band}' "
            f"stroke='{border}' stroke-width='1.4'/>"
        )
        lines = [(s, 13, INK, "bold", SANS) for s in _wrap(name, max(8, int(w / 7.4)))]
        if type_line:
            lines += [(s, 11, INK2, "normal", MONO) for s in _wrap(type_line, max(10, int(w / 6.6)))]
        lines += [(s, 11, INK, "normal", SANS) for d in desc for s in _wrap(d, max(10, int(w / 6.4)))]
        self.parts.append(self._block(x + w / 2, y + 2 * ry + (h - 2 * ry) / 2, lines))
        return Box(x, y, w, h)

    def person(self, x, y, name, desc="", w=120):
        band, _body, border, _ = KINDS["person"]
        self._use("person")
        cx, r = x + w / 2, 13
        self.parts.append(
            f"<circle cx='{cx}' cy='{y + r}' r='{r}' fill='{band}' stroke='{border}' stroke-width='1.2'/>"
            f"<path d='M{cx - 24},{y + 2 * r + 24} Q{cx - 24},{y + 2 * r + 2} {cx},{y + 2 * r + 2} "
            f"Q{cx + 24},{y + 2 * r + 2} {cx + 24},{y + 2 * r + 24} Z' fill='{band}' "
            f"stroke='{border}' stroke-width='1.2'/>"
        )
        yy = y + 2 * r + 24 + 15
        self.parts.append(self._text(cx, yy, name, size=12, color=INK, weight="bold"))
        for d in _wrap(desc, 24) if desc else []:
            yy += 14
            self.parts.append(self._text(cx, yy, d, size=11, color=INK3))
        return Box(x, y, w, yy - y + 6)

    def boundary(self, x, y, w, h, label):
        lw = len(label) * 6.6 + 16
        self.back.append(
            f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='12' fill='#ffffff' "
            f"fill-opacity='0.35' stroke='#94a3b8' stroke-width='1.3' stroke-dasharray='8 5'/>"
            f"<rect x='{x + 12}' y='{y - 11}' width='{lw:.1f}' height='22' rx='5' fill='#e2e8f0' "
            f"stroke='#94a3b8' stroke-width='1'/>"
            + self._text(x + 12 + lw / 2, y + 4, label, size=11.5, color=INK2, weight="bold")
        )

    def note(self, x, y, w, lines, title="Notes"):
        h = 30 + len(lines) * 16
        self.parts.append(
            f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='6' fill='#fffbeb' "
            f"stroke='#e8d48b' stroke-width='1'/>"
            f"<rect x='{x}' y='{y}' width='4' height='{h}' rx='2' fill='#d9a60b'/>"
            + self._text(x + 14, y + 19, title, size=11, color="#6b5900", weight="bold", anchor="start")
        )
        yy = y + 36
        for ln in lines:
            self.parts.append(self._text(x + 14, yy, ln, size=11, color="#6b5900", anchor="start"))
            yy += 16
        return Box(x, y, w, h)

    # ---------- connectors ----------
    def connect(self, a, b, label="", a_side=None, b_side=None, a_t=0.5, b_t=0.5,
                mid=None, dashed=False, label_at="auto"):
        """Orthogonal connector from Box a to Box b (arrow at b).

        Sides are chosen automatically from the boxes' relative position; override
        with a_side/b_side ('left'|'right'|'top'|'bottom'). a_t/b_t pick the exit and
        entry point along the edge (0..1); `mid` pins the trunk coordinate so parallel
        connectors can be staggered. label_at: 'auto' (longest segment, so the label
        never sits on a box edge) | 'start' | 'mid' | 'end'.
        """
        if a_side is None or b_side is None:
            dx, dy = b.cx - a.cx, b.cy - a.cy
            hs = (b.x - (a.x + a.w)) if dx > 0 else (a.x - (b.x + b.w))
            vs = (b.y - (a.y + a.h)) if dy > 0 else (a.y - (b.y + b.h))
            if hs >= vs:
                a_side = a_side or ("right" if dx > 0 else "left")
                b_side = b_side or ("left" if dx > 0 else "right")
            else:
                a_side = a_side or ("bottom" if dy > 0 else "top")
                b_side = b_side or ("top" if dy > 0 else "bottom")
        p1, p2 = a.port(a_side, a_t), b.port(b_side, b_t)
        horiz = {"left", "right"}
        if a_side in horiz and b_side in horiz:
            mx = mid if mid is not None else (p1[0] + p2[0]) / 2
            pts = [p1, (mx, p1[1]), (mx, p2[1]), p2]
        elif a_side not in horiz and b_side not in horiz:
            my = mid if mid is not None else (p1[1] + p2[1]) / 2
            pts = [p1, (p1[0], my), (p2[0], my), p2]
        elif a_side in horiz:
            pts = [p1, (p2[0], p1[1]), p2]
        else:
            pts = [p1, (p1[0], p2[1]), p2]
        pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        dash = " stroke-dasharray='6 4'" if dashed else ""
        self.parts.append(
            f"<path d='{_rounded_path(pts)}' fill='none' stroke='{LINE}' stroke-width='1.5' "
            f"stroke-linejoin='round' marker-end='url(#arrow)'{dash}/>"
        )
        if label:
            segs = list(zip(pts, pts[1:]))
            if label_at == "end":
                seg = segs[-1]
            elif label_at == "start":
                seg = segs[0]
            elif label_at == "mid":
                seg = segs[len(segs) // 2]
            else:
                seg = max(segs, key=lambda s: abs(s[1][0] - s[0][0]) + abs(s[1][1] - s[0][1]))
            self.parts.append(self._label((seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2, label))

    def line(self, x1, y1, x2, y2, label="", dashed=False):
        dash = " stroke-dasharray='6 4'" if dashed else ""
        self.parts.append(
            f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{LINE}' stroke-width='1.5' "
            f"marker-end='url(#arrow)'{dash}/>"
        )
        if label:
            self.parts.append(self._label((x1 + x2) / 2, (y1 + y2) / 2, label))

    # ---------- document ----------
    def _header(self):
        out = [self._text(24, 36, self.title, size=20, color=INK, weight="bold", anchor="start")]
        if self.subtitle:
            out.append(self._text(24, 56, self.subtitle, size=12, color=INK3, anchor="start"))
        if self.crumbs:
            x = 24
            for i, (label, href) in enumerate(self.crumbs):
                if i:
                    out.append(self._text(x, 76, "›", size=11, color=INK3, anchor="start"))
                    x += 12
                last = i == len(self.crumbs) - 1
                t = self._text(x, 76, label, size=11, color=INK if last else "#2f5fd1",
                               weight="bold" if last else "normal", anchor="start")
                out.append(f"<a href='{esc(href)}'>{t}</a>" if href and not last else t)
                x += len(label) * 6.4 + 10
        out.append(f"<line x1='24' y1='88' x2='{self.width - 24}' y2='88' stroke='#cbd5e1' stroke-width='1'/>")
        return "".join(out)

    def _legend(self):
        kinds = [k for k in KINDS if k in self.used]
        if not kinds:
            return ""
        items = [(k, KINDS[k][3]) for k in kinds]
        total = sum(len(lbl) * 6.4 + 34 for _k, lbl in items)
        x = self.width - 24 - total
        out = []
        for k, lbl in items:
            band, body, border, _ = KINDS[k]
            dash = " stroke-dasharray='3 2'" if k in DASHED else ""
            out.append(f"<rect x='{x:.1f}' y='24' width='14' height='14' rx='3' fill='{body}' "
                       f"stroke='{border}' stroke-width='1.2'{dash}/>"
                       f"<rect x='{x:.1f}' y='24' width='14' height='5' rx='2' fill='{band}'/>")
            out.append(self._text(x + 19, 35.5, lbl, size=11, color=INK2, anchor="start"))
            x += len(lbl) * 6.4 + 34
        return "".join(out)

    def svg(self):
        defs = (
            "<defs>"
            "<pattern id='grid' width='20' height='20' patternUnits='userSpaceOnUse'>"
            f"<path d='M20,0 L0,0 L0,20' fill='none' stroke='{GRID}' stroke-width='0.8'/></pattern>"
            "<filter id='shadow' x='-10%' y='-10%' width='120%' height='130%'>"
            "<feDropShadow dx='0' dy='1.5' stdDeviation='1.8' flood-color='#0f172a' flood-opacity='0.14'/>"
            "</filter>"
            "<marker id='arrow' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' "
            f"orient='auto-start-reverse'><path d='M0,0 L10,5 L0,10 z' fill='{LINE}'/></marker>"
            "<style>.c4 .drill{cursor:pointer}.c4 .drill:hover .card{stroke:#111827;stroke-width:2.4}"
            ".c4 .zoom{opacity:.8}.c4 .drill:hover .zoom{opacity:1}.c4 a{text-decoration:none}"
            ".c4 a:hover text{text-decoration:underline}</style>"
            "</defs>"
        )
        head = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{self.width}' height='{self.height}' "
                f"viewBox='0 0 {self.width} {self.height}'>")
        bg = (f"<rect width='{self.width}' height='{self.height}' fill='{PAPER}'/>"
              f"<rect width='{self.width}' height='{self.height}' fill='url(#grid)'/>")
        footer = self._text(24, self.height - 14,
                            "Agent-drafted, 2026-10-16. A human editor removes this line after review.",
                            size=10, color="#9aa0a6", anchor="start")
        return (head + defs + "<g class='c4'>" + bg + self._header() + self._legend()
                + "".join(self.back) + "".join(self.parts) + footer + "</g></svg>")


if __name__ == "__main__":
    d = Diagram(760, 440, "c4lib self-test", "blueprint style, standard library only",
                crumbs=[("L1", "l1.svg"), ("L2", "l2.svg"), ("Self-test", None)])
    d.boundary(40, 120, 680, 290, "Example boundary")
    user = d.person(60, 160, "User", "a person")
    web = d.box(240, 150, 170, 76, "Web App", "[container: SvelteKit]", ["serves the UI"],
                href="l3-web.svg", hint="Open L3: Web App")
    db = d.datastore(520, 150, 150, 76, "Database", "[Postgres 16]")
    plan = d.box(240, 290, 170, 66, "Worker", "[planned]", kind="planned")
    ext = d.box(520, 290, 150, 66, "Mailer", "[external]", kind="external")
    d.connect(user, web, "HTTPS")
    d.connect(web, db, "SQL")
    d.connect(web, plan, "enqueue", dashed=True)
    d.connect(web, ext, "SMTP", a_side="bottom", a_t=0.9, b_side="top")
    print(d.svg())
