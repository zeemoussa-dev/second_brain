"""Delegated knowledge-bootstrap orchestration (ADR-023) -- composes
already-real entry points deterministically: Hub routing (ADR-017) to
find who, then real invocation of the matched candidate's own
capability (skill invocation, ADR-022; the Vault Filing Expert's
placement function, ADR-021). This is the first code path in this
project that actually ACTS on a Hub-routing match rather than only
reporting it. Never a second, recursive run_agent_conversation call
per hop -- a fixed, deterministic three-hop composition (ADR-023's own
Alternatives Considered).

Genuinely `async def` in signature (this task's own Constraint,
mirroring MEMORY.md's standing async-graph-node discipline one call
path over) since its caller (agents_router.py's action-dispatch path)
is itself async -- but every composed call below
(route_cross_section_request, get_agent_working_mode, invoke_skill,
determine_placement_and_file) is a real, synchronous, deterministic
function (confirmed by direct reading of each's own real, current
implementation), so no `await` appears inside this function's own
body."""
from app.business import skill_registry, vault_filing_expert, working_mode_registry
from app.business.agent_orchestration import graph
from app.data_access import vault_writer


async def bootstrap_agent_knowledge(agent_id: str, subject: str) -> dict:
    # Hop 1: this agent's own Section Hub -> a Research Expert candidate.
    hop1 = graph.route_cross_section_request(
        agent_id, need_description=f"real web research about {subject}"
    )
    if not hop1["matched"]:
        _record(agent_id, f"Could not find a Research Expert to help build knowledge about {subject}.")
        return {"status": "no_match", "hop": "research"}
    research_expert_id = hop1["agent_id"]

    if working_mode_registry.get_agent_working_mode(research_expert_id) != "autonomous":
        _record(agent_id, f"{research_expert_id} is not in Autonomous mode — cannot complete this flow unattended.")
        return {"status": "not_autonomous", "matched_agent_id": research_expert_id}

    # Research. skill_registry.invoke_skill's own real call chain
    # (web_research -> anthropic_client.web_search) can RAISE on a
    # genuine external-API failure (a bad/absent credential, a network
    # error) rather than returning a result dict -- confirmed by direct
    # reading of anthropic_client.web_search's own real
    # "raise AnthropicResearchError" body, a real dependency behavior
    # this task's own sample did not account for. Caught here so a real
    # external failure honestly stops the chain (Scenario 5's own "no
    # step fabricates a confident result" Constraint) instead of
    # crashing it uncaught -- mirrors graph.py::_call_model's own
    # identical honest-failure-funnel precedent for the exact same class
    # of real-Provider-call failure.
    try:
        research_result = skill_registry.invoke_skill(
            research_expert_id, "web-research", {"query": subject}
        )
    except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel (Scenario 5)
        _record(agent_id, f"{research_expert_id}'s web research about {subject} failed: {exc}")
        return {"status": "no_results", "research_expert_id": research_expert_id}
    if not research_result.get("found"):
        reason = research_result.get("message") or "found nothing relevant"
        _record(agent_id, f"{research_expert_id}'s web research about {subject} — {reason}")
        return {"status": "no_results", "research_expert_id": research_expert_id}

    # Hop 2: the Research Expert's own Section Hub -> a Vault Filing Expert candidate.
    hop2 = graph.route_cross_section_request(
        research_expert_id, need_description="file this content into the vault"
    )
    if not hop2["matched"]:
        _record(agent_id, "Could not find a Vault Filing Expert to file the gathered research.")
        return {"status": "no_match", "hop": "filing"}
    vault_filing_expert_id = hop2["agent_id"]

    # Filing (Tier 1 writes immediately; Tier 2 creates a pending-approval record).
    filing_result = vault_filing_expert.determine_placement_and_file(
        content=research_result["summary"],
        source_description=f"Web research about {subject}",
        requesting_agent_id=agent_id,
    )
    if filing_result["status"] == "pending_approval":
        _record(
            agent_id,
            f"Research about {subject} gathered; filing paused pending approval of a new top-level vault area.",
        )
        return {
            "status": "pending_approval",
            "approval_id": filing_result["approval_id"],
            "research_expert_id": research_expert_id,
        }
    if filing_result["status"] == "unavailable":
        # A real, currently-declared vault_filing_expert.py outcome not
        # named in this task's own "returns one of" enumeration (that
        # module's own Provider-unavailable branch, confirmed by direct
        # reading) -- passed through as-is rather than dropped, so this
        # honest failure is never silently swallowed.
        _record(agent_id, f"Could not file the research about {subject} — {filing_result['message']}")
        return filing_result

    _record(agent_id, f"Built knowledge about {subject}: filed to {filing_result['path']}.")
    return {
        "status": "written",
        "path": filing_result["path"],
        "kind": filing_result["kind"],
        "research_expert_id": research_expert_id,
        "vault_filing_expert_id": vault_filing_expert_id,
    }


def _record(agent_id: str, message: str) -> None:
    vault_writer.append_agent_history_entry(agent_id, "run_event", message)
