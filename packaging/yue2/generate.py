"""One isolated inference attempt. The parent enforces the wall-clock deadline."""
import argparse
import json
import os
from pathlib import Path
import time
import traceback

import torch
from yue2 import YuE2Pipeline

from validate import samples_metrics, validate_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('request')
    parser.add_argument('output')
    parser.add_argument('--offload-ar', action='store_true')
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    pipe = None
    initializing = True
    start = time.monotonic()
    try:
        request = json.loads(Path(args.request).read_text())
        pipe = YuE2Pipeline.from_pretrained(os.environ.get('YUE2_MODEL_DIR', '/weights/model'),
            vae=os.environ.get('YUE2_VAE_DIR', '/weights/vae'), local_files_only=True, device='cuda',
            memory_budget_gib=int(os.environ.get('YUE2_MEMORY_BUDGET_GIB', '16')),
            backend='torch', quantization='none', offload_ar=args.offload_ar)
        initializing = False
        song = pipe(**request)
        raw = samples_metrics(song.audio, song.sample_rate)
        song.save_artifacts(output)
        decoded = validate_file(output / 'audio.flac')
        validation = {'raw': raw, 'decoded': decoded, 'truncated': song.truncated,
                      'passed': raw['passed'] and decoded['passed'] and not any(song.truncated.values()),
                      'listening': 'pending', 'lyric_adherence': 'pending',
                      'torch_peak_allocated_bytes': torch.cuda.max_memory_allocated(),
                      'torch_peak_reserved_bytes': torch.cuda.max_memory_reserved(),
                      'elapsed_seconds': time.monotonic() - start,
                      'offload_ar': args.offload_ar}
        (output / 'validation.json').write_text(json.dumps(validation, indent=2) + '\n')
        return 0 if validation['passed'] else 2
    except Exception as exc:
        message = str(exc).lower()
        oom = isinstance(exc, torch.cuda.OutOfMemoryError)
        if oom:
            category = 'cuda_oom'
        elif not torch.cuda.is_available() or 'cuda is required' in message or 'cuda unavailable' in message:
            category = 'device_unavailable'
        elif initializing and ('no such file' in message or 'not found' in message or 'weight' in message):
            category = 'missing_weights'
        elif initializing:
            category = 'initialization_error'
        else:
            category = 'inference_error'
        (output / 'failure.json').write_text(json.dumps({
            'category': category,
            'exception_type': type(exc).__name__, 'message': str(exc),
            'elapsed_seconds': time.monotonic() - start,
            'offload_ar': args.offload_ar}, indent=2) + '\n')
        traceback.print_exc()
        return 3 if oom else 1
    finally:
        if pipe is not None:
            pipe.close()


if __name__ == '__main__':
    raise SystemExit(main())
