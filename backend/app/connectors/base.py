"""
Common connector interface.

A connector's job is to legitimately fetch data it actually has access to
(a documented API, a configured credential) and normalize it into the
common event schema. If a connector has no legitimate way to get the data
it is asked for, it MUST say so via `is_available()` / the `reason` field
rather than fabricating anything.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectorStatus:
    available: bool
    reason: str = ""


@dataclass
class NormalizedEvent:
    employee_id: str | None
    task_id: str | None
    timestamp: str
    event_type: str
    source: str
    tool: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    name: str = "base"

    @abstractmethod
    def is_available(self) -> ConnectorStatus:
        """Return whether this connector has a legitimate, configured data source."""
        raise NotImplementedError

    @abstractmethod
    def collect(self) -> list[dict]:
        """Fetch raw data from the provider. Only called if is_available() is True."""
        raise NotImplementedError

    @abstractmethod
    def normalize(self, data: dict) -> NormalizedEvent:
        """Convert one raw provider record into the common event schema."""
        raise NotImplementedError
