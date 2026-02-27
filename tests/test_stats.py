"""Tests for session statistics tracking."""

from datetime import date, datetime, timedelta

from breathebreak.stats import DailyStats, StatsStore


class TestStatsRecording:
    def _noop_store(self):
        """Return a store with persistence disabled for fast unit tests."""
        store = StatsStore()
        store._persist = lambda: None
        return store

    def test_record_reminder(self):
        store = self._noop_store()
        store.record_reminder()
        today = date.today().isoformat()
        assert store.days[today].reminders_sent == 1

    def test_record_break(self):
        store = self._noop_store()
        store.record_break(duration_seconds=20)
        today = date.today().isoformat()
        assert store.days[today].breaks_acknowledged == 1
        assert store.days[today].total_break_seconds == 20

    def test_record_session_start(self):
        store = self._noop_store()
        store.record_session_start()
        today = date.today().isoformat()
        assert store.days[today].sessions_started == 1

    def test_multiple_reminders_accumulate(self):
        store = self._noop_store()
        for _ in range(5):
            store.record_reminder()
        today = date.today().isoformat()
        assert store.days[today].reminders_sent == 5


class TestFocusTracking:
    def _noop_store(self):
        store = StatsStore()
        store._persist = lambda: None
        return store

    def test_focus_session_tracks_time(self):
        store = self._noop_store()
        store.start_focus_session()
        # Backdate start to simulate 25 minutes of work
        store._focus_start = datetime.now() - timedelta(minutes=25)
        store.end_focus_session()
        today = date.today().isoformat()
        assert store.days[today].focus_seconds >= 24 * 60

    def test_end_without_start_is_noop(self):
        store = self._noop_store()
        store.end_focus_session()
        today = date.today().isoformat()
        assert today not in store.days

    def test_multiple_sessions_accumulate(self):
        store = self._noop_store()
        store.start_focus_session()
        store._focus_start = datetime.now() - timedelta(minutes=10)
        store.end_focus_session()
        store.start_focus_session()
        store._focus_start = datetime.now() - timedelta(minutes=15)
        store.end_focus_session()
        today = date.today().isoformat()
        assert store.days[today].focus_seconds >= 24 * 60


class TestStatsSummary:
    def test_empty_store(self):
        store = StatsStore()
        assert "No break data" in store.summary()

    def test_summary_includes_counts(self):
        today = date.today().isoformat()
        store = StatsStore(
            days={
                today: DailyStats(date=today, reminders_sent=10, breaks_acknowledged=8),
            }
        )
        summary = store.summary()
        assert "10" in summary
        assert "8" in summary
        assert "80%" in summary

    def test_zero_reminders_no_division_error(self):
        today = date.today().isoformat()
        store = StatsStore(days={today: DailyStats(date=today, reminders_sent=0)})
        summary = store.summary()
        assert "0%" in summary

    def test_summary_includes_focus_time(self):
        today = date.today().isoformat()
        store = StatsStore(
            days={today: DailyStats(date=today, focus_seconds=5400)}  # 1h 30m
        )
        summary = store.summary()
        assert "1h 30m" in summary


class TestStatsPersistence:
    def test_roundtrip(self, tmp_path, monkeypatch):
        stats_file = tmp_path / "stats.json"
        monkeypatch.setattr("breathebreak.stats.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("breathebreak.stats.STATS_FILE", stats_file)

        store = StatsStore()
        store.record_reminder()
        store.record_break(20)

        loaded = StatsStore.load()
        today = date.today().isoformat()
        assert loaded.days[today].reminders_sent == 1
        assert loaded.days[today].breaks_acknowledged == 1

    def test_corrupt_file_returns_empty(self, tmp_path, monkeypatch):
        stats_file = tmp_path / "stats.json"
        stats_file.write_text("not json {{{")
        monkeypatch.setattr("breathebreak.stats.STATS_FILE", stats_file)

        store = StatsStore.load()
        assert len(store.days) == 0

    def test_file_permissions(self, tmp_path, monkeypatch):
        stats_file = tmp_path / "stats.json"
        monkeypatch.setattr("breathebreak.stats.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("breathebreak.stats.STATS_FILE", stats_file)

        store = StatsStore()
        store.record_reminder()

        mode = oct(stats_file.stat().st_mode & 0o777)
        assert mode == "0o600"
