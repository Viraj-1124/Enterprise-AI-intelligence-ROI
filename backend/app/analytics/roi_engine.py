"""
ROI Engine — pure, dependency-free functions implementing the formulas.

No result here is ever hardcoded. Every function either returns a real
computed number or an explicit `None` (surfaced to the API/UI as "N/A" /
"unavailable"). Nothing is silently estimated.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskROIInputs:
    baseline_minutes: Optional[float]      # ASSUMPTION
    actual_minutes: Optional[float]        # OBSERVED (task started/completed)
    employee_hourly_cost: Optional[float]  # ASSUMPTION
    ai_cost: Optional[float]               # CONNECTOR, or None if unavailable


@dataclass
class TaskROIResult:
    time_saved_minutes: Optional[float]
    time_saved_percentage: Optional[float]
    estimated_labor_value: Optional[float]
    ai_cost: Optional[float]
    net_value: Optional[float]
    roi_percentage: Optional[float]
    roi_multiple: Optional[float]
    calculation_status: str  # calculated | partial | unavailable


def compute_ai_assisted_time_minutes(started_at, completed_at) -> Optional[float]:
    """Formula 1: actual AI-assisted time from observed timestamps."""
    if started_at is None or completed_at is None:
        return None
    delta = (completed_at - started_at).total_seconds() / 60.0
    return max(delta, 0.0)


def compute_time_saved(baseline_minutes: Optional[float], actual_minutes: Optional[float]) -> Optional[float]:
    """Formula 2: time_saved = max(baseline - actual, 0)."""
    if baseline_minutes is None or actual_minutes is None:
        return None
    return max(baseline_minutes - actual_minutes, 0.0)


def compute_time_saved_percentage(time_saved: Optional[float], baseline_minutes: Optional[float]) -> Optional[float]:
    """Formula 3: time_saved_percentage = (time_saved / baseline) * 100."""
    if time_saved is None or not baseline_minutes:
        return None
    return (time_saved / baseline_minutes) * 100.0


def compute_estimated_labor_value(time_saved_minutes: Optional[float], hourly_cost: Optional[float]) -> Optional[float]:
    """Formula 4: estimated_labor_value = (time_saved / 60) * hourly_cost."""
    if time_saved_minutes is None or hourly_cost is None:
        return None
    return (time_saved_minutes / 60.0) * hourly_cost


def compute_ai_cost_from_tokens(
    input_tokens: Optional[int],
    output_tokens: Optional[int],
    input_price_per_million: Optional[float],
    output_price_per_million: Optional[float],
) -> Optional[float]:
    """Formula 5: only computed when real token counts AND real pricing exist."""
    if input_tokens is None or output_tokens is None:
        return None
    if input_price_per_million is None or output_price_per_million is None:
        return None
    input_cost = (input_tokens / 1_000_000) * input_price_per_million
    output_cost = (output_tokens / 1_000_000) * output_price_per_million
    return input_cost + output_cost


def compute_net_value(estimated_labor_value: Optional[float], ai_cost: Optional[float]) -> Optional[float]:
    """Formula 6: only when ai_cost is available."""
    if estimated_labor_value is None or ai_cost is None:
        return None
    return estimated_labor_value - ai_cost


def compute_roi_percentage(estimated_labor_value: Optional[float], ai_cost: Optional[float]) -> Optional[float]:
    """Formula 7: N/A if ai_cost missing or zero."""
    if estimated_labor_value is None or ai_cost is None or ai_cost == 0:
        return None
    return ((estimated_labor_value - ai_cost) / ai_cost) * 100.0


def compute_roi_multiple(estimated_labor_value: Optional[float], ai_cost: Optional[float]) -> Optional[float]:
    """Formula 8: N/A if ai_cost missing or zero."""
    if estimated_labor_value is None or ai_cost is None or ai_cost == 0:
        return None
    return estimated_labor_value / ai_cost


def calculate_task_roi(inputs: TaskROIInputs) -> TaskROIResult:
    """Runs the full formula chain for a single task and derives calculation_status."""
    time_saved = compute_time_saved(inputs.baseline_minutes, inputs.actual_minutes)
    time_saved_pct = compute_time_saved_percentage(time_saved, inputs.baseline_minutes)
    labor_value = compute_estimated_labor_value(time_saved, inputs.employee_hourly_cost)
    net_value = compute_net_value(labor_value, inputs.ai_cost)
    roi_pct = compute_roi_percentage(labor_value, inputs.ai_cost)
    roi_multiple = compute_roi_multiple(labor_value, inputs.ai_cost)

    if labor_value is not None and inputs.ai_cost is not None and net_value is not None:
        status = "calculated"
    elif labor_value is not None:
        status = "partial"
    else:
        status = "unavailable"

    return TaskROIResult(
        time_saved_minutes=time_saved,
        time_saved_percentage=time_saved_pct,
        estimated_labor_value=labor_value,
        ai_cost=inputs.ai_cost,
        net_value=net_value,
        roi_percentage=roi_pct,
        roi_multiple=roi_multiple,
        calculation_status=status,
    )


@dataclass
class AggregateROIResult:
    total_estimated_value: float
    total_ai_cost: Optional[float]
    aggregate_net_value: Optional[float]
    aggregate_roi_percentage: Optional[float]
    tasks_with_cost_data: int
    tasks_missing_cost_data: int


def calculate_aggregate_roi(task_results: list[TaskROIResult]) -> AggregateROIResult:
    """
    Section 6: aggregate ROI is computed from SUMS, never by averaging
    individual task ROI percentages.
    """
    total_value = 0.0
    total_cost = 0.0
    have_cost = 0
    missing_cost = 0

    for r in task_results:
        if r.estimated_labor_value is not None:
            total_value += r.estimated_labor_value
        if r.ai_cost is not None:
            total_cost += r.ai_cost
            have_cost += 1
        else:
            missing_cost += 1

    if have_cost == 0 or total_cost == 0:
        return AggregateROIResult(
            total_estimated_value=total_value,
            total_ai_cost=None,
            aggregate_net_value=None,
            aggregate_roi_percentage=None,
            tasks_with_cost_data=have_cost,
            tasks_missing_cost_data=missing_cost,
        )

    net_value = total_value - total_cost
    roi_pct = ((total_value - total_cost) / total_cost) * 100.0

    return AggregateROIResult(
        total_estimated_value=total_value,
        total_ai_cost=total_cost,
        aggregate_net_value=net_value,
        aggregate_roi_percentage=roi_pct,
        tasks_with_cost_data=have_cost,
        tasks_missing_cost_data=missing_cost,
    )
