from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analytics.roi_engine import compute_ai_cost_from_tokens
from app.config import get_settings
from app.database.session import get_db
from app.models.models import ActivityEvent, AgentDecision, AIUsage, DataSource, Task
from app.schemas.schemas import AIUsageEventRequest, AIUsageOut
from app.services.agent_optimizer import model_pricing
from app.services.auth import get_current_employee

router = APIRouter(prefix="/api/tasks", tags=["ai-usage"])
settings = get_settings()


@router.post("/{task_id}/ai-events", response_model=AIUsageOut)
def record_ai_event(task_id: str, req: AIUsageEventRequest, db: Session = Depends(get_db), current=Depends(get_current_employee)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current.role.value == "employee" and (current.id != task.employee_id or req.employee_id != current.id):
        raise HTTPException(status_code=403, detail="Employees can only record usage for their own tasks")
    try:
        source = DataSource(req.source)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid source value")

    total_tokens = None
    cost = None
    if req.input_tokens is not None and req.output_tokens is not None:
        total_tokens = req.input_tokens + req.output_tokens
        pricing = model_pricing(req.provider, req.model) or settings.PROVIDER_PRICING_PER_MILLION_TOKENS.get(req.provider)
        if pricing and source in (DataSource.connector, DataSource.observed):
            cost = compute_ai_cost_from_tokens(
                req.input_tokens, req.output_tokens, pricing["input"], pricing["output"]
            )

    event = AIUsage(
        employee_id=req.employee_id,
        task_id=task_id,
        provider=req.provider,
        model=req.model,
        session_id=req.session_id,
        input_tokens=req.input_tokens,
        output_tokens=req.output_tokens,
        total_tokens=total_tokens,
        cost=cost,
        source=source,
        usage_metadata=req.metadata or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    decisions = db.query(AgentDecision).filter(
        AgentDecision.task_id == task_id,
        AgentDecision.selected_provider == req.provider,
        AgentDecision.selected_model == req.model,
    ).all()
    matching_events = db.query(AIUsage).filter(
        AIUsage.task_id == task_id, AIUsage.provider == req.provider, AIUsage.model == req.model,
    ).all()
    for decision in decisions:
        if matching_events and all(e.input_tokens is not None for e in matching_events):
            decision.actual_input_tokens = sum(e.input_tokens for e in matching_events)
        if matching_events and all(e.output_tokens is not None for e in matching_events):
            decision.actual_output_tokens = sum(e.output_tokens for e in matching_events)
        if matching_events and all(e.cost is not None for e in matching_events):
            decision.actual_cost = sum(e.cost for e in matching_events)
    if decisions:
        db.commit()

    db.add(ActivityEvent(
        employee_id=req.employee_id, task_id=task_id, event_type="ai_request",
        source=source.value, tool=req.provider, event_metadata={"model": req.model},
    ))
    db.commit()

    # Recalculate ROI now that AI cost may have changed.
    from app.api.tasks import _recalculate_roi
    _recalculate_roi(db, task)

    return event


@router.get("/{task_id}/ai-events", response_model=list[AIUsageOut])
def list_ai_events(task_id: str, db: Session = Depends(get_db), current=Depends(get_current_employee)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current.role.value == "employee" and current.id != task.employee_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return db.query(AIUsage).filter(AIUsage.task_id == task_id).all()
