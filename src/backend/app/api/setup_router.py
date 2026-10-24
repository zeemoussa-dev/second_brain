"""First-run setup wizard API (`REQ-SB-89`).

Every route here must stay reachable while the app is in setup mode -- this
is the one router whose whole job is to fix the configuration that put it
there, so `main.py`'s own setup-mode gate exempts this prefix explicitly.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business import setup_wizard, system_settings

router = APIRouter(prefix="/setup")


@router.get("/status")
def get_status() -> dict:
    return setup_wizard.get_setup_status()


@router.get("/hermes-health")
def get_hermes_health(vault_path: str = "") -> dict:
    """`vault_path` is the value currently typed into the wizard, so the
    vault-agreement row reflects what the operator is about to save rather
    than the (still empty, on a fresh install) saved setting."""
    return setup_wizard.get_hermes_health(vault_path)


class ValidateFieldBody(BaseModel):
    field: str
    value: str


@router.post("/validate")
def validate_field(body: ValidateFieldBody) -> dict:
    """Checks a value the operator has typed but NOT saved, so a wrong folder
    or a URL missing /chat/completions surfaces while it is still one
    keystroke from being fixed."""
    try:
        return system_settings.validate_candidate(body.field, body.value)
    except system_settings.UnknownFieldError:
        raise HTTPException(status_code=404, detail=f"Unknown field: {body.field}")


class TestCompassBody(BaseModel):
    compass_base_url: str
    compass_api_key: str
    compass_model: str


@router.post("/test-compass")
def test_compass(body: TestCompassBody) -> dict:
    """One real chat completion against the candidate credentials -- the only
    check that proves the three values work together."""
    return system_settings.test_compass_connection(
        body.compass_base_url, body.compass_api_key, body.compass_model
    )


class SaveSetupBody(BaseModel):
    values: dict[str, str]


@router.post("/save")
def save(body: SaveSetupBody) -> dict:
    """Writes the collected values to .env. A restart is always needed for
    them to take effect -- pydantic Settings loads once per process -- so the
    response says so and the UI offers `/setup/restart` next.

    Also mirrors the vault path and the App Database Folder into Hermes' own
    `.env` (`OBSIDIAN_VAULT_PATH` / `SECOND_BRAIN_DATA_PATH`, operator-
    directed 2026-09-04), so the agents and the app agree on where both live. Reported back as its own result
    rather than folded into `ok`: the app's own settings ARE saved even if
    Hermes isn't installed, and the UI should say exactly that instead of
    presenting the whole save as failed."""
    try:
        result = system_settings.update_system_settings(body.values)
    except system_settings.SystemSettingsError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    vault_path = body.values.get("vault_path", "")
    result["hermes_vault_sync"] = (
        setup_wizard.sync_settings_to_hermes(
            vault_path,
            body.values.get('second_brain_data_path', ''),
            body.values.get('self_email', ''),
        )
        if vault_path
        else {"ok": False, "detail": "No vault path in this save — Hermes left untouched", "files_written": 0}
    )
    return result


@router.post("/restart")
def restart() -> dict:
    """Graceful shutdown, then the launcher starts the app again -- reading the
    .env just written, which is the only way those values take effect.

    Not the same call as Settings > System's Shut down: that one is meant to
    leave the app down, this one must bring it back, and nothing supervises the
    backend by itself (see `request_restart`).

    `restarting` is false when this install has no launcher to restart through:
    the app still stops, but someone has to start it, and the UI should say
    that rather than wait for a return that is not coming."""
    restarting = system_settings.can_restart_itself()
    system_settings.request_restart()
    return {"ok": True, "restarting": restarting}
