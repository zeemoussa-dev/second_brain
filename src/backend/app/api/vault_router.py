import os
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.business.core.vault.vault import Vault
from app.business.core.vault.vault_manager import DuplicateEntityError, EntityNotFoundError, VaultManager
from app.business.logic import vault_export

router = APIRouter(prefix="/vault")
_vault_manager = VaultManager()


@router.get("/overview")
def get_overview() -> Vault:
    return _vault_manager.get_overview()


@router.get("/index-config")
def get_index_config() -> dict:
    return _vault_manager.get_index_config()


class UpdateIndexConfigBody(BaseModel):
    included: bool


@router.patch("/index-config/{folder_name}")
def update_index_config(folder_name: str, body: UpdateIndexConfigBody) -> dict:
    return _vault_manager.set_folder_included(folder_name, body.included)


@router.get("/templates")
def list_templates() -> dict:
    return {"templates": _vault_manager.list_templates()}


@router.get("/export-data/tree")
def get_export_data_tree() -> dict:
    return _vault_manager.get_export_tree()


class ExportDataExportBody(BaseModel):
    selection: list[str]
    extraction: Literal["flat", "hierarchy"]


@router.post("/export-data/export")
def export_data_export(body: ExportDataExportBody, background_tasks: BackgroundTasks) -> FileResponse:
    scratch_sbd_path = vault_export.build_export(body.selection, body.extraction)
    # Scratch temp .sbd cleaned up after the response is fully sent --
    # same "clean up scratch temp output after streaming" mechanism
    # REQ-SB-85-US-02-T04's own /commit route already established.
    background_tasks.add_task(os.remove, scratch_sbd_path)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return FileResponse(
        scratch_sbd_path,
        media_type="application/octet-stream",
        filename=f"second-brain-vault-export-{timestamp}.sbd",
        background=background_tasks,
    )


@router.get("/entities")
def list_entities() -> dict:
    return {"entities": _vault_manager.list_entities()}


class CreateEntityBody(BaseModel):
    name: str
    section: str
    domain: str = ""
    aliases: str = ""
    affiliate_of: str = ""


@router.post("/entities")
def create_entity(body: CreateEntityBody) -> dict:
    try:
        return _vault_manager.create_entity(body.name, body.section, body.domain, body.aliases, body.affiliate_of)
    except DuplicateEntityError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


class UpdateEntityBody(BaseModel):
    name: str | None = None
    section: str | None = None
    aliases: str | None = None
    affiliate_of: str | None = None
    domain: str | None = None
    ignore: bool | None = None


@router.patch("/entities/{name}")
def update_entity(name: str, body: UpdateEntityBody) -> dict:
    try:
        return _vault_manager.update_entity(name, body.model_dump(exclude_none=True))
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except DuplicateEntityError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete("/entities/{name}")
def delete_entity(name: str) -> dict:
    try:
        _vault_manager.delete_entity(name)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"deleted": True}
