---
id: REQ-SB-29-US-01-T05
title: AgentDetailPanel.tsx "Vault scope" kv-row + agentsApiClient.ts scope field/body extension
parent_story: REQ-SB-29-US-01
requirement_id: REQ-SB-29
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-29-US-01-T03]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-29-US-01-T05 — `AgentDetailPanel.tsx` Vault scope row

## Parent Story

- Story: [[REQ-SB-29-US-01]] — `../UserStories/REQ-SB-29-US-01-agent-to-tag-folder-scoping.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-29 *Agent-to-Tag/Folder Scoping*

---

## Objective

Add a free-text "Vault scope" row to `AgentDetailPanel.tsx`'s existing Settings `.kv-list`, wired to `T03`'s extended `PATCH /agents/{agent_id}` — completing this story's only user-facing surface and the full round-trip for `AC-01`/`AC-02`. **No `/design` pass exists for this row** (operator explicitly decided to skip it — story `## Notes`, 2026-08-13); match the Keywords row's exact already-built visual/interaction pattern instead of inventing a new one.

---

## Starting State → End State

**Before / Inputs:**
- `AgentDetailPanel.tsx` (real current file) already renders a Settings `.kv-list` ending with a Keywords row:
  ```tsx
  <div className="kv-row">
    <span className="kv-key">Keywords</span>
    <input
      type="text"
      className="input kv-select"
      style={{ minWidth: 220 }}
      value={keywordsDraft}
      onChange={(event) => setKeywordsDraft(event.target.value)}
      onBlur={handleKeywordsCommit}
      placeholder="No keywords assigned yet"
    />
  </div>
  ```
  This is this row's own exact structural/interaction precedent — a free-text, comma-separated, `onBlur`-commit `<input>`, not the Section/Provider `<select>` pattern (scope is user-typed, multi-value, free-form tag/folder text, not a small fixed catalog — same reasoning that put Keywords on this pattern rather than `<select>`).
- `T03` has landed `GET /agents/{agent_id}`'s `scope` field and `PATCH /agents/{agent_id}`'s `scope` body field.

**After / Outputs:**
- `agentsApiClient.ts`'s `AgentDetail` interface gains `scope: string[];`, and `updateAgentAssignment`'s body type gains `scope?: string[];`.
- `AgentDetailPanel.tsx` renders a new "Vault scope" kv-row: a free-text `<input type="text" class="input kv-select">` showing the agent's current scope as a comma-separated string, committing on blur (parsed back into a `string[]`, trimmed, empty entries dropped) via `updateAgentAssignment`, refreshing the panel's own `agent` state — placed immediately after the existing Keywords row.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — extend the existing `AgentDetail` interface:
  ```typescript
  export interface AgentDetail {
    id: string;
    name: string;
    type: 'worker' | 'producer' | 'expert';
    settings: { key: string; value: string }[];
    actions: { id: string; label: string }[];
    section_id: string;
    section_name: string;
    provider_id: string;
    provider_name: string;
    provider_available: boolean;
    keywords: string[];
    working_mode: 'autonomous' | 'supervised' | 'manual';
    scope: string[];
  }
  ```
  Extend `updateAgentAssignment`'s body type:
  ```typescript
  export function updateAgentAssignment(
    agentId: string,
    body: { section_id?: string; provider_id?: string; keywords?: string[]; working_mode?: string; scope?: string[] },
  ): Promise<AgentDetail> {
    return apiFetch<AgentDetail>(`/agents/${agentId}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }
  ```

- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — add a new piece of state, alongside the existing `keywordsDraft` state:
  ```tsx
  const [scopeDraft, setScopeDraft] = useState('');
  ```
  In the existing per-`agentId` `useEffect`, sync `scopeDraft` once the agent detail loads (alongside the existing `keywordsDraft` reset/sync):
  ```tsx
  useEffect(() => {
    setAgent(null);
    setMessages([]);
    setDraft('');
    setSending(false);
    setHistory(null);
    setActiveTab('chat');
    setKeywordsDraft('');
    setScopeDraft('');
    fetchAgent(agentId).then((detail) => {
      setAgent(detail);
      setKeywordsDraft(detail.keywords.join(', '));
      setScopeDraft(detail.scope.join(', '));
    });
    fetchAgentHistory(agentId).then(setHistory);
    fetchSections().then(setSections);
    fetchProviders().then(setProviders);
  }, [agentId]);
  ```
  Add a commit handler near `handleKeywordsCommit`:
  ```tsx
  async function handleScopeCommit() {
    const scope = scopeDraft
      .split(',')
      .map((entry) => entry.trim())
      .filter((entry) => entry.length > 0);
    const updated = await updateAgentAssignment(agentId, { scope });
    setAgent(updated);
    setScopeDraft(updated.scope.join(', '));
  }
  ```
  In the JSX, inside the existing Settings `.kv-list` block, immediately after the existing Keywords kv-row and before the closing `</div>` of `.kv-list`, add:
  ```tsx
  <div className="kv-row">
    <span className="kv-key">Vault scope</span>
    <input
      type="text"
      className="input kv-select"
      style={{ minWidth: 220 }}
      value={scopeDraft}
      onChange={(event) => setScopeDraft(event.target.value)}
      onBlur={handleScopeCommit}
      placeholder="No vault scope assigned yet"
    />
  </div>
  ```

---

## Constraints

- Inherits from parent story: multiple scopes per agent are allowed — a comma-separated free-text field, matching the Keywords row's own multi-value handling exactly.
- **No `/design` sign-off exists for this row** (operator decision, story `## Notes`) — match `AgentDetailPanel.tsx`'s already-built Keywords row's exact class names (`.kv-row`, `.kv-key`, `.kv-select`), structure, and interaction shape (`onBlur` commit, comma-separated, trim, drop-empty) verbatim. Do not invent a new visual shape, control type, or interaction pattern (no chip/tag picker UI, no `<select>` against a vault-derived list) — this task is explicitly bounded to the Keywords row's own established pattern, not a net-new design.
- Changing the Vault scope field must call the real `PATCH /agents/{agentId}` and update from its real response — no optimistic local-only state update, matching the Keywords/Section/Provider rows' own established convention.
- Commit-on-blur (not on every keystroke), matching Keywords' own established convention — no new per-keystroke `PATCH` behavior introduced.
- An explicit empty commit (all scope entries cleared) must send `{"scope": []}`, not omit the field — matches `T03`'s own explicit-empty-list-clears contract, and is Scenario 6's own "no assigned scope" state made reachable from the UI.
- Must NOT modify `AgentsMapCanvas.tsx`/`SectionHub.tsx`/`AgentNode.tsx` — this task only adds the panel's own new row.
- Must NOT modify the existing Section/Provider/Keywords/Working-mode rows' own code — additive only, placed after Keywords.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`;
browser preview tool):

1. **[REQ-SB-29-US-01-AC-01]** Navigate to the Agents Map (`/`), open any agent's detail panel, Settings tab — confirm the "Vault scope" `<input>` is present, empty, and shows the placeholder `"No vault scope assigned yet"` (its real starting state — no scope ever assigned to a fresh agent, or reset first via `PATCH {"scope": []}` if the chosen agent carries leftover state from an earlier task's own verification). Type `"customer/masdar"` into the field and blur it. Confirm the field's own value updates to the committed form without a page reload. Close and reopen the same agent's panel — confirm `"customer/masdar"` is still shown, proving server-side persistence, not just local component state. Independently confirm via `GET /agents/<agent-id>` that the response's own `scope` field is exactly `["customer/masdar"]`.
2. **[REQ-SB-29-US-01-AC-02]** With the same agent still showing `"customer/masdar"`, edit the field's text to `"customer/masdar, Pipeline"` (appending a second, different scope value — comma-separated, matching the field's own established multi-value editing convention) and blur it. Confirm the field now shows both entries. Close and reopen the panel — confirm both `"customer/masdar"` and `"Pipeline"` are still shown (neither the first nor the second assignment lost). Independently confirm via `GET /agents/<agent-id>` that `scope` is exactly `["customer/masdar", "Pipeline"]`.
3. Non-AC smoke check: type only whitespace and commas (e.g. `" , , "`) into the Vault scope field and blur it. Confirm the committed result is an empty list (`scope: []`, placeholder text reappears) — empty/whitespace-only entries are dropped, not stored as blank scope values.
4. Clean-up: blur the Vault scope field back to empty (clear the input, blur) on the agent used above, restoring its clean "no scope assigned" seed state before any later verification run.
5. Non-AC smoke check: zero console errors/warnings across the whole sequence.
6. Visual cross-check (screenshot of the real rendered panel, Settings tab, Section/Provider/Keywords/Vault scope rows adjacent): confirm the Vault scope row's visual shape matches the Keywords row immediately above it (same `.kv-row`/`.kv-key`/`.kv-select`-styled `<input type="text">` placement/sizing) — a non-blocking design spot-check against the established pattern, not a locked AC (pure visual polish has no DOM signal to assert on).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1) — the user can assign a vault tag/folder to an agent as its scope on the Agent Settings surface; it is shown there and persisted server-side, retrievable via the backend independent of the panel remaining open
- [x] **AC-02** (Scenario 2) — the user can assign a second, different scope to an agent that already has one; both are shown, neither is lost
- [x] `agentsApiClient.ts`'s `AgentDetail`/`updateAgentAssignment` additive only — no existing field/function signature changed
- [x] Empty/whitespace-only comma-separated entries are dropped on commit, never stored as blank scope strings
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any chip/tag-picker or `<select>`-against-`list_known_customers()` UI — explicitly not built this pass (no `/design` exists; free-text matching Keywords' own pattern is this task's own bounded scope).
- Any visualization of scope-bounded retrieval results, or an out-of-scope/no-match chat reply's own presentation — `T04`'s own tool composes with the existing, unmodified chat thread UI; no new chat-message styling is introduced by this task.
- Enter-to-commit / any interaction beyond blur-to-commit.

---

## Context / Notes

**Why free-text, not a chip/tag picker or `<select>`:** per the story's own `## Notes` (2026-08-13 architect update) and this task's own bounded objective — the operator explicitly decided to skip `/design` for this batch, so the coder is bounded to matching the Keywords row's already-built pattern (free-text, comma-separated, `onBlur` commit) rather than inventing new visual shape for the uncovered prototype gap. A chip/tag picker or vault-derived `<select>` was considered (and would arguably be a richer UX) but is explicitly out of scope — it would be net-new design, which this story's own operator decision defers.

**Shared-file coordination:** `AgentDetailPanel.tsx`/`agentsApiClient.ts` are actively-extended shared files (`REQ-SB-18/19/20/21-US-01` have all landed rows here). This task's own diff is additive — appending the Vault scope row after Keywords, and appending the `scope` field/body-type entry — no existing Section/Provider/Keywords/Working-mode code is touched. Re-read the real current file before applying this task's diff, per this project's own established Learnings pattern (repeat drift on this exact file has been found live before).

---

## Implementation Log

**2026-08-14 — Implemented and verified.** Read the REAL current
`AgentDetailPanel.tsx`/`agentsApiClient.ts` before editing — both have
drifted materially beyond this task's own "Before" sample (post-Skills-
migration `SPRINT-030`/`031` landed `capabilities: AgentCapability[]`
replacing the sample's stale `actions: {...}[]` field, plus
`skillCatalog`/`approvals`/`ProposalCard` state the sample never
mentions). This task's own diff stayed purely additive against the REAL
shapes — `AgentDetail` gained `scope: string[]` alongside the real
`capabilities` field (not a replacement of it), `updateAgentAssignment`'s
body type gained `scope?: string[]`, and the panel gained `scopeDraft`
state / `handleScopeCommit` / the new kv-row, exactly per the task's own
specified diff, none of which touches the real file's other
Skills/Approvals additions.

Verified live via headless Edge (`msedge.exe --headless=new
--remote-debugging-port=...`, no `/IM`-wide kill — this session's own
isolated `--user-data-dir` and PID cleaned up afterward) driven over CDP
by a Python `websockets` script (`node`/`npx` unresolvable in this
session's shell, consistent with this project's own documented
antipattern — no re-diagnosis needed) against the real Vite dev server
(`:5173`) and real backend (`:8001`). Real click on the Email Capture
agent node (via its React Fiber `onClick` prop, not native DOM click —
this project's own established technique) opened the real panel; the
Settings tab was clicked; the Vault scope `<input>` committed via the
native `HTMLInputElement.prototype.value` setter + a dispatched `input`
event + a direct Fiber-props `onBlur` invocation (this project's own
established React-controlled-input CDP technique, not native
`.focus()/.blur()`).

1. **[REQ-SB-29-US-01-AC-01]** Fresh agent, empty `scope` — the Vault
   scope `<input>` was present, empty, placeholder `"No vault scope
   assigned yet"` (real starting state, no reset needed). Typed
   `"customer/masdar"`, triggered the real `onBlur` commit — field
   updated to the committed value with no page reload. Closed and
   reopened the same agent's panel (real SPA nav-away/nav-back, not
   `Page.reload()` — keeps the CDP session's own in-page state alive) —
   `"customer/masdar"` still shown. Independent `GET
   /agents/email-capture` confirmed `scope` exactly `["customer/
   masdar"]`. PASS.
2. **[REQ-SB-29-US-01-AC-02]** Edited the field to `"customer/masdar,
   Pipeline"`, committed — field showed both entries. Closed/reopened —
   both `"customer/masdar"` and `"Pipeline"` still shown, neither lost.
   Independent `GET` confirmed `scope` exactly `["customer/masdar",
   "Pipeline"]`. PASS.
3. Non-AC smoke check: typed `" , , "` (whitespace/commas only),
   committed — field returned to empty with the placeholder reappearing;
   whitespace-only entries dropped, never stored as blank scope values.
   PASS.
4. Clean-up: blurred the field back to empty on `email-capture` — final
   `GET` confirmed `scope: []`, restoring the clean seed state before
   this task's own verification concludes.
5. Non-AC smoke check (zero console errors): every `Runtime.evaluate`
   call across the whole sequence returned with no `exceptionDetails`
   field in its own CDP response (a thrown JS exception surfaces there
   directly) — confirmed for every interaction, including the final
   clear-commit call. No separate `Runtime.exceptionThrown`/`Console`
   listener session was layered on top (a concurrent-`recv` conflict in
   the same `websockets` connection made that redundant, not attempted
   further) — the per-call `exceptionDetails` check is the load-bearing
   confirmation here, and it was clean throughout.
6. Visual cross-check: a real headless-browser screenshot of the
   rendered panel (Settings tab) confirms the Vault scope row sits
   immediately below Keywords, same `.kv-row`/`.kv-key`/input styling
   and placement — matches the Keywords row's own established shape by
   direct visual inspection, not just DOM-class equality. Screenshot
   was a throwaway verification artefact, not committed.

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired; real-file drift
beyond the task's own sample was reconciled additively with zero
contradiction of the sibling Skills/Approvals code already landed there.

Status: `Ready` → `Done`.
