"""Sequential GPU test supervisor; never imports torch into the parent."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import psutil
import pynvml as nvml


def save(path, data):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)


def terminate(process, grace=5):
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        process.wait(timeout=5)
        return
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def supervise(command, log, gpu, timeout=900):
    before = nvml.nvmlDeviceGetMemoryInfo(gpu).used
    peak_gpu, peak_rss = before, 0
    min_available = psutil.virtual_memory().available
    start = time.monotonic()
    timed_out = False
    with log.open('w') as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            while process.poll() is None:
                peak_gpu = max(peak_gpu, nvml.nvmlDeviceGetMemoryInfo(gpu).used)
                min_available = min(min_available, psutil.virtual_memory().available)
                try:
                    root = psutil.Process(process.pid)
                    rss = sum(p.memory_info().rss for p in [root, *root.children(recursive=True)])
                    peak_rss = max(peak_rss, rss)
                except psutil.NoSuchProcess:
                    pass
                if time.monotonic() - start >= timeout:
                    timed_out = True
                    break
                time.sleep(0.2)
        finally:
            terminate(process)
    elapsed = time.monotonic() - start
    # WSL reports whole-device use. Allow driver cleanup plus 256 MiB noise.
    recovery_deadline = time.monotonic() + 15
    after = nvml.nvmlDeviceGetMemoryInfo(gpu).used
    while after > before + 256 * 2**20 and time.monotonic() < recovery_deadline:
        time.sleep(0.5)
        after = nvml.nvmlDeviceGetMemoryInfo(gpu).used
    return {'exit_code': process.returncode, 'timed_out': timed_out,
            'elapsed_seconds': elapsed, 'peak_device_used_bytes': peak_gpu,
            'peak_process_tree_rss_bytes': peak_rss, 'minimum_host_available_bytes': min_available,
            'device_used_before_bytes': before, 'device_used_after_bytes': after,
            'gpu_memory_recovered': after <= before + 256 * 2**20}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', choices=['acoustic-folk', 'synth-pop', 'piano-ballad'])
    parser.add_argument('--label', default='batch')
    args = parser.parse_args()
    if not args.label.replace('-', '').isalnum():
        parser.error('label must be alphanumeric or hyphenated')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + args.label
    output = Path('/outputs') / run_id
    output.mkdir(parents=True)
    nvml.nvmlInit()
    gpu = nvml.nvmlDeviceGetHandleByIndex(0)
    report = {'run_id': run_id, 'driver': nvml.nvmlSystemGetDriverVersion(),
              'models': json.loads(Path('model-lock.json').read_text()), 'attempts': []}
    try:
        with (output / 'preflight.json').open('w') as stream:
            subprocess.run([sys.executable, 'preflight.py'], stdout=stream, check=True, timeout=120)
        preflight = json.loads((output / 'preflight.json').read_text())
        if not preflight['verified_weights']:
            raise RuntimeError('Run model acquisition before inference')
        requests = json.loads(Path('prompts.json').read_text())
        selected = [r for r in requests if not args.only or r['id'] == args.only]
        for request in selected:
            for offload in (False, True):
                attempt_id = request['id'] + ('-offload' if offload else '-baseline')
                folder = output / attempt_id
                folder.mkdir()
                save(folder / 'input.json', request)
                command = [sys.executable, 'generate.py', str(folder / 'input.json'), str(folder)]
                if offload:
                    command.append('--offload-ar')
                print(f'Starting {attempt_id}', flush=True)
                result = supervise(command, folder / 'process.log', gpu)
                result.update(id=attempt_id, prompt_id=request['id'], offload_ar=offload)
                for filename in ('validation', 'failure'):
                    path = folder / (filename + '.json')
                    if path.exists():
                        result[filename] = json.loads(path.read_text())
                report['attempts'].append(result)
                save(output / 'report.json', report)
                print(json.dumps(result), flush=True)
                if not result['gpu_memory_recovered']:
                    raise RuntimeError('GPU memory did not recover; refusing the next generation')
                if result.get('failure', {}).get('category') != 'cuda_oom':
                    break
        latest = {r['prompt_id']: r for r in report['attempts']}
        report['passed'] = all(r['exit_code'] == 0 and r['validation']['passed']
                               for r in latest.values()) and len(latest) == len(selected)
        return 0 if report['passed'] else 1
    finally:
        save(output / 'report.json', report)
        nvml.nvmlShutdown()
        print(f'Report: {output / "report.json"}', flush=True)


if __name__ == '__main__':
    raise SystemExit(main())
