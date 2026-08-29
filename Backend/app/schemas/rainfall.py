from datetime import datetime

from pydantic import BaseModel, Field


class RainfallCreate(BaseModel):
    location: str = Field(..., min_length=1, max_length=150)
    district: str = Field(..., min_length=1, max_length=100)

    latitude: float
    longitude: float

    rainfall_mm: float = Field(..., ge=0)

    timestamp: datetime | None = None


class RainfallResponse(RainfallCreate):
    id: int

    class Config:
        from_attributes = True