Phase 0 has four parts: install tools, create the repo, start InfluxDB, and run a write/read test. Your friends on Windows can follow the same steps, with the differences noted along the way.

## 1. Install the tools

**Arch (you):**
```bash
sudo pacman -S git python docker docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER   # then log out and back in
docker run --rm hello-world     # confirm Docker works
```

**Windows (friends):**
- Install Git, Python 3.11+ (tick "Add to PATH"), and Docker Desktop (it uses WSL2, so enable that when prompted).
- Use PowerShell or Git Bash for the commands below.

## 2. Create the repo

```bash
mkdir fleet-anomaly && cd fleet-anomaly
git init
mkdir simulator detector backend frontend scripts
touch README.md docker-compose.yml requirements.txt .gitignore
```

`.gitignore`:
```
.venv/
__pycache__/
.env
*.pkl
data/
```

`.gitattributes` (prevents line-ending problems between Windows and Linux):
```
* text=auto
*.sh text eol=lf
```

## 3. Start InfluxDB with Docker Compose

`docker-compose.yml`:
```yaml
services:
  influxdb:
    image: influxdb:3-core
    container_name: fleet-influx
    ports:
      - "8181:8181"
    command:
      - influxdb3
      - serve
      - --node-id=node0
      - --object-store=file
      - --data-dir=/var/lib/influxdb3
      - --without-auth        # dev only: no tokens needed
    volumes:
      - influx-data:/var/lib/influxdb3

volumes:
  influx-data:
```

Notes:
- I used a named volume instead of a folder path, so it behaves the same on Arch and Windows.
- `--without-auth` keeps phase 0 simple. By default InfluxDB 3 requires a token, so remember to turn auth on if you ever deploy this.
- Check that `influxdb:3-core` works for you. The docs say InfluxDB's `latest` tag will point to Core, so pin a specific version later to avoid surprise upgrades.

Start it and check health:
```bash
docker compose up -d
curl http://localhost:8181/health
```
On Windows PowerShell, use `curl.exe` instead of `curl`. If it responds without an error, the server is up. If something is wrong, `docker compose logs influxdb` shows why.

## 4. Python environment

`requirements.txt`:
```
influxdb3-python
pandas
```

**Arch / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
(If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.)

## 5. The write/read test

`scripts/hello_influx.py`:
```python
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
```

Run it:
```bash
python scripts/hello_influx.py
```

If you see a row for `bus_01`, Phase 0 is done. The database is created automatically on first write.

## 6. Commit and share

```bash
git add .
git commit -m "Phase 0: repo skeleton, InfluxDB compose, hello test"
git tag phase-0
```

Push to GitHub so your friends can clone it. Everyone then runs the same `docker compose up -d` and the same script.

## Common problems

- **Permission denied on Docker (Arch):** you didn't log out and back in after `usermod`.
- **Port 8181 in use:** stop whatever is using it or change the left side of the mapping (`"8182:8181"`).
- **Connection refused:** the container hasn't finished starting, so wait a few seconds and check the logs.
- **Import error on `influxdb_client_3`:** the package name is `influxdb3-python` but you import `influxdb_client_3`.

Library APIs change between versions. If the script errors, paste the error here and I'll fix it.

**Done when:** your script prints the row you just wrote. Tell me when it works and we'll move on to Phase 1, the simulator.
