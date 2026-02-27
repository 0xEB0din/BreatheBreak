import logging

import rumps

from breathebreak.config import Config
from breathebreak.tracker import SessionTracker

logger = logging.getLogger(__name__)

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


class BreakReminderApp(rumps.App):
    """macOS menu bar app for regular screen break reminders.

    Tracks work sessions and rotates through practical break activities
    to combat screen fatigue during long coding or design sessions.
    """

    def __init__(self):
        super().__init__("BreatheBreak", quit_button=None)
        self.config = Config()
        self.tracker = SessionTracker(self.config.data_dir)
        self._tip_index = 0
        self.timer = rumps.Timer(self._on_timer, self.config.interval * 60)

        self.menu = [
            "Start",
            "Stop",
            None,
            "Set Interval",
            "Today's Stats",
            None,
            "Quit",
        ]
        logger.info("BreatheBreak ready (interval=%dm)", self.config.interval)

    @rumps.clicked("Start")
    def on_start(self, sender):
        if self.timer.is_alive():
            return
        self.timer.start()
        sender.state = True
        self.tracker.start_session()
        rumps.notification(
            "BreatheBreak",
            "Reminders active",
            f"Break every {self.config.interval} minutes.",
        )
        logger.info("Started reminders")

    @rumps.clicked("Stop")
    def on_stop(self, _):
        if not self.timer.is_alive():
            return
        self.timer.stop()
        self.menu["Start"].state = False
        self.tracker.end_session()
        logger.info("Stopped reminders")

    @rumps.clicked("Set Interval")
    def on_set_interval(self, _):
        window = rumps.Window(
            "Reminder interval in minutes:",
            "BreatheBreak",
            default_text=str(self.config.interval),
            dimensions=(200, 24),
        )
        resp = window.run()
        if not resp.clicked:
            return

        try:
            minutes = int(resp.text.strip())
        except ValueError:
            rumps.notification("BreatheBreak", "Invalid input", "Enter a whole number.")
            return

        if not 1 <= minutes <= 480:
            rumps.notification(
                "BreatheBreak", "Out of range", "Choose between 1 and 480 minutes."
            )
            return

        was_running = self.timer.is_alive()
        if was_running:
            self.timer.stop()

        self.config.interval = minutes
        self.config.save()
        self.timer.interval = minutes * 60

        if was_running:
            self.timer.start()
        logger.info("Interval set to %dm", minutes)

    @rumps.clicked("Today's Stats")
    def on_stats(self, _):
        stats = self.tracker.today_stats()
        rumps.notification(
            "BreatheBreak — Today",
            f"Breaks taken: {stats['breaks_taken']}",
            f"Total focus time: {stats['focus_minutes']}m",
        )

    @rumps.clicked("Quit")
    def on_quit(self, _):
        if self.timer.is_alive():
            self.tracker.end_session()
        rumps.quit_application()

    def _on_timer(self, _):
        tip = BREAK_TIPS[self._tip_index % len(BREAK_TIPS)]
        self._tip_index += 1
        self.tracker.record_break()
        rumps.notification("BreatheBreak", "Time for a break!", tip)
