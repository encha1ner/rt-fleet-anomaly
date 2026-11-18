1) Install
    ```Git from git-scm.com
    Python 3.11+ from python.org, ticking “Add python.exe to PATH” in the installer
    Docker Desktop (enable the WSL2 backend when prompted, restart if asked)
2) Clone repo
3) open docker wait until its running then -
    ```docker compose up -d
    curl.exe http://localhost:8181/health
4) set up python venv -
    ```python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
5) If PowerShell blocks activation, run this once and retry:
    ```Set-ExecutionPolicy -Scope CurrentUser RemoteSigned```
6) run test: ```python scripts/hello_influx.py``` 
