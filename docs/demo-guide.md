# Demo Guide

See the root `README.md` "Live Demo Workflow" section for exact commands. In short:

1. Bootstrap an admin, a department, and an employee (with a real `hourly_cost` estimate).
2. Start a real development task with a `baseline_minutes` estimate (e.g. "60 minutes by hand").
3. Run `collector/collector.py start` pointed at a real git repository.
4. Do genuine work in Antigravity (or any editor): write code, run tests, commit.
5. Run `collector/collector.py stop` — reports real git evidence (commits, files/lines changed)
   to the backend's outcome endpoint.
6. Complete the task via the API — this stamps `actual_minutes` from real start/complete
   timestamps.
7. If (and only if) you have a legitimate way to attribute AI cost for that work (see
   "Known Limitations" in the root README), record it via `/api/tasks/{id}/ai-events`.
8. Open the task detail page in the frontend to see the full ROI calculation breakdown, or the
   management dashboard for the aggregate view.

Example task ideas (Section 26 of the original spec): build a FastAPI endpoint, fix a backend bug,
add validation, write unit tests, refactor a function, implement a database query, add a frontend
component, fix a UI issue. These are workload examples for the demo — not separate applications.
