#!/usr/bin/env python3
"""
Lightweight external collector CLI.

Usage:
    python collector/collector.py start --employee-id <id> --task-id <id> --tool antigravity [--repo .]
    python collector/collector.py stop [--tests-run N --tests-passed N --build-passed true|false]

The collector only observes externally/legitimately available evidence:
session timing, and git history in the repo you point it at. It never
inspects any AI tool's internals.
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(__file__))
from event_schema import NormalizedEvent  # noqa: E402
from git_tracker import get_activity_since  # noqa: E402
from session_tracker import SessionState, save_state, load_state, clear_state, now_iso  # noqa: E402

DEFAULT_BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8000")


def _post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as exc:
        print(f"[collector] WARNING: could not reach backend at {url}: {exc}", file=sys.stderr)
        return {}


def cmd_start(args):
    state = SessionState(
        employee_id=args.employee_id,
        task_id=args.task_id,
        tool=args.tool,
        repo_path=os.path.abspath(args.repo),
        started_at=now_iso(),
    )

    backend_session = {}
    if not args.no_backend:
        backend_session = _post(f"{args.backend}/api/sessions/start", {
            "employee_id": args.employee_id, "task_id": args.task_id, "tool": args.tool,
        })
    state.backend_session_id = backend_session.get("id")
    save_state(state)

    event = NormalizedEvent(
        employee_id=args.employee_id, task_id=args.task_id, timestamp=state.started_at,
        event_type="session_started", source="observed", tool=args.tool,
        metadata={"repo": state.repo_path},
    )
    print(f"[collector] session started: {json.dumps(event.to_dict())}")


def cmd_stop(args):
    state = load_state()
    if state is None:
        print("[collector] No active session found. Run `collector.py start` first.", file=sys.stderr)
        sys.exit(1)

    ended_at = now_iso()
    git_activity = get_activity_since(state.repo_path, state.started_at)

    if not args.no_backend and state.backend_session_id:
        _post(f"{args.backend}/api/sessions/{state.backend_session_id}/stop", {})

    if not args.no_backend and state.task_id:
        _post(f"{args.backend}/api/tasks/{state.task_id}/outcome", {
            "files_changed": git_activity.files_changed,
            "lines_added": git_activity.lines_added,
            "lines_removed": git_activity.lines_removed,
            "commits": git_activity.commits,
            "tests_run": args.tests_run or 0,
            "tests_passed": args.tests_passed or 0,
            "build_passed": args.build_passed,
            "output_generated": git_activity.commits > 0,
        })

    summary = {
        "employee_id": state.employee_id,
        "task_id": state.task_id,
        "tool": state.tool,
        "started_at": state.started_at,
        "ended_at": ended_at,
        "commits": git_activity.commits,
        "files_changed": git_activity.files_changed,
        "lines_added": git_activity.lines_added,
        "lines_removed": git_activity.lines_removed,
    }
    print(f"[collector] session stopped: {json.dumps(summary)}")
    clear_state()


def build_parser():
    parser = argparse.ArgumentParser(description="Enterprise AI Intelligence collector")
    parser.add_argument("--backend", default=DEFAULT_BACKEND, help="FastAPI backend base URL")
    parser.add_argument("--no-backend", action="store_true", help="Run locally without sending events to the backend")
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="Start observing a work session")
    p_start.add_argument("--employee-id", required=True)
    p_start.add_argument("--task-id", default=None)
    p_start.add_argument("--tool", default="antigravity")
    p_start.add_argument("--repo", default=".")
    p_start.set_defaults(func=cmd_start)

    p_stop = sub.add_parser("stop", help="Stop the active session and report evidence")
    p_stop.add_argument("--tests-run", type=int, default=None)
    p_stop.add_argument("--tests-passed", type=int, default=None)
    p_stop.add_argument("--build-passed", type=lambda s: s.lower() == "true", default=None)
    p_stop.set_defaults(func=cmd_stop)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
