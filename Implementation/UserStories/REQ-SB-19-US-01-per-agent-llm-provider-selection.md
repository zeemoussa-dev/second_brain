---
id: REQ-SB-19-US-01
title: Global LLM Provider CRUD in Settings, with a per-agent Provider picker defaulting to Compass
requirement_ids: [REQ-SB-19]
requirement_section: "REQ-SB-19: Per-Agent LLM Provider Selection"
phase: P1
status: Done
gate: clear
gate_reason: "Resolved 2026-08-12 — operator approved ADR-014 as written. All 8 ACs already built and verified live against it (2026-08-11); no rebuild required."
sprint: "SPRINT-012"
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-19-US-01 — Global LLM Provider CRUD in Settings, with a per-agent Provider picker defaulting to Compass

## Story

**As a** Second Brain user
**I want** to configure one or more LLM Providers in Global Settings, with
Compass pre-seeded as the default, and choose per agent which configured
Provider it uses
**So that** I can prepare for multiple LLM backends over time without any
agent silently behaving differently than I expect — an agent I haven't
touched keeps using Compass exactly as it does today, and an agent I do
point at a not-yet-built Provider tells me honestly rather than quietly
falling back or making something up

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-19: Per-Agent LLM Provider
  Selection* — "The user can configure one or more LLM Providers in Global
  Settings (each with at minimum a name, endpoint, credential, and model —
  Compass is pre-seeded as the default provider using its existing
  configuration) and, per agent, choose which configured Provider that
  agent uses. Compass remains the default for every agent unless the user
  explicitly picks a different one." Acceptance: "Global Settings has a
  Providers area where the user can add, edit, and remove a Provider entry,
  with Compass present by default; the Agent Settings surface lets the user
  pick a Provider for each agent individually, defaulting to Compass; an
  agent using Compass continues to work exactly as today; an agent whose
  selected Provider has no real client built yet honestly reports it's not
  available rather than silently falling back to Compass or fabricating a
  response."
- **PRD breadcrumb (2026-08-11, operator-resolved, cited verbatim, not
  re-decided here):** this pass adds the Provider *concept* only — Global
  Settings CRUD for providers, a per-agent provider picker, Compass
  functional as today's only real client. Selecting a non-Compass provider
  is honestly unavailable until a real client exists for it — **the same
  "declared but not yet backed by a real handler" pattern `ADR-011` already
  established for agent actions**, deliberately not building new provider
  clients (e.g. OpenAI/Anthropic) in this pass. Exact Provider field schema
  and where provider selection is persisted (a `.second-brain/` state file,
  `Settings`/`.env`-adjacent config, or another mechanism) are
  architecture-level decisions left to `/plan-tasks`, not decided here.
- **Compass's existing configuration is the template for a Provider's
  fields.** `src/backend/app/config.py`'s `Settings` already has
  `compass_base_url`, `compass_api_key`, `compass_model` — the PRD's
  "name, endpoint, credential, model" minimum field set maps directly onto
  this existing shape (name = "Compass", endpoint = `compass_base_url`,
  credential = `compass_api_key`, model = `compass_model`); the pre-seeded
  Compass Provider entry should read as continuous with this existing
  config, not a redesign of it.
- **Same honesty pattern as `ADR-011`.** `ADR-011` already established, for
  agent *actions*, that a declared-but-unbuilt capability must return an
  honest "not yet available" result rather than a fabricated success
  (`app/api/agents_router.py::_invoke_action`, `_ACTION_HANDLERS`). This
  requirement's own acceptance text asks for the identical shape one layer
  up, for Providers: a selected-but-unbuilt Provider must "honestly report
  it's not available rather than silently falling back to Compass or
  fabricating a response" — the same architectural posture, applied to a
  new axis. `/plan-tasks` should reuse this precedent rather than invent a
  new failure-reporting convention.
- **Design authority — a real gap, not settled by the approved prototype.**
  `html-prototype/settings.html` (approved for REQ-SB-12-US-01) has only a
  Vault card and a Connections card — no Providers area exists anywhere in
  the prototype. `html-prototype/agents-map.html`'s side panel (approved
  for REQ-SB-13-US-01) has no Provider field in its Settings `kv-list`, and
  no provider-picker control anywhere. See the Notes' "Prototype parity"
  subsection and the flag reasoning below.
- **Precedent surfaces this story attaches to (both already `Done`):**
  `REQ-SB-12-US-01` built the reachable, currently-placeholder Settings page
  (`src/frontend/src/pages/SettingsPage.tsx`, `styles/settings.css`) this
  story adds a Providers area to; `REQ-SB-13-US-01` built the Agent
  Settings detail panel (`AgentDetailPanel.tsx`) this story adds a provider
  picker to, and the `GET /agents`/`GET /agents/{id}` backend surface
  (`agents_router.py`, `agent_registry.py`) this story extends.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Global Settings' Providers area lists Compass pre-seeded as the default

```gherkin
Given the user has never added, edited, or removed any Provider
When the user opens Global Settings' Providers area
Then a Provider entry named "Compass" is present, using Compass's existing
    configuration (endpoint, credential, model)
```
<!-- AC-ID: REQ-SB-19-US-01-AC-01 -->

### Scenario 2: Adding a new Provider entry

```gherkin
Given the user is viewing Global Settings' Providers area
When the user adds a new Provider entry, supplying at minimum a name,
    endpoint, credential, and model
Then the new Provider entry appears in the Providers area
  And the new Provider is available as a choice on the Agent Settings
    surface's Provider picker
```
<!-- AC-ID: REQ-SB-19-US-01-AC-02 -->

### Scenario 3: Editing an existing Provider entry

```gherkin
Given a Provider entry exists (Compass, or one the user added)
When the user edits one or more of that entry's fields (name, endpoint,
    credential, or model)
Then the Provider entry reflects the updated field values in the Providers
    area
```
<!-- AC-ID: REQ-SB-19-US-01-AC-03 -->

### Scenario 4: Removing a Provider entry that no agent currently uses

```gherkin
Given a Provider entry exists that is not currently selected by any agent
When the user removes that Provider entry from Global Settings
Then the Provider entry no longer appears in the Providers area
  And the Provider is no longer offered as a choice on the Agent Settings
    surface's Provider picker
```
<!-- AC-ID: REQ-SB-19-US-01-AC-04 -->

### Scenario 4b: Removing a Provider entry still selected by an agent is blocked

```gherkin
Given a Provider entry exists that is currently selected by one or more
    agents
When the user attempts to remove that Provider entry from Global Settings
Then the removal is refused
  And a clear message explains that every agent using it must be switched
    to a different Provider first
  And the Provider entry, and every agent's selection, are unchanged
```
<!-- AC-ID: REQ-SB-19-US-01-AC-05 -->

### Scenario 5: The Agent Settings surface lets the user pick a Provider per agent, defaulting to Compass

```gherkin
Given an agent has never had its Provider explicitly changed
When the user opens that agent's Agent Settings surface
Then the agent's selected Provider is shown as Compass
When the user picks a different configured Provider for that agent
Then the agent's selected Provider updates to the newly picked one
```
<!-- AC-ID: REQ-SB-19-US-01-AC-06 -->

### Scenario 6: An agent using Compass continues to work exactly as today

```gherkin
Given an agent's selected Provider is Compass (the default, unchanged)
When that agent performs its normal LLM-backed work
Then it behaves exactly as it did before this story existed — no change in
    behaviour, endpoint, or credential used
```
<!-- AC-ID: REQ-SB-19-US-01-AC-07 -->

### Scenario 7: An agent whose selected Provider has no real client honestly reports it's not available

```gherkin
Given an agent's selected Provider is a configured Provider other than
    Compass, and no real client has been built for that Provider
When that agent's LLM-backed capability is invoked
Then the agent honestly reports that this Provider is not available
  And the agent does not silently fall back to Compass
  And the agent does not fabricate a response
```
<!-- AC-ID: REQ-SB-19-US-01-AC-08 -->

## Affected Screens

- `html-prototype/settings.html` — needs a new Providers area (add/edit/
  remove, Compass pre-seeded). Not present in the approved prototype; no
  design authority exists for its visual shape yet — see Notes.
- `html-prototype/agents-map.html` — the agent detail side panel's Settings
  block needs a new Provider field/picker. Not present in the approved
  prototype — see Notes.

## Dependencies

- **Blocked by:** REQ-SB-12-US-01 (`Done`) — the Settings page shell this
  story adds a Providers area to must exist first. Satisfied.
- **Blocked by:** REQ-SB-13-US-01 (`Done`) — the Agent Settings detail
  panel this story adds a provider picker to must exist first. Satisfied.
- **Related to:** `ADR-011` — this story's "honestly unavailable, not a
  silent fallback or fabrication" behaviour is the same posture `ADR-011`
  already established for undeclared agent actions; `/plan-tasks` should
  reuse, not reinvent, that precedent.
- **Related to:** `src/backend/app/config.py`'s existing `Settings` class —
  the template for what a Provider's fields should look like (Compass's
  `compass_base_url`/`compass_api_key`/`compass_model`).
- **External:** none new — this pass builds no new provider client (no
  OpenAI/Anthropic integration), per the PRD breadcrumb's explicit scope
  limit.

## Constraints

- **Only Compass is a real functional client this pass.** Building real
  clients for other providers (e.g. OpenAI, Anthropic) is explicitly out of
  scope, per the PRD breadcrumb.
- **No silent fallback, no fabrication.** An agent whose selected Provider
  has no real client must honestly report unavailability — it must not
  silently use Compass instead, and must not invent a plausible-looking
  response. This is a trust-surface requirement, not a convenience.
- Compass remains the default Provider for every agent unless the user
  explicitly picks a different one — no agent should end up on a
  non-Compass Provider without an explicit user action.
- **Removing a Provider entry currently selected by one or more agents is
  blocked** (operator-resolved, 2026-08-11) — the removal is refused with a
  clear message until every agent using it has been switched to a
  different Provider; no automatic fallback to Compass. Same policy
  REQ-SB-18-US-01 uses for section deletion, for consistency. This applies
  to Compass itself too, though in practice Compass being every agent's
  default means it is rarely, if ever, actually unused.
- The Provider field schema (name/endpoint/credential/model at minimum) and
  where Provider configuration and per-agent selection are persisted are
  architecture-level decisions left to `/plan-tasks`, not decided here, per
  the PRD breadcrumb's own explicit deferral.
- No backend endpoint currently exists for Provider CRUD or for updating an
  agent's selected Provider — new API surface is required; its exact shape
  is left to `/plan-tasks`.
- Credential fields (a Provider's API key/secret) must be handled with the
  same care as Compass's existing `.env`-sourced `compass_api_key` — not
  rendered/logged in plaintext beyond what the existing Compass credential
  handling already does; the exact UI/storage treatment is left to
  `/plan-tasks`.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-19-US-01-T01 | backend | `agent_providers.json` load/save primitives | `src/backend/app/data_access/vault_writer.py` | `../Tasks/REQ-SB-19-US-01-T01-providers-vault-writer-primitives.md` |
| REQ-SB-19-US-01-T02 | backend | `provider_registry.py` — Compass seed/self-heal/CRUD/block-remove/has_real_client | `src/backend/app/business/provider_registry.py` | `../Tasks/REQ-SB-19-US-01-T02-provider-registry.md` |
| REQ-SB-19-US-01-T03 | backend | `providers_router.py` — Provider CRUD API, credential never returned | `src/backend/app/api/providers_router.py`, `main.py` | `../Tasks/REQ-SB-19-US-01-T03-providers-router.md` |
| REQ-SB-19-US-01-T04 | backend | `PATCH /agents/{id}` (provider_id) + merged provider fields + availability gate | `src/backend/app/api/agents_router.py` | `../Tasks/REQ-SB-19-US-01-T04-agents-router-provider-assignment-and-gate.md` |
| REQ-SB-19-US-01-T05 | frontend | `ProvidersCard.tsx` + `settingsApiClient.ts` + Settings composition | `src/frontend/src/features/settings/`, `pages/SettingsPage.tsx` | `../Tasks/REQ-SB-19-US-01-T05-providers-card-settings.md` |
| REQ-SB-19-US-01-T06 | frontend | `AgentDetailPanel.tsx` Provider picker | `features/agents-map/AgentDetailPanel.tsx`, `agentsApiClient.ts` | `../Tasks/REQ-SB-19-US-01-T06-agent-detail-panel-provider-picker.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual-mode verification still current per `Implementation/Pipeline.md`'s coder-verification-mode section
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Building real clients for any Provider other than Compass** (e.g.
  OpenAI, Anthropic) — explicitly deferred by the PRD breadcrumb; this pass
  adds the Provider *concept* and CRUD only.
- **Falling back to Compass when a selected Provider is unavailable** —
  explicitly rejected behaviour; unavailability must be reported honestly,
  not masked by a silent substitution.
- **Removing or replacing Compass's existing `.env`-sourced configuration
  mechanism** — this story adds a Provider entry *alongside* it (pre-seeded
  from it), it does not migrate or remove `app/config.py`'s existing
  `compass_base_url`/`compass_api_key`/`compass_model` fields.
- **Provider-specific feature differences** (e.g. streaming, function-
  calling capability variance across providers) — out of scope; this pass
  is about *selecting* a Provider, not adapting behaviour to each one's
  capabilities.
- **Automatic fallback to Compass when removing an in-use Provider** —
  explicitly rejected (operator-resolved, 2026-08-11): removal of an
  in-use Provider is blocked, not auto-resolved. See Scenario 4b.

## Notes

**Prototype parity (settings.html, agents-map.html):**

- `settings.html`'s existing Vault card and Connections card — **N/A**, not
  touched by this story.
- `settings.html`'s new Providers area (add/edit/remove, Compass pre-
  seeded) — **not covered by the approved prototype.** No design authority
  exists for its visual shape (list layout, add/edit/remove controls,
  credential-field treatment).
- `agents-map.html`'s side panel — Available Actions/Chat/Communication
  History blocks — **N/A**, not touched by this story.
- `agents-map.html`'s side panel Settings block (`kv-list`) — needs a new
  Provider field/picker row — **not covered by the approved prototype.**

**Resolved 2026-08-11, operator-confirmed:**

- **Provider-removal-while-in-use policy:** block the removal until no
  agent still selects it — no automatic fallback to Compass. See Scenario
  4b, Constraints, and Non-Goals. Same policy REQ-SB-18-US-01 uses for
  section deletion, per the operator's explicit choice for consistency.

**Design — approved 2026-08-11 (operator):** `/design` ran against REQ-SB-18
and REQ-SB-19 together (`html-prototype/settings.html` gained a Providers
card — Compass default + seed rows for two not-yet-real providers,
add/edit/blocked-removal states; `agents-map.html`'s side panel gained an
editable Provider picker row, with one agent deliberately demonstrating the
"not yet available" honesty state). The operator reviewed the designer's
high-level output and approved before the pass's final artefact
notification landed, explicitly accepting that risk to keep moving —
`/plan-tasks` should still sanity-check the final `html-prototype/` pages
against this story's locked scenarios once available, and flag back only if
something concrete doesn't match (not re-litigate the approval itself).

gate: clear 2026-08-11 — both original triggers resolved: the
Provider-removal policy by direct operator decision, and the net-new-design
trigger by operator approval of the design pass. REQ-SB-19 itself is
finalised in the PRD (no `<!-- Draft -->` marker); no contradictory inputs;
no `ESCALATIONS.md` entry needed; not oversized — kept as one story per the
"no independent value alone" test (Provider CRUD with no per-agent
selection surface has no real value, and a per-agent picker with no
Providers configured beyond the pre-seeded Compass has little value either
— they belong together).

**Architecture pass (2026-08-11, `/plan-tasks` step 1 — architect):**
`ADR-014` written (new, appended to `Implementation/Architecture/ADR.md`,
shared with `REQ-SB-18-US-01` — both stories were designed together and
land on the same underlying mechanism; see `ADR-014`'s own Context) —
resolves this story's own explicitly-deferred architectural questions:
Providers become a new, persisted, user-mutable concern (`.second-brain/
agent_providers.json`, seeded with a Compass entry read once from
`app.config.settings.compass_*` on first read; a new `app/business/
provider_registry.py` owns CRUD, per-agent assignment, the block-until-
unused removal check, and `has_real_client()` — the "not yet available"
check for a non-Compass Provider), composed *alongside* — not inside —
the still-fully-`Accepted`, still-unmodified `app/business/agent_registry.
py` (`ADR-011` point 2's reasoning is untouched). **Credential handling:**
plaintext at rest (the same trust boundary `compass_api_key` already lives
inside — no new encryption, per the story's own "same care as... not
over-engineered" framing); `GET /providers` never returns a `credential`
field, in any response, masked or otherwise. **The pre-seeded "Compass"
entry is CRUD-editable but inert** — editing it from Settings does not
change the real, live Compass call path this pass (`app/data_access/
compass_client.py` keeps reading `.env`/`Settings.compass_*` directly,
unconditionally) — a deliberate, explicit limitation matching this story's
own Non-Goal against touching that mechanism and Scenario 6's "no change
in behaviour." **Provider-unavailability enforcement** (Scenario 7) lives
at the one shared funnel both the direct-action-trigger and chat-triggered
paths already go through, `agents_router.py::_invoke_action` — reusing
`ADR-011` point 3's "declared but not yet backed by a real handler"
pattern one layer up, per this story's own explicit instruction to reuse,
not reinvent, that precedent. New `app/api/providers_router.py` (`GET/
POST/PATCH/DELETE /providers`) and the shared `PATCH /agents/{agent_id}`
verb on `agents_router.py` (added by `REQ-SB-18-US-01`, this story adds
the `provider_id` portion of its body). Full reasoning, every alternative
considered, and every consequence: `ADR-014` in `Implementation/
Architecture/ADR.md`.

**Architecture scope (bounds the decomposer's task breakdown and the
coder's file access for this story):**
- Backend: `src/backend/app/data_access/vault_writer.py` (new
  `load_providers_state`/`save_providers_state` primitives only);
  `src/backend/app/business/provider_registry.py` (new);
  `src/backend/app/api/providers_router.py` (new);
  `src/backend/app/api/agents_router.py` (add the Provider-side portion of
  `PATCH /agents/{agent_id}`, the merged `provider_id`/`provider_name`/
  `provider_available` fields on `GET /agents/{agent_id}`, and the
  `has_real_client` gate inside `_invoke_action` — **not** the Section-side
  fields/endpoint, which are `REQ-SB-18-US-01`'s scope even though both
  land in the same file this pass); `src/backend/app/main.py` (register
  `providers_router`). `agent_registry.py` and `agent_chat.py` are
  explicitly **out of scope** — this story must not modify either.
  `app/data_access/compass_client.py` and `app/config.py` are explicitly
  **out of scope** — the real Compass call path is not touched, per this
  story's own Non-Goals.
- Frontend: `src/frontend/src/features/agents-map/AgentDetailPanel.tsx`
  (new Provider `<select>` kv-row only — the Section kv-row is
  `REQ-SB-18-US-01`'s scope), `agentsApiClient.ts` (the `provider_id`
  portion of the shared `updateAgentAssignment` call); new
  `src/frontend/src/features/settings/ProvidersCard.tsx`,
  `settingsApiClient.ts` (the `/providers` calls, added to the same shared
  client file `REQ-SB-18-US-01` starts with the `/sections` calls);
  `src/frontend/src/pages/SettingsPage.tsx` (compose `<ProvidersCard>`
  alongside `REQ-SB-18-US-01`'s `<SectionsCard>`).
- Architecture doc sections the coder is bounded by: `architecture.md` →
  "Source Layout" (the new `provider_registry.py`/`providers_router.py`
  bullet), "Frontend Application Architecture" → "Source structure" (the
  new `features/settings/` tree), "My Day & Agent Panel APIs" → "Agent
  Sections & LLM Providers — mutable, persisted agent configuration" (full
  mechanism), and `ADR-014` in full.

Per the architect's own MUST-FLAG trigger 3 (creating/changing an ADR):
`gate: flagged`, `gate_reason: trigger-3 (ADR-014 created)`. The decomposer
still runs in this same `/plan-tasks` pass — see
`Implementation/Pipeline.md`'s "Do NOT halt the stage" rule — so the human
reviews `ADR-014` and the resulting tasks together in one pass. A
`REVIEW-QUEUE.md` pointer has been added (shared with `REQ-SB-18-US-01`,
since both flag on the same `ADR-014`).

**Decomposition pass (2026-08-11, `/plan-tasks` step 2 — decomposer):**
All 8 scenarios locked as `REQ-SB-19-US-01-AC-01`…`AC-08` (sequential,
including `4b` as `AC-05`), each with a trailing `<!-- AC-ID: ... -->` tag
— no AC left non-locked, no material assumption needed to lock any of
them. 6 tasks created (`T01`–`T04` backend, `T05`–`T06` frontend) — see
`## Implementation Tasks` above for the full table. `depends_on` is
acyclic: `T01 → T02 → T03`, `T04` depends on `T02` and, cross-story, on
`REQ-SB-18-US-01-T04`; `T05` depends on `T03` and, cross-story, on
`REQ-SB-18-US-01-T07`; `T06` depends on `T04`/`T05` and, cross-story, on
`REQ-SB-18-US-01-T08`. Every locked AC has at least one AC-tagged
verification step in a task's `## Tests` (`AC-01`/`AC-03`/`AC-04`/`AC-05`
in `T05`; `AC-02` split across `T05`'s "appears in Settings" build and
`T06`'s completing "available as a picker choice" check, both tagged;
`AC-06` in `T06`; `AC-07`/`AC-08` verified directly against the real
backend in `T04`, since both scenarios describe agent *behavior*, not a
distinct screen rendering, with no frontend surface required to observe
them) — no locked AC without a tagged step.
**Shared-surface handling:** this story deliberately sequences *after*
`REQ-SB-18-US-01` on every file both stories touch (`agents_router.py`,
`AgentDetailPanel.tsx`, `agentsApiClient.ts`, `settingsApiClient.ts`,
`SettingsPage.tsx`) via explicit cross-story `depends_on` edges on `T04`,
`T05`, `T06` — see this story's own tasks' Context/Notes for the exact
diff each applies on top of `REQ-SB-18-US-01`'s already-landed code.
Story advances `Draft → Ready`; all 6 tasks written directly at
`status: Ready` (lockstep, per the decomposer's own mandate). `gate`
stays `flagged` — `ADR-014`'s own trigger-3 flag is not cleared by this
pass; the human still reviews `ADR-014` and this task breakdown together.

**Build pass (2026-08-11, `/implement-sprint` — coder, `SPRINT-012`).**
All 6 tasks built and live-verified in dependency order
(`T01→T02→T03→T04`, then `T05`, then `T06`), strictly on top of
`REQ-SB-18-US-01`/`SPRINT-011`'s already-landed shared surface (re-read
`agents_router.py`, `AgentDetailPanel.tsx`, `agentsApiClient.ts`,
`settingsApiClient.ts`, `SettingsPage.tsx` fresh before editing, per that
sprint's own retro guard). All 8 locked ACs confirmed passing against the
real backend (`uvicorn` on `:8001`) and a real browser
(`npm run dev` on `:5173`, driven headlessly via CDP — this project's
established zero-dependency Layer-1 harness): `AC-01`…`AC-05` live in
Settings' new Providers card; `AC-02`'s picker-availability half and
`AC-06` live on the Agents Map detail panel's new Provider `<select>`;
`AC-07`/`AC-08` — both trust-surface-defining scenarios — verified
directly against the real backend with one real Outlook/Compass/vault-write
capture run each (Compass no-regression-despite-edited-representation, and
honest-unavailable-no-fallback-no-fabrication for a non-Compass Provider).
`npx tsc -b && vite build` (`npm run build`) clean. Zero
`ESCALATIONS.md` entries this pass; one scope-internal observation logged
(`T02`'s Implementation Log — `create_provider` has no same-id-collision
guard, unlike `section_registry.create_section`; the task's own literal
code, not a locked-AC issue). Story advances `Ready → Done`. `gate` stays
`flagged` — the coder does not clear an ADR-creation flag; `ADR-014`'s own
human review (`REVIEW-QUEUE.md`) remains the sole open item, unaffected by
this story reaching `Done` (same posture `REQ-SB-18-US-01` already
established). All persisted state (`.second-brain/agent_providers.json`,
every agent's `provider_id`) confirmed back to the clean seed
(all 5 agents on `"compass"`, no test Providers) after verification.
