from datetime import datetime, timedelta

from app.database.connection import SessionLocal
from app.models.river_gauge import RiverGauge
from app.models.river_reading import RiverReading
from app.models.rainfall import Rainfall


db = SessionLocal()


def seed_data():
    # --------------------------------------------------
    # 1. Find our existing gauge
    # --------------------------------------------------

    gauge = db.query(RiverGauge).filter(
        RiverGauge.id == 1
    ).first()

    if not gauge:
        print("Gauge with ID 1 not found.")
        return

    # --------------------------------------------------
    # 2. Create historical river readings
    # --------------------------------------------------

    water_levels = [
        102.8,
        103.0,
        103.2,
        103.4,
        103.7,
        104.0,
        104.2,
        104.5,
        104.8,
        105.0,
        105.2,
        105.4,
    ]

    start_time = datetime.now() - timedelta(
        hours=len(water_levels)
    )

    for i, level in enumerate(water_levels):

        reading_time = start_time + timedelta(hours=i)

        reading = RiverReading(
            gauge_id=gauge.id,
            water_level=level,
            warning_level=105.0,
            danger_level=106.0,
            timestamp=reading_time,
        )

        db.add(reading)

    # --------------------------------------------------
    # 3. Create historical rainfall data
    # --------------------------------------------------

    rainfall_values = [
        12.0,
        18.5,
        25.0,
        31.5,
        45.0,
        52.0,
        68.0,
        75.5,
        82.5,
        91.0,
        105.0,
        118.0,
    ]

    for i, rainfall_amount in enumerate(rainfall_values):

        rainfall_time = start_time + timedelta(hours=i)

        rainfall = Rainfall(
            location="Pasighat",
            district="East Siang",
            latitude=28.0667,
            longitude=95.3268,
            rainfall_mm=rainfall_amount,
            timestamp=rainfall_time,
        )

        db.add(rainfall)

    db.commit()

    print("✅ Test flood data created successfully!")


if __name__ == "__main__":
    try:
        seed_data()
    finally:
        db.close()