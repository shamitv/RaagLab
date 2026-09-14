from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from museforge.api import routes
from museforge.config import Settings
from museforge.domain import CapabilitiesResponse, Provenance, provider_capabilities


def configured_settings(provider):
    if provider == "mock":
        return Settings(_env_file=None, music_provider="mock", lyrics_provider="mock")
    return Settings(
        _env_file=None,
        music_provider="yue2",
        lyrics_provider="user",
        device="cuda",
        precision="bfloat16",
        model_id="m-a-p/YuE2-3B",
        model_revision="29b3558dd46954a0cd9021dc76d5c91864a0f1c7",
        decoder_revision="9a94e1d0ea9f8087e98f77fa88df4a4068104d2a",
    )


@pytest.mark.parametrize("provider", ["mock", "yue2"])
def test_capabilities_endpoint_returns_evidence_and_readiness(monkeypatch, provider):
    settings = configured_settings(provider)
    monkeypatch.setattr(routes, "readiness", lambda _connection, _settings: {
        "state": "offline", "last_observed_at": None,
    })
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
        engine=SimpleNamespace(connect=lambda: nullcontext(object())),
        settings=settings,
    )))

    response = CapabilitiesResponse.model_validate(routes.get_capabilities(request))

    assert response.provider_id == provider
    assert response.readiness.state == "offline"
    assert response.default_lyrics_mode == settings.lyrics_provider
    assert response.provider_route == settings.provider_route
    assert response.capability_matrix["lyrics_text_input"].state == "supported"
    assert {
        "lyrics_text_input", "lyrics_text_generation", "instrumental_music_generation",
        "technical_audio_output",
        "vocal_generation", "exact_lyrics_singing", "language_fidelity",
        "instrument_control", "mood_control", "genre_control", "tempo_control",
        "duration_control", "seed_reproducibility", "audio_conditioning",
        "audio_editing", "continuation",
    } == set(response.capability_matrix)
    if provider == "mock":
        assert response.is_demo
        assert response.capability_matrix["instrumental_music_generation"].state == "unsupported"
    else:
        assert not response.is_demo
        assert response.model_revision == settings.model_revision
        assert response.text_to_instrumental is None
        assert response.vocals is None
        assert response.exact_lyrics_vocals is None
        assert response.capability_matrix["instrumental_music_generation"].state == "unknown"


def test_old_version_provenance_defaults_to_empty_capability_matrix():
    snapshot = provider_capabilities(configured_settings("mock"))
    snapshot.pop("capability_matrix")
    snapshot.update(lyrics={
        "text": "Persisted mock lyrics",
        "source": "mock",
        "provider_revision": "1",
        "fixture_id": None,
        "fixture_revision": None,
    })
    assert Provenance.model_validate(snapshot).capability_matrix == {}
