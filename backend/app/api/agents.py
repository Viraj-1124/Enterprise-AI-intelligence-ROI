from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import AgentDecision, AIUsage, ActivityEvent, Task
from app.schemas.schemas import AgentDecisionOut, AgentOptimizeRequest, AgentResultRequest
from app.services.agent_optimizer import AGENTS, recommend

router = APIRouter(prefix="/api/agents", tags=["agent-optimization"])


def _save_recommendation(db: Session, req: AgentOptimizeRequest, task=None):
    recommendation, _ = recommend(db, req)
    decision = AgentDecision(
        task_id=req.task_id, **{k: recommendation[k] for k in (
            "task_type", "complexity", "required_quality", "selected_provider", "selected_model",
            "predicted_input_tokens", "predicted_output_tokens", "predicted_cost",
            "predicted_latency_ms", "predicted_quality", "confidence", "rationale",
        )}, verification_required=recommendation["verification_required"],
    )
    db.add(decision)
    db.flush()
    if task:
        db.add(ActivityEvent(employee_id=task.employee_id, task_id=task.id, event_type="agent_recommended",
                             source="estimated", tool=decision.selected_provider,
                             event_metadata={"decision_id": decision.id, "model": decision.selected_model,
                                             "predicted_cost": decision.predicted_cost}))
    db.commit()
    db.refresh(decision)
    return decision


@router.post("/optimize", response_model=AgentDecisionOut)
def optimize(req: AgentOptimizeRequest, db: Session = Depends(get_db)):
    task = None
    if req.task_id:
        task = db.query(Task).filter(Task.id == req.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
    return _save_recommendation(db, req, task)


@router.post("/decisions/{decision_id}/result", response_model=AgentDecisionOut)
def record_result(decision_id: str, req: AgentResultRequest, db: Session = Depends(get_db)):
    decision = db.query(AgentDecision).filter(AgentDecision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Agent decision not found")
    for field in ("actual_input_tokens", "actual_output_tokens", "actual_cost", "actual_latency_ms",
                  "actual_quality", "outcome", "verification_required", "rework_required"):
        value = getattr(req, field)
        if value is not None:
            setattr(decision, field, value)
    if decision.task_id:
        events = db.query(AIUsage).filter(AIUsage.task_id == decision.task_id,
                                          AIUsage.provider == decision.selected_provider,
                                          AIUsage.model == decision.selected_model).all()
        if events:
            if decision.actual_input_tokens is None and all(e.input_tokens is not None for e in events):
                decision.actual_input_tokens = sum(e.input_tokens for e in events)
            if decision.actual_output_tokens is None and all(e.output_tokens is not None for e in events):
                decision.actual_output_tokens = sum(e.output_tokens for e in events)
            if decision.actual_cost is None and all(e.cost is not None for e in events):
                decision.actual_cost = sum(e.cost for e in events)
    db.commit()
    db.refresh(decision)
    if decision.task_id and decision.actual_cost is not None:
        task = db.query(Task).filter(Task.id == decision.task_id).first()
        if task:
            from app.api.tasks import _recalculate_roi
            _recalculate_roi(db, task)
    return decision


@router.get("/catalog")
def catalog():
    return [{"provider": a["provider"], "model": a["model"], "quality_estimate": a["quality"],
             "input_cost_per_million": a["input"], "output_cost_per_million": a["output"],
             "estimated_latency_ms": a["latency"]} for a in AGENTS]


@router.get("/tasks/{task_id}/decision", response_model=AgentDecisionOut)
def task_decision(task_id: str, db: Session = Depends(get_db)):
    decision = db.query(AgentDecision).filter(AgentDecision.task_id == task_id).order_by(AgentDecision.created_at.desc()).first()
    if not decision:
        raise HTTPException(status_code=404, detail="No agent recommendation recorded for this task")
    return decision


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    decisions = db.query(AgentDecision).all()
    observed = [d for d in decisions if d.actual_cost is not None]
    savings = sum(max(0, d.predicted_cost - d.actual_cost) for d in observed if d.predicted_cost is not None)
    evaluated = [d for d in decisions if d.outcome is not None]
    return {"recommendations": len(decisions), "results_recorded": len(evaluated),
            "observed_decisions_with_cost": len(observed), "predicted_cost": sum(d.predicted_cost or 0 for d in decisions),
            "actual_cost": sum(d.actual_cost for d in observed), "cost_below_prediction_total": savings,
            "average_actual_quality": (sum(d.actual_quality for d in decisions if d.actual_quality is not None) /
                                       max(1, sum(d.actual_quality is not None for d in decisions))),
            "models": {f"{p}/{m}": {"recommendations": sum(d.selected_provider == p and d.selected_model == m for d in decisions),
                                    "evaluated": sum(d.selected_provider == p and d.selected_model == m and d.outcome is not None for d in decisions)}
                       for p, m in {(d.selected_provider, d.selected_model) for d in decisions}}}
