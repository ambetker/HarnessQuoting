import pytest

from app import config, settings


@pytest.fixture(autouse=True)
def temp_settings_path(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SETTINGS_PATH", tmp_path / "settings.json")
    yield


def test_load_settings_defaults_when_no_file():
    loaded = settings.load_settings()
    assert loaded.initials == ""


def test_save_and_load_roundtrip():
    settings.save_settings(settings.AppSettings(initials="AB"))
    loaded = settings.load_settings()
    assert loaded.initials == "AB"


def test_load_tolerates_corrupt_file():
    config.SETTINGS_PATH.write_text("not valid json{{{")
    loaded = settings.load_settings()
    assert loaded.initials == ""
