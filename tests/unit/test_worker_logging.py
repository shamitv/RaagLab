import io
import logging
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from celery.worker.consumer import consumer

from museforge.worker.logging import ConsumerDiagnosticFilter, configure_worker_logging


@pytest.mark.parametrize(("method", "code", "acknowledged"), [
    ("on_unknown_message", "consumer_unknown_message", False),
    ("on_unknown_task", "consumer_unknown_task", False),
    ("on_invalid_task", "consumer_invalid_task", False),
    ("on_decode_error", "consumer_decode_error", True),
])
def test_actual_consumer_handlers_redact_payloads_and_preserve_disposition(method, code, acknowledged):
    secret = "sentinel-private-lyrics-and-password"
    output = io.StringIO()
    handler = logging.StreamHandler(output)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger = consumer.logger
    original_filters, original_level = logger.filters[:], logger.level
    trace_logger = logging.getLogger("celery.app.trace")
    original_trace_level = trace_logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    configure_worker_logging()
    configure_worker_logging()
    assert sum(isinstance(item, ConsumerDiagnosticFilter) for item in logger.filters) == 1
    instance = object.__new__(consumer.Consumer)
    instance.connection_errors = (OSError,)
    instance.app = SimpleNamespace(backend=Mock())
    instance.event_dispatcher = None
    message = Mock(body=secret.encode(), headers={"task": secret, "id": str(uuid4()), "secret": secret},
                   properties={}, delivery_info={"secret": secret}, content_type="application/json",
                   content_encoding="utf-8")
    try:
        try:
            raise ValueError(secret)
        except ValueError as exc:
            if method == "on_decode_error":
                instance.on_decode_error(message, exc)
            elif method == "on_unknown_message":
                instance.on_unknown_message(secret, message)
            else:
                getattr(instance, method)(secret, message, exc)
        logger.info("consumer_connected")
        rendered = output.getvalue()
        assert code in rendered and "consumer_connected" in rendered
        assert secret not in rendered and "Traceback" not in rendered
        assert message.ack.call_count == int(acknowledged)
        assert message.reject_log_error.call_count == int(not acknowledged)
        if method == "on_unknown_task":
            instance.app.backend.mark_as_failure.assert_called_once()
    finally:
        logger.removeHandler(handler)
        logger.filters[:] = original_filters
        logger.setLevel(original_level)
        trace_logger.setLevel(original_trace_level)


def test_filter_clears_preformatted_exception_and_stack():
    record = logging.LogRecord(consumer.logger.name, logging.ERROR, __file__, 1,
                               consumer.INVALID_TASK_ERROR, ("secret", "secret"), None)
    record.exc_text = record.stack_info = record.message = "secret"
    assert ConsumerDiagnosticFilter().filter(record)
    assert record.getMessage() == "consumer_invalid_task"
    assert record.args == () and record.exc_text is record.stack_info is record.exc_info is None
    assert "message" not in record.__dict__
