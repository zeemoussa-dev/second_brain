"""The watermark rule that decides whether a failed email is retried or lost
forever.

Run from this Skill's own scripts/ folder:
    python -m pytest tests/test_next_watermark.py

Written after the 2026-09-04 incident: `run_delta_capture.py` swallowed a
non-zero `ingest_email.py` exit, counted the email as processed, reported the
run "complete", and advanced the watermark past it. 54 real emails were
consumed and never written, and nothing surfaced it for a day.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from run_delta_capture import next_watermark  # noqa: E402

BEFORE = "2026-09-01 00:00:00+00:00"


def _failure(received: str) -> dict:
    return {"message_id": "m", "received": received, "subject": "s", "error": "boom"}


def test_a_clean_run_advances_to_the_newest_email() -> None:
    assert next_watermark(BEFORE, "2026-09-04 12:00:00+00:00", [], ["2026-09-04 12:00:00+00:00"]) == (
        "2026-09-04 12:00:00+00:00"
    )


def test_a_run_where_everything_failed_does_not_advance_at_all() -> None:
    """The exact shape of the incident: new emails seen, none written."""
    assert next_watermark(BEFORE, "2026-09-04 12:00:00+00:00", [_failure("2026-09-02 09:00:00+00:00")], []) == BEFORE


def test_the_watermark_stops_below_the_oldest_failure() -> None:
    succeeded = ["2026-09-02 08:00:00+00:00", "2026-09-03 10:00:00+00:00"]
    failures = [_failure("2026-09-02 09:00:00+00:00")]

    # 08:00 succeeded and is older than the failure, so it is safe to pass.
    # 10:00 also succeeded but sits AFTER the failure -- passing it would
    # strand the 09:00 email forever.
    assert next_watermark(BEFORE, "2026-09-03 10:00:00+00:00", failures, succeeded) == "2026-09-02 08:00:00+00:00"


def test_it_never_moves_backwards() -> None:
    later = "2026-09-05 00:00:00+00:00"
    assert next_watermark(later, "2026-09-04 12:00:00+00:00", [], []) == later


def test_a_failure_with_no_timestamp_blocks_every_advance() -> None:
    """An email we cannot even place in time is the one case where guessing is
    worst -- refuse to advance rather than risk stepping over it."""
    assert next_watermark(BEFORE, "2026-09-04 12:00:00+00:00", [_failure("")], ["2026-09-02 08:00:00+00:00"]) == BEFORE
