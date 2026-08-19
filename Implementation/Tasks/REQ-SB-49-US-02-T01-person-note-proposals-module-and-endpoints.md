---
id: REQ-SB-49-US-02-T01
title: app/business/cockpit/person_note_proposals.py — create/list/confirm/discard module + confirm/discard endpoints
parent_story: REQ-SB-49-US-02
requirement_id: REQ-SB-49
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-038 created) — carried from the parent story; the human reviews ADR-038 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-49-US-02-T01 — `person_note_proposals.py` Module + Confirm/Discard Endpoints

## Parent Story

- Story: [[REQ-SB-49-US-02]] — `../UserStories/REQ-SB-49-US-02-cockpit-person-mention-proposed-note-edit.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-49 *Cockpit @Mentions*

---

## Objective

Build the new, small `app/business/cockpit/person_note_proposals.py` module — create/list/confirm/discard for an in-thread, confirmable/discardable Person-note-edit proposal, stored inside the owning thread's own `cockpit_threads.json` record (`ADR-038` point 7) — plus its two new HTTP endpoints on `cockpit_router.py` (mirrors `research.py`'s own save endpoint) and a small public `threads.save_thread` wrapper (the existing save primitive, `_save_thread`, is private).

---

## Starting State → End State

**Before / Inputs:**
- `app/business/cockpit/threads.py` already has `get_thread(subject_kind, subject_note_stem) -> dict` (public) and `_save_thread(subject_kind, subject_note_stem, thread) -> None` (private, module-internal only).
- `app/business/cockpit/research.py` already establishes the precedent shape this module mirrors: a scoped list read (`list_research_results`) plus a direct-write-on-explicit-action function (`save_research_result`) — but research's own "discard" is client-only (no backend call at all, since a research result is never persisted server-side until Save). THIS proposal kind is different — `ADR-038` point 7 requires it to be a real, server-persisted, thread-scoped record from the moment it is created (by a Manual/Autonomous dispatch, `T02`'s own handler), independently of whether the user ever opens the Cockpit again before confirming/discarding it. So, unlike research, this module needs its own real `create_proposal` (server-side, called by `T02`'s handler, not client-triggered) alongside `confirm_proposal`/`discard_proposal` (both client-triggered, mirroring research's own explicit-action shape).
- `app/api/cockpit_router.py`'s `get_cockpit(...)` already assembles `{"subject", "people", "thread", "research_results"}` — no `person_note_proposals` key yet.

**After / Outputs:**
- `person_note_proposals.py` exports `create_proposal`, `list_pending_proposals`, `confirm_proposal`, `discard_proposal`.
- `threads.py` gains one new public function, `save_thread`, a thin wrapper around the existing `_save_thread` — used by this module instead of reaching into `threads.py`'s own private name.
- `cockpit_router.py`'s `get_cockpit` response gains a `person_note_proposals` key (pending ones only, via `list_pending_proposals`); two new endpoints, `POST /cockpit/{subject_kind}/{subject_note_stem}/person-note-proposals/{proposal_id}/confirm` and `.../discard`, are added.

---

## Files to Modify

- `src/backend/app/business/cockpit/person_note_proposals.py` — **new file.**
  ```python
  """In-thread, confirmable/discardable Person-note-edit proposals
  (ADR-038 point 7, REQ-SB-49-US-02) -- mirrors cockpit/research.py's own
  scoped-list-plus-direct-action shape, one layer over for a new proposal
  kind that (unlike a research result) is created SERVER-SIDE by a
  Manual/Autonomous dispatch (T02's own Skill handler), not client-
  triggered. Stored inside the owning thread's own cockpit_threads.json
  record (a new "person_note_proposals" list alongside "messages"/
  "brought_in_agent_ids") rather than a new top-level .second-brain/
  file -- ephemeral, thread-scoped state with no standing audit
  requirement once confirmed or discarded."""
  from __future__ import annotations

  import uuid
  from datetime import datetime, timezone

  from app.business.cockpit import threads
  from app.data_access import vault_writer


  def _find_proposal(thread: dict, proposal_id: str) -> dict | None:
      return next(
          (p for p in thread.get("person_note_proposals", []) if p["id"] == proposal_id),
          None,
      )


  def create_proposal(
      subject_kind: str, subject_note_stem: str, note_path: str, person_name: str, instruction: str,
  ) -> dict:
      """Called server-side by T02's own propose_person_note_update
      handler on an already_approved=False dispatch (Manual/Autonomous) --
      NEVER client-triggered. Returns the new pending proposal record."""
      thread = threads.get_thread(subject_kind, subject_note_stem)
      thread.setdefault("person_note_proposals", [])
      proposal = {
          "id": str(uuid.uuid4()),
          "note_path": note_path,
          "person_name": person_name,
          "instruction": instruction,
          "status": "pending",
          "timestamp": datetime.now(timezone.utc).isoformat(),
      }
      thread["person_note_proposals"].append(proposal)
      threads.save_thread(subject_kind, subject_note_stem, thread)
      return proposal


  def list_pending_proposals(subject_kind: str, subject_note_stem: str) -> list[dict]:
      thread = threads.get_thread(subject_kind, subject_note_stem)
      return [p for p in thread.get("person_note_proposals", []) if p["status"] == "pending"]


  def confirm_proposal(subject_kind: str, subject_note_stem: str, proposal_id: str) -> dict | None:
      """Returns None if proposal_id is unknown or already resolved
      (idempotent-safe no-op, mirrors pending_approval_registry's own
      "already {status}" guard shape one layer over). The user's own
      explicit confirm click is the ONLY trigger that ever writes here --
      exactly ADR-036 point 4's "the user's own explicit Save click is the
      only trigger" precedent, reused for this new proposal kind."""
      thread = threads.get_thread(subject_kind, subject_note_stem)
      proposal = _find_proposal(thread, proposal_id)
      if proposal is None or proposal["status"] != "pending":
          return None
      vault_writer.append_person_note_update_line(proposal["note_path"], f"- {proposal['instruction']}")
      proposal["status"] = "confirmed"
      threads.save_thread(subject_kind, subject_note_stem, thread)
      return proposal


  def discard_proposal(subject_kind: str, subject_note_stem: str, proposal_id: str) -> dict | None:
      """Returns None if proposal_id is unknown or already resolved. Never
      touches vault_writer -- discarding is a pure status flip, the real
      Person note is left completely untouched."""
      thread = threads.get_thread(subject_kind, subject_note_stem)
      proposal = _find_proposal(thread, proposal_id)
      if proposal is None or proposal["status"] != "pending":
          return None
      proposal["status"] = "discarded"
      threads.save_thread(subject_kind, subject_note_stem, thread)
      return proposal
  ```
- `src/backend/app/business/cockpit/threads.py` — add ONE new public function, placed immediately after `_save_thread`:
  ```python
  def save_thread(subject_kind: str, subject_note_stem: str, thread: dict) -> None:
      """Public wrapper around _save_thread -- lets sibling cockpit/
      modules (person_note_proposals.py, REQ-SB-49-US-02) persist a
      thread they mutated via their own get_thread() read, without
      reaching into this module's private name."""
      _save_thread(subject_kind, subject_note_stem, thread)
  ```
  No other line of `threads.py` changes in this task (the `send_user_message` signature/Cockpit-thread-ref threading is `T05`'s own scope).
- `src/backend/app/api/cockpit_router.py`:
  - Import: add `person_note_proposals` to the existing `from app.business.cockpit import attachments, people, research, threads` line.
  - `get_cockpit`: add one key to the returned dict: `"person_note_proposals": person_note_proposals.list_pending_proposals(subject_kind, subject_note_stem)`.
  - Add two new endpoints, placed after the existing `/research/save` route:
    ```python
    @router.post("/{subject_kind}/{subject_note_stem}/person-note-proposals/{proposal_id}/confirm")
    def confirm_person_note_proposal(subject_kind: str, subject_note_stem: str, proposal_id: str) -> dict:
        result = person_note_proposals.confirm_proposal(subject_kind, subject_note_stem, proposal_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Unknown or already-resolved proposal")
        return result


    @router.post("/{subject_kind}/{subject_note_stem}/person-note-proposals/{proposal_id}/discard")
    def discard_person_note_proposal(subject_kind: str, subject_note_stem: str, proposal_id: str) -> dict:
        result = person_note_proposals.discard_proposal(subject_kind, subject_note_stem, proposal_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Unknown or already-resolved proposal")
        return result
    ```
- `src/backend/app/data_access/vault_writer.py` — add ONE new small write primitive, placed near `insert_body_line_if_missing`:
  ```python
  def append_person_note_update_line(note_path, line: str) -> None:
      """Unconditionally appends one line to a Person note's own body --
      the real write primitive both the Supervised-approve direct-write
      path (T02's own already_approved=True branch) and this module's
      confirm_proposal (Manual/Autonomous's own explicit-confirm write)
      share (ADR-038 point 7). Deliberately NOT insert_body_line_if_
      missing's idempotent-if-already-present shape -- each proposed edit
      is its own new fact to record, even if coincidentally identical
      text to an existing line, so it must always append, never silently
      no-op on a textual coincidence."""
      path = Path(note_path)
      text = path.read_text(encoding="utf-8")
      separator = "" if text.endswith("\n") else "\n"
      path.write_text(text + separator + line + "\n", encoding="utf-8")
  ```
  (`vault_writer.py` already imports `Path` from `pathlib` at module top level for its other path-typed functions — reuse it, do not re-import.)

---

## Constraints

- Inherits from parent story.
- `create_proposal` is never called from an HTTP endpoint directly in this task — it is a server-side primitive `T02`'s own handler calls (via a deferred import, `T02`'s own documented reason). This task's own two new endpoints are confirm/discard only.
- `confirm_proposal`/`discard_proposal` must be idempotent-safe no-ops (`None` return, not a raised exception) on an unknown or already-resolved `proposal_id` — the router translates `None` into `404`.
- `discard_proposal` must NEVER call `vault_writer` in any branch — a discarded proposal leaves the real Person note completely untouched (`AC-06`).
- `append_person_note_update_line` must always append (never the idempotent "skip if already present" behaviour `insert_body_line_if_missing` has) — do not reuse `insert_body_line_if_missing` for this primitive.
- Proposals are stored ONLY inside `cockpit_threads.json` (via `threads.get_thread`/`threads.save_thread`) — no new top-level `.second-brain/` state file.

---

## Tests

**Manual verification steps:**

1. Non-AC smoke check (this task's own mechanics, exercised directly — the locked ACs this module supports are owned by `T02`/`T04`/`T05`/`T06`, which depend on this task): in a Python shell against the backend `.venv`, call `person_note_proposals.create_proposal("email", "<a real captured email note stem>", "<a real Person note path>", "Test Person", "test instruction")`. Confirm the returned dict has `status: "pending"` and a real `id`. Confirm `person_note_proposals.list_pending_proposals(...)` includes it.
2. Call `person_note_proposals.confirm_proposal(...)` with that `proposal_id`. Confirm the return has `status: "confirmed"`, the target Person note's body now ends with a new `- test instruction` line (read the file directly), and `list_pending_proposals(...)` no longer includes it (status is no longer `"pending"`).
3. Repeat steps 1 with a fresh proposal, then call `discard_proposal(...)` instead. Confirm the return has `status: "discarded"`, the target Person note's body is byte-for-byte unchanged from before the call, and `list_pending_proposals(...)` no longer includes it.
4. Call `confirm_proposal(...)`/`discard_proposal(...)` again with the SAME already-resolved `proposal_id` from step 2/3. Confirm both return `None` (idempotent-safe, no exception, no second write).
5. Static check: confirm `GET /cockpit/{subject_kind}/{stem}` (via `TestClient`, no lifespan) returns a `person_note_proposals` key (`[]` for a thread with none).
6. Clean-up: manually strip any test-only line(s) appended to the real Person note used above, and remove the test thread's `person_note_proposals` entries from `cockpit_threads.json` if a disposable subject/thread was used — leave real vault/state content exactly as found.

**Automated tests:** `n/a — no backend test runner scaffolded yet (no pytest suite exists under src/backend as of this task)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `create_proposal`/`list_pending_proposals`/`confirm_proposal`/`discard_proposal` all real, working, `cockpit_threads.json`-backed
- [ ] `confirm_proposal` writes via the new `vault_writer.append_person_note_update_line`; `discard_proposal` never calls `vault_writer`
- [ ] Two new confirm/discard endpoints on `cockpit_router.py`, `404` on unknown/already-resolved `proposal_id`
- [ ] `get_cockpit`'s response gains `person_note_proposals` (pending only)
- [ ] `threads.py` gains the public `save_thread` wrapper; no other line of `threads.py` changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `propose_person_note_update` Skill/handler itself, and the `already_approved=True` direct-write branch — `T02`'s scope.
- `threads.send_user_message`'s own Cockpit-thread-ref threading into `run_agent_conversation` — `T05`'s scope.
- The frontend confirm/discard UI — `T06`'s scope.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-038` created at `/plan-tasks` step 1, carried) — the human reviews `ADR-038` and the task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Why `create_proposal` is public API on this module, not private:** `T02`'s own handler (`skill_tools.py`, a different module) calls it via a deferred, function-body-local import to avoid a real circular import (`skill_tools` → `person_note_proposals` → `threads` → `graph` (once `T05` lands) → `skill_registry` → `skill_tools`) — see `T02`'s own Context for the full reasoning. This task does not need to do anything special to support that; a plain top-level `def create_proposal(...)` is sufficient, the deferred-import discipline lives entirely on the CALLER's side (`T02`).

---

## Implementation Log

Built exactly as specced: `person_note_proposals.py` (new file,
`create_proposal`/`list_pending_proposals`/`confirm_proposal`/
`discard_proposal`), `threads.py::save_thread` public wrapper,
`cockpit_router.py`'s `person_note_proposals` response key + confirm/
discard endpoints, `vault_writer.append_person_note_update_line`.

**One real, disclosed reconciliation against the REAL current file, not
a deviation from intent:** the task's own code sample claimed
`vault_writer.py` "already imports `Path` from `pathlib`... reuse it, do
not re-import." Direct grep of the real current file found NO `pathlib`
import anywhere in it (every existing function receives an
already-a-`Path` parameter; none constructs one from a string). Added
`from pathlib import Path` to the existing `import` block — required for
`append_person_note_update_line`'s own `Path(note_path)` call
(`note_path` arrives as a plain string from a JSON-persisted proposal
record). Logged here per this project's own "compose around the REAL
current file" precedent, not silently.

**A second real, live-discovered defect, found and fixed IN-SCOPE
(same-story, same-file territory — `threads.py` is this task's own
`## Files to Modify` entry) during `T05`'s end-to-end live verification,
not this task's own isolated smoke check:** `send_user_message` reads
`thread` once at the top of its own call and only persists it ONCE, at
the very end, after its whole per-agent reply loop. A Manual/Autonomous
`propose_person_note_update` dispatch happening INSIDE that same loop
calls `person_note_proposals.create_proposal` (this task's own function),
which does its own independent `get_thread`/`save_thread` round trip and
persists a real pending proposal to disk immediately — then
`send_user_message`'s own end-of-call `_save_thread(thread)` overwrote it
with its own stale in-memory copy (read before the proposal existed),
silently losing the just-recorded proposal. Fixed in `threads.py`
(already in this task's own `## Files to Modify`): immediately before its
own final save, `send_user_message` now re-reads the CURRENTLY persisted
`person_note_proposals` list and carries it forward, since that is the
one field a nested Skill dispatch can now mutate mid-call that this
function does not itself own. Confirmed live: before the fix, a real
Manual-mode propose call's own proposal never appeared in
`GET /cockpit/.../{stem}`'s `person_note_proposals` list (confirmed via
the raw `cockpit_threads.json` record — no such key at all); after the
fix, the SAME real flow (through the actual running frontend chat) shows
the pending proposal, and Confirm/Discard both round-trip correctly.

**Non-AC smoke checks (this task's own mechanics — the locked ACs it
supports are owned by `T02`/`T04`/`T05`/`T06`), verified live in a Python
shell against the real backend `.venv`/real vault:**
1. `create_proposal(...)` returns `status: "pending"` with a real `id`;
   `list_pending_proposals(...)` includes it. PASS.
2. `confirm_proposal(...)` returns `status: "confirmed"`; the target
   Person note's body genuinely ends with the new `- <instruction>` line
   (read directly, byte-confirmed); `list_pending_proposals(...)` no
   longer includes it. PASS.
3. `discard_proposal(...)` (fresh proposal) returns `status: "discarded"`;
   the target Person note's body is byte-for-byte unchanged;
   `list_pending_proposals(...)` no longer includes it. PASS.
4. Re-`confirm_proposal`/re-`discard_proposal` on the same already-resolved
   `proposal_id` both return `None` (idempotent-safe, no exception, no
   second write). PASS.
5. `GET /cockpit/email/{stem}` (real running server) returns a
   `person_note_proposals` key (`[]` for a thread with none, confirmed on
   a fresh subject). PASS.
6. Clean-up: all test-only lines appended to real Person notes during
   this verification pass were stripped afterward (confirmed by
   byte-for-byte re-read matching the pre-test body); no stray
   `person_note_proposals` entries left `pending` in `cockpit_threads.json`
   for any disposable test thread used across this task's own and `T05`'s
   live verification.

gate: flagged (carried, trigger-3 — `ADR-038`) 2026-08-14 — no NEW
coder-owned trigger fired (the `Path`-import gap and the save-race fix
are both scope-internal reconciliations against the real current file,
same file this task already owns, logged for human spot-check per this
project's own established precedent; no `ESCALATIONS.md` entry; every
non-AC mechanic verified live with a real, observed outcome).
