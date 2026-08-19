---
id: REQ-SB-51-US-01
title: Background Agents — explicit opt-in flag, excluded from Hub-routing and Cockpit addressing, displayed in a separate Agents Map area
requirement_ids: [REQ-SB-51]
requirement_section: "REQ-SB-51: Background Agents — Excluded from Inter-Agent Addressing, Displayed Separately"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-044"
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-51-US-01 — Background Agents — explicit opt-in flag, excluded from Hub-routing and Cockpit addressing, displayed in a separate Agents Map area

## Story

**As a** Second Brain user
**I want** to mark an agent as a Background Agent — one that runs its own
work but is never a valid target for another agent's Hub-routed request or
a Cockpit bring-in/`@mention` — and see it displayed in a distinct area of
the Agents Map
**So that** agents like Email Capture that only ever run their own
schedule stay out of every other agent's "who can I ask for help"
candidate list, while I can still open and use them myself exactly like
any other agent

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-51: Background Agents — Excluded
  from Inter-Agent Addressing, Displayed Separately*. Operator-directed,
  verbatim: "I need to have some Agents as Background Agents, They don't
  talk to others for example Email Capture is An Agent but not to be
  called by others I guess They should be Hidden Displayed in a Different
  Place." The PRD breadcrumb names 5 genuinely open sub-questions,
  explicitly "left to `/spec`" — resolved below, each grounded in the
  real, already-shipped code, not guessed.

- **(1) Explicit flag, not inferred Type.** A new per-agent boolean,
  `is_background_agent`, defaulting `False`. Read directly against the
  real agent shape (`agent_registry.py`'s `_SEED_AGENTS`/`create_agent`):
  every agent already carries a free-text `settings` kv-list (`Purpose`,
  `Domain`, `Schedule`, …) used for **Purpose/Domain-style descriptive,
  read-only-after-creation display fields** (`AgentDetailPanel.tsx`'s
  Settings tab renders `agent.settings` as plain `<span>` text, no edit
  control anywhere). Separately, every **user-toggleable, machine-checked
  assignment** (Section, Provider, Working mode, Keywords, Vault scope)
  lives in its own small dedicated registry module
  (`section_registry.py`/`provider_registry.py`/
  `working_mode_registry.py`/`agent_keywords.py`/`scope_registry.py`),
  each with a real `PATCH /agents/{agent_id}` field and a real edit
  control (`<select>`/`<input>`) in `AgentDetailPanel.tsx`'s Settings tab.
  Since this requirement's flag must be **user-settable via Settings**
  (sub-question 5's own "the operator's concern is about other agents,
  not the user" framing implies a live, user-facing toggle, not a
  creation-time-only value), it behaviourally belongs with the second
  family (Working Mode's own exact precedent: a small enum/boolean
  assignment, defaulting per-agent, edited live via a Settings control,
  read fresh — never cached — by every consuming check) rather than the
  first (a static, read-only-after-creation descriptive string). **The
  exact storage shape (a new dedicated registry mirroring
  `working_mode_registry.py`, vs. reusing the `settings` kv-list) is an
  architecture decision for `/plan-tasks`, not decided here** — this
  story specs the observable behaviour only: a boolean, gettable and
  settable per agent, defaulting `False`, editable via the agent's own
  Settings tab, and read live (no caching lag) by every exclusion check
  below.

- **(2) Retrofit the 3 real capture-pipeline Workers.** `email-capture`,
  `meeting-capture`, `todo-capture` (`agent_registry.py`'s
  `_SEED_AGENTS`, all `type: "worker"`) are backfilled to
  `is_background_agent: True`, mirroring this project's own established
  retrofit pattern (`REQ-SB-39`'s Skills migration, `REQ-SB-41`'s Purpose
  backfill — both backfilled all already-shipped agents to a new field
  without breaking any locked AC). **Confirmed this does not silently
  change any currently-`Done` AC:** `agent_keywords.py`'s
  `list_candidate_agents_for_keyword_match` (the real Hub-routing
  candidate function, `REQ-SB-20-US-01`, Done) requires an agent's own
  keyword list to be **non-empty** to ever be a candidate
  (`vault_writer.load_agent_keywords` defaults every agent to `[]`, and
  no seed data, fixture, or `Done` story assigns keywords to
  `email-capture`/`meeting-capture`/`todo-capture` — confirmed by direct
  grep of `src/backend`, no match). These 3 agents are therefore
  structurally never a live Hub-routing candidate today (empty keywords),
  so excluding them explicitly changes zero currently-observable
  behaviour for any locked, `Done` AC — it only forecloses a
  configuration the user could technically set today (assigning them
  keywords) but never has.

- **(3) Display treatment — a distinct "Background Agents" area on the
  Agents Map, outside the Section/ring layout.** Grounded against the
  real layout code: `layoutAgents.ts` currently places every fetched
  agent (`AgentSummary[]` from `GET /agents`) onto the Section/ring wheel
  via `agentsBySection`; a Background Agent must be excluded from that
  input set entirely (never occupies a ring slot, never counts toward
  `VISIBLE_SLOT_CAP` crowding/clustering, `REQ-SB-38-US-01`) and rendered
  instead in a separate list/rail. **No prototype screen anywhere
  currently depicts this rail** (confirmed by inspection of
  `agents-map.html`) — resolved as **not requiring a fresh `/design`
  pass**, per this session's own established precedent
  (`REQ-SB-49-US-01`'s `@mention` suggestion dropdown): this is a static
  list of agent name+type rows, strictly simpler than that precedent's
  live-narrowing autocomplete, and `agents-map.html` already has an
  approved `.card`/`.item-list` vocabulary directly below the map canvas
  (e.g. the demo-state legend card at line ~1232) that a Background
  Agents list can reuse without inventing new visual chrome. Exact
  placement/styling is left to the coder, matching this session's own
  "small, standard, vocabulary-reusing addition to an already-approved
  screen doesn't need a fresh `/design` pass" convention.

- **(4) Scope of "not to be called by others" — resolved broadly, per the
  PRD's own reading.** Excluded from:
  - **Hub-routing candidacy** (`REQ-SB-20`, `agent_keywords.py`'s
    `list_candidate_agents_for_keyword_match` — Done, real, live-checkable).
  - **Cockpit bring-in list** (`REQ-SB-43`/`44`, both Done — the left
    panel's real "Available Agents" list, `Cockpit.tsx`'s
    `fetchAgentList()` call, the same `GET /agents` source
    `AgentsMapCanvas`/the wizard also read).
  - **Cockpit inline `@mention`** (`REQ-SB-49-US-01`, Draft, **not yet
    built** — its own spec states its suggestion source is "the same
    Available Agents list the left panel already renders"
    (`fetchAgentList()`). Since this story's exclusion is enforced at
    that shared source (see Constraints), `REQ-SB-49-US-01` inherits the
    exclusion automatically once built — **not** re-specced here as a
    separate scenario against not-yet-existing code, matching Pipeline.md's
    own "don't spec against unbuilt mechanisms" posture; recorded as a
    Constraint on that future story instead.)
  - **The Wizard's own "Agent" trigger option** (`REQ-SB-46`, Draft, gate:
    flagged, **not yet built** — its own Step 4 "Trigger: Agent" choice is
    purely informational metadata today by that story's own Notes, with
    no exclusion mechanism of any kind to extend). Deferred — see
    Non-Goals; not a hard dependency in either direction (`REQ-SB-46` may
    land before or after this story with no rework either way, since
    Trigger metadata and `is_background_agent` are two independent
    fields).
- **(5) User can still reach it directly — yes.** A Background Agent's
  own detail panel (`AgentDetailPanel.tsx`, Overview/Chat/History/Settings
  tabs), direct chat (`sendChatMessage`), and direct actions remain fully
  functional and unrestricted — only OTHER agents' and the Cockpit's own
  addressing paths exclude it, never the user's own direct panel.

- **Real dependency/build-order note:** this story does **not** depend on
  `REQ-SB-49-US-01` or `REQ-SB-46` landing first. The exclusion is built
  and verified entirely against already-`Done` surfaces
  (`REQ-SB-20-US-01`'s Hub-routing, `REQ-SB-43-US-01`/`REQ-SB-44-US-01`'s
  Cockpit bring-in list) — both unbuilt stories compose with this one
  automatically once they ship, because both are specced to reuse the
  same `GET /agents`-sourced candidate list this story filters at the
  root.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Marking an agent as a Background Agent via Settings

```gherkin
Given the user opens any agent's detail panel and switches to the Settings tab
When the user toggles that agent's "Background Agent" setting on and it is saved
Then the agent's is_background_agent value is True
  And reopening the agent's Settings tab afterward shows the toggle still on
```
<!-- AC-ID: REQ-SB-51-US-01-AC-01 -->

### Scenario 2: The 3 real capture-pipeline Workers are backfilled to Background, with their direct-use behaviour unchanged

```gherkin
Given the system has been upgraded to include the is_background_agent field
When the user views "Email Capture", "Meeting Capture", or "To-Do Capture" in Settings
Then each one's "Background Agent" setting is already on, with no manual step required
  And the user can still trigger "Run capture now", "View last run", and "Pause schedule"
    on each of them exactly as before this change
  And each one's own scheduled/app-start capture run is unaffected
```
<!-- AC-ID: REQ-SB-51-US-01-AC-02 -->

### Scenario 3: A Background Agent is never a Hub-routing candidate, even with matching keywords configured

```gherkin
Given "email-capture" is marked as a Background Agent
  And "email-capture" has been assigned the keyword "invoice", in a different
    Section from the requesting agent
When another agent in a different Section requests cross-Section help with a
    need description containing "invoice"
Then "email-capture" is never returned as a Hub-routing candidate for that request
  And the request either matches a different, non-Background candidate agent with
    a matching keyword, or reports no match, exactly as if "email-capture" did
    not have that keyword assigned at all
```
<!-- AC-ID: REQ-SB-51-US-01-AC-03 -->

### Scenario 4: A non-Background agent with matching keywords remains a valid Hub-routing candidate (regression guard)

```gherkin
Given "vault-qa" is not marked as a Background Agent
  And "vault-qa" has been assigned a keyword matching another agent's cross-Section
    help request
When that other agent requests cross-Section help with a matching need description
Then "vault-qa" is still returned as a Hub-routing candidate exactly as it is today
```
<!-- AC-ID: REQ-SB-51-US-01-AC-04 -->

### Scenario 5: A Background Agent is excluded from the Cockpit's "Available Agents" bring-in list

```gherkin
Given a Meeting or Inbox Cockpit is open with its left panel showing "Available Agents"
  And "meeting-capture" is marked as a Background Agent
When the user views the Available Agents list
Then "meeting-capture" does not appear anywhere in that list
  And there is no way to bring "meeting-capture" into the Cockpit's shared thread
    from this panel
```
<!-- AC-ID: REQ-SB-51-US-01-AC-05 -->

### Scenario 6: A non-Background agent remains available in the Cockpit bring-in list (regression guard)

```gherkin
Given a Meeting or Inbox Cockpit is open with its left panel showing "Available Agents"
  And "vault-qa" is not marked as a Background Agent
When the user views the Available Agents list
Then "vault-qa" appears in the list exactly as it does today
  And the user can bring "vault-qa" into the shared thread via the existing
    "+ Bring in" action
```
<!-- AC-ID: REQ-SB-51-US-01-AC-06 -->

### Scenario 7: A Background Agent is displayed in a distinct Agents Map area, never on the main Section/ring layout

```gherkin
Given "todo-capture" is marked as a Background Agent
When the user views the Agents Map
Then "todo-capture" does not occupy a position on any Section's ring, and is never
    folded into a density cluster marker
  And "todo-capture" instead appears in a separate, clearly labeled "Background
    Agents" area of the same screen
  And clicking "todo-capture" in that separate area opens its normal agent detail
    panel, identical to clicking any agent on the main map
```
<!-- AC-ID: REQ-SB-51-US-01-AC-07 -->

### Scenario 8: A Background Agent remains fully reachable and usable directly by the user

```gherkin
Given "email-capture" is marked as a Background Agent
When the user opens its detail panel
Then the Overview, Chat, History, and Settings tabs are all present and functional,
    exactly as for any non-Background agent
  And the user can send it a direct chat message and receive a real reply
  And the user can trigger any of its available actions directly
```
<!-- AC-ID: REQ-SB-51-US-01-AC-08 -->

### Scenario 9: Un-marking a Background Agent restores full addressability everywhere, live

```gherkin
Given "email-capture" is currently marked as a Background Agent
When the user turns its "Background Agent" setting off in Settings
Then "email-capture" is now eligible to appear as a Hub-routing candidate (subject to
    having a matching keyword, exactly like any other agent)
  And "email-capture" now appears in the Cockpit's Available Agents list
  And "email-capture" now appears on the Agents Map's main Section/ring layout
    instead of the separate Background Agents area
  And no restart, redeploy, or cache-clear is required for any of the above to
    take effect
```
<!-- AC-ID: REQ-SB-51-US-01-AC-09 -->

## Affected Screens

- `html-prototype/agents-map.html` — gains a new "Background Agents" list
  area, separate from the Section/ring canvas, reusing the existing
  `.card`/`.item-list` visual vocabulary already present on this same
  screen (Scenario 7).
- `html-prototype/meeting-cockpit.html` / `html-prototype/inbox-cockpit.html`
  — the left panel's existing "Available Agents" list filters out any
  Background Agent (Scenarios 5-6); no new visual element, an existing
  list simply renders fewer rows.
- `html-prototype/settings.html` (via the real `AgentDetailPanel.tsx`
  Settings tab, not a separate settings screen) — gains one new toggle
  row, "Background Agent", alongside the existing Section/Provider/Working
  mode/Keywords/Vault scope rows (Scenario 1).

## Dependencies

- **Not blocked by, explicitly:** `REQ-SB-49-US-01` (Cockpit inline
  `@agent_id` mention, Draft, gate: clear, not yet built) — its own spec
  reuses the same `fetchAgentList()`/Available Agents source this story
  filters, so it inherits this story's exclusion automatically once built;
  no rework required in either build order.
- **Not blocked by, explicitly:** `REQ-SB-46` (Agent Creation Wizard
  Redesign, Draft, gate: flagged, not yet built) — its own Step 4 Trigger
  metadata is an independent field with no exclusion mechanism to extend;
  see Non-Goals.
- **Composes with (already Done):** `REQ-SB-20-US-01` (Hub-routing),
  `REQ-SB-43-US-01`/`REQ-SB-44-US-01` (Cockpit bring-in), `REQ-SB-38-US-01`
  (Agents Map density clustering — a Background Agent is excluded before
  clustering logic ever sees it).
- **External:** none new.

## Constraints

- `is_background_agent` defaults `False` for every existing and newly
  created agent unless explicitly backfilled (the 3 named Workers) or
  toggled on by the user.
- Every exclusion check (Hub-routing candidacy, Cockpit bring-in list, Map
  Section/ring layout) reads the flag live, from the same real source
  `GET /agents` already serves — no caching lag, no separate/stale copy of
  the flag anywhere.
- The Cockpit bring-in list and the not-yet-built `REQ-SB-49-US-01`
  `@mention` suggestion list must filter from the **same** underlying
  Available-Agents source this story filters — never a second,
  independently-filtered candidate list.
- A Background Agent's own detail panel, direct chat, direct actions, and
  scheduled/app-start runs are never restricted by this flag — the
  exclusion applies only to other agents' and the Cockpit's own addressing
  paths.
- No change to `email-capture`'s, `meeting-capture`'s, or `todo-capture`'s
  own existing actions, schedule, or capture-pipeline behaviour — this
  story only adds the flag and the exclusion checks that read it.

## Implementation Tasks

<!-- Decomposer's job at /plan-tasks — left empty here per template. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| T01 | backend | Background Agent registry module + JSON persistence (self-healing default, 3-agent backfill) | `app/business/background_agent_registry.py` (new), `app/data_access/vault_writer.py` | `REQ-SB-51-US-01-T01-background-agent-registry.md` |
| T02 | backend | `GET`/`PATCH /agents` — merge `is_background_agent` field | `app/api/agents_router.py` | `REQ-SB-51-US-01-T02-agents-endpoint-extension.md` |
| T03 | backend | `agent_keywords.py` — skip Background Agents in Hub-routing candidacy | `app/business/agent_keywords.py` | `REQ-SB-51-US-01-T03-hub-routing-exclusion.md` |
| T04 | frontend | Shared `isBackgroundAgent` predicate — Cockpit filter + `layoutAgents` partition | `agentsApiClient.ts`, `Cockpit.tsx`, `layoutAgents.ts` | `REQ-SB-51-US-01-T04-shared-predicate-and-consumers.md` |
| T05 | frontend | Agents Map — new "Background Agents" rail | `AgentsMapPage.tsx`, `AgentsMapCanvas.tsx` | `REQ-SB-51-US-01-T05-background-agents-rail.md` |
| T06 | frontend | Settings tab — "Background Agent" checkbox control | `AgentDetailPanel.tsx` | `REQ-SB-51-US-01-T06-settings-tab-toggle.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Setting `is_background_agent` from the Agent Creation Wizard** —
  deferred. Today's shipped wizard (`CreateAgentWizard.tsx`, `REQ-SB-37`,
  Done) is about to be superseded by `REQ-SB-46`'s own popup-modal
  redesign (Draft, gate: flagged, not yet built); adding a wizard-time
  toggle now would be rebuilt/relocated the moment `REQ-SB-46` ships.
  Setting the flag is fully available post-creation via Settings
  (Scenario 1) regardless of wizard state. A future story may add this to
  whichever wizard shape is current once `REQ-SB-46` lands.
- **The Wizard's own Step 4 "Agent" Trigger option** (`REQ-SB-46`) —
  unrelated, independent metadata field; not extended or gated by this
  story.
- **`REQ-SB-49-US-01`'s own inline `@mention` suggestion UI** — not built
  here; this story only guarantees the shared source it will read from is
  already filtered (see Constraints).
- **Within-Section Hub-routing, or any routing mechanism other than the
  real, shipped cross-Section keyword match** — unaffected/out of scope,
  matching `REQ-SB-20-US-01`'s own existing scope boundary.

## Notes

**Prototype parity (agents-map.html / meeting-cockpit.html / inbox-cockpit.html):**

- Agents Map Section/ring canvas — **Specced.** A Background Agent is
  excluded from this layout entirely (Scenario 7); everything else about
  the canvas (existing Sections, rings, clustering, activity pulses) is
  unchanged.
- Agents Map new "Background Agents" list area — **Specced**, net-new
  region with no prior prototype coverage, resolved as **not requiring a
  fresh `/design` pass** (see Context point 3's full reasoning) — reuses
  the screen's own existing `.card`/`.item-list` vocabulary; exact
  placement/styling left to the coder.
- Cockpit "Available Agents" list (`meeting-cockpit.html`/
  `inbox-cockpit.html`) — **Specced.** No new visual element; an existing,
  already-approved list simply renders fewer rows for a Background Agent
  (Scenarios 5-6).
- Agent detail panel's Settings tab — **Specced.** One new toggle row,
  "Background Agent," added alongside the existing Section/Provider/
  Working mode/Keywords/Vault scope rows, following the same `.kv-row`
  convention (Scenario 1). Exact control (checkbox/switch) left to the
  coder; the existing tab already mixes `<select>` and `<input>` controls
  in this exact row list.
- Everything else on every named screen (Overview/Chat/History tabs,
  research panel, message list, attendee/people chips) — **unchanged, out
  of scope** for this story.

**Why `gate: clear`:** No MUST-FLAG trigger fired. (1) The 5 sub-questions
the PRD breadcrumb itself names as "genuinely open, left to `/spec`" are
resolved above by direct inspection of the real, already-shipped code
(`agent_registry.py`, `agent_keywords.py`, `Cockpit.tsx`,
`AgentDetailPanel.tsx`, `layoutAgents.ts`), not by guessing into a PRD
gap — matching this session's own established `REQ-SB-49-US-01` precedent
for "explicitly delegated, code-grounded resolution is not a
gap-filling assumption." (2) `REQ-SB-51` carries no `<!-- Draft -->`
marker — finalised PRD text. (3) N/A (architect trigger) — the one open
architecture question (exact storage shape for the new flag) is named
explicitly for `/plan-tasks`, not decided here, and does not itself
require a flag from this role. (4) No `ESCALATIONS.md` entry written. (5)
Not oversized — one flag, one backend filter reused at two real call
sites, one new Map list region reusing existing visual vocabulary,
verified end-to-end against already-`Done` surfaces only. (6) N/A (coder
trigger). (7) No contradictory PRD inputs. (8) No genuinely unclear or
multiply-valid scoping question remains — every open question had a
single code-grounded best answer, named and justified above.

gate: clear 2026-08-14 — no triggers fired (no ADRs touched, all 5 PRD-
delegated open questions resolved via direct code inspection rather than
guessed, requirement finalised, exclusion built and verified entirely
against already-Done surfaces — REQ-SB-20-US-01, REQ-SB-43-US-01,
REQ-SB-44-US-01 — with no hard dependency on REQ-SB-46 or REQ-SB-49-US-01).

**Architect pass (2026-08-14):**

Architecture scope: §Background Agents — explicit opt-in exclusion from
Hub-routing and Cockpit addressing (REQ-SB-51-US-01, applies ADR-014/
ADR-018, no new ADR) — `Implementation/Architecture/architecture.md`.

Storage-shape decision (the one open question left for `/plan-tasks`):
a new dedicated registry, `app/business/background_agent_registry.py`,
mirroring `working_mode_registry.py`'s exact shape (self-healing default
folded into `_load_state()`, no separate catalog), backed by a new
sibling `.second-brain/agent_background_flags.json`. The only deviation
from `working_mode_registry.py`'s uniform-default pattern: a small
literal exception set (`email-capture`, `meeting-capture`,
`todo-capture`) self-heals to `True`; every other agent self-heals to
`False`. `GET /agents`/`GET /agents/{agent_id}` merge in
`is_background_agent` the way `working_mode` already is; `PATCH
/agents/{agent_id}` gains a matching optional field; `AgentDetailPanel.tsx`'s
Settings tab gains one new checkbox `.kv-row`, mirroring the Working-mode
row's handler shape.

Shared exclusion-filter design: backend, one call site —
`agent_keywords.list_candidate_agents_for_keyword_match` gains one skip
(`background_agent_registry.get_is_background_agent(agent_id)`) inside
its existing per-agent loop; `graph.py`'s `_route_hub_request` calls this
function exclusively and needs no change of its own. Frontend, one shared
predicate, two call sites — a new `isBackgroundAgent(agent)` exported
from `agentsApiClient.ts`, consumed by `Cockpit.tsx` (filters
`availableAgents` before rendering) and `layoutAgents.ts` (partitions
input into `addressableAgents`/`backgroundAgents`, the latter returned as
a new `AgentMapLayout.backgroundAgents` field, never fed into
`agentsBySection`/ring placement/density clustering). Confirmed by direct
inspection that `app/business/cockpit/threads.py` has no agent-listing
code of its own (`bring_in_agent` only accepts an already-chosen
`agent_id`) — the Cockpit's "Available Agents" list is sourced from the
same frontend `fetchAgentList()`/`GET /agents` call the Agents Map also
reads, so the exclusion is enforced once, frontend-side, at that shared
source. `AgentsMapCanvas.tsx` (or a sibling in `AgentsMapPage.tsx`, coder
latitude) gains a new "Background Agents" rail consuming
`AgentMapLayout.backgroundAgents`, reusing the existing `.card`/
`.item-list` vocabulary; clicking a row opens the same `AgentDetailPanel`
via the existing `onSelectAgent` callback.

Why no new ADR: this is an ordinary CRUD-pattern extension of `ADR-014`'s/
`ADR-018`'s already-`Accepted` "new persisted concern composed alongside
`agent_registry.py`, self-healing default, `PATCH`-endpoint-plus-edit-
control" shape, one boolean concept over — directly mirroring the already-
settled "Skills Repository ... applies ADR-014, no new ADR" precedent
(itself a more novel extension than a plain boolean). No `Accepted` ADR,
PRD text, or `MEMORY.md` constraint is contradicted; no new tool,
framework, or structural boundary introduced. Full detail:
`Implementation/Architecture/architecture.md` → "Background Agents —
explicit opt-in exclusion from Hub-routing and Cockpit addressing."

gate: clear 2026-08-14 (architect) — no ADR created or changed, no
assumptions beyond the analyst's own already-resolved open questions, no
contradiction of any Accepted ADR/PRD text/MEMORY.md constraint.

**Decomposer pass (2026-08-14):**

All 9 Gherkin scenarios locked as `REQ-SB-51-US-01-AC-01` through `AC-09`
(no wording changes needed — the analyst's untagged Gherkin was already
buildable as written; AC-IDs appended verbatim on the line after each
scenario's closing fence). Decomposed into 6 flat-root tasks, `T01`-`T06`,
read against the REAL current shape of every file the architect's Notes
named (`working_mode_registry.py`, `agent_keywords.py`, `agentsApiClient.ts`,
`layoutAgents.ts`, `AgentsMapCanvas.tsx`, `AgentsMapPage.tsx`, `Cockpit.tsx`,
`AgentDetailPanel.tsx`, `agents_router.py`, `vault_writer.py`) before
writing any task's own code sample — no drift found against the
architect's design.

Dependency chain: `T01` (registry + persistence, no deps) → `T02`
(`GET`/`PATCH /agents`, backend) and `T03` (Hub-routing skip, backend) both
depend only on `T01` and are mutually independent → `T04` (shared
`isBackgroundAgent` predicate + Cockpit filter + `layoutAgents` partition,
frontend) depends on `T02` → `T05` (Background Agents rail) depends on
`T04` → `T06` (Settings-tab checkbox) depends on `T02`, `T03`, `T04`, `T05`
— the widest fan-in, deliberately, so its own `AC-09` verification step
(un-marking restores Hub-routing/Cockpit/Map addressability live, no
restart) can exercise every other task's real, already-built code in one
end-to-end pass rather than only its own diff. Acyclic, confirmed by
construction.

AC → task coverage (every locked AC has at least one tagged manual step):
`AC-01`→`T02`(partial, HTTP round trip)+`T06`(full, UI persistence);
`AC-02`→`T01`; `AC-03`,`AC-04`→`T03`; `AC-05`,`AC-06`→`T04`; `AC-07`→`T05`;
`AC-08`,`AC-09`→`T06`. All 6 new task files created at `status: Ready` in
lockstep with this story's own `Draft → Ready` transition below.

Story advanced `Draft → Ready`: every AC is locked, every locked AC has a
tagged verification step, `depends_on` is acyclic. `gate: clear` — no
MUST-FLAG trigger fired this pass: no material assumption (all 6 task
designs read directly off the architect's own already-resolved Notes and
the real current files, not guessed); no unfinalised requirement; no ADR
touched by this role; no `ESCALATIONS.md` entry; no oversized task (each
is a single-file-or-tight-pair, one working session); every locked AC has
an observable, verifiable outcome; no contradictory inputs; no genuinely
unclear or multiply-valid task-breakdown question remained — the
architect's Notes already named one concrete design per concern.

gate: clear 2026-08-14 (decomposer) — no triggers fired (no ADR touched,
no material assumptions beyond the architect's own already-resolved
design, all 9 ACs locked with tagged verification, depends_on acyclic).

**Coder pass (2026-08-14, SPRINT-044):**

All 6 tasks (`T01`-`T06`) built and verified live in dependency order,
all 9 locked ACs confirmed with a real, observed outcome — see each
task's own Implementation Log for full detail. `app/business/
background_agent_registry.py` (new) mirrors `working_mode_registry.py`'s
exact self-healing shape; the 3 real capture-pipeline Workers
(`email-capture`/`meeting-capture`/`todo-capture`) self-heal to
`is_background_agent: True` with zero manual migration step, every other
agent to `False`. `GET`/`PATCH /agents` merge/accept the field the same
way `working_mode` already does. `agent_keywords.
list_candidate_agents_for_keyword_match` skips any Background Agent
inside its existing loop — confirmed live that a Background Agent with a
matching keyword is never a Hub-routing candidate, a non-Background
agent's candidacy is completely unaffected, and un-marking restores
candidacy live with no restart. Frontend: one shared `isBackgroundAgent`
predicate (`agentsApiClient.ts`), consumed by `Cockpit.tsx` (filters the
Available Agents bring-in list) and `layoutAgents.ts` (partitions
Background Agents out of ring placement/clustering into a new
`backgroundAgents` field, before `agentsBySection` is built) — confirmed
live via a real CDP-driven headless-Edge session that a Background Agent
never appears in a real Meeting Cockpit's Available Agents list, while a
non-Background agent's bring-in behaviour is unchanged. `AgentsMapCanvas.
tsx` gained a new "Background Agents" `.card`/`.item-list` rail
(reusing the existing visual vocabulary, no fresh `/design` pass, per
the story's own Notes) — confirmed live that a Background Agent never
occupies a ring position or a cluster marker, and clicking its rail row
opens the identical `AgentDetailPanel`. `AgentDetailPanel.tsx`'s Settings
tab gained one new "Background Agent" checkbox row mirroring the Working
mode row's own handler shape — confirmed live it persists across a
panel close/reopen, and that a Background Agent's own Overview/Chat/
History/Settings tabs, a real direct chat message (genuine LLM reply,
not fabricated), and a real direct action-trigger request all remain
completely unrestricted by the flag. **Full end-to-end restoration
(`AC-09`) independently confirmed live, no restart:** un-marking
`email-capture` via the real Settings toggle simultaneously restored its
Hub-routing candidacy (backend-layer), its presence in a real Cockpit's
Available Agents list, and its placement on the Agents Map's main ring
instead of the Background Agents rail — all 3 checked live in one
continuous session, then reverted and independently reconfirmed back to
the original backfilled state (`GET /agents` showing all 3 capture
Workers `True`, every other agent `False`).

No `ESCALATIONS.md`/`REVIEW-QUEUE.md` entries — no out-of-scope event,
no unverifiable locked AC, no new dependency/shared-interface change/ADR
deviation encountered. One environmental action taken, not a code
change: a stray, non-`--reload` uvicorn process already listening on
port 8001 (unrelated prior session) was killed and replaced with a
single, explicitly-controlled `--reload` instance before verification
began, per this project's own established anti-stray-process precedent.

Story advanced `Ready → Done`. `gate: clear` — no MUST-FLAG trigger
fired this pass.

gate: clear 2026-08-14 (coder) — no triggers fired (all 9 locked ACs
verified live with a real, observed outcome; no ADR touched; no
out-of-scope file; no unanticipated dependency).
