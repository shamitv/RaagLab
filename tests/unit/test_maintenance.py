from types import SimpleNamespace
import uuid

import pytest

from museforge.maintenance import collect, parse_attempt_file


def test_artifact_attempt_filenames_are_strictly_parsed():
    job = uuid.uuid4()
    artifact = uuid.uuid4()
    assert parse_attempt_file(f"{job}-4-{artifact}.wav") == (job, 4)
    assert parse_attempt_file(f".{job}-12-temporary-name.tmp") == (job, 12)
    assert parse_attempt_file(f"../{job}-4-{artifact}.wav") is None
    assert parse_attempt_file(f"{job}-0-{artifact}.mp3") is None


@pytest.mark.parametrize("apply", [False, True])
def test_gc_rejects_a_grace_period_shorter_than_one_day(apply):
    with pytest.raises(ValueError, match="at least 24 hours"):
        collect(None, SimpleNamespace(artifact_root="/unused"), apply=apply, grace_seconds=86399)
