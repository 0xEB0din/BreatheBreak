from datetime import datetime, timedelta

from breathebreak.tracker import SessionTracker


class TestSessionTracker:
    def test_record_break_increments(self, tmp_path):
        tracker = SessionTracker(str(tmp_path))
        tracker.record_break()
        tracker.record_break()
        stats = tracker.today_stats()
        assert stats["breaks_taken"] == 2

    def test_session_tracks_focus_time(self, tmp_path):
        tracker = SessionTracker(str(tmp_path))
        tracker.start_session()
        # Backdate the start to simulate 25 minutes of work
        tracker._session_start = datetime.now() - timedelta(minutes=25)
        tracker.end_session()
        stats = tracker.today_stats()
        assert stats["focus_minutes"] >= 24

    def test_empty_stats(self, tmp_path):
        tracker = SessionTracker(str(tmp_path))
        stats = tracker.today_stats()
        assert stats["breaks_taken"] == 0
        assert stats["focus_minutes"] == 0

    def test_persistence_across_instances(self, tmp_path):
        tracker1 = SessionTracker(str(tmp_path))
        tracker1.record_break()
        tracker1.record_break()
        tracker1.record_break()

        tracker2 = SessionTracker(str(tmp_path))
        stats = tracker2.today_stats()
        assert stats["breaks_taken"] == 3

    def test_end_session_without_start_is_noop(self, tmp_path):
        tracker = SessionTracker(str(tmp_path))
        tracker.end_session()  # should not raise
        stats = tracker.today_stats()
        assert stats["focus_minutes"] == 0

    def test_multiple_sessions_accumulate(self, tmp_path):
        tracker = SessionTracker(str(tmp_path))

        tracker.start_session()
        tracker._session_start = datetime.now() - timedelta(minutes=10)
        tracker.end_session()

        tracker.start_session()
        tracker._session_start = datetime.now() - timedelta(minutes=15)
        tracker.end_session()

        stats = tracker.today_stats()
        assert stats["focus_minutes"] >= 24
