---
id: REQ-SB-63-US-01
title: The Librarian — generalize the Vault Filing Expert into the consulted placement authority for REQ-SB-55/56/57/58's pipeline Jobs, extended to detect and surface cross-cutting KB updates
requirement_ids: [REQ-SB-63]
requirement_section: "REQ-SB-63: The Librarian — Vault Expert as the Central Placement/Restructuring/Enrichment Authority for the New KB Pipelines"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-1 (material assumption) — architect pass, /plan-tasks step 1, 2026-08-16: no new ADR was needed (verified independently, not taken on faith — see ## Notes), but the concrete shape of 'the deferred cross-reference write' was not specified by the story/PRD and was designed by this pass (an additive already_filed_path parameter, a new cross_cutting_implication decision field, a new customer/partner TAG write). Flagged for human confirmation. Decomposer pass, /plan-tasks step 2, 2026-08-16: all 6 scenarios locked (AC-01..AC-06), 3 tasks written (T01-T03), every locked AC has a tagged verification step, depends_on is acyclic — status advanced Draft to Ready per the gating contract (gate stays flagged as a breadcrumb for the architect's designed write-shape, not a blocker). See REVIEW-QUEUE.md."
sprint: "SPRINT-050"
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-63-US-01 — The Librarian — generalize the Vault Filing Expert into the consulted placement authority for REQ-SB-55/56/57/58's pipeline Jobs, extended to detect and surface cross-cutting KB updates

## Story

**As a** Second Brain user
**I want** every `REQ-SB-55`/`56`/`57`/`58` pipeline Job to consult one
central Librarian for placement, cross-reference, and KB-shaping decisions —
grounded in the live vault structure, rather than each pipeline growing its
own separate, divergent routing/cross-reference logic
**So that** the vault stays organized "under one master" (the operator's own
framing) with a single, consistent, always-vault-structure-aware authority
deciding where content belongs, and content whose arrival implies a change
elsewhere in the KB (e.g. this Thread also means a Customer's Glimpse needs
regenerating) is never silently dropped or silently applied with no trace

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-63: The Librarian — Vault Expert as
  the Central Placement/Restructuring/Enrichment Authority for the New KB
  Pipelines*.
- Raised 2026-08-16, same day as `SPRINT-048`'s close. Operator's own
  reasoning, verbatim: "If we have a vault expert then a pipeline of Threads
  starts, prepares everything, then gives it to the vault — the [expert]
  understands the vault structure, decides yes this is a Thread stored in
  that structure, maybe this is also customer info I will need to add
  there, etc. This will help the vault be always organized under one master
  (call him the Librarian), and the vault will be asking for approval of
  stuff if it needs my validation."
- **A genuine generalization of already-shipped code, not a new concept.**
  `app/business/vault_filing_expert.py` (`REQ-SB-35-US-01`, `Done`,
  `ADR-021`) already does almost exactly this today, scoped to one caller
  (chat-uploaded attachment review, reached via `REQ-SB-20`'s Hub routing):
  it reads the live vault structure fresh (`vault_writer.list_known_kinds`/
  `list_known_customers`/`list_known_partners`, never hardcoded), decides
  Tier 1 (fits an existing category — write immediately via
  `determine_placement_and_file`) vs. Tier 2 (a genuinely new top-level
  area — routes to a real Pending Approval via `_create_tier_2_proposal`),
  and mechanically links the referenced Customer/Partner hub note
  (`_link_referenced_entity`, reusing `customer_hub_linking`/
  `partner_hub_linking`'s existing primitives). This requirement extends
  that SAME module/Agent — never a second, divergent implementation — to
  (a) accept a new class of caller (a Job inside a `REQ-SB-55`-onward
  pipeline, not only the attachment-review chat flow), and (b) decide a
  genuinely new case it doesn't handle today: content whose arrival implies
  a cross-cutting update ELSEWHERE in the KB (e.g. "this Thread also means
  Customer X's Glimpse needs regenerating"), which should trigger
  `REQ-SB-57`'s Synthesizer rather than only ever producing one new note.
- **Open scope question #1 (retrofit scope) — RESOLVED DIRECTLY by the
  operator during this `/spec` pass, not left open:** asked whether "one
  master" also means retrofitting the already-`Done`, already-shipped
  Email/Meeting/Task/People capture pipelines (`REQ-SB-08`/`09`/`10` —
  `app/business/email_classification.py`, the equivalent meeting/todo
  classification modules, `people_extraction.py`) to route through the
  Librarian, the operator answered: **"There is no Retrofit we Will Redo
  everything any way and replace it with pipeline."** Meaning: those
  modules are not bridged, wrapped, or dual-maintained alongside the
  Librarian — they are, in time, fully REPLACED by new pipelines built
  under this KB redesign (`REQ-SB-55` onward, consulting the Librarian
  natively from the start), the same "wipe and fully re-run" philosophy
  `REQ-SB-59` already established for the DATA, now extended by the
  operator to the CODE/pipeline architecture itself. **This story's own
  scope is therefore: every `REQ-SB-55`/`56`/`57`/`58` pipeline Job (and,
  whenever it is eventually built, any future replacement for
  `REQ-SB-08`/`09`/`10`'s own scope) consults the Librarian. The CURRENT
  `email_classification.py`/meeting/todo classification modules and
  `people_extraction.py` are explicitly out of scope (see Non-Goals) — this
  story does not touch them, retrofit them, or bridge them; they keep
  working exactly as they do today until a future requirement replaces
  them.**
- **Open scope question #2 (trigger mechanism for the new cross-cutting-
  update case) — genuinely open, NOT resolved, flagged (MUST-FLAG
  trigger 8):** does the Librarian call `REQ-SB-57`'s Synthesizer directly
  (a new, synchronous Agent-to-Agent call), or does it create a Pending
  Approval/proposal the same way Tier 2 already does, letting the existing
  approval surface be the one place every "the vault wants to change
  something beyond the obvious new note" decision surfaces? Both are real,
  buildable, equally-valid designs — see `## Notes` for a proposed
  candidate answer awaiting operator confirmation. This is a DIFFERENT
  trigger surface from `REQ-SB-57`'s own already-designed "a Thread update
  automatically triggers ITS OWN Project's resynthesis" mechanism (that
  trigger fires unconditionally for the Thread's own, obvious Project —
  no Librarian involvement needed there). The Librarian's new case is
  specifically the NON-obvious implication: content that ALSO affects a
  DIFFERENT Customer/Project than the one it's being filed under. Resolving
  this question does not require or block on `REQ-SB-57-US-01`'s own
  separately-flagged, unrelated open question (the exact "worth a History
  line" bar) — the two flagged items are independent.
- **Minimum acceptance bar, per the PRD's own text:** a Job in `REQ-SB-55`'s
  Thread pipeline can consult the Librarian mid-flow (mirroring `ADR-041`'s
  own "branch to consult an Expert" pattern — consulting an Expert is
  additive, the Pipeline's own terminal step still runs either way) and
  receive a real placement decision grounded in the live vault structure;
  a decision that implies a cross-cutting update elsewhere surfaces as a
  real, human-visible event rather than being silently dropped or silently
  applied with no trace.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A Job in REQ-SB-55's Thread pipeline consults the Librarian mid-flow and receives a grounded placement decision

```gherkin
Given a Job inside REQ-SB-55's Thread capture pipeline (Consult-Librarian,
    wired to fire after Thread-Match/Merge) is processing an already-filed
    Thread mid-flow
When that Job calls determine_placement_and_file(..., already_filed_path=
    <the Thread's own note path>) — mirroring ADR-041's own "branch to
    consult an Expert" pattern; the Pipeline's own terminal step still
    runs either way
Then the Librarian returns a placement decision grounded in the live vault
    structure (known_kinds/known_customers/known_partners, read fresh in
    the SAME model completion, never hardcoded)
  And the SAME Tier 1 (write immediately/link) vs. Tier 2 (create a
    Pending Approval) boundary already proven for the chat-uploaded-
    attachment caller governs this decision — no second, divergent
    placement mechanism exists for this new caller
```
<!-- AC-ID: REQ-SB-63-US-01-AC-01 -->

### Scenario 2: A referenced Customer/Partner hub note is linked mechanically regardless of which caller invoked the Librarian

```gherkin
Given the Librarian is consulted with already_filed_path set by a Job
    inside REQ-SB-55's pipeline (not the original chat-attachment caller)
When the Librarian's decision names an existing or new Customer/Partner as
    its own primary referenced_customer/referenced_partner
Then the ALREADY-FILED Thread note (not a new note) is mechanically
    linked to that Customer/Partner's hub note via the SAME
    _link_referenced_entity mechanism already proven for the
    chat-uploaded-attachment caller — hub-linking is caller-agnostic and
    no second, redundant note is ever written for content the caller says
    is already filed
```
<!-- AC-ID: REQ-SB-63-US-01-AC-02 -->

### Scenario 3: Content whose arrival implies a cross-cutting update elsewhere in the KB surfaces as a real, human-visible event, never silently dropped or silently applied

```gherkin
Given a Thread being processed by the Librarian contains content whose
    model-returned cross_cutting_implication names a DIFFERENT,
    already-known Customer or Partner than the content's own primary
    placement — re-checked in Python against the SAME pre-fetched
    known_customers/known_partners lists and against the SAME decision's
    own referenced_customer/referenced_partner, never trusted from the
    model's own naming alone
When the Librarian identifies this cross-cutting implication
Then a new, independent Pending Approval is created (action_id
    "propose_cross_cutting_update"), never auto-applied
  And approving it runs finalize_cross_cutting_update, which writes an
    additive customer/<slug> or partner/<slug> tag onto the already-filed
    note (reusing REQ-SB-55-US-01-T01's own unconditional frontmatter-key
    setter, never captures.md, which ADR-042 reserves for operator-only
    writes) — the implication is never silently dropped and never
    silently applied with no trace
```
<!-- AC-ID: REQ-SB-63-US-01-AC-03 -->

### Scenario 4: Routine content that implies no cross-cutting update produces exactly the existing Tier 1/Tier 2 outcome, nothing extra

```gherkin
Given content processed by the Librarian has a null cross_cutting_
    implication, OR names an entity absent from the pre-fetched
    known_customers/known_partners lists (a genuinely new entity — normal
    Tier 1/2 new-entity handling already covers it), OR names the SAME
    entity as the SAME decision's own referenced_customer/
    referenced_partner (already mechanically hub-linked, not "elsewhere")
When the Librarian processes it
Then only the existing Tier 1 write/link or Tier 2 proposal outcome
    occurs
  And no "propose_cross_cutting_update" Pending Approval is spuriously
    created
```
<!-- AC-ID: REQ-SB-63-US-01-AC-04 -->

### Scenario 5: The Librarian's Provider unavailability is honestly surfaced to a new caller exactly as it already is to the original one

```gherkin
Given the Librarian's configured model Provider is unavailable
When a Job in REQ-SB-55's pipeline calls determine_placement_and_file(...,
    already_filed_path=<a real Thread path>) mid-flow
Then the pipeline receives the SAME honest {"status": "unavailable", ...}
    result already proven for the chat-uploaded-attachment caller — never
    a fabricated placement
  And the Pipeline's own terminal step for that item still completes to a
    clean, ordinary end (no crash, no interrupt) — this generalization
    changes nothing about that already-proven honesty behavior
```
<!-- AC-ID: REQ-SB-63-US-01-AC-05 -->

### Scenario 6: The already-shipped Email/Meeting/Task/People capture pipelines are untouched by this story

```gherkin
Given REQ-SB-08/REQ-SB-09/REQ-SB-10's already-Done capture pipelines
    continue writing directly via their own classification modules
    (email_classification.py's pre-existing classify_recent_emails path
    and its meeting/todo/people equivalents)
When this story ships
Then those pre-existing modules' own functions are byte-for-byte
    unaltered and are never routed through the Librarian — per the
    operator's own resolved decision ("no Retrofit... replace it with
    pipeline"); retiring them is future requirement work, not this
    story's scope
```
<!-- AC-ID: REQ-SB-63-US-01-AC-06 -->

## Affected Screens

None — backend only. Whatever new Pending Approval kind the cross-cutting-
update case may produce (if `## Notes`' candidate answer for the trigger
mechanism is confirmed) reuses the existing generic Pending Approvals card
(`my-day-approvals.html`), exactly as Tier 2's own proposal already does —
no new screen region. See `## Notes` for the prototype-parity note.

## Dependencies

- **Blocked by:** `REQ-SB-55-US-01` (Email Capture & Threading Pipeline,
  `Draft`, `gate: clear`) — the Thread pipeline this story's one concrete
  proof-of-concept consult call site lives inside (Scenarios 1, 2, 5).
- **Related to:** `REQ-SB-56-US-01`, `REQ-SB-57-US-01`, `REQ-SB-58-US-01`
  (all `Draft`) — the PRD's own text names all four pipelines as ones the
  Librarian becomes the consulted authority for. Wiring an equivalent
  consult call into each of THEIR OWN Jobs is each of those stories' own
  future addition (their current task lists do not yet include a Librarian
  consult step) — this story only builds the generalized, reusable
  mechanism plus the one concrete `REQ-SB-55` integration point the PRD's
  own minimum acceptance bar requires.
- **Related to:** `REQ-SB-57-US-01` (specifically) — the Synthesizer this
  story's cross-cutting-update case, if resolved as a direct call, would
  invoke. Independent of that story's own separately-flagged "worth a
  History line" open question (see Context).
- **Related to:** `REQ-SB-35-US-01` (Vault Filing Expert, `Done`) /
  `ADR-021` — the exact mechanism this story generalizes; never a second,
  divergent implementation.
- **Related to:** `REQ-SB-08`/`REQ-SB-09`/`REQ-SB-10` (all `Done`) —
  explicitly NOT touched by this story (Scenario 6, Non-Goals); superseded
  only when a future requirement replaces their pipelines.
- **External:** none beyond the already-live vault-write/model-Provider
  mechanisms this story extends.

## Constraints

- **Never a second, divergent placement implementation** — `vault_filing_
  expert.py` stays the single module/entry-point family this story
  extends (`ADR-021` point 2's own precedent); no parallel routing/
  cross-reference logic grows inside any pipeline Job.
- **Grounding stays live-vault-structure-aware and deterministic-context-
  injected** (`known_kinds`/`known_customers`/`known_partners`, read
  fresh, never hardcoded) — unchanged by adding a new caller.
- **The Tier 1/Tier 2 boundary is unchanged and re-checked in Python
  against the live vault structure, never trusted from the model's own
  boolean alone** (`ADR-021` point 2) — unchanged by this generalization.
- **A cross-cutting-update implication is never silently dropped and never
  silently applied with no trace** (the PRD's own Acceptance text) — must
  always surface as a real, human-visible event.
- **The cross-cutting trigger mechanism (direct Synthesizer call vs.
  Pending Approval) is NOT built until the operator confirms it** (see
  Notes) — do not silently pick one at `/plan-tasks`.
- **`REQ-SB-08`/`09`/`10`'s current classification modules are NOT touched,
  bridged, or retrofitted by this story** — resolved directly by the
  operator ("There is no Retrofit... replace it with pipeline"), not an
  assumption; see Non-Goals.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Decomposer-authored table (/plan-tasks step 2, 2026-08-16) — supersedes
the analyst's own starting-point table. T03 was split by function/file
rather than kept as one "trigger mechanism" task: T01 owns BOTH the
additive already_filed_path parameter AND the cross_cutting_implication
detection/proposal-creation (both live inside vault_filing_expert.py, both
evaluated in the SAME model completion); T03 owns only the deferred
finalize/write handler (a different file, pending_approvals_router.py's
dispatch table) — mirroring ADR-021's own real Tier-2 precedent of
propose/finalize as two distinct functions. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-63-US-01-T01 | backend | Generalize `determine_placement_and_file` — additive `already_filed_path` param (skip Tier1/2 write, link only) + additive `cross_cutting_implication` decision field, re-checked in Python, creating a `propose_cross_cutting_update` Pending Approval via a new `_create_cross_cutting_proposal` | `app/business/vault_filing_expert.py`, `app/business/vault_filing_methodology.py` | `../Tasks/REQ-SB-63-US-01-T01-generalize-entry-point.md` |
| REQ-SB-63-US-01-T02 | backend | Wire `Consult-Librarian` into REQ-SB-55's Thread pipeline — new `consult_librarian` Job in `email_classification.py`, a new additive branch node/edge in the compiled `StateGraph`, plus a small new `vault_writer.read_body_section` reader primitive | `app/data_access/vault_writer.py`, `app/business/email_classification.py`, `app/business/pipelines/email_capture_pipeline.py` | `../Tasks/REQ-SB-63-US-01-T02-thread-pipeline-consult.md` |
| REQ-SB-63-US-01-T03 | backend | `finalize_cross_cutting_update` — the deferred write half: additive `customer/<slug>`/`partner/<slug>` tag, dispatched via `_APPROVAL_HANDLERS`, never `captures.md` | `app/business/vault_filing_expert.py`, `app/api/pending_approvals_router.py` | `../Tasks/REQ-SB-63-US-01-T03-cross-cutting-update-finalize-handler.md` |

## Definition of Done

- [x] The cross-cutting-update trigger mechanism has been confirmed by the
      operator (Option B, Pending Approval) and recorded in this story's
      `## Notes`
- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual verification mode; test tooling still pending project-wide
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Retrofitting or bridging `REQ-SB-08`/`09`/`10`'s current classification
  modules** (`email_classification.py` and its meeting/todo/people
  equivalents) — resolved directly by the operator as explicitly out of
  scope ("There is no Retrofit... replace it with pipeline"); those modules
  keep working exactly as they do today. Superseding them is future
  requirement work (mirroring `REQ-SB-59`'s already-established wipe-and-
  rerun philosophy, now extended by the operator to the pipeline/code
  architecture itself, not just the data), not something this story
  anticipates the shape of.
- **Wiring an equivalent Librarian consult call into `REQ-SB-56`/`57`/`58`'s
  own pipeline Jobs** — each of those stories' own future addition; this
  story only proves the mechanism via `REQ-SB-55`.
- **Redesigning `REQ-SB-57`'s own existing evidence-change trigger**
  (a Thread update automatically triggers its OWN Project's resynthesis) —
  unchanged; this story's new trigger case is specifically the non-obvious,
  elsewhere-in-the-KB implication, a different surface entirely.
- **The Pipeline Builder / DAG UI** (`ADR-041` points 5–6) — unrelated,
  separately deferred work.
- **Locking the exact cross-cutting trigger mechanism** — genuinely open,
  flagged for operator confirmation (see Notes).
- **Designing a comprehensive, closed, final multi-agent KB-maintenance
  system** — per the operator's own framing (see Notes), this story is
  understood to be the FIRST step of a growing set of KB-maintenance/
  enrichment agents added incrementally over time, not a one-go design;
  this story deliberately does not build speculative extensibility hooks
  for agents/tasks nothing yet needs.

## Notes

**Scoping framing — this is the first of a growing set, not a closed,
final design:** the operator, when this story was drafted: "Just to put it
into perspective, this will be a growing set of Agents with different info
and tasks, not a one-go — take this into consideration." This story's own
Acceptance Criteria are deliberately kept narrow and concrete — the specific
`REQ-SB-55` Thread-routing consultation plus the cross-cutting-update
trigger, per the PRD's own Acceptance text — rather than a comprehensive
multi-agent KB-maintenance design. A future story adding more specialized
agents/tasks to this family is expected and not a redesign of this one;
this story does not build speculative extensibility hooks for capabilities
nothing yet needs (mirroring this project's own established "build one real
thing before building the generalized platform for it" precedent —
`ADR-041`'s own "build one real Pipeline before building the Builder"
sequencing).

**Prototype parity:** N/A — no new `html-prototype/` screen region. If the
candidate trigger-mechanism answer below (Pending Approval) is confirmed,
the resulting proposal reuses the existing generic Pending Approvals card
(`my-day-approvals.html`), same as Tier 2's own proposal and the same
precedent `REQ-SB-55-US-01`/`REQ-SB-57-US-01` already established for their
own new approval kinds. If the alternative (direct Synthesizer call) is
confirmed instead, no new screen region is needed either — its effect is
observed as an ordinary Glimpse update, already covered by `REQ-SB-57-US-01`'s
own screens note.

**Open scope question #1 (retrofit scope) — RESOLVED, not open:** the
operator answered directly during this `/spec` pass: "There is no Retrofit
we Will Redo everything any way and replace it with pipeline." Recorded in
`## Context` and `## Non-Goals` above — `REQ-SB-08`/`09`/`10`'s current
modules are explicitly untouched by this story; they are superseded, not
bridged, whenever a future requirement replaces their pipelines. This
question does NOT contribute to this story's `gate: flagged` status.

**Open scope question #2 (cross-cutting-update trigger mechanism) —
genuinely open, this is why `gate: flagged` (MUST-FLAG trigger 8):**

Both options are real, buildable, and equally defensible — the PRD's own
text names them as the two live candidates without preferring either:

- **Option A — direct Agent-to-Agent call into `REQ-SB-57`'s Synthesizer.**
  Lower latency, no human friction for what may often be a routine,
  obviously-correct cross-reference; but introduces a new call shape this
  codebase doesn't have yet (an Expert-tier agent calling a Producer-tier
  mechanism synchronously mid-pipeline, outside the Pending-Approval
  pattern), and risks a wrong or low-confidence cross-reference being
  applied with no operator checkpoint.
- **Option B — Pending Approval, mirroring the already-proven Tier-2
  mechanism.** Reuses `ADR-021` point 5's exact, already-shipped
  create-then-finalize shape (`pending_approval_registry.
  create_pending_approval` → operator approves → a `finalize_*` handler
  performs the deferred action) — no new call contract is invented.
  Approval, once granted, would perform a write that itself becomes new
  evidence, letting `REQ-SB-57`'s own already-designed evidence-change
  trigger fire normally afterward — no bespoke second write path into
  Glimpse is needed. Keeps every "the vault wants to change something
  beyond the obvious new note" decision inside the ONE approval surface the
  operator's own words describe ("the vault will be asking for approval of
  stuff if it needs my validation"). Costs an extra human step even when
  the cross-reference is obviously correct.

**RESOLVED 2026-08-16 — operator confirmed Option B (Pending Approval).**
The candidate answer proposed by this pass, confirmed as-is after review:
Option B requires no new architectural call shape (reuses `ADR-021`'s own
proven pattern verbatim), keeps ALL "vault wants to change something
beyond the obvious new note" decisions inside one existing, familiar
approval surface (directly matching the operator's own quoted framing),
and errs toward the same conservative, human-checkpointed default Tier 2
already established for exactly this class of "not the obvious placement"
decision. `T03` (cross-cutting-update detection + trigger) is unblocked —
build it against Option B: a new Pending Approval kind, created via
`pending_approval_registry.create_pending_approval` mirroring `_create_
tier_2_proposal`'s own shape, finalized via a new `finalize_*` handler
that performs the deferred cross-reference write, letting `REQ-SB-57`'s
own already-designed evidence-change trigger fire normally afterward —
no bespoke second write path into Glimpse.

**No other trigger fired:** no material assumption beyond the one flagged
above; `REQ-SB-63` carries no `<!-- Draft -->` marker in the PRD; no ADR
was created by this pass (extending an already-`Accepted` ADR-021 module
with a new caller and a new decision outcome is implementation-latitude
composition, not a new tool/framework/structural boundary — trigger 3 is
architect-scoped, not applicable to the analyst); no `ESCALATIONS.md` entry
was written — this is a forward, PRD-acknowledged design question awaiting
operator confirmation, not a backward pipeline step or an out-of-scope
event; not oversized — one generalized entry point plus one proof-of-concept
integration point plus one new decision outcome, kept as one story since
they are all facets of the same "one master" mechanism, not independently
designed things; no contradictory PRD inputs.

**What to do next (superseded by the architect pass below — the decomposer
runs next, not a second `/plan-tasks` invocation):** ~~`/plan-tasks
REQ-SB-63-US-01` — both open questions are resolved, `T03` can be locked
against Option B.~~

---

**Architect pass, 2026-08-16 (`/plan-tasks` step 1):**

- **Independently verified, not taken on faith:** this story's own Context
  argues extending `vault_filing_expert.py`/`ADR-021` with a new caller and
  a new decision outcome is implementation-latitude composition, not a new
  ADR. Confirmed correct by direct inspection this pass:
  - **New caller:** `determine_placement_and_file` is already, today, a
    plain business-layer function called directly by THREE structurally
    different real sites (`agents_router.py`'s chat-attachment handler,
    `knowledge_bootstrap.py`'s delegated-research chain, `knowledge_gap_
    tracking.py`'s human-answer/research-closing paths) — a fourth caller
    (a `REQ-SB-55` Pipeline Job) composes it exactly the same way
    `knowledge_gap_tracking.py` already does. No new call topology.
  - **New decision outcome:** the operator-confirmed Option B (Pending
    Approval) is EXACTLY the case `ADR-021`'s own Consequences already
    pre-authorized verbatim: "A future second Tier-2-shaped action...
    reuses the same `payload` field and `_APPROVAL_HANDLERS` dispatch-
    table pattern rather than inventing a third approval mechanism." No
    new call contract, no new persisted store, no new tool/framework.
  - **Conclusion: no new ADR.** `Implementation/Architecture/ADR.md` is
    unchanged by this pass.
- **Architecture scope:** §"The Librarian — Vault Filing Expert generalized
  to a Pipeline-Job caller + cross-cutting-update detection" (`Implementation/
  Architecture/architecture.md`, appended directly after the existing
  §"Vault Filing Expert — placement decision, Tier-1 write, Tier-2 approval
  override" section). Also read, for context the coder must not deviate
  from: §"Vault Filing Expert..." itself (`ADR-021`, the unmodified base
  mechanism), the amendment appended to §"Email Capture & Threading
  Pipeline — First Concrete Pipeline"'s own Fork/merge-shape bullet (the
  new `consult_librarian` branch Job, `REQ-SB-55`'s own pipeline), and
  §"Vault Knowledge Model Redesign..." (`REQ-SB-54`/`ADR-042`) for
  `captures.md`'s own operator-only invariant, which the finalize handler's
  write must not violate.
- **This pass DOES make one real, disclosed design decision the story/PRD
  did not itself specify — the concrete shape of "the deferred cross-
  reference write":**
  1. `determine_placement_and_file` gains an additive, keyword-only
     `already_filed_path: str | None = None` parameter (all 3 existing
     callers unaffected) — when set, skips the Tier-1/Tier-2 write branch
     (the content is already filed at a Pipeline-controlled deterministic
     path) and runs hub-linking against that path instead.
  2. The model's own JSON decision gains one additive field,
     `"cross_cutting_implication": {"customer": str|null, "partner":
     str|null, "reason": str} | null`, evaluated in the SAME completion —
     re-checked in Python against `known_customers`/`known_partners` and
     against the SAME decision's own `referenced_customer`/`referenced_
     partner`, never trusted from the model alone.
  3. A new, independent Pending Approval (`action_id=
     "propose_cross_cutting_update"`), created via `_create_cross_cutting_
     proposal` (mirrors `_create_tier_2_proposal`).
  4. A new `finalize_cross_cutting_update`, registered in `pending_
     approvals_router.py`'s existing `_APPROVAL_HANDLERS`, writes an
     additive `customer/<slug>`/`partner/<slug>` TAG onto the already-filed
     note (reusing `REQ-SB-55-US-01-T01`'s own new unconditional
     frontmatter-key setter) — the already-`Accepted` `ADR-004` tag idiom,
     never `captures.md` (operator-only, `ADR-042`).
  Full reasoning: `Implementation/Architecture/architecture.md` → "The
  Librarian...".
- **Honest, disclosed forward dependency, not silently assumed satisfied:**
  this story's own design intent (a write that "becomes new evidence,
  letting `REQ-SB-57`'s own already-designed evidence-change trigger fire
  normally afterward") assumes a discovery mechanism `REQ-SB-57` (still
  `Draft`, not yet architected) has not actually committed to. The tag
  write above is real, immediately vault-visible evidence (satisfying this
  story's own Scenario 3 "never silently dropped" bar) but will not, on its
  own, cause a Glimpse to regenerate until `REQ-SB-57` is built and
  extended to scan for it. NOT a blocking prerequisite for this story's own
  Definition of Done — the Pending Approval and the tag write are both
  fully buildable and verifiable today.
- **`gate: flagged`, trigger-1 (material assumption), NOT trigger-3** — no
  ADR was created or changed, so the ADR-review trigger does not apply; the
  concrete write mechanism above (parameter shape, tag convention) is a
  real architect-authored design filling a gap the story/PRD left open,
  flagged for a human look before the decomposer's tasks lock in around it,
  mirroring `REQ-SB-56-US-01`/`REQ-SB-57-US-01`'s own "architect proposes a
  concrete answer, operator confirms" precedent. Per `Pipeline.md`'s gating
  contract this does NOT halt the stage — the decomposer runs next. A
  `REVIEW-QUEUE.md` pointer was written.
- No `ESCALATIONS.md` entry — nothing in this pass contradicts an
  `Accepted` ADR, the PRD, or a `MEMORY.md` constraint; the design above
  extends `ADR-021`/`ADR-004`/`ADR-042` without reopening any of them, and
  `REQ-SB-57`'s own not-yet-built state is already correctly framed as
  "Related to," never "Blocked by," in this story's own `## Dependencies`
  — no factual inaccuracy to escalate.

**What to do next (superseded by the decomposer pass below):** ~~the
decomposer runs next (`/plan-tasks` step 2) — proceed directly, no
separate `/plan-tasks` re-invocation needed.~~

gate: flagged 2026-08-16 — trigger-1 (material assumption: the concrete
shape of "the deferred cross-reference write" was designed by this pass,
not specified by the story/PRD). No new ADR was needed — independently
verified, not taken on faith. A `REVIEW-QUEUE.md` entry has been added.

---

**Decomposer pass, 2026-08-16 (`/plan-tasks` step 2):**

- **All 6 untagged scenarios locked, no exceptions.** `AC-01`..`AC-06`
  assigned in scenario order, tightened to name the architect's own
  concrete shape verbatim (`already_filed_path`, `cross_cutting_
  implication`, `propose_cross_cutting_update`, `finalize_cross_cutting_
  update`) so the coder builds directly against the real design rather
  than the story's own original, deliberately-open prose. No AC was
  marked `locked: false` — every scenario is buildable and verifiable
  today against the architect's own already-concrete pass; nothing here
  needed a second open question.
- **3 tasks, matching the analyst's own original count, but `T01`/`T03`'s
  own boundary was redrawn around the architect's concrete design rather
  than kept as the analyst's original single "trigger mechanism" task:**
  `T01` (`vault_filing_expert.py`/`vault_filing_methodology.py`) owns
  BOTH the additive `already_filed_path` parameter AND the
  `cross_cutting_implication` detection/proposal-creation half — both
  live in the same file, both evaluated in the SAME model completion, and
  both are genuinely one cohesive "generalize the entry point" unit, not
  two. `T02` (`email_classification.py`/`email_capture_pipeline.py`/one
  small new `vault_writer.read_body_section` reader) owns the pipeline
  wiring — the one concrete `REQ-SB-55` integration point. `T03`
  (`vault_filing_expert.py`/`pending_approvals_router.py`) owns ONLY the
  deferred finalize/write handler — a different file (the Approve
  dispatch table), mirroring `ADR-021`'s own real, already-shipped
  `_create_tier_2_proposal`/`finalize_new_top_level_area` propose/
  finalize split exactly (confirmed by direct reading of the real,
  current `vault_filing_expert.py` this pass, not assumed).
- **`T02`'s own new `vault_writer.read_body_section(path, header)`
  reader is a small, undesigned gap this pass found and closed, not
  silently improvised:** the architect's own design says `Consult-
  Librarian` passes "the Thread's own regenerated `## Summary`" as
  `content`, but no existing `vault_writer` primitive reads a body
  section's own text back (`replace_body_section` only WRITES a region;
  `REQ-SB-55-US-01-T01`'s own new primitive only APPENDS). `read_body_
  section` reuses `replace_body_section`'s own header/next-header
  location regex verbatim (never a second, divergent header-finding
  mechanism) — a mechanical, same-pattern extension of an already-
  established shape, logged here per this project's own "log a scope-
  internal judgement call, don't silently expand or block" precedent
  (`Learnings.md`, `SPRINT-037`). Not a MUST-FLAG trigger on its own —
  purely mechanical, zero business-logic judgement, zero new call
  topology.
- **Real, honest cross-story `depends_on` edges recorded, not
  assumed satisfied:** `T02` depends on `REQ-SB-63-US-01-T01` (needs the
  generalized `already_filed_path` parameter) AND on `REQ-SB-55-US-01-
  T03` (`Thread-Match/Merge`, `Ready` — supplies `thread_result["thread_
  path"]`), `REQ-SB-55-US-01-T04` (`Route-to-Project`, `Ready` — the
  Consult-Librarian branch must never gate it, confirmed against that
  task's own real, already-written Constraints), and `REQ-SB-55-US-01-
  T07` (`Pipeline assembly`, `Ready` — `email_capture_pipeline.py` itself
  does not exist until that task lands; `T02` adds a 6th node into the
  graph `T07` compiles). All three `REQ-SB-55-US-01` tasks are real,
  already-decomposed, `Ready` task files (confirmed by direct reading
  this pass, not taken on faith) — this is a genuine cross-story
  dependency, not a placeholder. `T03` depends on `REQ-SB-63-US-01-T01`
  (the proposal's own payload shape) and `REQ-SB-55-US-01-T01` (`vault_
  writer.py` new primitives, `Ready` — the unconditional frontmatter-key
  setter `finalize_cross_cutting_update` reuses for the tag write).
  Acyclic: every cross-story edge points at an already-existing,
  earlier-numbered task in a sibling story; no task in this story is
  named back by any `REQ-SB-55-US-01` task's own `depends_on`.
- **Story `status:` advances `Draft` → `Ready`:** every AC is locked
  (a), every locked AC has at least one AC-ID-tagged verification step
  across `T01`-`T03` (b, confirmed: `AC-01`/`AC-02`/`AC-05` each appear
  in both `T01` and `T02`, `AC-03` appears in both `T01` and `T03`,
  `AC-04` appears in `T01`, `AC-06` appears in `T02`), and `depends_on`
  is acyclic (c). All three task files' own `status:` set to `Ready` in
  lockstep, per this role's own standing "status moves in lockstep with
  the story" rule — a `Ready` story with still-`Draft` tasks would stall
  the build loop.
- **`gate: flagged` STAYS flagged, unchanged from the architect pass —
  this is a breadcrumb for human review of the designed write-shape, not
  a blocker.** No new MUST-FLAG trigger fired during this pass on its
  own account (the `read_body_section` addition above is mechanical, not
  a material assumption; no new ADR, no new `<!-- Draft -->` reliance, no
  contradictory inputs, no oversized task — the heaviest task, `T01`,
  stays inside one file plus one prompt-instructions file, mirroring the
  already-`Done` `REQ-SB-35-US-01-T02`'s own comparable single-completion
  grounded-decision shape). Per `Pipeline.md`'s gating contract, `status`
  and `gate` are independent axes — this story is `Ready` AND `flagged`
  simultaneously until the human confirms the architect's designed write
  shape in `REVIEW-QUEUE.md`.
- No new `ESCALATIONS.md` entry — nothing in this pass contradicts an
  `Accepted` ADR, the PRD, a `MEMORY.md` constraint, or a sibling story's
  own already-decomposed tasks; the three real `REQ-SB-55-US-01` cross-
  story dependencies above were independently confirmed by direct
  reading, not assumed.

**What to do next:** eligible for `/plan-sprints` (status `Ready`,
ungrouped — no `sprint:` set). The open `REVIEW-QUEUE.md` item (architect's
designed write-shape) remains outstanding and does not block sprint
planning or the build loop picking up these tasks; it awaits a human
decision independent of delivery progress, per this story's own gate
reasoning above.

---

**Coder pass, 2026-08-16 (`/implement-sprint`, `SPRINT-050`) — story
closes:** all 3 tasks (`T01`, `T02`, `T03`) built and verified `Done`, in
dependency order (`T01` → `T02`/`T03` in parallel by file scope, `T02`
built last this session). All 6 locked ACs (`AC-01`..`AC-06`) verified
live, AC-ID-tagged, across `T01`/`T02`/`T03`'s own Implementation Logs —
no locked AC blocked or weakened. Story `status:` set to `Done` above.
`gate: flagged` STAYS flagged, unchanged — the architect's own designed
write-shape (trigger-1) remains an open `REVIEW-QUEUE.md` item awaiting
human confirmation; a `Done` story with an unresolved `flagged` gate is
the correct, intended state per `Pipeline.md`'s "status and gate are
independent axes" contract, not a build blocker. `BACKLOG.md`'s `REQ-SB-63`
row and `SPRINT-050`'s own status/Retrospective are updated in lockstep by
this same pass — see `Implementation/Sprints/
SPRINT-050-the-librarian-vault-expert-central-authority.md`. No new
`ESCALATIONS.md` entry from this closing pass — nothing here contradicts
an `Accepted` ADR, the PRD, or a `MEMORY.md` constraint.
