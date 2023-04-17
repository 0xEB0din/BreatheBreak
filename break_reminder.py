import time
import rumps
import schedule
from pync import Notifier

class BreakReminderApp(rumps.App):
    def __init__(self):
        super(BreakReminderApp, self).__init__(
            "Break Reminder",
            icon="your_icon_path_here"
        )
        self.menu = [
            rumps.MenuItem("Start", callback=self.start_reminder),
            rumps.MenuItem("Stop", callback=self.stop_reminder),
            rumps.separator,
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        self.reminder_started = False

    def send_break_notification(self):
        Notifier.notify(
            'Time for a break!',
            title='Break Reminder',
            subtitle='Remember to take a break every 20 minutes.',
            sound='default',
            group='break_reminder'
        )

    def start_reminder(self, sender):
        if not self.reminder_started:
            sender.state = not sender.state
            self.reminder_started = True
            schedule.every(20).minutes.do(self.send_break_notification)

    def stop_reminder(self, sender):
        if self.reminder_started:
            schedule.clear()
            self.reminder_started = False
            self.menu["Start"].state = False

    def quit_app(self, sender):
        rumps.quit_application()

if __name__ == '__main__':
    BreakReminderApp().run()