"""Orchestrates a vault index rebuild across two independent systems --
the backend's own in-process index (VaultManager) and the separate,
disk-persisted agent-facing index Hermes' own real `vault-index-rebuild`
cron job maintains -- moved out of vault_index_router.py (2026-08-28,
API layer holds no business logic).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.business.core.vault.vault_manager import VaultManager
from app.business.hermes.client import get_client

_vault_manager = VaultManager()


def rebuild_vault_index() -> dict:
    """Triggers both the backend's own fast in-process rebuild AND the
    separate, disk-persisted agent-facing index (Hermes-Provisioning/
    skills/vault-rebuild/vault-index) via the SAME real
    `vault-index-rebuild` cron job the recurring schedule fires -- so
    there is exactly one real rebuild path for agents, never a second
    one that could drift from it. The agent-facing trigger is
    fire-and-forget: an agent-mediated run (real LLM reasoning through
    Hermes' own skill-invocation loop, even for a mechanical skill) can
    take meaningfully longer than the in-process rebuild below, so this
    never waits on it -- confirmed live, 2026-08-27, both rebuilds
    independently."""
    index = _vault_manager.rebuild_index()
    # Best-effort -- the backend's own rebuild above must still succeed
    # either way; get_client().cli.run_cron_job already swallows "no real
    # Hermes install at the configured path" and any launch failure.
    get_client().cli.run_cron_job("vault-index-rebuild")
    return {
        "notes_indexed": len(index),
        "rebuilt_at": datetime.now(timezone.utc).isoformat(),
        "agent_index_rebuild_triggered": True,
    }
