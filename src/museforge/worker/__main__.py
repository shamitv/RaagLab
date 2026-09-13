import logging
from museforge.worker.app import app, settings

logging.basicConfig(level=settings.log_level, format="%(levelname)s %(name)s %(message)s")
# Task-rejection internals can include arbitrary message bodies. Keep diagnostics safe.
logging.getLogger("celery.app.trace").setLevel(logging.CRITICAL)
app.worker_main(["worker", "--loglevel=" + settings.log_level, "--pool=prefork", "--concurrency=1",
                 "--queues=" + settings.mock_queue, "--without-gossip", "--without-mingle"])
