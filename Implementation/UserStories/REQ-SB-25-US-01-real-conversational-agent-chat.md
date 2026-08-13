---
id: REQ-SB-25-US-01
title: Real, Provider-backed conversational replies for embedded agent chat, with the keyword-match action fast-path preserved
requirement_ids: [REQ-SB-25]
requirement_section: "REQ-SB-25: Real Conversational Agent Chat"
phase: P1
status: Done
gate: clear
gate_reason: "Spot-checked and accepted 2026-08-12 — all 5 flagged corrections across T05/T06/T07/T08 reviewed individually and accepted (see each task's own updated gate_reason). All 8 tasks Done, all 5 locked ACs verified live against the real backend/Compass/vault."
sprint: "SPRINT-014"
created: 2026-08-11
updated: 2026-08-12
---

# REQ-SB-25-US-01 — Real, Provider-backed conversational replies for embedded agent chat, with the keyword-match action fast-path preserved

## Story

**As a** Second Brain user
**I want** an agent's embedded chat (REQ-SB-13) to give me a real,
relevant conversational reply — backed by a real LLM call via that
agent's selected Provider — when I send it something other than a known
action-trigger phrase, and to be able to sustain a genuine back-and-forth
with it
**So that** I can actually talk to an agent, not just issue it a small
fixed set of recognized commands

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-25: Real Conversational Agent
  Chat* — "Agent chat (REQ-SB-13) becomes genuinely conversational —
  backed by a real LLM call via the agent's selected Provider (REQ-SB-19),
  not the keyword-substring matching this project built for
  action-triggering. An agent can hold an actual back-and-forth
  conversation, not just recognize a fixed set of trigger phrases."
  Acceptance: "Sending an agent a chat message that isn't a recognized
  trigger phrase still produces a real, relevant conversational reply (via
  the agent's selected Provider), not a generic fallback; an agent can
  sustain a multi-turn exchange, not just one-shot request/reply."
- **PRD breadcrumb (2026-08-11, operator-directed) — read in full before
  scoping this story:** this is an explicit, deliberate reversal of two
  `Accepted` architecture decisions, not a silent extension —
  `ADR-011` (`Implementation/Architecture/ADR.md`) chose keyword-substring
  matching specifically because real NLU was judged disproportionate to a
  one-real-action universe, and `ADR-007` scoped all agent-
  orchestration/NLU capability out of Second Brain's own stack, onto
  Hermes's side of the integration boundary. The breadcrumb is explicit
  that **a superseding ADR is expected at `/plan-tasks`, not avoided** —
  `ADR-007`'s own Consequences section pre-authorized exactly this trigger
  ("If a future requirement genuinely needs Second Brain itself to
  coordinate multi-step... work... that is new scope requiring its own
  requirement and a superseding ADR"). This story does **not** re-litigate
  or flag "should this exist" — the operator already decided that.
- **Fast-path-vs-replace, resolved directly from this requirement's own
  acceptance text, not guessed:** the acceptance text's own phrasing —
  "a chat message **that isn't a recognized trigger phrase**" — presupposes
  trigger-phrase recognition still exists as a live concept. Read literally,
  this resolves the breadcrumb's first open question: `ADR-011`'s
  keyword-match action-triggering is **kept, unchanged, as a fast path**
  for a message matching one of an agent's declared `trigger_phrases`
  (today, only `email-capture`'s `run_capture_now` has a real handler,
  per `ADR-011` point 3 — that does not change here). What changes is only
  the **fallback path**: a message that does *not* match any declared
  trigger phrase, which today produces a static, canned "I didn't
  understand that..." string (`app/business/agent_chat.py::
  handle_chat_message`'s `fallback_reply`), now instead produces a real,
  Provider-backed conversational reply. See Scenario 2 (fast path
  preserved) and Scenario 1 (fallback replaced).
- **Ties to REQ-SB-19 (Per-Agent LLM Provider Selection, `Done`):** the
  acceptance text explicitly requires the real reply come "via the agent's
  selected Provider." `app/business/provider_registry.py` already exists
  (`get_agent_provider`, `has_real_client`) and `app/api/agents_router.py::
  _invoke_action` already establishes the "declared but not yet backed by
  a real handler → honest unavailability, no silent fallback, no
  fabricated response" pattern one layer up, for actions. This story
  reuses that same honesty posture one layer over, for conversational
  replies (Scenario 4). Today only `"compass"` has a real client
  (`provider_registry._REAL_CLIENT_PROVIDER_IDS`); `app/data_access/
  compass_client.py` currently only exposes `classify_email` (a
  fixed-shape, single-purpose prompt/response function) — it has no
  general-purpose "have a conversation" function yet. Adding one (and its
  exact prompt/message shape, whether it's a new function or an extension)
  is an architecture-level decision left to `/plan-tasks`.
- **Multi-turn continuity, resolved within this story's own boundary:**
  "an agent can sustain a multi-turn exchange" is satisfied by the real
  LLM call being aware of the current conversation's own recent turns
  (e.g. replayed from the same `.second-brain/
  agent_communication_history.json` this agent's chat already writes to,
  per `REQ-SB-13-US-01`/`ADR-011`) — it does **not** require the deeper,
  cross-conversation, possibly-summarized "memory" concept `REQ-SB-26`
  names as its own, separate, dependent requirement. See Non-Goals — this
  boundary is deliberate, not an oversight, and keeps the two stories from
  overlapping.
- **No screen change identified.** `html-prototype/agents-map.html`'s
  chat block (`.chat-thread`, `data-role="agent-chat-thread"`, the send
  form) is unchanged in shape by this story — only what populates the
  agent-side reply bubble changes (a real, Provider-backed string instead
  of a keyword-matched confirmation or the canned fallback). Confirmed by
  direct inspection: no new visible region, no new interaction shape.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A chat message that isn't a recognized trigger phrase produces a real, relevant conversational reply

```gherkin
Given the user has an agent's detail panel open, and that agent's selected
    Provider has a real client built for it (e.g. Compass)
When the user sends a chat message that does not match any of the agent's
    declared trigger phrases
Then the reply is a real, relevant conversational response generated via
    a real call to the agent's selected Provider (app/business/
    agent_orchestration.run_agent_conversation)
  And the reply is not the previous static "I didn't understand that..."
    fallback string
```
<!-- AC-ID: REQ-SB-25-US-01-AC-01 -->

### Scenario 2: A message matching a declared trigger phrase still triggers the action directly, unchanged

```gherkin
Given the user has an agent's detail panel open, and that agent has an
    available action whose trigger phrase matches what the user is about
    to send (e.g. "run capture now")
When the user sends a chat message containing that trigger phrase
Then the matching backend action is triggered directly via the existing
    keyword-match fast path (agent_chat.handle_chat_message, ADR-011),
    exactly as before this story
  And the chat reply confirms what was done
  And no real LLM call is made for this message — the trigger-phrase-match
    branch never calls agent_orchestration.run_agent_conversation
```
<!-- AC-ID: REQ-SB-25-US-01-AC-02 -->

### Scenario 3: The agent sustains a multi-turn conversation

```gherkin
Given the user has already exchanged one or more messages with an agent in
    the current conversation
When the user sends a follow-up message whose meaning depends on what was
    said earlier in that same conversation
Then the agent's reply reflects awareness of the earlier turns in that
    conversation (replayed from that agent's existing
    agent_communication_history.json entries), not just the latest message
    in isolation
```
<!-- AC-ID: REQ-SB-25-US-01-AC-03 -->

### Scenario 4: An agent whose selected Provider has no real client honestly reports unavailability instead of a fabricated conversational reply

```gherkin
Given the user has an agent's detail panel open, and that agent's selected
    Provider has no real client built yet
When the user sends a chat message that does not match any declared
    trigger phrase
Then the reply honestly states that the Provider isn't available, the same
    honesty posture already established for actions
    (agents_router.py::_invoke_action's existing funnel-gate)
  And no fabricated or generic conversational-sounding reply is shown
  And no silent fallback to a different Provider (e.g. Compass) occurs
```
<!-- AC-ID: REQ-SB-25-US-01-AC-04 -->

### Scenario 5: A real Provider call that fails is reported honestly, not silently swallowed

```gherkin
Given the user has an agent's detail panel open, and that agent's selected
    Provider has a real client built for it
When the user sends a chat message that does not match any declared
    trigger phrase, and the real Provider call fails (e.g. network error,
    timeout, unparseable response)
Then the reply honestly communicates that the request failed
  And the failure is recorded in the agent's communication history as a
    normal chat_agent entry, the same shape as any other reply
```
<!-- AC-ID: REQ-SB-25-US-01-AC-05 -->

## Affected Screens

- None — backend only. `html-prototype/agents-map.html`'s chat block
  (`#agentPanel`'s `.chat-thread` + send form, built for
  `REQ-SB-13-US-01`) is unchanged in shape; only the source of the agent's
  reply text changes (real Provider-backed conversational text, or an
  honest unavailability/failure message, instead of the keyword-matched
  confirmation or the static canned fallback). No new visible region.

## Dependencies

- **Blocked by:** `REQ-SB-13-US-01` (`Done`) — the embedded chat surface,
  `POST /agents/{id}/chat`, and unified communication history this story
  changes the reply-generation mechanism of.
- **Blocked by:** `REQ-SB-19-US-01` (`Done`) — the Provider concept
  (`provider_registry.get_agent_provider`/`has_real_client`) this story's
  own acceptance text requires the real reply be routed through.
- **Related to:** `REQ-SB-20` (Hub Intelligence & Cross-Section Routing,
  `Draft`, not yet built) — also currently keyword-match-based (per its
  own `ADR-011`-reusing resolution), but a structurally separate mechanism
  (agent-to-Hub-to-Hub routing, not a user-facing chat reply). Not touched
  or blocked by this story; see the open scoping question in Notes.
- **Related to:** `REQ-SB-23` (My Day Intake Agent, `Draft`, needs
  re-spec) — its own PRD breadcrumb states it explicitly **depends on**
  this requirement's conversational mechanism ("this agent needs genuine
  multi-turn understanding, not keyword matching"). This story does not
  build REQ-SB-23's own conversational flow; it only needs to leave the
  new mechanism in a shape REQ-SB-23 can build on without a second
  architecture pass — see the flagged scoping question in Notes.
- **Related to:** `REQ-SB-26` (Agent Memory, `Draft`, this batch) —
  explicitly depends on this story ("memory has no purpose without a real
  conversation to inform"). This story's own multi-turn continuity
  (Scenario 3) is deliberately bounded to the current conversation, not
  REQ-SB-26's deeper cross-conversation memory concept — see Non-Goals.
- **External:** none new — the real Provider call reuses the existing
  Compass credential/endpoint/model configuration REQ-SB-19 already
  established; no new external system.

## Constraints

- **`ADR-011`'s keyword-match action-triggering fast path is kept,
  unchanged**, for a message matching a declared trigger phrase — resolved
  directly from this story's own acceptance text (see Context). This story
  replaces only the previously-canned, non-conversational fallback reply.
- **The real reply must come via the agent's selected Provider**
  (`provider_registry`), reusing the existing "declared but not yet backed
  by a real handler → honest unavailability, no silent fallback, no
  fabricated response" posture `ADR-011` point 3 / `ADR-014` already
  established for actions, applied one layer over for conversational
  replies (Scenario 4).
- **A superseding ADR is expected and required at `/plan-tasks`** — this
  is a deliberate reversal of `ADR-007` and `ADR-011`, not a silent
  extension; the architect must not treat the resulting ADR-creation flag
  as anything other than expected forward work for this specific story.
- The exact mechanism for the real conversational LLM call (a new
  `compass_client.py` function vs. an extension of `classify_email`; the
  exact prompt/message shape; how existing `agent_communication_history.
  json` entries are read back as conversational context) is an
  architecture-level decision left to `/plan-tasks`, not decided here.
- **This story does not build persistent, cross-conversation memory** —
  only continuity within the current, still-open conversation (Scenario
  3). REQ-SB-26 is the separate, dependent requirement for recalling
  information across distinct, separated conversations.
- No new external system dependency — the real call target is whichever
  Provider(s) already have a real client per `REQ-SB-19-US-01`
  (`"compass"` only, today).

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-25-US-01-T01 | backend | `langgraph`/`langchain-openai`/`mcp`/`langchain-mcp-adapters` added to `requirements.txt`; real `pip install` verified | `src/backend/requirements.txt` | `../Tasks/REQ-SB-25-US-01-T01-langgraph-dependency-install.md` |
| REQ-SB-25-US-01-T02 | backend | `agent_orchestration/` package skeleton + `state.py` — graph state schema, history-to-messages mapping | `src/backend/app/business/agent_orchestration/__init__.py`, `state.py` | `../Tasks/REQ-SB-25-US-01-T02-orchestration-state-and-history-mapping.md` |
| REQ-SB-25-US-01-T03 | backend | `model_factory.py` — resolve a per-agent `ChatOpenAI` or an honest unavailable signal | `src/backend/app/business/agent_orchestration/model_factory.py` | `../Tasks/REQ-SB-25-US-01-T03-model-factory.md` |
| REQ-SB-25-US-01-T04 | backend | `vault_query_tools.py` — thin wrappers over existing read-only `vault_writer` primitives | `src/backend/app/business/vault_query_tools.py` | `../Tasks/REQ-SB-25-US-01-T04-vault-query-tools.md` |
| REQ-SB-25-US-01-T05 | backend | `mcp_server.py` — `FastMCP` server registering `vault_query_tools`, mounted at `/mcp` | `src/backend/app/api/mcp_server.py`, `main.py` | `../Tasks/REQ-SB-25-US-01-T05-mcp-server.md` |
| REQ-SB-25-US-01-T06 | backend | `mcp_client.py` — `MultiServerMCPClient` wrapper loading `/mcp`'s registered tools | `src/backend/app/business/agent_orchestration/mcp_client.py` | `../Tasks/REQ-SB-25-US-01-T06-mcp-client.md` |
| REQ-SB-25-US-01-T07 | backend | `graph.py` — compiled `StateGraph` exposing `run_agent_conversation(agent_id, message, history)` | `src/backend/app/business/agent_orchestration/graph.py`, `__init__.py` | `../Tasks/REQ-SB-25-US-01-T07-conversation-graph.md` |
| REQ-SB-25-US-01-T08 | backend | `agents_router.py::chat`'s no-trigger-phrase-match branch calls `run_agent_conversation`; all 5 ACs verified live | `src/backend/app/api/agents_router.py` | `../Tasks/REQ-SB-25-US-01-T08-agents-router-chat-real-reply.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Persistent, cross-conversation agent memory** — recalling information
  from an earlier, separate conversation is `REQ-SB-26`'s own scope, not
  built here; this story's multi-turn continuity is bounded to the current
  conversation only (Scenario 3).
- **`REQ-SB-20`'s Hub-to-Hub routing mechanism** — a structurally separate,
  not-yet-built concern; this story does not modify or depend on it.
- **`REQ-SB-23`'s own conversational intake-agent flow** (follow-up
  questions, note refinement, temporal/organizational hints, filing) — a
  separate, dependent story; not built here.
- **Building real LLM clients for non-Compass Providers** — unchanged from
  `REQ-SB-19-US-01`'s own explicit Non-Goal; a Provider with no real
  client still honestly reports unavailability (Scenario 4).
- **Per-agent token/cost tracking for these new real conversational
  calls** — `REQ-SB-24`'s own separate, not-yet-built scope.
- **Function-calling / the real LLM itself deciding to trigger an action**
  — action-triggering stays exclusively the existing keyword-match fast
  path (Scenario 2); the real conversational reply path never triggers a
  backend action.

## Notes

**Prototype parity (agents-map.html's chat block):** no new region — the
existing `.chat-thread`/send-form interaction shape (built and approved for
`REQ-SB-13-US-01`) is unchanged; only the reply-text source changes. No
`/design` pass needed for this story.

**Genuinely open sub-mechanism questions, resolved directly from this
requirement's own acceptance text (not flagged):**

1. **Replace entirely vs. keep as a fast path?** Kept as a fast path,
   unchanged, for the one already-real action — see Context and
   Constraints. Resolved by literal reading of the acceptance text's own
   "isn't a recognized trigger phrase" phrasing, not guessed.
2. **Multi-turn scope?** Bounded to the current, still-open conversation
   (existing communication-history entries as context) — not REQ-SB-26's
   deeper cross-conversation memory. Resolved by the two requirements'
   own explicit dependency relationship (REQ-SB-26 depends on REQ-SB-25,
   named as a separate concept in the PRD).

**Genuinely open sub-question, flagged (`gate: flagged`, trigger-8 —
multiple equally-valid scoping options):** the breadcrumb separately names
"how this interacts with REQ-SB-20's Hub routing... and REQ-SB-23's
conversational intake agent, which depends on this requirement's
mechanism" as open. Neither REQ-SB-20 nor REQ-SB-23 is built yet, so
nothing here blocks *this* story's own build — but REQ-SB-23's PRD
breadcrumb explicitly names this story's mechanism as its own dependency,
which raises a real, not-yet-decided architecture-scoping question for
the superseding ADR at `/plan-tasks`: should the new "call an agent's
Provider for a real conversational reply" mechanism be built as a
narrow, single-endpoint integration scoped only to this story's own
`POST /agents/{id}/chat` reply path, or as a more general, reusable
primitive designed with REQ-SB-23's near-term reuse in mind (multi-turn,
follow-up-question-capable conversation, which REQ-SB-23 explicitly needs
too)? Building narrow now risks a second architecture pass when REQ-SB-23
is re-specced; building broad now costs more up front for a benefit that
isn't guaranteed to materialize exactly as anticipated. This is a genuine,
not-silently-decidable scoping call, not a guess this story should make on
its own.

**What to do:** at `/plan-tasks`, the architect's superseding ADR should
explicitly state and justify which of the two shapes above it chose,
rather than leaving the reusability question implicit in whatever gets
built. This does not block `/plan-tasks` from proceeding — the ADR
creation itself already triggers a review flag per Pipeline.md's own
architect rules; this note asks that the *specific* reusability question
be addressed within that same ADR, not treated as a separate blocker.

No `ESCALATIONS.md` entry was written — this is an ordinary open scoping
question for the next pipeline stage, not a contradiction, an out-of-scope
event, or a requirement dispute. `REVIEW-QUEUE.md` entry added pointing
here.

**Architect pass (`/plan-tasks` step 1, 2026-08-12):** confirmed
`ADR-015` (`Implementation/Architecture/ADR.md`, `Accepted`,
operator-approved 2026-08-11) already covers this story's full
architectural need end to end — the package set (`langgraph>=1,<2`,
`langchain-openai`, `mcp`, `langchain-mcp-adapters`), the new
`app/business/agent_orchestration/` layering (`state.py`,
`model_factory.py`, `mcp_client.py`, `graph.py`), the
`model_factory.py` unavailability funnel-gate mirroring
`_invoke_action`'s honesty posture (Scenario 4), the exact
`agents_router.py::chat` edit — no-trigger-phrase-match branch calls
`agent_orchestration.run_agent_conversation(agent_id, message, history)`
in place of the old canned fallback, trigger-phrase-match branch
untouched (Scenario 2, `ADR-015` Decision point 5), the
`agent_communication_history.json`-as-conversation-source-of-truth call
with no LangGraph checkpointer (Scenario 3), the honest-failure-recorded-
as-a-normal-`chat_agent`-entry call (Scenario 5), and the reusability
sub-question this story itself flagged (broad/reusable graph chosen over
a narrow single-endpoint integration, `ADR-015` Decision point 1 /
Alternatives). **No new or changed ADR resulted from this pass** —
`ADR-015` was neither rewritten nor superseded.

One genuine, narrower gap remained — the exact shape of turning
`history: list[dict]` into the graph's replayed message list, which
`ADR-015` deliberately left as an implementation-level detail, not an
architectural choice. Resolved as an ordinary architecture-scoping
decision (not an ADR — no tool/framework/structural-boundary choice is
involved): `"chat_user"`/`"chat_agent"` history entries map to
`HumanMessage`/`AIMessage`; `"run_event"` entries are excluded from the
replayed list (audit log, not a conversational turn); one minimal
`SystemMessage` is sourced from `agent_registry.get_agent(agent_id)`'s
`name`/`type`; no history truncation/window this pass (full replay,
matching Scenario 3 literally; a token-budget concern is `REQ-SB-24`'s
own separate scope). Full text recorded in `architecture.md` →
"In-App Agent Orchestration (LangGraph) & Shared MCP Server" → new
"Addendum (REQ-SB-25-US-01 architecture-scoping confirmation,
2026-08-12)" subsection.

**Architecture scope:** §"In-App Agent Orchestration (LangGraph) &
Shared MCP Server" (`REQ-SB-20, REQ-SB-25, REQ-SB-26, REQ-SB-27, see
ADR-015`) — both its "LangGraph — where it lives, what it composes with"
and "Shared MCP server" subsections, plus this pass's own new
"Addendum" subsection — and §"Agent detail panel — settings, actions,
chat, unified history (REQ-SB-13-US-01, see ADR-011)", scoped strictly
to `agents_router.py::chat`'s no-trigger-phrase-match branch (its
trigger-phrase-match branch and every other endpoint in that section are
out of this story's file scope, per `ADR-015` Decision point 5). The
decomposer's tasks and the eventual coder are bounded to these sections
plus `ADR-015`/`ADR-011`'s own Decision text — no file or module outside
what those sections name.

**Gate:** `gate: clear` 2026-08-12 — no ADR created or changed this pass
(`ADR-015` already `Accepted` and already covers this story in full), no
material assumption beyond the ordinary mechanism-filling detail above
(a narrow filling-in of an already-decided interface shape, not a new
architectural choice), no contradiction with any `Accepted` ADR, the
PRD, or a `MEMORY.md` constraint, and no other MUST-FLAG trigger fired.
Proceeding to the decomposer.

**Decomposition pass (2026-08-12, `/plan-tasks` step 2 — decomposer):**
All 5 scenarios locked as `REQ-SB-25-US-01-AC-01`…`AC-05` (sequential,
one per scenario) — wording tightened for buildability (each now names
the concrete module/function it maps to — `agent_orchestration.
run_agent_conversation`, `agent_chat.handle_chat_message`,
`agents_router.py::_invoke_action`'s funnel-gate) without weakening,
omitting, or deleting any locked content from the analyst's original
Gherkin. No AC left non-locked — this story's inputs were unambiguous
enough (`ADR-015` already resolves every open mechanism question; the
architect's own 2026-08-12 addendum resolves the one remaining
history-to-messages mapping detail) that no material assumption was
needed to lock any of them.

8 tasks created (all `backend`, all `phase: P1`), covering exactly the
architecture scope named above: `T01` (dependency install + a **real**
`pip install` verification, per `ADR-015`'s own honestly-flagged
Windows `cp314` wheel-availability risk — not assumed clean), `T02`
(`agent_orchestration/` package skeleton + `state.py`), `T03`
(`model_factory.py`), `T04` (`vault_query_tools.py` — no new-package
dependency, so it can build in parallel with `T02`/`T03`), `T05`
(`mcp_server.py` + `main.py` mount), `T06` (`mcp_client.py`), `T07`
(`graph.py`, the package's one public entry point), `T08`
(`agents_router.py::chat`'s no-trigger-phrase-match branch edit, the
only file-scope touch to the "Agent detail panel" architecture section
this story is bounded to).

`depends_on` is acyclic: `T01 → {T02, T03}`; `T04` has no dependency
(wraps only already-existing `vault_writer` primitives); `T05` depends
on `{T01, T04}`; `T06` depends on `{T01, T05}`; `T07` depends on `{T02,
T03, T06}`; `T08` depends on `{T07}` alone. No cross-story edges needed
— this story does not share a file with any other in-flight story this
pass.

**AC → verification mapping:** every locked AC is genuinely observable
only once a real HTTP request reaches `POST /agents/{id}/chat` — none of
`state.py`/`model_factory.py`/`vault_query_tools.py`/`mcp_server.py`/
`mcp_client.py`/`graph.py` is independently HTTP-reachable, so, per the
same "verify at the level where the outcome first becomes genuinely
observable" placement rule `REQ-SB-19-US-01-T04` already established,
all 5 AC-tagged live-verification steps are placed in `T08` (`AC-01`
real conversational reply, `AC-02` fast-path-unchanged/no-LLM-call,
`AC-03` multi-turn continuity, `AC-04` honest unavailability, `AC-05`
honest real-call-failure reporting) — no locked AC without a tagged
step. `T01`–`T07` each carry their own non-AC smoke check instead,
consistent with the established sibling-task pattern for internal
building blocks with no directly observable HTTP outcome of their own
(`REQ-SB-19-US-01-T01`'s own precedent).

Story advances `Draft → Ready`; all 8 tasks written directly at
`status: Ready` (lockstep, per the decomposer's own mandate). `gate`
stays `clear` — no MUST-FLAG trigger fired at this stage: `ADR-015` was
neither created nor changed by this pass (already `Accepted`,
architect-confirmed sufficient), no material assumption beyond ordinary
mechanism-filling detail already resolved by the architect's own
addendum, no locked AC judged unverifiable, no contradictory input, and
no genuinely unclear/multiple-equally-valid task breakdown — the
architecture scope named above maps onto this task breakdown directly,
with no real alternative decomposition worth flagging. No new
`ESCALATIONS.md` entry. The pre-existing `REVIEW-QUEUE.md` pointer for
this story (the REQ-SB-20/REQ-SB-23 reusability sub-question) was
already resolved by `ADR-015` itself, per the architect's own pass
above — no new review-queue entry needed from the decomposer.
Eligible for `/plan-sprints`.

**Coder pass (`/implement-sprint`, 2026-08-12, `SPRINT-014`):** all 8
tasks built and marked `Done` in dependency order (`T01`→`T02`/`T03`→
`T04`→`T05`→`T06`→`T07`→`T08`). All 5 locked ACs verified live against
the real backend (port 8002, this pass's own established convention —
see `T05`'s Implementation Log), the real Compass Provider, and the real
vault: `AC-01` (real, tool-backed conversational reply), `AC-02`
(trigger-phrase fast path byte-for-byte unchanged, confirmed via direct
diff inspection, no LLM call), `AC-03` (a second turn correctly recalled
the first turn's own content), `AC-04` (honest unavailability, no
fabrication, no silent fallback, confirmed via the agent's own history
audit trail), `AC-05` (a real Provider connection failure honestly
reported and recorded as a normal `chat_agent` entry). Full evidence for
each: `Implementation/Tasks/REQ-SB-25-US-01-T08-agents-router-chat-real-
reply.md`'s own Implementation Log.

Several real, live-discovered technical corrections were needed beyond
individual tasks' own literal code samples/Tests-section instructions —
each is documented in full in its own task's Implementation Log and
summarized in `MEMORY.md`'s Constraints (not repeated here): `T05`'s MCP
mount needed an explicit `streamable_http_path="/"` and a combined
FastAPI `lifespan` composing `mcp_server.session_manager.run()` alongside
the existing `capture_scheduler.lifespan`; `T07`'s `model_factory.py`
needed a `base_url` suffix strip for `ChatOpenAI`/the OpenAI SDK; `T07`'s
`graph.py` needed a minimal tool-execution loop (not literally a single
node) since a real tool-bound model call genuinely triggers real tool
calls; `T08`'s own live verification found and fixed a per-turn
round-count bug in that same loop, and found `AC-05`'s own literal
Provider-creation verification instruction is structurally unreachable
under `provider_registry`'s existing `has_real_client` gate, substituting
a verified-equivalent method (temporarily repointing the real `"compass"`
Provider's own endpoint) instead. None weakened, omitted, or deleted any
locked AC; every correction stayed within the correcting task's own
already-declared files. No `ESCALATIONS.md` entry was needed — none of
these met the out-of-scope/new-dependency/shared-interface-change/ADR-
deviation bar; each is an ordinary implementation-level correction found
via real, live verification, exactly the kind of finding this project's
own manual-verification-mode discipline exists to surface. Story advances
`Ready → Done`. `gate: flagged` (trigger 8) so a human can spot-check the
corrections above; nothing here blocks the sprint from closing.
