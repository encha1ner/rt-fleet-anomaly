from fastapi import APIRouter,Depends
from typing import List
from influxdb_client_3 import InfluxDBClient3
from backend.database import get_client
import backend.services as bk
from backend.schemas import Telemetry
from backend.exceptions import AppException
import logging



logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/telemetry",
    tags=["Telemetary"]
)

@router.post('/insertion')
def add_telemetry(data:List[Telemetry],client:InfluxDBClient3=Depends(get_client)):
    bk.rt_data_insertion(data,client)
    return {"saved":len(data)}


@router.get('/vehicle/{vehicle_id}/latest')
def latest_one(vehicle_id:str,client:InfluxDBClient3=Depends(get_client)):
    rows=bk.get_by_vehicle_id(vehicle_id,client)
    if not rows:
        AppException.vehicle_not_found()
    return rows[0]

