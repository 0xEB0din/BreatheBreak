import json
import os

from breathebreak.config import Config


class TestConfig:
    def test_defaults(self, tmp_path):
        cfg = Config(path=str(tmp_path / "config.json"))
        assert cfg.interval == 20
        assert cfg.sound is True

    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "config.json")
        cfg = Config(path=path)
        cfg.interval = 45
        cfg.save()

        cfg2 = Config(path=path)
        assert cfg2.interval == 45

    def test_file_permissions(self, tmp_path):
        path = str(tmp_path / "config.json")
        cfg = Config(path=path)
        cfg.save()
        mode = os.stat(path).st_mode & 0o777
        assert mode == 0o600

    def test_corrupt_config_uses_defaults(self, tmp_path):
        path = str(tmp_path / "config.json")
        with open(path, "w") as f:
            f.write("{not valid json")
        cfg = Config(path=path)
        assert cfg.interval == 20

    def test_partial_config_merges_with_defaults(self, tmp_path):
        path = str(tmp_path / "config.json")
        with open(path, "w") as f:
            json.dump({"interval_minutes": 30}, f)
        cfg = Config(path=path)
        assert cfg.interval == 30
        assert cfg.sound is True  # default preserved

    def test_data_dir_points_to_config_parent(self, tmp_path):
        path = str(tmp_path / "sub" / "config.json")
        cfg = Config(path=path)
        assert cfg.data_dir == str(tmp_path / "sub")
