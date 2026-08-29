from datetime import datetime

from pydantic import BaseModel, Field


class RiverReadingCreate(BaseModel):
    gauge_id: int

    water_level: float = Field(..., ge=0)
    warning_level: float = Field(..., ge=0)
    danger_level: float = Field(..., ge=0)

    timestamp: datetime | None = None


class RiverReadingResponse(RiverReadingCreate):
    id: int

    class Config:
        from_attributes = True