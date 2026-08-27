"""Subprocess wrapper for Hermes' own CLI binary (`hermes.exe`) -- the
only real way to reach some Hermes operations (profile create/delete,
which do more than a plain mkdir: cloning copies config.yaml/.env/SOUL.md/
skills; gateway/dashboard process control). Anything with no CLI
equivalent (SOUL.md content, this app's own custom SKILL.md files) is
direct file I/O instead, over in profiles.py/skills.py -- never guessed
or half-reimplemented here.

Real command surface (confirmed live against this machine's own
install, `hermes <command> --help`):
    hermes profile {create, delete, describe, list, show, ...}
    hermes gateway {start, stop, restart, status, setup, ...}
    hermes dashboard [--port] [--host] [--no-open] [--stop] [--status]
    hermes status [--deep]
    hermes cron {run, ...}
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from app.hermes.config import HermesConfig


class HermesCLI:
    def __init__(self, config: HermesConfig) -> None:
        self._config = config

    def _hermes_exe(self) -> Path | None:
        exe = self._config.home_path / "hermes-agent" / "bin" / "hermes.exe"
        return exe if exe.is_file() else None

    def _run(self, args: list[str], timeout: float = 30.0) -> tuple[bool, str]:
        """Runs to completion and captures output -- for commands whose
        real result the caller needs (profile create/delete/describe,
        status). Returns (success, stdout-or-stderr text); never raises
        -- a missing install or a timeout is a real, ordinary failure
        mode here, not exceptional."""
        exe = self._hermes_exe()
        if exe is None:
            return False, "No real Hermes install found at the configured home path"
        try:
            result = subprocess.run(
                [str(exe), *args], capture_output=True, timeout=timeout,
                # Hermes' own CLI output is real UTF-8 (checkmarks, box-
                # drawing characters) -- `text=True` alone decodes with
                # Windows' console codepage (cp1252 here), which crashes
                # a reader thread on the first non-Latin-1 byte and
                # silently loses the captured output. Explicit UTF-8,
                # `errors="replace"` so a genuinely unexpected byte
                # degrades to a replacement character instead of losing
                # the whole capture.
                encoding="utf-8", errors="replace",
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, str(exc)
        output = (result.stdout or result.stderr or "").strip()
        return result.returncode == 0, output

    def _run_background(self, args: list[str]) -> bool:
        """Fire-and-forget -- for long-running or already-async commands
        (a cron job's own real run, a gateway/dashboard server process)
        where the caller must never block on it finishing."""
        exe = self._hermes_exe()
        if exe is None:
            return False
        try:
            subprocess.Popen(
                [str(exe), *args], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except OSError:
            return False
        return True

    # -- Cron --------------------------------------------------------
    def run_cron_job(self, job_name: str) -> bool:
        return self._run_background(["cron", "run", job_name])

    # -- Profiles (create/delete/describe do more than a file write --
    # --clone copies config.yaml/.env/SOUL.md/skills too) -------------
    def create_profile(
        self, name: str, *, clone: bool = False, clone_all: bool = False,
        clone_from: str | None = None, no_alias: bool = False,
        no_skills: bool = False, description: str | None = None,
    ) -> tuple[bool, str]:
        args = ["profile", "create", name]
        if clone:
            args.append("--clone")
        if clone_all:
            args.append("--clone-all")
        if clone_from:
            args += ["--clone-from", clone_from]
        if no_alias:
            args.append("--no-alias")
        if no_skills:
            args.append("--no-skills")
        if description:
            args += ["--description", description]
        # --clone/--clone-all can copy a real skills/ bundle -- generous
        # timeout over the default.
        return self._run(args, timeout=120.0)

    def delete_profile(self, name: str) -> tuple[bool, str]:
        return self._run(["profile", "delete", name, "-y"])

    def describe_profile(
        self, name: str, *, text: str | None = None, auto: bool = False, overwrite: bool = False,
    ) -> tuple[bool, str]:
        args = ["profile", "describe", name]
        if text is not None:
            args += ["--text", text]
        if auto:
            args.append("--auto")
        if overwrite:
            args.append("--overwrite")
        return self._run(args)

    # -- Gateway (messaging platforms: WhatsApp, Telegram, ...) -------
    def start_gateway(self) -> tuple[bool, str]:
        return self._run(["gateway", "start"], timeout=60.0)

    def stop_gateway(self) -> tuple[bool, str]:
        return self._run(["gateway", "stop"])

    def restart_gateway(self) -> tuple[bool, str]:
        return self._run(["gateway", "restart"], timeout=60.0)

    def gateway_status(self, *, deep: bool = False) -> tuple[bool, str]:
        args = ["gateway", "status"]
        if deep:
            args.append("--deep")
        return self._run(args, timeout=60.0)

    def configure_gateway(self) -> bool:
        """`gateway setup` is an INTERACTIVE wizard (platform pairing,
        e.g. a real WhatsApp QR-code scan) -- there is no headless
        "just configure it" flag. Fired as a detached background
        process for a human to attach to via a real terminal, matching
        this codebase's own established "platform pairing needs a
        human" precedent (MEMORY.md). Never awaited/captured -- an
        interactive wizard has no meaningful captured-output result."""
        return self._run_background(["gateway", "setup"])

    # -- Dashboard (web UI) --------------------------------------------
    def start_dashboard(self, *, port: int | None = None, host: str | None = None, no_open: bool = True) -> bool:
        args = ["dashboard"]
        if port is not None:
            args += ["--port", str(port)]
        if host is not None:
            args += ["--host", host]
        if no_open:
            args.append("--no-open")
        return self._run_background(args)

    def stop_dashboard(self) -> tuple[bool, str]:
        return self._run(["dashboard", "--stop"])

    def dashboard_status(self) -> tuple[bool, str]:
        return self._run(["dashboard", "--status"])

    # -- System health --------------------------------------------------
    def get_system_status(self, *, deep: bool = False) -> tuple[bool, str]:
        """`hermes status` -- a human-readable component health dump,
        distinct from HermesRestAPI.get_status()'s structured JSON (that
        one needs `hermes serve`/the gateway actually running; this one
        works even when nothing is running yet)."""
        args = ["status"]
        if deep:
            args.append("--deep")
        return self._run(args, timeout=60.0)
