import socket
import threading

from celery import Celery, signals
from celery.exceptions import Reject
from kombu import Exchange, Queue

from museforge.config import Settings
from museforge.observability import probe_loop
from museforge.providers import YuE2Music
from museforge.worker.broker_probe import check_broker
from museforge.worker.tasks import GenerationEnvelope, TASK_NAME

settings = Settings()
app = Celery("museforge", broker=settings.broker_url.get_secret_value())
exchange = Exchange("museforge", type="direct", durable=True)
quarantine = Exchange("museforge.quarantine", type="direct", durable=True)
provider_queue = Queue(settings.provider_route, exchange, routing_key=settings.provider_route, durable=True,
                       queue_arguments={"x-queue-type": "classic", "x-dead-letter-exchange": quarantine.name,
                                        "x-dead-letter-routing-key": settings.quarantine_queue})
app.conf.update(
    task_serializer="json", accept_content=["json"], result_serializer="json",
    task_acks_late=True, task_acks_on_failure_or_timeout=True,
    task_reject_on_worker_lost=False, worker_prefetch_multiplier=1,
    task_ignore_result=True, result_backend=None, task_always_eager=False,
    task_create_missing_queues=False, task_default_queue=settings.provider_route,
    task_default_exchange="museforge", task_default_routing_key=settings.provider_route,
    task_default_delivery_mode="persistent",
    task_routes={TASK_NAME: {"queue": settings.provider_route, "routing_key": settings.provider_route}},
    task_queues=(
        provider_queue,
        Queue(settings.quarantine_queue, quarantine, routing_key=settings.quarantine_queue, durable=True,
              queue_arguments={"x-message-ttl": 86400000, "x-max-length": 1000}),
    ),
    broker_connection_retry_on_startup=True, broker_connection_max_retries=None,
    broker_connection_timeout=settings.broker_timeout_seconds,
    broker_transport_options={"confirm_publish": True},
    task_publish_retry=False, worker_send_task_events=False, task_send_sent_event=False,
    worker_hijack_root_logger=False, worker_redirect_stdouts=False,
    # RabbitMQ 4.3 disallows transient non-exclusive pidbox queues.
    # Operational health uses persisted probes; remote control is unnecessary.
    worker_enable_remote_control=False,
    task_soft_time_limit=settings.attempt_deadline_seconds,
    task_time_limit=settings.hard_watchdog_seconds,
)


def broker_check():
    check_broker(settings.broker_timeout_seconds)


@app.task(name=TASK_NAME, bind=True, typing=True)
def execute_generation(self, envelope):
    try:
        validated = GenerationEnvelope.model_validate(envelope)
    except Exception:
        raise Reject("unsupported_generation_envelope", requeue=False) from None
    from museforge.worker.execution import execute
    from museforge.domain import ProviderError
    try:
        execute(settings, validated)
    except ProviderError:
        raise Reject("incompatible_generation_envelope", requeue=False) from None


_stop = threading.Event()
_thread = None


@signals.worker_ready.connect
def worker_ready(**kwargs):
    global _thread
    _stop.clear()
    _thread = threading.Thread(target=probe_loop, args=(settings, "worker-mock", socket.gethostname(), _stop, broker_check),
                                kwargs={"provider_role": settings.worker_role}, daemon=True)
    _thread.start()


@signals.worker_shutdown.connect
def worker_shutdown(**kwargs):
    _stop.set()
    YuE2Music.shutdown()
    if _thread:
        _thread.join(timeout=settings.broker_timeout_seconds + 5)


@signals.worker_process_shutdown.connect
def worker_process_shutdown(**kwargs):
    YuE2Music.shutdown()
