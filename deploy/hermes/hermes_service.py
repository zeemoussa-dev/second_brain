"""Hermes as Windows services (production, 2026-10-28).

Hermes runs as two long-lived processes, and the split is not ours to change:

  * the **gateway** does the work -- cron, channels, capture. Without it
    Hermes is up and does nothing.
  * the **dashboard** answers HTTP on 127.0.0.1:9119: the REST API Second
    Brain reads, and the HTML it lifts its session token out of. It
    deliberately does not run cron (``web_server.py``: "cron execution
    belongs to the GATEWAY process"), and starting it does not start a
    gateway.

So each gets its own service, registered from this one file:

    python hermes_service.py gateway   --startup auto install
    python hermes_service.py dashboard --startup auto install

Two services rather than one supervising both, because the two halves fail
and recover separately: Windows shows which one is down, the restart policy
applies to each, and the dashboard can be restarted without taking the
capture down with it. The installer makes the dashboard depend on the
gateway so they still start in that order -- the dashboard decides per cron
tick whether a profile's own gateway is live, and it should never be the one
answering for a gateway that is merely late.

**Why not the Scheduled Task upstream uses on Windows.** It runs as whoever
is logged in, and on a server nobody is.

**Why a child process rather than importing Hermes.** Second Brain's own
service imports uvicorn and runs it in a thread; that cannot be done here.
Hermes is a CLI with its own process supervision, startup watchdog and
re-exec paths, and hosting its internals inside a service process would
fight all three. So each service runs the command line upstream documents
and manages its lifetime instead.

**Why a job object.** Hermes spawns children of its own -- a profile's
agent, a terminal, a browser. Terminating only the process we launched would
orphan them, and an orphaned gateway still holds the cron tick lock: the
next start then looks healthy and fires nothing. The child is created
suspended, assigned to a job that kills everything in it when its last
handle closes, and only then resumed -- so no descendant can escape,
because none exists yet.

**Why it exits instead of restarting a dead child.** The installer registers
each service with ``sc failure ... restart``, so Windows already owns the
restart policy, with backoff, and records it where someone will look.
Supervising twice would only hide the failure.

**Everything each service needs is in one file beside it**, written by the
installer: ``service-gateway.json`` / ``service-dashboard.json``. A service
runs as a machine account with no profile, no PATH of ours and no working
directory we chose, so nothing is inferred from the environment -- the paths
are read, not guessed.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import servicemanager
import win32api
import win32con
import win32event
import win32file
import win32job
import win32process
import win32security
import win32service
import win32serviceutil

HERE = Path(__file__).resolve().parent

# How long a graceful stop is given before the job object is closed and the
# whole process tree goes with it. The Service Control Manager's own patience
# is 30 seconds by default, and it kills the service process when that runs
# out -- which would leave the children behind, the one outcome this wrapper
# exists to prevent. So stay well inside it.
_GRACEFUL_STOP_SECONDS = 20


def _settings(role: str) -> dict:
    """What the installer wrote for this role. A missing or unreadable file is
    fatal and said so in the event log: a service that starts with invented
    paths would run a different Hermes than the one that was installed."""
    return json.loads((HERE / f"service-{role}.json").read_text(encoding="utf-8"))


def _a_job_that_kills_everything_in_it():
    job = win32job.CreateJobObject(None, "")
    limits = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
    limits["BasicLimitInformation"]["LimitFlags"] |= win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, limits)
    return job


def _inheritable(path: str, write: bool):
    """A handle the child may inherit, for its standard streams.

    A service has no console, so without this the child's output goes
    nowhere -- and a Hermes that dies three seconds into startup would leave
    nothing at all to read. Opened for append, not truncated: the reason a
    restart loop keeps happening is in the previous attempt.
    """
    attributes = win32security.SECURITY_ATTRIBUTES()
    attributes.bInheritHandle = True
    handle = win32file.CreateFile(
        path,
        win32file.GENERIC_WRITE if write else win32file.GENERIC_READ,
        win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
        attributes,
        win32con.OPEN_ALWAYS,
        0,
        None,
    )
    if write:
        win32file.SetFilePointer(handle, 0, win32file.FILE_END)
    return handle


class _HermesProcessService(win32serviceutil.ServiceFramework):
    """One Hermes command line, kept running. Subclassed per role below --
    the Service Control Manager identifies a service by its class, so two
    services means two classes, and everything that differs between them
    comes from that role's own settings file."""

    role = ""

    def __init__(self, args) -> None:
        super().__init__(args)
        self._stop_requested = win32event.CreateEvent(None, 0, 0, None)
        self._job = None
        self._child = None

    def SvcStop(self) -> None:
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self._stop_requested)

    def SvcDoRun(self) -> None:
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        try:
            self._run()
        except Exception as problem:  # noqa: BLE001 -- the event log is the only reader
            servicemanager.LogErrorMsg(f"{self._svc_name_} could not start: {problem!r}")
            self._kill_the_tree()
            raise

    # ------------------------------------------------------------------
    def _run(self) -> None:
        settings = _settings(self.role)
        home = Path(settings["hermes_home"])
        source = Path(settings["source_dir"])
        python = Path(settings["python"])

        logs = home / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        log_file = logs / f"service-{self.role}.log"

        command = subprocess.list2cmdline([str(python), "-m", "hermes_cli.main", *settings["arguments"]])
        self._job = _a_job_that_kills_everything_in_it()

        nothing = _inheritable("NUL", write=False)
        output = _inheritable(str(log_file), write=True)
        startup = win32process.STARTUPINFO()
        startup.dwFlags = win32process.STARTF_USESTDHANDLES
        startup.hStdInput = nothing
        startup.hStdOutput = output
        startup.hStdError = output

        child, main_thread, pid, _tid = win32process.CreateProcess(
            None,
            command,
            None,
            None,
            True,  # inherit the three handles above, and nothing else
            win32con.CREATE_SUSPENDED | win32con.CREATE_NO_WINDOW | win32con.CREATE_UNICODE_ENVIRONMENT,
            self._environment(settings, home),
            str(source),
            startup,
        )
        self._child = child
        win32job.AssignProcessToJobObject(self._job, child)
        win32process.ResumeThread(main_thread)
        win32api.CloseHandle(main_thread)
        servicemanager.LogInfoMsg(f"{self._svc_name_} started pid {pid}; its output goes to {log_file}.")

        # Either we are told to stop, or the child stops on its own.
        signalled = win32event.WaitForMultipleObjects(
            [self._stop_requested, child], False, win32event.INFINITE
        )
        if signalled == win32event.WAIT_OBJECT_0 + 1:
            code = win32process.GetExitCodeProcess(child)
            servicemanager.LogErrorMsg(
                f"{self._svc_name_}: hermes {' '.join(settings['arguments'])} exited with {code}. "
                f"Stopping so Windows restarts it; the reason is in {log_file}."
            )
            self._kill_the_tree()
            # Abrupt on purpose. A service that reports a clean stop has, as
            # far as Windows is concerned, been asked to stop -- and the
            # failure actions the installer configured never fire. Leaving
            # without reporting anything is what makes this a crash.
            os._exit(1)

        self._stop_the_child(settings, python, source, home)

    def _stop_the_child(self, settings: dict, python: Path, source: Path, home: Path) -> None:
        """Hermes' own stop command first, the job object second.

        ``hermes gateway stop`` and ``hermes dashboard --stop`` drain
        in-flight work and release their locks. Killing the tree does
        neither, so it is the backstop rather than the mechanism -- but it is
        unconditional, because a stop that hangs would have the Service
        Control Manager kill this process and leave the children running.
        """
        graceful = settings.get("stop_arguments")
        if graceful:
            try:
                subprocess.run(
                    [str(python), "-m", "hermes_cli.main", *graceful],
                    cwd=str(source),
                    env=self._environment(settings, home),
                    timeout=_GRACEFUL_STOP_SECONDS,
                    capture_output=True,
                    creationflags=win32con.CREATE_NO_WINDOW,
                    check=False,
                )
                win32event.WaitForSingleObject(self._child, _GRACEFUL_STOP_SECONDS * 1000)
            except Exception as problem:  # noqa: BLE001 -- we are stopping either way
                servicemanager.LogErrorMsg(
                    f"{self._svc_name_}: graceful stop failed ({problem!r}); killing the tree"
                )
        self._kill_the_tree()

    def _kill_the_tree(self) -> None:
        if self._job is not None:
            win32job.TerminateJobObject(self._job, 0)
            win32api.CloseHandle(self._job)
            self._job = None

    @staticmethod
    def _environment(settings: dict, home: Path) -> dict:
        environment = dict(os.environ)
        # HERMES_HOME is the whole install: config, profiles, skills, state.
        # Set rather than left to default, because the default is the running
        # account's %LOCALAPPDATA% -- for a service account, a directory under
        # C:\Windows nobody would think to look in.
        environment["HERMES_HOME"] = str(home)
        environment["PYTHONUNBUFFERED"] = "1"
        node = settings.get("node_dir")
        if node:
            environment["PATH"] = node + os.pathsep + environment.get("PATH", "")
        environment.update(settings.get("environment", {}))
        return environment


class HermesGatewayService(_HermesProcessService):
    role = "gateway"
    _svc_name_ = "HermesGateway"
    _svc_display_name_ = "Hermes Gateway"
    _svc_description_ = "Hermes: runs the scheduled jobs, the channels and the capture."


class HermesDashboardService(_HermesProcessService):
    role = "dashboard"
    _svc_name_ = "HermesDashboard"
    _svc_display_name_ = "Hermes Dashboard"
    _svc_description_ = "Hermes: the HTTP API and web interface Second Brain reads."


_ROLES = {"gateway": HermesGatewayService, "dashboard": HermesDashboardService}


if __name__ == "__main__":
    # `python hermes_service.py <role> <command>`: the role picks the class,
    # everything after it is pywin32's own command line (install, remove,
    # start, --startup auto). When the Service Control Manager starts a
    # service it does not come through here at all -- pywin32's host process
    # resolves the class from what `install` recorded in the registry.
    if len(sys.argv) < 2 or sys.argv[1] not in _ROLES:
        print(f"usage: {Path(sys.argv[0]).name} [{'|'.join(_ROLES)}] install|remove|start|stop|...")
        raise SystemExit(2)
    win32serviceutil.HandleCommandLine(_ROLES[sys.argv[1]], argv=[sys.argv[0], *sys.argv[2:]])
