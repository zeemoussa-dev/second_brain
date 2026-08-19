---
id: REQ-SB-43-US-01-T07
title: New src/frontend/src/features/cockpit/cockpitApiClient.ts — fetch wrapper over the /cockpit/{subject_kind}/{stem} endpoints
parent_story: REQ-SB-43-US-01
requirement_id: REQ-SB-43
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-43-US-01-T05]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-43-US-01-T07 — Frontend `cockpit/cockpitApiClient.ts`

## Parent Story

- Story: [[REQ-SB-43-US-01]] — `../UserStories/REQ-SB-43-US-01-meeting-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-43 *Meeting Cockpit — Expert-Assisted Meeting Workspace*

---

## Objective

New `src/frontend/src/features/cockpit/cockpitApiClient.ts` — the same thin-`apiFetch`-wrapper convention every other `features/*/client.ts` file already uses, over `T05`'s five `/cockpit/{subject_kind}/{stem}...` endpoints. Shared by this story's `MeetingCockpitPage.tsx` (`T09`) and `REQ-SB-44-US-01`'s own `InboxCockpitPage.tsx`.

---

## Starting State → End State

**Before / Inputs:** `src/frontend/src/api/client.ts::apiFetch<T>(path, init?)` is the established convention (`agentsApiClient.ts`, `features/my-day/client.ts`, etc.).

**After / Outputs:** new `src/frontend/src/features/cockpit/cockpitApiClient.ts`:
```typescript
import { apiFetch } from '../../api/client';

export interface CockpitPersonChip {
  name: string;
  email: string | null;
  has_note: boolean;
  note_path: string | null;
}

export interface CockpitMessage {
  speaker: 'user' | 'agent';
  agent_id: string | null;
  agent_name: string | null;
  text: string;
  timestamp: string;
}

export interface CockpitThread {
  messages: CockpitMessage[];
  brought_in_agent_ids: string[];
}

export interface CockpitResearchResult {
  stem: string;
  title: string;
}

export interface CockpitData {
  subject: Record<string, unknown>;
  people: CockpitPersonChip[];
  thread: CockpitThread;
  research_results: CockpitResearchResult[];
}

export function fetchCockpit(subjectKind: string, stem: string): Promise<CockpitData> {
  return apiFetch<CockpitData>(`/cockpit/${subjectKind}/${stem}`);
}

export function bringInAgent(subjectKind: string, stem: string, agentId: string): Promise<CockpitThread> {
  return apiFetch<CockpitThread>(`/cockpit/${subjectKind}/${stem}/bring-in`, {
    method: 'POST',
    body: JSON.stringify({ agent_id: agentId }),
  });
}

export function sendCockpitMessage(subjectKind: string, stem: string, message: string): Promise<CockpitThread> {
  return apiFetch<CockpitThread>(`/cockpit/${subjectKind}/${stem}/message`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export interface CockpitResearchTrigger {
  status: 'found' | 'no_results' | 'no_match';
  summary?: string;
  query?: string;
}

export function triggerCockpitResearch(
  subjectKind: string, stem: string, requestingAgentId: string, query: string,
): Promise<CockpitResearchTrigger> {
  return apiFetch<CockpitResearchTrigger>(`/cockpit/${subjectKind}/${stem}/research`, {
    method: 'POST',
    body: JSON.stringify({ requesting_agent_id: requestingAgentId, query }),
  });
}

export function saveCockpitResearch(
  subjectKind: string, stem: string, query: string, summary: string,
): Promise<{ note_path: string }> {
  return apiFetch<{ note_path: string }>(`/cockpit/${subjectKind}/${stem}/research/save`, {
    method: 'POST',
    body: JSON.stringify({ query, summary }),
  });
}
```

---

## Files to Modify

- `src/frontend/src/features/cockpit/cockpitApiClient.ts` (new) — per the code block above.

---

## Constraints

- Every function goes through `apiFetch` (existing convention) — no raw `fetch` call.
- `subjectKind` is `"meeting" | "email"` at every call site, but this file's own function signatures accept `string` (matches the backend router's own generic-over-`subject_kind` shape) — narrower typing at the CALL SITE (`T09`/`REQ-SB-44`'s own page) is fine, not required here.
- No discard function — matches the backend's own "no discard route" shape (`T05`).
- Does not modify `src/frontend/src/api/client.ts` (already exports `BASE_URL`/`apiFetch` as of `T06` of `REQ-SB-42-US-01`, if that task landed first; `apiFetch` itself needed no change either way).

---

## Tests

**Manual verification steps** (real backend dev server + a Vite dev server or a Node script importing this module against the real API; requires a real Meeting note stem, per `T05`'s own Tests):
1. **[REQ-SB-43-US-01-AC-02]** `fetchCockpit("meeting", "<real-stem>")` — confirm a real `CockpitData` object with real `subject`/`people`/`thread`/`research_results`.
2. **[REQ-SB-43-US-01-AC-05]** `bringInAgent("meeting", "<real-stem>", "vault-qa")` — confirm the returned thread's `brought_in_agent_ids` includes `"vault-qa"`.
3. **[REQ-SB-43-US-01-AC-06]** `sendCockpitMessage("meeting", "<real-stem>", "What's Acme's renewal history?")` — confirm the returned thread gained a real agent-attributed reply.
4. **[REQ-SB-43-US-01-AC-08]**/**[REQ-SB-43-US-01-AC-09]** `triggerCockpitResearch(...)` then `saveCockpitResearch(...)` — confirm each returns the real shape the backend sends.
5. Clean-up: as per `T05`'s own Tests.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] All six functions exist, typed, calling `T05`'s real endpoints via `apiFetch`
- [ ] No raw `fetch` call
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Rendering — `T08`/`T09`.
- Any backend change.

---

## Context / Notes

Shared by both Cockpit stories (`ADR-036` point 3) — `REQ-SB-44-US-01` imports this SAME file, does not create a second client.

---

## Implementation Log

Implemented exactly as spec'd — all 6 functions, every call through `apiFetch`,
no raw `fetch`.

**Manual verification (real backend on port 8001 + real Vite dev server on
5173, driven via a minimal from-scratch CDP WebSocket client against a real
headless-Edge browser — no Playwright/Puppeteer installed in this repo; the
bundled Node install located via the already-running Vite process's own
executable path, `tools/node/node.exe`, per this project's own established
technique):**
1. **AC-02:** in-page `await import('/src/features/cockpit/cockpitApiClient.ts')`, `fetchCockpit('meeting', '0-2026-08-10-CC920000')` → real `CockpitData` with real `subject`/`people`/`thread`/`research_results`. Confirmed.
2. **AC-05:** `bringInAgent(...)` → returned thread's `brought_in_agent_ids` includes `"vault-qa"`. Confirmed.
3. **AC-06:** `sendCockpitMessage(...)` → returned thread gained a real `agent_id`-attributed reply. Confirmed.
4. **AC-08/AC-09:** temporary real grant (`vault-qa` + `web-research` + `anthropic-claude` Provider, same reverted protocol as `T04`/`T05`) → `triggerCockpitResearch(...)` returned a real `{"status":"found", summary: <1022 real chars>}`; `saveCockpitResearch(...)` returned a real `note_path`, file confirmed on disk.
5. Cleanup: saved note + `.second-brain/cockpit_threads.json` test entries deleted; `vault-qa`'s temporary grant/Provider reverted and independently reconfirmed.

gate: clear 2026-08-14 — no triggers fired (thin, mechanical wrapper over `T05`'s
already-verified real endpoints).
