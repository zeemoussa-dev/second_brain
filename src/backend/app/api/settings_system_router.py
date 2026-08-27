from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business import system_settings

router = APIRouter(prefix="/settings/system")


@router.get("")
def get_settings() -> dict:
    return system_settings.get_system_settings()


@router.post("/test/{field}")
def test_field(field: str) -> dict:
    try:
        return system_settings.test_field(field)
    except system_settings.UnknownFieldError:
        raise HTTPException(status_code=404, detail=f"Unknown field: {field}")


class UpdateSystemSettingsBody(BaseModel):
    hermes_base_url: str | None = None
    hermes_home_path: str | None = None
    second_brain_data_path: str | None = None
    vault_path: str | None = None
    cors_allowed_origins: str | None = None


@router.put("")
def update_settings(body: UpdateSystemSettingsBody) -> dict:
    try:
        return system_settings.update_system_settings(body.model_dump(exclude_none=True))
    except system_settings.SystemSettingsError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/shutdown")
def shutdown() -> dict:
    system_settings.request_shutdown()
    return {"ok": True}
