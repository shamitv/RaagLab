"""Public-API smoke/seed client; audio metadata is measured, never fabricated."""
import argparse
import hashlib
import io
import json
import os
import time
import urllib.request
import uuid
import wave


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['seed','smoke'])
    parser.add_argument('--base-url', default=os.environ.get('API_BASE_URL','http://127.0.0.1:8000'))
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    def request(path, body=None, headers=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(base+path,data=data,headers={'Content-Type':'application/json',**(headers or {})})
        with urllib.request.urlopen(req,timeout=10) as response:
            return response.status, response.headers, response.read()
    records=[]
    for mode in (['user','static','mock'] if args.command=='seed' else ['user']):
        body=dict(brief=f'Original {mode} demo',instruments=['Piano'],mood='Calm',duration_seconds=5,
                  lyrics={'mode':mode,'text':'[Verse]\nA new morning, a quiet song\n' if mode=='user' else None})
        start=time.monotonic()
        status, _, data=request('/api/v1/generations',body,{'Idempotency-Key':str(uuid.uuid4())})
        assert status==202 and time.monotonic()-start<1
        identity=json.loads(data)
        deadline=time.monotonic()+90
        while True:
            _, _, data=request(identity['status_url']); job=json.loads(data)
            if job['state'] in ('succeeded','failed','cancelled','timed_out'): break
            if time.monotonic()>deadline: raise RuntimeError('generation_timeout')
            time.sleep(.5)
        assert job['state']=='succeeded',job
        _, _, data=request(job['version_url']); version=json.loads(data)
        _, _, data=request(version['audio']['url'])
        info=version['audio']
        assert len(data)==info['byte_size'] and hashlib.sha256(data).hexdigest()==info['sha256']
        with wave.open(io.BytesIO(data)) as audio:
            assert audio.getnframes()/audio.getframerate()==info['duration_seconds']
            assert audio.getframerate()==44100 and audio.getnchannels()==2
            decoded={'duration_seconds':audio.getnframes()/audio.getframerate(),
                     'sample_rate':audio.getframerate(),'channels':audio.getnchannels(),
                     'sample_width_bytes':audio.getsampwidth(),'frames':audio.getnframes(),
                     'non_silent':any(audio.readframes(audio.getnframes()))}
            assert decoded['non_silent']
        status, _, data=request(version['audio']['url'],headers={'Range':'bytes=0-43'})
        assert status==206 and len(data)==44
        records.append({'identity':identity,'job':job,'audio':info,'decoded':decoded})
    print(json.dumps(records,indent=2))

if __name__=='__main__':
    try: main()
    except Exception:
        import sys
        print('demo_check_failed: inspect API and worker readiness', file=sys.stderr)
        sys.exit(1)
