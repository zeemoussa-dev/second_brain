"""Explicit, on-demand vault re-index trigger (REQ-SB-01-US-01,
ESC-021 resolved trigger path (a)) -- alongside the scheduler-tick
refresh T04 wires up separately. HTTP-only, delegates to business/
(ADR-003). The real dual-rebuild orchestration (this backend's own
in-process index plus the disk-persisted agent-facing index) lives in
business/logic/vault_index_rebuild.py, not here."""
from __future__ import annotations

from fastapi import APIRouter

from app.business.logic import vault_index_rebuild

router = APIRouter(prefix="/vault-index")


@router.post("/rebuild")
def rebuild_vault_index() -> dict:
    """Plain (non-async) handler -- FastAPI/Starlette runs a synchronous
    route handler in its own threadpool automatically, so
    vault_index_rebuild's own blocking, read-heavy full-vault scan never
    blocks the event loop, with no manual asyncio.to_thread call needed
    at this layer (unlike capture_scheduler.py's run_capture_if_idle,
    which isn't reached through an HTTP request at all). Independent of
    capture_scheduler._capture_run_lock -- that lock guards overlapping
    *vault-writing* capture runs, a concern this read-only, side-effect-
    free rebuild does not share (ADR-024)."""
    return vault_index_rebuild.rebuild_vault_index()


@router.post("/refresh")
def refresh_vault_index() -> dict:
    """Re-reads the vault into the backend's own index, and triggers nothing
    else -- what the `vault-index-rebuild` cron job calls once it has written the
    agent-facing disk index (`BUG-082`).

    `/rebuild` above fires that same cron job, so the job cannot call it without
    triggering itself. The split is the whole point: `/rebuild` is "rebuild
    everything, I am a human pressing a button", `/refresh` is "my own index is
    behind the vault"."""
    return vault_index_rebuild.refresh_in_process_index()
