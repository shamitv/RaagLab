"""Container healthcheck entry point without optional HTTP/client dependencies."""
import json
import os
import sys
import time
from urllib.request import urlopen
from museforge.config import Settings


def main():
    try:
        role = sys.argv[1]
        if role == "api":
            with urlopen("http://127.0.0.1:8000/health/ready", timeout=5) as response:
                if response.status != 200:
                    raise ValueError("not ready")
        else:
            settings = Settings()
            data = json.loads(settings.health_file.read_text())
            age = time.time() - data["observed_at"]
            expected_role = "worker-mock" if role == "worker-yue2" else role
            if not data["healthy"] or data["role"] != expected_role or not 0 <= age < settings.lease_seconds:
                raise ValueError("stale or unhealthy process")
            os.kill(data["pid"], 0)
    except Exception:
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
