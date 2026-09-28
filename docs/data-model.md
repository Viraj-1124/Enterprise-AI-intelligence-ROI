# Data Model

See `backend/app/models/models.py` for the SQLAlchemy source of truth. Summary:

| Table | Purpose | Key provenance notes |
|---|---|---|
| `departments` | Org unit | — |
| `employees` | People; `hourly_cost` | `hourly_cost` is an **estimated** configuration value used only for ROI |
| `tasks` | Unit of work; `baseline_minutes`, `actual_minutes` | `baseline_minutes` is **estimated**; `actual_minutes` is **observed** (derived from `started_at`/`completed_at`) |
| `work_sessions` | Time-boxed activity in a tool | `started_at`/`ended_at`/`duration_minutes` are **observed** |
| `ai_usage` | One AI interaction's tokens/cost | Carries an explicit `source` column (`connector`/`observed`/`imported`/`estimated`/`unavailable`); cost is only populated when both real token counts and real pricing are present |
| `task_outcomes` | Git/test/build evidence | **observed**, reported by the collector or manually |
| `roi_metrics` | Computed ROI for a task | `calculation_status` is `calculated` / `partial` / `unavailable` — never silently upgraded |
| `activity_events` | Normalized event log backing the task timeline | Mirrors the generic event schema (see `collector/event_schema.py`) |

Full field lists match the spec's Section 4 exactly; migrations live in `backend/alembic/versions/`.
