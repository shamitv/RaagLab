#!/usr/bin/env python3
"""Run the Phase 6 release gate in isolated, disposable Compose projects.

The runner deliberately uses the public shell entry points for the normal
stack lifecycle and the Phase 4 harness for the durable recovery matrix. A
release run writes concise command output and JSON observations below
``test-results/phase6-<run-id>``; it never targets the user's default Compose
project.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
EVIDENCE = ROOT / "test-results" / f"phase6-{RUN_ID}"
EVIDENCE.mkdir(parents=True, exist_ok=True)
REPO_ENV = dict(os.environ)


class ReleaseFailure(RuntimeError):
    pass


outcomes: list[dict[str, object]] = []
OWNED_PROJECT_PREFIXES = ("museforge-phase6-test-", "museforge-phase6-runtime-")


def owned_project(project: str) -> bool:
    """Return whether a Compose project is safe for the release cleanup path."""
    return project.startswith(OWNED_PROJECT_PREFIXES)


def command_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(REPO_ENV)
    if extra:
        env.update(extra)
    return env


def run_step(name: str, command: list[str], *, env: dict[str, str] | None = None,
             cwd: Path = ROOT, timeout: int = 1800, check: bool = True) -> str:
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env or REPO_ENV,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    output = result.stdout
    (EVIDENCE / f"{name}.log").write_text(output, encoding="utf-8")
    record = {
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "log": f"{name}.log",
    }
    outcomes.append(record)
    if check and result.returncode:
        raise ReleaseFailure(f"{name} failed with exit code {result.returncode}")
    return output


def compose(project: str, *args: str) -> list[str]:
    return [
        "docker", "compose", "--project-name", project, "--env-file", ".env",
        "--profile", "mock", *args,
    ]


def last_output_line(output: str) -> str:
    """Extract a scalar from Compose output that may include progress banners."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return lines[-1] if lines else ""


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
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                raise ReleaseFailure(f"broken documentation link in {path}: {target}")


def sanitized_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if re.search(r"pass|secret|token|key|url", key, re.I):
            values[key] = "<redacted>"
        else:
            values[key] = value
    return values


def main() -> int:
    phase_project = f"museforge-phase6-test-{uuid.uuid4().hex[:10]}"
    runtime_project = f"museforge-phase6-runtime-{uuid.uuid4().hex[:10]}"
    phase_evidence = EVIDENCE / "recovery-gate"
    phase_evidence.mkdir(parents=True, exist_ok=True)
    phase_env = command_env({
        "MUSEFORGE_TEST_PROJECT": phase_project,
        "MUSEFORGE_TEST_PROJECT_PREFIX": "museforge-phase6-test-",
        "MUSEFORGE_EVIDENCE_DIR": str(phase_evidence),
        "MUSEFORGE_RECOVERY_CHECKS": "1",
        "PHASE4_BROWSER": "1",
        "PHASE6_VISUAL": "1",
    })
    runtime_env = command_env({
        "COMPOSE_PROJECT_NAME": runtime_project,
        "APP_PORT": "0",
    })
    release = {
        "phase": "06-release-verification-and-handoff",
        "run_id": RUN_ID,
        "phase_project": phase_project,
        "runtime_project": runtime_project,
        "source_revision": run_step("source-revision", ["git", "rev-parse", "HEAD"]).strip(),
        "environment": {},
        "outcomes": outcomes,
        "acceptance": {},
    }
    runtime_started = False
    try:
        run_step("setup", ["bash", "scripts/setup.sh"], env=runtime_env, timeout=180)
        release["environment"] = {
            "python": run_step("python-version", ["python3", "--version"]).strip(),
            "node": run_step("node-version", ["node", "--version"]).strip(),
            "docker": run_step("docker-version", ["docker", "version", "--format", "{{.Server.Version}}"]).strip(),
            "compose": run_step("compose-version", ["docker", "compose", "version", "--short"]).strip(),
            "sanitized_env": sanitized_env(),
            "locks": {
                str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in [
                    ROOT / "uv.lock",
                    ROOT / "apps/web/package-lock.json",
                    ROOT / "packaging/yue2/requirements.museforge.lock",
                    ROOT / "packaging/yue2/model-lock.json",
                ]
            },
            "runtime_overrides": {
                "COMPOSE_PROJECT_NAME": runtime_project,
                "APP_PORT": "0 (ephemeral loopback port)",
            },
        }

        # The recovery gate builds every pinned runtime/test image and exercises
        # A01-A12 through actual PostgreSQL, RabbitMQ, workers, and API browser.
        run_step("recovery-gate", ["python3", "scripts/verify-phase2.py"], env=phase_env, timeout=3600)
        phase_compose = compose(phase_project, "-f", "compose.yaml", "-f", "compose.test.yaml")
        run_step("frontend-unit", [*phase_compose, "run", "--rm", "--no-deps", "browser-tests", "npm", "test"],
                 env=phase_env, timeout=1200)
        release["environment"]["container_python"] = run_step(
            "container-python-version",
            [*phase_compose, "run", "--rm", "--no-deps", "tests", "python", "--version"],
            env=phase_env,
        )
        release["environment"]["container_python"] = last_output_line(release["environment"]["container_python"])
        release["environment"]["container_node"] = run_step(
            "container-node-version",
            [*phase_compose, "run", "--rm", "--no-deps", "browser-tests", "node", "--version"],
            env=phase_env,
        )
        release["environment"]["container_node"] = last_output_line(release["environment"]["container_node"])
        run_step("frontend-cleanup", [*phase_compose, "down", "--volumes", "--remove-orphans"],
                 env=phase_env, timeout=300)

        # Exercise the documented normal lifecycle in a separate project. The
        # project is explicitly named so cleanup cannot touch a user stack.
        run_step("start", ["bash", "scripts/start.sh", "mock"], env=runtime_env, timeout=1200)
        runtime_started = True
        runtime_compose = compose(runtime_project)
        origin = last_output_line(run_step("api-port", [*runtime_compose, "port", "api", "8000"], env=runtime_env))
        origin = f"http://{origin}"
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
        after_update = audio_snapshot(origin)
        assert_persistence(before_update, after_update)
        run_step("stop-preserving-volumes", ["bash", "scripts/stop.sh"], env=runtime_env, timeout=300)
        run_step("restart-after-stop", ["bash", "scripts/start.sh", "mock"], env=runtime_env, timeout=1200)
        origin = f"http://{last_output_line(run_step("api-port-after-stop", [*runtime_compose, "port", "api", "8000"], env=runtime_env))}"
        after_stop = audio_snapshot(origin)
        assert_persistence(before_update, after_stop)
        migration_revision = last_output_line(run_step(
            "migration-head",
            [*runtime_compose, "exec", "-T", "db", "psql", "-U", "museforge", "-d", "museforge", "-Atc",
             "select version_num from alembic_version"],
            env=runtime_env,
        ))
        release["acceptance"] = {
            "A01-A12": "passed by isolated recovery/browser gate",
            "restart-and-update-persistence": "passed",
            "documented-lifecycle": "passed",
            "frontend-unit": "passed",
            "workspace-native-zoom": "passed by recovery gate workspace-inspection output",
        }
        release["migration_head"] = {
            "revision": migration_revision,
            "readiness": url_json(origin, "/health/ready"),
        }
        release["images"] = run_step("resolved-images", [*runtime_compose, "config", "--images"], env=runtime_env).splitlines()
        release["status"] = "passed"
        static_audit()
        (EVIDENCE / "release-summary.json").write_text(json.dumps(release, indent=2), encoding="utf-8")
        print(json.dumps({"status": "passed", "evidence": str(EVIDENCE), "origin": origin}, indent=2))
        return 0
    except (ReleaseFailure, subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError, AssertionError) as exc:
        release["status"] = "failed"
        release["error"] = str(exc)
        (EVIDENCE / "release-summary.json").write_text(json.dumps(release, indent=2), encoding="utf-8")
        print(f"release verification failed: {exc}", file=sys.stderr)
        return 1
    finally:
        # The normal stop path is always attempted first. Only the named test
        # project is eligible for volume deletion after evidence is written.
        if runtime_started:
            subprocess.run(["bash", "scripts/stop.sh"], cwd=ROOT, env=runtime_env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
        if owned_project(runtime_project):
            subprocess.run([*compose(runtime_project), "down", "--volumes", "--remove-orphans"],
                           cwd=ROOT, env=runtime_env, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, check=False, timeout=300)
        if owned_project(phase_project):
            subprocess.run(
                [*compose(phase_project, "-f", "compose.yaml", "-f", "compose.test.yaml"),
                 "down", "--volumes", "--remove-orphans"],
                cwd=ROOT, env=phase_env, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, check=False, timeout=300,
            )


if __name__ == "__main__":
    raise SystemExit(main())
