from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analytics.roi_engine import calculate_aggregate_roi, TaskROIResult
from app.database.session import get_db
from app.models.models import ROIMetric, Task
from app.schemas.schemas import ROIOut

router = APIRouter(prefix="/api", tags=["roi"])


@router.get("/tasks/{task_id}/roi", response_model=ROIOut)
def get_task_roi(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    roi = db.query(ROIMetric).filter(ROIMetric.task_id == task_id).first()
    if not roi:
        raise HTTPException(status_code=404, detail="ROI not yet calculated for this task")
    return ROIOut(
        task_id=task_id,
        time_saved_minutes=roi.time_saved_minutes,
        time_saved_percentage=roi.time_saved_percentage,
        estimated_labor_value=roi.estimated_labor_value,
        ai_cost=roi.ai_cost,
        net_value=roi.net_value,
        roi_percentage=roi.roi_percentage,
        roi_multiple=roi.roi_multiple,
        calculation_status=roi.calculation_status.value,
    )


@router.get("/dashboard/roi")
def get_dashboard_roi(db: Session = Depends(get_db)):
    metrics = db.query(ROIMetric).all()
    task_results = [
        TaskROIResult(
            time_saved_minutes=m.time_saved_minutes,
            time_saved_percentage=m.time_saved_percentage,
            estimated_labor_value=m.estimated_labor_value,
            ai_cost=m.ai_cost,
            net_value=m.net_value,
            roi_percentage=m.roi_percentage,
            roi_multiple=m.roi_multiple,
            calculation_status=m.calculation_status.value,
        )
        for m in metrics
    ]
    agg = calculate_aggregate_roi(task_results)
    return {
        "total_estimated_value": agg.total_estimated_value,
        "total_ai_cost": agg.total_ai_cost if agg.total_ai_cost is not None else "unavailable",
        "aggregate_net_value": agg.aggregate_net_value if agg.aggregate_net_value is not None else "N/A",
        "aggregate_roi_percentage": agg.aggregate_roi_percentage if agg.aggregate_roi_percentage is not None else "N/A",
        "tasks_with_cost_data": agg.tasks_with_cost_data,
        "tasks_missing_cost_data": agg.tasks_missing_cost_data,
    }
