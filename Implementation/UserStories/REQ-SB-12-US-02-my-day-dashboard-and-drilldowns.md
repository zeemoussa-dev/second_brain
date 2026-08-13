---
id: REQ-SB-12-US-02
title: My Day dashboard surfacing Emails, Calendar, and To-Do, each with its own drill-down page
requirement_ids: [REQ-SB-12]
requirement_section: "REQ-SB-12: Primary Application UI Shell — Agents Map & My Day"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: SPRINT-009
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-12-US-02 — My Day dashboard surfacing Emails, Calendar, and To-Do, each with its own drill-down page

## Story

**As a** Second Brain user
**I want** a My Day dashboard, reachable from the app shell, that summarizes
today's most important actions across Emails, Calendar, and To-Do — each a
clickable section leading to its own dedicated page
**So that** I can see what needs my attention today without digging through
the vault myself

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-12: Primary Application UI Shell —
  Agents Map & My Day* — "From this shell the user can also reach 'My Day' —
  a dashboard surfacing the day's most important actions (Emails, Calendar,
  To-Do, Important Reads), each of which is clickable and navigates to its
  own dedicated page." Acceptance (this story's portion): "My Day shows
  Emails, Calendar, To-Do, and Important Reads as separate clickable
  sections, each navigating to its own page." The PRD's own breadcrumb on
  this requirement explicitly states: "My Day's four sections read from
  REQ-SB-07/08/09's capture pipelines and REQ-SB-11's observability data;
  which agent types exist beyond Worker/Producer/Expert, and **each My Day
  drill-down page's exact content, are open questions for /spec time**."
- **This story covers only the My Day portion of REQ-SB-12** — the shell/
  navigation and Agents Map are REQ-SB-12-US-01 (a dependency: this story
  reuses that shell, not rebuilds it). Split rationale: My Day's dashboard +
  its four drill-down pages form one coherent, independently valuable
  feature area of their own (a user can use My Day without the Agents Map
  chat panel existing, and vice versa) — same "no independent value alone"
  split test used for prior stories this session. Within My Day itself, the
  dashboard card grid and its four drill-down pages are **not** further split
  — a dashboard card that links to a page not built yet has no real value,
  and a drill-down page unreachable from the dashboard has no real value
  either; they are one vertical slice, same reasoning `REQ-SB-08-US-01` used
  for its own fetch→classify→write→link pipeline.
- **Design authority:** `html-prototype/` — approved by the operator
  2026-08-11. Reconciled against `html-prototype/my-day.html` (dashboard: 4
  cards, empty/populated states) and its four drill-down pages
  (`my-day-emails.html`, `my-day-calendar.html`, `my-day-todo.html`,
  `my-day-reads.html`), all sharing the `.item-list`/`.item-row` pattern
  first introduced in `my-day-emails.html`.
- **Resolved 2026-08-11, operator-confirmed:** this story originally flagged
  two open product questions rather than guessing through them; both are now
  resolved directly, not invented by the analyst:
  - **Important Reads is dropped from this story's scope entirely** — no PRD
    requirement (not even a not-yet-built one) defines what makes a note an
    "Important Read," and the operator chose not to invent a criterion now.
    My Day ships with three sections (Emails, Calendar, To-Do), not four; a
    future story can add Important Reads back once a real criterion exists.
  - **To-Do ships with an empty-state-only drill-down for now, deliberately
    waiting on REQ-SB-09** rather than defining a placeholder field set —
    REQ-SB-09's own PRD text leaves its task source open ("Outlook tasks,
    agent-created follow-ups, manually flagged emails") and has not been
    specced yet; committing to fields here would have pre-empted that future
    spec pass. This matches what the story already specced (Scenario 8), so
    no scenario changes were needed for this half of the resolution.
  - **Calendar and Emails, by contrast, were already resolvable** — their
    backing schemas are already resolved (REQ-SB-07 `Done`; REQ-SB-08's
    schema is resolved in `Implementation/Plans/
    2026-08-10-vault-taxonomy-draft.md` and `MEMORY.md`'s 2026-08-11
    Decision). This story writes concrete scenarios for those two
    drill-downs. See Non-Goals.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: My Day dashboard shows three clickable sections, each with a count

```gherkin
Given at least one of Email Capture, Meeting Capture, or To-Do Capture has
    produced results
When the user views the My Day page
Then three sections are shown — Emails, Calendar, and To-Do
  And each section shows a count reflecting how many items it currently has
```
<!-- AC-ID: REQ-SB-12-US-02-AC-01 -->

### Scenario 2: First run — nothing captured yet

```gherkin
Given no capture pipeline has produced any results yet
When the user views the My Day page
Then all three sections are still shown and still clickable
  And each shows an indication that nothing has been captured yet, instead of
    a count
```
<!-- AC-ID: REQ-SB-12-US-02-AC-02 -->

### Scenario 3: Clicking a My Day section navigates to its own dedicated page

```gherkin
Given the user is viewing the My Day dashboard
When the user clicks the Emails section
Then the app navigates to the Emails drill-down page
When the user instead clicks the Calendar or To-Do section
Then the app navigates to that section's own dedicated page, respectively
```
<!-- AC-ID: REQ-SB-12-US-02-AC-03 -->

### Scenario 4: Emails drill-down lists captured emails

```gherkin
Given one or more emails have been captured by Email Capture (REQ-SB-07)
When the user views the Emails drill-down page
Then each captured email is listed, showing at least its subject, sender, and
    customer classification (or an indication that it is unclassified)
```
<!-- AC-ID: REQ-SB-12-US-02-AC-04 -->

### Scenario 5: Emails drill-down shows an empty state

```gherkin
Given no emails have been captured yet
When the user views the Emails drill-down page
Then an empty-state message explains that Email Capture has not produced
    anything yet
```
<!-- AC-ID: REQ-SB-12-US-02-AC-05 -->

### Scenario 6: Calendar drill-down lists captured meetings

```gherkin
Given one or more meetings have been captured by Meeting Capture (REQ-SB-08)
When the user views the Calendar drill-down page
Then each captured meeting is listed, showing at least its subject, time, and
    customer classification (or an indication that it is unclassified)
```
<!-- AC-ID: REQ-SB-12-US-02-AC-06 -->

### Scenario 7: Calendar drill-down shows an empty state

```gherkin
Given no meetings have been captured yet (e.g. Meeting Capture has not run,
    or has not yet been built)
When the user views the Calendar drill-down page
Then an empty-state message explains that no meetings have been captured yet
```
<!-- AC-ID: REQ-SB-12-US-02-AC-07 -->

### Scenario 8: To-Do drill-down shows an empty state

```gherkin
Given no tasks have been captured yet (e.g. To-Do Capture has not run, or has
    not yet been built)
When the user views the To-Do drill-down page
Then an empty-state message explains that no tasks have been captured yet
```
<!-- AC-ID: REQ-SB-12-US-02-AC-08 -->
<!-- Populated-state content (which fields, sourced from what) is
deliberately not specced here — see Non-Goals; waiting on REQ-SB-09. -->

## Affected Screens

- `html-prototype/my-day.html` — dashboard: three clickable sections with
  counts (Important Reads card dropped from this story's scope); empty/
  populated states.
- `html-prototype/my-day-emails.html` — populated list + empty state.
- `html-prototype/my-day-calendar.html` — populated list + empty state.
- `html-prototype/my-day-todo.html` — empty state only in this story;
  populated-state field set deferred (see Non-Goals).
- `html-prototype/my-day-reads.html` — **not built** in this story; Important
  Reads is dropped from scope entirely (see Non-Goals).

## Dependencies

- **Blocked by:** REQ-SB-12-US-01 — needs the shared app shell/sidebar
  navigation to be reachable from.
- **Related to:** REQ-SB-07 (`Done`) — backs the Emails drill-down.
- **Related to:** REQ-SB-08 (`REQ-SB-08-US-01`, `Draft`, flagged) — backs the
  Calendar drill-down; this story does not require that story to be `Done`
  (Scenario 7's empty state covers the case where it isn't yet).
- **Related to:** REQ-SB-09 (To-Do Task Capture Pipeline, not yet specced) —
  would back the To-Do drill-down's populated state once its own task source
  is resolved at a future `/spec` pass; not built or decided here.
- **External:** none beyond the shared frontend scaffold.

## Constraints

- Reuses the app shell/navigation built in REQ-SB-12-US-01 — must not
  duplicate shell/nav code.
- Emails drill-down fields are grounded in REQ-SB-07's resolved note schema
  (subject, sender, customer/classification).
- Calendar drill-down fields are grounded in REQ-SB-08's resolved schema
  (subject, start/end time, customer) — the UI must tolerate the pipeline not
  having run yet (Scenario 7's empty state).
- To-Do drill-down: only its empty state is specced here; populated-state
  field set is explicitly deferred (see Non-Goals) pending REQ-SB-09's
  task-source resolution — not invented here.
- Important Reads is out of scope entirely for this story — no card, no
  page, no route (see Non-Goals).
- No backend endpoint currently returns My Day summary/drill-down data — new
  API surface is required; exact shape left to `/plan-tasks`.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-12-US-02-T01 | backend | `list_notes_in_kind_folder(kind)` read primitive | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-12-US-02-T01-list-notes-in-kind-folder-primitive.md` |
| REQ-SB-12-US-02-T02 | backend | My Day read-only aggregation (`summary`/`list_email_items`/`list_calendar_items`) | `app/business/my_day.py` (new) | `../Tasks/REQ-SB-12-US-02-T02-my-day-business-aggregation.md` |
| REQ-SB-12-US-02-T03 | backend | `GET /my-day/summary`, `/emails`, `/calendar`, `/todo` | `app/api/my_day_router.py` (new), `app/main.py` | `../Tasks/REQ-SB-12-US-02-T03-my-day-router.md` |
| REQ-SB-12-US-02-T04 | frontend | My Day dashboard page (3 sections + counts) + drill-down routing scaffold + `my-day.css` | `pages/MyDayPage.tsx`, `App.tsx`, `features/my-day/client.ts`, `styles/my-day.css` | `../Tasks/REQ-SB-12-US-02-T04-my-day-dashboard-page.md` |
| REQ-SB-12-US-02-T05 | frontend | Emails drill-down page (populated + empty) | `pages/MyDayEmailsPage.tsx` | `../Tasks/REQ-SB-12-US-02-T05-emails-drilldown-page.md` |
| REQ-SB-12-US-02-T06 | frontend | Calendar drill-down page (populated + empty) | `pages/MyDayCalendarPage.tsx` | `../Tasks/REQ-SB-12-US-02-T06-calendar-drilldown-page.md` |
| REQ-SB-12-US-02-T07 | frontend | To-Do drill-down page (empty state only) | `pages/MyDayTodoPage.tsx` | `../Tasks/REQ-SB-12-US-02-T07-todo-drilldown-page.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — n/a, manual-mode verification per the pipeline's default (no test-stack ADR exists yet)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **The app shell/navigation itself** — REQ-SB-12-US-01, a dependency, not
  rebuilt here.
- **The agent detail/chat panel** — REQ-SB-13-US-01.
- **Important Reads — dropped from scope entirely** (operator decision,
  2026-08-11) — no card on the dashboard, no drill-down page, no route. Not
  even an empty state is built for it in this story. A future story can add
  it back once a real criterion for "Important Read" exists.
- **Deciding To-Do's concrete task source and field set** — REQ-SB-09 itself
  has not resolved this yet; not pre-empted here.
- **Building the REQ-SB-08 or REQ-SB-09 capture pipelines** — this story
  only renders whatever they eventually produce; it does not build or modify
  either pipeline.
- **Any Second Brain UI beyond the pages listed in Affected Screens.**

## Notes

**Prototype parity (my-day.html + its drill-down pages):**

- Dashboard card grid (three sections, counts) — **Specced** (Scenario 1).
- Dashboard first-run/empty state — **Specced** (Scenario 2).
- Card-to-page navigation — **Specced** (Scenario 3).
- Emails drill-down populated list + empty state — **Specced** (Scenarios 4,
  5).
- Calendar drill-down populated list + empty state — **Specced** (Scenarios
  6, 7).
- To-Do drill-down empty state — **Specced** (Scenario 8).
- To-Do drill-down populated list (the specific subject/customer/due-date
  fields the prototype currently shows) — **Deferred** (reason: contingent
  on REQ-SB-09's still-unresolved task source, operator-confirmed 2026-08-11
  to wait rather than define a placeholder; lands in a future story once
  REQ-SB-09 is specced).
- Important Reads (`my-day-reads.html`) — **Dropped from scope entirely**
  (operator decision, 2026-08-11) — no card, no page, no empty state. Not
  deferred to a later story within this spec; would need its own future
  story once a real "Important Read" criterion exists.

**Originally flagged (`gate: flagged`), now resolved (`gate: clear`),
2026-08-11:**

REQ-SB-12's own PRD breadcrumb named "each My Day drill-down page's exact
content" as an open question for `/spec` time. Two of the four originally-
considered sections (Calendar, Emails) were already resolvable from
established schemas and specced concretely. The other two are now resolved
directly by the operator rather than guessed:

1. **Important Reads** — dropped from this story's scope entirely, since no
   note field, tag, or pipeline is named anywhere as its source. Not
   invented; genuinely deferred to whenever a future story defines it.
2. **To-Do** — confirmed to wait for REQ-SB-09's own future spec pass rather
   than define a placeholder field set now. This matched what the story
   already specced (empty-state-only, Scenario 8), so no scenario changes
   were needed for this half.

No material assumption was made; no `ESCALATIONS.md` entry was needed (no
PRD contradiction, no out-of-scope event — this was an unresolved-product-
question flag, resolved by the operator, not a requirement dispute). The
`REVIEW-QUEUE.md` entry pointing here has been removed now that both open
points are resolved. Ready for `/plan-tasks`.

**Architecture pass (2026-08-11, `/plan-tasks` step 1):** the Constraints'
"no backend endpoint currently returns My Day summary/drill-down data" gap
is resolved — new router `app/api/my_day_router.py` (`GET /my-day/summary`,
`GET /my-day/emails`, `GET /my-day/calendar`, `GET /my-day/todo`), new
business module `app/business/my_day.py`, new `vault_writer.
list_notes_in_kind_folder()` primitive. Full shape and reasoning:
`Implementation/Architecture/architecture.md` → "My Day & Agent Panel
APIs" → "My Day dashboard & drill-downs (REQ-SB-12-US-02)". **No ADR** —
this is a straight extension of already-`Accepted` structural decisions
(ADR-003's layering, the existing one-module-per-feature `business/`
shape, a `vault_writer` read primitive mirroring an existing one's shape
exactly); no new tool, framework, storage mechanism, or trust-surface
decision, and nothing contradicts any Accepted ADR, the PRD, or a
`MEMORY.md` constraint.

**Architecture scope:** `architecture.md` → "Frontend Application
Architecture" (routing/styling/component conventions this story must
reuse, not re-decide — `ADR-010`) and "My Day & Agent Panel APIs" → "My
Day dashboard & drill-downs (REQ-SB-12-US-02)" (the new backend surface
this story's tasks build against). Concrete files this bounds the
decomposer/coder to: `src/backend/app/api/my_day_router.py` (new),
`src/backend/app/business/my_day.py` (new),
`src/backend/app/data_access/vault_writer.py` (new
`list_notes_in_kind_folder` primitive), `src/backend/app/main.py` (router
registration), and `src/frontend/src/pages/MyDayPage.tsx` plus new
`src/frontend/src/features/my-day/` components/`api/client.ts` calls for
the frontend half — reusing `components/shell/AppShell.tsx`/`Sidebar.tsx`
and the existing `styles/` files as-is, per `ADR-010`.

`gate: clear` 2026-08-11 — no ADR triggered, no material assumption made
(the two real open product questions were resolved by the operator
directly, recorded above; the new API surface is a direct extension of
already-Accepted patterns). Ready for the decomposer.

**Decomposer pass (2026-08-11, `/plan-tasks` step 2):** all 8 scenarios
locked as `REQ-SB-12-US-02-AC-01`..`AC-08` (sequential, no non-locked ACs).
Seven tasks created — `T01`-`T03` backend (`data_access →
business → api` layering per `ADR-003`), `T04`-`T07` frontend (`T04`
dashboard + drill-down routing scaffold; `T05`/`T06`/`T07` one per
drill-down page) — flat root at `Implementation/Tasks/`. `depends_on` is
acyclic: `T01→T02→T03→T04→{T05,T06,T07}`; `T04` additionally
`depends_on: [REQ-SB-12-US-01-T01]` (a task-level edge, not just the
story-level "Blocked by" already recorded above) since it literally edits
that task's `App.tsx`/reuses its `AppShell`. Every locked AC has at least
one AC-tagged manual verification step: `AC-01`-`AC-03` in `T04`, `AC-04`/
`AC-05` in `T05`, `AC-06`/`AC-07` in `T06`, `AC-08` in `T07` — per the
"user-observable outcome" placement rule, tagged steps live on the frontend
page tasks that actually render what `T01`-`T03`'s backend endpoints
return; `T01`-`T03` carry thorough non-AC-tagged live-API-call smoke checks
instead (mirroring `REQ-SB-08-US-01`'s own `T01`-`T04`/`T05` split). Two
locked ACs (`AC-02` first-run-all-zero, `AC-06` Calendar populated) have no
naturally-occurring real-vault state to verify against today (the real
vault already has captured emails, and has no `Work/Meetings/` folder yet)
— their Tests steps use the same temporarily-swap-a-mock-or-stub-then-revert
technique `REQ-SB-12-US-01-T02` already established for its own first-run
state, or (for `AC-06`) a temporary real test note written to and then
deleted from the real vault, so no locked AC is left unverifiable
(trigger-6 avoided).

No material assumption was made beyond this run's own routing-shape choice
(`/my-day/emails`|`/my-day/calendar`|`/my-day/todo` as sibling routes,
matching the four endpoints' naming 1:1 — a direct, non-arbitrary mapping,
not a guess); no `ESCALATIONS.md` entry needed; no contradictory inputs; no
oversized task (each is one cohesive layer/page). `gate: clear` 2026-08-11
— no MUST-FLAG trigger fired this pass. **Story `status: Draft → Ready`**;
every task written at `status: Ready` in lockstep. Eligible for
`/plan-sprints`.

**Product-owner pass (2026-08-11, `/plan-sprints`):** grouped into
`SPRINT-009` as a single-story sprint (`depends_on_sprints: [SPRINT-008]`,
per `T04`'s task-level `depends_on: [REQ-SB-12-US-01-T01]`). Considered
combining with `REQ-SB-13-US-01` (also `Ready`, ungrouped, depends only on
`SPRINT-008`, no dependency edge between the two) but split into two
sprints on sizing grounds — 7 + 8 = 15 tasks would be more than double this
session's established ~4-6 task sprint precedent. Full rationale:
`Implementation/Sprints/SPRINT-009-my-day-dashboard-and-drilldowns.md` →
"Grouping Rationale & Sizing". `gate: clear`, `sprint: SPRINT-009`. Eligible
for `/implement-sprint` once `SPRINT-008` is `Done`.

**Coder pass (`/implement-sprint`), 2026-08-11.** Built end-to-end:
`T01` (`list_notes_in_kind_folder` primitive) → `T02` (`my_day.py`
aggregation) → `T03` (`my_day_router.py` + `main.py` registration) →
`T04` (dashboard + routing scaffold) → `{T05 (Emails), T06 (Calendar), T07
(To-Do)}`, all 7 tasks `Done`, all 8 locked ACs verified live — backend
smoke-checked directly against the real vault/Python shell; frontend ACs
verified in a real browser via headless-Chrome CDP (`npm run dev` +
`uvicorn` on port `8002`), per `Learnings.md`'s standing verification
pattern. `npm run build` (real `tsc -b`) ran clean, zero TypeScript
errors.

**Real-vault-state drift from spec time, handled without weakening any
AC:** `SPRINT-006` (`REQ-SB-08`, Meeting Capture) landed concurrently
while this sprint ran — the real vault's `Work/Meetings/` folder, empty
when this story/its tasks were written, now holds 39 real Meeting notes.
`AC-01`/`AC-06` ended up verified against real populated Calendar data
instead of the empty/synthetic-note techniques the tasks originally
planned (still exercising the same rendering paths); `AC-02`/`AC-05`/
`AC-07` (the three all-zero/empty states) used a temporary client-side
stub-and-revert technique instead, since the real vault can no longer
produce them naturally. No real vault file was created or left behind by
any task. Full detail: `T01`/`T02`/`T04`/`T06`'s own Implementation Logs.

**Genuine architectural gap found and fixed, flagged for spot-check:**
no CORS middleware existed anywhere in `src/backend` before this story —
this is the first task in the codebase making a real browser-to-FastAPI
fetch call (`REQ-SB-12-US-01`'s `api/client.ts` was built but never
actually called). Without it, every one of this story's 8 locked ACs
would be unverifiable and the feature itself non-functional in any real
deployment shape, not just this session's dev setup. Fixed within `T03`'s
own `main.py` scope (`fastapi.middleware.cors.CORSMiddleware`, no new
dependency) — logged as a scope-internal assumption (the allowed-origins
list itself), `T03`'s own `gate: flagged` for human spot-check, with a
`REVIEW-QUEUE.md` entry recommending a future ADR formalize the policy
rather than the current literal hardcoded dev-origin list (which a
concurrent `REQ-SB-13-US-01` pass already had to extend once). No
`ESCALATIONS.md` entry — no new external dependency, no shared-interface
change to an existing consumer, confined to a file already in `T03`'s own
`Files to Modify`.

Zero blocked tasks, zero `ESCALATIONS.md` entries. **Story `status: Ready
→ Done`.**
