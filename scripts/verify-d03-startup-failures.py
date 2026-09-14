"""Disposable real-worker startup failures with explicit exit-code evidence."""
import json
from pathlib import Path
import subprocess


def main():
    root = Path(__file__).resolve().parents[1]
    evidence = root / 'test-results/d03-real-acceptance'
    evidence.mkdir(parents=True, exist_ok=True)
    compose = ['docker', 'compose', '--project-name', 'museforge-d03-review', '--profile', 'yue2',
               '-f', 'compose.yaml', '-f', 'compose.yue2.yaml']
    results = {}
    for name, setting in (('missing-weights', 'WEIGHTS_DIR=/missing'),
                          ('missing-model', 'YUE2_MODEL_DIR=/missing'),
                          ('wrong-identity', 'MODEL_REVISION=wrong')):
        result = subprocess.run([*compose, 'run', '--rm', '--no-deps', '-e', setting,
                                 'worker-yue2', 'python', '-m', 'museforge.worker'],
                                cwd=root, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=60)
        (evidence / (name + '.log')).write_text(result.stdout)
        assert result.returncode == 78 and 'yue2_preflight_failed' in result.stdout, name
        results[name] = {'exit_code': result.returncode, 'ready': False, 'fallback': False}
    env = {'MUSIC_PROVIDER': 'yue2', 'LYRICS_PROVIDER': 'user', 'DEVICE': 'cuda',
           'PRECISION': 'bfloat16', 'MODEL_ID': 'm-a-p/YuE2-3B',
           'MODEL_REVISION': '29b3558dd46954a0cd9021dc76d5c91864a0f1c7',
           'DECODER_REVISION': '9a94e1d0ea9f8087e98f77fa88df4a4068104d2a'}
    command = ['docker', 'run', '--rm', '--network', 'none']
    for name, value in env.items(): command.extend(['-e', name + '=' + value])
    command.extend(['museforge-d03-review-worker-yue2', 'python', '-c',
        "from museforge.providers import YuE2Music\nfrom museforge.config import Settings\n"
        "from museforge.domain import ProviderError\nimport sys\n"
        "try:\n YuE2Music.preflight(Settings())\n"
        "except ProviderError as e:\n print(e.code); sys.exit(78)\n"])
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=60)
    (evidence / 'missing-device.log').write_text(result.stdout)
    assert result.returncode == 78 and 'initialization_failure' in result.stdout
    results['missing-device'] = {'exit_code': 78, 'outcome': 'initialization_failure', 'fallback': False}
    (evidence / 'startup-failures.json').write_text(json.dumps(results, indent=2) + '\n')
    print('Missing weights/model/device and conflicting identity all failed startup without fallback.')


if __name__ == '__main__':
    main()
