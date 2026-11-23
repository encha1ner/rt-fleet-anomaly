import logging

from fastapi import FastAPI

from backend.router import telemetry_router, anomaly_router,dashboard_router

# Configure logging once for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Real-Time Fleet Monitoring API",
    description="API for vehicle telemetry and anomaly monitoring",
    version="1.0.0"
)

# Register routers
app.include_router(telemetry_router.router)
app.include_router(anomaly_router.router)
app.include_router(dashboard_router.router)


@app.get("/")
def home():
    return {
        "message": "Fleet Monitoring API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
