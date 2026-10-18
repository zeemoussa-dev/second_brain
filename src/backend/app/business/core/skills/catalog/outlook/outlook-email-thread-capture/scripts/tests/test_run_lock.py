"""The delta's single-run lock: two runs must never capture at once.

Run from this Skill's own scripts/ folder:
    python -m pytest tests/test_run_lock.py

2026-10-18: the cron agent hit Hermes' 420s terminal timeout and retried
run_delta_capture.py in the background while the first run was still going.
Both created a Thread for the same conversation. A second run now stands down
with "already_running"; a lock left by a dead or long-gone run is taken over.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import run_delta_capture as rdc  # noqa: E402


@pytest.fixture()
def lock(tmp_path, monkeypatch):
    path = tmp_path / rdc.LOCK_FILE
    monkeypatch.setattr(rdc, "_lock_path", lambda: path)
    return path


@pytest.fixture()
def capture(tmp_path, monkeypatch, lock):
    """main() with the capture itself replaced by a recorder."""
    monkeypatch.setattr(rdc, "VAULT_PATH", str(tmp_path))
    runs: list[bool] = []

    def fake_capture(args):
        runs.append(lock.exists())
        return 0

    monkeypatch.setattr(rdc, "_capture", fake_capture)
    return runs


def dead_pid() -> int:
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    return child.pid


def hold(lock: Path, pid: int, minutes_ago: float = 0, **extra) -> dict:
    holder = {"pid": pid, "started_at": time.time() - minutes_ago * 60, **extra}
    lock.write_text(json.dumps(holder), encoding="utf-8")
    return holder


def test_a_run_holds_the_lock_while_capturing_and_releases_it(capture, lock):
    assert rdc.main([]) == 0
    assert capture == [True], "the capture ran with the lock held"
    assert not lock.exists()


def test_a_second_run_stands_down_while_a_live_run_holds_the_lock(capture, lock, capsys):
    holder = hold(lock, os.getpid())
    assert rdc.main([]) == 0, "standing down is a clean exit, not a failure"
    assert capture == [], "nothing was captured"
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert report["status"] == "already_running" and report["holder_pid"] == os.getpid()
    assert json.loads(lock.read_text(encoding="utf-8")) == holder, "the live run's lock is untouched"


def test_a_lock_left_by_a_dead_run_is_taken_over(capture, lock):
    hold(lock, dead_pid())
    assert rdc.main([]) == 0
    assert capture == [True] and not lock.exists()


def test_a_lock_older_than_an_hour_is_taken_over_even_if_its_pid_is_alive(capture, lock):
    hold(lock, os.getpid(), minutes_ago=rdc.STALE_LOCK_MINUTES + 1)
    assert rdc.main([]) == 0
    assert capture == [True]


def test_a_run_given_a_longer_budget_is_not_retired_at_an_hour(capture, lock):
    hold(lock, os.getpid(), minutes_ago=rdc.STALE_LOCK_MINUTES + 1, max_minutes=120)
    assert rdc.main([]) == 0
    assert capture == []


def test_a_fresh_lock_not_yet_written_is_not_mistaken_for_a_dead_one(capture, lock):
    lock.write_text("", encoding="utf-8")
    assert rdc.main([]) == 0
    assert capture == []


def test_the_lock_is_released_when_the_capture_crashes(tmp_path, monkeypatch, lock):
    monkeypatch.setattr(rdc, "VAULT_PATH", str(tmp_path))

    def crash(args):
        raise RuntimeError("boom")

    monkeypatch.setattr(rdc, "_capture", crash)
    with pytest.raises(RuntimeError):
        rdc.main([])
    assert not lock.exists()


def test_a_run_never_releases_a_lock_it_does_not_hold(lock):
    holder = hold(lock, os.getpid() + 1)
    rdc.release_run_lock(lock)
    assert json.loads(lock.read_text(encoding="utf-8")) == holder


def test_liveness_of_this_process_and_of_a_finished_one():
    assert rdc._pid_is_alive(os.getpid())
    assert not rdc._pid_is_alive(dead_pid())
    assert not rdc._pid_is_alive(0)
