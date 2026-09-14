import hashlib
import json
import argparse
import os
from pathlib import Path
import platform

import torch
from runtime import select_device


def validate_configured_identity(lock):
    for name, expected in (('MODEL_ID', lock['model']['repo']),
                           ('MODEL_REVISION', lock['model']['revision']),
                           ('DECODER_REVISION', lock['vae']['revision'])):
        if os.environ.get(name) != expected:
            raise RuntimeError('Configured identity does not match pinned weights: ' + name)


def verify_weights(lock, required):
    weights_root = Path(os.environ.get('WEIGHTS_DIR', '/weights'))
    manifest_path = weights_root / 'verified.json'
    if required and not manifest_path.exists():
        raise RuntimeError('Verified model weights are required')
    if manifest_path.exists():
        verified = json.loads(manifest_path.read_text())
        for key in ('model', 'vae'):
            if (verified[key]['revision'] != lock[key]['revision'] or
                    verified[key]['repo'] != lock[key]['repo'] or not verified[key]['files']):
                raise RuntimeError('Verified weights identity mismatch: ' + key)
            for item in verified[key]['files']:
                model_root = Path(os.environ.get('YUE2_MODEL_DIR', str(weights_root / 'model')))
                vae_root = Path(os.environ.get('YUE2_VAE_DIR', str(weights_root / 'vae')))
                root = (model_root if key == 'model' else vae_root).resolve()
                path = (root / item['file']).resolve()
                if not path.is_relative_to(root):
                    raise RuntimeError('Invalid verified weight path')
                with path.open('rb') as stream:
                    if hashlib.file_digest(stream, 'sha256').hexdigest() != item['sha256']:
                        raise RuntimeError('Weight checksum mismatch: ' + item['file'])
    return manifest_path.exists()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-weights', action='store_true')
    parser.add_argument('--load-model', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    lock = json.loads(Path(__file__).with_name('model-lock.json').read_text())
    if args.require_weights:
        validate_configured_identity(lock)
    verified = verify_weights(lock, args.require_weights)
    device, reason = select_device(os.environ.get('DEVICE', 'auto'))
    backend = 'torch' if device == 'cuda' else 'torch-eager'
    if device == 'cpu':
        torch.set_num_threads(int(os.environ.get('YUE2_CPU_THREADS', '4')))
    result = dict(python=platform.python_version(), torch=torch.__version__, cuda=torch.version.cuda,
                  device=device, backend=backend, fallback_reason=reason,
                  verified_weights=verified, models=lock)
    if device == 'cuda':
        result.update(gpu=torch.cuda.get_device_name(), capability=torch.cuda.get_device_capability(),
                      bf16=True, gpu_total_bytes=torch.cuda.get_device_properties(0).total_memory)
    if args.load_model:
        from yue2 import YuE2Pipeline
        with YuE2Pipeline.from_pretrained(os.environ.get('YUE2_MODEL_DIR', '/weights/model'),
            vae=os.environ.get('YUE2_VAE_DIR', '/weights/vae'), local_files_only=True, device=device,
            memory_budget_gib=int(os.environ.get('YUE2_MEMORY_BUDGET_GIB', '16')),
            backend=backend, quantization='none', offload_ar=os.environ.get('YUE2_OFFLOAD_AR') == '1') as pipe:
            # 0.1.6 constructs lazily; use its pinned private loader to verify startup.
            pipe._load_model()
        result['model_initialized'] = True
    if args.report:
        args.report.write_text(json.dumps(result) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
