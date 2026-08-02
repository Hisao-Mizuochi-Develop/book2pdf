# tests/test_config.py

import os
import json
from core.config import load_config, save_config, CONFIG_FILE, _deep_merge, DEFAULT_CONFIG


def test_deep_merge():
    base = {"a": {"b": 1}, "c": 2}
    override = {"a": {"b": 99}, "d": 3}
    merged = _deep_merge(base, override)
    assert merged["a"]["b"] == 99
    assert merged["d"] == 3
    assert base["a"]["b"] == 1  # base は汚染されない


def test_load_config_default(tmp_path, monkeypatch):
    monkeypatch.setattr("core.config.CONFIG_FILE", tmp_path / "config.json")
    cfg = load_config()
    assert cfg["capture"]["active_profile"] == "kindle"


def test_save_config(tmp_path, monkeypatch):
    monkeypatch.setattr("core.config.CONFIG_FILE", tmp_path / "config.json")
    cfg = load_config()
    cfg["capture"]["active_profile"] = "google_play"
    save_config(cfg)
    with open(tmp_path / "config.json") as f:
        data = json.load(f)
    assert data["capture"]["active_profile"] == "google_play"
