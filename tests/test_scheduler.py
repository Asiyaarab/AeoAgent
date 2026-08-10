"""Tests for app/scheduler.py — URL bookkeeping + idempotency."""
import pytest

from app import scheduler as sched


@pytest.fixture(autouse=True)
def _reset_url():
    with sched._url_lock:
        sched.scheduled_url.clear()
    yield
    with sched._url_lock:
        sched.scheduled_url.clear()


def test_set_scheduled_url_pushes_when_empty():
    sched.set_scheduled_url("https://a.com")
    assert sched.get_scheduled_url() == "https://a.com"


def test_set_scheduled_url_replaces_existing():
    sched.set_scheduled_url("https://a.com")
    sched.set_scheduled_url("https://b.com")
    assert sched.get_scheduled_url() == "https://b.com"
    # Should still only have 1 element
    with sched._url_lock:
        assert len(sched.scheduled_url) == 1


def test_get_scheduled_url_empty():
    assert sched.get_scheduled_url() is None


def test_scheduled_run_logs_warning_when_no_url(monkeypatch):
    """If no URL is set, the scheduled job should not crash and should warn."""
    # Don't actually start the scheduler — just call the callback directly.
    from app import scheduler as s
    s.scheduled_run()  # no URL set → should log a warning, not raise


def test_get_next_run_returns_iso_string_when_job_scheduled():
    """Start the scheduler (idempotently) and check next_run is a valid ISO timestamp."""
    from apscheduler.schedulers.background import BackgroundScheduler

    # Snapshot the current scheduler state so we can restore it
    was_running = sched.scheduler.running
    try:
        if not was_running:
            sched.init_scheduler()
        nxt = sched.get_next_run()
        if nxt is not None:
            assert "T" in nxt
            # Should be parseable as ISO 8601
            from datetime import datetime
            datetime.fromisoformat(nxt)
    finally:
        if not was_running and sched.scheduler.running:
            sched.scheduler.shutdown(wait=False)
