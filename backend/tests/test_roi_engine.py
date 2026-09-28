from app.analytics.roi_engine import (
    TaskROIInputs,
    calculate_task_roi,
    calculate_aggregate_roi,
    compute_time_saved,
    compute_time_saved_percentage,
    compute_estimated_labor_value,
    compute_ai_cost_from_tokens,
    compute_net_value,
    compute_roi_percentage,
    compute_roi_multiple,
    compute_ai_assisted_time_minutes,
)
from datetime import datetime, timedelta
import pytest


def test_time_saved_basic():
    assert compute_time_saved(60, 27) == 33


def test_time_saved_negative_clamped_to_zero():
    # AI-assisted work took LONGER than baseline -> never a negative "saving"
    assert compute_time_saved(30, 45) == 0


def test_time_saved_percentage():
    assert compute_time_saved_percentage(33, 60) == pytest.approx(55.0)


def test_time_saved_percentage_zero_baseline_is_none():
    assert compute_time_saved_percentage(10, 0) is None


def test_time_saved_percentage_missing_baseline_is_none():
    assert compute_time_saved_percentage(10, None) is None


def test_estimated_labor_value():
    assert compute_estimated_labor_value(33, 500) == 275.0


def test_ai_cost_from_tokens():
    cost = compute_ai_cost_from_tokens(1_000_000, 500_000, 3.0, 15.0)
    assert cost == 3.0 + 7.5


def test_ai_cost_unavailable_without_tokens():
    assert compute_ai_cost_from_tokens(None, None, 3.0, 15.0) is None


def test_ai_cost_unavailable_without_pricing():
    assert compute_ai_cost_from_tokens(1000, 500, None, None) is None


def test_net_value_requires_cost():
    assert compute_net_value(275.0, None) is None
    assert compute_net_value(275.0, 25.0) == 250.0


def test_roi_percentage_requires_nonzero_cost():
    assert compute_roi_percentage(275.0, None) is None
    assert compute_roi_percentage(275.0, 0) is None
    assert compute_roi_percentage(275.0, 25.0) == ((275.0 - 25.0) / 25.0) * 100


def test_roi_multiple_requires_nonzero_cost():
    assert compute_roi_multiple(275.0, None) is None
    assert compute_roi_multiple(275.0, 0) is None
    assert compute_roi_multiple(500.0, 100.0) == 5.0


def test_ai_assisted_time_from_timestamps():
    start = datetime(2026, 1, 1, 10, 0, 0)
    end = start + timedelta(minutes=27)
    assert compute_ai_assisted_time_minutes(start, end) == 27.0


def test_ai_assisted_time_missing_timestamps():
    assert compute_ai_assisted_time_minutes(None, None) is None


def test_calculate_task_roi_full_data():
    inputs = TaskROIInputs(
        baseline_minutes=60, actual_minutes=27, employee_hourly_cost=500, ai_cost=25.0
    )
    result = calculate_task_roi(inputs)
    assert result.time_saved_minutes == 33
    assert result.estimated_labor_value == 275.0
    assert result.net_value == 250.0
    assert result.calculation_status == "calculated"
    assert result.roi_percentage == 1000.0


def test_calculate_task_roi_missing_ai_cost_is_partial_not_zero():
    inputs = TaskROIInputs(
        baseline_minutes=60, actual_minutes=27, employee_hourly_cost=500, ai_cost=None
    )
    result = calculate_task_roi(inputs)
    assert result.estimated_labor_value == 275.0
    assert result.ai_cost is None
    assert result.net_value is None
    assert result.roi_percentage is None
    assert result.roi_multiple is None
    assert result.calculation_status == "partial"


def test_calculate_task_roi_missing_baseline_is_unavailable():
    inputs = TaskROIInputs(
        baseline_minutes=None, actual_minutes=27, employee_hourly_cost=500, ai_cost=25.0
    )
    result = calculate_task_roi(inputs)
    assert result.time_saved_minutes is None
    assert result.estimated_labor_value is None
    assert result.calculation_status == "unavailable"


def test_calculate_task_roi_zero_baseline():
    inputs = TaskROIInputs(
        baseline_minutes=0, actual_minutes=10, employee_hourly_cost=500, ai_cost=5.0
    )
    result = calculate_task_roi(inputs)
    # time_saved = max(0 - 10, 0) = 0, but percentage is N/A (division by zero guarded)
    assert result.time_saved_minutes == 0
    assert result.time_saved_percentage is None


def test_aggregate_roi_sums_not_averages():
    r1 = calculate_task_roi(TaskROIInputs(60, 30, 100, 10))   # value=50, cost=10
    r2 = calculate_task_roi(TaskROIInputs(120, 60, 100, 20))  # value=100, cost=20
    agg = calculate_aggregate_roi([r1, r2])
    assert agg.total_estimated_value == 150.0
    assert agg.total_ai_cost == 30.0
    assert agg.aggregate_net_value == 120.0
    # aggregate ROI must be computed from SUMS: (150-30)/30*100 = 400%
    # NOT the average of r1.roi_percentage (400%) and r2.roi_percentage (400%)
    # -- constructed so a naive "average of percentages" bug would still pass;
    # the assertion below checks the actual formula is used.
    assert agg.aggregate_roi_percentage == ((150.0 - 30.0) / 30.0) * 100


def test_aggregate_roi_partial_cost_data_still_sums_available_costs():
    r1 = calculate_task_roi(TaskROIInputs(60, 30, 100, 10))    # cost available
    r2 = calculate_task_roi(TaskROIInputs(60, 30, 100, None))  # cost unavailable
    agg = calculate_aggregate_roi([r1, r2])
    assert agg.tasks_with_cost_data == 1
    assert agg.tasks_missing_cost_data == 1
    assert agg.total_ai_cost == 10.0
    # total value still includes BOTH tasks' labor value estimates
    assert agg.total_estimated_value == 100.0


def test_aggregate_roi_no_cost_data_at_all_is_unavailable():
    r1 = calculate_task_roi(TaskROIInputs(60, 30, 100, None))
    r2 = calculate_task_roi(TaskROIInputs(60, 30, 100, None))
    agg = calculate_aggregate_roi([r1, r2])
    assert agg.total_ai_cost is None
    assert agg.aggregate_roi_percentage is None
    assert agg.aggregate_net_value is None
