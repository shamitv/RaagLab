"""Original, deterministic demo providers; no external audio or lyrics."""
import math
import json
import os
import random
import signal
import struct
import subprocess
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Callable, Protocol
from museforge.domain import ProviderError, Lyrics, capabilities

STATIC = '[Verse]\nMorning opens quiet doors\nLight is dancing on the floor\n\n[Chorus]\nCarry every little spark\nLet it glow against the dark\n'

class CancellationToken(Protocol):
    def __call__(self) -> None: ...

class LyricsProvider(Protocol):
    def capabilities(self) -> dict: ...
    def readiness(self) -> str: ...
    def normalize(self, request: dict) -> dict: ...
    def generate(self, request: dict, progress_callback: Callable, cancellation_token: CancellationToken) -> dict: ...

class MusicProvider(Protocol):
    def capabilities(self) -> dict: ...
    def readiness(self) -> str: ...
    def normalize(self, request: dict) -> dict: ...
    def generate(self, request: dict, progress_callback: Callable, cancellation_token: CancellationToken) -> Path: ...

class DemoLyrics:
    def capabilities(self): return capabilities()
    def readiness(self): return 'ready'
    def normalize(self, request):
        try: Lyrics.model_validate(request['lyrics'])
        except (ValueError, KeyError): raise ProviderError('invalid_request') from None
        return request
    def generate(self, request, progress_callback, cancellation_token):
        self.normalize(request)
        cancellation_token()
        mode = request['lyrics']['mode']
        if mode == 'user':
            content = request['lyrics']['text']
        elif mode == 'static':
            content = STATIC
        else:
            word = random.Random(request['seed']).choice(['morning', 'river', 'starlight', 'garden'])
            content = f'[Verse]\nWe follow the {word} today\nAnd find a little song along the way\n\n[Chorus]\nA moment held, a new day near\nWe carry all our music here\n'
        return {'text': content, 'source': mode, 'provider_revision': '1',
                'fixture_id': 'morning-spark' if mode == 'static' else None,
                'fixture_revision': '1' if mode == 'static' else None}

class MockMusic:
    def __init__(self, output: Path): self.output = output
    def capabilities(self): return capabilities()
    def readiness(self): return 'ready'
    def normalize(self, request):
        if not 5 <= request['duration_seconds'] <= 30:
            raise ProviderError('invalid_request')
        return request
    def generate(self, request, progress_callback, cancellation_token):
        self.normalize(request)
        rng = random.Random(request['seed'])
        notes = [rng.choice([220, 261.6256, 293.6648, 329.6276, 391.9954]) for _ in range(16)]
        rate, frames = 44100, 44100 * request['duration_seconds']
        with wave.open(str(self.output), 'wb') as audio:
            audio.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
            for start in range(0, frames, 4096):
                cancellation_token()
                block = bytearray()
                for i in range(start, min(start + 4096, frames)):
                    t = i / rate
                    frequency = notes[int(t * 2) % len(notes)]
                    envelope = min(1, t * 8, (frames - i) / rate * 8) * (0.65 + 0.35 * math.sin(math.pi * (t * 2 % 1)))
                    left = int(6500 * envelope * (math.sin(2 * math.pi * frequency * t) + .25 * math.sin(2 * math.pi * frequency / 2 * t)))
                    right = int(left * .9)
                    block.extend(struct.pack('<hh', left, right))
                audio.writeframesraw(block)
        return self.output


class YuE2Music:
    """Application adapter for the pinned YuE2 inference child process."""

    _active_processes = set()
    _process_lock = threading.Lock()

    def __init__(self, settings, output: Path):
        self.settings = settings
        self.output = output
        self.metadata = {}

    def capabilities(self):
        return capabilities('yue2', model_id=self.settings.model_id,
                            model_revision=self.settings.model_revision,
                            decoder_revision=self.settings.decoder_revision)

    def readiness(self):
        return 'ready'

    @staticmethod
    def preflight(settings):
        process = None
        try:
            with tempfile.TemporaryDirectory(prefix='yue2-preflight-') as folder:
                report_path = Path(folder) / 'report.json'
                process = YuE2Music._spawn(
                    [sys.executable, str(settings.yue2_preflight), '--require-weights', '--load-model',
                     '--report', str(report_path)], settings, cwd=str(settings.yue2_preflight.parent))
                if process.wait(timeout=settings.yue2_warmup_timeout_seconds) != 0:
                    raise ProviderError('initialization_failure')
                report = json.loads(report_path.read_text())
                if not report.get('model_initialized') or not report.get('verified_weights'):
                    raise ValueError('incomplete preflight')
                settings.set_yue2_runtime(report)
                return report
        except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            raise ProviderError('initialization_failure') from None
        finally:
            if process is not None:
                YuE2Music._terminate(process)
                with YuE2Music._process_lock:
                    YuE2Music._active_processes.discard(process)

    @staticmethod
    def child_environment(settings):
        env = os.environ.copy()
        env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HOME=str(settings.cache_dir),
                   WEIGHTS_DIR=str(settings.weights_dir), YUE2_MODEL_DIR=str(settings.yue2_model_dir),
                   YUE2_VAE_DIR=str(settings.yue2_vae_dir),
                   YUE2_MEMORY_BUDGET_GIB=str(settings.yue2_memory_budget_gib),
                   YUE2_OFFLOAD_AR='1' if settings.yue2_offload_ar else '0',
                   DEVICE=settings.inference_device, YUE2_CPU_THREADS=str(settings.yue2_cpu_threads),
                   MODEL_ID=settings.model_id, MODEL_REVISION=settings.model_revision,
                   DECODER_REVISION=settings.decoder_revision)
        return env

    @staticmethod
    def _spawn(command, settings, **kwargs):
        env = YuE2Music.child_environment(settings)
        if sys.platform == 'linux':
            control_read, control_write = os.pipe()
            try:
                process = subprocess.Popen(
                    [sys.executable, '-m', 'museforge.worker.inference_supervisor',
                     '--control-fd', str(control_read),
                     '--lock-path', '/tmp/museforge-yue2.inference.lock', '--', *command],
                    env=env, start_new_session=True, pass_fds=(control_read,), **kwargs)
                process._yue2_control_fd = control_write
                process._yue2_supervised = True
            except BaseException:
                os.close(control_write)
                raise
            finally:
                os.close(control_read)
        else:
            process = subprocess.Popen(command, env=env, start_new_session=os.name != 'nt', **kwargs)
        with YuE2Music._process_lock:
            YuE2Music._active_processes.add(process)
        return process

    @classmethod
    def shutdown(cls):
        with cls._process_lock:
            processes = list(cls._active_processes)
        for process in processes:
            cls._terminate(process)

    def normalize(self, request):
        if request.get('operation') != 'generate':
            raise ProviderError('unsupported_capability')
        if request.get('language') != 'English':
            raise ProviderError('unsupported_capability')
        if request.get('vocal_type') != 'Instrumental':
            raise ProviderError('unsupported_capability')
        if request.get('iteration_instruction') is not None:
            raise ProviderError('unsupported_capability')
        lyrics = request.get('lyrics') or {}
        if lyrics.get('mode') != 'user' or not lyrics.get('text', '').strip():
            raise ProviderError('invalid_request')
        if isinstance(request.get('seed'), bool) or not isinstance(request.get('seed'), int):
            raise ProviderError('invalid_request')
        return request

    def _style(self, request):
        instruments = ', '.join(request['instruments'])
        return (f"English {request['genre'].lower()} instrumental music, {request['mood'].lower()} mood, "
                f"{request['tempo'].lower()} tempo, featuring {instruments}. {request['brief'].strip()}. "
                'A complete short song with a natural ending.')

    @staticmethod
    def _terminate(process, grace=5):
        with YuE2Music._process_lock:
            control_fd = getattr(process, '_yue2_control_fd', None)
            process._yue2_control_fd = None
        if control_fd is not None:
            os.close(control_fd)
        if getattr(process, '_yue2_supervised', False):
            # The guardian retains the GPU lock until inference has been reaped.
            process.wait(timeout=15)
            return
        if process.poll() is not None:
            return
        try:
            if os.name == 'nt':
                process.terminate()
            else:
                os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            if os.name == 'nt':
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)

    @staticmethod
    def _failure_code(folder):
        failure = folder / 'failure.json'
        if not failure.exists():
            return ('malformed_media', False) if (folder / 'validation.json').exists() else ('transient_failure', True)
        try:
            category = json.loads(failure.read_text()).get('category')
        except (OSError, ValueError):
            category = None
        if category in {'cuda_oom', 'cpu_oom'}:
            return 'resource_exhaustion', False
        if category in {'missing_weights', 'initialization_error', 'device_unavailable'}:
            return 'initialization_failure', False
        if category in {'cancelled', 'deadline_exceeded'}:
            return category, False
        return 'transient_failure', True

    def generate(self, request, progress_callback, cancellation_token):
        self.normalize(request)
        if self.settings.inference_device not in {'cpu', 'cuda'}:
            raise ProviderError('initialization_failure')
        smoke = request.get('yue2_test_smoke', False)
        if not isinstance(smoke, bool) or smoke != self.settings.yue2_test_smoke:
            raise ProviderError('incompatible_envelope')
        progress_callback('composing_music')
        self.output.parent.mkdir(parents=True, exist_ok=True)
        work_dir = Path(tempfile.mkdtemp(prefix='.yue2-', dir=self.output.parent))
        input_path = work_dir / 'input.json'
        output_dir = work_dir / 'output'
        log_path = work_dir / 'process.log'
        yue_request = {'style': self._style(request), 'lyrics': request['lyrics']['text'],
                       'seed': request['seed'], 'cot': 'off' if smoke else 'full'}
        if smoke:
            yue_request['semantic_sampling'] = dict(temperature=0.0, top_k=1, min_tokens=32, max_tokens=32)
        input_path.write_text(json.dumps(yue_request, ensure_ascii=False) + '\n')
        command = [sys.executable, str(self.settings.yue2_runner), str(input_path), str(output_dir)]
        if self.settings.yue2_offload_ar:
            command.append('--offload-ar')
        if smoke:
            command.append('--test-smoke')
        started = time.monotonic()
        process = None
        try:
            with log_path.open('w', encoding='utf-8') as log:
                process = self._spawn(command, self.settings, stdout=log, stderr=subprocess.STDOUT)
                while process.poll() is None:
                    cancellation_token()
                    if time.monotonic() - started >= self.settings.yue2_process_timeout_seconds:
                        self._terminate(process)
                        raise ProviderError('deadline_exceeded')
                    time.sleep(.2)
            if process.returncode != 0:
                code, retryable = self._failure_code(output_dir)
                raise ProviderError(code, retryable)
            source = output_dir / 'audio.flac'
            validation_path = output_dir / 'validation.json'
            if not source.is_file():
                raise ProviderError('malformed_media')
            try:
                import numpy as np
                import soundfile as sf
                audio, rate = sf.read(source, dtype='float32', always_2d=True)
                if rate != 48000 or audio.shape[1] != 2 or len(audio) <= (0 if smoke else 5 * rate):
                    raise ValueError
                if not np.isfinite(audio).all() or not np.any(audio):
                    raise ValueError
                sf.write(self.output, audio, rate, format='WAV', subtype='PCM_16')
            except (ImportError, OSError, ValueError, RuntimeError):
                raise ProviderError('malformed_media') from None
            try:
                validation = json.loads(validation_path.read_text()) if validation_path.exists() else {}
            except (OSError, ValueError):
                validation = {}
            self.metadata = {
                'device': self.settings.inference_device,
                'backend': 'torch' if self.settings.inference_device == 'cuda' else 'torch-eager',
                'provider_revision': self.settings.provider_revision,
                'runtime_revision': '0edaf2f4053ef4731334b8329834b107977f9637',
                'fallback_reason': self.settings.runtime_metadata.get('fallback_reason'),
                'test_smoke': smoke,
                'decoder_revision': self.settings.decoder_revision,
                'requested_duration_seconds': request.get('duration_seconds'),
                'actual_duration_seconds': len(audio) / rate,
                'seed': request['seed'],
                'elapsed_seconds': time.monotonic() - started,
                'provider_output_format': 'FLAC',
                'published_format': 'WAV/PCM_16',
                'sample_rate': rate,
                'channels': int(audio.shape[1]),
                'effective_settings': {
                    'style': yue_request['style'], 'cot': yue_request['cot'],
                    'semantic_sampling': yue_request.get('semantic_sampling'),
                    'offload_ar': self.settings.yue2_offload_ar,
                    'memory_budget_gib': self.settings.yue2_memory_budget_gib,
                    'model_id': self.settings.model_id,
                    'model_revision': self.settings.model_revision,
                },
                'gpu_resource': {key: validation[key] for key in (
                    'torch_peak_allocated_bytes', 'torch_peak_reserved_bytes') if key in validation},
                'validation': validation,
            }
            return self.output
        except ProviderError:
            if process is not None and process.poll() is None:
                self._terminate(process)
            raise
        except OSError as exc:
            raise ProviderError('initialization_failure' if exc.errno in (2, 13) else 'transient_failure',
                                exc.errno not in (2, 13)) from None
        finally:
            if process is not None:
                self._terminate(process)
                with self._process_lock:
                    self._active_processes.discard(process)
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)
