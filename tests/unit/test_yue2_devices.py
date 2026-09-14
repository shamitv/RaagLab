"""Device selection, startup-only fallback, and opt-in short audio validation."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import types
import hashlib
import subprocess

import pytest
from pydantic import ValidationError

from museforge.config import Settings
from museforge.domain import ProviderError
from museforge.providers import YuE2Music

ROOT = Path(__file__).resolve().parents[2]


def load_module(monkeypatch, name, torch):
    monkeypatch.setitem(sys.modules, 'torch', torch)
    monkeypatch.syspath_prepend(str(ROOT / 'packaging/yue2'))
    spec = importlib.util.spec_from_file_location(name, ROOT / f'packaging/yue2/{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def real_settings(tmp_path, **updates):
    values = dict(_env_file=None, music_provider='yue2', lyrics_provider='user',
        device='auto', precision='bfloat16', model_id='m-a-p/YuE2-3B',
        model_revision='model', decoder_revision='vae',
        artifact_root=tmp_path, yue2_preflight=tmp_path / 'preflight.py')
    values.update(updates)
    return Settings(**values)


def fake_torch(available=True, bf16=True, probe_error=False):
    class Tensor:
        def __matmul__(self, other): return self
        def all(self): return self
        def item(self): return True
    def ones(*args, **kwargs):
        if probe_error: raise RuntimeError('driver failure')
        return Tensor()
    return types.SimpleNamespace(cuda=types.SimpleNamespace(
        is_available=lambda: available, is_bf16_supported=lambda: bf16,
        synchronize=lambda: None), ones=ones, isfinite=lambda x: x, bfloat16='bf16')


@pytest.mark.parametrize('available,bf16,probe_error,device,reason', [
    (True, True, False, 'cuda', None),
    (False, True, False, 'cpu', 'cuda_unavailable'),
    (True, False, False, 'cpu', 'cuda_bf16_unsupported'),
    (True, True, True, 'cpu', 'cuda_probe_failed'),
])
def test_auto_selects_cuda_or_cpu(monkeypatch, available, bf16, probe_error, device, reason):
    runtime = load_module(monkeypatch, 'runtime', fake_torch(available, bf16, probe_error))
    assert runtime.select_device('auto') == (device, reason)
    if reason:
        with pytest.raises(RuntimeError, match=reason): runtime.select_device('cuda')


def test_explicit_cpu_does_not_touch_cuda(monkeypatch):
    runtime = load_module(monkeypatch, 'runtime', types.SimpleNamespace())
    assert runtime.select_device('cpu') == ('cpu', None)
    with pytest.raises(ValueError): runtime.select_device('mps')


@pytest.mark.parametrize('device', ['auto', 'cpu', 'cuda'])
def test_real_config_accepts_devices(tmp_path, device):
    assert real_settings(tmp_path, device=device).device == device
    with pytest.raises(ValidationError): real_settings(tmp_path, device=device, precision='float32')
    with pytest.raises(ValidationError): real_settings(tmp_path, device='mps')


def test_default_real_device_is_auto(tmp_path, monkeypatch):
    monkeypatch.delenv('DEVICE', raising=False)
    settings = Settings(_env_file=None, music_provider='yue2', lyrics_provider='user',
        precision='bfloat16', model_id='model', model_revision='revision', decoder_revision='vae')
    assert settings.device == 'auto'


def test_preflight_retains_selected_device(tmp_path, monkeypatch):
    settings = real_settings(tmp_path)
    class Process:
        def wait(self, **kwargs): return 0
    def spawn(command, config, **kwargs):
        assert YuE2Music.child_environment(config)['DEVICE'] == 'auto'
        Path(command[command.index('--report') + 1]).write_text(json.dumps(dict(
            device='cpu', backend='torch-eager', fallback_reason='cuda_unavailable',
            model_initialized=True, verified_weights=True)))
        return Process()
    monkeypatch.setattr(YuE2Music, '_spawn', spawn)
    monkeypatch.setattr(YuE2Music, '_terminate', lambda *_: None)
    YuE2Music.preflight(settings)
    monkeypatch.setenv('DEVICE', 'cuda')
    assert settings.device == 'auto'
    assert YuE2Music.child_environment(settings)['DEVICE'] == 'cpu'
    assert settings.runtime_metadata['fallback_reason'] == 'cuda_unavailable'
    assert settings.runtime_metadata['backend'] == 'torch-eager'
    if hasattr(os, 'fork'):
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(read_fd)
            os.write(write_fd, YuE2Music.child_environment(settings)['DEVICE'].encode())
            os._exit(0)
        os.close(write_fd)
        try:
            assert os.read(read_fd, 64) == b'cpu'
            assert os.waitpid(pid, 0)[1] == 0
        finally:
            os.close(read_fd)


def test_unresolved_auto_cannot_start_a_job(tmp_path):
    provider = YuE2Music(real_settings(tmp_path), tmp_path / 'output.wav')
    request = dict(operation='generate', language='English', vocal_type='Instrumental',
        lyrics={'mode': 'user', 'text': '[Verse]\nTest'}, seed=7)
    with pytest.raises(ProviderError, match='initialization_failure'):
        provider.generate(request, lambda *_: None, lambda: None)


def test_weights_checked_before_device_selection(monkeypatch, tmp_path):
    preflight = load_module(monkeypatch, 'preflight', types.SimpleNamespace())
    monkeypatch.setattr(sys, 'argv', ['preflight.py', '--require-weights'])
    lock = json.loads((ROOT / 'packaging/yue2/model-lock.json').read_text())
    for key, value in [('MODEL_ID', lock['model']['repo']),
                       ('MODEL_REVISION', lock['model']['revision']),
                       ('DECODER_REVISION', lock['vae']['revision'])]:
        monkeypatch.setenv(key, value)
    monkeypatch.setenv('WEIGHTS_DIR', str(tmp_path))
    monkeypatch.setattr(preflight, 'select_device', lambda *_: pytest.fail('fallback hid missing weights'))
    with pytest.raises(RuntimeError, match='weights are required'): preflight.main()


def test_model_load_failure_does_not_trigger_cpu_retry(monkeypatch, tmp_path):
    torch = types.SimpleNamespace(__version__='test', version=types.SimpleNamespace(cuda=None),
                                 set_num_threads=lambda *_: None)
    preflight = load_module(monkeypatch, 'preflight', torch)
    selections = []
    monkeypatch.setattr(preflight, 'select_device', lambda device: (selections.append(device) or ('cpu', 'cuda_unavailable')))
    monkeypatch.setattr(preflight, 'verify_weights', lambda *_: True)
    monkeypatch.setattr(sys, 'argv', ['preflight.py', '--load-model', '--report', str(tmp_path / 'report.json')])
    class Pipeline:
        @staticmethod
        def from_pretrained(*args, **kwargs): raise RuntimeError('broken model weights')
    monkeypatch.setitem(sys.modules, 'yue2', types.SimpleNamespace(YuE2Pipeline=Pipeline))
    monkeypatch.setenv('DEVICE', 'auto')
    with pytest.raises(RuntimeError, match='broken model weights'): preflight.main()
    assert selections == ['auto'] and not (tmp_path / 'report.json').exists()


def test_short_audio_requires_smoke_mode(monkeypatch):
    np = pytest.importorskip('numpy')
    pytest.importorskip('soundfile')
    validate = load_module(monkeypatch, 'validate', types.SimpleNamespace())
    audio = np.ones((48000, 2), dtype=np.float32) * .01
    assert not validate.samples_metrics(audio, 48000)['passed']
    assert validate.samples_metrics(audio, 48000, test_smoke=True)['passed']
    for invalid in (audio[:0], audio * 0, audio * np.nan):
        assert not validate.samples_metrics(invalid, 48000, test_smoke=True)['passed']
    assert not validate.samples_metrics(audio, 44100, test_smoke=True)['passed']


def test_inference_failure_stays_explicit(tmp_path):
    (tmp_path / 'failure.json').write_text('{"category":"cuda_oom"}')
    assert YuE2Music._failure_code(tmp_path) == ('resource_exhaustion', False)
    (tmp_path / 'failure.json').write_text('{"category":"cpu_oom"}')
    assert YuE2Music._failure_code(tmp_path) == ('resource_exhaustion', False)


@pytest.mark.parametrize('failure', ['exit', 'missing_report', 'timeout'])
def test_preflight_failure_never_resolves_auto(monkeypatch, tmp_path, failure):
    settings = real_settings(tmp_path)
    class Process:
        def wait(self, **kwargs):
            if failure == 'timeout': raise subprocess.TimeoutExpired('preflight', 1)
            return 1 if failure == 'exit' else 0
    monkeypatch.setattr(YuE2Music, '_spawn', lambda *_args, **_kwargs: Process())
    monkeypatch.setattr(YuE2Music, '_terminate', lambda *_: None)
    with pytest.raises(ProviderError, match='initialization_failure'):
        YuE2Music.preflight(settings)
    assert settings.inference_device == 'auto' and not settings.runtime_metadata


def test_corrupt_weights_are_not_a_device_fallback(monkeypatch, tmp_path):
    preflight = load_module(monkeypatch, 'preflight', types.SimpleNamespace())
    lock = dict(model=dict(repo='model', revision='model-rev'), vae=dict(repo='vae', revision='vae-rev'))
    manifest = {}
    for key in lock:
        (tmp_path / key).mkdir()
        (tmp_path / key / 'weights').write_bytes(b'correct weights')
        manifest[key] = dict(lock[key], files=[dict(file='weights',
            sha256=hashlib.sha256(b'correct weights').hexdigest())])
    (tmp_path / 'verified.json').write_text(json.dumps(manifest))
    monkeypatch.setenv('WEIGHTS_DIR', str(tmp_path))
    monkeypatch.setenv('YUE2_MODEL_DIR', str(tmp_path / 'model'))
    monkeypatch.setenv('YUE2_VAE_DIR', str(tmp_path / 'vae'))
    assert preflight.verify_weights(lock, True)
    (tmp_path / 'model' / 'weights').write_bytes(b'corrupt weights')
    with pytest.raises(RuntimeError, match='checksum mismatch'):
        preflight.verify_weights(lock, True)


@pytest.mark.parametrize('snapshot_flag', [True, 'true', 1])
def test_smoke_cannot_relax_production_job(monkeypatch, tmp_path, snapshot_flag):
    provider = YuE2Music(real_settings(tmp_path, device='cpu'), tmp_path / 'output.wav')
    monkeypatch.setattr(provider, '_spawn', lambda *_args, **_kwargs: pytest.fail('mismatched smoke job started'))
    request = dict(operation='generate', language='English', vocal_type='Instrumental',
        lyrics={'mode': 'user', 'text': '[Verse]\nTest'}, seed=7, yue2_test_smoke=snapshot_flag)
    with pytest.raises(ProviderError, match='incompatible_envelope'):
        provider.generate(request, lambda *_: None, lambda: None)


@pytest.mark.parametrize('device,category', [('cuda', 'cuda_oom'), ('cpu', 'cpu_oom')])
def test_failed_job_does_not_change_startup_device(monkeypatch, tmp_path, device, category):
    settings = real_settings(tmp_path)
    settings.set_yue2_runtime(dict(device=device, backend='torch' if device == 'cuda' else 'torch-eager',
        fallback_reason=None if device == 'cuda' else 'cuda_unavailable'))
    before = settings.runtime_metadata
    runner = tmp_path / 'fail.py'
    runner.write_text('import sys,json\nfrom pathlib import Path\n'
        'out=Path(sys.argv[2]); out.mkdir(parents=True)\n'
        '(out/"failure.json").write_text(json.dumps({"category":' + repr(category) + '}))\n'
        'sys.exit(3)\n')
    settings.yue2_runner = runner
    monkeypatch.setattr(YuE2Music, 'preflight', lambda *_: pytest.fail('job attempted device fallback'))
    provider = YuE2Music(settings, tmp_path / 'output.wav')
    request = dict(operation='generate', language='English', vocal_type='Instrumental',
        lyrics={'mode': 'user', 'text': '[Verse]\nTest'}, seed=7, instruments=['Guitar'],
        genre='Folk', mood='Calm', tempo='Medium', brief='test')
    with pytest.raises(ProviderError, match='resource_exhaustion') as error:
        provider.generate(request, lambda *_: None, lambda: None)
    assert not error.value.retryable and settings.runtime_metadata == before
    assert not provider.output.exists()


@pytest.mark.parametrize('device', ['cpu', 'cuda'])
def test_tensor_oom_reports_actual_device(monkeypatch, tmp_path, device):
    pytest.importorskip('numpy')
    pytest.importorskip('soundfile')
    class OutOfMemoryError(RuntimeError): pass
    torch = types.SimpleNamespace(cuda=types.SimpleNamespace(
        OutOfMemoryError=OutOfMemoryError, is_available=lambda: True), set_num_threads=lambda *_: None)
    class Pipeline:
        @staticmethod
        def from_pretrained(*args, **kwargs): raise OutOfMemoryError('tensor allocation failed')
    monkeypatch.setitem(sys.modules, 'yue2', types.SimpleNamespace(YuE2Pipeline=Pipeline))
    generate = load_module(monkeypatch, 'generate', torch)
    request = tmp_path / 'request.json'
    request.write_text('{}')
    output = tmp_path / 'output'
    monkeypatch.setattr(sys, 'argv', ['generate.py', str(request), str(output)])
    monkeypatch.setenv('DEVICE', device)
    assert generate.main() == 3
    assert json.loads((output / 'failure.json').read_text())['category'] == device + '_oom'
