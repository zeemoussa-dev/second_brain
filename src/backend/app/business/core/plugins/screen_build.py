"""Building a plugin's screens inside this framework -- the gate that proves the
screens compile against the host they will run in (`ADR-022`).

The screens are copied beside the installed plugins under a folder name the host
never mounts (it is not a valid plugin id), the whole frontend is built, and the
copy is always removed. The copy sits at an installed plugin's depth, so
`../../pluginHost/...` resolves exactly as it will once installed.

**One build at a time, across processes.** `tsc -b` compiles the whole of
`src/`, so a second check running at the same moment is part of the first one's
program -- and when it finishes and deletes its folder, the first fails with
TS6053 "File ... not found" for files that existed when the build started. Two
sessions publishing at once hit this live (2026-10-17: an Azure Cost install
died on `__publish-check-entities/AccountPage.tsx` while the Entities session
ran its own dry run). A lock is the fix rather than excluding the other folder
from the program, because `npm run build` uses the project's own tsconfig and
the set of check folders is not known when that file is written.

Holding the lock also makes it safe to sweep check folders left behind by a run
that was killed: with one build at a time, any that exist are nobody's.

Deliberately **stdlib only, and importing nothing from `app`**: the publish
script loads it by file path without booting the application, and the
Marketplace calls it while installing from a repository.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

_LOCK_FILENAME = ".screen-build.lock"
# A build is tens of seconds, so a queued one waits minutes at most. Long enough
# that a second session queues instead of failing; short enough that a hung
# holder does not look like a hang of its own.
_LOCK_WAIT_SECONDS = 900
# Past this the holder is assumed dead (killed mid-build, machine restarted).
# Well above any real build, so a slow build is never stolen from.
_LOCK_STALE_SECONDS = 1800
_CHECK_DIR_PREFIX = "__"
_CHECK_DIR_MARKER = "-check-"


def check_dir_for(frontend_root: Path, plugin_id: str, purpose: str) -> Path:
    return Path(frontend_root) / "src" / "plugins" / f"{_CHECK_DIR_PREFIX}{purpose}{_CHECK_DIR_MARKER}{plugin_id}"


def _is_check_dir(path: Path) -> bool:
    return (
        path.is_dir()
        and path.name.startswith(_CHECK_DIR_PREFIX)
        and _CHECK_DIR_MARKER in path.name
    )


def _holder_is_alive(pid: int) -> bool:
    """Whether the process that took the lock still exists.

    Deliberately NOT `os.kill(pid, 0)`: that is the POSIX idiom, but on Windows
    CPython implements `os.kill` as TerminateProcess, so signal 0 would KILL the
    holder rather than ask after it -- and the holder is usually a live build.
    """
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        _SYNCHRONIZE = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(_SYNCHRONIZE, False, pid)
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # someone else's process: alive, just not ours to signal
    return True


def _holder_pid(lock_path: Path) -> int:
    try:
        return int(lock_path.read_text(encoding="ascii").strip() or 0)
    except (OSError, ValueError):
        return 0


@contextmanager
def screen_build_lock(
    frontend_root: Path, *,
    wait_seconds: float = _LOCK_WAIT_SECONDS,
    stale_seconds: float = _LOCK_STALE_SECONDS,
):
    """Exclusive across PROCESSES -- the publish script and the backend are not
    the same process, so an in-process lock would not see the other.

    `O_CREAT | O_EXCL` is the primitive: a single filesystem operation that
    either creates the file or fails, with no window between checking and
    taking. Raises TimeoutError when the wait runs out; the caller turns that
    into a refusal rather than letting it surface as a crash.
    """
    lock_path = Path(frontend_root) / _LOCK_FILENAME
    deadline = time.monotonic() + wait_seconds

    while True:
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                held_for = time.time() - lock_path.stat().st_mtime
            except OSError:
                continue  # released between the failed create and the stat
            # A killed build never reaches its `finally`. Two ways to tell: its
            # process is gone (immediate, and this really happens -- a lock from
            # a dead pid was found holding this checkout on 2026-10-18), or the
            # lock is simply too old to believe, which covers a pid the OS has
            # since reused for something unrelated.
            if not _holder_is_alive(_holder_pid(lock_path)) or held_for > stale_seconds:
                try:
                    lock_path.unlink()
                except OSError:
                    pass
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"another plugin screen build has held {lock_path.name} for "
                    f"{int(held_for)}s"
                )
            time.sleep(0.25)
            continue
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.close(descriptor)
        break

    try:
        yield
    finally:
        try:
            lock_path.unlink()
        except OSError:
            pass


def build_screens(frontend_root: Path, plugin_id: str, ui_dir: Path, *, purpose: str = "publish") -> str | None:
    """None when the screens build, otherwise why they do not.

    The build output left in `dist/` includes the copy until the next build; the
    dev server never serves `dist/`."""
    frontend_root, ui_dir = Path(frontend_root), Path(ui_dir)
    if not ui_dir.is_dir():
        return None
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if npm is None:
        return "npm was not found on PATH, so the screens could not be built"

    check_dir = check_dir_for(frontend_root, plugin_id, purpose)
    try:
        with screen_build_lock(frontend_root):
            for leftover in sorted((check_dir.parent).glob(f"{_CHECK_DIR_PREFIX}*{_CHECK_DIR_MARKER}*")):
                if _is_check_dir(leftover):
                    shutil.rmtree(leftover, ignore_errors=True)
            shutil.copytree(ui_dir, check_dir, ignore=shutil.ignore_patterns("node_modules"))
            try:
                completed = subprocess.run(
                    [npm, "run", "build"], cwd=frontend_root,
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                )
            finally:
                shutil.rmtree(check_dir, ignore_errors=True)
    except TimeoutError as waited_too_long:
        return f"the screens could not be built: {waited_too_long}"

    if completed.returncode == 0:
        return None
    tail = "\n".join((completed.stdout + completed.stderr).strip().splitlines()[-25:])
    return f"the screens do not build inside this framework:\n{tail}"
