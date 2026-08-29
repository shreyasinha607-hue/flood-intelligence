from pydantic import BaseModel, Field


class VillageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    district: str = Field(..., min_length=1, max_length=100)

    latitude: float
    longitude: float

    population: int = Field(..., ge=0)

    is_char: bool = False

    accessibility_score: float = Field(
        default=50,
        ge=0,
        le=100
    )


class VillageResponse(VillageCreate):
    id: int

    class Config:
        from_attributes = True