"""Artifact inventory HTTP surface (REQ-SB-85-US-01) -- the same flat,
single-purpose-router, thin-wrapper convention every other entity uses
(`pipelines_router.py`/`sections_router.py`/`system_health_router.py`).

The export sub-routes (`REQ-SB-85-US-02-T04`, `ADR-013`) are a real,
disclosed two-phase preview/commit split rather than one dual-mode `POST
/artifacts/export` (see the parent story's own Notes, "Decomposer
pass") -- `/preview` resolves the dependency closure and runs the secret
scan, writing nothing; `/commit` re-resolves/re-scans fresh and is the
ONLY request in this whole subsystem that ever writes a real file."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.business.logic import artifact_export, artifact_import, artifacts_inventory
from app.business.logic.artifact_secret_scan import SecretScanCancelledError, SecretScanIncompleteError
from app.business.logic.sbf_archive import MalformedBundleError

router = APIRouter(prefix="/artifacts")


@router.get("")
def list_artifacts() -> list[dict]:
    # Recomputed fresh on every call -- list_all_artifacts() has no
    # caching of its own (matches system_health.py's own convention).
    return artifacts_inventory.list_all_artifacts()


class ExportPreviewBody(BaseModel):
    selection: list[dict]


class ExportCommitBody(BaseModel):
    selection: list[dict]
    secret_decisions: dict[str, str] = {}


@router.post("/export/preview")
def preview_export(body: ExportPreviewBody) -> dict:
    return artifact_export.preview_export(body.selection)


@router.post("/export/commit")
def commit_export(body: ExportCommitBody, background_tasks: BackgroundTasks) -> FileResponse:
    try:
        scratch_sbf_path = artifact_export.commit_export(body.selection, body.secret_decisions)
    except SecretScanCancelledError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except SecretScanIncompleteError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    # Scratch temp .sbf cleaned up after the response is fully sent --
    # never left on disk once the client has the bytes (or the send
    # fails partway through).
    background_tasks.add_task(os.remove, scratch_sbf_path)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return FileResponse(
        scratch_sbf_path,
        media_type="application/octet-stream",
        filename=f"second-brain-export-{timestamp}.sbf",
        background=background_tasks,
    )


async def _scratch_sbf_from_upload(file: UploadFile) -> str:
    """Writes an uploaded `.sbf` to a scratch temp path -- `read_archive`
    (`T01`) needs a real filesystem path, not an in-memory stream."""
    fd, scratch_path = tempfile.mkstemp(suffix=".sbf", prefix="second-brain-import-")
    os.close(fd)
    Path(scratch_path).write_bytes(await file.read())
    return scratch_path


@router.post("/import/preview")
async def preview_import(file: UploadFile = File(...)) -> dict:
    scratch_path = await _scratch_sbf_from_upload(file)
    try:
        return artifact_import.preview_import(scratch_path)
    except MalformedBundleError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        os.remove(scratch_path)


@router.post("/import/commit")
async def commit_import(
    file: UploadFile = File(...),
    decisions: str = Form("{}"),
    skill_target_profiles: str = Form("{}"),
) -> list[dict]:
    scratch_path = await _scratch_sbf_from_upload(file)
    try:
        return artifact_import.commit_import(
            scratch_path, json.loads(decisions), json.loads(skill_target_profiles),
        )
    except MalformedBundleError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        os.remove(scratch_path)
