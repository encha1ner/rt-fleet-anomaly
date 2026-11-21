import os
from pathlib import Path
from dotenv import load_dotenv
from influxdb_client_3 import InfluxDBClient3

ENV_PATH = Path(__file__).parent / ".env"
print("looking for .env at:", ENV_PATH, "| exists:", ENV_PATH.exists())

load_dotenv(ENV_PATH, encoding="utf-8-sig")
print("INFLUX_HOST =", os.getenv("INFLUX_HOST"))

client = InfluxDBClient3(
    host=os.environ["INFLUX_HOST"],
    database=os.environ["INFLUX_DATABASE"],
    token=os.environ["INFLUX_TOKEN"],
)


def get_client():
    return client