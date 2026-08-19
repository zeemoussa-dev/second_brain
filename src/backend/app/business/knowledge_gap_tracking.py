"""Agent knowledge-gap tracking (ADR-032) -- the shared read/write core
every closing path (T05's human-answer path, T06's delegated-research
path) and the graph.py detection node (T04) compose. Mirrors
skill_registry.py's own "one dedicated business module + one dedicated
.second-brain/<concern>.json file, pure I/O in vault_writer, business
rules here" pattern (ADR-032 point 2) -- never folded into
agent_activity.py, whose own _ACTIVITY_KINDS scope stays
background-run-only (that story's own Constraints)."""
import uuid
from datetime import datetime, timezone

from app.business import vault_filing_expert
from app.business.agent_orchestration import knowledge_bootstrap
from app.data_access import vault_writer


def _load_state() -> dict:
    state = vault_writer.load_knowledge_gaps_state()
    if state is None:
        state = {"gaps": []}
        vault_writer.save_knowledge_gaps_state(state)
    return state


def record_gap(agent_id: str, question: str, topic: str) -> dict:
    """id is uuid.uuid4().hex[:12] -- the same synthetic-id precedent
    ADR-018 point 2 already established for a workflow record with no
    natural vault-derived identity (a gap is born from a conversation
    turn, not a vault fact)."""
    state = _load_state()
    record = {
        "id": uuid.uuid4().hex[:12],
        "agent_id": agent_id,
        "question": question,
        "topic": topic,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "closed_at": None,
        "resolution": None,
    }
    state["gaps"].append(record)
    vault_writer.save_knowledge_gaps_state(state)
    return record


def close_gap(gap_id: str, resolution: str) -> bool:
    """Returns False if gap_id is unknown or already closed -- a
    caller-meaningful distinction (T06's honest-no-results path, AC-07,
    must never call this at all for a "no_results" outcome; T05/T06's
    own "closed once, not twice" idempotency relies on this False
    return rather than silently succeeding a second time)."""
    state = _load_state()
    for gap in state["gaps"]:
        if gap["id"] == gap_id and gap["status"] == "open":
            gap["status"] = "closed"
            gap["closed_at"] = datetime.now(timezone.utc).isoformat()
            gap["resolution"] = resolution
            vault_writer.save_knowledge_gaps_state(state)
            return True
    return False


def list_agent_gaps(agent_id: str, status: str | None = None) -> list[dict]:
    state = _load_state()
    gaps = [gap for gap in state["gaps"] if gap["agent_id"] == agent_id]
    if status is not None:
        gaps = [gap for gap in gaps if gap["status"] == status]
    return gaps


def count_open_gaps(agent_id: str) -> int:
    return len(list_agent_gaps(agent_id, status="open"))


def get_gap(gap_id: str) -> dict | None:
    state = _load_state()
    return next((gap for gap in state["gaps"] if gap["id"] == gap_id), None)


def resolve_gap_with_human_answer(gap_id: str, agent_id: str, answer: str) -> dict:
    """Composes the already-Done Vault Filing Expert (ADR-021/
    REQ-SB-35-US-01) unchanged -- never a new correctness-verification
    step layered on top (ADR-032 point 3, mirrors MEMORY.md's standing
    no-staging-gate posture). Closes the gap only once filing actually
    completes: immediately for a Tier-1 write; for a Tier-2
    new-top-level-area proposal, the gap stays open, tagged with the
    pending approval's own id instead -- see close_gap_by_pending_
    approval, called from pending_approvals_router.py at
    approval-finalization time, never before content is actually
    filed."""
    filing_result = vault_filing_expert.determine_placement_and_file(
        content=answer,
        source_description=f"Human-provided answer to knowledge gap {gap_id}",
        requesting_agent_id=agent_id,
    )
    if filing_result["status"] == "written":
        close_gap(gap_id, "human_provided")
    elif filing_result["status"] == "pending_approval":
        _mark_gap_pending_approval(gap_id, filing_result["approval_id"], "human_provided")
    return filing_result


def _mark_gap_pending_approval(gap_id: str, approval_id: str, resolution: str) -> None:
    """Stores BOTH the pending approval's id and which resolution
    value should apply once it finalizes -- `T06`'s own delegated-
    research path composes this same helper with `resolution="research"`,
    so `close_gap_by_pending_approval` (below) can stay a single,
    resolution-agnostic completion point for either closing path,
    rather than pending_approvals_router.py needing to know which
    closing path originated a given Tier-2 proposal."""
    state = _load_state()
    for gap in state["gaps"]:
        if gap["id"] == gap_id:
            gap["pending_approval_id"] = approval_id
            gap["pending_resolution"] = resolution
            vault_writer.save_knowledge_gaps_state(state)
            return


def close_gap_by_pending_approval(approval_id: str) -> bool:
    """Called from pending_approvals_router.py's own Approve endpoint,
    once ANY Tier-2 propose_new_top_level_area record actually finishes
    filing (ADR-032 point 3) -- shared, resolution-agnostic completion
    point for both T05's human-answer path and T06's delegated-research
    path; reads which resolution applies from the gap's own stored
    pending_resolution field rather than the caller having to know.
    Never called for a declined record. A safe no-op (returns False)
    for every approval not tied to any open gap."""
    state = _load_state()
    for gap in state["gaps"]:
        if gap.get("pending_approval_id") == approval_id and gap["status"] == "open":
            gap["status"] = "closed"
            gap["closed_at"] = datetime.now(timezone.utc).isoformat()
            gap["resolution"] = gap.pop("pending_resolution", None)
            vault_writer.save_knowledge_gaps_state(state)
            return True
    return False


async def resolve_gap_via_research(gap_id: str, agent_id: str) -> dict:
    """Composes the already-Done delegated knowledge-bootstrap chain
    (REQ-SB-36-US-02/ADR-023) unchanged (ADR-032 point 4) -- subject is
    the gap's own real recorded question, never a re-derived summary.
    A real "written"/"pending_approval" outcome closes the gap
    (resolution="research"); every other status (no_match,
    not_autonomous, no_results, unavailable) leaves the gap open --
    Scenario 7's own regression guard is satisfied by this composition
    alone, no new logic needed to detect "research failed"."""
    gap = get_gap(gap_id)
    result = await knowledge_bootstrap.bootstrap_agent_knowledge(agent_id, subject=gap["question"])
    if result["status"] == "written":
        close_gap(gap_id, "research")
    elif result["status"] == "pending_approval":
        _mark_gap_pending_approval(gap_id, result["approval_id"], "research")
    return result
