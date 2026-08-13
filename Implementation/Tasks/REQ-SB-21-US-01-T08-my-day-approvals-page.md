---
id: REQ-SB-21-US-01-T08
title: New MyDayApprovalsPage.tsx (/my-day/approvals) — the background-pipeline Pending Approvals surface; App.tsx route + MyDayPage.tsx new card
parent_story: REQ-SB-21-US-01
requirement_id: REQ-SB-21
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-21-US-01-T06, REQ-SB-21-US-01-T07]
created: 2026-08-12
updated: 2026-08-12
---

**Re-confirmed unchanged, 2026-08-12 (`ADR-020` decomposer pass).** This
task's own design is untouched by `ADR-020`. **AC-tag renumbering only:**
the old `AC-05` (pre-re-spec "Supervised background also waits" scenario)
is now `AC-03` (the merged, current "mutating action proposes+waits,
regardless of trigger" scenario) — this page/card demonstrates its
background-trigger half from the frontend side, completing `T04`'s
chat/direct-side and `T05`'s backend-background-side verification of the
same AC.

# REQ-SB-21-US-01-T08 — New MyDayApprovalsPage.tsx

## Parent Story

- Story: [[REQ-SB-21-US-01]] — `../UserStories/REQ-SB-21-US-01-agent-working-modes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-21 *Agent Working Modes*

---

## Objective

Add `MyDayApprovalsPage.tsx` (route `/my-day/approvals`) — the real,
dedicated Pending Approvals surface `REQ-SB-21` requires for a Supervised
agent's **background/scheduled-pipeline** proposal (`AC-03`), per the
approved `html-prototype/my-day-approvals.html`. Add a new card to
`MyDayPage.tsx` linking to it. `app/business/my_day.py`/
`app/api/my_day_router.py` are **not** touched — this page fetches
`GET /pending-approvals` directly (`ADR-018`'s own "Alternatives
Considered" rejection of rolling this into `GET /my-day/summary`).

---

## Starting State → End State

**Before / Inputs:**
- `T07` has landed `pendingApprovalsApiClient.ts` (`fetchPendingApprovals`,
  `approvePendingApproval`, `declinePendingApproval`).
- `T06` has landed the real `GET /pending-approvals`, `POST
  /pending-approvals/{id}/approve|decline` backend.
- `MyDayPage.tsx` currently renders a 3-entry `SECTIONS` grid (Emails,
  Calendar, To-Do) plus a `fetchMyDaySummary()` count per section.
- `App.tsx` currently routes `/`, `/my-day`, `/my-day/emails`,
  `/my-day/calendar`, `/my-day/todo`, `/settings`.

**After / Outputs:**
- New `src/frontend/src/pages/MyDayApprovalsPage.tsx` — lists every
  `status: "pending"` approval (chat/direct proposals still resolve via
  each agent's own panel per `T07`; this page is specifically the
  background-pipeline-trigger surface a Supervised agent's own chat panel
  cannot cover, since the pipeline trigger fires with no chat window
  open) with working Approve/Decline actions, and an empty "queue caught
  up" state.
- `App.tsx` gains the `/my-day/approvals` route.
- `MyDayPage.tsx` gains a new "Pending Approvals" card linking to it, with
  its own live pending count.

---

## Files to Modify

- `src/frontend/src/pages/MyDayApprovalsPage.tsx` (new):
  ```tsx
  import { useEffect, useState } from 'react';
  import { Link } from 'react-router';
  import {
    fetchPendingApprovals,
    approvePendingApproval,
    declinePendingApproval,
    type PendingApproval,
  } from '../features/agents-map/pendingApprovalsApiClient';

  export function MyDayApprovalsPage() {
    const [items, setItems] = useState<PendingApproval[] | null>(null);

    function refresh() {
      fetchPendingApprovals({ status: 'pending' }).then(setItems);
    }

    useEffect(() => {
      refresh();
    }, []);

    async function handleApprove(id: string) {
      await approvePendingApproval(id);
      refresh();
    }

    async function handleDecline(id: string) {
      await declinePendingApproval(id);
      refresh();
    }

    return (
      <>
        <p className="text-muted"><Link className="text-muted" to="/my-day">&larr; My Day</Link></p>
        <h1>Pending Approvals</h1>
        <p className="text-muted">
          Actions a Supervised agent has proposed on its own background/
          scheduled pipeline trigger and is waiting on your approval before
          taking. Chat-triggered proposals from an active conversation
          appear inline in that agent's own Chat panel on the Agents Map
          instead of here. Change an agent's working mode from its Agent
          Settings panel.
        </p>
        <div className="card">
          {items && items.length > 0 ? (
            <div className="item-list">
              {items.map((item) => (
                <div className="item-row" key={item.id}>
                  <div className="item-row-main">
                    <span className="item-row-title">
                      {item.agent_name} <span className="badge badge-warning">Awaiting approval</span>
                    </span>
                    <span className="item-row-meta">{item.description}</span>
                  </div>
                  <div className="item-row-actions">
                    <button type="button" className="btn btn-primary" onClick={() => handleApprove(item.id)}>
                      Approve
                    </button>
                    <button type="button" className="btn btn-danger" onClick={() => handleDecline(item.id)}>
                      Decline
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            items && (
              <div className="empty-state">
                <div className="empty-state-icon">&#10003;</div>
                <p><strong>Nothing awaiting approval right now.</strong></p>
                <p className="text-muted">
                  Every Supervised agent's queue is caught up. Proposals from
                  a background/scheduled pipeline trigger will appear here
                  as soon as one is raised.
                </p>
              </div>
            )
          )}
        </div>
      </>
    );
  }
  ```

- `src/frontend/src/App.tsx` — add the import and route:
  ```tsx
  import { MyDayApprovalsPage } from './pages/MyDayApprovalsPage';
  ...
  <Route path="/my-day/approvals" element={<MyDayApprovalsPage />} />
  ```
  (Alongside the existing `/my-day/*` routes — additive only, no
  reordering.)

- `src/frontend/src/pages/MyDayPage.tsx` — add the import:
  ```tsx
  import { fetchPendingApprovals } from '../features/agents-map/pendingApprovalsApiClient';
  ```
  Add a new piece of state and fetch, alongside `summary`:
  ```tsx
  const [approvalsCount, setApprovalsCount] = useState<number | null>(null);

  useEffect(() => {
    fetchMyDaySummary().then(setSummary);
    fetchPendingApprovals({ status: 'pending' }).then((items) => setApprovalsCount(items.length));
  }, []);
  ```
  Add a new card after the `SECTIONS.map(...)` block, inside the same
  `.day-section-grid`:
  ```tsx
  <Link className="card day-section-card" to="/my-day/approvals">
    <h2>Pending Approvals</h2>
    {approvalsCount !== null && approvalsCount > 0 ? (
      <div className="day-section-count">{approvalsCount}</div>
    ) : (
      <span className="text-muted">Nothing awaiting approval yet</span>
    )}
  </Link>
  ```

---

## Constraints

- Inherits from parent story: `app/business/my_day.py`/`app/api/
  my_day_router.py` must NOT be modified — this page and card fetch
  `GET /pending-approvals` directly, never through `/my-day/summary`.
- `ADR-010`'s class-name-verbatim convention (`.card`, `.day-section-
  card`, `.day-section-count`, `.item-list`, `.item-row`, `.item-row-
  main`, `.item-row-title`, `.item-row-meta`, `.item-row-actions`,
  `.empty-state`, `.empty-state-icon`, `.badge-warning`) — reused exactly
  as the approved `my-day-approvals.html`/existing My Day drilldown pages
  define them, no new CSS.
- Approve/Decline on this page must call the real endpoints and
  re-fetch the list afterward — no optimistic local-only removal.
- Must NOT modify `MyDayEmailsPage.tsx`, `MyDayCalendarPage.tsx`,
  `MyDayTodoPage.tsx`, or the existing 3 `SECTIONS` entries in
  `MyDayPage.tsx` — additive extension only.
- Do not reorder any existing `App.tsx` route.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`;
browser preview tool; deliberate — step 2 triggers one real capture run
on Approve):

1. Non-AC smoke check: with no pending approvals (a fresh
   `.second-brain/agent_pending_approvals.json` or every existing record
   already resolved), navigate to `/my-day` — confirm the new "Pending
   Approvals" card reads "Nothing awaiting approval yet". Click through to
   `/my-day/approvals` — confirm the same empty state renders there
   ("Nothing awaiting approval right now.").
2. **[REQ-SB-21-US-01-AC-03]** Set `meeting-capture`'s working mode to
   "Supervised" (via its Agent Settings panel). Trigger a real background
   tick — call `POST /agents/meeting-capture/actions/run_capture_now`
   is **not** the background path; instead, from a backend Python shell,
   call `email_classification.run_capture_and_record_completion()` once
   (the same call the scheduler makes) to raise a real
   `trigger="background"` proposal. Navigate to `/my-day` — confirm the
   "Pending Approvals" card now shows a count of at least 1. Navigate to
   `/my-day/approvals` — confirm an item row for "Meeting Capture" is
   listed with the "Awaiting approval" badge and its own description.
   Click **Approve** — confirm the row disappears from the list (list
   re-fetched, `status: "pending"` filter now excludes it) and, via `GET
   /agents/meeting-capture/history`, a new `run_event` entry confirms the
   real meeting-capture step ran. Reassign `meeting-capture` back to
   "Autonomous" afterward.
3. Non-AC smoke check: repeat step 2's setup (Supervised, one real
   background tick) once more, then click **Decline** on the resulting
   row instead of Approve — confirm the row disappears from the list, and
   no new "run_event" success entry appears in `meeting-capture`'s
   history afterward (only the "Declined — no action taken" entry).
   Reassign `meeting-capture` back to "Autonomous".
4. Non-AC smoke check: zero console errors/warnings across the whole
   sequence.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] **AC-03** (frontend/background half — completing `T04`'s chat/direct
      half and `T05`'s backend-background half) — a real Supervised agent's
      background-pipeline proposal is visible and actionable on the
      standalone `/my-day/approvals` surface, not just via direct API calls
- [ ] The empty state renders correctly on both `/my-day` (the card) and
      `/my-day/approvals` (the page) when no approval is pending
- [ ] Approve/Decline on this page call the real endpoints and the list
      reflects the outcome without a manual page reload
- [ ] `app/business/my_day.py`/`app/api/my_day_router.py` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Chat-triggered proposal rendering (the `.chat-proposal` card on the
  Agents Map panel) — already landed by `T07`.
- Any change to `/my-day/summary`'s existing 3-key shape
  (`emails`/`calendar`/`todo`) — this page/card fetches
  `/pending-approvals` independently.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-018` created, later
`ADR-020` superseded points 3/5 only — this task's own frontend scope is
unaffected by `ADR-020`) — the human reviews `ADR-020` and this task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside the rest of the story.

This is the last task across this story's full breakdown. Once it lands,
every locked AC in `REQ-SB-21-US-01` has a passing, tagged, live-verified
check. The real `MyDayPage.tsx` currently has 3 `SECTIONS` entries (no
"Important Reads" card exists yet in the built app, unlike the
`html-prototype/my-day.html` prototype's own further-ahead 5-card
revision) — this task's new card is additive to whatever `SECTIONS`
currently renders, not tied to a specific card count/position.

---

## Implementation Log

**2026-08-12, coder (`/implement-sprint`, `SPRINT-021`).** Built exactly
as specified, composed around the REAL current `MyDayPage.tsx` — it had
already grown beyond the task's own stale sample (a `selectedDay`
navigator, `shiftDay`/`formatWindowRange`, `SECTIONS.map` with
`?day=`-scoped hrefs — `REQ-SB-22-US-01`'s rolling-7-day-window story,
landed after this task was authored). The new `approvalsCount`
state/fetch was added as its own independent `useEffect` (approvals are
not day-scoped, unlike `summary`), and the new card was appended after
the real `SECTIONS.map(...)` block inside the same `.day-section-grid`,
preserving every existing card/navigator control untouched. All CSS
classes used (`.item-list`/`.item-row*`/`.empty-state*`) already
existed in `src/frontend/src/styles/{my-day,settings}.css` — no new CSS
needed for this task.

**Live verification** (real backend port 8002, real frontend on 5173,
headless-Chrome-via-CDP, screenshots saved to this session's
scratchpad):

- Non-AC smoke check: with zero pending approvals, `/my-day`'s new
  "Pending Approvals" card read "Nothing awaiting approval yet";
  `/my-day/approvals` showed the same empty state ("Nothing awaiting
  approval right now."). PASS.
- **[AC-03]** (frontend/background half) Set `meeting-capture`
  Supervised, ran a real `run_capture_and_record_completion()` tick
  from a backend shell (the same call the scheduler makes) — raised a
  real `trigger="background"` proposal. `/my-day`'s card now showed
  count `1`; `/my-day/approvals` listed a "Meeting Capture" row with
  the "Awaiting approval" badge and its real description. Clicked
  **Approve** in the real browser — the row disappeared from the list
  after the real ~4-minute `classify_recent_meetings()` sweep
  completed and the list re-fetched (`status: "pending"` filter
  correctly excluded it); confirmed via history a new `run_event`
  landed. Repeated with **Decline** on a fresh proposal — the row
  disappeared, only the "Declined — no action taken" entry appeared
  (no success `run_event`). PASS.
- Console/network check: zero errors after `T07`'s own fix (see its
  Implementation Log) was applied — re-verified across a full
  `/my-day` → `/my-day/approvals` navigation.

Gate: `clear` — the locked AC this task carries (`AC-03`, completing
its frontend/background half alongside `T04`'s chat/direct half and
`T05`'s backend-background half) was verified live; no MUST-FLAG
trigger fired.
