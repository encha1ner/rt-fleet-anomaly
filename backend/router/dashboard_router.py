import logging
from datetime import datetime
from fastapi import APIRouter, Depends,HTTPException
from influxdb_client_3 import InfluxDBClient3
from backend.database import get_client
import backend.services as bk
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("")
def kpi(client:InfluxDBClient3=Depends(get_client)):
    return bk.dashboard_summary


# GET: Download vehicle history as CSV
@router.get("/vehicle/{vehicle_id}/history/export")
def export_vehicle_history(
    vehicle_id: str,
    start: datetime,
    end: datetime,
    client: InfluxDBClient3 = Depends(get_client)
):
    csv_data = bk.get_vehicle_history(
        vehicle_id, start, end, client
    )

    if csv_data is None:
        raise HTTPException(
            status_code=404,
            detail="No vehicle history found"
        )

    filename = f"{vehicle_id}_history.csv"

    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
