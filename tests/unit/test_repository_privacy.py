from __future__ import annotations

from pathlib import Path
import re
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]


def tracked_text() -> list[tuple[Path, str]]:
    if not (ROOT / ".git").exists():
        pytest.skip("tracked-file privacy audit requires a Git checkout")
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    records: list[tuple[Path, str]] = []
    for raw_name in result.stdout.split(b"\0"):
        if not raw_name:
            continue
        path = ROOT / raw_name.decode("utf-8")
        if not path.is_file():
            continue
        try:
            records.append((path, path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            continue
    return records


def test_tracked_tree_has_no_machine_specific_locations_or_addresses():
    patterns = {
        "personal home path": re.compile(
            r"(?:/home/[A-Za-z0-9._-]+/|/Users/[A-Za-z0-9._-]+/|/" + "root/)"
        ),
        "WSL-mounted drive path": re.compile(r"/mnt/[A-Za-z]/"),
        "Windows drive path": re.compile(r"(?:^|[\s`'\"])[A-Z]:[\\/]"),
        "Docker host volume path": re.compile(r"/var/lib/docker/" r"volumes/"),
    }
    private_address = re.compile(
        r"(?<![0-9.])(?:"
        r"10(?:\.[0-9]{1,3}){3}|"
        r"192\.168(?:\.[0-9]{1,3}){2}|"
        r"172\.(?:1[6-9]|2[0-9]|3[01])(?:\.[0-9]{1,3}){2}"
        r")(?![0-9.])"
    )
    # NVIDIA's pinned curand package version is syntactically a private IPv4
    # address, but it is dependency metadata rather than a host address.
    allowed_version = ".".join(("10", "3", "9", "90"))
    failures: list[str] = []
    for path, content in tracked_text():
        relative = path.relative_to(ROOT)
        for label, pattern in patterns.items():
            if pattern.search(content):
                failures.append(f"{relative}: {label}")
        if any(match.group() != allowed_version for match in private_address.finditer(content)):
            failures.append(f"{relative}: private IPv4 address")
    assert not failures, "machine-specific tracked content:\n" + "\n".join(failures)


def test_tracked_tree_has_no_retired_machine_aliases():
    # Assemble retired values so the regression test does not contain the
    # machine identifiers it prohibits.
    retired = (
        "Ubuntu" + "1",
        "ubuntu" + "1",
        "yo" + "lo1",
        "i3" + "tiny1",
    )
    failures: list[str] = []
    for path, content in tracked_text():
        relative = path.relative_to(ROOT)
        for value in retired:
            if value in content or value in relative.as_posix():
                failures.append(f"{relative}: retired machine alias")
    assert not failures, "retired machine identifiers remain:\n" + "\n".join(failures)


def test_tracked_documentation_does_not_link_into_local_state():
    local_link = re.compile(r"\]\([^)]*\.local/")
    failures = [
        str(path.relative_to(ROOT))
        for path, content in tracked_text()
        if path.suffix.lower() == ".md" and local_link.search(content)
    ]
    assert not failures, "tracked documentation links into ignored local state:\n" + "\n".join(failures)
