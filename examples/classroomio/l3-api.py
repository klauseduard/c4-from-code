#!/usr/bin/env python3
"""L3 component diagram for the api container (apps/api/src).

Regenerate:
    python3 l3-api.py > l3-api.svg
"""
from c4lib import Diagram

W, H = 1500, 900
d = Diagram(
    W, H,
    "ClassroomIO api - L3 Components",
    "origin/main, 2026-10-16 - internal modules of apps/api/src and the packages/stores they call",
    crumbs=[("L1 System context", "l1-system-context.svg"),
            ("L2 Containers", "l2-containers.svg"), ("L3 api", None)],
)

d.boundary(60, 130, 860, 720, "api container · apps/api/src  [Hono / Node 20]")

index = d.box(110, 170, 200, 66, "index.ts", "[entry]", ["@hono/node-server :3081"], kind="component")
app = d.box(110, 280, 200, 66, "app.ts", "[root Hono app]", ["mounts domain routers"], kind="component")
mw = d.box(540, 170, 330, 60, "middlewares/", "[auth · api-key · rate-limit · license]", kind="component")
val = d.box(540, 245, 250, 50, "@cio/utils", "[Zod validation schemas]", kind="external")
utils = d.box(540, 310, 250, 50, "utils/", "[handleError · hono]", kind="component")
routes = d.box(110, 400, 340, 96, "routes/<domain>/", "[HTTP handlers]",
               ["thin · 1 type per route", "/api/auth/* -> better-auth", "/public-api/v1 (API key)"],
               kind="component")
services = d.box(110, 570, 340, 96, "services/<domain>/", "[business logic]",
                 ["transactions · AppError", "orchestrate query functions"], kind="component")

d.note(110, 700, 340, [
    "Layer rule: validation (Zod) ->",
    "query (@cio/db) -> service -> route.",
    "Routes & services never call",
    "Drizzle directly (AGENTS.md).",
], title="Layering")

# --- consumed packages & stores (outside the container) ---
libs = d.box(970, 420, 230, 80, "@cio/email · ai-assistant", "[shared libs]", ["· core · analytics"], kind="external")
jobs = d.box(970, 520, 230, 70, "@cio/jobs", "[enqueue]", kind="external")
redis = d.datastore(1270, 520, 170, 70, "Redis 7")
db = d.box(970, 620, 230, 90, "@cio/db", "[query layer]", ["Drizzle · better-auth"], kind="external")
pg = d.datastore(1270, 620, 170, 90, "Postgres 16")
obj = d.datastore(970, 740, 230, 90, "Object storage", "[S3 / MinIO / R2]")

# --- internal flow ---
d.connect(index, app, "serves")
d.connect(app, routes, "mounts", b_t=0.294)
d.connect(routes, services, "calls")
d.connect(mw, routes, "wraps", a_side="left", b_side="right", b_t=0.3, mid=480)
d.connect(routes, val, "zValidator", a_side="right", a_t=0.5, b_side="left", mid=500)
d.connect(routes, utils, "handleError", a_side="right", a_t=0.7, b_side="left", mid=520)

# --- services -> packages & stores (staggered trunks, no crossings) ---
d.connect(services, libs, "compose", a_side="right", a_t=0.2, b_side="left", mid=600)
d.connect(services, jobs, "enqueue", a_side="right", a_t=0.4, b_side="left", mid=640)
d.connect(services, db, "query fns", a_side="right", a_t=0.6, b_side="left", mid=680)
d.connect(services, obj, "S3 presign", a_side="right", a_t=0.85, b_side="left", mid=560)
d.connect(jobs, redis, "BullMQ")
d.connect(db, pg, "Drizzle")

print(d.svg())
