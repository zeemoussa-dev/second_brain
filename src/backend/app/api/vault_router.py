import os
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.business.core.vault.vault import Vault
from app.business.core.vault.vault_manager import VaultManager
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


@router.get("/templates/{template_id}")
def get_template(template_id: str) -> dict:
    try:
        data = _vault_manager.get_template_json(template_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Template.json does not parse: {exc}") from exc
    if data is None:
        raise HTTPException(status_code=404, detail=f"no Template {template_id!r} on this install")
    return {"id": template_id, "json": data}


class UpdateTemplateBody(BaseModel):
    json_data: dict = Field(alias="json")


@router.put("/templates/{template_id}")
def update_template(template_id: str, body: UpdateTemplateBody) -> dict:
    try:
        template = _vault_manager.update_template(template_id, body.json_data)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"id": template_id, "json": _vault_manager.get_template_json(template_id), "template": template}


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
