"""Pending Approvals: the workflow-record concern behind a Supervised
agent's "propose and wait for approval" behavior (ADR-018 point 2) — a
genuinely different concern from working mode itself (a workflow record
with a lifecycle, not a settable property), so this stays its own
sibling module rather than folding into working_mode_registry.py,
mirroring ADR-014's own "one module per concern" discipline (Sections
vs. Providers) applied a second time.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.data_access import vault_writer


def _load_state() -> dict:
    state = vault_writer.load_pending_approvals_state()
    if state is None:
        state = {"pending": []}
        vault_writer.save_pending_approvals_state(state)
    return state


def list_pending_approvals(status: str | None = None, agent_id: str | None = None) -> list[dict]:
    state = _load_state()
    records = state["pending"]
    if status is not None:
        records = [r for r in records if r["status"] == status]
    if agent_id is not None:
        records = [r for r in records if r["agent_id"] == agent_id]
    return records


def get_pending_approval(approval_id: str) -> dict | None:
    state = _load_state()
    return next((r for r in state["pending"] if r["id"] == approval_id), None)


def create_pending_approval(
    agent_id: str, trigger: str, action_id: str | None, description: str,
    payload: dict | None = None,
) -> dict:
    """Idempotency guard applies to trigger == "background" only
    (ADR-018 point 2): without it, every hourly tick for a still-
    unapproved Supervised background agent would pile up a new record
    on top of the last, unbounded. trigger in ("chat", "direct") is
    never deduplicated — each is a distinct, deliberate user request, a
    user asking twice on purpose is expected, ordinary behaviour.

    payload is additive (ADR-021 point 4) — carries whatever structured
    data a deferred action needs to actually execute once approved (e.g.
    the Vault Filing Expert's own proposed kind/tags/body for a new
    top-level area). Defaults to None, so every pre-existing zero-payload
    caller (ADR-018's original chat/direct/background proposals, which
    re-dispatch via _execute_action/run_capture_for_agent instead) is
    unaffected."""
    state = _load_state()
    if trigger == "background":
        existing = next(
            (
                r for r in state["pending"]
                if r["agent_id"] == agent_id
                and r["trigger"] == "background"
                and r["status"] == "pending"
            ),
            None,
        )
        if existing is not None:
            return existing
    record = {
        "id": uuid.uuid4().hex[:12],
        "agent_id": agent_id,
        "trigger": trigger,
        "action_id": action_id,
        "description": description,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resolved_at": None,
        "payload": payload,
    }
    state["pending"].append(record)
    vault_writer.save_pending_approvals_state(state)
    return record


def resolve_pending_approval(approval_id: str, status: str) -> dict | None:
    state = _load_state()
    for record in state["pending"]:
        if record["id"] == approval_id:
            record["status"] = status
            record["resolved_at"] = datetime.now(timezone.utc).isoformat()
            vault_writer.save_pending_approvals_state(state)
            return record
    return None
