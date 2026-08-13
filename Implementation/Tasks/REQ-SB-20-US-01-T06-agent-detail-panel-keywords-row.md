---
id: REQ-SB-20-US-01-T06
title: AgentDetailPanel.tsx Keywords kv-row + agentsApiClient.ts keywords field/body extension
parent_story: REQ-SB-20-US-01
requirement_id: REQ-SB-20
type: frontend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-017 created) — carried from the parent story; the human reviews ADR-017 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-20-US-01-T03]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-20-US-01-T06 — `AgentDetailPanel.tsx` Keywords row

## Parent Story

- Story: [[REQ-SB-20-US-01]] — `../UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-20 *Section Hub Intelligence & Cross-Section Routing*

---

## Objective

Add a free-text Keywords row to `AgentDetailPanel.tsx`'s existing Settings
`.kv-list`, per the approved `html-prototype/agents-map.html` side panel
(sign-off recorded `REVIEW-QUEUE.md` 2026-08-12), wired to `T03`'s extended
`PATCH /agents/{agent_id}` — completing this story's only user-facing
surface and the full round-trip for `AC-01`.

---

## Starting State → End State

**Before / Inputs:**
- `AgentDetailPanel.tsx` (`REQ-SB-13-US-01`/`REQ-SB-18-US-01`/`REQ-SB-19-US-01`)
  already renders a Settings `.kv-list` with the agent's static settings
  rows, then Section and Provider `<select>` kv-rows — no Keywords row yet
  (real current file, verbatim relevant excerpt):
  ```tsx
  <div className="kv-row">
    <span className="kv-key">Provider</span>
    {providers && (
      <select
        className="input kv-select"
        value={agent.provider_id}
        onChange={(event) => handleProviderChange(event.target.value)}
      >
        {providers.map((provider) => (
          <option key={provider.id} value={provider.id}>
            {provider.name}{provider.is_default ? ' (default)' : ''}
          </option>
        ))}
      </select>
    )}
  </div>
  {!agent.provider_available && (
    <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
      {agent.provider_name} has no real client built yet — this agent
      honestly reports it's not available rather than silently falling
      back to Compass.
    </p>
  )}
  ```
- `T03` has landed `GET /agents/{agent_id}`'s `keywords` field and
  `PATCH /agents/{agent_id}`'s `keywords` body field.
- Approved prototype markup (`html-prototype/agents-map.html`, per the
  design sign-off):
  ```html
  <div class="kv-row"><span class="kv-key">Keywords</span>
    <input type="text" class="input kv-select" style="min-width:220px;" value="email, inbox, customer correspondence, message classification" />
  </div>
  ```
  and, for an agent with none assigned:
  ```html
  <div class="kv-row"><span class="kv-key">Keywords</span>
    <input type="text" class="input kv-select" style="min-width:220px;" value="" placeholder="No keywords assigned yet" />
  </div>
  ```

**After / Outputs:**
- `agentsApiClient.ts`'s `AgentDetail` interface gains `keywords: string[];`,
  and `updateAgentAssignment`'s body type gains `keywords?: string[];`.
- `AgentDetailPanel.tsx` renders a new `Keywords` kv-row: a free-text
  `<input type="text" class="input kv-select">` showing the agent's current
  keywords as a comma-separated string, committing on blur (parsed back
  into a `string[]`, trimmed, empty entries dropped) via
  `updateAgentAssignment`, refreshing the panel's own `agent` state.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — extend the
  existing `AgentDetail` interface:
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
  }
  ```
  Extend `updateAgentAssignment`'s body type:
  ```typescript
  export function updateAgentAssignment(
    agentId: string,
    body: { section_id?: string; provider_id?: string; keywords?: string[] },
  ): Promise<AgentDetail> {
    return apiFetch<AgentDetail>(`/agents/${agentId}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }
  ```

- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` — add a new
  piece of state, alongside the existing `agent`/`sections`/`providers`
  state:
  ```tsx
  const [keywordsDraft, setKeywordsDraft] = useState('');
  ```
  In the existing per-`agentId` `useEffect`, sync `keywordsDraft` once the
  agent detail loads:
  ```tsx
  useEffect(() => {
    setAgent(null);
    setMessages([]);
    setDraft('');
    setHistory(null);
    setKeywordsDraft('');
    fetchAgent(agentId).then((detail) => {
      setAgent(detail);
      setKeywordsDraft(detail.keywords.join(', '));
    });
    fetchAgentHistory(agentId).then(setHistory);
    fetchSections().then(setSections);
    fetchProviders().then(setProviders);
  }, [agentId]);
  ```
  Add a commit handler near `handleSectionChange`/`handleProviderChange`:
  ```tsx
  async function handleKeywordsCommit() {
    const keywords = keywordsDraft
      .split(',')
      .map((keyword) => keyword.trim())
      .filter((keyword) => keyword.length > 0);
    const updated = await updateAgentAssignment(agentId, { keywords });
    setAgent(updated);
    setKeywordsDraft(updated.keywords.join(', '));
  }
  ```
  In the JSX, inside the existing Settings `.kv-list` block, immediately
  after the Provider kv-row (and its `!agent.provider_available` message,
  if present) and before the closing `</div>` of `.kv-list`, add:
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

---

## Constraints

- Inherits from parent story: `ADR-010`'s class-name-verbatim convention
  (`.kv-row`, `.kv-key`, `.kv-select` matching `html-prototype/
  agents-map.html`'s side panel shape exactly, per the approved design —
  reusing the existing `.kv-select` sizing class on a free-text `<input
  type="text">` rather than a `<select>`, exactly as the approved prototype
  does; no new CSS needed).
- Changing the Keywords field must call the real `PATCH /agents/{agentId}`
  and update from its real response — no optimistic local-only state
  update, matching the Section/Provider rows' own established convention.
- Commit-on-blur (not on every keystroke) — a free-text field firing a
  `PATCH` per keystroke would spam the API; this is a scope-internal UX
  judgement call (no existing free-text-commit precedent in this codebase
  to mirror exactly), logged here rather than left implicit. Pressing
  Enter is not separately handled this pass — blur (including tabbing away
  or closing the panel) is the only commit trigger; a future story may add
  an Enter-to-commit affordance if asked for.
- An explicit empty commit (all keywords cleared) must send `{"keywords":
  []}`, not omit the field — matches `T03`'s own explicit-empty-list-clears
  contract.
- Must NOT modify `AgentsMapCanvas.tsx`/`SectionHub.tsx`/`AgentNode.tsx` —
  this task only adds the panel's own new row.
- Must NOT add a Working-mode row or any other new kv-row — out of this
  story's scope (`REQ-SB-21-US-01`'s own future concern).

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`;
browser preview tool):

1. **[REQ-SB-20-US-01-AC-01]** Navigate to the Agents Map (`/`), click
   `todo-capture`'s (To-Do Capture) `.agent-node` to open its detail panel
   — confirm the Keywords `<input>` is present, empty, and shows the
   placeholder `"No keywords assigned yet"` (its real starting state — no
   keywords ever assigned). Type `"email, inbox, customer correspondence"`
   into the field and blur it (click elsewhere in the panel). Confirm the
   field's own value updates to the committed, trimmed form without a page
   reload. Close and reopen the same agent's panel — confirm the same
   3 keywords are still shown, proving server-side persistence, not just
   local component state. Independently confirm via `GET
   /agents/todo-capture` that the response's own `keywords` field is
   `["email", "inbox", "customer correspondence"]` — this is the "the
   agent's Section's Hub has access to those keywords for routing
   purposes" clause made concrete: the value is backend-persisted and
   retrievable independent of the panel remaining open, exactly the shape
   `T05`'s routing node reads via `agent_keywords.get_agent_keywords`/
   `load_all_agent_keywords`.
2. Non-AC smoke check: type only whitespace and commas (e.g. `" , , "`)
   into the Keywords field and blur it. Confirm the committed result is an
   empty list (`keywords: []`, placeholder text reappears) — empty/
   whitespace-only entries are dropped, not stored as blank keywords.
3. Clean-up: blur the Keywords field back to empty (clear the input, blur)
   on `todo-capture`, restoring its clean "no keywords assigned" seed
   state before any later verification run.
4. Non-AC smoke check: zero console errors/warnings across the whole
   sequence.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1) — the user can assign one or more free-text
      keywords on the Agent Settings surface; they are shown there and
      persisted server-side, retrievable via the backend independent of
      the panel remaining open
- [x] `agentsApiClient.ts`'s `AgentDetail`/`updateAgentAssignment` additive
      only — no existing field/function signature changed
- [x] Empty/whitespace-only comma-separated entries are dropped on commit,
      never stored as blank keyword strings
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Working-mode kv-row, chat pending-approval UI — `REQ-SB-21-US-01`'s own
  scope, unrelated to this story.
- Any visualization of Hub-to-Hub routing on the Agents Map canvas — this
  story's own Non-Goals rule this out explicitly.
- Enter-to-commit / any interaction beyond blur-to-commit — not asked for
  by this story's own Acceptance text; a future story's own concern if
  requested.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-017` created at
`/plan-tasks` step 1) — the human reviews `ADR-017` and this task breakdown
together; the pipeline does not halt, so this task proceeds to `Ready`
alongside the rest of the story.

**Why `agentsApiClient.ts` is extended directly, not a new
`agentKeywordsApiClient.ts` file:** the architect's own `Architecture
scope` note in the story's `## Notes` left the exact file naming to this
decomposition pass ("exact file naming left to the decomposer"). Given the
extremely strong, twice-repeated precedent of extending this SAME file's
`AgentDetail` interface and `updateAgentAssignment`'s body type
(`REQ-SB-18-US-01-T08` for `section_id`, `REQ-SB-19-US-01-T06` for
`provider_id`) rather than a parallel per-concern client file, this task
follows that identical, already-established pattern — consistent, avoids
proliferation, and reuses the project's own "no independent value alone"
reasoning already applied elsewhere (this story's own `## Notes`
"Scoping decision" section makes the same argument for keeping this story
as one unit). A separate `agentKeywordsApiClient.ts` was considered and
rejected as inconsistent with both sibling tasks' own precedent.

**Shared-file coordination:** `AgentDetailPanel.tsx`/`agentsApiClient.ts`
were most recently landed by `REQ-SB-19-US-01-T06` (the Provider row, the
last task to touch these files). This task's own diff is additive —
appending the Keywords row after Provider's, and appending the `keywords`
field/body-type entry — no existing Section/Provider code is touched.

---

## Implementation Log

**Built 2026-08-12 (coder).** `agentsApiClient.ts`'s `AgentDetail` gained
`keywords: string[]`, `updateAgentAssignment`'s body type gained
`keywords?: string[]` — both additive, verbatim per this task's own code
block. `AgentDetailPanel.tsx` gained `keywordsDraft` state, synced from
`detail.keywords.join(', ')` in the existing per-agent-switch `useEffect`,
`handleKeywordsCommit` (parses comma-separated, trims, drops empty
entries, calls `updateAgentAssignment`, refreshes `agent`/`keywordsDraft`
from the real response), and the new Keywords kv-row placed immediately
after the Provider row + its conditional unavailability message, inside
the same Settings `.kv-list` — verbatim per this task's own code block.

**Live verification (real backend `:8001`, real frontend `npm run dev`
on `:5173`, headless-Chrome-via-CDP — this project's own established
zero-dependency pattern, `MEMORY.md` Patterns):**

- **[AC-01]** Opened `todo-capture`'s detail panel, Settings tab — Keywords
  `<input>` present, empty, placeholder `"No keywords assigned yet"` (real
  starting state, never assigned). Committed `"email, inbox, customer
  correspondence"` — field updated to the trimmed, committed form with no
  page reload. Closed and reopened the same agent's panel — the same 3
  keywords were still shown (proving server-side persistence, not local
  component state). Independently confirmed via a real `GET
  /agents/todo-capture` (issued from inside the browser page, not the
  React app's own fetch path) that the response's `keywords` field was
  exactly `["email", "inbox", "customer correspondence"]`. **PASS.**
- Non-AC smoke check: committed `" , , "` (whitespace/commas only) —
  resulting `keywords` was `[]` (confirmed both in the UI, which reverted
  to the placeholder, and via the real backend `GET`) — empty/whitespace
  entries dropped, never stored as blank keyword strings. **PASS.**
- Clean-up: `todo-capture`'s Keywords committed back to empty (already
  achieved by the whitespace-only test above) — confirmed `[]` via `GET`,
  real seed "no keywords assigned" state restored.
- Zero console errors/warnings across the whole sequence (`Runtime.
  consoleAPICalled`/`Runtime.exceptionThrown` both monitored via CDP for
  the full interaction). **PASS.**
- Visual cross-check (screenshot of the real rendered panel, To-Do Capture,
  Settings tab, Section/Provider/Keywords kv-rows adjacent, keywords
  committed and visible): matches the approved prototype's Keywords
  kv-row shape (`html-prototype/agents-map.html`'s side panel, 2026-08-12
  design sign-off) — same `.kv-row`/`.kv-key`/`.kv-select`-styled
  `<input type="text">` placement immediately below Provider.

**Scope-internal finding, logged (not an escalation):** dispatching a
plain synthetic `blur` `Event` at the `<input>` (with `bubbles: true`) did
**not** reliably reach React's delegated `onBlur` handler in this headless-
Chrome-via-CDP session, even after a real `input.focus()`/`input.blur()`
DOM-API call pair (confirmed `document.activeElement` genuinely changed,
yet no `PATCH` request was observed via the CDP `Network` domain) — React's
`onBlur` is wired to native `focusout` bubbling, and this specific headless
session did not deliver it reliably via either synthetic dispatch or a
real `.blur()` call. Resolved via this project's own already-documented
React-Fiber-props-direct-invoke pattern (`MEMORY.md` Patterns, found live
`REQ-SB-18-US-01-T07`): read the real `onBlur` handler off the input's own
`__reactProps$...` key and invoked it directly with `{ target: input }` —
confirmed this fires the identical real `handleKeywordsCommit` code path
(a real `PATCH /agents/todo-capture` was observed immediately after,
carrying the exact typed value) before relying on it for the rest of this
task's own verification sequence.

gate: flagged (carried, `ADR-017` — unresolved by this task itself, per
its own gating note; the Fiber-props-direct-invoke deviation above is a
scope-internal verification-technique judgement call, not a code/AC
change, logged for human spot-check per the same rule).

**This is the last task in `REQ-SB-20-US-01`'s own 6-task breakdown.**
Every locked AC (`AC-01` here; `AC-02`/`AC-03`/`AC-04` at `T05`) now has a
passing, tagged, live-verified check.
