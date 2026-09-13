"""Test-runner helper: publish only to the isolated foundation test broker."""
import os
import sys
from uuid import uuid4

from museforge.worker.app import app
from museforge.worker.tasks import TASK_NAME


def main():
    if os.environ.get("FOUNDATION_INTEGRATION") != "1":
        raise SystemExit("Use the isolated foundation verification runner")
    secret = sys.argv[1]
    with app.connection_for_write() as connection:
        producer = connection.Producer()
        options = dict(exchange="museforge", routing_key=app.conf.task_default_queue,
                       delivery_mode=2, retry=False, mandatory=True)
        # Unknown protocol, unknown task, invalid ETA, invalid JSON.
        producer.publish({"private": secret}, serializer="json", headers={"private": secret}, **options)
        producer.publish([[], {}, {}], serializer="json",
                         headers={"task": secret, "id": str(uuid4()), "private": secret}, **options)
        producer.publish([[], {}, {}], serializer="json",
                         headers={"task": TASK_NAME, "id": str(uuid4()), "eta": secret, "private": secret}, **options)
        producer.publish('{"private":"' + secret, content_type="application/json",
                         content_encoding="utf-8", headers={"private": secret}, **options)


if __name__ == "__main__":
    main()
