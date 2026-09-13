import hashlib
import json
from pathlib import Path
import platform

import torch


def main():
    assert torch.cuda.is_available(), 'CUDA is required; no CPU fallback'
    assert torch.cuda.is_bf16_supported(), 'BF16 is required'
    x = torch.ones((256, 256), device='cuda', dtype=torch.bfloat16)
    assert torch.isfinite(x @ x).all().item()
    torch.cuda.synchronize()
    lock = json.loads(Path('model-lock.json').read_text())
    manifest_path = Path('/weights/verified.json')
    if manifest_path.exists():
        verified = json.loads(manifest_path.read_text())
        for key in ('model', 'vae'):
            assert verified[key]['revision'] == lock[key]['revision']
            assert verified[key]['repo'] == lock[key]['repo']
            for item in verified[key]['files']:
                path = Path('/weights') / key / item['file']
                with path.open('rb') as stream:
                    assert hashlib.file_digest(stream, 'sha256').hexdigest() == item['sha256']
    print(json.dumps({'python': platform.python_version(), 'torch': torch.__version__,
                      'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(),
                      'capability': torch.cuda.get_device_capability(), 'bf16': True,
                      'gpu_total_bytes': torch.cuda.get_device_properties(0).total_memory,
                      'verified_weights': manifest_path.exists(), 'models': lock}, indent=2))


if __name__ == '__main__':
    main()
