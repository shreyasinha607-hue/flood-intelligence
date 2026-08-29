from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database.connection import Base


class RiverReading(Base):
    __tablename__ = "river_readings"

    id = Column(Integer, primary_key=True, index=True)

    gauge_id = Column(
        Integer,
        ForeignKey("river_gauges.id"),
        nullable=False
    )

    water_level = Column(Float, nullable=False)
    warning_level = Column(Float, nullable=False)
    danger_level = Column(Float, nullable=False)

    timestamp = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )