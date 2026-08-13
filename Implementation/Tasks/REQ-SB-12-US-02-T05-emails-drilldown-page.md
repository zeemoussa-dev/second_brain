---
id: REQ-SB-12-US-02-T05
title: Emails drill-down page — populated list + empty state
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

# REQ-SB-12-US-02-T05 — Emails drill-down page

## Parent Story

- Story: [[REQ-SB-12-US-02]] — `../UserStories/REQ-SB-12-US-02-my-day-dashboard-and-drilldowns.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-12 *Primary Application UI Shell — Agents Map & My Day*

---

## Objective

Replace `T04`'s `MyDayEmailsPage.tsx` placeholder with the real Emails
drill-down: a populated `.item-list` (subject, sender, customer) sourced
from `/my-day/emails`, or an empty-state message when there are none.

---

## Starting State → End State

**Before / Inputs:**
- `T04` has landed the `/my-day/emails` route and its placeholder page, plus
  `my-day.css`'s `.item-list`/`.item-row` classes and
  `features/my-day/client.ts`.
- `T03` has landed `GET /my-day/emails` →
  `[{"subject", "sender", "customer"}]`.

**After / Outputs:**
- `pages/MyDayEmailsPage.tsx` renders a back link to `/my-day`, an
  `.item-list` of `.item-row`s (one per captured email) when populated, or
  an `.empty-state` when the list is empty.
- `features/my-day/client.ts` gains `fetchMyDayEmails`.

---

## Files to Modify

- `src/frontend/src/features/my-day/client.ts` — add:
  ```ts
  export interface MyDayEmailItem {
    subject: string;
    sender: string;
    customer: string | null;
  }

  export function fetchMyDayEmails(): Promise<MyDayEmailItem[]> {
    return apiFetch<MyDayEmailItem[]>('/my-day/emails');
  }
  ```

- `src/frontend/src/pages/MyDayEmailsPage.tsx` — replace the `T04`
  placeholder body:
  ```tsx
  import { useEffect, useState } from 'react';
  import { Link } from 'react-router';
  import { fetchMyDayEmails, type MyDayEmailItem } from '../features/my-day/client';

  export function MyDayEmailsPage() {
    const [items, setItems] = useState<MyDayEmailItem[] | null>(null);

    useEffect(() => {
      fetchMyDayEmails().then(setItems);
    }, []);

    return (
      <>
        <p className="text-muted"><Link className="text-muted" to="/my-day">&larr; My Day</Link></p>
        <h1>Emails</h1>
        <p className="text-muted">Recently captured email, filed by Email Capture (REQ-SB-07).</p>
        <div className="card">
          {items && items.length > 0 ? (
            <div className="item-list">
              {items.map((item, index) => (
                <div className="item-row" key={index}>
                  <div className="item-row-main">
                    <span className="item-row-title">{item.subject}</span>
                    <span className="item-row-meta">
                      {item.customer ?? 'Unclassified'} &middot; from {item.sender}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            items && (
              <div className="empty-state">
                <div className="empty-state-icon">&#9993;</div>
                <p><strong>No emails captured yet.</strong></p>
                <p className="text-muted">
                  Email Capture runs hourly and once on app start — check
                  back after the next run.
                </p>
              </div>
            )
          )}
        </div>
      </>
    );
  }
  ```
  (`items &&` guards render nothing during the initial fetch — no locked AC
  requires a distinct loading state; `key={index}` is acceptable here since
  the list is read-only and never reordered client-side.)

---

## Constraints

- Inherits from parent story: ADR-010's styling convention (`.item-list`/
  `.item-row`/`.empty-state` class names verbatim, no renaming).
- Must not modify `T04`'s `MyDayPage.tsx`, `App.tsx` routing, or
  `my-day.css`.
- `customer` renders `"Unclassified"` for `null` — the frontend's own
  rendering choice for `T02`'s `null` convention, not a new backend
  sentinel.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `uvicorn app.main:app --reload --port 8001`; browser preview
tool):

1. **[REQ-SB-12-US-02-AC-04]** Load `/my-day/emails` with the real backend
   running (real vault already has captured emails per `MEMORY.md`).
   Confirm each real captured email renders as an `.item-row` showing at
   least its subject, sender, and customer classification (or
   "Unclassified" for one classified `Unsorted`/absent, if any exist).
2. **[REQ-SB-12-US-02-AC-05]** Temporarily stub `fetchMyDayEmails` in
   `features/my-day/client.ts` to return `[]` instead of calling the real
   endpoint (mirroring `REQ-SB-12-US-01-T02`'s established
   temporarily-swap-and-revert technique — the real vault already has
   captured emails, so this state cannot occur naturally against live
   data). Reload `/my-day/emails`. Confirm the `.empty-state` element
   renders with a message explaining Email Capture has not produced
   anything yet. Revert the temporary stub and reload once more to confirm
   the real populated state (step 1) is restored.
3. Non-AC smoke check: confirm no console errors/warnings on load or after
   the temporary stub swap in step 2.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Populated state renders one `.item-row` per captured email, showing
      subject/sender/customer (or "Unclassified")
- [x] Empty state renders `.empty-state` with a message explaining Email
      Capture hasn't produced anything yet
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `MyDayCalendarPage`/`MyDayTodoPage`'s content — `T06`/`T07`.
- Any email action (reply, mark read, etc.) — not requested by any locked AC.

---

## Context / Notes

None beyond what's in Files to Modify.

---

## Implementation Log

Implemented exactly as specified — `fetchMyDayEmails` added to
`features/my-day/client.ts`, `MyDayEmailsPage.tsx`'s real body replacing
`T04`'s placeholder.

**[REQ-SB-12-US-02-AC-04] — PASS.** Loaded `/my-day/emails` against the
real backend. 178 `.item-row` elements rendered (matching the real
captured-email count), each with a subject/sender/customer. Sample row:
subject "Involuntary Loss of Employment Insurance (ILOE)", meta "Core42 ·
from HC Onboarding Team". 5 rows rendered "Unclassified" (real notes with
an absent/`"Unsorted"` customer field), confirming the `null` ->
"Unclassified" fallback.

**[REQ-SB-12-US-02-AC-05] — PASS.** Temporarily stubbed `fetchMyDayEmails`
to return `[]` (real vault data cannot naturally produce this state
today). Reloaded `/my-day/emails`: `.empty-state` rendered with "No emails
captured yet." / "Email Capture runs hourly and once on app start — check
back after the next run." Reverted the stub; reloaded once more — confirmed
the real populated state (178 rows, same sample row) was restored exactly.

**Non-AC smoke check — PASS.** Zero console errors/exceptions across both
the populated load and the temporary-stub round trip.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired.
