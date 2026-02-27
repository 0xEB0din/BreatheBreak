"""Entry point for `python -m breathebreak`."""

import sys

from breathebreak.app import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
