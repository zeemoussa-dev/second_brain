---
id: REQ-SB-66-US-01-T07
title: New standalone Job-Settings-only component + AgentsMapPage.tsx conditional-mount wiring (ADR-044)
parent_story: REQ-SB-66-US-01
requirement_id: REQ-SB-66
type: frontend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-044) — carried from the parent story's architect pass. This task directly implements ADR-044's own Decision 3 (a genuinely separate, minimal frontend component, never a widening of AgentDetailPanel.tsx's shared tab machinery) and the parent story's own Scenario 7 (a Job becomes clickable, opening a real Settings-only view for the first time — a material narrowing of ADR-041/ADR-043 point 6). A REVIEW-QUEUE.md entry exists at the story level for human review of ADR-044 itself; it does not block this task's build. See ADR.md (ADR-044) and REVIEW-QUEUE.md."
phase: P1
depends_on: [REQ-SB-66-US-01-T06, REQ-SB-65-US-01-T02]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-66-US-01-T07 — Job-Settings frontend shell

## Parent Story

- Story: [[REQ-SB-66-US-01]] — `../UserStories/REQ-SB-66-US-01-real-editable-prompt-and-guardrails-placeholder.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-66 *Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings*

---

## Objective

Add a new, small, standalone `JobSettingsPanel`-equivalent component (Settings-only
— Prompt where a real call site exists, Guardrails always; no Chat/History/
Working-Mode/Schedule/Visual) and wire `AgentsMapPage.tsx` to mount it in place of
`AgentDetailPanel` whenever `selectedAgentId` is a known Job id — reusing the SAME
already-fetched `fetchAgentJobs(EMAIL_CAPTURE_PIPELINE_AGENT_ID)` list
`pipelineJobTreeAdapter.ts` already consumes (no new fetch for the Job-id-detection
itself), per `ADR-044` Decision 3.

---

## Starting State → End State

**Before / Inputs:**
- `AgentsMapPage.tsx`'s `refreshAgents()` already does
  `Promise.all([fetchAgentList(), fetchSections(), fetchAgentJobs(
  EMAIL_CAPTURE_PIPELINE_AGENT_ID).catch(() => [])])`, then
  `spliceEmailCapturePipelineJobTree(agentList, jobList)` — but `jobList` itself is
  a local variable inside the `.then()` callback today, never stored in component
  state; nothing outside that callback can currently ask "is this id a real Job
  id?".
- `AgentsMapPage.tsx`'s conditional mount is currently `{selectedAgentId &&
  <AgentDetailPanel agentId={selectedAgentId} onClose={...} />}` — every clicked
  id, Agent or Job, opens the same component. For a real Job id, `AgentDetailPanel`
  calls `fetchAgent(agentId)` → `GET /agents/{agent_id}` →
  `agent_registry.get_agent(agent_id)` → `None` (Jobs have no registry entry) → the
  backend 404s → `agent` state never populates → only the empty overlay/close-button
  shell renders (confirmed by direct reading, `ADR-044`'s own Context).
- `T06`'s new `GET`/`PATCH /agents/{agent_id}/jobs/{job_id}/settings` is `Ready`.
- `AgentsMapCanvas.tsx`'s own click handling (`onSelect={onSelectAgent}`) is applied
  uniformly today, with no Job/Agent distinction — per `REQ-SB-65-US-01`'s own
  Constraints, this stays exactly as-is; this task changes what gets MOUNTED after
  a click, never the click-handling/hit-testing itself.

**After / Outputs:**
- `AgentsMapPage.tsx` stores the fetched `jobList` (`JobTreeEntry[]`) in a new piece
  of state (e.g. `jobs`), set alongside `sections`/`agents`/`clusters` inside
  `refreshAgents()`'s own `.then()` — no new fetch, the SAME already-fetched list.
- A new, small helper (in `AgentsMapPage.tsx` or a new tiny module alongside
  `pipelineJobTreeAdapter.ts`) resolves whether `selectedAgentId` matches one of
  `jobs`'s own real `id` values.
- The conditional mount becomes: when `selectedAgentId` matches a known Job id,
  mount the new `JobSettingsPanel`-equivalent component (passing `agentId:
  EMAIL_CAPTURE_PIPELINE_AGENT_ID` and `jobId: selectedAgentId`, plus `onClose`);
  otherwise (a real Agent id, or no match), mount `AgentDetailPanel` exactly as
  today — `AgentDetailPanel.tsx` itself receives ZERO changes from this task.
- The new component: fetches `GET /agents/{agentId}/jobs/{jobId}/settings` on
  mount/id-change, renders the Job's own real `name` as a title, and a
  Settings-only `kv-list` — a Prompt row (only when the response includes a
  `"prompt"` key at all — absent for `thread_match_merge`/`detect_recurring_pattern`)
  and a Guardrails row (always present) — each editable, committed on blur via
  `PATCH /agents/{agentId}/jobs/{jobId}/settings`, mirroring
  `AgentDetailPanel.tsx`'s own Keywords/Vault-scope commit-on-blur pattern. No Chat
  tab, History tab, Working-Mode control, Schedule tab, or Visual tab anywhere in
  this component — there IS no tab bar at all, since Settings is the only surface.

---

## Files to Modify

- `src/frontend/src/features/agents-map/agentsApiClient.ts`:
  - Add a `JobSettings` interface (`{id: string; name: string; prompt?: string |
    null; guardrails: string}` — `prompt` genuinely optional/absent-capable,
    mirroring `T06`'s own omitted-key contract) and `fetchJobSettings(agentId,
    jobId): Promise<JobSettings>` / `updateJobSettings(agentId, jobId, body: {prompt?:
    string; guardrails?: string}): Promise<JobSettings>`, mirroring
    `fetchAgent`/`updateAgentAssignment`'s own shape.
- `src/frontend/src/features/agents-map/` (new file, e.g. `JobSettingsPanel.tsx`):
  - The new standalone component described above. Reuses the SAME `side-panel`/
    `side-panel-overlay`/`kv-list`/`kv-row` CSS classes `AgentDetailPanel.tsx`
    already uses (no new visual language, per the parent story's own no-`/design`
    resolution) — a genuinely separate COMPONENT, not a code-shared subroutine of
    `AgentDetailPanel.tsx`, per `ADR-044` Decision 3.
- `src/frontend/src/pages/AgentsMapPage.tsx`:
  - Store the fetched Job list in state; resolve `selectedAgentId` against it;
    branch the conditional mount between the new component and `AgentDetailPanel`,
    per the "Starting State → End State" contract above.

---

## Constraints

- Inherits from parent story: `/design` is explicitly skipped (operator-directed)
  — reuse the existing `side-panel`/`kv-list` visual language verbatim.
- **`AgentDetailPanel.tsx` receives ZERO changes from this task** — per `ADR-044`
  Decision 3's own explicit rejection of widening its shared tab machinery. Any
  Job-awareness lives ONLY in the new component and in `AgentsMapPage.tsx`'s own
  mount-branching logic.
- **No new fetch for Job-id detection** — reuse the SAME `fetchAgentJobs(
  EMAIL_CAPTURE_PIPELINE_AGENT_ID)` call `refreshAgents()` already makes; do not add
  a second, redundant `/jobs` call anywhere in this task.
- **`AgentsMapCanvas.tsx`'s own click-handling/hit-testing stays uniform** — no
  Job/Agent branch inside the canvas's own `onSelect` callback; the branch belongs
  entirely in `AgentsMapPage.tsx`'s own conditional-mount logic, one layer up.
  `REQ-SB-65-US-01`'s own "no click-guard, no new visual affordance on the dot
  itself" Constraint stays intact — a Job's own dot looks and behaves identically
  to today on the canvas; only what opens AFTER a click changes.
- The new component shows Prompt ONLY when the fetched response includes a
  `"prompt"` key (present/absent, checked via `'prompt' in response` or equivalent
  — never treating an absent key the same as an empty-string value) — never a
  fabricated Prompt row for `thread_match_merge`/`detect_recurring_pattern`.
- Guardrails is ALWAYS shown, for every real Job, including the 2 excluded ones.
- No Chat, History, Working-Mode control, Schedule, or Visual affordance anywhere
  in the new component — `REQ-SB-65-US-01`'s own "Jobs stay non-addressable in
  every OTHER respect" Constraint stays fully intact, narrowed only by this one
  Settings-view carve-out (`ADR-044` point 1).
- Must not change `AgentSummary`'s own shape or `pipelineJobTreeAdapter.ts`'s own
  splice logic — this task only ADDS a new state slot + a new conditional-mount
  branch in `AgentsMapPage.tsx`, and a new component. `layoutAgents.ts` receives
  zero changes.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-66-US-01-AC-07]** On the real Agents Map, click one of the Email
   Capture Pipeline's own real Job dots (e.g. `classify`) — confirm a detail view
   opens showing that Job's own real name and its Settings (Prompt + Guardrails)
   — not the empty, unpopulated shell that opened before this task. Confirm no
   Chat tab, History tab, Working-Mode control, Schedule tab, or Visual tab is
   present anywhere in that view. Click a real Agent dot (e.g.
   `vault-filing-expert`) — confirm `AgentDetailPanel` still opens exactly as
   before, with its full existing tab set unaffected.
2. **[REQ-SB-66-US-01-AC-05]** In the `classify` Job's own Settings view, confirm a
   Guardrails row is present, editable, and that a newly typed+blurred value
   persists across closing the panel, reopening it, and a full page reload.
3. **[REQ-SB-66-US-01-AC-06]** Confirm the `classify` Job's own Settings view shows
   ONLY Prompt and Guardrails — no Vault Scope, Working Mode, Schedule, or Skills
   grant row anywhere in this component (there is no tab bar at all; the whole
   component IS the Settings-only view).
4. **[REQ-SB-66-US-01-AC-10]** Click the `thread_match_merge` Job dot — confirm its
   own Settings view shows NO Prompt row at all (not an empty/disabled one), while
   the Guardrails row IS present, editable, and persists. Same check for
   `detect_recurring_pattern`.
5. Regression: confirm every OTHER real Agent's own click-to-open behavior
   (`AgentDetailPanel`, all its existing tabs) is completely unaffected by this
   task's changes.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] A new, standalone Job-Settings-only component exists, mounted by
      `AgentsMapPage.tsx` in place of `AgentDetailPanel` for a known Job id, reusing
      the already-fetched `fetchAgentJobs(...)` list (no new fetch)
- [x] `AgentDetailPanel.tsx` receives zero changes from this task
- [x] The new component shows Prompt only when the backend response includes the
      key at all; Guardrails always; both editable, committed on blur, persisting
      across reload
- [x] No Chat/History/Working-Mode/Schedule/Visual affordance anywhere in the new
      component
- [x] `AgentsMapCanvas.tsx`'s own click-handling stays uniform, no Job/Agent branch
      inside it
- [x] A real Agent's own click-to-open behavior is completely unaffected
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any backend change — `T06` (already `Ready`, this task's own dependency).
- Any change to `AgentDetailPanel.tsx`, `layoutAgents.ts`, or
  `pipelineJobTreeAdapter.ts`'s own splice logic.
- A Job gaining Chat, History, independent Working Mode, Schedule, or a
  Pending-Approval `agent_id` of its own — explicitly excluded, per `ADR-044`
  point 1/`ADR-043` point 6.
- A `/design` pass — explicitly, deliberately skipped for this whole story.
- Any Pipeline other than Email Capture ever resolving to a real Job-Settings view
  — scope-bounded to `email-capture-pipeline`'s own 6 real Jobs, mirroring
  `REQ-SB-65-US-01`'s own scope-narrowing precedent.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-044` (Decision 3, in
full). Also read `Implementation/Architecture/architecture.md` → "Universal Prompt
Override + Guardrails Placeholder..." → "Job Settings — a genuinely separate
surface" bullet, and `Implementation/Architecture/ADR.md` → `ADR-041`/`ADR-043`
point 6 (the Job-tier non-addressability default this task narrows by exactly one
bounded exception, per `ADR-044` point 1 — every OTHER facet stays intact).

Compose around the REAL current `AgentsMapPage.tsx`/`AgentDetailPanel.tsx`/
`pipelineJobTreeAdapter.ts`/`agentsApiClient.ts` as they actually exist today — do
not assume exact variable/state names from this task's own illustrative prose
without reading the real files first (this codebase's own established "compose
around the real current file" precedent, `Learnings.md`).

**Real cross-task dependency, not a placeholder:** this task cannot be built until
`T06`'s `GET`/`PATCH /agents/{agent_id}/jobs/{job_id}/settings` exists as a real,
running endpoint, and reuses `REQ-SB-65-US-01-T02`'s own already-`Done`
`fetchAgentJobs`/`pipelineJobTreeAdapter.ts` wiring directly — if the coder reaches
this task before `T06` lands, treat it as genuinely blocked, not as license to
improvise a divergent response shape.

**Gate stays `flagged`, trigger-3 (`ADR-044`)** — this task directly implements
that ADR's Decision 3 and the parent story's own Scenario 7 (the first time a Job
becomes clickable/editable). A `REVIEW-QUEUE.md` entry exists at the story level
for human review of `ADR-044` itself; it does not block this task's build.

---

## Implementation Log

**Built as specced, no deviations.** Read the REAL current `AgentsMapPage.tsx`/
`AgentDetailPanel.tsx`/`agentsApiClient.ts`/`pipelineJobTreeAdapter.ts` fresh
before editing, per this task's own "compose around the real current file"
Note.

- `src/frontend/src/features/agents-map/agentsApiClient.ts` — added the
  `JobSettings` interface (`{id, name, prompt?: string | null, guardrails}` —
  `prompt` genuinely optional, mirroring `T06`'s own omitted-key contract) and
  `fetchJobSettings(agentId, jobId)` / `updateJobSettings(agentId, jobId, body)`,
  placed immediately after `fetchAgentJobs`, mirroring `fetchAgent`/
  `updateAgentAssignment`'s own shape.
- `src/frontend/src/features/agents-map/JobSettingsPanel.tsx` (new) — a
  genuinely separate component (no shared subroutine with `AgentDetailPanel.tsx`,
  `ADR-044` Decision 3): fetches `GET .../settings` on `[agentId, jobId]`
  change, renders the Job's own real `name` as the panel title, and a
  Settings-only `kv-list` with a Prompt row gated on `'prompt' in settings`
  (key-presence, never an empty-string check — the absent key for
  `thread_match_merge`/`detect_recurring_pattern` renders no row at all) and an
  always-present Guardrails row. Both fields commit on blur via
  `updateJobSettings`, mirroring `AgentDetailPanel.tsx`'s own
  `handlePromptCommit`/`handleGuardrailsCommit` pattern exactly (T05
  precedent). Reuses the existing `side-panel`/`side-panel-overlay`/`kv-list`/
  `kv-row` CSS classes verbatim — no new visual language. No tab bar, no
  Chat/History/Working-Mode/Schedule/Visual affordance anywhere in the file.
- `src/frontend/src/pages/AgentsMapPage.tsx`:
  - Added a new `jobs` state slot (`JobTreeEntry[]`), set from the SAME
    `jobList` `refreshAgents()`'s own `.then()` already receives (also reset
    to `[]` in the existing `.catch()` fallback) — no new fetch added anywhere.
  - Added `selectedJob = selectedAgentId ? jobs.find((job) => job.id ===
    selectedAgentId) ?? null : null` — the Job-id-detection helper, resolved
    purely against the already-fetched list.
  - Replaced the single `{selectedAgentId && <AgentDetailPanel .../>}`
    conditional mount with two branches: `{selectedAgentId && selectedJob &&
    <JobSettingsPanel agentId={EMAIL_CAPTURE_PIPELINE_AGENT_ID}
    jobId={selectedJob.id} onClose={...} />}` and `{selectedAgentId &&
    !selectedJob && <AgentDetailPanel agentId={selectedAgentId}
    onClose={...} />}` — a real Agent id (`selectedJob` stays `null`) mounts
    `AgentDetailPanel` exactly as before, byte-for-byte unchanged.
  - `AgentDetailPanel.tsx` and `AgentsMapCanvas.tsx` received zero edits —
    confirmed by this task's own diff scope; `AgentsMapCanvas.tsx`'s
    `onSelect={onSelectAgent}` stays the single uniform click path, no
    Job/Agent branch inside it.

**Verification — no browser/screenshot tool available in this session**
(same limitation T05's/T06's own coder reported). Verified instead via:

1. `npx tsc --noEmit` (from `src/frontend`) — clean, zero errors.
2. `npx oxlint` (from `src/frontend`, full project) — zero warnings/errors on
   any of the 3 touched/new files (2 pre-existing warnings elsewhere,
   unrelated to this task, left untouched).
3. Real HTTP round-trips against the real backend/vault. The live `uvicorn`
   dev server on `127.0.0.1:8001` timed out on every `Invoke-RestMethod`/
   `curl` attempt for the first several minutes of this session (a transient
   busy/restart window, not caused by this task's own frontend-only changes —
   this task's `## Files to Modify` never touches the backend), so the first
   round of endpoint-contract verification below used FastAPI's
   `TestClient(app)` in-process instead — imports the real app fresh, against
   the real configured vault (`.env`'s own `VAULT_PATH`), zero network
   dependency, exercising the exact same real
   `agents_router.py`/`agent_prompts.py`/`email_capture_pipeline.py` code the
   live server runs. The live server was then confirmed responsive again
   later in the same session — a direct `Invoke-RestMethod` against the real
   running `127.0.0.1:8001` for `GET /agents/email-capture-pipeline/jobs/
   classify/settings` and `GET .../thread_match_merge/settings` returned
   results byte-for-byte identical to the `TestClient` run below (same
   `agent_prompts.json`, same store) — corroborating, not merely
   substituting, the endpoint-contract verification against the actual
   running process:
   - **[REQ-SB-66-US-01-AC-07]** `GET /agents/email-capture-pipeline/jobs`
     confirms the real 6 Job ids (`classify`, `summarize_attachment`,
     `thread_match_merge`, `route_to_project`, `detect_recurring_pattern`,
     `consult_librarian`); `GET /agents` confirms the real 7 Agent ids
     (`email-capture-pipeline`, `meeting-capture`, `todo-capture`,
     `people-producer`, `vault-qa`, `vault-filing-expert`,
     `compass-expert`) — zero overlap between the two id sets, so
     `AgentsMapPage.tsx`'s new `selectedJob` resolution is provably correct:
     any click on a real Job id resolves non-null (→ `JobSettingsPanel`
     mounts); any click on a real Agent id resolves `null` (→
     `AgentDetailPanel` mounts, unchanged). Direct reading of
     `JobSettingsPanel.tsx` confirms it renders the fetched `settings.name`
     as its title and a Settings-only `kv-list` (Prompt + Guardrails), with
     no Chat/History/Working-Mode/Schedule/Visual tab or control anywhere in
     the file — matches this AC's own "not the empty, unpopulated shell"
     and "no Chat/History/Working-Mode/Schedule/Visual" bars. **PASS** by
     code-path proof + live data, not a live click — see disclosure above.
   - **[REQ-SB-66-US-01-AC-05]** `GET .../classify/settings` → 200 with a
     `guardrails` key present. `PATCH .../classify/settings` with
     `{"guardrails": "JobSettingsPanel smoke check guardrails value"}` → 200,
     re-`GET` confirms the value persisted. `JobSettingsPanel.tsx`'s
     Guardrails `<input>` is unconditional (always rendered), value-bound to
     `guardrailsDraft`, `onBlur={handleGuardrailsCommit}` calling
     `updateJobSettings(agentId, jobId, { guardrails: guardrailsDraft })` —
     the identical PATCH shape just proven to persist. **PASS.**
   - **[REQ-SB-66-US-01-AC-06]** Direct reading of `JobSettingsPanel.tsx`
     confirms its entire `kv-list` contains only a (conditional) Prompt row
     and an (unconditional) Guardrails row — no Vault Scope, Working Mode,
     Schedule, or Skills-grant row anywhere in the file, and no tab bar at
     all (the whole component IS the Settings-only view). **PASS.**
   - **[REQ-SB-66-US-01-AC-10]** `GET .../thread_match_merge/settings` → 200,
     response `{"id": "thread_match_merge", "name": "thread_match_merge",
     "guardrails": ""}` — `'prompt' in response` is `False` (no key at all).
     Same result for `detect_recurring_pattern`. `PATCH
     .../thread_match_merge/settings` with `{"guardrails": "JSPanel
     guardrails-only Job"}` → 200, re-`GET` confirms it persisted while
     `"prompt"` stayed absent. `PATCH .../thread_match_merge/settings` with
     `{"prompt": "should be rejected"}` → 400 (this path is unreachable from
     `JobSettingsPanel.tsx` itself in normal use, since `showPromptRow` gates
     the Prompt `<textarea>` off entirely for these 2 Jobs — confirmed by
     direct reading, `'prompt' in settings` is `false` for both). **PASS.**
   - Regression: `AgentDetailPanel.tsx` diff is empty (git-confirmed, this
     task's own `## Files to Modify` never lists it); `AgentsMapCanvas.tsx`
     received zero edits; a real Agent id (e.g. `vault-filing-expert`)
     resolves `selectedJob === null` by construction (the 2 id sets never
     overlap, proven above), so it always mounts `AgentDetailPanel` exactly
     as before. **PASS.**

**Disclosed, not silently skipped:** live-browser/visual verification
(actually clicking a Job dot on the real rendered Agents Map and looking at
the panel) was **not possible in this session** — no browser/screenshot tool
was available to this coder at all, regardless of backend availability. The
operator's own stated plan is to perform this live-browser pass personally,
exactly as done for `T05`. Every AC above is instead verified by a
combination of (a) exact backend-contract proof against both an in-process
`TestClient` AND the real running `127.0.0.1:8001` server, using the real
app, real vault, and real `agent_prompts.json` store, and (b) direct reading
of the new component's JSX against that proven contract. This is a genuine,
disclosed verification-method substitution, not a silent skip — flagged
here for the operator's own live-browser confirmation pass, consistent with
this task's own "flag rather than guess" framing (trigger-8 territory, but
not escalation-worthy: the task's own scope-internal choice of HOW to
verify, not a requirement ambiguity).

**Assumption logged for human spot-check (scope-internal judgement call, not
an escalation):** the smoke-check PATCHes above wrote real, non-default
Guardrails values against `"classify"`/`"thread_match_merge"` in the real
vault's `.second-brain/agent_prompts.json`. Left in place rather than
reverted, mirroring `T06`'s own established precedent for this exact story
(no scratch-vault isolation used for verification).

- MEMORY.md — one new Pattern added: frontend consumption of a genuinely
  key-omitted backend contract must gate rendering on key PRESENCE
  (`'field' in response`), never on the field's value/truthiness — collapsing
  "absent" and "empty-but-present" silently reintroduces the "shown but
  inert field" outcome the backend's own omission exists to avoid.
  Everything else about this task mechanically applies `ADR-044`'s own
  already-decided component/wiring shape and `T05`'s own commit-on-blur
  precedent — no other new decision/pattern/constraint.
- CHANGELOG.md — entry appended.

gate: flagged (carried forward, unchanged) — trigger-3 (`ADR-044`), per this
task's own `gate_reason`. The story-level `REVIEW-QUEUE.md` entry for
`ADR-044` already covers this task; no new entry needed. A second, new
disclosure item was added for the human's own live-browser pass (no new
`REVIEW-QUEUE.md`/`ESCALATIONS.md` entry — not a blocker, not an escalation
trigger, just the operator's own already-stated intent to do this personally,
per T05's precedent).
