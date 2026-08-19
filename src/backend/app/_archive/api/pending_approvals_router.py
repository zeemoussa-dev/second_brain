from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.agents_router import _execute_action
from app.business import (
    agent_registry,
    knowledge_gap_tracking,
    pending_approval_registry,
    skill_registry,
    skill_tools,
    vault_filing_expert,
    vault_write_tools,
)
from app.business.email_classification import (
    finalize_classification_failure_acknowledgement,
    finalize_recurring_pipeline_proposal,
    finalize_thread_project_routing,
    run_capture_for_agent,
)
from app.business.pipelines.librarian_housekeeping import (
    finalize_company_review,
    finalize_customer_archival,
    finalize_customer_backfill_routing,
    finalize_librarian_company_link,
)
from app.business.project_customer_synthesizer import finalize_background_amendment_proposal
from app.data_access import vault_writer

router = APIRouter(prefix="/pending-approvals")


class CompanyReviewDecisionBody(BaseModel):
    """The Company Review proposal kind's own additive Approve-endpoint
    decision body (`REQ-SB-76-US-01-T07`, `ADR-057` Decision 3) -- the
    operator's 5-way choice (`outcome`), plus the Affiliate branch's own
    parent+kind pick and the Merge branch's own parent-only pick
    (`parent_kind` left `None` for Merge unless the picker itself also
    resolves it -- `finalize_company_review`'s own Merge branch reads
    `parent_kind` from the merged payload regardless)."""
    outcome: str
    parent_name: str | None = None
    parent_kind: str | None = None

# Approve dispatch for a pending record whose action_id is not an
# agent_registry-declared action at all (ADR-021 point 5) -- consulted
# BEFORE the existing _execute_action/run_capture_for_agent re-dispatch
# below, mirroring agents_router.py's own _ACTION_HANDLERS/
# skill_registry.py's own _SKILL_HANDLERS dispatch-table convention.
_APPROVAL_HANDLERS = {
    "propose_new_top_level_area": vault_filing_expert.finalize_new_top_level_area,
    "hermes_vault_write": vault_write_tools.finalize_hermes_write,
    "route_thread_to_project": finalize_thread_project_routing,
    "propose_recurring_pipeline": finalize_recurring_pipeline_proposal,
    "propose_cross_cutting_update": vault_filing_expert.finalize_cross_cutting_update,
    "acknowledge_classification_failure": finalize_classification_failure_acknowledgement,
    "propose_background_amendment": finalize_background_amendment_proposal,
    "propose_librarian_company_link": finalize_librarian_company_link,
    "propose_customer_backfill_routing": finalize_customer_backfill_routing,
    "propose_customer_archival_candidate": finalize_customer_archival,
    "propose_company_review": finalize_company_review,
}


def _resolved(record: dict) -> dict:
    agent = agent_registry.get_agent(record["agent_id"])
    return {**record, "agent_name": agent["name"] if agent else record["agent_id"]}


@router.get("")
def list_pending_approvals(status: str | None = None, agent_id: str | None = None) -> list[dict]:
    records = pending_approval_registry.list_pending_approvals(status=status, agent_id=agent_id)
    return [_resolved(r) for r in records]


@router.get("/known-companies")
def known_companies() -> dict:
    """The Company Review decision control's own parent-entity/canonical-
    entity picker source (`REQ-SB-76-US-01-T07`, `ADR-057` Decision 9) --
    composed fresh from already-existing, vault-derived enumerations
    (`vault_writer.list_customer_folders()`/`list_known_partners()`), zero
    new `vault_writer.py` code. Called fresh by the frontend on every
    Approvals page load -- never baked into a proposal's own stored
    payload, which would go stale the moment ANY OTHER Company Review
    batch resolves first. Registered BEFORE `/{approval_id}` below so
    this literal path segment is never shadowed by that path-parameter
    route."""
    customers = [
        entry["customer"] for entry in vault_writer.list_customer_folders() if entry.get("customer")
    ]
    partners = vault_writer.list_known_partners()
    return {"customers": customers, "partners": partners}


@router.get("/{approval_id}")
def get_pending_approval(approval_id: str) -> dict:
    record = pending_approval_registry.get_pending_approval(approval_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Unknown pending approval")
    return _resolved(record)


@router.post("/{approval_id}/approve")
def approve_pending_approval(
    approval_id: str, decision: CompanyReviewDecisionBody | None = None,
) -> dict:
    record = pending_approval_registry.get_pending_approval(approval_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Unknown pending approval")
    if record["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"Already {record['status']}")

    skip_history = False
    if record["action_id"] in skill_tools.SKILLS:
        # A migrated mutating Skill's own pending approval (REQ-SB-39-US-02,
        # ADR-029 point 4) -- checked FIRST, before _APPROVAL_HANDLERS,
        # since a skill_id can never collide with an _APPROVAL_HANDLERS key
        # but this ordering is the literal one ADR-029 point 4 specifies.
        # Calls skill_registry._dispatch_skill directly, NEVER
        # skill_registry.invoke_skill -- re-entering the gate on Approve
        # would find the agent still Supervised and create a second
        # pending record instead of ever running (mirrors this file's own
        # existing _execute_action-not-_invoke_action precedent, ADR-018
        # point 6).
        result = skill_registry._dispatch_skill(
            record["agent_id"], record["action_id"], record["payload"], already_approved=True,
        )
        outcome_message = result.get("message", "Approved.")
        # A handler that already recorded its own run_event internally
        # (build_knowledge's own bootstrap_agent_knowledge chain,
        # REQ-SB-39-US-02-T03) signals this the same way
        # _run_build_knowledge's Action-path handler already does
        # (REQ-SB-36-US-02) -- avoids a duplicate entry.
        skip_history = bool(result.get("history_recorded"))
    elif record["action_id"] in _APPROVAL_HANDLERS:
        # A Vault Filing Expert Tier-2 proposal (or any future action of
        # this same shape) -- never an agent_registry-declared action,
        # so _execute_action's own lookup would never find it. Runs the
        # deferred write directly off the record's own stored payload
        # (ADR-021 point 5). The Company Review proposal kind's own
        # additive decision body (REQ-SB-76-US-01-T07, ADR-057 Decision 3)
        # is merged into the stored payload BEFORE dispatch here -- every
        # one of the other 8 registered handlers' own stored payload never
        # contains outcome/parent_name/parent_kind keys, so
        # effective_payload == payload for them whenever no body is sent,
        # exactly as today.
        effective_payload = {**record["payload"], **(decision.model_dump() if decision else {})}
        result = _APPROVAL_HANDLERS[record["action_id"]](effective_payload)
        # Additive generalization (REQ-SB-55-US-01-T04) -- a handler MAY
        # now supply its own outcome message (e.g. finalize_thread_
        # project_routing's own Project-naming text) via a "message" key;
        # the two pre-existing handlers (finalize_new_top_level_area,
        # finalize_hermes_write) return no "message" key at all, so this
        # falls straight through to their original byte-for-byte wording.
        outcome_message = result.get("message") or f"Approved — filed at {result['path']}."
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
    knowledge_gap_tracking.close_gap_by_pending_approval(approval_id)
    if not skip_history:
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
