---
id: REQ-SB-26-US-01
title: Persistent, per-agent memory an agent's real conversational replies can draw on across separate conversations
requirement_ids: [REQ-SB-26]
requirement_section: "REQ-SB-26: Agent Memory"
phase: P1
status: Done
gate: clear
gate_reason: "Spot-checked and accepted 2026-08-12 — T03's correction reviewed and accepted (see its own updated gate_reason). All 4 locked ACs verified live and passing."
sprint: "SPRINT-015"
created: 2026-08-11
updated: 2026-08-12
---

# REQ-SB-26-US-01 — Persistent, per-agent memory an agent's real conversational replies can draw on across separate conversations

## Story

**As a** Second Brain user
**I want** an agent to remember, in a later conversation, information I
gave it in an earlier one — without me having to repeat myself
**So that** talking to an agent feels like talking to something that
actually knows me and my context, not a stateless request/reply box

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-26: Agent Memory* — "Agents retain
  memory across interactions — not just the flat chronological
  communication-history log already built (REQ-SB-13), but working context
  an agent can actually draw on in a later conversation (e.g. recalling
  something the user told it earlier)." Acceptance: "An agent's reply in a
  later conversation can correctly reference or use information the user
  provided in an earlier conversation with that same agent, without the
  user having to repeat it."
- **PRD breadcrumb (2026-08-11, operator-directed):** names four open
  questions — "memory scope (per-conversation/session vs. persistent
  across all time), what gets remembered (raw message history fed back as
  context, vs. a summarized/extracted memory store), storage mechanism
  (extends the existing `.second-brain/
  agent_communication_history.json` convention, or a new mechanism), and
  whether memory is shared across an agent's Section... or strictly
  per-agent." Two of the four are resolved directly below, from the
  acceptance text's own wording; two remain genuine architecture/
  implementation-mechanism deferrals for `/plan-tasks`, per this project's
  own established convention (mechanism questions are deferred as
  Constraints, not gated — see e.g. `REQ-SB-13-US-01`'s identical
  treatment of its own action-triggering/persistence mechanism questions).
- **Memory scope, resolved from the acceptance text's own wording:** "An
  agent's reply in **a later conversation**" — distinct from "an earlier
  conversation" — describes two separate conversations, not two turns
  within one still-open session. This resolves the scope question:
  memory is **persistent across separate conversations**, not merely
  held within one conversation/session's own runtime state (that
  narrower, single-conversation continuity is `REQ-SB-25`'s own already-
  built Scenario 3, not this requirement's point — REQ-SB-26 exists
  precisely because REQ-SB-25's own multi-turn continuity does not survive
  the conversation ending).
- **Section-sharing, resolved from the acceptance text's own wording:**
  "information the user provided in an earlier conversation **with that
  same agent**" — explicit, not "with any agent in the same Section."
  This resolves the scope question: memory is **strictly per-agent**, not
  shared across a Section's other agents (Scenario 2 makes this an
  explicit, tested boundary, not just an absence of a cross-agent
  scenario).
- **What gets remembered (raw history vs. summarized/extracted) and the
  storage mechanism** remain genuine architecture/implementation-mechanism
  decisions, left to `/plan-tasks` — see Constraints. This story's
  Acceptance Criteria are written at the level of observable agent
  behaviour (what the user experiences), not the internal representation,
  matching this project's own established Gherkin-authoring discipline.
- **Update (`ADR-015` approved by the operator 2026-08-11; reconciled into
  this story 2026-08-12) — the *storage location* and *architectural home*
  half of the mechanism question above is now settled, the *extraction
  mechanism* half is not.**
  `Implementation/Architecture/ADR.md` → `ADR-015` Decision point 13
  ("`REQ-SB-26` inherits a settled *storage-location* pattern, not a
  settled *mechanism*") resolves: (a) storage lives in a new sibling
  `.second-brain/agent_memory.json`, extending the project's established
  flat-JSON-file convention (mirroring `agent_sections.json`/
  `agent_providers.json`) — explicitly **not** LangGraph's own built-in
  checkpointer/store, and **not** a database, for the same reasoning
  `ADR-015` point 6 already applied to conversation state; (b)
  architecturally, this story's own capability plugs in as a new
  memory-retrieval node on the **same** compiled `langgraph.graph.
  StateGraph` `app/business/agent_orchestration/graph.py` builds for
  `REQ-SB-25` (`ADR-015` points 3/9's "grow by adding nodes to one shared
  graph, not a new graph per requirement" extensibility pattern). What
  `ADR-015` deliberately does **not** settle — and this story's own
  Acceptance Criteria still leave open, per this project's own established
  "mechanism questions are deferred as Constraints, not gated" convention
  — is *what* the memory-retrieval node actually stores/reads: raw
  message-history replay vs. a summarized/extracted representation. See
  the updated Constraints below.
- **Depends on `REQ-SB-25`** (this same batch) — the PRD's own stated
  dependency ("memory has no purpose without a real conversation to
  inform"). This story assumes `REQ-SB-25`'s real, Provider-backed
  conversational reply mechanism already exists to extend; it does not
  rebuild it. `REQ-SB-25-US-01`'s own `gate:` has since been reset to
  `clear` (operator approved `ADR-015` as written, `REVIEW-QUEUE.md`) and
  it is proceeding to `/plan-tasks` — this story remains sequenced behind
  it (see Dependencies) but is no longer blocked on an open architecture
  question at the batch level; `ADR-015` is now the settled architectural
  home for both stories' in-app orchestration surface.
- **No screen change identified.** Memory is invisible infrastructure,
  observable only through what an agent's replies contain — the existing
  `html-prototype/agents-map.html` chat block (unchanged by `REQ-SB-25`
  too) needs no new visible region for this story. Confirmed by direct
  inspection.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: An agent recalls information from an earlier, separate conversation

```gherkin
Given the user told an agent something in an earlier conversation, and
    that conversation has since ended (the panel was closed, or a
    materially later chat exchange with that same agent has since begun)
When the user starts or continues a later, separate conversation with that
    same agent and sends a message that depends on the earlier information
Then the agent's reply correctly references or uses that earlier
    information
  And the user does not have to repeat it
```
<!-- AC-ID: REQ-SB-26-US-01-AC-01 -->

### Scenario 2: Memory is strictly per-agent, not shared with other agents

```gherkin
Given the user told one agent something in an earlier conversation
When the user starts a conversation with a different agent (including one
    in the same Section) and sends a message that would depend on that
    earlier information if it were shared
Then the second agent's reply shows no awareness of what was told to the
    first agent
```
<!-- AC-ID: REQ-SB-26-US-01-AC-02 -->

### Scenario 3: An agent with no relevant earlier information honestly says so, rather than fabricating a memory

```gherkin
Given the user asks an agent to recall something the user never actually
    told it in any earlier conversation
When the agent replies
Then the reply honestly indicates it doesn't have that information, rather
    than fabricating a plausible-sounding answer
```
<!-- AC-ID: REQ-SB-26-US-01-AC-03 -->

### Scenario 4: Memory survives beyond the runtime that recorded it

```gherkin
Given the user told an agent something in an earlier conversation, and the
    backend has since been restarted (or otherwise recycled) between that
    conversation and the next one
When the user starts a later conversation with that same agent and sends a
    message that depends on the earlier information
Then the agent's reply still correctly references or uses that earlier
    information
```
<!-- AC-ID: REQ-SB-26-US-01-AC-04 -->

## Affected Screens

- None — backend only. Memory is invisible infrastructure, observable only
  through the content of an agent's replies in the existing, unchanged
  chat UI (`html-prototype/agents-map.html`'s `.chat-thread`). No new
  visible region identified.

## Dependencies

- **Blocked by:** `REQ-SB-25-US-01` (this batch, `Draft`, `gate: clear`,
  proceeding to `/plan-tasks`) — the real, Provider-backed conversational
  reply mechanism this story's memory extends. The PRD's own explicit
  statement: "memory has no purpose without a real conversation to
  inform."
- **Related to:** `ADR-015` (`Accepted`, operator-approved 2026-08-11) —
  the architecture decision that adopts LangGraph for Second Brain's own
  in-app agent orchestration and settles this story's storage location
  (`.second-brain/agent_memory.json`) and architectural home (a new
  memory-retrieval node on `app/business/agent_orchestration/graph.py`,
  Decision point 13) ahead of this story's own `/plan-tasks` pass. Does
  **not** settle what the node extracts/stores — see Constraints.
- **Related to:** `REQ-SB-13-US-01` (`Done`) — the existing
  `.second-brain/agent_communication_history.json` flat chronological log
  this requirement's own PRD text explicitly distinguishes itself from
  ("not just the flat chronological communication-history log already
  built"); `ADR-015` confirms this story's memory store is a **separate**
  new file (`agent_memory.json`), not an extension of
  `agent_communication_history.json` — that sub-question from the
  Constraints below is now resolved; what the new file's entries actually
  contain (raw replay vs. summarized/extracted) is not.
- **Related to:** `REQ-SB-20` (Hub Intelligence & Cross-Section Routing,
  `Draft`) — the PRD breadcrumb names Section-sharing as a question partly
  "tied to REQ-SB-20"; resolved here as strictly per-agent regardless
  (Scenario 2), so this story does not need REQ-SB-20 to exist first.
- **External:** none new.

## Constraints

- **Memory is persistent across separate conversations**, not scoped to a
  single still-open session — resolved directly from the acceptance
  text's own wording (see Context).
- **Memory is strictly per-agent**, never shared across a Section's other
  agents — resolved directly from the acceptance text's own wording (see
  Context); Scenario 2 is a locked, tested boundary, not an assumption.
- **What gets remembered (raw message history replayed as context, vs. a
  summarized/extracted memory store) is an architecture-level decision
  still left to `/plan-tasks`**, not decided here — the Acceptance Criteria
  are written at the level of observable behaviour and do not depend on
  which mechanism is chosen. Unaffected by `ADR-015` (see below), which
  deliberately settles *where* this plugs in, not *what* it extracts.
- **The storage location and architectural home are now settled by
  `ADR-015` (Decision point 13), not left open:** a new sibling
  `.second-brain/agent_memory.json` (extending the established flat-JSON
  convention, a **new** file — not an extension of the existing
  `agent_communication_history.json`, and not LangGraph's own built-in
  checkpointer/store, and not a database), consumed by a new
  memory-retrieval node on the same compiled `langgraph.graph.StateGraph`
  `app/business/agent_orchestration/graph.py` builds for `REQ-SB-25`. This
  narrows, but does not remove, the "what gets remembered" deferral above
  — `/plan-tasks` still designs the node's own extraction/summarization
  logic and the exact shape of what it writes into that file.
- **Memory must never be fabricated** when no relevant earlier information
  exists (Scenario 3) — mirrors this project's standing "honest, not
  fabricated" posture already established by `ADR-011`/`REQ-SB-19-US-01`/
  `REQ-SB-25-US-01`.
- Builds on `REQ-SB-25-US-01`'s real conversational reply mechanism —
  does not duplicate or rebuild the Provider-call path itself.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-26-US-01-T01 | backend | `vault_writer.py` — `load_agent_memory`/`append_agent_memory_entries` primitives + `agent_memory.json` state file | `src/backend/app/data_access/vault_writer.py` | `../Tasks/REQ-SB-26-US-01-T01-vault-writer-agent-memory-primitives.md` |
| REQ-SB-26-US-01-T02 | backend | `state.py` — `AgentConversationState` gains `memory`/`extracted_facts` fields (additive only) | `src/backend/app/business/agent_orchestration/state.py` | `../Tasks/REQ-SB-26-US-01-T02-orchestration-state-memory-fields.md` |
| REQ-SB-26-US-01-T03 | backend | `graph.py` — `retrieve_memory`/`extract_memory` nodes added to the existing compiled graph; `run_agent_conversation` gains `memory` param / `extracted_facts` return | `src/backend/app/business/agent_orchestration/graph.py` | `../Tasks/REQ-SB-26-US-01-T03-graph-memory-nodes.md` |
| REQ-SB-26-US-01-T04 | backend | `agents_router.py::chat` — loads memory, passes it into `run_agent_conversation`, persists any `extracted_facts`; all 4 ACs verified live | `src/backend/app/api/agents_router.py` | `../Tasks/REQ-SB-26-US-01-T04-agents-router-chat-memory-wiring.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — N/A, manual verification mode still in effect
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Cross-agent or Section-wide shared memory** — explicitly resolved as
  per-agent only (Scenario 2); a possible future extension, not built or
  implied here.
- **A user-facing surface to view, edit, or clear an agent's memory** —
  not requested by the acceptance text; memory is observed only through
  reply content, not managed directly, this pass.
- **Rebuilding or replacing `REQ-SB-13-US-01`'s existing unified
  communication-history log** — that log remains the chronological
  chat+run-event record; this story's memory mechanism is additional,
  not a replacement.
- **`REQ-SB-25`'s own real-conversational-reply mechanism** — a
  dependency, not rebuilt here.

## Notes

**Prototype parity:** N/A — no screen affected (see Affected Screens).

**Resolved directly from this requirement's own acceptance text, not
guessed (no MUST-FLAG trigger fired):**

1. **Memory scope** — persistent across separate conversations, not
   session-bound. See Context.
2. **Section-sharing** — strictly per-agent, never shared. See Context;
   locked as Scenario 2, not left as an unstated assumption.

**Left as ordinary implementation-mechanism deferrals, per this project's
own established convention (mechanism questions do not require a
`gate: flagged`, only genuine product-scope ambiguity does — see
`REQ-SB-13-US-01`'s identical treatment of its own action-triggering/
history-persistence mechanism questions):**

3. **What gets remembered** — raw history replay vs. summarized/extracted
   store. **Still** left to `/plan-tasks` — `ADR-015` deliberately does not
   settle this (see update below).
4. ~~**Storage mechanism** — extend `agent_communication_history.json` vs.
   a new file.~~ **Resolved 2026-08-12 by `ADR-015` Decision point 13** —
   a new sibling `.second-brain/agent_memory.json`, not an extension of
   `agent_communication_history.json`. See the update below.

`gate: clear` 2026-08-11 — no MUST-FLAG trigger fired: no material
assumption was needed (both scope questions this story's own Acceptance
Criteria depend on are resolved by literal reading of the PRD's own
acceptance text, not filled in); the requirement is finalized, not
`Draft`/unfinalised; no ADR was created or edited (analyst does not
touch architecture); no `ESCALATIONS.md` entry was needed; the story is
not oversized (one cohesive extension of REQ-SB-25's mechanism, four
scenarios); no contradictory PRD inputs were found; and the two questions
that remain open are architecture-mechanism deferrals (the same category
this project's own precedent — `REQ-SB-13-US-01` — already established
does not require gating), not genuinely-unclear product scope. Ready for
`/plan-tasks` once `REQ-SB-25-US-01` is `Ready`/`Done`.

**Update, 2026-08-12 (`/spec` re-pass, operator-supplied context) —
`gate: clear` reaffirmed, not reopened.** The operator's newly-approved
`ADR-015` (`Implementation/Architecture/ADR.md`, `Accepted` 2026-08-11)
settles item 4 above directly (storage location `.second-brain/
agent_memory.json`; architectural home a new memory-retrieval node on
`app/business/agent_orchestration/graph.py`, the same compiled graph
`REQ-SB-25` builds) — see Context and Constraints for the full detail.
Item 3 (what the node actually extracts/stores — raw replay vs.
summarized) is explicitly **not** settled by `ADR-015` and remains this
story's own open `/plan-tasks`-level mechanism deferral, per the same
non-gating convention already established above; this update narrows an
existing deferral, it does not introduce a new one. No MUST-FLAG trigger
fired by this update: no material assumption was made (the settled facts
are read directly from `ADR-015`'s own text, not inferred); no ADR was
created or edited by this pass (the analyst only reads and reconciles
against it, per role boundary); no contradiction exists between this
story's prior text and `ADR-015` (the prior text explicitly deferred both
questions to `/plan-tasks` — `ADR-015` resolving one of them at
`/plan-tasks`-adjacent architecture time is exactly what that deferral
anticipated, not a reversal of anything this story previously asserted).
`REQ-SB-26-US-01` remains sequenced behind `REQ-SB-25-US-01` (Dependencies)
and is ready for `/plan-tasks` once that story reaches `Ready`/`Done`.

---

**Update, 2026-08-12 (`/plan-tasks` step 1 — architect).**
`REQ-SB-25-US-01` has since reached `status: Ready`/`gate: clear` (8 tasks,
`T01`–`T08`), clearing this story's own sequencing dependency. This pass
resolves item 3 above — the extraction mechanism `ADR-015` point 13
deliberately left open — via a new ADR.

**Decision (new `ADR-016`):** memory is an **LLM-based extracted/
summarized fact store**, not raw cross-conversation replay. Raw replay
was rejected outright: `REQ-SB-25-US-01-T02`'s own
`history_entries_to_messages` already replays a *single, still-open*
conversation's full history with no truncation this pass (its own
docstring punts token-budget to `REQ-SB-24`); replaying every *past,
separate* conversation's raw transcript, unbounded, into every future
call would compound that already-deferred concern across an agent's
entire lifetime history with the user, and would risk Scenario 3's
"honest, not fabricated" bar by burying whatever fact is actually
relevant in a large volume of unrelated past chat noise. A small,
purpose-extracted fact store avoids both problems. Two new nodes are
added to `ADR-015`'s single existing compiled graph
(`app/business/agent_orchestration/graph.py`) — not a second graph:
`retrieve_memory` (read path, before `call_model`; the router loads
`agent_memory.json` via a new `vault_writer.load_agent_memory(agent_id)`
primitive and passes it in as a new `memory` parameter, mirroring how
`history` is already passed in fresh from outside) and `extract_memory`
(write path, after `call_model`, same graph, same `.invoke()` call, no
second Provider resolution — reuses the already-resolved model for one
additional, narrowly-scoped completion, honestly returning no facts
rather than inventing one). Storage: a new sibling
`.second-brain/agent_memory.json`, `{agent_id: [{"fact": str,
"recorded_at": iso8601}, ...]}` — confirms and narrows `ADR-015` point
13's already-settled file. Full reasoning, every alternative considered
(raw cross-conversation replay; a hand-rolled heuristic extractor; a
second LLM call made outside the graph; folding retrieval/extraction into
one combined structured-output call; embedding-similarity retrieval; no
extraction at all), and every consequence (including the real cost/
latency consequence of a second LLM completion per reply):
`Implementation/Architecture/ADR.md` → `ADR-016`. `architecture.md`
gained a new "Agent Memory — extraction mechanism" subsection under
"In-App Agent Orchestration (LangGraph) & Shared MCP Server," and its
`Last reviewed` footer was updated.

**`ADR-016` extends `ADR-015` point 13 — it does not reopen or rewrite
`ADR-015` itself** (which stays `Accepted`, unedited); it is a new,
additional ADR, linked from `ADR-015`'s own text.

**Architecture scope:** the coder is bounded to:
- `src/backend/app/business/agent_orchestration/graph.py` (two new
  nodes, `retrieve_memory`/`extract_memory`, added to the existing
  compiled graph — no second graph) and `state.py` (`AgentConversationState`
  gains `memory: list[dict]`/`extracted_facts: list[str]`, additive
  only — no existing field removed/renamed).
- `src/backend/app/business/agent_orchestration/__init__.py` /
  `run_agent_conversation`'s public signature (gains `memory` parameter;
  return shape gains `extracted_facts` key — both additive).
- `src/backend/app/data_access/vault_writer.py` (two new primitives,
  `load_agent_memory(agent_id)` / `append_agent_memory_entries(agent_id,
  facts)`, mirroring `load_agent_history`/`append_agent_history_entry`'s
  exact shape) and the new `.second-brain/agent_memory.json` state file
  it owns.
- `src/backend/app/api/agents_router.py::chat` (loads memory via
  `vault_writer.load_agent_memory`, passes it into
  `run_agent_conversation`, persists any `extracted_facts` via
  `vault_writer.append_agent_memory_entries` — mirroring its existing
  `append_agent_history_entry` calls; no other endpoint on this router
  changes).
- **Out of scope for this story's tasks:** `app/business/agent_chat.py`,
  `app/business/agent_registry.py`, `app/data_access/compass_client.py`,
  `app/api/mcp_server.py`, `app/business/vault_query_tools.py`,
  `app/business/skill_registry.py`/`skill_tools.py` — none of these are
  touched by this story.

**Architecture scope: §"In-App Agent Orchestration (LangGraph) & Shared
MCP Server" → "Agent Memory — extraction mechanism (`REQ-SB-26`, see
ADR-016)"** (`Implementation/Architecture/architecture.md`) — the
decomposer/coder are bounded by this section plus the two file lists
immediately above.

`gate: flagged`, `gate_reason: "trigger-3 (ADR-016 created)"` — a new ADR
was created (`ADR-016`), per Pipeline.md's MUST-FLAG trigger 3. Per
Pipeline.md, this does **not** halt `/plan-tasks` — the decomposer
proceeds so the human can review the ADR and the resulting locked ACs/
tasks together in one pass. `REVIEW-QUEUE.md` entry added. No
`ESCALATIONS.md` entry — `ADR-016` extends `ADR-015` point 13's already-
anticipated deferral; it does not contradict any `Accepted` ADR, the PRD,
or a `MEMORY.md` constraint.

---

**Update, 2026-08-12 (`/plan-tasks` step 2 — decomposer).**
`status: Draft → Ready`. All 4 scenarios locked as
`REQ-SB-26-US-01-AC-01`..`AC-04`, wording tightened only for tense
consistency (Scenario 1's "the user does not have to repeat it" — no
scenario weakened, omitted, or deleted). 4 tasks created, all at the flat
root:

- `REQ-SB-26-US-01-T01` — `vault_writer.py` primitives + `agent_memory.json`
  (`depends_on: []`).
- `REQ-SB-26-US-01-T02` — `state.py` additive `memory`/`extracted_facts`
  fields (`depends_on: [REQ-SB-25-US-01-T02]`).
- `REQ-SB-26-US-01-T03` — `graph.py`'s `retrieve_memory`/`extract_memory`
  nodes, `run_agent_conversation`'s additive signature/return-shape
  extension (`depends_on: [REQ-SB-26-US-01-T02, REQ-SB-25-US-01-T07]`).
- `REQ-SB-26-US-01-T04` — `agents_router.py::chat` memory wiring; carries
  all 4 locked ACs' own verification steps, mirroring
  `REQ-SB-25-US-01-T08`'s own "verify where the outcome first becomes
  observable" placement (`depends_on: [REQ-SB-26-US-01-T01,
  REQ-SB-26-US-01-T03, REQ-SB-25-US-01-T08]`).

`depends_on` graph confirmed acyclic (`T01`/`T02` are roots; `T03` depends
on `T02`; `T04` depends on `T01` + `T03`; the three cross-story edges onto
`REQ-SB-25-US-01-T02`/`T07`/`T08` are real, already-`Ready` task IDs read
directly from those task files, not guessed). Every locked AC has at least
one AC-ID-tagged manual verification step, all in `T04` — AC-01's step is
deliberately designed to isolate recall via `agent_memory.json` from
`REQ-SB-25`'s own already-tested `history`-replay mechanism (temporarily
clearing the agent's history entry between the two chat calls), so the
verification genuinely exercises this story's own new mechanism, not an
artefact of the dependency it builds on. All task `status:` set to `Ready`
in lockstep with the story, per this project's own established rule (a
`Ready` story with `Draft` tasks stalls the build loop).

Task `status:` moved to `Ready` in lockstep (see frontmatter of each task
file above).

**`status: Ready`, `gate: flagged` — gate is left exactly as the architect
set it (`trigger-3`, `ADR-016` created), not cleared by this pass.** This
pass did not itself trigger any new MUST-FLAG condition (no material
assumption was needed for the task breakdown — every task boundary and
`depends_on` edge is read directly off `ADR-016`'s own two-node design and
the parent story's already-bounded `Architecture scope:` file list, not
guessed; no new ADR was created or edited by this pass; no
`ESCALATIONS.md` entry was written; the 4-task decomposition is not
oversized — each task is a single, cohesive file-level change; every
locked AC is verifiable via a real HTTP round trip, none is unverifiable;
no contradictory inputs were found; and the two-node split vs. a
single-node design, plus the tool-binding choice for `extract_memory`, are
narrow implementation-mechanism calls resolved directly from `ADR-016`'s
own explicit text, not genuinely open product-level ambiguity). The one
standing flag — the human's own review of `ADR-016` itself — is the
architect's, not the decomposer's, to clear; per Pipeline.md's own
decomposer contract ("you are the only role that can mark an AC
non-locked... [gate clearing is] only if NONE of the MUST-FLAG triggers
fired" and "If the architect flagged the story this run for an ADR
change, leave it `gate: flagged`"), this pass does not clear it. The
existing `REVIEW-QUEUE.md` entry for this story (added by the architect)
stands unchanged; no new entry is needed for the decomposition itself.
This story is now eligible for `/plan-sprints` once a human clears (or the
human's own review otherwise resolves) the standing `ADR-016` flag — the
product-owner is not blocked from *grouping* it by an open `gate`, but the
operator's own stated intent throughout this batch has been to resolve
`ADR-016`'s review before the story proceeds further; no sprint action is
taken by this pass regardless (decomposer never touches sprints).

---

**Coder pass (`/implement-sprint SPRINT-015`, 2026-08-12).** All 4 tasks
built and `Done`, in dependency order (`T01`→`T02`→`T03`→`T04`). All 4
locked ACs verified live against the real backend (port `8002` — ports
`8000`/`8001` both live-occupied, same established pattern
`SPRINT-014` set), real vault, and real Compass Provider:

- **AC-01**: a fact stated in one conversation ("My favourite customer is
  Acme Corp") was correctly recalled in a later, separate conversation
  with the same agent — verified with that agent's own
  `agent_communication_history.json` entry list cleared beforehand, to
  isolate `agent_memory.json`/`retrieve_memory` as the genuine source,
  not `REQ-SB-25`'s own already-tested history replay.
- **AC-02**: a second, unrelated agent (`vault-qa`) showed no awareness of
  the "Acme Corp" fact; `agent_memory.json` confirmed to gain no
  cross-agent entry at all — isolation is structural, not just
  behavioural.
- **AC-03**: an agent asked to recall something never actually shared (a
  dog's name) honestly said it didn't know; no fabricated entry was
  written to `agent_memory.json`.
- **AC-04**: the "Acme Corp" fact was still correctly recalled after a
  full backend process restart, proving on-disk persistence, not
  in-memory/process state.

One real, live-discovered technical correction was needed in `T03`
(`graph.py`), beyond that task's own literal code sample — full detail in
`T03`'s own Implementation Log — because the real `graph.py` had already
grown a tool-execution loop (`REQ-SB-25-US-01-T08`'s own live correction)
since this story's own decomposer pass authored `T03`'s sample against an
earlier, simpler shape. The fix extends the real current graph correctly
(adds `retrieve_memory`/`extract_memory` around the existing
`call_model`⇄`execute_tools` loop, does not regress it) and corrects
`_extract_memory`'s own completion-context construction to avoid
duplicating the model's own final reply message. No locked AC was
weakened, omitted, or changed in meaning by either correction. `gate:
flagged` on `T03` (and this story) for a human spot-check of that
correction — not a blocker, `T04` proceeds on top of the corrected,
verified code, same pattern `SPRINT-014` established for its own five
corrections.

`status: Ready → Done`. Full evidence in each task's own Implementation
Log.
