"""Configuration management — load, validate, and persist user preferences.

Config lives at ~/.config/breathebreak/config.yaml and is created on first
interval change. All values are bounds-checked before use. File permissions
are restricted to owner-only (0600) to prevent other local users from
tampering with app behavior.
"""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

CONFIG_DIR = Path.home() / ".config" / "breathebreak"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
STATS_FILE = CONFIG_DIR / "stats.json"

# Boundaries
DEFAULT_INTERVAL = 20  # minutes — matches the 20-20-20 rule
DEFAULT_BREAK_DURATION = 20  # seconds
MIN_INTERVAL = 1
MAX_INTERVAL = 480


@dataclass
class Config:
    """Validated application configuration."""

    interval_minutes: int = DEFAULT_INTERVAL
    break_duration_seconds: int = DEFAULT_BREAK_DURATION
    sound_enabled: bool = True
    track_stats: bool = True
    notification_title: str = "BreatheBreak"

    @classmethod
    def load(cls) -> "Config":
        """Load config from YAML file, falling back to safe defaults."""
        if not CONFIG_FILE.exists():
            return cls()

        try:
            with open(CONFIG_FILE) as f:
                raw = yaml.safe_load(f) or {}
        except (yaml.YAMLError, OSError):
            # Corrupt or unreadable config — don't crash, just use defaults.
            return cls()

        return cls(
            interval_minutes=cls._clamp_interval(raw.get("interval_minutes", DEFAULT_INTERVAL)),
            break_duration_seconds=_clamp(
                raw.get("break_duration_seconds", DEFAULT_BREAK_DURATION), 5, 300
            ),
            sound_enabled=bool(raw.get("sound_enabled", True)),
            track_stats=bool(raw.get("track_stats", True)),
            notification_title=str(raw.get("notification_title", "BreatheBreak"))[:64],
        )

    def save(self) -> None:
        """Write current config to disk with restricted permissions.

        Uses atomic write (tmp + rename) to avoid corruption if the process
        is killed mid-write.
        """
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "interval_minutes": self.interval_minutes,
            "break_duration_seconds": self.break_duration_seconds,
            "sound_enabled": self.sound_enabled,
            "track_stats": self.track_stats,
            "notification_title": self.notification_title,
        }
        tmp = CONFIG_FILE.with_suffix(".tmp")
        with open(tmp, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        os.chmod(tmp, 0o600)
        tmp.replace(CONFIG_FILE)

    @staticmethod
    def _clamp_interval(value) -> int:
        """Validate and clamp an interval value to safe bounds."""
        try:
            minutes = int(value)
        except (ValueError, TypeError):
            return DEFAULT_INTERVAL
        return max(MIN_INTERVAL, min(MAX_INTERVAL, minutes))


def _clamp(value, lo: int, hi: int) -> int:
    """Clamp a numeric value to [lo, hi], falling back to lo on bad input."""
    try:
        return max(lo, min(hi, int(value)))
    except (ValueError, TypeError):
        return lo
