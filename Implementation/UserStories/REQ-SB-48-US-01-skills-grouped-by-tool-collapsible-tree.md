---
id: REQ-SB-48-US-01
title: Skills Capabilities Tree — Collapsible, Icon-Bearing, Multi-Select Groups by Tool
requirement_ids: [REQ-SB-48]
requirement_section: "REQ-SB-48: Skills Grouped by Tool — Collapsible Multi-Select Tree with Icons"
phase: P1
status: Done
gate: flagged
gate_reason: "coder found BUG-013 (pre-existing, out-of-scope) during live AC-06 verification; 2 scope-internal judgement calls logged for human spot-check — see REVIEW-QUEUE.md"
sprint: "SPRINT-042"
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-48-US-01 — Skills Capabilities Tree — Collapsible, Icon-Bearing, Multi-Select Groups by Tool

## Story

**As a** Second Brain user configuring an agent's Capabilities
**I want** the agent detail panel's Skills list to render as a collapsible
tree grouped under the Tool each Skill operates against, with an icon per
Tool/Skill and the ability to select more than one Skill inside an expanded
Tool group and grant or revoke them all in one action
**So that** I can scan and manage a growing Skill catalog by the real system
it touches (Outlook, Vault, Web, Compass) instead of hunting through one long
flat alphabetical list, and can grant/revoke a related batch of Skills
without repeating the same click once per Skill

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-48: Skills Grouped by Tool —
  Collapsible Multi-Select Tree with Icons* — "The unified Capabilities list
  (`REQ-SB-39`, shipped) reorganizes from a flat list into Skills grouped
  under a parent 'Tool' concept ... each Tool and Skill carrying an icon,
  presented as a collapsible tree the user can multi-select within (grant/
  revoke more than one Skill under a Tool at once)."

- **Operator's own words, verbatim (2026-08-14):** "Skills should be Grouped
  by Tools Outlook as a Tool with the Skills in it. Icons should be Added and
  we need to be able to Multiselect those tools in the Agent in a Collapse
  tree like Approach." The PRD's own breadcrumb explicitly leaves the full
  Tool taxonomy and icon-sourcing approach open to `/spec` — both are
  resolved here, from direct inspection of the real, current codebase, not
  guessed.

- **What this replaces (ground truth, read directly from the real code):**
  `AgentDetailPanel.tsx`'s Settings tab → Capabilities section
  (`SPRINT-030-T09`) renders one flat `<div className="kv-list">`: first the
  agent's currently-granted capabilities (`agent.capabilities`) — `action`-
  kind rows show a static "Built-in" label with no button, `skill`-kind rows
  show a per-row **Revoke** button — then every catalog Skill the agent does
  **not** yet hold (`skillCatalog` filtered against `agent.capabilities`)
  with a per-row **Grant** button. No grouping, no icons, no multi-select.
  `handleGrantSkill`/`handleRevokeSkill` each call `skillsApiClient.ts`'s
  `grantAgentSkill`/`revokeAgentSkill` (`POST`/`DELETE
  /agents/{agentId}/skills/{skillId}`) for exactly one Skill id, then
  refetch the agent. This story upgrades the presentation/interaction layer
  only — it does not touch these endpoints, `skill_registry.py`'s
  grant/revoke logic, or `skill_tools.SKILLS`.

- **Real, current `skill_tools.SKILLS` catalog (post-`REQ-SB-39` migration,
  confirmed by direct read, exactly 11 entries) — the complete, final set
  this story's taxonomy must place every one of, with no leftovers:**
  `diagram-understanding`, `web-research`, `view_last_run`, `ask_question`,
  `view_channel_status`, `run_capture_now`, `pause_schedule`,
  `rebuild_person_note`, `build_knowledge`, `write-to-vault-draft`,
  `summarize-file`.

- **Resolved Tool taxonomy (final — confirms 3 of the PRD breadcrumb's 4
  proposed groups verbatim, adjusts one placement with direct code
  evidence), reasoned per Skill:**

  **Outlook** — `view_last_run`, `run_capture_now`, `pause_schedule`. All
  three are capture-pipeline management Skills. `run_capture_now`'s only
  real (non-stub) handler is `email_classification.py`
  (`outlook_com.list_recent_mail`) — genuinely Outlook-backed; and the other
  two capture pipelines these Skills also apply to (meeting-capture,
  todo-capture) are themselves Outlook-sourced (`outlook_com.
  list_calendar_events`, the Outlook Tasks folder), confirmed by direct
  code read. Matches the PRD breadcrumb and the operator's own verbatim
  "Outlook as a Tool" instruction exactly.

  **Vault** — `ask_question`, `view_channel_status`, `rebuild_person_note`,
  `write-to-vault-draft`. `ask_question` is explicitly "grounded in the
  indexed vault." `rebuild_person_note`/`write-to-vault-draft` both write
  vault notes by name/description. `view_channel_status` is the one
  genuinely debatable placement in this whole taxonomy — its own
  description ("View this agent's current channel status") is actually
  about Hermes-channel reachability, not vault content, and its parent
  agent's own setting literally says "Reachable via this panel + Hermes
  channels." No dedicated "Hermes"/"Channel" Tool exists elsewhere in this
  taxonomy, and inventing a 5th group for exactly one still-stub Skill (it
  has no real handler today) is not warranted pre-P1-Hermes-integration.
  Kept under Vault as a pragmatic default — it is `vault-qa`'s own
  status-check action and the PRD's own breadcrumb already proposed this
  exact placement — not flagged, since this is a defensible call on one
  low-stakes Skill, not a genuinely blocking ambiguity.

  **Web** — `web-research`. Matches the PRD breadcrumb exactly — the only
  Skill whose real handler (`anthropic_client.web_search`) queries the open
  web.

  **Compass** — `build_knowledge`, `diagram-understanding`, `summarize-file`
  (**one adjustment from the PRD breadcrumb's own default**: `summarize-file`
  moves from the breadcrumb's proposed "Vault" placement to Compass here).
  Direct code read of `skill_tools.summarize_file` shows its real handler
  literally calls `compass_client.summarize_content` — it operates on
  already-extracted file text, not a vault note, and is Compass-generated
  content synthesis, not a vault read/write. This is the same functional
  shape as `diagram-understanding` (intended future Compass/multimodal
  understanding, per its own docstring) and `build_knowledge` (delegated,
  AI-driven self-knowledge synthesis). Grouping by "AI-synthesized
  understanding of a given input" rather than "operates on the vault" is
  the more code-grounded reading, and does not orphan `summarize-file` in a
  Vault group where none of its real behavior touches vault content at all.

  Total: 3 + 4 + 1 + 3 = 11 — every real Skill placed exactly once.

- **Icon-sourcing decision: a fixed icon per Tool group (4 icons total),
  each Skill row inheriting/displaying its parent Tool's icon — not a
  distinct icon per individual Skill.** The PRD's Acceptance text ("each
  Tool and Skill showing an icon") is satisfied because every Skill row
  visibly shows an icon; it does not require that icon to be unique per
  Skill. Recommended as the simpler option: 4 icons to source/maintain
  instead of 11+ (growing with every future Skill), and this codebase's own
  existing convention (`Sidebar.tsx`'s `.nav-icon` spans, `html-prototype`'s
  nav icons) already uses plain Unicode glyph characters, not an icon
  library/SVG asset pipeline — this story continues that exact convention
  rather than introducing a new one. No strong reason found to source
  per-Skill icons instead (no design precedent for it anywhere in this
  codebase, and it would add real maintenance cost on every future Skill
  with no functional benefit named anywhere in the PRD).

- **Built-in (`action`-kind) capabilities are unaffected by this story.**
  `skill_registry.list_agent_capabilities` combines still-real `action`-kind
  Actions (agent-type-hardcoded, never in `skill_tools.SKILLS`) with granted
  `skill`-kind Skills into one list; REQ-SB-48's own Tool taxonomy only ever
  names Skills. This story groups/trees only the `skill`-kind rows; `action`
  -kind rows keep rendering exactly as today (a plain row, "Built-in" label,
  no button, no grouping) — see Constraints.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then
edge cases and error states. Do NOT add AC-IDs — the decomposer assigns them
at /plan-tasks. -->

### Scenario 1: The Capabilities panel groups Skills into a collapsible tree by Tool

```gherkin
Given an agent's Settings tab is open on the Capabilities section
When the panel renders the agent's Skills (both already-granted and
    available-to-grant from the catalog)
Then every Skill is shown nested under exactly one Tool group — Outlook,
    Vault, Web, or Compass — matching this story's resolved taxonomy
  And each Tool group is expanded by default, showing its Skill rows
  And no Skill appears under more than one Tool group, and no Skill is
    omitted from the tree
```
<!-- AC-ID: REQ-SB-48-US-01-AC-01 -->

### Scenario 2: Collapsing a Tool group hides its Skills without losing grant state

```gherkin
Given a Tool group is expanded, showing a mix of granted and not-yet-granted
    Skill rows
When the user collapses that Tool group
Then its Skill rows are no longer visible
  And the underlying grant state of every Skill in that group is unchanged
    — collapsing never grants or revokes anything
```
<!-- AC-ID: REQ-SB-48-US-01-AC-02 -->

### Scenario 3: Expanding a collapsed Tool group restores its Skills unchanged

```gherkin
Given a Tool group was collapsed per Scenario 2
When the user expands it again
Then the same Skill rows reappear, showing the same grant state each had
    before it was collapsed
```
<!-- AC-ID: REQ-SB-48-US-01-AC-03 -->

### Scenario 4: Every Tool group and every Skill row shows an icon

```gherkin
Given the Capabilities tree is rendered
When the user views any Tool group header
Then it shows that Tool's own fixed icon
  And when the user views any Skill row nested under it
  Then that row shows the same parent Tool's icon
```
<!-- AC-ID: REQ-SB-48-US-01-AC-04 -->

### Scenario 5: Multi-select grants more than one not-yet-granted Skill within one Tool group in a single action

```gherkin
Given a Tool group is expanded and shows more than one Skill the agent does
    not currently hold
When the user selects more than one of those not-yet-granted Skill rows and
    triggers Grant
Then exactly one grant call is made per selected Skill (the same
    `POST /agents/{agentId}/skills/{skillId}` call the flat list makes today,
    once per Skill, not a new batch endpoint)
  And every selected Skill now appears as granted in that agent's
    Capabilities, and no unselected Skill in that group or any other group
    changes state
```
<!-- AC-ID: REQ-SB-48-US-01-AC-05 -->

### Scenario 6: Multi-select revokes more than one granted Skill within one Tool group in a single action

```gherkin
Given a Tool group is expanded and shows more than one Skill the agent
    currently holds
When the user selects more than one of those granted Skill rows and
    triggers Revoke
Then exactly one revoke call is made per selected Skill (the same
    `DELETE /agents/{agentId}/skills/{skillId}` call the flat list makes
    today, once per Skill, not a new batch endpoint)
  And none of the selected Skills appear as granted afterward, and no
    unselected Skill in that group or any other group changes state
```
<!-- AC-ID: REQ-SB-48-US-01-AC-06 -->

### Scenario 7: Selecting Skills of a different grant state starts a new selection

```gherkin
Given the user has one or more not-yet-granted Skill rows selected within a
    Tool group (building toward a Grant action)
When the user selects a Skill row that is already granted
Then the prior not-yet-granted selection is cleared and the newly-selected
    granted row becomes the start of a new selection
  And the available bulk action updates to Revoke, matching the new
    selection's own grant state
```
<!-- AC-ID: REQ-SB-48-US-01-AC-07 -->

### Scenario 8: Multi-select grant/revoke leaves the resulting capability state identical to today's one-at-a-time mechanism

```gherkin
Given an agent's real, current set of granted Skills
When the user grants Skill A and Skill B one at a time (today's existing
    per-row mechanism) on one agent, and grants the same Skill A and Skill B
    together via multi-select (this story's new mechanism) on an otherwise
    identical second agent
Then both agents end up with the exact same resulting set of granted Skills
  And no additional Skill, Action, or other capability differs between the
    two agents as a result of which mechanism was used
```
<!-- AC-ID: REQ-SB-48-US-01-AC-08 -->

### Scenario 9: Built-in (non-Skill) capabilities remain a separate, ungrouped list

```gherkin
Given an agent has one or more still-real, hardcoded Actions (capabilities
    of kind "action", not present in the Skills catalog)
When the Capabilities section renders
Then those Action rows continue to render exactly as today — outside the
    Tool tree, with no Tool icon, no checkbox, and no Grant/Revoke button
  And the Tool tree contains only Skills (kind "skill")
```
<!-- AC-ID: REQ-SB-48-US-01-AC-09 -->

## Affected Screens

- `html-prototype/` — **no screen or region covers this today.** Direct
  search of every `.html` file in `html-prototype/` for the Capabilities/
  Skills grant-revoke region (`Grant|Revoke|Capabilities|side-panel`) found
  it only in `agents-map.html`'s side panel, and that panel's own inline
  comment (line ~346) confirms it only ever demonstrated `REQ-SB-20`/`21`'s
  Chat/Working-mode/Keywords content — the Skills/Capabilities section was
  added later, directly in real code (`SPRINT-030-T09`), and was never
  ported back into the prototype. There is therefore no approved visual
  reference for a flat list, let alone a collapsible/multi-select/icon tree,
  anywhere in `html-prototype/` — confirmed directly, not assumed from the
  PRD breadcrumb's own claim. See the `gate: flagged` above.
- Real screen this story upgrades: `AgentDetailPanel.tsx`'s Settings tab →
  Capabilities section (the flat `kv-list` described in Context).

## Dependencies

- **Blocked by:** none technically — `REQ-SB-39-US-01`/`-02` (Done) already
  built the real grant/revoke endpoints and `skill_registry.py` gate this
  story reuses unmodified; `REQ-SB-27-US-01` (Done) built the underlying
  Skills-repository plumbing.
- **Related to:** `REQ-SB-37-US-02` — the Worker Agent Creation flow's own
  flat Skills multi-select (checkbox list, no grouping) is a separate
  control on a different screen (the creation wizard, not the detail
  panel's Capabilities section) — out of scope here, not touched by this
  story.
- **External:** a human should run `/design REQ-SB-48` to produce an
  approved collapsible/multi-select/icon tree prototype before `/plan-tasks`
  commits to a concrete DOM/CSS shape — see `gate_reason` and Notes.

## Constraints

- **No new backend behavior.** This is a pure presentation/interaction
  upgrade over the already-real, working `POST`/`DELETE
  /agents/{agentId}/skills/{skillId}` endpoints and `skill_registry.py`'s
  grant/revoke logic — neither may change as part of this story. Multi-select
  must compose N sequential single-Skill calls, never a new bulk-grant/
  revoke endpoint (Scenarios 5/6/8).
- **Tool taxonomy is fixed by this story** (see Context) — Outlook: `view_
  last_run`, `run_capture_now`, `pause_schedule`; Vault: `ask_question`,
  `view_channel_status`, `rebuild_person_note`, `write-to-vault-draft`; Web:
  `web-research`; Compass: `build_knowledge`, `diagram-understanding`,
  `summarize-file`. A future new Skill needs an explicit taxonomy placement
  decision when it's added — this story does not define a self-classifying
  mechanism.
- **Icon sourcing is fixed by this story**: 4 fixed Tool-level icons (Unicode
  glyphs, matching the existing `.nav-icon` convention), inherited by every
  Skill row under that Tool — no per-individual-Skill icon asset.
- **`action`-kind (Built-in) capabilities are out of this story's Tool tree
  entirely** — they keep rendering as a separate, ungrouped list exactly as
  today (Scenario 9).
- Collapsing/expanding a Tool group is purely a client-side display toggle —
  it must never itself fire a grant/revoke call.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-48-US-01-T01 | backend | Add `"tool"` field to every `SKILLS` catalog entry; pass through `list_agent_capabilities`'s skill-kind branch | `src/backend/app/business/skill_tools.py`, `src/backend/app/business/skill_registry.py` | `Implementation/Tasks/REQ-SB-48-US-01-T01-skills-tool-field.md` |
| REQ-SB-48-US-01-T02 | frontend | Replace the flat Capabilities `kv-list` with a collapsible, icon-bearing, multi-select Tool tree | `src/frontend/src/features/agents-map/skillsApiClient.ts`, `src/frontend/src/features/agents-map/agentsApiClient.ts`, `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` | `Implementation/Tasks/REQ-SB-48-US-01-T02-capabilities-tool-tree.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **A new bulk grant/revoke API endpoint.** Multi-select is a client-side
  batching of the existing single-Skill calls (Constraints).
- **Per-individual-Skill icons.** Explicitly decided against in favor of a
  fixed icon per Tool (Context).
- **Grouping/treeing `action`-kind (Built-in) capabilities.** They stay a
  separate, ungrouped list (Scenario 9).
- **Cross-Tool-group multi-select** (selecting Skills spanning more than one
  Tool group in one Grant/Revoke action). The PRD's own text scopes
  multi-select to "within" an expanded Tool group; this story does not
  extend it further.
- **A self-classifying mechanism for future new Skills' Tool placement.**
  This story fixes the taxonomy for today's 11 real Skills only.
- **Reworking `REQ-SB-37-US-02`'s own separate Worker-creation flat Skills
  multi-select** on the Agent Creation Wizard — a different screen, not
  touched here.

## Notes

**Prototype parity:** There is no prototype region to reconcile against —
`html-prototype/` has never depicted the Capabilities/Skills grant-revoke
area in any state (flat or otherwise), confirmed by direct search (see
Affected Screens). This is the trigger for `gate: flagged` /
`net-new-design-needed` below, not a gap in an existing approved design.

**Why this is flagged, not cleared:**

1. **`net-new-design-needed`** — no `html-prototype/` screen covers the
   Capabilities/Skills region at all, so there is no approved visual
   reference for the collapsible-tree/icon/multi-select interaction this
   story specs. Per the analyst's mandatory prototype-reconciliation rule,
   this must flag rather than silently proceed with an unreviewed layout.
2. Several concrete interaction defaults were decided here without a human
   confirming them first (though each is disclosed and reasoned, not
   silently guessed): Tool groups expand by default (Scenario 1); a
   same-grant-state-only selection model, where selecting a Skill of the
   opposite grant state starts a new selection rather than allowing a mixed
   Grant+Revoke selection (Scenario 7); and the one taxonomy placement
   (`summarize-file` → Compass, not the PRD breadcrumb's own proposed Vault)
   that differs from the PRD's own literal default.

**What to do:** run `/design REQ-SB-48` to produce an approved collapsible/
multi-select/icon tree prototype for the Capabilities section before
`/plan-tasks` commits to a concrete DOM/CSS shape; separately confirm (or
redirect) the resolved Tool taxonomy, the icon-sourcing decision, and the
three disclosed interaction defaults named above. If confirmed, `/plan-tasks`
may proceed with `gate: clear` reasoning recorded at that pass, or the
story's own `gate:`/`status:` can be reset to redo this pass with different
answers.

gate: flagged 2026-08-14, gate_reason: net-new-design-needed — see above;
`REQ-SB-48` itself carries no `<!-- Draft -->` marker in the PRD (finalized
text) — the flag is about missing prototype coverage and disclosed
interaction-default decisions, not about the requirement's own finalization
state.

---

**Architect pass (2026-08-14) — flag resolved, `gate: clear`.** The
operator explicitly decided to skip a formal `/design` pass for this story
(matching this session's established precedent for well-understood,
coder-improvisable UI patterns) and confirmed the analyst's resolved Tool
taxonomy and fixed-icon-per-Tool decision as final, superseding the
analyst's own `net-new-design-needed` flag above — the three disclosed
interaction defaults (Tool groups expand by default; same-grant-state-only
selection; `summarize-file` → Compass) are likewise adopted as final, not
re-opened.

- **Taxonomy re-confirmed against the current, real `skill_tools.SKILLS`**
  — direct re-read at this pass confirms the catalog is still exactly the
  same 11 entries the analyst's own pass enumerated (nothing landed since
  that changed it; `REQ-SB-47-US-01`'s own architecture pass reads
  `skill_tools.SKILLS[...]["mutates"]` but adds no new catalog entry). No
  correction needed to the analyst's per-Skill Tool assignment.
- **Server-side taxonomy storage, not a frontend static map.** `skill_
  tools.SKILLS` gains a `"tool"` field per entry (single source of truth,
  avoids frontend/backend drift as the Skill catalog grows), passed
  through by the already-existing `list_skills()`/`list_agent_capabilities`
  read paths — no new endpoint. Icons stay a frontend-only static lookup
  (4 fixed Tool glyphs, mirrors `Sidebar.tsx`'s existing convention) — the
  drift risk that justifies a server-side `"tool"` field does not apply
  symmetrically to a 4-entry, rarely-changing icon set.
- **No new ADR.** This is an additive field on an already-`Accepted`
  catalog shape (`ADR-015`, extended the same way `ADR-028`'s `"mutates"`
  field already was) plus a frontend presentation/interaction upgrade —
  no new mechanism, endpoint, persisted store, or trust-boundary decision.
  Full reasoning: `Implementation/Architecture/architecture.md` →
  "Amendment — Skills grouped by Tool: collapsible multi-select tree with
  icons" under "Skills Repository — registration & per-agent access".
- **No assumptions made at this pass** — every open question the analyst
  disclosed is resolved by the operator's own confirmation, not guessed
  here.

gate: clear 2026-08-14 — no ADR triggered, no new assumptions made; the
analyst's `net-new-design-needed` flag is resolved by the operator's
explicit confirmation above, not by architect judgement call.

**Architecture scope:** `Implementation/Architecture/architecture.md` →
"Skills Repository — registration & per-agent access" → "Amendment —
Skills grouped by Tool: collapsible multi-select tree with icons
(REQ-SB-48-US-01, no new ADR)" — the coder is bounded to:
`src/backend/app/business/skill_tools.py` (new `"tool"` field on every
`SKILLS` entry only — no handler-body changes), `src/backend/app/business/
skill_registry.py` (`list_agent_capabilities`'s skill-kind branch passes
`"tool"` through; `list_skills()` needs no change, its existing full-dict
passthrough already carries it), `src/frontend/src/features/agents-map/
skillsApiClient.ts` (`SkillSummary` gains `tool: string`), `src/frontend/
src/features/agents-map/agentsApiClient.ts` (`AgentCapability` gains
`tool?: string`), and `src/frontend/src/features/agents-map/
AgentDetailPanel.tsx`'s Capabilities section (replaces the flat `kv-list`
with the new collapsible, icon-bearing, multi-select Tool tree — new
sibling component file vs. inline is decomposer/coder latitude).

---

**Decomposer pass (2026-08-14).** Locked all 9 scenarios as `REQ-SB-48-US-01-AC-01`
through `-AC-09` (sequential, none marked non-locked). Read the real current
`skill_tools.py` (11-entry `SKILLS` dict, no `"tool"` field yet),
`skill_registry.py` (`list_agent_capabilities`'s existing action/skill split),
`skillsApiClient.ts` (`SkillSummary` has no `tool` field yet),
`agentsApiClient.ts` (`AgentCapability` has no `tool` field yet), and the real
current `AgentDetailPanel.tsx` (flat `kv-list` at lines ~449-487, confirmed)
before authoring tasks — no stale sample trusted. Split into 2 tasks:
`REQ-SB-48-US-01-T01` (backend: `"tool"` field on all 11 `SKILLS` entries +
`list_agent_capabilities` pass-through) and `REQ-SB-48-US-01-T02` (frontend:
API-client type additions + the collapsible/icon/multi-select Tool tree,
depends_on T01). All 9 locked ACs are tagged with a manual verification step
in T02 (the user-observable layer); AC-01 and AC-09 additionally get a
backend-level tagged step in T01 (data-shape correctness, ahead of the UI
layer — per `Implementation/Learnings.md`'s "backend-layer-first
verification" pattern). `depends_on` graph is a straight line (T02 → T01),
acyclic. Both task files written `status: Ready` in lockstep with the story.

gate: clear 2026-08-14 — no triggers fired (no ADR change this pass, no new
assumptions — every open question was already resolved by the architect's
pass above, requirement is finalized, both tasks fit comfortably in one
working session, all 9 locked ACs have an observable, verifiable outcome).
Story advances `Draft → Ready`.

---

**Coder pass (2026-08-14).** Both tasks built and verified live end-to-end
against all 9 locked ACs (`T01`: `AC-01`/`AC-09` at the backend data-shape
layer; `T02`: all 9 at the real UI layer, real headless-Edge/CDP session
against the real running app, `window.fetch`-spy-confirmed exact call
counts/URLs throughout). `SkillsTree.tsx` shipped as the exact standalone,
mode-parameterized file/shape `## Files to Modify` mandated for
`REQ-SB-46-US-01-T04`'s own future `depends_on` edge — confirmed real,
importable, and structurally correct via direct inspection and a real
screenshot. One genuine, pre-existing, out-of-scope defect
(`skill_registry._load_state`'s migration-seed self-heal) was found live
during `AC-06`'s own verification and captured as `BUGS.md` → `BUG-013` /
`ESCALATIONS.md` → `ESC-035`, not fixed here; `AC-06` was independently
re-verified honestly against a Skill/agent pair unaffected by that bug.
Two scope-internal judgement calls logged for human spot-check (see each
task's own Implementation Log and `REVIEW-QUEUE.md`). All real agent state
touched during verification was independently reconfirmed reverted to its
exact original values. Both tasks `Done`; story `Done`.

gate: flagged 2026-08-14 — trigger 6 analog (a locked AC's verification
path hit a genuine external/pre-existing defect, resolved via a disclosed
technique substitution) plus 2 scope-internal judgement calls, both parked
in `REVIEW-QUEUE.md` for human spot-check. No AC was weakened, omitted, or
left unverified.
