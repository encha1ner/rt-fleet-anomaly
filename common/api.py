import requests


class Api:
    """Small HTTP helper. Never crashes the caller: failures are counted and reported once."""

    def __init__(self, base_url, timeout=2.0):
        self.base = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.ok = 0
        self.failed = 0
        self._down = False

    def _call(self, method, path, **kwargs):
        try:
            r = self.session.request(method, self.base + path, timeout=self.timeout, **kwargs)
            r.raise_for_status()
        except requests.RequestException as e:
            self.failed += 1
            if not self._down:
                print(f"[api] {method} {path} failed: {e}")
                self._down = True
            return None
        self.ok += 1
        if self._down:
            print("[api] connection restored")
            self._down = False
        return r

    def post(self, path, payload):
        return self._call("POST", path, json=payload) is not None

    def get_json(self, path):
        r = self._call("GET", path)
        return r.json() if r is not None else None
