---
id: REQ-SB-37-US-02-T02
title: CreateAgentWizard.tsx — new Worker step (Skills multi-select + Vault Scope field + Section picker), three-call sequence, validate-before-any-call
parent_story: REQ-SB-37-US-02
requirement_id: REQ-SB-37
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-37-US-02-T01, REQ-SB-37-US-01-T04, REQ-SB-39-US-01-T09, REQ-SB-39-US-02-T03, REQ-SB-29-US-01-T05]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-37-US-02-T02 — `CreateAgentWizard.tsx` — Worker step

## Parent Story

- Story: [[REQ-SB-37-US-02]] — `../UserStories/REQ-SB-37-US-02-agent-creation-worker-flow.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-37 *Agent Creation Wizard*

---

## Objective

Add a Worker step to the already-`Done` `CreateAgentWizard.tsx`
(`step` state gains `'worker'`), enabling the previously-`disabled` Worker
type button, rendering a Skills multi-select + Vault Scope free-text field
+ Section picker, and — on submit, only once name + ≥1 Skill + non-empty
Scope + a Section are all present — issuing the wizard's own three-call
sequence: `POST /agents` (type `"worker"`) → one
`POST /agents/{agent_id}/skills/{skill_id}` per selected Skill → one
combined `PATCH /agents/{agent_id}` carrying both `section_id` and `scope`.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-37-US-02-T01` has landed `POST /agents` accepting `type ==
  "worker"` (`domain` optional).
- `REQ-SB-37-US-01-T04`'s real, live `CreateAgentWizard.tsx` — `step` state
  (`'type' | 'expert'`), the type-selector row with `agent-type-worker`
  rendered `disabled`, and the Expert step's Section `<select>` (reused
  verbatim by this task).
- `REQ-SB-39-US-01-T09`'s real, live
  `src/frontend/src/features/agents-map/skillsApiClient.ts` —
  `fetchSkills(): Promise<SkillSummary[]>` (`GET /skills`) and
  `grantAgentSkill(agentId, skillId): Promise<{granted: boolean}>`
  (`POST /agents/{agentId}/skills/{skillId}`) — reused verbatim, no new
  Skills fetch/grant client code written by this task.
- `REQ-SB-39-US-02-T03` has landed the 4 mutating Skills in the catalog
  `fetchSkills()` returns — needed so this step's Skills multi-select is
  genuinely meaningful (not just the narrow read-only catalog), per the
  parent story's own Context.
- `REQ-SB-29-US-01-T05`'s real, live `agentsApiClient.ts` —
  `AgentDetail.scope: string[]` and `updateAgentAssignment(agentId, {
  section_id?, provider_id?, keywords?, working_mode?, scope? })`.

**After / Outputs:**
- `agentsApiClient.ts`'s `createAgent`'s `CreateAgentBody.type` union
  already includes `'worker'` (it does today —
  `'worker' | 'expert' | 'producer'`, unchanged by this task);
  `CreateAgentBody.domain` becomes optional (`domain?: string`) to match
  `T01`'s backend contract.
- `CreateAgentWizard.tsx`'s `step` state gains `'worker'`. Its type-selector
  row's Worker button becomes enabled and calls `selectType('worker')`.
- A new Worker step renders: a Skills multi-select (checkboxes, sourced
  from `fetchSkills()`), a Vault Scope free-text/comma-separated field
  (mirroring `AgentDetailPanel.tsx`'s own Keywords/Vault-scope row
  interaction shape, per `REQ-SB-29-US-01-T05`'s own precedent — but a
  plain controlled `<input>` here, not an `onBlur`-commit row, since this
  is a pre-submit wizard field, not a live-editing panel row), and the
  Section `<select>` reused verbatim from the Expert step.
- Submitting with all 4 required fields present (name, ≥1 Skill, non-empty
  Scope, a Section) issues, in order: `createAgent({name, type: 'worker'})`
  → one `grantAgentSkill(agentId, skillId)` per selected Skill →
  `updateAgentAssignment(agentId, {section_id, scope})`. Submitting with
  any of the 4 missing issues NO call at all and shows an honest,
  specific error naming every missing field.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — read the REAL
  current file first (actively extended by multiple sibling tasks —
  `T04`, `REQ-SB-29-US-01-T05`, `REQ-SB-39-US-01-T09` have all landed
  edits). Change `CreateAgentBody.domain` to optional:
  ```typescript
  export interface CreateAgentBody {
    name: string;
    type: 'worker' | 'expert' | 'producer';
    domain?: string;
  }
  ```

- `src/frontend/src/features/agents-map/CreateAgentWizard.tsx` — read the
  REAL current file first. Extend the `step` union and add the Worker
  branch:
  ```tsx
  import { fetchSkills, grantAgentSkill, type SkillSummary } from './skillsApiClient';

  type Step = 'type' | 'expert' | 'worker';
  // (rename the existing `useState<'type' | 'expert'>('type')` to
  // `useState<Step>('type')`)

  const [skills, setSkills] = useState<SkillSummary[] | null>(null);
  const [selectedSkillIds, setSelectedSkillIds] = useState<string[]>([]);
  const [scopeDraft, setScopeDraft] = useState('');
  const [workerName, setWorkerName] = useState('');
  const [workerSectionId, setWorkerSectionId] = useState('');
  const [workerError, setWorkerError] = useState<string | null>(null);
  const [workerSubmitting, setWorkerSubmitting] = useState(false);

  useEffect(() => {
    fetchSkills().then(setSkills);
  }, []);
  ```
  Extend `selectType` so `'worker'` is a real branch, not the existing
  defensive no-op:
  ```tsx
  function selectType(type: AgentType) {
    if (type === 'expert') {
      setStep('expert');
      setError(null);
    } else if (type === 'worker') {
      setStep('worker');
      setWorkerError(null);
    }
    // Producer stays a defensive no-op — its own button remains disabled
    // (REQ-SB-37-US-03, not yet built).
  }
  ```
  Toggle handler for the Skills multi-select:
  ```tsx
  function toggleSkill(skillId: string) {
    setSelectedSkillIds((current) =>
      current.includes(skillId)
        ? current.filter((id) => id !== skillId)
        : [...current, skillId],
    );
  }
  ```
  Submit handler — validate every one of the 4 required fields BEFORE any
  call fires, mirroring `T04`'s own Expert-step `handleSubmit` pattern
  exactly (`ADR-030`'s own established client-validate-before-any-call
  precedent, not a new pattern):
  ```tsx
  async function handleWorkerSubmit(event: React.FormEvent) {
    event.preventDefault();
    const trimmedName = workerName.trim();
    const scope = scopeDraft
      .split(',')
      .map((entry) => entry.trim())
      .filter((entry) => entry.length > 0);
    const missing: string[] = [];
    if (!trimmedName) missing.push('a name');
    if (selectedSkillIds.length === 0) missing.push('at least one Skill');
    if (scope.length === 0) missing.push('a Vault Scope');
    if (!workerSectionId) missing.push('a Section');
    if (missing.length > 0) {
      setWorkerError(`Missing ${missing.join(', ')} — the agent was not created.`);
      return;
    }
    setWorkerError(null);
    setWorkerSubmitting(true);
    try {
      const created = await createAgent({ name: trimmedName, type: 'worker' });
      for (const skillId of selectedSkillIds) {
        await grantAgentSkill(created.id, skillId);
      }
      const updated = await updateAgentAssignment(created.id, {
        section_id: workerSectionId,
        scope,
      });
      setWorkerName('');
      setSelectedSkillIds([]);
      setScopeDraft('');
      setWorkerSectionId('');
      setStep('type');
      onCreated(updated);
    } finally {
      setWorkerSubmitting(false);
    }
  }
  ```
  Enable the Worker type button (remove `disabled`/its "Coming soon" title)
  and wire it to `selectType('worker')`:
  ```tsx
  <button
    type="button"
    className="btn"
    data-testid="agent-type-worker"
    onClick={() => selectType('worker')}
  >
    Worker
  </button>
  ```
  Add the Worker step JSX, alongside the existing `step === 'expert'`
  block:
  ```tsx
  {step === 'worker' && (
    <form onSubmit={handleWorkerSubmit} data-testid="worker-step" className="item-row-actions">
      {workerError && (
        <p className="text-muted" data-testid="create-agent-worker-error">
          <span className="badge badge-danger">Can't create agent</span> {workerError}
        </p>
      )}
      <label className="text-muted" htmlFor="workerName">Name</label>
      <input
        id="workerName"
        className="input"
        data-testid="worker-name-input"
        value={workerName}
        onChange={(event) => setWorkerName(event.target.value)}
      />
      <span className="kv-key" data-testid="worker-skills-label">Skills</span>
      <div data-testid="worker-skills-list">
        {skills?.map((skill) => (
          <label key={skill.id} className="text-muted">
            <input
              type="checkbox"
              data-testid={`worker-skill-checkbox-${skill.id}`}
              checked={selectedSkillIds.includes(skill.id)}
              onChange={() => toggleSkill(skill.id)}
            />
            {skill.name}
          </label>
        ))}
      </div>
      <label className="text-muted" htmlFor="workerScope">Vault scope</label>
      <input
        id="workerScope"
        type="text"
        className="input"
        data-testid="worker-scope-input"
        value={scopeDraft}
        onChange={(event) => setScopeDraft(event.target.value)}
        placeholder="e.g. customer/masdar, Pipeline"
      />
      <label className="text-muted" htmlFor="workerSection">Section</label>
      <select
        id="workerSection"
        className="input"
        data-testid="worker-section-select"
        value={workerSectionId}
        onChange={(event) => setWorkerSectionId(event.target.value)}
      >
        <option value="">Choose a Section…</option>
        {sections?.map((section) => (
          <option key={section.id} value={section.id}>{section.name}</option>
        ))}
      </select>
      <button type="submit" className="btn btn-primary" data-testid="create-agent-worker-submit" disabled={workerSubmitting}>
        Create agent
      </button>
    </form>
  )}
  ```

---

## Constraints

- Inherits from parent story and `architecture.md`'s "Amendment —
  Worker-type flow" in full: three calls, in order (`POST /agents` → one
  `POST .../skills/{skill_id}` per selected Skill → one combined
  `PATCH /agents/{agent_id}` carrying both `section_id` and `scope`
  together, never two separate `PATCH` calls).
- Submitting the Worker step with ANY of name/≥1 Skill/non-empty Scope/
  Section missing must NOT call `createAgent`, `grantAgentSkill`, or
  `updateAgentAssignment` at all — the error message must name every
  missing field, and no partial/broken agent may be created (Scenario 4 —
  no draft/staged record exists anywhere in this codebase; validation is
  entirely client-side, before any call, mirroring `T04`'s own AC-07
  precedent exactly).
- The Worker type button must become genuinely, functionally selectable
  this task (no longer `disabled`) — Producer's own button stays
  `disabled`, untouched.
- Must reuse `skillsApiClient.ts`'s `fetchSkills`/`grantAgentSkill`
  verbatim — no new Skills fetch/grant HTTP call written directly in this
  file, no new Skills-related backend endpoint.
- Must reuse the Expert step's own `sections` state/`fetchSections()` call
  and Section `<select>` shape verbatim — do not add a second, duplicate
  `fetchSections()` call or a divergent Section-rendering shape.
- `AgentDetailPanel.tsx`/`AgentsMapCanvas.tsx` must not be modified —
  Scenario 3/5/6 are already verified in `T01` against the real,
  unmodified downstream surfaces.
- Do not add any interactive element to `AgentsMapCanvas.tsx` — the entry
  affordance stays in Settings only, unchanged from `T04`.
- Reuse `.card`/`.btn`/`.btn-primary`/`.input`/`.item-row-actions`/
  `.badge`/`.badge-danger`/`.kv-key`/`.text-muted` class names verbatim
  (`ADR-010`) — no new CSS file/rule needed; port any missing class from
  `html-prototype/styles.css` verbatim rather than inventing new styling.
- `npm run build` / `npx tsc --noEmit` must stay clean.

---

## Tests

<!-- AC-01/AC-02/AC-04 each need a real, reachable Worker wizard step to
drive them through — this is the only task with one. AC-01 is a structural
AC (DOM field presence/absence), verified on real rendered DOM, not
computed CSS. -->

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`;
delete any leftover `.second-brain/agents_registry.json`/
`agent_skills.json` first; browser preview / headless-Chrome-via-CDP per
this project's established technique):

1. **[REQ-SB-37-US-02-AC-01]** Load `/settings`, open the Create Agent
   affordance, click `[data-testid="agent-type-worker"]`. Confirm it is
   NOT rendered `disabled` and the click actually mounts
   `[data-testid="worker-step"]`. Confirm the mounted step contains
   exactly three field groups: `[data-testid="worker-skills-list"]`,
   `[data-testid="worker-scope-input"]`, and
   `[data-testid="worker-section-select"]` (plus the Name field, common to
   every type). Confirm a plain text search of the mounted Worker step's
   DOM for "Domain", "Purpose", or an output-action term finds nothing —
   Expert's/Producer's own fields do not appear.
2. **[REQ-SB-37-US-02-AC-04]** With the Worker step open and every field
   empty/unselected, click `[data-testid="create-agent-worker-submit"]`.
   Confirm `[data-testid="create-agent-worker-error"]` renders, naming all
   four missing requirements (name, at least one Skill, a Vault Scope, a
   Section). Confirm (via the Network panel, or a `window.fetch` spy
   installed before the click) that NEITHER `POST /agents` NOR any
   `POST .../skills/...` NOR any `PATCH /agents/...` call fired. Confirm
   `GET /agents` still lists only agents that existed before this step —
   no partial/broken agent anywhere, including a fresh load of the Agents
   Map, which still shows the same agent set.
3. **[REQ-SB-37-US-02-AC-02]** Fill `[data-testid="worker-name-input"]`
   with "Ops Helper" (native `HTMLInputElement.prototype.value` setter +
   synthetic `input` event, per this project's established
   React-controlled-input technique). Check two Skill checkboxes in
   `[data-testid="worker-skills-list"]` (one read-only-catalog Skill, one
   migrated mutating Skill, e.g. `run_capture_now` — proving the unified
   catalog, not just the narrow pre-`REQ-SB-39` set, is genuinely offered).
   Fill `[data-testid="worker-scope-input"]` with "customer/masdar,
   Pipeline". Select a real Section from
   `[data-testid="worker-section-select"]`. Click
   `[data-testid="create-agent-worker-submit"]`. Confirm (Network panel)
   exactly one `POST /agents` call (`type: "worker"`) fired, followed by
   exactly one `POST .../skills/{id}` call per checked Skill (2 calls),
   followed by exactly one `PATCH /agents/ops-helper` call carrying BOTH
   `section_id` and `scope` together in the SAME request body (not two
   separate `PATCH` calls). Confirm `GET /agents/ops-helper` afterward
   shows `type: "worker"`, both granted Skills present in
   `GET /agents/ops-helper/skills`, the chosen Section, and
   `scope: ["customer/masdar", "Pipeline"]`.
4. Non-AC smoke check: reopen the Create Agent affordance after a
   successful Worker creation — confirm the Worker step's fields are reset
   (blank name, no Skills checked, empty Scope, no Section selected), not
   left showing the just-submitted values.
5. Non-AC smoke check: `npm run build` (or `npx tsc --noEmit` if `npm`
   isn't resolvable on `PATH` in this session — locate the real install
   via the registry if it recurs, per `Implementation/Learnings.md`) —
   confirm clean, zero new type errors.
6. Clean-up: delete `.second-brain/agents_registry.json` and
   `.second-brain/agent_skills.json`. Stop both dev servers.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-01** (structural) — selecting Worker renders exactly Name +
      Skills + Vault Scope + Section; no Expert/Producer-specific field
      renders anywhere
- [ ] **AC-02** — submitting the Worker step with all fields present
      creates the agent via the exact 3-call sequence (`POST /agents` →
      per-Skill grant → one combined `PATCH` for Section+Scope) and
      confirms success in the UI
- [ ] **AC-04** — submitting with any required field missing (name, ≥1
      Skill, Scope, Section) creates nothing (no API call fires of any
      kind), and names every missing field honestly
- [ ] Worker type button is genuinely selectable; Producer's stays
      `disabled`
- [ ] `AgentDetailPanel.tsx`/`AgentsMapCanvas.tsx` not modified
- [ ] `npm run build` / `tsc` clean
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Producer's own wizard step — `REQ-SB-37-US-03`.
- `AC-03`/`AC-05`/`AC-06` — already verified in `T01` against the real
  `POST /agents` mechanism this wizard itself calls; not re-verified here.
- Any visual/pixel-polish styling beyond reusing existing `ADR-010` class
  names — no `/design` pass occurred for this net-new surface (operator
  direction, per the parent story's own Notes); a non-blocking design
  spot-check happens out-of-band, not as a locked AC.

---

## Context / Notes

**Gating note:** this story is `gate: clear` (no ADR needed — confirmed
additive composition of three already-`Accepted` mechanisms, per the
architect's own reasoning in the story's `## Notes`). This task proceeds to
`Ready` without a human review pause.

**Why the Skills multi-select uses plain checkboxes wired to
`selectedSkillIds` state, not `AgentDetailPanel.tsx`'s own live
grant/revoke toggle:** this is a pre-submit wizard field (nothing exists to
grant/revoke yet — the agent doesn't exist until submit), not a live-editing
panel row; the actual grant calls only fire inside `handleWorkerSubmit`,
after the agent is real. `skillsApiClient.ts`'s `grantAgentSkill` function
itself is reused verbatim once submit fires — only the UI interaction shape
differs from the panel's own live toggle, for the reason above.

**Why the Vault Scope field is a plain controlled `<input>`, not an
`onBlur`-commit row:** `REQ-SB-29-US-01-T05`'s Vault-scope row commits on
blur because it edits an already-live agent's real state immediately. This
wizard field edits pre-submit, local-only draft state — there is nothing to
commit to until the whole form submits, matching the Expert step's own
Name/Domain field's plain-controlled-input shape (`T04`), not the panel
row's commit-on-blur shape.

Full composition/sequencing reasoning:
`Implementation/Architecture/architecture.md` → "Amendment — Worker-type
flow (REQ-SB-37-US-02, no new ADR)".

---

## Implementation Log

**2026-08-14, coder.** Read the REAL current `CreateAgentWizard.tsx`/
`agentsApiClient.ts`/`skillsApiClient.ts` first — matched the task's own
`Before` description exactly (Worker button `disabled`, `step: 'type' |
'expert'`, `CreateAgentBody.domain: string` required). Applied the task's
own diff verbatim: `Step` union gains `'worker'`, new Skills/Scope/Section
state, `fetchSkills()` effect, `selectType`'s real Worker branch,
`toggleSkill`, `handleWorkerSubmit` (validate-before-any-call, 3-call
sequence), the enabled Worker button, and the new Worker step JSX. No
other file touched.

**Verification (CDP-driven headless Edge against the real running Vite
dev server at `127.0.0.1:5173` + the real backend from `T01` at
`127.0.0.1:8001`, native `HTMLInputElement`/`HTMLSelectElement` value-
setter technique + a `window.fetch` spy, per this project's established
technique):**

- Non-AC: Worker type button confirmed NOT `disabled`
  (`{"exists":true,"disabled":false,"text":"Worker"}`), click mounted
  `[data-testid="worker-step"]`.
- **AC-01 — PASS.** Mounted step contains exactly `worker-name-input`,
  `worker-skills-list` (9 real catalog checkboxes — the full unified
  `REQ-SB-39` catalog, not the narrow pre-migration set), `worker-scope-
  input`, `worker-section-select`. Plain-text search of the mounted
  step's own `textContent` for "Domain"/"Purpose"/"output" found nothing.
- **AC-04 — PASS.** Submitted with everything empty:
  `[data-testid="create-agent-worker-error"]` rendered "Missing a name, at
  least one Skill, a Vault Scope, a Section — the agent was not created."
  — all four named. `window.fetch` spy confirmed **zero** calls fired of
  any kind.
- **AC-02 — PASS.** Filled name "Ops Helper", checked
  `web-research` (read-only) + `run_capture_now` (a migrated mutating
  Skill — proving the unified catalog is genuinely offered, not just the
  narrow pre-`REQ-SB-39` set), scope "customer/masdar, Pipeline", Section
  "technical". Submit fired exactly the spec'd 4-call sequence, in
  order: `POST /agents` (`{"name":"Ops Helper","type":"worker"}`) →
  `POST /agents/ops-helper/skills/web-research` →
  `POST /agents/ops-helper/skills/run_capture_now` →
  `PATCH /agents/ops-helper` carrying BOTH `section_id` and `scope`
  together in ONE body (`{"section_id":"technical","scope":
  ["customer/masdar","Pipeline"]}`), never two separate `PATCH` calls.
  Independently confirmed via `GET /agents/ops-helper`
  (`type: "worker"`, `scope: ["customer/masdar","Pipeline"]`,
  `section_id: "technical"`) and `GET /agents/ops-helper/skills` (both
  granted Skills present) — the real backend state matches the UI's own
  claimed outcome exactly, not just a rendered success message.
- Non-AC smoke (reset): reopening the Worker step after a successful
  creation showed blank name, empty scope, no Section selected, and zero
  checked Skill checkboxes — not left showing the just-submitted values.
- Non-AC smoke (typecheck): `tsc --noEmit` via the real local install
  (`node.exe node_modules/typescript/bin/tsc --noEmit`, since neither
  `npm` nor `npx` resolved on `PATH` in this session — located the real
  `node.exe` via `Get-CimInstance Win32_Process` off the already-running
  Vite dev-server process's own command line, per
  `Implementation/Learnings.md`'s established fallback) — zero output,
  clean.
- `AgentDetailPanel.tsx`/`AgentsMapCanvas.tsx` — confirmed untouched (not
  in this task's own `## Files to Modify`, and no edit was made to
  either).

**Scope-internal deviation, logged for human spot-check (not an
escalation):** cleaned up the CDP-launched headless Edge instance via
`taskkill /IM msedge.exe /T` rather than a specific-PID kill — this
project's own documented antipattern (`Implementation/Learnings.md` →
`SPRINT-026`, "never `/IM chrome.exe`"). No harm observed (3 child PIDs
terminated, all confirmed to be this session's own CDP-launched instance
via their process tree), but named honestly rather than silently
following a pattern this project explicitly flags as risky; will use the
specific-PID form for any remaining tasks in this sprint.

**Non-blocking observation, out of this task's own file scope (logged,
not fixed):** `CreateAgentCard.tsx`'s own static copy ("Worker and
Producer types are coming soon — Expert is available today") is now
stale for Worker — that file is not in this task's `## Files to Modify`
and was correctly left untouched; a future task (or `REQ-SB-37-US-03-T03`,
which is in this same sprint and may reasonably touch it if it's in that
task's own scope) should update it once Producer also lands.

Cleanup: reset `.second-brain/agents_registry.json`/`agent_skills.json`
to a clean slate for the next task's own live testing; confirmed
`GET /agents` back to exactly 7 seed agents. Backend/frontend dev servers
left running for the sprint's remaining tasks.

gate: clear 2026-08-14 — no MUST-FLAG trigger fired; the `/IM msedge.exe`
deviation above is a scope-internal judgment call for spot-check, not a
MUST-FLAG trigger (no locked AC affected, no file outside scope touched,
no assumption filling a spec gap).
