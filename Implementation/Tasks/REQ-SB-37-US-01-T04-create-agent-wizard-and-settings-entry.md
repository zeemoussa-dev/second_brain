---
id: REQ-SB-37-US-01-T04
title: CreateAgentWizard.tsx (type selector + Expert step) + Settings entry affordance + agentsApiClient.ts createAgent
parent_story: REQ-SB-37-US-01
requirement_id: REQ-SB-37
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-37-US-01-T03]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-37-US-01-T04 — CreateAgentWizard.tsx + Settings entry affordance

## Parent Story

- Story: [[REQ-SB-37-US-01]] — `../UserStories/REQ-SB-37-US-01-agent-creation.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-37 *Agent Creation Wizard*

---

## Objective

Build the wizard's own entry affordance, type selector, and Expert-type
step, and wire them into Settings — the first real UI path a user can
reach without any source-code change. Merges the wizard component with its
own Settings entry point in one task (mirrors this project's own
`REQ-SB-18-US-01-T07` precedent: `SectionsCard.tsx` + `SettingsPage.tsx`
composition landed together, not split) — a wizard component with no
reachable entry affordance yet has no mount point to click-through-verify
against.

---

## Starting State → End State

**Before / Inputs:**
- `T03` has landed `POST /agents` (Expert type only) and `PATCH
  /agents/{id}` already accepts `section_id`.
- `src/frontend/src/features/agents-map/agentsApiClient.ts` already has
  `AgentDetail`, `fetchAgent`, `updateAgentAssignment`.
- `src/frontend/src/features/settings/settingsApiClient.ts` already has
  `fetchSections`/`SectionSummary`.
- `src/frontend/src/pages/SettingsPage.tsx` currently composes
  `<SectionsCard />` and `<ProvidersCard />` only.

**After / Outputs:**
- `agentsApiClient.ts` gains `createAgent({name, type, domain}) ->
  Promise<AgentDetail>` (`POST /agents`).
- `src/frontend/src/features/agents-map/CreateAgentWizard.tsx` (new) — a
  type selector (Expert enabled; Worker/Producer visibly-present-but-
  disabled, "Coming soon") and, once Expert is chosen, a step with name,
  knowledge-domain, and Section fields; submitting calls `createAgent`
  then `updateAgentAssignment` for the Section, or shows an honest,
  specific error naming any missing required field without calling either.
- `src/frontend/src/features/settings/CreateAgentCard.tsx` (new) — the
  Settings entry affordance (`+ Create agent`, mirroring
  `SectionsCard.tsx`/`ProvidersCard.tsx`'s own precedent and
  `html-prototype/settings.html`'s own `<details>`-based "+ Create new
  section" pattern) that mounts `CreateAgentWizard`.
- `SettingsPage.tsx` additionally composes `<CreateAgentCard />`.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — append:
  ```typescript
  export interface CreateAgentBody {
    name: string;
    type: 'worker' | 'expert' | 'producer';
    domain: string;
  }

  export function createAgent(body: CreateAgentBody): Promise<AgentDetail> {
    return apiFetch<AgentDetail>('/agents', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }
  ```

- `src/frontend/src/features/agents-map/CreateAgentWizard.tsx` (new):
  ```tsx
  import { useEffect, useState } from 'react';
  import { fetchSections, type SectionSummary } from '../settings/settingsApiClient';
  import { createAgent, updateAgentAssignment, type AgentDetail } from './agentsApiClient';

  type AgentType = 'worker' | 'expert' | 'producer';

  interface CreateAgentWizardProps {
    onCreated: (agent: AgentDetail) => void;
  }

  export function CreateAgentWizard({ onCreated }: CreateAgentWizardProps) {
    const [step, setStep] = useState<'type' | 'expert'>('type');
    const [sections, setSections] = useState<SectionSummary[] | null>(null);
    const [name, setName] = useState('');
    const [domain, setDomain] = useState('');
    const [sectionId, setSectionId] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
      fetchSections().then(setSections);
    }, []);

    function selectType(type: AgentType) {
      // Worker/Producer: visibly-present-but-disabled this pass
      // (REQ-SB-37-US-02/US-03, hard-blocked on REQ-SB-39) — their own
      // buttons are rendered `disabled`, so this branch is a defensive
      // no-op, never actually reachable via a real click.
      if (type !== 'expert') return;
      setStep('expert');
      setError(null);
    }

    async function handleSubmit(event: React.FormEvent) {
      event.preventDefault();
      const trimmedName = name.trim();
      const trimmedDomain = domain.trim();
      const missing: string[] = [];
      if (!trimmedName) missing.push('a name');
      if (!trimmedDomain) missing.push('a knowledge domain');
      if (!sectionId) missing.push('a Section');
      if (missing.length > 0) {
        setError(`Missing ${missing.join(', ')} — the agent was not created.`);
        return;
      }
      setError(null);
      setSubmitting(true);
      try {
        const created = await createAgent({ name: trimmedName, type: 'expert', domain: trimmedDomain });
        const updated = await updateAgentAssignment(created.id, { section_id: sectionId });
        setName('');
        setDomain('');
        setSectionId('');
        setStep('type');
        onCreated(updated);
      } finally {
        setSubmitting(false);
      }
    }

    return (
      <div data-testid="create-agent-wizard">
        {step === 'type' && (
          <div className="item-row-actions">
            <button
              type="button"
              className="btn btn-primary"
              data-testid="agent-type-expert"
              onClick={() => selectType('expert')}
            >
              Expert
            </button>
            <button
              type="button"
              className="btn"
              data-testid="agent-type-worker"
              disabled
              title="Coming soon — REQ-SB-37-US-02"
            >
              Worker (coming soon)
            </button>
            <button
              type="button"
              className="btn"
              data-testid="agent-type-producer"
              disabled
              title="Coming soon — REQ-SB-37-US-03"
            >
              Producer (coming soon)
            </button>
          </div>
        )}
        {step === 'expert' && (
          <form onSubmit={handleSubmit} data-testid="expert-step" className="item-row-actions">
            {error && (
              <p className="text-muted" data-testid="create-agent-error">
                <span className="badge badge-danger">Can't create agent</span> {error}
              </p>
            )}
            <label className="text-muted" htmlFor="expertName">Name</label>
            <input
              id="expertName"
              className="input"
              data-testid="expert-name-input"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
            <label className="text-muted" htmlFor="expertDomain">Knowledge domain</label>
            <input
              id="expertDomain"
              className="input"
              data-testid="expert-domain-input"
              value={domain}
              onChange={(event) => setDomain(event.target.value)}
            />
            <label className="text-muted" htmlFor="expertSection">Section</label>
            <select
              id="expertSection"
              className="input"
              data-testid="expert-section-select"
              value={sectionId}
              onChange={(event) => setSectionId(event.target.value)}
            >
              <option value="">Choose a Section…</option>
              {sections?.map((section) => (
                <option key={section.id} value={section.id}>{section.name}</option>
              ))}
            </select>
            <button type="submit" className="btn btn-primary" data-testid="create-agent-submit" disabled={submitting}>
              Create agent
            </button>
          </form>
        )}
      </div>
    );
  }
  ```

- `src/frontend/src/features/settings/CreateAgentCard.tsx` (new):
  ```tsx
  import { useState } from 'react';
  import { CreateAgentWizard } from '../agents-map/CreateAgentWizard';
  import type { AgentDetail } from '../agents-map/agentsApiClient';

  export function CreateAgentCard() {
    const [lastCreated, setLastCreated] = useState<AgentDetail | null>(null);

    return (
      <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
        <h2>Agents</h2>
        <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
          Create a new agent without any source-code change. Worker and
          Producer types are coming soon — Expert is available today.
        </p>
        {lastCreated && (
          <p className="text-muted" data-testid="create-agent-success">
            <span className="badge">Created</span> {lastCreated.name} is now on the Agents Map.
          </p>
        )}
        <details data-testid="create-agent-affordance">
          <summary className="btn btn-primary">+ Create agent</summary>
          <div style={{ marginTop: 'var(--space-3)' }}>
            <CreateAgentWizard onCreated={setLastCreated} />
          </div>
        </details>
      </div>
    );
  }
  ```

- `src/frontend/src/pages/SettingsPage.tsx` — add the new card, additive:
  ```tsx
  import { SectionsCard } from '../features/settings/SectionsCard';
  import { ProvidersCard } from '../features/settings/ProvidersCard';
  import { CreateAgentCard } from '../features/settings/CreateAgentCard';

  export function SettingsPage() {
    return (
      <>
        <h1>Settings</h1>
        <p className="text-muted">
          Vault and Connections content is not built yet — this page is
          reachable from the sidebar, per REQ-SB-12's acceptance criteria.
        </p>
        <SectionsCard />
        <ProvidersCard />
        <CreateAgentCard />
      </>
    );
  }
  ```

---

## Constraints

- Inherits from parent story and `ADR-030` point 6 — `POST /agents`
  (`createAgent`) never receives `section_id`; Section assignment is
  always the separate, already-`Done` `updateAgentAssignment` call.
- Worker/Producer buttons must be rendered `disabled` (visibly-present,
  not hidden) — never functionally selectable this pass.
- Submitting the Expert step with any of name/domain/Section missing must
  NOT call `createAgent` or `updateAgentAssignment` at all — the error
  message must name every missing field, and no partial/broken agent may
  be created.
- `AgentDetailPanel.tsx` must not be modified — Scenario 6 already reuses
  it unchanged (verified in `T03`).
- Do not add any interactive element to `AgentsMapCanvas.tsx` — the entry
  affordance lives in Settings only, per the architect's own sequencing
  call (`architecture.md`).
- Reuse `.card`/`.btn`/`.btn-primary`/`.input`/`.item-row-actions`/
  `.badge`/`.badge-danger` class names verbatim (`ADR-010`) — no new CSS
  file/rule needed for this task; if a class used above does not yet exist
  in `settings.css`, port it from `html-prototype/styles.css` verbatim
  rather than inventing new styling.

---

## Tests

<!-- AC-01/AC-02/AC-03/AC-07 each need a real, reachable wizard UI to
drive them through — this is the only task with one. AC-02 is a
structural AC (DOM field presence/absence), verified on real rendered
DOM, not computed CSS. -->

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`;
delete any leftover `.second-brain/agents_registry.json` first; browser
preview / headless-Chrome-via-CDP per this project's established
technique):

1. **[REQ-SB-37-US-01-AC-01]** Load `/settings`. Confirm a
   `[data-testid="create-agent-affordance"]` element renders with a "+
   Create agent" summary. Open it (click/expand). Confirm
   `[data-testid="create-agent-wizard"]` mounts, showing three type
   choices: `[data-testid="agent-type-expert"]` (enabled),
   `[data-testid="agent-type-worker"]` and
   `[data-testid="agent-type-producer"]` (both rendering the native
   `disabled` attribute) — reached purely by navigating the already-built
   app (Settings sidebar link → this new card), no source-code change
   required to reach it.
2. **[REQ-SB-37-US-01-AC-02]** Click `[data-testid="agent-type-expert"]`.
   Confirm `[data-testid="expert-step"]` renders with exactly
   `[data-testid="expert-name-input"]`, `[data-testid="expert-domain-input"]`,
   and `[data-testid="expert-section-select"]` as its fields. Confirm no
   element anywhere in the DOM at this point is labeled/named for Skills,
   Vault Scope, Purpose, or an output action (Worker's/Producer's own
   fields) — a plain text search of the mounted wizard's DOM for those
   terms finds nothing.
3. **[REQ-SB-37-US-01-AC-07]** With the Expert step open and all three
   fields empty, click `[data-testid="create-agent-submit"]`. Confirm
   `[data-testid="create-agent-error"]` renders, naming all three missing
   fields (name, knowledge domain, Section). Confirm (via the Network
   panel, or a `window.fetch` spy installed before the click) that neither
   `POST /agents` nor any `PATCH /agents/...` call fired. Confirm
   `GET /agents` (a direct check) still lists only the 7 seed agents — no
   partial/broken agent anywhere, including a fresh load of the Agents Map
   (`/agents-map`), which still shows only the 7 seed agents.
4. **[REQ-SB-37-US-01-AC-03]** Fill `[data-testid="expert-name-input"]`
   with "Widgets Expert" (using the native
   `HTMLInputElement.prototype.value` setter + a synthetic `input` event,
   per this project's established React-controlled-input technique),
   `[data-testid="expert-domain-input"]` with "Widgets manufacturing", and
   select a real Section from `[data-testid="expert-section-select"]`.
   Click `[data-testid="create-agent-submit"]`. Confirm
   `[data-testid="create-agent-success"]` renders naming "Widgets Expert".
   Confirm (Network panel) exactly one `POST /agents` call fired followed
   by exactly one `PATCH /agents/widgets-expert` call with the chosen
   `section_id` — the wizard's own two-call sequence, no source-code
   change required to have created it. Confirm `GET /agents` now includes
   `widgets-expert` with the chosen Section.
5. Non-AC smoke check: reopen the Create Agent affordance after a
   successful creation — confirm the Expert step's fields are reset
   (blank name/domain, no Section selected), ready for a second creation,
   not left showing the just-submitted values.
6. Clean-up: delete `.second-brain/agents_registry.json`. Stop both dev
   servers.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** — the Create Agent affordance is reachable from Settings;
      opening it shows a type choice, no source-code change needed
- [x] **AC-02** (structural) — selecting Expert renders exactly the
      name/domain/Section fields; no Worker/Producer-specific field
      renders anywhere
- [x] **AC-03** — submitting the Expert step with all fields present
      creates the agent (via `POST /agents` then `PATCH` for Section) and
      confirms success in the UI
- [x] **AC-07** — submitting with any required field missing creates
      nothing (no API call fires), and names every missing field honestly
- [x] Worker/Producer type buttons render `disabled`, never functionally
      selectable
- [x] `AgentDetailPanel.tsx`/`AgentsMapCanvas.tsx` not modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Worker's/Producer's own wizard steps — `REQ-SB-37-US-02`/`US-03`.
- `AC-04`/`AC-05`/`AC-06`/`AC-08` — already verified in `T03` against the
  real `POST /agents` mechanism this wizard itself calls; not re-verified
  here.
- Any visual/pixel-polish styling beyond reusing existing `ADR-010`
  class names — no `/design` pass occurred for this net-new surface
  (operator direction, per the parent story's own Notes); a non-blocking
  design spot-check happens out-of-band, not as a locked AC.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-030` created at
`/plan-tasks` step 1) — the human reviews `ADR-030` and this task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside the rest of the story.

**Why this task merges the wizard component with its Settings entry
point, rather than splitting them (a genuine decomposition choice, not a
guess):** a `CreateAgentWizard.tsx` with no affordance to open it has no
real mount point to click-through-verify — mirrors this project's own
`REQ-SB-18-US-01-T07` precedent, which landed `SectionsCard.tsx` and its
`SettingsPage.tsx` composition in one task for the identical reason.

React-controlled-input verification technique (step 4) and headless-CDP
browser tooling reused per this project's own established `Learnings.md`
entries (`SPRINT-026`) — set values via the native
`HTMLInputElement.prototype.value` setter before dispatching a synthetic
`input` event, not a plain `.value =` assignment.

---

## Implementation Log

**Coder pass, 2026-08-14.** Read the real current
`agentsApiClient.ts`/`SettingsPage.tsx`/`settingsApiClient.ts` before
editing — matched the task's own "Before" description exactly (no drift
since this task was written; `SPRINT-030`'s unified Capabilities list and
`SPRINT-032`'s Vault-scope row both landed on `AgentDetailPanel.tsx`, which
this task never touches). Implemented exactly per the task's own code
samples: `createAgent` appended to `agentsApiClient.ts`; new
`CreateAgentWizard.tsx` and `CreateAgentCard.tsx`; `SettingsPage.tsx`
additionally composes `<CreateAgentCard />`. Confirmed via
`grep`/direct-read that `.card`/`.btn`/`.btn-primary`/`.input`/
`.item-row-actions`/`.badge`/`.badge-danger` all already exist in
`settings.css` — no new CSS needed. Confirmed all 4 touched/new files
transform cleanly through the real running Vite dev server (200, no
esbuild error) before live verification.

Live verification via a real CDP-driven headless-Edge session (own
remote-debugging profile, port 9333) against the real backend
(`--reload --port 8001`, started for this task) and the already-running
real frontend dev server (port 5173, confirmed genuine before reuse) —
values set via the native `HTMLInputElement.prototype.value`/
`HTMLSelectElement.prototype.value` setter + a synthetic event, per this
project's established technique; a `window.fetch` spy installed
in-page to confirm exact call counts, with `Runtime.exceptionThrown`
listening throughout (zero exceptions, zero console errors beyond the
ordinary Vite/React-DevTools banner).

- **AC-01:** loaded `/settings` → `[data-testid="create-agent-affordance"]`
  present with "+ Create agent" summary; clicked it →
  `[data-testid="create-agent-wizard"]` mounted with all 3 type choices —
  Expert `disabled: false`, Worker `disabled: true`, Producer
  `disabled: true`. Reached purely by navigating the already-built app
  (Settings sidebar → new card), no source-code change to reach it. **PASS.**
- **AC-02:** clicked Expert → `[data-testid="expert-step"]` renders with
  exactly `expert-name-input`/`expert-domain-input`/
  `expert-section-select`; a lowercase text scan of the mounted step's own
  `innerHTML` found zero occurrences of "skill", "vault scope"/"vault-scope",
  "purpose", or "output action". **PASS.**
- **AC-07:** with the Expert step open and all fields empty, clicked
  Submit → `[data-testid="create-agent-error"]` renders "Missing a name, a
  knowledge domain, a Section — the agent was not created."; the
  `window.fetch` spy recorded **zero** calls (neither `POST /agents` nor
  any `PATCH` fired); a direct `GET /agents` from the same page confirmed
  still exactly the 7 seed agents — no partial/broken agent. **PASS.**
- **AC-03:** filled name "Widgets Expert", domain "Widgets manufacturing",
  selected the real `"technical"` Section option, submitted →
  `[data-testid="create-agent-success"]` renders "Created Widgets Expert is
  now on the Agents Map."; the fetch spy recorded **exactly** two calls, in
  order — `POST http://127.0.0.1:8001/agents` then
  `PATCH http://127.0.0.1:8001/agents/widgets-expert` (the wizard's own
  two-call sequence) — no source-code change required to have created it.
  `GET /agents` afterward includes `widgets-expert` with
  `section_id: "technical"`, the chosen Section. **PASS.**
- Non-AC smoke check: reopened the Create Agent affordance after the
  successful creation — the wizard had already returned to the type step;
  clicking Expert again showed all three fields reset to blank/unselected
  (`name: ""`, `domain: ""`, `section: ""`), ready for a second creation.
  Confirmed.
- Clean-up: deleted `.second-brain/agents_registry.json`. Stopped the
  headless-Edge CDP session (its own specific PID tree only, per this
  project's established protocol) and the backend dev server started for
  this task (resolved its real Windows PID via `Get-NetTCPConnection` →
  `Stop-Process`, since the bash-emulated PID from this task's own launch
  command did not match a real killable process — same class of PID-
  translation mismatch this project has hit before). Left the
  already-running frontend dev server (pre-existing before this task,
  confirmed genuine, not started or owned by this task) running,
  untouched.

`AgentDetailPanel.tsx`/`AgentsMapCanvas.tsx` — confirmed not modified
(only the 3 new/edited files listed above appear in this task's diff).

gate: clear 2026-08-14 — no MUST-FLAG trigger fired.

**Status: Done.**
