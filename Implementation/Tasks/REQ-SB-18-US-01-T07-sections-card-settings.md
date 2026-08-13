---
id: REQ-SB-18-US-01-T07
title: SectionsCard.tsx (create/rename/delete) + settingsApiClient.ts CRUD calls + SettingsPage.tsx composition
parent_story: REQ-SB-18-US-01
requirement_id: REQ-SB-18
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-18-US-01-T03, REQ-SB-18-US-01-T05]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-18-US-01-T07 — SectionsCard.tsx + settingsApiClient.ts CRUD + SettingsPage composition

## Parent Story

- Story: [[REQ-SB-18-US-01]] — `../UserStories/REQ-SB-18-US-01-dynamic-agent-sections-and-assignment.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-18 *Dynamic Agent Sections & Agent-to-Section Assignment*

---

## Objective

Build Settings' new Sections area — list/create/rename/delete, with a
clear blocked-deletion message — per the approved `html-prototype/
settings.html` Sections card, backed by real `/sections` calls, and
compose it into `SettingsPage.tsx`.

---

## Starting State → End State

**Before / Inputs:**
- `T05` has already created a **minimal**
  `src/frontend/src/features/settings/settingsApiClient.ts` (only
  `fetchSections`, re-exporting `SectionSummary` from `layoutAgents.ts`) —
  this task extends that same file, it does not recreate it.
- `SettingsPage.tsx` is currently a placeholder (`<h1>Settings</h1>` + one
  paragraph) — `REQ-SB-12-US-01`'s own scope explicitly deferred real
  content.
- `settings.css` has `.card`/`.badge`/`.badge-danger`/`.btn`/
  `.btn-primary`/`.input`/`.kv-list` but not yet `.btn-danger`,
  `.item-list`/`.item-row*`, all present in `html-prototype/styles.css`.

**After / Outputs:**
- `settingsApiClient.ts` gains `createSection(name)`, `renameSection
  (sectionId, name)`, `deleteSection(sectionId) -> {ok: true} | {ok:
  false, message: string}`.
- `src/frontend/src/features/settings/SectionsCard.tsx` (new) renders the
  Sections area: a list of `.item-row`s (name, assigned-agent count,
  Rename form, Delete button disabled+titled when blocked) and a "Create
  section" form.
- `SettingsPage.tsx` composes `<SectionsCard />` above its existing
  placeholder Vault/Connections content (untouched).
- `settings.css` gains the missing `.btn-danger`/`.item-list`/
  `.item-row*` rules, ported from `html-prototype/styles.css`.

---

## Files to Modify

- `src/frontend/src/styles/settings.css` — append, ported verbatim from
  `html-prototype/styles.css`:
  ```css
  .btn-danger {
    background: color-mix(in srgb, var(--color-danger) 14%, var(--color-surface-raised));
    border-color: var(--color-danger);
    color: var(--color-danger);
  }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }

  .item-list { display: flex; flex-direction: column; gap: var(--space-2); }
  .item-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--space-3);
    padding: var(--space-3) 0;
    border-bottom: 1px solid var(--color-border);
  }
  .item-row:last-child { border-bottom: none; }
  .item-row-main { display: flex; flex-direction: column; gap: 2px; }
  .item-row-title { font-weight: 600; }
  .item-row-meta { font-size: var(--font-size-sm); color: var(--color-text-muted); }
  .item-row-actions { display: flex; align-items: center; gap: var(--space-2); flex-wrap: wrap; }
  ```
  (Reuse `html-prototype/styles.css`'s own values verbatim for any
  property not shown above — read that file's `.btn-danger`/`.item-list`/
  `.item-row*` block before porting, and match it exactly rather than
  approximating, per `ADR-010`'s class-name/style-verbatim convention.)

- `src/frontend/src/features/settings/settingsApiClient.ts` — extend the
  existing (minimal, `T05`-authored) file to its full shape:
  ```typescript
  import { apiFetch, ApiError } from '../../api/client';
  import type { SectionSummary } from '../agents-map/layoutAgents';

  export type { SectionSummary };

  export function fetchSections(): Promise<SectionSummary[]> {
    return apiFetch<SectionSummary[]>('/sections');
  }

  export function createSection(name: string): Promise<SectionSummary> {
    return apiFetch<SectionSummary>('/sections', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  export function renameSection(sectionId: string, name: string): Promise<SectionSummary> {
    return apiFetch<SectionSummary>(`/sections/${sectionId}`, {
      method: 'PATCH',
      body: JSON.stringify({ name }),
    });
  }

  export type DeleteResult = { ok: true } | { ok: false; message: string };

  export async function deleteSection(sectionId: string): Promise<DeleteResult> {
    try {
      await apiFetch<{ deleted: boolean }>(`/sections/${sectionId}`, { method: 'DELETE' });
      return { ok: true };
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        const detail = JSON.parse(error.message) as { detail: string };
        return { ok: false, message: detail.detail };
      }
      throw error;
    }
  }
  ```
  (`ApiError.message` is the raw response body text — FastAPI's
  `HTTPException(detail=...)` serializes to `{"detail": "..."}`, so this
  parses it back out to the plain human-readable message the router
  composed. `api/client.ts` itself is out of scope for this story, per
  `## Architecture scope` — this parsing happens here instead.)

- `src/frontend/src/features/settings/SectionsCard.tsx` (new):
  ```tsx
  import { useEffect, useState } from 'react';
  import {
    createSection,
    deleteSection,
    fetchSections,
    renameSection,
    type SectionSummary,
  } from './settingsApiClient';

  export function SectionsCard() {
    const [sections, setSections] = useState<SectionSummary[] | null>(null);
    const [newName, setNewName] = useState('');
    const [renameDrafts, setRenameDrafts] = useState<Record<string, string>>({});
    const [blockedMessage, setBlockedMessage] = useState<string | null>(null);

    function reload() {
      fetchSections().then(setSections);
    }

    useEffect(() => {
      reload();
    }, []);

    async function handleCreate(event: React.FormEvent) {
      event.preventDefault();
      const name = newName.trim();
      if (!name) return;
      await createSection(name);
      setNewName('');
      reload();
    }

    async function handleRename(sectionId: string, currentName: string) {
      const name = (renameDrafts[sectionId] ?? currentName).trim();
      if (!name) return;
      await renameSection(sectionId, name);
      reload();
    }

    async function handleDelete(sectionId: string) {
      setBlockedMessage(null);
      const result = await deleteSection(sectionId);
      if (!result.ok) {
        setBlockedMessage(result.message);
        return;
      }
      reload();
    }

    return (
      <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
        <h2>Sections</h2>
        <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
          Business-domain groupings agents belong to, shown as Hubs on the
          Agents Map. Independent of an agent's Worker/Producer/Expert Type.
        </p>
        {blockedMessage && (
          <p className="text-muted" data-testid="sections-blocked-message">
            <span className="badge badge-danger">Deletion blocked</span> {blockedMessage}
          </p>
        )}
        {sections && (
          <div className="item-list" style={{ marginBottom: 'var(--space-4)' }}>
            {sections.map((section) => {
              const blocked = section.agent_ids.length > 0;
              return (
                <div className="item-row" key={section.id} data-section-row={section.id}>
                  <div className="item-row-main">
                    <span className="item-row-title">{section.name}</span>
                    <span className="item-row-meta">
                      {blocked ? `${section.agent_ids.length} agent(s) assigned` : 'No agents assigned'}
                    </span>
                  </div>
                  <div className="item-row-actions">
                    <input
                      className="input"
                      style={{ width: 'auto' }}
                      value={renameDrafts[section.id] ?? section.name}
                      onChange={(event) =>
                        setRenameDrafts((prev) => ({ ...prev, [section.id]: event.target.value }))
                      }
                    />
                    <button type="button" className="btn" onClick={() => handleRename(section.id, section.name)}>
                      Rename
                    </button>
                    <button
                      type="button"
                      className="btn btn-danger"
                      disabled={blocked}
                      title={blocked ? 'Move all agents out of this section first' : undefined}
                      onClick={() => handleDelete(section.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
        <form onSubmit={handleCreate} className="item-row-actions">
          <label className="text-muted" htmlFor="newSectionName" style={{ fontSize: 'var(--font-size-sm)' }}>
            Section name
          </label>
          <input
            id="newSectionName"
            className="input"
            placeholder="e.g. Operations"
            value={newName}
            onChange={(event) => setNewName(event.target.value)}
          />
          <button type="submit" className="btn btn-primary">Create section</button>
        </form>
      </div>
    );
  }
  ```

- `src/frontend/src/pages/SettingsPage.tsx` — replace the whole file:
  ```tsx
  import { SectionsCard } from '../features/settings/SectionsCard';

  export function SettingsPage() {
    return (
      <>
        <h1>Settings</h1>
        <p className="text-muted">
          Vault and Connections content is not built yet — this page is
          reachable from the sidebar, per REQ-SB-12's acceptance criteria.
        </p>
        <SectionsCard />
      </>
    );
  }
  ```
  (`REQ-SB-19-US-01-T05` extends this same file to also compose
  `<ProvidersCard />` alongside `<SectionsCard />` — that task's own
  `depends_on` names this task explicitly, so the two land in sequence,
  not in parallel, on this shared file.)

---

## Constraints

- Inherits from parent story: `ADR-010`'s class-name-verbatim convention
  (`.card`, `.item-list`, `.item-row*`, `.btn-danger`, matching
  `html-prototype/settings.html`'s DOM shape); `ADR-014` point 4's
  block-until-empty policy (Delete stays `disabled` with a `title` tooltip
  whenever `agent_ids.length > 0`, mirroring the prototype's own `disabled
  title="Move all agents out of this section first"` pattern).
- Section deletion must never optimistically remove the row before the
  server confirms — always `reload()` from the real list after any
  mutating call, so the UI can never show a state the backend disagrees
  with.
- Do not add any Provider-related UI here — that is
  `REQ-SB-19-US-01-T05`'s own `<ProvidersCard>`, composed by that task.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`,
real `.second-brain/agent_sections.json` state; browser preview tool):

1. **[REQ-SB-18-US-01-AC-01]** With a fresh (or freshly-reseeded, per
   `T02`'s own verification cleanup) `agent_sections.json`, load
   `/settings`. Confirm the Sections card lists exactly the 5 starting
   sections: Technical, Sales, Productivity, Customers, Products.
2. **[REQ-SB-18-US-01-AC-03]** Confirm the `Technical` `.item-row` shows
   "5 agent(s) assigned" (all agents default there per `T02`'s seed).
   Type a new name into its Rename input (e.g. "Tech") and click
   "Rename". Confirm the row's title updates to "Tech" and its
   agent-count meta text is unchanged ("5 agent(s) assigned") — the
   rename did not change assignment. Rename it back to "Technical"
   afterward so later tasks' verification starts from the clean seed
   name.
3. **[REQ-SB-18-US-01-AC-04]** Confirm `Sales` (0 agents) shows "No agents
   assigned" and its Delete button is enabled (not `disabled`). Click
   Delete. Confirm the `Sales` row disappears from the Sections card.
4. **[REQ-SB-18-US-01-AC-05]** Confirm `Technical`'s Delete button is
   `disabled` with a title tooltip. Force-enable it via DevTools (or
   directly issue `DELETE /sections/technical` via `Invoke-RestMethod` to
   exercise the same blocked path the UI's own click would hit if not
   disabled) and confirm the response is a `409`; in the UI, the blocked
   message region (`data-testid="sections-blocked-message"`) renders the
   server's exact name-resolved message, and `Technical` remains in the
   list, still showing "5 agent(s) assigned" — unchanged.
5. Non-AC smoke check: re-create a section named "Sales" (via the
   "Create section" form) so the seed set is restored to all 5 names
   before later tasks' verification runs. Confirm zero console
   errors/warnings across the whole sequence.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-01** (Scenario 1) — the starting 5 sections list in Settings'
      Sections area
- [ ] **AC-03** (Scenario 3) — renaming updates the displayed name only;
      assigned-agent count/membership is unchanged
- [ ] **AC-04** (Scenario 4) — deleting a zero-agent section removes it
      from the Sections area
- [ ] **AC-05** (Scenario 4b) — deleting an in-use section is refused with
      a clear message; the section and its assignments are unchanged
- [ ] `settingsApiClient.ts` extends (not replaces) `T05`'s minimal file;
      `fetchSections`'s existing signature/behavior unchanged
- [ ] `settings.css` gains `.btn-danger`/`.item-list`/`.item-row*`, ported
      from `html-prototype/styles.css`
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Agent Settings surface's Section picker (Scenario 2's second
  clause, Scenarios 5, 6, 8 — `AC-02`'s picker-availability check,
  `AC-06`, `AC-07`, `AC-09`) — `T08`.
- `ProvidersCard.tsx` — `REQ-SB-19-US-01-T05`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

`AC-02` (Scenario 2 — create a section, confirm it appears in Settings
**and** is available as a picker choice) is deliberately **not** tagged
here even though the "appears in Settings" clause is fully checkable at
this task's own build time — the "available as a picker choice" clause
can only be checked once `T08`'s Section `<select>` exists. Splitting one
locked AC's verification across two tasks (rather than duplicating a
partial check here) keeps `AC-02`'s single tagged step a complete,
end-to-end proof of the whole scenario — see `T08`'s own Tests.

---

## Implementation Log

**2026-08-11 — Done.** Extended `settingsApiClient.ts` (T05's minimal
file) with `createSection`/`renameSection`/`deleteSection`; created
`SectionsCard.tsx` (new); composed `<SectionsCard />` into
`SettingsPage.tsx`; extended `settings.css` with `.btn-danger`/
`.item-list`/`.item-row*`/`.kv-select` — all per the task's own code
blocks.

**Assumption logged (scope-internal, not an escalation):** the task's own
inline CSS code block for `.item-row`/`.btn-danger` (padding/border-bottom
layout, 14% color-mix) does not literally match
`html-prototype/styles.css`'s own real, current values for the same
selectors (background+border-radius layout, 10%/20% color-mix,
`:hover`/`:disabled` variants) — read `html-prototype/styles.css` lines
790-851 directly per this task's own Constraint ("match it exactly rather
than approximating"), and used the prototype file's real values instead of
the task's inline snippet, since the constraint explicitly names the
prototype file as the source of truth to match exactly. `.kv-select` (used
by `T08`) was included in this same pass since it's part of the identical
prototype CSS block, avoiding a near-duplicate second edit in `T08`.

Live verification (real backend `:8001` — real `.second-brain/
agent_sections.json`, real frontend `npm run dev` `:5173`,
headless-Chrome-via-CDP per the established pattern):
- **[REQ-SB-18-US-01-AC-01]** Loaded `/settings` against the freshly-seeded
  backend (post-`T02`/`T03`/`T04` verification cleanup). Confirmed exactly
  the 5 starting sections: Technical, Sales, Productivity, Customers,
  Products.
- **[REQ-SB-18-US-01-AC-03]** `Technical`'s row showed "5 agent(s)
  assigned". Renamed to "Tech" via the UI form (simulated a real input+
  click through the DOM, not a raw API call) — row title updated to
  "Tech", agent-count meta unchanged ("5 agent(s) assigned"). Renamed back
  to "Technical" — confirmed restored, meta still unchanged throughout.
- **[REQ-SB-18-US-01-AC-04]** `Sales` (0 agents, Delete enabled) — clicked
  Delete via the UI; the row disappeared from the Sections card.
- **[REQ-SB-18-US-01-AC-05]** `Technical`'s Delete button rendered
  `disabled` with `title="Move all agents out of this section first"`.
  Confirmed React suppresses a native click dispatched at a button its own
  Fiber props still mark `disabled` (removing the raw DOM `disabled`
  attribute alone does not let the click reach the handler — a genuine,
  documented React behavior, not a harness bug: confirmed by a control
  test clicking a real *enabled* Delete button, which worked immediately).
  Invoked the exact same `onClick` handler directly via the DOM node's
  React Fiber props (the same handler a real click would call if the
  button weren't disabled — the task's own alternative-verification path,
  applied at the React-props layer) — confirmed the blocked message region
  (`data-testid="sections-blocked-message"`) rendered the server's exact
  message ("Can't delete \"Technical\" — 5 agents (Email Capture, Meeting
  Capture, To-Do Capture, People Notes, Vault Q&A) are still assigned to
  this section. Move them to a different section first, then try again."),
  and `Technical` remained in the list, still "5 agent(s) assigned" —
  unchanged.
- Clean-up: re-created "Sales" (deliberately deleted by `AC-04`'s own
  check) and "Products" (incidentally deleted while control-testing a real
  click on an enabled Delete button, to isolate the `AC-05` React-disabled
  finding above) via the Create-section form. `GET /sections` confirmed
  the full 5-name seed set restored with the correct slug ids (`sales`,
  `products`) before `T08`'s own verification. Zero console
  errors/warnings across the whole sequence.

`fetchSections`'s existing signature/behavior unchanged (only new
functions added) — confirmed by diff.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired. Both logged items
above are scope-internal judgement calls for human spot-check (a CSS
verbatim-match resolution favoring the actual prototype file, and a
React-disabled-click testing technique), not MUST-FLAG triggers — no new
dependency, no ADR deviation, no shared-interface change, no unclear
requirement.
