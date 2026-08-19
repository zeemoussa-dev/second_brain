---
id: REQ-SB-79-US-01
title: The Librarian — Two Sub-Pipelines (Threads Cleaning, Company & Partner Building)
requirement_ids: [REQ-SB-79]
requirement_section: "REQ-SB-79: The Librarian — Two Sub-Pipelines (Threads Cleaning, Company & Partner Building)"
phase: P2
status: Ready
gate: flagged
gate_reason: "trigger-3 (ADR-058 created) — architect pass, 2026-08-19. The analyst's own prior gate:clear pass (below, unedited) found no MUST-FLAG trigger of its own; this NEW flag is raised entirely by the architect step, which created ADR-058 (a new 'retire without delete' agent_registry.py primitive, the run_housekeeping_pass() split, and the full re-homing of every Pending-Approval-creating call site onto the new Company and Partner Building identity). Does not halt /plan-tasks — the decomposer still locks ACs/tasks against this same architecture pass so the human reviews the ADR and the resulting tasks together in one pass, per Pipeline.md."
sprint: "SPRINT-073"
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-79-US-01 — The Librarian — Two Sub-Pipelines (Threads Cleaning, Company & Partner Building)

## Story

**As a** Second Brain operator
**I want** the Librarian Section to house two real, independently-
controllable sub-agents — **"Threads Cleaning"** (the existing
`rename_threads` → `link_thread_messages` → `backfill_files` →
`populate_thread_related_links` chain, unchanged fixed order) and
**"Company and Partner Building"** (`backfill_company_folders` plus the
newer, separately-dispatched `propose_customer_backfill`/
`propose_customer_archival_candidates`, and `propose_company_review` once
`REQ-SB-76` ships) — instead of the single shared `librarian-housekeeping`
identity all of this runs under today
**So that** I can see, schedule, and control the two conceptually distinct
pipelines (Thread hygiene vs. Customer/Partner/Affiliate entity building)
separately in the Agents Map, without one's own cadence being coupled to
the other's

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-79: The Librarian — Two
  Sub-Pipelines (Threads Cleaning, Company & Partner Building)*. Raised
  2026-08-19, operator: "I can see in the Liberian Section in the UI its a
  one Agent not a Pipeline" then "How big is the Change to make it a
  pipeline so instead of visiting all steps everytime we have one Sub Agent
  Per job" — explored and sized directly with the operator, then
  concretized to a fixed, final shape: "Just be Concrete / 2 Pipelines When
  for Threads Cleaning and one for Cumpany and Partner Building." No
  `<!-- Draft -->` marker; the requirement's own concrete 2-sub-agent scope
  is the requirement's real, final text, not a suggestion layered on a more
  open "one agent per job" design — this story does not re-open that
  question.
- **Real current chain, confirmed live this pass:**
  `app/business/pipelines/librarian_housekeeping.py::run_housekeeping_pass`
  bundles FIVE jobs in this exact fixed order:
  `rename_threads()` → `link_thread_messages()` → `backfill_files()` →
  `populate_thread_related_links()` → `backfill_company_folders()`. The
  first four map directly onto the PRD's own named "Threads Cleaning" set
  (`rename_threads`, `link_thread_messages`, `backfill_files`,
  `populate_thread_related_links`) — confirmed to run together, in this
  same fixed order, exactly as the PRD's own text asserts. The fifth,
  `backfill_company_folders`, is the first job the PRD's own "Company and
  Partner Building" set names — it currently runs on `run_housekeeping_
  pass`'s own shared schedule alongside Threads Cleaning, which this story
  separates.
- **The newer Customer/Partner/Affiliate jobs are already separately-
  dispatched, confirmed live:** `propose_customer_backfill()` (line 596)
  and `propose_customer_archival_candidates()` (line 1085) — both
  `REQ-SB-74`, already `Done` — exist in the SAME module but are NOT wired
  into `run_housekeeping_pass()`'s own chain (confirmed by reading the
  function body above); each is dispatched independently, never on the old
  shared schedule, exactly per the PRD's own framing. `propose_company_
  review()` (line 773, `REQ-SB-76`) is the third member of this same set,
  not yet `Done` (`REQ-SB-76-US-01`, `SPRINT-072`, `In Progress`) — this
  story's own Scenario 5 covers the case where it joins after this story
  ships.
- **Real files touching the shared `librarian-housekeeping` identity or the
  `librarian_housekeeping` module, confirmed by direct grep this pass (not
  trusted from the PRD's own count alone, per this role's own "confirm by
  grep" instruction):**
  - `app/main.py` — seed-agent bootstrap, creates the ONE `librarian-
    housekeeping` Agent record at app start (line 55).
  - `app/business/skill_registry.py` — schedule-to-agent registration:
    `"run_housekeeping_pass": ["librarian-housekeeping"]` (line 91).
  - `app/business/pipelines/librarian_housekeeping.py` itself — multiple
    `agent_id="librarian-housekeeping"`/`requesting_agent_id="librarian-
    housekeeping"` literal call sites inside the Job functions that create
    Pending Approvals (lines 494, 589, 693, 849, 1118) — each belongs to
    one specific Job and needs to move to whichever of the two new agent
    identities now owns that Job.
  - `app/api/pending_approvals_router.py` — the `_APPROVAL_HANDLERS`
    dispatch table's 4 `finalize_*` entries for this module's own proposal
    kinds (`propose_librarian_company_link`, `propose_customer_backfill_
    routing`, `propose_customer_archival_candidate`, `propose_company_
    review`) — all currently resolved against the one shared agent
    identity via `agent_registry.get_agent(record["agent_id"])`.
  - `app/api/email_poc_router.py` — POC endpoints dispatching into this
    module's own Jobs.
  - `app/business/email_classification.py` — references `librarian_
    housekeeping.populate_thread_related_links` in its own comments
    (ownership-transfer context).
  - `app/data_access/section_ownership.py` — the `_CALLER_ALLOW_LISTS`
    registry's dotted-caller-name keys (`"librarian_housekeeping.backfill_
    files"`, `"librarian_housekeeping.populate_thread_related_links"`,
    `"librarian_housekeeping.link_thread_messages"`) — these key off the
    FUNCTION's own dotted name, not the agent identity, so may need zero
    change; confirmed for the architect to verify, not asserted here.
  - `app/business/skill_tools.py` — a skill-gate comment naming
    `librarian-housekeeping` as the one identity `run_housekeeping_pass`
    can ever be granted to (line ~346).
  - **8 real production files total** (excluding a `.scratch/` throwaway
    verification script this pass also matched, which is not real
    application code) — the PRD's own text names 4 categories (Pending
    Approvals call sites, `section_ownership.py`, `skill_registry.py`,
    `main.py`) which this grep confirms, and additionally surfaces `email_
    classification.py`, `email_poc_router.py`, and `skill_tools.py` as
    real, disclosed call sites the PRD's own text did not individually
    name. Exact per-file, per-Job reassignment is a mechanism-level
    decision left to the architect (mirrors `REQ-SB-73-US-01`'s own
    "Gherkin specifies outcome, not mechanism" precedent), not asserted
    scenario-by-scenario here.
  - `app/api/agents_router.py`'s own `get_job_tree()` gate (hardcoded to
    `email-capture-pipeline` only, `REQ-SB-65`) is real, disclosed
    background context for WHY the Librarian currently shows as a single
    agent with no Job Tree — but is NOT itself part of this story's own
    concrete 2-sub-agent scope (see `## Non-Goals`).
- **Sizing:** the PRD's own text estimates this smaller than `REQ-SB-72`
  itself (9 tasks/L, which built these Jobs from scratch) — "mostly
  re-registration/re-wiring of already-working logic, not new logic."

## Acceptance Criteria

### Scenario 1: The Librarian Section houses two real, independently-listed Agents instead of one

```gherkin
Given the Librarian Section currently houses a single Agent identity
    (librarian-housekeeping) in the Agents Map
When this story ships
Then the Librarian Section houses two real, independently-listed Agents —
    "Threads Cleaning" (agent id threads-cleaning) and "Company and
    Partner Building" (agent id company-and-partner-building) — each its
    own real Agent record via agent_registry.create_agent, both assigned
    to the same already-existing "librarian" Section, neither one merely
    a cosmetic relabeling that hides the other's own jobs, and the old
    librarian-housekeeping identity no longer appears in a real
    GET /agents listing (retired, not deleted)
```
<!-- AC-ID: REQ-SB-79-US-01-AC-01 -->

### Scenario 2: Threads Cleaning bundles its 4 jobs in the existing fixed order, unchanged

```gherkin
Given a real Thread directory needing rename/message-linking/files-backfill/
    related-links work
When run_threads_cleaning_pass() runs
Then rename_threads, link_thread_messages, backfill_files, and populate_
    thread_related_links all still run together, in that SAME existing
    fixed order (rename first), on one shared schedule — the rename-must-
    run-first ordering guarantee stays intact by construction, exactly as
    it is today
```
<!-- AC-ID: REQ-SB-79-US-01-AC-02 -->

### Scenario 3: Company and Partner Building bundles backfill_company_folders under its own independent schedule

```gherkin
Given a real company-folder-backfill need
When run_company_partner_building_pass() runs, on its own real, persisted
    schedule (agent_schedule_registry.create_or_update_schedule for
    company-and-partner-building)
Then backfill_company_folders runs as part of it, on a schedule
    independent of the Threads Cleaning sub-agent's own cadence — never
    coupled to (blocked by, or blocking) Threads Cleaning's own run,
    confirmed by two distinct, independently-adjustable schedule records
```
<!-- AC-ID: REQ-SB-79-US-01-AC-03 -->

### Scenario 4: The already-shipped, separately-dispatched Customer/Partner jobs (REQ-SB-74) are owned by Company and Partner Building

```gherkin
Given propose_customer_backfill and propose_customer_archival_candidates
    already exist and are already separately-dispatched (never on the old
    shared schedule)
When either is called and creates a real Pending Approval
Then that record's own agent_id is "company-and-partner-building",
    reachable/dispatchable exactly as it is today — the real,
    already-working mechanism is untouched, only the owning-agent
    identity changes
```
<!-- AC-ID: REQ-SB-79-US-01-AC-04 -->

### Scenario 5: propose_company_review (REQ-SB-76) joins Company and Partner Building once it ships, whenever that happens relative to this story

```gherkin
Given REQ-SB-76-US-01's own propose_company_review job may ship before,
    during, or after this story
When propose_company_review exists in the codebase (whether already true
    at the time this story is built, or true only later)
Then it is registered under the Company and Partner Building agent
    identity this story establishes (its own default requesting_agent_id/
    call site already set to "company-and-partner-building" by this
    story's own re-wiring pass) — never a new, third agent, and never
    folded into Threads Cleaning
```
<!-- AC-ID: REQ-SB-79-US-01-AC-05 -->

### Scenario 6: Every already-existing Pending Approval / Agent History record attributed to the old shared identity remains intact and correctly attributed after the split

```gherkin
Given real, already-existing Pending Approval and Agent History records
    currently attributed to the single librarian-housekeeping identity
When this story's re-registration/re-wiring lands (librarian-housekeeping
    retired via agent_registry.retire_agent, never renamed or deleted)
Then no existing record is silently orphaned, deleted, or misattributed —
    agent_registry.get_agent("librarian-housekeeping") keeps resolving a
    real, honest agent_name forever, so every already-resolved and
    still-pending record's own agent attribution remains correct and
    traceable
```
<!-- AC-ID: REQ-SB-79-US-01-AC-06 -->

### Scenario 7: Threads Cleaning's own re-run idempotency, already proven per-job, is unaffected by the split

```gherkin
Given the existing idempotency guarantees each of the 4 Threads Cleaning
    jobs already individually proved (REQ-SB-72/REQ-SB-73's own locked
    ACs)
When run_threads_cleaning_pass() runs again against an already-
    fully-processed corpus
Then it remains a true no-op, unchanged from today's behavior — the split
    does not introduce any new re-run side effect
```
<!-- AC-ID: REQ-SB-79-US-01-AC-07 -->

## Affected Screens

None new — the Agents Map already renders whatever real Agents exist under
a Section generically (confirmed by every prior Librarian-family story
shipping with zero new screen). This story changes WHICH/HOW MANY real
Agent records exist under the Librarian Section, not the Agents Map's own
rendering logic.

**Prototype parity:** N/A — no new `html-prototype/` screen region; the
existing generic Section/Agent card rendering already covers two Agents
under one Section (already proven by every other multi-agent Section in
the app today).

## Dependencies

- **Blocked by (hard):** `REQ-SB-72-US-01` (The Librarian Section — First
  Housekeeping Pipeline, `Done`, `SPRINT-063`) — this story splits that
  story's own already-shipped `run_housekeeping_pass()`/Librarian Section/
  Agent; nothing here is buildable before that shape exists.
- **Blocked by (hard):** `REQ-SB-73-US-01` (Bidirectional Thread ↔ Message
  Linking, `Done`, `SPRINT-067`) — `link_thread_messages()` is one of the 4
  Threads Cleaning jobs this story redistributes.
- **Blocked by (hard):** `REQ-SB-74-US-01` (Customer Backfill, `Done`,
  `SPRINT-068`) — `propose_customer_backfill`/`propose_customer_archival_
  candidates`, owned by Company and Partner Building (Scenario 4).
- **Related to (soft, sequencing note for `/plan-sprints`, NOT a hard
  blocker):** `REQ-SB-76-US-01` (Company Review, `Draft`, `gate: flagged`,
  `SPRINT-072` `In Progress`) — `propose_company_review` joins Company and
  Partner Building once it ships (Scenario 5 explicitly handles either
  ordering); whichever of the two stories ships second should confirm its
  own task correctly wires into the already-existing agent identity the
  first one established.
- **External:** none new.

## Constraints

- **No new Section.** The Librarian stays ONE Section, housing 2 Agents —
  never 2 Sections, never a one-agent-per-job (5-agent) shape, per the
  operator's own final, concrete direction.
- **The rename-must-run-first ordering guarantee inside Threads Cleaning is
  preserved by construction** — all 4 jobs stay bundled together, on the
  same schedule; this story does not re-litigate that ordering tradeoff.
- **Zero new Job logic.** Every job this story redistributes (`rename_
  threads`, `link_thread_messages`, `backfill_files`, `populate_thread_
  related_links`, `backfill_company_folders`, `propose_customer_backfill`,
  `propose_customer_archival_candidates`, plus `propose_company_review`
  once it exists) is already-shipped, already-working logic — this story
  is re-registration/re-wiring of agent ownership only, never a rewrite of
  any job's own mechanism.
- **Every real capability stays reachable via its own real HTTP endpoint**
  (standing project convention).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Decomposer-authored table (/plan-tasks step 2, 2026-08-19) — supersedes
the analyst's provisional table, restructured around ADR-058's own real
decision set (the new "retire without delete" primitive, the two-orchestrator
split, the skill/grant/schedule split, and main.py bootstrap wiring). -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-79-US-01-T01 | backend | `agent_registry.py` gains its first "retire without delete" primitive — `retired: bool`, `retire_agent()`, `list_agents(include_retired=False)`; `get_agent()` unchanged | `app/business/agent_registry.py` | `../Tasks/REQ-SB-79-US-01-T01-retire-without-delete-primitive.md` |
| REQ-SB-79-US-01-T02 | backend | Create the two new Agent identities under the Librarian Section; split `run_housekeeping_pass()` into `run_threads_cleaning_pass()`/`run_company_partner_building_pass()` (the latter composing `people_extraction.retrofit_people_from_emails()`, `REQ-SB-77-US-01` Scenario 6b); re-wire all 5 literal `agent_id="librarian-housekeeping"` call sites to `"company-and-partner-building"` | `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-79-US-01-T02-split-orchestrators-and-agents.md` |
| REQ-SB-79-US-01-T03 | backend | Skill/grant catalog split — replace `run_housekeeping_pass`'s single Skill entry with `run_threads_cleaning_pass`/`run_company_partner_building_pass`, each with its own `@mcp_server.tool()` wrapper and grant | `app/business/skill_tools.py`, `app/business/skill_registry.py` | `../Tasks/REQ-SB-79-US-01-T03-skill-grant-split.md` |
| REQ-SB-79-US-01-T04 | backend | `email_poc_router.py` route split — replace `/poc/librarian-run-housekeeping-pass` with the two new per-pipeline POC routes; every per-Job endpoint unchanged | `app/api/email_poc_router.py` | `../Tasks/REQ-SB-79-US-01-T04-poc-router-split.md` |
| REQ-SB-79-US-01-T05 | backend | `main.py` bootstrap wiring — call the renamed `ensure_librarian_agents_and_section()`, idempotently retire `librarian-housekeeping` and remove its stale schedule, create the two new independent schedules | `app/main.py`, `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-79-US-01-T05-main-bootstrap-wiring.md` |
| REQ-SB-79-US-01-T06 | backend | Real-vault, end-to-end verification: both Agents independently listed (Scenario 1), no orphaned/misattributed historical records (Scenario 6), Threads Cleaning idempotency (Scenario 7), confirm `section_ownership.py`/`pending_approvals_router.py`/`email_classification.py` genuinely need zero change | `app/business/pipelines/librarian_housekeeping.py` (verification only; in-scope fix only on a genuine live-found defect) | `../Tasks/REQ-SB-79-US-01-T06-live-verification.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Extending `REQ-SB-65`'s Job Tree visualization** (currently hardcoded
  to `email-capture-pipeline` only, confirmed live:
  `app/api/agents_router.py`'s `get_job_tree()` gate) to show either new
  sub-agent's own real jobs — a real, disclosed, pre-existing gap named as
  BACKGROUND CONTEXT in the PRD's own text for why the Librarian currently
  displays as one agent, but not something this story's own concrete
  2-sub-agent scope asks to fix. Both new Agents will appear as real
  Agents in the Agents Map; neither gets a populated Job Tree yet — the
  same limitation every non-`email-capture-pipeline` agent already has
  today.
- **A one-job-per-agent (5-agent) shape** — explicitly rejected by the
  operator's own concrete direction ("Just be Concrete / 2 Pipelines").
- **Any change to any individual Job's own internal mechanism, ordering
  logic, or output shape** — pure re-registration/re-wiring of agent
  ownership.
- **Building `propose_company_review` itself** — that is `REQ-SB-76-US-01`'s
  own scope; this story only registers it under the correct owning agent
  once it exists (Scenario 5).

## Notes

**Prototype parity:** N/A — see `## Affected Screens` above.

**Why this pass sets `gate: clear`:**

- **Trigger 1 (material assumption):** none baked into a locked AC — the
  one open mechanism question (exact new-agent-id naming, and the precise
  per-call-site reassignment mapping) is explicitly left to the architect,
  mirroring `REQ-SB-73-US-01`'s own established "Gherkin specifies outcome,
  not mechanism" precedent; Scenario 6 is itself written mechanism-neutral
  ("whether by inheriting one of the two new identities or by an explicit,
  visible migration step").
- **Trigger 2:** `REQ-SB-79` carries no `<!-- Draft -->` marker — the
  requirement's own final concretization ("Just be Concrete / 2
  Pipelines...") is the requirement's real, finalized text.
- **Trigger 4:** no `ESCALATIONS.md` entry needed — the one count
  discrepancy found (8 real files via direct grep vs. an unconfirmed "9"
  expectation) is a minor, disclosed correction (see `## Context`), not a
  contradiction requiring escalation.
- **Trigger 5 (oversized):** 5 starting tasks, smaller than `REQ-SB-72-US-
  01`'s own proven 9-task/L ceiling for this SAME module, consistent with
  the PRD's own "smaller than REQ-SB-72" sizing estimate.
- **Trigger 7 (contradictory inputs):** none found — direct reading of
  `librarian_housekeeping.py`'s real Job chain, the real hardcode
  footprint, and `REQ-SB-74`/`REQ-SB-76`'s own real dispatch shape all
  confirm the PRD's own framing, with only the file-count detail refined
  (not contradicted).
- **Trigger 8 (multiple equally-valid / unclear):** the one real sequencing
  question (does this story need `REQ-SB-76-US-01` `Done` first) is
  explicitly resolved by Scenario 5's own either-ordering wording, not
  left unclear.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired (see the itemized
trigger-by-trigger reasoning above).

**What to do next:** eligible for `/plan-tasks REQ-SB-79-US-01` — the
architect resolves the new-agent-id naming and the per-call-site
reassignment mapping named in `## Context`/`## Implementation Tasks`, then
the decomposer locks ACs and writes tasks. The product-owner should note
the soft `REQ-SB-76-US-01` sequencing consideration (`## Dependencies`)
when grouping sprints.

---

## Architect pass, 2026-08-19 (`/plan-tasks` step 1)

**New-agent-id naming (resolves the analyst's own open mechanism
question):** `threads-cleaning` (from `agent_registry.create_agent
("Threads Cleaning", ...)`) and `company-and-partner-building` (from
`agent_registry.create_agent("Company and Partner Building", ...)`), both
assigned to the SAME already-existing `"librarian"` Section.

**Per-call-site reassignment mapping (resolves the analyst's own second
open mechanism question), confirmed by direct reading, not assumed:**
ALL FIVE literal `agent_id="librarian-housekeeping"`-shaped references in
`librarian_housekeeping.py` (the `_create_librarian_company_link_
proposal` default parameter + its one call site inside `backfill_
company_folders`, plus `propose_customer_backfill`, `propose_company_
review`, `propose_customer_archival_candidates`) become
`"company-and-partner-building"` — the complete, exhaustive set. The four
Threads Cleaning jobs (`rename_threads`, `link_thread_messages`,
`backfill_files`, `populate_thread_related_links`) create ZERO Pending
Approvals between them and need no per-call-site identity edit at all.

**Scenario 6 (no orphaned/misattributed historical records) resolved as:**
a NEW `agent_registry.py` primitive — `retired: bool` + `retire_agent()` +
`list_agents(include_retired=False)` — retires the existing
`librarian-housekeeping` identity (idempotently, at every app start,
never deleted) rather than renaming it or rewriting any historical
record's own `agent_id`. `get_agent()` stays unfiltered, so every
already-existing record keeps resolving a real, honest `agent_name`
forever. Full reasoning and every alternative considered: [ADR-058]
(`Implementation/Architecture/ADR.md`).

**Real cross-story composition, decided this same pass:** `run_company_
partner_building_pass()` (this story's own new scheduled orchestrator)
additionally calls the already-existing `people_extraction.retrofit_
people_from_emails()` — `REQ-SB-77-US-01` Scenario 6b's own self-healing
catch-all. This makes `REQ-SB-77-US-01`'s own scheduled-self-heal task
genuinely `depends_on` whichever task in THIS story creates `run_company_
partner_building_pass()` — see `REQ-SB-77-US-01`'s own `## Notes` for the
full finding. The decomposer should sequence/label this story's own task
that introduces `run_company_partner_building_pass()` clearly enough for
that cross-story edge to be wired correctly.

**Architecture scope:** §"The Librarian — Two Sub-Pipelines: Threads
Cleaning, Company and Partner Building" (`Implementation/Architecture/
architecture.md`) — bounds the coder to that section plus [ADR-058].

**Trigger 3 fired — ADR-058 created.** `gate: flagged`, see `gate_reason`
above and `REVIEW-QUEUE.md` → `REQ-SB-79-US-01`. Does not halt
`/plan-tasks` — the decomposer proceeds to lock ACs/tasks against this
same architecture pass.

---

## Decomposer pass, 2026-08-19 (`/plan-tasks` step 2)

All 7 Gherkin scenarios locked as `REQ-SB-79-US-01-AC-01` … `AC-07`,
tightened to name the concrete, `ADR-058`-resolved mechanism (agent ids
`threads-cleaning`/`company-and-partner-building`, the `run_threads_
cleaning_pass()`/`run_company_partner_building_pass()` split, `retire_
agent()`) in place of the analyst's own outcome-level phrasing — no locked
AC's own substance changed, only buildability.

Six tasks, `T01`-`T06` (see `## Implementation Tasks`), sequenced around
`ADR-058`'s own real ordering constraints (`create_or_update_schedule`
refuses a `capability_id` that is not both a granted Skill and classified
`"mutates": True`, so the Skill/grant split (`T03`) must land before the
schedule-creation bootstrap (`T05`)):

- `T01` — `agent_registry.py` retire-without-delete primitive.
  `depends_on: []`.
- `T02` — new agents + orchestrator split + 5-call-site rewire.
  `depends_on: []` (uses only already-existing `create_agent`/
  `set_agent_section`).
- `T03` — Skill/grant catalog split. `depends_on: [T02]` (the two new
  `@mcp_server.tool()` wrappers delegate to `T02`'s own two new
  orchestrator functions).
- `T04` — `email_poc_router.py` route split. `depends_on: [T02]`.
- `T05` — `main.py` bootstrap wiring. `depends_on: [T01, T02, T03]` —
  needs `retire_agent` (`T01`), `ensure_librarian_agents_and_section`
  (`T02`), and both capabilities granted (`T03`) before
  `create_or_update_schedule` will succeed for either new identity.
- `T06` — real-vault, end-to-end verification. `depends_on: [T04, T05]`.

**AC coverage:** `AC-01` (`T06`, real `GET /agents` listing), `AC-02`
(`T02`, direct `run_threads_cleaning_pass()` call), `AC-03` (`T05`, two
independent schedule records confirmed via `list_schedules`), `AC-04`
(`T02`, real Pending Approval `agent_id` confirmed), `AC-05` (`T02`, code-
reading confirmation the default/call-site is already re-wired regardless
of `REQ-SB-76-US-01`'s own ship status), `AC-06` (`T06`, `get_agent`
resolution + historical-record traceability), `AC-07` (`T06`, re-run
no-op). Every locked AC has at least one tagged step; `T06` additionally
re-confirms `AC-01`-`AC-05` end-to-end as the story's own final integration
pass, mirroring `REQ-SB-76-US-01-T09`'s own established "re-confirm every
AC live, end-to-end" precedent for a story that touches this many real
call sites.

**Status:** every AC is locked (7/7), every locked AC has at least one
AC-tagged verification step, and `depends_on` is acyclic (`T01`/`T02` →
`T03`/`T04` → `T05` → `T06`). Story advances **`Draft` → `Ready`**.
`gate` stays `flagged` — unchanged by this pass, per the architect's own
`gate_reason` (`ADR-058` still awaits a human look) and the operator's own
explicit instruction for this batch. This does not block the tasks above
from being `Ready` and buildable — the human reviews `ADR-058` and this
same task set together, in one pass, per `Implementation/Pipeline.md`'s
"Promotion of a flagged item" gate.

**Real cross-story composition, confirmed:** `T02`'s own `run_company_
partner_building_pass()` includes the literal `people_extraction.
retrofit_people_from_emails()` call `REQ-SB-77-US-01` Scenario 6b depends
on — `REQ-SB-77-US-01-T03` (verification-only) carries a real `depends_on:
[..., REQ-SB-79-US-01-T02]` edge onto this exact task. See `REQ-SB-77-
US-01`'s own `## Notes` (Decomposer pass) for the full reasoning on why
this is recorded as a task-level edge, not deferred to
`depends_on_sprints`.
