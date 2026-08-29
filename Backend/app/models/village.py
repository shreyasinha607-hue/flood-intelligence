from sqlalchemy import Column, Integer, String, Float, Boolean

from app.database.connection import Base


class Village(Base):
    __tablename__ = "villages"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)
    district = Column(String(100), nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    population = Column(Integer, nullable=False, default=0)

    is_char = Column(Boolean, nullable=False, default=False)

    # 0 = extremely difficult to access
    # 100 = very easy to access
    accessibility_score = Column(Float, nullable=False, default=50)