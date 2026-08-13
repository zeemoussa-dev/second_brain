---
id: REQ-SB-12-US-02-T06
title: Calendar drill-down page — populated list + empty state
parent_story: REQ-SB-12-US-02
requirement_id: REQ-SB-12
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-12-US-02-T04]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-12-US-02-T06 — Calendar drill-down page

## Parent Story

- Story: [[REQ-SB-12-US-02]] — `../UserStories/REQ-SB-12-US-02-my-day-dashboard-and-drilldowns.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-12 *Primary Application UI Shell — Agents Map & My Day*

---

## Objective

Replace `T04`'s `MyDayCalendarPage.tsx` placeholder with the real Calendar
drill-down: a populated `.item-list` (subject, start time, customer) sourced
from `/my-day/calendar`, or an empty-state message when there are none —
which is the real vault's current state today, since REQ-SB-08 hasn't
shipped.

---

## Starting State → End State

**Before / Inputs:**
- `T04` has landed the `/my-day/calendar` route and its placeholder page.
- `T03` has landed `GET /my-day/calendar` →
  `[{"subject", "start", "customer"}]`, which resolves to `[]` today against
  the real vault (no `Work/Meetings/` folder yet).

**After / Outputs:**
- `pages/MyDayCalendarPage.tsx` renders a back link to `/my-day`, an
  `.item-list` when populated, or an `.empty-state` when empty.
- `features/my-day/client.ts` gains `fetchMyDayCalendar`.

---

## Files to Modify

- `src/frontend/src/features/my-day/client.ts` — add:
  ```ts
  export interface MyDayCalendarItem {
    subject: string;
    start: string;
    customer: string | null;
  }

  export function fetchMyDayCalendar(): Promise<MyDayCalendarItem[]> {
    return apiFetch<MyDayCalendarItem[]>('/my-day/calendar');
  }
  ```

- `src/frontend/src/pages/MyDayCalendarPage.tsx` — replace the `T04`
  placeholder body:
  ```tsx
  import { useEffect, useState } from 'react';
  import { Link } from 'react-router';
  import { fetchMyDayCalendar, type MyDayCalendarItem } from '../features/my-day/client';

  export function MyDayCalendarPage() {
    const [items, setItems] = useState<MyDayCalendarItem[] | null>(null);

    useEffect(() => {
      fetchMyDayCalendar().then(setItems);
    }, []);

    return (
      <>
        <p className="text-muted"><Link className="text-muted" to="/my-day">&larr; My Day</Link></p>
        <h1>Calendar</h1>
        <p className="text-muted">Today's meetings, filed by Meeting Capture (REQ-SB-08).</p>
        <div className="card">
          {items && items.length > 0 ? (
            <div className="item-list">
              {items.map((item, index) => (
                <div className="item-row" key={index}>
                  <div className="item-row-main">
                    <span className="item-row-title">{item.subject}</span>
                    <span className="item-row-meta">
                      {item.start} &middot; {item.customer ?? 'No customer'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            items && (
              <div className="empty-state">
                <div className="empty-state-icon">&#128197;</div>
                <p><strong>No meetings captured yet.</strong></p>
                <p className="text-muted">
                  Meeting Capture (REQ-SB-08) syncs on the same hourly
                  schedule as email — nothing filed yet.
                </p>
              </div>
            )
          )}
        </div>
      </>
    );
  }
  ```

---

## Constraints

- Inherits from parent story: ADR-010's styling convention (`.item-list`/
  `.item-row`/`.empty-state` class names verbatim).
- Must not modify `T04`'s `MyDayPage.tsx`, `App.tsx` routing, or
  `my-day.css`.
- Must tolerate `/my-day/calendar` resolving to `[]` — no special-casing for
  "pipeline not built yet" vs. "pipeline built but found nothing today,"
  matching `T02`/`T03`'s own backend design.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `uvicorn app.main:app --reload --port 8001`; browser preview
tool):

1. **[REQ-SB-12-US-02-AC-07]** Load `/my-day/calendar` with the real backend
   running (real vault has no `Work/Meetings/` folder yet — REQ-SB-08 isn't
   built). Confirm the `.empty-state` element renders with a message
   explaining no meetings have been captured yet.
2. **[REQ-SB-12-US-02-AC-06]** Temporarily write one real Meeting-shaped
   test note under the real vault's `Work/Meetings/` folder (e.g.
   `Work/Meetings/verify-t06-test-meeting.md`, with `subject`/`start`/
   `customer` frontmatter matching `T02`'s resolved schema — same
   real-vault-note technique already used to verify the analogous "populated
   state that doesn't naturally occur yet" case elsewhere in this codebase).
   Reload `/my-day/calendar`. Confirm it renders as an `.item-row` showing
   at least its subject, start time, and customer classification (or "No
   customer"). **Delete the temporary test note afterward** (this task does
   not modify the real vault permanently) and reload once more to confirm
   the empty state (step 1) is restored.
3. Non-AC smoke check: confirm no console errors/warnings on load or after
   the temporary note add/remove in step 2.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Populated state renders one `.item-row` per captured meeting, showing
      subject/start time/customer (or "No customer")
- [x] Empty state renders `.empty-state` with a message explaining no
      meetings have been captured yet
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `MyDayEmailsPage`/`MyDayTodoPage`'s content — `T05`/`T07`.
- Building the REQ-SB-08 Meeting Capture pipeline itself — this page only
  renders whatever it eventually produces.

---

## Context / Notes

Step 2's temporary test note must be deleted before this task is marked
`Done` — leaving it would permanently pollute the real trusted vault with
fabricated data, contrary to this project's own no-staging/trusted-vault
premise (`CLAUDE.md`).

---

## Implementation Log

Implemented exactly as specified — `fetchMyDayCalendar` added to
`features/my-day/client.ts`, `MyDayCalendarPage.tsx`'s real body replacing
`T04`'s placeholder.

**Deviation from the task's own planned verification technique (logged as
an assumption, not a scope change):** the task's Tests section planned
AC-07 (empty state) as the *naturally-occurring* case and AC-06
(populated) via a *temporarily-written real test note* under
`Work/Meetings/` — written when the real vault had no `Work/Meetings/`
folder at all. By the time this task ran, `SPRINT-006` had landed
concurrently and the real vault's `Work/Meetings/` folder already holds
39 real Meeting notes — the natural/synthetic cases are exactly reversed
from what the task anticipated. Verified accordingly: AC-06 (populated)
directly against the now-real 39 Meeting notes (no temporary note needed
or written — cleaner than the task's own plan, nothing to clean up
afterward), and AC-07 (empty) via a temporary stub of `fetchMyDayCalendar`
in `features/my-day/client.ts` (the same technique `T05` already used for
its own AC-05), since the real vault can no longer naturally produce an
empty Calendar drill-down. No real vault file was created or modified by
this task.

**[REQ-SB-12-US-02-AC-06] — PASS.** Loaded `/my-day/calendar` against the
real backend (real data, no stub). 39 `.item-row` elements rendered
(matching the real captured-meeting count), each with subject/start
time/customer. Sample row: subject "0", meta "2026-08-10 10:30:00+00:00 ·
No customer". 3 rows rendered "No customer" (real notes with an empty
`customer` field), confirming the `null` -> "No customer" fallback.

**[REQ-SB-12-US-02-AC-07] — PASS.** Temporarily stubbed
`fetchMyDayCalendar` to return `[]` (see deviation note above). Reloaded
`/my-day/calendar`: `.empty-state` rendered with "No meetings captured
yet." / "Meeting Capture (REQ-SB-08) syncs on the same hourly schedule as
email — nothing filed yet." Reverted the stub; reloaded once more —
confirmed the real populated state (39 rows, same sample row) was
restored exactly.

**Non-AC smoke check — PASS.** Zero console errors/exceptions across the
populated load and the temporary-stub round trip.

gate: clear 2026-08-11 — the verification-technique swap above is a
scope-internal judgement call responding to real vault state changing
underneath the task since it was written, not a material assumption about
this task's own code or a deviation from any locked AC's intent (both ACs
were still fully exercised, just via the other of the two techniques the
task itself already named as acceptable precedent). No `ESCALATIONS.md`
entry needed.
