"""Local, Docker-free checks for Phase 6 release-runner safety."""

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("museforge_verify_release", ROOT / "scripts/verify-release.py")
assert SPEC and SPEC.loader
release = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = release
SPEC.loader.exec_module(release)


def test_compose_and_cleanup_names_are_explicitly_owned():
    project = "museforge-phase6-test-0123456789"
    command = release.compose(project, "config", "--images")
    assert command[command.index("--project-name") + 1] == project
    assert release.owned_project(project)
    assert release.owned_project("museforge-phase6-runtime-abcdef1234")
    assert not release.owned_project("default")
    assert not release.owned_project("survey_app")
    assert not release.owned_project("museforge-phase6-test-user-owned")


def test_cleanup_rejects_foreign_docker_labels(monkeypatch):
    class Result:
        returncode = 0
        stdout = "foreign-container\n"

    def fake_run(command, **kwargs):
        assert command[:3] in (["docker", "ps", "-aq"], ["docker", "inspect", "--format"])
        if command[1] == "ps":
            return Result()
        result = Result()
        result.stdout = '{"com.docker.compose.project":"someone-else"}'
        return result

    monkeypatch.setattr(release.subprocess, "run", fake_run)
    with pytest.raises(release.ReleaseFailure, match="outside owned project"):
        release.verify_project_ownership("museforge-phase6-test-0123456789", release.command_env())


def test_child_environment_is_allowlisted():
    child = release.command_env({"PATH": "/safe", "MUSEFORGE_SECRET": "do-not-pass"})
    assert child["PATH"] == "/safe"
    assert "MUSEFORGE_SECRET" not in child


def test_failed_step_keeps_output_and_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(release, "EVIDENCE", tmp_path)
    with pytest.raises(release.ReleaseFailure):
        release.run_step(
            "expected-failure",
            [sys.executable, "-c", "print('release failure fixture'); raise SystemExit(7)"],
            timeout=10,
        )
    assert (tmp_path / "expected-failure.log").read_text().strip() == "release failure fixture"


def test_timeout_keeps_partial_output(tmp_path, monkeypatch):
    monkeypatch.setattr(release, "EVIDENCE", tmp_path)
    with pytest.raises(release.ReleaseFailure, match="timed out"):
        release.run_step(
            "expected-timeout",
            [sys.executable, "-c", "import sys,time; print('partial', flush=True); time.sleep(2)"],
            timeout=0.5,
        )
    assert "partial" in (tmp_path / "expected-timeout.log").read_text()


@pytest.mark.skipif(sys.platform != "linux", reason="process-group semantics are Linux-specific")
def test_timeout_terminates_process_group(tmp_path, monkeypatch):
    monkeypatch.setattr(release, "EVIDENCE", tmp_path)
    marker = tmp_path / "child.pid"
    code = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); open(sys.argv[1],'w').write(str(p.pid)); time.sleep(30)"
    with pytest.raises(release.ReleaseFailure, match="timed out"):
        release.run_step("group-timeout", [sys.executable, "-c", code, str(marker)], timeout=0.2)
    assert marker.exists()
    child_pid = int(marker.read_text())
    try:
        state = (Path(f"/proc/{child_pid}/stat").read_text().split()[2])
    except FileNotFoundError:
        state = "gone"
    assert state in {"gone", "Z"}


def test_cleanup_failure_is_recorded(tmp_path, monkeypatch):
    monkeypatch.setattr(release, "EVIDENCE", tmp_path)
    result = release.cleanup_step(
        "cleanup-failure",
        [sys.executable, "-c", "raise SystemExit(9)"],
        release.command_env(),
        timeout=10,
    )
    assert result["returncode"] == 9
    assert (tmp_path / "cleanup-failure.log").exists()


def test_persistence_comparison_rejects_mutation():
    before = {"projects": [{"id": "p", "audio": {"sha256": "a"}}], "settings": {"revision": 1}}
    release.assert_persistence(before, before.copy())
    with pytest.raises(release.ReleaseFailure):
        release.assert_persistence(before, {**before, "settings": {"revision": 2}})
