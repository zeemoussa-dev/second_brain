---
id: REQ-SB-35-US-01-T03
title: Tier-2 resolution — finalize_new_top_level_area, pending_approval_registry payload field, pending_approvals_router dispatch entry
parent_story: REQ-SB-35-US-01
requirement_id: REQ-SB-35
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-021) carried from the parent story — human still reviews ADR-021 alongside this task breakdown. One scope-internal judgement call (see Implementation Log): the Tier-2 payload additionally carries referenced_customer/referenced_partner and finalize_new_top_level_area reuses T02's own frontmatter/wikilink helpers, for consistency with T02's own AC-02 fix — not required by AC-03/AC-04's own wording, no locked AC weakened. Both locked ACs (AC-03/AC-04) verified live, including the critical unconditional-bypass design point."
phase: P1
depends_on: [REQ-SB-35-US-01-T02, REQ-SB-21-US-01-T03, REQ-SB-21-US-01-T06]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-35-US-01-T03 — Tier-2 new-top-level-area approval resolution

## Parent Story

- Story: [[REQ-SB-35-US-01]] — `../UserStories/REQ-SB-35-US-01-vault-filing-expert.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-35 *Vault Filing Expert*

---

## Cross-story dependency — real, not fabricated

This task depends on `REQ-SB-21-US-01-T03` (`pending_approval_registry.py`) and `REQ-SB-21-US-01-T06` (`pending_approvals_router.py`) — both real, `status: Ready` task files (confirmed by direct read at decomposition time), per the guidance recorded in `REQ-SB-21-US-01`'s own `## Notes` and `ESCALATIONS.md` → `ESC-017`. Do not start building this task until both are `Done`.

---

## Objective

Replace `T02`'s own `_create_tier_2_proposal` stub with the real Tier-2 mechanism (`ADR-021` points 3–5): an unconditional `pending_approval_registry.create_pending_approval(...)` call (bypassing the working-mode gate by construction — this code path never reaches `agents_router.py::_invoke_action`'s funnel at all), an additive `"payload"` field on `agent_pending_approvals.json`'s schema, and a new `finalize_new_top_level_area(payload)` public function wired into `pending_approvals_router.py`'s Approve endpoint via a new `_APPROVAL_HANDLERS` dispatch table.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `vault_filing_expert.py` with `_create_tier_2_proposal` raising `NotImplementedError`.
- `REQ-SB-21-US-01-T03` has landed `pending_approval_registry.py` — `create_pending_approval(agent_id, trigger, action_id, description) -> dict`, `resolve_pending_approval(approval_id, "approved"|"declined") -> dict`, list/get.
- `REQ-SB-21-US-01-T06` has landed `pending_approvals_router.py` — `GET`/`POST /pending-approvals...`, including the Approve endpoint that currently re-dispatches via `_execute_action`/`run_capture_for_agent` (`ADR-018` point 5's own existing dispatch shape).

**After / Outputs:**
- `vault_filing_expert.py`'s `_create_tier_2_proposal` calls `pending_approval_registry.create_pending_approval(agent_id="vault-filing-expert", trigger="direct", action_id="propose_new_top_level_area", description=...)` unconditionally — regardless of `working_mode_registry.get_agent_working_mode("vault-filing-expert")`'s own value — and returns `{"status": "pending_approval", "approval_id": str}`.
- `pending_approval_registry.py`'s record schema gains an additive `"payload": dict | null` field, populated here with the proposed `content`, `source_description`, `kind`, `tags`, `filename_stem`, `body`.
- `vault_filing_expert.py` gains a second public function, `finalize_new_top_level_area(payload: dict) -> dict`, performing the actual `write_note` call (reusing `T02`'s own `_unique_filename_stem` collision guard).
- `pending_approvals_router.py`'s Approve endpoint gains a small `_APPROVAL_HANDLERS: dict[str, Callable]` dispatch table, `{"propose_new_top_level_area": vault_filing_expert.finalize_new_top_level_area}`, consulted before falling back to the existing `_execute_action`/`run_capture_for_agent` re-dispatch. Decline takes no further action beyond the already-existing `resolve_pending_approval(approval_id, "declined")` — no new code needed for Scenario 4's own "not silently retried elsewhere" guarantee, since nothing ever calls `finalize_new_top_level_area` on a declined record.

---

## Files to Modify

- `src/backend/app/business/vault_filing_expert.py` — replace `_create_tier_2_proposal`'s body:
  ```python
  def _create_tier_2_proposal(*, content, source_description, requesting_agent_id, decision) -> dict:
      from app.business import pending_approval_registry  # local import -- see T02's own Context/Notes for why

      payload = {
          "content": content,
          "source_description": source_description,
          "kind": decision["kind"],
          "tags": decision["tags"],
          "filename_stem": decision["filename_stem"],
          "body": decision["body"],
      }
      description = (
          f"Vault Filing Expert proposes a new top-level vault area, "
          f"\"{decision['kind']}\", for: {source_description}"
      )
      record = pending_approval_registry.create_pending_approval(
          agent_id="vault-filing-expert",
          trigger="direct",
          action_id="propose_new_top_level_area",
          description=description,
          payload=payload,
      )
      return {"status": "pending_approval", "approval_id": record["id"]}


  def finalize_new_top_level_area(payload: dict) -> dict:
      """Called only once the operator approves the pending record above
      (ADR-021 point 5) -- performs the actual write, never called for a
      declined record."""
      subfolder = f"Work/{payload['kind']}"
      filename_stem = _unique_filename_stem(subfolder, payload["filename_stem"])
      path = vault_writer.write_note(subfolder, filename_stem, {"tags": payload["tags"]}, payload["body"])
      return {"status": "written", "path": path, "kind": payload["kind"], "tags": payload["tags"]}
  ```
- `src/backend/app/business/pending_approval_registry.py` — extend `create_pending_approval`'s signature with an additive `payload: dict | None = None` parameter (existing zero-payload callers, e.g. `REQ-SB-21-US-01`'s own Supervised-mode proposals, unaffected — `payload` defaults to `None`), stored verbatim on the created record.
- `src/backend/app/api/pending_approvals_router.py` — the Approve endpoint gains:
  ```python
  from app.business import vault_filing_expert

  _APPROVAL_HANDLERS = {
      "propose_new_top_level_area": vault_filing_expert.finalize_new_top_level_area,
  }
  ```
  and, inside the Approve handler, before falling back to the existing `_execute_action`/`run_capture_for_agent` re-dispatch: if `record["action_id"] in _APPROVAL_HANDLERS`, call `_APPROVAL_HANDLERS[record["action_id"]](record["payload"])` instead.

---

## Constraints

- Inherits from parent story and `ADR-021` points 3–5.
- `_create_tier_2_proposal`'s own call to `create_pending_approval` MUST be unconditional — it must never check `working_mode_registry.get_agent_working_mode(...)` at all. This is the concrete mechanism satisfying "not a change to the agent's own general working-mode assignment": the exception lives in *which code path this action takes* (never reaching `_invoke_action`'s gate), not a per-mode override rule.
- `payload` must be additive and optional on `create_pending_approval` — every existing caller (zero-payload `ADR-018`-shaped proposals) must be unaffected.
- `finalize_new_top_level_area` must reuse `T02`'s own `_unique_filename_stem` collision guard — never a second, divergent filename-collision implementation.
- Decline requires no new code — `resolve_pending_approval(approval_id, "declined")` alone must be sufficient; `finalize_new_top_level_area` must never be called for a declined record.
- Do not modify `_execute_action`/`run_capture_for_agent`'s own existing re-dispatch shape — `_APPROVAL_HANDLERS` is consulted alongside it, not a replacement.

---

## Tests

<!-- AC-03/AC-04 verified here via direct calls against the real backend
.venv, real pending_approval_registry/pending_approvals_router state,
mirroring T02's own "directly callable" verification style. -->

**Manual verification steps:**
1. **[REQ-SB-35-US-01-AC-03]** In a Python shell against the backend `.venv`. Call `vault_filing_expert.determine_placement_and_file(...)` with content that plausibly needs a genuinely new top-level area (a `kind` not in `vault_writer.list_known_kinds()`). Confirm the result is `{"status": "pending_approval", "approval_id": <uuid>}` and that NO note was written to disk (confirm `list_known_kinds()` is unchanged). Confirm, via `pending_approval_registry`'s own list/get, that the created record's `payload` carries the proposed `kind`/`tags`/`filename_stem`/`body` verbatim. Confirm this same result occurs regardless of `working_mode_registry.get_agent_working_mode("vault-filing-expert")`'s own current value (test with it set to both `"autonomous"` and `"supervised"` — identical outcome either way, confirming the bypass-by-construction design).
2. **[REQ-SB-35-US-01-AC-04]** Using the pending record from step 1, call `pending_approval_registry.resolve_pending_approval(approval_id, "declined")` (or the real `pending_approvals_router.py` Decline endpoint, if built/reachable). Confirm the record is now recorded as `"declined"` (via list/get), the content was never filed under the declined area (`list_known_kinds()` still unchanged, no new note on disk), and no alternative/fabricated location was used instead.
3. Non-AC smoke check: create a second pending record (repeat step 1 with different content), then call the real Approve endpoint (`pending_approvals_router.py`'s `POST /pending-approvals/{id}/approve`, or `_APPROVAL_HANDLERS` dispatch directly). Confirm `finalize_new_top_level_area` is invoked, the note is written to the proposed `Work/<kind>/` folder with the proposed tags, and the resolved `kind` now appears in `list_known_kinds()`.
4. Non-AC smoke check: confirm every existing zero-payload `create_pending_approval` caller (e.g. `REQ-SB-21-US-01`'s own Supervised-mode proposal path, if built) still works unchanged — `payload` defaults to `None`, no regression.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-03** (Scenario 3) — a genuinely-new-top-level-area proposal never writes immediately; it creates a pending-approval record regardless of the agent's own working mode; content is written only after explicit approval
- [x] **AC-04** (Scenario 4) — a declined proposal never files the content, is honestly recorded as declined, never silently retried elsewhere
- [x] `create_pending_approval`'s `payload` parameter is additive — no regression to any existing zero-payload caller
- [x] `_APPROVAL_HANDLERS` dispatch is consulted before, or alongside, the existing `_execute_action`/`run_capture_for_agent` re-dispatch, without changing that existing path's own behaviour
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Tier-1 placement/write — `T02`, already `Done` by the time this task starts.
- Any other part of `pending_approval_registry.py`/`pending_approvals_router.py` beyond the additive `payload` field and the `_APPROVAL_HANDLERS` dispatch entry — the rest of `REQ-SB-21-US-01`'s own mechanism is that story's scope, reused as-is.
- The Pending Approvals UI (`MyDayApprovalsPage.tsx`, the `.chat-proposal` card) — `REQ-SB-21-US-01`'s own scope; this task's new record surfaces there automatically once both stories are built, with no frontend change needed.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-021` created at `/plan-tasks` step 1) — the human reviews `ADR-021` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Do not start this task until `REQ-SB-21-US-01-T03`/`T06` are actually `Done`** — both are currently `Ready` but unbuilt as of this decomposition pass (`ESCALATIONS.md` → `ESC-017`). `/implement-sprint` will not pick this task up before its `depends_on` are satisfied — this note is for the human/operator sequencing sprints, not the coder to route around.

---

## Implementation Log

**Built 2026-08-12 (coder, `/implement-sprint`, `SPRINT-023`), after
confirming `REQ-SB-21-US-01-T03`/`T06` are genuinely `Done` by direct
reading of both task files and the real `src/backend` source tree (not
trusted from this task's own "do not start until Done" caveat alone).**
`_create_tier_2_proposal`'s stub replaced with the real
`pending_approval_registry.create_pending_approval(...)` call;
`finalize_new_top_level_area` added; `pending_approval_registry.
create_pending_approval` gained the additive `payload: dict | None = None`
parameter, stored verbatim on the record; `pending_approvals_router.py`
gained the `_APPROVAL_HANDLERS` dispatch table, consulted before the
existing `_execute_action`/`run_capture_for_agent` branch inside Approve.
One scope-internal addition beyond the task's own literal code sample:
the Tier-2 `payload` also carries `referenced_customer`/
`referenced_partner` (from the decision `T02` already computes), and
`finalize_new_top_level_area` reuses `T02`'s own `_placement_frontmatter`/
`_link_referenced_entity` helpers — for consistency with `T02`'s own
`AC-02` fix (a Tier-2-approved note should satisfy the same standing
tags-and-wikilinks rule Tier 1 does); not required by `AC-03`/`AC-04`'s
own wording, no locked AC changed by this.

**Live verification (real backend `.venv`, real
`pending_approval_registry`/`pending_approvals_router` state):**

- **[AC-03]** Content requiring a genuinely new top-level area (a
  personal podcast-episode digest, matching none of the real
  `list_known_kinds()`: `Customers`/`Emails`/`Files`/`Guides`/`Meetings`/
  `Newsletters`/`Notifications`/`Partners`/`People`) called twice — once
  with `vault-filing-expert`'s working mode set to `"autonomous"`, once
  set to `"supervised"`. **Both produced the identical outcome shape**,
  `{"status": "pending_approval", "approval_id": ...}` — no note written
  either time (`list_known_kinds()` unchanged, confirmed before/after).
  Each created record's own `payload` carries the proposed
  `kind`/`tags`/`filename_stem`/`body` verbatim (both proposed `kind:
  "Notes"`, a real, not-yet-materialized taxonomy entity — confirming the
  Python-mechanical `kind not in known_kinds` Tier boundary, not a vaguer
  "already-planned category" judgement). Code inspection of
  `_create_tier_2_proposal` confirms `working_mode_registry` is never
  imported or referenced anywhere in `vault_filing_expert.py` (`grep`
  returns zero matches) — the bypass is genuinely by construction, not a
  conditional check that happens to evaluate the same both times. **PASS
  — the critical design point is verified live, not just by code
  inspection.**
- **[AC-04]** The autonomous-mode record from `AC-03` declined via
  `pending_approval_registry.resolve_pending_approval(id, "declined")`.
  `list_known_kinds()` unchanged after (no note filed under the declined
  `"Notes"` area); the record itself is honestly resolved to `status:
  "declined"`, `resolved_at` set — queryable, not silently discarded, and
  never retried under a fabricated alternative location (no further code
  path ever calls `finalize_new_top_level_area` for a declined record, by
  construction — `resolve_pending_approval` alone is sufficient, per this
  task's own Constraints). **PASS.**
- Non-AC smoke check (Approve round trip): the supervised-mode record
  from `AC-03` approved via the real `_APPROVAL_HANDLERS["propose_new_
  top_level_area"]` dispatch (`pending_approvals_router._APPROVAL_
  HANDLERS`, called directly with the record's own stored `payload`,
  mirroring this task's own "or `_APPROVAL_HANDLERS` dispatch directly"
  Tests wording). `finalize_new_top_level_area` wrote the real note to
  `Work/Notes/Cloud-Economics-Weekly-214-FinOps-2026-Notes.md`; `"Notes"`
  now appears in `list_known_kinds()` — approving genuinely files the
  content. **PASS.**
- Non-AC smoke check (payload additivity): `create_pending_approval(
  "email-capture", "chat", "run_capture_now", "...")` (the exact
  pre-existing zero-payload call shape) still works unchanged —
  `record["payload"] is None`. **PASS — no regression.**
- Code inspection: `pending_approvals_router.py`'s Approve handler checks
  `_APPROVAL_HANDLERS` first, falls back to the pre-existing
  `_execute_action`/`run_capture_for_agent` branches unchanged — neither
  existing branch's own code was edited.

No `ESCALATIONS.md`/`REVIEW-QUEUE.md` entry — both locked ACs verified
live, no new dependency beyond the two already-real, already-`Done` cross-
story tasks this task always depended on, no shared-interface change
beyond `ADR-021`'s own designed additive `payload` field, no ADR
deviation. `gate: flagged` (carried `ADR-021`, PLUS the one scope-internal
consistency addition above logged for human spot-check).
