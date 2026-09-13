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


def test_demo_commands_fail_when_api_is_unavailable():
    for name in ('seed-demo', 'smoke'):
        result = subprocess.run(['bash', str(ROOT / f'scripts/{name}.sh')], capture_output=True, env=dict(os.environ, API_BASE_URL='http://127.0.0.1:1'), timeout=15)
        assert result.returncode != 0
        assert b'demo_check_failed' in result.stderr


def test_shell_scripts_have_lf_and_valid_bash_syntax():
    for path in (ROOT / 'scripts').glob('*.sh'):
        assert b'\r' not in path.read_bytes(), path.name
        subprocess.run(['bash', '-n', str(path)], check=True)


def test_git_checkout_preserves_lf_with_autocrlf(tmp_path):
    if not shutil.which('git'):
        import pytest
        pytest.skip('Git checkout check runs on the authoring host; runtime images omit Git')
    checkout = tmp_path / 'checkout'
    checkout.mkdir()
    commands = ['git', '-c', 'core.autocrlf=true', '-C', str(checkout)]
    subprocess.run([*commands, 'init', '--quiet'], check=True)
    shutil.copy(ROOT / '.gitattributes', checkout / '.gitattributes')
    shutil.copytree(ROOT / 'scripts', checkout / 'scripts')
    subprocess.run([*commands, 'add', '.gitattributes', 'scripts'], check=True, capture_output=True)
    exported = tmp_path / 'exported'
    subprocess.run([*commands, 'checkout-index', '--all', '--prefix=' + exported.as_posix() + '/'], check=True)
    for path in (exported / 'scripts').glob('*.sh'):
        assert b'\r' not in path.read_bytes(), path.name
