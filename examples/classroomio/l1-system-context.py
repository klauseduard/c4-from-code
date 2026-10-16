#!/usr/bin/env python3
"""L1 system context for ClassroomIO.

Regenerate:
    python3 l1-system-context.py > l1-system-context.svg
"""
from c4lib import Diagram

W, H = 1500, 900
d = Diagram(
    W, H,
    "ClassroomIO - L1 System Context",
    "origin/main, 2026-10-16 - who uses ClassroomIO and the external systems it exchanges data with",
    crumbs=[("L1 System context", None)],
)

# --- the system (click to open L2) ---
system = d.box(580, 380, 300, 160, "ClassroomIO", "[software system]",
               ["Multi-tenant LMS: courses,", "lessons, cohorts, certificates"],
               href="l2-containers.svg", hint="Open L2: containers")

# --- actors (left) ---
student = d.person(65, 150, "Student", "learns", w=110)
tutor = d.person(65, 310, "Tutor", "teaches & grades", w=110)
admin = d.person(65, 470, "Admin", "runs the org", w=110)
client = d.box(50, 660, 180, 64, "API / MCP client", "[external integrator]", kind="external")

d.connect(student, system, "uses (browser, HTTPS)", a_side="right", b_side="left", b_t=0.2, mid=280, label_at="end")
d.connect(tutor, system, "teaches & grades", a_side="right", b_side="left", b_t=0.4, mid=250, label_at="end")
d.connect(admin, system, "administers", a_side="right", b_side="left", b_t=0.6, mid=330, label_at="end")
d.connect(client, system, "REST API / MCP (API key)", a_side="right", b_side="left", b_t=0.8, mid=380, label_at="end")

# --- external systems (right) ---
externals = [
    ("Identity providers", "[Google / GitHub / SSO-OIDC]", "OAuth / OIDC sign-in"),
    ("Payments", "[Polar]", "subscriptions, webhooks"),
    ("LLM providers", "[OpenAI / Anthropic / Google / Moonshot]", "AI tutor & course gen"),
    ("Email", "[ZeptoMail / SMTP]", "transactional email"),
    ("Analytics & errors", "[PostHog / Umami / Sentry]", "telemetry"),
    ("Image search", "[Unsplash]", "image search"),
    ("Enterprise license API", "[enterprise-api.classroomio.dev]", "license check (self-hosted)"),
]
ys = [120, 230, 340, 450, 560, 670, 780]
mids = [910, 940, 970, 1000, 970, 940, 910]
ports = [0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875]
for (name, type_line, label), ey, mx, t in zip(externals, ys, mids, ports):
    ext = d.box(1120, ey, 260, 66, name, type_line, kind="external")
    d.connect(system, ext, label, a_side="right", a_t=t, b_side="left", mid=mx, label_at="end")

print(d.svg())
