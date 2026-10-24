from pathlib import Path

import pytest

from core import save_data


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    return tmp_path


def _set_system(monkeypatch, name):
    monkeypatch.setattr(save_data.platform, "system", lambda: name)


def test_linux_default_path(fake_home, monkeypatch):
    _set_system(monkeypatch, "Linux")
    expected = fake_home / ".local" / "share" / "RestenRinger2"
    assert save_data.user_data_dir() == expected
    assert expected.is_dir()


def test_linux_respects_xdg_data_home(fake_home, monkeypatch):
    _set_system(monkeypatch, "Linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(fake_home / "xdg"))
    assert save_data.user_data_dir() == fake_home / "xdg" / "RestenRinger2"


def test_macos_path(fake_home, monkeypatch):
    _set_system(monkeypatch, "Darwin")
    expected = fake_home / "Library" / "Application Support" / "RestenRinger2"
    assert save_data.user_data_dir() == expected


def test_windows_uses_appdata(fake_home, monkeypatch):
    _set_system(monkeypatch, "Windows")
    monkeypatch.setenv("APPDATA", str(fake_home / "Roaming"))
    assert save_data.user_data_dir() == fake_home / "Roaming" / "RestenRinger2"


def test_windows_falls_back_without_appdata(fake_home, monkeypatch):
    _set_system(monkeypatch, "Windows")
    expected = fake_home / "AppData" / "Roaming" / "RestenRinger2"
    assert save_data.user_data_dir() == expected


def test_save_and_load_roundtrip(fake_home, monkeypatch):
    _set_system(monkeypatch, "Linux")
    data = {"runs": 3, "best_floor": 2}
    path = save_data.save_json("runs.json", data)
    assert path.parent == save_data.user_data_dir()
    assert save_data.load_json("runs.json") == data
    assert not path.with_suffix(".json.tmp").exists()


def test_load_missing_returns_default(fake_home, monkeypatch):
    _set_system(monkeypatch, "Linux")
    assert save_data.load_json("nope.json", default={}) == {}


def test_load_corrupt_returns_default(fake_home, monkeypatch):
    _set_system(monkeypatch, "Linux")
    save_data.data_path("bad.json").write_text("{not json", encoding="utf-8")
    assert save_data.load_json("bad.json", default={"ok": True}) == {"ok": True}
