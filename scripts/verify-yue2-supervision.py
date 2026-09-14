"""GPU guardian acceptance: kill its owner and verify cleanup and exclusivity.

Run in the integrated worker image while application inference is idle. Allocates
256 MiB of CUDA memory in a synthetic inference child; does not run the model.
"""
import json
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import pynvml as nvml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--real-model', action='store_true')
    args = parser.parse_args()
    nvml.nvmlInit()
    gpu = nvml.nvmlDeviceGetHandleByIndex(0)
    before = nvml.nvmlDeviceGetMemoryInfo(gpu).used
    with tempfile.TemporaryDirectory(prefix='yue2-guardian-check-') as directory:
        root = Path(directory)
        child = root / 'gpu.py'
        pid_file = root / 'gpu.pid'
        resource_file = root / 'resource.json'
        child.write_text('''import os,signal,time
from pathlib import Path
import torch
signal.signal(signal.SIGTERM, signal.SIG_IGN)
x = torch.ones(256 * 1024 * 1024, dtype=torch.uint8, device='cuda')
torch.cuda.synchronize()
Path(''' + repr(str(pid_file)) + ''').write_text(str(os.getpid()))
time.sleep(120)
''')
        if args.real_model:
            child.write_text('''import os,signal,time,json,threading
from pathlib import Path
import torch
from yue2 import YuE2Pipeline
signal.signal(signal.SIGTERM, signal.SIG_IGN)
pipe = YuE2Pipeline.from_pretrained(os.environ['YUE2_MODEL_DIR'],
    vae=os.environ['YUE2_VAE_DIR'], local_files_only=True, device='cuda',
    memory_budget_gib=int(os.environ['YUE2_MEMORY_BUDGET_GIB']), backend='torch', quantization='none')
def observe_gpu():
    while torch.cuda.memory_allocated() < 256 * 2**20:
        time.sleep(.05)
    Path(''' + repr(str(resource_file)) + ''').write_text(json.dumps({
        'torch_allocated_bytes': torch.cuda.memory_allocated(),
        'torch_reserved_bytes': torch.cuda.memory_reserved()}))
    Path(''' + repr(str(pid_file)) + ''').write_text(str(os.getpid()))
threading.Thread(target=observe_gpu, daemon=True).start()
song = pipe(style='Warm acoustic folk song', lyrics='[Verse]\\nMorning by the river\\n[Chorus]\\nCarry on together', cot='full', seed=42)
time.sleep(120)
''')
        owner = root / 'owner.py'
        owner.write_text('''import os,subprocess,sys,time
r,w = os.pipe()
p = subprocess.Popen([sys.executable, '-m', 'museforge.worker.inference_supervisor',
    '--control-fd', str(r), '--lock-path', '/tmp/museforge-yue2.inference.lock',
    '--', sys.executable, sys.argv[1]], pass_fds=(r,), start_new_session=True)
os.close(r)
time.sleep(120)
''')
        pool = subprocess.Popen([sys.executable, str(owner), str(child)])
        replacement = None
        control_write = None
        inference_pid = None
        try:
            deadline = time.monotonic() + 120
            while not pid_file.exists():
                assert pool.poll() is None and time.monotonic() < deadline
                time.sleep(.1)
            inference_pid = int(pid_file.read_text())
            peak = nvml.nvmlDeviceGetMemoryInfo(gpu).used
            pool.kill()
            pool.wait()
            marker = root / 'replacement'
            read_fd, control_write = os.pipe()
            try:
                replacement = subprocess.Popen([sys.executable, '-m', 'museforge.worker.inference_supervisor',
                    '--control-fd', str(read_fd), '--lock-path', '/tmp/museforge-yue2.inference.lock',
                    '--', sys.executable, '-c',
                    'from pathlib import Path; Path(' + repr(str(marker)) + ').touch()'], pass_fds=(read_fd,))
            finally:
                os.close(read_fd)
            time.sleep(.3)
            assert not marker.exists(), 'GPU inference overlapped replacement'
            assert replacement.wait(timeout=20) == 0 and marker.exists()
            try:
                os.kill(inference_pid, 0)
            except ProcessLookupError:
                pass
            else:
                raise AssertionError('GPU child was not reaped')
            deadline = time.monotonic() + 15
            after = nvml.nvmlDeviceGetMemoryInfo(gpu).used
            while after > before + 256 * 2**20 and time.monotonic() < deadline:
                time.sleep(.2)
                after = nvml.nvmlDeviceGetMemoryInfo(gpu).used
            assert after <= before + 256 * 2**20
            print(json.dumps(dict(result='passed', real_model=args.real_model, owner_killed=True, inference_reaped=True,
                exclusive_replacement=True, device_before_bytes=before,
                device_peak_bytes=peak, device_after_bytes=after, gpu_memory_recovered=True,
                inference_resource=json.loads(resource_file.read_text()) if resource_file.exists() else {}), indent=2))
        finally:
            if control_write is not None: os.close(control_write)
            if pool.poll() is None: pool.kill(); pool.wait()
            if replacement is not None and replacement.poll() is None:
                replacement.terminate(); replacement.wait(timeout=20)
            if inference_pid is not None:
                try: os.kill(inference_pid, 9)
                except ProcessLookupError: pass
    nvml.nvmlShutdown()


if __name__ == '__main__':
    main()
