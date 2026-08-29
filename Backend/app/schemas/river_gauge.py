from pydantic import BaseModel, Field


class RiverGaugeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    river: str = Field(..., min_length=1, max_length=100)
    district: str = Field(..., min_length=1, max_length=100)

    latitude: float
    longitude: float


class RiverGaugeResponse(RiverGaugeCreate):
    id: int

    class Config:
        from_attributes = True