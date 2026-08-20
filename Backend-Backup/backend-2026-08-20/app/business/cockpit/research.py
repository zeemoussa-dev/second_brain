"""On-the-spot Cockpit research (ADR-036) -- Hub-routes from the
requesting (currently brought-in) Expert to a real Research Expert
(mirrors knowledge_bootstrap.bootstrap_agent_knowledge's own Hop 1
exactly), invokes the already-Done web-research Skill, and records the
exchange in the shared Cockpit thread -- reproducing the approved
prototype's own "Quick research: {query}" / Expert-reply chat exchange.
Save/discard never routes through skill_registry -- Save is a direct
vault_writer.write_note call (ADR-036 point 4)."""
from __future__ import annotations

from app.business import skill_registry, vault_indexing
from app.business.agent_orchestration import graph
from app.business.cockpit import threads
from app.data_access import vault_writer

_SUBJECT_SUBFOLDER = {"meeting": "Work/Research", "email": "Work/Research"}
_SUBJECT_NOTE_SUBFOLDER = {"meeting": "Work/Meetings", "email": "Work/Emails"}


async def trigger_research(
    subject_kind: str, subject_note_stem: str, requesting_agent_id: str, query: str,
) -> dict:
    threads.append_system_message(  # T02's own sync primitive -- appends without triggering a reply
        subject_kind, subject_note_stem, f"Quick research: {query}",
    )
    hop = graph.route_cross_section_request(
        requesting_agent_id, need_description=f"real web research about {query}"
    )
    if not hop["matched"]:
        reply = "Could not find a Research Expert to help with this."
        threads.append_system_message(subject_kind, subject_note_stem, reply)
        return {"status": "no_match"}
    research_expert_id = hop["agent_id"]
    try:
        result = skill_registry.invoke_skill(
            research_expert_id, "web-research", {"query": query}, trigger="direct"
        )
    except Exception as exc:  # noqa: BLE001 -- honest-failure funnel, mirrors knowledge_bootstrap's own precedent
        reply = f"Research about {query} failed: {exc}"
        threads.append_system_message(subject_kind, subject_note_stem, reply)
        return {"status": "no_results"}
    if not result.get("found"):
        reason = result.get("message") or result.get("reason") or "found nothing relevant"
        reply = f"{research_expert_id}'s research about {query} — {reason}"
        threads.append_system_message(subject_kind, subject_note_stem, reply)
        return {"status": "no_results"}
    summary = result["summary"]
    threads.append_system_message(
        subject_kind, subject_note_stem,
        "Found a result — check the left panel to save it into the vault or discard it.",
    )
    return {"status": "found", "summary": summary, "query": query, "research_expert_id": research_expert_id}


def save_research_result(subject_kind: str, subject_note_stem: str, query: str, summary: str) -> dict:
    subfolder = _SUBJECT_SUBFOLDER[subject_kind]
    note_path = vault_writer.write_note(
        subfolder=subfolder,
        filename_stem=f"Research - {query}",
        frontmatter={"type": "Research", "source_query": query},
        body=f"{summary}\n\n[[{subject_note_stem}]]\n",
    )
    return {"note_path": note_path}


def list_research_results(subject_kind: str, subject_note_stem: str) -> list[dict]:
    entry = vault_indexing.get_index().get(subject_note_stem)
    if entry is None:
        return []
    index = vault_indexing.get_index()
    results = []
    for source_stem in entry["incoming_wikilinks"]:
        source_entry = index.get(source_stem)
        if source_entry and source_entry["frontmatter"].get("type") == "Research":
            results.append({"stem": source_stem, "title": source_entry["frontmatter"].get("source_query", source_stem)})
    return results
