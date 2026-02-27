# BreatheBreak

[![CI](https://github.com/0xEB0din/BreatheBreak/actions/workflows/ci.yml/badge.svg)](https://github.com/0xEB0din/BreatheBreak/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

A lightweight macOS menu bar utility that reminds you to take regular screen breaks. Built to do one thing well — keep you from burning out during long coding or design sessions.

## Why This Exists

I kept losing track of time during long coding sessions. 3-4 hours would pass without me moving, and my eyes and back were paying for it. The tools I found were either bloated Electron apps eating 200MB+ of RAM, or SaaS products that wanted access to my calendar and usage patterns.

BreatheBreak sits in your menu bar, tracks nothing beyond your local machine, sends no data anywhere, and reminds you to step away. That's it.

## Features

- **Menu bar native** — lives in the macOS status bar, completely out of your way
- **Rotating break tips** — cycles through practical activities: stretches, eye rest, hydration, posture checks
- **Configurable interval** — default 20 min (the [20-20-20 rule](https://www.aao.org/eye-health/tips-prevention/computer-usage)), adjustable 1–480 min
- **Session tracking** — logs daily focus time and breaks taken, stored locally
- **Persistent config** — settings survive app restarts (`~/.config/breathebreak/`)
- **Zero network calls** — no telemetry, no analytics, no phoning home

## Architecture

```
breathebreak/
├── __init__.py        # Package metadata
├── __main__.py        # Entry point, logging setup
├── app.py             # Menu bar UI and event handling (rumps)
├── config.py          # JSON-backed persistent configuration
└── tracker.py         # Session and break tracking
```

The app follows a layered design with clear module boundaries:

| Layer | Responsibility | Module |
|-------|---------------|--------|
| **UI** | Menu bar, dialogs, notifications | `app.py` |
| **Config** | Load/save settings, file permissions | `config.py` |
| **Tracking** | Session timing, daily break counts | `tracker.py` |

Separation is deliberate but minimal — this is a single-purpose utility, not a framework. Each module owns its concerns without unnecessary abstraction layers.

### Design Decisions

- **`rumps` over PyObjC** — rumps wraps the Cocoa APIs I need (NSStatusBar, NSUserNotification) without pulling in the full PyObjC bridge. One dependency instead of six.
- **JSON over SQLite** — the data model is trivial (a dict of daily counters). A JSON file is human-readable, easy to back up, and good enough for single-process desktop use.
- **No singleton/global state** — Config and SessionTracker are injected into the app at init time. Easier to test, easier to reason about.
- **Timer via rumps.Timer** — hooks into the Cocoa run loop natively. No threading, no `schedule` library, no polling.

## Installation

**Requirements:** Python 3.9+ and macOS (uses native Cocoa APIs via [rumps](https://github.com/jaredks/rumps))

```bash
git clone https://github.com/0xEB0din/BreatheBreak.git
cd BreatheBreak
pip install .
```

## Usage

```bash
# Via installed command
breathebreak

# Or as a module
python -m breathebreak
```

Once running, click the **BreatheBreak** menu bar item:

| Action | What it does |
|--------|-------------|
| **Start** | Begin break reminders, start tracking focus time |
| **Stop** | Pause reminders, log accumulated focus time |
| **Set Interval** | Change reminder frequency (1–480 min) |
| **Today's Stats** | Show breaks taken and total focus time |
| **Quit** | Stop tracking and exit |

Settings persist at `~/.config/breathebreak/config.json`.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
make test

# Lint & format check
make lint

# Auto-format
make format
```

## Security Considerations

Even for a local utility, security hygiene matters:

| Concern | Approach |
|---------|----------|
| **Config file permissions** | `config.json` is written with `0600` (owner read/write only) to prevent other local users from reading or modifying settings |
| **No network access** | Zero outbound connections — no telemetry, no update checks, no analytics |
| **Input validation** | Interval values are validated for type (`int`) and range (1–480) before being applied to the timer |
| **Local-only data** | Session logs stay on disk at `~/.config/breathebreak/`. Nothing leaves the machine |
| **Minimal dependencies** | Single runtime dependency (`rumps`) to keep the supply chain surface small |
| **No elevated privileges** | Runs entirely in user space — no root, no admin, no entitlements beyond notifications |

### Not Yet Addressed

These are acknowledged gaps, documented here for transparency:

- **Config file integrity** — no HMAC or signature on `config.json`. A local attacker with file access could modify settings silently. Low risk for a break timer, but worth noting.
- **Log rotation** — `sessions.json` grows unbounded. Not a security issue per se, but a resource concern over months of use.
- **Code signing** — the app isn't signed or notarized for macOS Gatekeeper. Users must allow it manually in System Settings.
- **Dependency pinning** — `rumps>=0.4.0` allows any compatible version. A lockfile with hash pinning would improve supply chain integrity.
- **No sandboxing** — the app runs with full user-space permissions. An App Sandbox profile would restrict filesystem and network access to only what's needed.

## Limitations & Tradeoffs

| Decision | Tradeoff |
|----------|----------|
| **macOS only** | `rumps` depends on PyObjC / Cocoa. No Linux or Windows support. Chose platform-native UX over cross-platform reach. |
| **No GUI preferences pane** | Settings are changed via menu bar dialogs or by editing the JSON config directly. Keeps the codebase small but is less discoverable for non-technical users. |
| **JSON for storage** | Human-readable and simple, but no concurrent write safety. Fine for a single-process desktop app; wouldn't scale to multi-instance. |
| **No break enforcement** | The app notifies but doesn't force you to stop. By design — aggressively interrupting flow state would make it annoying enough to disable. |
| **Timer drift** | `rumps.Timer` isn't a precision clock. Reminders may drift by seconds over long sessions. Acceptable for this use case. |
| **No custom notification sounds** | Uses the default macOS notification sound. Custom audio would require additional Cocoa bindings. |

## Roadmap

Planned improvements, roughly in priority order:

- [ ] **Pomodoro mode** — configurable work/break cycles (25m work → 5m break → repeat, 15m long break every 4 cycles)
- [ ] **Quiet hours** — suppress reminders during configurable time windows or when Do Not Disturb is active
- [ ] **Break compliance tracking** — detect whether the user actually stepped away (idle detection via `IOKit`)
- [ ] **Custom break messages** — let users define their own break activity pool via config
- [ ] **Log rotation** — auto-prune session data older than N days to prevent unbounded growth
- [ ] **Sound alerts** — optional audio cue alongside or instead of the notification banner
- [ ] **py2app packaging** — distribute as a native `.app` bundle with code signing and notarization
- [ ] **Weekly stats summary** — aggregate focus time and break patterns over 7 days
- [ ] **Cross-platform support** — investigate `pystray` + `plyer` for Linux/Windows portability
- [ ] **Config file signing** — HMAC-based integrity check to detect local tampering
- [ ] **Launch at login** — register as a macOS login item so it starts automatically

## License

MIT — see [LICENSE](LICENSE) for details.
