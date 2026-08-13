---
id: REQ-SB-13-US-01
title: Embedded agent detail panel — settings, actions, chat, and communication history from the Agents Map
requirement_ids: [REQ-SB-13]
requirement_section: "REQ-SB-13: Embedded Agent Chat & Communication History"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: SPRINT-010
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-13-US-01 — Embedded agent detail panel — settings, actions, chat, and communication history from the Agents Map

## Story

**As a** Second Brain user
**I want** to select an agent on the Agents Map and open a panel showing its
settings, available actions, an embedded chat I can converse with it through
directly inside Second Brain, and a chronological log of its past
communications
**So that** I can understand, configure, and talk to any agent without
leaving Second Brain's own UI or going through an external Hermes channel

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-13: Embedded Agent Chat &
  Communication History* — "From the Agents Map, the user can select an
  agent to open a right-side panel showing that agent's configuration/markup
  settings, available actions, an embedded chat to converse with the agent
  directly inside Second Brain's own UI (not only through an external Hermes
  channel, per REQ-SB-03), and a log of that agent's past communications."
  Acceptance: "Selecting an agent on the Agents Map opens a panel showing
  that agent's settings and available actions, lets the user send it a
  message and receive a reply without leaving Second Brain, and lists that
  agent's past communications in chronological order."
- **This story depends on REQ-SB-12-US-01** — the Agents Map screen and its
  agent nodes must exist for this panel to be opened from. It is its own
  story (not folded into REQ-SB-12-US-01) because it is a distinct PRD
  requirement with its own acceptance text and a materially different kind of
  work (live chat/conversation surface vs. static visualization) — same
  "distinct, independently valuable requirement" reasoning used to keep
  REQ-SB-12 and REQ-SB-13 as separate PRD entries in the first place.
- **Design authority:** `html-prototype/agents-map.html`'s side panel
  (`#agentPanel`, opened by clicking any `.agent-node`), approved 2026-08-11.
  It shows, per agent: a Settings block (`kv-list` of configuration fields),
  an Available Actions block (buttons), a Chat block (`chat-thread` +
  send form), and a Communication History block (chronological `log-list`,
  or an empty state for an agent whose backing pipeline "is not yet built").
  `html-prototype/app.js`'s chat handler is explicitly a **non-functional
  demo**: it appends the user's message, then after a delay appends a
  hardcoded string — "(demo reply — this panel is a design prototype, not a
  live agent)" — "this prototype never calls a backend," per its own
  comment. The prototype settles the panel's **visual surface and
  interaction shape** (open/close, settings/actions/chat/history sections,
  chronological history ordering) — it does not settle, and was never meant
  to settle, what the chat is actually backed by.
- **Resolved 2026-08-11, operator-confirmed.** REQ-SB-13's own PRD
  breadcrumb left this trust surface open for `/spec` time, the same
  category of question REQ-SB-04 already required a human resolution for —
  now resolved directly rather than guessed:
  - **The chat can trigger backend actions via natural language**, not just
    converse — e.g. asking it to "run capture now" can actually trigger that
    capture run, the same permissive resolution style REQ-SB-04 used for
    agent vault-write access. The prototype's separate Available Actions
    buttons remain as an additional direct-trigger surface alongside the
    chat, not a replacement for it — both paths can invoke the same
    underlying actions.
  - **Communication history is one unified, chronological timeline per
    agent** — chat messages *and* the agent's background run events (e.g.
    "Capture run completed — 3 emails filed") are merged into the same log,
    not two separate lists. This resolves the prototype's two-different-
    shapes ambiguity (capture agents showing run logs, Vault Q&A showing
    conversation logs) in favor of one concept covering both.
  - **What the chat can read/see**, exact persistence mechanism, and
    retention duration remain implementation-mechanism deferrals for
    `/plan-tasks` (not trust-surface questions) — see Constraints.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. These scenarios cover what the PRD's own acceptance text commits
to (the panel's surface and interaction shape); they intentionally do not
assert what the chat is backed by or what "communication history" retains
beyond "past communications, chronological" — see the trust-surface flag
above. -->

### Scenario 1: Selecting an agent opens its detail panel showing settings and available actions

```gherkin
Given the user is viewing the Agents Map with one or more configured agents
When the user selects one of the agents
Then a panel opens showing that agent's settings
  And the panel shows that agent's available actions
```
<!-- AC-ID: REQ-SB-13-US-01-AC-01 -->

### Scenario 2: Sending the agent a message and receiving a reply, without leaving Second Brain

```gherkin
Given the user has an agent's detail panel open
When the user types a message into the panel's chat input and sends it
Then the user's message appears in the chat thread
  And the agent's reply appears in the chat thread
  And the user remains inside Second Brain's own UI throughout — no
    navigation to an external Hermes channel occurs
```
<!-- AC-ID: REQ-SB-13-US-01-AC-02 -->

### Scenario 3: Communication history lists past communications in chronological order

```gherkin
Given the selected agent has one or more past communications recorded
When the user views the panel's communication history section
Then the past communications are listed in chronological order
```
<!-- AC-ID: REQ-SB-13-US-01-AC-03 -->

### Scenario 3b: Communication history unifies chat messages and background run events

```gherkin
Given the selected agent has both past chat exchanges and background run
    events (e.g. a completed capture run) recorded
When the user views the panel's communication history section
Then both the chat exchanges and the run events appear together in the same
    chronological list, not as two separate lists
```
<!-- AC-ID: REQ-SB-13-US-01-AC-04 -->

### Scenario 4: An agent with no communication history yet shows an empty state

```gherkin
Given the selected agent has no past communications recorded yet (e.g. its
    backing pipeline has not run, or has never been built)
When the user views the panel's communication history section
Then an empty-state message explains that nothing has been recorded yet
```
<!-- AC-ID: REQ-SB-13-US-01-AC-05 -->

### Scenario 5: Closing the panel returns to the Agents Map

```gherkin
Given an agent's detail panel is open
When the user closes it (via its close control, or by clicking outside the
    panel)
Then the panel closes
  And the Agents Map remains visible and interactive underneath
```
<!-- AC-ID: REQ-SB-13-US-01-AC-06 -->

### Scenario 6: Selecting a different agent while the panel is open updates its content

```gherkin
Given an agent's detail panel is open, showing that agent's settings, actions,
    chat, and history
When the user selects a different agent on the Agents Map
Then the panel updates to show the newly selected agent's own settings,
    actions, chat, and history
  And no content from the previously selected agent remains shown
```
<!-- AC-ID: REQ-SB-13-US-01-AC-07 -->

### Scenario 7: Sending a chat message that requests an action triggers it

```gherkin
Given the user has an agent's detail panel open, and that agent has an
    available action matching what the user is about to ask for (e.g. "run
    capture now")
When the user sends a chat message requesting that action in natural
    language
Then the agent triggers the matching backend action
  And the chat reply confirms what was done
  And the triggered action appears in the communication history alongside
    the chat exchange, per Scenario 3b
```
<!-- AC-ID: REQ-SB-13-US-01-AC-08 -->

## Affected Screens

- `html-prototype/agents-map.html` — the agent detail side panel
  (`#agentPanel`), opened from any `.agent-node`: settings, available
  actions, embedded chat, communication history. No separate page — an
  overlay on the Agents Map built in REQ-SB-12-US-01.

## Dependencies

- **Blocked by:** REQ-SB-12-US-01 — the Agents Map and its agent nodes must
  exist for this panel to be opened from.
- **Related to:** REQ-SB-03 (Conversational Agent Access via Hermes, not yet
  specced) — the external-channel counterpart this requirement's own PRD
  text explicitly contrasts itself against; this story is the in-app surface
  only, not a replacement for or a rebuild of REQ-SB-03.
- **Related to:** REQ-SB-04 (Agent Vault Write Access) — the PRD explicitly
  cross-references this requirement's write-access trust-surface carve-out
  as the precedent for REQ-SB-13's own open trust-surface question (see
  flag reasoning above).
- **Related to:** REQ-SB-11 (Agent Activity & Error Observability, not yet
  specced) — plausibly the eventual source of run-history data that could
  feed this panel's communication history for capture-type agents, but not
  confirmed or built here.
- **External:** none new beyond what REQ-SB-12-US-01 already introduces
  (this story adds no new external system dependency of its own — whatever
  backs the chat reply and history storage is an architecture-level
  decision deferred to `/plan-tasks`, once the trust-surface flag below is
  resolved).

## Constraints

- Reuses the Agents Map built in REQ-SB-12-US-01 — the panel opens from
  agent nodes already rendered there, not a new entry point.
- The chat's reply must come from a real backend response, not the
  prototype's canned demo text.
- **The chat can trigger backend actions via natural language** (operator-
  confirmed 2026-08-11) — the exact mechanism (intent parsing/routing from a
  chat message to a concrete backend action call) is an architecture-level
  decision left to `/plan-tasks`, not decided here; only the *behavior*
  (can trigger, not read-only) is resolved.
- **Communication history is one unified chronological timeline** per agent,
  merging chat messages and background run events (operator-confirmed
  2026-08-11) — the exact persistence mechanism and retention duration are
  left to `/plan-tasks`.
- What the chat may read (vault content scope, an agent's own internal
  state) remains an implementation-mechanism deferral for `/plan-tasks`, not
  decided here.
- No backend endpoint currently returns per-agent settings, actions, chat
  responses, or communication history — a new API surface is required; its
  shape is left to `/plan-tasks`.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-13-US-01-T01 | backend | Agent-history read/write primitives (`append_agent_history_entry`/`load_agent_history`) | `app/data_access/vault_writer.py`, new `.second-brain/agent_communication_history.json` | `../Tasks/REQ-SB-13-US-01-T01-agent-history-vault-writer-primitives.md` |
| REQ-SB-13-US-01-T02 | backend | Static agent/settings/actions/trigger-phrases registry | `app/business/agent_registry.py` (new) | `../Tasks/REQ-SB-13-US-01-T02-agent-registry.md` |
| REQ-SB-13-US-01-T03 | backend | Chat trigger-phrase matching mechanism | `app/business/agent_chat.py` (new) | `../Tasks/REQ-SB-13-US-01-T03-agent-chat-matching.md` |
| REQ-SB-13-US-01-T04 | backend | Capture-completion `run_event` history hook | `app/business/email_classification.py` (1 added call) | `../Tasks/REQ-SB-13-US-01-T04-capture-completion-history-hook.md` |
| REQ-SB-13-US-01-T05 | backend | `GET /agents/{id}`, `POST /agents/{id}/actions/{action_id}`, `POST /agents/{id}/chat`, `GET /agents/{id}/history` | `app/api/agents_router.py` (new), `app/main.py` | `../Tasks/REQ-SB-13-US-01-T05-agents-router.md` |
| REQ-SB-13-US-01-T06 | frontend | Agent detail panel shell — open/close, settings, actions, `AgentNode` click wiring | `features/agents-map/AgentDetailPanel.tsx`, `AgentNode.tsx`, `AgentsMapCanvas.tsx`, `pages/AgentsMapPage.tsx`, `styles/agent-panel.css` | `../Tasks/REQ-SB-13-US-01-T06-agent-detail-panel-shell.md` |
| REQ-SB-13-US-01-T07 | frontend | Embedded chat thread — send/receive, action-triggering via natural language | `features/agents-map/AgentDetailPanel.tsx`, `agentsApiClient.ts` | `../Tasks/REQ-SB-13-US-01-T07-embedded-chat-thread.md` |
| REQ-SB-13-US-01-T08 | frontend | Communication history — unified chronological log, empty state, full agent-switching refresh | `features/agents-map/AgentDetailPanel.tsx`, `agentsApiClient.ts` | `../Tasks/REQ-SB-13-US-01-T08-communication-history-and-agent-switching.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **The Agents Map itself and its shell/navigation** — REQ-SB-12-US-01, a
  dependency, not rebuilt here.
- **Whether the chat can read/write the vault per REQ-SB-04's own carve-out**
  — a separate, not-yet-resolved question from "can the chat trigger
  actions"; not decided here.
- **Persisting real communication history in a backend data store** — the
  storage mechanism and retention policy are left to `/plan-tasks`; only the
  unified chat+run-events *shape* is resolved (see Constraints).
- **The exact set of actions the chat can trigger** — which backend actions
  exist and are exposed to natural-language triggering is left to
  `/plan-tasks`/future stories, not enumerated here.
- **Hermes-channel chat (REQ-SB-03)** — this story is the in-app embedded
  surface only; it does not build or modify the external-channel path.
- **REQ-SB-11's own observability UI** — a separate, not-yet-specced
  requirement; this panel's communication history may eventually relate to
  it, but that integration is not built here.

## Notes

**Prototype parity (agents-map.html's side panel):**

- Panel header + close control — **Specced** (Scenario 1, 5).
- Settings section (`kv-list`) — **Specced** (Scenario 1).
- Available Actions section (buttons) — **Specced** (Scenario 1); the exact
  action set per agent shown in the prototype (e.g. "Run capture now",
  "Pause schedule") is illustrative of the surface, not asserted as a fixed
  final list — which actions exist depends on which agents/pipelines are
  actually configured, per REQ-SB-12-US-01's same reasoning.
- Chat thread + send form — **Specced** (Scenario 2) for the send/receive
  interaction shape, plus (Scenario 7) for action-triggering; the reply's
  actual source is a real backend response — the prototype's canned demo
  reply is explicitly not real and will be replaced.
- Communication history (chronological log / empty state) — **Specced**
  (Scenarios 3, 3b, 4) — unified chat + run-events timeline, chronological
  ordering, empty state.
- Switching agents while the panel is open — **Specced** (Scenario 6),
  inferred directly from the panel's `data-agent-id`/`data-agent-detail`
  wiring (one shared panel, swapped content) rather than one panel instance
  per agent.

**Originally flagged (`gate: flagged`), now resolved (`gate: clear`),
2026-08-11:**

REQ-SB-13's own PRD breadcrumb explicitly deferred "the trust surface (what
the in-app chat can do/see, and what 'communication history' retains)" to
`/spec` time — the same category of question REQ-SB-04 already required a
human resolution for. Now resolved directly by the operator:

1. **Can the chat trigger actions?** Yes — matches REQ-SB-04's permissive
   resolution style. See Scenario 7 and Constraints.
2. **What does communication history retain?** One unified chronological
   timeline per agent, merging chat messages and background run events. See
   Scenario 3b and Constraints.

What the chat may read, the exact action-triggering/intent-routing
mechanism, and history's persistence/retention mechanics remain
implementation-level deferrals for `/plan-tasks` — these were never the
trust-surface question itself, only its downstream mechanics.

No material assumption was made; no `ESCALATIONS.md` entry was needed (no
PRD contradiction, no out-of-scope event — this was an open-product-question
flag, resolved by the operator, not a requirement dispute). The
`REVIEW-QUEUE.md` entry pointing here has been removed now that both open
points are resolved. Ready for `/plan-tasks`.

**Architecture pass (2026-08-11, `/plan-tasks` step 1) — new `ADR-011`,
re-flags this story (trigger 3).** The three implementation-mechanism
deferrals this story's Constraints left open (action-triggering mechanism,
agent/action registry source, history persistence) are now resolved:

1. **New API surface** (Constraints: "no backend endpoint currently
   returns per-agent settings, actions, chat responses, or communication
   history"): new router `app/api/agents_router.py` — `GET
   /agents/{agent_id}` (settings + available actions), `POST
   /agents/{agent_id}/actions/{action_id}` (direct trigger), `POST
   /agents/{agent_id}/chat` (natural-language trigger), `GET
   /agents/{agent_id}/history` (unified chronological log).
2. **Action-triggering mechanism** (Constraints: "the exact mechanism...
   is an architecture-level decision left to `/plan-tasks`"): exact-
   phrase/keyword substring matching against a small, per-agent
   `trigger_phrases` set declared in the new `app/business/
   agent_registry.py` — deliberately **not** an LLM/NLU pipeline (this
   project has none, anywhere; `ADR-007` keeps that class of capability
   out of Second Brain's own stack). Only `email-capture`'s
   `run_capture_now` has a real handler this pass (the only capture
   pipeline that's actually `Done`); every other declared action returns
   an honest "not yet available" response rather than a fabricated
   success.
3. **Communication history persistence** (Constraints: "the exact
   persistence mechanism... are left to `/plan-tasks`"): a new
   `.second-brain/agent_communication_history.json`, extending the
   existing flat-JSON-file state convention
   (`processed_email_ids.json`/`conversation_index.json`/
   `last_capture_run.json`) rather than a new storage mechanism or a
   database — new `vault_writer.append_agent_history_entry` /
   `load_agent_history` primitives.

Full reasoning, including every alternative considered (a real LLM-backed
intent router; vault-deriving the agent registry; a database for history;
per-agent history files): `Implementation/Architecture/ADR.md` →
`ADR-011`. Full API/module shape:
`Implementation/Architecture/architecture.md` → "My Day & Agent Panel
APIs" → "Agent detail panel — settings, actions, chat, unified history
(REQ-SB-13-US-01, see ADR-011)".

**What remains genuinely open, not decided by this ADR** — per this
story's own Non-Goals, not pre-empted here: the exact final set of
actions exposed once REQ-SB-08/09/03 actually ship (ADR-011's
Consequences name this as expected, additive future work); whether the
chat can read/write vault content beyond triggering the declared action
set (REQ-SB-04's own separate carve-out, untouched).

**Architecture scope:** `architecture.md` → "Frontend Application
Architecture" (`ADR-010`'s routing/styling/component conventions, reused
not re-decided) and "My Day & Agent Panel APIs" → "Agent detail panel —
settings, actions, chat, unified history (REQ-SB-13-US-01, see ADR-011)".
Concrete files this bounds the decomposer/coder to:
`src/backend/app/api/agents_router.py` (new),
`src/backend/app/business/agent_registry.py` (new),
`src/backend/app/business/agent_chat.py` (new),
`src/backend/app/data_access/vault_writer.py` (new
`append_agent_history_entry`/`load_agent_history` primitives),
`src/backend/app/business/email_classification.py` (one additional call
in `run_capture_and_record_completion`), `src/backend/app/main.py`
(router registration), and `src/frontend/src/features/agents-map/
AgentNode.tsx` (click handling, extended per `ADR-010`'s own Consequences)
plus a new agent-detail-panel component under `src/frontend/src/features/
agents-map/` for the frontend half.

**Gating:** `gate: flagged`, `gate_reason: trigger-3 (ADR-011 created)` —
per the architect's own MUST-FLAG rule, creating an ADR always flags the
story for human review even though the underlying product question was
already resolved by the operator; the pipeline does **not** halt — the
decomposer still runs so the human reviews `ADR-011` and the resulting
task breakdown together in one pass. `REVIEW-QUEUE.md` entry added
pointing here.

**Decomposer pass (2026-08-11, `/plan-tasks` step 2):** all 8 scenarios
(`Scenario 1`..`7`, including `3b`) locked as
`REQ-SB-13-US-01-AC-01`..`AC-08` (sequential, no non-locked ACs). Eight
tasks created — `T01`-`T05` backend (`data_access → business → api`
layering per `ADR-003`, matching `ADR-011`'s own module boundaries
exactly: `T01` history primitives, `T02` static registry, `T03` chat
matching, `T04` the one hook into already-`Done` `email_classification.py`,
`T05` the router wiring all four together), `T06`-`T08` frontend (`T06`
panel shell/settings/actions/open-close, `T07` chat thread, `T08`
communication history + full agent-switching verification) — flat root at
`Implementation/Tasks/`. `depends_on` is acyclic:
`T01→T03→T05`, `T02→T03`, `T02→T05`, `T04→T05`, `T01→T04`,
`T05→T06→T07→T08`. `T06` additionally `depends_on:
[REQ-SB-12-US-01-T02]` (a task-level edge, not just the story-level
"Blocked by" already recorded above) since it literally edits that task's
`AgentNode.tsx`.

Every locked AC has at least one AC-tagged manual verification step:
`AC-01`/`AC-06` in `T06`, `AC-02`/`AC-08` in `T07`, `AC-03`/`AC-04`/`AC-05`/
`AC-07` in `T08` — per the "user-observable outcome" placement rule (same
as `REQ-SB-12-US-02`'s own split), tagged steps live on the frontend panel
tasks; `T01`-`T05` carry thorough non-AC-tagged live-API-call smoke checks
instead. `T05`'s and `T07`'s Tests explicitly flag that triggering
`email-capture`'s `run_capture_now` (via the direct endpoint or a matching
chat message) fires a **real** Outlook/Compass/vault-write capture run —
verification steps say "exactly once"/"be deliberate," consistent with
`MEMORY.md`'s standing dev-server-restart caution, so this isn't a new,
unflagged live-side-effect risk.

No material assumption was made beyond this run's own low-risk
implementation choices already scoped by `ADR-011` itself (the exact
`AgentDetailPanel`/`agentsApiClient` component/file split, and the
direct-action-button `onClick` wiring left explicitly Out of Scope in `T06`-
`T08` since no locked AC exercises that path — only the chat-trigger path,
Scenario 7, is locked); no `ESCALATIONS.md` entry needed; no contradictory
inputs; no oversized task (each is one cohesive layer/panel-section,
mirroring the prototype's own four `side-panel-section` boundaries:
settings+actions, chat, history). `gate: flagged` **stays flagged**
(`gate_reason: trigger-3, ADR-011 created`) per the architect's own MUST-
FLAG rule — the human still reviews `ADR-011` and this full task breakdown
together, even though **no new decomposer-level trigger fired this pass**.
**Story `status: Draft → Ready`**; every task written at `status: Ready` in
lockstep, `gate: flagged` on each task file mirroring the story's own flag
(so the human's review of `ADR-011` covers the whole story+task set in one
place, not just the story file). Eligible for `/plan-sprints` once the
human clears the flag (or, per `Pipeline.md`'s gating contract, the
product-owner may still batch it — `gate: flagged` parks it in
`REVIEW-QUEUE.md` for review, it does not block `/plan-sprints` from
running against other eligible stories).

**Product-owner pass (2026-08-11, `/plan-sprints`):** the operator
confirmed `ADR-011` was already reviewed and approved this session, so this
story's own `gate: flagged` (trigger-3) did not block grouping — resetting
a story's `gate:` value is not this role's job, per the identical precedent
already established for `REQ-SB-16-US-01`/`SPRINT-007` and
`REQ-SB-12-US-01`/`SPRINT-008`. Grouped into `SPRINT-010` as a
single-story sprint (`depends_on_sprints: [SPRINT-008]`, per `T06`'s
task-level `depends_on: [REQ-SB-12-US-01-T02]`). Considered combining with
`REQ-SB-12-US-02` (also `Ready`, ungrouped, depends only on `SPRINT-008`,
no dependency edge between the two) but split into two sprints on sizing
and risk-isolation grounds — 8 + 7 = 15 tasks would be more than double
this session's established ~4-6 task sprint precedent, and this story's
`ADR-011`-driven novelty (new chat/action-triggering surface) is kept
isolated from the lower-risk `REQ-SB-12-US-02`, the same call
`SPRINT-006` made against `SPRINT-007`. Full rationale:
`Implementation/Sprints/SPRINT-010-embedded-agent-chat-and-communication-history.md`
→ "Grouping Rationale & Sizing". The sprint's own `gate: clear`,
`sprint: SPRINT-010` (the story's own `gate:` field is left as
`flagged`/`trigger-3` — a permanent record of the ADR review, not reset by
this pass). Eligible for `/implement-sprint` once `SPRINT-008` is `Done`.

**Coder pass (2026-08-11, `/implement-sprint`):** all 8 tasks (`T01`-`T08`)
built and `Done`. All 8 locked ACs (`AC-01`-`AC-08`) verified live —
backend via real HTTP calls against a live `uvicorn` server (port 8003,
since 8000/8001/8002 were all already occupied by the known `agentic-map`
process and concurrent Second Brain sessions verifying other in-flight
sprints), frontend via headless-Chrome CDP browser automation against a
real `npm run dev` server, per this session's established zero-dependency
verification pattern. `Scenario 7`/`AC-08` (a chat message triggering a
real backend action) and `Scenario 3b`/`AC-04` (unified chat+run-event
history) — the two ACs this story's trust-surface resolution hinges on —
both confirmed live: sending "please run capture now" via the actual chat
UI triggered one real Outlook/Compass/vault-write capture run, the reply
confirmed completion, and the triggered action's `run_event` entries
appeared in the same chronological `.log-list` as the chat exchange, not a
separate list. `npm run build` (`tsc -b && vite build`) passed clean.
Zero blocked tasks, zero `ESCALATIONS.md` entries — two small
scope-internal judgment calls were made and logged in each task's own
Implementation Log (substituting `todo-capture` for `meeting-capture` in
`T05`'s no-handler smoke check to keep `meeting-capture`'s history
pristine for `T08`'s empty-state AC; consolidating the "exactly once"
real action-trigger check into `T07`'s live UI verification instead of a
separate direct-HTTP call in `T05`, to avoid two real capture runs in
immediate succession) plus one small additive CORS-origin extension in the
shared `app/main.py` (Vite landed on port 5174, not the already-bound
5173) — already flagged by a concurrent session's own `REVIEW-QUEUE.md`
entry (`REQ-SB-12-US-02-T03`), not duplicated here. Story `status: Ready →
Done`; `gate:` reset to `clear` (the ADR-011 review this story's flag
recorded is resolved — operator confirmation already noted above — same
precedent as `REQ-SB-12-US-01`/`SPRINT-008`).
