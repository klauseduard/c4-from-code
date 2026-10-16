#!/usr/bin/env python3
"""L3 component diagram for the dashboard container (apps/dashboard/src).

Regenerate:
    python3 l3-dashboard.py > l3-dashboard.svg
"""
from c4lib import Diagram

W, H = 1320, 860
d = Diagram(
    W, H,
    "ClassroomIO dashboard - L3 Components",
    "origin/main, 2026-10-16 - internal modules of apps/dashboard/src and how a request reaches the api",
    crumbs=[("L1 System context", "l1-system-context.svg"),
            ("L2 Containers", "l2-containers.svg"), ("L3 dashboard", None)],
)

d.boundary(60, 130, 760, 700, "dashboard container · apps/dashboard/src  [SvelteKit / Node]")

pages = d.box(110, 170, 320, 80, "routes/(app|auth)/", "[SvelteKit pages]",
              ["thin UI · login · app shell"], kind="component")
feats = d.box(110, 310, 320, 96, "features/<domain>/api/*.svelte.ts", "[API classes]",
              ["this.execute() · client Zod"], kind="component")
types = d.box(520, 318, 290, 80, "features/<domain>/utils/types.ts", "[inferred types]",
              ["InferResponseType"], kind="component")
rpc = d.box(110, 480, 320, 86, "utils/services/api", "[typed RPC client]", ["classroomio (hc)"],
            kind="component")
hooks = d.box(110, 640, 320, 96, "hooks.server.ts", "[SSR + proxy]",
              ["proxyRequestToApi:", "/api/auth/* · /proxy/*"], kind="component")
auth = d.box(520, 660, 290, 90, "utils/services/auth/client.ts", "[better-auth client]",
             ["login: signIn.email()", "-> /api/auth/*"], kind="component")

api = d.box(860, 480, 220, 86, "api container", "[Hono]", href="l3-api.svg", hint="Open L3: api")

d.note(860, 170, 380, [
    "@cio/db is imported type-only",
    "(TLocale, TUser, ...). Every read",
    "and write goes through the api,",
    "via the hooks.server proxy.",
], title="No direct database access")
d.note(860, 640, 380, [
    "Polar webhooks: routes/api/polar.",
    "PostHog · Umami · Sentry. See L1.",
], title="External & analytics")

d.connect(pages, feats, "calls")
d.connect(feats, rpc, "execute()")
d.connect(feats, types, "infer")
d.connect(rpc, hooks, "same-origin /proxy/*")
d.connect(auth, hooks, "/api/auth")
d.connect(hooks, api, "forward (Bearer)", a_side="right", a_t=0.3, b_side="left", mid=470)

print(d.svg())
