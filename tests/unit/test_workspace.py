import pytest
from pydantic import ValidationError
from museforge.domain import GenerationDefaults, SettingsPatch
from museforge.workspace import DEFAULT_GENERATION_DEFAULTS, TEMPLATES


def test_generation_defaults_match_the_composer_vocabulary():
    assert GenerationDefaults().model_dump() == DEFAULT_GENERATION_DEFAULTS
    with pytest.raises(ValidationError):
        GenerationDefaults(instruments=[])
    with pytest.raises(ValidationError):
        GenerationDefaults(instruments=['Piano', 'Piano'])
    with pytest.raises(ValidationError):
        GenerationDefaults(genre='Unsupported')


def test_settings_patch_is_nonempty_and_strict():
    with pytest.raises(ValidationError):
        SettingsPatch()
    with pytest.raises(ValidationError):
        SettingsPatch(volume=1.1)
    with pytest.raises(ValidationError):
        SettingsPatch(repeat_mode='forever')
    assert SettingsPatch(volume=0.5).model_dump(exclude_unset=True) == {'volume': 0.5}


def test_templates_are_original_complete_mock_drafts():
    assert len(TEMPLATES) == 5
    assert len({item['id'] for item in TEMPLATES}) == len(TEMPLATES)
    assert all(item['revision'] == 1 and item['draft']['lyrics']['mode'] == 'mock' for item in TEMPLATES)
