#!/usr/bin/env python3
"""Build one self-contained, navigable page that inlines every C4 SVG beside this file.

Diagrams are discovered as l*.svg (l1-..., l2-..., l3-...). Their drill-down links
(system -> L2, container -> L3) are rewritten to in-page anchors, each diagram card
hugs its drawing at natural size (never upscaled) and is centred, a size control
scales the whole set down, and a zoom lightbox opens any diagram full-screen.
Standard library only.

Usage:
    python3 build-index.py "System" "origin/main, 2026-10-16" > index.html
    python3 build-index.py "System" "origin/main, 2026-10-16" --artifact > system-c4.html

The default emits a standalone HTML file. --artifact emits only the page content
(<title>, <style>, body markup; no <html>/<head>/<body>) with light and dark theme
tokens, ready to publish as a Claude Artifact.
"""
import datetime
import re
import sys
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
ARTIFACT = "--artifact" in sys.argv[1:]
SYSTEM = ARGS[0] if ARGS else "System"
STATE = ARGS[1] if len(ARGS) > 1 else ""
TODAY = datetime.date.today().isoformat()

svgs = sorted(HERE.glob("l*.svg"))
stems = [p.stem for p in svgs]
STEMS = "|".join(re.escape(s) for s in stems)


def title_of(stem):
    level, _, rest = stem.partition("-")
    return f"{level.upper()} - {rest.replace('-', ' ')}"


def read_svg(path):
    svg = path.read_text(encoding="utf-8")
    if not STEMS:
        return svg
    return re.sub(rf"href=(['\"])({STEMS})\.svg\1", r"href=\1#\2\1", svg)


def natural_width(svg):
    m = re.search(r"<svg[^>]*\swidth=['\"](\d+)", svg)
    return int(m.group(1)) if m else 1500


def section(p):
    svg = read_svg(p)
    return (
        f"<section id='{p.stem}'><h2>{escape(title_of(p.stem))} <a class='top' href='#top'>↑ top</a></h2>"
        f"<p class='src'>Generator: <code>{p.stem}.py</code> · click a card with a magnifier to drill down</p>"
        f"<figure style='--w:{natural_width(svg)}px'>{svg}</figure></section>"
    )


sections = "".join(section(p) for p in svgs)
nav = " · ".join(f"<a href='#{s}'>{escape(title_of(s))}</a>" for s in stems)
state = f" Code state: {escape(STATE)}." if STATE else ""
page_title = f"{escape(SYSTEM)} Architecture"

LIGHT = ("--bg: #eef1f6; --surface: #ffffff; --fg: #1f2937; --muted: #6b7280; "
         "--line: #d7dde7; --accent: #2f5fd1; --paper: #f7f9fc;")
DARK = ("--bg: #0f151b; --surface: #161e26; --fg: #e6ebf0; --muted: #98a4b1; "
        "--line: #2c3843; --accent: #7aa2ff; --paper: #f7f9fc; color-scheme: dark;")

dark_blocks = f"""
  @media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ {DARK} }} }}
  :root[data-theme="dark"] {{ {DARK} }}""" if ARTIFACT else ""

css = """
  /* layout: one centred column; each diagram card hugs its drawing (never upscaled) and is centred */
  :root { """ + LIGHT + """ }""" + dark_blocks + """
  body { font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 0;
         color: var(--fg); background: var(--bg); font-size: 14px; line-height: 1.45;
         padding-block: 24px 40px;
         padding-left: max(16px, env(safe-area-inset-left, 0px));
         padding-right: max(16px, env(safe-area-inset-right, 0px)); }
  .wrap { max-width: 1560px; margin: 0 auto; }
  h1 { margin: 0 0 4px; font-size: 26px; }
  .meta { color: var(--muted); margin: 0 0 14px; max-width: 80ch; }
  nav { margin-bottom: 10px; }
  .size { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; font-size: 13px;
          color: var(--muted); margin: 0 0 28px; }
  .size button, #ov .bar button, figure .zoom {
    font: inherit; font-size: 12px; padding: 3px 9px; border: 1px solid var(--line); border-radius: 6px;
    background: var(--surface); color: var(--fg); cursor: pointer; }
  .size button.on { background: var(--accent); color: #fff; border-color: var(--accent); }
  section { margin: 0 0 44px; scroll-margin-top: 16px; }
  h2 { margin: 0 0 4px; font-size: 20px; }
  h2 .top { font-size: 12px; font-weight: normal; margin-left: 10px; }
  .src { color: var(--muted); font-size: 13px; margin: 0 0 12px; }
  /* the drawings are light "paper" in both themes; the card takes the paper colour */
  figure { position: relative; box-sizing: border-box; margin: 0 auto;
           width: min(100%, calc(var(--w, 1500px) * var(--zoom, 1) + 26px));
           background: var(--paper); border: 1px solid var(--line); border-radius: 10px; padding: 12px;
           box-shadow: 0 1px 3px rgba(15, 23, 42, .08); }
  figure svg { display: block; width: 100%; height: auto; border-radius: 6px; }
  figure .zoom { position: absolute; top: 10px; right: 10px; }
  a { color: var(--accent); }
  :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  footer { color: var(--muted); font-size: 12px; margin-top: 32px; }
  #ov { display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, .92); z-index: 10; }
  #ov.on { display: block; }
  #ov .bar { position: absolute; top: 0; left: 0; right: 0; display: flex; gap: 8px; align-items: center;
             padding: calc(10px + env(safe-area-inset-top, 0px)) max(16px, env(safe-area-inset-right, 0px))
                      10px max(16px, env(safe-area-inset-left, 0px));
             background: var(--surface); color: var(--fg); z-index: 11; font-size: 13px; }
  #ov .stage { position: absolute; top: calc(46px + env(safe-area-inset-top, 0px)); bottom: 0; left: 0; right: 0;
               overflow: auto; padding: 16px; }
  #ov .stage svg { height: auto; display: block; background: var(--paper); border-radius: 6px; }
"""

body = f"""<a id="top"></a>
<div class="wrap">
<h1>{page_title}</h1>
<p class="meta">C4 diagrams generated from the code.{state} Each diagram is emitted by a standard-library
Python script; the repository's <code>architecture/diagrams/README.md</code> holds the method, the
label-to-source list and the report. Navigate like C4: click the system in L1 to open its containers,
click a container in L2 to open its components, use the breadcrumbs to go back up.</p>
<nav>{nav}</nav>
<div class="size">Diagram size:
<button data-s="0.5">50%</button><button data-s="0.75">75%</button><button data-s="1">100%</button>
<button data-s="fit">Fit width</button><span>· ⤢ Zoom on a diagram opens it full-screen with its own − / +</span></div>
{sections}
<footer>Agent-drafted, {TODAY}. A human editor removes this line after review.</footer>
</div>
<div id="ov"><div class="bar"><strong>Zoom</strong>
<button data-z="-">−</button><span id="pct">100%</span><button data-z="+">+</button>
<button data-z="1">Fit</button><span style="flex:1"></span><button data-z="x">Close (Esc)</button></div>
<div class="stage"></div></div>
<script>
(function () {{
  var ov = document.getElementById('ov'), stage = ov.querySelector('.stage'), scale = 1;
  function apply() {{
    var s = stage.querySelector('svg');
    if (s) s.style.width = (100 * scale) + '%';
    document.getElementById('pct').textContent = Math.round(scale * 100) + '%';
  }}
  document.querySelectorAll('figure').forEach(function (f) {{
    var b = document.createElement('button');
    b.className = 'zoom'; b.textContent = '⤢ Zoom';
    b.onclick = function () {{
      stage.replaceChildren(f.querySelector('svg').cloneNode(true));
      scale = 1; apply(); ov.classList.add('on');
    }};
    f.appendChild(b);
  }});
  ov.addEventListener('click', function (e) {{
    var z = e.target.dataset && e.target.dataset.z;
    if (z === '+') scale *= 1.25; else if (z === '-') scale /= 1.25; else if (z === '1') scale = 1;
    else if (z === 'x' || e.target === ov || e.target === stage) ov.classList.remove('on');
    apply();
  }});
  document.addEventListener('keydown', function (e) {{ if (e.key === 'Escape') ov.classList.remove('on'); }});

  var root = document.documentElement, sizeBtns = document.querySelectorAll('.size button');
  function setZoom(v) {{
    root.style.setProperty('--zoom', v === 'fit' ? '100' : v);
    sizeBtns.forEach(function (b) {{ b.classList.toggle('on', b.dataset.s === v); }});
    try {{ localStorage.setItem('c4-zoom', v); }} catch (e) {{}}
  }}
  sizeBtns.forEach(function (b) {{ b.onclick = function () {{ setZoom(b.dataset.s); }}; }});
  var saved = '1';
  try {{ saved = localStorage.getItem('c4-zoom') || '1'; }} catch (e) {{}}
  setZoom(saved);
}})();
</script>
"""

if ARTIFACT:
    print(f"<title>{page_title}</title>\n"
          '<meta name="claude:viewport-fit-sides" content="cover">\n'
          f"<style>{css}</style>\n{body}")
else:
    print(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title}</title>
<style>{css}</style>
</head>
<body>
{body}</body>
</html>""")
