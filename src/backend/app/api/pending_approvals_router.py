from fastapi import APIRouter, HTTPException

from app.api.agents_router import _execute_action
from app.business import agent_registry, pending_approval_registry, vault_filing_expert, vault_write_tools
from app.business.email_classification import run_capture_for_agent
from app.data_access import vault_writer

router = APIRouter(prefix="/pending-approvals")

# Approve dispatch for a pending record whose action_id is not an
# agent_registry-declared action at all (ADR-021 point 5) -- consulted
# BEFORE the existing _execute_action/run_capture_for_agent re-dispatch
# below, mirroring agents_router.py's own _ACTION_HANDLERS/
# skill_registry.py's own _SKILL_HANDLERS dispatch-table convention.
_APPROVAL_HANDLERS = {
    "propose_new_top_level_area": vault_filing_expert.finalize_new_top_level_area,
    "hermes_vault_write": vault_write_tools.finalize_hermes_write,
}


def _resolved(record: dict) -> dict:
    agent = agent_registry.get_agent(record["agent_id"])
    return {**record, "agent_name": agent["name"] if agent else record["agent_id"]}


@router.get("")
def list_pending_approvals(status: str | None = None, agent_id: str | None = None) -> list[dict]:
    records = pending_approval_registry.list_pending_approvals(status=status, agent_id=agent_id)
    return [_resolved(r) for r in records]


@router.get("/{approval_id}")
def get_pending_approval(approval_id: str) -> dict:
    record = pending_approval_registry.get_pending_approval(approval_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Unknown pending approval")
    return _resolved(record)


@router.post("/{approval_id}/approve")
def approve_pending_approval(approval_id: str) -> dict:
    record = pending_approval_registry.get_pending_approval(approval_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Unknown pending approval")
    if record["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Already {record['status']}")

    if record["action_id"] in _APPROVAL_HANDLERS:
        # A Vault Filing Expert Tier-2 proposal (or any future action of
        # this same shape) -- never an agent_registry-declared action,
        # so _execute_action's own lookup would never find it. Runs the
        # deferred write directly off the record's own stored payload
        # (ADR-021 point 5).
        result = _APPROVAL_HANDLERS[record["action_id"]](record["payload"])
        outcome_message = f"Approved — filed at {result['path']}."
    elif record["action_id"] is not None:
        # Chat/direct proposal — execute unconditionally via
        # _execute_action, NEVER _invoke_action (re-entering the gate
        # would find the agent still Supervised and create a second
        # pending record instead of ever actually running — ADR-018
        # point 6's own infinite-defer-bug rejection).
        result = _execute_action(record["agent_id"], record["action_id"])
        outcome_message = result["message"]
    else:
        # Background proposal — no discrete action id; runs the same
        # capture step the scheduled tick would have run.
        results = run_capture_for_agent(record["agent_id"])
        outcome_message = f"Approved — background step ran, {len(results)} result(s)."

    resolved = pending_approval_registry.resolve_pending_approval(approval_id, "approved")
    vault_writer.append_agent_history_entry(record["agent_id"], "run_event", outcome_message)
    return _resolved(resolved)


@router.post("/{approval_id}/decline")
def decline_pending_approval(approval_id: str) -> dict:
    record = pending_approval_registry.get_pending_approval(approval_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Unknown pending approval")
    if record["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Already {record['status']}")

    resolved = pending_approval_registry.resolve_pending_approval(approval_id, "declined")
    vault_writer.append_agent_history_entry(record["agent_id"], "run_event", "Declined — no action taken")
    return _resolved(resolved)
