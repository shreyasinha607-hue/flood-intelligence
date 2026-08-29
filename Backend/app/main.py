from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import Base, engine, get_db
from app.models.village import Village
from app.schemas.village import VillageCreate, VillageResponse
from app.schemas.river_gauge import RiverGaugeCreate, RiverGaugeResponse
from app.schemas.river_reading import RiverReadingCreate, RiverReadingResponse
from sqlalchemy import text
from app.models.river_gauge import RiverGauge
from app.models.river_reading import RiverReading
from app.models.rainfall import Rainfall
from app.schemas.rainfall import RainfallCreate, RainfallResponse
from app.models.ifewras_models import Catchment, TriggerEvent, ReliefResource, DispatchPlan, AlertLog




app = FastAPI(
    title="Assam Flood Intelligence & Relief System",
    description="AI-assisted flood prediction, risk assessment and relief allocation system for Assam.",
    version="0.1.0",
)

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "message": "Assam Flood Intelligence System API is running",
        "status": "ok",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/database-test")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "test_result": value
    }

@app.post("/villages", response_model=VillageResponse)
def create_village(
    village: VillageCreate,
    db: Session = Depends(get_db)
):
    new_village = Village(
        name=village.name,
        district=village.district,
        latitude=village.latitude,
        longitude=village.longitude,
        population=village.population,
        is_char=village.is_char,
        accessibility_score=village.accessibility_score,
    )

    db.add(new_village)
    db.commit()
    db.refresh(new_village)

    return new_village

@app.get("/villages", response_model=list[VillageResponse])
def get_villages(db: Session = Depends(get_db)):
    return db.query(Village).all()

@app.get("/villages/{village_id}", response_model=VillageResponse)
def get_village(
    village_id: int,
    db: Session = Depends(get_db)
):
    village = db.query(Village).filter(
        Village.id == village_id
    ).first()

    if not village:
        raise HTTPException(
            status_code=404,
            detail="Village not found"
        )

    return village

@app.post("/river-gauges", response_model=RiverGaugeResponse)
def create_river_gauge(
    gauge: RiverGaugeCreate,
    db: Session = Depends(get_db)
):
    new_gauge = RiverGauge(
        name=gauge.name,
        river=gauge.river,
        district=gauge.district,
        latitude=gauge.latitude,
        longitude=gauge.longitude,
    )

    db.add(new_gauge)
    db.commit()
    db.refresh(new_gauge)

    return new_gauge

@app.get("/river-gauges", response_model=list[RiverGaugeResponse])
def get_river_gauges(db: Session = Depends(get_db)):
    return db.query(RiverGauge).all()

@app.get("/river-gauges/{gauge_id}", response_model=RiverGaugeResponse)
def get_river_gauge(
    gauge_id: int,
    db: Session = Depends(get_db)
):
    gauge = db.query(RiverGauge).filter(
        RiverGauge.id == gauge_id
    ).first()

    if not gauge:
        raise HTTPException(
            status_code=404,
            detail="River gauge not found"
        )

    return gauge

@app.post("/river-readings", response_model=RiverReadingResponse)
def create_river_reading(
    reading: RiverReadingCreate,
    db: Session = Depends(get_db)
):
    # Check that the gauge exists
    gauge = db.query(RiverGauge).filter(
        RiverGauge.id == reading.gauge_id
    ).first()

    if not gauge:
        raise HTTPException(
            status_code=404,
            detail="River gauge not found"
        )

    new_reading = RiverReading(
        gauge_id=reading.gauge_id,
        water_level=reading.water_level,
        warning_level=reading.warning_level,
        danger_level=reading.danger_level,
        timestamp=reading.timestamp,
    )

    db.add(new_reading)
    db.commit()
    db.refresh(new_reading)

    return new_reading
@app.get("/river-readings", response_model=list[RiverReadingResponse])
def get_river_readings(db: Session = Depends(get_db)):
    return db.query(RiverReading).order_by(
        RiverReading.timestamp.desc()
    ).all()

@app.get("/river-gauges/{gauge_id}/status")
def get_river_status(
    gauge_id: int,
    db: Session = Depends(get_db)
):
    gauge = db.query(RiverGauge).filter(
        RiverGauge.id == gauge_id
    ).first()

    if not gauge:
        raise HTTPException(
            status_code=404,
            detail="River gauge not found"
        )

    latest_reading = db.query(RiverReading).filter(
        RiverReading.gauge_id == gauge_id
    ).order_by(
        RiverReading.timestamp.desc()
    ).first()

    if not latest_reading:
        raise HTTPException(
            status_code=404,
            detail="No river readings available for this gauge"
        )

    water_level = latest_reading.water_level
    warning_level = latest_reading.warning_level
    danger_level = latest_reading.danger_level

    if water_level >= danger_level:
        status = "DANGER"
    elif water_level >= warning_level:
        status = "WARNING"
    else:
        status = "NORMAL"

    percentage = (water_level / danger_level) * 100

    return {
        "gauge_id": gauge.id,
        "gauge_name": gauge.name,
        "river": gauge.river,
        "district": gauge.district,
        "water_level": water_level,
        "warning_level": warning_level,
        "danger_level": danger_level,
        "danger_level_percentage": round(percentage, 2),
        "status": status,
        "timestamp": latest_reading.timestamp
    }

@app.get("/river-gauges/{gauge_id}/trend")
def get_river_trend(
    gauge_id: int,
    db: Session = Depends(get_db)
):
    gauge = db.query(RiverGauge).filter(
        RiverGauge.id == gauge_id
    ).first()

    if not gauge:
        raise HTTPException(
            status_code=404,
            detail="River gauge not found"
        )

    readings = db.query(RiverReading).filter(
        RiverReading.gauge_id == gauge_id
    ).order_by(
        RiverReading.timestamp.desc()
    ).limit(2).all()
    # Get the latest rainfall record
    latest_rainfall = db.query(Rainfall).order_by(
        Rainfall.timestamp.desc()
    ).first()

    rainfall_mm = 0

    if latest_rainfall:
        rainfall_mm = latest_rainfall.rainfall_mm

    if len(readings) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least two readings are required to calculate river trend"
        )

    latest = readings[0]
    previous = readings[1]

    time_difference = (
        latest.timestamp - previous.timestamp
    ).total_seconds() / 3600

    if time_difference <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid reading timestamps"
        )

    level_difference = (
        latest.water_level - previous.water_level
    )

    rise_rate = level_difference / time_difference

    if rise_rate > 0:
        trend = "RISING"
    elif rise_rate < 0:
        trend = "FALLING"
    else:
        trend = "STABLE"

    return {
        "gauge_id": gauge.id,
        "gauge_name": gauge.name,
        "river": gauge.river,
        "latest_water_level": latest.water_level,
        "previous_water_level": previous.water_level,
        "rise_rate_meters_per_hour": round(rise_rate, 3),
        "trend": trend,
        "latest_timestamp": latest.timestamp,
        "previous_timestamp": previous.timestamp
    }

@app.post("/rainfall", response_model=RainfallResponse)
def create_rainfall(
    rainfall: RainfallCreate,
    db: Session = Depends(get_db)
):
    new_rainfall = Rainfall(
        location=rainfall.location,
        district=rainfall.district,
        latitude=rainfall.latitude,
        longitude=rainfall.longitude,
        rainfall_mm=rainfall.rainfall_mm,
        timestamp=rainfall.timestamp,
    )

    db.add(new_rainfall)
    db.commit()
    db.refresh(new_rainfall)

    return new_rainfall

@app.get("/rainfall", response_model=list[RainfallResponse])
def get_rainfall(db: Session = Depends(get_db)):
    return db.query(Rainfall).order_by(
        Rainfall.timestamp.desc()
    ).all()

@app.get("/flood-risk/{gauge_id}")
def get_flood_risk(
    gauge_id: int,
    db: Session = Depends(get_db)
):
    # 1. Find the river gauge
    gauge = db.query(RiverGauge).filter(
        RiverGauge.id == gauge_id
    ).first()

    if not gauge:
        raise HTTPException(
            status_code=404,
            detail="River gauge not found"
        )

    # 2. Get latest river reading
    latest_reading = db.query(RiverReading).filter(
        RiverReading.gauge_id == gauge_id
    ).order_by(
        RiverReading.timestamp.desc()
    ).first()

    if not latest_reading:
        raise HTTPException(
            status_code=404,
            detail="No river readings available"
        )

    # 3. Get latest rainfall record
    latest_rainfall = db.query(Rainfall).order_by(
        Rainfall.timestamp.desc()
    ).first()

    # 4. Calculate river level percentage
    water_level = latest_reading.water_level
    warning_level = latest_reading.warning_level
    danger_level = latest_reading.danger_level

    danger_percentage = (
        water_level / danger_level
    ) * 100

    # 5. Determine river status
    if water_level >= danger_level:
        river_status = "DANGER"
    elif water_level >= warning_level:
        river_status = "WARNING"
    else:
        river_status = "NORMAL"

    # 6. Calculate rainfall contribution
    rainfall_mm = 0

    if latest_rainfall:
        rainfall_mm = latest_rainfall.rainfall_mm

    # 7. Basic risk scoring
    risk_score = 0

    # River level
    if water_level >= danger_level:
        risk_score += 60
    elif water_level >= warning_level:
        risk_score += 40
    else:
        risk_score += 20

    # Rainfall
    if rainfall_mm >= 100:
        risk_score += 30
    elif rainfall_mm >= 50:
        risk_score += 20
    elif rainfall_mm >= 25:
        risk_score += 10

    # 8. Determine overall risk
    if risk_score >= 80:
        risk_level = "CRITICAL"
    elif risk_score >= 60:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    return {
        "gauge_id": gauge.id,
        "gauge_name": gauge.name,
        "river": gauge.river,
        "district": gauge.district,

        "water_level": water_level,
        "warning_level": warning_level,
        "danger_level": danger_level,
        "danger_level_percentage": round(
            danger_percentage,
            2
        ),

        "river_status": river_status,

        "latest_rainfall_mm": rainfall_mm,

        "risk_score": risk_score,
        "risk_level": risk_level
    }

@app.get("/prediction/{gauge_id}")
def get_prediction(
    gauge_id: int,
    db: Session = Depends(get_db)
):
    # Find the gauge
    gauge = db.query(RiverGauge).filter(
        RiverGauge.id == gauge_id
    ).first()

    if not gauge:
        raise HTTPException(
            status_code=404,
            detail="River gauge not found"
        )

    # Get the latest two readings
    # Get the latest two readings
    readings = db.query(RiverReading).filter(
        RiverReading.gauge_id == gauge_id
    ).order_by(
    RiverReading.timestamp.desc()
    ).limit(2).all()

# Get the latest rainfall record
    latest_rainfall = db.query(Rainfall).order_by(
    Rainfall.timestamp.desc()
    ).first()

    rainfall_mm = 0

    if latest_rainfall:
        rainfall_mm = latest_rainfall.rainfall_mm

    if len(readings) < 2:
        raise HTTPException(
            status_code=404,
            detail="Not enough river readings for prediction"
        )
    latest = readings[0]
    previous = readings[1]

    # Calculate time difference in hours
    time_difference = (
        latest.timestamp - previous.timestamp
    ).total_seconds() / 3600

    if time_difference <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid reading timestamps"
        )

    # Calculate rate of change
    rise_rate = (
        latest.water_level - previous.water_level
    ) / time_difference

    # Baseline projections
    prediction_24h = (
        latest.water_level + rise_rate * 24
    )

    prediction_48h = (
        latest.water_level + rise_rate * 48
    )

    prediction_72h = (
        latest.water_level + rise_rate * 72
    )

    # Determine warning status
    danger_level = latest.danger_level

    if prediction_24h >= danger_level:
        prediction_status = "DANGER EXPECTED WITHIN 24 HOURS"
    elif prediction_48h >= danger_level:
        prediction_status = "DANGER EXPECTED WITHIN 48 HOURS"
    elif prediction_72h >= danger_level:
        prediction_status = "DANGER EXPECTED WITHIN 72 HOURS"
    else:
        prediction_status = "DANGER NOT EXPECTED"

    return {
    "gauge_id": gauge.id,
    "gauge_name": gauge.name,
    "river": gauge.river,
    "district": gauge.district,

    "current_water_level": latest.water_level,
    "previous_water_level": previous.water_level,

    "latest_rainfall_mm": rainfall_mm,

    "rise_rate_m_per_hour": round(
        rise_rate,
        4
    ),

    "prediction_24h": round(
        prediction_24h,
        2
    ),

    "prediction_48h": round(
        prediction_48h,
        2
    ),

    "prediction_72h": round(
        prediction_72h,
        2
    ),

    "warning_level": latest.warning_level,
    "danger_level": danger_level,

    "prediction_status": prediction_status,

    "model_type": "baseline_linear_forecast"
}
# ==========================================
# NEW PRD ENDPOINTS (Stage 1 & Stage 3 Additions)
# ==========================================

@app.post("/catchments/trigger-check/{catchment_id}")
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


def generate_multilingual_alert(village_name: str, risk_level: str, language: str) -> str:
    if language == "Bodo":
        return f"सावधान! {village_name} गामिआव दैबानाव {risk_level} खैफोद दं। सांग्रां था।"
    elif language == "Assamese":
        return f"সতৰ্কতা! {village_name} গাঁৱত বানপানীৰ {risk_level} বিপদাশংকা আছে। সুৰক্ষিত স্থানলৈ যাওঁক।"
    return f"ALERT! {village_name} is under {risk_level} flood risk. Move to higher ground."


@app.post("/relief/run-allocation/{district}")
def run_district_relief_allocation(district: str, db: Session = Depends(get_db)):
    villages = db.query(Village).filter(Village.district == district).all()
    resource = db.query(ReliefResource).filter(ReliefResource.district == district).first()

    if not villages:
        raise HTTPException(status_code=404, detail="No villages found in this district")

    evaluated_villages = []

    for v in villages:
        latest_rainfall = db.query(Rainfall).filter(
            Rainfall.district == district
        ).order_by(Rainfall.timestamp.desc()).first()
        
        rainfall_mm = latest_rainfall.rainfall_mm if latest_rainfall else 0.0

        access_difficulty = 10 - v.accessibility_score
        char_factor = 20 if v.is_char else 0
        risk_score = round(min(100.0, (rainfall_mm * 0.5) + (v.population / 200) + (access_difficulty * 3) + char_factor), 2)

        if v.is_char or risk_score > 70:
            access_profile = "BOAT_ONLY"
        elif risk_score > 90:
            access_profile = "HELICOPTER_ONLY"
        else:
            access_profile = "ROAD_CONNECTED"

        if access_profile in ["BOAT_ONLY", "HELICOPTER_ONLY"]:
            kit_type = "Medical + Boat-Deployable Emergency Kits"
        else:
            kit_type = "Dry Ration & Clean Water Kits"

        evaluated_villages.append({
            "village_id": v.id,
            "village_name": v.name,
            "risk_score": risk_score,
            "access_profile": access_profile,
            "kit_type": kit_type,
            "language": getattr(v, "primary_language", "Assamese")
        })

    evaluated_villages.sort(key=lambda x: x["risk_score"], reverse=True)

    dispatch_results = []
    avail_boats = resource.boats_available if resource else 2
    avail_medical = resource.medical_teams_available if resource else 2

    for rank, item in enumerate(evaluated_villages, start=1):
        assigned_boats = 1 if item["access_profile"] == "BOAT_ONLY" and avail_boats > 0 else 0
        assigned_med = 1 if item["risk_score"] > 60 and avail_medical > 0 else 0

        avail_boats -= assigned_boats
        avail_medical -= assigned_med

        dispatch = DispatchPlan(
            village_id=item["village_id"],
            risk_score=item["risk_score"],
            rank_priority=rank,
            access_profile=item["access_profile"],
            recommended_kit_type=item["kit_type"],
            allocated_boats=assigned_boats,
            allocated_medical_teams=assigned_med,
            status="PENDING"
        )
        db.add(dispatch)

        if item["risk_score"] >= 50.0:
            msg = generate_multilingual_alert(item["village_name"], "HIGH", item["language"])
            alert = AlertLog(
                village_id=item["village_id"],
                language=item["language"],
                channel="SMS/WhatsApp",
                message_body=msg
            )
            db.add(alert)

        dispatch_results.append({
            "rank": rank,
            "village_name": item["village_name"],
            "risk_score": item["risk_score"],
            "access_profile": item["access_profile"],
            "allocated_boats": assigned_boats,
            "allocated_medical_teams": assigned_med
        })

    db.commit()

    return {
        "district": district,
        "processed_count": len(dispatch_results),
        "dispatch_plan": dispatch_results
    }