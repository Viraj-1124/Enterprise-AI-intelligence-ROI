# Architecture

```
AI / Work Tools (Antigravity, OpenAI, Claude, Gemini, GitHub)
        │
        ▼
  Connector Layer (backend/app/connectors)
        │
        ▼
   FastAPI (ONE backend, backend/app)
        │
        ▼
   SQLAlchemy models → SQLite (default) / PostgreSQL (via DATABASE_URL)
        │
        ▼
   Analytics / ROI Engine (backend/app/analytics/roi_engine.py — pure functions)
        │
        ▼
   Next.js / React UI (frontend/)
        │
        ▼
   Management / Department / Employee dashboards, Task ROI detail,
   Prompt Intelligence
```

## Why one backend

Everything — tasks, sessions, AI usage, outcomes, ROI, dashboards, prompt intelligence — lives
under `backend/app`. There is no second/demo backend and no fake business application; the
"business logic" the platform demonstrates ROI on is real development tasks (see `docs/demo-guide.md`).

## Data provenance, not just data

Every value that could be mistaken for ground truth carries an explicit source: `observed`
(timestamps/git activity), `connector` (a real provider API), `estimated` (a configured assumption
like `hourly_cost` or `baseline_minutes`), `imported`, or `unavailable`. The ROI engine
(`backend/app/analytics/roi_engine.py`) never silently converts one into another — see its
docstrings and `backend/tests/test_roi_engine.py` for the enforced edge cases (missing baseline,
zero baseline, missing AI cost, negative time-saved clamped to zero, aggregate ROI computed from
sums rather than an average of per-task percentages).

## Antigravity

Antigravity is never modified or reached into. The `AntigravityConnector`
(`backend/app/connectors/providers.py`) always reports `unavailable` for AI-specific telemetry.
Externally observable work evidence (session timing, git commits/diffs, test results) is instead
collected by `collector/collector.py`, which only reads the developer's own git history and local
session timing — nothing Antigravity-specific.
