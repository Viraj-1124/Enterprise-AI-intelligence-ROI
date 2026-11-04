"""Small plugin registry for organization-specific evaluation metrics."""
from collections.abc import Callable
from typing import Any

Metric = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


class MetricRegistry:
    def __init__(self) -> None:
        self._metrics: dict[str, Metric] = {}

    def register(self, name: str, metric: Metric) -> None:
        if not name or name in self._metrics:
            raise ValueError(f"Metric name is empty or already registered: {name}")
        self._metrics[name] = metric

    def evaluate(self, case: dict[str, Any], transcript: dict[str, Any]) -> dict[str, Any]:
        return {name: metric(case, transcript) for name, metric in self._metrics.items()}
