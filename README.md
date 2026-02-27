# BreatheBreak

A macOS menu bar utility that reminds you to take regular screen breaks. Configurable, lightweight, and privacy-respecting — no telemetry, no network calls, all data stays on your machine.

[![CI](https://github.com/0xEB0din/BreatheBreak/actions/workflows/ci.yml/badge.svg)](https://github.com/0xEB0din/BreatheBreak/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

---

## Why This Exists

Long debugging sessions and code reviews have a way of making hours disappear. I kept ending the day with strained eyes and a stiff neck because I'd forget to step away from the screen. Existing break reminder tools were either bloated Electron apps burning 200MB of RAM or SaaS products that wanted calendar access and telemetry.

I wanted something minimal: a native menu bar app that does one thing well — nudge me to step away at a regular interval. No accounts, no cloud sync, no heavy runtime. Just a timer and a notification.

The [20-20-20 rule](https://www.aao.org/eye-health/tips-prevention/computer-usage) is the default: every 20 minutes, look at something 20 feet away for 20 seconds. The interval is configurable if you prefer something different.

## Architecture

```
breathebreak/
├── __init__.py          # Package metadata and version
├── __main__.py          # python -m breathebreak entry point
├── app.py               # Menu bar application (rumps.App subclass)
├── config.py            # YAML config — loading, validation, persistence
├── notifier.py          # Notification dispatch with error isolation
└── stats.py             # Local-only session statistics and focus tracking

tests/
├── conftest.py          # Shared test fixtures
├── test_config.py       # Config validation, loading, persistence
└── test_stats.py        # Statistics, focus tracking, and storage
```

Each module has a single responsibility:

| Module | Responsibility | External deps |
|--------|----------------|---------------|
| `config.py` | Load, validate, and persist user preferences | `pyyaml` |
| `stats.py` | Track daily break compliance and focus time | stdlib only |
| `notifier.py` | Fire macOS notifications, isolate failures | `rumps` |
| `app.py` | Menu bar UI, timer lifecycle, user interaction | `rumps` |

Config and stats are decoupled from the UI layer — they're testable without a display server or macOS environment.

### Design Decisions

- **rumps over Electron** — rumps wraps PyObjC for native macOS integration. The app uses ~15MB of memory vs. hundreds for an Electron equivalent. For a menu bar utility, native is the right call.
- **YAML config over CLI flags** — a config file persists across sessions and is easier to version-control. YAML was chosen over JSON for readability (comments, no trailing comma issues).
- **No singleton/global state** — Config and StatsStore are injected into the app at init time. Easier to test, easier to reason about.
- **Timer via rumps.Timer** — hooks into the Cocoa run loop natively. No threading, no `schedule` library, no polling.
- **Local-only analytics** — break compliance stats are useful for self-accountability, but they should never leave the machine. There's no telemetry, no network calls, and stats are stored as readable JSON so you can inspect or delete them anytime.
- **Atomic file writes** — config and stats are written to a `.tmp` file first, then renamed into place. This prevents data corruption if the process is killed mid-write.
- **Fail-open on config errors** — if the config file is missing, corrupt, or has out-of-range values, the app falls back to safe defaults instead of crashing. A break reminder that can't start isn't useful.

## Features

- **Menu bar native** — lightweight macOS-native app, no Electron
- **Rotating break tips** — cycles through practical activities: stretches, eye rest, hydration, posture checks
- **Configurable interval** — adjust from the menu bar or via config file (1–480 min)
- **Session statistics** — tracks reminders sent, breaks taken, and focus time per day
- **20-20-20 rule default** — evidence-based interval out of the box
- **YAML configuration** — human-readable, version-controllable config at `~/.config/breathebreak/config.yaml`
- **Privacy-first** — fully offline, zero telemetry, all data local

## Installation

Requires **macOS** and **Python 3.10+**.

```bash
git clone https://github.com/0xEB0din/BreatheBreak.git
cd BreatheBreak

# Install
pip install -e .

# Or with dev dependencies (for testing)
pip install -e ".[dev]"
```

## Usage

```bash
# Launch from CLI
breathebreak

# Or run as a module
python -m breathebreak
```

The app appears in your menu bar. Click it to:

- **Reminders** — toggle break reminders on/off (checkmark when active)
- **Set Interval** — change the reminder frequency (1–480 min)
- **Stats** — view your break compliance and focus time for the past 7 days
- **Quit** — stop tracking and exit

Settings persist at `~/.config/breathebreak/config.yaml`.

## Configuration

Optional. The app works out of the box with sensible defaults. To customize:

```bash
mkdir -p ~/.config/breathebreak
cp config.example.yaml ~/.config/breathebreak/config.yaml
```

```yaml
# How often to remind (minutes)
interval_minutes: 20

# Recommended break duration (seconds)
break_duration_seconds: 20

# Play notification sound
sound_enabled: true

# Track break statistics locally
track_stats: true
```

All values are validated on load. Out-of-range or malformed values fall back to defaults — the app won't crash on a bad config.

## Development

```bash
make dev     # install with dev deps
make test    # pytest
make lint    # ruff check + format check
make format  # auto-format
```

Tests cover config validation, bounds checking, file permission enforcement, persistence round-trips, focus time tracking, and graceful handling of corrupt data. GUI-dependent code (rumps interactions) is kept thin and tested manually.

## Security Considerations

Even for a local utility, security hygiene matters. Small projects are where habits form — and habits carry over to production systems.

**Data handling:**
- Config and stats files are written with `0600` permissions (owner read/write only)
- Atomic writes (`write-to-tmp` + `rename`) prevent partial/corrupt state on disk
- All data stored as human-readable YAML/JSON — no binary formats, no pickle, no `eval`
- Notification title field is length-capped to prevent memory abuse from malformed config

**Network posture:**
- Zero outbound network calls — the app is fully offline
- No auto-update mechanism — updates should be explicit and auditable
- No telemetry, analytics, or crash reporting

**Input validation:**
- Interval values are bounds-checked (1–480 minutes) before use
- Malformed config files fall back to safe defaults rather than raising
- User input from dialogs is validated and rejected with feedback on bad input
- YAML is loaded with `safe_load` (no arbitrary object deserialization)

**Minimal attack surface:**
- Single runtime dependency (`rumps`) to keep the supply chain surface small
- Runs entirely in user space — no root, no admin, no entitlements beyond notifications

**What's not covered (yet):**
- Stats are stored as plaintext JSON — not encrypted at rest
- No HMAC or signature on config file. A local attacker with file access could modify settings silently. Low risk for a break timer, but worth noting.
- No code signing or notarization for distribution
- No sandboxing beyond what macOS provides by default
- `sessions.json` grows unbounded. Not a security issue per se, but a resource concern over months of use.
- `rumps>=0.4.0` allows any compatible version. A lockfile with hash pinning would improve supply chain integrity.

## Limitations & Tradeoffs

| Limitation | Reasoning |
|------------|-----------|
| macOS only | `rumps` wraps PyObjC — it's inherently macOS-specific. Cross-platform would require abstracting the entire UI and notification layer. |
| No idle detection | The timer runs even when you're away. Adding idle detection requires IOKit bindings and adds platform-specific complexity. |
| No Focus/DND awareness | macOS doesn't expose Focus mode state to third-party apps through public APIs without entitlements. |
| No break enforcement | Notifications are advisory. I deliberately chose not to lock the screen or block input — that's hostile UX for a personal tool. |
| No GUI preferences pane | Settings are changed via menu bar dialogs or by editing the YAML config directly. Keeps the codebase small but is less discoverable. |
| Timer drift | `rumps.Timer` isn't a precision clock. Reminders may drift by seconds over long sessions. Acceptable for this use case. |
| Plaintext stats | Stats are local-only and non-sensitive (just counters). Encryption is on the roadmap but isn't a priority for this threat model. |

## Roadmap

Planned improvements, roughly in priority order:

- [ ] **Idle detection** — pause the timer when the user is AFK (via IOKit / `CGEventSource`)
- [ ] **Quiet hours** — suppress reminders during configurable time windows or when Do Not Disturb is active
- [ ] **Break acknowledgment** — actionable notifications to confirm you actually took a break
- [ ] **Pomodoro mode** — configurable work/break cycles (25m work, 5m break, 15m long break every 4 cycles)
- [ ] **Custom break messages** — let users define their own break activity pool via config
- [ ] **Log rotation** — auto-prune session data older than N days to prevent unbounded growth
- [ ] **Encrypted stats storage** — AES-256 for local data at rest
- [ ] **py2app packaging** — standalone `.app` bundle, no Python install required
- [ ] **Code signing & notarization** — for Gatekeeper-friendly distribution
- [ ] **Config file signing** — HMAC-based integrity check to detect local tampering
- [ ] **Launch at login** — register as a macOS login item so it starts automatically
- [ ] **Homebrew formula** — `brew install breathebreak`
- [ ] **Weekly stats summary** — aggregate focus time and break patterns over 7 days
- [ ] **Cross-platform notification backends** — Linux (`libnotify`) and Windows (toast notifications)
- [ ] **Local REST API** — HTTP endpoint for integration with other developer tools

## License

MIT — see [LICENSE](LICENSE) for details.
