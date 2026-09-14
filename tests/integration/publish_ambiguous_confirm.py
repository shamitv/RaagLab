"""Drive the real publisher-confirm ambiguity case from the isolated runner."""
import argparse
import json
import os
import time
from datetime import timedelta
from uuid import UUID, uuid4

import sqlalchemy as sa

from museforge.config import Settings
from museforge.db import schema as db
from museforge.db.connection import engine_for
from museforge.jobs import now
from museforge.worker.app import app
from museforge.worker.tasks import TASK_NAME


def identifiers():
    return UUID(os.environ["RECOVERY_JOB_ID"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("publish", "wait-reclaimed", "verify-single-result"))
    mode = parser.parse_args().mode
    settings = Settings()
    engine = engine_for(settings)
    job_id = identifiers()
    try:
        if mode == "publish":
            with engine.begin() as connection:
                job = connection.execute(sa.select(db.jobs).where(
                    db.jobs.c.id == job_id,
                    db.jobs.c.workspace_id == settings.workspace_id,
                ).with_for_update()).mappings().one()
                message = connection.execute(sa.select(db.outbox).where(
                    db.outbox.c.job_id == job_id,
                    db.outbox.c.dispatch_sequence == job["dispatch_sequence"],
                ).with_for_update()).mappings().one()
                assert job["state"] == "queued" and message["state"] == "pending"
                timestamp = now(connection)
                token = uuid4()
                connection.execute(db.outbox.update().where(
                    db.outbox.c.id == message["id"],
                ).values(
                    state="publishing",
                    claim_token=token,
                    claim_expires_at=timestamp - timedelta(seconds=1),
                    publication_count=1,
                ))
                envelope = {
                    "schema_version": message["schema_version"],
                    "message_id": str(message["id"]),
                    "job_id": str(job_id),
                    "correlation_id": str(job["correlation_id"]),
                    "dispatch_sequence": message["dispatch_sequence"],
                    "dispatched_at": timestamp.isoformat(),
                    "provider_route": message["provider_route"],
                }
            # A successful return means RabbitMQ confirmed this first publication.
            app.send_task(
                TASK_NAME,
                args=[envelope],
                task_id=envelope["message_id"],
                queue=settings.mock_queue,
            )
            print(json.dumps({"confirmed_message_id": envelope["message_id"], "job_id": str(job_id)}))
        elif mode == "wait-reclaimed":
            deadline = time.monotonic() + 60
            while True:
                with engine.connect() as connection:
                    message = connection.execute(sa.select(db.outbox).where(
                        db.outbox.c.job_id == job_id,
                    )).mappings().one()
                    state, count = message["state"], message["publication_count"]
                if state == "published" and count >= 2:
                    print(json.dumps({"state": state, "publication_count": count, "job_id": str(job_id)}))
                    break
                assert time.monotonic() < deadline, (state, count)
                time.sleep(.25)
        else:
            with engine.connect() as connection:
                job = connection.execute(sa.select(db.jobs).where(
                    db.jobs.c.id == job_id,
                    db.jobs.c.workspace_id == settings.workspace_id,
                )).mappings().one()
                versions = connection.scalar(sa.select(sa.func.count()).select_from(db.versions).where(
                    db.versions.c.generation_job_id == job_id,
                ))
            assert job["state"] == "succeeded" and job["attempt_count"] == 1
            assert versions == 1 and job["result_version_id"] is not None
            print(json.dumps({"state": job["state"], "attempt_count": job["attempt_count"],
                              "version_count": versions, "job_id": str(job_id)}))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
