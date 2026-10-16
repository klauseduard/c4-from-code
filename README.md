# c4-from-code

A Claude Code skill that draws a **C4 architecture diagram set from a codebase** — L1 system
context, L2 containers, L3 components — as reproducible standard-library Python → SVG, with
C4 drill-down (click the system to open its containers, a container to open its components),
and a single self-contained `index.html` viewer.

What makes it more than a drawing tool is the method it enforces:

- **Code is ground truth.** If it isn't in the code it isn't on the diagram; where docs and code
  disagree, the code is drawn and the disagreement is reported.
- **Two gates.** Every diagram is rendered and *looked at* (catches layout defects), and the
  load-bearing claims are then **verified against source** (catches edges that look right but
  aren't — type-only imports mistaken for runtime calls, declared-but-unused queues, swapped
  hostnames). The second gate exists because the first one cannot see a plausible lie.
- **Every label traces to a file.** The report ends with a label → `path:line` table.

## What's in this package

```
.claude-plugin/        plugin.json (plugin manifest) and marketplace.json (so this repo is a marketplace)
skills/c4-from-code/   SKILL.md (the method), c4lib.py (SVG helper), build-index.py (viewer), render.mjs
examples/classroomio/  a complete worked example: generator scripts, README/report and index.html
```

Open `examples/classroomio/index.html` in a browser to see a finished set — it is one file,
navigable, with a size control and a zoom lightbox.

## Install

Pick whichever fits. All three give you the same skill.

**A. Try it without installing** (also works straight from the `.zip`):

```bash
claude --plugin-dir ./c4-from-code-plugin        # or: claude --plugin-dir ./c4-from-code-plugin.zip
```

**B. Install from GitHub as a plugin** (this repository is its own marketplace):

```text
/plugin marketplace add klauseduard/c4-from-code
/plugin install c4-from-code@klaus-tools
```

Installed this way the skill is invoked as `/c4-from-code:c4-from-code`.

**C. Plain skill, no plugin machinery** — copy the skill folder so `SKILL.md` sits directly in it:

```bash
cp -r skills/c4-from-code  .claude/skills/        # this project only
cp -r skills/c4-from-code  ~/.claude/skills/      # every project, this user
```

Invoked as `/c4-from-code`.

## Use

Ask Claude for an architecture map, or invoke the skill and tell it:

- the **system name** and **scope** (paths or repositories),
- the **branch** that is ground truth (e.g. `origin/main`),
- which containers should get an **L3**, and where to put the output
  (default `architecture/diagrams/`).

It will inventory the code, **stop and show you the inventory** with the decisions that change
the diagrams (deployment topology, L3 targets, container granularity) before drawing, then draw
L1 → L2 → L3, render and check each one, verify the claims against source, build `index.html`,
write the report, and commit one level per commit without pushing.

## Requirements

- Python 3 (standard library only) for generating diagrams.
- Any SVG renderer for the look gate: `resvg`, `rsvg-convert`, `cairosvg`, or the bundled
  `render.mjs` with Node 18+ (`npm install @resvg/resvg-js@2.6.2` in a scratch directory).

## Notes

- Generated `index.html` inlines SVG; exclude it from code formatters (e.g. `.prettierignore`).
- The skill is opinionated about style (blueprint look, orthogonal connectors) so that every set
  a team produces reads the same way. The style lives in `c4lib.py`.
- Each generated file carries an `Agent-drafted, <date>` line for a human reviewer to remove.
