---
id: REQ-SB-37-US-01
title: Agent creation — a real Create Agent flow, replacing hand-editing agent_registry.py, with existing per-agent properties configurable on the created agent
requirement_ids: [REQ-SB-37]
requirement_section: "REQ-SB-37: Agent Creation"
phase: P1
status: Draft
gate: flagged
gate_reason: "unclear-requirement (ESC-020) — custom-actions fork left genuinely open per the PRD's own breadcrumb; the persisted-agent-registry mechanism reverses ADR-011 point 2 and needs a superseding ADR at /plan-tasks; net-new-design-needed — no html-prototype/ screen has a Create Agent affordance anywhere."
sprint: ""
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-37-US-01 — Agent creation — a real Create Agent flow, replacing hand-editing agent_registry.py, with existing per-agent properties configurable on the created agent

## Story

**As a** Second Brain user
**I want** to create a new agent from within the app — giving it a name, a
type, and a Section at minimum — without editing source code
**So that** I can add a new agent (e.g. a new Expert for a subject I care
about) the same way I already create a new Section or Provider, instead of
needing a code change every time

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-37: Agent Creation* — "The user can
  create a new agent from the app itself — no place in the UI currently lets
  the user do this; every agent that exists today ... was added by editing
  `app/business/agent_registry.py`'s source code directly." **Acceptance:**
  "The user can create a new agent from within the app, without editing
  source code; the new agent is immediately visible alongside existing
  agents (e.g. on the Agents Map); its already-existing per-agent properties
  (Section, Provider, Keywords, Working mode, Skill grants, Vault Scope) can
  be configured the same way an existing agent's can, using the surfaces
  those requirements already built."

- **PRD breadcrumb (2026-08-13, operator-directed, verbatim: "Add the
  Creation of Agents As we have no place to create an agent"), cited in
  full, not re-decided here:** this is a direct reversal of `ADR-011` point
  2 ("agent identity/type/actions stay hardcoded... not a persisted/mutable
  concern"), a decision every subsequent agent-touching ADR this session
  (`ADR-014`, `ADR-017`, `ADR-018`, `ADR-020`, `ADR-021`, `ADR-023`) built on
  without reopening. `REQ-SB-36-US-02`'s own architect pass had already
  resolved "how does a new agent get created" as "a manual, code-level
  `agent_registry.py` addition" — **that resolution is now superseded by
  this requirement, not silently kept alongside it.** The breadcrumb names
  four things as genuinely open, explicitly left to `/spec`: (1) which of a
  created agent's properties become persisted/user-editable — resolved
  below, by direct reading of the PRD's own Acceptance text — vs. whether it
  can define bespoke *actions* — **not resolved, see the flag below**; (2)
  where creation lives in the UI (Agents Map, Settings, or both); (3) what a
  newly-created agent can do before any property is configured; (4) whether
  creation is itself gated by anything (e.g. a Tier-2-style approval,
  mirroring `REQ-SB-35`'s new-top-level-vault-area check, for some part of
  agent creation).

- **Resolved here, directly from the PRD's own Acceptance text (not a
  guess):** the set of properties this story makes configurable on a
  created agent is exactly the list the Acceptance text names — Section,
  Provider, Keywords, Working mode, Skill grants, Vault Scope — using "the
  surfaces those requirements already built." **Custom bespoke actions are
  not in that list.** Live code inspection confirms every existing action
  (`run_capture_now`, `rebuild_person_note`, `ask_question`,
  `pause_schedule`, `view_last_run`, `view_channel_status`, `build_knowledge`)
  is backed by real, specific Python code in `app/api/agents_router.py`'s
  `_ACTION_HANDLERS` — there is no generic "any action" mechanism anywhere
  in this codebase for a newly-created agent to plug into. This story
  resolves that a created agent starts with an **empty `actions: []` list**
  (Scenario 3) — reachable via chat/Hub-routing like any Expert with no
  actions yet (mirrors the already-`Done` `vault-filing-expert`/
  `compass-expert` pilot agents' own "start empty, gains capability over
  time" precedent from `REQ-SB-36`) — and does **not** attempt to build any
  generic/no-code custom-action mechanism. See the flag below: whether a
  user should ever be able to define a bespoke action for their own
  created agent is a real, separate architectural fork, named explicitly by
  the PRD's own breadcrumb as "not an implementation detail," and is left
  open here.

- **Resolved here, by direct code inspection (not a guess):** a created
  agent's **type** must be one of the three existing values — Worker,
  Producer, Expert — not a user-invented arbitrary string. The Agents Map's
  own polar-grid layout (`AgentsMapCanvas.tsx`'s `RING_RADIUS` lookup) is
  structurally built around exactly these three rings; a fourth type has no
  ring to render on and no design precedent anywhere in `html-prototype/`.

- **Genuinely NOT resolved here — the persisted-registry mechanism itself.**
  Every already-`Done` per-agent property registry
  (`section_registry.py`, `provider_registry.py`, `agent_keywords.py`,
  `working_mode_registry.py`, `skill_registry.py`) self-heals its own
  default assignment by iterating `agent_registry.list_agents()` — meaning
  a user-created agent would automatically pick up a default Section/
  Provider/Working mode/etc. the moment `agent_registry.list_agents()`/
  `get_agent()` themselves report it. But **every one of those five
  registries was deliberately built to compose alongside `agent_registry.py`
  without modifying it** (`ADR-014`, `ADR-017`, `ADR-018`, all explicit that
  "`agent_registry.py` itself is not modified — `ADR-011` point 2's ...
  reasoning is untouched"). This story requires the opposite: `AGENTS`
  becomes genuinely mutable, or `list_agents()`/`get_agent()` must merge the
  static built-in dict with a new persisted, user-created set — a real,
  load-bearing change to a read path five already-`Done` modules depend on,
  not a "compose alongside, don't touch" extension like every prior agent
  ADR. Whether that's a new sibling `.second-brain/agents.json` +
  `user_agent_registry.py` module (mirroring `ADR-014`'s Section/Provider
  shape, with `agent_registry.list_agents()`/`get_agent()` updated to merge
  both sources) — the pattern this project's own "reuse first" discipline
  would suggest — or a different persisted shape entirely, is an ADR-level
  call for the architect at `/plan-tasks`, not decided here. See the flag
  below.

- **A factual gap found while resolving this story, not silently carried
  forward:** the PRD's own Acceptance text calls Vault Scope one of the
  "already-existing per-agent properties," but `BACKLOG.md` shows
  `REQ-SB-29` (Agent-to-Tag/Folder Scoping — the Vault Scope requirement) is
  still `Draft`, `gate: flagged`, with **no built surface anywhere** — unlike
  Section/Provider/Keywords/Working mode/Skill grants, which are all
  genuinely `Done`. This story's own Acceptance Criteria therefore cover
  only the five properties that are actually built today; Vault Scope
  configuration is explicitly deferred (see Non-Goals), not silently
  dropped.

- **No `html-prototype/` screen has a Create Agent affordance anywhere** —
  confirmed by direct inspection of `agents-map.html` and `settings.html`
  (both have `+ Create new section` / `+ Add new Provider` `<details>`
  affordances for their own entities, but no equivalent for agents). See
  the flag below.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Creating a new agent with a name, type, and Section

```gherkin
Given the user is on a Create Agent affordance reachable from within the app
When the user enters a name, selects a type (Worker, Producer, or Expert),
    and selects a Section, then submits
Then a new agent is created with that name, type, and Section
  And no source-code change was required to create it
```

### Scenario 2: The new agent appears immediately on the Agents Map

```gherkin
Given the user has just created a new agent
When the user views the Agents Map
Then the new agent appears alongside existing agents, in its assigned
    Section and on the ring matching its type
  And no reload or restart of the app is required for it to appear
```

### Scenario 3: A newly created agent starts empty, with honest defaults

```gherkin
Given the user has just created a new agent, before configuring any of its
    properties
When the user opens that agent's own detail/settings surface
Then it shows no actions available yet
  And it shows the same default Provider and default Working mode an
    existing agent would get before being explicitly configured
  And nothing about the agent is fabricated as already configured or
    already capable of something it is not
```

### Scenario 4: Configuring the new agent's Provider

```gherkin
Given the user has created a new agent
When the user selects a Provider for it, using the same Provider picker an
    existing agent's Settings surface already uses
Then the new agent's assigned Provider is updated
  And the change is shown immediately on that agent's own Settings surface
```

### Scenario 5: Configuring the new agent's Keywords

```gherkin
Given the user has created a new agent
When the user assigns Keywords to it, using the same Keywords field an
    existing agent's Settings surface already uses
Then the new agent's assigned Keywords are updated
  And the change is shown immediately on that agent's own Settings surface
```

### Scenario 6: Configuring the new agent's Working mode

```gherkin
Given the user has created a new agent
When the user selects a Working mode (Autonomous, Supervised, or Manual)
    for it, using the same Working-mode picker an existing agent's Settings
    surface already uses
Then the new agent's Working mode is updated
  And the change is shown immediately on that agent's own Settings surface
```

### Scenario 7: Granting the new agent access to an existing Skill

```gherkin
Given the user has created a new agent
  And at least one Skill is already registered in the Skills Repository
When the user grants that Skill to the new agent, using the same
    skill-access surface an existing agent already uses
Then the new agent has access to that Skill
  And the change is shown immediately on that agent's own Settings surface
```

### Scenario 8: Creating an agent without a required field is rejected honestly

```gherkin
Given the user is on the Create Agent affordance
When the user submits without providing a name, or without selecting a type
    or a Section
Then the agent is not created
  And the user sees a clear, honest message naming what's missing
  And no partial or broken agent appears anywhere, including the Agents Map
```

### Scenario 9: A newly created agent works like any other agent afterward

```gherkin
Given the user has created a new agent and configured at least one of its
    properties
When the user opens that agent's Chat and Communication History tabs
Then both work the same way they already do for an existing, built-in agent
  And the created agent is not treated as a second-class or read-only
    agent anywhere in the app
```

## Affected Screens

- `html-prototype/agents-map.html` — needs a new "Create Agent" affordance
  (or `html-prototype/settings.html`, or both — **placement is genuinely
  open, not decided here**, see the flag below). No existing region of
  either screen covers this.
- `html-prototype/agents-map.html` — the agent detail side panel (Settings
  tab) already covers Section/Provider/Keywords/Working-mode/Skill-access
  configuration for an *existing* agent; this story's Scenarios 4-7 reuse
  that surface unchanged for a *created* agent — no new design needed for
  configuration itself, only for the creation affordance.

## Dependencies

- **Not blocked by (all satisfied already):** `REQ-SB-18-US-01` (Section,
  Done), `REQ-SB-19-US-01` (Provider, Done), `REQ-SB-20-US-01` (Keywords,
  Done), `REQ-SB-21-US-01` (Working mode, Done), `REQ-SB-27-US-01` (Skill
  grants, plumbing Done) — this story configures a created agent using
  these five already-built surfaces; it does not extend or modify any of
  them.
- **Related to, explicitly deferred:** `REQ-SB-29` (Agent-to-Tag/Folder
  Scoping / Vault Scope) — still `Draft`, `gate: flagged`, no built surface.
  The PRD's own Acceptance text names Vault Scope as an "already-existing"
  configurable property, but it factually is not yet — see Non-Goals.
- **Related to, superseded by this story:** `REQ-SB-36-US-02`'s own
  architect pass, which resolved "how does a new agent get created" as "a
  manual, code-level `agent_registry.py` addition." That resolution stands
  for every agent created before this story ships; it is superseded, not
  silently kept alongside, once this story's own mechanism exists.
- **External:** none new.

## Constraints

- A created agent's **type** is limited to the existing Worker/Producer/
  Expert enumeration — the Agents Map's ring-based layout has no rendering
  path for any other value.
- A created agent starts with an **empty actions list** — this story does
  not build any mechanism for a user to define a bespoke/custom action (see
  Non-Goals; the fork itself is flagged, not resolved).
- Configuring Section/Provider/Keywords/Working mode/Skill grants on a
  created agent must use the exact same surfaces (and therefore the exact
  same UX/validation) an existing built-in agent already uses — no
  parallel/duplicate configuration mechanism for created agents.
- Creating an agent must not require any source-code change (the PRD's own
  explicit acceptance bar — the opposite of today's `agent_registry.py`
  hand-edit).
- Vault Scope is **out of scope for this story** (see Non-Goals) — do not
  build a Vault Scope field for created agents ahead of `REQ-SB-29-US-01`
  shipping.

## Implementation Tasks

<!-- Left for the architect/decomposer at /plan-tasks, once the flagged
persisted-registry mechanism (ESC-020) and the custom-actions fork are
reviewed. -->

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Bespoke/custom actions for a user-created agent** — every existing
  action is backed by specific, real Python code; this story does not
  invent a generic "any action" mechanism. A created agent is reachable via
  chat/Hub-routing with zero actions, exactly like the already-`Done`
  `vault-filing-expert`/`compass-expert` pilot agents started. Whether a
  future story should build a generic/no-code action mechanism is a real,
  separate architectural fork — **flagged, not decided here** (see Notes).
- **Vault Scope configuration for a created agent** — `REQ-SB-29-US-01` (the
  requirement that defines Vault Scope) is still `Draft` with no built
  surface; this story does not build a Vault Scope field ahead of it.
- **Deleting or renaming an existing built-in agent** — this story is
  additive (creating new agents); it does not touch the seven existing
  static `AGENTS` entries or add a delete/rename flow for any agent, built-in
  or created.
- **Any gating/approval step on agent creation itself** (e.g. a Tier-2-style
  check mirroring `REQ-SB-35`'s new-top-level-vault-area approval) — the PRD
  breadcrumb names this as open; no such gate is asked for or built here.
- **Migrating the seven existing static `AGENTS` entries into whatever
  persisted mechanism this story introduces** — out of scope; the
  architect's `/plan-tasks` pass decides whether built-in agents stay
  purely static or are folded into the same store, but this story does not
  require moving them.

## Notes

**Prototype parity (agents-map.html / settings.html):**

- Both screens' existing Sections/Providers `+ Create new …` `<details>`
  affordances — **Specced** as the closest existing precedent for this
  story's own Create Agent affordance, but the affordance itself is
  **not covered by the approved prototype** anywhere — net-new design
  needed (see the flag below).
- `agents-map.html`'s agent detail side panel Settings tab (Section/
  Provider/Keywords/Working-mode/Skill-access rows) — **Specced**,
  Scenarios 4-7 reuse this surface unchanged; already approved for
  `REQ-SB-18/19/20/21/27`.
- `agents-map.html`'s agent detail side panel Chat/Communication History
  tabs — **Specced**, Scenario 9; already approved, unchanged by this
  story.
- `agents-map.html`'s agent detail side panel Available Actions block —
  **Specced** (Scenario 3's "no actions available yet" case), already
  approved as an empty-list state (`vault-filing-expert` demonstrates this
  today).

**Why this is flagged, not cleared (`ESCALATIONS.md` → `ESC-020`):**

1. **Custom bespoke actions — a real, unresolved architectural fork,** named
   explicitly by the PRD's own breadcrumb as "not an implementation
   detail." This story resolves only that a created agent starts with zero
   actions; whether the roadmap should ever support user-defined actions
   (and if so, via what mechanism — a generic no-code action builder would
   be substantial, separate work) is left open for a human product
   decision, not guessed.
2. **The persisted-registry mechanism directly reverses `ADR-011` point 2**
   and, unlike every prior agent-touching ADR this session, cannot be built
   as a "compose alongside, don't touch `agent_registry.py`" extension —
   `list_agents()`/`get_agent()` themselves must start reporting
   user-created agents for the five already-`Done` property registries'
   own self-healing to work at all. This is an ADR-level call belonging to
   the architect at `/plan-tasks`, flagged here rather than guessed.
3. **Net-new-design-needed** — no `html-prototype/` screen has a Create
   Agent affordance anywhere, and the PRD breadcrumb itself leaves the
   affordance's placement (Agents Map vs. Settings vs. both) genuinely
   open.

`ESCALATIONS.md` → `ESC-020` records this in full. A `REVIEW-QUEUE.md`
entry recommends: (a) a human/product decision on the custom-actions fork
(at minimum, confirming "zero actions, chat/routing-only" is acceptable for
this pass), (b) running `/plan-tasks` so the architect can write the
superseding ADR over `ADR-011` point 2 for the persisted-registry mechanism,
and (c) running `/design REQ-SB-37` for the Create Agent affordance itself
before `/plan-tasks` locks tasks against a UI shape no one has approved.

gate: flagged 2026-08-13, gate_reason: unclear-requirement (`ESC-020`,
custom-actions fork + persisted-registry mechanism reversing `ADR-011`
point 2) + net-new-design-needed (no Create Agent affordance in any
`html-prototype/` screen). `REQ-SB-37` itself is finalised PRD text (no
`<!-- Draft -->` marker) — the flag is about the open architectural fork,
the ADR-level mechanism decision, and the missing prototype coverage, not
about the requirement's own finalization state.
