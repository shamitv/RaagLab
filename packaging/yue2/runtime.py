"""Startup-only device selection for the pinned YuE2 runtime."""
import torch


def select_device(requested):
    if requested not in {'auto', 'cuda', 'cpu'}:
        raise ValueError('DEVICE must be auto, cuda, or cpu')
    if requested == 'cpu':
        return 'cpu', None
    # Weight verification and model loading must remain outside this boundary.
    reason = None
    try:
        if not torch.cuda.is_available():
            reason = 'cuda_unavailable'
        elif not torch.cuda.is_bf16_supported():
            reason = 'cuda_bf16_unsupported'
        else:
            x = torch.ones((256, 256), device='cuda', dtype=torch.bfloat16)
            if not torch.isfinite(x @ x).all().item():
                raise RuntimeError('Nonfinite CUDA device probe')
            torch.cuda.synchronize()
            del x
            return 'cuda', None
    except Exception:
        reason = 'cuda_probe_failed'
    if requested == 'cuda':
        raise RuntimeError('Required CUDA startup probe failed: ' + reason)
    return 'cpu', reason
