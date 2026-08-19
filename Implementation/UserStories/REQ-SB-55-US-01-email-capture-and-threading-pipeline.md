---
id: REQ-SB-55-US-01
title: Email Capture & Threading Pipeline — Fetch/Classify/Thread-Match-Merge/Route-to-Project, attachment summarization, recurring-pattern detection
requirement_ids: [REQ-SB-55]
requirement_section: "REQ-SB-55: Email Capture & Threading Pipeline"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-043 created) — architect pass, /plan-tasks step 1, carried through the decomposer pass. This story's own design questions were already fully resolved before the architect pass (see the original gate: clear reasoning preserved verbatim in ## Notes below); no NEW decomposer-owned trigger fired on this pass — all 9 Gherkin scenarios locked as AC-01..AC-09, every locked AC has at least one AC-tagged verification step across the 8 task files below, depends_on is acyclic (T01→T02 independent roots; T03 depends on T01; T04/T05 depend on T01+T03; T06 depends on T02+T04; T07 depends on T03/T04/T05/T06; T08 depends on T07), all 8 tasks set to status: Ready alongside this story. Human reviews ADR-043 and this task breakdown together in one pass, per Pipeline.md's gating contract — gate stays flagged as a standing breadcrumb even though status is Ready (status and gate are independent axes, same shape as REQ-SB-54-US-01/REQ-SB-49-US-02)."
sprint: "SPRINT-049"
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-55-US-01 — Email Capture & Threading Pipeline — Fetch/Classify/Thread-Match-Merge/Route-to-Project, attachment summarization, recurring-pattern detection

## Story

**As a** Second Brain user
**I want** captured email to merge into one running Thread note per
conversation, get routed (with my approval) to the right Project, have
attachments summarized as their own dated sub-entries, and have genuinely
recurring/structured email flagged as a candidate for a new standing
Pipeline instead of manual retyping
**So that** I stop getting one disconnected note per email and instead see
one running, correctly-filed record per conversation, with repeating work
surfaced as reusable automation rather than something I redo by hand every
time

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-55: Email Capture & Threading
  Pipeline*. Replaces the monolithic `email-capture` Worker
  (`app/business/email_classification.py::classify_recent_emails`) with a
  Pipeline of Jobs, under `ADR-041`'s Agent/Pipeline/Job/Hub model, built on
  the Thread data shape `REQ-SB-54-US-01` establishes. **Supersedes
  `REQ-SB-53-US-01`** (Email Pull/Tag/Link/Store split) — that story was
  built on the pre-`ADR-041` Agent-Type model and was already parked
  pending "a Pipeline Builder requirement" (`BACKLOG.md`'s own note on
  `REQ-SB-53`); this requirement is that trigger. `REQ-SB-53-US-01` stays
  `Parked`, not reworked into this story.
- Raised 2026-08-16, same extended discussion as `REQ-SB-54`.
- **Job chain — resolved, not open:** `Fetch` (existing Outlook pull,
  unchanged) → `Classify` (existing customer/kind classification, PLUS two
  new outcomes: does this belong to an existing Thread or start a new one;
  does this look like a recurring/structured artifact that wants its own
  standing Pipeline) → `Thread-Match/Merge` (create the Thread note on the
  first message of a `conversation_id`, update — full regeneration per
  `REQ-SB-54` point 8 — on every later one) → `Route-to-Project` (guess
  which of the matched Customer's currently-open Projects this belongs to,
  or propose a NEW Project if none fit).
- **Two branch Jobs — resolved:**
  - `Summarize-Attachment` — each attachment gets its own summarized, dated
    sub-entry appended to the Thread's body, kept separate from the
    regenerated top-level summary so attachment content isn't lossily
    compressed into one paragraph.
  - `Detect-Recurring-Pattern` — operator: "sometimes I get an Email that
    contains the pipeline or consumption of a customer, I need to take
    that email and start a pipeline for it... I am trying to build a
    reusable system here, not just a one-time code." When this Job fires,
    it does NOT do the recurring work itself — it proposes a NEW standing
    Pipeline, seeded from the triggering email, pre-filling the EXISTING
    Agent Creation Wizard (`REQ-SB-37`, `Done`) rather than inventing new
    infrastructure. Detection must be general (structural/pattern-based —
    "does this look like a recurring, structured artifact" — not a
    hardcoded rule for one customer's consumption-report format), so the
    SAME mechanism catches invoices, weekly exports, or anything else
    structured and repeating in the future, per the operator's own
    reusability framing.
- **Approval gating — confirmed directly, not left to guess:**
  - Thread → Project routing (or new-Project proposal): operator, asked
    whether the agent should decide or ask — "Agent Guess and it Goes to
    my Approve list."
  - New-Pipeline proposal from `Detect-Recurring-Pattern`: operator, asked
    the same question at the bigger-stakes level — "Agent detected, but
    let me approve before it builds." Both route through the EXISTING
    Pending Approvals surface (`agent_pending_approvals.json`, My Day →
    Approvals, `REQ-SB-21`, `Done`) — no new approval mechanism, reuse what
    exists.
  - Once a Thread's Project placement is approved, later replies in that
    SAME conversation are NOT re-routed or re-approved — they're just an
    update to the already-placed Thread note (per `REQ-SB-54` point 1). The
    approve list scales with new things happening, not with email volume.
- **Tags — resolved:** unioned onto the Thread's frontmatter on every
  update, never overwritten or pruned in v1 (per `REQ-SB-54`'s general
  regenerate-vs-append split — tags follow the "accumulate" side, same as
  Customer's Glimpse follows "regenerate").
- **Explicitly out of scope for this requirement:** the actual build of
  whatever new Pipeline `Detect-Recurring-Pattern` proposes — that's a new,
  separate Pipeline created (with operator approval) through the existing
  wizard at RUNTIME, not something this requirement's own implementation
  needs to anticipate the shape of.
- **Hard prerequisite, not this story's own scope to verify:**
  `REQ-SB-54-US-01`'s ConversationID-stability live verification (point 9)
  must be complete before this story's own `Thread-Match/Merge` Job — which
  literally joins on `conversation_id` — is built. This story is `Blocked
  by` `REQ-SB-54-US-01`, not independently re-flagged here.
- **UPDATE 2026-08-16, same day as the verification above, resolved
  same day too:** the operator flagged that `ConversationID` alone
  under-merges ("sometimes different emails with different ConversationID
  are linked to the same thread"), then resolved it by scope split rather
  than requiring a new merge mechanism here: "I guess we keep threads as
  is... we will need to have an entity called Conversation... we will
  handle the data in the KB later." **`T02` (`Thread-Match/Merge`) is
  UN-blocked — it may be built exactly as originally specced,
  `conversation_id`-only.** Reconciling multiple `ConversationID`s into
  one real Conversation is `REQ-SB-60`'s own future scope, not this
  story's.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Two messages in the same real conversation produce ONE Thread note, not two

```gherkin
Given a real, live Outlook mailbox with a multi-message conversation
When the first message in that conversation is captured
Then a single Thread note is created, classified by customer/kind
When a second message in the SAME conversation is captured
Then no second note is created — the same Thread note's transcript is
    updated and its top-level summary is regenerated fresh
```
<!-- AC-ID: REQ-SB-55-US-01-AC-01 -->

### Scenario 2: An attachment appears as its own dated, summarized sub-entry

```gherkin
Given a captured email in a Thread has a real attachment
When that email is processed through the pipeline
Then the attachment gets its own summarized, dated sub-entry appended to
    the Thread's body
  And the attachment's content is not compressed into the Thread's
    regenerated top-level summary — the sub-entry stays a separate,
    distinct record
```
<!-- AC-ID: REQ-SB-55-US-01-AC-02 -->

### Scenario 3: Thread → Project routing creates a Pending Approval, never an auto-committed write

```gherkin
Given a new Thread has been created from a first message in a new
    conversation
When the pipeline guesses which of the matched Customer's currently-open
    Projects this Thread belongs to (or proposes a new Project if none
    fit)
Then a Pending Approval is created for that routing decision — the Thread
    is not silently filed under a Project without the operator's approval
When the operator approves it
Then the Thread is placed under the approved Project
```
<!-- AC-ID: REQ-SB-55-US-01-AC-03 -->

### Scenario 4: A second message in an already-routed conversation does NOT produce a second approval

```gherkin
Given a Thread's Project placement has already been approved
When a later message in the SAME conversation is captured
Then it updates the existing Thread note directly — no new Pending
    Approval is created for this message, and no re-routing/re-approval
    step occurs
```
<!-- AC-ID: REQ-SB-55-US-01-AC-04 -->

### Scenario 5: A structured, repeating test email trips Detect-Recurring-Pattern and proposes a new Pipeline, not built automatically

```gherkin
Given a deliberately structured/repeating test email (e.g. a recurring
    consumption report or invoice-shaped artifact) is captured
When the Classify Job's Detect-Recurring-Pattern branch evaluates it
Then a Pending Approval is created proposing a NEW standing Pipeline,
    seeded from the triggering email and pre-filled into the existing
    Agent Creation Wizard
  And the proposed Pipeline is NOT built or executed automatically —
    nothing runs the recurring work itself until the operator explicitly
    approves and completes the wizard
```
<!-- AC-ID: REQ-SB-55-US-01-AC-05 -->

### Scenario 6: Recurring-pattern detection is structural, not hardcoded to one known format

```gherkin
Given two different structured/repeating test emails from two different,
    unrelated customers, each with a genuinely different structural
    pattern (not the same known template)
When each is captured through the pipeline
Then Detect-Recurring-Pattern fires for both, using the same general,
    pattern-based detection mechanism — not a rule hardcoded to a single
    customer's known consumption-report format
```
<!-- AC-ID: REQ-SB-55-US-01-AC-06 -->

### Scenario 7: Tags accumulate on the Thread across updates, never pruned

```gherkin
Given a Thread note already carries a set of tags from its first message
When a later message in the same conversation is captured with different
    (but relevant) tags
Then the new tags are unioned onto the Thread's existing tag set
  And no previously-present tag is removed or overwritten by this update
```
<!-- AC-ID: REQ-SB-55-US-01-AC-07 -->

### Scenario 8: email-capture no longer exists as a separate agent once this pipeline ships

```gherkin
Given this story has shipped
When the list of known agents is queried (e.g. via the Agents Map or
    GET /agents)
Then email-capture no longer appears as its own agent — it has been fully
    replaced by this requirement's Pipeline of Jobs
  And REQ-SB-53-US-01 is marked superseded (not reworked) in BACKLOG.md
```
<!-- AC-ID: REQ-SB-55-US-01-AC-08 -->

### Scenario 9: A real, live Outlook-backed capture run produces the correct end-to-end outcome

```gherkin
Given the real, live Outlook mailbox this project is configured against
When a real scheduled or manually-triggered capture run processes real,
    genuinely new email through this pipeline
Then the resulting Thread note(s), attachment sub-entries, and Pending
    Approval(s) all reflect the real captured content correctly — not a
    mocked/simulated pipeline
```
<!-- AC-ID: REQ-SB-55-US-01-AC-09 -->

## Affected Screens

None — backend only. Pending Approvals (`html-prototype/my-day-approvals.html`)
already renders any Supervised-agent proposal generically via its existing
`.item-list`/`.item-row` pattern — this story's two new approval kinds
(Thread→Project routing, new-Pipeline proposal) reuse that same generic card
with no new screen region. The Agent Creation Wizard (`REQ-SB-37`, `Done`)
already accepts pre-filled seed data through its existing flow; no new wizard
screen is introduced. See `## Notes` for the prototype-parity breakdown.

## Dependencies

- **Was blocked by, now satisfied:** `REQ-SB-54-US-01` (Vault Knowledge
  Model Redesign) — the Thread data shape this pipeline populates, and the
  `ConversationID` stability live verification (point 9) this pipeline's
  `Thread-Match/Merge` Job depends on directly. Closed `Done` 2026-08-16
  (`SPRINT-048`, all 6 tasks verified live). No longer a blocker.
- **Related to:** `REQ-SB-37` (Agent Creation Wizard, `Done`) — the existing
  wizard `Detect-Recurring-Pattern`'s proposal pre-fills into; unmodified by
  this story.
- **Related to:** `REQ-SB-21` (Agent Working Modes / Pending Approvals,
  `Done`) — the existing approval surface both new approval kinds reuse.
- **Related to:** `REQ-SB-38`/`REQ-SB-51` (Agents Map density clustering,
  Background Agents, both `Done`) — already agent-count-agnostic; absorbs
  whatever new agent/Job identities this pipeline introduces with no code
  change, per the established precedent (`REQ-SB-53-US-01`'s own Context).
- **Supersedes:** `REQ-SB-53-US-01` (Email Pull/Tag/Link/Store split,
  `Parked`) — not reworked; `BACKLOG.md`'s `REQ-SB-53` row already notes
  this.
- **External:** the already-live Outlook COM / Compass integrations this
  pipeline extends, unchanged in kind.

## Constraints

- **No second, independent Compass/classification call chain** — this is
  an extension of the existing `Fetch`→`Classify` shape
  (`email_classification.py`/`compass_client.py`), not a parallel pipeline.
- **`Fetch` is unchanged** — the real Outlook pull mechanism carries over
  as-is.
- **Detect-Recurring-Pattern must be general/structural**, never a rule
  hardcoded to one customer's known format (Scenario 6) — this is a hard
  requirement from the operator's own reusability framing, not a
  nice-to-have.
- **Both new approval kinds route through the existing Pending Approvals
  mechanism** — no new approval surface/mechanism is introduced.
- **Once a Thread's Project placement is approved, later replies in the
  same conversation never re-trigger approval** (Scenario 4) — the approve
  list scales with new things happening, not email volume.
- **Building the proposed recurring Pipeline itself is explicitly out of
  scope** — this story only proposes it through the existing wizard; the
  wizard flow, once triggered by the operator, is `REQ-SB-37`'s own already
  `Done` mechanism.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).
- This work runs against the user's real, live Outlook desktop and Obsidian
  vault (`VAULT_PATH`) — Scenario 9's live-verification requirement is not
  satisfiable via a mocked/simulated pipeline.

## Implementation Tasks

<!-- Decomposer-authored, /plan-tasks step 2 (2026-08-16) — supersedes the
analyst's own starting-point table above (preserved in git history only).
Adjusted from the analyst's 6-task sketch to match the architect's now-
concrete module shape (ADR-043): a new app/business/pipelines/ subpackage
owns DAG assembly only; every Job's real logic is a plain, LangGraph-
ignorant function in email_classification.py; a dedicated foundational
data_access task precedes the Job tasks; pipeline assembly and the
multi-file retirement each get their own task. -->

| ID | Type | Task | Files / Area | Task File | depends_on |
|---|---|---|---|---|---|
| REQ-SB-55-US-01-T01 | backend | `vault_writer.py` new primitives — header-scoped growing body-section append (Transcript/Attachments), unconditional frontmatter-key set (project/participants/last_message_at/tags-union), Customer's open-Projects enumeration | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-55-US-01-T01-vault-writer-thread-primitives.md` | — |
| REQ-SB-55-US-01-T02 | backend | `Classify` Job extension — general/structural recurring-pattern-candidate outcome | `app/data_access/compass_client.py`, `app/business/email_classification.py` | `../Tasks/REQ-SB-55-US-01-T02-classify-recurring-pattern-detection.md` | — |
| REQ-SB-55-US-01-T03 | backend | `Thread-Match/Merge` Job — create-on-first-message, regenerate-on-update, tag union, customer/participants/last_message_at | `app/business/email_classification.py` | `../Tasks/REQ-SB-55-US-01-T03-thread-match-merge-job.md` | T01 |
| REQ-SB-55-US-01-T04 | backend | `Route-to-Project` Job — Customer's open-Projects guess + new-Project proposal via Pending Approval; new `_APPROVAL_HANDLERS` entry + router generalization | `app/business/email_classification.py`, `app/data_access/compass_client.py`, `app/api/pending_approvals_router.py` | `../Tasks/REQ-SB-55-US-01-T04-route-to-project-job.md` | T01, T03 |
| REQ-SB-55-US-01-T05 | backend | `Summarize-Attachment` branch Job — per-attachment dated summarized sub-entry | `app/business/email_classification.py` | `../Tasks/REQ-SB-55-US-01-T05-summarize-attachment-job.md` | T01, T03 |
| REQ-SB-55-US-01-T06 | backend | `Detect-Recurring-Pattern` branch Job — Pending Approval proposing a new Pipeline, wizard-seed payload, never builds it; second `_APPROVAL_HANDLERS` entry | `app/business/email_classification.py`, `app/api/pending_approvals_router.py` | `../Tasks/REQ-SB-55-US-01-T06-detect-recurring-pattern-job.md` | T02, T04 |
| REQ-SB-55-US-01-T07 | backend | Pipeline assembly — new `app/business/pipelines/email_capture_pipeline.py`, `StateGraph` wiring all 6 Jobs, Fetch pre-graph batch loop, `run_email_capture_pipeline(limit)` entry point | `app/business/pipelines/__init__.py`, `app/business/pipelines/email_capture_pipeline.py` | `../Tasks/REQ-SB-55-US-01-T07-pipeline-assembly.md` | T03, T04, T05, T06 |
| REQ-SB-55-US-01-T08 | backend | Retire `email-capture`; register the new `email-capture-pipeline` Agent-tier identity across every real referencing file; full live end-to-end verification | `app/business/agent_registry.py`, `app/business/background_agent_registry.py`, `app/business/skill_tools.py`, `app/business/skill_registry.py`, `app/api/agents_router.py`, `app/business/email_classification.py`, `app/business/demo_taxonomy.py` | `../Tasks/REQ-SB-55-US-01-T08-retire-email-capture.md` | T07 |

## Definition of Done

- [x] All acceptance-criteria scenarios pass (all 9, `AC-01`-`AC-09`, verified live/manually across `T01`-`T08`)
- [x] Every Implementation Task above is complete (`T01`-`T08` all `Done`)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (n/a — test tooling still pending project-wide; manual mode throughout, per every task's own Tests block)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Building whatever new Pipeline `Detect-Recurring-Pattern` proposes** —
  a separate, runtime, operator-approved creation through the existing
  wizard, not anticipated here.
- **Meeting capture / Thread linking** — `REQ-SB-56`'s own scope.
- **The synthesis mechanism that keeps Project/Customer Glimpse current
  off of Thread updates** — `REQ-SB-57`'s own scope; this story only
  produces the Thread-level evidence.
- **Glimpse-first chat answering** — `REQ-SB-58`'s own scope.
- **Backfilling existing Email notes into Thread notes** — `REQ-SB-59`'s
  own scope.
- **A real, persisted queue/staging architecture between Jobs** — this
  pipeline runs in-process, in one atomic pass per email, per `ADR-041`'s
  own model (mirroring `REQ-SB-53-US-01`'s own equivalent, now-superseded
  constraint).

## Notes

**Architect pass, 2026-08-16 (`/plan-tasks` step 1):**

- **Architecture scope:** §"Email Capture & Threading Pipeline — First
  Concrete Pipeline" (`Implementation/Architecture/architecture.md`) — the
  coder is bounded by this section for every task under this story. Also
  read, for context the coder must not deviate from: §"Agent / Pipeline /
  Job / Hub Domain Model — Taxonomy" (near the top of `architecture.md`),
  §"Vault Knowledge Model Redesign — Threads, Manual Captures, OKF-
  Conformant Customer & Project Directories" (`REQ-SB-54`, the Thread/OKF
  primitives this pipeline populates), and the amended note under
  §"Meeting → Thread Linking" (the `participants`/`last_message_at`
  ownership resolution this pass made on `REQ-SB-56`'s behalf).
- **`ADR-043` created** — "Email Capture & Threading Pipeline — the first
  concrete Pipeline built under `ADR-041`'s model." Resolves, concretely
  for this one Pipeline, three questions `ADR-041` itself left open: the
  DAG's own module/data-model shape (a new `app/business/pipelines/`
  subpackage, code-defined `StateGraph`, not yet a persisted/user-editable
  definition), whether mid-pipeline human approval needs a LangGraph
  checkpointer (it does not — reuses the existing flat-JSON Pending
  Approval mechanism, `_APPROVAL_HANDLERS` dispatch table, mirroring the
  Vault Filing Expert Tier-2 precedent, `ADR-021` point 5), and whether a
  Job ever earns its own Agent-like Map/chat/Working-Mode surface (it
  doesn't — one new Agent-tier identity replaces `email-capture` 1:1;
  none of the six Jobs get their own registry entry). Full reasoning:
  `Implementation/Architecture/ADR.md` → `ADR-043`.
- **`gate: flagged`, trigger-3 (ADR-043 created/changed)** — per
  `Implementation/Pipeline.md`'s gating contract, this does NOT halt the
  stage; the decomposer runs next so the human reviews `ADR-043` and the
  resulting tasks together in one pass. A `REVIEW-QUEUE.md` pointer was
  written for this.
- No `ESCALATIONS.md` entry — nothing in this pass contradicts an
  `Accepted` ADR, the PRD, or a `MEMORY.md` constraint; `ADR-043` extends
  `ADR-041`/`ADR-021`/`ADR-042` without reopening any of them.

**Original analyst `gate: clear` reasoning, preserved verbatim (superseded
by the flag above, not deleted — the analyst's own design-question
resolution below still stands; only the ADR-creation trigger changed the
gate):**

> Why `gate: clear`: every design question the PRD raises specifically
> for `REQ-SB-55` (job chain shape, the two branch Jobs, both
> approval-gating decisions, the tag-accumulation rule, the
> general-not-hardcoded detection requirement) is directly resolved by a
> quoted, confirmed operator answer — no material assumption, no
> genuinely unclear/multiple-equally-valid scoping question, no
> contradictory PRD input, and no oversized scope (six Jobs sharing one
> atomic pipeline pass, matching this codebase's own `REQ-SB-53-US-01`
> single-story precedent for a comparable Email-pipeline scope). The only
> reason this story cannot start today is the real, external dependency
> on `REQ-SB-54-US-01` shipping first (its Thread data shape and its
> mandatory `ConversationID` verification) — the same "gate: clear —
> blocked on X shipping" pattern this project already uses for
> `REQ-SB-03-US-01` (blocked on `REQ-SB-01`/`REQ-SB-02`).

**Prototype parity (my-day-approvals.html, agents-map.html):**

- Pending Approvals list — **Specced** (Scenario 3, 5) — reuses the exact
  existing `.item-list`/`.item-row` pattern; no new region. Two new
  approval KINDS (Thread→Project routing, new-Pipeline proposal) render as
  ordinary rows within the already-approved generic card.
- Agents Map — **Specced (reuse)** — whatever Job/Agent identities this
  pipeline introduces render on the already agent-count-agnostic canvas
  with zero bespoke code, per the established `REQ-SB-53-US-01` precedent.
- Agent Creation Wizard pre-fill — **Specced (reuse)** — the wizard
  (`REQ-SB-37`, `Done`) already accepts a seeded initial state through its
  existing flow; no new wizard screen.

**Why the analyst originally set `gate: clear`:** see the verbatim-preserved
reasoning near the top of this `## Notes` section — superseded to
`gate: flagged` by this architect pass solely on the ADR-043-creation
trigger, not because any of that original reasoning stopped holding.

**Decomposer pass, 2026-08-16 (`/plan-tasks` step 2):**

- All 9 untagged Gherkin scenarios locked as `REQ-SB-55-US-01-AC-01`..
  `AC-09`, tags appended verbatim after each scenario's closing fence. No
  wording changes were needed for buildability — the analyst's own
  scenarios, already tightened against the operator's directly-quoted
  answers, were concrete enough to lock as-is.
- 8 flat-root task files created (`T01`-`T08`), superseding the analyst's
  6-task starting-point table — adjusted to the architect's now-concrete
  module shape (`ADR-043`): a dedicated foundational `vault_writer.py`
  primitives task (`T01`) precedes every Job task that needs a new
  data_access primitive (header-scoped growing body-section append for
  `## Transcript`/`## Attachments`; an unconditional frontmatter-key
  setter for `project`/`participants`/`last_message_at`/tag-union writes,
  since `insert_frontmatter_key_if_missing` cannot overwrite an
  already-present key and this Job needs to); each of the six Jobs is its
  own plain, LangGraph-ignorant function living in
  `email_classification.py` per `ADR-043` point 1; pipeline assembly
  (`T07`, the new `app/business/pipelines/email_capture_pipeline.py`
  subpackage) is its own task, built only once every Job function it
  wires exists; the multi-file `email-capture` retirement (`T08`)
  enumerates every real reference found by direct search this pass —
  `agent_registry.py` (`_SEED_AGENTS`), `background_agent_registry.py`
  (`_DEFAULT_BACKGROUND_AGENT_IDS`), `skill_tools.py`
  (`run_capture_now`'s handler), `skill_registry.py` (three grant lists —
  `view_last_run`/`run_capture_now`/`pause_schedule`), `agents_router.py`
  (`_ACTION_HANDLERS`), `email_classification.py` itself
  (`run_capture_for_agent`/`run_capture_and_record_completion`'s own
  agent_id string uses) — plus `demo_taxonomy.py` (a disconnected demo
  fixture only, left to coder judgement whether to reconcile its
  coincidentally-matching `"pipeline-email-capture"` id or leave it,
  logged either way, not locked-AC-bearing). The new Agent-tier identity
  is named `email-capture-pipeline` (`type: "worker"`, matching the
  retired entry's own type per `ADR-043` point 6) — a genuinely new id,
  not a reused `"email-capture"` key, since Scenario 8/`AC-08`'s own
  wording ("`email-capture` no longer appears as its own agent") requires
  the old id string to actually stop resolving, not just have its
  settings rewritten in place.
- **Both new Pending-Approval kinds use `trigger="direct"`, never
  `"background"`** — a deliberate, load-bearing decomposer-level design
  choice, not explicitly spelled out by `ADR-043`: `create_pending_
  approval`'s own idempotency guard (`app/business/pending_approval_
  registry.py`) only deduplicates `trigger == "background"` records,
  collapsing every subsequent call for the same `agent_id` into the
  single already-pending record. Since a single pipeline tick can
  legitimately produce MULTIPLE distinct Thread→Project routing guesses
  and/or recurring-pattern proposals across different emails in the same
  run, `"background"` would silently collapse them into one — `"direct"`
  (never deduplicated, each a distinct, deliberate proposal) is the
  correct trigger value for both `T04`/`T06`. Logged here since it's a
  genuine judgement call over an ADR-silent implementation detail, not
  itself a new MUST-FLAG trigger (a single correct reading of an existing,
  already-`Accepted` primitive's own documented dedup contract — not a
  material assumption filling a real gap).
- `depends_on` is acyclic: `T01`/`T02` are independent roots; `T03` → `T01`;
  `T04`/`T05` → `T01`, `T03`; `T06` → `T02`, `T04` (reuses `T04`'s own
  router-generalization edit to `pending_approvals_router.py`'s
  `_APPROVAL_HANDLERS` outcome-message construction, rather than a second,
  divergent edit); `T07` → `T03`, `T04`, `T05`, `T06`; `T08` → `T07`. No
  task references a task ID that doesn't exist; no cycle.
- Every locked AC has at least one AC-tagged manual verification step in
  at least one task (manual mode throughout — no automated test stack
  exists yet for this backend): `AC-01`→`T03`+`T08`; `AC-02`→`T05`+`T03`;
  `AC-03`→`T04`; `AC-04`→`T07`; `AC-05`→`T06`; `AC-06`→`T02`+`T06`;
  `AC-07`→`T03`; `AC-08`→`T08`; `AC-09`→`T08` (the mandatory real,
  live Outlook-backed run).
- Status advances `Draft` → `Ready`, all 8 tasks written directly at
  `status: Ready` (in lockstep, per this pipeline's own contract) — every
  AC is locked, every locked AC has a tagged step, `depends_on` is
  acyclic. `gate` stays `flagged` (trigger-3, `ADR-043`) as a standing
  breadcrumb — status and gate are independent axes, per this project's
  own established `REQ-SB-54-US-01`/`REQ-SB-49-US-02` precedent (a
  `Ready`/eventually-`Done` story can carry a permanently-`flagged` gate
  once the ADR review is a standing breadcrumb, not a blocking condition).
  Eligible for `/plan-sprints`.
- No new `ESCALATIONS.md` entry from this pass — no contradiction with an
  `Accepted` ADR, the PRD, or a `MEMORY.md` constraint surfaced while
  writing these 8 tasks; the `REVIEW-QUEUE.md` pointer already written for
  `ADR-043`'s human review (this architect-pass trigger) covers this
  pass's own flag — no second, separate `REVIEW-QUEUE.md` line item was
  needed.

**Coder pass, 2026-08-16 — story closed `Done`.** All 8 tasks (`T01`-`T08`)
`Done`; all 9 locked ACs verified (`AC-01`/`AC-02`/`AC-03`/`AC-04`/`AC-07`
live against a real, disposable scratch vault with a real, configured
Compass Provider; `AC-05`/`AC-06` live against real structured test
emails; `AC-08` confirmed against the real agent registry;
`AC-09` — the mandatory real, live, non-mocked, non-simulated
Outlook-backed run — confirmed against this project's own real,
configured mailbox and vault, producing a real Thread note and a real,
genuinely-derived Pending Approval). `status: Ready` → `Done`.
`gate: flagged` (trigger-3, `ADR-043`) stays as a standing breadcrumb,
unresolved by this pass — the human review of `ADR-043` this flag exists
for is independent of delivery completion, per this project's own
established `REQ-SB-54-US-01`/`SPRINT-048` precedent (a `Done` story can
carry a permanently-`flagged` gate). `BACKLOG.md`'s `REQ-SB-55` row and
`SPRINT-049`'s own status/retrospective updated in the same pass — see
`SPRINT-049`'s own `## Retrospective`.
