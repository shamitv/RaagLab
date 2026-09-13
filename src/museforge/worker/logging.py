"""Redact broker-controlled data before consumer diagnostics reach handlers."""
import logging

from celery.worker.consumer import consumer


class ConsumerDiagnosticFilter(logging.Filter):
    codes = {
        consumer.UNKNOWN_FORMAT: "consumer_unknown_message",
        consumer.UNKNOWN_TASK_ERROR: "consumer_unknown_task",
        consumer.INVALID_TASK_ERROR: "consumer_invalid_task",
        consumer.MESSAGE_DECODE_ERROR: "consumer_decode_error",
    }

    def filter(self, record):
        code = self.codes.get(record.msg) if isinstance(record.msg, str) else None
        if code:
            record.msg = code
            record.args = ()
            record.exc_info = None
            record.exc_text = None
            record.stack_info = None
            # A preceding handler may already have formatted this record.
            record.__dict__.pop("message", None)
        return True


def configure_worker_logging():
    if not any(isinstance(item, ConsumerDiagnosticFilter) for item in consumer.logger.filters):
        consumer.logger.addFilter(ConsumerDiagnosticFilter())
    # Task-rejection internals also include arbitrary argument/result bodies.
    logging.getLogger("celery.app.trace").setLevel(logging.CRITICAL)
