"""Original, deterministic demo providers; no external audio or lyrics."""
import math
import random
import struct
import wave
from pathlib import Path
from typing import Callable, Protocol
from museforge.domain import ProviderError, Lyrics, capabilities

STATIC = '[Verse]\nMorning opens quiet doors\nLight is dancing on the floor\n\n[Chorus]\nCarry every little spark\nLet it glow against the dark\n'

class CancellationToken(Protocol):
    def __call__(self) -> None: ...

class LyricsProvider(Protocol):
    def capabilities(self) -> dict: ...
    def readiness(self) -> str: ...
    def normalize(self, request: dict) -> dict: ...
    def generate(self, request: dict, progress_callback: Callable, cancellation_token: CancellationToken) -> dict: ...

class MusicProvider(Protocol):
    def capabilities(self) -> dict: ...
    def readiness(self) -> str: ...
    def normalize(self, request: dict) -> dict: ...
    def generate(self, request: dict, progress_callback: Callable, cancellation_token: CancellationToken) -> Path: ...

class DemoLyrics:
    def capabilities(self): return capabilities()
    def readiness(self): return 'ready'
    def normalize(self, request):
        try: Lyrics.model_validate(request['lyrics'])
        except (ValueError, KeyError): raise ProviderError('invalid_request') from None
        return request
    def generate(self, request, progress_callback, cancellation_token):
        self.normalize(request)
        cancellation_token()
        mode = request['lyrics']['mode']
        if mode == 'user':
            content = request['lyrics']['text']
        elif mode == 'static':
            content = STATIC
        else:
            word = random.Random(request['seed']).choice(['morning', 'river', 'starlight', 'garden'])
            content = f'[Verse]\nWe follow the {word} today\nAnd find a little song along the way\n\n[Chorus]\nA moment held, a new day near\nWe carry all our music here\n'
        return {'text': content, 'source': mode, 'provider_revision': '1',
                'fixture_id': 'morning-spark' if mode == 'static' else None,
                'fixture_revision': '1' if mode == 'static' else None}

class MockMusic:
    def __init__(self, output: Path): self.output = output
    def capabilities(self): return capabilities()
    def readiness(self): return 'ready'
    def normalize(self, request):
        if not 5 <= request['duration_seconds'] <= 30:
            raise ProviderError('invalid_request')
        return request
    def generate(self, request, progress_callback, cancellation_token):
        self.normalize(request)
        rng = random.Random(request['seed'])
        notes = [rng.choice([220, 261.6256, 293.6648, 329.6276, 391.9954]) for _ in range(16)]
        rate, frames = 44100, 44100 * request['duration_seconds']
        with wave.open(str(self.output), 'wb') as audio:
            audio.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
            for start in range(0, frames, 4096):
                cancellation_token()
                block = bytearray()
                for i in range(start, min(start + 4096, frames)):
                    t = i / rate
                    frequency = notes[int(t * 2) % len(notes)]
                    envelope = min(1, t * 8, (frames - i) / rate * 8) * (0.65 + 0.35 * math.sin(math.pi * (t * 2 % 1)))
                    left = int(6500 * envelope * (math.sin(2 * math.pi * frequency * t) + .25 * math.sin(2 * math.pi * frequency / 2 * t)))
                    right = int(left * .9)
                    block.extend(struct.pack('<hh', left, right))
                audio.writeframesraw(block)
        return self.output
