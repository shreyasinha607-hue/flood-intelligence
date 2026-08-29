from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.ifewras_models import Catchment, TriggerEvent

router = APIRouter(prefix="/stage1", tags=["Stage 1: Watch the Hills"])

@router.post("/trigger-check/{catchment_id}")
def evaluate_upstream_trigger(
    catchment_id: int, 
    gpm_rainfall_mm: float, 
    soil_moisture_index: float, 
    db: Session = Depends(get_db)
):
    catchment = db.query(Catchment).filter(Catchment.id == catchment_id).first()
    if not catchment:
        raise HTTPException(status_code=404, detail="Catchment not found")

    effective_rainfall = gpm_rainfall_mm * (1.0 + soil_moisture_index)
    is_triggered = effective_rainfall >= catchment.critical_rainfall_threshold_mm

    if is_triggered:
        confidence = min(1.0, effective_rainfall / (catchment.critical_rainfall_threshold_mm * 1.5))
        time_to_plains = max(2.0, 6.0 - (gpm_rainfall_mm / 20.0))

        trigger = TriggerEvent(
            catchment_id=catchment.id,
            gpm_rainfall_mm=gpm_rainfall_mm,
            soil_moisture_index=soil_moisture_index,
            estimated_time_to_plains_hr=round(time_to_plains, 1),
            confidence_score=round(confidence, 2)
        )
        db.add(trigger)
        db.commit()
        db.refresh(trigger)

        return {
            "status": "TRIGGERED",
            "message": f"Flash flood risk detected in {catchment.name}",
            "trigger_details": trigger
        }

    return {
        "status": "NORMAL",
        "message": "Rainfall within safe limits",
        "effective_rainfall_mm": round(effective_rainfall, 2)
    }