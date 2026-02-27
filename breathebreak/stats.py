"""Local-only session statistics.

Tracks daily break compliance in a JSON file at
~/.config/breathebreak/stats.json. No data ever leaves the machine.
File permissions are restricted to owner-only (0600).
"""

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date

from breathebreak.config import CONFIG_DIR, STATS_FILE


@dataclass
class DailyStats:
    """Aggregated stats for a single calendar day."""

    date: str
    reminders_sent: int = 0
    breaks_acknowledged: int = 0
    total_break_seconds: int = 0
    sessions_started: int = 0


@dataclass
class StatsStore:
    """Manages per-day break statistics with JSON persistence."""

    days: dict = field(default_factory=dict)

    # -- recording --

    def record_reminder(self) -> None:
        self._today().reminders_sent += 1
        self._persist()

    def record_break(self, duration_seconds: int = 0) -> None:
        today = self._today()
        today.breaks_acknowledged += 1
        today.total_break_seconds += duration_seconds
        self._persist()

    def record_session_start(self) -> None:
        self._today().sessions_started += 1
        self._persist()

    # -- reporting --

    def summary(self, last_n_days: int = 7) -> str:
        """Human-readable summary of recent break activity."""
        keys = sorted(self.days.keys(), reverse=True)[:last_n_days]
        if not keys:
            return "No break data recorded yet."

        reminders = sum(self.days[k].reminders_sent for k in keys)
        breaks = sum(self.days[k].breaks_acknowledged for k in keys)
        rate = (breaks / reminders * 100) if reminders else 0

        return (
            f"Last {len(keys)} day(s):\n"
            f"  Reminders sent: {reminders}\n"
            f"  Breaks taken:   {breaks}\n"
            f"  Compliance:     {rate:.0f}%"
        )

    # -- persistence --

    def _persist(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {k: asdict(v) for k, v in self.days.items()}
        tmp = STATS_FILE.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.chmod(tmp, 0o600)
        tmp.replace(STATS_FILE)

    @classmethod
    def load(cls) -> "StatsStore":
        """Load stats from disk. Returns empty store on any error."""
        if not STATS_FILE.exists():
            return cls()
        try:
            with open(STATS_FILE) as f:
                raw = json.load(f)
            days = {}
            for key, val in raw.items():
                days[key] = DailyStats(**val)
            return cls(days=days)
        except (json.JSONDecodeError, OSError, TypeError, KeyError):
            return cls()

    # -- internals --

    def _today(self) -> DailyStats:
        key = date.today().isoformat()
        if key not in self.days:
            self.days[key] = DailyStats(date=key)
        return self.days[key]
