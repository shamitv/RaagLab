"""Run broker I/O in a disposable process with a total operation deadline."""
import subprocess
import sys


class BrokerProbeTimeout(RuntimeError):
    pass


class BrokerProbeFailed(RuntimeError):
    pass


def _run_probe(command, timeout):
    try:
        # run() kills and reaps the child on timeout. No broker-controlled output
        # or connection credentials enter either the parent logs or its errors.
        subprocess.run(
            command, check=True, timeout=timeout,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    except subprocess.TimeoutExpired:
        raise BrokerProbeTimeout("broker_probe_timeout") from None
    except (subprocess.CalledProcessError, OSError):
        raise BrokerProbeFailed("broker_probe_failed") from None


def check_broker(timeout):
    _run_probe([sys.executable, "-m", "museforge.worker.broker_probe"], timeout)


def main():
    # Import the configured app only in the probe child. Its deadline includes
    # channel creation, queue declarations, and graceful connection cleanup.
    from museforge.worker.app import app, settings

    with app.connection_for_write(connect_timeout=settings.broker_timeout_seconds) as connection:
        connection.ensure_connection(max_retries=0, timeout=settings.broker_timeout_seconds)
        with connection.channel() as channel:
            for queue in app.conf.task_queues:
                queue(channel).declare()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit(1) from None
