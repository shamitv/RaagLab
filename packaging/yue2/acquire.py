"""Download immutable public snapshots with hf, then verify every file."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from huggingface_hub import HfApi

ROOT = Path('/weights')
LOCK = json.loads(Path(__file__).with_name('model-lock.json').read_text())


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(ROOT).free < 12 * 2**30:
        raise RuntimeError('At least 12 GiB free is required for model acquisition')
    evidence = {}
    api = HfApi(token=False)
    for key in ('model', 'vae'):
        spec = LOCK[key]
        target = ROOT / key
        info = api.model_info(spec['repo'], revision=spec['revision'], files_metadata=True)
        assert info.sha == spec['revision'], 'Revision mismatch'
        files = [f for f in info.siblings if f.rfilename.endswith(
            ('.json', '.py', '.safetensors', '.tiktoken', '.md'))
            or f.rfilename == 'LICENSE' or f.rfilename.startswith('licenses/')]
        # Exclude examples and marketing assets; retain model code and notices.
        files = [f for f in files if not f.rfilename.startswith(('assets/', 'examples/'))]
        subprocess.run(['hf', 'download', spec['repo'], *[f.rfilename for f in files],
                        '--revision', spec['revision'], '--local-dir', str(target),
                        '--max-workers', '2'], check=True)
        verified = []
        for item in files:
            path = target / item.rfilename
            sha = hashlib.sha256()
            # Hub Git blobs use a header; LFS files use ordinary SHA-256.
            git_sha = hashlib.sha1(f'blob {path.stat().st_size}\0'.encode())
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                    sha.update(block)
                    git_sha.update(block)
            if item.lfs:
                assert sha.hexdigest() == item.lfs.sha256, f'Hash mismatch: {path.name}'
            else:
                assert git_sha.hexdigest() == item.blob_id, f'Hash mismatch: {path.name}'
            verified.append({'file': item.rfilename, 'bytes': path.stat().st_size,
                             'sha256': sha.hexdigest()})
        evidence[key] = {**spec, 'files': verified}
    (ROOT / 'verified.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print('Both pinned snapshots verified')


if __name__ == '__main__':
    main()
