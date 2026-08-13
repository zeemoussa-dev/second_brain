---
id: REQ-SB-22-US-01
title: My Day drill-downs and dashboard counts scoped to a rolling 7-day window
requirement_ids: [REQ-SB-22]
requirement_section: "REQ-SB-22: My Day Rolling 7-Day Window"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-013"
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-22-US-01 — My Day drill-downs and dashboard counts scoped to a rolling 7-day window

## Story

**As a** Second Brain user
**I want** My Day's Emails, Calendar, and To-Do drill-downs (and the dashboard's
own counts) to show items from 3 days before today through 3 days after
today, and to keep advancing automatically as days pass
**So that** I can see what just happened and what's coming up without
leaving the dashboard, instead of either only today or an unbounded
all-time list

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-22: My Day Rolling 7-Day Window* —
  "My Day's Emails, Calendar, and To-Do views (REQ-SB-12) show a 7-day
  rolling window — 3 days in the past, today, and 3 days in the future —
  instead of only 'today'." Acceptance: "My Day's Emails, Calendar, and
  To-Do drill-downs show items spanning 3 days before today through 3 days
  after today, not only today; the window advances automatically as days
  pass, with no manual step required."
- **PRD breadcrumb (2026-08-11, operator-directed):** two questions
  explicitly left to `/spec`: (1) exact per-section presentation (a single
  combined list spanning all 7 days? grouped by day? a day-by-day
  navigator?), and (2) how "today" is anchored (the app's local clock,
  presumably). Both resolved below, by direct code inspection and
  precedent, not guessed.
- **Follow-on to the already-`Done` `REQ-SB-12-US-02`, not a rebuild** — this
  story extends that story's already-shipped `app/business/my_day.py`,
  `app/api/my_day_router.py`, and the `MyDayPage`/`MyDayEmailsPage`/
  `MyDayCalendarPage`/`MyDayTodoPage` frontend pages.
- **A real finding, not an assumption: today's actual code does not filter
  by date at all** — read directly (`src/backend/app/business/my_day.py`,
  `src/backend/app/data_access/vault_writer.py::list_notes_in_kind_folder`)
  before writing this story. `list_email_items()`/`list_calendar_items()`
  return **every** note ever written under `Work/Emails/`/`Work/Meetings/`,
  unfiltered by date — there is no "only today" behaviour in the code today
  despite the PRD's framing. This story is therefore not "widening an
  existing window" — it is **adding date-range filtering for the first
  time**, narrowing from "everything, forever" down to the 7-day window.
  This is a materially different (and larger) change than the PRD text's
  own phrasing implies, and is called out here for visibility, not silently
  absorbed.
- **Presentation choice, resolved by precedent (not guessed):** kept as a
  **single flat, item-list per drill-down page** — the same
  `.item-list`/`.item-row` pattern `my-day-emails.html`/
  `my-day-calendar.html` already use (approved, `REQ-SB-12-US-02`) — rather
  than introducing a grouped-by-day layout or a day-by-day navigator.
  Reasoning: the three options are not equally valid from a scope
  standpoint — a flat list needs **zero new screen regions or components**
  (it is the already-approved, already-`Done` pattern, just backed by a
  narrower query and one added per-item date field), while grouped-by-day
  and a day navigator would both be genuinely new UI with no design
  authority anywhere in `html-prototype/`. Per the analyst's own
  prototype-reconciliation rule, choosing either of those would trigger
  `net-new-design-needed`; choosing the flat-list extension avoids that
  trigger entirely while still satisfying the literal acceptance text
  ("show items spanning 3 days before... through 3 days after"). Since
  each item now potentially comes from a different day, each item row must
  show its own date (Calendar already does via `start`; Emails currently
  does **not** show any date at all — see Constraints).
- **"Today" anchoring, resolved by the breadcrumb's own stated
  presumption:** the app's local (server host) clock — the same host that
  already runs the hourly/app-start capture scheduler and every other
  date-adjacent value in this codebase (e.g. `received[:10]` slicing in
  `email_classification.py`). Exact timezone-handling mechanics (e.g.
  whether "day" boundaries use naive local time or a stored offset) are an
  implementation detail left to `/plan-tasks`, not decided here — this
  story only requires that "today" tracks the host's current calendar
  date, recalculated on every request (never a value computed once and
  cached).

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Emails drill-down shows only items within the 7-day window

```gherkin
Given captured emails exist with a `received` date inside the 7-day window
    (3 days before today through today) and other captured emails exist
    with a `received` date more than 3 days before today
When the user views the Emails drill-down page
Then only the emails received within the window are listed
  And each listed email shows the date it was received
```
<!-- AC-ID: REQ-SB-22-US-01-AC-01 -->

### Scenario 2: Calendar drill-down shows only items within the 7-day window, including future meetings

```gherkin
Given captured meetings exist with a `start` date inside the 7-day window
    (3 days before today through 3 days after today) and other captured
    meetings exist with a `start` date more than 3 days before or after
    today
When the user views the Calendar drill-down page
Then only the meetings starting within the window are listed
  And each listed meeting shows its own date/time, as it already does today
```
<!-- AC-ID: REQ-SB-22-US-01-AC-02 -->

### Scenario 3: Items outside the window are excluded, not just visually de-emphasized

```gherkin
Given a captured email or meeting exists whose date falls more than 3 days
    before today, or more than 3 days after today
When the user views that item's drill-down page
Then the item does not appear in the list at all — not shown de-emphasized,
    not hidden behind a toggle, simply absent from the returned list
```
<!-- AC-ID: REQ-SB-22-US-01-AC-03 -->

### Scenario 4: The window advances automatically as days pass

```gherkin
Given the user viewed a My Day drill-down page on one day
When a later day arrives and the user views the same drill-down page again,
    with no action taken to change or refresh any date setting
Then the window has shifted forward to be centered on the new current day,
    with no manual step required
```
<!-- AC-ID: REQ-SB-22-US-01-AC-04 -->

### Scenario 5: My Day dashboard's section counts reflect only items within the window

```gherkin
Given some captured emails or meetings fall within the 7-day window and
    others fall outside it
When the user views the My Day dashboard
Then each section's count reflects only the items within the window, not
    the all-time total
```
<!-- AC-ID: REQ-SB-22-US-01-AC-05 -->

### Scenario 6: Empty state when nothing falls within the window

```gherkin
Given no captured emails (or meetings) have a date within the 7-day window
    — whether because nothing has ever been captured, or because
    everything captured falls outside the window
When the user views that drill-down page
Then the existing empty-state message is shown, as it is today
```
<!-- AC-ID: REQ-SB-22-US-01-AC-06 -->

## Affected Screens

- `html-prototype/my-day.html` — no structural change; section counts now
  reflect the windowed count instead of all-time (data-only change).
- `html-prototype/my-day-emails.html` — same `.item-list`/`.item-row`
  pattern, narrowed to the window; each row gains a visible date (not shown
  today).
- `html-prototype/my-day-calendar.html` — same pattern, narrowed to the
  window; already shows a date per row (`start`), unchanged visually.
- `html-prototype/my-day-todo.html` — unchanged in this story (still
  empty-state-only, per `REQ-SB-12-US-02`'s own deferral — see Non-Goals).

## Dependencies

- **Blocked by:** `REQ-SB-12-US-02` (`Done`) — this story extends its
  already-shipped `my_day.py`/`my_day_router.py`/drill-down pages; not a
  rebuild.
- **Related to:** `REQ-SB-07` (`Done`) — backs the Emails window.
- **Related to:** `REQ-SB-08` (`Done`) — backs the Calendar window,
  including future meetings.
- **Related to:** `REQ-SB-09` (To-Do Task Capture Pipeline, not yet
  specced) — the To-Do drill-down's windowing logic has no observable
  effect until a real task source exists (see Non-Goals); not built or
  decided here.
- **External:** none beyond the shared backend/frontend scaffold.

## Constraints

- **Emails currently carry no visible date in the My Day UI at all** —
  `my_day.list_email_items()` returns `{"subject", "sender", "customer"}`
  only, even though the underlying note's `received` frontmatter field
  already exists (written by `email_classification.py`). This story must
  add the date to what's returned and displayed — not invent a new data
  source, just surface an already-captured field.
- **No date-filtering mechanism exists anywhere in `my_day.py` today** —
  `list_notes_in_kind_folder()` returns every note in a kind folder
  unfiltered; this story is the first to add date-range filtering to My
  Day's read path. Exact filtering mechanism (in `business/my_day.py`,
  reading each note's date field and comparing to a computed window) is
  left to `/plan-tasks`.
- "Today" is the app/server host's current local calendar date, recomputed
  on every request — never a cached or client-supplied value (see Context).
- Presentation stays a flat item-list per drill-down page (see Context) —
  do not introduce a grouped-by-day layout or a day navigator; that would
  require new, currently-unapproved UI.
- To-Do's drill-down keeps its existing empty-state-only behaviour
  (`REQ-SB-12-US-02`'s own deferral, pending `REQ-SB-09`) — this story does
  not add a populated To-Do state or invent a task-date field.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-22-US-01-T01 | backend | Backend query-time 7-day window filtering + `received` field | `app/business/my_day.py` | `../Tasks/REQ-SB-22-US-01-T01-backend-rolling-window-filtering.md` |
| REQ-SB-22-US-01-T02 | frontend | Emails/Calendar drill-downs + dashboard consume the windowed response; Emails row gains a visible `received` date | `features/my-day/client.ts`, `pages/MyDayEmailsPage.tsx` | `../Tasks/REQ-SB-22-US-01-T02-drilldowns-consume-windowed-response.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — n/a, manual-mode verification still the live default
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Grouped-by-day layout or a day-by-day navigator** — explicitly rejected
  presentation options for this pass (see Context); a flat list is used
  instead, avoiding any new-design trigger.
- **To-Do's populated-state field set and its own date semantics** — still
  blocked on `REQ-SB-09`'s unresolved task source, exactly as
  `REQ-SB-12-US-02` already deferred; this story does not pre-empt that.
- **A user-configurable window size** — the window is fixed at 3 days
  before/after today, per the PRD's literal acceptance text; no settings
  control is added to change it.
- **Historical browsing beyond the 7-day window** (e.g. "view last week")
  — not requested by REQ-SB-22; out of scope.
- **Timezone-aware "today" computation beyond the host's own local clock**
  — e.g. per-user timezone preference — not requested; this is a
  single-user, single-host app.

## Notes

**Prototype parity (my-day.html + its drill-down pages):**

- Dashboard section counts — **Specced** (Scenario 5) — data-only change
  (windowed count instead of all-time), no new screen region.
- Emails drill-down populated list — **Specced** (Scenario 1) — reuses the
  approved `.item-list`/`.item-row` pattern, adds one visible date field to
  each row (not a new region, an addition within the existing row's
  metadata line, same as Calendar already does for `start`).
- Calendar drill-down populated list — **Specced** (Scenario 2) — reuses
  the approved pattern unchanged visually; only the underlying query
  narrows.
- Both drill-downs' empty state — **Specced** (Scenario 6) — reuses the
  existing empty-state copy/markup as-is; no new copy authored here (the
  existing "No emails/meetings captured yet" message stays accurate enough
  for a personal single-user app — a more precise "nothing in the last/next
  3 days" distinction was considered and deliberately not added, to avoid
  a copy change needing its own prototype sign-off for a nuance with low
  practical value here).
- To-Do drill-down — **Deferred**, unchanged from `REQ-SB-12-US-02`'s own
  deferral (see Non-Goals).
- Grouped-by-day / day-navigator presentations — **Superseded** (this
  story's own resolution, see Context) — a flat list is used instead;
  these presentations are not built and would need their own future
  `/design` pass if ever wanted.

**Resolution record (2026-08-11, analyst):** both of the PRD breadcrumb's
"left to /spec" open questions (presentation shape; "today" anchoring) are
resolved directly above, grounded in (a) direct inspection of the current
code — confirming no date filtering exists at all today, which is itself a
material finding worth flagging even though it didn't block this story —
and (b) the breadcrumb's own stated presumption for "today." Neither
resolution required guessing among genuinely equally-valid options: the
flat-list presentation is the only one requiring zero new UI, and "the
app's local clock" is the breadcrumb's own suggested answer, not invented
here. No `ESCALATIONS.md` entry needed — no PRD contradiction, no
out-of-scope event.

`gate: clear` 2026-08-11 — no MUST-FLAG trigger fired: REQ-SB-22 is
finalized text in the PRD (no `<!-- Draft -->` marker); both breadcrumb
questions were resolved by precedent/direct code inspection, not a guess
among equally-valid options; no new UI region is introduced (no
`net-new-design-needed`); not oversized (one coherent extension of an
already-`Done` story's read path); no contradictory inputs; no
`ESCALATIONS.md` entry written. Ready for `/plan-tasks`.

---

**Architect pass (2026-08-11, `/plan-tasks` step 1):**

Confirmed by direct code reading (`app/business/my_day.py`,
`app/api/my_day_router.py`, `app/data_access/vault_writer.py`,
`MyDayEmailsPage.tsx`/`MyDayCalendarPage.tsx`/`MyDayPage.tsx`/
`features/my-day/client.ts`) that the story's own findings are accurate:
`list_email_items()`/`list_calendar_items()` return every note under their
kind folder, completely unfiltered by date, today.

- **Filtering mechanism:** backend, query-time, inside
  `app/business/my_day.py` — not a frontend filter over an already-fetched
  full list. The unfiltered list only grows; pushing it all to the browser
  and filtering client-side would duplicate the window logic on both sides
  of the HTTP boundary for no benefit.
- **Presentation:** confirmed buildable as a straightforward, additive
  extension of `MyDayEmailsPage.tsx`/`MyDayCalendarPage.tsx` — no new
  component/region. One real complication, already called out in this
  story's own Constraints: `list_email_items()`/`GET /my-day/emails` must
  gain a `received` field (Emails currently return none), so
  `MyDayEmailItem` and its row rendering both need that one additive field;
  Calendar already renders `start` and needs no equivalent change.
- **"Today" anchoring:** backend, `datetime.now()` (naive local host
  clock, no timezone library), recomputed on every request — never cached,
  never client-supplied. Both drill-down pages already re-fetch on every
  mount (`useEffect([])`), so a plain page revisit already re-derives
  "today," satisfying Scenario 4 with no new polling/refresh mechanism.
  Date-field comparison uses the existing `received[:10]`/`start[:10]`
  ISO-date-string-slice precedent (`email_classification.py`,
  `vault_writer.meeting_note_filename_stem`) — no new timezone-conversion
  logic introduced.
- **ADR:** none needed. This is a query-time filter added inside an
  already-`Accepted` `business/` module, behind the already-`Accepted`
  `api → business → data_access` layering (ADR-003) — no new tool,
  framework, storage mechanism, endpoint contract shape (additive field +
  narrower result set only), or trust-surface decision. Nothing here
  contradicts any `Accepted` ADR, the PRD, or a `MEMORY.md` constraint.
  `gate` stays `clear` — no MUST-FLAG trigger fired on this pass either.

Full detail recorded in `architecture.md` → "My Day & Agent Panel APIs" →
"Amendment — rolling 7-day window date-filtering (REQ-SB-22-US-01)".

---

**Decomposer pass (2026-08-11, `/plan-tasks` step 2):**

Locked all 6 of the analyst's untagged Gherkin scenarios as-is (only
backtick-quoting `received`/`start` field names and slightly sharpening
Scenario 3's exclusion wording for buildability — no scope change):
`REQ-SB-22-US-01-AC-01` through `-AC-06`. No structural ACs added beyond
what `REQ-SB-12-US-02` already locked — this story is a data-only
narrowing of an already-approved `.item-list`/`.item-row` pattern, no new
screen region or interactive affordance is introduced (confirmed against
the architect's own note and `Non-Goals`).

Decomposed into 2 tasks, matching the architect's own filtering-mechanism
note (backend query-time filtering entirely inside `my_day.py`; the
router's endpoint signatures are unchanged so no router task is needed):

- `REQ-SB-22-US-01-T01` (backend, `app/business/my_day.py` only) —
  computes the 3-day-before/3-day-after window fresh on every call
  (`datetime.now()`, never cached), string-compares each note's
  `received[:10]`/`start[:10]` against the window bounds, and adds the
  `received` field to `list_email_items()`'s projection. Holds
  `AC-03` (exclusion is real, not cosmetic — verified by cross-checking
  the filtered result against the full unfiltered note set read directly)
  and `AC-04` (window advances automatically — verified by temporarily
  monkeypatching the module's `datetime` reference in a live Python shell
  to simulate a later "today," mirroring the project's established
  temporary-stub-and-revert verification technique, extended server-side
  since no real day can be waited out during verification).
- `REQ-SB-22-US-01-T02` (frontend, `client.ts` + `MyDayEmailsPage.tsx`) —
  `MyDayEmailItem` gains `received: string`, rendered in the existing
  `.item-row-meta` line. Holds `AC-01`, `AC-02`, `AC-05`, `AC-06`.
  `MyDayCalendarPage.tsx` needs no code change (it already renders `start`
  per row) but is exercised live in this task's own verification pass as
  an unmodified consumer of the now-windowed `/my-day/calendar` response —
  `AC-02`'s Calendar-drill-down scenario and half of `AC-03`/`AC-06` are
  observed there without any file edit. `MyDayPage.tsx` (dashboard) is
  likewise unedited but loaded live to verify `AC-05`'s windowed counts,
  per the architect's own note that dashboard counts change only via the
  already-windowed `summary()` call.

`depends_on`: `T02` depends on `T01` (frontend renders what the backend
now returns; `T01` has no task-level dependency — its own story-level
`Blocked by REQ-SB-12-US-02` is already `Done`). Acyclic, 2 nodes.

Every locked AC has at least one tagged verification step across `T01`/
`T02` (checked: AC-01 T02, AC-02 T02, AC-03 T01, AC-04 T01, AC-05 T02,
AC-06 T02). `depends_on` is acyclic. Story and both tasks advance
`Draft → Ready`.

`gate: clear` 2026-08-11 — no MUST-FLAG trigger fired: no material
assumption was needed (the architect's own pass already resolved the
filtering mechanism, field shape, and "today" source); REQ-SB-22 is
finalized PRD text; no ADR was created or changed this pass (architect
confirmed none needed); no `ESCALATIONS.md` entry; the 2-task split is not
oversized (each is a single-file, single-session change); both locked ACs
requiring creative verification (AC-03, AC-04) have a genuine observable
outcome, not an unverifiable assertion; no contradictory inputs; the task
split was not one of multiple equally-valid options — the architect's own
note ("filtering... inside `app/business/my_day.py`... router's
endpoint contract shape unchanged") already determined which files need a
task, leaving no genuine judgement call about task boundaries.

**Architecture scope: §My Day & Agent Panel APIs → My Day dashboard &
drill-downs (REQ-SB-12-US-02) → Amendment — rolling 7-day window
date-filtering (REQ-SB-22-US-01)** — bounds the decomposer/coder to:
`src/backend/app/business/my_day.py`, `src/backend/app/api/
my_day_router.py`, `src/backend/app/data_access/vault_writer.py` (read-only
access to existing `received`/`start` frontmatter, no new primitive
required), `src/frontend/src/features/my-day/client.ts`, `src/frontend/src/
pages/MyDayEmailsPage.tsx`, `src/frontend/src/pages/MyDayCalendarPage.tsx`.
`MyDayPage.tsx`/`MyDayTodoPage.tsx` are out of this scope (dashboard counts
change only via the shared `summary()` call already routed through the
windowed lists; To-Do stays hardcoded `[]` per this story's own Non-Goals).

---

**Coder pass (`/implement-sprint`), 2026-08-11.** Both tasks built and
verified live end-to-end against the real vault (179 real Email notes, 39
real Meeting notes): `T01` (`app/business/my_day.py` — `_compute_window()`/
`_within_window()` helpers, windowed `list_email_items()`/
`list_calendar_items()`, `received` field added) and `T02`
(`features/my-day/client.ts` + `MyDayEmailsPage.tsx` — `MyDayEmailItem`
gains `received`, rendered per row). All 6 locked ACs verified live —
`AC-03`/`AC-04` via direct backend-level manipulation (real out-of-window
notes confirmed absent; a monkeypatched later "today," reverted exactly,
confirmed the window recomputes on every call); `AC-01`/`AC-02`/`AC-05`/
`AC-06` via a real browser (headless-Chrome CDP) against the real, now
`:8002`-hosted backend and `:5174`-hosted frontend. `npm run build` clean.
Zero blocked tasks, zero `ESCALATIONS.md` entries. Story `status: Ready ->
Done`. Full detail in each task's own `## Implementation Log`.
