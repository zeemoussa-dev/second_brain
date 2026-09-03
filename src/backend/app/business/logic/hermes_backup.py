"""Business-layer wrapper over `tools/hermes_backup.py`/`hermes_restore.py`
(repo-root-level, not under `src/`) -- the real, tested, standalone CLI
pair for a full Hermes structural backup/restore (Agents/Profiles, Cron,
Skills) plus the Second Brain app's own matching data.

Deliberately a subprocess wrapper, not a re-import or a port of that
logic into this module tree -- those two scripts are already real,
scratch-tested, live-verified against this actual machine (see
`MEMORY.md`, 2026-09-03). Calling the exact same tested code path here
means zero risk of this API surface subtly diverging in behaviour from
what was already proven; `app/business/hermes/client.py::HermesCLI`
already establishes the same "shell out to a real, external, independently
correct executable" shape for the real `hermes` CLI itself.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from app.config import settings

_TOOLS_DIR = Path(__file__).resolve().parents[5] / "tools"
_BACKUP_SCRIPT = _TOOLS_DIR / "hermes_backup.py"
_RESTORE_SCRIPT = _TOOLS_DIR / "hermes_restore.py"


class HermesBackupError(Exception):
    """A real, structured failure from either script -- always carries
    the script's own parsed JSON (never a raw stdout/stderr blob) so the
    router can surface exactly what the script itself reported."""

    def __init__(self, detail: dict | str):
        self.detail = detail
        super().__init__(str(detail))


def _hermes_home() -> Path:
    return Path(os.path.expandvars(r"%LOCALAPPDATA%\hermes"))


def create_backup() -> str:
    """Runs the real hermes_backup.py against this machine's own current
    Hermes home and the app's own configured vault. Returns the real
    scratch .sbb path -- the router owns streaming it and cleaning it up
    afterward, same convention `artifact_export.commit_export` already
    established."""
    fd, scratch_path = tempfile.mkstemp(suffix=".sbb", prefix="second-brain-backup-")
    os.close(fd)
    result = subprocess.run(
        [
            sys.executable, str(_BACKUP_SCRIPT),
            "--vault-path", str(settings.vault_path),
            "--hermes-home", str(_hermes_home()),
            "--output", scratch_path,
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        Path(scratch_path).unlink(missing_ok=True)
        raise HermesBackupError(result.stderr.strip() or "hermes_backup.py failed")
    return scratch_path


def restore_backup(archive_path: str, force: bool) -> dict:
    """Runs the real hermes_restore.py against the uploaded archive, this
    machine's own current Hermes home, and the app's own configured
    vault. Returns the script's own real, structured result dict on
    success; raises HermesBackupError (carrying that same structured
    JSON) on a validation refusal or a real mid-restore failure -- never
    a raw traceback, matching the script's own "should say error in
    restore instead of Destroying my self" design (MEMORY.md,
    2026-09-03)."""
    args = [
        sys.executable, str(_RESTORE_SCRIPT),
        "--archive", archive_path,
        "--vault-path", str(settings.vault_path),
        "--hermes-home", str(_hermes_home()),
    ]
    if force:
        args.append("--force")
    result = subprocess.run(args, capture_output=True, text=True)

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise HermesBackupError(result.stderr.strip() or result.stdout.strip() or "hermes_restore.py produced no parseable output")

    if result.returncode != 0 or parsed.get("status") != "ok":
        raise HermesBackupError(parsed)
    return parsed
