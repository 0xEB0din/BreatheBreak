import rumps


class BreakReminderApp(rumps.App):
    """Menu bar app that reminds you to take breaks."""

    def __init__(self):
        super().__init__("BreatheBreak")
        self.interval = 20  # minutes
        self.timer = rumps.Timer(self.send_reminder, self.interval * 60)

    @rumps.clicked("Start")
    def start_reminder(self, sender):
        if not self.timer.is_alive():
            self.timer.start()
            sender.state = True
            rumps.notification(
                "BreatheBreak",
                "Reminders started",
                f"You'll get a reminder every {self.interval} minutes.",
            )

    @rumps.clicked("Stop")
    def stop_reminder(self, sender):
        if self.timer.is_alive():
            self.timer.stop()
            self.menu["Start"].state = False

    @rumps.clicked("Set Interval")
    def set_interval(self, _):
        window = rumps.Window(
            "Enter reminder interval (minutes):",
            "BreatheBreak",
            default_text=str(self.interval),
            dimensions=(200, 24),
        )
        response = window.run()
        if response.clicked:
            try:
                minutes = int(response.text.strip())
                if minutes < 1:
                    return
                was_running = self.timer.is_alive()
                self.timer.stop()
                self.interval = minutes
                self.timer.interval = minutes * 60
                if was_running:
                    self.timer.start()
            except ValueError:
                pass

    def send_reminder(self, _):
        rumps.notification(
            "BreatheBreak",
            "Time for a break!",
            "Step away from the screen, stretch, rest your eyes.",
        )


if __name__ == "__main__":
    BreakReminderApp().run()
