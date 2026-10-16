---
name: c4-from-code
description: Generate a navigable C4 architecture diagram set (L1 system context -> L2 containers -> L3 components, with drill-down links and breadcrumbs) from a codebase treated as ground truth, as reproducible standard-library Python -> SVG in a blueprint style, plus a single-file index.html viewer. Use when asked to map or visualize a system's architecture, produce C4 diagrams, document how services/containers fit together, or build an architecture overview from code.
---

# C4 diagrams from code

Produce a C4 diagram set for a system by reading its code, not its docs. Each diagram is a small
Python script that emits one SVG through the bundled `c4lib.py`; `build-index.py` folds the set
into one navigable `index.html`. Everything is standard library, reproducible and diffable.

The point of this skill is **discipline against confident fabrication**, and there are two kinds
of error to defend against, each with its own gate:

- **Layout errors** (clipped labels, lines through boxes, colliding labels): caught by rendering
  every diagram and looking at it.
- **Factual errors that look fine** (an edge the inventory inferred but the code does not have):
  invisible to the eye. Only a verification pass against source catches them. A diagram that has
  passed the look gate is *not yet true*; it is only legible.

Do not relax either gate to move faster.

## Arguments (the invoker supplies; ask if missing)

- **System name** and **scope**: the paths/repos that make up the system.
- **Ground-truth branch** (e.g. `origin/main`); today's date is the "as of".
- **Which containers get an L3** (default: every deployable unit with more than one module).
- **Output dir** (default `architecture/diagrams/`) and where to embed (default: that dir's
  `README.md` plus the generated `index.html`).

## Ground truth, in order of authority

1. The code. 2. Build/deploy files (Dockerfiles, compose, wrangler, packaging). 3. Committed docs.

- Draw what the code does on the named branch as of today. Mark branch-only/PoC as `poc`,
  planned-only as `planned`.
- **Do not invent components. If you cannot find it in the code, it is not on the diagram.**
- Where a doc and the code disagree, draw the code and record the disagreement in the report.

## Method (the gates, in order)

1. **Inventory first.** Per repo/unit: entry points; listeners (port, protocol, auth); outbound
   calls; data stores; packaging; language + version. Delegating this to an exploration agent is
   fine, but **treat the result as a draft**: it summarizes, and summaries infer edges.
2. **Checkpoint with the human before drawing L2.** Show the inventory table and ask the
   decisions that change the diagrams, explicitly, rather than guessing:
   - topology scope (self-hosted only / cloud only / both, with boundaries);
   - which containers get an L3;
   - container granularity (e.g. one worker image, or one container per worker);
   - anything the inventory flagged as ambiguous.
3. **Draw L1 -> L2 -> L3.** After emitting each SVG, render it to PNG and look at it. Fix every
   clipped label, every line through a box, every label collision before moving on. If no
   renderer exists, install one (below); never skip the gate.
   Then **check the composed viewer, not just the drawings** — the SVG gate says nothing about how
   the page lays them out, and that is where the first usability defect appeared (diagrams
   upscaled to a wide monitor, taller than the viewport, pinned left). After `build-index.py`:
   figure count equals diagram count; every drill-down `href='#…'` has a matching section id;
   the inline script passes `node --check`; and for `--artifact` output there is no
   `<html>`/`<head>`/`<body>` and the dark-theme blocks are present. Reason about the page at a
   wide (~2500 px) and a narrow (~400 px) viewport: nothing upscales past natural size, cards are
   centred, the body never scrolls sideways.
4. **Verify the load-bearing claims against source** before calling the set done. Ask of each
   edge "is this true", not "does it look right". The classic traps, all seen in practice:
   - **Type-only imports read as runtime dependencies.** `import type { X } from 'pkg'` is not a
     call. For every "A reads/writes B" edge, grep A's imports and usages of B and confirm a
     runtime path exists; if every import is `import type`, there is no edge.
   - **Declared but unused.** A queue, route, flag or module that is defined but has neither a
     producer nor a consumer anywhere. Find both ends or draw none; state the finding in a note.
   - **Docs vs code drift** in ports, counts, names. Draw the code; list the disagreement.
   - **Misleading names.** Hostnames, env vars and comments can be wrong or swapped; follow what
     the code does with the value.
   - **Where logic runs vs where it is defined.** A worker that calls a library's runner means the
     boundary is "worker -> library -> provider", not "worker -> provider".
   Record the pass in the report under "Verified against the code"; when a claim fails, fix the
   diagram and say what changed.
5. **Keep a `label -> source file:line` list** the whole way and include it in the report.

## Deliverables

1. **L1 system context**: the system as one box; the people and machine clients that use it;
   external systems it exchanges data with; one labelled line per exchange. The system box links
   to L2.
2. **L2 containers**: every deployable unit with runtime and listeners, data stores, boundaries
   by host/deployment (e.g. a core stack and a cloud-edge boundary). Each container that has an
   L3 links to it. External SaaS is summarized in a note ("see L1") rather than redrawn.
3. **L3 components**, one per chosen container: modules as the code divides them (type line
   names the file/dir), the packages and stores they call, a note for what is deliberately not
   drawn and for known limitations. Breadcrumbs back to L2 and L1.
4. **Generators**: one script per diagram beside its SVG, importing `c4lib`.
5. **`index.html`** from `build-index.py`: one self-contained file that inlines every SVG and
   rewrites the drill-down links to in-page anchors. This is what people actually open; treat it
   as the primary deliverable, and hold it to these invariants:
   - a diagram is **never upscaled** past its natural width (read from the SVG's `width`), so a
     wide monitor shows it at 1:1 instead of blown up and taller than the screen;
   - each card **hugs its drawing and is centred** in a centred column, so no empty card sprawls
     to the right;
   - a **size control** (50 / 75 / 100 % / fit width) scales the whole set down and is remembered
     per browser; a zoom lightbox opens one diagram full-screen with its own − / +.
   `build-index.py … --artifact` emits the same page as artifact-ready content (no
   `<html>`/`<head>`/`<body>`, light + dark theme tokens, mobile gutters; the drawings stay light
   "paper" in both themes) for publishing with the Artifact tool when a hosted link is wanted.
   One builder serves both outputs so the repo viewer and the hosted page cannot drift; a
   published artifact is private until the owner shares it.
6. **`README.md`**: regenerate commands per diagram, the embedded SVGs, and the report.

Do not keep superseded rounds in the tree (no `v1/` snapshots, no side-by-side viewers); git
history is the comparison.

## Generating (house backend and style)

Copy `c4lib.py`, `build-index.py` and `render.mjs` from `${CLAUDE_SKILL_DIR}` (the directory that
holds this file, in both the plugin layout and a plain `.claude/skills/` install) into the output
dir. Extend `c4lib.py` only if a shape is genuinely missing. `python3 c4lib.py` emits a self-test.

**Style** (fixed, so every set reads the same): paper with a faint grid; a title block with
breadcrumbs; an automatic legend of the kinds used; carded boxes with a coloured header band,
monospace type line and a soft shadow; dark text on light bodies; orthogonal connectors with
rounded corners; a magnifier glyph on every card that links somewhere.

**API**

- `Diagram(w, h, title, subtitle, crumbs=[(label, href_or_None), ...])` — crumbs are the
  drill-up trail; the last entry is the current diagram.
- Shapes return a `Box`: `.box(x,y,w,h,name,type_line,desc,kind,href=,hint=)`,
  `.datastore(...)`, `.person(x,y,name,desc,w)`, `.note(x,y,w,lines,title)`; `.boundary(...)`.
  Kinds: `container`, `component` (L3 internals), `datastore`, `external` (outside systems and
  packages outside the container), `person`, `poc`, `planned`.
- `connect(a, b, label, a_side=, b_side=, a_t=, b_t=, mid=, dashed=, label_at=)` routes an elbow
  between box edges, arrow at `b`. `.line(...)` is a straight fallback.

**Layout heuristics that make elbow routing clean**

- A fan from one box to a column: give each connector its own trunk with `mid`, ~30-40 px apart,
  and spread the exits with `a_t`. **Lowest target -> nearest trunk** (and for targets above the
  source, highest target -> nearest trunk) yields zero crossings.
- Labels sit on the longest segment by default (`label_at="auto"`), so they never land on a box
  edge. If a label must sit between two adjacent boxes, leave >= 90 px between them or route
  elsewhere.
- Connectors do not avoid boxes. Keep side columns above or below the band a fan sweeps, and
  check corner clips (a line passing a box's corner is still a line through a box).
- Mixed-side L routes (`a_side="bottom", b_side="left"`) are convenient but cut through anything
  below `a`; prefer V-H-V with a `mid` that stays in a gap.
- One-row connections between neighbours are straight; let their label width decide the gap.

**Rendering (the look gate)**

Any SVG renderer works (`resvg`, `rsvg-convert`, `cairosvg`). When none is installed, the
bundled `render.mjs` needs only a prebuilt npm package, in a scratch dir, not the repo:

```bash
npm init -y >/dev/null && npm install @resvg/resvg-js@2.6.2
node render.mjs l2-containers.svg /tmp/l2.png     # then open the PNG and look
```

**Formatter and hook gates.** A pre-commit formatter will try to parse the generated
`index.html` (it inlines SVG) and may rewrite or reject it: add it to the formatter's ignore file
(e.g. `.prettierignore`). `.svg` and `.py` are usually skipped. Ignore `__pycache__/` in the
output dir.

## Style rules

- **Subtitle on every diagram**: code state + date + one sentence of purpose, e.g.
  `"origin/main, 2026-10-16 - how the API, workers and stores connect"`.
- Box: name; type line in brackets (`[container: Hono / Node 20]`, `[module: dispatch.rs]`); at
  most three short description lines; text inside the box at every size.
- Lines: label the protocol **or** the data, not both unless both are surprising. Arrowhead on
  the direction of the request.
- **One term for one thing** across all diagrams; use the names the code uses.
- Readable at display width: no text under 11 px at 1:1; no note longer than five lines.
- **Drill-down, like C4 intends**: L1 system -> L2; each L2 container -> its L3; every diagram
  carries `crumbs` back up.
- Each drafted file carries, under its heading or as a footer:
  `_Agent-drafted, YYYY-MM-DD. A human editor removes this line after review._`

## Report (end with) and commits

The list of diagrams and their scripts; the `label -> source` list; **verified against the
code** (what was checked, what changed); every place the code disagreed with docs; everything
left out and why; every boundary decided, and by whom.

Commit one diagram or level per commit with an imperative subject (Conventional Commits if the
repo uses them). Follow the repo's rules on attribution trailers (many forbid them). Never
reference the prompting conversation. **Do not push.**
