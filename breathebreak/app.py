"""BreatheBreak — macOS menu bar application.

Ties together config, stats, and notifications into a rumps menu bar app.
The menu provides a single toggle for reminders, an interval setter, and
a stats viewer. Break notifications rotate through practical tips to keep
them useful rather than repetitive.
"""

import logging

import rumps

from breathebreak.config import Config
from breathebreak.notifier import notify
from breathebreak.stats import StatsStore

log = logging.getLogger(__name__)

BREAK_TIPS = [
    "Look at something 20 feet away for 20 seconds.",
    "Stand up and stretch your arms overhead.",
    "Roll your shoulders — forward, then backward.",
    "Close your eyes and take 5 deep breaths.",
    "Walk to the window. Natural light resets your focus.",
    "Grab a glass of water. Hydration matters.",
    "Do a quick posture check — shoulders back, feet flat.",
    "Stretch your wrists and fingers. They do a lot of work.",
    "Focus on something green. It reduces eye strain.",
    "Take a short walk. Even 2 minutes helps.",
]


class BreatheBreakApp(rumps.App):
    """Menu bar break reminder with session tracking."""

    def __init__(self, config: Config | None = None):
        self.cfg = config or Config.load()
        super().__init__("BreatheBreak", quit_button=None)

        self.stats = StatsStore.load() if self.cfg.track_stats else StatsStore()
        self._timer = rumps.Timer(self._on_tick, self.cfg.interval_minutes * 60)
        self._active = False
        self._tip_index = 0

        self.menu = [
            "Reminders",
            None,
            "Set Interval",
            "Stats",
            None,
            "Quit",
        ]

    # -- menu callbacks --

    @rumps.clicked("Reminders")
    def toggle_reminders(self, sender):
        if self._active:
            self._timer.stop()
            self._active = False
            sender.state = False
            self.stats.end_focus_session()
            log.info("Reminders paused")
        else:
            self._timer.start()
            self._active = True
            sender.state = True
            self.stats.record_session_start()
            self.stats.start_focus_session()
            notify(
                "BreatheBreak",
                "Reminders active",
                f"Break every {self.cfg.interval_minutes} min.",
                sound=self.cfg.sound_enabled,
            )
            log.info("Reminders started — interval %d min", self.cfg.interval_minutes)

    @rumps.clicked("Set Interval")
    def set_interval(self, _):
        window = rumps.Window(
            "Interval in minutes (1\u2013480):",
            "BreatheBreak",
            default_text=str(self.cfg.interval_minutes),
            dimensions=(200, 24),
        )
        resp = window.run()
        if not resp.clicked:
            return

        try:
            minutes = int(resp.text.strip())
        except ValueError:
            notify("BreatheBreak", "", "Please enter a valid number.", sound=False)
            return

        if not 1 <= minutes <= 480:
            notify("BreatheBreak", "", "Choose between 1 and 480 minutes.", sound=False)
            return

        was_active = self._active
        if self._active:
            self._timer.stop()

        self.cfg.interval_minutes = minutes
        self._timer.interval = minutes * 60
        self.cfg.save()

        if was_active:
            self._timer.start()

        notify(
            "BreatheBreak",
            "Interval updated",
            f"Reminders set to every {minutes} min.",
            sound=self.cfg.sound_enabled,
        )
        log.info("Interval changed to %d min", minutes)

    @rumps.clicked("Stats")
    def show_stats(self, _):
        rumps.alert(title="Break Statistics", message=self.stats.summary())

    @rumps.clicked("Quit")
    def quit_app(self, _):
        if self._active:
            self._timer.stop()
            self.stats.end_focus_session()
        rumps.quit_application()

    # -- timer --

    def _on_tick(self, _):
        tip = BREAK_TIPS[self._tip_index % len(BREAK_TIPS)]
        self._tip_index += 1
        self.stats.record_reminder()
        notify(
            "BreatheBreak",
            "Time for a break",
            tip,
            sound=self.cfg.sound_enabled,
        )


def main():
    """Launch BreatheBreak."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    app = BreatheBreakApp()
    app.run()
