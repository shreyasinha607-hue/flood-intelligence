from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.connection import Base

# --- STAGE 1: WATCH THE HILLS ---

class Catchment(Base):
    __tablename__ = "catchments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    region = Column(String(100), nullable=False)
    downstream_river_reach = Column(String(100), nullable=False)
    critical_rainfall_threshold_mm = Column(Float, default=50.0)

    triggers = relationship("TriggerEvent", back_populates="catchment")


class TriggerEvent(Base):
    __tablename__ = "trigger_events"

    id = Column(Integer, primary_key=True, index=True)
    catchment_id = Column(Integer, ForeignKey("catchments.id"), nullable=False)
    gpm_rainfall_mm = Column(Float, nullable=False)
    soil_moisture_index = Column(Float, nullable=False)
    estimated_time_to_plains_hr = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    catchment = relationship("Catchment", back_populates="triggers")


# --- STAGE 2: PREDICT THE PLAINS ---

class RiverGauge(Base):
    __tablename__ = "river_gauges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    river = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    warning_level = Column(Float, nullable=False)
    danger_level = Column(Float, nullable=False)

    forecasts = relationship("RiverForecast", back_populates="gauge")


class RiverForecast(Base):
    __tablename__ = "river_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    gauge_id = Column(Integer, ForeignKey("river_gauges.id"), nullable=False)
    lead_time_hours = Column(Integer, nullable=False)
    forecasted_water_level = Column(Float, nullable=False)
    model_version = Column(String(50), default="v1_baseline_linear")
    timestamp = Column(DateTime, default=datetime.utcnow)

    gauge = relationship("RiverGauge", back_populates="forecasts")


class RoadSegment(Base):
    __tablename__ = "road_segments"

    id = Column(Integer, primary_key=True, index=True)
    road_name = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    is_submerged = Column(Boolean, default=False)
    submerged_depth_m = Column(Float, default=0.0)


# --- STAGE 3: HELP THE PEOPLE ---

class Village(Base):
    __tablename__ = "villages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    population = Column(Integer, nullable=False)
    is_char = Column(Boolean, default=False)
    accessibility_score = Column(Integer, nullable=False)
    primary_language = Column(String(20), default="Assamese")

    flood_extents = relationship("VillageFloodExtent", back_populates="village")
    dispatches = relationship("DispatchPlan", back_populates="village")


class VillageFloodExtent(Base):
    __tablename__ = "village_flood_extents"

    id = Column(Integer, primary_key=True, index=True)
    village_id = Column(Integer, ForeignKey("villages.id"), nullable=False)
    lead_time_hours = Column(Integer, nullable=False)
    estimated_depth_m = Column(Float, nullable=False)
    inundated_area_sq_km = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    village = relationship("Village", back_populates="flood_extents")


class ReliefResource(Base):
    __tablename__ = "relief_resources"

    id = Column(Integer, primary_key=True, index=True)
    district = Column(String(100), nullable=False)
    boats_available = Column(Integer, default=0)
    medical_teams_available = Column(Integer, default=0)
    food_kits_stock = Column(Integer, default=0)
    medical_kits_stock = Column(Integer, default=0)


class DispatchPlan(Base):
    __tablename__ = "dispatch_plans"

    id = Column(Integer, primary_key=True, index=True)
    village_id = Column(Integer, ForeignKey("villages.id"), nullable=False)
    risk_score = Column(Float, nullable=False)
    rank_priority = Column(Integer, nullable=False)
    access_profile = Column(String(50), nullable=False)
    recommended_kit_type = Column(String(100), nullable=False)
    allocated_boats = Column(Integer, default=0)
    allocated_medical_teams = Column(Integer, default=0)
    status = Column(String(50), default="PENDING")
    timestamp = Column(DateTime, default=datetime.utcnow)

    village = relationship("Village", back_populates="dispatches")


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    village_id = Column(Integer, ForeignKey("villages.id"), nullable=False)
    language = Column(String(20), nullable=False)
    channel = Column(String(20), nullable=False)
    message_body = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)