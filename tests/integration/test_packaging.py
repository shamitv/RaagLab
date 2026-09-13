import os
import httpx
from sqlalchemy import text
from museforge.worker.app import app, broker_check


def test_service_readiness_and_registration(engine):
    with httpx.Client(base_url=os.environ['API_BASE_URL'], timeout=10) as client:
        assert client.get('/health/live').json()['status'] == 'alive'
        response = client.get('/health/ready')
        assert response.status_code == 200
        body = response.json()
        assert body['generation'] == 'not_implemented'
        assert body['services']['dispatcher'] == body['services']['worker-mock'] == 'ready'
        assert body['services']['provider'] == 'not_implemented'
    with engine.connect() as connection:
        rows = connection.execute(text("SELECT readiness, capability_revision FROM worker_registrations WHERE expires_at > now()" )).all()
        assert rows and all(row.readiness == 'initializing' for row in rows)
        assert all(row.capability_revision == 'foundation-no-generation' for row in rows)
        assert connection.scalar(text('SELECT count(*) FROM generation_jobs')) == 0


def test_real_broker_queues():
    broker_check()
    with app.connection_for_read() as connection:
        with connection.channel() as channel:
            result = channel.queue_declare(queue='museforge.mock.v1', passive=True)
            assert result.consumer_count == 1
            channel.queue_declare(queue='museforge.quarantine.v1', passive=True)
