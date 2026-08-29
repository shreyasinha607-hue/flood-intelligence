from fastapi import FastAPI
from sqlalchemy import text

from app.database.connection import engine


app = FastAPI(
    title="Assam Flood Intelligence & Relief System",
    description="AI-assisted flood prediction, risk assessment and relief allocation system for Assam.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "Assam Flood Intelligence System API is running",
        "status": "ok",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/database-test")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "test_result": value
    }