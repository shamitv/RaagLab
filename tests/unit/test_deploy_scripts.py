from pathlib import Path
import subprocess
import shutil
import os
import pytest

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / 'scripts' / 'deploy'


def test_deployment_scripts_are_valid_bash_and_scoped():
    for path in DEPLOY.glob('*.sh'):
        assert b'\r' not in path.read_bytes(), path
        if shutil.which('bash'):
            result = subprocess.run(['bash', '-n', str(path)], capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
    text = (DEPLOY / 'lib.sh').read_text()
    assert 'museforge-ubuntu1' in text
    assert 'docker stop --time 30 $containers' in text


def test_backup_and_restore_refuse_unsafe_or_incomplete_inputs():
    rollback = (DEPLOY / 'rollback.sh').read_text()
    restore = (DEPLOY / 'restore.sh').read_text()
    assert 'requires a verified backup directory' in rollback
    assert 'PROJECT_NAME" != museforge-ubuntu1' in restore
    assert 'sha256sum -c SHA256SUMS' in restore


def test_real_mode_selects_cpu_without_gpu_override():
    lib = (DEPLOY / 'lib.sh').read_text()
    assert 'YUE2_DEVICE must be auto, cpu, or cuda' in lib
    assert 'host_gpu_runtime_available' in lib
    assert 'compose.yue2.gpu.yaml' in lib
    assert '[[ "$device" == cuda ]]' in lib
    assert '[[ "$device" == auto ]]' in lib


def test_cpu_gate_requires_normal_provenance_and_resource_evidence():
    verifier = (ROOT / 'scripts' / 'verify-yue2-devices.py').read_text()
    d03 = (ROOT / 'scripts' / 'verify-d03.py').read_text()
    overlay = (ROOT / 'compose.yue2.test.yaml').read_text()
    assert '--normal' in verifier
    assert 'YUE2_MEMORY_LIMIT_GIB' in verifier
    assert 'DeviceRequests' in verifier
    assert "expected_fallback = 'cuda_unavailable' if settings.device == 'auto' else None" in d03
    assert 'mem_limit: ${YUE2_MEMORY_LIMIT_GIB:-28}g' in overlay
    assert 'DEVICE: ${YUE2_DEVICE:-cpu}' in overlay
    assert 'user: "${MUSEFORGE_CONTAINER_UID:-1000}:${MUSEFORGE_CONTAINER_GID:-1000}"' in overlay


@pytest.mark.skipif(not shutil.which('bash'), reason='bash is required for deployment behavior checks')
def test_mode_file_rewrite_does_not_duplicate_saved_device(tmp_path):
    deploy_root = tmp_path / 'deploy'
    deploy_root.mkdir()
    (deploy_root / '.env').write_text(
        'APP_PORT=18000\nDATABASE_URL=postgresql+psycopg://u:p@db:5432/d\n'
        'BROKER_URL=amqp://u:p@broker:5672//\nWORKSPACE_ID=00000000-0000-4000-8000-000000000001\n'
        'YUE2_DEVICE=cpu\nMUSIC_PROVIDER=mock\nDEVICE=cpu\n', encoding='utf-8')
    command = 'source scripts/deploy/lib.sh; write_mode_env real; write_mode_env real; grep "^YUE2_DEVICE=" "$MUSEFORGE_DEPLOY_ROOT/.mode.env"'
    result = subprocess.run(['bash', '-lc', command], cwd=ROOT, env=dict(os.environ, MUSEFORGE_DEPLOY_ROOT=str(deploy_root)),
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines() == ['YUE2_DEVICE=cpu']
