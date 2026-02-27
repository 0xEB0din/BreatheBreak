import json
import logging
import os
from datetime import date, datetime

logger = logging.getLogger(__name__)


class SessionTracker:
    """Tracks work sessions and break events in a local JSON log.

    Each day gets its own entry keyed by ISO date. Data is stored alongside
    the config at ~/.config/breathebreak/sessions.json.
    """

    def __init__(self, data_dir):
        self._path = os.path.join(data_dir, "sessions.json")
        self._sessions = self._load()
        self._session_start = None

    def start_session(self):
        self._session_start = datetime.now()
        logger.debug("Session started at %s", self._session_start.isoformat())

    def end_session(self):
        if self._session_start is None:
            return
        elapsed = int((datetime.now() - self._session_start).total_seconds())
        today = self._today_key()
        entry = self._sessions.setdefault(today, {"breaks": 0, "focus_seconds": 0})
        entry["focus_seconds"] += elapsed
        self._session_start = None
        self._save()
        logger.debug("Session ended, +%ds focus time", elapsed)

    def record_break(self):
        today = self._today_key()
        entry = self._sessions.setdefault(today, {"breaks": 0, "focus_seconds": 0})
        entry["breaks"] += 1
        self._save()

    def today_stats(self):
        entry = self._sessions.get(self._today_key(), {})
        return {
            "breaks_taken": entry.get("breaks", 0),
            "focus_minutes": entry.get("focus_seconds", 0) // 60,
        }

    def _today_key(self):
        return date.today().isoformat()

    def _load(self):
        if not os.path.isfile(self._path):
            return {}
        try:
            with open(self._path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._sessions, f, indent=2)
