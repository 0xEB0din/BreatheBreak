"""Notification dispatch — thin wrapper around rumps.notification.

Isolates the rest of the codebase from notification failures so a
single bad notification can't crash the app.
"""

import logging

log = logging.getLogger(__name__)


def notify(title: str, subtitle: str, message: str, sound: bool = True) -> None:
    """Send a macOS notification. Logs and swallows errors."""
    try:
        import rumps

        rumps.notification(title, subtitle, message, sound=sound)
    except Exception:
        log.warning("Failed to deliver notification", exc_info=True)
