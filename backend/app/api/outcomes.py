from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import ActivityEvent, Task, TaskOutcome
from app.schemas.schemas import TaskOutcomeOut, TaskOutcomeRequest

router = APIRouter(prefix="/api/tasks", tags=["outcomes"])


@router.post("/{task_id}/outcome", response_model=TaskOutcomeOut)
def record_outcome(task_id: str, req: TaskOutcomeRequest, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    outcome = db.query(TaskOutcome).filter(TaskOutcome.task_id == task_id).first()
    if outcome is None:
        outcome = TaskOutcome(task_id=task_id)
        db.add(outcome)

    outcome.files_changed = req.files_changed
    outcome.lines_added = req.lines_added
    outcome.lines_removed = req.lines_removed
    outcome.commits = req.commits
    outcome.tests_run = req.tests_run
    outcome.tests_passed = req.tests_passed
    outcome.build_passed = req.build_passed
    outcome.output_generated = req.output_generated
    outcome.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(outcome)

    db.add(ActivityEvent(
        employee_id=task.employee_id, task_id=task_id, event_type="build",
        source="observed", tool=None,
        event_metadata={"tests_run": req.tests_run, "tests_passed": req.tests_passed, "build_passed": req.build_passed},
    ))
    db.commit()
    return outcome


@router.get("/{task_id}/outcome", response_model=TaskOutcomeOut)
def get_outcome(task_id: str, db: Session = Depends(get_db)):
    outcome = db.query(TaskOutcome).filter(TaskOutcome.task_id == task_id).first()
    if not outcome:
        raise HTTPException(status_code=404, detail="No outcome recorded for this task")
    return outcome
