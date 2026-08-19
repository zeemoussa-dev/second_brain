---
id: REQ-SB-41-US-01
title: Agent Overview surface — purpose, Guardrails, and Working mode shown before Chat, with a graceful "not yet assigned" Vault Scope region
requirement_ids: [REQ-SB-41]
requirement_section: "REQ-SB-41: Agent Overview Surface"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-033 created, /plan-tasks architect pass, 2026-08-13) — supersedes the prior net-new-design-needed + unclear-requirement flag (ESC-031); navigation shape and Purpose-data-source are now resolved by ADR-033. Decomposer pass (2026-08-13): REQ-SB-29-US-01 and REQ-SB-40-US-01 are both now Ready (not Draft, as at /spec time) — T02 carries real depends_on edges on REQ-SB-29-US-01-T05 and REQ-SB-40-US-01-T08, so Scenario 5 (real assigned Scope) and the gap-count region are both fully buildable/verifiable in this story's own T02, not deferred. Flag stays open only for the ADR-033 human review breadcrumb, not for any remaining decomposer-owned ambiguity."
sprint: SPRINT-036
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-41-US-01 — Agent Overview surface

## Story

**As a** Second Brain user
**I want** to see an overview of what an agent actually is — its purpose,
its Vault Scope, its grounding/guardrail behavior, and whether it's
Autonomous, Supervised, or Manual — before I land in its Chat
**So that** I understand what I'm about to talk to before I start
chatting with it, instead of being dropped straight into a chat box with
no context

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-41: Agent Overview Surface* —
  "Opening an agent currently lands straight on its Chat tab. Before
  chatting, the user can see an overview of what the agent actually is:
  its purpose, its Vault Scope, its grounding/guardrail behavior, and
  whether it's Autonomous, Supervised, or Manual — a real summary, not
  just a chat box." **Acceptance:** "Opening an agent shows an overview —
  its purpose, its Vault Scope (once assigned), a statement of its
  grounding/guardrail behavior, and its current working mode — before or
  instead of landing directly on the Chat tab."
- **PRD breadcrumb (2026-08-13, operator-directed, cited verbatim, NOT
  re-decided here):** "The Agents Tab now Opens Straight to Chat I need to
  have an Overview Of what the Agent do, Scope, Guardrails and Is It
  Autonomous Etc before [I] Can Chat with it." The breadcrumb itself notes
  `AgentDetailPanel.tsx` (`REQ-SB-13`/`REQ-SB-21`, both `Done`) already has
  a tab structure (Chat/History/Settings) — this requirement is most
  naturally a new tab or new default landing view on that same panel, not a
  wholly new surface — but two of the four things the operator wants shown
  have no existing UI representation to reuse: **Scope** (`REQ-SB-29`,
  still `Draft`, never built) and **Guardrails** (`REQ-SB-33`, `Done`, but
  "no new Agent Settings UI needed this pass" per its own Notes — never
  surfaced anywhere in the UI, for any agent). Genuinely open, not decided
  in the PRD, named explicitly: (1) whether this is a new 4th tab
  ("Overview") alongside Chat/History/Settings, replaces Settings' current
  landing position, or becomes the panel's new default tab (currently
  Chat); (2) exact Guardrails copy/presentation, given the guardrail itself
  is global and non-configurable today — likely a static, informational
  statement rather than a toggle; (3) whether `REQ-SB-40`'s gap count (once
  built) belongs on this same Overview. Left to `/spec` — a `/design` pass
  is also needed (no prototype shows this). Depends on `REQ-SB-21-US-01`
  (Working Modes, `Done`) and `REQ-SB-33-US-01` (Grounding, `Done`); blocked
  on `REQ-SB-29-US-01` (Vault Scope, still `Draft`) for the Scope half
  specifically — the rest of this requirement (purpose, guardrails, working
  mode) does not need to wait for it.
- **Real code read directly, not assumed, to confirm what "opens straight
  to Chat" means today and what already exists to build on:**
  `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — `TABS =
  ['chat', 'history', 'settings']`, `activeTab` state initialised (and reset
  on every agent switch) to `'chat'` — confirming the operator's own
  complaint exactly: opening any agent always lands on Chat first, with no
  overview step. The existing `Settings` tab already renders a `kv-list`
  (Section/Provider/Working mode/Keywords rows sourced from `agent.settings`
  plus live pickers) and a separate "Available actions" block
  (`agent.actions`, one button per action) — this is the closest existing
  analog to a "what the agent do" summary, but it is a *configuration*
  surface, not a purpose narrative.
- **A real, material finding from direct inspection — not silently carried
  forward:** contrary to what the PRD breadcrumb's own phrasing implies
  ("purpose/description ... already on every agent's existing Settings
  tab"), **no dedicated purpose/description text field exists anywhere in
  the current data model or UI.** Checked directly:
  `app/business/agent_registry.py`'s static `AGENTS` catalog carries only
  `name`, `type` (`worker`/`producer`/`expert`), `settings` (a kv-list of
  operational config like Schedule/Vault target/Classifier), and `actions`
  — no `description`/`purpose` string anywhere.
  `src/frontend/src/features/agents-map/agentsApiClient.ts` and
  `html-prototype/agents-map.html` both confirm the same: an agent's "what
  it does" today is only ever implicitly conveyed via its `name`, its
  `type` badge, and its `settings`/`actions` rows — never a standalone
  purpose sentence. This is a genuine gap between the PRD breadcrumb's own
  claim and the real code, not a guess — see the flag below and
  `ESCALATIONS.md` → `ESC-031`.
- **Resolved here, directly from the PRD's own Acceptance text, not a
  guess — the Scope half does NOT block the rest of this story:** the
  Acceptance text itself parenthesises Scope as "(once assigned)" — the
  Overview is not required to show a populated Scope value today; it needs
  to honestly show whatever the agent's real current Scope state is,
  which for every agent today (since `REQ-SB-29-US-01` is `Draft`,
  unbuilt) is "no Scope assigned." Scenario 6 below specs that honest,
  buildable-today state directly; only Scenario 5 (a real assigned-scope
  value rendering correctly) is genuinely blocked on `REQ-SB-29-US-01`
  shipping.
- **Resolved here, by direct inspection of `REQ-SB-40-US-01`'s own current
  state — the knowledge-gaps count/link is NOT included in this story's
  scope, not silently ignored:** `REQ-SB-40-US-01` is itself `Draft`,
  `gate: flagged` (`ESC-030`), with its own detection mechanism, its
  gap-record data model, and its display-surface placement all still
  genuinely undecided — there is no gap-count data anywhere yet to display.
  Building a placeholder region on this Overview for data that does not
  exist would be speculative UI ahead of its own producing story. This
  story's own Non-Goals name this explicitly; `REQ-SB-40`'s own future
  `/plan-tasks`/`/design` pass is expected to extend this Overview once its
  own mechanism and data model are resolved, per its own PRD breadcrumb's
  "likely fit, not confirmed" framing — not built here.
- **Resolved here, by direct inspection of `REQ-SB-39-US-01`/`-US-02`'s own
  current state — this story's Purpose region reads from today's Actions
  shape, not a future Skills shape:** both `REQ-SB-39` stories are `Draft`,
  `gate: flagged` (`ESC-029`), unbuilt — `agent_registry.py`'s `actions`
  list and `agents-map.html`'s "Available actions" panel are still the
  real, live capability shape today. This story's Purpose region (if it
  summarizes capabilities at all) composes with whatever capability data
  actually exists at build time — no hard dependency on `REQ-SB-39`
  shipping first, and no assumption that Skills will exist by the time this
  story is built.
- **No `html-prototype/agents-map.html` screen shows an Overview region
  anywhere.** Confirmed by direct inspection of all agent detail panels —
  each panel's tab bar is `Settings`/`Chat`/`History`(where applicable)
  only; no "Overview" tab, no purpose narrative, no Guardrails copy exists
  in the approved prototype. A `/design` pass is required before
  `/plan-tasks` can lock tasks against a UI shape no one has approved.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then), at the observable-
behavior level — deliberately not presuming the navigation shape (new tab
vs. new default landing vs. interstitial) or the Purpose region's exact data
source, per the open questions named in Context. Happy path first, then each
of the four required regions, then the graceful degraded-Scope state, then a
regression guard for Chat itself. Do NOT add AC-IDs — the decomposer assigns
them at /plan-tasks. -->

### Scenario 1: Opening an agent shows an overview before the user can chat with it

```gherkin
Given the user opens an agent from the Agents Map
When the agent's detail panel opens
Then the panel's Overview tab is selected by default — the user sees an
    overview of that agent (its purpose, its Vault Scope state, a
    statement of its grounding/guardrail behavior, and its current
    working mode) instead of landing directly on the Chat tab
  And the user can reach Chat from this overview in one click when they
    are ready to chat
```
<!-- AC-ID: REQ-SB-41-US-01-AC-01 -->

### Scenario 2: The overview states the agent's purpose

```gherkin
Given the user is viewing an agent's overview
Then the overview states what that agent actually does / its purpose in
    the system, sourced from that agent's own "Purpose" (or "Domain")
    settings entry, or an honest "No stated purpose recorded for this
    agent" statement when neither entry exists
```
<!-- AC-ID: REQ-SB-41-US-01-AC-02 -->

### Scenario 3: The overview shows the agent's current working mode

```gherkin
Given an agent's working mode is Autonomous, Supervised, or Manual
    (REQ-SB-21)
When the user views that agent's overview
Then the overview shows the agent's current working mode
```
<!-- AC-ID: REQ-SB-41-US-01-AC-03 -->

### Scenario 4: The overview states the agent's grounding/guardrail behavior

```gherkin
Given the user is viewing an agent's overview
Then the overview states that the agent's replies are grounded in what
    its own tools actually find, and that it honestly says it doesn't
    know rather than guessing (REQ-SB-33) — a static, non-configurable
    informational statement, the same for every agent
```
<!-- AC-ID: REQ-SB-41-US-01-AC-04 -->

### Scenario 5: The overview shows a real assigned Vault Scope, once one exists

```gherkin
Given an agent has one or more vault tags or folders assigned as its
    scope (REQ-SB-29)
When the user views that agent's overview
Then the overview shows the agent's assigned scope
```
<!-- AC-ID: REQ-SB-41-US-01-AC-05 -->

### Scenario 6: An agent with no assigned Vault Scope is shown honestly, not omitted or fabricated

```gherkin
Given an agent has no vault tag or folder currently assigned as its scope
When the user views that agent's overview
Then the overview honestly indicates that no scope is currently assigned,
    rather than omitting the Scope region entirely or fabricating one
```
<!-- AC-ID: REQ-SB-41-US-01-AC-06 -->

### Scenario 7: Chat remains fully reachable and unaffected (regression guard)

```gherkin
Given the user has viewed an agent's overview
When the user navigates from the overview into that agent's Chat
Then the existing Chat tab and its conversational behavior (REQ-SB-13,
    REQ-SB-25) work exactly as they did before this story
  And the History and Settings tabs' own content is unchanged
```
<!-- AC-ID: REQ-SB-41-US-01-AC-07 -->

## Affected Screens

- `html-prototype/agents-map.html` — the agent detail side panel needs a
  new Overview region (purpose, Vault Scope state, Guardrails statement,
  Working mode) shown before or instead of Chat. **Not present in the
  approved prototype** — no design authority exists yet for its visual
  shape (a new 4th tab, a new default landing view replacing Chat's
  current default position, or an interstitial). See the flag below.

## Dependencies

- **Blocked by, partially — Scenario 5 only:** `REQ-SB-29-US-01`
  (Agent-to-Tag/Folder Scoping, `Draft`, unbuilt) — a real assigned-scope
  value cannot render until an agent can actually be assigned one.
  Scenario 6 (the honest no-scope-assigned state) does **not** depend on
  this and is buildable today, for every agent, as-is.
- **Depends on:** `REQ-SB-21-US-01` (Agent Working Modes, `Done`) — the
  working-mode data (`agent.working_mode`) this story's Scenario 3 reads
  and displays; already real, persisted, and shown on the existing
  Settings tab.
- **Depends on:** `REQ-SB-33-US-01` (Agent Grounding & Honest-Uncertainty
  Guardrail, `Done`) — the real, shipped behavior this story's Scenario 4
  states as a static, informational summary. This story does not change
  that guardrail's own mechanism or ACs — it only surfaces a description
  of it.
- **Related to:** `REQ-SB-13-US-01` (`Done`) — the `AgentDetailPanel.tsx`
  tab structure (Chat/History/Settings) this story extends with a new
  Overview region; the panel itself already exists.
- **Related to, deliberately not built here:** `REQ-SB-40-US-01` (Agent
  Knowledge-Gap Tracking & Expert Readiness, `Draft`, flagged,
  `ESC-030`) — its own PRD breadcrumb names this Overview as "the likely
  fit, but not confirmed" for its gap-count display. That story's own
  detection mechanism and data model are still undecided; this story does
  not build a knowledge-gaps region for data that does not exist yet. A
  future pass on `REQ-SB-40` is expected to extend this Overview once its
  own mechanism is resolved — see Non-Goals.
- **Related to, not a hard dependency:** `REQ-SB-39-US-01`/`REQ-SB-39-US-02`
  (Unify Agent Capabilities Under Skills, both `Draft`, flagged,
  `ESC-029`) — unbuilt. This story's Purpose region composes with whatever
  capability data (today's Actions shape, or a future Skills shape if
  `REQ-SB-39` ships first) actually exists at build time; no assumption
  either way is baked in.
- **External:** none new.

## Constraints

- **Navigation shape — RESOLVED by `ADR-033`, no longer open:** Overview is
  `AgentDetailPanel.tsx`'s new default-landing tab (`TABS` gains
  `'overview'`, first; `activeTab` no longer defaults to `'chat'`). Not a
  new 4th tab reached only after Chat, and not an interstitial — see
  `ADR-033` point 1 and this story's own `## Notes`.
- **Guardrails copy is a static, informational statement, not a toggle or
  per-agent configurable setting** — mirrors `REQ-SB-33-US-01`'s own
  resolution that the guardrail itself is a global, non-configurable
  baseline with no per-agent Settings UI. This story only surfaces a
  description of that existing behavior; it does not add any new
  Guardrails configuration.
- **Purpose data source — RESOLVED by `ADR-033`, no longer open:** reads
  the existing `settings` kv-list (`"Purpose"`, falling back to
  `"Domain"`); an honest "No stated purpose recorded for this agent."
  string when neither exists. No new field. All 7 shipped agents are
  additionally backfilled with a real, authored Purpose entry
  (`REQ-SB-41-US-01-T01`) — see `ADR-033` point 2/3.
- **Open-knowledge-gap count — RESOLVED by `ADR-033`, no longer punted:**
  composes `REQ-SB-40-US-01`'s existing `GET /agents/{agent_id}/
  knowledge-gaps` `open_count` field for Expert-type agents only, now
  that `REQ-SB-40-US-01` is `Ready` with a real endpoint — the original
  objection ("speculative UI for data that doesn't exist yet") no longer
  applies. See `ADR-033` point 4 and `REQ-SB-41-US-01-T02`.
- **Do not build against a future Skills shape** — `REQ-SB-39` is unbuilt;
  the Purpose region (if it summarizes capabilities) reads from whatever
  capability data actually exists at build time.
- Do not restructure or remove the existing Chat, History, or Settings
  tabs' own content — this story adds a new Overview region; it does not
  replace or degrade any existing tab's functionality (Scenario 7).

## Implementation Tasks

| Task | Title | Depends on | Covers |
|---|---|---|---|
| [[REQ-SB-41-US-01-T01]] | `agent_registry.py` — backfill 7 shipped agents with a real Purpose settings entry | — | AC-02 (data half; verified downstream in T02, per this project's own "verify at the user-observable layer" precedent) |
| [[REQ-SB-41-US-01-T02]] | `AgentDetailPanel.tsx` — new Overview default-landing tab (Purpose/Guardrails/Working-mode/Scope regions + Expert-only gap count) | REQ-SB-41-US-01-T01, REQ-SB-40-US-01-T08, REQ-SB-29-US-01-T05 | AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07 |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, test tooling still pending; manual mode per Pipeline.md
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints — n/a, no new decision/pattern/constraint emerged this pass (composes `ADR-033`'s already-recorded decisions)
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **`REQ-SB-29`'s own scope-assignment mechanism** — this story only
  displays an agent's already-assigned scope (or its honest absence); it
  does not build the assignment UI or the retrieval mechanism, both
  `REQ-SB-29-US-01`'s own scope.
- ~~A knowledge-gaps count/link for Expert-type agents~~ — **superseded by
  `ADR-033` point 4, now IN scope:** `REQ-SB-40-US-01` is now `Ready` with
  a real `GET /agents/{agent_id}/knowledge-gaps` endpoint; this Overview
  composes its `open_count` field for Expert-type agents only, built in
  `REQ-SB-41-US-01-T02`. This line is struck through, not deleted, so the
  original (now-outdated) reasoning stays visible per this project's own
  append-only-spec convention.
- **Any change to the Guardrails behavior itself, or a per-agent
  Guardrails toggle** — `REQ-SB-33` already resolved this as a global,
  non-configurable baseline; this story only states it, never configures
  it.
- **A new Skills-aware Purpose region** — `REQ-SB-39` is unbuilt; this
  story does not presume or build against a Skills capability shape.
- **Any restructuring of the existing Chat/History/Settings tabs'
  content** — this story adds a new Overview region alongside them, not a
  redesign of the panel as a whole.
- **Designing the concrete Overview screen itself** — flagged as
  net-new-design-needed (see `## Affected Screens`); this story's
  Acceptance Criteria are written at the observable-behavior level and do
  not presume a specific screen shape.

## Notes

**Prototype parity (`html-prototype/agents-map.html`, all agent panels):**

- Side panel header (agent name + type badge) — **Specced (reused
  as-is).** No change needed; the overview sits below/alongside this,
  unchanged.
- Tabs bar (`Settings`/`Chat`/`History`) — **Net-new design needed.**
  Gains a new Overview region; whether as a 4th tab, a new default
  landing tab, or an interstitial is undecided — see Constraints. Not
  present in the approved prototype in any form.
- Settings `kv-list` block — **N/A, unaffected.** This story does not move
  or restructure Section/Provider/Working-mode/Keywords rows; Scenario 3's
  working-mode display is a read of the same underlying data, not a
  relocation of this block.
- Available Actions block — **N/A, unaffected.** Not moved or replaced;
  the Purpose region (Scenario 2) may summarize what an agent does but
  does not remove or duplicate this block's own button list.
- Chat `chat-thread`/`chat-message` region — **N/A, unaffected** (Scenario
  7 is a regression guard, not a change).
- Communication History block — **N/A, unaffected.**
- A Guardrails statement region — **Net-new design needed.** No such
  region exists anywhere in the approved prototype, for any agent.
- A Vault Scope display region (assigned or "not yet assigned") — **Net-new
  design needed.** No such region exists anywhere in the approved
  prototype, for any agent — consistent with `REQ-SB-29-US-01`'s own
  identical finding for its own (different) Settings-surface scope field.

**Why this stays ONE story, not split by readiness (assignment-blocked vs.
buildable-today):** applying this project's own established precedent —
`REQ-SB-29-US-01` kept its own retrieval scenarios (blocked on an unbuilt
foundation) in the same story as its buildable assignment scenarios, rather
than splitting by readiness. This story does the same: Scenario 6 (the
honest no-scope-assigned state) is buildable today and gives the Overview
real value the moment it ships; Scenario 5 (a real assigned-scope value) is
the same region's natural completion once `REQ-SB-29-US-01` ships — not a
different feature. Splitting would produce two stories both needing the
exact same screen region, one of them a strict subset of the other.

**Why the knowledge-gaps question (`REQ-SB-40`'s own explicit cross-
reference) is punted, not silently dropped:** `REQ-SB-40-US-01`'s own PRD
breadcrumb names this Overview as "the likely fit, but not confirmed" and
explicitly left the question for this story to resolve or explicitly punt
on. Resolved here: punt, not build. Building a placeholder region for data
whose own detection mechanism, data model, and even whether it composes
with Vault Scope's "Expert-type agent" framing are all still undecided in
`REQ-SB-40-US-01` itself would be speculative UI ahead of its own producing
story — the same "don't build ahead of an unresolved foundation" reasoning
already applied to Scope's own genuinely-blocked half (Scenario 5). This is
recorded as a real decision, not an oversight — `ESCALATIONS.md` →
`ESC-031` and `REQ-SB-40-US-01`'s own Notes both point at this resolution.

**Architect pass (`/plan-tasks` step 1, 2026-08-13) — navigation shape and
Purpose-data-source questions resolved, `ADR-033` written, `/design`
remains skipped for this batch (operator-directed, unchanged from the
prior flag):**

- **Landscape change since this story was specced, applied directly, not
  re-derived:** `REQ-SB-37-US-01`/`-US-02`/`-US-03` (Agent Creation
  Wizard) are all `Ready` now and introduce the first real Purpose-shaped
  data (`ADR-030`/`ADR-031`) — Expert gets `{"key": "Domain", ...}`,
  Producer gets `{"key": "Purpose", ...}`, both via `create_agent`'s
  `settings` kv-list. `REQ-SB-40-US-01` (Knowledge-Gap Tracking) is also
  `Ready` now, with a real `count_open_gaps()`/`GET /agents/{agent_id}/
  knowledge-gaps` endpoint that did not exist at spec time.
- **Navigation shape — resolved toward the operator's own framing.**
  Overview becomes `AgentDetailPanel.tsx`'s new **default-landing tab**,
  not a new tab reached only after Chat and not an interstitial. `TABS`
  gains `'overview'`, placed first (final order: `['overview', 'chat',
  'history', 'settings', 'gaps']`, `'gaps'` unchanged from `ADR-032`'s own
  Expert-type gating). `activeTab`'s initial/reset value changes from
  `'chat'` to `'overview'`. Chat remains fully reachable, one click away,
  unmodified (Scenario 7's regression guard).
- **Purpose data source — resolved as a read of the existing `settings`
  kv-list**, not a new field: look for `"Purpose"`, then `"Domain"`; if
  neither exists, show an honest "No stated purpose recorded for this
  agent" state — never a fabricated or Skills/Scope-derived summary.
- **Worker-purpose decision — backfill, not display-time inference.** All
  7 shipped agents (3 Worker-type: `email-capture`/`meeting-capture`/
  `todo-capture`; 1 Producer-type: `people-producer`; 3 Expert-type:
  `vault-qa`/`vault-filing-expert`/`compass-expert`) are backfilled with
  one real, authored `"Purpose"` settings entry each — a static-seed-data
  edit only, appended to each entry's existing `settings` list, that does
  **not** touch `create_agent`/`POST /agents` or reopen
  `REQ-SB-37-US-02-T01`'s already-`Ready`, already-locked "Worker's
  `create_agent` call MUST pass `settings=[]`" constraint (that constraint
  governs the runtime wizard-creation path only). A Worker created after
  this pass via the wizard, with no Purpose entry, shows the honest
  "No stated purpose recorded" state instead.
- **Gap-count decision — wired this pass, not deferred again.** The
  objection that motivated `REQ-SB-40-US-01`'s original punt
  ("speculative UI for data that doesn't exist yet") no longer applies now
  that its endpoint is real and `Ready`. The Overview composes
  `GET /agents/{agent_id}/knowledge-gaps`'s existing `open_count` field
  for Expert-type agents only, no new endpoint — a real, sequencing-only
  build dependency on `REQ-SB-40-US-01`'s endpoint landing first (the rest
  of the Overview has no such dependency).
- Full mechanism, every alternative considered, and every consequence:
  `Implementation/Architecture/ADR.md` → `ADR-033`. Full file-level shape,
  including the 7 draft backfill Purpose lines: `Implementation/
  Architecture/architecture.md` → "Agent Overview surface" (under "My Day
  & Agent Panel APIs").

**Architecture scope: §My Day & Agent Panel APIs → "Agent Overview
surface" subsection (`ADR-033`); §My Day & Agent Panel APIs → "Agent
detail panel — settings, actions, chat, unified history" (`ADR-011`,
`TABS`/`activeTab` structure this pass extends); §Agent-to-Tag/Folder
Vault Scoping (`REQ-SB-29-US-01`, Scope field read); §Addendum
(`REQ-SB-33-US-01` guardrail, static statement); §Agent Working Modes &
Pending Approvals (`REQ-SB-21-US-01`, `working_mode` field); §Agent
Knowledge-Gap Tracking & Expert Readiness (`ADR-032`, `open_count`
composition); §Agent Creation Wizard (`ADR-030`/`ADR-031`, `settings`
kv-list Purpose/Domain convention).** The coder is bounded to these
sections plus `agent_registry.py`'s 7 seed entries (the backfill) — no
other architecture.md section is in scope for this story.

gate: flagged 2026-08-13, gate_reason: trigger-3 (`ADR-033` created,
`/plan-tasks` architect pass) — supersedes the prior net-new-design-needed
+ unclear-requirement flag (`ESC-031`); the navigation-shape and
Purpose-data-source questions that flag named are now resolved (above),
not still open. `/design` stays skipped for this batch, per the operator's
own standing direction — this is standard ADR-creation review, not a
design-sign-off gate. Decomposer proceeds to lock ACs/tasks; the human
reviews `ADR-033` and the resulting tasks together in one pass, per
Pipeline.md's "do NOT halt the stage" rule. `REVIEW-QUEUE.md` has an entry
pointing at `ADR-033` and this story.

**Decomposer pass (`/plan-tasks` step 2, 2026-08-13) — ACs locked, tasks
created, story advanced `Draft → Ready`, gate left `flagged` (breadcrumb
only — the ADR-033 flag carries forward unchanged, per Pipeline.md; no new
decomposer-owned trigger fired):**

- All 7 scenarios tightened for buildability and assigned sequential
  AC-IDs (`AC-01`…`AC-07`), locked by default — no AC required
  `locked: false`. Two tasks: `REQ-SB-41-US-01-T01` (backend Purpose
  backfill, `agent_registry.py`) and `REQ-SB-41-US-01-T02` (frontend —
  `AgentDetailPanel.tsx`'s new Overview tab, the nav-default change, and
  all 4 regions + the Expert-only gap-count line). Every AC's real
  user-observable verification lives in `T02` (mirrors this project's own
  established "verify at the observable layer, not the data layer"
  precedent, e.g. `REQ-SB-29-US-01-T03`→`T05`); `T01`'s own Tests are
  non-AC smoke checks confirming the 7 backfilled settings entries exist.
- **`AC-05` (Scenario 5, a real assigned Vault Scope) is fully buildable
  and verifiable in this pass, not deferred** — `REQ-SB-29-US-01` is now
  `Ready` (was `Draft`/unbuilt at `/spec` time, per this story's own
  Dependencies section above); `T02` carries a real `depends_on` edge on
  `REQ-SB-29-US-01-T05` (the task landing the `scope` field on
  `AgentDetailPanel.tsx`'s `AgentDetail` interface), so by `T02`'s own
  build order `scope` is real, not speculative. This narrows the story's
  own prior "Scenario 5 genuinely blocked" framing — it no longer is,
  once sequenced correctly.
- **`T02` also carries a real `depends_on` edge on `REQ-SB-40-US-01-T08`**
  (the task landing the conditionally-rendered `'gaps'` tab and the base
  `TABS` array/tab-bar JSX in the same shared `AgentDetailPanel.tsx`
  file) — `T02` composes `'overview'` into that same `TABS` constant, and
  must land after `T08`'s own diff to avoid two divergent edits to the
  same array. This is the real, sequencing-only dependency `ADR-033`'s own
  Consequences named for the gap-count region; the rest of the Overview
  (Purpose, Guardrails, Working mode, and — per the paragraph above — Scope
  too) has no such dependency in principle, but `T02` is one combined
  frontend task (all 4 regions + gap count live in the same new tab
  content block), so the task-level `depends_on` reflects the edge any of
  its regions needs.
- **`REQ-SB-37-US-01` is cited informationally only, no `depends_on`
  edge** — `T01`'s backfill is a static-seed-data edit to whichever
  top-level dict name is real at build time (`AGENTS` today; possibly
  renamed to `_SEED_AGENTS` by `REQ-SB-37-US-01-T02` if that lands first)
  — `T01`'s own Files to Modify instructs the coder to read the real
  current file and compose around whichever name is present, so no hard
  build-order dependency is needed either way.
- `depends_on` graph is acyclic (`T01` → `T02`; `T02` also → two external
  tasks from already-`Ready` sibling stories, neither of which depends on
  anything in this story). Every locked AC has at least one AC-tagged
  verification step in `T02`. Story and both tasks advance to `status:
  Ready` together, per the task-lockstep rule.

**Coder pass (`/implement-sprint SPRINT-036`, 2026-08-14) — both tasks
built and verified live, story advances `Ready → Done`, `gate: flagged`
left unchanged (carried breadcrumb only, per `REQ-SB-40-US-01`'s own
identical precedent — a story stays flagged once an ADR was created for
it, independent of build completion):**

- `T01` backfilled all 7 shipped agents' `settings` lists with a real,
  authored `Purpose` entry (verbatim `ADR-033` point 3a copy); verified via
  Python-shell + real HTTP smoke checks (non-AC layer, per the story's own
  "verify at the observable layer" convention).
- `T02` landed the Overview default-landing tab exactly as `ADR-033`
  specified: `TABS` gained `'overview'` first, `activeTab`'s default
  changed `'chat'` → `'overview'`, 4 regions (Purpose/Working
  mode/Guardrails/Vault scope) plus an Expert-only gap-count line. All 7
  locked ACs (`AC-01`–`AC-07`) verified live via a CDP-driven headless Edge
  session against the real running app (real Vite dev server + real
  backend on `:8001`) — spot-checked across 3 different agent types
  (`vault-qa` Expert, `todo-capture` Worker, `people-producer` Producer),
  confirming: real backfilled Purpose text for each; Overview as the true
  default landing tab with Chat one click away and fully functional; the
  Expert-only gap-count region present (and composing `REQ-SB-40-US-01`'s
  real `open_count`) for `vault-qa` only, genuinely absent from the DOM for
  the other two; the honest "No vault scope assigned yet" state for every
  agent with no scope, and a real assigned scope (`"customer/masdar"`)
  rendering correctly and surviving a panel close/reopen once assigned.
  Zero console errors/warnings across the full session. Full detail in
  each task's own Implementation Log.
- One real, transparently-noted drift from `T02`'s own "before" code
  sample: `REQ-SB-39` (Skills unification) has also since landed,
  replacing `agent.actions`/the "Available actions" block with
  `agent.capabilities`/a "Capabilities" block — out of scope for this
  story (the Overview's own Purpose region never read `actions`), required
  no diff change, logged for transparency only.
- No new MUST-FLAG trigger fired during the build — no new dependency, no
  shared-interface change beyond what `T08`/`T05` already anticipated, no
  ADR deviation, no unanticipated file, no unclear/contradictory
  requirement. Nothing written to `ESCALATIONS.md`/`REVIEW-QUEUE.md` this
  pass; the existing `ESC-031`/`ADR-033` review item on `REVIEW-QUEUE.md`
  is left as-is for the human's own independent review.
