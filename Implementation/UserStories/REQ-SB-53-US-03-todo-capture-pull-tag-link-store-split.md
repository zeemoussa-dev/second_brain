---
id: REQ-SB-53-US-03
title: To-Do capture split into Puller/Tagger/Linker/Storer agents, replacing the monolithic todo-capture Worker
requirement_ids: [REQ-SB-53]
requirement_section: "REQ-SB-53: Split Capture Pipelines into Staged Pull / Tag / Link / Store Agents"
phase: P1
status: Draft
gate: flagged
gate_reason: "trigger-3 (ADR-040 created — Capture Pipeline Split mechanism, established by REQ-SB-53-US-01, reused here)"
sprint: ""
created: 2026-08-15
updated: 2026-08-15
---

# REQ-SB-53-US-03 — To-Do capture split into Puller/Tagger/Linker/Storer agents, replacing the monolithic todo-capture Worker

## Story

**As a** Second Brain user
**I want** the To-Do capture pipeline's internal steps (fetch from
Outlook's Tasks folder, classify by customer via Compass, link the
customer hub, write the Task note) to run as 4 separate, individually-
visible, individually-addressable agents instead of one opaque
`todo-capture` Worker
**So that** I can see exactly which stage of a to-do capture run
succeeded or failed for a given task, and configure each stage's own
automation level independently, without losing any of today's
todo-capture behavior

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-53: Split Capture Pipelines into
  Staged Pull / Tag / Link / Store Agents*. The PRD's own comment block
  states To-Do has "the same real Pull/Tag/Link/Store shape" as Email and
  Meetings, without naming To-Do's own functions line-by-line — this
  story confirms that mapping directly against the real, current
  `app/business/todo_classification.py::classify_recent_todos`:
  - **Pull:** `outlook_com.list_outlook_tasks(limit)` — fetch Outlook
    Tasks-folder items.
  - **Tag:** `compass_client.classify_task(subject, body,
    known_customers)` — derives `customer` (or `None`/`_UNSORTED_CUSTOMER`
    resolved to no-field, per `REQ-SB-09-US-01`'s own resolved schema).
  - **Link:** `customer_hub_linking.ensure_customer_hub_note(...)` +
    `link_note_to_customer_hub(...)`, only when a confirmed customer match
    exists.
  - **Store:** `vault_writer.lookup_task_note_stem(...)`-keyed dedup
    lookup, `create_task_note_baseline(...)`/
    `ensure_task_note_baseline_frontmatter(...)` (create-or-top-up),
    `record_task_note(...)`.
  Verified directly against the real current file — not assumed.
  **To-Do's own Link stage is narrower than Email's/Meeting's**: an
  Outlook Task has no sender/attendee list, so there is no Person-note
  linking step here at all — only the customer-hub link, and only when a
  match exists (`REQ-SB-09-US-01`'s own established, deliberate schema
  choice: "Unlike Meeting notes, a Task note links no Person"). This
  story's Linker agent therefore performs strictly less work than its
  Email/Meeting siblings — a real, disclosed asymmetry, not an oversight.
- **Locked inputs — identical to `REQ-SB-53-US-01`'s own resolved
  clarifying-question block, not re-litigated here:** dedicated per
  capture type; in-process, same scheduled tick, no queue/staging between
  stages; a 4th "Linker" stage; partial-failure semantics — the WHOLE
  task fails end-to-end if any stage fails, with the upstream stage's own
  success record reverted; independent per-stage Working Mode; Puller/
  Tagger = Worker, Storer = Producer (Linker's Type — see `## Notes`,
  same open question `REQ-SB-53-US-01` flagged, not re-flagged
  independently here).
- **`todo-capture` is RETIRED by this story**, replaced by its own
  4-stage chain. Proposed (not locked) agent ids: `todo-puller`,
  `todo-tagger`, `todo-linker`, `todo-storer`.
- **Builds directly on `REQ-SB-53-US-01`'s own generic mechanism** (multi-
  agent history attribution across a pipeline, partial-failure rollback,
  independent per-stage Working Mode composing with the existing
  `skill_registry` gate, Background Agent inheritance) — this story
  applies that already-designed mechanism to To-Do's own real fetch →
  classify → link-customer-only → write shape; it does not redesign the
  mechanism itself. Should not be planned into tasks until
  `REQ-SB-53-US-01`'s own architecture (and any resulting ADR) is
  established (see Dependencies).
- **To-Do-specific divergence worth naming explicitly:** To-Do's own
  dedup mechanism is EntryID-keyed via `task_note_index.json`, consulted
  BEFORE any filename is computed (`REQ-SB-09-US-01`/`ADR-027`'s own
  established, empirically-EntryID-stability-confirmed design) — a
  genuine divergence from Meeting's recompute-and-`exists()`-check
  mechanism. This story preserves whichever real dedup mechanism To-Do
  already uses; it does not change To-Do's dedup semantics, only which
  agent identity performs each step.
  `background_agent_registry.py::_DEFAULT_BACKGROUND_AGENT_IDS` also
  hardcodes `todo-capture` in its 3-id exception set — the same
  Background Agent inheritance requirement `REQ-SB-53-US-01` established
  for Email applies here: the 4 new To-Do-stage agents must inherit
  `todo-capture`'s own exclusion from Hub-routing/Cockpit `@mention`.
- No `html-prototype/` screen is touched by this story — same reasoning
  as `REQ-SB-53-US-01`/`US-02` (every UI surface that renders agents is
  already agent-count-agnostic). This story does not touch My Day's
  To-Do drill-down (`REQ-SB-09-US-01`'s own read-path scope) — only the
  capture pipeline's internal agent structure changes; the resulting Task
  notes are byte-for-byte the same shape My Day already reads.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A real captured task produces 4 separate, attributed agent history entries

```gherkin
Given an item exists in Outlook's Tasks folder that has not yet produced
    a Task note
When the scheduled capture run processes it through the To-Do pipeline
Then 4 separate communication-history entries are produced for that
    item's run — one attributed to todo-puller's own agent_id, one to
    todo-tagger's, one to todo-linker's, and one to todo-storer's — not
    one monolithic history entry
  And the task ends up captured with the SAME real-world outcome as
    today's single-function implementation: a Task note correctly
    classified by customer (via Compass, when a match exists), correctly
    linked to its matched customer hub (when applicable), and correctly
    written into the vault
```

### Scenario 2: todo-capture no longer exists as a separate agent

```gherkin
Given this story has shipped
When the list of known agents is queried
Then todo-capture no longer appears as its own agent — it has been fully
    replaced by todo-puller, todo-tagger, todo-linker, and todo-storer
  And no code path still references todo-capture as a live agent id
```

### Scenario 3: The 4-stage pipeline runs in one atomic pass, on the same existing schedule

```gherkin
Given the existing scheduled capture trigger fires (hourly, once on app
    start, or a missed-run catch-up)
When that trigger fires
Then all 4 To-Do stages run in-process, in the same call chain, for
    every fetched Outlook Task item — no stage waits on an independently-
    scheduled trigger of its own
  And no new, separate schedule was added specifically for any one of the
    4 stages
```

### Scenario 4: A downstream-stage failure rolls back the upstream stage's own success record for that item

```gherkin
Given an Outlook Task is fetched successfully (Pull succeeds) and
    classified successfully (Tag succeeds, a customer match is found),
    but the Link stage then fails for that same item (e.g. a
    customer-hub-linking error)
When the pipeline finishes processing that item for this run
Then the whole item is treated as failed end-to-end for this run — Tag's
    own history entry for that specific item is marked failed/reverted,
    even though classification itself completed without error
  And Store never runs for that item — no Task note is created or topped
    up for it this run
  And the item is retried as a whole (from Pull onward) on the next
    scheduled run
```

### Scenario 5: Each of the 4 stages has its own independent Working Mode setting

```gherkin
Given the Settings surface where an agent's Working Mode is configured
When the user views todo-puller, todo-tagger, todo-linker, and
    todo-storer
Then each of the 4 has its own separate Working Mode control
    (Autonomous | Supervised | Manual), independently settable
```

### Scenario 6: A Supervised stage creates a real Pending Approval before acting, while Autonomous stages ahead of it complete normally

```gherkin
Given todo-puller, todo-tagger, and todo-linker are set to Autonomous,
    and todo-storer is set to Supervised
When the scheduled capture run processes a new Outlook Task item
Then Pull, Tag, and Link all run and complete without requiring approval
  And when the pipeline reaches Store, a real Pending Approval is created
    (attributed to todo-storer) instead of the Task note being
    created/topped-up immediately
  And the Task note is only created/topped-up once a human approves that
    pending approval
```

### Scenario 7: A Manual-mode stage leaves that item dormant, and no downstream stage acts on it

```gherkin
Given one of the 4 stages (e.g. todo-storer) is set to Manual working
    mode
When the scheduled capture run reaches that stage for a given item
Then that stage takes no action for that item this run — no vault
    write, no Pending Approval, no history entry for it
  And any stage downstream of it acts no further either, once its own
    upstream input is unavailable
```

### Scenario 8: Existing agent-count-agnostic downstream surfaces work unmodified with the 4 new agents

```gherkin
Given todo-puller, todo-tagger, todo-linker, and todo-storer now exist
    as real agents
When the user views the Agents Map, the Cockpit's @mention/bring-in
    candidate list, or a Background-Agent-eligibility check
Then all 4 new agents render/behave correctly with zero bespoke,
    per-agent-count code required
  And all 4 inherit the same Background Agent status the retired
    todo-capture agent had — none of the 4 appears as a Hub-routing
    candidate or a Cockpit @mention/bring-in option
```

## Affected Screens

None — backend only. Same reasoning as `REQ-SB-53-US-01`/`US-02`: every
UI surface this story touches already renders agents/settings
generically, and My Day's To-Do drill-down (`REQ-SB-09-US-01`) continues
to read the same Task-note shape unchanged.

## Dependencies

- **Blocked by:** `REQ-SB-53-US-01` — reuses that story's own generic
  multi-stage pipeline mechanism (rollback semantics, per-stage Working
  Mode wiring, Background Agent inheritance pattern, any resulting ADR).
  Should not be planned into tasks until `REQ-SB-53-US-01`'s own
  architecture is established.
- **Related to:** `REQ-SB-09` (`Done`) — the real To-Do-capture
  implementation this story splits, including its own established
  EntryID-keyed dedup mechanism (`ADR-027`) and Task-note schema.
- **Related to:** `REQ-SB-07`, `REQ-SB-11`, `REQ-SB-21`, `REQ-SB-39`,
  `REQ-SB-38`, `REQ-SB-51` — same relationships `REQ-SB-53-US-01` names
  for Email, one layer over for To-Do.
- **Related to:** `REQ-SB-53-US-02` (Meetings) — sibling story, same
  mechanism.
- **External:** none beyond the already-live Outlook COM / Compass
  integrations this pipeline already uses today.

## Constraints

- **No behavior regression.** The end-to-end real-world outcome for a
  captured task (customer classification, customer-hub linking, Task-note
  content, My Day's To-Do drill-down read path) must stay identical to
  today's single-function `classify_recent_todos` implementation.
- **In-process only, this pass** — same constraint as `REQ-SB-53-US-01`.
- **Type assignment:** Puller = Worker, Tagger = Worker, Storer =
  Producer (locked). **Linker's Type is NOT locked** — do not silently
  default it; the human decision in `REVIEW-QUEUE.md` (shared across all
  3 `REQ-SB-53` stories) must be resolved first.
- **Partial-failure rollback outcome is locked (Scenario 4); the
  implementation mechanism reuses whatever `REQ-SB-53-US-01` establishes**
  — do not design a second, divergent rollback mechanism for To-Do.
- Must preserve To-Do's own existing EntryID-keyed dedup mechanism
  (`task_note_index.json`, consulted before any filename is computed,
  per `ADR-027`) — this story does not change WHAT dedup key To-Do uses,
  only which agent identity performs each pipeline step.
- Must register all 4 new agent ids with `working_mode_registry.py`'s
  existing self-healing default with zero migration step.
- Must extend `background_agent_registry.py`'s exclusion to the 4 new
  agent ids (Scenario 8).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).
- This work runs against the user's real, live Outlook desktop and
  Obsidian vault (`VAULT_PATH`) — not a fixture/mocked Tasks folder.

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-53-US-03-T01 | backend | New `todo-puller`/`todo-tagger`/`todo-linker`/`todo-storer` seed agents; retire `todo-capture` | `app/business/agent_registry.py` | `../Tasks/REQ-SB-53-US-03-T01-todo-agent-registry-split.md` |
| REQ-SB-53-US-03-T02 | backend | Split `classify_recent_todos` into 4 attributed stage functions with per-stage Working Mode gating and multi-agent history attribution, reusing `REQ-SB-53-US-01`'s established mechanism | `app/business/todo_classification.py` | `../Tasks/REQ-SB-53-US-03-T02-todo-pipeline-stage-split.md` |
| REQ-SB-53-US-03-T03 | backend | Background Agent exclusion extended to the 4 new agent ids | `app/business/background_agent_registry.py` | `../Tasks/REQ-SB-53-US-03-T03-background-agent-inheritance.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **A real, persisted queue/staging architecture** — same as
  `REQ-SB-53-US-01`, explicitly declined by the operator.
- **Redesigning the multi-stage pipeline/rollback mechanism** — reuses
  `REQ-SB-53-US-01`'s own established design.
- **Changing To-Do's own dedup mechanism or Task-note schema** — out of
  scope; this is a re-attribution of WHO performs each step, not a change
  to `ADR-027`'s established WHAT.
- **A Person-note linking step for To-Do's Linker** — Outlook Tasks have
  no attendee/sender list; `REQ-SB-09-US-01`'s own established schema
  choice (no Person link for Task notes) is unchanged here.
- **A `/design` pass for Agents Map visual density** — same disclosed,
  non-blocking follow-on named by `REQ-SB-53-US-01`.
- **Locking Linker's agent Type** — genuinely open, same question
  `REQ-SB-53-US-01` flagged (see Notes).

## Notes

**Why this is flagged (MUST-FLAG triggers 1, 8) — same question as
`REQ-SB-53-US-01`/`US-02`, not independently re-derived here.** Linker's
agent Type (Worker/Expert/Producer) is left open by the PRD itself; this
story does not silently default `todo-linker` to Producer. See
`REQ-SB-53-US-01`'s own `## Notes` for the full reasoning — it applies
identically here.

No other trigger fired: no ADR was created or changed by this analyst
pass; the requirement text carries no `<!-- Draft -->` marker; no
`ESCALATIONS.md` entry was written (this is a forward scoping question
the PRD itself names as open, not a backward/out-of-scope event); this
story is reasonably sized on its own (3 tasks, reusing an already-designed
mechanism rather than inventing a second one, and with a genuinely
narrower Link stage than its siblings); no contradictory PRD inputs
exist.

`REVIEW-QUEUE.md` carries ONE shared entry covering all 3 `REQ-SB-53`
sibling stories for the Linker-Type decision — resolving it once resolves
it for `email-linker`, `meeting-linker`, and `todo-linker` together.

---

**Architect pass, 2026-08-15 (`/plan-tasks` step 1).** `ADR-040`
(`Implementation/Architecture/ADR.md`) — written against `REQ-SB-53-US-01`
(Email), this story's own blocking dependency — establishes the generic
mechanism this story reuses unchanged: a new shared, capture-type-agnostic
`app/business/capture_pipeline.py` orchestration engine (mirroring the
Cockpit's own `app/business/cockpit/` shared-package precedent, `ADR-036`);
a per-stage, per-tick, batch-level working-mode gate generalizing `ADR-018`
point 4's already-Accepted 2-block background-tick gate to 4 blocks, never
routed through `skill_registry.invoke_skill`; partial-failure rollback via
a buffered/deferred per-item history commit (a new additive `"reverted"`
history kind, never an immediate-write-then-mutate — history stays
append-only per `ADR-018` point 7); and Supervised-stage suspension/
resumption via one new `pending_approvals_router.py` Approve branch reusing
`trigger="background"`'s existing per-tick idempotency-dedup guard. This
story applies that same engine to To-Do's own real fetch → classify-via-
Compass → link-customer-only (no Person linking, `ADR-027`'s established
schema) → write shape (`todo-puller`/`todo-tagger`/`todo-linker`/
`todo-storer`), preserving To-Do's own real divergences from Email/Meeting
(EntryID-keyed dedup consulted before any filename is computed, per
`ADR-027`; a narrower Link stage with no attendee/Person-note linking)
entirely inside `todo_classification.py`'s own 4 stage functions — the
shared engine itself needs no To-Do-specific branch or change. No second,
divergent mechanism was designed here.

**Architecture scope: `architecture.md` → "Capture Pipeline Split —
Pull/Tag/Link/Store Agent Stages", plus `§ ADR-005`, `§ ADR-011`/
`§ ADR-018`, `§ ADR-020`/`§ ADR-029` (confirmed untouched), `§ ADR-027`
(To-Do's own EntryID dedup, preserved unchanged), `§ ADR-030`,
`§ ADR-036`.** The decomposer is bounded to these sections plus `ADR-040`
itself for this story's own tasks.

**Gating:** `gate: flagged` (frontmatter updated), trigger-3 — `ADR-040`
was created by this same architect pass (against the sibling `US-01`
story); this story's own tasks are reviewed alongside it in the same
`REVIEW-QUEUE.md` entry. Does not halt the pipeline — the decomposer runs
next. No `ESCALATIONS.md` entry — forward work, no contradiction with any
`Accepted` ADR, the PRD, or a `MEMORY.md` constraint.

**Update, 2026-08-15 — mid-flow reconsideration (`ESCALATIONS.md` →
`ESC-036`).** The operator directly asked, before the decomposer ran,
whether `ADR-040`'s hand-rolled mechanism should instead adopt LangGraph's
checkpointer + `interrupt()` primitive (`langgraph` is already installed,
`ADR-015` — not a new-dependency question). Reconsidered and confirmed
rejected — `ADR-040` is unchanged, this story's own reused mechanism is
unaffected. Full reasoning is recorded once, in `ADR-040`'s own
Alternatives Considered section and `REQ-SB-53-US-01`'s own Notes, not
re-derived here — same "resolve once, reference from siblings" pattern
this story already uses for the Linker-Type question, above.
