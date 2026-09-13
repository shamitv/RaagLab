import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def test_setup_preserves_existing_env_even_without_engine(tmp_path):
    shutil.copytree(ROOT / 'scripts', tmp_path / 'scripts')
    shutil.copy(ROOT / '.env.example', tmp_path / '.env.example')
    # Fake unavailable engine avoids depending on the developer's Docker context.
    executable = tmp_path / 'bin'
    executable.mkdir()
    docker = executable / 'docker'
    docker.write_text('#!/bin/sh\nexit 1\n')
    docker.chmod(0o755)
    env = dict(os.environ, PATH=f'{executable}:/usr/bin:/bin')
    first = subprocess.run(['bash', 'scripts/setup.sh'], cwd=tmp_path, env=env, capture_output=True)
    assert first.returncode != 0
    target = tmp_path / '.env'
    assert target.read_text() == (tmp_path / '.env.example').read_text()
    assert target.stat().st_mode & 0o777 == 0o600
    target.write_text('# existing local values\nAPP_PORT=8123\n')
    second = subprocess.run(['bash', 'scripts/setup.sh'], cwd=tmp_path, env=env, capture_output=True)
    assert second.returncode != 0
    assert target.read_text() == '# existing local values\nAPP_PORT=8123\n'


def test_future_commands_do_not_report_success():
    for name in ('seed-demo', 'smoke'):
        result = subprocess.run(['bash', str(ROOT / f'scripts/{name}.sh')], capture_output=True)
        assert result.returncode == 2
        assert b'Not implemented' in result.stderr
