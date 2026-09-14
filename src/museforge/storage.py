"""Validated attempt-specific publication and constrained artifact lookup."""
import hashlib
import os
import wave
from pathlib import Path
from uuid import uuid4
from museforge.domain import ProviderError


def resolve(root: Path, key: str) -> Path:
    if root.is_symlink() or Path(key).is_absolute() or any(p in ('.', '..') for p in key.split('/')):
        raise ProviderError('artifact_unavailable')
    candidate = root
    for part in Path(key).parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ProviderError('artifact_unavailable')
    try:
        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
            raise ProviderError('artifact_unavailable')
        return resolved
    except OSError:
        raise ProviderError('artifact_unavailable') from None


def inspect(path: Path, *, expected_sample_rate: int = 44100) -> dict:
    try:
        with wave.open(str(path), 'rb') as audio:
            rate, channels, width, frames = audio.getframerate(), audio.getnchannels(), audio.getsampwidth(), audio.getnframes()
            samples = audio.readframes(frames)
            if rate != expected_sample_rate or channels != 2 or width != 2 or not frames or len(samples) != frames * channels * width or not any(samples):
                raise ValueError
        content = path.read_bytes()
        return dict(sha256=hashlib.sha256(content).hexdigest(), byte_size=len(content), media_type='audio/wav',
                    sample_rate=rate, channels=channels, duration_seconds=frames / rate)
    except (OSError, EOFError, wave.Error, ValueError):
        raise ProviderError('malformed_media') from None


def publish(root: Path, temporary: Path, job_id, fence: int, duration: int | None = None,
            *, expected_sample_rate: int = 44100) -> dict:
    metadata = inspect(temporary, expected_sample_rate=expected_sample_rate)
    if duration is not None and metadata['duration_seconds'] != duration:
        raise ProviderError('malformed_media')
    key = f'{job_id}-{fence}-{uuid4()}.wav'
    with temporary.open('rb') as file:
        os.fsync(file.fileno())
    temporary.replace(root / key)
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(directory)
    finally: os.close(directory)
    return dict(metadata, storage_key=key)


def open_artifact(root: Path, key: str):
    """Open each stored component without following symlinks, including at read time."""
    import stat
    components = key.split('/')
    if not components or any(part in ('', '.', '..') for part in components):
        raise ProviderError('artifact_unavailable')
    directory = None
    try:
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for component in components[:-1]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        descriptor = os.open(components[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        file = os.fdopen(descriptor, 'rb')
        if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
            file.close()
            raise ProviderError('artifact_unavailable')
        return file
    except (OSError, ValueError):
        raise ProviderError('artifact_unavailable') from None
    finally:
        if directory is not None: os.close(directory)


def range_bounds(value: str, size: int) -> tuple[int, int]:
    import re
    match = re.fullmatch(r'bytes=(\d*)-(\d*)', value)
    if not match or not any(match.groups()): raise ValueError('invalid_range')
    start, end = match.groups()
    if not start:
        suffix = int(end)
        if suffix == 0: raise ValueError('invalid_range')
        return max(0, size-suffix), size-1
    first = int(start)
    last = min(int(end),size-1) if end else size-1
    if first >= size or last < first: raise ValueError('invalid_range')
    return first,last
