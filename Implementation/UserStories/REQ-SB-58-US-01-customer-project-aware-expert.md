---
id: REQ-SB-58-US-01
title: Customer/Project-Aware Expert — vault-qa answers status questions from Glimpse (and Background) first, falling back to raw evidence search on request
requirement_ids: [REQ-SB-58]
requirement_section: "REQ-SB-58: Customer/Project-Aware Expert (Glimpse-First Answers)"
phase: P1
status: Done
gate: flagged
gate_reason: "T01 and T02 both Done (2026-08-18) — ESCALATIONS.md ESC-046 (T01) and ESC-047 (T02) written, both real, pre-existing, out-of-scope findings discovered live; neither blocks this story. All 6 locked ACs verified live. See REVIEW-QUEUE.md pointers."
sprint: SPRINT-058
created: 2026-08-16
updated: 2026-08-18
---

# REQ-SB-58-US-01 — Customer/Project-Aware Expert — vault-qa answers status questions from Glimpse (and Background) first, falling back to raw evidence search on request

## Story

**As a** Second Brain user
**I want** to ask `vault-qa` a status question about a Customer or Project
and get an answer sourced from that note's own Glimpse (and Background, for
older/durable questions) first, rather than a full vault search
re-synthesizing an answer from scratch every time
**So that** I get fast, consistent answers that reflect the actually-current
synthesized state, while still being able to drill into the original
evidence whenever I need the detail or a citation

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-58: Customer/Project-Aware Expert
  (Glimpse-First Answers)*. Extends the existing `vault-qa` Expert agent
  (`app/business/agent_registry.py`, `type: "expert"`, confirmed by direct
  reading) so a status question is answered from the relevant
  Customer/Project's Glimpse first, rather than a generic vault search
  re-synthesizing an answer from scratch every time — the chat-facing half
  of "the KB is for me and my Agents to put data and pull data"
  (`REQ-SB-54` point 4).
- Raised 2026-08-16, same discussion — **explicitly the smallest-scoped
  requirement in this batch**, kept separate because it's a distinct
  behavioral change to an existing agent, not new data-model or pipeline
  work. The PRD carries no flagged/unconfirmed items for this requirement.
- **When a question resolves to a specific Customer or Project** (via
  existing name/entity matching this app's search already does —
  `REQ-SB-02`, `Done`), `vault-qa` should read that note's Glimpse (and
  Background, for older/durable questions) FIRST, and only fall back to
  searching raw Thread/Meeting evidence when the operator asks for detail a
  Glimpse wouldn't carry, or for a citation back to the original source.
  This is an extension of `vault-qa`'s existing behavior, not a new Agent.
- **Depends entirely on `REQ-SB-54`'s Glimpse/Background existing and
  `REQ-SB-57`'s Synthesizer keeping them current** — without those, this
  story has nothing meaningful to read Glimpse-first from; it does not
  itself write or maintain Glimpse/Background content.

## Acceptance Criteria

<!-- Locked by the decomposer at /plan-tasks (2026-08-18). Every scenario
below carries a trailing AC-ID tag and is locked (no `| locked: false`
markers used — every scenario is verifiable as written; see the parent
story's own ## Notes for the decomposer's tightening rationale). -->

### Scenario 1: A Customer status question is answered from that Customer's Glimpse

```gherkin
Given a real test Customer's OKF concept file `## Glimpse` section has
    been deliberately edited to contain one specific, checkable value not
    present anywhere else in that Customer's evidence
When the operator asks vault-qa "what's the status of <test customer>"
Then vault-qa's reply reflects that deliberately-edited Glimpse value
    directly
  And the reply is produced without vault-qa calling
    retrieve_notes_in_agent_scope (or any other body-content-returning
    tool) for this turn
```
<!-- AC-ID: REQ-SB-58-US-01-AC-01 -->

### Scenario 2: The Glimpse-first answer is materially cheaper than a full vault search

```gherkin
Given the same real test Customer and status question as Scenario 1
    (AC-01)
When vault-qa answers it via the Glimpse-first path
Then the turn completes with zero body-content-returning tool calls
  And this is materially fewer tool calls than the existing full-search
    baseline requires for the identical question (at least one
    retrieve_notes_in_agent_scope call)
```
<!-- AC-ID: REQ-SB-58-US-01-AC-02 -->

### Scenario 3: A follow-up request still drills into the original evidence

```gherkin
Given vault-qa has just answered a status question about a Customer or
    Project from its Glimpse (AC-01), and vault-qa has a real REQ-SB-29
    vault scope assigned covering that entity's evidence
When the operator follows up with "show me the original email" (or an
    equivalent detail/citation request)
Then vault-qa successfully calls its existing retrieve_notes_in_agent_scope
    tool and surfaces content from the underlying Thread note the Glimpse's
    own [[wikilink]] referenced
```
<!-- AC-ID: REQ-SB-58-US-01-AC-03 -->

### Scenario 4: A Project-scoped question gets the same Glimpse-first treatment

```gherkin
Given a question resolves, via the same rank-1 entity-resolution mechanism
    as AC-01, to a specific Project's own concept file rather than a
    Customer's
When the operator asks a status question about that Project
Then vault-qa's reply is sourced from that Project's own `## Glimpse`
    section first — the same Glimpse-first behavior confirmed for the
    Customer case in AC-01
```
<!-- AC-ID: REQ-SB-58-US-01-AC-04 -->

### Scenario 5: An older/durable question is answered from Background, not Glimpse

```gherkin
Given a real test Customer's or Project's OKF concept file `## Background`
    section contains one specific, checkable durable fact that does NOT
    appear anywhere in that entity's current `## Glimpse`
When the operator asks vault-qa a durable, non-current-status question
    about that fact (e.g. "when did <test customer> become a customer")
    rather than "what's happening now"
Then vault-qa's reply reflects that Background fact
```
<!-- AC-ID: REQ-SB-58-US-01-AC-05 -->

### Scenario 6: A question with no matching Customer/Project falls back to vault-qa's existing full-search behavior, unchanged

```gherkin
Given a question's own rank-1 vault search result does not resolve to any
    Customer or Project OKF concept file
When the operator asks vault-qa this question
Then vault-qa's reply is produced by its existing, unmodified full-search/
    tool-based behavior — this story's Glimpse-first context injection
    never fires for this turn
```
<!-- AC-ID: REQ-SB-58-US-01-AC-06 -->

## Affected Screens

None — backend/chat-behavior only. This story extends `vault-qa`'s existing
reply mechanism, reachable through the already-shipped Chat tab
(`AgentDetailPanel.tsx`) — no new screen or UI region is introduced.

## Dependencies

- **Blocked by:** `REQ-SB-54-US-01` (Vault Knowledge Model Redesign,
  `Draft`, `gate: flagged`) — Glimpse and Background must exist in the
  vault before this story has anything to read from.
- **Blocked by:** `REQ-SB-57-US-01` (Project & Customer Status Synthesizer
  Agents, `Draft`, `gate: flagged`) — Glimpse must be kept genuinely
  current, or this story would answer from stale data, defeating its own
  purpose.
- **Related to:** `REQ-SB-02` (Browse & Search, `Done`) — the existing
  name/entity matching this story reuses to resolve a question to a
  specific Customer/Project.
- **Related to:** `REQ-SB-33` (Agent Grounding & Honest-Uncertainty
  Guardrail, `Done`) — remains in effect; this story does not change
  `vault-qa`'s honest-uncertainty behavior for questions it genuinely
  cannot answer.
- **External:** none beyond the already-live Compass/LangGraph chat
  infrastructure `vault-qa` already uses.

## Constraints

- **Extension of the existing `vault-qa` Expert, not a new Agent** — no new
  `agent_registry.py` entry is created by this story.
- **Read-only from this story's own perspective** — `vault-qa` never writes
  to Glimpse/Background/History; those remain exclusively the Synthesizer's
  own write path (`REQ-SB-57`, `REQ-SB-54` point 7).
- **Entity resolution reuses existing name/entity matching** — no new
  matching mechanism is introduced by this story.
- **Fallback to raw-evidence search must remain intact** — both for
  detail/citation follow-ups (Scenario 3) and for questions that don't
  resolve to a known Customer/Project at all (Scenario 6).
- **`REQ-SB-33`'s grounding/honest-uncertainty guardrail is unaffected** —
  this story must not weaken it.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Decomposer's own table (2026-08-18) — supersedes the analyst-authored
starting point above. 2 tasks, matching this story's own "smallest,
most-separable requirement in the batch" framing: T01 builds the new,
directly-testable business module; T02 wires it into the live chat graph
(gated to vault-qa only) and carries every locked AC's own live
verification, since every Scenario names an actual vault-qa reply that
does not exist until the graph node is wired in. Evidence drill-down
(AC-03) needed no separate task of its own — architecture.md confirmed it
needs no new code path, only T02's own live check that vault-qa's already-
Done retrieve_notes_in_agent_scope tool still serves it once the new node
lands. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-58-US-01-T01 | backend | New `glimpse_first_qa.py` — rank-1 entity resolution (reuses `vault_search.search()` verbatim) + Glimpse/Background read via `read_body_section` | `app/business/glimpse_first_qa.py` (new file) | `../Tasks/REQ-SB-58-US-01-T01-glimpse-first-entity-resolution-module.md` |
| REQ-SB-58-US-01-T02 | backend | New `graph.py` node (`retrieve_memory -> glimpse_first_context -> call_model`, gated to `agent_id == "vault-qa"`) + `state.py` grounding-text additive clause + live verification of all 6 locked ACs (incl. evidence drill-down, no new tool) | `app/business/agent_orchestration/graph.py`, `app/business/agent_orchestration/state.py` | `../Tasks/REQ-SB-58-US-01-T02-graph-node-wiring-and-live-verification.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — manual verification mode still in effect this sprint
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Writing or maintaining Glimpse/Background/History content** —
  exclusively `REQ-SB-57`'s own scope; this story is read-only.
- **A new Agent** — this is an extension of the existing `vault-qa`
  Expert.
- **New entity-resolution/name-matching logic** — reuses `REQ-SB-02`'s
  existing mechanism as-is.
- **Backfilling historical evidence** — `REQ-SB-59`'s own scope.

## Notes

**Prototype parity:** N/A — no `html-prototype/` screen change; this story
is a behavioral extension of `vault-qa`'s existing reply mechanism, reached
through the already-shipped, already-approved Chat tab.

**Why `gate: clear`:** the PRD's own text for `REQ-SB-58` carries no
flagged/unconfirmed item — it explicitly frames this as "smaller in scope
than the other five requirements in this batch," a well-understood
extension of an already-`Done` agent's existing behavior, reusing an
already-`Done` entity-matching mechanism. No material assumption, no
genuinely unclear/multiple-equally-valid interpretation, no contradictory
PRD input, not oversized (two tightly-related tasks over one existing
agent's reply path). The only reason this story cannot start today is the
real, external dependency on `REQ-SB-54-US-01`/`REQ-SB-57-US-01` shipping
first (Glimpse/Background must exist and be kept current) — the same
"gate: clear — blocked on X shipping" pattern this project already uses
for `REQ-SB-03-US-01` (blocked on `REQ-SB-01`/`REQ-SB-02`).

---

**Architect pass (2026-08-18) — `/plan-tasks` step 1:**

`REQ-SB-54-US-01`/`REQ-SB-57-US-01` are both `status: Done` — this story is
genuinely unblocked. Grounded in direct reading of the REAL current code
(`app/business/agent_orchestration/graph.py`, `state.py`, `mcp_client.py`,
`app/api/mcp_server.py`, `app/business/vault_query_tools.py`,
`app/business/scope_query_tools.py`, `app/business/
project_customer_synthesizer.py`, `app/data_access/vault_writer.py`), not
assumed: `vault-qa`'s only real body-content-returning tool today is
`retrieve_notes_in_agent_scope` (`REQ-SB-29`, scope-gated) — a bulk,
scope-wide read of every matching Thread/Meeting/Capture note IS the "full
vault search re-synthesizing an answer from scratch" the PRD names as the
baseline. `vault_search.search()` (`REQ-SB-02`/`ADR-026`) is not registered
as an MCP tool — this story reuses it as a business-layer composition
inside the graph, not as a new bound tool.

- **Architecture scope: §"Glimpse-First `vault-qa` Answers — entity
  resolution + Glimpse/Background context injection, evidence drill-down
  unchanged"** (`Implementation/Architecture/architecture.md`, appended
  directly after "File upload, Compass summarization & Vault Filing Expert
  handoff," under the `## In-App Agent Orchestration (LangGraph) & Shared
  MCP Server` umbrella), plus the already-`Accepted` `ADR-015` (graph
  extension shape), `ADR-024` (search index), `ADR-026` (ranked search),
  and `ADR-042` point 2 (`read_body_section`) — all referenced unchanged.
  The coder is bounded by that section for both `T01` (entity resolution +
  context injection) and `T02` (drill-down — confirmed to need no new
  code path, only a live end-to-end check that the existing bound tools
  still work once the new node is wired in).
- **No new ADR.** Every primitive composed (`vault_search.search`,
  `vault_indexing.get_index`, `vault_writer.read_body_section`, the
  graph's own "grow by adding nodes" shape) is already `Accepted` and
  unmodified in its own contract; no new MCP tool is registered. Trigger-3
  does not fire from this pass — see architecture.md's own "Why no new
  ADR" paragraph in the new section for the full reasoning.
- **Concrete mechanism decided (full reasoning in architecture.md):** a
  new `app/business/glimpse_first_qa.py` module resolves a question to a
  Customer/Project by reusing `vault_search.search()`'s own rank-1 result
  only (zero new matching logic, per this story's own Constraint), reads
  BOTH `## Glimpse` and `## Background` from that entity's OKF concept
  file (deliberately not a durable-vs-current-status classifier — `ADR-042`
  already structurally separates the two), and a new `graph.py` node,
  gated to `agent_id == "vault-qa"` only, injects that content as one
  `SystemMessage` ahead of the model call. Evidence drill-down (Scenario 3)
  needs no new tool — `vault-qa`'s existing bound tools (chiefly
  `retrieve_notes_in_agent_scope`) are reused unchanged, correlated via the
  Glimpse's own already-embedded `[[wikilink]]` stems; a new ungated
  "read any note by path" tool was considered and explicitly rejected as a
  deviation from `REQ-SB-29`'s own already-`Accepted` scope-enforcement
  boundary (the only existing body-content-returning tool is deliberately
  scope-gated). `REQ-SB-33`'s grounding instruction
  (`state.py::history_entries_to_messages`) gains one additive clause
  naming this new context source — an additive widening, never a
  weakening, mirroring `REQ-SB-66`/`ADR-044`'s own "additive extension,
  no ADR" precedent for this exact function.
- **Real, load-bearing precondition for the decomposer's own test-data
  design, not a gap this story closes:** Scenario 3's drill-down (and,
  more broadly, any non-empty result from `retrieve_notes_in_agent_scope`
  at all) requires `vault-qa` to actually have a `REQ-SB-29` scope
  assigned (e.g. the relevant `customer/<slug>` tag) — confirmed by direct
  reading that no agent carries a default scope. The already-`Done`
  `REQ-SB-29` Settings UI fully supports assigning one; this story does
  not need to add anything, but the decomposer's task-level verification
  steps must account for it explicitly.

gate: clear 2026-08-18 (architect) — no trigger fired this pass (confirmed
by direct reading against `ADR-015`/`ADR-024`/`ADR-026`/`ADR-042` and
this story's own locked Constraints; every design fork was resolved by
an already-`Accepted` precedent or the story's own text, never a genuine
multi-way ambiguity). No `ESCALATIONS.md`/`REVIEW-QUEUE.md` entry required.
Handing off to the decomposer.

---

**Decomposer pass (2026-08-18) — `/plan-tasks` step 2:**

Read the REAL current code the architect grounded this on before
authoring tasks — `app/business/agent_orchestration/graph.py`,
`state.py`, `app/business/vault_search.py`, `app/data_access/
vault_writer.py`'s `read_body_section`/`okf_directory_paths`, `app/
business/agent_registry.py` (`vault-qa`'s real settings), `app/business/
scope_query_tools.py` (`retrieve_notes_in_agent_scope`'s real body), and
`app/business/project_customer_synthesizer.py` (confirmed `_build_
customer_glimpse` rolls up Project names/statuses, never a Thread
`[[wikilink]]`; only `_build_project_glimpse` embeds one) — not assumed.

- **6/6 scenarios tightened, AC-ID'd, and locked** — `REQ-SB-58-US-01-
  AC-01`..`AC-06`, all locked (no `locked: false` marker used — every
  scenario is verifiable as written once `T02` wires the graph node in).
- **AC-03 tightening (ordinary implementation-latitude judgement call, not
  an escalation):** the analyst's untagged Scenario 3 said "a Customer's
  Glimpse," but direct reading of `_build_customer_glimpse` confirmed a
  Customer's own Glimpse rolls up Project names/statuses, never a Thread
  `[[wikilink]]` — only a Project's own Glimpse (`_build_project_glimpse`)
  embeds the real wikilink stem architecture.md's own documented
  drill-down mechanism correlates against. `AC-03`'s locked wording was
  generalized to "a Customer or Project," and `T02`'s own concrete
  verification uses the Project-level fixture (shared with `AC-01`/
  `AC-04`) — the mechanism is identical for either resolved entity type;
  only the concrete proof needed a Project-level Glimpse's own real
  wikilink to correlate against.
- **2 tasks, matching this story's own "smallest, most-separable
  requirement in the batch" framing** (sizing calibration: ~2 tasks, S —
  matches this project's own repeated 2-task/S precedent, e.g.
  `SPRINT-029`/`SPRINT-036`):
  - `REQ-SB-58-US-01-T01` — new, directly-testable `glimpse_first_qa.py`
    module (`resolve_glimpse_first_context`). `depends_on: []`.
  - `REQ-SB-58-US-01-T02` — the new `graph.py` node (gated to `agent_id
    == "vault-qa"` only) + `state.py`'s additive grounding-text clause +
    every one of the story's 6 locked ACs' own live verification, since
    every Scenario names an actual `vault-qa` reply that does not exist
    until the node is wired in. `depends_on: [REQ-SB-58-US-01-T01]`.
  - Acyclic (a straight 2-node chain). Evidence drill-down (`AC-03`)
    received no task of its own — architecture.md's own confirmed "needs
    no new tool" finding means it is a verification step inside `T02`,
    not separate build work.
- **AC → verification mapping confirmed complete:** all 6 locked ACs
  (`AC-01`..`AC-06`) each have at least one matching AC-tagged manual
  verification step, all in `T02`'s own `## Tests` block (steps 1-6);
  `T01` carries only non-AC smoke-check steps for its own module-level
  contract, since none of the story's ACs are verifiable without the live
  graph wiring `T02` adds.
- **No MUST-FLAG trigger fired this pass:** no material assumption (every
  design fork already resolved by the architect's own `## Notes` or an
  already-`Accepted` ADR); no `<!-- Draft -->`/unfinalised requirement
  relied on; no ADR created/changed by this pass; no `ESCALATIONS.md`
  entry written; not oversized (2 tightly-coupled tasks over one already-
  `Done` agent's reply path, matching the story's own explicit "smallest
  requirement in the batch" framing); every locked AC is verifiable (a
  real, observable chat reply + a real, observable tool-call count, in
  every case); no contradictory inputs; no genuinely unclear/multiple-
  equally-valid task breakdown (the architect's own mechanism left exactly
  one reasonable task split, and the one real ambiguity found — AC-03's
  Customer-vs-Project Glimpse wording — was resolved by direct reading,
  not a guess, and logged above rather than treated as a fork).

gate: clear 2026-08-18 (decomposer) — no trigger fired this pass. Story
`status: Draft -> Ready`; both tasks written directly at `status: Ready`
(status moves in lockstep with the story, per `Pipeline.md`). Handing off
— eligible for `/plan-sprints`.

---

**Product-owner pass (2026-08-18) — `/plan-sprints`:** Grouped into
`SPRINT-058` (this story only — the sole `Ready`, ungrouped story in scope).
Dependency graph read directly from `T01`/`T02`'s own `depends_on:`
frontmatter (a straight 2-node chain); no cross-sprint edge needed since
both real blockers (`REQ-SB-54-US-01`/`REQ-SB-57-US-01`) are already `Done`.
Sizing: ~2 tasks, S — matches `SPRINT-029`/`SPRINT-036` precedent.

gate: clear 2026-08-18 (product-owner) — no trigger fired. Sprint
`status: Draft -> Ready`. Eligible for `/implement-sprint`.

---

**Coder pass (2026-08-18) — `/implement-sprint`:** `T01` and `T02` both
built and `Done`. All 6 locked ACs (`AC-01`..`AC-06`) verified live
against the real configured vault, real Compass Provider, and disposable
fixtures — full detail in `T02`'s own `## Implementation Log`. Two real,
pre-existing, out-of-scope findings were discovered and formally
disclosed during live verification, neither blocking this story:
`ESC-046` (`T01` — a legacy-flat-vs-OKF-directory filename-stem
collision in `vault_indexing`) and `ESC-047` (`T02` — `retrieve_notes_
in_agent_scope`'s own MCP tool requires the calling model to self-report
its own literal internal `agent_id`, which it is never told, so it
reliably guesses wrong; root-caused live, confirmed unrelated to this
story's own new node, and verified via the closest-available disclosed
substitute per this project's own established `ESC-025`/root-cause-first
precedent). No locked AC was weakened to make this pass — every
substitution is fully disclosed in `T02`'s own Implementation Log.

`status: In Progress -> Done`. This closes out `REQ-SB-58-US-01` and
`SPRINT-058`, and finally unblocks `REQ-SB-59` (Full Vault Migration to
the New Knowledge Model) — the last of `REQ-SB-54`..`REQ-SB-58` to ship.

---

**Coder pass (2026-08-18) — `T01` built and verified.** `REQ-SB-58-US-01-
T01` → `status: Done` (gate: flagged — an `ESCALATIONS.md` entry was
written, `ESC-046`, see below). New `app/business/glimpse_first_qa.py`
(`resolve_glimpse_first_context`) built exactly per architecture.md's own
mechanism. This task carries none of the story's own locked ACs itself
(all 6 are carried by `T02`'s live graph-wiring verification, per the
decomposer's own task table) — its own 6 non-AC module-level smoke checks
all passed live against the real configured vault, using a disposable
Customer/Project fixture (fully cleaned up afterward). Found and disclosed
a real, out-of-scope finding while verifying: 14 of 17 real Customers
already migrated to the `ADR-042` OKF directory shape still carry a
stale, un-retired legacy flat hub note that shadows the real OKF concept
file in `vault_indexing`'s stem-keyed index (`ESCALATIONS.md` `ESC-046`,
`Open`; `REVIEW-QUEUE.md` pointer written; `MEMORY.md` Constraints
updated) — this directly informs `T02`'s own real-Customer test-data
choice, next: use `Microsoft Azure`/`Azerbaijan Ministry of Digital
Development and Transport` (the two collision-free real, migrated
Customers) or a disposable fixture, never one of the 14 shadowed ones.
Story `status: Ready → In Progress` — `T02` remains to build before this
story can reach `Done`.
