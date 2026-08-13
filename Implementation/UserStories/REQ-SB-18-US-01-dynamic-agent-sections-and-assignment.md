---
id: REQ-SB-18-US-01
title: User-editable agent Sections, decoupled from agent Type, with per-agent section reassignment
requirement_ids: [REQ-SB-18]
requirement_section: "REQ-SB-18: Dynamic Agent Sections & Agent-to-Section Assignment"
phase: P1
status: Done
gate: clear
gate_reason: "Resolved 2026-08-12 — operator approved ADR-014 as written. All 9 ACs already built and verified live against it (2026-08-11); no rebuild required."
sprint: "SPRINT-011"
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-18-US-01 — User-editable agent Sections, decoupled from agent Type, with per-agent section reassignment

## Story

**As a** Second Brain user
**I want** to create, rename, and delete my own business-domain Sections from
Settings, and move any agent into a different Section independently of that
agent's Worker/Producer/Expert Type
**So that** the Agents Map's grouping reflects how I actually think about my
work (Technical/Sales/Productivity/Customers/Products, or whatever I rename
it to), instead of a fixed structure where the only grouping axis is an
agent's implementation type

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-18: Dynamic Agent Sections &
  Agent-to-Section Assignment* — "The Agents Map's angular grouping (its
  'sections' — today Capture/People/Q&A, one per agent type) becomes a
  user-editable concept, replacing the current 1:1 section-equals-type
  structure: sections are named business-domain groupings (starting with
  Technical, Sales, Productivity, Customers, Products) that the user can
  create and edit from Settings, independent of an agent's Worker/Producer/
  Expert type (which continues to drive the agent's ring position — the two
  are now separate axes, not the same thing). Every agent belongs to exactly
  one section; the user can move any agent to a different section from the
  Agent Settings surface." Acceptance: "Settings has a Sections area where
  the user can create, rename, and delete a section; the Agent Settings
  surface (REQ-SB-13's detail panel, or a dedicated Settings agent list)
  lets the user reassign any agent to a different existing section; the
  Agents Map reflects the current section set and agent-to-section
  assignments, including sections with zero agents and agents whose section
  was just changed, without a code change or restart."
- **PRD breadcrumb (2026-08-11, operator-resolved, cited verbatim, not
  re-decided here):** Section and Type are independent axes — an agent keeps
  its ring-determining Worker/Producer/Expert Type and separately has a
  Section; a section can contain agents of any type. Starting section set:
  Technical, Sales, Productivity, Customers, Products — editable/extensible
  via Settings (create/rename/delete), not a fixed enum. Initial
  agent→section assignment (Email/Meeting/To-Do Capture → Productivity,
  People Notes → Customers, Vault Q&A → Technical) is a starting default the
  user picked, immediately rearrangeable — not load-bearing product meaning,
  so no scenario below asserts that specific starting mapping as a locked
  behaviour beyond "the starting section set exists and is populated."
- **Real architectural consequence, explicitly left open by the PRD
  breadcrumb, not resolved here:** agents and their type/settings/actions
  currently live in a static, hardcoded Python dict
  (`src/backend/app/business/agent_registry.py`), per `ADR-011` point 2 —
  reasoned there as "app/deployment configuration, not vault content, not
  something a future process could organically add to." This story's
  user-driven CRUD via a Settings UI is, per the PRD breadcrumb's own words,
  "a different kind of mutability than that reasoning was written against"
  (explicit user action, not automatic growth) — `/plan-tasks` must decide
  the new persistence mechanism (e.g. a mutable `.second-brain/` state file
  extending the existing convention `ADR-011` already used for
  communication history, vs. some other store) and how it interacts with
  `ADR-011`'s still-otherwise-valid "not vault-derived" reasoning for the
  agent identity/type/actions portion of the registry (only the *section*
  field becomes user-mutable here — the agent's own existence, type, and
  actions are unaffected by this story).
- **Design authority — a real gap, not settled by the approved prototype.**
  `html-prototype/settings.html` (approved for REQ-SB-12-US-01) has only a
  Vault card and a Connections card — no Sections area exists anywhere in
  the prototype. `html-prototype/agents-map.html`'s side panel (approved for
  REQ-SB-13-US-01) has no Section field in its Settings `kv-list`, and no
  section-reassignment control anywhere. The Agents Map canvas itself
  (`layoutAgents.ts`) currently hardcodes exactly 3 sections
  (`capture`/`people`/`qa`) at hand-picked `hubAngleDeg` values, 1:1 with the
  3 agent types — this story's decoupled, user-created, arbitrary-N-section
  model needs a genuinely new layout approach (computing hub angles for
  however many sections currently exist, including zero-agent sections),
  which the approved prototype never designed. See the Notes' "Prototype
  parity" subsection and the flag reasoning below.
- **Precedent surfaces this story attaches to (both already `Done`):**
  `REQ-SB-12-US-01` built the reachable, currently-placeholder Settings page
  (`src/frontend/src/pages/SettingsPage.tsx`, `styles/settings.css`) this
  story adds a Sections area to; `REQ-SB-13-US-01` built the Agent Settings
  detail panel (`AgentDetailPanel.tsx`) this story adds a section-picker
  control to, and the `GET /agents`/`GET /agents/{id}` backend surface
  (`agents_router.py`, `agent_registry.py`) this story extends.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: The Sections area shows the starting section set

```gherkin
Given the user has never created or edited any section
When the user opens Settings' Sections area
Then the starting section set is listed: Technical, Sales, Productivity,
    Customers, Products
```
<!-- AC-ID: REQ-SB-18-US-01-AC-01 -->

### Scenario 2: Creating a new section from Settings

```gherkin
Given the user is viewing Settings' Sections area
When the user creates a new section with a name that doesn't already exist
Then the new section appears in the Sections area
  And the new section is available as a choice on the Agent Settings
    surface's section picker
```
<!-- AC-ID: REQ-SB-18-US-01-AC-02 -->

### Scenario 3: Renaming an existing section

```gherkin
Given a section exists with one or more agents currently assigned to it
When the user renames that section from Settings
Then the section's new name is shown in Settings' Sections area
  And every agent previously assigned to it remains assigned to the same
    section under its new name (the rename does not change assignment)
```
<!-- AC-ID: REQ-SB-18-US-01-AC-03 -->

### Scenario 4: Deleting a section that has no agents assigned

```gherkin
Given a section exists with zero agents currently assigned to it
When the user deletes that section from Settings
Then the section no longer appears in the Sections area
  And the section is no longer offered as a choice on the Agent Settings
    surface's section picker
```
<!-- AC-ID: REQ-SB-18-US-01-AC-04 -->

### Scenario 4b: Deleting a section that still has agents assigned is blocked

```gherkin
Given a section exists with one or more agents currently assigned to it
When the user attempts to delete that section from Settings
Then the deletion is refused
  And a clear message explains that every agent must be moved out of the
    section first
  And the section, and every agent still assigned to it, are unchanged
```
<!-- AC-ID: REQ-SB-18-US-01-AC-05 -->

### Scenario 5: Reassigning an agent to a different section from the Agent Settings surface

```gherkin
Given the user has an agent's Agent Settings surface open, and at least one
    other existing section besides its current one
When the user picks a different existing section for that agent
Then the agent's section assignment updates to the newly picked section
```
<!-- AC-ID: REQ-SB-18-US-01-AC-06 -->

### Scenario 6: An agent's Section is independent of its Type

```gherkin
Given an agent has a given Worker/Producer/Expert Type
When the user reassigns that agent to a different Section
Then the agent's Type, and the ring position that Type drives, remain
    unchanged
  And the agent's new Section may contain agents of any Type, not only
    agents sharing its Type
```
<!-- AC-ID: REQ-SB-18-US-01-AC-07 -->

### Scenario 7: The Agents Map reflects the current section set, including a section with zero agents

```gherkin
Given a section exists with zero agents currently assigned to it
When the user views the Agents Map
Then that section's hub is rendered on the map (as an empty group), without
    requiring a code change or an application restart
```
<!-- AC-ID: REQ-SB-18-US-01-AC-08 -->

### Scenario 8: The Agents Map reflects an agent's just-changed section assignment

```gherkin
Given the user has just reassigned an agent to a different section via the
    Agent Settings surface
When the user views the Agents Map
Then the agent is rendered grouped under its newly assigned section's hub,
    not its previous section's hub, without requiring a code change or an
    application restart
```
<!-- AC-ID: REQ-SB-18-US-01-AC-09 -->

## Affected Screens

- `html-prototype/settings.html` — needs a new Sections area (create/rename/
  delete). Not present in the approved prototype; no design authority exists
  for its visual shape yet — see Notes.
- `html-prototype/agents-map.html` — the agent detail side panel's Settings
  block needs a new Section field/picker. Not present in the approved
  prototype. The canvas's hub/section layout itself needs to become
  N-section-generic instead of the approved prototype's fixed 3-section
  model — see Notes.

## Dependencies

- **Blocked by:** REQ-SB-12-US-01 (`Done`) — the Settings page shell and
  Agents Map this story extends must exist first. Satisfied.
- **Blocked by:** REQ-SB-13-US-01 (`Done`) — the Agent Settings detail panel
  this story adds a section picker to must exist first. Satisfied.
- **Related to:** `ADR-011` — the static `agent_registry.py` design this
  story's persistence mechanism must reconcile with, per the PRD breadcrumb;
  a genuine architecture-level question for `/plan-tasks`, not resolved
  here.
- **External:** none new.

## Constraints

- Section is a new, independent axis from an agent's existing Worker/
  Producer/Expert Type — Type continues to drive ring position exactly as
  REQ-SB-12-US-01 built it; this story must not collapse or merge the two
  concepts.
- Every agent belongs to exactly one section at all times. **Deleting a
  section that still has agents assigned is blocked** (operator-resolved,
  2026-08-11) — the deletion is refused with a clear message until every
  agent has been moved out of that section; no automatic/cascading
  reassignment. Same policy REQ-SB-19-US-01 uses for Provider removal, for
  consistency.
- The starting section set (Technical, Sales, Productivity, Customers,
  Products) and the starting agent→section defaults named in the PRD
  breadcrumb are seed data, not fixed/hardcoded — the user must be able to
  rename or delete any of them (subject to the deletion question flagged
  below) the same as a section they created themselves.
- The persistence mechanism for user-created/edited sections and per-agent
  section assignment (extending `.second-brain/`'s existing flat-JSON-file
  convention vs. another store) is an architecture-level decision left to
  `/plan-tasks`, not decided here, per the PRD breadcrumb's own explicit
  deferral.
- No backend endpoint currently exists for section CRUD or for updating an
  agent's section assignment — new API surface is required; its exact shape
  is left to `/plan-tasks`.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-18-US-01-T01 | backend | `agent_sections.json` load/save primitives | `src/backend/app/data_access/vault_writer.py` | `../Tasks/REQ-SB-18-US-01-T01-sections-vault-writer-primitives.md` |
| REQ-SB-18-US-01-T02 | backend | `section_registry.py` — seed/self-heal/CRUD/block-delete | `src/backend/app/business/section_registry.py` | `../Tasks/REQ-SB-18-US-01-T02-section-registry.md` |
| REQ-SB-18-US-01-T03 | backend | `sections_router.py` — Section CRUD API | `src/backend/app/api/sections_router.py`, `main.py` | `../Tasks/REQ-SB-18-US-01-T03-sections-router.md` |
| REQ-SB-18-US-01-T04 | backend | `PATCH /agents/{id}` (section_id) + merged section fields | `src/backend/app/api/agents_router.py` | `../Tasks/REQ-SB-18-US-01-T04-agents-router-section-assignment.md` |
| REQ-SB-18-US-01-T05 | frontend | `layoutAgents.ts`/`mockAgents.ts` N-section-generic | `src/frontend/src/features/agents-map/` | `../Tasks/REQ-SB-18-US-01-T05-layout-agents-n-generic.md` |
| REQ-SB-18-US-01-T06 | frontend | Canvas N-generic dividers + neutral hub color | `AgentsMapCanvas.tsx`, `SectionHub.tsx` | `../Tasks/REQ-SB-18-US-01-T06-canvas-n-generic-dividers-neutral-hub.md` |
| REQ-SB-18-US-01-T07 | frontend | `SectionsCard.tsx` + `settingsApiClient.ts` + Settings composition | `src/frontend/src/features/settings/`, `pages/SettingsPage.tsx` | `../Tasks/REQ-SB-18-US-01-T07-sections-card-settings.md` |
| REQ-SB-18-US-01-T08 | frontend | `AgentDetailPanel.tsx` Section picker | `features/agents-map/AgentDetailPanel.tsx`, `agentsApiClient.ts` | `../Tasks/REQ-SB-18-US-01-T08-agent-detail-panel-section-picker.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — manual mode still the live default per `Implementation/Pipeline.md`; no test-stack ADR exists yet
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Redesigning the Worker/Producer/Expert Type taxonomy or the ring layout
  it drives** — unchanged from REQ-SB-12-US-01; this story only decouples
  Section from Type, it does not touch Type itself.
- **Multi-section membership per agent** — the PRD is explicit that every
  agent belongs to exactly one section; a many-to-many model is not built
  here.
- **Automatic reassignment or cascading deletion of agents when their
  section is deleted** — explicitly rejected (operator-resolved, 2026-08-11):
  deletion of an in-use section is blocked, not auto-resolved. See
  Scenario 4b.
- **Any change to Hermes's own internal Section/Department concept**
  (`MEMORY.md`'s Hermes-taxonomy constraint) — Second Brain's Section
  concept here is its own UI/data concept, not a sync with Hermes's.
- **A full visual redesign of the Agents Map's polar-grid aesthetic** — the
  computed-layout *mechanism* (`layoutAgents.ts`) must become N-section-
  generic, but the goal is to extend the existing approved visual language
  (rings, hubs, spokes, radar background), not invent a new map metaphor.

## Notes

**Prototype parity (settings.html, agents-map.html):**

- `settings.html`'s existing Vault card and Connections card — **N/A**, not
  touched by this story.
- `settings.html`'s new Sections area (create/rename/delete) — **not
  covered by the approved prototype.** No design authority exists for its
  visual shape (list layout, create/rename/delete controls, empty state).
- `agents-map.html`'s side panel — Available Actions/Chat/Communication
  History blocks — **N/A**, not touched by this story.
- `agents-map.html`'s side panel Settings block (`kv-list`) — needs a new
  Section field/picker row — **not covered by the approved prototype.**
- `agents-map.html`'s canvas hub/section layout — currently a fixed,
  hand-placed 3-hub model (`SECTION_META` in `layoutAgents.ts`, mirroring
  the prototype's 3 hardcoded `.hub-node`/`.section-title` positions) — an
  arbitrary-N, includes-zero-agent-sections layout is **not covered by the
  approved prototype** and needs new visual design (how do 5+ hubs, some
  empty, lay out around the same Knowledge Base without collision — the
  same kind of geometry problem `agents-map.html`'s own revision history
  already solved once for 3 fixed hubs, now needing a generic solution).

**Resolved 2026-08-11, operator-confirmed:**

- **Section-deletion-while-in-use policy:** block the deletion until the
  section is empty — no automatic/cascading reassignment. See Scenario 4b,
  Constraints, and Non-Goals. Same policy REQ-SB-19-US-01 uses for
  Provider removal, per the operator's explicit choice for consistency.

**Design — approved 2026-08-11 (operator):** `/design` ran against REQ-SB-18
and REQ-SB-19 together. The operator reviewed the designer's high-level
output and approved before the pass's final artefact notification landed,
explicitly accepting that risk to keep moving — `/plan-tasks` should still
sanity-check the final `html-prototype/` pages this designer pass produces
against this story's locked scenarios once available, and flag back only if
something concrete doesn't match (not re-litigate the approval itself).

gate: clear 2026-08-11 — both original triggers resolved: the
section-deletion policy by direct operator decision, and the net-new-design
trigger by operator approval of the design pass. REQ-SB-18 itself is
finalised in the PRD (no `<!-- Draft -->` marker); no contradictory inputs;
no `ESCALATIONS.md` entry needed; not oversized — kept as one story per the
"no independent value alone" test (section CRUD with no way to assign
agents to the new sections has no real value, and per-agent reassignment
among a fixed set has little value either — they belong together).

**Architecture pass (2026-08-11, `/plan-tasks` step 1 — architect):**
`ADR-014` written (new, appended to `Implementation/Architecture/ADR.md`) —
resolves this story's own explicitly-deferred architectural questions:
Sections become a new, persisted, user-mutable concern (`.second-brain/
agent_sections.json`, seeded with the starting 5-section set on first
read; a new `app/business/section_registry.py` owns CRUD, per-agent
assignment, and the block-until-empty deletion check), composed
*alongside* — not inside — the still-fully-`Accepted`, still-unmodified
`app/business/agent_registry.py` (`ADR-011` point 2's "agent identity/
type/actions stay hardcoded" reasoning is untouched). New
`app/api/sections_router.py` (`GET/POST/PATCH/DELETE /sections`) and a new
`PATCH /agents/{agent_id}` verb on the existing `agents_router.py` for
per-agent reassignment; a blocked deletion returns `HTTP 409` with a
name-resolved message. `src/frontend/src/features/agents-map/
layoutAgents.ts` becomes genuinely N-section-generic (hub angles evenly
spaced around the full circle, computed from the real `GET /sections`
list, replacing the fixed 3-entry `SECTION_META`/`TYPE_TO_SECTION` lookup)
and `AgentsMapCanvas.tsx`'s section-boundary divider lines generalize from
3 fixed positions to N midpoint-computed ones; Section Hubs move to a
neutral color (no longer 1:1 with a Type, per the approved "5 sections"
prototype reference state). Full reasoning, every alternative considered,
and every consequence: `ADR-014` in `Implementation/Architecture/ADR.md`.
This ADR also resolves `REQ-SB-19-US-01`'s parallel Provider-CRUD
questions in the same pass (both stories were designed together and share
the identical underlying mechanism — see `ADR-014`'s own Context).

**Architecture scope (bounds the decomposer's task breakdown and the
coder's file access for this story):**
- Backend: `src/backend/app/data_access/vault_writer.py` (new
  `load_sections_state`/`save_sections_state` primitives only — no other
  primitive in this file is in scope); `src/backend/app/business/
  section_registry.py` (new); `src/backend/app/api/sections_router.py`
  (new); `src/backend/app/api/agents_router.py` (add `PATCH
  /agents/{agent_id}` and the merged `section_id`/`section_name` fields on
  `GET /agents`/`GET /agents/{agent_id}` — **not** the Provider-side
  fields/checks, which are `REQ-SB-19-US-01`'s scope even though both land
  in the same file this pass); `src/backend/app/main.py` (register
  `sections_router`). `agent_registry.py` and `agent_chat.py` are
  explicitly **out of scope** — this story must not modify either.
- Frontend: `src/frontend/src/features/agents-map/layoutAgents.ts`,
  `mockAgents.ts` (drop `AgentSection.type`, `SectionId` becomes `string`),
  `AgentsMapCanvas.tsx` (N-generic section-boundary lines), `SectionHub.tsx`
  (neutral color), `AgentDetailPanel.tsx` (new Section `<select>` kv-row
  only — the Provider kv-row is `REQ-SB-19-US-01`'s scope), `agentsApiClient.
  ts` (the `section_id` portion of the new `updateAgentAssignment` call —
  shared with `REQ-SB-19-US-01`, which adds the `provider_id` portion);
  new `src/frontend/src/features/settings/SectionsCard.tsx`,
  `settingsApiClient.ts` (the `/sections` calls only — `REQ-SB-19-US-01`
  adds the `/providers` calls to the same shared client file);
  `src/frontend/src/pages/SettingsPage.tsx` (compose `<SectionsCard>`).
- Architecture doc sections the coder is bounded by: `architecture.md` →
  "Source Layout" (the new `section_registry.py`/`sections_router.py`
  bullet), "Frontend Application Architecture" → "Source structure" (the
  updated `features/agents-map/` and new `features/settings/` tree), "My
  Day & Agent Panel APIs" → "Agent Sections & LLM Providers — mutable,
  persisted agent configuration" (full mechanism), and `ADR-014` in full.

Per the architect's own MUST-FLAG trigger 3 (creating/changing an ADR):
`gate: flagged`, `gate_reason: trigger-3 (ADR-014 created)`. The decomposer
still runs in this same `/plan-tasks` pass — see
`Implementation/Pipeline.md`'s "Do NOT halt the stage" rule — so the human
reviews `ADR-014` and the resulting tasks together in one pass. A
`REVIEW-QUEUE.md` pointer has been added.

**Build pass (2026-08-11, `/implement-sprint` — coder):** All 8 tasks
(`T01`–`T08`) built and verified live, in dependency order, against the
real backend (`.second-brain/agent_sections.json`, real
`uvicorn app.main:app --port 8001`) and real frontend
(`npm run dev`, headless-Chrome-via-CDP browser verification — this
project's established zero-dependency frontend verification pattern, no
test-stack ADR exists yet). All 9 locked ACs (`AC-01`…`AC-09`) confirmed
passing live — see each task's own `## Implementation Log` for the exact
verification steps and observed outcomes. `npx tsc --noEmit` and
`npm run build` both clean after every task. Two scope-internal judgement
calls were made and logged for human spot-check (not escalations): `T06`
fixed one additional `section.type`-referencing spot in
`AgentsMapCanvas.tsx` the task's own diff didn't name (the section-title
accent color), using the same neutral-color pattern `ADR-014` point 6
already establishes for the two spots it does name; `T07` used
`html-prototype/styles.css`'s own real `.item-row`/`.btn-danger` CSS
values (background+border-radius, 10%/20% color-mix) rather than the
task's slightly different inline snippet, per that task's own "match it
exactly rather than approximating" instruction. Neither required an
`ESCALATIONS.md` entry — no new dependency, no ADR deviation, no
out-of-scope file. `ADR-014`'s own human review (this story's sole
still-open item, per the `REVIEW-QUEUE.md` pointer below) is unaffected by
this build pass — the coder does not clear that flag; `gate` stays
`flagged` for that reason alone. Story advances `Ready → Done`.

**Decomposition pass (2026-08-11, `/plan-tasks` step 2 — decomposer):**
All 9 scenarios locked as `REQ-SB-18-US-01-AC-01`…`AC-09` (sequential,
including `4b` as `AC-05`), each with a trailing `<!-- AC-ID: ... -->` tag
— no AC left non-locked, no material assumption needed to lock any of
them. 8 tasks created (`T01`–`T04` backend, `T05`–`T08` frontend) —
see `## Implementation Tasks` above for the full table.
`depends_on` is acyclic: `T01 → T02 → {T03, T04} → T05 → T06 → {T07,
T08}`, `T07` also depends on `T03`/`T05`, `T08` depends on `T04`/`T06`/
`T07`. Every locked AC has at least one AC-tagged verification step in a
task's `## Tests` (`AC-01`/`AC-03`/`AC-04`/`AC-05` in `T07`; `AC-02`
split across `T07`'s "appears in Settings" build and `T08`'s completing
"available as a picker choice" check, both tagged; `AC-06`/`AC-07`/`AC-09`
in `T08`; `AC-08` in `T06`) — no locked AC without a tagged step.
**Shared-surface handling:** this story and `REQ-SB-19-US-01` both touch
`app/api/agents_router.py`'s `PATCH /agents/{agent_id}` and
`AgentDetailPanel.tsx`/`agentsApiClient.ts`/`settingsApiClient.ts`/
`SettingsPage.tsx`. Rather than both stories building independent,
possibly-conflicting endpoints/components, this story's `T04` (backend)
and `T07`/`T08` (frontend) land the shared surface first (Section
portion), and `REQ-SB-19-US-01`'s `T04`/`T05`/`T06` each carry an explicit
cross-story `depends_on` edge naming this story's task ids, so the build
loop applies the Provider portion strictly after, as a literal diff on
top of already-landed code — never two tasks racing to edit the same file
in parallel. Story advances `Draft → Ready`; all 8 tasks written directly
at `status: Ready` (lockstep, per the decomposer's own mandate). `gate`
stays `flagged` — `ADR-014`'s own trigger-3 flag is not cleared by this
pass; the human still reviews `ADR-014` and this task breakdown together.
