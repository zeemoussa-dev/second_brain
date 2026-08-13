---
id: REQ-SB-20-US-01
title: Per-agent keyword assignment and Hub-mediated routing for cross-Section help requests, via keyword matching
requirement_ids: [REQ-SB-20]
requirement_section: "REQ-SB-20: Section Hub Intelligence & Cross-Section Routing"
phase: P1
status: Done
gate: clear
gate_reason: "Built and verified live 2026-08-12 (coder, /implement-sprint SPRINT-020) — all 6 tasks Done, all 4 locked ACs (AC-01..AC-04) verified live against the real backend/frontend. gate: flagged (inherited from T02/T04/T05/T06's own flags, per the 'a flagged task flags its parent story for the human's spot-check pass' convention) — not a blocker; see the story's own Notes (coder pass) and REVIEW-QUEUE.md for the scope-internal judgement calls awaiting spot-check, plus ADR-017's own still-open human review (unresolved by this build pass, not required for it)."
sprint: SPRINT-020
created: 2026-08-11
updated: 2026-08-12
---

# REQ-SB-20-US-01 — Per-agent keyword assignment and Hub-mediated routing for cross-Section help requests, via keyword matching

## Story

**As a** Second Brain user
**I want** each agent to have keywords describing what it's knowledgeable
about, and a request it can't handle itself to be routed, via keyword
matching, through Section Hubs rather than sent straight to another agent
in a different Section
**So that** an agent can get help from whichever agent in another Section
actually knows the answer, without any agent needing hardcoded knowledge
of every other agent in the system

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-20: Section Hub Intelligence &
  Cross-Section Routing* — "Each Section's Hub (REQ-SB-18) acts as a manager
  for its section: it understands which of its agents is knowledgeable
  about what, using a set of keywords assigned per agent alongside its
  Section. When an agent needs help with something outside its own
  knowledge, the request is routed through Hubs, not directly
  agent-to-agent — and this routing is particularly load-bearing across
  Sections: an agent in one Section needing another Section's agent must
  have that request go through both Sections' Hubs (its own Hub, then the
  target Section's Hub), never a direct agent-to-agent call across
  Sections." Acceptance: "Each agent has one or more keywords assigned
  alongside its Section; when an agent needs help outside its own
  knowledge, the request is routed via Hub(s) rather than directly to
  another agent; a request that needs an agent in a different Section is
  never sent directly agent-to-agent across Sections — it goes through the
  requesting agent's own Hub and the target Section's Hub."
- **PRD breadcrumb (2026-08-11, operator-authored, cited verbatim):**
  "Genuinely open, not decided here: the exact keyword-assignment
  mechanism (free text per agent? a fixed vocabulary? who assigns them —
  the user, or inferred?), what 'the Hub understands' and 'talk to each
  other to route the request' actually means mechanically (a real
  LLM-backed routing decision? a keyword-match lookup table, same shape as
  REQ-SB-19's chat action-triggering? something else?), and whether
  within-Section routing ... is in scope here or a separate concern from
  cross-Section routing."
- **Resolved 2026-08-11, operator-confirmed:**
  - **Routing mechanism: keyword matching**, reusing `ADR-011`'s exact
    posture (keyword-substring matching against a small per-agent-declared
    set, not a real LLM-backed/NLU pipeline) one layer up at the Hub
    level. This keeps the mechanism comfortably inside `ADR-007`'s "no
    agent-orchestration framework" boundary — no superseding ADR needed for
    the mechanism choice itself (the architect may still judge that
    Hub-to-Hub *relaying* is a new-enough capability to warrant recording
    architecturally, but the routing-decision logic itself is a direct,
    proportionate extension of an already-Accepted pattern, not new
    machinery).
  - **Within-Section routing is deferred, out of scope for this pass.**
    This reverses the analyst's own provisional "include it" reading of
    the PRD's general Acceptance clause — the operator confirmed
    **cross-Section only** for now. Scenario 2 below (within-Section
    routing) is accordingly moved to Non-Goals, not built here; a future
    story can add it once cross-Section routing is proven out.
  - **Keyword-assignment mechanism: free-text keywords per agent**,
    user-assigned on the Agent Settings surface (`AgentDetailPanel.tsx`,
    the same `kv-list` surface carrying `REQ-SB-18`'s Section picker and
    `REQ-SB-19`'s Provider picker) — no fixed vocabulary, mirroring the
    shape of `agent_registry.py`'s existing `trigger_phrases` field per
    action. Not inferred automatically.
- **Why this doesn't create an `ADR-007` tension.** `ADR-011`
  (`Implementation/Architecture/ADR.md`) already established, for chat
  action-triggering, that this project deliberately uses keyword-substring
  matching against a small per-agent-declared phrase set —
  "proportionate to what actually exists in this project today... not an
  NLU/LLM pipeline." The operator's resolution above extends that exact
  same posture one layer up (Hub-level keyword matching instead of
  agent-level trigger-phrase matching), rather than introducing a real
  LLM-backed routing decision — so `ADR-007`'s "no agent-orchestration
  framework... Hermes owns orchestration" boundary is not crossed by the
  mechanism itself. Full reasoning: `Implementation/Architecture/ADR.md` →
  `ADR-007`, `ADR-011`.
- **Genuinely new ground, not an extension of an existing mechanism.**
  Nothing in the codebase today represents "what an agent knows" beyond its
  static registry entry (id/type/label/settings/actions/trigger_phrases in
  `app/business/agent_registry.py`, per `ADR-011`), and no agent currently
  initiates a request to another agent — every existing trigger is
  user-initiated (a button, a chat message, a scheduler tick) calling
  exactly one agent's own declared action. This story is the first to
  introduce both a "what this agent knows" concept and an agent-to-agent
  (via Hub) request flow.
- **Depends on REQ-SB-18 conceptually, not just administratively.**
  Sections and their Hubs must exist as a real, addressable concept before
  a Hub can have "intelligence" about its agents or talk to another
  Section's Hub. `REQ-SB-18-US-01` (`Implementation/UserStories/REQ-SB-18-
  US-01-dynamic-agent-sections-and-assignment.md`) is `status: Ready` as of
  this spec pass — **not yet `Done`.** This story cannot actually be built
  until `REQ-SB-18-US-01` ships (a real, persisted Section concept with a
  Hub per Section). Recorded honestly here, not assumed complete.
- **Design authority — a real gap, not settled by the approved prototype.**
  `html-prototype/agents-map.html`'s side panel Settings `kv-list` (approved
  for `REQ-SB-13-US-01`) has no keyword field, and no Hub-routing visual
  concept exists anywhere in the prototype (the Hub nodes themselves are
  currently just visual section labels, per `REQ-SB-12-US-01`/`REQ-SB-18-
  US-01`'s own not-yet-built work). See the Notes' "Prototype parity"
  subsection.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. These scenarios describe only the externally observable routing
behaviour the PRD's own Acceptance text commits to; they deliberately do not
assert a specific keyword-assignment UI shape or a specific routing-decision
mechanism — both are left open per the Context above. -->

### Scenario 1: An agent has one or more keywords assigned alongside its Section

```gherkin
Given the user is viewing an agent's Agent Settings surface (the
    AgentDetailPanel side panel's kv-list)
When the user assigns one or more free-text keywords to that agent,
    describing what it is knowledgeable about
Then the agent's assigned keywords are shown on its Agent Settings surface
  And the keywords are persisted so the agent's Section's Hub can read them
    for routing purposes (retrievable via the backend, independent of the
    panel remaining open)
```
<!-- AC-ID: REQ-SB-20-US-01-AC-01 -->

### Scenario 2: A cross-Section help request is routed through both Sections' Hubs

```gherkin
Given an agent needs help with something outside its own assigned keywords
  And an agent in a different Section has keywords matching what is needed
When the request is routed
Then the routing decision resolves the requesting agent's own Section Hub
    first
  And then resolves the target Section's Hub by keyword-matching against
    every agent outside the requesting agent's own Section
  And the request is never sent directly agent-to-agent across Sections —
    both hops are recorded as explicit, inspectable fields on the routing
    result
```
<!-- AC-ID: REQ-SB-20-US-01-AC-02 -->

### Scenario 3: No agent in any other Section has matching keywords

```gherkin
Given an agent needs help with something outside its own assigned keywords
  And no agent in any other Section has keywords matching what is needed
When the request is routed
Then the routing decision reports no match, honestly and deterministically
    (never a fabricated or unrelated match)
  And the request is not delivered to any agent
```
<!-- AC-ID: REQ-SB-20-US-01-AC-03 -->

### Scenario 4: An agent with no keywords assigned is never selected as a routing target

```gherkin
Given an agent exists with no keywords currently assigned to it
When a Hub is deciding which agent should receive a routed request, for any
    need description
Then that agent is never selected as the target, regardless of what the
    request is about — structurally guaranteed by having no keyword to
    match against, not by an explicit exclusion check
```
<!-- AC-ID: REQ-SB-20-US-01-AC-04 -->

## Affected Screens

- `html-prototype/agents-map.html` — the agent detail side panel's Settings
  block needs a new keyword field (free-text, per the operator's
  resolution). Not present in the approved prototype; needs its own
  `/design` pass. No screen anywhere in the prototype visualizes
  Hub-to-Hub routing.

## Dependencies

- **Blocked by:** `REQ-SB-18-US-01` (`Ready`, **not yet `Done`**) — Sections
  and their Hubs must exist as a real, persisted, addressable concept
  before a Hub can have "intelligence" about its agents or talk to another
  Section's Hub. **Not satisfied yet as of this spec pass.**
- **Related to:** `ADR-011` — the existing keyword-substring chat
  action-triggering precedent this story's routing mechanism directly
  reuses (operator-confirmed, see Context).
- **Related to:** `ADR-007` — confirmed not in tension (see Context); the
  keyword-match mechanism stays inside its stated boundary.
- **External:** none new.

## Constraints

- A request routed outside an agent's own knowledge must never be sent
  directly agent-to-agent across Sections — it must go through the
  requesting agent's own Section Hub, then the target Section's Hub. This
  is the one piece of the PRD's Acceptance text that is fully resolved and
  non-negotiable regardless of which mechanism is chosen for the "which
  agent knows this" decision itself.
- **Keyword-assignment mechanism (operator-resolved):** free-text keywords
  per agent, user-assigned on the Agent Settings surface — no fixed
  vocabulary, no inference.
- **Routing-decision mechanism (operator-resolved):** keyword-match lookup,
  reusing `ADR-011`'s exact posture one layer up — not a real LLM-backed
  routing decision. No `ADR-007` tension (see Context).
- **Within-Section routing is explicitly out of scope this pass**
  (operator-resolved, reversing the analyst's provisional inclusion) —
  cross-Section routing only. See Non-Goals.
- This story cannot be built until `REQ-SB-18-US-01` (Sections/Hubs as a
  real concept) is `Done`.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| `REQ-SB-20-US-01-T01` | backend | `agent_keywords.json` load/save/load-all primitives | `app/data_access/vault_writer.py` | `Implementation/Tasks/REQ-SB-20-US-01-T01-agent-keywords-vault-writer-primitives.md` |
| `REQ-SB-20-US-01-T02` | backend | `agent_keywords.py` — get/set keywords + cross-Section candidate matching | `app/business/agent_keywords.py` (new) | `Implementation/Tasks/REQ-SB-20-US-01-T02-agent-keywords-business-module.md` |
| `REQ-SB-20-US-01-T03` | backend | `PATCH`/`GET /agents/{agent_id}` gain `keywords` | `app/api/agents_router.py` | `Implementation/Tasks/REQ-SB-20-US-01-T03-agents-router-keywords-field.md` |
| `REQ-SB-20-US-01-T04` | backend | `AgentConversationState` gains `hub_routing_result` | `app/business/agent_orchestration/state.py` | `Implementation/Tasks/REQ-SB-20-US-01-T04-orchestration-state-routing-field.md` |
| `REQ-SB-20-US-01-T05` | backend | `route_hub_request` node + `request_cross_section_help` tool + conditional edge + `route_cross_section_request(...)` | `app/business/agent_orchestration/graph.py` | `Implementation/Tasks/REQ-SB-20-US-01-T05-graph-route-hub-request-node.md` |
| `REQ-SB-20-US-01-T06` | frontend | Keywords kv-row + API client extension | `AgentDetailPanel.tsx`, `agentsApiClient.ts` | `Implementation/Tasks/REQ-SB-20-US-01-T06-agent-detail-panel-keywords-row.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Building a real LLM-backed intent-routing/NLU capability for Hub
  decisions** — explicitly rejected (operator-resolved); this story uses
  keyword matching only, per `ADR-011`'s existing posture.
- **Within-Section routing** (an agent asking its own Hub for help with
  another agent in the *same* Section) — explicitly deferred
  (operator-resolved 2026-08-11); this pass is cross-Section only. A
  future story can add it once cross-Section routing is proven out.
- **Any change to Hermes's own internal Section/Department/Hub concept**
  (`MEMORY.md`'s Hermes-taxonomy constraint) — Second Brain's Hub-routing
  concept here is its own business-logic concept, not a sync with Hermes's.
- **New agent capabilities beyond routing a "needs help" request** — this
  story is about routing plumbing between existing agents, not about giving
  any agent new actions or skills.
- **A full multi-step/general-purpose agent-orchestration engine** — out of
  scope regardless of the mechanism chosen; the PRD's own Acceptance text
  describes a bounded, at-most-two-hop Hub relay (own Hub, then target
  Hub), not arbitrary multi-agent planning.
- **A visual redesign of the Agents Map to depict routing paths** — not
  asked for by the PRD's acceptance text; any future visualization of
  Hub-to-Hub routing is a separate concern.

## Notes

**Prototype parity (agents-map.html):**

- `agents-map.html`'s canvas (Hub nodes, agent nodes, rings) — **N/A**, not
  touched by this story's own behavior (routing is a business-logic
  concern); the visual Hub nodes REQ-SB-18-US-01 builds are reused as-is,
  no new visual routing indicator is specced here.
- `agents-map.html`'s side panel Settings block (`kv-list`) — needs a new
  keyword field/row — **not covered by the approved prototype.** No design
  authority exists for its visual shape.
- `agents-map.html`'s side panel Available Actions/Chat/Communication
  History blocks — **N/A**, not touched by this story.
- No screen anywhere in `html-prototype/` visualizes a Hub-to-Hub routed
  request or a "no matching agent found" outcome — **not covered by the
  approved prototype.** If the resolved routing mechanism needs any new
  UI surface beyond the keyword field (e.g. a visible routing-in-progress
  or no-match indicator), that also needs its own `/design` pass.

**Resolved 2026-08-11, operator-confirmed (`ESC-004` closed on all three
points):**

1. Keyword-assignment mechanism → free text, user-assigned.
2. Routing-decision mechanism → keyword matching, reusing `ADR-011`'s
   posture — no `ADR-007` tension.
3. Within-Section routing → deferred, out of scope this pass (reverses the
   analyst's provisional inclusion).

**Still open — `/design` needed** for the keyword field on the Agent
Settings surface (no prototype coverage), and this story remains blocked
on `REQ-SB-18-US-01` shipping.

**Scoping decision (why this stays ONE story, not split into
"keyword-assignment" and "routing mechanism"):** applying this project's
standing "no independent value alone" test (already used to keep
`REQ-SB-18-US-01`'s section CRUD + per-agent assignment together, and
`REQ-SB-19-US-01`'s Provider CRUD + per-agent picker together) — a
keyword field with no routing logic ever consuming it has no value, and a
routing mechanism with no keywords to route by has no value either. The
PRD itself already reached the same conclusion, combining Hub intelligence
and cross-Section routing into one requirement "since [they are] the same
mechanism." Kept as one story here for the same reason.

gate: flagged 2026-08-11 — all three originally-open product/architecture
questions are now operator-resolved (see above); the remaining trigger is
net-new-design (`/design` pending for the keyword field) plus the
still-unmet `REQ-SB-18-US-01` dependency. See `REVIEW-QUEUE.md`.

**Reconciliation, architect pass 2026-08-12 (`/plan-tasks` step 1 —
resolves `ESCALATIONS.md` → `ESC-010`):** the Context/Constraints text
above, recorded 2026-08-11 resolving `ESC-004`, said the routing
mechanism was "keyword matching, reusing `ADR-011`'s exact posture...
This keeps the mechanism comfortably inside `ADR-007`'s 'no
agent-orchestration framework' boundary — no superseding ADR needed for
the mechanism choice itself." That conclusion is now **factually
superseded** — later the same day, `ADR-015` (LangGraph adoption,
`Accepted`) was decided, and its own Decision point 12 states plainly
that this story's Hub-routing mechanism "moves from pure keyword-
substring matching to a LangGraph-orchestrated routing node... using
each agent's declared keywords as that node's own routing input." This
was recorded honestly as a contradiction, not silently patched, in
`ESCALATIONS.md` → `ESC-010` (now flipped to `Resolved` by this
reconciliation). **What is and isn't affected:**
- The **routing algorithm itself is unchanged** — deterministic,
  case-insensitive keyword-substring matching, first-match-wins, exactly
  `ADR-011`'s posture. Only the algorithm's *housing* moves onto
  `ADR-015`'s graph. "No `ADR-007` tension" for the algorithm choice
  itself remains true; `ADR-007` is separately superseded by `ADR-015`
  for the *housing* question only (that supersession is `ADR-015`'s own
  concern, not re-litigated here).
- This story's own Acceptance Criteria (a keyword field per agent; a
  cross-Section request relayed via both Hubs, never agent-to-agent
  directly; an honest no-match report; an agent with no keywords never
  selected) are **unaffected** — they describe externally observable
  behaviour, not a specific mechanism, and remain satisfiable under the
  new housing unchanged.
- **A superseding ADR *was* needed after all — `ADR-017`** (this
  architect pass), extending `ADR-015` point 12 the same way `ADR-016`
  extended point 13 for `REQ-SB-26`. `ADR-017` settles the two things
  `ADR-015` point 12 deliberately left open:
  1. **Keyword storage:** new sibling `.second-brain/
     agent_keywords.json`, `{agent_id: [keyword, ...]}` — mirrors
     `agent_communication_history.json`/`agent_memory.json`'s per-agent-
     id-keyed-list shape, not `agent_sections.json`/`agent_providers.
     json`'s registry+assignments shape (keywords have no separate,
     shared, renameable identity the way a Section/Provider does). New
     `vault_writer.py` primitives (`load_agent_keywords`,
     `save_agent_keywords`, `load_all_agent_keywords`) and a new
     business module, `app/business/agent_keywords.py` (sibling to
     `section_registry.py`/`provider_registry.py`).
  2. **Routing-node design:** one new node, `route_hub_request`, added
     to `ADR-015`'s SAME compiled `app/business/agent_orchestration/
     graph.py` graph (not a second graph) — reached via a new
     conditional edge off the existing `call_model` node, triggered by a
     new, **orchestration-internal** (deliberately NOT registered on the
     shared MCP server) LangChain tool,
     `request_cross_section_help(need_description)` — this codebase's
     first real tool-execution loop. The mandatory "own Hub, then target
     Hub" two-hop relay is two sequential lookups inside that one node
     (`section_registry.get_agent_section` for the requester's own Hub,
     then `agent_keywords.list_candidate_agents_for_keyword_match` for
     the target Hub, cross-Section only), both hops recorded as explicit
     result fields — a real, inspectable property, not just a narrative.
     A directly callable `route_cross_section_request(...)` function is
     also exposed, mirroring `T07`'s own "public entry point, directly
     testable" precedent for `run_agent_conversation`.
  Full reasoning, every alternative considered, and every consequence:
  `Implementation/Architecture/ADR.md` → `ADR-017`; `architecture.md`
  → "Section-Hub cross-Section routing — keyword storage & routing-node
  mechanism."

**Architecture scope (bounds the decomposer/coder):** `Implementation/
Architecture/architecture.md` → "In-App Agent Orchestration (LangGraph)
& Shared MCP Server" (specifically its "Section-Hub cross-Section
routing" subsection) and "Agent Sections & LLM Providers" (for
`section_registry.py`'s existing shape this story composes with, and the
Agent Settings kv-list editing convention the keyword field follows).
Concretely: `app/business/agent_keywords.py` (new), `app/business/
agent_orchestration/graph.py` (extended — new `route_hub_request` node,
new conditional edge, new local `request_cross_section_help` tool),
`app/business/agent_orchestration/state.py` (extended — routing-outcome
field(s) as needed), `app/data_access/vault_writer.py` (new
`load_agent_keywords`/`save_agent_keywords`/`load_all_agent_keywords`
primitives + new `.second-brain/agent_keywords.json` state file),
`app/business/section_registry.py` (read-only composition, unmodified),
`app/business/agent_registry.py` (read-only composition, unmodified —
`ADR-011` point 2's "agent identity/type/actions stay hardcoded"
reasoning stays untouched). `app/api/mcp_server.py` /
`app/business/vault_query_tools.py` / `app/business/skill_tools.py` are
explicitly OUT of this story's scope — `request_cross_section_help` is
deliberately not registered there (`ADR-017` point 7). Frontend: the
Agent Settings `kv-list` (`AgentDetailPanel.tsx`) gains the approved
Keywords row (per `REVIEW-QUEUE.md`'s 2026-08-12 design sign-off), a new
`agentKeywordsApiClient.ts`-shaped call (exact file naming left to the
decomposer, mirroring `settingsApiClient.ts`'s existing convention) —
still blocked on `REQ-SB-18-US-01`'s `Done` Section concept, which is
already satisfied (`SPRINT-011`, `Done`).

**Decomposer pass, 2026-08-12 (`/plan-tasks` step 2).** All 4 scenarios
locked as `REQ-SB-20-US-01-AC-01`..`AC-04`, wording tightened for
buildability without omitting or weakening any clause:
- **AC-01** — "the agent's Section's Hub has access to those keywords for
  routing purposes" tightened to "the keywords are persisted so the
  agent's Section's Hub can read them for routing purposes (retrievable
  via the backend, independent of the panel remaining open)" — same
  substance, phrased as the concrete, verifiable persistence contract
  `T03`/`T06` actually build and verify.
- **AC-02** — "the request goes through... then through..." tightened to
  name the explicit, inspectable result fields (`ADR-017` point 6) the
  routing decision must produce, so "never agent-to-agent" is a checkable
  structural property, not just narrative.
- **AC-03** — "the requesting agent honestly reports that no matching agent
  was found" tightened to "the routing decision reports no match, honestly
  and deterministically" — per `ADR-017`'s own Context, the deterministic
  no-match decision and the eventual LLM-composed reply that narrates it
  to the user are two different layers (routing decision vs. reply
  composition); this story's own locked AC targets the decision layer,
  which is fully verifiable this pass without requiring
  `REQ-SB-25-US-01-T08`'s own live chat-wiring to be `Done` first (see
  `T05`'s own Context/Notes). Substance unchanged: no agent is ever
  contacted on a no-match, and no match is ever fabricated.
- **AC-04** — tightened to make explicit that the exclusion is
  "structurally guaranteed... not by an explicit exclusion check," per
  `ADR-017` point 4 — same requirement, naming the mechanism the ACs
  Gherkin already implied.

**Tasks:** `T01`–`T06` (table above). `T01`→`T02`→`T03`→`T06` is the
keyword-storage-and-Settings-surface chain (all within this story).
`T04`→`T05` extends `REQ-SB-25-US-01`'s own `state.py`/`graph.py` — real,
cross-story `depends_on` edges onto `REQ-SB-25-US-01-T02` (`T04`) and
`REQ-SB-25-US-01-T07` (`T05`), both already `status: Ready`, not blockers.
`T05` additionally depends on this story's own `T02` (the matching
function it composes) and `T04` (the state field it populates). No cycle:
`T01 → T02 → {T03 → T06, T05} `, `T04 → T05` (T04's own upstream is the
sibling story's `T02`, not this story's `T01`/`T02`). Every locked AC has
at least one AC-tagged verification step: `AC-01` in `T06`; `AC-02`/`AC-03`/
`AC-04` in `T05` (via the directly-callable `route_cross_section_request`
`ADR-017` explicitly built for this purpose — see `T05`'s own Context/Notes
for why this does not require `REQ-SB-25-US-01-T08`'s live chat-wiring to
be `Done` first).

**Status → `Ready`; `gate` stays `flagged`.** Every AC is locked, every
locked AC has a tagged verification step, `depends_on` is acyclic — the
decomposer-owned advancement checks all pass, so `status:` moves
`Draft → Ready` and every task above is written at `status: Ready`
(lockstep). `gate:` is **left `flagged`** — per `Implementation/
Pipeline.md`, an ADR-creation flag set by the architect (`ADR-017`, this
same `/plan-tasks` pass) is not the decomposer's to clear; the human
reviews `ADR-017` alongside this task breakdown together (see
`REVIEW-QUEUE.md`'s existing 2026-08-12 entry, unchanged by this pass — no
new entry needed, no new MUST-FLAG trigger fired at this decomposition
step itself). No `ESCALATIONS.md` entry written by this pass.

---

**Coder pass (2026-08-12, `/implement-sprint SPRINT-020`).** All 6 tasks
built and verified live, in dependency order (`T01` → `T02` → `{T03 → T06,
T05}`; `T04` independent, cross-story `depends_on` onto already-`Done`
`REQ-SB-25-US-01-T02`/`T07`). All 4 locked ACs (`AC-01`..`AC-04`) pass —
real backend (`.venv`, real `.second-brain/` state files, real
`--reload` dev server on `:8001`), real frontend dev server on `:5173`,
real headless-Chrome-via-CDP interaction and screenshots against the
approved prototype sign-off. Full verification transcripts are in each
task's own `## Implementation Log` (`Implementation/Tasks/
REQ-SB-20-US-01-T01`..`T06`).

Several real files (`graph.py`, `state.py`, `agents_router.py`) had grown
materially beyond this task breakdown's own literal "Before" code samples
by build time (`REQ-SB-26-US-01`/`ADR-016` memory nodes,
`REQ-SB-25-US-01-T08`/`REQ-SB-31-US-01`'s live tool-execution-loop and
async corrections had all landed in between). Every task was composed
around the REAL current file, never overwritten with a stale sample, per
this project's own established Learnings pattern — most load-bearing at
`T05`: the real `graph.py` already has a *generic* `_execute_tools` node
that invokes any tool call by name, so the new `route_hub_request`
conditional-edge branch had to intercept `request_cross_section_help`
calls *before* that generic path, or the tool's own intentionally-
`NotImplementedError` body would have been genuinely invoked. Full
reasoning in each affected task's own Implementation Log
(`T02`/`T04`/`T05` most substantively; `T03`/`T06` composed around real
current files too, with no load-bearing correction needed). One additional
minor finding: two of the task files' own illustrative example
need-descriptions (`T02`/`T05`) did not actually contain their own example
keywords as a substring under the exact deterministic algorithm specified
— a wording slip in the test data, not a code defect; corrected consistently
across both tasks' own verification, logged in each.

This story's own `gate: flagged` (inherited from `T02`/`T04`/`T05`/`T06`'s
own flags, per the "a flagged task flags its parent story for the human's
spot-check pass" convention) — not a blocker, `status: Done`. `ADR-017`'s
own separate, still-open human-review item (`REVIEW-QUEUE.md`, unresolved
since 2026-08-12) is unaffected and unresolved by this build pass — per
this story's own prior note, an ADR-creation flag does not halt
`/implement-sprint` either, mirroring the same posture already established
for `/plan-tasks`. `SPRINT-020` is also `Done` — see its own Retrospective.

**Working-mode-aware Hub-routing gating — explicitly deferred, not built
this pass (2026-08-12, analyst — `ESCALATIONS.md` → `ESC-013`).** This
story's own `status:`/`gate:` were reset `Ready → Draft` /
`clear → flagged` on the premise that `REQ-SB-21`'s Manual-mode correction
(only a direct human ask "asked" a Manual agent — never another agent's
Hub-routed request) would need a matching new AC/constraint here: a
Manual-mode agent excluded from `list_candidate_agents_for_keyword_match`'s
candidate results. The operator has since directly clarified this is
**out of scope for this pass**: "REQ-SB-20 It can be Offered but it
doesn't execute — We will get to this Part when we reach this level of
the product." Concretely: `ADR-017`'s already-approved routing-node design
only ever *returns a matched-candidate description to the requester* — it
does not itself invoke any action on the target agent, Manual-mode or
otherwise (no story yet lets a routed request actually execute anything on
its target). Since there is no real cross-agent action-execution mechanism
to gate yet, gating candidate selection by working mode has nothing real
to protect at this story's own level right now, and would be speculative,
premature scope. **No Acceptance Criteria, Constraint, or
candidate-selection logic changes as a result of `ESC-013`** — `AC-01`
through `AC-04` above, and `T01`-`T06`, stand exactly as the 2026-08-12
decomposer pass left them. This deferral is deliberately recorded here as
a Note (not a Constraint, not a new AC) so a future story that adds real
cross-agent action execution knows to revisit working-mode-aware gating of
Hub-routing candidacy at that point — `REQ-SB-21`'s own Manual-mode
correction (`ESC-013`) stands on its own, scoped entirely to `_invoke_action`'s
direct-trigger gate, independent of Hub routing.
**Gate: `gate: clear`, 2026-08-12.** No MUST-FLAG trigger fires: no
material assumption was made (the operator's own words, quoted above,
directly resolve the question the premature reset raised); no PRD text is
`<!-- Draft -->`/unfinalised; no ADR created/edited by this note; no new
`ESCALATIONS.md` entry opened (this resolves the already-open `ESC-013`,
for this story's own portion of it); not oversized; no contradictory
inputs; and the operator's direct words leave no genuinely open
interpretation. **`status:` reset directly `Draft → Ready`** — per the
operator's own explicit authorization (having confirmed no real change was
needed beyond this Note), not this analyst unilaterally advancing a story
past `Draft` on its own judgement; the already-locked `AC-01`-`AC-04` and
`T01`-`T06` are unaffected and untouched, so no re-decomposition was
required to justify the reinstated `Ready` status.
