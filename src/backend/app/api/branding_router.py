"""This install's name and logo (operator, 2026-10-21).

**Reading is public; writing needs an Admin.** The sign-in screen
renders the name and the logo, so a caller who cannot read branding
cannot be shown the door they are meant to come through. `GET /branding`
and `GET /branding/logo` are therefore in `auth_guard`'s public list,
and they are deliberately the only two things an anonymous caller learns
about this install -- a name and a picture the operator chose to show.

Writing goes through `MANAGE_SETTINGS`, which is Admin-only: the app's
name and logo are what everyone else sees, and changing them is closer
to changing a setting than to editing your own profile.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.api.auth_guard import requires
from app.business.core.branding.branding_manager import (
    FONT_CHOICES,
    MAX_LOGO_BYTES,
    THEME_MODES,
    BrandingError,
    BrandingManager,
)
from app.business.core.users.user import Capability

router = APIRouter(prefix="/branding", tags=["branding"])

_admin_only = Depends(requires(Capability.MANAGE_SETTINGS))


class AppNameBody(BaseModel):
    app_name: str


class ThemeBody(BaseModel):
    """All three optional: the page saves one control at a time, and a body
    carrying every field would let a stale form put back what another admin
    just changed."""

    theme_mode: str | None = None
    font: str | None = None
    accent_color: str | None = None


def _as_dict(manager: BrandingManager) -> dict:
    branding = manager.get()
    return {
        "app_name": branding.app_name,
        "has_logo": branding.has_logo,
        "is_customised": branding.is_customised,
        "max_logo_bytes": MAX_LOGO_BYTES,
        "theme_mode": branding.theme_mode,
        "font": branding.font,
        "accent_color": branding.accent_color,
        # What the picker may offer, from the one place that decides it, so a
        # fourth font is a backend change and not two.
        "theme_modes": list(THEME_MODES),
        "fonts": list(FONT_CHOICES),
    }


@router.get("")
def read_branding() -> dict:
    """Public. `is_customised` is separate from `app_name` so the UI can
    tell "this install chose to be called Second Brain" from "this
    install never chose" -- which matters only if the product is ever
    renamed, and costs one boolean to keep honest."""
    return _as_dict(BrandingManager())


@router.get("/logo")
def read_logo():
    """Public, and 404 when there is none -- the frontend asks for it
    unconditionally and renders the name alone if it is absent, so an
    install with no logo must answer "no logo", not an error page."""
    found = BrandingManager().logo_file()
    if found is None:
        raise HTTPException(status_code=404, detail="This install has no logo set.")
    path, content_type = found
    return FileResponse(path, media_type=content_type)


@router.put("", dependencies=[_admin_only])
def set_app_name(body: AppNameBody) -> dict:
    """An empty name resets to the product's own. That is the only way
    back from a rename, so it is accepted rather than refused."""
    manager = BrandingManager()
    try:
        manager.set_app_name(body.app_name)
    except BrandingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _as_dict(manager)


@router.put("/theme", dependencies=[_admin_only])
def set_theme(body: ThemeBody) -> dict:
    """Admin-only, like the name: a theme is what everyone on this install
    sees, not a personal preference (operator's own choice, 2026-10-24)."""
    manager = BrandingManager()
    try:
        manager.set_theme(
            theme_mode=body.theme_mode,
            font=body.font,
            accent_color=body.accent_color,
        )
    except BrandingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _as_dict(manager)


@router.post("/logo", dependencies=[_admin_only])
async def set_logo(file: UploadFile = File(...)) -> dict:
    manager = BrandingManager()
    try:
        manager.set_logo(file.filename or "", await file.read())
    except BrandingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _as_dict(manager)


@router.delete("/logo", dependencies=[_admin_only])
def clear_logo() -> dict:
    manager = BrandingManager()
    manager.clear_logo()
    return _as_dict(manager)
