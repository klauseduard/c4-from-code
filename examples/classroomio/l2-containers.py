#!/usr/bin/env python3
"""L2 container diagram for ClassroomIO (both deployment topologies).

Regenerate:
    python3 l2-containers.py > l2-containers.svg
"""
from c4lib import Diagram

W, H = 1500, 980
d = Diagram(
    W, H,
    "ClassroomIO - L2 Containers",
    "origin/main, 2026-10-16 - deployable units, data stores and the cloud edge, and how they wire together",
    crumbs=[("L1 System context", "l1-system-context.svg"), ("L2 Containers", None)],
)

browser = d.person(80, 150, "Browser", "end user", w=110)

# --- cloud edge boundary (cloud deploy only) ---
d.boundary(320, 130, 1140, 250, "Cloud edge · Cloudflare Workers (cloud deploy only)")
tr = d.box(360, 180, 190, 100, "tenant-router", "[CF Worker]", ["routing · HLS auth", "PostHog proxy"])
r2 = d.datastore(640, 185, 150, 85, "R2", "[videos / assets]")
d.datastore(820, 185, 120, 85, "KV", "[website cache]")
d.box(970, 185, 150, 70, "website", "[CF Worker]")
d.box(1140, 185, 130, 70, "docs", "[Astro static]")
d.box(1290, 185, 130, 70, "help", "[Astro static]")
helpcms = d.box(970, 275, 150, 70, "help-cms", "[CF Worker]")
github = d.box(1150, 280, 150, 60, "GitHub OAuth", "[external]", kind="external")
d.connect(helpcms, github)

# --- core application boundary (click a container to open its L3) ---
d.boundary(320, 460, 900, 170, "Core application · self-hosted compose & cloud / Render")
dash = d.box(380, 505, 210, 100, "dashboard", "[SvelteKit / Node]",
             [":5173 dev · :3082 container", "no direct DB access"],
             href="l3-dashboard.svg", hint="Open L3: dashboard")
api = d.box(700, 505, 210, 100, "api", "[Hono / Node 20]", [":3002 dev · :3081 container"],
            href="l3-api.svg", hint="Open L3: api")
jobs = d.box(980, 505, 210, 100, "jobs", "[BullMQ + ffmpeg]", ["no HTTP listener"],
             href="l3-jobs.svg", hint="Open L3: jobs")

# --- data stores (only api and jobs reach them) ---
d.boundary(320, 740, 900, 170, "Data stores")
redis = d.datastore(560, 785, 170, 95, "Redis 7", "[BullMQ broker]")
pg = d.datastore(790, 785, 200, 95, "Postgres 16", "[DATABASE_URL]")
obj = d.datastore(1030, 785, 180, 95, "Object storage", "[MinIO / S3 / R2]")

d.note(1250, 500, 230, [
    "LLM, email, Polar, analytics,",
    "license, Unsplash - called by",
    "api and jobs. See L1.",
], title="External SaaS (omitted)")
d.note(1250, 690, 230, [
    "Cloud: Browser -> edge.",
    "Self-hosted: Browser ->",
    "dashboard directly.",
    "Storage: MinIO (self-host)",
    "/ R2 (cloud).",
], title="Topology")

# --- entry ---
d.connect(browser, tr, "HTTPS (cloud)")
d.connect(browser, dash, "HTTPS (self-hosted)", a_side="bottom", b_side="left", b_t=0.3)

# --- edge -> core / edge internal ---
d.connect(tr, dash, "routes /*", a_side="bottom", a_t=0.35, b_side="top", b_t=0.4, mid=400)
d.connect(tr, api, "routes /api", a_side="bottom", a_t=0.75, b_side="top", b_t=0.5, mid=425)
d.connect(tr, r2, "HLS", a_t=0.475)

# --- core internal (dashboard reaches data only through the api) ---
d.connect(dash, api, "proxy (Bearer)")

# --- core -> stores (staggered trunks) ---
d.connect(api, redis, "enqueue", a_side="bottom", a_t=0.15, b_side="top", b_t=0.35, mid=640)
d.connect(api, pg, "read/write", a_side="bottom", a_t=0.5, b_side="top", b_t=0.35, mid=658)
d.connect(api, obj, "presign", a_side="bottom", a_t=0.85, b_side="top", b_t=0.3, mid=676)
d.connect(jobs, redis, "consume", a_side="bottom", a_t=0.15, b_side="top", b_t=0.7, mid=694)
d.connect(jobs, pg, "read/write", a_side="bottom", a_t=0.3, b_side="top", b_t=0.7, mid=712)
d.connect(jobs, obj, "stream media", a_side="bottom", a_t=0.838, b_side="top", b_t=0.7)

print(d.svg())
