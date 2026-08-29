from fastapi import FastAPI

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