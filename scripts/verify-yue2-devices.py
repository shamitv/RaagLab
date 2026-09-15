"""Run one isolated real-provider generation with explicit device semantics.

The default invocation keeps the short smoke check used by the provider
readiness phase. ``--cpu --normal`` is the Phase 6 release gate: it runs the
real pinned model with normal planning and validates durable CPU provenance.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import re
import hashlib
import signal
from urllib.request import urlopen
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]


def owned_project(project: str) -> bool:
    return bool(re.fullmatch(r"museforge-yue2-test-[0-9a-f]{12}", project))


def available_memory_gib() -> float | None:
    """Read Linux's available memory estimate without requiring psutil."""
    try:
        values = dict(
            line.split(":", 1)
            for line in Path("/proc/meminfo").read_text().splitlines()
            if ":" in line
        )
        return int(values["MemAvailable"].split()[0]) / (1024 * 1024)
    except (OSError, KeyError, ValueError, IndexError):
        return None


def api_audio_snapshot(origin: str, audio_url: str) -> str:
    with urlopen(f"{origin}{audio_url}", timeout=30) as response:
        return hashlib.sha256(response.read()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu", action="store_true", help="Expose CUDA and require CUDA selection")
    parser.add_argument("--cpu", action="store_true", help="Require explicit CPU selection")
    parser.add_argument("--normal", action="store_true", help="Disable short smoke mode")
    parser.add_argument("--min-host-memory-gib", type=int, default=0)
    parser.add_argument("--memory-limit-gib", type=int, default=28)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    if args.gpu and args.cpu:
        parser.error("--gpu and --cpu are mutually exclusive")
    if args.min_host_memory_gib < 0 or args.memory_limit_gib < 1:
        parser.error("memory limits must be positive")

    project = "museforge-yue2-test-" + uuid4().hex[:12]
    evidence = args.evidence_dir or ROOT / "test-results/yue2-devices" / project
    evidence.mkdir(parents=True, exist_ok=True)
    requested_device = "cuda" if args.gpu else "cpu" if args.cpu else "auto"
    expected_device = requested_device if requested_device in {"cpu", "cuda"} else None
    smoke = not args.normal
    env = dict(
        os.environ,
        YUE2_DEVICE=requested_device,
        YUE2_TEST_SMOKE=str(smoke).lower(),
        YUE2_MEMORY_LIMIT_GIB=str(args.memory_limit_gib),
        YUE2_EVIDENCE_DIR=str(evidence),
    )
    compose = [
        "docker", "compose", "--project-name", project, "--profile", "yue2",
        "-f", "compose.yaml", "-f", "compose.yue2.yaml",
    ]
    if args.gpu:
        compose += ["-f", "compose.yue2.gpu.yaml"]
    compose += ["-f", "compose.yue2.test.yaml"]

    command_index = 0

    def run(*command: str, timeout: int = 1800, compose_cmd=None):
        nonlocal command_index
        command_index += 1
        prefix = "-".join(re.sub(r"[^A-Za-z0-9_.-]", "_", item) for item in command[:2])
        log = evidence / f"compose-{command_index:02d}-{prefix}.log"
        argv = [*(compose_cmd or compose), *command]
        try:
            process = subprocess.Popen(argv, cwd=ROOT, env=env, text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       start_new_session=(os.name != 'nt'))
            try:
                output, _ = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                partial = exc.stdout or ""
                if os.name == 'nt':
                    process.kill()
                else:
                    os.killpg(process.pid, signal.SIGTERM)
                try:
                    tail, _ = process.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    if os.name == 'nt':
                        process.kill()
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
                    tail, _ = process.communicate(timeout=10)
                output = (partial.decode(errors='replace') if isinstance(partial, bytes) else partial or '') + (tail or '')
                log.write_text(output, encoding="utf-8")
                raise
            output = output or ""
        except subprocess.TimeoutExpired as exc:
            if not log.exists():
                partial = exc.stdout or ""
                log.write_text(partial.decode(errors='replace') if isinstance(partial, bytes) else partial,
                               encoding="utf-8")
            raise
        log.write_text(output, encoding="utf-8")
        if process.returncode:
            raise RuntimeError(f"compose {' '.join(command)} failed with {process.returncode}")
        return output

    stop_samples = threading.Event()
    samples: list[dict[str, object]] = []
    sampler: threading.Thread | None = None
    cleanup_error = False
    passed = False

    def sample_worker(container: str) -> None:
        while not stop_samples.is_set():
            try:
                result = subprocess.run(
                    ["docker", "stats", "--no-stream", "--format", "{{json .}}", container],
                    capture_output=True, text=True, check=False, timeout=30,
                )
                if result.returncode == 0 and result.stdout.strip():
                    samples.append({"observed_at": time.time(), "container": container,
                                    "stats": result.stdout.strip()})
            except (OSError, subprocess.TimeoutExpired):
                pass
            stop_samples.wait(5)

    try:
        if args.min_host_memory_gib:
            observed = available_memory_gib()
            if observed is None:
                raise RuntimeError("could not read host available memory")
            if observed < args.min_host_memory_gib:
                raise RuntimeError(
                    f"host has {observed:.1f} GiB available; {args.min_host_memory_gib} GiB required"
                )
            (evidence / "host-resources.json").write_text(json.dumps({
                "available_memory_gib": observed,
                "required_memory_gib": args.min_host_memory_gib,
                "worker_memory_limit_gib": args.memory_limit_gib,
                "cpu_threads": int(env.get("YUE2_CPU_THREADS", "4")),
            }, indent=2) + "\n")
            volume = subprocess.run(["docker", "volume", "inspect", "musicgen-yue2-test_weights", "--format", "{{json .}}"],
                                    capture_output=True, text=True, timeout=30, check=False)
            if volume.returncode or not volume.stdout.strip():
                raise RuntimeError("pinned musicgen-yue2-test_weights volume is required")
            (evidence / "weights-volume.json").write_text(volume.stdout.strip() + "\n", encoding="utf-8")

        run("build", "api", "migrate", "dispatcher", "worker-yue2", "yue2-smoke-tests", timeout=3600)
        run("up", "-d", "--wait", "--wait-timeout", "1000", "api", "dispatcher", "worker-yue2", timeout=1800)
        container = run("ps", "-q", "worker-yue2").strip().splitlines()[-1]
        if not container:
            raise RuntimeError("worker-yue2 container id was not reported")
        inspect = subprocess.run(["docker", "inspect", container], capture_output=True, text=True, check=True, timeout=30)
        inspection = json.loads(inspect.stdout)[0]
        (evidence / "worker-inspect.json").write_text(json.dumps({
            "id": container,
            "device_requests": inspection.get("HostConfig", {}).get("DeviceRequests") or [],
            "memory_limit_bytes": inspection.get("HostConfig", {}).get("Memory", 0),
            "env": [entry for entry in inspection.get("Config", {}).get("Env", [])
                    if not any(secret in entry.upper() for secret in ("PASSWORD", "TOKEN", "SECRET"))],
        }, indent=2) + "\n")
        worker_env = dict(entry.split('=', 1) for entry in inspection.get("Config", {}).get("Env", []) if '=' in entry)
        if worker_env.get('DEVICE') != requested_device:
            raise RuntimeError(f"worker DEVICE mismatch: expected {requested_device}, got {worker_env.get('DEVICE')}")
        if worker_env.get('YUE2_TEST_SMOKE') != str(smoke).lower():
            raise RuntimeError("worker smoke mode mismatch")
        if not smoke and worker_env.get('YUE2_PROCESS_TIMEOUT_SECONDS') != '3600':
            raise RuntimeError("normal CPU worker process timeout is not 3600 seconds")
        if not smoke and worker_env.get('ATTEMPT_DEADLINE_SECONDS') != '3600':
            raise RuntimeError("normal CPU worker attempt deadline is not 3600 seconds")
        if args.cpu and inspection.get("HostConfig", {}).get("Memory", 0) < args.memory_limit_gib * 1024 ** 3 * 0.99:
            raise RuntimeError("CPU worker memory limit is below the requested budget")
        if args.cpu and inspection.get("HostConfig", {}).get("DeviceRequests"):
            raise RuntimeError("CPU verification worker unexpectedly has GPU device requests")
        sampler = threading.Thread(target=sample_worker, args=(container,), daemon=True)
        sampler.start()

        command = ["run", "--rm", "--no-deps", "yue2-smoke-tests", "python", "/verification/verify-d03.py"]
        if expected_device:
            command.extend(["--expected-device", expected_device])
        if smoke:
            command.append("--smoke")
        start = time.monotonic()
        run(*command, timeout=1800 if smoke else 3600)
        elapsed = time.monotonic() - start
        if not smoke:
            accepted = json.loads((evidence / "accepted.json").read_text(encoding="utf-8"))
            version = json.loads((evidence / "version.json").read_text())
            version_id = version["id"]
            audio_url = version["audio"]["url"]
            address = run("port", "api", "8000").strip().splitlines()[-1]
            origin = f"http://{address}"
            before_hash = api_audio_snapshot(origin, audio_url)
            run("stop", "api", "dispatcher", "worker-yue2", timeout=300)
            run("up", "-d", "--wait", "--wait-timeout", "1000", "api", "dispatcher", "worker-yue2", timeout=1800)
            address_after = run("port", "api", "8000").strip().splitlines()[-1]
            after_hash = api_audio_snapshot(f"http://{address_after}", audio_url)
            if before_hash != after_hash:
                raise RuntimeError("CPU audio checksum changed across stop/start")
            (evidence / "persistence.json").write_text(json.dumps({
                "version_id": version_id,
                "before_sha256": before_hash,
                "after_sha256": after_hash,
            }, indent=2) + "\n")
            # Keep the CPU API and accepted project alive while Chromium checks
            # playback, seeking, download bytes, and refresh/reopen behavior.
            browser_compose = [*compose, "-f", "compose.test.yaml"]
            run("run", "--rm", "--no-deps",
                "-e", f"D03_PROJECT_ID={accepted['project_id']}",
                "-e", "PLAYWRIGHT_OUTPUT_DIR=/evidence/browser",
                "-v", f"{evidence}:/evidence",
                "browser-tests", "npm", "run", "test:browser", "--",
                "d03-real.spec.ts", "--project=desktop", compose_cmd=browser_compose, timeout=1200)
            (evidence / "browser.json").write_text(json.dumps({
                "project_id": accepted["project_id"],
                "result": "passed",
                "checks": ["playback", "seek", "download-checksum", "refresh", "reopen"],
            }, indent=2) + "\n")
        (evidence / "verifier-timing.json").write_text(json.dumps({
            "requested_device": requested_device,
            "expected_device": expected_device,
            "smoke": smoke,
            "inference_wall_seconds": round(elapsed, 3),
        }, indent=2) + "\n")
        passed = True
    except (OSError, RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        (evidence / "failure.json").write_text(json.dumps({
            "result": "failed", "project": project, "requested_device": requested_device,
            "smoke": smoke, "error": str(exc),
        }, indent=2) + "\n")
        raise
    finally:
        stop_samples.set()
        if sampler:
            sampler.join(timeout=10)
        (evidence / "resource-samples.json").write_text(json.dumps(samples, indent=2) + "\n")
        if owned_project(project):
            try:
                ids = subprocess.run([*compose, "ps", "-q"], cwd=ROOT, env=env,
                                     capture_output=True, text=True, timeout=30, check=False).stdout.splitlines()
                for resource in ids:
                    labels = subprocess.run(["docker", "inspect", "--format", "{{ index .Config.Labels \"com.docker.compose.project\" }}", resource],
                                             capture_output=True, text=True, timeout=30, check=True).stdout.strip()
                    if labels != project:
                        raise RuntimeError("refusing cleanup for resource outside owned Compose project")
                with (evidence / "services.log").open("w") as log:
                    logs_result = subprocess.run([*compose, "logs", "--no-color"], cwd=ROOT, env=env,
                                                 stdout=log, stderr=subprocess.STDOUT, timeout=120, check=False)
                    if logs_result.returncode:
                        cleanup_error = True
            except (OSError, RuntimeError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
                cleanup_error = True
                (evidence / "cleanup-errors.log").write_text(str(exc) + "\n", encoding="utf-8")
            try:
                down_result = subprocess.run([*compose, "down", "--volumes", "--remove-orphans"],
                                             cwd=ROOT, env=env, check=False, timeout=300,
                                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                (evidence / "cleanup-down.log").write_text(down_result.stdout or "", encoding="utf-8")
                if down_result.returncode:
                    cleanup_error = True
            except (OSError, subprocess.TimeoutExpired) as exc:
                cleanup_error = True
                with (evidence / "cleanup-errors.log").open("a") as errors:
                    errors.write(str(exc) + "\n")
    if cleanup_error:
        raise RuntimeError("test-owned Compose cleanup failed")
    if passed:
        print(json.dumps({"result": "passed", "project": project, "evidence": str(evidence),
                          "requested_device": requested_device, "smoke": smoke,
                          "inference_wall_seconds": round(elapsed, 3)}, indent=2))
        return 0
    return 1


if __name__ == '__main__':
    main()
