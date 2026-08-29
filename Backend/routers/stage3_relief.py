from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.ifewras_models import Village, VillageFloodExtent, ReliefResource, DispatchPlan, AlertLog

router = APIRouter(prefix="/stage3", tags=["Stage 3: Help the People"])

def generate_multilingual_alert(village_name: str, risk_level: str, language: str) -> str:
    if language == "Bodo":
        return f"सावधान! {village_name} गामिआव दैबानाव {risk_level} खैफोद दं। सांग्रां था।"
    elif language == "Assamese":
        return f"সতর্কতা! {village_name} গাঁৱত বানপানীৰ {risk_level} বিপদাশংকা আছে। সুৰক্ষিত স্থানলৈ যাওঁক।"
    return f"ALERT! {village_name} is under {risk_level} flood risk. Move to higher ground."

@router.post("/run-allocation-engine/{district}")
def run_risk_and_allocation(district: str, db: Session = Depends(get_db)):
    villages = db.query(Village).filter(Village.district == district).all()
    resource = db.query(ReliefResource).filter(ReliefResource.district == district).first()

    if not villages:
        raise HTTPException(status_code=404, detail="No villages found in district")

    evaluated_villages = []

    for v in villages:
        extent = db.query(VillageFloodExtent).filter(
            VillageFloodExtent.village_id == v.id
        ).order_by(VillageFloodExtent.timestamp.desc()).first()

        depth = extent.estimated_depth_m if extent else 0.0

        access_difficulty = 10 - v.accessibility_score
        char_factor = 20 if v.is_char else 0
        risk_score = round(min(100.0, (depth * 25) + (v.population / 200) + (access_difficulty * 3) + char_factor), 2)

        if v.is_char or depth > 2.0:
            access_profile = "BOAT_ONLY"
        elif depth > 3.5:
            access_profile = "HELICOPTER_ONLY"
        else:
            access_profile = "ROAD_CONNECTED"

        if access_profile in ["BOAT_ONLY", "HELICOPTER_ONLY"] and depth > 1.5:
            kit_type = "Medical + Boat-Deployable Emergency Kits"
        else:
            kit_type = "Dry Ration & Clean Water Kits"

        evaluated_villages.append({
            "village_id": v.id,
            "village_name": v.name,
            "risk_score": risk_score,
            "access_profile": access_profile,
            "kit_type": kit_type,
            "is_char": v.is_char,
            "language": v.primary_language
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
            "allocated_medical": assigned_med
        })

    db.commit()

    return {
        "district": district,
        "processed_count": len(dispatch_results),
        "dispatch_plan": dispatch_results
    }