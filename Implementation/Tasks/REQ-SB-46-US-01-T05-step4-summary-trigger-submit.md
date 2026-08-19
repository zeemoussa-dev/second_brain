---
id: REQ-SB-46-US-01-T05
title: Step 4 — summary + Trigger choice + submit wiring (additive backend trigger field); regression-guard verification
parent_story: REQ-SB-46-US-01
requirement_id: REQ-SB-46
type: fullstack
status: Done
gate: flagged
gate_reason: "scope-internal implementation-sequencing judgement call — see T02's Implementation Log; one disclosed judgement call on Expert/Producer's own optional Step-3 Skills grants — see below"
phase: P1
depends_on: [REQ-SB-46-US-01-T04]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-46-US-01-T05 — Step 4: summary, Trigger choice, submit wiring, regression guard

## Parent Story

- Story: [[REQ-SB-46-US-01]] — `../UserStories/REQ-SB-46-US-01-agent-creation-wizard-popup-modal-redesign.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-46 *Agent Creation Wizard Redesign — Popup Modal with Visual Step Bar*

---

## Objective

Build Step 4 (read-only summary + Trigger choice + "Create agent"),
add the one additive `trigger` field to the backend `create_agent`
mechanism, wire the final per-type submit call sequences (unchanged in
shape, now reading Steps 1-4's own collected state), and verify the whole
wizard end-to-end for all 3 types (the story's own regression guard).

---

## Starting State → End State

**Before / Inputs:**
- `T04` has produced a working Steps 1-3 sequence advancing to
  `currentStep === 4`, with `name`/`type`/`domain`/`scopeDraft`/
  `sectionId`/`workingMode`/`purposeDraft`/`selectedOutputSkillId`/
  `selectedSkillIds` all lifted at the `CreateAgentWizardModal` component
  level (per `T02`/`T03`/`T04`'s own Context notes) — read the real file
  as `T04` leaves it to confirm exact state names before wiring submission
  against them.
- `src/backend/app/api/agents_router.py`'s `CreateAgentBody` (line ~82,
  confirmed by direct read) is `{name: str, type: str, domain: str | None,
  purpose: str | None}` — no `trigger` field. `create_agent` (line ~260)
  builds one `settings` kv-list per type branch (Expert: `[{"key":
  "Domain", ...}]`; Worker: `[]`; Producer: `[{"key": "Purpose", ...}]`)
  then calls `agent_registry.create_agent(name, type, settings=settings)`.
- `src/frontend/src/features/agents-map/agentsApiClient.ts`'s
  `CreateAgentBody` interface (line ~149, confirmed by direct read) is
  `{name, type, domain?, purpose?}` — no `trigger` field.
- The pre-existing file's three submit handlers
  (`handleSubmit`/`handleWorkerSubmit`/`handleProducerSubmit`, confirmed
  by direct read) each already issue the correct call sequence: Expert —
  `createAgent({name, type: 'expert', domain})` →
  `updateAgentAssignment(id, {section_id})`; Worker — `createAgent({name,
  type: 'worker'})` → N × `grantAgentSkill(id, skillId)` →
  `updateAgentAssignment(id, {section_id, scope})`; Producer —
  `createAgent({name, type: 'producer', purpose})` →
  `grantAgentSkill(id, outputSkillId)` → `updateAgentAssignment(id,
  {section_id})`. This task relocates these three handlers to fire from
  Step 4's "Create agent" button, extending each with the new fields
  Steps 2-4 collected — it does not change their call ORDER or COUNT.

**After / Outputs:**
- Backend: `CreateAgentBody` gains `trigger: str | None = None`.
  `create_agent` appends `{"key": "Trigger", "value": trigger or "user"}`
  to each of the 3 type branches' own `settings` list, after that
  branch's existing settings are built (uniform trailing append, no
  per-type special-casing — `ADR-039` point 3, verbatim).
  `agentsApiClient.ts`'s `CreateAgentBody` gains `trigger?: string`.
- Step 4 (`currentStep === 4`) renders `data-testid="wizard-step4-
  summary"` — a read-only recap listing every field entered across Steps
  1-3 for the current Type (Name, Type, Section, the Type-conditional
  Step 1 field, Working mode, the Type-conditional Step 2 fields, selected
  Skills).
- A Trigger radio group: `data-testid="wizard-step4-trigger-user"`,
  `-agent"`, `-schedule"`, defaulting to `user` selected. Selecting
  `schedule` reveals `data-testid="wizard-step4-schedule-placeholder"` — a
  message stating schedule configuration happens on the agent's own
  Schedule tab once available; selecting `schedule` (or any option) never
  opens any schedule-configuration UI inline.
- A `data-testid="wizard-step4-create"` button. On click: validates every
  required field is still present across all 4 steps for the current Type
  (defense-in-depth — each step's own "Next" already gated this, but a
  user cannot reach Step 4 with a missing field via this wizard's own
  navigation, so this is a final consistency check, not new UX); on
  success, issues the SAME 3 call-sequence shapes described above, each
  now also passing `trigger: selectedTrigger` on the `createAgent` call
  and `working_mode: workingMode` on the final `updateAgentAssignment`
  PATCH (an additive param on the SAME existing PATCH call, not a new
  call). On success, calls the `onCreated` prop (`T01`'s wiring) with the
  resulting `AgentDetail`, which `AgentsMapPage` uses to close the modal
  and refresh the map. On failure (a real backend error, not a client
  validation gap), renders `data-testid="wizard-step4-error"` and does not
  close the modal or fabricate a created agent.
- A `data-testid="wizard-step4-back"` button returns to Step 3.

---

## Files to Modify

- `src/backend/app/api/agents_router.py` — `CreateAgentBody` gains
  `trigger: str | None = None`; `create_agent`'s 3 branches each append
  the `Trigger` settings entry.
- `src/frontend/src/features/agents-map/agentsApiClient.ts` —
  `CreateAgentBody` gains `trigger?: string`.
- `src/frontend/src/features/agents-map/CreateAgentWizardModal.tsx` —
  Step 4 summary/Trigger UI; relocate and extend the 3 submit handlers to
  fire from Step 4, reading all 4 steps' lifted state; wire `onCreated`.
- `src/frontend/src/pages/AgentsMapPage.tsx` — confirm/complete the
  `onCreated` handler `T01` wired through actually closes the modal and
  re-runs the map's own agent-list refresh (if `T01` left this as a
  pass-through, this task is where it is finally exercised for real).

---

## Constraints

- Inherits from parent story (hard constraint, verified by this task's own
  regression-guard steps below): the resulting created agent must be
  functionally identical — same backend calls, same resulting
  fields/capabilities — to one created via today's shipped wizard, for
  every one of the three types.
- No new backend field beyond the additive `trigger` — `working_mode` is
  NOT new (already accepted by `updateAgentAssignment`/`PATCH
  /agents/{id}`, `REQ-SB-21-US-01`, `Done`); this task only newly SENDS it
  from the creation flow, on the same existing PATCH call.
- Selecting "Schedule" or "Agent" as Trigger must not attempt to build or
  simulate any part of `REQ-SB-47`'s own schedule-configuration mechanism
  or any new Hub-routing behavior — both are recorded as metadata only.
- Read the real current `CreateAgentWizardModal.tsx`/`agents_router.py`/
  `agentsApiClient.ts` (as `T04` and the backend's own current state leave
  them) before editing.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-46-US-01-AC-06] Complete Steps 1-3 for any Type, advance to
   Step 4. Expect `[data-testid="wizard-step4-summary"]` listing every
   field entered so far, the Trigger radio group defaulted to
   `[data-testid="wizard-step4-trigger-user"]` selected, and
   `[data-testid="wizard-step4-create"]` present.
2. [REQ-SB-46-US-01-AC-07] (Regression guard, Expert) Using a
   `window.fetch` spy, complete the wizard for an Expert-type agent (Name,
   Description, Section; skip Skills at Step 3). Click Create. Expect
   exactly 2 calls in order: `POST /agents` with `{type: "expert", domain:
   <value>}` in the body, then `PATCH /agents/{id}` with `{section_id:
   <value>, working_mode: <value>}`. Fetch the resulting agent and confirm
   its shape (settings containing Domain + Trigger entries, capabilities,
   section) is indistinguishable from an Expert agent created via a direct
   `POST /agents` call with the same inputs (cross-check against a
   parallel agent created that way, per this project's own established
   cross-check pattern). Confirm the agent appears on the Agents Map on
   the Expert ring immediately after modal close.
3. [REQ-SB-46-US-01-AC-07] (Regression guard, Worker) Complete the wizard
   for a Worker-type agent (Name, Scope, Section, 2 selected Skills at
   Step 3). Click Create. Expect exactly `1 (POST /agents) + 2 (one
   grantAgentSkill POST per selected Skill) + 1 (PATCH combining
   section_id + scope + working_mode)` = 4 calls, in that order, unchanged
   in shape from today's shipped Worker flow. Confirm both granted Skills
   appear on the resulting agent's capabilities.
4. [REQ-SB-46-US-01-AC-07] (Regression guard, Producer) Complete the
   wizard for a Producer-type agent (Name, Purpose, output Skill at Step
   2, Section; optionally 1 additional Skill at Step 3). Click Create.
   Expect `1 (POST /agents) + 1 (grant of the output Skill) + [0 or 1
   additional grant] + 1 (PATCH section_id + working_mode)` calls, in
   order. Confirm the output Skill and any additional Skill both appear
   granted.
5. [REQ-SB-46-US-01-AC-08] On Step 4, select
   `[data-testid="wizard-step4-trigger-schedule"]`. Expect
   `[data-testid="wizard-step4-schedule-placeholder"]` to render its
   honest message, and confirm no schedule-configuration UI element of any
   kind mounts. Complete Create; fetch the resulting agent and confirm its
   `settings` list contains `{"key": "Trigger", "value": "schedule"}`.
6. [REQ-SB-46-US-01-AC-09] On Step 4, select
   `[data-testid="wizard-step4-trigger-agent"]` and Create. Fetch the
   resulting agent, confirm `{"key": "Trigger", "value": "agent"}` in
   `settings`. Send a Hub-routable message that would route to this new
   agent (or a direct chat message) and confirm it responds exactly as any
   other already-shipped agent of the same type does — no different
   behavior gated by the Trigger value.
7. [REQ-SB-46-US-01-AC-10] (Full walkthrough) Starting fresh: on Step 1
   leave Name empty, click Next — blocked (already covered structurally in
   `T02`, reconfirm here as part of the end-to-end chain). Advance
   correctly through Steps 1-3 for a Worker agent, arrive at Step 4 with
   all required fields present, click
   `[data-testid="wizard-step4-create"]` — expect success (this confirms
   the full chain's own final-step validation does not spuriously block a
   fully-valid submission). Confirm no partial/broken agent appears on the
   Agents Map at any point before the final successful Create.
8. [REQ-SB-46-US-01-AC-11] Open the wizard, enter a Name and a Description
   at Step 1, advance to Step 2, enter a Purpose (Producer type) — then
   close the modal via `[data-testid="wizard-modal-close"]` without
   clicking Create. Using a `window.fetch` spy, confirm zero `POST
   /agents` calls fired. Reopen the wizard via the FAB. Expect Step 1 to
   render with Name and Description both empty (the conditional-mount
   unmount `T01` established makes this true by construction — confirm it
   holds now that real field state exists).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Step 4 shows a read-only summary of Steps 1-3, a Trigger choice defaulting to User, and a "Create agent" action
- [ ] Expert/Worker/Producer each issue the exact same backend call sequence (count, order, shape) as today's shipped wizard, extended only with the additive `trigger`/now-sent `working_mode` params
- [ ] Every created agent appears immediately on the Agents Map on the correct ring
- [ ] Selecting Schedule as Trigger records `{"key": "Trigger", "value": "schedule"}`, shows an honest placeholder message, and opens no inline schedule-configuration UI
- [ ] Selecting Agent as Trigger records `{"key": "Trigger", "value": "agent"}` and produces no different runtime behavior than User/Schedule
- [ ] A missing required field anywhere in the wizard blocks creation with a clear, honest message and never produces a partial/broken agent
- [ ] Closing the modal mid-wizard creates no agent; reopening starts a genuinely fresh, empty Step 1
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any part of `REQ-SB-47`'s own schedule-configuration mechanism.
- Any part of `REQ-SB-51`'s `is_background_agent` toggle.
- Editing an already-created agent's Trigger value post-creation.
- Visual polish — not a locked AC.

---

## Context / Notes

- `ADR-039` point 3 is this task's authority for the Trigger field's exact
  shape and the decision NOT to compose `REQ-SB-47`'s real schedule-CRUD
  endpoints here.
- This task is also where the parent story's Scenario 7 regression guard,
  Scenario 10's full validation walkthrough, and Scenario 11's full
  discard walkthrough are verified — by this point in the dependency
  chain every prior step's fields genuinely exist to exercise end-to-end;
  no separate task builds new code for these three scenarios.

---

## Implementation Log

**Sequencing note:** built together with `T02`/`T03`/`T04` in one coherent
pass — see `T02`'s own Implementation Log for the full disclosed
reasoning. This task's own real backend edit (`agents_router.py`'s
additive `trigger` field) and the final Step 4/submit-wiring frontend
edits were what this task's own coder actually authored and verified.

**Disclosed scope-internal judgement call (not a locked-AC requirement,
logged for human spot-check):** the task's own Starting-State description
of the Expert submit sequence names only 2 calls (`POST` then `PATCH`,
no Skill grants), matching AC-07's own literal 0-selected-Skills Expert
test case exactly. Since Step 3 (`T04`) makes Skills selection genuinely
available and optional for Expert too (Scenario 5), this task's own coder
extended Expert's submit handler to also grant any Step-3-selected Skills
(mirroring Worker's/Producer's own "loop-grant selectedSkillIds" shape) —
otherwise a real Expert-selected Skill would be silently discarded at
submit time, contradicting Step 3's own "available to Expert" contract.
This is structurally a no-op when zero Skills are selected (a `for`
loop over an empty array executes zero calls), so it satisfies AC-07's own
literal 2-call Expert test exactly while not silently dropping a real
selection in the untested (by any locked AC) but real "Expert selects
Skills at Step 3" case.

**Implemented (2026-08-14):**
- `agents_router.py`'s `CreateAgentBody` gains `trigger: str | None = None`;
  `create_agent` now computes `trigger_value = (body.trigger or
  "user").strip() or "user"` once and appends `{"key": "Trigger", "value":
  trigger_value}` to each of the 3 branches' own `settings` list, after
  their existing settings (Domain/none/Purpose) — uniform trailing append,
  no per-type special-casing, per `ADR-039` point 3 verbatim.
  `agentsApiClient.ts`'s `CreateAgentBody` gains `trigger?: string`.
- Step 4 (`currentStep === 4`) renders `wizard-step4-summary` (a read-only
  `kv-list` recap of every field collected across Steps 1-3 for the
  current Type), a Trigger radio group (`wizard-step4-trigger-user/
  -agent/-schedule`, defaulting to `user`), a `wizard-step4-schedule-
  placeholder` honest message shown only when Schedule is selected (no
  schedule-configuration UI mounts, confirmed live below), and
  `wizard-step4-create`. `handleCreate` re-validates every required field
  across all 4 steps (defense-in-depth — Scenario 10), then issues the
  SAME per-type call sequence (shape/order/count) today's shipped wizard
  already issues, extended only with `trigger` on the `createAgent` call
  and `working_mode` on the existing `updateAgentAssignment` PATCH (an
  additive param on the same call, not a new one); on success calls
  `onCreated` (`T01`'s wiring), which `AgentsMapPage` uses to close the
  modal and re-run its own real `refreshAgents()` sequence.
  `wizard-step4-back` returns to Step 3.

**Verification — real backend (port 8001, restarted after the backend
edit) + real frontend + a from-scratch Node CDP driver, PLUS direct
backend HTTP calls for independent cross-checks (all real, no mocks):**

- **[REQ-SB-46-US-01-AC-06]** PASS. Completed Steps 1-3, advanced to
  Step 4: `wizard-step4-summary` present and populated,
  `wizard-step4-trigger-user` checked by default, `wizard-step4-create`
  present.
- **[REQ-SB-46-US-01-AC-07]** PASS, all 3 types, verified via a real
  `window.fetch` spy plus independent `GET /agents/{id}` calls (not just
  trusting the UI's own claim):
  - **Expert:** submit-sequence calls (non-GET, isolated from the map's
    own incidental `GET /agents`/`GET /sections` refresh calls `T01`
    wired) were exactly `POST /agents` → `PATCH /agents/{id}`, 2 calls, in
    order. The resulting agent's `settings` (`Domain` + `Trigger`),
    `section_id`, `working_mode`, `type` were byte-for-byte identical to
    an agent created via a parallel, independent direct `POST /agents` +
    `PATCH` call with the same inputs (`shapeMatches: true`). Appeared
    with `type: "expert"` on the map's own data (Expert ring) immediately
    after modal close.
  - **Worker:** exactly 4 calls — `POST /agents`, 2× `POST
    .../skills/{id}` (one per the 2 selected Skills), `PATCH
    /agents/{id}` (carrying `section_id` + `scope` + `working_mode`
    combined) — in order. Resulting agent: `capabilities.length === 2`,
    `scope === ["customer/cdp-worker-test"]`.
  - **Producer:** exactly 4 calls — `POST /agents`, `POST
    .../skills/{outputSkillId}`, `POST .../skills/{extraSkillId}`, `PATCH
    /agents/{id}` — in order (the extra Step-3 Skill explicitly chosen to
    have a DIFFERENT id than the Step-2 output Skill, confirmed via
    `data-testid` matching, not index position, since the Tool-grouped
    tree's own row order differs from the flat output-Skill radio order).
    Resulting agent: `capabilities.length === 2` (output Skill + the one
    extra).
- **[REQ-SB-46-US-01-AC-08]** PASS. Selected Schedule Trigger:
  `wizard-step4-schedule-placeholder` rendered its honest message; no
  element matching any schedule-config/-form/-interval `data-testid`
  pattern ever mounted. After Create, the real agent's `settings`
  contained `{"key": "Trigger", "value": "schedule"}`.
- **[REQ-SB-46-US-01-AC-09]** PASS. Selected Agent Trigger; after Create,
  `settings` contained `{"key": "Trigger", "value": "agent"}`. Sent a real
  `POST /agents/{id}/chat` message to the freshly created agent — got back
  the same `{reply, action_triggered}` shape every other agent's chat
  endpoint already returns (`REQ-SB-33`'s honest-uncertainty grounding
  path, agent-agnostic by construction, confirmed by this project's own
  prior `REQ-SB-37-US-01`/`ADR-030` finding that no per-agent branching
  exists anywhere in this call path) — no different behavior gated by the
  Trigger value.
- **[REQ-SB-46-US-01-AC-10]** PASS (full walkthrough). Fresh wizard, empty
  Name, clicked Next at Step 1: blocked (reconfirms `T02`'s own result as
  part of the end-to-end chain). Advanced correctly through Steps 1-3 for
  a Worker (name, scope, section, 1 Skill), reached Step 4 with all
  required fields present. Confirmed `GET /agents` count was UNCHANGED
  immediately before clicking Create (no partial/broken agent exists
  mid-flow at any point). Clicked `wizard-step4-create`: succeeded (modal
  closed, no spurious block), and the new agent was confirmed present
  afterward.
- **[REQ-SB-46-US-01-AC-11]** PASS. Entered a Name + Description at Step
  1 for an Expert-type draft, closed via `wizard-modal-close` before
  clicking Create — a `window.fetch` spy confirmed ZERO `POST /agents`
  calls fired. Reopened the wizard via the FAB: Step 1 rendered with Name
  empty, Type reset to its default (`expert`), Description empty — the
  discarded draft was not restored, confirming `T01`'s conditional-mount
  mechanism holds now that real field state exists.

**Visual check (screenshots, not just DOM assertions) — headless-Edge CDP
screenshots of Step 1 (Expert, default) and Step 2 (Producer, Working
mode + Purpose + Output Skill radios) reviewed directly:** a centered,
visually distinct modal over a dimmed Agents Map backdrop, a clean 4-circle
step bar with connector lines and a green-accent glow on the current step
(matching this codebase's own `--color-accent`/`color-mix` token
language, not a new design system), the FAB visible bottom-right behind
the modal. No layout breakage, no unstyled/raw HTML appearance.

All 11 of `REQ-SB-46-US-01`'s locked ACs (`AC-01` through `AC-11`) are now
verified live across `T01`-`T05`. `gate: flagged` — the disclosed
sequencing note (shared with `T02`-`T04`) plus this task's own Expert-
Skills-grant judgement call, both for human spot-check; neither is an
escalation.
