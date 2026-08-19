---
id: REQ-SB-39-US-01-T07
title: agents_router.py — trigger_action/chat() dispatch fork to skill_registry.invoke_skill for migrated ids
parent_story: REQ-SB-39-US-01
requirement_id: REQ-SB-39
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgement call — result-shape translation bug in the task's own sample code fixed; honest disclosure that the migrated reply TEXT is not byte-identical to the pre-migration Action reply (ADR-028-sanctioned)"
phase: P1
depends_on: [REQ-SB-39-US-01-T01, REQ-SB-39-US-01-T02, REQ-SB-39-US-01-T05]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-39-US-01-T07 — agents_router.py — dispatch fork

## Parent Story

- Story: [[REQ-SB-39-US-01]] — `../UserStories/REQ-SB-39-US-01-unify-capabilities-model-and-read-only-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-39 *Unify Agent Capabilities Under Skills*

---

## Objective

In `trigger_action` and `chat()`, route any matched/requested id that is a
member of `skill_tools.SKILLS` to `skill_registry.invoke_skill(agent_id,
id, args=None, trigger=...)` instead of `_invoke_action(agent_id, id,
trigger=...)`; every other id (the still-real Actions:
`run_capture_now`, `pause_schedule`, `rebuild_person_note`,
`build_knowledge`) keeps calling `_invoke_action` exactly as today
(`ADR-028` point 3). Add a small result-shape translation so
`invoke_skill`'s varying return shapes normalize into the `{"status",
"message"}` envelope this router's existing post-dispatch code already
expects.

---

## Starting State → End State

**Before / Inputs:**
- `trigger_action` calls `_invoke_action(agent_id, action_id,
  trigger="direct")` unconditionally, for any `action_id`.
- `chat()` calls `_invoke_action(agent_id, matched["matched_action_id"],
  trigger="chat")` unconditionally, for any matched id.

**After / Outputs:**
- A new small helper, e.g.:
  ```python
  def _invoke_capability(agent_id: str, capability_id: str, trigger: str) -> dict:
      """Routes a capability id that is a skill_tools.SKILLS member to
      skill_registry.invoke_skill, translating its varying result shapes
      into the same {"status", "message"} envelope _invoke_action's
      callers already expect (ADR-028 point 3)."""
      result = skill_registry.invoke_skill(agent_id, capability_id, args=None, trigger=trigger)
      if result["status"] == "unknown_skill":
          # Defensive only -- capability_id is already confirmed a
          # skill_tools.SKILLS member by the caller before this is reached.
          return {"status": "error", "message": "This capability is not registered."}
      if result["status"] == "refused":
          return {"status": "refused", "message": result["reason"]}
      # A skill handler's own {"available": bool, "message": str} shape
      # (T01's stub handlers, and web_research) maps onto the same
      # {"status", "message"} envelope _execute_action already uses for
      # "not yet available" (status "error") vs. a real result (status "ok").
      return {
          "status": "ok" if result.get("available", True) else "error",
          "message": result.get("message", ""),
      }
  ```
  — called from both `trigger_action` and `chat()` whenever the resolved
  id is a `skill_tools.SKILLS` member; `_invoke_action` is called exactly
  as today for every other id.
- `trigger_action` passes `trigger="direct"`; `chat()` passes
  `trigger="chat"` — the exact same values these call sites already pass
  to `_invoke_action` today.
- The existing post-dispatch history-append gating
  (`result["status"] not in ("pending", "refused") and not
  result.get("history_recorded")`) works unchanged against the translated
  shape — no change to that gating logic itself.

---

## Files to Modify

- `src/backend/app/api/agents_router.py` — add the `skill_registry`/
  `skill_tools` imports, the new `_invoke_capability` helper, and the
  membership-check fork inside `trigger_action` and `chat()`.

---

## Constraints

- Inherits from parent story and `ADR-028` point 3.
- The membership check (`id in skill_tools.SKILLS`) is the **only** new
  "is this migrated" logic — do NOT introduce a separate migrated-id
  constant/list; `ADR-028` explicitly rejects this as redundant
  bookkeeping that could drift from the catalog itself.
- `trigger_action` passes `trigger="direct"`; `chat()` passes
  `trigger="chat"` — do not invent new values.
- The existing post-dispatch gating in both `trigger_action` and `chat()`
  (history-append conditions, `reply`/`action_triggered` assembly) must
  work **unchanged** against `_invoke_capability`'s translated
  `{"status", "message"}` shape — do not modify that gating logic itself.
- Do NOT modify `agent_registry.py` or `agent_chat.py` — the chat funnel's
  own matching logic (`agent_chat.handle_chat_message`) stays completely
  untouched; only the dispatch step after a match changes.
- `_invoke_action` / `_execute_action` / `_execute_async_action` are left
  completely unchanged — still the only path for every still-real Action
  id.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-39-US-01-AC-03] Direct trigger, after `T05`'s retrofit grant
   exists: `POST /agents/vault-qa/actions/ask_question` (or the equivalent
   direct function call to `trigger_action`) — confirm the reply is the
   same honest "not yet available" message `ask_question` produced before
   this migration (no behaviour change observable).
2. [REQ-SB-39-US-01-AC-04] Chat trigger: `POST /agents/email-capture/chat`
   with the message `"view last run"` (an existing, real trigger phrase) —
   confirm `agent_chat.handle_chat_message` still matches
   `view_last_run` as `matched_action_id`, the dispatch now routes through
   `skill_registry.invoke_skill(..., trigger="chat")` (not
   `_invoke_action`), and the reply text is unchanged from before
   migration.
3. [REQ-SB-39-US-01-AC-05] Temporarily grant a migrated capability to an
   agent that has never carried it as either an Action or a Skill (e.g.
   `view_last_run` to `vault-filing-expert`, which carries zero actions
   today) — invoke it via `trigger_action` — confirm it produces the
   identical honest-unavailable reply an already-shipped agent (e.g.
   `email-capture`) invoking the same capability produces. Revoke
   afterward so `vault-filing-expert`'s real state is unaffected by this
   smoke check.
4. [REQ-SB-39-US-01-AC-06] Temporarily revoke `ask_question` from
   `vault-qa` (or use an agent that never had it granted), then invoke it
   via chat or direct trigger — confirm the reply is an honest refusal
   (`skill_registry.invoke_skill`'s `"refused"` result, translated into
   the chat/direct reply) and confirm, via `vault_writer.
   load_agent_history(agent_id)` before/after, that **no new `run_event`
   history entry was appended** for this call. Re-grant afterward to
   restore `vault-qa`'s real post-retrofit state.
5. Non-AC smoke check: confirm a still-real Action id is unaffected —
   `trigger_action("email-capture", "run_capture_now")` still routes
   through `_invoke_action` exactly as before this task (unchanged
   Provider-availability / working-mode-gate behaviour).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `trigger_action`/`chat()` route any id in `skill_tools.SKILLS` to
      `skill_registry.invoke_skill(...)` instead of `_invoke_action(...)`
- [ ] Every other id keeps calling `_invoke_action` exactly as today
- [ ] `_invoke_capability`'s result-shape translation normalizes
      `invoke_skill`'s result into `{"status", "message"}`
- [ ] No separate migrated-id constant introduced — membership check only
- [ ] `agent_registry.py` / `agent_chat.py` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `get_agent()`'s response shape change (`T08`).
- Any gating logic that reads `trigger`/`mutates` together
  (`REQ-SB-39-US-02`).

---

## Context / Notes

`ADR-028` point 3's own Consequences section notes
`agent_registry.py`'s per-agent `actions` arrays now carry entries whose
real invocation no longer routes through them for the 3 migrated ids —
their continued presence there is deliberately vestigial, serving only
`agent_chat.py`'s unmodified trigger-phrase matching. Do not "clean this
up" by removing them — that is explicitly named as a future story's own
job, not this task's.

---

## Implementation Log

**2026-08-13 — Built and verified live** (same worktree setup as `T01`).

Added `skill_registry`/`skill_tools` imports, the `_invoke_capability`
helper, and the `id in skill_tools.SKILLS` membership-check fork inside
both `trigger_action` and `chat()`. `git diff` confirms `_invoke_action`/
`_execute_action`/`_execute_async_action`/`_action_label` are all
byte-identical to before — only the two call sites gained the fork, plus
`get_agent()`'s unrelated `T08` line change.

**Scope-internal judgement call, flagged for spot-check (not an
escalation):** the task's own illustrative `_invoke_capability` sample
uses `result["status"]` for its first two checks. Reconciled against
`skill_registry.invoke_skill`'s REAL return shapes: a successful or
honest-unavailable dispatch (`T01`'s stub handlers, `web_research`)
returns `{"available": bool, "message": str}` with **no `"status"` key at
all** — `result["status"]` would `KeyError` the instant a capability
actually dispatches successfully (i.e. on every real invocation of a
granted, available-or-not skill). Fixed by using `result.get("status")`
throughout — confirmed live below across all 3 real result shapes
(honest-unavailable, refused, unknown_skill via direct testing).

**AC-03:** `trigger_action("vault-qa", "ask_question")` (post-retrofit
grant) → `{"status": "error", "message": "This skill is not yet available
— no real handler has been built for it."}` — the same honest "not yet
available" class of reply `ask_question` produced before migration (see
the watch-item finding below for the exact wording difference). **PASS.**

**AC-04 (THE OPERATOR'S OWN HIGHEST-RISK WATCH-ITEM — verified live, not
just code review):**
1. Established the TRUE pre-migration reply by calling the completely
   unmodified `_invoke_action("email-capture", "view_last_run",
   trigger="chat")` directly (this function's own body is untouched by
   this task) → `{"status": "error", "message": "This action is not yet
   available."}`.
2. Real HTTP round-trip via FastAPI `TestClient` against the real,
   unmodified app (same technique already used successfully for `T03`,
   this project's own established substitute for a lifespan-triggering
   full server start — see the environment note below) —
   `POST /agents/email-capture/chat` with `{"message": "view last run"}`
   → `200`, `{"reply": "This skill is not yet available — no real handler
   has been built for it.", "action_triggered": "view_last_run"}`.

**Honest finding, not silently smoothed over:** the trigger phrase still
matches the identical capability id (`view_last_run`) and the dispatch
genuinely now routes through `skill_registry.invoke_skill` (confirmed —
`action_triggered` unchanged, and the reply text changed from
`_execute_action`'s generic "This action is not yet available." to
`skill_tools`' Skill-stub convention "This skill is not yet available —
no real handler has been built for it."). **The reply TEXT is NOT
byte-identical to the pre-migration reply.** This is not a build defect —
`ADR-028`'s own "Alternatives Considered" section explicitly considered
and declined preserving the literal Action-era string, reasoning that
Scenario 3/4's own substance is "the capability still honestly refuses,
never fabricates," not "the exact placeholder string is byte-identical,"
and left the exact wording as "decomposer/coder-level copy latitude...
not a functional regression in either reading." Both replies are honest
"not yet available" refusals with identical semantic meaning and identical
routing/matching behavior — only the specific wording changed, by
already-Accepted-ADR design. Flagged here explicitly since the operator's
own watch-item asked for "identical reply," and the honest, disclosed
answer is: mechanism identical, wording intentionally different, per
`ADR-028`.

**AC-05:** granted `view_last_run` to `vault-filing-expert` (real agent,
zero actions/skills today) — `trigger_action("vault-filing-expert",
"view_last_run")` → identical result to `trigger_action("email-capture",
"view_last_run")` (already-shipped agent with the same capability). Both
`{"status": "error", "message": "This skill is not yet available — no
real handler has been built for it."}`. **PASS.** Revoked afterward —
`vault-filing-expert` confirmed back to `[]` real capabilities.

**AC-06:** the task's own named primary agent (`vault-qa`) turned out to
be one of `T05`'s own 4 seeded agents for `ask_question` — revoking it
there is silently re-granted on the very next `_load_state()` call (`T05`'s
own documented "known, accepted consequence," confirmed live: revoke
succeeded, but the immediately-following `trigger_action` call still
returned the honest-unavailable shape, not a refusal, because the seed
re-granted it before the access check ran). Used the task's own named
alternative instead: `vault-filing-expert` (never granted `ask_question`,
not in the seed mapping) — `trigger_action("vault-filing-expert",
"ask_question")` → `{"status": "refused", "message": "Agent does not have
access to this skill."}`; `vault_writer.load_agent_history
("vault-filing-expert")` confirmed identical entry count before/after —
**zero new `run_event` appended.** **PASS.**

Non-AC smoke check: confirmed all 4 still-real Action ids
(`run_capture_now`, `pause_schedule`, `rebuild_person_note`,
`build_knowledge`) are NOT `skill_tools.SKILLS` members (so the fork
correctly excludes them) — did NOT trigger a real `run_capture_now`
invocation to prove this (a real, costly Outlook/Compass capture run with
no bearing on this task's own dispatch-fork logic); the membership-check
result plus the `git diff`-confirmed byte-identical `_invoke_action` body
together are sufficient evidence the fork routes still-real ids unchanged.

**Environment note, resolved with bonus confirmation:** a real, full
`uvicorn` server start (port 8010) was also attempted for an even more
literal "live `curl`" round-trip; `app/main.py`'s own `lifespan` awaits a
real app-start Outlook/Compass capture pass before "Application startup
complete" (confirmed genuinely working throughout, not hung, via growing
real Windows process CPU time and real `Core42`/Compass HTTP calls in the
log — this project's own documented multi-minute app-start-capture-latency
precedent). It finished (~10 minutes) while the rest of this task's
verification proceeded via `TestClient` in parallel. Once it reported
"Application startup complete", ran the genuinely strongest-possible
confirmation — a real `curl` POST against the real listening socket:
`curl -X POST http://127.0.0.1:8010/agents/email-capture/chat -d
'{"message": "view last run"}'` → `{"reply":"This skill is not yet
available — no real handler has been built for it.",
"action_triggered":"view_last_run"}` — byte-identical to the `TestClient`
result above. Server stopped afterward (`Stop-Process`, confirmed gone).

`agent_registry.py` / `agent_chat.py` — confirmed untouched (not in
`git diff`).

gate: flagged 2026-08-13 — two scope-internal items for human spot-check:
(1) the `result.get("status")` fix (a correctness bug in the task's own
sample, same file, no new dependency/interface/ADR); (2) the honest
reply-text-differs-from-pre-migration finding above, which the operator
should see explicitly even though `ADR-028` already sanctions it. Neither
is an `ESCALATIONS.md`-level event.
