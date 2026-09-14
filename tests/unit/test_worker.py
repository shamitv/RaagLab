from datetime import datetime, timezone
from uuid import uuid4
import pytest
from celery.exceptions import Reject
from pydantic import ValidationError
from museforge.worker.app import app, execute_generation
from museforge.worker.tasks import GenerationEnvelope, TASK_NAME


def envelope():
    return dict(schema_version=1, message_id=str(uuid4()), job_id=str(uuid4()), correlation_id=str(uuid4()),
                dispatch_sequence=1, dispatched_at=datetime.now(timezone.utc).isoformat(), provider_route='museforge.mock.v1')


@pytest.mark.parametrize('change', [{'schema_version': 2}, {'lyrics': 'not allowed'}, {'provider_route': ''},
                                    {'dispatch_sequence': 0}, {'dispatched_at': '2026-09-13T10:00:00'}])
def test_invalid_message_is_rejected(change):
    with pytest.raises(ValidationError):
        GenerationEnvelope.model_validate(envelope() | change)


def test_invalid_envelope_is_quarantined():
    with pytest.raises(Reject) as error:
        execute_generation.run(envelope() | {'schema_version': 9})
    assert error.value.requeue is False


def test_worker_delivery_contract():
    config = app.conf
    assert config.accept_content == ['json']
    assert config.task_acks_late and config.task_acks_on_failure_or_timeout
    assert config.worker_prefetch_multiplier == 1
    assert config.task_ignore_result and config.result_backend is None
    assert not config.task_always_eager and not config.task_create_missing_queues
    assert not config.task_reject_on_worker_lost
    assert config.task_routes[TASK_NAME]['queue'] == 'museforge.mock.v1'
    assert config.broker_transport_options['confirm_publish']
    assert not config.worker_enable_remote_control
