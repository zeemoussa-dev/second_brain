---
id: REQ-SB-22-US-01-T02
title: Emails/Calendar drill-downs and dashboard consume the windowed response; Emails row gains a received date
parent_story: REQ-SB-22-US-01
requirement_id: REQ-SB-22
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-22-US-01-T01]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-22-US-01-T02 — Drill-downs and dashboard consume the windowed response

## Parent Story

- Story: [[REQ-SB-22-US-01]] — `../UserStories/REQ-SB-22-US-01-my-day-rolling-7-day-window.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-22 *My Day Rolling 7-Day Window*

---

## Objective

Widen `MyDayEmailItem` to carry the new `received` field `T01` adds and
render it on each Emails row; verify live that Emails, Calendar, and the
My Day dashboard all correctly reflect the now-windowed, backend-filtered
data with no other frontend code changes needed.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed backend query-time 7-day-window filtering in
  `app/business/my_day.py`; `GET /my-day/emails` now returns a `received`
  field per item and only items inside the window; `GET /my-day/calendar`
  and `GET /my-day/summary` are correspondingly narrower with unchanged
  shapes.
- `features/my-day/client.ts`'s `MyDayEmailItem` interface has `subject`/
  `sender`/`customer` only (no `received`).
- `pages/MyDayEmailsPage.tsx` renders each row's subject/sender/customer,
  no date.
- `pages/MyDayCalendarPage.tsx` already renders `item.start` per row —
  unaffected by the new field, but now consumes a narrower list.
- `pages/MyDayPage.tsx` already renders `summary()`'s counts unchanged —
  unaffected by any file edit in this task, but now displays windowed
  counts once `T01` is deployed.

**After / Outputs:**
- `MyDayEmailItem` gains `received: string`.
- `MyDayEmailsPage.tsx` renders each row's received date alongside its
  existing subject/sender/customer, in the same `.item-row-meta` line
  Calendar already uses for `start`.
- No other file changes; `MyDayCalendarPage.tsx`/`MyDayPage.tsx` are
  verified live as correct, already-working consumers of the narrower
  backend response, with zero code changes needed in either.

---

## Files to Modify

- `src/frontend/src/features/my-day/client.ts` — widen the existing
  `MyDayEmailItem` interface only (no other export changes):
  ```ts
  export interface MyDayEmailItem {
    subject: string;
    sender: string;
    customer: string | null;
    received: string;
  }
  ```

- `src/frontend/src/pages/MyDayEmailsPage.tsx` — add the received date to
  the existing meta line:
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
                      {item.received} &middot; {item.customer ?? 'Unclassified'} &middot; from {item.sender}
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
  (Only the `.item-row-meta` line's content changes — one added
  `{item.received} &middot; ` prefix; everything else is identical to the
  already-`Done` `REQ-SB-12-US-02-T05` version.)

---

## Constraints

- Inherits from parent story: ADR-010's styling convention (`.item-list`/
  `.item-row`/`.item-row-meta`/`.empty-state` class names verbatim, no
  renaming, no new component/region).
- Must NOT modify `MyDayCalendarPage.tsx`, `MyDayPage.tsx`,
  `MyDayTodoPage.tsx`, `App.tsx` routing, or `my-day.css` — out of this
  story's scope per the architect's own note.
- `received` renders as the raw ISO date-prefixed string the backend
  returns — no client-side date formatting/parsing is introduced (matches
  `T01`'s own "no timezone conversion" constraint).

---

## Tests

<!-- AC-01/AC-02/AC-05/AC-06 are the user-observable Gherkin scenarios —
verified here, live, on the actual pages a user visits. AC-03/AC-04 are
verified in T01 (backend-level manipulation, since neither "confirm an
item is truly absent" nor "simulate a later day" can be usefully
distinguished from AC-01/AC-02's own live-page checks without also
re-deriving the raw vault date list — already done once, in T01; not
repeated here to avoid re-triggering the same real-world observation
twice for no new evidence, per MEMORY.md's consolidation pattern). -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001` or next free
port per `MEMORY.md`'s port-conflict constraint; from `src/frontend`:
`npm run dev`; CDP-based headless-Chrome live browser verification per
`MEMORY.md`'s established technique):

1. **[REQ-SB-22-US-01-AC-01]** Load `/my-day/emails` against the real
   backend (real vault has captured emails per `MEMORY.md`). Confirm every
   rendered `.item-row` shows a received date in its `.item-row-meta` text
   (matching the corresponding note's real `received` frontmatter value),
   and confirm the number of rendered rows matches
   `GET /my-day/emails`'s own real response length for the current
   window — not the full all-time count (compare against `T01`'s own
   Implementation Log figures or a fresh direct call to the endpoint).
2. **[REQ-SB-22-US-01-AC-02]** Load `/my-day/calendar` against the real
   backend. Confirm every rendered `.item-row` shows its existing
   date/time (`item.start`, unchanged rendering) and that the rendered row
   count matches `GET /my-day/calendar`'s own real windowed response
   length — including confirming at least one rendered meeting's `start`
   date is in the future relative to today, if the real vault has one
   (Meeting Capture, REQ-SB-08, captures upcoming meetings).
3. **[REQ-SB-22-US-01-AC-05]** Load `/my-day` (the dashboard). Confirm the
   Emails and Calendar section counts shown match `GET /my-day/summary`'s
   own real response (`emails.count`/`calendar.count`), and that those
   counts equal the row counts confirmed live in steps 1 and 2 — not a
   larger, all-time figure.
4. **[REQ-SB-22-US-01-AC-06]** Temporarily stub `fetchMyDayEmails` (and,
   separately, `fetchMyDayCalendar`) in `features/my-day/client.ts` to
   return `[]` instead of calling the real endpoint (the real vault
   already has captured data inside the window, so this state cannot
   occur naturally today — mirroring `REQ-SB-12-US-02-T05`'s established
   temporary-stub-and-revert technique). Reload `/my-day/emails`, confirm
   the existing `.empty-state` ("No emails captured yet.") renders
   unchanged; reload `/my-day/calendar`, confirm its own existing
   `.empty-state` ("No meetings captured yet.") renders unchanged. Revert
   both stubs and reload each page once more to confirm the real populated
   states (steps 1/2) are restored exactly.
5. Non-AC smoke check: confirm no console errors/warnings across all four
   page loads and the temporary-stub round trip in step 4.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Each Emails row renders its `received` date alongside subject/
      sender/customer
- [x] Emails/Calendar drill-downs render exactly the windowed rows the
      backend returns — no larger, unfiltered count
- [x] The My Day dashboard's Emails/Calendar counts match the windowed
      row counts, not the all-time totals
- [x] Both drill-downs' existing empty state renders unchanged when their
      windowed response is empty
- [x] `MyDayCalendarPage.tsx`/`MyDayPage.tsx`/`MyDayTodoPage.tsx`/`App.tsx`/
      `my-day.css` left unmodified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `MyDayCalendarPage.tsx`, `MyDayPage.tsx`,
  `MyDayTodoPage.tsx` — verified live only, no code edits.
- A grouped-by-day layout or day navigator — explicitly rejected
  presentation options per the parent story's own Non-Goals.
- Any client-side date filtering or formatting — filtering is entirely
  backend-side (`T01`); this task only renders the field it's given.

---

## Context / Notes

Matches `architecture.md`'s "Amendment — rolling 7-day window
date-filtering (REQ-SB-22-US-01)" section: "Frontend changes are additive
only... `MyDayEmailItem` gains a `received: string` field, rendered in the
existing `.item-row-meta` line... No new component, region, or route."

---

## Implementation Log

**Coder pass, 2026-08-11.** Implemented both files exactly as specified in
this task's `## Files to Modify`: `MyDayEmailItem` gained `received:
string` in `client.ts`; `MyDayEmailsPage.tsx`'s existing `.item-row-meta`
line gained a `{item.received} · ` prefix, no other change to that file.
No deviations from the plan. `MyDayCalendarPage.tsx`, `MyDayPage.tsx`,
`MyDayTodoPage.tsx`, `App.tsx`, and `my-day.css` were read but not touched.

Live verification setup: backend `uvicorn app.main:app --port 8002`
(ports 8000/8001 already occupied by other concurrent sessions, per
`MEMORY.md`'s standing port-scan constraint), frontend `npm run dev --
--port 5174` with `VITE_API_BASE_URL=http://127.0.0.1:8002` set as a
process-only environment override (port 5173 also already occupied by a
concurrent session; `.env.local`'s own committed value was left
untouched, out of this task's `## Files to Modify`), against the real,
`.env`-configured vault. Verified in a real browser via headless
Chrome + CDP (`--headless=new --remote-debugging-port=9333`), per
`MEMORY.md`'s established zero-dependency frontend-verification pattern
(precedent: `SPRINT-008`/`SPRINT-009`).

- **[REQ-SB-22-US-01-AC-01]** PASS. `/my-day/emails` rendered exactly 21
  `.item-row` elements, matching `GET /my-day/emails`'s own real windowed
  response length (confirmed against `T01`'s own Implementation Log
  figures and a fresh `GET /my-day/summary` call: `emails.count: 21`).
  Every rendered row's `.item-row-meta` text starts with a real received
  date (e.g. `2026-08-09 20:55:47.386000+00:00 · ADNOC · from Mohamed
  Eltanany`) — screenshot captured and visually reviewed, matching the
  approved `.item-list`/`.item-row` prototype pattern with the one
  additive date field.
- **[REQ-SB-22-US-01-AC-02]** PASS. `/my-day/calendar` rendered exactly 17
  `.item-row` elements, matching `GET /my-day/calendar`'s real windowed
  response length (`calendar.count: 17`). Each row shows its existing
  `start` date/time unchanged (e.g. `2026-08-10 10:30:00+00:00 · No
  customer`). Today is 2026-08-11; rendered rows include real meetings on
  2026-08-12 and 2026-08-13 — confirmed future meetings are included, not
  just today's.
- **[REQ-SB-22-US-01-AC-05]** PASS. `/my-day` dashboard rendered `Emails
  21` and `Calendar 17`, matching `GET /my-day/summary`'s real response
  (`{"emails":{"count":21},"calendar":{"count":17},"todo":{"count":0}}`)
  exactly, and matching the row counts confirmed live in AC-01/AC-02 above
  — not a larger, all-time figure (the real vault has 179 total Email
  notes and 39 total Meeting notes, both far larger than the windowed
  counts shown).
- **[REQ-SB-22-US-01-AC-06]** PASS. Temporarily stubbed
  `fetchMyDayEmails`/`fetchMyDayCalendar` in `client.ts` (each body
  replaced with `Promise.resolve([])`, mirroring
  `REQ-SB-12-US-02-T05`/`T06`'s established temporary-stub-and-revert
  technique — the real vault already has real data inside the window, so
  this state cannot occur naturally today). Reloaded `/my-day/emails`:
  the existing `.empty-state` rendered unchanged ("No emails captured
  yet." + the existing hourly-schedule copy), screenshot captured and
  visually reviewed. Reloaded `/my-day/calendar`: its own existing
  `.empty-state` rendered unchanged ("No meetings captured yet." + the
  existing copy), screenshot captured and visually reviewed. Reverted both
  stubs back to their real `apiFetch(...)` calls and reloaded both pages
  once more: `/my-day/emails` restored to 21 rows, `/my-day/calendar`
  restored to 17 rows — the real populated states from AC-01/AC-02 are
  restored exactly, byte-for-byte code identical to before the stub. No
  vault file was ever created or needed.
- **Non-AC smoke check** PASS. Zero console errors/warnings captured (via
  CDP `Console.enable`/`Runtime.enable` listening through page navigation)
  across all three pages (`/my-day/emails`, `/my-day/calendar`, `/my-day`)
  both before and after the stub-and-revert round trip in AC-06.

`npm run build` (`tsc -b && vite build`) ran clean — zero TypeScript
errors, build succeeded in 170ms.

Cleanup: the headless-Chrome CDP process, the backend dev server (port
8002), and the frontend dev server (port 5174) were each stopped by their
own specific PID (`Stop-Process -Id <pid>`), never by image name, per
`MEMORY.md`'s standing constraint against `taskkill /IM <name> /F /T` in
this multi-concurrent-session environment.

`gate: clear` 2026-08-11 — no MUST-FLAG trigger fired: no new dependency,
no shared-interface change, no ADR deviation, no unanticipated file (the
`VITE_API_BASE_URL` process-env override was a local dev-run convenience,
not a file edit, and `.env.local`'s committed value is untouched), all 4
locked ACs verified live in a real browser against real data with exact
count/content matches, not approximations. Task `status: Ready -> Done`.
