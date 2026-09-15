#!/usr/bin/env python3
"""Run the Phase 6 release gate in a disposable, isolated checkout.

The outer invocation creates a detached worktree at the requested revision and
re-executes this script there. The inner invocation runs the mock release gate
and, when requested, the full normal-mode CPU YuE2 gate. Evidence is retained
outside the temporary worktree so a failed run remains inspectable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import uuid


ORIGINAL_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get("MUSEFORGE_RELEASE_ROOT", str(ORIGINAL_ROOT))).resolve()
RUN_ID = os.environ.get("MUSEFORGE_RELEASE_RUN_ID") or (
    time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
)
EVIDENCE = Path(os.environ.get("MUSEFORGE_RELEASE_EVIDENCE_DIR", str(
    ORIGINAL_ROOT / "test-results" / f"phase6-{RUN_ID}"
))).resolve()
EVIDENCE.mkdir(parents=True, exist_ok=True)

ENV_ALLOWLIST_EXACT = {
    "CI", "DOCKER_CONFIG", "DOCKER_CONTEXT", "DOCKER_HOST", "HOME", "LANG",
    "LOGNAME", "NO_COLOR", "PATH", "TERM", "TMP", "TEMP", "TMPDIR", "USER",
    "XDG_CONFIG_HOME", "XDG_RUNTIME_DIR",
}
SAFE_EXTRA_KEYS = {
    "API_BASE_URL", "APP_PORT", "COMPOSE_PROJECT_NAME", "MUSEFORGE_EVIDENCE_DIR",
    "MUSEFORGE_RECOVERY_CHECKS", "MUSEFORGE_RELEASE_EVIDENCE_DIR",
    "MUSEFORGE_RELEASE_IN_CHECKOUT", "MUSEFORGE_RELEASE_ROOT", "MUSEFORGE_RELEASE_RUN_ID",
    "MUSEFORGE_TEST_PROJECT", "MUSEFORGE_TEST_PROJECT_PREFIX", "PHASE4_BROWSER",
    "PHASE6_VISUAL", "YUE2_CPU_THREADS", "MUSEFORGE_CONTAINER_UID", "MUSEFORGE_CONTAINER_GID",
}


def allowed_environment(source: dict[str, str] | None = None) -> dict[str, str]:
    source = source or os.environ
    return {
        key: value for key, value in source.items()
        if key in ENV_ALLOWLIST_EXACT or key.startswith("LC_")
    }


REPO_ENV = allowed_environment()


class ReleaseFailure(RuntimeError):
    pass


outcomes: list[dict[str, object]] = []
OWNED_PROJECT_PREFIXES = ("museforge-phase6-test-", "museforge-phase6-runtime-")


def owned_project(project: str) -> bool:
    """Return whether a Compose project is safe for release cleanup."""
    return bool(re.fullmatch(r"museforge-phase6-(?:test|runtime)-[0-9a-f]{10,32}", project))


def command_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(REPO_ENV)
    if extra:
        env.update({key: value for key, value in extra.items()
                    if key in SAFE_EXTRA_KEYS or key in ENV_ALLOWLIST_EXACT or key.startswith("LC_")})
    return env


def _text_output(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def run_step(name: str, command: list[str], *, env: dict[str, str] | None = None,
             cwd: Path = ROOT, timeout: int = 1800, check: bool = True) -> str:
    """Run a bounded command, retaining output for both success and failure."""
    started = time.monotonic()
    timed_out = False
    returncode: int | None = None
    process = None
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env or REPO_ENV,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=(os.name != "nt"),
        )
        try:
            stdout, _ = process.communicate(timeout=timeout)
            output = _text_output(stdout)
            returncode = process.returncode
        except subprocess.TimeoutExpired as exc:
            partial = _text_output(exc.stdout)
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGTERM)
            try:
                tail, _ = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    process.kill()
                else:
                    os.killpg(process.pid, signal.SIGKILL)
                tail, _ = process.communicate(timeout=10)
            output = partial + _text_output(tail)
            timed_out = True
            returncode = process.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        output = _text_output(exc.stdout) + _text_output(exc.stderr)
    log_name = f"{name}.log"
    (EVIDENCE / log_name).write_text(output, encoding="utf-8")
    outcomes.append({
        "name": name,
        "command": command,
        "returncode": returncode,
        "timed_out": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "log": log_name,
    })
    if timed_out:
        raise ReleaseFailure(f"{name} timed out after {timeout}s")
    if check and returncode:
        raise ReleaseFailure(f"{name} failed with exit code {returncode}")
    return output


def cleanup_step(name: str, command: list[str], env: dict[str, str], *, timeout: int = 300) -> dict[str, object]:
    started = time.monotonic()
    output = ""
    returncode: int | None = None
    error = None
    try:
        result = subprocess.run(
            command, cwd=ROOT, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=timeout, check=False,
        )
        output = _text_output(result.stdout)
        returncode = result.returncode
    except (OSError, subprocess.TimeoutExpired) as exc:
        output = _text_output(getattr(exc, "stdout", ""))
        error = str(exc)
    log_name = f"{name}.log"
    (EVIDENCE / log_name).write_text(output, encoding="utf-8")
    result = {
        "name": name,
        "command": command,
        "returncode": returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "log": log_name,
    }
    if error:
        result["error"] = error
    return result


def verify_project_ownership(project: str, env: dict[str, str]) -> None:
    """Refuse destructive cleanup if any matching Docker resource is foreign."""
    if not owned_project(project):
        raise ReleaseFailure(f"refusing cleanup for unowned Compose project: {project}")
    result = subprocess.run(
        ["docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={project}"],
        cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=30, check=False,
    )
    if result.returncode:
        raise ReleaseFailure(f"could not inspect owned Compose resources for {project}")
    for container in [line.strip() for line in result.stdout.splitlines() if line.strip()]:
        inspected = subprocess.run(
            ["docker", "inspect", "--format", "{{json .Config.Labels}}", container],
            cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=30, check=False,
        )
        if inspected.returncode:
            raise ReleaseFailure(f"could not inspect cleanup resource {container}")
        try:
            labels = json.loads(inspected.stdout.strip())
        except ValueError as exc:
            raise ReleaseFailure(f"invalid labels on cleanup resource {container}") from exc
        if labels.get("com.docker.compose.project") != project:
            raise ReleaseFailure(f"refusing cleanup for resource outside owned project {project}")


def compose(project: str, *args: str) -> list[str]:
    return [
        "docker", "compose", "--project-name", project, "--env-file", ".env",
        "--profile", "mock", *args,
    ]


def last_output_line(output: str) -> str:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def url_json(origin: str, path: str) -> object:
    with urllib.request.urlopen(urllib.parse.urljoin(origin, path), timeout=15) as response:
        return json.load(response)


def audio_snapshot(origin: str) -> dict[str, object]:
    projects = url_json(origin, "/api/v1/projects?limit=100")
    settings = url_json(origin, "/api/v1/settings")
    items: list[dict[str, object]] = []
    for project in projects["items"]:  # type: ignore[index]
        detail = url_json(origin, f"/api/v1/projects/{project['id']}")
        version_id = detail.get("active_version_id")
        audio = None
        if version_id:
            version = url_json(origin, f"/api/v1/versions/{version_id}")
            audio_info = version.get("audio")
            if audio_info:
                audio_url = urllib.parse.urljoin(origin, audio_info["url"])
                with urllib.request.urlopen(audio_url, timeout=15) as response:
                    payload = response.read()
                audio = {
                    "version_id": version_id,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "byte_size": len(payload),
                }
        items.append({"id": project["id"], "active_version_id": version_id, "audio": audio})
    return {"projects": items, "settings": settings}


def assert_persistence(before: dict[str, object], after: dict[str, object]) -> None:
    if before != after:
        raise ReleaseFailure("database, selection, settings, or playable audio changed across restart")


def static_audit() -> None:
    run_step("git-diff-check", ["git", "diff", "--check"])
    tracked = run_step("tracked-files", ["git", "ls-files"])
    forbidden = re.compile(r"(^|/)(secrets|weights|models|artifacts|service-data)(/|$)|(^|/)\.env$")
    bad = [line for line in tracked.splitlines() if forbidden.search(line)]
    if bad:
        raise ReleaseFailure(f"forbidden tracked files: {bad}")
    documentation = [ROOT / "README.md", *sorted(ROOT.glob("docs/**/*.md"))]
    for path in documentation:
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
            target = urllib.parse.unquote(target.split("#", 1)[0])
            if not target or re.match(r"(?:[a-z]+:)?//", target) or target.startswith("mailto:"):
                continue
            if re.match(r"^[A-Za-z]:[/\\]", target):
                continue
            if not (path.parent / target).resolve().exists():
                raise ReleaseFailure(f"broken documentation link in {path}: {target}")


def sanitized_env() -> dict[str, str]:
    path = ROOT / ".env"
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = "<redacted>" if re.search(r"pass|secret|token|key|url", key, re.I) else value
    return values


def image_records(compose_command: list[str], env: dict[str, str], label: str) -> list[dict[str, object]]:
    image_names = [line.strip() for line in run_step(
        f"{label}-images", [*compose_command, "config", "--images"], env=env
    ).splitlines() if line.strip()]
    records: list[dict[str, object]] = []
    for index, image in enumerate(dict.fromkeys(image_names)):
        raw = run_step(
            f"{label}-image-inspect-{index}",
            ["docker", "image", "inspect", image, "--format", "{{json .}}"], env=env,
        )
        info = json.loads(raw.strip().splitlines()[-1])
        records.append({
            "name": image,
            "id": info.get("Id"),
            "repo_digests": info.get("RepoDigests", []),
        })
    return records


def clean_checkout(args: argparse.Namespace) -> int:
    """Re-execute at an exact detached revision and clean only that worktree."""
    revision = last_output_line(run_step(
        "candidate-revision", ["git", "rev-parse", "--verify", f"{args.revision}^{{commit}}"],
        cwd=ORIGINAL_ROOT,
    ))
    temp_root = Path(tempfile.mkdtemp(prefix="museforge-phase6-checkout-"))
    checkout = temp_root / "source"
    try:
        result = subprocess.run(
            ["git", "worktree", "add", "--detach", str(checkout), revision],
            cwd=ORIGINAL_ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, check=False, timeout=120,
        )
        (EVIDENCE / "clean-checkout-add.log").write_text(result.stdout, encoding="utf-8")
        if result.returncode:
            raise ReleaseFailure(f"could not create clean checkout: {result.returncode}")
        child_env = command_env({
            "MUSEFORGE_RELEASE_IN_CHECKOUT": "1",
            "MUSEFORGE_RELEASE_ROOT": str(checkout),
            "MUSEFORGE_RELEASE_EVIDENCE_DIR": str(EVIDENCE),
            "MUSEFORGE_RELEASE_RUN_ID": RUN_ID,
        })
        command = [sys.executable, str(checkout / "scripts/verify-release.py"), "--in-clean-checkout",
                   "--revision", revision]
        if args.real_cpu:
            command.append("--real-cpu")
        returncode = 0
        try:
            run_step("clean-checkout-run", command, env=child_env, cwd=ORIGINAL_ROOT, timeout=args.timeout)
        except ReleaseFailure:
            returncode = 1
        return returncode
    finally:
        result = subprocess.run(
            ["git", "worktree", "remove", "--force", str(checkout)],
            cwd=ORIGINAL_ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, check=False, timeout=120,
        )
        (EVIDENCE / "clean-checkout-remove.log").write_text(result.stdout, encoding="utf-8")
        if result.returncode:
            raise ReleaseFailure(f"could not remove owned clean checkout: {result.returncode}")
        shutil.rmtree(temp_root, ignore_errors=False)


def inner_main(args: argparse.Namespace) -> int:
    phase_project = f"museforge-phase6-test-{uuid.uuid4().hex[:10]}"
    runtime_project = f"museforge-phase6-runtime-{uuid.uuid4().hex[:10]}"
    phase_evidence = EVIDENCE / "recovery-gate"
    phase_evidence.mkdir(parents=True, exist_ok=True)
    # Compose bind-mounts browser artifacts from the disposable checkout. Make
    # the mount root writable before Docker creates it so browser containers
    # running as the host UID can retain their own traces without leaving
    # root-owned files that block worktree cleanup.
    test_results_root = ROOT / "test-results"
    test_results_root.mkdir(parents=True, exist_ok=True)
    try:
        test_results_root.chmod(0o777)
    except OSError:
        pass
    phase_env = command_env({
        "MUSEFORGE_TEST_PROJECT": phase_project,
        "MUSEFORGE_TEST_PROJECT_PREFIX": "museforge-phase6-test-",
        "MUSEFORGE_EVIDENCE_DIR": str(phase_evidence),
        "MUSEFORGE_RECOVERY_CHECKS": "1",
        "PHASE4_BROWSER": "1",
        "PHASE6_VISUAL": "1",
        "MUSEFORGE_CONTAINER_UID": str(getattr(os, "getuid", lambda: 1000)()),
        "MUSEFORGE_CONTAINER_GID": str(getattr(os, "getgid", lambda: 1000)()),
    })
    runtime_port = free_loopback_port()
    runtime_env = command_env({
        "COMPOSE_PROJECT_NAME": runtime_project,
        "APP_PORT": str(runtime_port),
    })
    release: dict[str, object] = {
        "phase": "06-release-verification-and-handoff",
        "run_id": RUN_ID,
        "source_revision": None,
        "candidate_revision": args.revision,
        "phase_project": phase_project,
        "runtime_project": runtime_project,
        "environment_allowlist": sorted(ENV_ALLOWLIST_EXACT),
        "environment": {},
        "outcomes": outcomes,
        "acceptance": {},
        "cleanup": [],
    }
    runtime_setup = False
    failure: BaseException | None = None
    try:
        expected_revision = last_output_line(run_step(
            "candidate-revision", ["git", "rev-parse", "--verify", f"{args.revision}^{{commit}}"]
        ))
        release["source_revision"] = run_step("source-revision", ["git", "rev-parse", "HEAD"]).strip()
        release["candidate_revision"] = expected_revision
        if release["source_revision"] != expected_revision:
            raise ReleaseFailure("clean checkout revision did not match requested candidate")
        run_step("setup", ["bash", "scripts/setup.sh"], env=runtime_env, timeout=180)
        runtime_setup = True
        phase_compose = compose(phase_project, "-f", "compose.yaml", "-f", "compose.test.yaml")
        release["environment"] = {
            "python": run_step("python-version", ["python3", "--version"]).strip(),
            "docker": run_step("docker-version", ["docker", "version", "--format", "{{.Server.Version}}"]).strip(),
            "compose": run_step("compose-version", ["docker", "compose", "version", "--short"]).strip(),
            "sanitized_env": sanitized_env(),
            "locks": {
                str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in [
                    ROOT / "uv.lock", ROOT / "apps/web/package-lock.json",
                    ROOT / "packaging/yue2/requirements.museforge.lock",
                    ROOT / "packaging/yue2/model-lock.json",
                ] if path.exists()
            },
            "runtime_overrides": {
                "COMPOSE_PROJECT_NAME": runtime_project,
                "APP_PORT": f"{runtime_port} (ephemeral loopback port)",
            },
        }
        release["environment"]["node"] = last_output_line(run_step(
            "container-node-version", [*phase_compose, "run", "--rm", "--no-deps", "browser-tests", "node", "--version"],
            env=phase_env,
        ))
        run_step("recovery-gate", ["python3", "scripts/verify-phase2.py"], env=phase_env, timeout=3600)
        run_step("frontend-unit", [*phase_compose, "run", "--rm", "--no-deps", "--user", "0:0", "browser-tests", "npm", "test"],
                 env=phase_env, timeout=1200)
        release["environment"]["container_python"] = last_output_line(run_step(
            "container-python-version", [*phase_compose, "run", "--rm", "--no-deps", "tests", "python", "--version"],
            env=phase_env,
        ))
        release["environment"]["container_node"] = last_output_line(run_step(
            "container-node-version", [*phase_compose, "run", "--rm", "--no-deps", "browser-tests", "node", "--version"],
            env=phase_env,
        ))
        run_step("frontend-cleanup", [*phase_compose, "down", "--volumes", "--remove-orphans"],
                 env=phase_env, timeout=300)

        runtime_compose = compose(runtime_project)
        run_step("start", ["bash", "scripts/start.sh", "mock"], env=runtime_env, timeout=1200)
        origin = f"http://{last_output_line(run_step('api-port', [*runtime_compose, 'port', 'api', '8000'], env=runtime_env))}"
        api_env = dict(runtime_env, API_BASE_URL=origin)
        run_step("migrate", ["bash", "scripts/migrate.sh"], env=runtime_env, timeout=900)
        run_step("seed", ["bash", "scripts/seed-demo.sh"], env=api_env, timeout=600)
        run_step("smoke", ["bash", "scripts/smoke.sh", "mock"], env=api_env, timeout=600)
        run_step("logs", ["bash", "scripts/logs.sh"], env=runtime_env, timeout=180)
        run_step("artifact-maintenance-dry-run", ["bash", "scripts/artifact-gc.sh"], env=runtime_env, timeout=300)
        before_update = audio_snapshot(origin)
        (EVIDENCE / "before-update.json").write_text(json.dumps(before_update, indent=2), encoding="utf-8")
        run_step("rebuild-update", [*runtime_compose, "up", "-d", "--build", "--wait", "--wait-timeout", "180"],
                 env=runtime_env, timeout=2400)
        assert_persistence(before_update, audio_snapshot(origin))
        run_step("stop-preserving-volumes", ["bash", "scripts/stop.sh"], env=runtime_env, timeout=300)
        run_step("restart-after-stop", ["bash", "scripts/start.sh", "mock"], env=runtime_env, timeout=1200)
        origin = f"http://{last_output_line(run_step('api-port-after-stop', [*runtime_compose, 'port', 'api', '8000'], env=runtime_env))}"
        assert_persistence(before_update, audio_snapshot(origin))
        migration_revision = last_output_line(run_step(
            "migration-head", [*runtime_compose, "exec", "-T", "db", "psql", "-U", "museforge", "-d", "museforge", "-Atc",
                                "select version_num from alembic_version"], env=runtime_env,
        ))
        release["migration_head"] = {"revision": migration_revision, "readiness": url_json(origin, "/health/ready")}
        release["images"] = {"runtime": image_records(runtime_compose, runtime_env, "runtime"),
                              "phase": image_records(phase_compose, phase_env, "phase")}
        release["acceptance"] = {
            "A01-A12": "passed by isolated recovery/browser gate",
            "restart-and-update-persistence": "passed",
            "documented-lifecycle": "passed",
            "frontend-unit": "passed",
            "workspace-native-zoom": "passed by recovery gate workspace-inspection output",
        }
        if args.real_cpu:
            cpu_evidence = EVIDENCE / "real-cpu"
            cpu_env = command_env({"YUE2_CPU_THREADS": "4"})
            run_step("real-cpu-gate", ["python3", "scripts/verify-yue2-devices.py", "--cpu", "--normal",
                                        "--min-host-memory-gib", "32", "--memory-limit-gib", "28",
                                        "--evidence-dir", str(cpu_evidence)], env=cpu_env, timeout=7800)
            if not (cpu_evidence / "browser.json").is_file():
                raise ReleaseFailure("normal CPU gate did not retain browser acceptance evidence")
            release["acceptance"]["normal-mode-yue2-cpu"] = "passed"
            release["acceptance"]["normal-mode-yue2-browser"] = "passed"
            release["cpu_timing"] = json.loads((cpu_evidence / "timing.json").read_text(encoding="utf-8")) if (cpu_evidence / "timing.json").exists() else {}
        static_audit()
    except (ReleaseFailure, AssertionError, OSError, subprocess.TimeoutExpired) as exc:
        failure = exc
    except KeyboardInterrupt as exc:
        failure = exc
    finally:
        cleanup: list[dict[str, object]] = []
        if runtime_setup and owned_project(runtime_project):
            try:
                verify_project_ownership(runtime_project, runtime_env)
            except (OSError, ReleaseFailure, subprocess.TimeoutExpired) as exc:
                cleanup.append({"name": "cleanup-runtime-ownership", "returncode": 1, "error": str(exc)})
            else:
                cleanup.append(cleanup_step("cleanup-runtime-stop", ["bash", "scripts/stop.sh"], runtime_env))
                cleanup.append(cleanup_step("cleanup-runtime-down", [*compose(runtime_project), "down", "--volumes", "--remove-orphans"], runtime_env))
        if owned_project(phase_project):
            try:
                verify_project_ownership(phase_project, phase_env)
            except (OSError, ReleaseFailure, subprocess.TimeoutExpired) as exc:
                cleanup.append({"name": "cleanup-phase-ownership", "returncode": 1, "error": str(exc)})
            else:
                cleanup.append(cleanup_step("cleanup-phase-down", [*compose(phase_project, "-f", "compose.yaml", "-f", "compose.test.yaml"),
                                                                     "down", "--volumes", "--remove-orphans"], phase_env))
        release["cleanup"] = cleanup
        cleanup_failures = [item for item in cleanup if item.get("returncode") not in (0, None) or item.get("error")]
        release["outcomes"] = outcomes
        release["status"] = "failed" if failure or cleanup_failures else "passed"
        if failure:
            release["error"] = str(failure)
        if cleanup_failures:
            release["cleanup_error"] = "test-owned cleanup did not complete cleanly"
        (EVIDENCE / "release-summary.json").write_text(json.dumps(release, indent=2), encoding="utf-8")
    if failure or release["status"] != "passed":
        message = "interrupted" if isinstance(failure, KeyboardInterrupt) else str(failure or release.get("cleanup_error"))
        print(f"release verification failed: {message}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "passed", "evidence": str(EVIDENCE)}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--real-cpu", action="store_true", help="also run normal-mode pinned YuE2 on CPU")
    parser.add_argument("--in-clean-checkout", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--timeout", type=int, default=10800, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.timeout < 600:
        parser.error("timeout must be at least 600 seconds")
    if not args.in_clean_checkout and not os.environ.get("MUSEFORGE_RELEASE_IN_CHECKOUT"):
        return clean_checkout(args)
    return inner_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
