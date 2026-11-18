from datetime import datetime, timezone
from influxdb_client_3 import InfluxDBClient3, Point

client = InfluxDBClient3(
    host="http://localhost:8181",
    database="fleet",
    token="dev",          # ignored when auth is off
)

# write one point
point = (
    Point("vehicle_telemetry")
    .tag("vehicle_id", "bus_01")
    .field("lat", 26.8467)
    .field("lon", 80.9462)
    .field("speed", 32.5)
    .time(datetime.now(timezone.utc))
)
client.write(record=point)

# read it back
table = client.query(
    "SELECT * FROM vehicle_telemetry ORDER BY time DESC LIMIT 5",
    language="sql",
)
print(table.to_pandas())
