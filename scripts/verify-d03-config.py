"""Non-mutating Compose checks using disposable custom deployment settings."""
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='d03-compose-config-') as directory:
        temporary = Path(directory)
        (temporary / '.env').write_text(
            'DATABASE_URL=postgresql+psycopg://custom:config-test-only@db/custom\n'
            'BROKER_URL=amqp://custom:config-test-only@broker:5672//\n'
            'WORKSPACE_ID=00000000-0000-4000-8000-000000000099\n')
        output = subprocess.check_output(['docker', 'compose', '--project-directory', directory,
            '--env-file', str(temporary / '.env'), '--profile', 'yue2', '-f', str(root / 'compose.yaml'),
            '-f', str(root / 'compose.yue2.yaml'), 'config', '--format', 'json'], text=True)
        config = json.loads(output)
        services = config['services']
        for name in ('DATABASE_URL', 'BROKER_URL', 'WORKSPACE_ID'):
            values = [services[service]['environment'][name] for service in ('api', 'dispatcher', 'worker-yue2')]
            assert len(set(values)) == 1
        worker = services['worker-yue2']
        assert worker['deploy']['resources']['reservations']['devices'] == [
            {'capabilities': ['gpu'], 'driver': 'nvidia', 'count': 1}]
        weights = next(mount for mount in worker['volumes'] if mount['target'] == '/weights')
        artifacts = next(mount for mount in worker['volumes'] if mount['target'].endswith('/artifacts'))
        assert weights['read_only'] and not artifacts.get('read_only', False)
        assert services['api']['volumes'][0]['read_only']
        assert 'worker-mock' not in services, 'YuE2 profile unexpectedly enabled mock worker'
        print('Custom credentials/workspace, GPU reservation, and mount access checks passed.')


if __name__ == '__main__':
    main()
