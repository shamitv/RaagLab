"""Technical audio checks; these do not judge music or lyric adherence."""
import hashlib
from pathlib import Path

import numpy as np
import soundfile as sf


def samples_metrics(audio, rate, *, test_smoke=False):
    finite = bool(np.isfinite(audio).all())
    channels = audio.shape[1] if audio.ndim == 2 else 1
    result = {'frames': len(audio), 'sample_rate': rate, 'channels': channels,
              'duration_seconds': len(audio) / rate, 'finite': finite}
    if finite and audio.size:
        absolute = np.abs(audio)
        result.update(peak=float(absolute.max()),
                      rms=float(np.sqrt(np.mean(audio.astype(np.float64) ** 2))),
                      near_clip_fraction=float(np.mean(absolute >= 0.999)),
                      silence_fraction=float(np.mean(absolute < 0.0001)))
    result['passed'] = (finite and len(audio) > 5 * rate and rate == 48000
                        and channels == 2 and result.get('rms', 0) > 0.0001
                        and result.get('near_clip_fraction', 1) < 0.01)
    if test_smoke:
        result['passed'] = finite and len(audio) > 0 and rate == 48000 and channels == 2 and result.get('peak', 0) > 0
    return result


def validate_file(path, *, test_smoke=False):
    path = Path(path)
    audio, rate = sf.read(path, dtype='float32', always_2d=True)
    result = samples_metrics(audio, rate, test_smoke=test_smoke)
    result.update(file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  pcm_sha256=hashlib.sha256(audio.tobytes()).hexdigest(),
                  byte_size=path.stat().st_size, format=sf.info(path).format)
    return result
