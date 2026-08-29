from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import Base, engine, get_db
from app.models.village import Village
from app.schemas.village import VillageCreate, VillageResponse
from sqlalchemy import text



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