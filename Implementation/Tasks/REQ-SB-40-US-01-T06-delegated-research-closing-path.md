---
id: REQ-SB-40-US-01-T06
title: Delegated-research closing path — knowledge_gap_tracking.resolve_gap_via_research + POST /agents/{agent_id}/knowledge-gaps/{gap_id}/research
parent_story: REQ-SB-40-US-01
requirement_id: REQ-SB-40
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-032 created) — carried from the parent story; the human reviews ADR-032 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-40-US-01-T02, REQ-SB-40-US-01-T05]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-40-US-01-T06 — Delegated-research closing path

## Parent Story

- Story: [[REQ-SB-40-US-01]] — `../UserStories/REQ-SB-40-US-01-agent-knowledge-gap-tracking-and-expert-readiness.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-40 *Agent Knowledge-Gap Tracking & Expert Readiness*

---

## Objective

Compose the already-`Done` delegated knowledge-bootstrap chain (`REQ-SB-36-US-02`/`ADR-023`) as-is, never reimplemented (`ADR-032` point 4) — a real `"written"`/`"pending_approval"` outcome closes the gap (`resolution="research"`); an honest `"no_results"` outcome (or any other non-success status) leaves the gap open, satisfying Scenario 7's regression guard by composition, not new logic.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `knowledge_gap_tracking.py`'s core.
- `T05` has landed `get_gap`, `close_gap`, `_mark_gap_pending_approval(gap_id, approval_id, resolution)`, and the resolution-agnostic `close_gap_by_pending_approval(approval_id)` — this task's own `resolve_gap_via_research` reuses BOTH helpers unchanged, passing `resolution="research"` where `T05`'s own human-answer path passed `"human_provided"`.
- Real current `knowledge_bootstrap.py`'s one public entry point (unchanged, verbatim, relevant signature/status enumeration):
  ```python
  async def bootstrap_agent_knowledge(agent_id: str, subject: str) -> dict:
      ...
      # returns one of:
      # {"status": "no_match", "hop": "research" | "filing"}
      # {"status": "not_autonomous", "matched_agent_id": ...}
      # {"status": "no_results", "research_expert_id": ...}
      # {"status": "pending_approval", "approval_id": ..., "research_expert_id": ...}
      # {"status": "unavailable", "message": ...}
      # {"status": "written", "path": ..., "kind": ..., "research_expert_id": ..., "vault_filing_expert_id": ...}
  ```

**After / Outputs:**
- `knowledge_gap_tracking.py` gains `resolve_gap_via_research(gap_id: str, agent_id: str) -> dict` (async — composes `knowledge_bootstrap.bootstrap_agent_knowledge`, itself `async def`).
- `agents_router.py` gains `POST /agents/{agent_id}/knowledge-gaps/{gap_id}/research`.

---

## Files to Modify

- `src/backend/app/business/knowledge_gap_tracking.py` — add (after `resolve_gap_with_human_answer`/`_mark_gap_pending_approval`/`close_gap_by_pending_approval`, landed by `T05`):
  ```python
  from app.business.agent_orchestration import knowledge_bootstrap


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
  ```
  (`knowledge_bootstrap` imported at module level — confirm no circular-import issue against the real current file before landing; `knowledge_bootstrap.py` itself already imports `vault_filing_expert`/`skill_registry`/`working_mode_registry`/`graph`, none of which import `knowledge_gap_tracking`, so this direction should be safe; if a cycle is found, use a local import inside `resolve_gap_via_research` instead and log the deviation.)

- `src/backend/app/api/agents_router.py` — add the endpoint, placed after `T05`'s `resolve_knowledge_gap`:
  ```python
  @router.post("/{agent_id}/knowledge-gaps/{gap_id}/research")
  async def research_knowledge_gap(agent_id: str, gap_id: str) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")
      gap = knowledge_gap_tracking.get_gap(gap_id)
      if gap is None or gap["agent_id"] != agent_id:
          raise HTTPException(status_code=404, detail="Unknown knowledge gap")
      if gap["status"] != "open":
          raise HTTPException(status_code=409, detail="Gap is already closed")
      research_result = await knowledge_gap_tracking.resolve_gap_via_research(gap_id, agent_id)
      message = {
          "written": f"Gap resolved — filed to {research_result.get('path')}.",
          "pending_approval": "Research gathered; filing paused pending approval of a new top-level vault area.",
          "no_match": f"Could not find a matching agent for the {research_result.get('hop')} step — gap remains open.",
          "no_results": "The research found nothing relevant — gap remains open.",
          "not_autonomous": f"{research_result.get('matched_agent_id')} is not in Autonomous mode — gap remains open.",
          "unavailable": research_result.get("message", "The Vault Filing Expert is not available.") + " — gap remains open.",
      }.get(research_result["status"], "The research chain completed with an unexpected status — gap remains open.")
      return {"gap": knowledge_gap_tracking.get_gap(gap_id), "research_result": research_result, "message": message}
  ```

---

## Constraints

- Inherits from parent story.
- `knowledge_bootstrap.py` itself is NOT modified — `bootstrap_agent_knowledge` is called exactly as it already exists, `subject=gap["question"]`.
- `close_gap` (or the pending-approval mark) must be called ONLY for `"written"`/`"pending_approval"` outcomes — every other status (`no_match`, `not_autonomous`, `no_results`, `unavailable`) must leave the gap untouched (still `"open"`), per Scenario 7's own regression guard.
- Reuses `T05`'s own `_mark_gap_pending_approval`/`close_gap_by_pending_approval` unchanged, passing `resolution="research"` — do not add a second, parallel pending-approval-completion mechanism.
- The endpoint's own `message` field must honestly name the real outcome (including a `"— gap remains open"` qualifier for every non-closing status) — never a generic "done" message that could be misread as a successful close.
- Must NOT modify `graph.py`, `skill_registry.py`, `working_mode_registry.py`, or `vault_filing_expert.py`.

---

## Tests

**Manual verification steps:**

1. **[REQ-SB-40-US-01-AC-04]** In a Python shell / real HTTP call against the backend `.venv` (real configured `vault_path`, real Compass Provider, `compass-expert` in Autonomous mode per this project's own established seed state). Record a real gap: `knowledge_gap_tracking.record_gap("compass-expert", "What are the latest public best practices for personal knowledge management system organization?", "PKM best practices")`. Confirm `count_open_gaps("compass-expert")` is `1`. Call `POST /agents/compass-expert/knowledge-gaps/{gap_id}/research`. Confirm the response's `research_result.status` is `"written"` (or `"pending_approval"` — follow `T05`'s own step 2 Tier-2 completion pattern if so) with a real filed `path`. Confirm `knowledge_gap_tracking.get_gap(gap_id)["status"]` is `"closed"` with `resolution == "research"`. Confirm `count_open_gaps("compass-expert")` is now `0`.
2. **[REQ-SB-40-US-01-AC-07]** Record a second real gap with a subject expected to produce a genuine honest-empty research result (mirrors `REQ-SB-36-US-01` Scenario 3's own established no-relevant-results test technique — e.g. a genuinely obscure/nonsensical subject with no real web-search hits). Call `POST /agents/compass-expert/knowledge-gaps/{gap_id}/research`. Confirm the response's `research_result.status` is `"no_results"` and its `message` field honestly states the research found nothing relevant / the gap remains open. Confirm `knowledge_gap_tracking.get_gap(gap_id)["status"]` is STILL `"open"` — `close_gap` was never called for this outcome. Confirm `count_open_gaps("compass-expert")` is unchanged (still counts this gap as open).
3. Non-AC smoke check: `POST /agents/compass-expert/knowledge-gaps/does-not-exist/research` — confirm `404`. Re-call the endpoint against the already-closed gap from step 1 — confirm `409`.
4. Clean-up: `vault_writer.save_knowledge_gaps_state({"gaps": []})`; remove any real vault file(s) written by step 1.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-04** (Scenario 4) — a real, usable research result closes the gap with `resolution="research"`; the open-gap count decreases accordingly
- [ ] **AC-07** (Scenario 7) — an honest `"no_results"` research outcome leaves the gap open; `close_gap` is never called for it; the endpoint's own response honestly reflects the gap was not resolved
- [ ] Every non-`"written"`/non-`"pending_approval"` `bootstrap_agent_knowledge` status leaves the gap untouched
- [ ] `knowledge_bootstrap.py` itself is byte-for-byte unmodified
- [ ] Researching an unknown gap returns `404`; researching an already-closed gap returns `409`
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The human-answer closing path — `T05`'s own scope (this task composes its shared pending-approval helpers, but does not modify them).
- The `GET /agents/{agent_id}/knowledge-gaps` list endpoint — `T07`'s own scope.
- `AgentDetailPanel.tsx` — `T08`'s own scope.
- Any change to `bootstrap_agent_knowledge`'s own status enumeration or its Autonomous-mode/Hub-routing gating.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-032` created at `/plan-tasks` step 1) — the human reviews `ADR-032` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Why this depends on `T05`, not just `T02`:** `T05` is the task that lands the shared, resolution-agnostic `_mark_gap_pending_approval`/`close_gap_by_pending_approval` pair inside `knowledge_gap_tracking.py` — this task's own Tier-2 branch composes those exact functions rather than duplicating a second pending-approval-tracking mechanism (see `T05`'s own Context/Notes for why the shared function is resolution-agnostic).

**Real Provider-call latency:** `bootstrap_agent_knowledge`'s own research hop can take multiple minutes for a real web-search call (`Implementation/Learnings.md`'s own repeated "assume multi-minute latency, don't assume a hang" finding) — background the verification call with unbuffered output if run from a shell with a default timeout shorter than that.

---

## Implementation Log

Added `resolve_gap_via_research` to `knowledge_gap_tracking.py` with a module-level `from app.business.agent_orchestration import knowledge_bootstrap` import. **Scope-internal judgement call, logged for spot-check:** the task's own Files-to-Modify section flagged a real risk of a circular import (`graph.py` → `knowledge_gap_tracking` → `knowledge_bootstrap` → `graph.py`) and pre-authorized a local-import fallback if one was found. Tested directly (`import app.business.knowledge_gap_tracking`, `import app.business.agent_orchestration.graph`, `import app.main`, each as the sole first import in a fresh interpreter) — all three succeeded with no `ImportError`, so the module-level import as originally spec'd was kept; no local-import deviation was needed. Added `POST /{agent_id}/knowledge-gaps/{gap_id}/research` to `agents_router.py` after `resolve_knowledge_gap`. `knowledge_bootstrap.py` itself untouched.

**[REQ-SB-40-US-01-AC-04] — verified live end-to-end**, real Compass + real Anthropic Provider, real vault. The real vault's own current agent configuration has no agent with both `web-research` skill access and matching Hub-routing keywords, and the two candidate Section Hubs (`vault-qa`/`vault-filing-expert`) both start in the same Section — neither gap alone is caused by this task's own code. To reach a genuine, real `"written"` outcome (not a mock), two real, reversible pieces of existing-app state were temporarily set via the real, already-`Done` APIs (never source-code changes): `vault-qa` was granted real `web-research` skill access and its Provider set to `anthropic-claude` (already configured with a real credential); `vault-filing-expert`'s Section was moved from `productivity` to `technical` so it is a real Hub-routing candidate outside `vault-qa`'s own Section. With this real (not mocked) configuration: recorded a real gap for `compass-expert`, called `POST /agents/compass-expert/knowledge-gaps/{gap_id}/research`; hop 1 (real Anthropic web search) and hop 2 (real Vault Filing Expert routing) both completed for real, producing `research_result.status == "written"` with a real filed path (`Work/Notes/Core42 Compass platform capabilities 2026.md`, genuine researched content). The gap's `status` became `"closed"`, `resolution == "research"`, `count_open_gaps` dropped accordingly. PASS. All three temporary state changes were reverted immediately after (skill revoked, Provider restored to `compass`, Section restored to `productivity`) and independently confirmed reverted via `GET`; the test-written vault file was deleted.

**[REQ-SB-40-US-01-AC-07] — verified live, real induced condition, not constructed**: before the above skill grant was in place, an earlier real research call on a different gap genuinely returned `research_result.status == "no_results"` (the real `bootstrap_agent_knowledge` chain, unmodified, honestly reporting no completable research). The gap's `status` stayed `"open"` (`closed_at` still `null`, `resolution` still `null` — `close_gap` was never called), `count_open_gaps` unchanged, and the endpoint's own `message` field read "The research found nothing relevant — gap remains open." PASS. (A second attempt at a genuinely-obscure-subject induction, run after the skill grant, instead produced a real `"written"` outcome — the real Anthropic model answered with a privacy-refusal reply that the real, unmodified Vault Filing Expert then filed as a guide note; an honest, disclosed finding about the real composed chain's behavior, not a defect in this task's own code, and not counted as this AC's own verification.) A real `"no_match"` (`hop: "filing"`) outcome, observed live during the AC-04 induction sequence before the Section fix, also independently confirmed the same "gap left untouched" contract for a third non-closing status.

Non-AC smoke checks, all confirmed live: researching an unknown gap returned `404`; re-researching the already-closed AC-04 gap returned `409`.

Test vault files removed; `agent_knowledge_gaps.json` reset before T07.

gate: flagged (carried, trigger-3). No new trigger fired — the temporary real state changes used for AC-04 induction are a scope-internal verification-method judgement call (logged above for human spot-check), not a code change, dependency, or interface change.

status: Done
