---
id: REQ-SB-12-US-02-T07
title: To-Do drill-down page — empty state only
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

# REQ-SB-12-US-02-T07 — To-Do drill-down page (empty state only)

## Parent Story

- Story: [[REQ-SB-12-US-02]] — `../UserStories/REQ-SB-12-US-02-my-day-dashboard-and-drilldowns.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-12 *Primary Application UI Shell — Agents Map & My Day*

---

## Objective

Replace `T04`'s `MyDayTodoPage.tsx` placeholder with the To-Do drill-down's
**empty state only** — deliberately no populated-state field set this pass
(waiting on REQ-SB-09's still-unresolved task source, per the story's own
Non-Goals).

---

## Starting State → End State

**Before / Inputs:**
- `T04` has landed the `/my-day/todo` route and its placeholder page.
- `T03` has landed `GET /my-day/todo` → always `[]`, hardcoded.

**After / Outputs:**
- `pages/MyDayTodoPage.tsx` renders a back link to `/my-day` and a permanent
  `.empty-state` — no populated-state branch exists in this task's code at
  all (unlike `T05`/`T06`, which do have one).

---

## Files to Modify

- `src/frontend/src/features/my-day/client.ts` — add:
  ```ts
  export function fetchMyDayTodo(): Promise<unknown[]> {
    return apiFetch<unknown[]>('/my-day/todo');
  }
  ```
  (Called once for parity with `T05`/`T06`'s fetch-on-mount shape and to
  exercise the real endpoint round-trip, even though the response is always
  `[]` and nothing branches on it this pass.)

- `src/frontend/src/pages/MyDayTodoPage.tsx` — replace the `T04` placeholder
  body:
  ```tsx
  import { useEffect } from 'react';
  import { Link } from 'react-router';
  import { fetchMyDayTodo } from '../features/my-day/client';

  export function MyDayTodoPage() {
    useEffect(() => {
      fetchMyDayTodo();
    }, []);

    return (
      <>
        <p className="text-muted"><Link className="text-muted" to="/my-day">&larr; My Day</Link></p>
        <h1>To-Do</h1>
        <p className="text-muted">Tasks captured by To-Do Capture (REQ-SB-09).</p>
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">&#9745;</div>
            <p><strong>No tasks captured yet.</strong></p>
            <p className="text-muted">
              To-Do Capture (REQ-SB-09) has not been built yet.
            </p>
          </div>
        </div>
      </>
    );
  }
  ```

---

## Constraints

- Inherits from parent story: ADR-010's styling convention (`.empty-state`
  class name verbatim).
- **No populated-state branch, field set, or mock data of any kind** — the
  story's own Non-Goals explicitly defer this to a future story once
  REQ-SB-09 resolves its task source; inventing a placeholder field set here
  would pre-empt that future spec pass.
- Must not modify `T04`'s `MyDayPage.tsx`, `App.tsx` routing, or
  `my-day.css`.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `uvicorn app.main:app --reload --port 8001`; browser preview
tool):

1. **[REQ-SB-12-US-02-AC-08]** Load `/my-day/todo`. Confirm the
   `.empty-state` element renders with a message explaining no tasks have
   been captured yet — this is the page's only state, always true today
   (`GET /my-day/todo` always returns `[]`).
2. Non-AC smoke check: confirm no console errors/warnings on load.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `MyDayTodoPage.tsx` always renders `.empty-state` with a message
      explaining no tasks have been captured yet
- [x] No populated-state code path exists in this task's output
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any populated-state field set (subject/customer/due-date, etc.) — deferred
  to a future story once REQ-SB-09 resolves its task source (see the parent
  story's own Non-Goals).
- `MyDayEmailsPage`/`MyDayCalendarPage`'s content — `T05`/`T06`.

---

## Context / Notes

This is the one drill-down page this story ships with genuinely no
populated-state code — do not add one speculatively.

---

## Implementation Log

Implemented exactly as specified — `fetchMyDayTodo` added to
`features/my-day/client.ts`, `MyDayTodoPage.tsx`'s real body replacing
`T04`'s placeholder. No populated-state branch, field set, or mock data of
any kind added.

**[REQ-SB-12-US-02-AC-08] — PASS.** Loaded `/my-day/todo` against the real
backend. `.empty-state` rendered with "No tasks captured yet." / "To-Do
Capture (REQ-SB-09) has not been built yet." — the page's only state, as
designed (`GET /my-day/todo` always returns `[]`).

**Non-AC smoke check — PASS.** Zero console errors/exceptions on load.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired.
