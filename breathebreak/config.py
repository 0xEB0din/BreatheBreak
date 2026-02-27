import json
import logging
import os
import stat

logger = logging.getLogger(__name__)

_DEFAULTS = {
    "interval_minutes": 20,
    "sound": True,
}

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "breathebreak")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


class Config:
    """Persistent configuration backed by a JSON file.

    Config lives at ~/.config/breathebreak/config.json with 0600 permissions
    to prevent other local users from reading or modifying settings.
    """

    def __init__(self, path=None):
        self._path = path or CONFIG_FILE
        self._data = dict(_DEFAULTS)
        self._load()

    @property
    def data_dir(self):
        return os.path.dirname(self._path)

    @property
    def interval(self):
        return self._data.get("interval_minutes", _DEFAULTS["interval_minutes"])

    @interval.setter
    def interval(self, minutes):
        self._data["interval_minutes"] = minutes

    @property
    def sound(self):
        return self._data.get("sound", _DEFAULTS["sound"])

    def save(self):
        self._ensure_dir()
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)
        self._lock_permissions()
        logger.debug("Config saved to %s", self._path)

    def _load(self):
        if not os.path.isfile(self._path):
            return
        try:
            with open(self._path) as f:
                stored = json.load(f)
            self._data.update(stored)
            logger.debug("Config loaded from %s", self._path)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not load config (%s), using defaults", exc)

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)

    def _lock_permissions(self):
        """Restrict config file to owner-only read/write (0600)."""
        try:
            os.chmod(self._path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass  # non-critical on filesystems that ignore POSIX permissions
