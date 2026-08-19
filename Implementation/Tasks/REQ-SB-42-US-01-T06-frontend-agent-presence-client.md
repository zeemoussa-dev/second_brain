---
id: REQ-SB-42-US-01-T06
title: New src/frontend/src/features/agent-presence/client.ts — EventSource wrapper over GET /agent-presence/stream
parent_story: REQ-SB-42-US-01
requirement_id: REQ-SB-42
type: frontend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-42-US-01-T05]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-42-US-01-T06 — Frontend `agent-presence/client.ts` (EventSource wrapper)

## Parent Story

- Story: [[REQ-SB-42-US-01]] — `../UserStories/REQ-SB-42-US-01-real-time-agent-activity-pulses.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-42 *Real-Time Agent Activity Pulses (Agents Map)*

---

## Objective

New `src/frontend/src/features/agent-presence/client.ts` — a thin wrapper over the browser's native `EventSource` (no new npm dependency, `ADR-035` point 1) against `GET /agent-presence/stream`, parsing each `data:` payload into a typed snapshot and delivering it to a caller-supplied callback. `EventSource` auto-reconnects on drop with zero reconnect code of this task's own.

---

## Starting State → End State

**Before / Inputs:** no `features/agent-presence/` directory exists. `src/frontend/src/api/client.ts` exports `ApiError` and `apiFetch` but does not currently export its own `BASE_URL` constant.

**After / Outputs:**
- `src/frontend/src/api/client.ts` — `BASE_URL` gains `export` (additive change to one existing line; nothing else in this file changes) so `agent-presence/client.ts` can build the correct absolute `EventSource` URL against the same configurable backend host `apiFetch` already uses.
- New `src/frontend/src/features/agent-presence/client.ts`:
  ```typescript
  import { BASE_URL } from '../../api/client';

  export interface AgentPresenceSnapshot {
    active: Record<string, { kind: 'capture' | 'chat'; since: string; token: string }>;
    hub_routes: { from_agent_id: string; to_agent_id: string; since: string }[];
    pending_approval_agent_ids: string[];
  }

  export function subscribeToAgentPresence(
    onSnapshot: (snapshot: AgentPresenceSnapshot) => void,
  ): () => void {
    const source = new EventSource(`${BASE_URL}/agent-presence/stream`);
    source.onmessage = (event) => {
      const snapshot = JSON.parse(event.data) as AgentPresenceSnapshot;
      onSnapshot(snapshot);
    };
    return () => source.close();
  }
  ```

---

## Files to Modify

- `src/frontend/src/api/client.ts` — add `export` to the existing `const BASE_URL = ...` line only; no other change.
- `src/frontend/src/features/agent-presence/client.ts` (new) — per the code block above.

---

## Constraints

- No new npm dependency — the browser's native `EventSource` only.
- `subscribeToAgentPresence` returns an unsubscribe/cleanup function (`() => source.close()`) — the caller (`T07`/`T08`, inside a React `useEffect`) is responsible for calling it on unmount; this task does not itself manage React lifecycle.
- Does not swallow/log-suppress a malformed `event.data` payload silently in a way that would hide a real backend contract mismatch — a `JSON.parse` failure should surface (e.g. via an uncaught exception in dev, or a `console.error`), not a silent no-op, since this is this project's first SSE consumer and a shape mismatch is exactly the kind of integration bug worth surfacing loudly during build.
- Do not modify `src/frontend/src/api/client.ts` beyond exporting the existing constant.

---

## Tests

**Manual verification steps** (real backend dev server on port 8001 per `T05`'s own Tests; a small Node/browser script, or Vite dev server + browser devtools console):
1. **[REQ-SB-42-US-01-AC-07]** In a browser console (or a small script run via the Vite dev server), `import('./features/agent-presence/client').then(m => m.subscribeToAgentPresence(s => console.log(s)))` — confirm the initial snapshot logs within ~1s of subscribing.
2. **[REQ-SB-42-US-01-AC-07]** With the subscription from step 1 still active, trigger a real backend state change (e.g. `POST /agents/email-capture/chat` with an ordinary message, per `T02`'s wrap) — confirm a SECOND snapshot logs automatically, without the frontend code making any new request (native `EventSource` push, not poll).
3. Non-AC smoke check: call the cleanup function returned by `subscribeToAgentPresence` — confirm no further snapshots log after a subsequent real backend state change (the connection was actually closed).
4. Non-AC smoke check: temporarily stop the backend dev server while a subscription is open, confirm the browser's `EventSource` auto-reconnects once the server is restarted (a fresh initial snapshot arrives again) — no reconnect code of this task's own, confirming the native browser behavior is relied on correctly.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `subscribeToAgentPresence` connects to `GET /agent-presence/stream` via native `EventSource`, delivers each parsed snapshot to the caller's callback
- [ ] Returns a cleanup function that closes the connection
- [ ] No new npm dependency added
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Applying the snapshot to any rendered node/CSS class — `T07`/`T08`.
- Any backend change.

---

## Context / Notes

Full mechanism: `ADR-035` point 5. This is the first frontend consumer of `BASE_URL`'s own export — every other existing client file (`agentsApiClient.ts`, `features/my-day/client.ts`, etc.) goes through `apiFetch` and never needed `BASE_URL` directly; `EventSource`'s constructor takes a raw URL string, not a `fetch`-style wrapper, which is why this one case needs the constant exported.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
