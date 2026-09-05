---
id: REQ-SB-31-US-01-T04
title: SystemHealthPage.tsx — Health Issues, MCP status, Providers, Last capture run, plus nav wiring
parent_story: REQ-SB-31-US-01
requirement_id: REQ-SB-31
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-31-US-01-T03, REQ-SB-12-US-01-T01]
sprint: "SPRINT-019"
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-31-US-01-T04 — `SystemHealthPage.tsx`

## Parent Story

- Story: [[REQ-SB-31-US-01]] — `../UserStories/REQ-SB-31-US-01-system-health-view.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-31 *System Health View*

---

## Objective

Build the real System Health page against `T03`'s `GET /system-health`,
per the approved prototype (`html-prototype/system-health.html`): a Health
Issues card (MCP-unreachable + each Disabled agent, or an empty-state when
none), an MCP/agent-orchestration status card, a Providers status card,
and a Last capture run card — plus a new top-level nav item and route.

**Task-level dependency note:** this task literally edits `App.tsx`
(built by `REQ-SB-12-US-01-T01`) and `Sidebar.tsx` (same task) — hence the
explicit `depends_on` on that specific task file, mirroring
`REQ-SB-12-US-02-T04`'s own identical dependency shape on the same task.

---

## Starting State → End State

**Before / Inputs:**
- `T03` has landed `GET /system-health`.
- `App.tsx` routes `/`, `/my-day` (+ 3 drill-downs), `/settings` inside
  `<AppShell>`; `Sidebar.tsx` has nav items for Agents Map, My Day,
  Settings.
- `styles/settings.css` already carries `.card`, `.badge*`, `.kv-list`,
  `.item-list`, `.empty-state`, `.btn`/`.btn-primary` — no new CSS needed.

**After / Outputs:**
- `src/frontend/src/features/system-health/client.ts` exists
  (`fetchSystemHealth()`).
- `src/frontend/src/pages/SystemHealthPage.tsx` exists, rendering the four
  regions from real `GET /system-health` data, with a manual Refresh
  button.
- `App.tsx` gains route `/system-health` → `SystemHealthPage`.
- `Sidebar.tsx` gains one new `<NavLink to="/system-health">` ("System
  Health"), positioned after Settings, matching the approved prototype's
  sidebar order.

---

## Files to Modify

- `src/frontend/src/features/system-health/client.ts` (new):
  ```typescript
  import { apiFetch } from '../../api/client';

  export interface SystemHealthProvider {
    id: string;
    name: string;
    endpoint: string;
    model: string;
    credential_set: boolean;
    is_default: boolean;
    has_real_client: boolean;
    agent_ids: string[];
    agent_names: string[];
  }

  export interface SystemHealthDisabledAgent {
    agent_id: string;
    agent_name: string;
    provider_name: string | null;
  }

  export interface SystemHealthResponse {
    mcp: { reachable: boolean };
    providers: SystemHealthProvider[];
    disabled_agents: SystemHealthDisabledAgent[];
    last_capture_run: { finished_at: string } | null;
  }

  export function fetchSystemHealth(): Promise<SystemHealthResponse> {
    return apiFetch<SystemHealthResponse>('/system-health');
  }
  ```

- `src/frontend/src/pages/SystemHealthPage.tsx` (new):
  ```tsx
  import { useEffect, useState } from 'react';
  import {
    fetchSystemHealth,
    type SystemHealthResponse,
  } from '../features/system-health/client';

  export function SystemHealthPage() {
    const [health, setHealth] = useState<SystemHealthResponse | null>(null);

    const load = () => {
      fetchSystemHealth().then(setHealth);
    };

    useEffect(load, []);

    if (!health) {
      return (
        <>
          <h1>System Health</h1>
          <p className="text-muted">Loading...</p>
        </>
      );
    }

    const hasIssues = !health.mcp.reachable || health.disabled_agents.length > 0;

    return (
      <>
        <h1>System Health</h1>
        <p className="text-muted">
          Whether Second Brain's own moving pieces are genuinely working — not
          just "the process is up" — so a real failure is visible at a glance
          instead of discovered by symptom-chasing through individual features
          or digging through raw server logs (REQ-SB-31).
        </p>
        <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
          <button
            type="button"
            className="btn"
            style={{
              padding: 'var(--space-1) var(--space-3)',
              fontSize: 'var(--font-size-sm)',
              marginRight: 'var(--space-2)',
            }}
            onClick={load}
          >
            &#8635; Refresh
          </button>
          Every check below recomputes fresh on open or refresh — never a
          cached snapshot from an earlier page load.
        </p>

        <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
          <h2>Health Issues</h2>
          {hasIssues ? (
            <div className="item-list">
              {!health.mcp.reachable && (
                <div className="item-row">
                  <div className="item-row-main">
                    <span className="item-row-title">
                      MCP / Agent-orchestration path{' '}
                      <span className="badge badge-danger">Unreachable</span>
                    </span>
                    <span className="item-row-meta">
                      GET /mcp did not respond with its expected "alive" signal
                      (HTTP 406) — no response, or an unexpected response.
                    </span>
                  </div>
                </div>
              )}
              {health.disabled_agents.map((agent) => (
                <div className="item-row" key={agent.agent_id}>
                  <div className="item-row-main">
                    <span className="item-row-title">
                      {agent.agent_name} <span className="badge badge-danger">Disabled</span>
                    </span>
                    <span className="item-row-meta">
                      Selected Provider ({agent.provider_name ?? 'none'}) has no
                      real client configured yet.
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">&#10003;</div>
              <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
                No Health Issues
              </p>
              <p style={{ margin: 'var(--space-1) 0 0' }}>
                MCP/agent-orchestration is reachable and every agent's selected
                Provider has a real client configured.
              </p>
            </div>
          )}
        </div>

        <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
          <h2>MCP / Agent-orchestration path</h2>
          <div className="kv-list">
            <div className="kv-row">
              <span className="kv-key">Mount</span>
              <span className="mono">GET /mcp</span>
            </div>
            <div className="kv-row">
              <span className="kv-key">Status</span>
              <span className={`badge ${health.mcp.reachable ? 'badge-success' : 'badge-danger'}`}>
                {health.mcp.reachable ? 'Reachable' : 'Unreachable'}
              </span>
            </div>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
          <h2>Providers</h2>
          <p
            className="text-muted"
            style={{ fontSize: 'var(--font-size-sm)', marginTop: 'calc(-1 * var(--space-3))' }}
          >
            Rolled up per distinct Provider, from each agent's own selection.
            "Available" means a real client is configured for it — not that it
            has been verified reachable right now.
          </p>
          <div className="item-list">
            {health.providers.map((provider) => (
              <div className="item-row" key={provider.id}>
                <div className="item-row-main">
                  <span className="item-row-title">
                    {provider.name}{' '}
                    {provider.has_real_client ? (
                      <span className="badge badge-success">Available</span>
                    ) : (
                      <span className="badge badge-warning">No client built yet</span>
                    )}
                  </span>
                  <span className="item-row-meta">
                    {provider.agent_names.length > 0
                      ? `Selected by ${provider.agent_names.length} agent(s) (${provider.agent_names.join(', ')})`
                      : 'Not currently selected by any agent'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <h2 style={{ marginTop: 'var(--space-6)' }}>Last capture run</h2>
        <div className="card">
          {health.last_capture_run ? (
            <div className="kv-list">
              <div className="kv-row">
                <span className="kv-key">Last completed</span>
                <span className="mono">{health.last_capture_run.finished_at}</span>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
                No capture run has completed yet
              </p>
              <p style={{ margin: 'var(--space-1) 0 0' }}>
                <span className="mono">last_capture_run.json</span> does not
                exist yet — shown honestly, not fabricated as a timestamp or a
                misleadingly healthy-looking default.
              </p>
            </div>
          )}
        </div>
      </>
    );
  }
  ```

- `src/frontend/src/App.tsx` — add the import and route, additive only:
  ```tsx
  import { SystemHealthPage } from './pages/SystemHealthPage';
  ...
  <Route path="/system-health" element={<SystemHealthPage />} />
  ```

- `src/frontend/src/components/shell/Sidebar.tsx` — add one new
  `<NavLink>` after the Settings one, additive only:
  ```tsx
  <NavLink
    to="/system-health"
    className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
  >
    <span className="nav-icon">⚡</span>
    <span className="nav-label">System Health</span>
  </NavLink>
  ```

---

## Constraints

- Inherits from parent story, and `ADR-010`'s conventions: `react-router`
  `<NavLink>` for the nav item, native `fetch` behind the existing
  `apiFetch` client, class names reused verbatim from already-ported CSS
  — **no new CSS file, no new class**.
- `GET /system-health` is re-fetched on every mount and on every manual
  Refresh click — no polling interval, no caching of the previous
  response (Scenario 7).
- The Providers card's own neutral "No client built yet" language and the
  Health Issues card's "Disabled" language must both come from the same
  underlying `has_real_client`/`disabled_agents` signals but render as two
  different rows for two different reasons, per the approved prototype
  and the story's own Context — do not collapse them into one list.
- Do not modify `MyDayPage.tsx`, `SettingsPage.tsx`, `AgentsMapPage.tsx`,
  or any other existing page/route.

---

## Tests

<!-- Structural ACs, per the decomposer's own "durable design layer"
rule -- DOM structure/regions, not visual polish. jsdom sees no computed
CSS/layout/colour; pure visual polish is spot-checked against the
approved prototype out-of-band, not a locked AC. -->

**Manual verification steps** (frontend dev server running against the
real backend on port `8001`; open `http://localhost:5173/system-health`
in a browser):

1. `[REQ-SB-31-US-01-AC-01]` With the real backend healthy (MCP reachable,
   every agent's Provider has a real client — the real vault's default
   all-Compass state), open the System Health page. Confirm: an "MCP /
   Agent-orchestration path" card showing `Reachable`; a "Providers" card
   listing Compass as `Available`; a "Health Issues" card showing the
   empty-state ("No Health Issues"), not a failure list.
2. `[REQ-SB-31-US-01-AC-02]` Temporarily stop the backend (or block port
   `8001`) so `GET /mcp` cannot respond, reload the page. Confirm the MCP
   card shows `Unreachable` (a `badge-danger`, visibly distinct from
   `badge-success`), and it appears as a row in the Health Issues card.
   Restore the backend afterward.
3. `[REQ-SB-31-US-01-AC-03]` Temporarily reassign one agent to a Provider
   with no real client, reload the page. Confirm that agent's row appears
   in the Health Issues card with a `Disabled` badge. Revert afterward.
4. `[REQ-SB-31-US-01-AC-04]` With every agent's Provider having a real
   client (the reverted/default state), confirm none of them appears in
   the Health Issues card.
5. `[REQ-SB-31-US-01-AC-05]` With a real, already-completed capture run on
   disk (the real vault's own `.second-brain/last_capture_run.json`),
   confirm the "Last capture run" card shows its `finished_at` timestamp.
6. `[REQ-SB-31-US-01-AC-06]` Temporarily rename/move
   `.second-brain/last_capture_run.json` aside, reload the page. Confirm
   the card shows the honest "No capture run has completed yet" empty
   state — no fabricated timestamp. Restore the file afterward.
7. `[REQ-SB-31-US-01-AC-07]` After any of the above temporary changes,
   confirm clicking the Refresh button (or reloading the page) reflects
   the current state, not a value cached from an earlier load — verified
   implicitly by steps 2/3/6 above already showing state changes taking
   effect on reload/refresh, not requiring a hard browser cache-clear.
8. Non-AC structural check: confirm a `.nav-item` for "System Health"
   renders in the sidebar on every page (not just this one), and that it
   carries the `active` class only when the current route is
   `/system-health`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-31-US-01-AC-01` — everything healthy: MCP reachable,
      Providers available, Health Issues empty-state, no failure styling
- [x] `REQ-SB-31-US-01-AC-02` — MCP unreachable is visibly distinguished
      and listed as a Health Issue
- [x] `REQ-SB-31-US-01-AC-03` — a Provider-less agent is shown Disabled
      and listed as a Health Issue
- [x] `REQ-SB-31-US-01-AC-04` — a Provider-backed agent is shown available,
      not listed as a Health Issue
- [x] `REQ-SB-31-US-01-AC-05` — last capture run's completion time is shown
      from the recorded completion record
- [x] `REQ-SB-31-US-01-AC-06` — no capture run ever completed is shown
      honestly, no fabricated timestamp
- [x] `REQ-SB-31-US-01-AC-07` — reopening/refreshing reflects current
      state, not a cached snapshot
- [x] New `System Health` nav item present and correctly highlighted on
      every page
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `REQ-SB-31-US-01-AC-08` (the `run_agent_conversation` crash-gap fix) —
  `T01`, backend-only, no screen.
- Any change to `app/business/system_health.py`/
  `app/api/system_health_router.py` — `T02`/`T03`.
- Auto-refresh/polling beyond the manual Refresh button and per-mount
  fetch — the story's own Non-Goals.
- Extending the Disabled/Health Issue display to Agents Map or per-agent
  Settings — a separate product question, not this story's scope.

---

## Context / Notes

**Gating note:** this story is `gate: clear` (no ADR created/changed at
`/plan-tasks`) — no human-review pointer is required before this task
proceeds to `Ready`.

Reuses `.card`/`.badge*`/`.kv-list`/`.item-list`/`.empty-state`/`.btn`
verbatim from `styles/settings.css`, per the approved prototype's own
"composed entirely from existing tokens/components" header note — no new
CSS file, no new class name.

---

## Implementation Log

**Build (2026-08-12).** `src/frontend/src/features/system-health/
client.ts` (new, `fetchSystemHealth()` + response types) and
`src/frontend/src/pages/SystemHealthPage.tsx` (new, four regions: Health
Issues / MCP path / Providers / Last capture run) created exactly per the
task's own literal code sample — zero new CSS, composed entirely from
`.card`/`.badge*`/`.kv-list`/`.item-list`/`.empty-state`/`.btn` already
global via `main.tsx`'s existing `styles/settings.css` import.
`App.tsx` gained the `/system-health` route (additive), `Sidebar.tsx`
gained one new `<NavLink>` after Settings (additive). No other page/
route/component touched.

**Environment note before verification:** the shared dev backend
(started earlier the same day, PID `14784`/`39904`) was found serving
stale code — `GET /system-health` 404'd even after `T01`-`T03`'s files
were saved and `--reload`'s own watcher window had long passed, while
`GET /agents` on the same process answered correctly with live data (not
the literal "reloader parent died" shape from `MEMORY.md`'s own
Pattern — the reloader/worker/fork-child process tree was fully alive —
but the same "edits not reflected" symptom). Recovered via the standing
`MEMORY.md` specific-PID-kill-and-restart protocol: killed the exact 3
PIDs (`10248` fork child, `39904` worker, `14784` reloader) individually,
confirmed port `8001` freed, restarted via `tools/run-backend.cmd`. The
fresh process picked up `T01`-`T04`'s code correctly on first request.

**Verification tool:** no Playwright/Puppeteer exists in `src/frontend`
yet — reused this project's own established zero-dependency
Headless-Chrome-via-CDP pattern (`MEMORY.md` Patterns): launched
`chrome.exe --headless=new --remote-debugging-port=9333` with a scratch
profile dir, drove it via a small Node (v24, built-in `fetch`/
`WebSocket`) script against the real `npm run dev` server on `5173`
(already running), navigating real routes, reading real rendered DOM
text/classes, and capturing real PNG screenshots. Cleaned up (killed the
specific Chrome PID) at the end of this task's own verification.

**`[REQ-SB-31-US-01-AC-01]` — everything healthy.** Opened
`http://localhost:5173/system-health` against the real backend's default
state (MCP mount alive, all 5 agents on Compass, a real completed capture
run). Rendered: `<h1>System Health</h1>`; "Health Issues" card showing
the `.empty-state` ("No Health Issues" + checkmark, matching the
approved prototype's healthy state); "MCP / Agent-orchestration path"
card showing `Status: Reachable` (`badge-success`); "Providers" card
listing "Compass Available" (`badge-success`), "Selected by 5 agent(s)
(Email Capture, Meeting Capture, To-Do Capture, People Notes, Vault
Q&A)"; "Last capture run" card showing the real `finished_at`
timestamp. Screenshot confirms visual parity with the approved
prototype's `healthy` state (`.state-switcher` "Everything healthy"
panel). **PASS.**

**`[REQ-SB-31-US-01-AC-02]` + `[REQ-SB-31-US-01-AC-03]` — issues present
(verified together, one real state change, per this project's own
"consolidate a real-side-effect verification across sibling checks"
pattern, matching the prototype's own combined "issues" panel):**
temporarily pointed `system_health._MCP_MOUNT_URL` at an unreachable
loopback port (`18001`, reverted immediately after) AND created a
throwaway no-real-client Provider + reassigned `people-producer` to it
(reverted immediately after, throwaway Provider deleted) — both via real
HTTP calls against the real running backend, no mocking. Reloaded the
real page: "Health Issues" card now lists two real rows — "MCP /
Agent-orchestration path Unreachable" (`badge-danger`) and "People Notes
Disabled" (`badge-danger`, "Selected Provider (Verify No-Client
Provider) has no real client configured yet."); "MCP / Agent-
orchestration path" card shows `Status: Unreachable` (`badge-danger`,
visibly distinguished from the earlier `badge-success` "Reachable");
"Providers" card correctly keeps the neutral "Verify No-Client Provider
No client built yet" (`badge-warning`) wording — confirming the
Providers-card language and the Health-Issues-card "Disabled" language
stay two separate rows for two separate reasons, per the task's own
Constraints, not collapsed into one list. Screenshot confirms visual
parity with the approved prototype's `issues` panel. **PASS** (both
ACs).

**`[REQ-SB-31-US-01-AC-04]`** — after reverting the above (`people-
producer` back to `compass`, throwaway Provider deleted), re-`GET
/system-health` and reloaded the page: `disabled_agents: []`, "Health
Issues" card back to the empty-state, no agent listed. Confirms a
Provider-backed agent is never shown Disabled/never listed. **PASS.**

**`[REQ-SB-31-US-01-AC-05]`** — the real vault's own
`.second-brain/last_capture_run.json` (a genuinely completed run,
`finished_at: "2026-08-12T08:26:58...+00:00"` at first observation, and
the scheduler's own hourly/on-start trigger produced fresh completions
over the course of this verification session) renders verbatim in the
"Last capture run" card's `kv-row`, confirmed in every screenshot above.
**PASS.**

**`[REQ-SB-31-US-01-AC-06]`** — temporarily moved the real
`last_capture_run.json` aside (`Move-Item` to a `.verify-backup`
sibling, same directory, same real vault — `C:\myWorx\<operator vault>\Moussa
Brain\.second-brain\`), confirmed `GET /system-health` →
`last_capture_run: null`, then reloaded the real page: "Last capture
run" card showed the honest `.empty-state` — "No capture run has
completed yet" / "`last_capture_run.json` does not exist yet — shown
honestly, not fabricated as a timestamp or a misleadingly healthy-looking
default" — no fabricated timestamp anywhere. Restored the file
immediately afterward (`Move-Item` back) and re-`GET /system-health`
confirmed the exact original `finished_at` value was restored
byte-exact. **PASS.**

**`[REQ-SB-31-US-01-AC-07]`** — proven implicitly by every state
transition above: each of `AC-02`/`AC-03`'s induced-issue state, its
revert, and `AC-06`'s file-removal/restore was observed to take effect
on the very next `GET`/page load with no stale/cached value ever
observed, matching this project's own "recomputes fresh on every call,
never cached" precedent (`REQ-SB-22-US-01`). The page's own Refresh
button calls the identical `fetchSystemHealth()` path as the initial
mount `useEffect` — same code, same guarantee. **PASS.**

**Non-AC structural check:** confirmed the `System Health` `.nav-item`
renders on every page (checked `/system-health` — `active`; `/my-day` —
present, correctly NOT `active`, while `My Day`'s own nav item is
`active` there instead). **PASS.**

**One real, live-discovered bug found and fixed in-scope during this
verification — NOT this task's own file, logged here for traceability
and in full in `T02`'s own Implementation Log (the owning task):**
`system_health.py::mcp_mount_reachable()`'s literal `httpx.get()` call
(no `follow_redirects`) returned `307` for the real `/mcp` mount, not the
`406` needed to report "reachable" — without the `follow_redirects=True`
fix, `AC-01`'s real "everything healthy" state would have falsely shown
MCP as unreachable. Confirmed fixed and re-verified live (see `AC-01`
above, observed AFTER the fix).

`gate: clear` 2026-08-12 — this task's own three files were built exactly
per spec, verified live end-to-end against the real backend and real
frontend dev server, real screenshots taken and visually compared against
the approved prototype (`html-prototype/system-health.html`) for both its
`healthy` and `issues` states. No MUST-FLAG trigger fired on this task's
own file scope (the one live-discovered correction belongs to `T02`'s own
file, gated there). `status: Done`.
