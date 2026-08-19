---
id: REQ-SB-53-US-01
title: Email capture split into Puller/Tagger/Linker/Storer agents, replacing the monolithic email-capture Worker
requirement_ids: [REQ-SB-53]
requirement_section: "REQ-SB-53: Split Capture Pipelines into Staged Pull / Tag / Link / Store Agents"
phase: P1
status: Draft
gate: flagged
gate_reason: "trigger-3 (ADR-040 created — Capture Pipeline Split mechanism)"
sprint: ""
created: 2026-08-15
updated: 2026-08-15
---

# REQ-SB-53-US-01 — Email capture split into Puller/Tagger/Linker/Storer agents, replacing the monolithic email-capture Worker

## Story

**As a** Second Brain user
**I want** the Email capture pipeline's internal steps (fetch from Outlook,
classify by customer/kind, derive links, write the vault note) to run as 4
separate, individually-visible, individually-addressable agents instead of
one opaque `email-capture` Worker
**So that** I can see exactly which stage of a capture run succeeded or
failed for a given email, configure each stage's own automation level
independently (e.g. auto-fetch and auto-classify, but require my approval
before anything actually lands in the vault), and get this without losing
any of today's email-capture behavior

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-53: Split Capture Pipelines into
  Staged Pull / Tag / Link / Store Agents*. This is the PRD's own worked
  example — its `<!-- Raised 2026-08-15 ... -->` comment block maps Email's
  real, existing implementation to the 4 new stages by reading
  `app/business/email_classification.py::classify_recent_emails` directly:
  - **Pull:** `outlook_com.list_recent_mail(limit)` — fetch raw messages.
  - **Tag:** `compass_client.classify_email(...)` — derive `customer`/
    `kind`/`confidence`.
  - **Link:** `vault_writer.find_related_note_stems(conversation_id)`
    (same-thread wikilinks), `customer_hub_linking.
    ensure_hub_note_and_link(...)`, `people_extraction.
    ensure_person_note_for_captured_email(...)` +
    `link_email_to_person(...)`.
  - **Store:** `vault_writer.write_note(...)`, `write_attachments(...)`,
    `mark_email_processed(...)`, `record_conversation_note(...)`.
  Verified directly against the real current file — the mapping above is
  accurate, not assumed.
- **Locked inputs from the PRD's own resolved clarifying-question
  block (2026-08-15) — not re-litigated here:**
  1. **Dedicated per capture type.** This story builds Email's own 4-agent
     chain only; Meetings and To-Do get their own sibling stories
     (`REQ-SB-53-US-02`, `REQ-SB-53-US-03`) — not one shared/generic
     Puller/Tagger/Linker/Storer set all 3 types route through.
  2. **In-process, same scheduled tick, no queue/staging between stages.**
     The 4 stages run inside ONE atomic pipeline pass per email, in the
     SAME call chain, on the SAME `capture_scheduler.py` trigger
     (`AsyncIOScheduler`, hourly + app-start) email-capture already runs
     on — not 4 independently-scheduled processes. They ARE 4 separate
     agent identities (own `agent_id`, own communication-history entries,
     own Agents Map node) for attribution/extensibility, never separate
     triggerable processes this pass.
  3. **Partial-failure semantics — the WHOLE item fails if any stage
     fails.** If Link fails after Tag already succeeded for a given email,
     the pipeline treats that email as failed end-to-end for the run —
     Tag's own history entry for that email is marked failed/reverted even
     though tagging itself worked in isolation, so a human reviewing Agent
     Activity sees ONE clear failure for that email, not a confusing
     split trail. Store never runs for that email; it is retried whole
     (from Pull) on the next scheduled run — same retry granularity as
     today. **The OUTCOME above is locked; the implementation mechanism
     (e.g. does Tag's history write happen only after the whole pipeline
     settles, or write-then-amend/supersede on downstream failure?) is
     left to `/plan-tasks`.**
  4. **Independent per-stage working mode.** Each of Puller/Tagger/
     Linker/Storer gets its OWN Working Mode setting in Settings, exactly
     like every other agent today (Autonomous/Supervised/Manual) — e.g.
     Puller and Tagger could run Autonomous while Storer is Supervised,
     requiring a human Approve on Pending Approvals before anything
     actually lands in the vault. This is 4 settings where today there was
     1, a disclosed increase in Settings surface area.
  5. **Type per stage.** Puller and Tagger are both Worker-type (the
     operator's own words). Storer maps to Producer (the stage that
     actually writes/maintains the vault note — this app's own definition
     of a Producer). **Linker's Type is NOT confirmed by the operator** —
     see `## Notes` for why this story is flagged rather than silently
     defaulting to the PRD's own suggested Producer.
- **`email-capture` is RETIRED by this story**, replaced by its own
  4-stage chain — not kept alongside as a 5th coordinator layer on top.
  Proposed (not locked) agent ids: `email-puller`, `email-tagger`,
  `email-linker`, `email-storer`.
- **Read directly, not assumed — real code this story touches or must
  stay compatible with:**
  - `app/business/agent_registry.py::_SEED_AGENTS` — `email-capture`'s own
    seed entry is removed/replaced by the 4 new seed entries.
  - `app/scheduling/capture_scheduler.py` — the existing hourly +
    app-start `AsyncIOScheduler` trigger calling
    `email_classification.run_capture_and_record_completion()` as one
    opaque unit; per the locked in-process decision above, this file needs
    zero structural change — the same trigger still fires one opaque
    pipeline call, now internally attributing its work across 4 agent
    identities instead of 1.
  - `app/business/working_mode_registry.py` — its self-healing
    `_load_state()` already folds in ANY agent id returned by
    `agent_registry.list_agents()` with zero code change, confirmed by
    direct reading; the 4 new agents get a default Working Mode
    (Autonomous) with no migration step, the same way every prior new
    agent id already has (`REQ-SB-37-US-01`'s own confirmed precedent).
  - `app/business/skill_registry.py::invoke_skill`/`_dispatch_skill` —
    today's two-axis working-mode gate (`ADR-020`/`ADR-029`) is a
    single-call gate: one agent, one Skill/action invocation, one
    Autonomous/Supervised/Manual check. This story's Storer stage running
    Supervised while Pull/Tag/Link run Autonomous is a genuinely NEW
    shape this gate has never composed with — a multi-stage pipeline
    where only SOME stages are gated, in sequence, with the pipeline's
    own downstream stages depending on an upstream stage's real output.
    **How the existing single-call gate mechanism composes correctly with
    a 4-stage, partial-failure-aware pipeline (per point 3 above) is a
    real design question left to `/plan-tasks` — not solved by this
    story**, which specifies the OBSERVABLE outcome only (Scenarios 5-7
    below).
  - `app/business/background_agent_registry.py::_DEFAULT_BACKGROUND_AGENT_IDS`
    — a literal, hardcoded 3-id exception set
    (`{"email-capture", "meeting-capture", "todo-capture"}`) that
    self-heals to `is_background_agent: True`, excluding these 3 agents
    from Hub-routing candidacy and Cockpit `@mention`/bring-in
    (`REQ-SB-51`). Once `email-capture` is retired, its replacement 4
    agents must inherit the SAME Background Agent status — otherwise they
    would newly appear as addressable/Hub-routable agents, a real,
    disclosed behavior change the PRD's own "no existing downstream
    consumer... needs bespoke per-agent-count logic" acceptance text rules
    out. The exact mechanism (extend the hardcoded set to the new ids, or
    a more general rule) is left to `/plan-tasks` (Scenario 8).
- No `html-prototype/` screen is touched by this story. Every UI surface
  that renders agents (Agents Map, Settings' Working Mode control, Pending
  Approvals, Agent Activity history) is already agent-count-agnostic —
  confirmed directly: `AgentsMapCanvas.tsx`/`layoutAgents.ts` iterate
  whatever `list_agents()` returns; `AgentDetailPanel.tsx`'s Working Mode
  control and History tab render per-agent generically; `REQ-SB-38-US-01`'s
  density clustering (`Done`) already handles an arbitrary, growing agent
  count with no hardcoded assumption. This story adds agents to those
  already-generic surfaces; it does not change any of them. The 4x-denser
  capture cluster this produces is a disclosed, non-blocking future
  `/design` concern (Agents Map visual density), not resolved here — see
  Non-Goals.

## Scoping decision (3 sibling stories, not 1)

REQ-SB-53 splits 3 existing monolithic Workers into 12 new agents total,
retires the 3 old ones, and requires a genuinely new pipeline/rollback/
gating mechanism — too large for one working context and one live-
verification pass. Per this codebase's own precedent for "one architectural
mechanism, applied per-type, with a real shared-infrastructure dependency"
(`REQ-SB-43-US-01`/`REQ-SB-44-US-01`'s Cockpit split; `REQ-SB-37`'s 3-way
Expert/Worker/Producer split), this requirement is split into 3 sibling
stories, each anchored on `REQ-SB-53`:

- **`REQ-SB-53-US-01` (this story) — Email.** Establishes the generic
  4-stage-agent-identity pipeline mechanism (multi-agent history
  attribution, partial-failure rollback semantics, independent per-stage
  Working Mode, Supervised-stage-creates-Pending-Approval composition with
  the existing gate, Background Agent inheritance) AND applies it to
  Email — the PRD's own worked example. Carries the PRD's mandatory real,
  live Outlook-backed capture run (Scenario 9) — satisfying the
  requirement's "confirmed via a real, live Outlook-backed capture run for
  at least one of the 3 types" acceptance clause.
- **`REQ-SB-53-US-02` — Meetings.** Reuses this story's own proven
  mechanism, applied to `meeting-capture`'s real fetch → derive-customer →
  link-attendees → write shape.
- **`REQ-SB-53-US-03` — To-Do.** Reuses this story's own proven mechanism,
  applied to `todo-capture`'s real fetch → classify → link-customer-only →
  write shape (no attendee/person linking — Outlook Tasks have no attendee
  list, per `REQ-SB-09-US-01`'s own established schema).

Each of the 3 sibling stories independently satisfies REQ-SB-53's
per-capture-type acceptance text once built; the requirement's own "no
existing downstream consumer breaks" and "3 previous monolithic agents no
longer exist" clauses are only FULLY satisfied once all 3 ship — `BACKLOG.md`
links all 3 stories against the one requirement row.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A real captured email produces 4 separate, attributed agent history entries

```gherkin
Given a new email exists in the Outlook mailbox that has not yet been
    captured
When the scheduled capture run processes it through the Email pipeline
Then 4 separate communication-history entries are produced for that
    email's run — one attributed to email-puller's own agent_id, one to
    email-tagger's, one to email-linker's, and one to email-storer's —
    not one monolithic history entry
  And the email ends up captured with the SAME real-world outcome as
    today's single-function implementation: a Task-equivalent Email note
    correctly classified by customer and kind, correctly linked (same-
    thread wikilinks, customer hub link, sender's Person-note link where
    applicable), and correctly written into the vault
```

### Scenario 2: email-capture no longer exists as a separate agent

```gherkin
Given this story has shipped
When the list of known agents is queried (e.g. via the Agents Map or
    GET /agents)
Then email-capture no longer appears as its own agent — it has been fully
    replaced by email-puller, email-tagger, email-linker, and email-storer
  And no code path still references email-capture as a live agent id
```

### Scenario 3: The 4-stage pipeline runs in one atomic pass, on the same existing schedule

```gherkin
Given the existing scheduled capture trigger fires (hourly, once on app
    start, or a missed-run catch-up, per REQ-SB-07's unchanged schedule)
When that trigger fires
Then all 4 Email stages run in-process, in the same call chain, for every
    fetched email — no stage waits on an independently-scheduled trigger
    of its own, and no separate queue/staging mechanism sits between
    stages
  And no new, separate schedule was added specifically for any one of the
    4 stages
```

### Scenario 4: A downstream-stage failure rolls back the upstream stage's own success record for that item

```gherkin
Given an email is fetched successfully (Pull succeeds) and classified
    successfully (Tag succeeds), but the Link stage then fails for that
    same email (e.g. a customer-hub-linking error)
When the pipeline finishes processing that email for this run
Then the whole email is treated as failed end-to-end for this run — Tag's
    own history entry for that specific email is marked failed/reverted,
    even though tagging itself completed without error in isolation
  And Store never runs for that email — no vault note is written for it
    this run
  And the email is retried as a whole (from Pull onward) on the next
    scheduled run, not resumed from the Link stage
  And a human reviewing this email's Agent Activity sees one clear
    failure for it, not a split trail of one success and one failure
    across two different agents
```

### Scenario 5: Each of the 4 stages has its own independent Working Mode setting

```gherkin
Given the Settings surface where an agent's Working Mode is configured
When the user views email-puller, email-tagger, email-linker, and
    email-storer
Then each of the 4 has its own separate Working Mode control
    (Autonomous | Supervised | Manual), independently settable — changing
    one stage's mode does not change any of the other 3
```

### Scenario 6: A Supervised stage creates a real Pending Approval before acting, while Autonomous stages ahead of it complete normally

```gherkin
Given email-puller, email-tagger, and email-linker are set to Autonomous,
    and email-storer is set to Supervised
When the scheduled capture run processes a new email
Then Pull, Tag, and Link all run and complete without requiring approval
  And when the pipeline reaches Store, a real Pending Approval is created
    (attributed to email-storer) instead of the vault note being written
    immediately
  And the vault note is only written once a human approves that pending
    approval, at which point the same real Store logic runs
```

### Scenario 7: A Manual-mode stage leaves that item dormant, and no downstream stage acts on it

```gherkin
Given one of the 4 stages (e.g. email-tagger) is set to Manual working
    mode
When the scheduled capture run reaches that stage for a given email
Then that stage takes no action for that email this run — no vault
    write, no Pending Approval, no history entry for it — mirroring
    today's single-agent "stays dormant" Manual-mode behavior
  And no stage downstream of it (e.g. Link, Store) acts on that same
    email this run either, since a later stage has nothing to work from
    until the Manual stage's own output exists
```

### Scenario 8: Existing agent-count-agnostic downstream surfaces work unmodified with the 4 new agents

```gherkin
Given email-puller, email-tagger, email-linker, and email-storer now
    exist as real agents
When the user views the Agents Map, the Cockpit's @mention/bring-in
    candidate list, or a Background-Agent-eligibility check
Then all 4 new agents render/behave correctly with zero bespoke,
    per-agent-count code required
  And all 4 inherit the same Background Agent status the retired
    email-capture agent had — none of the 4 appears as a Hub-routing
    candidate or a Cockpit @mention/bring-in option, the same exclusion
    email-capture itself had before retirement
```

### Scenario 9: A real, live Outlook-backed capture run produces the same correct final vault-note outcome as today

```gherkin
Given the real, live Outlook mailbox this project is configured against
    (VAULT_PATH-backed vault, not a mocked/simulated pipeline)
When a real scheduled or manually-triggered capture run processes real,
    genuinely new email through the 4-stage Email pipeline
Then the resulting Email note in the vault is classified, linked, and
    written correctly — byte-for-byte equivalent in outcome to what
    today's single-function email-capture implementation would have
    produced for the same email
  And the run's real communication-history activity shows all 4 stages'
    own attributed entries for that email, confirming the split pipeline
    genuinely executed, not just individually-tested pieces
```

## Affected Screens

None — backend only. Every UI surface this story touches (Agents Map,
Settings' Working Mode control, Pending Approvals list, Agent History)
already renders agents/settings generically for an arbitrary agent count —
see Context. No `html-prototype/` prototype reconciliation applies; this
story adds new agent entities to already-generic, already-approved UI, it
does not introduce or change any screen region.

## Dependencies

- **Related to:** `REQ-SB-07` (`Done`) — the recurring-schedule trigger
  (`capture_scheduler.py`) this pipeline still runs on, unchanged in
  structure.
- **Related to:** `REQ-SB-11` (`Done`) — the communication-history/Agent
  Activity mechanism this story attributes 4 stages' worth of entries
  into, instead of 1.
- **Related to:** `REQ-SB-21` (`Done`) — the Working Mode gate
  (`working_mode_registry.py`) this story extends to 4 independent
  settings per capture type instead of 1.
- **Related to:** `REQ-SB-39` (`Done`) — the Skill/Action working-mode gate
  (`skill_registry.invoke_skill`/`_dispatch_skill`, `ADR-020`/`ADR-029`)
  this story's Supervised-Storer scenario composes with; the exact
  composition mechanism for a multi-stage pipeline is a `/plan-tasks`
  design question (see Context).
- **Related to:** `REQ-SB-38` (`Done`) — Agents Map density clustering,
  already generic over agent count; absorbs the 4 new agents with no
  code change, though the resulting visual density is a disclosed future
  `/design` concern (see Non-Goals).
- **Related to:** `REQ-SB-51` (`Done`) — Background Agent exclusion; the
  4 new agents must inherit `email-capture`'s own exclusion (Scenario 8).
- **Blocks:** `REQ-SB-53-US-02` (Meetings), `REQ-SB-53-US-03` (To-Do) —
  both sibling stories reuse this story's own generic multi-stage
  pipeline mechanism (rollback semantics, per-stage Working Mode wiring,
  Background Agent inheritance pattern); they should not be planned into
  tasks until this story's architecture (and any resulting ADR) is
  established.
- **External:** none beyond the already-live Outlook COM / Compass
  integrations this pipeline already uses today.

## Constraints

- **No behavior regression.** The end-to-end real-world outcome for a
  captured email (classification, linking, vault-note content) must stay
  identical to today's single-function `classify_recent_emails`
  implementation — this is a structural refactor of WHO does the work and
  HOW it's attributed, not a change to WHAT gets captured or how it's
  classified/linked/written (Scenario 1, 9).
- **In-process only, this pass.** No persisted queue/staging mechanism
  between stages — a real queue/staging architecture (each stage
  independently triggerable on its own schedule) was explicitly declined
  by the operator as a separate, later, bigger follow-on (Scenario 3).
- **Type assignment:** Puller = Worker, Tagger = Worker, Storer = Producer
  (all locked by the PRD's own resolved clarifying-question block).
  **Linker's Type is NOT locked** — do not silently default it to
  Producer at `/plan-tasks`; the human decision in `REVIEW-QUEUE.md` must
  be resolved first (see Notes).
- **Partial-failure rollback outcome is locked (Scenario 4); the
  implementation mechanism is not.** `/plan-tasks` designs how the
  rollback is actually implemented (deferred history write vs.
  write-then-amend, etc.) — do not treat the PRD's own illustrative
  question as dictating the mechanism.
- Must register all 4 new agent ids with `working_mode_registry.py`'s
  existing self-healing default (Autonomous) with zero migration step,
  per the confirmed precedent (Context).
- Must extend `background_agent_registry.py`'s exclusion to the 4 new
  agent ids, so none of them newly appears as a Hub-routing candidate or
  Cockpit `@mention` option (Scenario 8).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).
- This work runs against the user's real, live Outlook desktop and
  Obsidian vault (`VAULT_PATH`) — Scenario 9's live-verification
  requirement is not satisfiable via a mocked/simulated pipeline.

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this, per this project's own established
precedent (e.g. REQ-SB-09-US-01). -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-53-US-01-T01 | backend | New `email-puller`/`email-tagger`/`email-linker`/`email-storer` seed agents; retire `email-capture` | `app/business/agent_registry.py` | `../Tasks/REQ-SB-53-US-01-T01-email-agent-registry-split.md` |
| REQ-SB-53-US-01-T02 | backend | Split `classify_recent_emails` into 4 attributed stage functions with per-stage Working Mode gating and multi-agent history attribution | `app/business/email_classification.py` | `../Tasks/REQ-SB-53-US-01-T02-email-pipeline-stage-split.md` |
| REQ-SB-53-US-01-T03 | backend | Partial-failure rollback mechanism (whole-item failure semantics across stages) | `app/business/email_classification.py` | `../Tasks/REQ-SB-53-US-01-T03-email-pipeline-rollback.md` |
| REQ-SB-53-US-01-T04 | backend | Background Agent exclusion extended to the 4 new agent ids | `app/business/background_agent_registry.py` | `../Tasks/REQ-SB-53-US-01-T04-background-agent-inheritance.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **A real, persisted queue/staging architecture** (each stage genuinely
  decoupled, running on its own independent schedule) — explicitly
  declined by the operator as a bigger, separate follow-on, not this
  pass's scope.
- **Meetings and To-Do capture pipeline splits** — `REQ-SB-53-US-02` and
  `REQ-SB-53-US-03`, sibling stories.
- **A `/design` pass for Agents Map visual density** at 4x the current
  capture-agent count — a real, disclosed follow-on concern named
  directly by the PRD, not blocking this story's backend scope.
- **Any new UI surface or screen change** — every touched surface is
  already agent-count-agnostic (see Affected Screens).
- **Locking Linker's agent Type** — genuinely open, flagged for a human
  decision (see Notes).

## Notes

**Why this is flagged (MUST-FLAG triggers 1, 8):**

The PRD's own `<!-- Raised 2026-08-15 ... -->` comment block resolves
every other real design question via direct operator clarifying-question
answers (dedicated-per-type, in-process pipeline, the 4th Linker stage,
partial-failure rollback outcome, independent per-stage working mode,
Puller/Tagger/Storer Type assignment) — those are treated as locked inputs
here, not re-litigated. The ONE thing the PRD itself explicitly leaves
open is **Linker's agent Type** (Worker / Expert / Producer):

> "Linker's Type is NOT confirmed by the operator and is left open here —
> Producer (it also touches/maintains the living document graph, arguably
> the same job as Storer just split in two) is a reasonable default, but
> this is exactly the kind of call the architect/decomposer should flag
> rather than silently assume, per this project's own MUST-FLAG list."

This story does not silently default Linker to Producer. **Trigger 1**
(material assumption) would fire if a default were picked without
flagging; **trigger 8** (multiple equally-valid options) fires because
Worker, Expert, and Producer are all structurally defensible readings —
Linker performs read-derivation work over existing vault entities (a
Worker-like "does a fetch/lookup step" shape), touches/extends the living
document graph (a Producer-like "maintains vault content" shape), and its
own output feeds a downstream Producer stage (an argument for treating it
as upstream, non-Producer work). No PRD text, code precedent, or resolved
clarifying answer favors one reading over the others.

**This same open question applies identically to `REQ-SB-53-US-02`'s and
`REQ-SB-53-US-03`'s own Linker agents** (`meeting-linker`, `todo-linker`)
— resolving it here (email-linker) resolves the naming convention for
all 3 sibling stories at once; each sibling story's own Notes references
this entry rather than re-flagging the identical question independently.

No other trigger fired: no ADR was created or changed by this analyst
pass (n/a — that is the architect's role at `/plan-tasks`); the
requirement text itself carries no `<!-- Draft -->` marker (trigger 2
n/a); no `ESCALATIONS.md` entry was written (trigger 4 n/a — this is a
forward scoping question the PRD itself explicitly names as open, not a
backward/out-of-scope event); the 3-way story split (Scoping decision,
above) keeps each individual story reasonably sized, mirroring this
project's own `REQ-SB-37`/`REQ-SB-43`/`REQ-SB-44` split precedents
(trigger 5 not fired at this granularity — `/plan-tasks` may still find
this story itself needs further task-level splitting, that is its own
call to make); no contradictory PRD inputs exist (trigger 7 n/a — the
PRD's own resolved block is internally consistent).

`REVIEW-QUEUE.md` carries one entry (below) asking the human to resolve
Linker's Type before `/plan-tasks` runs on any of the 3 `REQ-SB-53`
stories. Once resolved, reset `gate:` to `clear` on all 3 (or the human
may resolve it directly in this story's own Notes/Constraints, the same
pattern `REQ-SB-30-US-01`'s own retrofit-question resolution used).

**Resolved 2026-08-15 — Linker's Type is `Producer`.** Decided directly
(not by the operator via a fresh clarifying question — the PRD's own
text already argued the case thoroughly enough that re-asking would be
redundant ceremony): `email-linker`/`meeting-linker`/`todo-linker` are
all `type: "producer"`. Reasoning, weighing the same 3 readings this
Notes section laid out above: Linker's defining trait is that it
MODIFIES/EXTENDS the living vault document graph (writes wikilinks,
ensures hub notes exist, links Person notes) — the exact behavior this
app's own data model already defines Producer by ("maintains a living
document"). Its read-derivation work (finding related note stems,
looking up known customers) is incidental to that goal, not its own
purpose, unlike a true Worker (whose whole job IS the fetch/capture
step) — so the Worker reading is the weaker of the two live candidates.
Ring placement follows automatically: Producer is innermost (closest to
the KB), which is visually apt — Linker's output feeds directly into the
KB-adjacent Storer stage. This also means, per capture type, the Pull/Tag
stages are Worker-type and the Link/Store stages are BOTH Producer-type
— two distinct Producer agents in sequence, not a naming collision (they
have different `agent_id`s and different jobs, same as any two Workers
already coexist today, e.g. `email-capture`/`meeting-capture`).
`gate: clear` on all 3 `REQ-SB-53` stories as of this resolution;
`REVIEW-QUEUE.md`'s shared entry is removed. Eligible for `/plan-tasks`.

---

**Architect pass, 2026-08-15 (`/plan-tasks` step 1).** Wrote `ADR-040`
(`Implementation/Architecture/ADR.md`), resolving both design questions
this story's own Context left open: (1) partial-failure rollback is a
**buffered/deferred per-item history commit** — each item's per-stage
outcomes are held in memory until its fate for the tick is known; a full
success commits one real `"run_event"` entry per stage, a downstream
failure commits `"run_error"` for the failing stage and a new, additive
`"reverted"` kind for every earlier stage that item had already
tentatively passed (never an immediate-write-then-mutate — history stays
append-only, per `ADR-018` point 7); (2) the existing single-call
`skill_registry.invoke_skill` gate is **not** reused or modified at all —
these 4 stages are gated exactly like `ADR-018` point 4's already-Accepted
whole-pipeline background-tick gate (a direct `working_mode_registry`
check per stage, per tick, batch-level, never through `invoke_skill`),
generalized from 2 explicit blocks to 4. A Supervised stage creates ONE
Pending Approval per tick covering the whole batch reaching it (reusing
`trigger="background"`'s existing idempotency-dedup guard verbatim), with
a new `payload.pipeline_resume` shape and one new `pending_approvals_
router.py` Approve branch that resumes the pipeline from the approved
stage onward — a downstream stage may cascade a second approval if it is
also Supervised, which is intended. A new, shared, capture-type-agnostic
`app/business/capture_pipeline.py` provides this generic 4-stage
orchestration/history/rollback/gate-composition engine (mirroring the
Cockpit's own `app/business/cockpit/` shared-package precedent, `ADR-036`)
— each capture type's own real Pull/Tag/Link/Store business logic stays
inside its own existing file (`email_classification.py`, etc.), plugged
into the shared engine as 4 plain stage functions; the engine itself never
contains any capture-type-specific logic. Full reasoning, alternatives
considered (including why per-item approval granularity and routing
through `invoke_skill` were both rejected), and consequences: `ADR-040`.

**Architecture scope: `architecture.md` → "Capture Pipeline Split —
Pull/Tag/Link/Store Agent Stages" (§ new, inserted after "Per-Agent
Scheduler & Shared Outlook-COM Dispatch Lock"), plus the already-referenced
`§ ADR-005` (scheduler layering), `§ ADR-011`/`§ ADR-018` (history/
working-mode gate), `§ ADR-020`/`§ ADR-029` (Skills gate — confirmed
untouched), `§ ADR-030` (agent registry), `§ ADR-036` (Cockpit shared-module
precedent this pass follows).** The decomposer is bounded to these
sections plus `ADR-040` itself — no other architecture area is in scope
for this story's tasks.

**Gating:** per Pipeline.md hard rule / MUST-FLAG trigger 3, creating
`ADR-040` sets `gate: flagged` on all 3 `REQ-SB-53` sibling stories
(frontmatter updated on each) with a shared `REVIEW-QUEUE.md` entry — this
does **not** halt the pipeline; the decomposer still runs immediately
after this pass so the human reviews `ADR-040` and the resulting tasks
together in one pass. No `ESCALATIONS.md` entry was written — this is a
forward architectural decision, not a backward step or an ADR deviation;
nothing in `ADR-040` contradicts an existing `Accepted` ADR, the PRD, or a
`MEMORY.md` constraint (confirmed directly: no staging/promotion gate is
introduced — the buffered history commit is an in-memory-only, same-tick
mechanism, never a persisted staging layer between stages).

**Update, 2026-08-15 — mid-flow reconsideration (`ESCALATIONS.md` →
`ESC-036`).** Before the decomposer ran, the operator directly asked
whether `ADR-040`'s own hand-rolled suspension/rollback mechanism should
instead be built on LangGraph's checkpointer + `interrupt()`/human-in-the-
loop primitive — `langgraph` is already a real, installed dependency
(`ADR-015`), so this was a genuine "which mechanism," not "which
dependency" question. Reconsidered directly, concretely, against this
project's own already-Accepted precedent (`ADR-015` point 6's own
Alternatives Considered already rejected a LangGraph checkpointer for
conversation state on identical grounds; its own Consequences explicitly
flagged this exact future scenario and left it to `REQ-SB-21`'s later pass,
which became `ADR-018` and built the hand-rolled Pending Approval
mechanism this ADR is the third reuse of) — **`ADR-040` is unchanged**;
the mechanism stays fully hand-rolled. Full reasoning (4 concrete points:
already-declined precedent, cross-restart durability needing a new SQLite
checkpointer this project has repeatedly rejected, zero dynamic/LLM-driven
branching for a graph engine to manage, and a checkpointer duplicating
rather than replacing the hand-rolled Pending-Approval bridging code) is
now recorded directly in `ADR-040`'s own Alternatives Considered section,
not just this Notes summary. This retroactively updates the "No
`ESCALATIONS.md` entry was written" line above — that was true of the
original architect pass; `ESC-036` was appended by this later
reconsideration, triggered by direct operator question, per `Pipeline.md`
hard rule 6. `gate` stays `flagged` (unchanged) — the reconsideration
confirms rather than revises the reviewable decision.
