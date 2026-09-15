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
    command = release.compose("museforge-phase6-test-abc", "config", "--images")
    assert command[command.index("--project-name") + 1] == "museforge-phase6-test-abc"
    assert release.owned_project("museforge-phase6-test-abc")
    assert release.owned_project("museforge-phase6-runtime-abc")
    assert not release.owned_project("default")
    assert not release.owned_project("survey_app")


def test_failed_step_keeps_output_and_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(release, "EVIDENCE", tmp_path)
    with pytest.raises(release.ReleaseFailure):
        release.run_step(
            "expected-failure",
            [sys.executable, "-c", "print('release failure fixture'); raise SystemExit(7)"],
            timeout=10,
        )
    assert (tmp_path / "expected-failure.log").read_text().strip() == "release failure fixture"


def test_persistence_comparison_rejects_mutation():
    before = {"projects": [{"id": "p", "audio": {"sha256": "a"}}], "settings": {"revision": 1}}
    release.assert_persistence(before, before.copy())
    with pytest.raises(release.ReleaseFailure):
        release.assert_persistence(before, {**before, "settings": {"revision": 2}})
