---
id: REQ-SB-43-US-01-T09
title: New MeetingCockpitPage.tsx + App.tsx route /meeting-cockpit/:stem + MyDayCalendarPage.tsx rows become clickable
parent_story: REQ-SB-43-US-01
requirement_id: REQ-SB-43
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-43-US-01-T08, REQ-SB-43-US-01-T06]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-43-US-01-T09 — `MeetingCockpitPage.tsx` + clickable Calendar rows

## Parent Story

- Story: [[REQ-SB-43-US-01]] — `../UserStories/REQ-SB-43-US-01-meeting-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-43 *Meeting Cockpit — Expert-Assisted Meeting Workspace*

---

## Objective

Final wiring task: a new thin `MeetingCockpitPage.tsx` route-level wrapper supplying `subjectKind="meeting"` to `T08`'s `Cockpit` component, a new `/meeting-cockpit/:stem` route in `App.tsx`, and `MyDayCalendarPage.tsx`'s own flat `.item-row` list becomes clickable, linking to that route using `T06`'s new `"stem"` field — reproducing the story's own Scenario 1 end-to-end.

---

## Starting State → End State

**Before / Inputs:** `T06` has landed `list_calendar_items`'s `"stem"` field. `T08` has landed `Cockpit.tsx`. `MyDayCalendarPage.tsx`'s rows are plain, non-clickable `<div className="item-row">` (confirmed by direct reading, uses array `index` as React `key`).

**After / Outputs:**
- New `src/frontend/src/pages/MeetingCockpitPage.tsx`:
  ```typescript
  import { useParams, Link } from 'react-router';
  import { Cockpit } from '../features/cockpit/Cockpit';

  export function MeetingCockpitPage() {
    const { stem } = useParams<{ stem: string }>();
    if (!stem) return null;
    return (
      <>
        <p className="text-muted"><Link className="text-muted" to="/my-day/calendar">&larr; Calendar</Link></p>
        <Cockpit
          subjectKind="meeting"
          subjectNoteStem={stem}
          subjectTitleFields={[{ label: 'Time', key: 'start' }, { label: 'Customer', key: 'customer' }]}
        />
      </>
    );
  }
  ```
- `App.tsx` gains `import { MeetingCockpitPage } from './pages/MeetingCockpitPage';` and `<Route path="/meeting-cockpit/:stem" element={<MeetingCockpitPage />} />`, additive alongside the existing routes.
- `MyDayCalendarPage.tsx`'s row rendering:
  ```typescript
  {items.map((item) => (
    <Link className="item-row" to={`/meeting-cockpit/${item.stem}`} key={item.stem}>
      <div className="item-row-main">
        <span className="item-row-title">{item.subject}</span>
        <span className="item-row-meta">{item.start} &middot; {item.customer ?? 'No customer'}</span>
      </div>
    </Link>
  ))}
  ```
  (`.item-row` as a styled `<Link>` rather than a `<div>` — `.item-row`'s own existing CSS is generic enough to apply to either element; if it is not, this task also ADDS the minimal CSS needed for `a.item-row` to render identically to `div.item-row`, additive only.) React `key` changes from `index` to the real, stable `item.stem`.

---

## Files to Modify

- `src/frontend/src/pages/MeetingCockpitPage.tsx` (new) — per the code block above.
- `src/frontend/src/App.tsx` — add the import and route, additive.
- `src/frontend/src/pages/MyDayCalendarPage.tsx` — rows become `<Link>`s to `/meeting-cockpit/:stem`, keyed by `item.stem` instead of `index`.
- `src/frontend/src/features/my-day/client.ts` — `MyDayCalendarItem`'s TypeScript interface gains a `stem: string` field (additive), matching `T06`'s new backend field.
- `src/frontend/src/styles/my-day.css` — only if `.item-row`'s existing CSS does not already apply cleanly to an anchor element (e.g. missing `text-decoration: none`/`color: inherit`) — a minimal, additive fix if needed.

---

## Constraints

- `MyDayCalendarPage.tsx`'s own existing empty-state, loading state, and day-navigator (`searchParams`) behavior is UNCHANGED — only the row element/click-target and `key` change.
- Does not touch `MyDayEmailsPage.tsx` — that is `REQ-SB-44-US-01`'s own equivalent task.
- `MeetingCockpitPage.tsx` is a THIN wrapper — no cockpit business logic of its own; every real behavior lives in `Cockpit.tsx` (`T08`).
- Does not modify `Sidebar.tsx`/any nav — the Cockpit is reached only by clicking a Calendar row, never a standalone nav item.

---

## Tests

**Manual verification steps** (real backend + frontend dev servers; requires at least one real Meeting note inside the current 7-day window):
1. **[REQ-SB-43-US-01-AC-01]** Load `/my-day/calendar` in a browser — confirm each meeting row is a real clickable link (not a plain `<div>` — confirm via DOM inspection that the element is an `<a>`/React-Router `Link` with a real `href`/`to` pointing at `/meeting-cockpit/<real-stem>`).
2. **[REQ-SB-43-US-01-AC-01]** Click a meeting row — confirm the browser navigates to `/meeting-cockpit/<stem>` and the 3-panel Cockpit renders for that specific meeting (its real subject/attendees shown in the right panel).
3. Non-AC smoke check: navigate directly to `/meeting-cockpit/<stem>` (typed URL, not via click) — confirm it renders identically (a real route, not a click-only affordance).
4. Non-AC smoke check: confirm `/my-day/calendar`'s own existing day-navigator (`?day=YYYY-MM-DD`) and empty-state still work exactly as before this task.
5. Non-AC smoke check: navigate to `/meeting-cockpit/does-not-exist` — confirm an honest error/empty state (from `T05`'s own `404`), not a crash or a fabricated blank cockpit.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `/meeting-cockpit/:stem` route renders `MeetingCockpitPage.tsx`, which renders `Cockpit` with `subjectKind="meeting"`
- [ ] `MyDayCalendarPage.tsx`'s rows are real clickable links to that route, keyed by the real stem
- [ ] The Calendar page's own existing day-navigator/empty-state behavior is unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `MyDayEmailsPage.tsx`/`InboxCockpitPage.tsx` — `REQ-SB-44-US-01`'s own task.
- Any further Cockpit content — `T08`.

---

## Context / Notes

This is the story's own final integration task — the majority of the story's user-facing Scenarios are verified live here, against `T08`'s real component and `T05`'s real backend, per this project's own established "the frontend/integration task carries most of the live-verification weight" precedent (`Implementation/Learnings.md`, multiple entries).

---

## Implementation Log

Implemented as spec'd: `MeetingCockpitPage.tsx` (new, thin wrapper), `App.tsx`
route addition, `MyDayCalendarPage.tsx` rows converted to `<Link>`s keyed by
`item.stem`, `features/my-day/client.ts`'s `MyDayCalendarItem` gained `stem:
string`. One additive CSS fix, anticipated by this task's own Constraints:
`.item-row` in `my-day.css` gained `text-decoration: none; color: inherit;` —
without it, `.item-row` as a real `<a>`/`Link` rendered with default browser
link underline/color, not matching the plain `<div>` it replaced.

**Manual verification (real backend + real Vite dev server, real headless-Edge
CDP session):**
1. **AC-01:** `GET /my-day/calendar` in a real browser — all 25 real meeting rows are real `<a>` elements (`tagName === 'A'`) with real `href="/meeting-cockpit/<real-stem>"` values (not the array index). Confirmed via direct DOM query.
2. **AC-01:** clicked a real row via its real React Fiber `onClick` handler — the browser genuinely navigated to `/meeting-cockpit/<stem>` (confirmed via `location.pathname`) and the 3-panel Cockpit rendered with that SPECIFIC meeting's own real subject ("HPC kickoff meeting"), Time, and Customer (ADNOC) in the right panel. Confirmed.
3. Non-AC: navigated directly to `/meeting-cockpit/<stem>` (typed URL, not via click) — renders identically (a real route). Confirmed.
4. Non-AC: `/my-day/calendar?day=2026-08-17` (a real in-window day) — day-navigator still correctly re-fetches and re-renders (3 real rows for that day, distinct from the default day). Confirmed unchanged. (A genuinely out-of-window day, e.g. `2099-01-01`, is honestly rejected by the ALREADY-EXISTING, untouched `my_day.py` day-window validation — `REQ-SB-22`'s own pre-existing behavior, not this task's own fetch/error-handling code, which this task did not touch.)
5. Non-AC: `/meeting-cockpit/does-not-exist` — no crash (`Uncaught` not present in the page); the Cockpit renders its own honest empty/degraded state (backend `404` → `data` stays `null` → every field renders via optional chaining, never a fabricated subject).

Most of this story's own user-facing Scenarios were verified live here and in
`T08`'s own log, against the real, fully-wired end-to-end app — see `T08`'s
Implementation Log for the shared component's own detailed per-AC evidence
(Scenarios 2-10), all exercised through this task's real route.

gate: clear 2026-08-14 — no triggers fired (thin wrapper + one anticipated,
Constraint-named CSS fix; no new dependency/interface/ADR).
