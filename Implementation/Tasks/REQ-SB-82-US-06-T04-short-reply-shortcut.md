---
id: REQ-SB-82-US-06-T04
title: chat_turn.py — short-reply shortcut (pre-routing check) + persist last_answering_agent on dispatch
parent_story: REQ-SB-82-US-06
requirement_id: REQ-SB-82
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-82-US-06-T01]
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-82-US-06-T04 — chat_turn.py: short-reply shortcut (pre-routing check) + persist last_answering_agent on dispatch

## Parent Story

- Story: [[REQ-SB-82-US-06]] — `../UserStories/REQ-SB-82-US-06-live-routing-fix-and-reply-to-message.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Add a pre-routing short-reply shortcut to `chat_turn.py::send_user_message`
(checked before any moderator call) that routes a low-signal acknowledgment
straight to whoever answered last, and make `_dispatch_reply` persist that
"last answering agent" on every real dispatch so the shortcut has real data
to read.

---

## Starting State → End State

**Before / Inputs:**
- `send_user_message` appends the user's message, then always runs a
  routing decision (`@mention` → `moderator.route_question` → suggestion/
  fallback chain) with no shortcut for a low-signal reply. `_dispatch_reply`
  appends the agent's reply via `chat_store.append_message` but never
  records who answered. `T01`'s `chat_store.set_last_answering_agent` now
  exists.

**After / Outputs:**
- A new private helper, `_is_short_low_signal_reply(text: str) -> bool`,
  implementing the decomposer-authored detection rule (see the story's own
  "Decomposer-authored scope-internal judgement calls" section): the
  trimmed text does NOT end in `?`, AND EITHER it lowercases/strips
  trailing punctuation to an exact match in a small fixed acknowledgment
  vocabulary, OR its stripped length is `<= 3` characters.
- `send_user_message` checks this helper BEFORE the `@mention`/moderator
  logic: if true AND `chat_store.get_thread(...)`'s
  `last_answering_agent_id` is set, dispatch directly to that agent id
  (same `_dispatch_reply` call shape used everywhere else) — no
  `moderator.route_question`/LLM call made at all for this path. If the
  shortcut condition is false, OR `last_answering_agent_id` is unset,
  execution falls through to the existing routing logic unchanged (this
  task does not touch the LLM-primary wiring itself — that's `T05`; the
  fallthrough still calls today's `moderator.route_question` since `T05`
  hasn't landed yet when this task is built first, and `T05` will compose
  cleanly on top).
- `_dispatch_reply` calls `chat_store.set_last_answering_agent(subject_kind,
  subject_note_stem, agent_id, agent_name)` right after
  `chat_store.append_message(...)` succeeds, for every dispatched reply —
  Expert, Research Agent, or Customer-Section fallback alike (matches
  `ADR-012` point 1: "whoever most recently answered, not just
  permanently-brought-in Experts").

---

## Files to Modify

- `src/backend/app/business/cockpit/chat_turn.py` — add
  `_is_short_low_signal_reply`, the pre-routing shortcut branch in
  `send_user_message`, and the `set_last_answering_agent` call in
  `_dispatch_reply`.

---

## Constraints

- Inherits from parent story.
- **Checked BEFORE any moderator call** (deterministic or LLM) — Scenario
  1's own "no full moderator routing decision... is needed to reach that
  outcome" is enforced structurally, not just by outcome.
- **No prior answering agent → shortcut cannot fire** (Scenario 7) — an
  absence-of-data check (`last_answering_agent_id is None`), never a
  separate flag to keep in sync.
- **Compose around the REAL current `chat_turn.py`** before editing — this
  file was substantially built by `REQ-SB-82-US-04` (now `Done`); read it
  fresh rather than trusting this task's own prose paraphrase of its
  current shape (this project's own established discipline,
  `SPRINT-020`/`027`/`030`).
- Do not alter `@mention` override behavior, the tie-break, the
  suggestion message, or the Customer-Section fallback chain — this task
  only adds a NEW branch checked earlier, leaving everything else byte-
  identical in behavior when the shortcut doesn't fire.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-82-US-06-AC-01]` Seed a subject's thread with
   `chat_store.set_last_answering_agent(subject_kind, stem, "azure-expert",
   "Azure Expert")` (or drive it live: bring in an Expert, send a
   substantive question, let a reply dispatch); then call
   `send_user_message(subject_kind, stem, "Yes")`. Confirm the reply is
   dispatched directly to `azure-expert` (inspect the returned `answering`
   dict / the persisted thread's new message `agent_id`) and — via a
   monkeypatch/spy on `moderator.route_question` (and, once `T05` lands,
   the LLM function too) — confirm neither was called for this message.
2. `[REQ-SB-82-US-06-AC-07]` For a subject with Experts brought in but
   `last_answering_agent_id` still unset (a brand-new thread), call
   `send_user_message(subject_kind, stem, "ok")`. Confirm the shortcut does
   NOT fire (the existing routing path — `moderator.route_question` today,
   pending `T05` — is invoked instead, producing its own normal outcome),
   proving the absence-of-data check works.
3. Send a short-but-substantive message that ends in `?` (e.g. "Cost?") to
   a subject WITH `last_answering_agent_id` set; confirm the shortcut does
   NOT fire (routes normally instead) — no AC tag (supports `AC-01`'s own
   "never for a substantive question that merely happens to be short"
   Constraint, a detection-rule correctness check rather than a separate
   locked scenario).
4. After a real `_dispatch_reply` completes for any agent (Expert, or the
   Research Agent/Customer fallback), confirm
   `chat_store.get_thread(...)['last_answering_agent_id']`/`_name` now
   reflect that agent (no AC tag — supporting groundwork for `AC-01`/
   `AC-07` above, confirms the setter is actually wired at the real call
   site).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] A short, low-signal reply with a prior answering agent routes
      directly to that agent, with no moderator call made
- [x] A short, low-signal reply with NO prior answering agent falls through
      to normal routing
- [x] `last_answering_agent_id`/`_name` are persisted on every real
      dispatched reply, regardless of which fallback path produced it
- [x] Existing `@mention`/tie-break/suggestion/Customer-fallback behavior
      unchanged when the shortcut doesn't fire
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Replacing `moderator.route_question` with the LLM-primary function —
  `T05` (built next, on top of this task's own shortcut branch).
- `reply_to_message_id` resolution — `T05`/`T06`.

---

## Context / Notes

The detection rule is a decomposer-authored, pre-authorized judgement call
— see the parent story's own "Decomposer-authored scope-internal judgement
calls" section for the full rule and rationale; implement it exactly as
written there rather than re-deriving it.

`ADR-012` point 1 (`Implementation/Architecture/ADR.md`) is the
authoritative design for the shortcut's mechanism and its schema
dependency (not the literal detection rule, which this ADR deliberately
leaves open).

---

## Implementation Log

**Changed:** `src/backend/app/business/cockpit/chat_turn.py` only, per
`## Files to Modify`.

- Added `_SHORT_REPLY_ACKNOWLEDGMENTS` (the decomposer-authored fixed
  vocabulary, copied verbatim from the story's own "Decomposer-authored
  scope-internal judgement calls" section) and
  `_is_short_low_signal_reply(text)`, implementing exactly the locked
  rule: trimmed text that does NOT end in `?`, AND EITHER its lowercased/
  trailing-punctuation-stripped form is an exact vocabulary match, OR its
  stripped length is `<= 3`. Not re-derived — implemented as decided.
- `send_user_message` now checks `_is_short_low_signal_reply(text)` AND
  `thread.get("last_answering_agent_id")` immediately after appending the
  user's message, BEFORE the `@mention`-match line — structurally
  guarantees no `moderator.route_question`/LLM call happens on this path.
  When both are true it dispatches directly (same `_dispatch_reply`/
  `asyncio.create_task` call shape as every other path) and returns early;
  otherwise falls straight through into the pre-existing, byte-unchanged
  routing logic (no lines below that point were touched).
- `_dispatch_reply` now calls
  `chat_store.set_last_answering_agent(subject_kind, subject_note_stem,
  agent_id, _agent_name(agent_id))` right after `chat_store.append_message`
  succeeds, for every dispatched reply (Expert, Research Agent, or
  Customer-Section fallback alike — the call site is shared by all three,
  so no branching was needed).

**Scope-internal judgement call (for human spot-check, not a re-decision):**
the story's own decomposer-authored rule left the exact placement of the
shortcut check implicit beyond "before `@mention`/moderator logic" — placed
it as the very first statement after `append_message`, ahead of the
`@mention`-match line itself (not just ahead of the `moderator.route_question`
call), so an `@mention`-prefixed message (which never matches the
low-signal vocabulary or the length floor, since it starts with `@`) still
falls through to the unchanged mention-resolution path naturally, with no
special-casing needed between the two mechanisms.

**MEMORY.md:** not updated — this task is a direct, literal build of a
decision already recorded in the parent story file (the detection rule)
and an already-`Accepted` `ADR-012` mechanism; no new decision, pattern,
or constraint emerged during the build itself.

**CHANGELOG.md:** entry appended, `## [Unreleased]`.

### Verification (manual mode — in-process, scoped, disclosed monkeypatch,
this project's own established technique, `SPRINT-022`/`024`/`050`)

A throwaway script (`verify_t04.py`, not committed) loaded the real,
unmodified `chat_turn`/`chat_store`/`moderator` modules and monkeypatched
only: (a) `chat_store._load_state`/`vault_writer.save_cockpit_chat_state`
to an in-memory dict (no real vault state file touched), (b)
`chat_turn._reply_via_agent` to return instantly (no real Hermes call —
the shortcut/dispatch WIRING is what's under test), (c)
`moderator.route_question` wrapped with a call-counting spy so an actual
zero-vs-one-call assertion could be made. Every assertion below ran
against the real, unmodified `send_user_message`/`_dispatch_reply`
functions.

- `[REQ-SB-82-US-06-AC-01]` **PASS.** Seeded a subject with
  `bring_in_agent("azure-expert")` +
  `set_last_answering_agent(..., "azure-expert", "Azure Expert")`, then
  called `send_user_message(..., "Yes")`. Observed: `answering ==
  {"agent_id": "azure-expert", "agent_name": "Azure Expert"}`,
  `route_question` call count `== 0`, and the persisted thread's last
  message has `agent_id == "azure-expert"` after the background dispatch
  task completed.
- `[REQ-SB-82-US-06-AC-07]` **PASS.** Same roster, `last_answering_agent_id`
  left unset (fresh thread), called `send_user_message(..., "ok")`.
  Observed: `route_question` call count `== 1` (existing routing path
  invoked instead of the shortcut), proving the absence-of-data check
  works.
- Unlabeled (Test 3 — detection-rule correctness, not a separate locked
  scenario): with `last_answering_agent_id` set, sent `"Cost?"`. Observed:
  `route_question` call count `== 1` — the trailing `?` correctly excluded
  it from the shortcut. Also spot-checked `_is_short_low_signal_reply`
  directly for `"Yes"`→True, `"yes!"`→True, `"np"`→True, `"Why?"`→False,
  `"Cost?"`→False, a full substantive sentence→False, `"sounds good"`→True,
  `""`/`"   "`→False, `"yep!!"`→True, `"nope"`→True, `"ok?"`→False — all
  matched the rule's intended shape.
- Unlabeled (Test 4 — setter wiring at the real call site): after a real
  `_dispatch_reply` completed via the shortcut path (above), the thread's
  `last_answering_agent_id`/`_name` reflected `"azure-expert"`/`"Azure
  Expert"`. Additionally verified the SAME setter fires for the Research
  Agent fallback path (forced a genuine tie via a stubbed
  `route_question`, unchanged tie-break logic routed to
  `research-agent`) — thread's `last_answering_agent_id` became
  `"research-agent"` afterward, confirming "regardless of which fallback
  path produced it."
- Existing-behavior-unchanged checklist item: confirmed by construction
  (no line below the new early-return block was edited — diff-reviewed)
  AND live — the tie-break→Research-Agent-fallback check above exercised
  the unchanged tie-break logic end-to-end; a separate live check with a
  substantive `@mention`-prefixed message
  (`"@azure-expert what is the migration timeline for this workload"`,
  stubbed `agents_map_adapter.list_agent_summaries`/`get_agent_detail`)
  confirmed the `@mention` override still resolves and wins with
  `route_question` call count `== 0`, exactly as before this task's edit.

No AC could not be verified; nothing blocked. No new dependency, shared-
interface change, ADR deviation, or unanticipated file — stayed entirely
within `## Files to Modify`.

gate: clear 2026-08-31 — no MUST-FLAG trigger fired (no material
assumption beyond the one pre-authorized detection-rule placement note
above, logged for spot-check, not an escalation; no ADR touched; every
locked AC verified).
