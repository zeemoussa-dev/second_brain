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

from app.config import REQUIRED_FOR_STARTUP, settings

_ENV_PATH = Path(".env")

# What the UI shows in place of a real secret. A GET never returns the real
# credential, so the wizard/Settings page can round-trip a field it did not
# change -- update_system_settings() drops any incoming value equal to this
# sentinel rather than writing the mask itself over a working key.
SECRET_MASK = "•" * 12

_FIELDS: dict[str, dict[str, str]] = {
    "vault_path": {
        "label": "Vault Location",
        "icon": "folder_open",
        "description": "The folder holding your Obsidian vault — the notes Second Brain reads and organizes.",
        "env_key": "VAULT_PATH",
    },
    "self_email": {
        "label": "Your Email Address",
        "icon": "alternate_email",
        "description": "Your own work email. Second Brain uses it to tell your own messages apart from everyone else's when it reads a thread.",
        "env_key": "SELF_EMAIL",
    },
    "compass_base_url": {
        "label": "Compass API URL",
        "icon": "api",
        "description": "The FULL chat-completions endpoint, ending in /chat/completions — Second Brain posts to this URL exactly as given. (Hermes' own config wants the opposite: a base URL WITHOUT that suffix, because Hermes appends it itself.)",
        "env_key": "COMPASS_BASE_URL",
    },
    "compass_api_key": {
        "label": "Compass API Key",
        "icon": "key",
        "description": "Your Compass credential. Stored in .env on this machine and never shown again after you save it.",
        "env_key": "COMPASS_API_KEY",
        "secret": True,
    },
    "compass_model": {
        "label": "Compass Model",
        "icon": "smart_toy",
        "description": "Which model Compass should serve, e.g. gpt-5.",
        "env_key": "COMPASS_MODEL",
    },
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
    """The real, unmasked value. `vault_path`/`second_brain_data_path` are
    `Path | None` before setup has run -- `str(None)` would hand the UI the
    literal string "None" and every folder check would then report that a
    folder named "None" is missing, which reads as a broken path rather than
    an unconfigured one."""
    value = getattr(settings, field)
    return "" if value is None else str(value)


def _display_value(field: str) -> str:
    """What a GET is allowed to return. A configured secret comes back as
    SECRET_MASK; an unconfigured one comes back empty, so the wizard can tell
    "already set, leave it alone" apart from "still needs a value"."""
    value = _current_value(field)
    if _FIELDS[field].get("secret") and value:
        return SECRET_MASK
    return value


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


def _check_email(value: str) -> dict:
    # Deliberately shape-only: the real proof an address is right is that
    # thread attribution starts working, which no check here can establish.
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        return {"ok": False, "detail": "Doesn't look like an email address"}
    return {"ok": True, "detail": "Looks like an email address"}


def _check_compass_url(value: str) -> dict:
    if not value.startswith(("http://", "https://")):
        return {"ok": False, "detail": "Must start with http:// or https://"}
    # data_access/compass_client.py POSTs to this URL verbatim -- it appends
    # nothing. A base URL that stops short of the endpoint yields a 404 at
    # first real use, long after setup, so catch it here instead.
    if not value.rstrip("/").endswith("/chat/completions"):
        return {
            "ok": False,
            "detail": "Should end in /chat/completions — Second Brain posts to this URL exactly as given",
        }
    return {"ok": True, "detail": "Well-formed chat-completions URL"}


def _check_present(value: str, *, noun: str) -> dict:
    if not value.strip():
        return {"ok": False, "detail": f"No {noun} set"}
    return {"ok": True, "detail": "Set"}


def _check_cors_origins(value: str) -> dict:
    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    if not origins:
        return {"ok": False, "detail": "No origins configured"}
    bad = [origin for origin in origins if not origin.startswith(("http://", "https://"))]
    if bad:
        return {"ok": False, "detail": f"Not a valid origin: {', '.join(bad)}"}
    return {"ok": True, "detail": f"{len(origins)} origin(s) configured"}


def _run_check(field: str, value: str | None = None) -> dict:
    """Checks `value` if given (an unsaved candidate the wizard is offering),
    otherwise whatever is configured right now."""
    if value is None:
        value = _current_value(field)
    try:
        if field == "self_email":
            return _check_email(value)
        if field == "compass_base_url":
            return _check_compass_url(value)
        if field == "compass_api_key":
            return _check_present(value, noun="API key")
        if field == "compass_model":
            return _check_present(value, noun="model")
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
                "value": _display_value(field),
                "secret": bool(meta.get("secret")),
                "required": field in REQUIRED_FOR_STARTUP,
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
    """An empty value REMOVES its line rather than writing a bare `KEY=`.

    Writing `KEY=` is actively harmful for the two Path settings: pydantic
    parses "" into `Path(".")`, not `None`, so an empty
    SECOND_BRAIN_DATA_PATH silently makes the app's data folder whatever
    directory the backend was started from -- and the validator that would
    otherwise default it to <vault>/.second-brain never runs, because the
    field is no longer None. Verified live 2026-09-04.
    """
    write_env_updates_to(_ENV_PATH, updates)


def write_env_updates_to(env_path: Path, updates: dict[str, str]) -> None:
    """The same merge against any .env file -- shared with the Hermes vault
    sync so both preserve comments, blank lines, and key order identically."""
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.is_file() else []
    seen: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            seen.add(key)
            if updates[key] != "":
                new_lines.append(f"{key}={updates[key]}")
            continue
        new_lines.append(line)
    for key, value in updates.items():
        if key not in seen and value != "":
            new_lines.append(f"{key}={value}")
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


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


def validate_candidate(field: str, value: str) -> dict:
    """Runs a field's own real check against a value that has NOT been saved
    yet -- what the wizard calls before letting the operator move on, so a
    wrong path or a base URL missing /chat/completions is caught while it is
    still one keystroke from being fixed."""
    if field not in _FIELDS:
        raise UnknownFieldError(field)
    return _run_check(field, value)


def test_compass_connection(base_url: str, api_key: str, model: str) -> dict:
    """One real, minimal chat completion against the candidate Compass
    credentials. The per-field checks above only establish shape; this is the
    only thing that proves the three values work TOGETHER, which is exactly
    the failure the operator would otherwise not discover until first use.

    Deliberately does not go through `data_access/compass_client.py`: that
    module reads the SAVED `settings`, and the whole point here is to try
    values that are not saved yet."""
    if not (base_url and api_key and model):
        return {"ok": False, "detail": "Fill in the URL, key, and model first"}

    # Retried ONCE, and only for a connect-level failure. On this corporate
    # network the first request over a cold connection is reliably killed by
    # the TLS-inspecting middlebox ("[WinError 10054] forcibly closed"),
    # while the immediate retry succeeds -- verified live 2026-09-04: attempt
    # 1 reset, attempts 2 and 3 both HTTP 200 with identical credentials.
    # Without this the wizard shows a red "could not reach Compass" for
    # perfectly correct settings, which is exactly the wrong thing to tell
    # someone who is trying to work out whether they typed their key right.
    # An HTTP-level failure (401/404/400) is NEVER retried -- that is a real
    # answer from the server, not a transport hiccup.
    response = None
    for attempt in (1, 2):
        try:
            response = httpx.post(
                base_url,
                json={"model": model, "messages": [{"role": "user", "content": "ping"}]},
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                timeout=20.0,
            )
            break
        except httpx.HTTPError as exc:
            if attempt == 2:
                return {"ok": False, "detail": f"Could not reach Compass: {exc}"}
    if response.status_code == 404:
        return {"ok": False, "detail": "HTTP 404 -- check the URL ends in /chat/completions"}
    if response.status_code >= 400:
        # Compass answers a bad credential with 400 + an OpenAI-shaped error
        # body, not the 401 the shape would suggest (verified live
        # 2026-09-04). Surfacing its own message beats echoing raw JSON at
        # someone who is trying to work out what they mistyped.
        message = _error_message(response)
        if "api key" in message.lower():
            return {"ok": False, "detail": f"{message.rstrip('.')} -- check the key"}
        return {"ok": False, "detail": f"HTTP {response.status_code}: {message}"}
    try:
        response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        return {"ok": False, "detail": f"Replied, but not in the expected shape: {exc}"}
    return {"ok": True, "detail": f"Compass answered as {model}"}


def _error_message(response: httpx.Response) -> str:
    """The server's own message out of an OpenAI-shaped error body, falling
    back to the raw text when it isn't that shape."""
    try:
        body = response.json()
        message = body["error"]["message"]
    except (KeyError, TypeError, ValueError):
        return response.text[:200]
    return message if isinstance(message, str) else response.text[:200]


def update_system_settings(patch: dict[str, str]) -> dict:
    unknown = set(patch) - set(_FIELDS)
    if unknown:
        raise SystemSettingsError(f"Unknown field(s): {', '.join(sorted(unknown))}")

    # A GET hands back SECRET_MASK in place of a configured secret, so a UI
    # that submits a whole form round-trips the mask for any secret the
    # operator did not touch. Writing that through would destroy a working
    # credential and replace it with bullet characters.
    patch = {field: value for field, value in patch.items() if value != SECRET_MASK}
    if not patch:
        return {"ok": True, "restart_required": False}

    if "second_brain_data_path" in patch:
        # None on a fresh install: there is no existing folder to move, so the
        # new location is simply created by the move helper's own else-branch.
        current = settings.second_brain_data_path
        _move_second_brain_folder(
            current if current is not None else Path(patch["second_brain_data_path"]),
            Path(patch["second_brain_data_path"]),
        )

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
