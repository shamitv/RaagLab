"""Disposable offline checks: strict CUDA, explicit CPU, and startup failures."""
import argparse
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', default='museforge-yue2:0.1.6')
    args = parser.parse_args()
    weights_volume = os.environ.get('MUSEFORGE_YUE2_WEIGHTS_VOLUME', 'museforge-yue2-weights')
    root = Path(__file__).resolve().parents[1]
    evidence = root / 'test-results/yue2-devices/startup'
    evidence.mkdir(parents=True, exist_ok=True)
    environment = dict(MUSIC_PROVIDER='yue2', LYRICS_PROVIDER='user', DEVICE='auto',
        PRECISION='bfloat16', MODEL_ID='m-a-p/YuE2-3B',
        MODEL_REVISION='29b3558dd46954a0cd9021dc76d5c91864a0f1c7',
        DECODER_REVISION='9a94e1d0ea9f8087e98f77fa88df4a4068104d2a',
        WEIGHTS_DIR='/weights', YUE2_MODEL_DIR='/weights/model', YUE2_VAE_DIR='/weights/vae',
        YUE2_PREFLIGHT='/opt/yue2-test/preflight.py', YUE2_CPU_THREADS='4')
    code = '''import json, sys
from museforge.config import Settings
from museforge.domain import ProviderError
from museforge.providers import YuE2Music
settings = Settings(_env_file=None)
try:
    YuE2Music.preflight(settings)
except ProviderError as exc:
    print(json.dumps(dict(error=exc.code, runtime=settings.runtime_metadata)))
    sys.exit(78)
print(json.dumps(settings.runtime_metadata))
'''
    results = {}
    for name, updates, exit_code in [
        ('strict-cuda-no-gpu', {'DEVICE': 'cuda'}, 78),
        ('explicit-cpu', {'DEVICE': 'cpu'}, 0),
        ('missing-weights-auto', {'WEIGHTS_DIR': '/missing'}, 78),
        ('wrong-identity-auto', {'MODEL_REVISION': 'wrong'}, 78),
        ('warmup-timeout-auto', {'YUE2_WARMUP_TIMEOUT_SECONDS': '1'}, 78),
    ]:
        command = ['docker', 'run', '--rm', '--init', '--network', 'none', '--memory', '28g',
                   '-v', f'{weights_volume}:/weights:ro']
        for key, value in (environment | updates).items():
            command += ['-e', key + '=' + value]
        command += [args.image, 'python', '-c', code]
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=180)
        (evidence / (name + '.log')).write_text(result.stdout)
        assert result.returncode == exit_code, (name, result.returncode, result.stdout)
        report = json.loads(result.stdout.strip().splitlines()[-1])
        if exit_code:
            assert report == dict(error='initialization_failure', runtime={}), report
        else:
            assert report['device'] == 'cpu' and report['fallback_reason'] is None
            assert report['backend'] == 'torch-eager'
        results[name] = dict(exit_code=exit_code, report=report)
    (evidence / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    print('Strict CUDA, explicit CPU, missing weights/identity, and timeout checks passed.')


if __name__ == '__main__':
    main()
