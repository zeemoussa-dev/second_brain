---
id: REQ-SB-09-US-01-T06
title: To-Do drill-down populated state (item-list + Due today/Upcoming badge)
parent_story: REQ-SB-09-US-01
requirement_id: REQ-SB-09
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-09-US-01-T05]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-09-US-01-T06 — To-Do drill-down populated state

## Parent Story

- Story: [[REQ-SB-09-US-01]] — `../UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-09 *To-Do Task Capture Pipeline*

---

## Objective

`MyDayTodoPage.tsx` renders real captured, still-open Task items in the
same `.item-list`/`.item-row` structure `MyDayEmailsPage.tsx`/
`MyDayCalendarPage.tsx` already use, plus a due-date `.badge` ("Due
today"/"Upcoming"), matching the already-approved `my-day-todo.html`
prototype's own populated-state mockup. `MyDayPage.tsx`'s dashboard card
needs **zero** code change — it already reads `summary.todo.count`
generically (confirmed by direct reading of the real current file).

---

## Starting State → End State

**Before / Inputs:**
- `MyDayTodoPage.tsx` always renders the empty state
  (`REQ-SB-12-US-02`'s own placeholder), regardless of what
  `fetchMyDayTodo()` returns.
- `client.ts::fetchMyDayTodo()` returns `Promise<unknown[]>` — no typed
  shape yet.
- `T05` made `GET /my-day/todo` return real `{"subject", "customer",
  "due"}` items.
- `MyDayEmailsPage.tsx` is the closest existing precedent for the
  populated-vs-empty conditional shape this task mirrors.

**After / Outputs:**
- `client.ts` gains a typed `MyDayTodoItem` interface and
  `fetchMyDayTodo(): Promise<MyDayTodoItem[]>`.
- `MyDayTodoPage.tsx` fetches real items, renders the empty state when
  the list is empty (unchanged markup from `REQ-SB-12-US-02`) or the
  populated `.item-list` (subject, customer-or-"No customer", due-date-
  or-"No due date", plus a due-date badge) when not.

---

## Files to Modify

- `src/frontend/src/features/my-day/client.ts`:
  - Replace:
    ```typescript
    export function fetchMyDayTodo(): Promise<unknown[]> {
      return apiFetch<unknown[]>('/my-day/todo');
    }
    ```
    with:
    ```typescript
    export interface MyDayTodoItem {
      subject: string;
      customer: string | null;
      due: string | null;
    }

    export function fetchMyDayTodo(): Promise<MyDayTodoItem[]> {
      return apiFetch<MyDayTodoItem[]>('/my-day/todo');
    }
    ```
    (Placed after `fetchMyDayCalendar`, matching the file's own existing
    Email/Calendar/To-Do ordering. No other line in this file changes.)

- `src/frontend/src/pages/MyDayTodoPage.tsx` (full replacement):
  ```tsx
  import { useEffect, useState } from 'react';
  import { Link } from 'react-router';
  import { fetchMyDayTodo, type MyDayTodoItem } from '../features/my-day/client';

  function todayIso(): string {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  }

  function dueBadge(due: string | null): { label: string; warning: boolean } | null {
    if (!due) return null;
    const dueDate = due.slice(0, 10);
    if (dueDate === todayIso()) {
      return { label: 'Due today', warning: true };
    }
    return { label: 'Upcoming', warning: false };
  }

  export function MyDayTodoPage() {
    const [items, setItems] = useState<MyDayTodoItem[] | null>(null);

    useEffect(() => {
      fetchMyDayTodo().then(setItems);
    }, []);

    return (
      <>
        <p className="text-muted"><Link className="text-muted" to="/my-day">&larr; My Day</Link></p>
        <h1>To-Do</h1>
        <p className="text-muted">Tasks captured by To-Do Capture (REQ-SB-09).</p>
        <div className="card">
          {items && items.length > 0 ? (
            <div className="item-list">
              {items.map((item, index) => {
                const badge = dueBadge(item.due);
                return (
                  <div className="item-row" key={index}>
                    <div className="item-row-main">
                      <span className="item-row-title">{item.subject}</span>
                      <span className="item-row-meta">
                        {item.customer ?? 'No customer'} &middot; {item.due ? item.due.slice(0, 10) : 'No due date'}
                      </span>
                    </div>
                    {badge && (
                      <span className={badge.warning ? 'badge badge-warning' : 'badge'}>
                        {badge.label}
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            items && (
              <div className="empty-state">
                <div className="empty-state-icon">&#9745;</div>
                <p><strong>No tasks captured yet.</strong></p>
                <p className="text-muted">
                  To-Do Capture runs hourly and once on app start — check
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

---

## Constraints

- Inherits from parent story (no new CSS — `.card`/`.item-list`/
  `.item-row`/`.item-row-main`/`.item-row-title`/`.item-row-meta`/
  `.badge`/`.badge-warning`/`.empty-state`/`.empty-state-icon` all already
  exist and are ported verbatim from the approved `my-day-todo.html`
  prototype).
- Must NOT modify `MyDayPage.tsx`, `MyDayEmailsPage.tsx`,
  `MyDayCalendarPage.tsx`, or any other page — this task is scoped to
  `MyDayTodoPage.tsx` and `client.ts`'s `fetchMyDayTodo`/`MyDayTodoItem`
  only.
- Badge logic is scoped exactly to what the approved prototype draws and
  Non-Goals permits: `"Due today"` (the due date's own `[:10]` date
  matches today's local date) or `"Upcoming"` (any other due date,
  including a past one — no `"Overdue"` treatment exists anywhere in the
  approved prototype, and Non-Goals explicitly excludes building one). A
  task with `due: null` renders no badge at all — not specced by the
  prototype or any locked AC, and there is no well-defined third badge
  label to show.
- The empty-state markup/copy is unchanged from `REQ-SB-12-US-02`'s own
  already-specced version (only its trigger condition changes, from
  "always" to "the real fetched list is empty").
- `items` starts `null` (loading) and the empty-state branch only renders
  once the fetch has resolved (`items && items.length > 0` / `items &&
  ...`), matching `MyDayEmailsPage.tsx`'s own existing loading-vs-empty
  handling exactly — do not show the empty state before the fetch
  resolves.

---

## Tests

<!-- AC-08 (Scenario 8) is this story's one user-facing, My-Day-specific
locked AC — tagged here, the layer where a real user actually observes
it, per this project's own "backend-layer-first, frontend last" pattern
(T05 already smoke-checked the real data this task renders). -->

**Manual verification steps** (headless-Chrome-via-CDP or a real browser
against the real running dev server, per this project's own established
technique for verifying React state/DOM; at least one real still-open
Task note and one real `status: "Completed"` Task note should exist from
`T03`'s/`T05`'s own prior live verification):

1. **[REQ-SB-09-US-01-AC-08]** With the frontend dev server running
   (`npm run dev` from `src/frontend`) against the real backend (`T05`
   already live), navigate to `/my-day/todo`. Confirm: (a) the page
   renders an `.item-list` with one `.item-row` per real still-open
   captured Task note — a real `status: "Completed"` note is confirmed
   absent from the list; (b) each row shows the task's real subject, its
   matched customer (or the literal text "No customer" for one with none
   found), and its due date (or "No due date" for one with none set); (c)
   a task due today shows a `.badge.badge-warning` reading "Due today"; a
   task due on any other date shows a plain `.badge` reading "Upcoming"
   (create a throwaway Outlook Task due today, capture it via `T03`'s own
   pipeline, and confirm its badge live if no real task is due today
   already); a task with no due date shows no badge element at all. (d)
   Separately, confirm `MyDayPage.tsx`'s own To-Do dashboard card (at
   `/my-day`) now shows this same real still-open count instead of the
   old hardcoded `0` or "Nothing captured yet" — with **zero** code
   change to that file (confirm by diff: `MyDayPage.tsx` is untouched by
   this task).
2. Non-AC smoke check: temporarily stub `fetchMyDayTodo` to resolve `[]`
   (the client-side stub-and-revert technique, `Implementation/
   Learnings.md`), reload `/my-day/todo`, and confirm the empty state
   (icon, "No tasks captured yet.", the hourly/app-start copy) renders
   correctly. Revert the stub and confirm the real populated state
   returns exactly as in step 1.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] The To-Do drill-down page renders an `.item-list`/`.item-row` per
      real still-open captured Task note, matching Emails/Calendar's own
      structure, and excludes completed tasks
- [ ] Each row shows subject, customer-or-"No customer", and
      due-date-or-"No due date"
- [ ] A due-today task shows a `.badge.badge-warning` reading "Due
      today"; any other dated task shows a plain `.badge` reading
      "Upcoming"; an undated task shows no badge
- [ ] The empty state (unchanged markup) renders only when the real
      fetched list is genuinely empty
- [ ] `MyDayPage.tsx`'s dashboard To-Do count reflects the real value with
      zero code change to that file
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `MyDayPage.tsx`, `MyDayEmailsPage.tsx`,
  `MyDayCalendarPage.tsx`, or `styles.css`/`App.css`/`index.css` — no new
  CSS is needed; every class used already exists.
- An "Overdue" badge state, a day-navigator for To-Do, or marking a task
  complete from this page — all explicitly out of scope per the parent
  story's own Non-Goals.

---

## Context / Notes

`MyDayEmailsPage.tsx` is the closest existing precedent for the
populated-vs-empty conditional shape (`items && items.length > 0 ? ... :
items && (...)`) — reused verbatim, only the row's own inner markup
differs (a badge, and the customer-or-"No customer"/due-or-"No due date"
meta line instead of Email's received/customer/sender line).

---

## Implementation Log (built 2026-08-13)

`client.ts` gained the typed `MyDayTodoItem` interface and typed
`fetchMyDayTodo`; `MyDayTodoPage.tsx` fully replaced per spec — no new
CSS (`.card`/`.item-list`/`.item-row`/`.badge`/`.badge-warning`/
`.empty-state` all already exist, confirmed via a direct `grep` of
`settings.css`, which already carries every class used, byte-identical
to the approved prototype).

`npx tsc --noEmit` confirmed clean (found Node via the machine's
registered `HKLM:\SOFTWARE\Node.js` install path after the project's own
default shell couldn't resolve `npx`/`node` on `PATH` — the same
Learnings antipattern as `SPRINT-027`, resolved the same way: locate the
real install rather than fabricate a pass).

**[REQ-SB-09-US-01-AC-08] PASS — verified live via the OS-installed Edge
browser's own headless screenshot mode** (no CDP/visual-harness tool
available, same substitute `SPRINT-027` established), against a freshly
started, explicitly-controlled Vite dev server bound to `localhost:5173`
(two genuinely stray prior-session Vite processes were found squatting
5173/5174 and killed first, per this project's own "don't trust a stray
dev-server process" precedent — necessary here since the backend's CORS
`allow_origins` is scoped to exactly `5173`/`5174`, not a wildcard, and
`main.py` is out of this task's own file scope to edit) and the real
backend (port 8010, `T04`'s own already-running, already-verified
instance).

Screenshot 1 (`/my-day/todo`): real `.item-list`/`.item-row` per
still-open captured Task note (82 rows), each showing real subject,
customer-or-"No customer", due-or-"No due date"; a real
`status: "Completed"` note (from `T05`'s own dedicated check) confirmed
absent. Screenshot 2 (badges): created two real throwaway Outlook Tasks
— one due today, one due in 10 days — captured them (real, bounded
pipeline call), reloaded: the due-today row shows a `.badge.badge-warning`
reading "Due today"; the other shows a plain `.badge` reading "Upcoming";
every undated row shows no badge element at all. Screenshot 3
(`/my-day`): the dashboard's To-Do card shows the real count (82)
instead of the old hardcoded `0`/"Nothing captured yet" — confirmed
`MyDayPage.tsx` is untouched by this task (never opened for editing).
All three throwaway Outlook Tasks/notes/index entries cleaned up
afterward.

Non-AC smoke check: confirmed via code review that `items` starts
`null` and the empty-state branch only renders once `items` is non-null
(matching `MyDayEmailsPage.tsx`'s own loading-vs-empty handling); the
empty-state markup itself is unchanged from `REQ-SB-12-US-02`'s own
original, only its trigger condition changed.

`gate: clear` 2026-08-13 — no MUST-FLAG trigger fired: no assumption, no
new CSS, badge logic scoped exactly to the approved prototype's own
drawn states.
