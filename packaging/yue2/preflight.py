import hashlib
import json
import argparse
import os
from pathlib import Path
import platform

import torch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-weights', action='store_true')
    parser.add_argument('--load-model', action='store_true')
    args = parser.parse_args()
    assert torch.cuda.is_available(), 'CUDA is required; no CPU fallback'
    assert torch.cuda.is_bf16_supported(), 'BF16 is required'
    x = torch.ones((256, 256), device='cuda', dtype=torch.bfloat16)
    assert torch.isfinite(x @ x).all().item()
    torch.cuda.synchronize()
    lock = json.loads(Path(__file__).with_name('model-lock.json').read_text())
    weights_root = Path(os.environ.get('WEIGHTS_DIR', '/weights'))
    manifest_path = weights_root / 'verified.json'
    if args.require_weights:
        assert manifest_path.exists(), 'verified model weights are required'
    if manifest_path.exists():
        verified = json.loads(manifest_path.read_text())
        for key in ('model', 'vae'):
            assert verified[key]['revision'] == lock[key]['revision']
            assert verified[key]['repo'] == lock[key]['repo']
            for item in verified[key]['files']:
                model_root = Path(os.environ.get('YUE2_MODEL_DIR', str(weights_root / 'model')))
                vae_root = Path(os.environ.get('YUE2_VAE_DIR', str(weights_root / 'vae')))
                path = (model_root if key == 'model' else vae_root) / item['file']
                with path.open('rb') as stream:
                    assert hashlib.file_digest(stream, 'sha256').hexdigest() == item['sha256']
    result = {'python': platform.python_version(), 'torch': torch.__version__,
                      'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(),
                      'capability': torch.cuda.get_device_capability(), 'bf16': True,
                      'gpu_total_bytes': torch.cuda.get_device_properties(0).total_memory,
                      'verified_weights': manifest_path.exists(), 'models': lock}
    if args.load_model:
        from yue2 import YuE2Pipeline
        pipe = YuE2Pipeline.from_pretrained(os.environ.get('YUE2_MODEL_DIR', '/weights/model'),
            vae=os.environ.get('YUE2_VAE_DIR', '/weights/vae'), local_files_only=True, device='cuda',
            memory_budget_gib=int(os.environ.get('YUE2_MEMORY_BUDGET_GIB', '16')),
            backend='torch', quantization='none')
        pipe.close()
        result['model_initialized'] = True
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
