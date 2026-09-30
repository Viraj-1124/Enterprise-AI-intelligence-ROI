from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analytics.roi_engine import TaskROIInputs, calculate_task_roi, compute_ai_assisted_time_minutes
from app.database.session import get_db
from app.models.models import ActivityEvent, AgentDecision, AIUsage, Employee, ROIMetric, Task, TaskStatus, CalculationStatus
from app.schemas.schemas import TaskCompleteRequest, TaskOut, TaskStartRequest
from app.schemas.schemas import AgentOptimizeRequest
from app.api.agents import _save_recommendation
from app.services.auth import get_current_employee

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _recalculate_roi(db: Session, task: Task) -> ROIMetric:
    ai_costs = [e.cost for e in task.ai_usage_events if e.cost is not None]
    decision_costs = [d.actual_cost for d in db.query(AgentDecision).filter(AgentDecision.task_id == task.id).all()
                      if d.actual_cost is not None]
    # Usage events are the primary source; a reported agent result can fill a gap
    # when an integration has not emitted a separate usage event.
    ai_cost = sum(ai_costs) if ai_costs else (sum(decision_costs) if decision_costs else None)

    result = calculate_task_roi(
        TaskROIInputs(
            baseline_minutes=task.baseline_minutes,
            actual_minutes=task.actual_minutes,
            employee_hourly_cost=task.employee.hourly_cost if task.employee else None,
            ai_cost=ai_cost,
        )
    )

    roi = db.query(ROIMetric).filter(ROIMetric.task_id == task.id).first()
    if roi is None:
        roi = ROIMetric(task_id=task.id)
        db.add(roi)

    roi.time_saved_minutes = result.time_saved_minutes
    roi.time_saved_percentage = result.time_saved_percentage
    roi.estimated_labor_value = result.estimated_labor_value
    roi.ai_cost = result.ai_cost
    roi.net_value = result.net_value
    roi.roi_percentage = result.roi_percentage
    roi.roi_multiple = result.roi_multiple
    roi.calculation_status = CalculationStatus(result.calculation_status)
    roi.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(roi)
    return roi


@router.post("/start", response_model=TaskOut)
def start_task(req: TaskStartRequest, db: Session = Depends(get_db), current=Depends(get_current_employee)):
    if current.role.value == "employee" and current.id != req.employee_id:
        raise HTTPException(status_code=403, detail="Employees can only start tasks for themselves")
    employee = db.query(Employee).filter(Employee.id == req.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if req.baseline_minutes is not None and req.baseline_minutes < 0:
        raise HTTPException(status_code=400, detail="Invalid baseline: must be >= 0")

    task = Task(
        employee_id=req.employee_id,
        title=req.title,
        description=req.description,
        category=req.category,
        baseline_minutes=req.baseline_minutes,
        started_at=datetime.utcnow(),
        status=TaskStatus.in_progress,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    db.add(ActivityEvent(
        employee_id=req.employee_id, task_id=task.id, event_type="task_started",
        source="observed", tool=None, event_metadata={"title": req.title},
    ))
    db.commit()
    _save_recommendation(db, AgentOptimizeRequest(
        task_id=task.id, title=task.title, description=task.description, task_type=task.category,
    ), task, current.id)
    return task


@router.post("/{task_id}/complete", response_model=TaskOut)
def complete_task(task_id: str, req: TaskCompleteRequest, db: Session = Depends(get_db), current=Depends(get_current_employee)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current.role.value == "employee" and current.id != task.employee_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if task.status == TaskStatus.completed:
        raise HTTPException(status_code=400, detail="Task is already completed")
    if task.started_at is None:
        raise HTTPException(status_code=400, detail="Task was never started")

    task.completed_at = datetime.utcnow()
    task.actual_minutes = compute_ai_assisted_time_minutes(task.started_at, task.completed_at)
    task.status = TaskStatus.completed
    db.commit()
    db.refresh(task)

    db.add(ActivityEvent(
        employee_id=task.employee_id, task_id=task.id, event_type="task_completed",
        source="observed", tool=None, event_metadata={"notes": req.notes},
    ))
    db.commit()

    _recalculate_roi(db, task)
    return task


@router.get("", response_model=list[TaskOut])
def list_tasks(employee_id: str | None = None, status: str | None = None, db: Session = Depends(get_db), current=Depends(get_current_employee)):
    query = db.query(Task)
    if current.role.value == "employee":
        query = query.filter(Task.employee_id == current.id)
    if employee_id:
        query = query.filter(Task.employee_id == employee_id)
    if status:
        query = query.filter(Task.status == status)
    return query.order_by(Task.created_at.desc()).all()


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str, db: Session = Depends(get_db), current=Depends(get_current_employee)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current.role.value == "employee" and current.id != task.employee_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return task
