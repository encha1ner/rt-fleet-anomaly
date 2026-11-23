import logging

from fastapi import APIRouter, Depends
from influxdb_client_3 import InfluxDBClient3

from backend.database import get_client
import backend.services as bk
from backend.schemas import AnomalyBatch

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/anomalies",
    tags=["Anomalies"]
)


# POST: Receive and store anomaly events
@router.post("")
def add_anomalies(
    data: AnomalyBatch,
    client: InfluxDBClient3 = Depends(get_client)
):
    return bk.anomaly_insertion(data.anomalies, client)


# GET: Get currently active anomaly alerts
@router.get("/active")
def get_active_anomalies(
    client: InfluxDBClient3 = Depends(get_client)
):
    return bk.anomalies_active(client)


# GET: Get active anomalies by type
@router.get("/type/{anomaly_type}/active")
def get_anomalies_by_type(
    anomaly_type: str,
    client: InfluxDBClient3 = Depends(get_client)
):
    return bk.anomalies_flag(anomaly_type, client)
