from pathlib import Path
import subprocess
import shutil

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
