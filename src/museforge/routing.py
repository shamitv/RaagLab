"""Explicit durable queue definitions shared by publishers and consumers."""
from celery import Celery
from kombu import Exchange, Queue


def provider_queues(settings):
    exchange = Exchange('museforge', type='direct', durable=True)
    return {route: Queue(route, exchange, routing_key=route, durable=True,
                        queue_arguments={'x-queue-type': 'classic',
                                         'x-dead-letter-exchange': 'museforge.quarantine',
                                         'x-dead-letter-routing-key': settings.quarantine_queue})
            for route in (settings.mock_queue, settings.yue2_queue)}


def publication_options(settings, route):
    if route not in provider_queues(settings):
        raise ValueError('unsupported_provider_route')
    return {'queue': route, 'routing_key': route}


def publisher_app(settings):
    app = Celery('museforge-publisher', broker=settings.broker_url.get_secret_value())
    app.conf.update(task_serializer='json', accept_content=['json'],
                    task_create_missing_queues=False,
                    task_queues=tuple(provider_queues(settings).values()),
                    task_default_queue=settings.provider_route,
                    task_default_routing_key=settings.provider_route,
                    task_default_exchange='museforge', task_default_exchange_type='direct',
                    task_publish_retry=False,
                    broker_connection_timeout=settings.broker_timeout_seconds,
                    broker_transport_options={'confirm_publish': True},
                    task_ignore_result=True, result_backend=None)
    return app
