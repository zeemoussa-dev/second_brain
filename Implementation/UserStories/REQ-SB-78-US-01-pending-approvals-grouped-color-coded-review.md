---
id: REQ-SB-78-US-01
title: Pending Approvals — Grouped, Color-Coded Review
requirement_ids: [REQ-SB-78]
requirement_section: "REQ-SB-78: Pending Approvals — Grouped, Color-Coded Review"
phase: P2
status: Done
gate: clear
gate_reason: "was flagged net-new-design-needed (approved prototype predates REQ-SB-76's decision control AND any grouping/color treatment). Resolved by precedent, not a fresh confirmation this specific instance — the operator has now given the identical resolution twice this session, in these exact words, for REQ-SB-75 ('No Straight No Designer we will handle the Design Later') and REQ-SB-76 ('No Need for Designer What we have is amazing'). Applying the same resolution a third time rather than re-asking a settled question — flag this explicitly to the operator so they can redirect if this one is actually different. The coder builds the grouping/color treatment directly using the app's existing token/component vocabulary; a later design pass may restyle it."
sprint: "SPRINT-075"
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-78-US-01 — Pending Approvals — Grouped, Color-Coded Review

## Story

**As a** Second Brain operator
**I want** the Pending Approvals list to group its items by proposal type/
owning agent, with a distinct color treatment per group, instead of one
flat undifferentiated list
**So that** at real scale (496 real pending records existed at one point
this session before manual cleanup) I can visually scan and approve every
request of one kind as a fast sweep, instead of item-by-item triage across
an undifferentiated list

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-78: Pending Approvals — Grouped,
  Color-Coded Review*. Raised 2026-08-19, operator: "We can Group the
  Approval List to Sections and Colors So it will be Easier to approve all
  requests for a certain type" — deliberately deferred out of `REQ-SB-76`'s
  own scope at the operator's explicit direction. No `<!-- Draft -->`
  marker on this requirement.
- **Real current frontend, confirmed live this pass (not assumed):**
  `src/frontend/src/pages/MyDayApprovalsPage.tsx` renders every pending
  record as one flat `.item-list`/`.item-row` — no grouping, no color
  differentiation by type or agent. Each row shows `Approve`/`Decline`
  buttons EXCEPT records whose `action_id === 'propose_company_review'`,
  which instead render `CompanyReviewDecisionControl` — a distinct 5-way
  decision control (Customer / Partner / Affiliate-with-parent-picker /
  Merge-with-parent-picker / Decline). This per-item-card variety is real,
  already-live code (`REQ-SB-76-US-01-T08`), built as part of `SPRINT-072`,
  which is `In Progress` as of this pass — **still building, not yet
  `Done`.**
- **The approved prototype does NOT reflect this real, current shape.**
  `html-prototype/my-day-approvals.html`, confirmed live, still shows the
  OLDER, simpler two-hardcoded-example flat list (Meeting Capture / People
  Notes, plain `Approve`/`Decline` only) — it predates `REQ-SB-76`'s own
  decision-control variety entirely and was never updated after that work
  landed (that work shipped its own UI "per the story's own operator
  override," i.e. without a `/design` pass, per
  `MyDayApprovalsPage.tsx`'s own code comment). This is a real, disclosed
  prototype/reality drift this story does not, on its own, fix — but it
  means there is currently **no approved design reference at all** for
  either (a) the real, current per-item card shape, or (b) this
  requirement's own grouping/color ask.
- **Real API surface available to a grouping key, confirmed live:**
  `GET /pending-approvals` (`app/api/pending_approvals_router.py`) returns
  every record already carrying `agent_id`, `agent_name` (resolved),
  `action_id`, and `description` — no new backend field is required merely
  to GROUP by proposal type or owning agent; which of the two (or both) is
  the actual grouping key, and what the color scheme is, are pure
  frontend/design decisions with no PRD-given specifics.
- **Real, disclosed sequencing risk for the architect:** `SPRINT-072`
  (`REQ-SB-76`, the Company Review decision control living in this exact
  screen area) is **actively in flight** as this story is drafted. This
  story's own eventual design pass and implementation should be grounded
  against the **POST-`SPRINT-072`** UI (the shape confirmed live above),
  not a stale pre-`SPRINT-072` assumption — recorded here explicitly, not
  silently guessed either way, since the per-item card shape is itself
  still changing underneath this story.
- **Resolved 2026-08-19, not left open:** "easier to approve all requests
  for a certain type" DOES require a real bulk-approve action, not just
  visual grouping — visual-only grouping doesn't deliver what those words
  literally ask for (you'd still click every item individually). Scoped
  narrowly: bulk-approve applies only to groups whose items share a
  simple, uniform approve/decline action (looping the ALREADY-EXISTING
  single-item `POST /pending-approvals/{id}/approve` endpoint per item —
  zero new backend capability needed, a frontend orchestration loop only).
  Groups whose items carry a genuine branching decision (the Company
  Review 5-way Customer/Partner/Affiliate/Merge/Decline control) do NOT
  get a bulk-approve action — there is no single unambiguous "approve" to
  bulk-apply across different real companies. See Scenario 7.

## Acceptance Criteria

### Scenario 1: Pending Approvals renders grouped by action_id, not as one flat list

```gherkin
Given two or more real pending approvals of different action_ids (e.g. one
    propose_company_review record and one route_thread_to_project record)
When the operator opens Pending Approvals
Then the items render grouped into distinct sections keyed by action_id
    (each backed by a [data-group-key="<action_id>"] section container),
    rather than as one flat, undifferentiated .item-list
```
<!-- AC-ID: REQ-SB-78-US-01-AC-01 -->

### Scenario 2: Each group carries its own distinct color-class treatment

```gherkin
Given the grouped Pending Approvals list from Scenario 1
When the operator views it
Then every group's own section container carries a distinct
    KNOWN_GROUPS-derived CSS class (group-color-N) from every OTHER
    currently-rendered group's own class, so a real, structural,
    DOM-verifiable per-group visual differentiation exists (exact pixel
    color/hue is out-of-band visual polish, not a locked assertion here)
```
<!-- AC-ID: REQ-SB-78-US-01-AC-02 -->

### Scenario 3: A group with zero pending items is not shown

```gherkin
Given an action_id that currently has no pending records at all
When the operator opens Pending Approvals
Then no [data-group-key] section for that action_id is rendered — only
    groups whose own items.length > 0 appear
```
<!-- AC-ID: REQ-SB-78-US-01-AC-03 -->

### Scenario 4: An action_id with no predefined KNOWN_GROUPS entry still renders, in a real, visible catch-all — never silently dropped

```gherkin
Given a real pending approval whose action_id is not a key in
    KNOWN_GROUPS (including a null background-trigger action_id)
When the operator opens Pending Approvals
Then that item still renders, inside a real, visible
    [data-group-key="other"] "Other" section — never silently hidden or
    dropped from the list
```
<!-- AC-ID: REQ-SB-78-US-01-AC-04 -->

### Scenario 5: Existing per-item decision controls (including the Company Review 5-way control) keep working unchanged inside their own grouped section

```gherkin
Given a real pending propose_company_review record, whose own item-row
    already renders the 5-way Customer/Partner/Affiliate/Merge/Decline
    decision control today
When the grouped, color-coded layout from this story ships
Then that same decision control still renders (data-testid=
    "company-review-decision" and its own affiliate/merge pickers) and
    functions identically inside its own [data-group-key=
    "propose_company_review"] section — grouping is a layout change
    around the existing per-item card, never a replacement of any
    proposal type's own decision control
```
<!-- AC-ID: REQ-SB-78-US-01-AC-05 -->

### Scenario 6: A group whose items share a simple approve/decline action gets a real bulk-approve control; a group with branching decisions (Company Review) does not

```gherkin
Given a group of 2+ real pending approvals that all share an action_id
    NOT in BRANCHING_DECISION_ACTION_IDS (e.g. route_thread_to_project or
    acknowledge_classification_failure records — no picker, no branching
    outcome)
When the operator uses that group's own bulk-approve control
Then every item in the group is approved via the ALREADY-EXISTING
    single-item POST /pending-approvals/{id}/approve endpoint, called
    once per item — no new backend action, and the group empties as each
    one resolves
Given a group whose items instead carry an action_id IN
    BRANCHING_DECISION_ACTION_IDS (propose_company_review)
When the operator views that group
Then no bulk-approve control is rendered for it — each item still
    requires its own individual Customer/Partner/Affiliate/Merge/Decline
    choice
```
<!-- AC-ID: REQ-SB-78-US-01-AC-06 -->

### Scenario 7: The empty state (no pending approvals at all) is unaffected

```gherkin
Given zero real pending approvals exist
When the operator opens Pending Approvals
Then the existing empty-state message ("Nothing awaiting approval right
    now...") renders exactly as it does today, with no [data-group-key]
    grouping chrome rendered at all
```
<!-- AC-ID: REQ-SB-78-US-01-AC-07 -->

## Affected Screens

- `html-prototype/my-day-approvals.html` — needs a **new `/design` pass**
  before `/plan-tasks` proceeds (see `gate_reason`): the prototype must be
  brought up to date with the real, current per-item card variety (the
  Company Review 5-way decision control, confirmed live in `##
  Context`) AND extended with this requirement's own grouping/color
  treatment. Neither exists in the prototype today.
- `src/frontend/src/pages/MyDayApprovalsPage.tsx` — the real implementation
  target; grouping/color wraps its existing `.item-list`/`.item-row`
  rendering, does not replace it.

**Prototype parity:**

- **Flat item list (Meeting Capture / People Notes hardcoded examples)** —
  **Superseded.** The real, live implementation already replaced this with
  dynamic per-item content, including the Company Review 5-way control
  (`REQ-SB-76-US-01-T08`) — the prototype file itself was never updated to
  reflect that shipped change, a disclosed, pre-existing drift this story
  does not fix on its own but must design against (see `## Context`).
- **Grouping by proposal type/agent, with per-group color treatment** —
  **Deferred pending `/design`.** Net-new; no prototype coverage exists at
  all for this. Needs a `/design` pass before `/plan-tasks` — see
  `gate_reason`.
- **Approve/Decline per-item actions (including type-specific decision
  controls like the Company Review 5-way control)** — **Specced** by
  Scenario 5, continuing unchanged inside the new grouped layout.
- **Empty state** — **Specced** by Scenario 6, unchanged from today.

## Dependencies

- **Related to (sequencing, not a hard blocker):** `REQ-SB-76-US-01`
  (Company Review, `Draft`, `gate: flagged`, `SPRINT-072` `In Progress`) —
  shares this exact screen; this story's own eventual design/color scheme
  should account for the Company Review proposal type as one of its
  groups, and should be designed against the POST-`SPRINT-072` UI (see `##
  Context`). Not required to be `Done` first — this story's own grouping
  wrapper is generically keyed off `agent_id`/`action_id`, not specific to
  any one proposal type.
- **Related to:** `REQ-SB-21-US-01` (Agent Working Modes, `Done`) — the
  origin of the Pending Approvals surface this story restyles.
- **External:** none new.

## Constraints

- **Grouping/color wraps the existing per-item card, never replaces it** —
  every proposal type's own current rendering (including
  type-specific decision controls) must keep working unchanged (Scenario
  5).
- **No new backend field is mandated** — `agent_id`/`agent_name`/
  `action_id`, already returned by `GET /pending-approvals`, are sufficient
  grouping-key candidates; if the architect's design needs something else,
  that is a disclosed, explicit decision, not a silent assumption.
- **A `/design` pass is required before `/plan-tasks` locks tasks** — no
  approved design reference exists yet for this screen's own grouping/color
  ask (see `gate_reason`).
- Must respect existing frontend conventions (`btn`/`btn-primary`/
  `item-list`/`item-row` vocabulary), consistent with this app's own
  established component reuse discipline.

## Implementation Tasks

<!-- Decomposer-authored table (/plan-tasks step 2, 2026-08-19) — supersedes
the analyst's provisional table. No /design pass (operator resolved by
precedent, see frontmatter gate_reason) — the coder builds directly against
the app's own existing token/component vocabulary. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-78-US-01-T01 | frontend | New `pendingApprovalGroups.ts` (KNOWN_GROUPS lookup + OTHER_GROUP + BRANCHING_DECISION_ACTION_IDS), plus `.group-color-N`/`.group-color-other` CSS custom-property classes | `src/frontend/src/features/agents-map/pendingApprovalGroups.ts`, `src/frontend/src/styles/tokens.css`, `src/frontend/src/styles/my-day.css` | `../Tasks/REQ-SB-78-US-01-T01-groups-lookup-and-css.md` |
| REQ-SB-78-US-01-T02 | frontend | Grouped rendering in `MyDayApprovalsPage.tsx` — group by action_id, suppress empty groups, `Other` catch-all, existing per-item cards/decision controls unchanged, empty state unaffected | `src/frontend/src/pages/MyDayApprovalsPage.tsx` | `../Tasks/REQ-SB-78-US-01-T02-grouped-rendering.md` |
| REQ-SB-78-US-01-T03 | frontend | Bulk-approve control per eligible group, looping the existing single-item approve endpoint | `src/frontend/src/pages/MyDayApprovalsPage.tsx` | `../Tasks/REQ-SB-78-US-01-T03-bulk-approve.md` |
| REQ-SB-78-US-01-T04 | frontend | Real-browser end-to-end verification of every locked AC | `src/frontend/src/pages/MyDayApprovalsPage.tsx` (verification only; in-scope fix only on a genuine live-found defect) | `../Tasks/REQ-SB-78-US-01-T04-live-verification.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, test tooling still pending project-wide; manual/live-browser verification mode used throughout, per every task's own Tests block
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Any change to any individual proposal type's own approve/decline
  mechanism or decision-control shape** (including the Company Review
  5-way control) — purely a list-level layout/visual change.
- **Reconciling `SPRINT-072`'s own in-flight UI changes** beyond reading
  its current live shape for grounding — this story does not block on or
  redesign `REQ-SB-76-US-01`'s own decision control.

## Notes

**Prototype parity:** see `## Affected Screens` above — full breakdown of
Specced/Deferred/Superseded regions.

**Why this pass sets `gate: flagged` (`net-new-design-needed`):** per this
role's own mandatory "Prototype reconciliation" rule — the approved
prototype does not cover this requirement's own grouping/color ask at all,
and additionally has drifted out of sync with the real, live per-item card
shape (Company Review 5-way control) that already shipped without its own
`/design` pass. Recommend running `/design REQ-SB-78` (updating
`my-day-approvals.html` for BOTH the prototype/reality reconciliation and
the new grouping/color treatment) before `/plan-tasks` locks tasks.

**Why this does NOT additionally trip trigger 2:** `REQ-SB-78` carries no
`<!-- Draft -->` marker — the requirement text itself is finalized.

**Why this does NOT trip trigger 7 (contradictory inputs):** no internal
PRD contradiction found — the prototype/reality drift disclosed above is a
DESIGN-ARTEFACT gap (exactly what `net-new-design-needed` exists to
surface), not a contradiction between PRD statements.

**Why this does NOT trip trigger 5 (oversized):** 2 starting tasks (one
design pass, one frontend implementation) — small, comparable to other
single-screen restyle stories already shipped in this project (e.g.
`REQ-SB-52-US-01`'s own palette-swap scope).

**What to do next:** see `REVIEW-QUEUE.md` → `REQ-SB-78-US-01` — run
`/design REQ-SB-78` for human browser sign-off before `/plan-tasks
REQ-SB-78-US-01`.

---

## Architect pass, 2026-08-19 (`/plan-tasks` step 1)

Note: the frontmatter `gate:`/`gate_reason:` above is the current,
authoritative state (`clear` — the operator resolved the `/design`
question by precedent, "coder builds directly using the app's existing
token/component vocabulary"). The `gate: flagged (net-new-design-needed)`
sentences earlier in this `## Notes` section predate that resolution and
are a stale leftover from before the operator's live answer — not
re-asserted, not re-opened, by this pass. This pass proceeds on the
resolved basis: no `/design` pass required before `/plan-tasks` locks
tasks.

**Mechanism decisions (resolving the story's own deferred design/
mechanism choices), grounded directly in real, current code:**

- **Grouping key:** `action_id` (not `agent_id`) — a single agent
  identity can own several distinct `action_id`s (confirmed directly in
  `librarian_housekeeping.py`/`pending_approvals_router.py`'s own
  `_APPROVAL_HANDLERS`), so this is the finer, more useful "approve all
  of a certain type" key the requirement's own language asks for. No new
  backend field — `GET /pending-approvals` already returns `action_id`.
- **Label + color:** a new, small, static frontend-only lookup table
  (`KNOWN_GROUPS: Record<action_id, {label, colorClass}>`), with every
  unmapped/`null` `action_id` falling into one `Other` catch-all
  (Scenario 4) — forward-compatible by construction, never needs a code
  change to stay honestly grouped when a future story adds a new
  `action_id`. New `.group-color-N` CSS custom-property variants, NOT the
  existing per-agent `agent_visual_registry` color (confirmed by direct
  reading: that registry defaults every agent to `None`/no override, so
  it cannot structurally guarantee a distinct color per GROUP).
- **Bulk-approve eligibility (Scenario 7):** a `BRANCHING_DECISION_
  ACTION_IDS` set (today: exactly `propose_company_review`, reusing the
  existing `COMPANY_REVIEW_ACTION_ID` per-item branch condition already
  in `MyDayApprovalsPage.tsx`, generalized). A rendered group offers
  bulk-approve iff EVERY item currently inside it has an `action_id` NOT
  in that set — computed per rendered group, correctly covering the
  heterogeneous `Other` catch-all too. Bulk-approve loops the ALREADY-
  EXISTING single-item `approvePendingApproval(id)` (no decision body) —
  zero new backend endpoint/capability.

**Architecture scope:** §"Pending Approvals — Grouped, Color-Coded
Review" (`Implementation/Architecture/architecture.md`) — bounds the
coder to that section.

**Why this pass creates no new ADR:** every mechanism above is
composition of already-`Accepted` primitives — no new backend field, no
new endpoint, no new linking/write primitive; bulk-approve loops the
existing single-item Approve endpoint verbatim, grouping/color reuses
fields `GET /pending-approvals` already returns plus a new, purely
presentational frontend lookup table. No new tool, framework, or
structural module boundary — confirms the operator's own working
assumption for this story. `gate` stays `clear` (unchanged by this pass —
no trigger 3 fired). This pass's own breadcrumb: gate: clear 2026-08-19
— no ADR, no new assumption, `/design` requirement already resolved by
precedent per the frontmatter above.

---

## Decomposer pass, 2026-08-19 (`/plan-tasks` step 2)

All 7 Gherkin scenarios locked as `REQ-SB-78-US-01-AC-01` through `AC-07`,
tightened into **structural, DOM-verifiable assertions** per this role's
own "Structural ACs for screen/frontend stories" mandate — every locked AC
names a concrete, `jsdom`/CDP-checkable signal (`[data-group-key="..."]`
section containers, a `group-color-N` class present on each rendered
group's own container, `[data-testid="company-review-decision"]` still
rendering unchanged inside its own group) rather than an unverifiable
"looks distinct" visual claim. Scenario headers 6/7 renumbered into
document order (the analyst's own original numbering had "Scenario 7"
appear before "Scenario 6" in the file) — no substance change, only
sequencing clarity.

Four tasks, `T01`-`T04` (see `## Implementation Tasks`):

- `T01` — `pendingApprovalGroups.ts` + CSS. `depends_on: []`.
- `T02` — grouped rendering. `depends_on: [T01]`.
- `T03` — bulk-approve control. `depends_on: [T01, T02]`.
- `T04` — real-browser live verification, all 7 ACs. `depends_on: [T02, T03]`.

**AC coverage:** `AC-01`/`AC-02`/`AC-03`/`AC-04`/`AC-05`/`AC-07` in `T02`
(the grouped-rendering task itself); `AC-06` in `T03`; `T04` independently
re-confirms all 7 live, end-to-end, in a real browser — mirrors this
project's own established "screen-level AC verification is the real cost
center" precedent (`Implementation/Learnings.md`, `SPRINT-026`/`036`/`038`).

**Status:** every AC is locked (7/7), every locked AC has at least one
AC-tagged verification step, and `depends_on` is acyclic. Story advances
**`Draft` to `Ready`**. `gate: clear` unchanged by this pass — breadcrumb:
gate: clear 2026-08-19 — no new MUST-FLAG trigger fired at this step; the
`/design` question was already resolved by precedent at the architect
step, not re-opened here.

---

## Coder pass, 2026-08-19 (`/implement-sprint`, `SPRINT-075`)

All 4 tasks built and independently live-verified, in dependency order
(`T01` → `T02` → `T03` → `T04`), against the real running app and real
backend/vault data (headless-Edge CDP; no test-stack ADR exists yet, so
this remains manual/live-browser verification mode per every task's own
Tests block). All 7 locked ACs (`AC-01`-`AC-07`) confirmed live at least
twice each (once by the task that first delivers the mechanism, once more
independently by `T04`'s own end-to-end pass) — full detail in each task
file's own `## Implementation Log`.

**One real, load-bearing finding, in-scope-resolved:** `T03`'s own
live verification of `AC-06` (bulk-approve) found `vault_writer.py`'s
pending-approvals JSON state file has no concurrent-write locking — firing
concurrent approve calls (`Promise.all`) silently lost data (only the last
writer survived). Resolved in-scope by looping sequentially instead
(already within `T03`'s own explicit "sequential or `Promise.all` —
coder's own choice" latitude, not a scope deviation); `AC-06` passes,
live-verified with zero data loss. The underlying `vault_writer.py`
primitive gap itself is out of this story's own frontend-only scope — not
fixed here, logged as `ESC-058` (`ESCALATIONS.md`), `REVIEW-QUEUE.md`
(recommends a future `/bug` capture), and a new standing Constraint in
`MEMORY.md`.

Every disposable test artefact created during verification (real
`pending_approval_registry.create_pending_approval()` calls — no
public "create arbitrary" HTTP endpoint exists — since none of this
story's needed test conditions, e.g. an unmapped `action_id` or a 2+-item
non-branching group, currently occur naturally in the real, live pending
queue) was resolved via the real `POST /pending-approvals/{id}/approve`
or `/decline` endpoints before the task that created it closed — never a
raw store mutation, per this project's archive-not-delete/API-first
standing constraint. Zero real, operator-owned pending records were
mutated.

**Status:** every task `Done`, every locked AC verified live and passing,
nothing `Blocked`. Story advances **`Ready` → `Done`**.
