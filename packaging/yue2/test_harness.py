import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf

from run import supervise
from validate import samples_metrics, validate_file


class AudioChecks(unittest.TestCase):
    def setUp(self):
        time_axis = np.arange(48000 * 6) / 48000
        self.audio = np.repeat((0.1 * np.sin(2 * np.pi * 440 * time_axis))[:, None], 2, axis=1)

    def test_valid_flac_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'audio.flac'
            sf.write(path, self.audio, 48000, subtype='PCM_24')
            result = validate_file(path)
            self.assertTrue(result['passed'])
            self.assertEqual(result['format'], 'FLAC')
            self.assertEqual(result['duration_seconds'], 6)
            self.assertEqual(len(result['file_sha256']), 64)

    def test_silent_audio_fails(self):
        self.assertFalse(samples_metrics(np.zeros_like(self.audio), 48000)['passed'])

    def test_clipped_audio_fails(self):
        self.assertFalse(samples_metrics(np.ones_like(self.audio), 48000)['passed'])

    def test_nonfinite_audio_fails(self):
        self.audio[0, 0] = np.nan
        self.assertFalse(samples_metrics(self.audio, 48000)['passed'])

    def test_wrong_format_dimensions_fail(self):
        for audio, rate in [(self.audio[:, 0], 48000), (self.audio, 44100), (self.audio[:100], 48000)]:
            with self.subTest(rate=rate, shape=audio.shape):
                self.assertFalse(samples_metrics(audio, rate)['passed'])


class ProcessChecks(unittest.TestCase):
    def call(self, code, timeout=2):
        with tempfile.TemporaryDirectory() as directory:
            with patch('run.nvml.nvmlDeviceGetMemoryInfo', return_value=SimpleNamespace(used=100)):
                return supervise([sys.executable, '-c', code], Path(directory) / 'process.log',
                                 None, timeout=timeout)

    def test_success_and_failure(self):
        self.assertEqual(self.call('pass')['exit_code'], 0)
        self.assertEqual(self.call('raise SystemExit(7)')['exit_code'], 7)

    def test_timeout_reaps_and_subsequent_request_recovers(self):
        result = self.call('import time; time.sleep(100)', timeout=0.2)
        self.assertTrue(result['timed_out'])
        self.assertIsNotNone(result['exit_code'])
        self.assertLess(result['elapsed_seconds'], 3)
        self.assertEqual(self.call('pass')['exit_code'], 0)

    def test_stubborn_process_is_killed(self):
        result = self.call('import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(100)', timeout=0.5)
        self.assertTrue(result['timed_out'])
        self.assertEqual(result['exit_code'], -9)
        self.assertLess(result['elapsed_seconds'], 8)

    def test_prompt_contract(self):
        prompts = json.loads(Path('prompts.json').read_text())
        self.assertEqual([p['seed'] for p in prompts], [42, 43, 44])
        self.assertEqual(len({p['id'] for p in prompts}), 3)
        self.assertTrue(all('[Verse]' in p['lyrics'] and '[Chorus]' in p['lyrics']
                            and p['cot'] == 'full' for p in prompts))


if __name__ == '__main__':
    unittest.main()
