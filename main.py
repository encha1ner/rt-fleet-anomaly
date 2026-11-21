import logging
from typing import List
# from fastapi.middleware.cors import CORSMiddleware
from logging.handlers import RotatingFileHandler
from influxdb_client_3 import InfluxDBClient3
from fastapi import Depends, FastAPI
from datetime import datetime
from backend.database import get_client
from backend.schemas import Telemetry 
import backend.services as bk
from backend.exceptions import AppException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        RotatingFileHandler("app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/telemetry")
def add_telemetry(data:List[Telemetry],client:InfluxDBClient3=Depends(get_client)):
    bk.rt_data_insertion(data,client)
    return {"saved":len(data)}


@app.get("search/{vehicle_id}/latest")
def latest_one(vehicle_id:str,client:InfluxDBClient3=Depends(get_client)):
    rows=bk.get_by_vehicle_id(vehicle_id,client)
    if not rows:
        AppException.vehicle_not_found()
    return rows[0]


@app.get("/search/{vehicle_id}/readings")
def readings(
    vehicle_id: str,
    start: datetime,
    end: datetime,
    client: InfluxDBClient3 = Depends(get_client),
):
    if start >= end:
        AppException.time_valid()
    return bk.get_by_time(client, vehicle_id.upper(), start, end)

@app.get("/health")
def health(client: InfluxDBClient3 = Depends(get_client)):
    try:
        client.query("SELECT 1", language="sql")
    except Exception:
        logger.exception("health check failed")
        AppException.server_error()
    return {"status": "ok"}
