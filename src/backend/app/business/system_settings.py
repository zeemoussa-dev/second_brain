"""System settings page (Settings > System, 2026-08-27) -- the five real,
system-wide config values the operator asked to see/edit: Hermes System
URL, Hermes Deployment Folder, App Database Folder (.second-brain), Vault
Location, CORS Allowed Origins. Every value here is read straight from
app.config.settings, never fabricated.

Editing writes to .env and requires a restart to take effect (pydantic
Settings loads once at process start) -- paired with request_shutdown()
for a graceful exit the operator triggers themselves, then restarts
manually. Changing second_brain_data_path is the one edit with a real
side effect beyond .env: the existing folder is actually MOVED to the new
location (operator: "Move the real folder on save... nothing left
behind"), not just repointed, since ~10-12 files across the backend treat
that path as the single source of truth for Second Brain's own state
(registry, chat threads, uploads, email staging).
"""
from __future__ import annotations

import asyncio
import shutil
import signal
from pathlib import Path

import httpx

from app.config import settings

_ENV_PATH = Path(".env")

_FIELDS: dict[str, dict[str, str]] = {
    "hermes_base_url": {
        "label": "Hermes System URL",
        "icon": "cable",
        "description": "Where Second Brain reaches Hermes to send and receive live agent chat.",
        "env_key": "HERMES_BASE_URL",
    },
    "hermes_home_path": {
        "label": "Hermes Deployment Folder",
        "icon": "folder_managed",
        "description": "The folder on this computer where Hermes itself is installed — its profiles, cron jobs, and logs.",
        "env_key": "HERMES_HOME_PATH",
    },
    "second_brain_data_path": {
        "label": "App Database Folder (.second-brain)",
        "icon": "database",
        "description": "Where Second Brain keeps its own data — chat history, registry, uploads. Independent of your vault, so it can live anywhere.",
        "env_key": "SECOND_BRAIN_DATA_PATH",
    },
    "vault_path": {
        "label": "Vault Location",
        "icon": "folder_open",
        "description": "The folder holding your Obsidian vault — the notes Second Brain reads and organizes.",
        "env_key": "VAULT_PATH",
    },
    "cors_allowed_origins": {
        "label": "CORS Allowed Origins",
        "icon": "shield",
        "description": "Which web addresses are allowed to call this backend. Only change this if you're running the app from somewhere other than the default local address.",
        "env_key": "CORS_ALLOWED_ORIGINS",
    },
}


class SystemSettingsError(Exception):
    """A requested change is invalid or unsafe to apply."""


class UnknownFieldError(SystemSettingsError):
    def __init__(self, field: str) -> None:
        super().__init__(f"Unknown field: {field}")


def _current_value(field: str) -> str:
    return str(getattr(settings, field))


def _check_hermes_reachable(url: str) -> dict:
    try:
        response = httpx.get(url.rstrip("/") + "/", timeout=5.0)
        return {"ok": True, "detail": f"Reachable (HTTP {response.status_code})"}
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": f"Unreachable: {exc}"}


def _check_folder(path_str: str, *, must_be_writable: bool = False) -> dict:
    path = Path(path_str)
    if not path.exists():
        return {"ok": False, "detail": "Folder does not exist"}
    if not path.is_dir():
        return {"ok": False, "detail": "Path exists but is not a folder"}
    if must_be_writable:
        probe = path / ".system_settings_write_test"
        try:
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
        except OSError as exc:
            return {"ok": False, "detail": f"Exists but not writable: {exc}"}
    return {"ok": True, "detail": "Exists"}


def _check_cors_origins(value: str) -> dict:
    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    if not origins:
        return {"ok": False, "detail": "No origins configured"}
    bad = [origin for origin in origins if not origin.startswith(("http://", "https://"))]
    if bad:
        return {"ok": False, "detail": f"Not a valid origin: {', '.join(bad)}"}
    return {"ok": True, "detail": f"{len(origins)} origin(s) configured"}


def _run_check(field: str) -> dict:
    value = _current_value(field)
    try:
        if field == "hermes_base_url":
            return _check_hermes_reachable(value)
        if field == "hermes_home_path":
            return _check_folder(value)
        if field == "second_brain_data_path":
            return _check_folder(value, must_be_writable=True)
        if field == "vault_path":
            return _check_folder(value)
        if field == "cors_allowed_origins":
            return _check_cors_origins(value)
    except Exception as exc:  # a broken check must never break the whole page
        return {"ok": False, "detail": f"Check failed: {exc}"}
    raise UnknownFieldError(field)


def get_system_settings() -> dict:
    return {
        "fields": [
            {
                "key": field,
                "label": meta["label"],
                "icon": meta["icon"],
                "description": meta["description"],
                "value": _current_value(field),
                "status": _run_check(field),
            }
            for field, meta in _FIELDS.items()
        ],
    }


def test_field(field: str) -> dict:
    if field not in _FIELDS:
        raise UnknownFieldError(field)
    return _run_check(field)


def _read_env_lines() -> list[str]:
    if not _ENV_PATH.exists():
        return []
    return _ENV_PATH.read_text(encoding="utf-8").splitlines()


def _write_env_updates(updates: dict[str, str]) -> None:
    lines = _read_env_lines()
    seen: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            new_lines.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            new_lines.append(line)
    for key, value in updates.items():
        if key not in seen:
            new_lines.append(f"{key}={value}")
    _ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _move_second_brain_folder(old_path: Path, new_path: Path) -> None:
    old_path = old_path.resolve()
    new_path = new_path.resolve()
    if old_path == new_path:
        return
    if old_path in new_path.parents or new_path in old_path.parents:
        raise SystemSettingsError(
            "The new App Database Folder can't be inside (or contain) the current one."
        )
    if new_path.exists():
        if any(new_path.iterdir()):
            raise SystemSettingsError(f"{new_path} already exists and is not empty — refusing to overwrite it.")
        new_path.rmdir()  # confirmed empty above -- safe, lets shutil.move rename cleanly onto it
    new_path.parent.mkdir(parents=True, exist_ok=True)
    if old_path.exists():
        shutil.move(str(old_path), str(new_path))
        if old_path.exists() or not new_path.exists():
            raise SystemSettingsError(
                "Move verification failed — check both folders by hand before retrying."
            )
    else:
        new_path.mkdir(parents=True, exist_ok=True)


def update_system_settings(patch: dict[str, str]) -> dict:
    unknown = set(patch) - set(_FIELDS)
    if unknown:
        raise SystemSettingsError(f"Unknown field(s): {', '.join(sorted(unknown))}")

    if "second_brain_data_path" in patch:
        _move_second_brain_folder(settings.second_brain_data_path, Path(patch["second_brain_data_path"]))

    _write_env_updates({_FIELDS[field]["env_key"]: value for field, value in patch.items()})
    return {"ok": True, "restart_required": True}


async def _delayed_shutdown() -> None:
    await asyncio.sleep(0.3)
    # os.kill(pid, SIGTERM) on Windows calls TerminateProcess() directly and
    # does NOT invoke any registered Python signal handler (a real CPython/
    # Windows gap) -- signal.raise_signal() properly triggers uvicorn's own
    # installed SIGTERM handler in-process on every platform, giving a real
    # graceful shutdown instead of an abrupt kill.
    signal.raise_signal(signal.SIGTERM)


def request_shutdown() -> None:
    asyncio.create_task(_delayed_shutdown())
