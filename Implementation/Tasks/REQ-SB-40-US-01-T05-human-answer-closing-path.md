---
id: REQ-SB-40-US-01-T05
title: Human-answer closing path — knowledge_gap_tracking.resolve_gap_with_human_answer + POST /agents/{agent_id}/knowledge-gaps/{gap_id}/resolve
parent_story: REQ-SB-40-US-01
requirement_id: REQ-SB-40
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-032 created) — carried from the parent story; the human reviews ADR-032 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-40-US-01-T02]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-40-US-01-T05 — Human-answer closing path

## Parent Story

- Story: [[REQ-SB-40-US-01]] — `../UserStories/REQ-SB-40-US-01-agent-knowledge-gap-tracking-and-expert-readiness.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-40 *Agent Knowledge-Gap Tracking & Expert Readiness*

---

## Objective

Compose the already-`Done`, already-trusted Vault Filing Expert (`REQ-SB-35-US-01`/`ADR-021`) — never a new correctness-verification step layered on top (`ADR-032` point 3) — so a human's direct answer to an open knowledge gap is filed into the vault unchanged, and the gap closes (`resolution="human_provided"`) only once filing actually completes: immediately for a Tier-1 write, or at Tier-2 approval-finalization time for a new-top-level-area proposal.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `knowledge_gap_tracking.py`'s `record_gap`/`close_gap`/`list_agent_gaps`/`count_open_gaps`.
- Real current `vault_filing_expert.py`'s one public entry point (unchanged, verbatim, relevant signature/return shapes):
  ```python
  def determine_placement_and_file(
      content: str, source_description: str, requesting_agent_id: str
  ) -> dict:
      ...
      return {"status": "written", "path": path, "kind": ..., "tags": ..., "confidence": ...}
      # or, for a new top-level area:
      return {"status": "pending_approval", "approval_id": record["id"]}
      # or, if the Provider is unavailable:
      return {"status": "unavailable", "message": ...}
  ```
- Real current `pending_approvals_router.py`'s `approve_pending_approval` (verbatim, relevant excerpt):
  ```python
  _APPROVAL_HANDLERS = {
      "propose_new_top_level_area": vault_filing_expert.finalize_new_top_level_area,
      "hermes_vault_write": vault_write_tools.finalize_hermes_write,
  }

  @router.post("/{approval_id}/approve")
  def approve_pending_approval(approval_id: str) -> dict:
      record = pending_approval_registry.get_pending_approval(approval_id)
      ...
      if record["action_id"] in _APPROVAL_HANDLERS:
          result = _APPROVAL_HANDLERS[record["action_id"]](record["payload"])
          outcome_message = f"Approved — filed at {result['path']}."
      elif record["action_id"] is not None:
          result = _execute_action(record["agent_id"], record["action_id"])
          outcome_message = result["message"]
      else:
          results = run_capture_for_agent(record["agent_id"])
          outcome_message = f"Approved — background step ran, {len(results)} result(s)."

      resolved = pending_approval_registry.resolve_pending_approval(approval_id, "approved")
      vault_writer.append_agent_history_entry(record["agent_id"], "run_event", outcome_message)
      return _resolved(resolved)
  ```

**After / Outputs:**
- `knowledge_gap_tracking.py` gains `get_gap(gap_id) -> dict | None`, `resolve_gap_with_human_answer(gap_id, agent_id, answer) -> dict`, and `close_gap_by_pending_approval(approval_id, resolution) -> bool` (a gap record additively gains an optional `pending_approval_id` key, set only while a Tier-2 proposal is in flight).
- `agents_router.py` gains `POST /agents/{agent_id}/knowledge-gaps/{gap_id}/resolve`.
- `pending_approvals_router.py`'s `approve_pending_approval` gains one additive call — `knowledge_gap_tracking.close_gap_by_pending_approval(approval_id, "human_provided")` — a no-op for every approval NOT tied to a gap (the overwhelming majority), and the completion of Scenario 3's Tier-2 path for the rare one that is.

---

## Files to Modify

- `src/backend/app/business/knowledge_gap_tracking.py` — add (after `count_open_gaps`):
  ```python
  from app.business import vault_filing_expert


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
  ```
  (`vault_filing_expert` import placed at module level alongside `vault_writer` — confirm no circular-import issue against the real current file before landing; if one exists, use a local import inside `resolve_gap_with_human_answer` instead, mirroring `vault_filing_expert.py`'s own local-import precedent for `pending_approval_registry`, and log the deviation.)

- `src/backend/app/api/agents_router.py`:
  - Add `knowledge_gap_tracking` to the existing `from app.business import (...)` block.
  - Add a request body model, alongside `AgentAssignmentUpdateBody`:
    ```python
    class GapResolveBody(BaseModel):
        answer: str
    ```
  - Add the endpoint, placed after `get_history`:
    ```python
    @router.post("/{agent_id}/knowledge-gaps/{gap_id}/resolve")
    def resolve_knowledge_gap(agent_id: str, gap_id: str, body: GapResolveBody) -> dict:
        agent = agent_registry.get_agent(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Unknown agent")
        gap = knowledge_gap_tracking.get_gap(gap_id)
        if gap is None or gap["agent_id"] != agent_id:
            raise HTTPException(status_code=404, detail="Unknown knowledge gap")
        if gap["status"] != "open":
            raise HTTPException(status_code=409, detail="Gap is already closed")
        filing_result = knowledge_gap_tracking.resolve_gap_with_human_answer(gap_id, agent_id, body.answer)
        return {"gap": knowledge_gap_tracking.get_gap(gap_id), "filing_result": filing_result}
    ```

- `src/backend/app/api/pending_approvals_router.py`:
  - Add `knowledge_gap_tracking` to the existing `from app.business import (...)` import line.
  - In `approve_pending_approval`, add one line immediately after `resolved = pending_approval_registry.resolve_pending_approval(approval_id, "approved")` and before `vault_writer.append_agent_history_entry(...)`:
    ```python
        knowledge_gap_tracking.close_gap_by_pending_approval(approval_id)
    ```
    (Resolution-agnostic — reads which resolution value to apply, `"human_provided"` or `"research"`, from the matched gap's own stored `pending_resolution` field; see `T06` for the delegated-research path that also composes this same function.)

---

## Constraints

- Inherits from parent story.
- `vault_filing_expert.py` itself is NOT modified — `determine_placement_and_file`/`finalize_new_top_level_area` are called exactly as they already exist; the gap↔pending-approval association lives entirely inside `knowledge_gap_tracking.py`'s own state (the additive `pending_approval_id` field), never inside `vault_filing_expert.py`'s own payload shape.
- `close_gap` must never be called before filing genuinely completes — a `"pending_approval"` outcome must NOT close the gap; only `close_gap_by_pending_approval`, called from the real Approve endpoint once `finalize_new_top_level_area` has actually run, may close it for that path.
- `close_gap_by_pending_approval` must be a safe no-op for every `approval_id` not tied to any gap (the ordinary case for every existing `hermes_vault_write`/agent-action approval) — never raises, never mutates state when no match is found.
- `close_gap_by_pending_approval` is resolution-agnostic by design (reads `pending_resolution` off the matched gap itself) — `T06`'s delegated-research path shares this exact function unchanged; do not add a second, parallel completion function for research.
- Must NOT change `pending_approval_registry.py`, `vault_write_tools.py`, or `_APPROVAL_HANDLERS`'s own two existing entries.
- An explicit empty/whitespace-only `answer` is not specially validated this pass — `vault_filing_expert.determine_placement_and_file` receives it as-is; that module's own existing behavior (a low-confidence placement note, or an honest model-driven outcome) governs, not new validation logic here.

---

## Tests

**Manual verification steps:**

1. **[REQ-SB-40-US-01-AC-03]** In a Python shell against the backend `.venv` (real configured `vault_path`, real Compass Provider). Record a real gap: `knowledge_gap_tracking.record_gap("vault-qa", "What is the team's Q3 travel reimbursement policy?", "Q3 travel reimbursement")`. Confirm `knowledge_gap_tracking.count_open_gaps("vault-qa")` is `1`. Call `POST /agents/vault-qa/knowledge-gaps/{gap_id}/resolve` with `{"answer": "The Q3 travel reimbursement policy: submit receipts within 14 days via the finance portal; economy class only for trips under 6 hours."}` (content shaped to land as a Tier-1 write against this vault's real existing taxonomy — confirm which `kind` it resolves to via the response). Confirm the response's `filing_result.status` is `"written"` with a real `path`. Confirm `knowledge_gap_tracking.get_gap(gap_id)["status"]` is now `"closed"` with `resolution == "human_provided"` and a real `closed_at` timestamp. Confirm `knowledge_gap_tracking.count_open_gaps("vault-qa")` is now `0`. Confirm the real vault file at the returned `path` actually exists and contains the submitted answer text.
2. Non-AC smoke check (Tier-2 path, if a real "new top-level area" placement can be induced with genuinely novel content — otherwise log as not independently reachable this pass and rely on static code inspection instead): record a second gap, resolve it with content engineered to trigger a new top-level area proposal. Confirm the response's `filing_result.status` is `"pending_approval"` and `knowledge_gap_tracking.get_gap(gap_id)["status"]` is STILL `"open"` (not prematurely closed). Approve the resulting pending approval via `POST /pending-approvals/{approval_id}/approve`. Confirm `knowledge_gap_tracking.get_gap(gap_id)["status"]` is now `"closed"` with `resolution == "human_provided"`, only after this real approval step.
3. Non-AC smoke check: `POST /agents/vault-qa/knowledge-gaps/{gap_id}/resolve` against an already-closed `gap_id` from step 1 — confirm a `409` response (gap already closed), never a silent double-file or a raw 500.
4. Non-AC smoke check: `POST /agents/vault-qa/knowledge-gaps/does-not-exist/resolve` — confirm a `404` response.
5. Clean-up: `vault_writer.save_knowledge_gaps_state({"gaps": []})`; remove any real vault file(s) written by steps 1/2 during this task's own verification.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-03** (Scenario 3) — a human-provided answer is filed via the unmodified Vault Filing Expert; the gap closes with `resolution="human_provided"` only once filing completes (immediately for Tier-1, at approval-finalization for Tier-2); the open-gap count decreases accordingly
- [ ] `close_gap_by_pending_approval` is a safe no-op for every non-gap-related approval
- [ ] `vault_filing_expert.py` itself is byte-for-byte unmodified
- [ ] Resolving an unknown gap returns `404`; resolving an already-closed gap returns `409`
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The delegated-research closing path — `T06`'s own scope.
- The `GET /agents/{agent_id}/knowledge-gaps` list endpoint — `T07`'s own scope.
- `AgentDetailPanel.tsx` — `T08`'s own scope.
- Any new validation/rejection of the submitted `answer` text beyond what `vault_filing_expert.py` already does.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-032` created at `/plan-tasks` step 1) — the human reviews `ADR-032` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Why `pending_approvals_router.py` is touched here, not left to a separate task:** `ADR-032` point 3 explicitly names "the existing `_APPROVAL_HANDLERS` dispatch table on `pending_approvals_router.py`" as the Tier-2 completion point for this exact closing path — it is inseparable from this task's own Scenario 3 (a Tier-2 gap-closing answer that is never actually closed would be a locked-AC failure), not a distinct concern warranting its own task.

**Why `close_gap_by_pending_approval` is called unconditionally on every approval, not gated by action_id:** simpler and structurally safer than special-casing `propose_new_top_level_area` — it is already a safe no-op (a plain state scan with no match) for every one of this project's other approval kinds (`hermes_vault_write`, any agent-registry action), so no `if` branch is needed to keep it side-effect-free for non-gap approvals.

---

## Implementation Log

Added `get_gap`, `resolve_gap_with_human_answer`, `_mark_gap_pending_approval`, `close_gap_by_pending_approval` to `knowledge_gap_tracking.py` exactly as spec'd, with a module-level `from app.business import vault_filing_expert` import (confirmed no circular-import issue — `vault_filing_expert.py`'s own import chain, `customer_hub_linking`/`partner_hub_linking`/`vault_filing_methodology`/`model_factory`/`vault_writer`, never touches `knowledge_gap_tracking`). Added `GapResolveBody` + `POST /{agent_id}/knowledge-gaps/{gap_id}/resolve` to `agents_router.py` after `get_history`. Added `knowledge_gap_tracking.close_gap_by_pending_approval(approval_id)` to `pending_approvals_router.py::approve_pending_approval`, called unconditionally right after `resolve_pending_approval`. `vault_filing_expert.py` itself untouched.

**[REQ-SB-40-US-01-AC-03] — verified live**, real Compass Provider, real vault: recorded a real gap for `vault-qa` ("What is the team's Q3 travel reimbursement policy?"), confirmed `count_open_gaps == 1`. `POST /agents/vault-qa/knowledge-gaps/{gap_id}/resolve` with a real answer returned `filing_result.status == "written"` with a real `path`. The gap's `status` became `"closed"`, `resolution == "human_provided"`, real `closed_at`, `count_open_gaps` dropped to `0`. Confirmed the real vault file at the returned path exists and contains the submitted answer text. PASS.

**Tier-2 path — attempted live, not independently reached this pass**, per this task's own Tests step 2 fallback ("otherwise log as not independently reachable... rely on static code inspection instead"): a second, deliberately novel-content gap ("staff pet-adoption sponsorship benefits") was resolved live, but the real Vault Filing Expert classified it under the vault's own existing "Guides" catch-all kind (a real Tier-1 write, not Tier-2) — consistent with this project's own prior Learnings finding (`SPRINT-024`) that a broad catch-all kind can absorb genuinely novel content. Relying on static code inspection for the Tier-2 branch: `resolve_gap_with_human_answer`'s `elif filing_result["status"] == "pending_approval"` branch calls `_mark_gap_pending_approval` (never `close_gap`) and `pending_approvals_router.py`'s new `close_gap_by_pending_approval(approval_id)` call is unconditional and reads the resolution from the gap's own stored `pending_resolution` field — both directly composed from `T02`'s own already-live-verified `close_gap`/state-write primitives.

Non-AC smoke checks, all confirmed live: re-resolving the already-closed gap returned `409` ("Gap is already closed"); resolving an unknown `gap_id` returned `404`. `close_gap_by_pending_approval` confirmed a safe no-op (`False`, no exception, no state mutation) for a random non-gap-tied approval id.

Test vault files removed; `agent_knowledge_gaps.json` reset to `{"gaps": []}` before T06.

gate: flagged (carried, trigger-3). No new trigger fired.

status: Done
