"""Tests for configuration management."""

import yaml

from breathebreak.config import (
    DEFAULT_INTERVAL,
    MAX_INTERVAL,
    MIN_INTERVAL,
    Config,
)


class TestConfigDefaults:
    def test_default_interval(self):
        cfg = Config()
        assert cfg.interval_minutes == DEFAULT_INTERVAL

    def test_default_sound_enabled(self):
        assert Config().sound_enabled is True

    def test_default_track_stats(self):
        assert Config().track_stats is True


class TestIntervalValidation:
    def test_clamps_to_minimum(self):
        assert Config._clamp_interval(0) == MIN_INTERVAL
        assert Config._clamp_interval(-10) == MIN_INTERVAL

    def test_clamps_to_maximum(self):
        assert Config._clamp_interval(999) == MAX_INTERVAL

    def test_accepts_valid_value(self):
        assert Config._clamp_interval(45) == 45

    def test_rejects_non_numeric(self):
        assert Config._clamp_interval("abc") == DEFAULT_INTERVAL
        assert Config._clamp_interval(None) == DEFAULT_INTERVAL

    def test_boundary_values(self):
        assert Config._clamp_interval(MIN_INTERVAL) == MIN_INTERVAL
        assert Config._clamp_interval(MAX_INTERVAL) == MAX_INTERVAL


class TestConfigLoad:
    def test_missing_file_returns_defaults(self, tmp_path, monkeypatch):
        monkeypatch.setattr("breathebreak.config.CONFIG_FILE", tmp_path / "nonexistent.yaml")
        cfg = Config.load()
        assert cfg.interval_minutes == DEFAULT_INTERVAL

    def test_corrupt_yaml_returns_defaults(self, tmp_path, monkeypatch):
        bad = tmp_path / "bad.yaml"
        bad.write_text(": [invalid\n\x00")
        monkeypatch.setattr("breathebreak.config.CONFIG_FILE", bad)
        cfg = Config.load()
        assert cfg.interval_minutes == DEFAULT_INTERVAL

    def test_empty_file_returns_defaults(self, tmp_path, monkeypatch):
        empty = tmp_path / "empty.yaml"
        empty.write_text("")
        monkeypatch.setattr("breathebreak.config.CONFIG_FILE", empty)
        cfg = Config.load()
        assert cfg.interval_minutes == DEFAULT_INTERVAL

    def test_loads_custom_values(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({"interval_minutes": 30, "sound_enabled": False}))
        monkeypatch.setattr("breathebreak.config.CONFIG_FILE", cfg_file)
        cfg = Config.load()
        assert cfg.interval_minutes == 30
        assert cfg.sound_enabled is False

    def test_out_of_range_values_are_clamped(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({"interval_minutes": 9999}))
        monkeypatch.setattr("breathebreak.config.CONFIG_FILE", cfg_file)
        cfg = Config.load()
        assert cfg.interval_minutes == MAX_INTERVAL

    def test_title_is_length_capped(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({"notification_title": "A" * 200}))
        monkeypatch.setattr("breathebreak.config.CONFIG_FILE", cfg_file)
        cfg = Config.load()
        assert len(cfg.notification_title) == 64


class TestConfigSave:
    def test_creates_file_with_restricted_permissions(self, tmp_path, monkeypatch):
        config_dir = tmp_path / "cfg"
        config_file = config_dir / "config.yaml"
        monkeypatch.setattr("breathebreak.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("breathebreak.config.CONFIG_FILE", config_file)

        Config(interval_minutes=30).save()

        assert config_file.exists()
        mode = oct(config_file.stat().st_mode & 0o777)
        assert mode == "0o600"

    def test_roundtrip(self, tmp_path, monkeypatch):
        config_dir = tmp_path / "cfg"
        config_file = config_dir / "config.yaml"
        monkeypatch.setattr("breathebreak.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("breathebreak.config.CONFIG_FILE", config_file)

        original = Config(interval_minutes=42, sound_enabled=False)
        original.save()

        loaded = Config.load()
        assert loaded.interval_minutes == 42
        assert loaded.sound_enabled is False
