"""
Generic normalized event format (Section 10 of the spec).
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional

SUPPORTED_EVENT_TYPES = {
    "session_started",
    "session_ended",
    "ai_request",
    "commit",
    "file_change",
    "test_run",
    "test_passed",
    "test_failed",
    "build",
    "task_started",
    "task_completed",
}


@dataclass
class NormalizedEvent:
    employee_id: Optional[str]
    task_id: Optional[str]
    timestamp: str
    event_type: str
    source: str
    tool: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.event_type not in SUPPORTED_EVENT_TYPES:
            raise ValueError(f"Unsupported event_type: {self.event_type}")

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
