from sqlalchemy import Column, Integer, Float, DateTime, String
from sqlalchemy.sql import func

from app.database.connection import Base


class Rainfall(Base):
    __tablename__ = "rainfall"

    id = Column(Integer, primary_key=True, index=True)

    location = Column(String(150), nullable=False)
    district = Column(String(100), nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    rainfall_mm = Column(Float, nullable=False)

    timestamp = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )