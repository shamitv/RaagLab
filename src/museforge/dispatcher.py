"""Durable confirmed outbox publication and lease reconciliation."""
import logging
import multiprocessing
import secrets
import signal
import socket
import threading
import time
from datetime import timedelta
from uuid import uuid4
import sqlalchemy as sa
from museforge.config import Settings
from museforge.db.connection import engine_for
from museforge.db import schema as db
from museforge.jobs import TERMINAL, finish_error, insert_outbox, lock_job, now
from museforge.observability import probe_loop
from museforge.worker.app import broker_check

log = logging.getLogger('museforge')


def publish_child(envelope, settings, result):
    # A process boundary also bounds connection/channel/cleanup hangs.
    import os
    null = os.open(os.devnull, os.O_WRONLY)
    os.dup2(null, 1)
    os.dup2(null, 2)
    from museforge.worker.app import app, TASK_NAME
    try:
        with app.connection_for_write() as connection:
            connection.ensure_connection(max_retries=0)
            producer = app.amqp.Producer(connection, on_return=lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError('unroutable')))
            route = envelope['provider_route']
            app.send_task(TASK_NAME, args=[envelope], task_id=envelope['message_id'], producer=producer,
                queue=route, routing_key=route, mandatory=True, retry=False,
                delivery_mode=2, timeout=settings.broker_timeout_seconds,
                confirm_timeout=settings.broker_timeout_seconds)
        result.send(True)
    except Exception:
        result.send(False)
    finally:
        result.close()


def publish(envelope, settings):
    context = multiprocessing.get_context('spawn')
    receive, send = context.Pipe(duplex=False)
    process = context.Process(target=publish_child, args=(envelope, settings, send))
    process.start()
    send.close()
    try:
        if not receive.poll(settings.broker_timeout_seconds): return False
        return receive.recv()
    except EOFError:
        return False
    finally:
        if process.is_alive(): process.terminate()
        process.join(timeout=1)
        if process.is_alive(): process.kill(); process.join()
        receive.close()


def dispatch_once(engine, settings):
    with engine.begin() as c:
        timestamp = now(c)
        message = c.execute(sa.select(db.outbox).where(
            db.outbox.c.workspace_id == settings.workspace_id,
            sa.or_(sa.and_(db.outbox.c.state == 'pending', db.outbox.c.next_publication_at <= timestamp),
                   sa.and_(db.outbox.c.state == 'publishing', db.outbox.c.claim_expires_at <= timestamp)))
            .order_by(db.outbox.c.next_publication_at).with_for_update(skip_locked=True).limit(1)).mappings().first()
        if not message: return False
        token = uuid4()
        c.execute(db.outbox.update().where(db.outbox.c.id == message['id']).values(state='publishing', claim_token=token,
            claim_expires_at=timestamp + timedelta(seconds=settings.outbox_claim_seconds), publication_count=message['publication_count'] + 1))
        envelope = dict(schema_version=1, message_id=str(message['id']), job_id=str(message['job_id']),
            correlation_id=str(message['correlation_id']), dispatch_sequence=message['dispatch_sequence'],
            dispatched_at=timestamp.isoformat(), provider_route=message['provider_route'])
    success = publish(envelope, settings)
    with engine.begin() as c:
        timestamp = now(c)
        values = dict(state='published' if success else 'pending', claim_token=None, claim_expires_at=None)
        if success: values.update(confirmed_at=timestamp, error_code=None)
        else: values.update(error_code='publication_failed', error_at=timestamp,
            next_publication_at=timestamp + timedelta(seconds=min(30, 2 ** min(message['publication_count'], 5)) + secrets.randbelow(1000) / 1000))
        c.execute(db.outbox.update().where(db.outbox.c.id == message['id'], db.outbox.c.claim_token == token).values(**values))
    log.info('outbox_publication job=%s message=%s confirmed=%s', message['job_id'], message['id'], success)
    return True


def reconcile(engine, settings):
    with engine.connect() as c:
        identifiers = c.execute(sa.select(db.jobs.c.id).where(db.jobs.c.workspace_id == settings.workspace_id,
            db.jobs.c.state.not_in(TERMINAL)).order_by(db.jobs.c.next_action_at).limit(100)).scalars().all()
    for identifier in identifiers:
        with engine.begin() as c:
            _, job = lock_job(c, identifier, settings)
            timestamp = now(c)
            if job['state'] in TERMINAL: continue
            limits = job['execution_snapshot']['limits']
            if job['state'] == 'cancellation_requested' and job['cancellation_requested_at'] + timedelta(seconds=limits['cancellation_grace_seconds']) <= timestamp:
                finish_error(c, job, settings, 'cancelled')
            elif job['state'] in ('queued', 'retrying'):
                if job['queue_deadline'] <= timestamp:
                    finish_error(c, job, settings, 'deadline_exceeded')
                else:
                    message = c.execute(sa.select(db.outbox).where(db.outbox.c.job_id == identifier,
                        db.outbox.c.dispatch_sequence == job['dispatch_sequence']).with_for_update()).mappings().one()
                    if message['state'] == 'published' and message['confirmed_at'] + timedelta(seconds=settings.unclaimed_seconds) <= timestamp:
                        sequence = job['dispatch_sequence'] + 1
                        c.execute(db.jobs.update().where(db.jobs.c.id == identifier).values(dispatch_sequence=sequence))
                        insert_outbox(c, dict(job, dispatch_sequence=sequence), settings)
            elif job['state'] in ('running', 'cancellation_requested'):
                attempt = c.execute(sa.select(db.attempts).where(db.attempts.c.job_id == identifier,
                    db.attempts.c.fence_token == job['fence_token']).with_for_update()).mappings().one()
                if job['attempt_deadline'] <= timestamp:
                    finish_error(c, job, settings, 'deadline_exceeded')
                elif attempt['lease_expires_at'] <= timestamp:
                    finish_error(c, job, settings, 'worker_lost', True)
            current = c.scalar(sa.select(db.jobs.c.state).where(db.jobs.c.id == identifier))
            if current in TERMINAL:
                c.execute(db.outbox.update().where(db.outbox.c.job_id == identifier,
                    db.outbox.c.state.in_(['pending', 'publishing'])).values(state='abandoned', claim_token=None, claim_expires_at=None))


def main():
    settings = Settings()
    logging.basicConfig(level=settings.log_level, format='%(levelname)s %(name)s %(message)s')
    stop = threading.Event()
    for signum in (signal.SIGTERM, signal.SIGINT): signal.signal(signum, lambda *_: stop.set())
    probe = threading.Thread(target=probe_loop, args=(settings, 'dispatcher', socket.gethostname(), stop, broker_check), daemon=True)
    probe.start()
    engine = engine_for(settings)
    last = 0
    try:
        while not stop.is_set():
            try:
                if time.monotonic() - last >= settings.reconciliation_seconds:
                    reconcile(engine, settings)
                    last = time.monotonic()
                worked = dispatch_once(engine, settings)
            except Exception:
                log.warning('dispatcher_cycle_failed')
                worked = False
            if not worked: stop.wait(settings.dispatcher_poll_seconds)
    finally:
        stop.set()
        probe.join(timeout=10)
        engine.dispose()

if __name__ == '__main__': main()
