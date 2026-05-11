"""Unit tests for intel_failure_tracker."""
import pytest
from pathlib import Path
from intel_failure_tracker import FailureTracker


@pytest.fixture
def tracker(tmp_path):
    return FailureTracker(tmp_path / ".intel_failures")


def test_default_count_when_file_missing(tracker):
    assert tracker.count() == 0


def test_record_failure_increments(tracker):
    tracker.record_failure()
    assert tracker.count() == 1
    tracker.record_failure()
    assert tracker.count() == 2


def test_reset_to_zero(tracker):
    tracker.record_failure()
    tracker.record_failure()
    tracker.reset()
    assert tracker.count() == 0


def test_should_alert_returns_false_below_threshold(tracker):
    tracker.record_failure()
    tracker.record_failure()
    assert tracker.should_alert(threshold=3) is False


def test_should_alert_returns_true_at_threshold(tracker):
    tracker.record_failure()
    tracker.record_failure()
    tracker.record_failure()
    assert tracker.should_alert(threshold=3) is True


def test_alert_resets_counter(tracker):
    """When alert fires, counter resets so we don't spam every run."""
    for _ in range(3):
        tracker.record_failure()
    assert tracker.should_alert(threshold=3) is True
    tracker.reset()
    assert tracker.count() == 0


def test_corrupt_file_treated_as_zero(tracker, tmp_path):
    """If someone manually writes junk into the counter file, don't crash."""
    (tmp_path / ".intel_failures").write_text("not a number", encoding="utf-8")
    assert tracker.count() == 0
