"""Isolated, bounded real-service acceptance; never resets an ordinary deployment."""
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
project = "museforge-foundation-test-" + uuid.uuid4().hex[:12]
# Docker allocates an unused host port, avoiding the developer's ordinary instance.
env = dict(os.environ, APP_PORT="0")
base = ["docker", "compose", "--project-name", project, "--env-file", ".env", "--profile", "mock", "-f", "compose.yaml", "-f", "compose.test.yaml"]


def run(*args, capture=False, timeout=600):
    result = subprocess.run([*base, *args], cwd=ROOT, env=env, check=True, text=True,
                            stdout=subprocess.PIPE if capture else None, timeout=timeout)
    return result.stdout if capture else None


def inspect_boundaries():
    config = json.loads(run("config", "--format", "json", capture=True))
    services = config["services"]
    assert set(services) == {"db", "broker", "migrate", "api", "dispatcher", "worker-mock", "tests"}
    assert not services["db"].get("ports") and not services["broker"].get("ports")
    assert services["api"]["ports"][0]["host_ip"] == "127.0.0.1"
    assert services["api"]["build"]["target"] == "api"
    assert services["worker-mock"]["build"]["target"] == "mock-worker"
    assert services["api"]["volumes"][0]["read_only"]
    assert services["db"]["volumes"][0]["target"] == "/var/lib/postgresql"


def verify_worker_log_redaction():
    secret = "foundation-private-sentinel-" + uuid.uuid4().hex
    run("run", "--rm", "--no-deps", "tests", "/app/.venv/bin/python",
        "tests/integration/publish_invalid_messages.py", secret)
    expected = {"consumer_unknown_message", "consumer_unknown_task", "consumer_invalid_task", "consumer_decode_error"}
    deadline = time.monotonic() + 30
    while True:
        logs = run("logs", "--no-color", "worker-mock", capture=True, timeout=10)
        assert secret not in logs, "Worker logs exposed private message content"
        if all(code in logs for code in expected):
            break
        assert time.monotonic() < deadline, "Worker did not log all safe message diagnostics"
        time.sleep(0.25)
    run("exec", "-T", "worker-mock", "python", "-m", "museforge.healthcheck", "worker-mock")
    print("Worker malformed-message diagnostics are redacted; worker remains healthy.")


try:
    subprocess.run(["docker", "version"], check=True, timeout=30)
    subprocess.run(["docker", "compose", "version"], check=True, timeout=30)
    inspect_boundaries()
    run("build", "--no-cache", timeout=1800)
    run("up", "-d", "--wait", "--wait-timeout", "180", "api", "dispatcher", "worker-mock")
    for role in ("api", "worker-mock"):
        packages = json.loads(run("exec", "-T", role, "python", "-c",
            "import importlib.metadata as m,json; print(json.dumps(sorted(d.metadata['Name'].lower() for d in m.distributions())))", capture=True))
        assert not any(p.startswith(("torch", "transformers", "nvidia", "tensorflow", "cuda")) for p in packages), packages
        assert ("fastapi" in packages) == (role == "api")
        assert ("celery" in packages) == (role == "worker-mock")
        print(role, "packages:", packages)
    run("run", "--rm", "tests", "/app/.venv/bin/pytest", "tests/unit")
    run("run", "--rm", "tests")
    verify_worker_log_redaction()
    workspace_before = run("exec", "-T", "db", "sh", "-c", 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT id FROM workspaces"', capture=True)
    data_directory = run("exec", "-T", "db", "sh", "-c", 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SHOW data_directory"', capture=True).strip()
    assert data_directory.startswith("/var/lib/postgresql/18/"), data_directory
    run("exec", "-T", "worker-mock", "python", "-c",
        "from pathlib import Path; Path('/var/lib/museforge/artifacts/foundation-persistence.txt').write_text('foundation-persistence')")
    run("exec", "-T", "worker-mock", "python", "-c",
        "from museforge.worker.app import app; from kombu import Queue; c=app.connection_for_write(); c.connect(); q=Queue('foundation.persistence',durable=True)(c); q.declare(); c.Producer().publish({'foundation':True},exchange='',routing_key=q.name,serializer='json',delivery_mode=2,mandatory=True); c.close()")
    run("down")
    run("up", "-d", "--wait", "--wait-timeout", "180", "api", "dispatcher", "worker-mock")
    workspace_after = run("exec", "-T", "db", "sh", "-c", 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT id FROM workspaces"', capture=True)
    assert workspace_before.strip() and workspace_before == workspace_after
    run("exec", "-T", "api", "python", "-c",
        "from pathlib import Path; assert Path('/var/lib/museforge/artifacts/foundation-persistence.txt').read_text() == 'foundation-persistence'")
    run("exec", "-T", "worker-mock", "python", "-c",
        "from museforge.worker.app import app; from kombu import Queue; c=app.connection_for_read(); c.connect(); q=Queue('foundation.persistence',durable=True)(c); m=q.get(no_ack=False); assert m is not None and m.payload == {'foundation':True}; m.ack(); q.delete(); c.close()")
    print("Persisted PostgreSQL directory:", data_directory)
    run("run", "--rm", "tests")
    print("Foundation container acceptance passed; workspace, broker message and artifact survive ordinary down/up.")
finally:
    try:
        run("logs", "--no-color", "--tail", "40", timeout=30)
    finally:
        # Explicitly test-owned project only. User start/stop never uses --volumes.
        assert project.startswith("museforge-foundation-test-")
        run("down", "--volumes", "--remove-orphans", timeout=120)
