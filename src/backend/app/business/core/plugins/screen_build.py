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

**The build is bounded and uses this checkout's own npm.** Serialising builds
means a single hung build stops every publish and install, so the two ways one
can hang are closed off. It gets a hard timeout and its whole process tree is
killed, because npm is a `cmd.exe` shim whose Node child survives being
orphaned. And npm is resolved from `tools/node/` before PATH: the first npm on
the operator's PATH is Hermes' bundled Node, which on 2026-10-18 started and
never ran the build, holding the lock while the backend answered nothing --
twice, until a worker was killed by hand each time.

Deliberately **stdlib only, and importing nothing from `app`**: the publish
script loads it by file path without booting the application, and the
Marketplace calls it while installing from a repository.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import threading
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
# A build is tens of seconds. This is not a performance budget, it is the bound
# on how long a HUNG npm can hold the lock: on 2026-10-18 npm started and never
# ran the build (a `cmd.exe /c npm.CMD run build` with no Node child under it),
# and with no timeout here it held the lock while the backend answered nothing
# for thirteen minutes -- the worker had to be killed by hand, twice.
_BUILD_TIMEOUT_SECONDS = 600


def _npm_executable(frontend_root: Path) -> str | None:
    """This checkout's own npm first, PATH second.

    PATH is not trustworthy for this: on the operator's machine the first npm on
    it is Hermes' bundled Node (`AppData/Local/hermes/node/npm.CMD`), which is
    what hung on 2026-10-18. The repo ships its own Node in `tools/node/` and
    every launcher puts that first (`tools/use-node.ps1`); this had been the one
    place that asked PATH instead.
    """
    repo_root = Path(frontend_root).resolve().parents[1]
    for candidate in (repo_root / "tools" / "node" / "npm.cmd", repo_root / "tools" / "node" / "npm"):
        if candidate.is_file():
            return str(candidate)
    return shutil.which("npm") or shutil.which("npm.cmd")


def _kill_process_tree(process: subprocess.Popen) -> None:
    """`process.kill()` is not enough on Windows: npm is a `cmd.exe` shim and
    the real work is a Node CHILD of it, so killing the shim alone orphans the
    build -- which is exactly what was found holding the lock (pid 42708, no
    Node child, still running after its parent was gone)."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process.pid)],
            capture_output=True, check=False,
        )
    else:
        process.kill()


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


def _holder(lock_path: Path) -> tuple[int, int]:
    """`(pid, thread id)` of whoever holds the lock, or `(0, 0)`.

    The thread matters because the backend serves requests from a THREADPOOL:
    two installs at once share a pid, and refusing the second because "this
    process already holds it" would turn ordinary concurrency into a failure.
    Only the same pid AND the same thread is a nested build.
    """
    try:
        written = lock_path.read_text(encoding="ascii").strip()
    except OSError:
        return 0, 0
    pid, _, thread = written.partition(":")
    try:
        return int(pid or 0), int(thread or 0)
    except ValueError:
        return 0, 0


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
            holder_pid, holder_thread = _holder(lock_path)
            # Held by this very THREAD: nobody will release it while we wait,
            # because we are the waiter. Waiting out the window would wedge the
            # request for fifteen minutes rather than fail. Another thread of
            # this same process is ordinary concurrency and waits normally.
            if (holder_pid, holder_thread) == (os.getpid(), threading.get_ident()):
                raise TimeoutError(
                    f"{lock_path.name} is already held by this thread (pid {holder_pid}) -- "
                    "a screen build cannot nest inside another"
                )
            # A killed build never reaches its `finally`. Two ways to tell: its
            # process is gone (immediate, and this really happens -- a lock from
            # a dead pid was found holding this checkout on 2026-10-18), or the
            # lock is simply too old to believe, which covers a pid the OS has
            # since reused for something unrelated.
            if not _holder_is_alive(holder_pid) or held_for > stale_seconds:
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
        os.write(descriptor, f"{os.getpid()}:{threading.get_ident()}".encode("ascii"))
        os.close(descriptor)
        break

    try:
        yield
    finally:
        # `finally`, so a cancelled request releases too: asyncio's
        # CancelledError is a BaseException rather than an Exception, but
        # `finally` runs for both. This was a suspect for the 2026-10-18
        # outages and was not the cause -- the lock outlived the request
        # because the worker was KILLED, which no Python-level cleanup can
        # survive. That case is covered by the dead-holder takeover instead.
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
    npm = _npm_executable(frontend_root)
    if npm is None:
        return "npm was not found in tools/node or on PATH, so the screens could not be built"

    check_dir = check_dir_for(frontend_root, plugin_id, purpose)
    try:
        with screen_build_lock(frontend_root):
            for leftover in sorted((check_dir.parent).glob(f"{_CHECK_DIR_PREFIX}*{_CHECK_DIR_MARKER}*")):
                if _is_check_dir(leftover):
                    shutil.rmtree(leftover, ignore_errors=True)
            shutil.copytree(ui_dir, check_dir, ignore=shutil.ignore_patterns("node_modules"))
            try:
                output, timed_out = _run_build(npm, frontend_root)
            finally:
                shutil.rmtree(check_dir, ignore_errors=True)
    except TimeoutError as waited_too_long:
        return f"the screens could not be built: {waited_too_long}"

    if timed_out:
        return (
            f"the screens could not be built: npm did not finish within "
            f"{_BUILD_TIMEOUT_SECONDS}s and was stopped. The build may have hung before "
            f"starting -- check which npm ran ({npm})."
        )
    if output is None:
        return None
    tail = "\n".join(output.strip().splitlines()[-25:])
    return f"the screens do not build inside this framework:\n{tail}"


def _run_build(npm: str, frontend_root: Path) -> tuple[str | None, bool]:
    """`(None, False)` when the build succeeds, `(output, False)` when it fails,
    `(None, True)` when it had to be stopped.

    `Popen` rather than `subprocess.run(timeout=...)` so the whole process TREE
    can be killed: run()'s own timeout kills the direct child, which for npm is
    a `cmd.exe` shim, and would leave the Node build running and the lock held.
    """
    process = subprocess.Popen(
        [npm, "run", "build"], cwd=str(frontend_root),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    try:
        output, _ = process.communicate(timeout=_BUILD_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        _kill_process_tree(process)
        try:
            # Drain what it wrote, briefly: the pipes are closed by the kill, but
            # a wait with no bound here would reintroduce the hang this prevents.
            process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            pass
        return None, True
    return (None, False) if process.returncode == 0 else (output, False)
