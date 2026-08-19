---
id: REQ-SB-53-US-02
title: Meeting capture split into Puller/Tagger/Linker/Storer agents, replacing the monolithic meeting-capture Worker
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

# REQ-SB-53-US-02 — Meeting capture split into Puller/Tagger/Linker/Storer agents, replacing the monolithic meeting-capture Worker

## Story

**As a** Second Brain user
**I want** the Meetings capture pipeline's internal steps (fetch from the
Outlook calendar, derive a customer via attendee majority vote, link
attendee/customer notes, write the Meeting note) to run as 4 separate,
individually-visible, individually-addressable agents instead of one
opaque `meeting-capture` Worker
**So that** I can see exactly which stage of a meeting-capture run
succeeded or failed for a given event, and configure each stage's own
automation level independently, without losing any of today's
meeting-capture behavior

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-53: Split Capture Pipelines into
  Staged Pull / Tag / Link / Store Agents*. The PRD's own comment block
  states Meetings has "the same real Pull/Tag/Link/Store shape" as Email,
  without naming Meeting's own functions line-by-line — this story
  confirms that mapping directly against the real, current
  `app/business/meeting_classification.py::classify_recent_meetings`:
  - **Pull:** `outlook_com.list_calendar_events(days_back, days_ahead,
    limit)` — fetch calendar events in the sync window.
  - **Tag:** `_exclude_self(...)` (filters `settings.self_email` from the
    attendee list before any customer derivation) +
    `_derive_meeting_customer(...)` — majority vote among attendee
    companies via `people_extraction.derive_company_from_email`/
    `find_matching_customer`, ties broken by first-seen attendee order.
    Unlike Email's Tag stage, this is deterministic rule-based derivation,
    not a Compass call — still the same conceptual "classify by customer"
    role in the pipeline.
  - **Link:** `people_extraction.ensure_person_note(...)` per (post-
    exclusion) attendee + `vault_writer.upsert_attendee_links(...)`,
    `customer_hub_linking.ensure_customer_hub_note(...)` +
    `link_note_to_customer_hub(...)` when a customer was matched.
  - **Store:** `vault_writer.resolve_meeting_note_path(...)`,
    `create_meeting_note_baseline(...)`/
    `ensure_meeting_note_baseline_frontmatter(...)` (idempotent
    create-or-top-up), `mark_meeting_processed(...)`.
  Verified directly against the real current file — not assumed.
- **Locked inputs — identical to `REQ-SB-53-US-01`'s own resolved
  clarifying-question block, not re-litigated here:** dedicated per
  capture type; in-process, same scheduled tick, no queue/staging between
  stages; a 4th "Linker" stage; partial-failure semantics — the WHOLE
  meeting fails end-to-end if any stage fails, with the upstream stage's
  own success record reverted; independent per-stage Working Mode; Puller/
  Tagger = Worker, Storer = Producer (Linker's Type — see `## Notes`,
  same open question `REQ-SB-53-US-01` flagged, not re-flagged
  independently here).
- **`meeting-capture` is RETIRED by this story**, replaced by its own
  4-stage chain. Proposed (not locked) agent ids: `meeting-puller`,
  `meeting-tagger`, `meeting-linker`, `meeting-storer`.
- **Builds directly on `REQ-SB-53-US-01`'s own generic mechanism** (multi-
  agent history attribution across a pipeline, partial-failure rollback,
  independent per-stage Working Mode composing with the existing
  `skill_registry` gate, Background Agent inheritance) — this story
  applies that already-designed mechanism to Meeting's own real fetch →
  derive-customer → link-attendees → write shape; it does not redesign
  the mechanism itself. Should not be planned into tasks until
  `REQ-SB-53-US-01`'s own architecture (and any resulting ADR) is
  established (see Dependencies).
- **Meeting-specific divergences from Email worth naming explicitly:**
  Meeting's own Tag stage derives customer via a deterministic majority
  vote over attendees, not a Compass/LLM call — the 4-stage split does
  not change this; Tag is still the "classify by customer" stage
  regardless of mechanism. Meeting's own dedup/top-up mechanism
  (`resolve_meeting_note_path`'s deterministic-filename check, not an
  EntryID-keyed lookup) is a real, already-established divergence from
  Email's own `mark_email_processed`-by-EntryID dedup — this story
  preserves whichever real dedup mechanism Meeting already uses; it does
  not change Meeting's dedup semantics, only which agent identity performs
  each step.
  `background_agent_registry.py::_DEFAULT_BACKGROUND_AGENT_IDS` also
  hardcodes `meeting-capture` in its 3-id exception set — the same
  Background Agent inheritance requirement `REQ-SB-53-US-01` established
  for Email applies here: the 4 new Meeting-stage agents must inherit
  `meeting-capture`'s own exclusion from Hub-routing/Cockpit `@mention`.
- No `html-prototype/` screen is touched by this story — same reasoning
  as `REQ-SB-53-US-01` (every UI surface that renders agents is already
  agent-count-agnostic).

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A real captured meeting produces 4 separate, attributed agent history entries

```gherkin
Given a new calendar event exists in the sync window that has not yet
    produced a Meeting note
When the scheduled capture run processes it through the Meeting pipeline
Then 4 separate communication-history entries are produced for that
    event's run — one attributed to meeting-puller's own agent_id, one to
    meeting-tagger's, one to meeting-linker's, and one to
    meeting-storer's — not one monolithic history entry
  And the meeting ends up captured with the SAME real-world outcome as
    today's single-function implementation: a Meeting note correctly
    classified by customer (via attendee majority vote, self-excluded),
    correctly linked (attendee Person notes, customer hub link when
    matched), and correctly written into the vault
```

### Scenario 2: meeting-capture no longer exists as a separate agent

```gherkin
Given this story has shipped
When the list of known agents is queried
Then meeting-capture no longer appears as its own agent — it has been
    fully replaced by meeting-puller, meeting-tagger, meeting-linker, and
    meeting-storer
  And no code path still references meeting-capture as a live agent id
```

### Scenario 3: The 4-stage pipeline runs in one atomic pass, on the same existing schedule

```gherkin
Given the existing scheduled capture trigger fires (hourly, once on app
    start, or a missed-run catch-up)
When that trigger fires
Then all 4 Meeting stages run in-process, in the same call chain, for
    every fetched calendar event — no stage waits on an independently-
    scheduled trigger of its own
  And no new, separate schedule was added specifically for any one of the
    4 stages
```

### Scenario 4: A downstream-stage failure rolls back the upstream stage's own success record for that item

```gherkin
Given a calendar event is fetched successfully (Pull succeeds) and its
    customer derived successfully (Tag succeeds), but the Link stage then
    fails for that same event (e.g. an attendee Person-note-linking
    error)
When the pipeline finishes processing that event for this run
Then the whole event is treated as failed end-to-end for this run —
    Tag's own history entry for that specific event is marked
    failed/reverted, even though customer derivation itself completed
    without error
  And Store never runs for that event — no Meeting note is created or
    topped up for it this run
  And the event is retried as a whole (from Pull onward) on the next
    scheduled run
```

### Scenario 5: Each of the 4 stages has its own independent Working Mode setting

```gherkin
Given the Settings surface where an agent's Working Mode is configured
When the user views meeting-puller, meeting-tagger, meeting-linker, and
    meeting-storer
Then each of the 4 has its own separate Working Mode control
    (Autonomous | Supervised | Manual), independently settable
```

### Scenario 6: A Supervised stage creates a real Pending Approval before acting, while Autonomous stages ahead of it complete normally

```gherkin
Given meeting-puller, meeting-tagger, and meeting-linker are set to
    Autonomous, and meeting-storer is set to Supervised
When the scheduled capture run processes a new calendar event
Then Pull, Tag, and Link all run and complete without requiring approval
  And when the pipeline reaches Store, a real Pending Approval is created
    (attributed to meeting-storer) instead of the Meeting note being
    written/topped-up immediately
  And the Meeting note is only created/topped-up once a human approves
    that pending approval
```

### Scenario 7: A Manual-mode stage leaves that item dormant, and no downstream stage acts on it

```gherkin
Given one of the 4 stages (e.g. meeting-linker) is set to Manual working
    mode
When the scheduled capture run reaches that stage for a given event
Then that stage takes no action for that event this run — no vault
    write, no Pending Approval, no history entry for it
  And no stage downstream of it (Store) acts on that same event this run
    either
```

### Scenario 8: Existing agent-count-agnostic downstream surfaces work unmodified with the 4 new agents

```gherkin
Given meeting-puller, meeting-tagger, meeting-linker, and meeting-storer
    now exist as real agents
When the user views the Agents Map, the Cockpit's @mention/bring-in
    candidate list, or a Background-Agent-eligibility check
Then all 4 new agents render/behave correctly with zero bespoke,
    per-agent-count code required
  And all 4 inherit the same Background Agent status the retired
    meeting-capture agent had — none of the 4 appears as a Hub-routing
    candidate or a Cockpit @mention/bring-in option
```

## Affected Screens

None — backend only. Same reasoning as `REQ-SB-53-US-01`: every UI
surface this story touches already renders agents/settings generically.

## Dependencies

- **Blocked by:** `REQ-SB-53-US-01` — reuses that story's own generic
  multi-stage pipeline mechanism (rollback semantics, per-stage Working
  Mode wiring, Background Agent inheritance pattern, any resulting ADR).
  Should not be planned into tasks until `REQ-SB-53-US-01`'s own
  architecture is established.
- **Related to:** `REQ-SB-08` (`Done`) — the real Meeting-capture
  implementation this story splits.
- **Related to:** `REQ-SB-07`, `REQ-SB-11`, `REQ-SB-21`, `REQ-SB-39`,
  `REQ-SB-38`, `REQ-SB-51` — same relationships `REQ-SB-53-US-01` names
  for Email, one layer over for Meeting.
- **Related to:** `REQ-SB-53-US-03` (To-Do) — sibling story, same
  mechanism.
- **External:** none beyond the already-live Outlook COM integration this
  pipeline already uses today.

## Constraints

- **No behavior regression.** The end-to-end real-world outcome for a
  captured meeting (customer derivation, attendee/customer linking,
  Meeting-note content) must stay identical to today's single-function
  `classify_recent_meetings` implementation.
- **In-process only, this pass** — same constraint as `REQ-SB-53-US-01`.
- **Type assignment:** Puller = Worker, Tagger = Worker, Storer =
  Producer (locked). **Linker's Type is NOT locked** — do not silently
  default it; the human decision in `REVIEW-QUEUE.md` (shared across all
  3 `REQ-SB-53` stories) must be resolved first.
- **Partial-failure rollback outcome is locked (Scenario 4); the
  implementation mechanism reuses whatever `REQ-SB-53-US-01` establishes**
  — do not design a second, divergent rollback mechanism for Meeting.
- Must preserve Meeting's own existing dedup/top-up mechanism
  (`resolve_meeting_note_path`'s deterministic-filename check) — this
  story does not change WHAT dedup key Meeting uses, only which agent
  identity performs each pipeline step.
- Must register all 4 new agent ids with `working_mode_registry.py`'s
  existing self-healing default with zero migration step.
- Must extend `background_agent_registry.py`'s exclusion to the 4 new
  agent ids (Scenario 8).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).
- This work runs against the user's real, live Outlook desktop and
  Obsidian vault (`VAULT_PATH`) — not a fixture/mocked calendar.

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-53-US-02-T01 | backend | New `meeting-puller`/`meeting-tagger`/`meeting-linker`/`meeting-storer` seed agents; retire `meeting-capture` | `app/business/agent_registry.py` | `../Tasks/REQ-SB-53-US-02-T01-meeting-agent-registry-split.md` |
| REQ-SB-53-US-02-T02 | backend | Split `classify_recent_meetings` into 4 attributed stage functions with per-stage Working Mode gating and multi-agent history attribution, reusing `REQ-SB-53-US-01`'s established mechanism | `app/business/meeting_classification.py` | `../Tasks/REQ-SB-53-US-02-T02-meeting-pipeline-stage-split.md` |
| REQ-SB-53-US-02-T03 | backend | Background Agent exclusion extended to the 4 new agent ids | `app/business/background_agent_registry.py` | `../Tasks/REQ-SB-53-US-02-T03-background-agent-inheritance.md` |

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
  `REQ-SB-53-US-01`'s own established design; this story does not
  introduce a second, divergent mechanism.
- **Changing Meeting's own dedup/top-up mechanism** — out of scope; this
  is a re-attribution of WHO performs each step, not a change to WHAT
  dedup key or top-up logic Meeting uses.
- **A `/design` pass for Agents Map visual density** — same disclosed,
  non-blocking follow-on named by `REQ-SB-53-US-01`.
- **Locking Linker's agent Type** — genuinely open, same question
  `REQ-SB-53-US-01` flagged (see Notes).

## Notes

**Why this is flagged (MUST-FLAG triggers 1, 8) — same question as
`REQ-SB-53-US-01`, not independently re-derived here.** Linker's agent
Type (Worker/Expert/Producer) is left open by the PRD itself; this story
does not silently default `meeting-linker` to Producer. See
`REQ-SB-53-US-01`'s own `## Notes` for the full reasoning — it applies
identically here, since the PRD's own resolved clarifying-question block
covers all 3 capture types uniformly, not per-type.

No other trigger fired: no ADR was created or changed by this analyst
pass; the requirement text carries no `<!-- Draft -->` marker; no
`ESCALATIONS.md` entry was written (this is a forward scoping question
the PRD itself names as open, not a backward/out-of-scope event); this
story is reasonably sized on its own (3 tasks, reusing an already-designed
mechanism rather than inventing a second one); no contradictory PRD
inputs exist.

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
story applies that same engine to Meeting's own real fetch → derive-
customer-via-majority-vote → link-attendees/customer → write shape
(`meeting-puller`/`meeting-tagger`/`meeting-linker`/`meeting-storer`),
preserving Meeting's own real divergences from Email (deterministic
majority-vote Tag, not a Compass call; recompute-and-`exists()` dedup, not
EntryID-keyed) entirely inside `meeting_classification.py`'s own 4 stage
functions — the shared engine itself needs no Meeting-specific branch or
change. No second, divergent mechanism was designed here.

**Architecture scope: `architecture.md` → "Capture Pipeline Split —
Pull/Tag/Link/Store Agent Stages", plus `§ ADR-005`, `§ ADR-011`/
`§ ADR-018`, `§ ADR-020`/`§ ADR-029` (confirmed untouched), `§ ADR-030`,
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
