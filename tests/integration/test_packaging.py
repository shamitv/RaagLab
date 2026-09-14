import os
import time
import httpx
from sqlalchemy import text
from museforge.worker.app import app, broker_check


def test_service_readiness_and_registration(engine):
    with httpx.Client(base_url=os.environ['API_BASE_URL'], timeout=10) as client:
        assert client.get('/health/live').json()['status'] == 'alive'
        deadline = time.monotonic() + 30
        while True:
            response = client.get('/health/ready')
            body = response.json()
            if response.status_code == 200 and body['services']['dispatcher'] == body['services']['worker-mock'] == 'ready':
                break
            assert time.monotonic() < deadline, body
            time.sleep(.5)
        assert response.status_code == 200
        assert body['generation'] == 'ready'
        assert body['services']['dispatcher'] == body['services']['worker-mock'] == 'ready'
        assert body['services']['provider'] in ('ready', 'busy')
    with engine.connect() as connection:
        rows = connection.execute(text("SELECT readiness, capability_revision FROM worker_registrations WHERE expires_at > now()" )).all()
        assert rows and all(row.readiness in ('ready', 'busy') for row in rows)
        assert all(row.capability_revision == '1' for row in rows)


def test_real_broker_queues():
    broker_check()
    with app.connection_for_read() as connection:
        with connection.channel() as channel:
            result = channel.queue_declare(queue='museforge.mock.v1', passive=True)
            assert result.consumer_count >= 1
            channel.queue_declare(queue='museforge.quarantine.v1', passive=True)
