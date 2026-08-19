---
id: REQ-SB-37-US-03
title: Agent Creation Wizard — the Producer-type flow (Purpose + output action)
requirement_ids: [REQ-SB-37]
requirement_section: "REQ-SB-37: Agent Creation Wizard"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-031 created at /plan-tasks step 1) — carried forward, does not halt: the human reviews ADR-031 and this story's tasks together. Decomposer pass (2026-08-13) found no additional MUST-FLAG trigger of its own — all 6 ACs locked, depends_on acyclic, every locked AC has a tagged verification step."
sprint: SPRINT-034
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-37-US-03 — Agent Creation Wizard — the Producer-type flow

## Story

**As a** Second Brain user
**I want** to create a new Producer-type agent from within the app —
giving it a Purpose and a way to act on what it produces — without editing
source code
**So that** I can add a new agent whose job is to produce and act on
output (e.g. write results somewhere), the same way I can already create an
Expert or a Worker, instead of needing a code change every time

## Context

- **New sibling of `REQ-SB-37-US-01`**, created by this same re-spec pass
  as part of a three-way split of the rewritten `REQ-SB-37: Agent Creation
  Wizard`. See `REQ-SB-37-US-01`'s own Context for the full split rationale
  and `ESCALATIONS.md` → `ESC-020`'s follow-up note.

- PRD: `Documentation/PRD.md` → *REQ-SB-37: Agent Creation Wizard* — "a
  **Producer** is configured with a Purpose and an output action (what it
  does with what it produces)." **Acceptance (the Producer-relevant
  clause):** "the user can create a new agent from within the app... via a
  wizard whose fields depend on the chosen Type (...Producer: a Purpose + an
  output action)."

- **PRD breadcrumb (2026-08-13, operator-directed), cited verbatim, not
  re-decided here:** "3. Producers Need to have a Purpose and then do
  something with [it]." The PRD's own body text is explicit that the exact
  mechanical shape of "an output action" is **genuinely still open, not
  decided**: "the exact Producer 'output action' shape — is this also a
  Skill (write to a Section, mirroring the already-shipped
  Worker/capture-pipeline pattern), or something else... Left to `/spec`."

- **Genuinely NOT resolved here — the output-action mechanism (per
  Pipeline.md MUST-FLAG trigger 8, multiple equally-valid readings, flagged
  rather than guessed):**
  - Reading A: the output action is itself a Skill — the same unification
    `REQ-SB-39` establishes for a Worker's tools — meaning a Producer's
    "do something with it" step is really a Skill-grant step wearing a
    different label (e.g. a Skill that writes a structured result to a
    Section, mirroring the capture-pipeline pattern `REQ-SB-07`/`08`/`09`
    already established for Workers).
  - Reading B: the output action is a materially different concept — not a
    grantable capability at all, but a configuration of *where/how* a
    Producer's own output gets delivered (e.g. a target Section + a write
    mode), closer to a destination setting than an invocable tool.
  - Both readings are internally consistent with the PRD's own wording and
    neither is preferred by the breadcrumb, which names the fork explicitly
    without resolving it. Picking one here would be exactly the kind of
    guess the analyst is required to flag instead of make. This is a
    genuine human/architect decision, most naturally made once
    `REQ-SB-39`'s own Skills model is real and the architect can see
    concretely which reading composes more cleanly with it.
  - **Because of this fork, this story's Acceptance Criteria below cover
    only the Purpose + Section half of Producer creation** — the part the
    PRD's own text states plainly. The output-action step itself is
    deliberately left unspecced pending the fork's resolution (see
    Non-Goals) — writing Gherkin against an undecided mechanism would
    misrepresent the requirement as settled when it is not.

- **Why this story is also hard-blocked on BOTH halves of `REQ-SB-39`
  regardless of which output-action reading is eventually chosen (resolved
  here, by direct reasoning, not a guess):** under Reading A, the
  dependency is direct (a Skill-grant step needs the unified catalog,
  exactly as `REQ-SB-37-US-02`'s Worker step does). Under Reading B, a
  "write mode" configuration still needs somewhere real and mutating to
  target — and every currently-mutating write path in this codebase
  (`rebuild_person_note`, `run_capture_now`) is itself mid-migration to
  Skills under `REQ-SB-39-US-02`. Either reading composes on top of
  `REQ-SB-39`'s unified model, not around it — so this story cannot progress
  regardless of which fork the architect eventually picks. Both
  `REQ-SB-39-US-01` and `REQ-SB-39-US-02`'s own Dependencies sections name
  this story (corrected from the stale `REQ-SB-37-US-01` reference — see
  `REQ-SB-37-US-01`'s own housekeeping edit).

- **Resolved here, by direct code inspection (not a guess):** Producer is
  one of the three existing agent-type values, matching the Agents Map's
  Producer ring.

## Acceptance Criteria

<!-- Decomposer pass, 2026-08-13: analyst's original untagged Gherkin
(Purpose + Section only) tightened for buildability and amended per
ADR-031's own point 5 direction — Scenario 2 now names the concrete
single output-Skill grant, and a new Scenario 5 covers the honest
rejection of a missing output Skill (mirroring REQ-SB-37-US-02-AC-04's own
multi-field validation pattern) — then all 6 scenarios locked with
sequential AC-IDs (REQ-SB-37-US-03-AC-01..06). All 6 ACs are locked (no
non-locked exception used). -->

### Scenario 1: Selecting the Producer type shows Producer-specific fields

```gherkin
Given the user is on the wizard's type-selection step (REQ-SB-37-US-01)
When the user selects the Producer type
Then the wizard shows a field for Purpose, a single-select control for
    exactly one output Skill (not Worker's multi-select checkbox list),
    and a Section picker
  And it does not show Expert's Domain field or Worker's Skills
    multi-select/Vault-Scope fields anywhere in the mounted step
```
<!-- AC-ID: REQ-SB-37-US-03-AC-01 -->

### Scenario 2: Creating a Producer agent with a Purpose, an output Skill, and a Section

```gherkin
Given the user is on the Producer-type wizard step
  And at least one output Skill is registered in the unified Skills
    catalog (REQ-SB-39), e.g. the write-to-vault-draft placeholder Skill
When the user enters a name, a Purpose, selects exactly one output Skill,
    selects a Section, and submits
Then a new Producer-type agent is created with that name and Purpose
  And the selected output Skill is granted to it via a single Skills-grant
    call — the same underlying mechanism a Worker's own Skills grant uses,
    called at most once
  And the agent is assigned to the chosen Section
  And no source-code change was required to create it
```
<!-- AC-ID: REQ-SB-37-US-03-AC-02 -->

### Scenario 3: The new Producer agent appears immediately on the Agents Map

```gherkin
Given the user has just created a Producer agent
When the user views the Agents Map
Then the new agent appears alongside existing agents, in its assigned
    Section and on the Producer ring
  And no reload or restart of the app is required for it to appear
```
<!-- AC-ID: REQ-SB-37-US-03-AC-03 -->

### Scenario 4: Creating a Producer agent without a required field is rejected honestly

```gherkin
Given the user is on the Producer-type wizard step
When the user submits without providing a name, a Purpose, an output
    Skill, or a Section (any one or more missing)
Then the agent is not created and no create/grant/assignment call is
    issued
  And the user sees a clear, honest message naming every missing field
  And no partial or broken agent appears anywhere, including the Agents Map
```
<!-- AC-ID: REQ-SB-37-US-03-AC-04 -->

### Scenario 5: Creating a Producer agent with every other field present but no output Skill selected is rejected honestly

```gherkin
Given the user is on the Producer-type wizard step, with a name, a
    Purpose, and a Section all provided
When the user submits without selecting an output Skill
Then the agent is not created and no create/grant/assignment call is
    issued
  And the user sees a clear, honest message specifically naming the
    missing output Skill
  And no partial or broken agent appears anywhere, including the Agents Map
```
<!-- AC-ID: REQ-SB-37-US-03-AC-05 -->

### Scenario 6: A newly created Producer agent works like any other agent afterward

```gherkin
Given the user has created a Producer agent with a Purpose, a granted
    output Skill, and a Section
When the user opens that agent's Chat and Communication History tabs
Then both work the same way they already do for an existing, built-in
    agent — no second-class/read-only distinction anywhere in either
```
<!-- AC-ID: REQ-SB-37-US-03-AC-06 -->

## Affected Screens

- `html-prototype/agents-map.html` — needs the Producer-type wizard step
  (Purpose field + Section picker; the output-action portion is explicitly
  not designed here — see Non-Goals). **No approved prototype coverage
  anywhere.**

## Dependencies

- **Hard prerequisite:** `REQ-SB-37-US-01` — this story extends that
  story's own wizard shell/type-selector.
- **Hard prerequisite (both, not either):** `REQ-SB-39-US-01` and
  `REQ-SB-39-US-02` — see Context; either output-action reading composes on
  top of the unified capability model.
- **Not blocked by (already satisfied):** `REQ-SB-18-US-01` (Section,
  Done).
- **External:** none new.

## Constraints

- **Resolved by `ADR-031` — no longer open (superseding this Constraint's
  own prior "Purpose + Section only" framing):** the output-action
  mechanism is a granted Skill, single-select at creation. Output-Skill
  grants at creation must use the exact same grant mechanism `REQ-SB-39`'s
  unified model establishes for any other agent — no parallel,
  Producer-specific capability mechanism.
- Purpose is stored via `create_agent`'s existing `settings` kv-list —
  `[{"key": "Purpose", "value": purpose}]` — mirroring Expert's Domain
  exactly (`ADR-031` point 3), not a new field on the agent record.
- The output-Skill step is a single-select (at most one grant call at
  creation) — not Worker's multi-select; a human can still grant a second
  Skill later via `AgentDetailPanel.tsx`'s existing, unrestricted
  grant/revoke control (`ADR-031` point 1).
- A Producer agent created by this story's own scope has a Purpose, a
  granted output Skill, and a Section — but the granted `write-to-vault-
  draft` Skill is itself an honest-unavailable stub (no real write handler
  built this pass); this is an honest, disclosed intermediate state, not a
  silently-dropped requirement.

## Implementation Tasks

| Task | Title | Depends On |
|---|---|---|
| [[REQ-SB-37-US-03-T01]] | `skill_tools.py`/`skill_registry.py` — `write-to-vault-draft` placeholder output Skill (`mutates: True`) | `REQ-SB-39-US-01-T01`, `REQ-SB-39-US-01-T02`, `REQ-SB-39-US-02-T01` |
| [[REQ-SB-37-US-03-T02]] | `agents_router.py` — `POST /agents` `type` check extended to accept `"producer"` (Purpose via `settings`, required) | `REQ-SB-37-US-02-T01`, `REQ-SB-37-US-03-T01` |
| [[REQ-SB-37-US-03-T03]] | `CreateAgentWizard.tsx` — new Producer step (Purpose field + single-select output Skill + Section picker), sequential three-call sequence, client-side validate-before-any-call | `REQ-SB-37-US-03-T02`, `REQ-SB-37-US-02-T02`, `REQ-SB-39-US-01-T09` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Expert-type and Worker-type wizard flows** — `REQ-SB-37-US-01` and
  `REQ-SB-37-US-02` respectively.
- **A real write-to-vault handler** — the seeded `write-to-vault-draft`
  Skill is an honest-unavailable stub only (`ADR-031` point 2); building a
  real write path is not this story's scope.
- **Building `REQ-SB-39`'s own unified capability model** — this story only
  consumes it once built.
- **Granting a Producer a second output Skill after creation** — always
  possible via `AgentDetailPanel.tsx`'s existing, unrestricted grant/revoke
  control, but not part of this story's own creation-flow scope.

## Notes

**Prototype parity (agents-map.html):** no region of the approved
prototype covers a Producer wizard step of any kind — **net-new design
needed**, and cannot be meaningfully designed until the output-action fork
is resolved (a Purpose-only screen would need redesigning the moment the
output-action step is added).

**Why this is flagged, not cleared:**

1. **Multiple equally-valid readings of the output-action shape** (Pipeline.md
   MUST-FLAG trigger 8) — the PRD's own text names this fork explicitly
   without resolving it; guessing either reading would risk building the
   wrong mechanism.
2. **Genuine cross-story dependency** — hard-blocked on `REQ-SB-39-US-01`
   and `REQ-SB-39-US-02`, neither built.
3. **Net-new-design-needed.**

Because of (1), even once `REQ-SB-39` ships, this story's own output-action
half likely needs a small follow-on story (or an amendment here, since it
has not yet reached `Done`) once a human/architect decision resolves the
fork — recorded here so it is not lost.

gate: flagged 2026-08-13, gate_reason: unclear-requirement (the output-action
shape is a genuine, PRD-acknowledged open fork) + new-dependency
(`REQ-SB-39-US-01` + `REQ-SB-39-US-02`, neither built) + net-new-design-needed.
`REQ-SB-37` itself is finalised PRD text — the flag is about the open
mechanism fork and unbuilt prerequisites, not about the requirement's own
finalization state.

---

## Architect pass (2026-08-13) — `ADR-031`, resolves the output-action fork

**The fork above is resolved — operator-directed, relayed for architecture
record, not re-derived here:** Reading A. A Producer's output action is a
granted Skill — the exact same mechanism a Worker uses for its tools, not a
separate destination/write-mode concept. Full reasoning, alternatives, and
consequences: `Implementation/Architecture/ADR.md` → `ADR-031`.

**Architecture scope: §"Agent Creation Wizard — entry point, type selector,
Expert-type flow" → "Amendment — Producer-type flow (REQ-SB-37-US-03,
ADR-031)", §"Amendment — Worker-type flow (REQ-SB-37-US-02, no new ADR)"
(the Skills-grant call pattern this story's own output-Skill step reuses
verbatim)** — the coder is bounded to these two sections of
`Implementation/Architecture/architecture.md`.

**Key decisions, by direct reasoning against the real code (not assumed):**

1. **Output-Skill cardinality: single-select, not multi-select.** The
   wizard's Skills-grant step for a Producer offers exactly one output
   Skill (one `POST /agents/{agent_id}/skills/{skill_id}` call at most),
   not Worker's checkbox multi-select — the PRD's own consistently singular
   phrasing ("an output action") and a Producer's conceptual identity (one
   Purpose paired with one way of acting on its output, unlike a Worker's
   open toolbox) drove this. Not a data-model cap — `AgentDetailPanel.tsx`'s
   existing grant/revoke control can still add a second Skill to a Producer
   later, unrestricted, same as any agent.
2. **A minimal placeholder output Skill, `write-to-vault-draft`, is
   seeded** into `skill_tools.SKILLS` (`"mutates": True`, honest-
   unavailable stub, mirrors `diagram-understanding`'s exact precedent) —
   confirmed by direct reading of the real (and `ADR-028`/`ADR-029`-planned)
   catalog that **zero** existing or already-planned Skill is a plausible
   output/destination Skill; without seeding one, the operator's own
   directed Skills-grant step would have nothing to render or verify
   against. This is scaffolding an honestly-labeled mechanism, not
   fabrication — consistent with this codebase's honest-empty-over-
   fabrication standing pattern, not a violation of it.
3. **Purpose field origin: this story introduces it, via the existing
   `create_agent` `settings` kv-list — `[{"key": "Purpose", "value":
   purpose}]`, mirroring Expert's Domain exactly.** Confirmed by direct
   reading of `agent_registry.py` and `REQ-SB-41-US-01`'s own Context (which
   independently found "no dedicated purpose/description field exists
   anywhere") that no Purpose field exists anywhere yet. This story does
   **not** depend on `REQ-SB-41-US-01` landing first — that story remains
   `Draft`/unbuilt and its own "Purpose data source" question stays open for
   its own future `/plan-tasks` pass; this ADR only settles where *this
   story's own* Producer Purpose value lives, using the exact composition
   `ADR-030`'s own Consequences section already anticipated.
4. **A real, named gap between the now-resolved architecture and this
   story's own current Acceptance Criteria:** Scenarios 1–5, as specced,
   cover only Purpose + Section — they predate this fork's resolution and
   do not include a Scenario for granting the output Skill. Per this
   story's own Notes above (anticipating "an amendment here, since it has
   not yet reached `Done`") and `ADR-031` point 5, **the decomposer is
   directed to amend Scenario 2 and add a missing-output-Skill rejection
   Scenario** as part of locking this story's ACs, rather than routing this
   back through a fresh `/spec` pass — the mechanism (single grant call, one
   seeded catalog entry) is fully specified in `ADR-031` and above; whether
   the output-Skill grant is required or optional at submit time is left to
   the decomposer's own tightening latitude.

**Gating:** `gate: flagged` — trigger-3 (an ADR, `ADR-031`, was created).
This does **not** halt the decomposer; it proceeds so the human reviews
`ADR-031` and the resulting/amended tasks together in one pass, per
Pipeline.md's own "review the ADR and the tasks together" framing. See
`REVIEW-QUEUE.md`.

---

## Decomposer pass (2026-08-13) — `/plan-tasks` step 2

**Scenarios amended per `ADR-031` point 5, then all 6 locked.** Scenario 2
(the scenario that references the output action — the create scenario) is
amended to name the concrete single output-Skill grant (one Skills-grant
call, at most one, alongside Purpose and Section). A new Scenario 5 is
added for the honest rejection of a Producer creation attempt with every
other field present but no output Skill selected, mirroring
`REQ-SB-37-US-02-AC-04`'s own multi-field validation pattern (validate
client-side before any call, name exactly what's missing, no partial agent
created). Scenario 4 (the general missing-field scenario) is also widened
to include the output Skill among the fields that can be missing, so the
two scenarios together cover both "several fields missing at once" and
"only the output Skill missing" honestly. **The output-Skill grant is
decided to be required at submit time** (not optional) — a Producer with
no output Skill has no way to act on what it produces, which would
contradict the PRD's own framing of a Producer's identity ("a Purpose and
an output action"); this is the decomposer's own tightening latitude per
`ADR-031` point 5's explicit invitation. All 6 scenarios locked as
`REQ-SB-37-US-03-AC-01`..`AC-06` — no non-locked exception used.

**Three flat-root task files created**, one per distinct file-group named
in the architect's own composition:

- `REQ-SB-37-US-03-T01` (backend) — `skill_tools.py`/`skill_registry.py`:
  seeds the `write-to-vault-draft` placeholder Skill (`ADR-031` point 2).
  `depends_on` `REQ-SB-39-US-01-T01`/`T02` (the `"mutates"` field +
  `_SKILL_HANDLERS` dispatch pattern this task's own new entry reuses) and
  `REQ-SB-39-US-02-T01` (the two-axis working-mode gate this genuinely
  mutating entry must already be gated by, per `ADR-031`'s own claim,
  verified live in this task's own Tests).
- `REQ-SB-37-US-03-T02` (backend) — `agents_router.py`: extends
  `POST /agents`'s `type` dispatch with a third, `"producer"` branch
  (Purpose via `settings`, required non-blank), per `ADR-031` points 1/3/4.
  `depends_on` `REQ-SB-37-US-02-T01` (the real current `POST /agents`
  dispatch shape this task extends — reconciled against the REAL file at
  build time, not the stale Worker-only sample) and `REQ-SB-37-US-03-T01`
  (needs a real, selectable output Skill to grant in its own live
  verification).
- `REQ-SB-37-US-03-T03` (frontend) — `CreateAgentWizard.tsx`: the Producer
  step (Purpose + single-select output Skill + Section), sequential
  three-call sequence, validate-before-any-call. `depends_on`
  `REQ-SB-37-US-03-T02` (the backend endpoint this step calls),
  `REQ-SB-37-US-02-T02` (the sibling Worker step this file already carries
  — reconciled against the REAL current `CreateAgentWizard.tsx`, not a
  stale sample), and `REQ-SB-39-US-01-T09` (`skillsApiClient.ts` —
  `fetchSkills`/`grantAgentSkill`, reused verbatim).

Zero cycles — verified by direct inspection of every named task's own
`depends_on` (none of `REQ-SB-37-US-03-T01`/`T02`/`T03` is depended on by
any task it itself depends on, directly or transitively).

**AC → verification mapping (every locked AC has ≥1 tagged step):**
`AC-01` (structural — exact field set, single-select control, no
Expert/Worker fields), `AC-04` (general missing-field rejection), and
`AC-05` (missing-output-Skill-only rejection) each need the real wizard UI
— tagged in `T03` only. `AC-02` (creation + output-Skill grant + Section,
the full mechanism), `AC-03` (appears on the Agents Map), and `AC-06`
(Chat/History behave identically) each have a Given clause that only
requires "a Producer agent has just been created," not specifically "via
the wizard" — verified backend-layer-first in `T02`, against the real
`POST /agents` mechanism the wizard itself will call, mirroring
`REQ-SB-37-US-01-T03`/`REQ-SB-37-US-02-T01`'s own placement precedent
exactly.

**No additional MUST-FLAG trigger fired this pass** beyond the
already-carried-forward trigger-3 (`ADR-031`, created by the architect,
not this step): no new material assumption (the output-Skill-required
decision is disclosed tightening latitude the architect's own `ADR-031`
point 5 explicitly invited, not a gap-filling guess); no `Draft`/
unfinalised requirement relied on (`REQ-SB-39-US-01`/`-US-02` are both
`Ready` with real task files); no new ADR created/changed by this step; no
`ESCALATIONS.md` entry needed; no oversized task (3 tasks, S, matches the
2-3-task shape of this story's already-`Ready` siblings); every locked AC
maps to a real, observable HTTP/DOM outcome and is verifiable; no
contradictory inputs; the one genuine judgment call (output-Skill required
vs. optional) is recorded above with its reasoning, not left silent.

`status: Draft → Ready`, `gate` stays `flagged` (trigger-3, `ADR-031`,
carried forward — the human reviews the ADR and this story's now-locked
ACs/tasks together in one pass; this does not block `/plan-sprints` from
picking up this story). Nothing new written to `REVIEW-QUEUE.md` or
`ESCALATIONS.md` this pass — the existing `REVIEW-QUEUE.md` entry for
`ADR-031` already covers this story's own flagged state.

**Coder pass, 2026-08-14 (`/implement-sprint SPRINT-034`).** All three
tasks (`T01`, `T02`, `T03`) built and verified live end-to-end against all
6 locked ACs, in the story's own dependency order (the placeholder
`write-to-vault-draft` Skill landed first, then the backend `POST /agents`
Producer branch, then the wizard's own Producer step) — see each task's
own Implementation Log for full detail. A real Producer agent
(`vault-scribe`) was created end-to-end through the actual wizard UI, with
a Purpose, a single granted output Skill, and a Section, and independently
confirmed via `GET /agents/vault-scribe` + `GET /agents/vault-scribe/
skills` to match the UI's own claimed outcome exactly. `status: Ready →
Done`. `gate` stays `flagged` (trigger-3, `ADR-031`, carried forward from
the architect/decomposer passes — the human still reviews `ADR-031`
itself; nothing new this coder pass requires a fresh flag).
