"""Marketplace HTTP surface -- Settings > Marketplace (`ADR-022`).

`preflight` never changes anything, so the page can show what installing
would do, and what would stop it, before the operator commits. `install`
re-runs preflight itself and refuses on failure. Both install and uninstall
answer `restart_required`: a plugin's backend is loaded at startup.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.business.core.marketplace.marketplace_manager import MarketplaceManager

router = APIRouter(prefix="/marketplace")
_manager = MarketplaceManager()


@router.get("")
def list_marketplace() -> list[dict]:
    return _manager.get_all()


@router.get("/{plugin_id}/{version}/preflight")
def preflight(plugin_id: str, version: str) -> dict:
    """404 only for a package that was never published; one that exists but
    cannot be installed is a 200 carrying `ok: false` and its `problems`."""
    if not _manager.has_package(plugin_id, version):
        raise HTTPException(status_code=404, detail=f"no published package {plugin_id} {version}")
    return _manager.preflight(plugin_id, version)


@router.post("/{plugin_id}/{version}/install")
def install(plugin_id: str, version: str) -> dict:
    if not _manager.has_package(plugin_id, version):
        raise HTTPException(status_code=404, detail=f"no published package {plugin_id} {version}")
    result = _manager.install(plugin_id, version)
    if not result["installed"]:
        raise HTTPException(status_code=409, detail=result)
    return result


@router.post("/{plugin_id}/uninstall")
def uninstall(plugin_id: str) -> dict:
    if not _manager.is_installed(plugin_id):
        raise HTTPException(status_code=404, detail=f"{plugin_id} is not installed")
    return _manager.uninstall(plugin_id)
