import json
import importlib.util
import os
from pathlib import Path
import subprocess
import threading
import sys
import time
import types
from uuid import uuid4
from unittest.mock import Mock

import pytest

from museforge.config import Settings
from museforge.domain import ProviderError
from museforge.providers import YuE2Music
from museforge.routing import publication_options, publisher_app
from museforge.worker.tasks import GenerationEnvelope


def settings(tmp_path, provider='yue2'):
    paths = {name: tmp_path / name for name in ('artifact_root', 'web_dist', 'weights_dir',
             'cache_dir', 'health_file', 'yue2_model_dir', 'yue2_vae_dir', 'yue2_runner', 'yue2_preflight')}
    return Settings(_env_file=None, **paths, music_provider=provider,
                    lyrics_provider='user' if provider == 'yue2' else 'mock',
                    device='cuda' if provider == 'yue2' else 'cpu',
                    precision='bfloat16', model_id='model' if provider == 'yue2' else None,
                    model_revision='revision' if provider == 'yue2' else None,
                    decoder_revision='decoder' if provider == 'yue2' else None)


@pytest.mark.parametrize('provider', ['mock', 'yue2'])
@pytest.mark.parametrize('route', ['museforge.mock.v1', 'museforge.yue2.v1'])
def test_publisher_routes_are_independent_of_configured_provider(tmp_path, provider, route):
    config = settings(tmp_path, provider)
    app = publisher_app(config)
    try:
        # Exercise Celery's real routing resolution without requiring RabbitMQ.
        routed = app.amqp.router.route(publication_options(config, route), 'museforge.generate')
        assert routed['queue'].name == route
        producer = Mock()
        message = app.amqp.create_task_message(str(uuid4()), 'museforge.execute_generation', args=[{}])
        app.amqp.send_task_message(producer, 'museforge.execute_generation', message, **routed)
        assert producer.publish.call_args.kwargs['routing_key'] == route
        assert not app.conf.task_create_missing_queues
        with pytest.raises(ValueError, match='unsupported_provider_route'):
            publication_options(config, 'unknown')
    finally:
        app.close()


def test_wrong_worker_rejects_before_database_access(tmp_path, monkeypatch):
    from museforge.worker import execution
    monkeypatch.setattr(execution, 'engine_for', lambda *_: pytest.fail('wrong worker touched database'))
    envelope = GenerationEnvelope(schema_version=1, message_id=uuid4(), job_id=uuid4(),
        correlation_id=uuid4(), dispatch_sequence=1, dispatched_at='2026-09-14T00:00:00Z',
        provider_route='museforge.yue2.v1')
    with pytest.raises(ProviderError, match='incompatible_envelope'):
        execution.execute(settings(tmp_path, 'mock'), envelope)


def test_warmup_uses_same_effective_environment_as_generation(tmp_path, monkeypatch):
    config = settings(tmp_path)
    captured = {}
    class Process:
        def wait(self, **kwargs): return 0
    def spawn(command, settings, **kwargs):
        captured['env'] = YuE2Music.child_environment(settings)
        return Process()
    monkeypatch.setattr(YuE2Music, '_spawn', spawn)
    monkeypatch.setattr(YuE2Music, '_terminate', lambda *_: None)
    monkeypatch.setenv('YUE2_MODEL_DIR', '/wrong')
    YuE2Music.preflight(config)
    assert captured['env'] == YuE2Music.child_environment(config)
    assert captured['env']['YUE2_MODEL_DIR'] == str(config.yue2_model_dir)
    assert captured['env']['MODEL_REVISION'] == config.model_revision
    assert captured['env']['HF_HUB_OFFLINE'] == '1'


def test_readiness_requires_compatible_identity(tmp_path):
    from museforge.api.routes import readiness
    from sqlalchemy.dialects import postgresql
    class Result:
        def mappings(self): return self
        def all(self): return []
    class Connection:
        statement = None
        def execute(self, statement):
            self.statement = statement
            return Result()
    connection = Connection()
    assert readiness(connection, settings(tmp_path))['state'] == 'offline'
    sql = str(connection.statement.compile(dialect=postgresql.dialect()))
    for name in ('provider_id', 'provider_revision', 'model_id', 'model_revision', 'capability_revision'):
        assert 'worker_registrations.' + name + ' =' in sql
    connection = Connection()
    readiness(connection, settings(tmp_path, 'mock'))
    assert 'model_revision IS NULL' in str(connection.statement.compile(dialect=postgresql.dialect()))


@pytest.mark.parametrize('field', ['MODEL_ID', 'MODEL_REVISION', 'DECODER_REVISION'])
def test_preflight_rejects_identity_mismatch_before_initialization(monkeypatch, field):
    root = Path(__file__).resolve().parents[2]
    monkeypatch.setitem(sys.modules, 'torch', types.SimpleNamespace())
    spec = importlib.util.spec_from_file_location('yue_preflight', root / 'packaging/yue2/preflight.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    lock = json.loads((root / 'packaging/yue2/model-lock.json').read_text())
    for key, value in (('MODEL_ID', lock['model']['repo']), ('MODEL_REVISION', lock['model']['revision']),
                       ('DECODER_REVISION', lock['vae']['revision'])):
        monkeypatch.setenv(key, value)
    module.validate_configured_identity(lock)
    monkeypatch.setenv(field, 'wrong')
    with pytest.raises(RuntimeError, match=field):
        module.validate_configured_identity(lock)


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux real-worker lifecycle')
def test_guardian_cleans_up_when_pool_child_is_killed_and_serializes_replacement(tmp_path):
    owner = tmp_path / 'owner.py'
    pid_file = tmp_path / 'inference.pid'
    lock = tmp_path / 'gpu.lock'
    guardian_pid = tmp_path / 'guardian.pid'
    escaped_pid_file = tmp_path / 'escaped.pid'
    escaped_code = ('import os,signal,time; from pathlib import Path; '
        'signal.signal(signal.SIGTERM,signal.SIG_IGN); '
        'Path(' + repr(str(escaped_pid_file)) + ').write_text(str(os.getpid())); time.sleep(120)')
    inference = tmp_path / 'inference.py'
    inference.write_text('import os,signal,time,subprocess,sys\nfrom pathlib import Path\n'
        'signal.signal(signal.SIGTERM,signal.SIG_IGN)\n'
        'subprocess.Popen([sys.executable,"-c",' + repr(escaped_code) + '],start_new_session=True)\n'
        'Path(' + repr(str(pid_file)) + ').write_text(str(os.getpid()))\ntime.sleep(120)\n')
    owner.write_text('''import os, subprocess, sys, time
from pathlib import Path
r, w = os.pipe()
child = subprocess.Popen([sys.executable, '-m', 'museforge.worker.inference_supervisor',
    '--control-fd', str(r), '--lock-path', sys.argv[1], '--', sys.executable, sys.argv[2]],
    pass_fds=(r,), start_new_session=True)
os.close(r)
Path(sys.argv[3]).write_text(str(child.pid))
time.sleep(120)
''')
    root = Path(__file__).resolve().parents[2]
    env = dict(os.environ, PYTHONPATH=str(root / 'src'))
    pool = subprocess.Popen([sys.executable, str(owner), str(lock), str(inference), str(guardian_pid)], env=env)
    replacement = None
    replacement_write = None
    inference_pid = None
    try:
        deadline = time.monotonic() + 10
        while not pid_file.exists() or not escaped_pid_file.exists():
            assert pool.poll() is None
            assert time.monotonic() < deadline
            time.sleep(.05)
        inference_pid = int(pid_file.read_text())
        pool.kill()
        pool.wait()
        marker = tmp_path / 'replacement'
        read_fd, replacement_write = os.pipe()
        try:
            replacement = subprocess.Popen([sys.executable, '-m', 'museforge.worker.inference_supervisor',
                '--control-fd', str(read_fd), '--lock-path', str(lock), '--', sys.executable, '-c',
                'from pathlib import Path; Path(' + repr(str(marker)) + ').touch()'],
                pass_fds=(read_fd,), env=env)
        finally:
            os.close(read_fd)
        time.sleep(.3)
        assert not marker.exists(), 'replacement ran while old inference retained the lock'
        assert replacement.wait(timeout=15) == 0
        assert marker.exists()
        with pytest.raises(ProcessLookupError):
            os.kill(inference_pid, 0)
        with pytest.raises(ProcessLookupError):
            os.kill(int(escaped_pid_file.read_text()), 0)
    finally:
        if replacement_write is not None: os.close(replacement_write)
        if pool.poll() is None: pool.kill(); pool.wait()
        if replacement is not None and replacement.poll() is None: replacement.terminate(); replacement.wait()
        if inference_pid is not None:
            try: os.kill(inference_pid, 9)
            except ProcessLookupError: pass
        if escaped_pid_file.exists():
            try: os.kill(int(escaped_pid_file.read_text()), 9)
            except ProcessLookupError: pass


def test_actual_flac_is_transcoded_to_valid_pcm_wav(tmp_path):
    np = pytest.importorskip('numpy')
    sf = pytest.importorskip('soundfile')
    config = settings(tmp_path)
    runner = tmp_path / 'runner.py'
    runner.write_text('''import sys
from pathlib import Path
import numpy as np
import soundfile as sf
out = Path(sys.argv[2]); out.mkdir(parents=True)
t = np.arange(48000 * 6) / 48000
audio = np.column_stack([.1*np.sin(2*np.pi*440*t), .1*np.sin(2*np.pi*441*t)])
sf.write(out / 'audio.flac', audio, 48000, format='FLAC')
(out / 'validation.json').write_text('{"passed":true}')
''')
    config = config.model_copy(update={'yue2_runner': runner})
    output = tmp_path / 'audio.wav'
    request = dict(operation='generate', language='English', vocal_type='Instrumental',
        lyrics={'mode': 'user', 'text': '[Verse]\nExact lyrics'}, seed=42, genre='Folk',
        mood='Calm', tempo='Medium', instruments=['Guitar'], brief='test', duration_seconds=8)
    provider = YuE2Music(config, output)
    provider.generate(request, lambda *_: None, lambda: None)
    from museforge.storage import inspect
    assert inspect(output, expected_sample_rate=48000)['duration_seconds'] == 6
    assert sf.info(output).subtype == 'PCM_16'
    assert provider.metadata['requested_duration_seconds'] == 8


@pytest.mark.skipif(sys.platform != 'linux', reason='Linux real-worker shutdown')
def test_shutdown_closes_guardian_control_and_reaps_inference(tmp_path):
    pid_file = tmp_path / 'shutdown.pid'
    runner = tmp_path / 'shutdown.py'
    runner.write_text('import os,time\nfrom pathlib import Path\n'
        'Path(' + repr(str(pid_file)) + ').write_text(str(os.getpid()))\ntime.sleep(30)\n')
    config = settings(tmp_path).model_copy(update={'yue2_runner': runner})
    provider = YuE2Music(config, tmp_path / 'output.wav')
    errors = []
    request = dict(operation='generate', language='English', vocal_type='Instrumental',
        lyrics={'mode': 'user', 'text': '[Verse]\nShutdown test'}, seed=42, genre='Folk',
        mood='Calm', tempo='Medium', instruments=['Guitar'], brief='test', duration_seconds=8)
    def generate():
        try:
            provider.generate(request, lambda *_: None, lambda: None)
        except ProviderError as exc:
            errors.append(exc.code)
    thread = threading.Thread(target=generate)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not pid_file.exists():
            assert thread.is_alive() and time.monotonic() < deadline
            time.sleep(.05)
        pid = int(pid_file.read_text())
        YuE2Music.shutdown()
        thread.join(timeout=10)
        assert not thread.is_alive() and not YuE2Music._active_processes
        assert errors == ['transient_failure']
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)
    finally:
        YuE2Music.shutdown()
        thread.join(timeout=10)
