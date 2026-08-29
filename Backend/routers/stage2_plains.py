from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.ifewras_models import RiverGauge, RiverForecast, Village, VillageFloodExtent

router = APIRouter(prefix="/stage2", tags=["Stage 2: Predict the Plains"])

@router.post("/generate-forecast/{gauge_id}")
def generate_forecast_and_extent(
    gauge_id: int, 
    current_level: float, 
    upstream_rainfall_mm: float, 
    db: Session = Depends(get_db)
):
    gauge = db.query(RiverGauge).filter(RiverGauge.id == gauge_id).first()
    if not gauge:
        raise HTTPException(status_code=404, detail="Gauge not found")

    runoff_rate = 0.02 * upstream_rainfall_mm
    forecasts = {}

    for lead_hr in [24, 48, 72]:
        proj_level = current_level + (runoff_rate * (lead_hr / 24.0))
        forecast = RiverForecast(
            gauge_id=gauge.id,
            lead_time_hours=lead_hr,
            forecasted_water_level=round(proj_level, 2)
        )
        db.add(forecast)
        forecasts[f"{lead_hr}h"] = proj_level

    db.commit()

    villages = db.query(Village).filter(Village.district == gauge.district).all()
    impacted_villages = []

    for v in villages:
        max_proj_24h = forecasts["24h"]
        if max_proj_24h > gauge.danger_level:
            depth = round((max_proj_24h - gauge.danger_level) * 1.2, 2)
            extent = VillageFloodExtent(
                village_id=v.id,
                lead_time_hours=24,
                estimated_depth_m=depth,
                inundated_area_sq_km=round(depth * 0.8, 2)
            )
            db.add(extent)
            impacted_villages.append({"village_id": v.id, "name": v.name, "estimated_depth": depth})

    db.commit()

    return {
        "gauge": gauge.name,
        "water_level_forecasts": forecasts,
        "impacted_villages_count": len(impacted_villages),
        "impacted_villages": impacted_villages
    }