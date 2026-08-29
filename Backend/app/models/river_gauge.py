from sqlalchemy import Column, Integer, String, Float

from app.database.connection import Base


class RiverGauge(Base):
    __tablename__ = "river_gauges"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)
    river = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)