---
id: REQ-SB-11-US-01-T04
title: AgentActivityPage.tsx — chronological activity log + Outlook channel status, plus nav wiring
parent_story: REQ-SB-11-US-01
requirement_id: REQ-SB-11
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-11-US-01-T03, REQ-SB-12-US-01-T01]
sprint: "SPRINT-027"
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-11-US-01-T04 — `AgentActivityPage.tsx`

## Parent Story

- Story: [[REQ-SB-11-US-01]] — `../UserStories/REQ-SB-11-US-01-agent-activity-and-error-observability.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-11 *Agent Activity & Error Observability*

---

## Objective

Build the real Agent Activity page against `T03`'s `GET /agent-activity`,
per the approved prototype (`html-prototype/agent-activity.html`): a
chronological Activity log card (each entry's own success/error badge, a
failed entry's error detail shown inline, an honest empty state when
nothing has run yet) and a Communication channels card (Outlook COM
reachable/unreachable, the real detail message on failure) — plus a new
top-level nav item and route.

**Task-level dependency note:** this task literally edits `App.tsx` and
`Sidebar.tsx` (both built by `REQ-SB-12-US-01-T01`) — hence the explicit
`depends_on` on that specific task file, mirroring
`REQ-SB-31-US-01-T04`'s own identical dependency shape on the same task.

---

## Starting State → End State

**Before / Inputs:**
- `T03` has landed `GET /agent-activity`.
- `App.tsx` routes `/`, `/my-day` (+ drill-downs), `/settings`,
  `/system-health` (and any others landed by concurrent stories) inside
  `<AppShell>`; `Sidebar.tsx` has nav items for Agents Map, My Day,
  Settings, System Health.
- `styles/settings.css`/`shell.css` already carry `.card`, `.badge*`,
  `.kv-list`, `.log-list`/`.log-item`, `.empty-state`, `.btn`/
  `.btn-primary` — no new CSS needed.

**After / Outputs:**
- `src/frontend/src/features/agent-activity/client.ts` exists
  (`fetchAgentActivity()`).
- `src/frontend/src/pages/AgentActivityPage.tsx` exists, rendering the two
  regions from real `GET /agent-activity` data, with a manual Refresh
  button.
- `App.tsx` gains route `/agent-activity` → `AgentActivityPage`.
- `Sidebar.tsx` gains one new `<NavLink to="/agent-activity">` ("Agent
  Activity"), positioned after System Health, matching the approved
  prototype's sidebar order.

---

## Files to Modify

- `src/frontend/src/features/agent-activity/client.ts` (new):

  ```typescript
  import { apiFetch } from '../../api/client';

  export interface AgentActivityLogEntry {
    agent_id: string;
    agent_name: string;
    kind: 'run_event' | 'run_error';
    text: string;
    timestamp: string;
  }

  export interface AgentActivityOutlookChannel {
    reachable: boolean;
    detail: string | null;
  }

  export interface AgentActivityResponse {
    activity_log: AgentActivityLogEntry[];
    outlook_channel: AgentActivityOutlookChannel;
  }

  export function fetchAgentActivity(): Promise<AgentActivityResponse> {
    return apiFetch<AgentActivityResponse>('/agent-activity');
  }
  ```

- `src/frontend/src/pages/AgentActivityPage.tsx` (new):

  ```tsx
  import { useEffect, useState } from 'react';
  import {
    fetchAgentActivity,
    type AgentActivityResponse,
  } from '../features/agent-activity/client';

  export function AgentActivityPage() {
    const [activity, setActivity] = useState<AgentActivityResponse | null>(null);

    const load = () => {
      fetchAgentActivity().then(setActivity);
    };

    useEffect(load, []);

    if (!activity) {
      return (
        <>
          <h1>Agent Activity</h1>
          <p className="text-muted">Loading...</p>
        </>
      );
    }

    return (
      <>
        <h1>Agent Activity</h1>
        <p className="text-muted">
          A chronological record of what background agent runs have happened
          — email, meeting, and (once built) to-do capture — with whether
          each succeeded or failed, plus whether Outlook is currently
          reachable, so a real capture failure is visible in the UI itself
          instead of only discoverable by symptom-chasing or digging through
          server logs (REQ-SB-11).
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
          Both the run list and the Outlook status below recompute fresh on
          open or refresh — never a cached snapshot from an earlier page
          load.
        </p>

        <h2 style={{ marginTop: 'var(--space-6)' }}>Activity log</h2>
        <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
          {activity.activity_log.length > 0 ? (
            <div className="log-list">
              {activity.activity_log.map((entry, index) => (
                <div className="log-item" key={index}>
                  <span>
                    {entry.kind === 'run_error' ? (
                      <span className="badge badge-danger">Failed</span>
                    ) : (
                      <span className="badge badge-success">Success</span>
                    )}{' '}
                    {entry.agent_name} — {entry.text}
                  </span>
                  <span className="log-item-meta">{entry.timestamp}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <p style={{ margin: 0, fontWeight: 600, color: 'var(--color-text)' }}>
                No agent activity recorded yet
              </p>
              <p style={{ margin: 'var(--space-1) 0 0' }}>
                No background capture agent has completed a run yet — shown
                honestly, not fabricated as a run entry or a
                misleadingly-empty "everything is fine" default.
              </p>
            </div>
          )}
        </div>

        <h2 style={{ marginTop: 'var(--space-6)' }}>Communication channels</h2>
        <div className="card">
          <div className="kv-list">
            <div className="kv-row">
              <span className="kv-key">Channel</span>
              <span>Outlook (direct COM)</span>
            </div>
            <div className="kv-row">
              <span className="kv-key">Status</span>
              <span
                className={`badge ${
                  activity.outlook_channel.reachable ? 'badge-success' : 'badge-danger'
                }`}
              >
                {activity.outlook_channel.reachable ? 'Reachable' : 'Unreachable'}
              </span>
            </div>
          </div>
          {!activity.outlook_channel.reachable && activity.outlook_channel.detail && (
            <p
              className="text-muted"
              style={{ margin: 'var(--space-3) 0 0', fontSize: 'var(--font-size-sm)' }}
            >
              Error: {activity.outlook_channel.detail}
            </p>
          )}
        </div>
      </>
    );
  }
  ```

- `src/frontend/src/App.tsx` — add the import and route, additive only:

  ```tsx
  import { AgentActivityPage } from './pages/AgentActivityPage';
  ...
  <Route path="/agent-activity" element={<AgentActivityPage />} />
  ```

- `src/frontend/src/components/shell/Sidebar.tsx` — add one new
  `<NavLink>` after the System Health one, additive only:

  ```tsx
  <NavLink
    to="/agent-activity"
    className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
  >
    <span className="nav-icon">&#128203;</span>
    <span className="nav-label">Agent Activity</span>
  </NavLink>
  ```

---

## Constraints

- Inherits from parent story, and `ADR-010`'s conventions: `react-router`
  `<NavLink>` for the nav item, native `fetch` behind the existing
  `apiFetch` client, class names reused verbatim from already-ported CSS
  — **no new CSS file, no new class**.
- `GET /agent-activity` is re-fetched on every mount and on every manual
  Refresh click — no polling interval, no caching of the previous
  response (Scenario 7).
- Every entry's success/failure badge is driven purely by `kind ===
  "run_error"` — do not introduce a second, parallel success/failure
  signal.
- A failed entry's error detail must be visible without a separate click
  — inline in the log list (the entry's own `text`, which already
  contains "Capture run failed — {exc}" per `T01`'s fix), never hidden
  behind an expand/collapse interaction not in the approved prototype.
- Do not modify `MyDayPage.tsx`, `SettingsPage.tsx`, `AgentsMapPage.tsx`,
  `SystemHealthPage.tsx`, or any other existing page/route.

---

## Tests

<!-- Structural ACs, per the decomposer's own "durable design layer"
rule -- DOM structure/regions, not visual polish. jsdom sees no computed
CSS/layout/colour; pure visual polish is spot-checked against the
approved prototype out-of-band, not a locked AC. -->

**Manual verification steps** (frontend dev server running against the
real backend on port `8001`; open `http://localhost:5173/agent-activity`
in a browser):

1. `[REQ-SB-11-US-01-AC-01]` With at least one real, previously-recorded
   `"run_event"` entry on disk (e.g. from `T01`'s own verification, or a
   real capture tick), open the Agent Activity page. Confirm the Activity
   log card shows at least one entry with the agent that ran, its
   timestamp, and a `badge-success` "Success" outcome, and confirm
   entries render in chronological (newest-first) order.
2. `[REQ-SB-11-US-01-AC-02]` Temporarily induce a real capture failure
   (reuse `T01`'s own induced-failure technique — e.g. monkeypatch
   `run_capture_for_agent` to raise, or close Outlook desktop and trigger
   a real capture tick), then reload the page. Confirm the failed run
   appears with a `badge-danger` "Failed" badge and its real error detail
   text visible inline, not silently dropped. Revert the induced failure
   afterward.
3. `[REQ-SB-11-US-01-AC-03]` With both email-capture's and
   meeting-capture's working modes `autonomous` (the real default) and at
   least one completed tick for each, confirm the Activity log lists runs
   from **both** agents — no configured capture agent's successful runs
   are missing.
4. `[REQ-SB-11-US-01-AC-04]` With Outlook desktop running and reachable,
   open the page. Confirm the Communication channels card shows
   `Status: Reachable` (`badge-success`), no error detail line rendered.
5. `[REQ-SB-11-US-01-AC-05]` Temporarily close Outlook desktop (or
   otherwise make it unreachable), reload the page. Confirm the
   Communication channels card shows `Status: Unreachable` (`badge-danger`
   — visibly distinct from `badge-success`), with the real
   `OutlookUnavailable` error message shown inline. Restart Outlook
   afterward and confirm it flips back on reload.
6. `[REQ-SB-11-US-01-AC-06]` Temporarily rename/move
   `.second-brain/agent_communication_history.json` aside (or use a fresh
   vault with none of the relevant agent ids having ever run), reload the
   page. Confirm the Activity log card shows the honest "No agent activity
   recorded yet" empty state — no fabricated entry, no misleadingly-empty
   "everything is fine" default. Restore the file afterward.
7. `[REQ-SB-11-US-01-AC-07]` After any of the above temporary changes,
   confirm clicking the Refresh button (or reloading the page) reflects
   the current state, not a value cached from an earlier load — verified
   implicitly by steps 2/5/6 above already showing state changes taking
   effect on reload/refresh.
8. Non-AC structural check: confirm a `.nav-item` for "Agent Activity"
   renders in the sidebar on every page (not just this one), and that it
   carries the `active` class only when the current route is
   `/agent-activity`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-11-US-01-AC-01` — completed runs shown chronologically, each
      with agent/timestamp/outcome
- [x] `REQ-SB-11-US-01-AC-02` — a failed run is shown with its error
      detail visible, not silently dropped
- [x] `REQ-SB-11-US-01-AC-03` — every configured capture agent's runs
      appear, not only some of them
- [x] `REQ-SB-11-US-01-AC-04` — Outlook shown as reachable when it is
- [x] `REQ-SB-11-US-01-AC-05` — Outlook shown as unreachable, visibly
      distinguished, when it is not
- [x] `REQ-SB-11-US-01-AC-06` — no runs yet is shown honestly, no
      fabricated entry
- [x] `REQ-SB-11-US-01-AC-07` — reopening/refreshing reflects current
      state, not a cached snapshot
- [x] New `Agent Activity` nav item present and correctly highlighted on
      every page
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `app/business/agent_activity.py`/
  `app/api/agent_activity_router.py` — `T02`/`T03`.
- The `email_classification.py` honest-failure-recording fix's own
  internal mechanics — `T01`; this task only consumes its observable
  effect (real entries appearing via `T02`/`T03`).
- Auto-refresh/polling beyond the manual Refresh button and per-mount
  fetch — the story's own Non-Goals.
- `chat_user`/`chat_agent`/`proposal` entries — remain on
  `AgentDetailPanel.tsx`'s own Communication History tab and the Pending
  Approvals surface respectively, not duplicated here.

---

## Context / Notes

**Gating note:** this story is `gate: clear` (no ADR created/changed at
`/plan-tasks`) — no human-review pointer is required before this task
proceeds to `Ready`.

Reuses `.log-list`/`.log-item`/`.badge*`/`.kv-list`/`.empty-state`/`.btn`
verbatim from already-ported CSS, per the approved prototype's own
"composed entirely from existing tokens/components" header note — no new
CSS file, no new class name.

---

## Implementation Log

**Built 2026-08-13** exactly per the task's own sample (all 4 files:
`client.ts`, `AgentActivityPage.tsx`, `App.tsx` route, `Sidebar.tsx` nav
item). `App.tsx` had drifted from the task's own "Before" sample by build
time (a concurrent sibling session's own `VaultBrowserPage`/
`NoteDetailPage` routes landed mid-session) — composed the new
`/agent-activity` route around the REAL current file, additive only, no
existing route touched.

**Verification-tooling note:** no automated test tooling exists yet
(story-wide `n/a`); this project also has no Layer-1 visual harness
(`npm run visual` or equivalent — confirmed: no such script in
`package.json`, no `playwright`/screenshot dependency anywhere in this
repo). `npx`/`tsc` were also not resolvable on this session's own PATH
(neither Bash nor PowerShell), so a full `tsc -b --noEmit` type-check
could not be run directly; Vite's own dev-server transform of
`AgentActivityPage.tsx` was confirmed live and error-free (fetched the
transformed module directly), and the new code is structurally identical
to `SystemHealthPage.tsx`'s already-verified-live pattern (same
`useEffect`/`useState`/`fetchX().then(setX)` shape, same conditional
badge/kv-list/empty-state composition).

**Real browser verification performed** (the strongest tool actually
available this session — no CDP/screenshot tool was provided to this
Coder instance, so the OS-installed Edge browser's own headless
screenshot mode, `msedge.exe --headless=new --screenshot=...`, was used
as the closest-to-real substitute; genuinely renders the live page via a
real browser engine against the real Vite dev server + real backend, not
a mock):

- **`AC-01`/`AC-03`** — real screenshot of the populated Activity log
  (`agent-activity-populated.png`) against the real, live
  `agent_communication_history.json` (154 real entries by session end):
  both `Email Capture` and `Meeting Capture` agents' runs visible,
  newest-first order confirmed (a `11:50:06` Meeting Capture entry
  precedes an `11:49:00` Email Capture entry, etc.), each entry shows
  agent name, real timestamp, and a `Success`/`Failed` badge. PASS.
- **`AC-02`** — the same screenshot shows a real induced failure entry
  (`T01`'s own Tests-step-2 monkeypatch run) — "Failed / Email Capture —
  Capture run failed — INDUCED-VERIFY: simulated Outlook failure" — with
  its error detail visible inline, not behind any expand/collapse. PASS.
- **`AC-04`** — real screenshot (`agent-activity-empty.png`, taken while
  Outlook was genuinely reachable) shows "Status: Reachable"
  (`badge-success`), no error-detail line rendered. PASS.
- **`AC-05`** — physically closing Outlook does not produce a genuine
  unreachable state on this machine (Windows COM auto-relaunches
  `Dispatch("Outlook.Application")`'s target, confirmed live by Outlook's
  own process `StartTime` advancing immediately after
  `Stop-Process -Force`). Per this project's own established
  "in-process monkeypatch of a real, already-loaded dependency" pattern,
  the live backend on port 8001 was **stopped and temporarily replaced**
  (same port, same real unmodified `app.main:app`, only
  `outlook_com._connect_namespace` monkeypatched in-process before
  import) purely to produce a real, screen-observable unreachable state;
  screenshot (`agent-activity-unreachable-crop.png`) confirms "Status:
  Unreachable" (`badge-danger`, visibly distinct from `badge-success`)
  with the real error detail rendered inline ("Error: INDUCED-VERIFY:
  couldn't connect to Outlook — is it running? (simulated COM failure for
  AC-05 screenshot verification)"). The temporary instance was stopped
  and the real, unmodified backend restarted normally immediately after
  — no lasting code/config change, no lasting side effect beyond the
  disclosed extra real history entries this induced tick itself wrote
  (consistent with this project's own "genuine, disclosed, reverted"
  verification precedent). PASS.
- **`AC-06`** — real screenshot (`agent-activity-empty.png`) taken with
  the real `agent_communication_history.json` moved aside: "No agent
  activity recorded yet" honest empty state rendered, no fabricated
  entry. File restored immediately after. PASS.
- **`AC-07`** — demonstrated implicitly and directly across the above:
  four distinct real state changes (empty → populated → Outlook
  unreachable → reachable again) were each reflected on the very next
  page load/reload with zero caching, confirmed both via the live `GET
  /agent-activity` HTTP response at each step and the corresponding
  screenshot. PASS.
- **Nav-item structural check:** screenshot of `/system-health`
  (`system-health-nav-check.png`) confirms the "Agent Activity" nav item
  renders on every page and carries the `active` class only on its own
  route (`System Health` shown active there instead) — zero regression
  to the untouched System Health page. PASS.

`gate: clear` 2026-08-13 — no MUST-FLAG trigger fired. Honestly disclosed,
scope-internal verification-method notes (not weakenings of any locked
AC): (1) no `npx`/`tsc` on this session's PATH — substituted with a live
Vite-transform check + structural parity with an already-verified
identical pattern; (2) no visual-harness/CDP tool provided to this Coder
instance — substituted with the OS-installed Edge browser's own headless
screenshot mode, which is a real browser engine rendering the real app,
not a weaker mock; (3) `AC-05`'s physical-Outlook-closure technique named
in this task's own Tests block doesn't produce a genuine unreachable
state on this machine (COM auto-relaunch) — substituted with the
same disclosed monkeypatch technique already used successfully for `T01`/
`T02`'s own equivalent checks, applied to a temporary, port-identical,
immediately-reverted backend swap so the check remained genuinely
screen-observable rather than backend-only. Every locked AC was actually,
visually confirmed against real data — none was weakened or skipped.
