# ClassroomIO architecture - C4 diagrams

_Agent-drafted, 2026-10-16. A human editor removes this line after review._

A C4 diagram set generated **from the code** (not from docs) on `origin/main` as of 2026-10-16.
Each diagram is one standard-library Python script that emits one SVG via the shared `c4lib.py`
helper. No Mermaid, PlantUML, or external rendering services.

## Regenerate

Use Node 20 and Python 3 (no third-party Python deps):

```bash
cd architecture/diagrams
python3 l1-system-context.py > l1-system-context.svg
python3 l2-containers.py     > l2-containers.svg
python3 l3-api.py            > l3-api.svg
python3 l3-dashboard.py      > l3-dashboard.svg
python3 l3-jobs.py           > l3-jobs.svg
python3 build-index.py "ClassroomIO" "origin/main, 2026-10-16" > index.html   # navigable viewer
# add --artifact to emit the same page as theme-aware content for publishing as a Claude Artifact
```

To look at a diagram rendered (the method requires inspecting the PNG before trusting a diagram),
render with any SVG renderer, e.g. `@resvg/resvg-js`, `rsvg-convert`, or `cairosvg`.

To view the whole set from one file, open `index.html` in a browser: it inlines every SVG, makes
the C4 drill-down clickable (system -> containers -> components, breadcrumbs back up), adds a
zoom lightbox.
The standalone SVGs are navigable too: a card with a magnifier glyph opens the next level.

---

## L1 - System context

![L1 system context](l1-system-context.svg)

Source: `l1-system-context.py`

## L2 - Containers

![L2 containers](l2-containers.svg)

Source: `l2-containers.py`

## L3 - api components

![L3 api](l3-api.svg)

Source: `l3-api.py`

## L3 - dashboard components

![L3 dashboard](l3-dashboard.svg)

Source: `l3-dashboard.py`

## L3 - jobs components

![L3 jobs](l3-jobs.svg)

Source: `l3-jobs.py`

---

## Report

### Label -> source (every box/line traces to the code)

| Claim on a diagram | Source |
| --- | --- |
| api Hono entry, server-to-server `Bearer PRIVATE_SERVER_KEY` | `apps/api/src/index.ts`; `apps/api/src/middlewares/api-key.ts:24` |
| api port `:3002` dev / `:3081` container | `apps/api/src/constants/index.ts:5`; `docker-compose.yaml`; `docker/Dockerfile.api` (EXPOSE 3081) |
| dashboard `:5173` dev / `:3082` container, proxy with Bearer | `apps/dashboard/package.json`; `docker-compose.yaml`; `apps/dashboard/src/lib/utils/proxy-api-request.ts` |
| `/api/auth/*` handled by better-auth | `apps/api/src/app.ts`; `packages/db/src/auth.ts` |
| dashboard has **no direct DB access**: `@cio/db` is type-only, all data via the hooks.server proxy | every `@cio/db` import in `apps/dashboard/src` is `import type … from '@cio/db/types'`; `apps/dashboard/src/hooks.server.ts`; `proxy-api-request.ts:11` (`AUTH_PREFIX = '/api/auth'`) |
| layered rule route -> service -> query | `AGENTS.md`; `skills/writing-code/SKILL.md` |
| validation layer: `@cio/utils` Zod schemas via `zValidator` | 46 route files use `zValidator`, 57 import `@cio/utils/validation` (`apps/api/src/routes/**`) |
| jobs no HTTP listener, +ffmpeg | `docker/Dockerfile.jobs`; `apps/jobs/src/index.ts` |
| BullMQ queue names | `packages/jobs/src/queues/names.ts` |
| worker concurrencies (media 2, emails 5, ...) | `apps/jobs/src/workers/*.ts` (e.g. `media.ts:13`, `emails.ts:13`) |
| `audience` worker runs standalone (not in index.ts) | `apps/jobs/package.json`; `apps/jobs/src/index.ts` |
| `webhooks` / `course-imports` / `onboarding-bootstrap`: declared, **no producer and no worker** | `packages/jobs/src/queues/names.ts:11,12,14`; `defaults.ts:44,50,62`; no other reference under `apps/**` or `packages/**` |
| Postgres 16 / Redis 7 / object storage | `docker-compose.yaml` (postgres, redis, minio profile); `packages/jobs/src/connection.ts`; `@aws-sdk/client-s3` |
| tenant-router routing, HLS, PostHog proxy; R2/KV | `apps/tenant-router/src/index.ts`; `apps/tenant-router/wrangler.toml`; `apps/website/wrangler.jsonc` |
| website / docs / help / help-cms are CF Workers | `apps/{website,docs,help,help-cms}/wrangler.{jsonc,toml}` |
| help-cms GitHub OAuth proxy | `apps/help-cms/src/index.ts` |
| Polar billing + webhooks | `apps/dashboard/src/routes/api/polar/*/+server.ts` |
| PostHog / Umami / Sentry | `apps/dashboard/.../posthog/index.ts:40`; `.../umami/index.ts:11`; `apps/api/src/instrument.ts` |
| Email ZeptoMail / SMTP | `packages/email/src/send.ts:132` |
| LLM providers; OpenAI transcription + agent | `packages/ai-assistant/src/providers/index.ts`; `apps/jobs` (`OPENAI_API_KEY`) |
| agent course generation: jobs worker -> `@cio/core` runner -> `@cio/ai-assistant` | `apps/jobs/src/workers/agent-course-generation.ts:7,29`; `packages/core/src/services/agent/course-generation-runner.ts:102` (imports `@cio/ai-assistant/providers`:14, `generateText`:262) |
| Unsplash image search | `apps/api/src/routes/unsplash/unsplash.ts` |
| Enterprise license API (self-hosted) | `apps/api/src/services/license.ts` |
| Roles ADMIN/TUTOR/STUDENT; SSO/OIDC; Google OAuth | `packages/utils/src/constants/roles.ts`; `packages/db/src/auth.ts:64,138` |
| MCP / public API consumer | `packages/mcp/src/index.ts`, `config.ts:4`; `apps/api/src/app.ts` (`/public-api/v1`) |

### Round 3 - blueprint style and drill-down

Content unchanged from round 2; presentation and navigation reworked in `c4lib.py`:

- Blueprint look: paper with a faint grid, a title block with breadcrumbs, an automatic legend,
  carded boxes with a coloured header band and a soft shadow, dark text on light bodies.
- Orthogonal (elbow) connectors routed from box edges by `connect(a, b, ...)`, with staggered
  trunks so fans do not cross; labels sit on the longest segment, never on a box edge.
- C4 navigation: the system in L1 links to L2, each container in L2 links to its L3, every
  diagram has breadcrumbs back up; `index.html` rewrites those links to in-page anchors.

### Round 2 - verified against the code

A second pass checked the first draft's soft spots directly against the source (not the
inventory) and changed the diagrams accordingly. The round-1 renders stay in git history
(`a48a06d9`) if a comparison is ever needed.

- **Corrected: the dashboard has no direct database access.** Every `@cio/db` import under
  `apps/dashboard/src` is `import type … from '@cio/db/types'`; all data goes through
  `hooks.server.ts` -> `proxyRequestToApi` -> api. Round 1 drew a dashboard -> Postgres "SSR read"
  line (L2) and a hooks.server -> `@cio/db` -> Postgres chain (L3 dashboard); both removed.
- **Firmed up: `webhooks`, `course-imports`, `onboarding-bootstrap` are declared but unused.**
  They appear only in `QUEUE_NAMES` and `defaults.ts`; nothing enqueues to them and nothing
  consumes them. Round 1 hedged ("dormant or consumed elsewhere").
- **Resolved the agent boundary.** The `agent-course-generation` worker calls
  `runAgentCourseGenerationJob` in `@cio/core`, which drives `@cio/ai-assistant` providers and
  `generateText`. L3 jobs now shows `@cio/core` as the runner.
- **Added the validation layer** (`@cio/utils` Zod schemas via `zValidator`) to L3 api.
- Confirmed unchanged: 7 wired workers + standalone `audience`; the tenant-router naming trap; L1.

### Where the code disagreed with the docs (drawn as code says)

1. **API port.** Docs say `:3002` everywhere; every container sets `PORT=3081`. 3002 is dev-only.
   (`README.md`, `DEV_SETUP_NOTES.md`, `AGENTS.md:27,927` vs `docker-compose.yaml`, `Dockerfile.api`.)
2. **Dashboard port.** `:5173` dev (correct), but compose runs `:3082` and `Dockerfile.dashboard`
   sets `:3000` - three numbers across layers.
3. **"5 BullMQ workers"** (`AGENTS.md:927`) is stale: `apps/jobs/src/index.ts` wires **7**, plus a
   standalone `audience` worker.
4. **tenant-router naming trap:** in `wrangler.toml`, `cio-api.onrender.com` is actually the
   *dashboard* upstream and `cio-api-vymh.onrender.com` is the real *api*. Diagrams use true roles.

### Deliberately not drawn (and why)

- `apps/embeds` - a build step that uploads widgets to R2, not a running service.
- `apps/course-app`, `packages/course-app`, `@classroomio/mcp` - published CLIs / template gallery,
  not part of the running system (MCP appears in L1 as an external consumer).
- `apps/db-agent` - excluded from the pnpm workspace.
- `@cio/storybook` - dev-only tool.
- External SaaS is drawn in L1 only; L2/L3 reference it via notes to stay readable.
- `jobs` is drawn as one container; it ships as one image but can be split per worker.
- L3 is limited to `api`, `dashboard`, `jobs` (the multi-module runtime units).
- A Stripe SDK is present in dashboard deps, but Polar is the active billing integration.

### Boundaries decided

- **Topology:** both deployment shapes shown, with a self-hosted core boundary and a cloud-edge
  boundary (chosen with the maintainer).
- **L3 targets:** `api`, `dashboard`, `jobs` (chosen with the maintainer).
- `jobs` as a single container; `embeds` as an R2 asset; unused queues shown as a note;
  true service roles over the misleading onrender hostnames; subtitle labelled `origin/main`
  although the working branch (`klaus`) adds only a docs commit (defaults applied by the drafter).
