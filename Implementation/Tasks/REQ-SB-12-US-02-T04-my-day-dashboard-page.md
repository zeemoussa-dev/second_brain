---
id: REQ-SB-12-US-02-T04
title: My Day dashboard page — three clickable sections with counts, drill-down routing scaffold, my-day.css
parent_story: REQ-SB-12-US-02
requirement_id: REQ-SB-12
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-12-US-02-T03, REQ-SB-12-US-01-T01]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-12-US-02-T04 — My Day dashboard page

## Parent Story

- Story: [[REQ-SB-12-US-02]] — `../UserStories/REQ-SB-12-US-02-my-day-dashboard-and-drilldowns.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-12 *Primary Application UI Shell — Agents Map & My Day*

---

## Objective

Replace `REQ-SB-12-US-01-T01`'s `MyDayPage.tsx` placeholder with the real My
Day dashboard — three clickable `.day-section-card`s (Emails, Calendar,
To-Do) each showing a live count (or an empty indication) fetched from
`T03`'s `/my-day/summary`, plus register the three new drill-down routes
(`/my-day/emails`, `/my-day/calendar`, `/my-day/todo`) as placeholders for
`T05`/`T06`/`T07` to fill in — mirroring `REQ-SB-12-US-01-T01`'s own
placeholder-then-fill convention. Also ports `my-day.css`'s shared
`.day-section-grid`/`.item-list`/`.item-row` classes, reused by all three
drill-down pages.

**Task-level dependency note:** this task literally edits `App.tsx` (built by
`REQ-SB-12-US-01-T01`) and reuses `AppShell`/`Sidebar` — hence the explicit
`depends_on` on that specific task file, not just the story-level
"Blocked by REQ-SB-12-US-01" dependency already recorded in the parent
story's own `## Dependencies`.

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-12-US-01-T01` has landed `App.tsx`'s three routes (`/`, `/my-day`,
  `/settings`) and `pages/MyDayPage.tsx` as a placeholder (`<h1>My Day</h1>`).
- `T03` has landed `GET /my-day/summary` → `{"emails": {"count"},
  "calendar": {"count"}, "todo": {"count": 0}}`.
- `src/frontend/src/api/client.ts` (from `REQ-SB-12-US-01-T01`) exists,
  unused until now.

**After / Outputs:**
- `App.tsx` gains three new routes: `/my-day/emails`, `/my-day/calendar`,
  `/my-day/todo`, each a minimal placeholder page this pass
  (`T05`/`T06`/`T07` replace their bodies).
- `pages/MyDayPage.tsx` renders three `.day-section-card` links (Emails,
  Calendar, To-Do), each showing its count or a "nothing captured yet"
  indication, fetched from `/my-day/summary` via `api/client.ts`.
- `src/frontend/src/features/my-day/client.ts` exists — the `/my-day/*`
  fetch calls.
- `src/frontend/src/styles/my-day.css` exists, ported from
  `html-prototype/styles.css`.

---

## Files to Modify

- `src/frontend/src/App.tsx` — add three new routes inside the existing
  `<Route element={<AppShell />}>` block, alongside the existing `/my-day`
  route:
  ```tsx
  <Route path="/my-day" element={<MyDayPage />} />
  <Route path="/my-day/emails" element={<MyDayEmailsPage />} />
  <Route path="/my-day/calendar" element={<MyDayCalendarPage />} />
  <Route path="/my-day/todo" element={<MyDayTodoPage />} />
  ```
  Add the three new page imports alongside the existing ones. Leave `/`,
  `/settings`, and the `<AppShell>` layout route unchanged.

- `src/frontend/src/pages/MyDayEmailsPage.tsx` (new, placeholder — `T05`
  replaces the body): `export function MyDayEmailsPage() { return
  <h1>Emails</h1>; }`
- `src/frontend/src/pages/MyDayCalendarPage.tsx` (new, placeholder — `T06`
  replaces the body): `export function MyDayCalendarPage() { return
  <h1>Calendar</h1>; }`
- `src/frontend/src/pages/MyDayTodoPage.tsx` (new, placeholder — `T07`
  replaces the body): `export function MyDayTodoPage() { return
  <h1>To-Do</h1>; }`

- `src/frontend/src/features/my-day/client.ts` (new):
  ```ts
  import { apiFetch } from '../../api/client';

  export interface MyDaySummary {
    emails: { count: number };
    calendar: { count: number };
    todo: { count: number };
  }

  export function fetchMyDaySummary(): Promise<MyDaySummary> {
    return apiFetch<MyDaySummary>('/my-day/summary');
  }
  ```
  (`T05`/`T06`/`T07` each add their own `fetchMyDayEmails`/
  `fetchMyDayCalendar`/`fetchMyDayTodo` export to this same file — this task
  only adds `fetchMyDaySummary`.)

- `src/frontend/src/pages/MyDayPage.tsx` — replace the `REQ-SB-12-US-01-T01`
  placeholder body:
  ```tsx
  import { useEffect, useState } from 'react';
  import { Link } from 'react-router';
  import { fetchMyDaySummary, type MyDaySummary } from '../features/my-day/client';

  const SECTIONS = [
    { key: 'emails', label: 'Emails', href: '/my-day/emails' },
    { key: 'calendar', label: 'Calendar', href: '/my-day/calendar' },
    { key: 'todo', label: 'To-Do', href: '/my-day/todo' },
  ] as const;

  export function MyDayPage() {
    const [summary, setSummary] = useState<MyDaySummary | null>(null);

    useEffect(() => {
      fetchMyDaySummary().then(setSummary);
    }, []);

    return (
      <>
        <h1>My Day</h1>
        <p className="text-muted">
          The day's most important actions, surfaced from your background
          agents. Open a section for the full list.
        </p>
        <div className="day-section-grid">
          {SECTIONS.map((section) => {
            const count = summary?.[section.key].count;
            return (
              <Link key={section.key} className="card day-section-card" to={section.href}>
                <h2>{section.label}</h2>
                {count && count > 0 ? (
                  <div className="day-section-count">{count}</div>
                ) : (
                  <span className="text-muted">Nothing captured yet</span>
                )}
              </Link>
            );
          })}
        </div>
      </>
    );
  }
  ```
  (`count && count > 0` reads `undefined` — before the fetch resolves — the
  same as "nothing captured yet"; a brief empty-state flash before real data
  arrives is acceptable, no loading-spinner state was requested by any
  locked AC.)

- `src/frontend/src/styles/my-day.css` (new) — port verbatim from
  `html-prototype/styles.css`: `.day-section-grid`/`.day-section-card`/
  `.day-section-count`, plus `.item-list`/`.item-row`/`.item-row-main`/
  `.item-row-title`/`.item-row-meta` (the shared list pattern `T05`/`T06`/
  `T07` reuse). `.empty-state`/`.card`/`.badge` are already in
  `settings.css` (`REQ-SB-12-US-01-T01`) — do not duplicate them here.

- `src/frontend/src/main.tsx` — add `import './styles/my-day.css';`
  alongside the existing style imports.

---

## Constraints

- Inherits from parent story: ADR-010's routing (declarative `react-router`
  only)/styling (plain global CSS, prototype class names verbatim)/
  data-fetching (`api/client.ts` convention) conventions.
- Must not modify `REQ-SB-12-US-01-T01`'s `AppShell`/`Sidebar`, or the
  existing `/`, `/settings` routes.
- No card for "Important Reads" — dropped from this story's scope entirely
  (see the story's own Notes) — exactly three sections.
- No new dependency.

---

## Tests

**Manual verification steps** (from `src/frontend`: `npm run dev`; from
`src/backend`: `uvicorn app.main:app --reload --port 8001` per `MEMORY.md`'s
port-8000 caution; set `VITE_API_BASE_URL=http://127.0.0.1:8001` if the
frontend's dev env doesn't already default there; use the browser preview
tool):

1. **[REQ-SB-12-US-02-AC-01]** Load `/my-day` with the real backend running
   (real vault has captured emails, no `Work/Meetings/` folder). Confirm
   exactly three `.day-section-card` elements render — Emails, Calendar,
   To-Do — no fourth "Important Reads" card. Confirm the Emails card shows a
   numeric `.day-section-count` matching the real captured-email count
   (a count "reflecting how many items it currently has"), and confirm both
   the Calendar and To-Do cards remain clickable `.day-section-card` links
   even while showing "Nothing captured yet" instead of a count — this is
   the same per-section `count === 0` rendering Scenario 2 (below) exercises
   for all three sections at once, per `architecture.md`'s explicit
   "no separate has-a-pipeline-ever-run flag" design note.
2. **[REQ-SB-12-US-02-AC-02]** Temporarily edit `MyDayPage.tsx`'s `summary`
   state seed (or temporarily stub `fetchMyDaySummary` in
   `features/my-day/client.ts` to return `{"emails": {"count": 0},
   "calendar": {"count": 0}, "todo": {"count": 0}}` instead of calling the
   real endpoint) to exercise the genuine all-zero first-run state — the
   real vault already has captured emails, so this state cannot occur
   naturally against live data today; this mirrors
   `REQ-SB-12-US-01-T02`'s own established "temporarily swap in constants,
   verify, revert" technique. Reload `/my-day`. Confirm all three
   `.day-section-card` elements still render and remain clickable, and each
   shows "Nothing captured yet" instead of a count. Revert the temporary
   edit and reload once more to confirm the real populated state (step 1)
   is restored.
3. **[REQ-SB-12-US-02-AC-03]** From `/my-day`, click the Emails card.
   Confirm the URL becomes `/my-day/emails` and the `MyDayEmailsPage`
   placeholder renders. Navigate back to `/my-day` (browser back or the
   sidebar's My Day nav item), then click the Calendar card — confirm the
   URL becomes `/my-day/calendar`. Repeat for the To-Do card — confirm the
   URL becomes `/my-day/todo`.
4. Non-AC smoke check: confirm no console errors/warnings on load or after
   each navigation click.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `MyDayPage.tsx` renders exactly three `.day-section-card` links
      (Emails, Calendar, To-Do), each showing a live count from
      `/my-day/summary` or "Nothing captured yet" when that section's count
      is `0`
- [x] `App.tsx` registers `/my-day/emails`, `/my-day/calendar`,
      `/my-day/todo` routes, each a placeholder page this pass
- [x] `features/my-day/client.ts` exists with `fetchMyDaySummary`
- [x] `my-day.css` ported per the selector groups above and imported once in
      `main.tsx`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `MyDayEmailsPage`/`MyDayCalendarPage`/`MyDayTodoPage`'s real content —
  `T05`/`T06`/`T07`.
- Any "Important Reads" card/page/route — dropped from this story's scope
  entirely (see the story's own Non-Goals).

---

## Context / Notes

`count && count > 0` (rather than `count !== undefined && count > 0`) is a
deliberate simplification since `0` and `undefined` both correctly fall
through to the "nothing captured" branch here — no locked AC distinguishes
"data hasn't loaded yet" from "data loaded and is zero."

---

## Implementation Log

Implemented exactly as specified — three placeholder pages
(`MyDayEmailsPage`/`MyDayCalendarPage`/`MyDayTodoPage`), `App.tsx`'s three
new routes, `features/my-day/client.ts` with `fetchMyDaySummary`,
`MyDayPage.tsx`'s real body, `styles/my-day.css` ported verbatim from
`html-prototype/styles.css`, `main.tsx`'s new import. `App.tsx`/
`MyDayPage.tsx`/`main.tsx` re-read fresh immediately before editing (no
concurrent change from another sprint at that point).

**Verification tooling:** headless Chrome via CDP (Node's built-in
`WebSocket`/`fetch`, zero new dependency), reusing `SPRINT-008`'s
established pattern per `MEMORY.md`/`Learnings.md`. `npm run dev`
(port 5173) + a real backend on port 8002 (see `T03`'s port note).

**[REQ-SB-12-US-02-AC-01] — PASS.** Loaded `/my-day` against the real
backend. Exactly 3 `.day-section-card` elements rendered (Emails,
Calendar, To-Do — no fourth "Important Reads" card). Emails card showed
`.day-section-count` = `178` (real captured-email count). Calendar card
showed `.day-section-count` = `39` — **note:** the task's own step 1
expected Calendar to show "Nothing captured yet" (written when the real
vault had no `Work/Meetings/` folder yet); by the time this task ran,
SPRINT-006 had landed concurrently and the real vault now has 39 real
Meeting notes, so Calendar's real count renders instead. This is a
stronger confirmation of the per-section count-rendering behavior AC-01
requires, not a failure — both the nonzero-count and zero-count render
paths are now exercised by real data across the three cards. To-Do card
showed "Nothing captured yet" and was still a clickable `<a>` link to
`/my-day/todo`, confirming the "clickable even while empty" requirement.

**[REQ-SB-12-US-02-AC-02] — PASS.** Temporarily stubbed
`fetchMyDaySummary` in `features/my-day/client.ts` to return
`{"emails": {"count": 0}, "calendar": {"count": 0}, "todo": {"count": 0}}`
(real vault data cannot naturally produce this state today). Reloaded
`/my-day`: all 3 cards still rendered and remained clickable `<a>`
elements, each showing "Nothing captured yet". Reverted the stub;
reloaded once more — confirmed the real populated state (AC-01's numbers)
was restored exactly.

**[REQ-SB-12-US-02-AC-03] — PASS.** From `/my-day`, clicked the Emails
card: URL became `/my-day/emails`, `MyDayEmailsPage` placeholder heading
rendered. Navigated back, clicked Calendar: URL became `/my-day/calendar`.
Navigated back, clicked To-Do: URL became `/my-day/todo`.

**Non-AC smoke check — PASS.** Zero console errors/exceptions across the
full sequence (initial load, both temporary-stub round trips, all three
navigation clicks).

**Post-verification:** ran `npm run build` (real `tsc -b && vite build`,
not just the dev server, per `Learnings.md`'s standing pattern) — clean
build, zero TypeScript errors, `dist/` produced successfully.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired for this task's own
frontend code (the real-vault-state note above is an observation about
current data, not a code deviation; the CORS gap that had to be fixed for
this task's fetch calls to work at all is logged and flagged on `T03`,
where `main.py` lives).
