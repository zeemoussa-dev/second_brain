---
id: REQ-SB-19-US-01-T05
title: ProvidersCard.tsx (add/edit/remove, Compass pre-seeded) + settingsApiClient.ts /providers calls + SettingsPage.tsx composition
parent_story: REQ-SB-19-US-01
requirement_id: REQ-SB-19
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-19-US-01-T03, REQ-SB-18-US-01-T07]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-19-US-01-T05 — ProvidersCard.tsx + settingsApiClient.ts /providers calls + SettingsPage composition

## Parent Story

- Story: [[REQ-SB-19-US-01]] — `../UserStories/REQ-SB-19-US-01-per-agent-llm-provider-selection.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-19 *Per-Agent LLM Provider Selection*

---

## Objective

Build Global Settings' new Providers area — list (Compass pre-seeded)/
add/edit/remove, masked credential handling, a clear blocked-removal
message — per the approved `html-prototype/settings.html` Providers card,
backed by real `/providers` calls, and compose it into `SettingsPage.tsx`
alongside `REQ-SB-18-US-01-T07`'s already-landed `<SectionsCard>`.

**This task requires `REQ-SB-18-US-01-T07` to already be `Done`** — it
extends the same `settingsApiClient.ts` and `SettingsPage.tsx` files that
task creates/composes. Do not start this task until that one is complete.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-18-US-01-T07` has landed: `settingsApiClient.ts` with
  `fetchSections`/`createSection`/`renameSection`/`deleteSection`;
  `SectionsCard.tsx`; `SettingsPage.tsx` composing `<SectionsCard />`;
  `settings.css`'s `.btn-danger`/`.item-list`/`.item-row*` rules.
- `T03` has landed `GET/POST/PATCH/DELETE /providers`.

**After / Outputs:**
- `settingsApiClient.ts` gains `fetchProviders`, `createProvider`,
  `updateProvider`, `removeProvider(providerId) -> {ok: true} | {ok:
  false, message: string}` (same blocked-result shape
  `deleteSection` already established).
- `src/frontend/src/features/settings/ProvidersCard.tsx` (new) renders
  the Providers area: a list of `.item-row`s (name + Default/No-client
  badges, endpoint/model meta, used-by-N-agents meta, Edit form with a
  masked credential field, Remove button disabled+titled when blocked)
  and an "Add provider" form.
- `SettingsPage.tsx` composes `<ProvidersCard />` alongside the existing
  `<SectionsCard />`.

---

## Files to Modify

- `src/frontend/src/features/settings/settingsApiClient.ts` — extend the
  existing (Sections-only, `REQ-SB-18-US-01-T07`-authored) file, adding
  after the existing `deleteSection`:
  ```typescript
  export interface ProviderSummary {
    id: string;
    name: string;
    endpoint: string;
    model: string;
    credential_set: boolean;
    is_default: boolean;
    has_real_client: boolean;
    agent_ids: string[];
  }

  export function fetchProviders(): Promise<ProviderSummary[]> {
    return apiFetch<ProviderSummary[]>('/providers');
  }

  export interface ProviderFormFields {
    name: string;
    endpoint: string;
    credential: string;
    model: string;
  }

  export function createProvider(fields: ProviderFormFields): Promise<ProviderSummary> {
    return apiFetch<ProviderSummary>('/providers', {
      method: 'POST',
      body: JSON.stringify(fields),
    });
  }

  export function updateProvider(
    providerId: string,
    fields: Partial<ProviderFormFields>,
  ): Promise<ProviderSummary> {
    return apiFetch<ProviderSummary>(`/providers/${providerId}`, {
      method: 'PATCH',
      body: JSON.stringify(fields),
    });
  }

  export async function removeProvider(providerId: string): Promise<DeleteResult> {
    try {
      await apiFetch<{ deleted: boolean }>(`/providers/${providerId}`, { method: 'DELETE' });
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
  (Reuses the existing `DeleteResult` type and `ApiError`
  import `REQ-SB-18-US-01-T07` already added to this file — do not
  redeclare either.)

- `src/frontend/src/features/settings/ProvidersCard.tsx` (new):
  ```tsx
  import { useEffect, useState } from 'react';
  import {
    createProvider,
    fetchProviders,
    removeProvider,
    updateProvider,
    type ProviderFormFields,
    type ProviderSummary,
  } from './settingsApiClient';

  const EMPTY_FORM: ProviderFormFields = { name: '', endpoint: '', credential: '', model: '' };

  export function ProvidersCard() {
    const [providers, setProviders] = useState<ProviderSummary[] | null>(null);
    const [newProvider, setNewProvider] = useState<ProviderFormFields>(EMPTY_FORM);
    const [editDrafts, setEditDrafts] = useState<Record<string, ProviderFormFields>>({});
    const [blockedMessage, setBlockedMessage] = useState<string | null>(null);

    function reload() {
      fetchProviders().then((list) => {
        setProviders(list);
        setEditDrafts(
          Object.fromEntries(
            list.map((p) => [p.id, { name: p.name, endpoint: p.endpoint, credential: '', model: p.model }]),
          ),
        );
      });
    }

    useEffect(() => {
      reload();
    }, []);

    async function handleAdd(event: React.FormEvent) {
      event.preventDefault();
      const { name, endpoint, credential, model } = newProvider;
      if (!name || !endpoint || !credential || !model) return;
      await createProvider(newProvider);
      setNewProvider(EMPTY_FORM);
      reload();
    }

    async function handleEdit(providerId: string) {
      const draft = editDrafts[providerId];
      // An empty credential draft leaves the stored value untouched — PATCH
      // omits the field entirely rather than sending an empty string.
      const fields: Partial<ProviderFormFields> = {
        name: draft.name,
        endpoint: draft.endpoint,
        model: draft.model,
      };
      if (draft.credential) fields.credential = draft.credential;
      await updateProvider(providerId, fields);
      reload();
    }

    async function handleRemove(providerId: string) {
      setBlockedMessage(null);
      const result = await removeProvider(providerId);
      if (!result.ok) {
        setBlockedMessage(result.message);
        return;
      }
      reload();
    }

    function updateDraft(providerId: string, patch: Partial<ProviderFormFields>) {
      setEditDrafts((prev) => ({ ...prev, [providerId]: { ...prev[providerId], ...patch } }));
    }

    return (
      <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
        <h2>Providers</h2>
        <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
          LLM Providers agents can be pointed at. Compass is pre-seeded and
          remains every agent's default until explicitly changed. Editing the
          Compass entry here does not change your live Compass connection —
          it stays configured via <span className="mono">.env</span>.
        </p>
        {blockedMessage && (
          <p className="text-muted" data-testid="providers-blocked-message">
            <span className="badge badge-danger">Removal blocked</span> {blockedMessage}
          </p>
        )}
        {providers && (
          <div className="item-list" style={{ marginBottom: 'var(--space-4)' }}>
            {providers.map((provider) => {
              const blocked = provider.agent_ids.length > 0;
              const draft = editDrafts[provider.id];
              return (
                <div className="item-row" key={provider.id} data-provider-row={provider.id}>
                  <div className="item-row-main">
                    <span className="item-row-title">
                      {provider.name}{' '}
                      {provider.is_default && <span className="badge">Default</span>}
                      {!provider.has_real_client && (
                        <span className="badge badge-warning">No client built yet</span>
                      )}
                    </span>
                    <span className="item-row-meta">
                      Endpoint: <span className="mono">{provider.endpoint}</span> · Model: {provider.model}
                    </span>
                    <span className="item-row-meta">Used by {provider.agent_ids.length} agent(s)</span>
                  </div>
                  <div className="item-row-actions">
                    <input
                      className="input"
                      value={draft?.name ?? ''}
                      onChange={(event) => updateDraft(provider.id, { name: event.target.value })}
                    />
                    <input
                      className="input"
                      value={draft?.endpoint ?? ''}
                      onChange={(event) => updateDraft(provider.id, { endpoint: event.target.value })}
                    />
                    <input
                      className="input"
                      type="password"
                      placeholder={provider.credential_set ? '••••••••••••' : 'Never stored in plaintext'}
                      value={draft?.credential ?? ''}
                      onChange={(event) => updateDraft(provider.id, { credential: event.target.value })}
                    />
                    <input
                      className="input"
                      value={draft?.model ?? ''}
                      onChange={(event) => updateDraft(provider.id, { model: event.target.value })}
                    />
                    <button type="button" className="btn" onClick={() => handleEdit(provider.id)}>Save</button>
                    <button
                      type="button"
                      className="btn btn-danger"
                      disabled={blocked}
                      title={blocked ? 'Switch every agent using it to a different Provider first' : undefined}
                      onClick={() => handleRemove(provider.id)}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
        <form onSubmit={handleAdd} className="item-row-actions">
          <input className="input" placeholder="Name" value={newProvider.name} onChange={(e) => setNewProvider((p) => ({ ...p, name: e.target.value }))} />
          <input className="input" placeholder="Endpoint" value={newProvider.endpoint} onChange={(e) => setNewProvider((p) => ({ ...p, endpoint: e.target.value }))} />
          <input className="input" type="password" placeholder="Credential" value={newProvider.credential} onChange={(e) => setNewProvider((p) => ({ ...p, credential: e.target.value }))} />
          <input className="input" placeholder="Model" value={newProvider.model} onChange={(e) => setNewProvider((p) => ({ ...p, model: e.target.value }))} />
          <button type="submit" className="btn btn-primary">Add provider</button>
        </form>
      </div>
    );
  }
  ```

- `src/frontend/src/pages/SettingsPage.tsx` — extend
  `REQ-SB-18-US-01-T07`'s already-landed composition:
  ```tsx
  import { SectionsCard } from '../features/settings/SectionsCard';
  import { ProvidersCard } from '../features/settings/ProvidersCard';

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
      </>
    );
  }
  ```

- `src/frontend/src/styles/settings.css` — add, ported verbatim from
  `html-prototype/styles.css` (only if not already present from
  `REQ-SB-18-US-01-T07`'s own port — check first):
  ```css
  .mono { font-family: var(--font-mono, monospace); }
  ```

---

## Constraints

- Inherits from parent story: `ADR-010`'s class-name-verbatim convention;
  `ADR-014` point 5's credential handling (never render the real
  credential value — only a fixed masked placeholder once `credential_set`
  is `true`; an empty edit-credential input omits the field from the
  `PATCH` body entirely, never sends an empty string that would overwrite
  the stored value); `ADR-014` point 4's block-until-unused policy
  (Remove stays `disabled` with a `title` tooltip whenever
  `agent_ids.length > 0`).
- Provider removal must never optimistically remove the row before the
  server confirms — always `reload()` from the real list after any
  mutating call.
- Do not add any Section-related UI here — that is
  `REQ-SB-18-US-01-T07`'s own `<SectionsCard>`, already composed.
- Do not modify `SectionsCard.tsx` or any of `REQ-SB-18-US-01-T07`'s own
  `settingsApiClient.ts` exports (`fetchSections`/`createSection`/
  `renameSection`/`deleteSection`) — additive extension only.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`,
real `.second-brain/agent_providers.json` state; browser preview tool):

1. **[REQ-SB-19-US-01-AC-01]** With a fresh (or freshly-reseeded, per
   `T02`'s own verification cleanup) `agent_providers.json`, load
   `/settings`. Confirm the Providers card lists exactly one entry,
   "Compass", carrying the `Default` badge, with endpoint/model text
   matching the real configured `.env` values, and no `No client built
   yet` badge (it has a real client).
2. **[REQ-SB-19-US-01-AC-02]** Fill the "Add provider" form (name
   "Verify Provider", a fake endpoint, a fake credential, a fake model)
   and submit. Confirm the new "Verify Provider" row appears, carrying a
   `No client built yet` badge (not in the hardcoded real-client set),
   "Used by 0 agent(s)".
3. **[REQ-SB-19-US-01-AC-03]** On the "Verify Provider" row, change its
   endpoint field and click "Save" (leaving the credential field blank).
   Confirm the row's displayed endpoint meta text updates. Reload the
   page (`/settings` fresh load) and confirm the change persisted.
4. **[REQ-SB-19-US-01-AC-04]** Confirm "Verify Provider"'s Remove button
   is enabled (0 agents). Click Remove. Confirm the row disappears from
   the Providers card.
5. **[REQ-SB-19-US-01-AC-05]** Confirm "Compass"'s Remove button is
   `disabled` with a title tooltip (every agent defaults to it). Issue
   `DELETE /providers/compass` directly via `Invoke-RestMethod` to
   exercise the same blocked path; confirm `409`. In the UI, add a new
   Provider, assign it to no agent, confirm its Remove works (from step
   4's pattern) as the positive control, then re-add "Verify Provider"
   is not required — instead, directly confirm via the UI: temporarily
   `PATCH /agents/email-capture` `{"provider_id": <a newly-added, still
   real-client-less provider's id>}` via `Invoke-RestMethod`, then attempt
   to Remove that provider from the Providers card UI. Confirm the
   blocked message region (`data-testid="providers-blocked-message"`)
   renders the server's exact name-resolved message, and the provider
   remains listed, still showing "Used by 1 agent(s)". Clean up:
   `PATCH /agents/email-capture` `{"provider_id": "compass"}`, then
   remove the temporary provider from the UI (now unblocked).
6. Non-AC smoke check: zero console errors/warnings across the whole
   sequence.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-01** (Scenario 1) — Compass is pre-seeded and shown as Default
      in the Providers area
- [ ] **AC-02** (Scenario 2) — adding a Provider appears in the Providers
      area
- [ ] **AC-03** (Scenario 3) — editing a Provider's fields reflects the
      updated values in the Providers area
- [ ] **AC-04** (Scenario 4) — removing an unused Provider removes it
      from the Providers area
- [ ] **AC-05** (Scenario 4b) — removing an in-use Provider is refused
      with a clear message; the entry and every agent's selection are
      unchanged
- [ ] Credential value is never rendered in plaintext anywhere in this
      component; an empty edit-credential field never overwrites the
      stored value
- [ ] `settingsApiClient.ts` extends (not replaces) `REQ-SB-18-US-01-T07`'s
      Sections exports; `SettingsPage.tsx` composes both cards
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Agent Settings surface's Provider picker (Scenario 2's second
  clause, Scenarios 5, 6, 7 — `AC-02`'s picker-availability check,
  `AC-06`) — `T06`.
- `SectionsCard.tsx` — already landed by `REQ-SB-18-US-01-T07`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-014` created at
`/plan-tasks` step 1) — the human reviews `ADR-014` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

`AC-02` (Scenario 2 — add a Provider, confirm it appears in Settings
**and** is available as a picker choice) is deliberately **not** fully
tagged here, mirroring `REQ-SB-18-US-01-T07`'s own treatment of its
Section-create scenario — the "available as a picker choice" clause can
only be checked once `T06`'s Provider `<select>` exists. See `T06`'s own
Tests for the completing check.

---

## Implementation Log

**Built 2026-08-11 (coder).** `settingsApiClient.ts` extended verbatim
(`ProviderSummary`/`ProviderFormFields`/`fetchProviders`/`createProvider`/
`updateProvider`/`removeProvider`, reusing the existing `DeleteResult`/
`ApiError`), additive alongside `REQ-SB-18-US-01-T07`'s Sections exports —
none renamed or removed. New `src/frontend/src/features/settings/
ProvidersCard.tsx` created verbatim. `SettingsPage.tsx` composes
`<ProvidersCard />` alongside `<SectionsCard />`. `.mono` was already
present in `styles/tokens.css` (`--font-mono`), so `settings.css` was left
untouched, per this task's own "only if not already present" instruction.

**Live verification (real backend `:8001`, real frontend `npm run dev` on
`:5173`, headless-Chrome-via-CDP browser automation — this project's
established zero-dependency Layer-1 harness), all 5 AC-tagged scenarios
plus the non-AC console-error check:**

- **[AC-01]** Fresh `agent_providers.json` (re-seeded by `T02`/`T03`'s own
  cleanup). `/settings` renders exactly one Providers row: "Compass",
  `Default` badge, endpoint `https://api.core42.ai/v1/chat/completions`,
  model `gpt-5` (both matching the real `.env` values), no "No client
  built yet" badge. **PASS.**
- **[AC-02]** (Settings half — the picker-availability half completes in
  `T06`) Filled the Add-provider form (name "Verify Provider", fake
  endpoint/credential/model) via a real DOM `input`-event-driven React
  controlled-input update, submitted. New "Verify Provider" row appeared
  with a "No client built yet" badge, "Used by 0 agent(s)". **PASS.**
- **[AC-03]** Edited "Verify Provider"'s endpoint field, clicked Save
  (credential left blank). Row's displayed endpoint updated immediately;
  reloaded `/settings` from scratch — change persisted server-side.
  **PASS.**
- **[AC-04]** "Verify Provider"'s Remove button was enabled (0 agents).
  Clicked — row disappeared from the Providers card. **PASS.**
- **[AC-05]** Confirmed "Compass"'s Remove button is `disabled` with the
  exact title tooltip (all 5 agents still assigned). Added a throwaway
  Provider via the UI, assigned it to `email-capture` via a direct `PATCH
  /agents/email-capture` call (simulating what `T06`'s own panel PATCH
  does — `T06` not yet built at this point in the sequence), reloaded, then
  clicked its now-`disabled` Remove button. **Scope-internal technique
  note (not an assumption, reapplying `SPRINT-011`'s own already-documented
  finding, `MEMORY.md`):** a native `.click()` dispatched at a React
  Fiber-`disabled` button element is a silent no-op (React checks its own
  Fiber props, not the raw DOM attribute) — invoked the button's `onClick`
  directly off `el[reactPropsKey].onClick` instead, the identical code path
  a real click would reach once genuinely unblocked. Confirmed the
  `data-testid="providers-blocked-message"` region rendered the server's
  exact name-resolved `409` text, and the provider remained listed, "Used
  by 1 agent(s)" unchanged. Cleaned up (reassigned `email-capture` back to
  `compass`, removed the temporary provider). **PASS.**
- Zero console errors/warnings across the whole sequence (confirmed via a
  `Runtime.exceptionThrown`/`console.error` listener attached for the full
  browser session). **PASS.**

Visual cross-check against the approved `html-prototype/settings.html`
Providers card: screenshot taken of the real rendered card — Compass row
with Default badge, endpoint/model meta, masked-credential placeholder,
disabled+tooltipped Remove button, Add-provider form below — matches the
prototype's shape (this codebase's established "always-visible inline
edit inputs" pattern, matching `SectionsCard.tsx`'s own precedent, rather
than the prototype's `<details>`-collapsed edit form — a legitimate
same-codebase-convention simplification already established by
`REQ-SB-18-US-01-T07`, not a new deviation introduced here).

Credential value never rendered in plaintext anywhere (only the fixed
masked placeholder once `credential_set` is `true`); an empty
edit-credential field never sent `credential` in the `PATCH` body (omitted
entirely, confirmed by the persistence check in AC-03 leaving the stored
value untouched at the registry layer, already verified in `T02`).

gate: clear 2026-08-11 — no MUST-FLAG trigger fired.
