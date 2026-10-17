"""One plugin screen build at a time, across processes.

`tsc -b` compiles the whole of `src/`, so a second check running at the same
moment is part of the first one's program, and deleting its folder when it
finishes fails the first with TS6053 for files that existed when the build
started. Two sessions publishing at once hit this live on 2026-10-17.

The lock is tested directly rather than through `build_screens`, which shells
out to npm: these pin the ordering, the takeover of a dead holder, and the
sweep, without a real build.
"""
import os
import threading
import time
from pathlib import Path

import pytest

from app.business.core.plugins.screen_build import (
    check_dir_for,
    screen_build_lock,
)

_LOCK_NAME = ".screen-build.lock"


def test_the_lock_is_released_after_the_block(tmp_path: Path):
    with screen_build_lock(tmp_path):
        assert (tmp_path / _LOCK_NAME).is_file()

    assert not (tmp_path / _LOCK_NAME).exists()


def test_it_is_released_even_when_the_build_raises(tmp_path: Path):
    with pytest.raises(RuntimeError):
        with screen_build_lock(tmp_path):
            raise RuntimeError("the build blew up")

    # A holder that never releases blocks every later publish and install.
    assert not (tmp_path / _LOCK_NAME).exists()


def test_a_second_build_waits_for_the_first(tmp_path: Path):
    order: list[str] = []
    first_is_holding = threading.Event()
    release_first = threading.Event()

    def first():
        with screen_build_lock(tmp_path):
            order.append("first in")
            first_is_holding.set()
            release_first.wait(timeout=5)
            order.append("first out")

    def second():
        first_is_holding.wait(timeout=5)
        with screen_build_lock(tmp_path):
            order.append("second in")

    threads = [threading.Thread(target=first), threading.Thread(target=second)]
    for thread in threads:
        thread.start()
    # The second thread is now waiting on a lock the first still holds.
    time.sleep(0.5)
    assert order == ["first in"]
    release_first.set()
    for thread in threads:
        thread.join(timeout=10)

    # Not interleaved: the second build starts only once the first has finished,
    # which is the whole point -- its folder must not exist during the first's
    # tsc program.
    assert order == ["first in", "first out", "second in"]


def test_waiting_gives_up_rather_than_hanging(tmp_path: Path):
    # This process IS alive, so the lock is genuinely held and waiting is right.
    (tmp_path / _LOCK_NAME).write_text(str(os.getpid()), encoding="utf-8")

    with pytest.raises(TimeoutError):
        with screen_build_lock(tmp_path, wait_seconds=0.5, stale_seconds=3600):
            pass


def test_a_dead_holder_is_taken_over_without_waiting(tmp_path: Path):
    lock_path = tmp_path / _LOCK_NAME
    # A pid that is not running, with a FRESH mtime: a build killed seconds ago.
    # Waiting out the stale window here would block every publish and install on
    # the machine for half an hour, which is what a real leftover lock from a
    # dead pid did to this checkout on 2026-10-18.
    lock_path.write_text("999999", encoding="utf-8")

    with screen_build_lock(tmp_path, wait_seconds=2, stale_seconds=1800):
        assert lock_path.is_file()


def test_a_dead_holders_lock_is_taken_over(tmp_path: Path):
    lock_path = tmp_path / _LOCK_NAME
    lock_path.write_text("999999", encoding="utf-8")
    stale = time.time() - 7200
    os.utime(lock_path, (stale, stale))

    # A build killed mid-run never reaches its release, and without takeover it
    # would block every publish and install from then on.
    with screen_build_lock(tmp_path, wait_seconds=5, stale_seconds=1800):
        assert lock_path.is_file()


def test_check_dir_sits_at_an_installed_plugins_depth(tmp_path: Path):
    check_dir = check_dir_for(tmp_path, "azure-cost-manager", "publish")

    # `../../pluginHost/...` has to resolve from inside the copy exactly as it
    # will once installed, which is what makes the gate meaningful.
    assert check_dir.parent == tmp_path / "src" / "plugins"
    assert check_dir.name == "__publish-check-azure-cost-manager"
    # And it must never be a valid plugin id, or the host would mount it.
    assert check_dir.name.startswith("__")
