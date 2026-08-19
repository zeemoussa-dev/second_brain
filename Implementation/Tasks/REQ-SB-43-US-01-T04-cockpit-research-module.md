---
id: REQ-SB-43-US-01-T04
title: New app/business/cockpit/research.py — trigger_research (Hub-route to a Research Expert + web-research skill), save_research_result, list_research_results (via vault_indexing backlinks)
parent_story: REQ-SB-43-US-01
requirement_id: REQ-SB-43
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-43-US-01-T02]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-43-US-01-T04 — `app/business/cockpit/research.py`

## Parent Story

- Story: [[REQ-SB-43-US-01]] — `../UserStories/REQ-SB-43-US-01-meeting-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-43 *Meeting Cockpit — Expert-Assisted Meeting Workspace*

---

## Objective

The on-the-spot research mechanism (Scenario 8) and the explicit save/discard flow (Scenarios 9/10). **Decomposer-level mechanism decision, not guessed at the spec stage per the story's own Context (single defensible reading, grounded directly in the approved prototype's own visible behavior — see Context/Notes below):** triggering research Hub-routes from the currently-brought-in requesting Expert to a real Research Expert (mirroring `knowledge_bootstrap.bootstrap_agent_knowledge`'s own Hop 1 exactly), invokes the already-Done `web-research` Skill, and appends both the user's own "Quick research: {query}" turn and the Expert's own reply to the SAME shared Cockpit thread — reproducing `html-prototype/meeting-cockpit.html`'s own approved "research-pending" chat exchange exactly. Saving/discarding never routes through `skill_registry`/`_invoke_action` (`ADR-036` point 4) — Save is a direct `vault_writer.write_note` call.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `threads.append_system_message`/`get_thread`.
- `app.business.agent_orchestration.graph.route_cross_section_request(agent_id, need_description) -> dict` (`{"matched": bool, "agent_id": str}` on match) is Done (`ADR-017`).
- `app.business.skill_registry.invoke_skill(agent_id, skill_id, args, trigger) -> dict` is Done.
- `app.business.vault_indexing.get_index()` is Done — each entry's `incoming_wikilinks` is a list of resolved SOURCE stems (`ADR-024` point 3).
- `app.data_access.vault_writer.write_note(subfolder, filename_stem, frontmatter, body) -> str` is Done.

**After / Outputs:** new `app/business/cockpit/research.py`:
```python
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
        reason = result.get("message") or "found nothing relevant"
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
```

---

## Files to Modify

- `src/backend/app/business/cockpit/research.py` (new) — per the code block above. Composes `T02`'s own `threads.append_system_message` (already synchronous/persists immediately per `T02`'s own shape) — do not add a second variant.

---

## Constraints

- Save/discard NEVER call `skill_registry.invoke_skill`/`agents_router._invoke_action` (`ADR-036` point 4) — `save_research_result` is a direct `vault_writer.write_note` call only.
- Discard requires NO backend call at all — the frontend simply never calls `save_research_result` for a discarded result (this task builds no `discard` endpoint/function).
- A saved note wikilinks to the subject note (`[[{subject_note_stem}]]` in its own body) — NEVER appended into the subject note's own body (Scenario 9's own Constraint).
- `list_research_results` reads the subject note's OWN `incoming_wikilinks` (backlinks) — a saved research note's forward link to the subject note is what makes it appear (forward-only-linking convention) — never a separate persisted "this meeting's research list" file.
- `trigger_research`'s own pending result (`summary`/`query`) is NOT persisted anywhere by this function — the caller (the router, `T05`) returns it to the frontend, which holds it in ephemeral state until Save/Discard (mirrors the story's own precedent for "ephemeral until an explicit action," and REQ-SB-44's own draft-reply resolution one layer over).
- Read `T02`'s own REAL, as-built `threads.py` before wiring `append_system_message`/any needed variant — reconcile function names/signatures against what `T02` actually built, do not assume the code sample above is unchanged.

---

## Tests

**Manual verification steps** (Python shell, backend `.venv`, `PYTHONPATH=.`, `asyncio.run(...)` for the async function; requires a real, routable Section/agent pairing with a real Research Expert in Autonomous mode, e.g. the same fixture `knowledge_bootstrap`'s own verification uses):
1. **[REQ-SB-43-US-01-AC-08]** `asyncio.run(cockpit.research.trigger_research("meeting", "test-stem", "<a real routable requesting agent id>", "Acme Corp's Q3 earnings"))` — confirm the return is `{"status": "found", "summary": <real string>, ...}` (or an honest `"no_results"`/`"no_match"` if the real web-research dependency is genuinely unavailable in this environment — record which was observed). Confirm `cockpit.threads.get_thread("meeting", "test-stem")["messages"]` gained the "Quick research: Acme Corp's Q3 earnings" user turn AND the "Found a result…" (or honest failure) system turn.
2. **[REQ-SB-43-US-01-AC-09]** `cockpit.research.save_research_result("meeting", "test-stem", "Acme Corp's Q3 earnings", "<real summary from step 1>")` — confirm a new note is written under `Work/Research/`, its body contains `[[test-stem]]`, and it is NOT appended into any existing Meeting note's own body (confirm the Meeting note file itself is byte-identical before/after).
3. **[REQ-SB-43-US-01-AC-07]**/**[REQ-SB-43-US-01-AC-09]** `vault_indexing.rebuild_index()`. `cockpit.research.list_research_results("meeting", "test-stem")` — confirm the just-saved result appears. Call it for a DIFFERENT, unrelated meeting stem — confirm the result does NOT appear there (scoped to one meeting, not global).
4. **[REQ-SB-43-US-01-AC-10]** Confirm no function in this module was called for a "discard" — trigger research again, do NOT call `save_research_result`, re-run `list_research_results` — confirm no new entry appeared (nothing was written for the discarded result).
5. Clean-up: delete the test note written under `Work/Research/` and the `test-stem` entry from `.second-brain/cockpit_threads.json`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `trigger_research` Hub-routes to a real Research Expert, invokes `web-research`, records the exchange in the shared thread, returns an honest `found`/`no_results`/`no_match` result — never fabricates a summary
- [ ] `save_research_result` writes a new standalone note, wikilinked to the subject note, never appended into it
- [ ] `list_research_results` reads via the subject note's own backlinks, scoped to that one subject
- [ ] Discard requires no backend call
- [ ] Neither function routes through `skill_registry.invoke_skill`/`_invoke_action` for save/discard
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The shared thread mechanism itself — `T02` (composed here, not modified).
- People-chip resolution — `T03`.
- The HTTP router — `T05`.

---

## Context / Notes

**Mechanism grounding (decomposer judgment call, single defensible reading, not a MUST-FLAG):** the story's own Context left "the on-the-spot research mechanism itself" open at the mechanism level. `html-prototype/meeting-cockpit.html`'s own approved "research-pending" state shows the trigger as a `chat-message--user` bubble reading "Quick research: Acme Corp's Q3 earnings", followed by a real Expert reply — this task reproduces that exact visible exchange via an explicit `trigger_research` call (not free-text sniffing of ordinary chat messages, which would be fragile/ambiguous), Hub-routing exactly like `knowledge_bootstrap.bootstrap_agent_knowledge`'s own already-proven Hop 1, per the story's own "Related to: REQ-SB-36-US-01 (web-research Skill)" dependency note. `requesting_agent_id` is a required parameter — mirrors the prototype's own "chat input disabled until an Expert is brought in" empty-state gating (`meeting-cockpit.html`'s `data-state="empty"` panel): the frontend only offers the research trigger once at least one Expert has been brought in.

---

## Implementation Log

Implemented per the code block, with one small in-scope readability addition:
the `no_results` branch's `reason` falls back to `result.get("message") or
result.get("reason") or "found nothing relevant"` (the sample only checked
`"message"`) — `invoke_skill`'s own real "refused" shape (e.g. no skill access)
carries `"reason"`, not `"message"`; without this the honest refusal text would
read as the generic default instead of the real reason. No Constraint/AC
affected (still an honest, non-fabricated `no_results`).

**Manual verification (real `.venv`, real vault, temporary real state changes
through already-`Done` APIs — `vault-qa` granted `web-research` + swapped to the
`anthropic-claude` Provider — reverted and independently reconfirmed afterward,
mirroring this project's own established `SPRINT-035` precedent):**

1. **AC-08 (honest baseline, no grant yet):** `trigger_research("meeting", "test-stem", "compass-expert", "Acme Corp's Q3 earnings")` → Hub-routed correctly to `vault-qa` (its own real `"research"`/`"web research"` keywords matched, cross-Section from `compass-expert`), `vault-qa` had no `web-research` access yet → real, honest `{"status": "no_results"}`, thread gained the real "Quick research: ..." user turn and an honest "...Agent does not have access to this skill." system turn. Confirmed, no fabrication.
2. **AC-08 (positive path):** after the temporary grant/Provider swap, same call → real `{"status": "found", "summary": <genuine multi-paragraph real Anthropic web-search result about Acme United Corp's real Q3 2025 earnings>, ...}`; thread gained the real "Found a result…" system turn. Confirmed — a real, non-fabricated Anthropic web-search call.
3. **AC-09:** `save_research_result("meeting", "0-2026-08-10-CC920000", ...)` (a REAL, existing captured Meeting note, not a throwaway stem) → new note written under `Work/Research/`, body contains `[[0-2026-08-10-CC920000]]`; the real Meeting note's own file content read back byte-for-byte identical before/after (direct `read_text()` comparison — an initial `hash()`-based comparison attempt was discarded mid-verification once recognized as unreliable across separate process runs due to Python's per-process hash randomization for `bytes`/`str`, not a real content difference; re-verified via direct string comparison instead).
4. **AC-07/AC-09:** `vault_indexing.rebuild_index()`; `list_research_results("meeting", "0-2026-08-10-CC920000")` → the just-saved result appears; `list_research_results("meeting", "test-stem")` (a different, unrelated stem) → `[]`. Confirmed scoped, not global.
5. **AC-10:** discard requires no backend call by construction — no `discard` function/route exists anywhere in this module (confirmed by direct code read); the frontend (`T08`) simply never calls `save_research_result` for a discarded result.
6. Cleanup: saved test note deleted; `.second-brain/cockpit_threads.json` test entries deleted; `vault-qa`'s temporary `web-research` grant revoked and Provider reverted to `compass` — both independently reconfirmed via fresh `list_agent_skills`/`get_agent_provider` calls matching the pre-test state exactly.

gate: clear 2026-08-14 — no triggers fired (composes `ADR-036`'s own already-made
decision; the one code addition above is a minor, non-AC-affecting readability
fix within this task's own file, not a new assumption or dependency).
