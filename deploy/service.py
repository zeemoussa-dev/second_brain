"""Second Brain as a Windows service (production, 2026-10-28).

Registered with `sc.exe` and started by Windows at boot, so the app survives a
reboot and nobody has to sign in to the server for it to be up.

**Why a Python service and not a wrapper.** `sc.exe create` pointing at
`uvicorn.exe` produces a service that starts and is immediately killed:
Windows expects the process to answer the Service Control Manager within
30 seconds, and uvicorn does not speak that protocol. The usual answer is a
third-party wrapper (NSSM), which would be one more unsigned binary to get
through a change board and onto an offline server. `pywin32` is already a
dependency of this app, so the service is a dozen lines of our own code and
nothing new arrives.

**Everything it needs is in one file beside it**, `service.json`, written by
the installer. The service runs as a machine account with no profile, no
PATH of ours and no working directory we chose, so nothing may be inferred
from the environment -- the paths are read, not guessed.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import threading
from pathlib import Path

import servicemanager
import win32event
import win32service
import win32serviceutil

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "service.json"


def _settings() -> dict:
    """What the installer wrote. A missing or unreadable file is fatal and
    said so in the event log: a service that starts with invented defaults is
    worse than one that refuses to start."""
    return json.loads(CONFIG.read_text(encoding="utf-8"))


class SecondBrainService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SecondBrain"
    _svc_display_name_ = "Second Brain"
    _svc_description_ = (
        "Second Brain: the knowledge base and its web interface, served on one port."
    )

    def __init__(self, args) -> None:
        super().__init__(args)
        self._stop_event = win32event.CreateEvent(None, 0, 0, None)
        self._server = None
        socket.setdefaulttimeout(60)

    def SvcStop(self) -> None:
        """Asks uvicorn to stop and lets it finish in-flight requests.

        `should_exit` is uvicorn's own cooperative shutdown. The service also
        reports STOP_PENDING first, so Windows waits instead of killing the
        process while a request is still being written.
        """
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self._server is not None:
            self._server.should_exit = True
        win32event.SetEvent(self._stop_event)

    def SvcDoRun(self) -> None:
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )
        try:
            self._serve()
        except Exception as problem:  # noqa: BLE001 -- the event log is the only reader
            servicemanager.LogErrorMsg(f"Second Brain could not start: {problem!r}")
            raise

    def _serve(self) -> None:
        settings = _settings()
        backend = Path(settings["backend_dir"])

        # The app is imported from the backend folder, which is NOT on the
        # service's path: a service starts in C:\Windows\system32 with the
        # machine's environment, not a developer's shell.
        os.chdir(backend)
        sys.path.insert(0, str(backend))

        import uvicorn  # imported here: it lives in the venv this service runs under

        options = {
            "host": settings.get("host", "0.0.0.0"),
            "port": int(settings.get("port", 443)),
            # Never --reload in a service: it runs the app in a child process
            # that the Service Control Manager knows nothing about, and
            # stopping the service would leave it running.
            "log_config": None,
            "timeout_graceful_shutdown": 15,
        }
        certificate = settings.get("ssl_certfile")
        key = settings.get("ssl_keyfile")
        if certificate and key:
            options["ssl_certfile"] = certificate
            options["ssl_keyfile"] = key

        config = uvicorn.Config("app.main:app", **options)
        self._server = uvicorn.Server(config)

        # uvicorn installs signal handlers, which only the main thread may do
        # and which mean nothing to a service: Windows stops us through
        # SvcStop above, not through SIGINT.
        self._server.install_signal_handlers = lambda: None

        runner = threading.Thread(target=self._server.run, name="uvicorn", daemon=True)
        runner.start()
        win32event.WaitForSingleObject(self._stop_event, win32event.INFINITE)
        runner.join(timeout=30)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SecondBrainService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(SecondBrainService)
