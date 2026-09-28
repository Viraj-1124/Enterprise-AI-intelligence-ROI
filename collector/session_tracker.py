"""
Tracks a local collector session's start time/metadata in a small state
file so `collector.py stop` can compute duration and diff git activity
since `start` even if run as two separate CLI invocations.
"""
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

STATE_PATH = os.path.join(os.path.dirname(__file__), ".session_state.json")


@dataclass
class SessionState:
    employee_id: str
    task_id: str | None
    tool: str
    repo_path: str
    started_at: str
    backend_session_id: str | None = None


def save_state(state: SessionState, path: str = STATE_PATH) -> None:
    with open(path, "w") as f:
        json.dump(asdict(state), f)


def load_state(path: str = STATE_PATH) -> SessionState | None:
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    return SessionState(**data)


def clear_state(path: str = STATE_PATH) -> None:
    if os.path.exists(path):
        os.remove(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
