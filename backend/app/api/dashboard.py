from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analytics.roi_engine import calculate_aggregate_roi, TaskROIResult
from app.database.session import get_db
from app.models.models import AIUsage, Department, Employee, ROIMetric, Task, TaskStatus

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _roi_result_from_metric(m: ROIMetric) -> TaskROIResult:
    return TaskROIResult(
        time_saved_minutes=m.time_saved_minutes,
        time_saved_percentage=m.time_saved_percentage,
        estimated_labor_value=m.estimated_labor_value,
        ai_cost=m.ai_cost,
        net_value=m.net_value,
        roi_percentage=m.roi_percentage,
        roi_multiple=m.roi_multiple,
        calculation_status=m.calculation_status.value,
    )


def _na(value):
    return value if value is not None else "N/A"


@router.get("/management")
def management_dashboard(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    metrics = db.query(ROIMetric).all()
    ai_events = db.query(AIUsage).all()
    departments = db.query(Department).all()

    task_results = [_roi_result_from_metric(m) for m in metrics]
    agg = calculate_aggregate_roi(task_results)

    ai_assisted_task_ids = {e.task_id for e in ai_events if e.task_id}
    total_tasks = len(tasks)
    completed_tasks = [t for t in tasks if t.status == TaskStatus.completed]

    # AI spend: only sum costs that are actually available.
    known_costs = [e.cost for e in ai_events if e.cost is not None]
    total_ai_spend = sum(known_costs) if known_costs else None
    any_usage_recorded = len(ai_events) > 0
    unpriced_usage_exists = any(e.cost is None for e in ai_events)

    total_time_saved = sum(m.time_saved_minutes for m in metrics if m.time_saved_minutes is not None)

    provider_stats = defaultdict(lambda: {"events": 0, "total_tokens": 0, "cost": 0.0, "cost_available": False})
    for e in ai_events:
        stats = provider_stats[e.provider]
        stats["events"] += 1
        stats["total_tokens"] += e.total_tokens or 0
        if e.cost is not None:
            stats["cost"] += e.cost
            stats["cost_available"] = True

    dept_stats = []
    for dept in departments:
        dept_employee_ids = {emp.id for emp in dept.employees}
        dept_tasks = [t for t in tasks if t.employee_id in dept_employee_ids]
        dept_task_ids = {t.id for t in dept_tasks}
        dept_metrics = [m for m in metrics if m.task_id in dept_task_ids]
        dept_time_saved = sum(m.time_saved_minutes for m in dept_metrics if m.time_saved_minutes is not None)
        dept_ai_assisted = len([t for t in dept_tasks if t.id in ai_assisted_task_ids])
        dept_costs = [m.ai_cost for m in dept_metrics if m.ai_cost is not None]
        dept_stats.append({
            "department_id": dept.id,
            "department": dept.name,
            "employees": len(dept.employees),
            "tasks": len(dept_tasks),
            "ai_assisted_tasks": dept_ai_assisted,
            "ai_adoption_pct": round(dept_ai_assisted / len(dept_tasks) * 100, 1) if dept_tasks else 0,
            "time_saved_minutes": dept_time_saved,
            "ai_spend": sum(dept_costs) if dept_costs else "unavailable",
        })

    cost_per_ai_task = None
    if total_ai_spend is not None and len(ai_assisted_task_ids) > 0:
        cost_per_ai_task = total_ai_spend / len(ai_assisted_task_ids)

    return {
        "ai_spend": {
            "value": total_ai_spend,
            "source": "connector" if total_ai_spend is not None else "unavailable",
            "note": "Partial: some AI usage recorded without cost data" if unpriced_usage_exists and total_ai_spend is not None else None,
        },
        "ai_assisted_tasks": len(ai_assisted_task_ids),
        "total_tasks": total_tasks,
        "completed_tasks": len(completed_tasks),
        "time_saved_minutes": {"value": total_time_saved, "source": "observed"},
        "estimated_business_value": {"value": agg.total_estimated_value, "source": "estimated"},
        "net_estimated_value": {"value": _na(agg.aggregate_net_value), "source": "estimated" if agg.aggregate_net_value is not None else "unavailable"},
        "aggregate_roi_percentage": {"value": _na(agg.aggregate_roi_percentage), "source": "estimated" if agg.aggregate_roi_percentage is not None else "unavailable"},
        "roi_multiple": {
            "value": (agg.total_estimated_value / agg.total_ai_cost) if agg.total_ai_cost else "N/A",
        },
        "ai_adoption_pct": round(len(ai_assisted_task_ids) / total_tasks * 100, 1) if total_tasks else 0,
        "cost_per_ai_assisted_task": _na(cost_per_ai_task),
        "department_stats": dept_stats,
        "provider_stats": {
            provider: {
                "events": s["events"],
                "total_tokens": s["total_tokens"],
                "cost": s["cost"] if s["cost_available"] else "unavailable",
            }
            for provider, s in provider_stats.items()
        },
        "tasks_with_cost_data": agg.tasks_with_cost_data,
        "tasks_missing_cost_data": agg.tasks_missing_cost_data,
    }


@router.get("/department/{department_id}")
def department_dashboard(department_id: str, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    employee_ids = [e.id for e in dept.employees]
    tasks = db.query(Task).filter(Task.employee_id.in_(employee_ids)).all() if employee_ids else []
    task_ids = {t.id for t in tasks}
    metrics = db.query(ROIMetric).filter(ROIMetric.task_id.in_(task_ids)).all() if task_ids else []
    ai_events = db.query(AIUsage).filter(AIUsage.task_id.in_(task_ids)).all() if task_ids else []

    task_results = [_roi_result_from_metric(m) for m in metrics]
    agg = calculate_aggregate_roi(task_results)
    ai_assisted = len({e.task_id for e in ai_events if e.task_id})

    return {
        "department": dept.name,
        "employees": len(dept.employees),
        "tasks": len(tasks),
        "ai_assisted_tasks": ai_assisted,
        "ai_adoption_pct": round(ai_assisted / len(tasks) * 100, 1) if tasks else 0,
        "time_saved_minutes": sum(m.time_saved_minutes for m in metrics if m.time_saved_minutes is not None),
        "estimated_value": agg.total_estimated_value,
        "ai_spend": _na(agg.total_ai_cost),
        "roi_percentage": _na(agg.aggregate_roi_percentage),
    }


@router.get("/employee/{employee_id}")
def employee_dashboard(employee_id: str, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    tasks = db.query(Task).filter(Task.employee_id == employee_id).all()
    task_ids = {t.id for t in tasks}
    metrics = db.query(ROIMetric).filter(ROIMetric.task_id.in_(task_ids)).all() if task_ids else []
    ai_events = db.query(AIUsage).filter(AIUsage.task_id.in_(task_ids)).all() if task_ids else []

    task_results = [_roi_result_from_metric(m) for m in metrics]
    agg = calculate_aggregate_roi(task_results)
    ai_assisted_task_ids = {e.task_id for e in ai_events if e.task_id}

    return {
        "employee": employee.name,
        "department_id": employee.department_id,
        "tasks_completed": len([t for t in tasks if t.status == TaskStatus.completed]),
        "ai_assisted_tasks": len(ai_assisted_task_ids),
        "time_saved_minutes": sum(m.time_saved_minutes for m in metrics if m.time_saved_minutes is not None),
        "ai_usage_events": len(ai_events),
        "ai_cost": _na(agg.total_ai_cost),
        "estimated_value": agg.total_estimated_value,
        "roi_percentage": _na(agg.aggregate_roi_percentage),
    }
