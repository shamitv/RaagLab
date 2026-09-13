import logging
from museforge.worker.app import app, settings
from museforge.worker.logging import configure_worker_logging

logging.basicConfig(level=settings.log_level, format="%(levelname)s %(name)s %(message)s")
configure_worker_logging()
app.worker_main(["worker", "--loglevel=" + settings.log_level, "--pool=prefork", "--concurrency=1",
                 "--queues=" + settings.mock_queue, "--without-gossip", "--without-mingle"])
