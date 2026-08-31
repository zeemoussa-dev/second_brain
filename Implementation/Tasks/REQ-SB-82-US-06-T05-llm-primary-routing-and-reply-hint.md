---
id: REQ-SB-82-US-06-T05
title: chat_turn.py — LLM-primary routing with deterministic degrade path + reply-to hint resolution
parent_story: REQ-SB-82-US-06
requirement_id: REQ-SB-82
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-82-US-06-T03, REQ-SB-82-US-06-T04]
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-82-US-06-T05 — chat_turn.py: LLM-primary routing with deterministic degrade path + reply-to hint resolution

## Parent Story

- Story: [[REQ-SB-82-US-06]] — `../UserStories/REQ-SB-82-US-06-live-routing-fix-and-reply-to-message.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Replace `chat_turn.py`'s call to `moderator.route_question` (for the
non-shortcut, brought-in-roster case) with `moderator.route_question_llm`
as the PRIMARY routing decision, with the existing deterministic scorer
retained unmodified as the explicit degrade path on any Compass failure;
also thread an optional `reply_to_message_id` into `send_user_message`,
resolving it to real message text fed into the LLM moderator's prompt as a
hint.

---

## Starting State → End State

**Before / Inputs:**
- `chat_turn.py::send_user_message` (as left by `T04`) calls
  `moderator.route_question(text, brought_in_agent_ids)` directly for the
  non-`@mention`, non-shortcut case. `T03`'s `moderator.route_question_llm`
  now exists.

**After / Outputs:**
- `send_user_message` gains a new optional parameter,
  `reply_to_message_id: str | None = None`. When present, it is resolved
  against the CURRENT thread's own `messages` (before the user's new
  message is appended, or immediately after — either is fine as long as
  the referenced id is looked up against the real, current thread state):
  if a message with that id exists, its `text` becomes `reply_to_text`; if
  it does NOT exist (stale/unresolvable reference — Scenario 8), treat it
  as `None` — no error raised, no special-cased branch, the call proceeds
  exactly as if no `reply_to_message_id` had been given.
- In the non-`@mention`, non-shortcut branch: build `candidates` from
  `agents_map_adapter.list_agent_summaries()` filtered to
  `brought_in_agent_ids`, gather the thread's own recent `messages` (a
  reasonable bounded window, e.g. the last ~10), and call
  `moderator.route_question_llm(text, candidates, recent_messages,
  reply_to_text)` inside a `try/except CompassClientError`:
  - **On success:** if it returns an agent id, that becomes the answering
    agent (same as today's `route["agent_id"]` truthy path). If it returns
    `None` (the LLM decided nobody currently brought-in fits), fall into
    the EXISTING "genuinely nobody matched" branch unchanged
    (`suggest_expert_for_question` → Customer-Section fallback →
    `_RESEARCH_AGENT_ID`) — same shape as today's `route["agent_id"] is
    None and not route["tied"]` path (the LLM has no "tied" concept, so
    this branch is reached directly on `None`).
  - **On `CompassClientError`:** fall back to calling the EXISTING
    `moderator.route_question(text, brought_in_agent_ids)` exactly as it
    ran before this task (including its own `tied` handling and the
    surrounding suggestion/fallback chain) — never re-raise, never leave
    the user without a routing outcome (Scenario 6).
- `reply_to_text` is passed ONLY into `route_question_llm`'s prompt — the
  deterministic degrade path (`moderator.route_question`) has no concept
  of it and is called exactly as before, unchanged.
- The `@mention` override and the short-reply shortcut (`T04`) both
  continue to run BEFORE this new logic, unchanged — this task only
  replaces what happens once execution reaches "no mention, not a
  shortcut, at least one Expert brought in."

---

## Files to Modify

- `src/backend/app/business/cockpit/chat_turn.py` — the routing branch
  described above, plus the new `reply_to_message_id` parameter and its
  resolution.
- `src/backend/app/business/cockpit/moderator.py` — only if
  `route_question_llm`'s own signature (from `T03`) needs a small
  adjustment to cleanly accept the recent-messages/candidates shape this
  task actually has on hand; no new routing logic added here beyond what
  `T03` already built.

---

## Constraints

- Inherits from parent story.
- **`route_question` (the deterministic scorer) is retained completely
  unmodified in its own logic** — only its call site moves from "always"
  to "degrade path only" (`ADR-012` point 3). Do not edit
  `moderator.route_question`'s own body in this task.
- **A reply-to hint never overrides the moderator's own decision**
  (Scenario 5) — it is passed as prompt context only, inside the SAME
  `route_question_llm` call, never a separate branch that could
  short-circuit routing to whoever sent the replied-to message.
- **A stale/unresolvable `reply_to_message_id` never raises or breaks the
  send** (Scenario 8, backend half) — resolved defensively, treated as
  absent.
- **Compose around the REAL current `chat_turn.py`** — read the file fresh
  (as left by `T04`) before editing; do not assume this task's own prose
  above is a literal diff.
- The `@mention` override always still wins regardless of any
  `reply_to_message_id` present — this task does not change override
  precedence.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-82-US-06-AC-02]` With 2+ Experts brought in, monkeypatch
   `compass_client.request_chat_completion` (in-process, before
   `send_user_message` is called) to return an engineered reply naming one
   specific brought-in agent for a clearly-on-topic substantive question;
   call `send_user_message(...)` with no `@mention`; confirm the
   `answering` result names exactly that one agent, and confirm (via a spy
   on `moderator.route_question`) the deterministic scorer was NOT called
   for this message. Disclosed: real Compass credentials are still blank
   placeholders — this is the scoped, disclosed monkeypatch substitute;
   the real live happy-path is blocked-pending-credentials (see `T02`'s
   own Tests block), not silently skipped.
2. `[REQ-SB-82-US-06-AC-06]` Same setup as step 1, but monkeypatch
   `compass_client.request_chat_completion` to raise `CompassClientError`
   (a genuinely induced failure, not just a code read); confirm
   `send_user_message(...)` still returns a valid `answering` outcome
   (produced by the existing deterministic `route_question`/suggestion/
   fallback chain, unchanged in its own behavior) and does NOT raise or
   return a broken/error state to the caller — the user is never shown a
   broken chat.
3. `[REQ-SB-82-US-06-AC-03]` Send a message with a real
   `reply_to_message_id` pointing at an earlier real message in the
   thread; via the same `compass_client` monkeypatch technique as step 1
   (capturing its own call arguments), confirm the replied-to message's
   own text is present in the prompt/messages payload passed to
   `route_question_llm`/`compass_client.request_chat_completion`.
4. `[REQ-SB-82-US-06-AC-05]` Set up a reply-to hint pointing at a message
   from Expert A, but engineer the monkeypatched Compass reply to name
   Expert B (a different brought-in Expert) for a question whose text
   clearly belongs to B's own domain; confirm the routing outcome is
   Expert B, not automatically Expert A — proves the hint doesn't override
   the reasoning pass.
5. `[REQ-SB-82-US-06-AC-08]` Call `send_user_message(...)` with a
   `reply_to_message_id` value that does NOT exist in the current thread
   (e.g. a random uuid); confirm the call still succeeds, a routing
   decision is still produced normally (via whichever path — LLM or
   degrade — is exercised), and no exception/error state is raised or
   returned on account of the unresolved reference.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] The LLM-based moderator is the PRIMARY routing decision for every
      non-shortcut, non-`@mention`, roster-nonempty message
- [x] Any `CompassClientError` degrades to the existing, unmodified
      `route_question` chain with no broken/fabricated outcome
- [x] An optional `reply_to_message_id` resolves to real text fed into the
      LLM prompt when present, and is safely ignored (no crash, no error)
      when unresolvable
- [x] The reply-to hint never forces a specific routing outcome — the LLM's
      own reasoning still decides
- [x] `@mention` override and short-reply shortcut precedence unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Accepting `reply_to_message_id` from the HTTP request body — `T06`
  (this task only adds the parameter to `send_user_message` itself).
- Any frontend UI for picking a reply-to message — `T07`/`T08`.
- The single-agent Chat panel's own reply-to mechanism — architecturally
  separate (`ADR-012` point 5), built in `T08` with zero dependency on this
  task.

---

## Context / Notes

`ADR-012` points 2-4 (`Implementation/Architecture/ADR.md`) are the
authoritative design for this task in full. This is the heaviest task in
the story by orchestration complexity — budget real verification time for
the 5 Tests steps above, each inducing a genuinely different real code
path (LLM success, LLM failure/degrade, hint-present, hint-overridden,
hint-unresolvable).

---

## Implementation Log

**Changed:** `src/backend/app/business/cockpit/chat_turn.py` only, per
`## Files to Modify`. `moderator.py` was NOT touched — `route_question_llm`'s
real signature/candidate shape (`T03`) already matches what this task has on
hand (`agents_map_adapter.list_agent_summaries()` already returns
`{"id", "name", "description", ...}` per entry, filtered to the brought-in
roster), so no adjustment was needed.

- `send_user_message` gained `reply_to_message_id: str | None = None`, plus
  a new `_resolve_reply_to_text(thread, reply_to_message_id)` helper —
  resolved against the thread loaded at the TOP of the function (before the
  user's own new message is appended), returning the matched message's
  `text` or `None` (stale/unresolvable, never an error, never a special
  branch — Scenario 8).
- In the `elif brought_in_agent_ids:` branch: built `candidates` (roster
  summaries filtered to `brought_in_agent_ids`) and `recent_messages`
  (`thread["messages"][-_RECENT_MESSAGES_WINDOW:]`, new `_RECENT_MESSAGES_WINDOW
  = 10` constant), then called `moderator.route_question_llm(text, candidates,
  recent_messages, reply_to_text)` inside `try/except
  compass_client.CompassClientError`:
  - **`try` (success):** an agent id becomes `agent_id` directly; `None`
    falls into the existing "genuinely nobody matched" chain.
  - **`except`:** calls the EXISTING `moderator.route_question(text,
    brought_in_agent_ids)` exactly as it ran before this task, including its
    own `tied` handling and the surrounding suggestion/fallback chain —
    never re-raised.
- Factored the "genuinely nobody matched" chain (suggest → Customer-Section
  fallback → `_RESEARCH_AGENT_ID`, previously inline only in the
  deterministic branch) into a new shared `_resolve_no_match_agent_id`
  helper, called identically from BOTH the LLM-success-`None` case and the
  degrade-path's own `not route["tied"]` case — same real behavior in both,
  zero duplicated logic, byte-identical system-message text to before.
- `@mention` override and the `T04` short-reply shortcut both still run
  BEFORE this branch, completely untouched (no line above the
  `elif brought_in_agent_ids:` block was edited).
- New import: `from app.data_access import compass_client` (already an
  existing, `Done` module — `T02`).

**MEMORY.md:** not updated — the `route_question_llm`/degrade-path split
implemented here is a direct, literal build of the already-recorded
`ADR-012` points 2-3 design and the already-recorded MEMORY.md pattern entry
("LLM-composing routing/decision function shape... deliberately does NOT
catch the client's own dedicated error type — the degrade decision belongs
to the caller", added by `T03`); no new decision, pattern, or constraint
emerged during this task's own build.

**CHANGELOG.md:** entry appended, `## [Unreleased]`.

### Verification (manual mode — live, real `.env`-backed Compass
credentials, `COMPASS_MODEL=gpt-5`; disclosed reuse of `T03`'s own
authorization, `ESC-060` precedent)

A throwaway script (`t05_verify.py`, not committed) imported the real,
unmodified `chat_turn`/`chat_store`/`moderator`/`compass_client` modules and
monkeypatched only: (a) `chat_sessions.send_and_await_reply` to a stub
returning instantly (isolates the ROUTING decision under test from the
already-`Done` real-Hermes-dispatch mechanism — no real background Hermes
call made to a production agent profile), (b)
`compass_client.request_chat_completion`, per-step, per the task's own
mandated technique (each Tests step names this exact monkeypatch). Every run
used a disposable test-subject key (`Thread:__t05-live-verification-test__`)
in the REAL `.second-brain/cockpit_chat.json`, brought in two real
registered agents (`azure-expert`/`banking-expert`, real distinct
name/description) via the real `chat_store.bring_in_agent`, and was cleaned
up (disposable key removed) after every step, confirmed empty afterward
(`0` leftover test keys, `14` real thread keys unchanged).

- `[REQ-SB-82-US-06-AC-02]` **PASS.** Engineered `compass_client
  .request_chat_completion` to reply "I'll route this to azure-expert.";
  spied on `moderator.route_question` (call-counting wrapper); called
  `send_user_message(..., "What is Microsoft Azure and what services does
  it offer for our cloud migration?")` with no `@mention`. Observed:
  `answering == {"agent_id": "azure-expert", "agent_name":
  "azure-expert"}`, `route_question` call count `== 0` (never invoked for
  this message).
- `[REQ-SB-82-US-06-AC-06]` **PASS.** Same 2-Expert setup; monkeypatched
  `compass_client.request_chat_completion` to `raise CompassClientError(
  "induced failure for AC-06 verification")` (a genuinely induced failure).
  Called `send_user_message` with the same substantive Azure question.
  Observed: no exception propagated to the caller; `answering ==
  {"agent_id": "azure-expert", "agent_name": "azure-expert"}` — produced by
  the real, unmodified deterministic `route_question` (matched "Azure"
  overlap against `azure-expert`'s own real name/description) — a valid,
  non-broken routing outcome from the degrade chain.
- `[REQ-SB-82-US-06-AC-03]` **PASS.** Appended a real earlier agent message
  ("Azure Landing Zones use a hub-and-spoke network topology.", from
  `azure-expert`) to the thread. Engineered the Compass reply; captured the
  real `messages` payload passed into `request_chat_completion`. Called
  `send_user_message(..., "Can you go deeper on that topology point?",
  reply_to_message_id=<that earlier message's real id>)`. Observed: the
  replied-to message's own exact text ("hub-and-spoke network topology")
  is present in the captured prompt payload (confirmed via substring
  match against the joined `content` fields).
- `[REQ-SB-82-US-06-AC-05]` **PASS.** Same reply-to hint (pointing at the
  `azure-expert` message above), but engineered the Compass reply to name
  `banking-expert` instead, for a question whose text ("what UAE banks
  offer corporate digital banking") clearly belongs to Banking's own
  domain. Observed: `answering == {"agent_id": "banking-expert",
  "agent_name": "banking-expert"}` — NOT automatically `azure-expert` —
  proving the hint doesn't override the reasoning pass.
- `[REQ-SB-82-US-06-AC-08]` **PASS.** Called `send_user_message(...,
  reply_to_message_id=<a freshly-generated random uuid never present in
  the thread>)`. Observed: no exception raised, `answering ==
  {"agent_id": "azure-expert", "agent_name": "azure-expert"}` (a normal
  routing decision was still produced via the LLM path exercised in this
  run) — the unresolved reference was silently ignored, exactly as
  `_resolve_reply_to_text` is built to do.

**Bonus, non-AC-required live confirmation:** called
`moderator.route_question_llm` directly (unpatched, real Compass HTTP round
trip, no chat_store touched) with the same 2-candidate roster and the Azure
question — the real Compass endpoint (`COMPASS_MODEL=gpt-5`) returned
`"azure-expert"`, confirming the whole real wiring genuinely works
end-to-end, not just via the monkeypatched substitute the task's own Tests
block specifies as its required technique.

No AC could not be verified; nothing blocked. No new dependency, shared-
interface change, ADR deviation, or unanticipated file — stayed entirely
within `## Files to Modify`. `moderator.py` needed zero changes (confirmed
directly, not assumed) — logged as a scope-internal judgement call, not an
escalation.

gate: clear 2026-08-31 — no MUST-FLAG trigger fired (no material assumption,
no ADR touched, every locked AC verified live, real `.env`-backed Compass
credentials used and disclosed).
