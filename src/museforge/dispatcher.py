"""Observable dispatcher process; durable publication lands with Phase 02."""
import logging
import signal
import socket
import threading

from museforge.config import Settings
from museforge.observability import probe_loop
from museforge.worker.app import broker_check


def main():
    settings = Settings()
    logging.basicConfig(level=settings.log_level, format="%(levelname)s %(name)s %(message)s")
    stop = threading.Event()
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda *_: stop.set())
    logging.getLogger("museforge").info("dispatcher_started mode=foundation publication=not_implemented")
    probe_loop(settings, "dispatcher", socket.gethostname(), stop, broker_check)


if __name__ == "__main__":
    main()
