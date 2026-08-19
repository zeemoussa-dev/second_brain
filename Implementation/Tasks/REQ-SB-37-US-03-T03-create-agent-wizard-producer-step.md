---
id: REQ-SB-37-US-03-T03
title: CreateAgentWizard.tsx — new Producer step (Purpose field + single-select output Skill + Section picker), sequential three-call sequence, validate-before-any-call
parent_story: REQ-SB-37-US-03
requirement_id: REQ-SB-37
type: frontend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-031 created at /plan-tasks step 1) — carried forward, does not halt"
phase: P1
depends_on: [REQ-SB-37-US-03-T02, REQ-SB-37-US-02-T02, REQ-SB-39-US-01-T09]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-37-US-03-T03 — `CreateAgentWizard.tsx` — Producer step

## Parent Story

- Story: [[REQ-SB-37-US-03]] — `../UserStories/REQ-SB-37-US-03-agent-creation-producer-flow.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-37 *Agent Creation Wizard*

---

## Objective

Add a Producer step to the already-`Done` `CreateAgentWizard.tsx` (`step`
state gains `'producer'`), enabling the previously-`disabled` Producer type
button, rendering a Purpose field + a **single-select** output-Skill
control (radio-equivalent, not Worker's checkbox multi-select) + a Section
picker, and — on submit, only once name + Purpose + a selected output
Skill + a Section are all present — issuing the wizard's own sequential
three-call sequence: `POST /agents` (type `"producer"`) → exactly one
`POST /agents/{agent_id}/skills/{skill_id}` for the selected output Skill →
`PATCH /agents/{agent_id}` carrying `section_id` alone (never combined with
another field — a Producer has no Scope-equivalent field to combine with
Section, per `ADR-031` point 4).

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-37-US-03-T02` has landed `POST /agents` accepting `type ==
  "producer"` (`purpose` required, non-blank).
- `REQ-SB-37-US-02-T02`'s real, live `CreateAgentWizard.tsx` — `step` state
  (`'type' | 'expert' | 'worker'`), the type-selector row with
  `agent-type-producer` rendered `disabled`, the Expert/Worker steps' own
  Section `<select>`, and `handleWorkerSubmit`'s own
  validate-before-any-call pattern this task mirrors for the Producer step.
- `REQ-SB-39-US-01-T09`'s real, live
  `src/frontend/src/features/agents-map/skillsApiClient.ts` —
  `fetchSkills(): Promise<SkillSummary[]>` (`GET /skills`) and
  `grantAgentSkill(agentId, skillId): Promise<{granted: boolean}>`
  (`POST /agents/{agentId}/skills/{skillId}`) — reused verbatim, no new
  Skills fetch/grant client code written by this task.
- `REQ-SB-37-US-03-T01`'s real `write-to-vault-draft` catalog entry —
  needed so this step's output-Skill single-select is genuinely
  meaningful (not an empty control) and so this task's own live
  verification has a real Skill to select.

**After / Outputs:**
- `agentsApiClient.ts`'s `CreateAgentBody` gains `purpose?: string` (the
  `type` union already includes `'producer'`, unchanged since `T04`).
- `CreateAgentWizard.tsx`'s `step` state gains `'producer'`. Its
  type-selector row's Producer button becomes enabled and calls
  `selectType('producer')`.
- A new Producer step renders: a Name field (common to every type), a
  Purpose field, a single-select output-Skill control (radio inputs, at
  most one selectable at a time) sourced from `fetchSkills()`, and the
  Section `<select>` reused verbatim from the Expert/Worker steps.
- Submitting with all 4 required fields present (name, Purpose, a selected
  output Skill, a Section) issues, in order: `createAgent({name, type:
  'producer', purpose})` → exactly one `grantAgentSkill(agentId,
  selectedOutputSkillId)` → `updateAgentAssignment(agentId, {section_id})`
  (section alone, sequential — never combined with another field the way
  Worker's step combines `section_id` + `scope`). Submitting with any of
  the 4 missing issues NO call at all and shows an honest, specific error
  naming every missing field.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — read the REAL
  current file first (actively extended by multiple sibling tasks). Add
  `purpose` to `CreateAgentBody`:
  ```typescript
  export interface CreateAgentBody {
    name: string;
    type: 'worker' | 'expert' | 'producer';
    domain?: string;
    purpose?: string;
  }
  ```

- `src/frontend/src/features/agents-map/CreateAgentWizard.tsx` — read the
  REAL current file first. Extend the `step` union and add the Producer
  branch:
  ```tsx
  type Step = 'type' | 'expert' | 'worker' | 'producer';
  // (extend the existing useState<Step>('type') union)

  const [outputSkills, setOutputSkills] = useState<SkillSummary[] | null>(null);
  const [selectedOutputSkillId, setSelectedOutputSkillId] = useState('');
  const [producerName, setProducerName] = useState('');
  const [purposeDraft, setPurposeDraft] = useState('');
  const [producerSectionId, setProducerSectionId] = useState('');
  const [producerError, setProducerError] = useState<string | null>(null);
  const [producerSubmitting, setProducerSubmitting] = useState(false);

  useEffect(() => {
    fetchSkills().then(setOutputSkills);
  }, []);
  ```
  (`fetchSkills`/`SkillSummary` are already imported from `./skillsApiClient`
  by `REQ-SB-37-US-02-T02`'s own Worker-step import — reuse it, do not add
  a second import line; the Worker step's own `skills`/`selectedSkillIds`
  state stays untouched, this task's own `outputSkills`/
  `selectedOutputSkillId` are separate, single-select state.)

  Extend `selectType` so `'producer'` is a real branch:
  ```tsx
  function selectType(type: AgentType) {
    if (type === 'expert') {
      setStep('expert');
      setError(null);
    } else if (type === 'worker') {
      setStep('worker');
      setWorkerError(null);
    } else if (type === 'producer') {
      setStep('producer');
      setProducerError(null);
    }
  }
  ```

  Submit handler — validate every one of the 4 required fields BEFORE any
  call fires, mirroring `T02`'s own `handleWorkerSubmit` pattern exactly:
  ```tsx
  async function handleProducerSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmedName = producerName.trim();
    const trimmedPurpose = purposeDraft.trim();
    const missing: string[] = [];
    if (!trimmedName) missing.push('a name');
    if (!trimmedPurpose) missing.push('a Purpose');
    if (!selectedOutputSkillId) missing.push('an output Skill');
    if (!producerSectionId) missing.push('a Section');
    if (missing.length > 0) {
      setProducerError(`Missing ${missing.join(', ')} — the agent was not created.`);
      return;
    }
    setProducerError(null);
    setProducerSubmitting(true);
    try {
      const created = await createAgent({ name: trimmedName, type: 'producer', purpose: trimmedPurpose });
      await grantAgentSkill(created.id, selectedOutputSkillId);
      const updated = await updateAgentAssignment(created.id, { section_id: producerSectionId });
      setProducerName('');
      setPurposeDraft('');
      setSelectedOutputSkillId('');
      setProducerSectionId('');
      setStep('type');
      onCreated(updated);
    } finally {
      setProducerSubmitting(false);
    }
  }
  ```
  Enable the Producer type button (remove `disabled`/its "Coming soon"
  title) and wire it to `selectType('producer')`:
  ```tsx
  <button
    type="button"
    className="btn"
    data-testid="agent-type-producer"
    onClick={() => selectType('producer')}
  >
    Producer
  </button>
  ```
  Add the Producer step JSX, alongside the existing `step === 'worker'`
  block:
  ```tsx
  {step === 'producer' && (
    <form onSubmit={handleProducerSubmit} data-testid="producer-step" className="item-row-actions">
      {producerError && (
        <p className="text-muted" data-testid="create-agent-producer-error">
          <span className="badge badge-danger">Can't create agent</span> {producerError}
        </p>
      )}
      <label className="text-muted" htmlFor="producerName">Name</label>
      <input
        id="producerName"
        className="input"
        data-testid="producer-name-input"
        value={producerName}
        onChange={(event) => setProducerName(event.target.value)}
      />
      <label className="text-muted" htmlFor="producerPurpose">Purpose</label>
      <textarea
        id="producerPurpose"
        className="input"
        data-testid="producer-purpose-input"
        value={purposeDraft}
        onChange={(event) => setPurposeDraft(event.target.value)}
      />
      <span className="kv-key" data-testid="producer-output-skill-label">Output Skill</span>
      <div data-testid="producer-output-skill-list">
        {outputSkills?.map((skill) => (
          <label key={skill.id} className="text-muted">
            <input
              type="radio"
              name="producerOutputSkill"
              data-testid={`producer-output-skill-radio-${skill.id}`}
              checked={selectedOutputSkillId === skill.id}
              onChange={() => setSelectedOutputSkillId(skill.id)}
            />
            {skill.name}
          </label>
        ))}
      </div>
      <label className="text-muted" htmlFor="producerSection">Section</label>
      <select
        id="producerSection"
        className="input"
        data-testid="producer-section-select"
        value={producerSectionId}
        onChange={(event) => setProducerSectionId(event.target.value)}
      >
        <option value="">Choose a Section…</option>
        {sections?.map((section) => (
          <option key={section.id} value={section.id}>{section.name}</option>
        ))}
      </select>
      <button type="submit" className="btn btn-primary" data-testid="create-agent-producer-submit" disabled={producerSubmitting}>
        Create agent
      </button>
    </form>
  )}
  ```

---

## Constraints

- Inherits from parent story, `ADR-031`, and `architecture.md`'s
  "Amendment — Producer-type flow" in full.
- The output-Skill control MUST be single-select (radio-equivalent, at
  most one checked at a time) — NEVER checkboxes/multi-select — this is
  the one deliberate structural distinction from Worker's own Skills step
  (`ADR-031` point 1's cardinality reasoning).
- The submit sequence MUST be, in order: `createAgent` → exactly one
  `grantAgentSkill` call (for the single selected output Skill) →
  `updateAgentAssignment` carrying `section_id` **alone** — never combined
  with any other field the way Worker's own combined `PATCH` is (a
  Producer has no Scope-equivalent field to combine with Section,
  `ADR-031` point 4).
- Submitting the Producer step with ANY of name/Purpose/output
  Skill/Section missing must NOT call `createAgent`, `grantAgentSkill`, or
  `updateAgentAssignment` at all — the error message must name every
  missing field, and no partial/broken agent may be created (mirrors
  `T02`'s own AC-04 precedent exactly).
- The Producer type button must become genuinely, functionally selectable
  this task (no longer `disabled`).
- Must reuse `skillsApiClient.ts`'s `fetchSkills`/`grantAgentSkill`
  verbatim — no new Skills fetch/grant HTTP call written directly in this
  file, no new Skills-related backend endpoint.
- Must reuse the Expert/Worker steps' own `sections` state/
  `fetchSections()` call and Section `<select>` shape verbatim — do not add
  a second, duplicate `fetchSections()` call or a divergent
  Section-rendering shape.
- `AgentDetailPanel.tsx`/`AgentsMapCanvas.tsx` must not be modified —
  AC-02/AC-03/AC-06 are already verified in `T02` against the real,
  unmodified downstream surfaces.
- Do not add any interactive element to `AgentsMapCanvas.tsx` — the entry
  affordance stays in Settings only, unchanged.
- Reuse `.card`/`.btn`/`.btn-primary`/`.input`/`.item-row-actions`/
  `.badge`/`.badge-danger`/`.kv-key`/`.text-muted` class names verbatim
  (`ADR-010`) — no new CSS file/rule needed; port any missing class from
  `html-prototype/styles.css` verbatim rather than inventing new styling.
- `npm run build` / `npx tsc --noEmit` must stay clean.

---

## Tests

<!-- AC-01/AC-04/AC-05 each need a real, reachable Producer wizard step to
drive them through — this is the only task with one. AC-01 is a structural
AC (DOM structure/control-type presence, not computed CSS). -->

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`;
delete any leftover `.second-brain/agents_registry.json`/
`agent_skills.json` first; browser preview / headless-Chrome-via-CDP per
this project's established technique):

1. **[REQ-SB-37-US-03-AC-01]** Load `/settings`, open the Create Agent
   affordance, click `[data-testid="agent-type-producer"]`. Confirm it is
   NOT rendered `disabled` and the click actually mounts
   `[data-testid="producer-step"]`. Confirm the mounted step contains
   exactly the Name field, `[data-testid="producer-purpose-input"]`,
   `[data-testid="producer-output-skill-list"]`, and
   `[data-testid="producer-section-select"]`. Confirm every input inside
   `[data-testid="producer-output-skill-list"]` has `type="radio"` (a
   genuine single-select, never `type="checkbox"`). Confirm a plain text
   search of the mounted Producer step's DOM for "Domain", "Skills"
   (Worker's own multi-select label), or "Vault Scope" finds nothing —
   Expert's/Worker's own fields do not appear.
2. **[REQ-SB-37-US-03-AC-04]** With the Producer step open and every field
   empty/unselected, click
   `[data-testid="create-agent-producer-submit"]`. Confirm
   `[data-testid="create-agent-producer-error"]` renders, naming all four
   missing requirements (name, a Purpose, an output Skill, a Section).
   Confirm (via the Network panel, or a `window.fetch` spy installed
   before the click) that NEITHER `POST /agents` NOR any
   `POST .../skills/...` NOR any `PATCH /agents/...` call fired. Confirm
   `GET /agents` still lists only agents that existed before this step —
   no partial/broken agent anywhere, including a fresh load of the Agents
   Map.
3. **[REQ-SB-37-US-03-AC-05]** Fill `[data-testid="producer-name-input"]`
   with "Vault Scribe" (native `HTMLInputElement.prototype.value` setter +
   synthetic `input` event, per this project's established
   React-controlled-input technique), `[data-testid="producer-purpose-
   input"]` with "Draft outbound account-plan notes for review.", and
   select a real Section from `[data-testid="producer-section-select"]` —
   but leave the output-Skill control unselected. Click
   `[data-testid="create-agent-producer-submit"]`. Confirm
   `[data-testid="create-agent-producer-error"]` renders, naming
   specifically "an output Skill" as the missing requirement (and only
   that one — name/Purpose/Section are satisfied). Confirm (Network panel)
   that neither `POST /agents` nor any `POST .../skills/...` nor any
   `PATCH /agents/...` call fired. Confirm `GET /agents` unchanged.
4. Non-AC smoke check (functional wiring, confirms the real sequential
   3-call sequence, complementing `T02`'s own backend-layer proof): with
   the same three fields from step 3 still filled, select the
   `write-to-vault-draft` radio in
   `[data-testid="producer-output-skill-list"]`. Click
   `[data-testid="create-agent-producer-submit"]`. Confirm (Network panel)
   exactly one `POST /agents` call (`type: "producer"`, `purpose` in the
   body) fired, followed by exactly one `POST .../skills/
   write-to-vault-draft` call, followed by exactly one
   `PATCH /agents/vault-scribe` call carrying ONLY `section_id` in its
   body (never combined with `scope` or any other field). Confirm
   `[data-testid="create-agent-success"]` (or the equivalent success
   surface `T02`/`REQ-SB-37-US-01-T04` already established) names "Vault
   Scribe". Confirm `GET /agents/vault-scribe` afterward shows `type:
   "producer"`, the Purpose entry in `settings`, `write-to-vault-draft`
   present in `GET /agents/vault-scribe/skills`, and the chosen Section.
5. Non-AC smoke check: reopen the Create Agent affordance after a
   successful Producer creation — confirm the Producer step's fields are
   reset (blank name/Purpose, no output Skill selected, no Section
   selected), not left showing the just-submitted values.
6. Non-AC smoke check: `npm run build` (or `npx tsc --noEmit` if `npm`
   isn't resolvable on `PATH` in this session — locate the real install
   via the registry if it recurs, per `Implementation/Learnings.md`) —
   confirm clean, zero new type errors.
7. Clean-up: delete `.second-brain/agents_registry.json` and
   `.second-brain/agent_skills.json`. Stop both dev servers.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-01** (structural) — selecting Producer renders exactly Name +
      Purpose + a single-select (radio) output-Skill control + Section; no
      Expert/Worker-specific field renders anywhere
- [ ] **AC-04** — submitting with any required field missing creates
      nothing (no API call fires of any kind), and names every missing
      field honestly
- [ ] **AC-05** — submitting with only the output Skill unselected (all
      other fields present) creates nothing, and names specifically the
      missing output Skill
- [ ] Producer type button is genuinely selectable
- [ ] Output-Skill control is single-select (radio inputs), never
      multi-select
- [ ] Submit sequence is `createAgent` → one `grantAgentSkill` → one
      `updateAgentAssignment` carrying `section_id` alone
- [ ] `AgentDetailPanel.tsx`/`AgentsMapCanvas.tsx` not modified
- [ ] `npm run build` / `tsc` clean
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `AC-02`/`AC-03`/`AC-06` — already verified in `T02` against the real
  `POST /agents` mechanism this wizard itself calls; not re-verified here.
- Any visual/pixel-polish styling beyond reusing existing `ADR-010` class
  names — no `/design` pass occurred for this net-new surface (operator
  direction, per the parent story's own Notes); a non-blocking design
  spot-check happens out-of-band, not as a locked AC.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-031` created at
`/plan-tasks` step 1) — the human reviews `ADR-031` and this task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside the rest of the story.

**Why the output-Skill control uses plain radio inputs wired to
`selectedOutputSkillId` state, not `AgentDetailPanel.tsx`'s own live
grant/revoke toggle:** this is a pre-submit wizard field (nothing exists to
grant/revoke yet — the agent doesn't exist until submit), not a
live-editing panel row; the actual grant call only fires inside
`handleProducerSubmit`, after the agent is real. `skillsApiClient.ts`'s
`grantAgentSkill` function itself is reused verbatim once submit fires —
only the UI interaction shape (single-select radio vs. Worker's
multi-select checkboxes) differs, per `ADR-031` point 1's cardinality
decision.

**Why the Section `PATCH` carries `section_id` alone, not combined with
another field the way Worker's does:** a Producer has no Vault-Scope-
equivalent field — `ADR-031` point 4's own sequential-shape decision,
mirroring `ADR-030` point 6's original Expert-only two-call shape, not
`REQ-SB-37-US-02`'s combined-`PATCH` amendment.

Full composition/sequencing reasoning: `Implementation/Architecture/
architecture.md` → "Amendment — Producer-type flow (REQ-SB-37-US-03,
ADR-031)"; `Implementation/Architecture/ADR.md` → `ADR-031`.

---

## Implementation Log

**2026-08-14, coder.** Read the REAL current `CreateAgentWizard.tsx`
first — matched the task's own `Before` description exactly (Producer
button `disabled`, `Step` already `'type' | 'expert' | 'worker'` from
`REQ-SB-37-US-02-T02`, `fetchSkills`/`SkillSummary` already imported).
Applied the task's own diff verbatim: `Step` gains `'producer'`, new
Purpose/output-Skill/Producer-name/Producer-section state (kept fully
separate from the Worker step's own `skills`/`selectedSkillIds` state, per
the task's own instruction), a second `fetchSkills()` effect into
`outputSkills`, `selectType`'s real Producer branch, `handleProducerSubmit`
(validate-before-any-call, sequential 3-call sequence with `section_id`
carried alone, never combined with another field), the enabled Producer
button, and the new Producer step JSX (radio-input single-select, not
checkboxes). `agentsApiClient.ts` gained `purpose?: string` on
`CreateAgentBody`. No other file touched.

**Verification (CDP-driven headless Edge against the real running Vite
dev server + the real backend from `T02`, same native-setter + `window.
fetch`-spy technique as `REQ-SB-37-US-02-T02`):**

- Non-AC: Producer button confirmed NOT `disabled`, click mounted
  `[data-testid="producer-step"]`.
- **AC-01 — PASS.** Mounted step contains exactly `producer-name-input`,
  `producer-purpose-input`, `producer-output-skill-list` (10 real catalog
  entries, ALL rendered as genuine `type="radio"` inputs sharing one
  `name` group — confirmed programmatically, never `checkbox`),
  `producer-section-select`. Plain-text search of the step's own
  `textContent` for "Domain"/"Skills" (Worker's own label)/"Vault Scope"
  found nothing — Expert's/Worker's own fields do not appear.
- **AC-04 — PASS.** Submitted with everything empty: error named all four
  missing requirements ("Missing a name, a Purpose, an output Skill, a
  Section..."). Zero `fetch` calls of any kind.
- **AC-05 — PASS.** Filled name/Purpose/Section, left the output-Skill
  radio group unselected, submitted: error named SPECIFICALLY "an output
  Skill" (name/Purpose/Section already satisfied, none re-listed). Zero
  `fetch` calls.
- Non-AC smoke (functional wiring): selected the `write-to-vault-draft`
  radio, submitted with all 4 fields present. Confirmed the exact spec'd
  sequential 3-call sequence: `POST /agents` (`{"name":"Vault
  Scribe","type":"producer","purpose":"Draft outbound account-plan notes
  for review."}`) → `POST /agents/vault-scribe/skills/write-to-vault-draft`
  → `PATCH /agents/vault-scribe` carrying `{"section_id":"technical"}`
  **alone** — never combined with any other field, confirming the one
  deliberate structural difference from Worker's own combined `PATCH`.
  Independently confirmed via `GET /agents/vault-scribe` (`type:
  "producer"`, Purpose in `settings`) and `GET /agents/vault-scribe/skills`
  (`write-to-vault-draft` present) — real backend state matches the UI's
  own claimed outcome. Success surface named "Vault Scribe".
- Non-AC smoke (reset): reopening the Producer step after a successful
  creation showed blank name/Purpose, no output-Skill radio checked, no
  Section selected.
- Non-AC smoke (typecheck): `tsc --noEmit` via the same located
  `node.exe` — zero output, clean.
- `AgentDetailPanel.tsx`/`AgentsMapCanvas.tsx` — confirmed untouched.

**Non-blocking observation (unchanged from `T02`'s own finding, still
out of this task's own file scope):** `CreateAgentCard.tsx`'s static copy
is now stale for BOTH Worker and Producer — still not in this task's
`## Files to Modify`, correctly left untouched; flagged for a human
follow-up edit (single-line copy change, zero ambiguity, deliberately not
absorbed into either task's own scope per the Learnings precedent for
mechanical, zero-judgment gaps outside a task's named files).

Final sprint-wide cleanup performed here (last task in the sprint's own
build order): reset `.second-brain/agents_registry.json`/
`agent_skills.json` to a clean slate; confirmed the one remaining
`pending` approval (`7e7fda92d83c`, a real background-triggered
`email-capture` record that pre-dated this session — see `MEMORY.md`'s
own prior note on this exact stray-dev-server finding) was NOT created by
any task in this sprint and was correctly left untouched, not
silently resolved. Stopped the backend dev server (specific-PID-tree
kill, including its `--multiprocessing-fork` child) at the end of this
sprint's own build order. The frontend Vite dev server was already
running before this sprint started (not started by this session) and was
left running, unmodified.

gate stays flagged (trigger-3, `ADR-031`, carried forward) — no new
MUST-FLAG trigger fired this pass.
