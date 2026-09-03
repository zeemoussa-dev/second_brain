"""Backup/Restore HTTP surface -- the same flat, single-purpose-router,
thin-wrapper convention every other entity uses (`artifacts_router.py`/
`pipelines_router.py`). Business logic (`app/business/logic/
hermes_backup.py`) shells out to the real, tested `tools/hermes_backup.py`/
`hermes_restore.py` -- this router's own job is exactly parse-request /
call-one-function / map-result, nothing else."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.business.logic import hermes_backup

router = APIRouter(prefix="/backup")


@router.post("/export")
def export_backup(background_tasks: BackgroundTasks) -> FileResponse:
    try:
        scratch_sbb_path = hermes_backup.create_backup()
    except hermes_backup.HermesBackupError as exc:
        raise HTTPException(status_code=500, detail=str(exc.detail))
    # Scratch temp .sbb cleaned up after the response is fully sent --
    # same convention artifact_export.py's own /commit route already
    # established.
    background_tasks.add_task(os.remove, scratch_sbb_path)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return FileResponse(
        scratch_sbb_path,
        media_type="application/octet-stream",
        filename=f"second-brain-backup-{timestamp}.sbb",
        background=background_tasks,
    )


@router.post("/restore")
async def restore_backup(file: UploadFile = File(...), force: str = Form("false")) -> dict:
    import tempfile
    from pathlib import Path

    fd, scratch_path = tempfile.mkstemp(suffix=".sbb", prefix="second-brain-restore-upload-")
    os.close(fd)
    Path(scratch_path).write_bytes(await file.read())
    try:
        return hermes_backup.restore_backup(scratch_path, force=force.lower() == "true")
    except hermes_backup.HermesBackupError as exc:
        # exc.detail is either the real script's own structured
        # {"status": "refused"|"failed_mid_restore", ...} dict, or a
        # plain string (e.g. the subprocess itself never ran) -- either
        # way, surfaced verbatim, never re-worded.
        raise HTTPException(status_code=400, detail=exc.detail)
    finally:
        os.remove(scratch_path)
