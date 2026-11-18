0) used volume instead of file path so that it behaves same on arch and on windows
1) in docker compose, auth is off so remember to turn it on when deploying
2) currently using influxdb:3-core so pin specific verison to avoid suprise upgrades
3) run the docker compose file via commande: "docker compose up -d"
4)``
