"""No-fallback HTTP proof; run while the real worker is stopped."""
import argparse
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--origin', required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    def request(path, body=None, method='GET'):
        headers = {'Content-Type': 'application/json', 'Idempotency-Key': str(uuid4())}
        with urlopen(Request(args.origin + path, method=method, headers=headers,
                data=json.dumps(body).encode() if body is not None else None), timeout=15) as response:
            return json.load(response)
    deadline = time.monotonic() + 60
    while request('/api/v1/capabilities')['readiness']['state'] != 'offline':
        assert time.monotonic() < deadline, 'Worker registration did not expire'
        time.sleep(1)
    accepted = request('/api/v1/generations', dict(brief='Unavailable real-worker probe',
        instruments=['Guitar'], mood='Calm', language='English',
        lyrics={'mode': 'user', 'text': '[Verse]\nNo mock fallback'}, duration_seconds=8), 'POST')
    time.sleep(5)
    job = request(accepted['status_url'])
    assert job['state'] == 'queued' and job['attempt_count'] == 0 and job['result_version_id'] is None
    request(accepted['status_url'] + '/cancel', {}, 'POST')
    cancelled = request(accepted['status_url'])
    assert cancelled['state'] == 'cancelled' and cancelled['result_version_id'] is None
    args.evidence.write_text(json.dumps(dict(result='passed', no_mock_fallback=True,
        accepted=accepted, queued_job=job, cancelled_job=cancelled), indent=2) + '\n')
    print('Unavailable real worker left the request queued with no attempt or result; cancellation passed.')


if __name__ == '__main__':
    main()
