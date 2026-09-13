from pathlib import Path
import pytest
from pydantic import ValidationError
from museforge.domain import Generation, ProviderError, Lyrics
from museforge.providers import DemoLyrics, MockMusic, STATIC
from museforge.storage import inspect, publish, resolve

TEXT = '  [अंतरा]\r\nहवा 🎵\n\n[பல்லவி]\nவானம்\t\n'

@pytest.mark.parametrize('mode', ['user', 'static', 'mock'])
def test_lyrics_source_and_exact_preservation(mode):
    request = {'lyrics': {'mode': mode, 'text': TEXT}, 'seed': 12}
    provider = DemoLyrics()
    first = provider.generate(request, lambda *_: None, lambda: None)
    assert first == provider.generate(request, lambda *_: None, lambda: None)
    assert first['source'] == mode
    assert first['text'] == (TEXT if mode == 'user' else STATIC if mode == 'static' else first['text'])
    assert first['text']

@pytest.mark.parametrize('duration', [5, 8, 30])
def test_audio_decodes_deterministically_and_publishes(tmp_path, duration):
    request = {'duration_seconds': duration, 'seed': 123}
    paths = [tmp_path / f'{i}.tmp' for i in range(2)]
    for path in paths: MockMusic(path).generate(request, lambda *_: None, lambda: None)
    assert paths[0].read_bytes() == paths[1].read_bytes()
    info = inspect(paths[0])
    assert info['duration_seconds'] == duration
    assert info['sample_rate'] == 44100 and info['channels'] == 2
    assert info['byte_size'] == duration * 44100 * 4 + 44
    result = publish(tmp_path, paths[0], 'test', 1, duration)
    assert resolve(tmp_path, result['storage_key']).exists()
    assert not paths[0].exists()

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
    with pytest.raises(ProviderError, match='cancelled'):
        MockMusic(tmp_path/'audio.tmp').generate({'duration_seconds': 8,'seed': 1}, lambda *_: None, cancel)


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
