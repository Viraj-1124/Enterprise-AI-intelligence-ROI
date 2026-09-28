from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import ActivityEvent, WorkSession
from app.schemas.schemas import SessionOut, SessionStartRequest

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/start", response_model=SessionOut)
def start_session(req: SessionStartRequest, db: Session = Depends(get_db)):
    session = WorkSession(
        employee_id=req.employee_id,
        task_id=req.task_id,
        tool=req.tool,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    db.add(ActivityEvent(
        employee_id=req.employee_id, task_id=req.task_id, event_type="session_started",
        source="observed", tool=req.tool, event_metadata={},
    ))
    db.commit()
    return session


@router.post("/{session_id}/stop", response_model=SessionOut)
def stop_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(WorkSession).filter(WorkSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.ended_at is not None:
        raise HTTPException(status_code=400, detail="Session already stopped")

    session.ended_at = datetime.utcnow()
    session.duration_minutes = (session.ended_at - session.started_at).total_seconds() / 60.0
    db.commit()
    db.refresh(session)

    db.add(ActivityEvent(
        employee_id=session.employee_id, task_id=session.task_id, event_type="session_ended",
        source="observed", tool=session.tool, event_metadata={"duration_minutes": session.duration_minutes},
    ))
    db.commit()
    return session


@router.get("", response_model=list[SessionOut])
def list_sessions(employee_id: str | None = None, task_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(WorkSession)
    if employee_id:
        query = query.filter(WorkSession.employee_id == employee_id)
    if task_id:
        query = query.filter(WorkSession.task_id == task_id)
    return query.order_by(WorkSession.started_at.desc()).all()
