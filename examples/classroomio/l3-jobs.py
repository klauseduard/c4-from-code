#!/usr/bin/env python3
"""L3 component diagram for the jobs container (apps/jobs/src).

Regenerate:
    python3 l3-jobs.py > l3-jobs.svg
"""
from c4lib import Diagram

W, H = 1300, 960
d = Diagram(
    W, H,
    "ClassroomIO jobs - L3 Components",
    "origin/main, 2026-10-16 - BullMQ workers in apps/jobs/src and the stores/packages they call",
    crumbs=[("L1 System context", "l1-system-context.svg"),
            ("L2 Containers", "l2-containers.svg"), ("L3 jobs", None)],
)

d.boundary(60, 130, 620, 660, "jobs container · apps/jobs/src  [BullMQ + ffmpeg]")

index = d.box(110, 170, 320, 66, "index.ts", "[entry]", ["registers 7 workers"], kind="component")
workers = d.box(110, 270, 320, 200, "workers/", "[BullMQ workers]", [
    "media (2) · media-transcribe (1)",
    "youtube-captions · emails (5)",
    "notifications (5) · maintenance",
    "agent-course-generation",
    "(audience runs standalone)",
], kind="component")
d.note(110, 500, 370, [
    "webhooks · course-imports ·",
    "onboarding-bootstrap exist in",
    "QUEUE_NAMES + defaults only:",
    "no producer, no worker anywhere.",
], title="Declared but unused")

# --- consumed outside the container ---
redis = d.datastore(740, 180, 190, 80, "Redis 7", "[BullMQ broker]")
db = d.box(740, 310, 220, 80, "@cio/db", "[query layer]", kind="external")
pg = d.datastore(1010, 310, 170, 80, "Postgres 16")
obj = d.datastore(740, 440, 220, 80, "Object storage", "[S3 / MinIO / R2]")
email = d.box(740, 570, 220, 66, "@cio/email", "[SMTP / ZeptoMail]", kind="external")
core = d.box(740, 690, 220, 70, "@cio/core", "[agent runner]", ["runAgentCourseGenerationJob"], kind="external")
llm = d.box(740, 800, 270, 70, "@cio/ai-assistant · OpenAI", "[LLM · transcription]", kind="external")

d.connect(index, workers, "starts")
# lowest target gets the nearest trunk, so no connector crosses another
d.connect(workers, redis, "consume", a_side="right", a_t=0.15, b_side="left", mid=700)
d.connect(workers, db, "read/write", a_side="right", a_t=0.3, b_side="left", mid=660)
d.connect(workers, obj, "media (S3)", a_side="right", a_t=0.5, b_side="left", mid=620)
d.connect(workers, email, "send email", a_side="right", a_t=0.65, b_side="left", mid=580)
d.connect(workers, core, "agent course gen", a_side="right", a_t=0.8, b_side="left", mid=540)
d.connect(workers, llm, "transcribe", a_side="right", a_t=0.93, b_side="left", mid=500)
d.connect(db, pg, "Drizzle")
d.connect(core, llm, "generateText")

print(d.svg())
