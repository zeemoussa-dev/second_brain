"""Explicit, on-demand vault re-index trigger (REQ-SB-01-US-01,
ESC-021 resolved trigger path (a)) -- alongside the scheduler-tick
refresh T04 wires up separately. HTTP-only, delegates to business/
(ADR-003).

Also triggers the separate, disk-persisted agent-facing index
(Hermes-Provisioning/skills/vault-rebuild/vault-index,
Implementation/Plans/2026-08-27-vault-index-and-section-agents.md) via
`hermes cron run vault-index-rebuild` -- the SAME job the recurring
schedule fires, so there is exactly one real rebuild path for agents,
never a second one that could drift from it. Fire-and-forget: an
agent-mediated run (real LLM reasoning through Hermes' own skill-
invocation loop, even for a mechanical skill) can take meaningfully
longer than this endpoint's own fast in-process rebuild below, so the
response never waits on it -- confirmed live, 2026-08-27, both rebuilds
independently."""
from __future__ import annotations

import subprocess
from datetime import datetime, timezone

from fastapi import APIRouter

from app.business import vault_indexing
from app.config import settings

router = APIRouter(prefix="/vault-index")


def _trigger_agent_index_rebuild() -> None:
    hermes_exe = settings.hermes_home_path / "hermes-agent" / "bin" / "hermes.exe"
    if not hermes_exe.is_file():
        return  # no real Hermes install at the configured path -- nothing to trigger
    try:
        subprocess.Popen(
            [str(hermes_exe), "cron", "run", "vault-index-rebuild"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass  # best-effort -- the backend's own rebuild below must still succeed either way


@router.post("/rebuild")
def rebuild_vault_index() -> dict:
    """Plain (non-async) handler -- FastAPI/Starlette runs a synchronous
    route handler in its own threadpool automatically, so this blocking,
    read-heavy full-vault scan never blocks the event loop, with no
    manual asyncio.to_thread call needed at this layer (unlike
    capture_scheduler.py's run_capture_if_idle, which isn't reached
    through an HTTP request at all). Independent of capture_scheduler.
    _capture_run_lock -- that lock guards overlapping *vault-writing*
    capture runs, a concern this read-only, side-effect-free rebuild
    does not share (ADR-024)."""
    index = vault_indexing.rebuild_index()
    _trigger_agent_index_rebuild()
    return {
        "notes_indexed": len(index),
        "rebuilt_at": datetime.now(timezone.utc).isoformat(),
        "agent_index_rebuild_triggered": True,
    }
