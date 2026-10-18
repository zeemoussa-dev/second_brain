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
import subprocess
import threading
import time
from pathlib import Path

import pytest

from app.business.core.plugins import screen_build
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


def test_a_build_cannot_nest_inside_another_on_the_same_thread(tmp_path: Path):
    # Nobody will release it while we wait, because we are the waiter. Waiting
    # out the window would wedge the request instead of failing.
    with screen_build_lock(tmp_path):
        with pytest.raises(TimeoutError, match="already held by this thread"):
            with screen_build_lock(tmp_path, wait_seconds=30):
                pass


def test_another_thread_of_the_same_process_waits_rather_than_failing(tmp_path: Path):
    # The backend serves requests from a THREADPOOL, so two installs at once
    # share a pid. Keying this check on the pid alone (the first version of it)
    # turned ordinary concurrency into a failure -- caught by the serialisation
    # test above, which is exactly that shape.
    outcome: list[str] = []

    def second():
        try:
            with screen_build_lock(tmp_path, wait_seconds=5):
                outcome.append("acquired")
        except TimeoutError:
            outcome.append("refused")

    with screen_build_lock(tmp_path):
        waiter = threading.Thread(target=second)
        waiter.start()
        time.sleep(0.4)
        assert outcome == []          # still waiting, not refused
    waiter.join(timeout=10)

    assert outcome == ["acquired"]


def test_npm_comes_from_this_checkout_before_PATH(tmp_path: Path):
    frontend_root = tmp_path / "src" / "frontend"
    frontend_root.mkdir(parents=True)
    bundled = tmp_path / "tools" / "node"
    bundled.mkdir(parents=True)
    (bundled / "npm.cmd").write_text("@echo off", encoding="utf-8")

    # PATH's first npm on the operator's machine is Hermes' bundled Node, which
    # hung before starting the build; the repo ships its own in tools/node and
    # every launcher puts that first.
    assert screen_build._npm_executable(frontend_root) == str(bundled / "npm.cmd")


def test_without_a_bundled_npm_it_falls_back_to_PATH(tmp_path: Path, monkeypatch):
    frontend_root = tmp_path / "src" / "frontend"
    frontend_root.mkdir(parents=True)
    monkeypatch.setattr(screen_build.shutil, "which", lambda name: f"C:/somewhere/{name}")

    assert screen_build._npm_executable(frontend_root) == "C:/somewhere/npm"


def test_a_hung_build_is_killed_as_a_tree_and_reported(tmp_path: Path, monkeypatch):
    killed: list[int] = []

    class HungProcess:
        pid = 4242
        returncode = None

        def communicate(self, timeout=None):
            if not killed:
                raise subprocess.TimeoutExpired(cmd="npm run build", timeout=timeout)
            return ("", "")

    monkeypatch.setattr(screen_build.subprocess, "Popen", lambda *a, **k: HungProcess())
    monkeypatch.setattr(screen_build, "_kill_process_tree", lambda process: killed.append(process.pid))

    output, timed_out = screen_build._run_build("npm", tmp_path)

    # The whole tree, not just the shim: npm is a cmd.exe wrapper and its Node
    # child outlives being orphaned -- pid 42708 was found still running.
    assert timed_out is True
    assert output is None
    assert killed == [4242]


def test_the_build_is_spawned_without_the_workers_stdin_or_console(tmp_path, monkeypatch):
    captured: dict = {}

    class DoneProcess:
        pid = 1
        returncode = 0

        def communicate(self, timeout=None):
            return ("", "")

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return DoneProcess()

    monkeypatch.setattr(screen_build.subprocess, "Popen", fake_popen)

    screen_build._run_build(str(tmp_path / "tools" / "node" / "npm.cmd"), tmp_path)

    # npm is a BATCH file: given a console CTRL event it asks "Terminate batch
    # job (Y/N)?" and waits. A uvicorn --reload worker has no console, so that
    # read never returns -- the hang that wedged the backend on 2026-10-18.
    assert captured["stdin"] is screen_build.subprocess.DEVNULL
    if os.name == "nt":
        flags = captured["creationflags"]
        # Its own process group, so the reloader's CTRL event does not reach it.
        assert flags & screen_build.subprocess.CREATE_NEW_PROCESS_GROUP
        assert flags & screen_build.subprocess.CREATE_NO_WINDOW


def test_the_build_env_puts_this_nodes_directory_first_and_silences_npm(tmp_path):
    npm = tmp_path / "tools" / "node" / "npm.cmd"

    environment = screen_build._build_environment(str(npm))

    # npm looks `node` up itself, and the first Node on the operator's PATH
    # belongs to Hermes.
    assert environment["PATH"].split(os.pathsep)[0] == str(npm.parent)
    assert environment["CI"] == "true"
    assert environment["npm_config_update_notifier"] == "false"


def test_check_dir_sits_at_an_installed_plugins_depth(tmp_path: Path):
    check_dir = check_dir_for(tmp_path, "azure-cost-manager", "publish")

    # `../../pluginHost/...` has to resolve from inside the copy exactly as it
    # will once installed, which is what makes the gate meaningful.
    assert check_dir.parent == tmp_path / "src" / "plugins"
    assert check_dir.name == "__publish-check-azure-cost-manager"
    # And it must never be a valid plugin id, or the host would mount it.
    assert check_dir.name.startswith("__")
