from pathlib import Path
import sys
import types
import wave
import pytest
from pydantic import ValidationError
from museforge.domain import (
    CapabilitiesResponse, Generation, ProviderError, Lyrics,
    capability_matrix, provider_capabilities,
)
from museforge.providers import DemoLyrics, MockMusic, YuE2Music, STATIC
from museforge.config import Settings
from museforge.storage import inspect, publish, resolve

TEXT = '  [अंतरा]\r\nहवा 🎵\n\n[பல்லவி]\nவானம்\t\n'

@pytest.mark.parametrize('mode', ['user', 'static', 'mock'])
def test_lyrics_source_and_exact_preservation(mode):
    request = {'lyrics': {'mode': mode, 'text': TEXT}, 'seed': 12}
    provider = DemoLyrics()
    progress = []
    first = provider.generate(request, progress.append, lambda: None)
    assert first == provider.generate(request, lambda *_: None, lambda: None)
    assert progress == ['writing_lyrics']
    assert first['source'] == mode
    assert first['text'] == (TEXT if mode == 'user' else STATIC if mode == 'static' else first['text'])
    assert first['text']

@pytest.mark.parametrize('duration', [5, 8, 30])
def test_audio_decodes_deterministically_and_publishes(tmp_path, duration):
    request = {'duration_seconds': duration, 'seed': 123}
    paths = [tmp_path / f'{i}.tmp' for i in range(2)]
    progress = []
    providers = [MockMusic(path) for path in paths]
    for provider in providers:
        provider.generate(request, progress.append, lambda: None)
    assert paths[0].read_bytes() == paths[1].read_bytes()
    assert progress == ['composing_music', 'composing_music']
    assert providers[0].readiness() == 'ready'
    assert providers[0].metadata == {
        'actual_duration_seconds': duration, 'sample_rate': 44100, 'channels': 2,
        'seed': 123, 'provider_output_format': 'WAV/PCM_16',
        'effective_settings': {'duration_seconds': duration, 'seed': 123},
    }
    info = inspect(paths[0])
    assert info['duration_seconds'] == duration
    assert info['sample_rate'] == 44100 and info['channels'] == 2
    assert info['byte_size'] == duration * 44100 * 4 + 44
    result = publish(tmp_path, paths[0], 'test', 1, duration)
    assert resolve(tmp_path, result['storage_key']).exists()
    assert not paths[0].exists()


def test_real_audio_rate_can_be_published_without_requested_duration(tmp_path):
    path = tmp_path / 'real.wav'
    rate, frames = 48000, 48000 * 6
    with wave.open(str(path), 'wb') as audio:
        audio.setparams((2, 2, rate, 0, 'NONE', 'not compressed'))
        audio.writeframes(b'\x01\x00\x01\x00' * frames)
    result = publish(tmp_path, path, 'real', 1, None, expected_sample_rate=48000)
    assert result['sample_rate'] == 48000
    assert result['duration_seconds'] == 6

@pytest.mark.parametrize('change', [{'brief': ' '}, {'brief': 'a'*501}, {'instruments': []}, {'instruments': ['Tabla','Tabla']},
    {'seed': -1}, {'seed': True}, {'duration_seconds': 4}, {'duration_seconds': 31}, {'duration_seconds': 8.5},
    {'vocal_type':'Male Vocals'}, {'unknown': True}, {'lyrics': {'mode':'user','text':' '}}])
def test_invalid_generation(change):
    with pytest.raises(ValidationError):
        Generation.model_validate(dict(brief='hello', instruments=['Tabla'], mood='Calm') | change)


def test_unicode_limits():
    assert Lyrics(mode='user', text=TEXT).text == TEXT
    with pytest.raises(ValidationError): Lyrics(mode='user', text='a'*20001)
    with pytest.raises(ValidationError): Lyrics(mode='user', text='\ud800')
    assert len(Generation(brief='🎵'*500, instruments=['Piano'], mood='Calm').brief) == 500


def test_cooperative_cancellation(tmp_path):
    def cancel(): raise ProviderError('cancelled')
    progress = []
    with pytest.raises(ProviderError, match='cancelled'):
        MockMusic(tmp_path/'audio.tmp').generate({'duration_seconds': 8,'seed': 1}, progress.append, cancel)
    assert progress == ['composing_music']
    assert not (tmp_path/'audio.tmp').exists()


@pytest.mark.parametrize('provider_request', [
    {'duration_seconds': True, 'seed': 1},
    {'duration_seconds': 4, 'seed': 1},
    {'duration_seconds': 8, 'seed': True},
    {'duration_seconds': 8, 'seed': '4'},
])
def test_mock_music_rejects_invalid_provider_input(tmp_path, provider_request):
    with pytest.raises(ProviderError, match='invalid_request'):
        MockMusic(tmp_path / 'audio.tmp').normalize(provider_request)


def yue2_settings():
    return Settings(_env_file=None, music_provider='yue2', lyrics_provider='user', device='cuda',
                    precision='bfloat16', model_id='m-a-p/YuE2-3B',
                    model_revision='model-revision', decoder_revision='vae-revision')


def yue2_request(**changes):
    request = {'operation': 'generate', 'language': 'English', 'vocal_type': 'Instrumental',
               'lyrics': {'mode': 'user', 'text': '[Verse]\nA test lyric'}, 'brief': 'A short test song',
               'genre': 'Folk', 'mood': 'Calm', 'tempo': 'Medium',
               'instruments': ['Guitar'], 'seed': 42, 'duration_seconds': 8}
    return request | changes


def yue2_runner(tmp_path, body):
    path = tmp_path / 'runner.py'
    path.write_text('import sys\nimport time\nfrom pathlib import Path\n' + body)
    return path


def yue2_fake_audio_modules(monkeypatch):
    class Audio:
        shape = (288001, 2)

        def __len__(self):
            return self.shape[0]

    class Finite:
        def all(self):
            return True

    fake_numpy = types.SimpleNamespace(isfinite=lambda value: Finite(), any=lambda value: True)
    fake_soundfile = types.SimpleNamespace(
        read=lambda *args, **kwargs: (Audio(), 48000),
        write=lambda path, audio, rate, **kwargs: Path(path).write_bytes(b'RIFF'),
    )
    monkeypatch.setitem(sys.modules, 'numpy', fake_numpy)
    monkeypatch.setitem(sys.modules, 'soundfile', fake_soundfile)


def test_yue2_normalizes_verified_request_and_maps_style(tmp_path):
    provider = YuE2Music(yue2_settings(), tmp_path / 'audio.wav')
    request = provider.normalize(yue2_request())
    assert request['lyrics']['mode'] == 'user'
    assert 'English folk instrumental music' in provider._style(request)
    assert 'A short test song' in provider._style(request)


def test_yue2_child_success_transcodes_and_records_provenance(tmp_path, monkeypatch):
    runner = yue2_runner(tmp_path, """
output = Path(sys.argv[2])
output.mkdir(parents=True)
(output / 'audio.flac').write_bytes(b'fake flac')
(output / 'validation.json').write_text('{\"torch_peak_allocated_bytes\": 11, \"torch_peak_reserved_bytes\": 22}')
""")
    settings = yue2_settings().model_copy(update={'yue2_runner': runner})
    output = tmp_path / 'audio.wav'
    provider = YuE2Music(settings, output)
    yue2_fake_audio_modules(monkeypatch)
    provider.generate(yue2_request(), lambda *_: None, lambda: None)
    assert output.read_bytes() == b'RIFF'
    assert provider.metadata['sample_rate'] == 48000
    assert provider.metadata['gpu_resource']['torch_peak_reserved_bytes'] == 22


def test_yue2_child_cancellation_reaps_process(tmp_path):
    runner = yue2_runner(tmp_path, """
time.sleep(30)
""")
    settings = yue2_settings().model_copy(update={'yue2_runner': runner})
    provider = YuE2Music(settings, tmp_path / 'audio.wav')
    def cancel():
        raise ProviderError('cancelled')
    with pytest.raises(ProviderError, match='cancelled'):
        provider.generate(yue2_request(), lambda *_: None, cancel)
    assert not YuE2Music._active_processes


def test_yue2_child_deadline_and_malformed_output(tmp_path):
    runner = yue2_runner(tmp_path, """
time.sleep(30)
""")
    settings = yue2_settings().model_copy(update={'yue2_runner': runner, 'yue2_process_timeout_seconds': 1})
    provider = YuE2Music(settings, tmp_path / 'deadline.wav')
    with pytest.raises(ProviderError, match='deadline_exceeded'):
        provider.generate(yue2_request(), lambda *_: None, lambda: None)

    malformed_runner = yue2_runner(tmp_path, """
output = Path(sys.argv[2])
output.mkdir(parents=True)
""")
    malformed_settings = settings.model_copy(update={'yue2_runner': malformed_runner, 'yue2_process_timeout_seconds': 5})
    with pytest.raises(ProviderError, match='malformed_media'):
        YuE2Music(malformed_settings, tmp_path / 'malformed.wav').generate(
            yue2_request(), lambda *_: None, lambda: None)


@pytest.mark.parametrize('change', [
    {'language': 'Hindi'}, {'lyrics': {'mode': 'mock', 'text': None}},
    {'operation': 'variation'}, {'vocal_type': 'Male Vocals'},
    {'iteration_instruction': 'add a bridge'},
])
def test_yue2_rejects_unverified_request_shapes(tmp_path, change):
    provider = YuE2Music(yue2_settings(), tmp_path / 'audio.wav')
    with pytest.raises(ProviderError):
        provider.normalize(yue2_request(**change))


def test_yue2_failure_classification(tmp_path):
    folder = tmp_path / 'output'
    folder.mkdir()
    (folder / 'failure.json').write_text('{"category":"cuda_oom"}')
    assert YuE2Music._failure_code(folder) == ('resource_exhaustion', False)
    (folder / 'failure.json').write_text('{"category":"missing_weights"}')
    assert YuE2Music._failure_code(folder) == ('initialization_failure', False)
    (folder / 'failure.json').unlink()
    (folder / 'validation.json').write_text('{}')
    assert YuE2Music._failure_code(folder) == ('malformed_media', False)


def test_yue2_capabilities_are_narrow_and_provider_specific():
    caps = provider_capabilities(yue2_settings())
    assert caps['provider_id'] == 'yue2'
    assert caps['provider_route'] == 'museforge.yue2.v1'
    assert caps['sample_rates'] == [48000]
    assert caps['operations'] == ['generate']
    assert caps['text_to_instrumental'] is None
    assert caps['vocals'] is None
    assert caps['exact_lyrics_vocals'] is None
    assert caps['capability_matrix']['instrumental_music_generation'].state == 'unknown'
    assert caps['capability_matrix']['vocal_generation'].state == 'unknown'
    assert caps['capability_matrix']['exact_lyrics_singing'].state == 'unknown'
    assert caps['capability_matrix']['duration_control'].state == 'unsupported'
    assert any('may contain vocals' in warning for warning in caps['warnings'])


def test_capability_matrix_distinguishes_known_gaps_from_unknown_behavior():
    mock = capability_matrix('mock')
    real = capability_matrix('yue2')
    assert mock['lyrics_text_generation'].state == 'supported'
    assert mock['vocal_generation'].state == 'unsupported'
    assert mock['instrument_control'].state == 'unsupported'
    assert real['lyrics_text_generation'].state == 'unsupported'
    assert real['instrument_control'].state == 'unknown'
    assert real['continuation'].state == 'unsupported'

    response = CapabilitiesResponse.model_validate(
        provider_capabilities(yue2_settings()) | {
            'default_lyrics_mode': 'user',
            'readiness': {'state': 'offline', 'last_observed_at': None},
            'duration': {'min': 5, 'max': 30, 'default': 8},
        }
    )
    assert response.capability_matrix['exact_lyrics_singing'].state == 'unknown'


def test_storage_rejects_traversal_symlink_and_malformed(tmp_path):
    path = tmp_path/'bad.wav'; path.write_bytes(b'not audio')
    (tmp_path/'link').symlink_to(path)
    for key in ('../outside', '/etc/passwd', 'link', 'missing', './bad.wav'):
        with pytest.raises(ProviderError): resolve(tmp_path,key)
    with pytest.raises(ProviderError, match='malformed_media'): inspect(path)

@pytest.mark.parametrize(('value','expected'), [('bytes=0-43',(0,43)),('bytes=-20',(80,99)),('bytes=90-',(90,99)),('bytes=-500',(0,99)),('bytes=0-500',(0,99))])
def test_single_ranges(value,expected):
    from museforge.storage import range_bounds
    assert range_bounds(value,100)==expected

@pytest.mark.parametrize('value',['bytes=100-','bytes=9-2','bytes=-0','bytes=-','items=0-2','bytes=0-2,5-6'])
def test_bad_ranges(value):
    from museforge.storage import range_bounds
    with pytest.raises(ValueError): range_bounds(value,100)


def test_safe_open_rejects_changed_symlink(tmp_path):
    from museforge.storage import open_artifact
    file=tmp_path/'audio';file.write_bytes(b'original')
    with open_artifact(tmp_path,'audio') as opened: assert opened.read()==b'original'
    file.unlink();file.symlink_to('/etc/passwd')
    for key in ('audio','../etc/passwd','/etc/passwd','missing'):
        with pytest.raises(ProviderError): open_artifact(tmp_path,key)
