import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from museforge.worker import broker_probe


def test_probe_success_and_failure_discard_output(capfd):
    code = "import sys; print('private-body'); print('private-password', file=sys.stderr)"
    broker_probe._run_probe([sys.executable, "-c", code], timeout=3)
    with pytest.raises(broker_probe.BrokerProbeFailed, match="^broker_probe_failed$"):
        broker_probe._run_probe([sys.executable, "-c", code + "; sys.exit(7)"], timeout=3)
    assert capfd.readouterr() == ("", "")


def test_probe_spawn_failure_is_safe(tmp_path):
    with pytest.raises(broker_probe.BrokerProbeFailed, match="^broker_probe_failed$"):
        broker_probe._run_probe([str(tmp_path / "private-password-executable")], timeout=1)


@pytest.mark.parametrize("stage", ["connect", "channel", "declare", "cleanup"])
def test_deadline_covers_all_broker_operations_and_reaps_child(stage, monkeypatch):
    # Exercise the actual child entrypoint while a fake transport stalls in one
    # operation. Socket timeouts cannot protect every one of these operations.
    code = f"""
import sys, time
from types import SimpleNamespace
from museforge.worker.broker_probe import main
def operation(stage):
    if stage == {stage!r}:
        time.sleep(60)
class Connection:
    def __enter__(self): return self
    def __exit__(self, *args): operation('cleanup')
    def ensure_connection(self, **kwargs): operation('connect')
    def channel(self):
        operation('channel')
        return self
class Queue:
    def __call__(self, channel): return self
    def declare(self): operation('declare')
app = SimpleNamespace(connection_for_write=lambda **kwargs: Connection(),
                      conf=SimpleNamespace(task_queues=[Queue()]))
sys.modules['museforge.worker.app'] = SimpleNamespace(
    app=app, settings=SimpleNamespace(broker_timeout_seconds=1))
main()
"""
    children = []
    popen = subprocess.Popen

    def track_child(*args, **kwargs):
        child = popen(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(broker_probe.subprocess, "Popen", track_child)
    started = time.monotonic()
    with pytest.raises(broker_probe.BrokerProbeTimeout, match="^broker_probe_timeout$"):
        broker_probe._run_probe([sys.executable, "-c", code], timeout=1)
    assert time.monotonic() - started < 3
    assert len(children) == 1 and children[0].poll() is not None
    broker_probe._run_probe([sys.executable, "-c", "pass"], timeout=3)


def test_timeout_updates_health_and_allows_worker_shutdown(monkeypatch, tmp_path):
    import importlib
    from museforge import observability

    worker = importlib.import_module("museforge.worker.app")
    stop = threading.Event()
    started = threading.Event()
    observations = []
    engine = SimpleNamespace(dispose=lambda: None)
    settings = SimpleNamespace(health_file=tmp_path / "health.json", heartbeat_seconds=0.01,
                               broker_timeout_seconds=1)

    def stalled_probe():
        started.set()
        broker_probe._run_probe([sys.executable, "-c", "import time; time.sleep(60)"], timeout=1)

    monkeypatch.setattr(observability, "engine_for", lambda _: engine)
    monkeypatch.setattr(observability, "write_probe", lambda path, **values: observations.append(values))
    monkeypatch.setattr(worker, "settings", settings)
    monkeypatch.setattr(worker, "_stop", stop)
    thread = threading.Thread(target=observability.probe_loop,
                              args=(settings, "worker-mock", "test", stop, stalled_probe))
    monkeypatch.setattr(worker, "_thread", thread)
    thread.start()
    try:
        assert started.wait(timeout=3)
        before = time.monotonic()
        worker.worker_shutdown()
        assert time.monotonic() - before < 3
        assert not thread.is_alive()
        assert observations and all(not item["healthy"] for item in observations)
    finally:
        stop.set()
        thread.join(timeout=3)


def test_probe_loop_recovers_after_timeout(monkeypatch, tmp_path):
    from museforge import observability

    stop = threading.Event()
    health = []
    attempts = []
    connection = Mock()

    class Engine:
        @contextmanager
        def begin(self):
            yield connection

        def dispose(self):
            pass

    def probe():
        attempts.append(True)
        if len(attempts) == 1:
            raise broker_probe.BrokerProbeTimeout("broker_probe_timeout")

    def write_probe(path, *, healthy, role):
        health.append(healthy)
        if healthy:
            stop.set()

    monkeypatch.setattr(observability, "engine_for", lambda _: Engine())
    monkeypatch.setattr(observability, "check_schema", lambda *_: None)
    monkeypatch.setattr(observability, "write_probe", write_probe)
    settings = SimpleNamespace(health_file=tmp_path / "health.json", heartbeat_seconds=0,
                               lease_seconds=30)
    observability.probe_loop(settings, "dispatcher", "test", stop, probe)
    assert len(attempts) == 2
    assert health == [False, True, False]  # Failed, recovered, then shut down.
    connection.execute.assert_called_once()
