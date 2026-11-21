import logging
import time
from datetime import datetime, timezone
from influxdb_client_3 import InfluxDBClient3, Point
from backend.schemas import Telemetry
from typing import List

logger=logging.getLogger(__name__)
def rt_data_insertion(data: List[Telemetry],client: InfluxDBClient3) -> None:


    points = []

    for record in data:

        point = (
            Point("vehicle_telemetry")
            .tag("vehicle_id", record.vehicle_id)
            .field("route_id", record.route_id)
            .field("lat", record.lat)
            .field("lon", record.lon)
            .field("speed", record.speed)
            .time(datetime.now(timezone.utc))
        )

        points.append(point)
    if not points:
        logger.warning("empty batch received")
        return
    start=time.perf_counter()
    try:
        client.write(record=points)

    except Exception:
        logger.exception("influx write failed for %d points", len(points))
        raise
    ms= (time.perf_counter()-start)*1000
    logger.info("wrote %d points in %.0f ms", len(points), ms)


def latest_data(client:InfluxDBClient3):
    table=client.query(
        """ SELECT DISTINCT ON(vehicle_id) vehicle_id,route_id,lat,lon,speed,time
        FROM vehicle_telemetry WHERE time >= now()-Interval '5 minutes'
        ORDER BY vehicle_id,time DESC""" ,

        language="sql",

    )

    return table.to_pylist()

def get_by_vehicle_id(client:InfluxDBClient3,vehicle_id:str):
    table=client.query(
        """ SELECT vehicle_id,route_id,lat,lon,speed,time
        FROM vehicle_telemetry
        WHERE vehicle_id=$vehicle_id
        ORDER BY time DESC LIMIT 1""",
        language="sql",
        query_parameters={"vehicle_id":vehicle_id},
    )
    rows=table.to_pylist()
    if not rows:
        logger.warning("no data found for vehicle %s", vehicle_id)
    return rows

def get_by_time(vehicle_id:str,start:datetime,end:datetime,client:InfluxDBClient3):
    table=client.query(
               """SELECT vehicle_id,route_id,lat,lon,speed,time
                FROM vehicle_telemetry
                WHERE vehicle_id=$vehicle_id AND
                time BETWEEN $start AND $end
                ORDER BY time""",
                language="sql",
                query_parameters={"vehicle_id":vehicle_id,"start":start.isoformat(),"end":end.isoformat()},
                )
    rows = table.to_pylist()
    logger.debug("readings for %s between %s and %s: %d rows", vehicle_id, start, end, len(rows))
    return rows

# AND time BETWEEN CAST($start AS TIMESTAMP) AND CAST($end AS TIMESTAMP)




    


    