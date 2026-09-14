"""Real API/queue/worker smoke flow, in a unique CPU or CUDA test project."""
import argparse
import os
from pathlib import Path
import subprocess
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpu', action='store_true', help='Expose CUDA and expect CUDA selection')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    project = 'museforge-yue2-test-' + uuid4().hex[:12]
    evidence = root / 'test-results/yue2-devices' / project
    evidence.mkdir(parents=True)
    env = dict(os.environ, YUE2_DEVICE='auto', YUE2_TEST_SMOKE='true',
               YUE2_EVIDENCE_DIR=str(evidence))
    compose = ['docker', 'compose', '--project-name', project, '--profile', 'yue2',
               '-f', 'compose.yaml', '-f', 'compose.yue2.yaml']
    if args.gpu:
        compose += ['-f', 'compose.yue2.gpu.yaml']
    compose += ['-f', 'compose.yue2.test.yaml']
    def run(*command, timeout=1800):
        return subprocess.run([*compose, *command], cwd=root, env=env, check=True, timeout=timeout)
    try:
        run('build', 'api', 'migrate', 'dispatcher', 'worker-yue2', 'yue2-smoke-tests')
        run('up', '-d', '--wait', '--wait-timeout', '1000', 'api', 'dispatcher', 'worker-yue2')
        run('run', '--rm', 'yue2-smoke-tests', 'python', '/verification/verify-d03.py',
            '--smoke', '--expected-device', 'cuda' if args.gpu else 'cpu')
        print(f'YuE2 integration passed. Evidence: {evidence}')
    finally:
        # Only this UUID-named test project is cleaned. External weights remain.
        with (evidence / 'services.log').open('w') as log:
            subprocess.run([*compose, 'logs', '--no-color'], cwd=root, env=env,
                           stdout=log, stderr=subprocess.STDOUT, timeout=60)
        subprocess.run([*compose, 'down', '--volumes', '--remove-orphans'],
                       cwd=root, env=env, check=True, timeout=120)


if __name__ == '__main__':
    main()
