import logging
import os
import socket
import threading
from museforge.worker.app import app, broker_check, settings
from museforge.worker.logging import configure_worker_logging
from museforge.domain import ProviderError
from museforge.providers import YuE2Music
from museforge.observability import probe_loop

logging.basicConfig(level=settings.log_level, format="%(levelname)s %(name)s %(message)s")
configure_worker_logging()
startup_stop = threading.Event()
startup_probe = threading.Thread(target=probe_loop,
    args=(settings, 'worker-mock', socket.gethostname(), startup_stop, broker_check),
    kwargs={'provider_role': settings.worker_role, 'readiness': 'initializing'}, daemon=True)
startup_probe.start()
try:
    if settings.music_provider == 'yue2':
        try:
            YuE2Music.preflight(settings)
            logging.getLogger('museforge').info('yue2_startup device=%s backend=%s fallback_reason=%s',
                settings.inference_device, settings.runtime_metadata['backend'],
                settings.runtime_metadata['fallback_reason'])
        except ProviderError:
            logging.getLogger('museforge').error('yue2_preflight_failed')
            raise SystemExit(78)
finally:
    startup_stop.set()
    startup_probe.join(timeout=settings.broker_timeout_seconds + 5)
app.worker_main(["worker", "--loglevel=" + settings.log_level, "--pool=prefork", "--concurrency=1",
                 "--queues=" + settings.provider_route, "--without-gossip", "--without-mingle"])
