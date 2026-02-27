"""Entry point for `python -m breathebreak`."""

import logging
import sys

from breathebreak.app import BreakReminderApp


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    try:
        BreakReminderApp().run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
