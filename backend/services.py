import logging
import time
from datetime import datetime, timezone
from influxdb_client_3 import InfluxDBClient3, Point
from backend.schemas import Telemetry,Anomaly
from typing import List
import pandas as pd


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

def get_by_vehicle_id(vehicle_id:str,client:InfluxDBClient3):
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


def anomaly_insertion(data:List[Anomaly],client:InfluxDBClient3):
    points = []
    
    for record in data:
    
            point = (
                Point("vehicle_anomalies")
                .tag("vehicle_id", record.vehicle_id)
                .field("anomaly_type", record.anomaly_type)
                .field("anomaly", record.anomaly)
                .field("score", record.score)
                .time(record.ts)
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


def anomalies_active(client:InfluxDBClient3):
    table=client.query(""" SELECT vehicle_id,anomaly_type,anomaly,score,time
            FROM (SELECT DISTINCT ON(vehicle_id) vehicle_id,anomaly_type,anomaly,score,time
                    FROM vehicle_anomalies
                    ORDER BY vehicle_id,time DESC) AS latest
                    WHERE anomaly=True
                    ORDER BY time DESC""",
                    language="sql",
    )
    return table.to_pylist()

def anomalies_flag(anomaly_type:str,client:InfluxDBClient3):
    table=client.query(
            """ SELECT vehicle_id,anomaly_type,score,time
            FROM vehicle_anomalies
            WHERE anomaly_type=$anomaly_type AND anomaly=True
            ORDER BY time DESC""",
            language="sql",
            query_parameters={"anomaly_type":anomaly_type},
        )
    rows=table.to_pylist()
    if not rows:
        logger.warning("no anomaly found for vehicle %s", anomaly_type)
    return rows
def anomaly_history(client: InfluxDBClient3):
    table = client.query("""
        SELECT vehicle_id, anomaly_type, anomaly, score, time
        FROM vehicle_anomalies
        ORDER BY time DESC
    """, language="sql")

    rows = table.to_pandas()

    if rows.empty:
        logger.warning("No anomaly history found")
        return

    rows.to_csv("anomaly_history.csv", index=False)

    return rows



def dashboard_summary(client: InfluxDBClient3):

   
    total_table = client.query("""
        SELECT COUNT(DISTINCT vehicle_id) AS total
        FROM vehicle_telemetry
    """, language="sql")

    
    active_table = client.query("""
        SELECT COUNT(DISTINCT vehicle_id) AS active
        FROM vehicle_telemetry
        WHERE time >= now() - INTERVAL '5 minutes'
    """, language="sql")

   
    anomaly_table = client.query("""
        SELECT vehicle_id, anomaly
        FROM (
            SELECT DISTINCT ON (vehicle_id)
                vehicle_id, anomaly, time
            FROM vehicle_anomalies
            ORDER BY vehicle_id, time DESC
        ) AS latest
        WHERE anomaly = TRUE
    """, language="sql")

    # Convert query results into Python lists
    total_rows = total_table.to_pylist()
    active_rows = active_table.to_pylist()
    anomaly_rows = anomaly_table.to_pylist()

    # Extract counts
    total = total_rows[0]["total"] if total_rows else 0
    active = active_rows[0]["active"] if active_rows else 0
    anomalous = len(anomaly_rows)

    # Normal vehicles = total vehicles - anomalous vehicles
    normal = total - anomalous

    return {
        "total_vehicles": total,
        "active_vehicles": active,
        "normal_vehicles": normal,
        "anomalous_vehicles": anomalous
    }

