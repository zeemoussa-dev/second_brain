---
id: REQ-SB-74-US-01
title: Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation
requirement_ids: [REQ-SB-74]
requirement_section: "REQ-SB-74: Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-055 created) — standing architect-level review item, unresolved by the coder, see REVIEW-QUEUE.md"
sprint: "SPRINT-068"
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-74-US-01 — Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation

## Story

**As a** Second Brain operator
**I want** the Librarian to propose, in batched per-Customer approvals, a real
Customer match for every real Unsorted Thread — writing its `customer`
frontmatter and correcting its `customer/<slug>` tag only after I approve that
Customer's whole batch — while also surfacing any existing Customer folder
that ends the pass with zero real Thread matches as an evidence-based
archival candidate
**So that** the real 137-Thread backlog gets routed to real Customers
(including brand-new ones like TAQA, created the same way any Customer
folder is created today) without a single silent write, and the noise left
over from an earlier unchecked extraction pass gets reconciled from real
evidence rather than a name guess — archived, never deleted

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-74: Customer Backfill —
  Propose/Approve Thread Routing + Noise Reconciliation*. Raised 2026-08-19,
  operator: "Start as well The Enrichement, Tags and Customers Back file From
  the data." Scoped down through 3 direct clarifying questions (noise
  cleanup, backfill method, tag scope) — operator confirmed "Archive noise,
  then backfill" and "Propose, then you approve" as given, and the operator's
  own free-text answer on tag scope ("Customer Backfill and Tag the Customer
  we will work more on Threads Later") is what bounds this story to
  Customer-tag correction only. No `<!-- Draft -->` marker on this
  requirement — finalized text.
- **Confirmed live against the real vault (2026-08-19, restated directly in
  the PRD entry):** `Work/Customers/` already has 26 OKF-conformant Customer
  folders (real accounts — ADNOC, Aldar, Masdar, G42, Mubadala, EWEC, SimplAI
  — mixed with confirmed noise — Apple, Google, Instagram, LinkedIn, Twitter,
  YouTube, Microsoft, NVIDIA, Razer — each an identical empty `## Glimpse`/
  `## Background` shell, `status: "active"`, from an earlier mechanical
  company-name-extraction pass with no correctness check). Zero of the real
  137 Threads have ever been routed — all still carry `customer: "Unsorted"`.
  A real, repeatedly-mentioned company (TAQA) has no folder at all.
- **This story follows the SAME propose-then-approve posture `REQ-SB-57`
  already established for `## Background` amendments, not a new mechanism.**
  Directly confirmed by reading the real, shipped
  `app/business/project_customer_synthesizer.py`: `_propose_background_
  amendment` creates a `pending_approval_registry.create_pending_approval`
  record with `trigger="direct"` and a structured `payload`;
  `finalize_background_amendment_proposal` performs the deferred write only
  once approved, via `app/api/pending_approvals_router.py`'s
  `_APPROVAL_HANDLERS` registry. This story's own two new proposal kinds
  (Customer-routing batch, archival candidate) reuse this exact shape.
- **This story is a new Job under the ALREADY-EXISTING "Librarian"
  Section/`librarian-housekeeping` Agent `REQ-SB-72-US-01` created — no new
  Section, no new Agent.** Directly confirmed by reading the real, shipped
  `app/business/pipelines/librarian_housekeeping.py` (`REQ-SB-72-US-01`,
  `Done`, `SPRINT-063`): `backfill_company_folders()` already proposes an
  `"ambiguous"` company mention via `_create_librarian_company_link_
  proposal`/`finalize_librarian_company_link` (registered in
  `_APPROVAL_HANDLERS` as `"propose_librarian_company_link"`), and a
  `"new_unambiguous"` mention already auto-creates its Customer folder via
  the unmodified `customer_hub_linking.ensure_customer_hub_note` — the exact
  mechanism this story reuses for the TAQA-shaped "new Customer" proposal
  (Scenario 3), except here EVERY match (existing or new) routes through an
  explicit approval, never an auto-create, because the PRD's own text is
  explicit: "never a silent write."
- **`ensure_customer_hub_note` (`app/business/customer_hub_linking.py`) is
  reused unmodified** for creating TAQA's (or any other new company's) OKF
  directory on approval — this story does not touch that function.
- **`pending_approval_registry.create_pending_approval`/`resolve_pending_
  approval` (`app/business/pending_approval_registry.py`) are reused
  unmodified** — `payload` is already documented as additive (`ADR-021`
  point 4: "carries whatever structured data a deferred action needs to
  actually execute once approved"), which is what accommodates this story's
  own new batched-per-Customer shape (a payload naming MULTIPLE target
  Thread paths under one approval decision) without changing the registry's
  own create/resolve contract.
- **Genuinely new grouping shape, disclosed by the PRD itself as a design
  choice for `/plan-tasks` to size, not pre-decided by the operator:** every
  existing Pending Approval in this codebase (Background amendment,
  cross-cutting update, librarian company link, route-to-project) targets
  exactly ONE note. This story's own Customer-routing proposal targets
  potentially MANY Threads (all of them proposed for the same Customer)
  under ONE approval decision — "the practical scale this needs to actually
  get reviewed," per the PRD's own words. See `## Notes` for why this is
  judged a mechanism-sizing question, not a scope ambiguity (trigger 8).
- **Evidence-based noise reconciliation, not name-guessed:** the PRD is
  explicit that several of the 26 existing folder names are genuinely
  ambiguous without checking real Thread evidence (Columbus, Sindan, AZCON
  Holding, HR Avatar) — deliberately NOT hand-classified in this pass. A
  folder is only proposed for archival if this pass's own real Thread-match
  evidence finds zero matches for it — never from its name alone.
- **Explicitly deferred, not this requirement's scope** (operator's own
  words this same conversation: "we will work more on Threads Later"):
  - Project-level routing (Thread → Project beneath a Customer) — untouched;
    this requirement only reaches Customer, one level up.
  - Pipeline-stage or topic/content tags on Threads — the deeper Thread
    taxonomy question stays open for a later conversation; the only tag
    change here is correcting the existing `customer/<slug>` tag element.
  - Wiring `synthesize_customer`/`resync_project_from_thread` into the live
    capture pipeline (`#128`, still parked) — this story writes `customer:`
    frontmatter directly via the approval handler; it does NOT call
    `synthesize_customer` as a side effect. A routed Thread's Customer
    `## Glimpse` stays exactly as empty as it is today.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: The Librarian proposes a Customer match per Unsorted Thread, grouped into ONE batched Pending Approval per proposed Customer

```gherkin
Given one or more real Threads still carrying customer: "Unsorted" whose own
    subject/participants/message content give a clear signal of the same
    real Customer (an existing folder among the real 26, or a clearly-named
    real company with none yet)
When the Librarian's Customer backfill Job runs
Then exactly one Pending Approval record is created per distinct proposed
    Customer, its payload naming every one of that Customer's matched
    Thread paths together
  And no Thread's customer frontmatter or tags are written yet — this is a
    proposal, never a silent write
```
<!-- AC-ID: REQ-SB-74-US-01-AC-01 -->

### Scenario 2: Approving a batch writes customer frontmatter and corrects the customer/<slug> tag for every Thread in it

```gherkin
Given a pending, batched Customer-routing approval naming N real Unsorted
    Threads matched to the same proposed Customer
When the operator approves that batch
Then every one of the N Threads' customer frontmatter is written to the
    approved Customer name
  And each of those N Threads' tags list entry customer/unsorted is
    corrected to the real customer/<slug> for the approved Customer, in the
    same write
  And no Thread outside this batch is touched
```
<!-- AC-ID: REQ-SB-74-US-01-AC-02 -->

### Scenario 3: A real company with no existing folder is proposed as a NEW Customer and created via ensure_customer_hub_note on approval

```gherkin
Given a real Unsorted Thread whose content clearly names a real company
    (e.g. TAQA) with no matching folder among the real 26 existing Customer
    folders
When the Librarian's Customer backfill Job runs
Then that company is proposed as a NEW Customer in its own batched Pending
    Approval, distinct from any existing-folder batch
When the operator approves that batch
Then the new Customer's OKF-conformant folder is created via the existing,
    unmodified ensure_customer_hub_note mechanism
  And every Thread in that batch receives the new Customer's frontmatter
    and corrected customer/<slug> tag, in the same approval
```
<!-- AC-ID: REQ-SB-74-US-01-AC-03 -->

### Scenario 4: An existing Customer folder that ends the pass with zero real Thread matches is surfaced as an archival candidate

```gherkin
Given an existing Customer folder among the real 26 that received no real
    Thread match during this backfill pass
When the Librarian's Customer backfill Job completes
Then that Customer folder is surfaced as its own explicit "no evidence
    found — candidate for archival" Pending Approval
  And no folder is ever classified as an archival candidate from its name
    alone — only from this pass's own real, zero-match evidence
```
<!-- AC-ID: REQ-SB-74-US-01-AC-04 -->

### Scenario 5: Approving an archival-candidate proposal moves the folder to Work/Archive/Customers/, content unchanged, never deleted

```gherkin
Given a pending archival-candidate approval for an existing Customer folder
    with zero real Thread matches
When the operator approves it
Then the whole folder is moved to Work/Archive/Customers/ with every one of
    its files' content byte-for-byte unchanged
  And the folder is never deleted — archive-not-delete, this project's
    standing value
```
<!-- AC-ID: REQ-SB-74-US-01-AC-05 -->

### Scenario 6: Declining a proposed Customer-routing batch leaves every one of its Threads' customer frontmatter and tags unchanged

```gherkin
Given a pending, batched Customer-routing approval naming one or more real
    Unsorted Threads
When the operator declines that batch
Then none of the named Threads' customer frontmatter or tags are modified
  And every one of them stays exactly customer: "Unsorted" /
    customer/unsorted, as if the proposal never ran
```
<!-- AC-ID: REQ-SB-74-US-01-AC-06 -->

### Scenario 7: Declining an archival-candidate proposal leaves the existing Customer folder exactly where it is

```gherkin
Given a pending archival-candidate approval for an existing Customer folder
When the operator declines it
Then the folder stays at its current location under Work/Customers/,
    completely unchanged
```
<!-- AC-ID: REQ-SB-74-US-01-AC-07 -->

### Scenario 8: A Thread with no clear Customer signal in its own content is left Unsorted — never a forced guess

```gherkin
Given a real Unsorted Thread whose own subject/participants/message content
    give no clear signal of any real Customer
When the Librarian's Customer backfill Job runs
Then that Thread is not included in any proposed batch
  And its customer frontmatter stays "Unsorted"
```
<!-- AC-ID: REQ-SB-74-US-01-AC-08 -->

### Scenario 9: Re-running the backfill Job after some batches are already approved never re-proposes an already-routed Thread

```gherkin
Given a real Thread whose batch was already approved, whose customer
    frontmatter and customer/<slug> tag are already correctly routed
When the Librarian's Customer backfill Job runs again
Then that Thread is not included in any new proposal
  And only Threads still carrying customer: "Unsorted" are ever considered
    by a subsequent run
```
<!-- AC-ID: REQ-SB-74-US-01-AC-09 -->

## Affected Screens

- `html-prototype/my-day-approvals.html` — reused generically, no new screen
  region. Each batched Customer-routing proposal (Scenarios 1–3) and each
  archival-candidate proposal (Scenario 4) renders as one more `.item-row`
  using the exact existing title + `badge-warning` "Awaiting approval" +
  free-text `.item-row-meta` lines + Approve/Decline `.item-row-actions`
  shape this page already uses for its two current examples (Meeting
  Capture, People Notes). No new component, state, or layout is needed.

## Dependencies

- **Blocked by (hard):** `REQ-SB-54` (Vault Knowledge Model Redesign — OKF
  directory shape, `Done`) — `ensure_customer_hub_note`/`customer_directory_
  paths` this story reuses unmodified for both existing-folder and
  new-Customer routing.
- **Blocked by (hard):** `REQ-SB-57` (Project & Customer Status Synthesizer
  Agents, `Done`) — establishes the exact propose-via-Pending-Approval,
  finalize-on-approve posture (`_propose_background_amendment`/`finalize_
  background_amendment_proposal`) this story's own two new proposal kinds
  mirror structurally.
- **Blocked by (hard):** `REQ-SB-72-US-01` (The Librarian Section — First
  Housekeeping Pipeline, `Done`, `SPRINT-063`) — this story's new Job lives
  in the SAME already-existing `librarian_housekeeping.py` module, Section,
  and Agent, and reuses `backfill_company_folders`'s own propose/finalize
  shape (`_create_librarian_company_link_proposal`/`finalize_librarian_
  company_link`) as its nearest structural precedent.
- **Related to:** `REQ-SB-71` (Redesigned Email & Meeting Capture, `Done`)
  — the real 137-Thread corpus and `customer: "Unsorted"` placeholder this
  story backfills.
- **Related to:** `REQ-SB-73` (Bidirectional Thread ↔ Message Linking,
  `Draft`) — same Librarian module, no direct dependency (a separate Job,
  independently orderable in `run_housekeeping_pass()` or its own
  manually-triggered entry point).
- **External:** none new.

## Constraints

- **Never a silent write** — every Thread routing and every folder archival
  goes through an explicit Pending Approval; no auto-create, auto-route, or
  auto-archive, even for a high-confidence match.
- **Reuses the existing `pending_approval_registry.create_pending_approval`/
  `resolve_pending_approval` contract unmodified** — the batched-per-Customer
  grouping is a payload-shape extension (a list of target Thread paths under
  one record), not a new registry mechanism (`ADR-021` point 4's own
  "additive payload" precedent).
- **New Customer creation uses `ensure_customer_hub_note` unmodified** —
  never reinvented.
- **This is a Job under the SAME already-existing Librarian Section/
  `librarian-housekeeping` Agent** (`REQ-SB-72-US-01`) — no new Section, no
  new Agent.
- **Manually-triggered, one-time backfill — NOT wired into `run_housekeeping_
  pass()`'s own recurring schedule chain.** This requirement is explicitly
  kept separate from live/ongoing capture, which stays manual
  (`REQ-SB-70`/`71`'s standing constraint, reaffirmed by the operator this
  same conversation).
- **Archival is never a delete** — archive-not-delete, this project's
  standing value.
- **Project-level routing (Thread → Project) stays untouched** — this
  requirement only reaches Customer, one level up.
- **Pipeline-stage or topic/content tags on Threads are out of scope** — the
  only tag change is correcting the existing `customer/<slug>` element.
- **`synthesize_customer`/`resync_project_from_thread` are NOT called as a
  side effect of this requirement's writes** — a routed Thread's Customer
  `## Glimpse` stays exactly as empty as it is today until that separate,
  still-parked decision (`#128`) is made.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this. Task count/shape is provisional
until the architect resolves the mechanism-level open questions in ## Notes
(batched-approval payload shape, Customer-match detection call, and the new
OKF-directory-move primitive for archival). -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-74-US-01-T01 | backend | `propose_customer_backfill()` Job — new `compass_client.detect_customer_for_thread`, new `vault_writer.list_customer_folders()`, per-Thread Customer-match detection (skipping already-routed Threads), grouped into per-Customer batched Pending Approval payloads (existing-match + new-Customer batches), `action_id="propose_customer_backfill_routing"` | `app/data_access/compass_client.py`, `app/data_access/vault_writer.py`, `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-74-US-01-T01-propose-customer-backfill-job.md` |
| REQ-SB-74-US-01-T02 | backend | `finalize_customer_backfill_routing(payload)` — writes `customer` frontmatter + corrects the `customer/<slug>` tags-list element for every Thread in an approved batch; creates a NEW Customer folder via unmodified `ensure_customer_hub_note` when the batch's proposed Customer has no existing folder | `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-74-US-01-T02-finalize-customer-backfill-routing.md` |
| REQ-SB-74-US-01-T03 | backend | `propose_customer_archival_candidates(matched_existing_customer_names)` Job — surfaces every `list_customer_folders()` entry NOT in that set as its own archival-candidate Pending Approval, `action_id="propose_customer_archival_candidate"` | `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-74-US-01-T03-propose-customer-archival-candidates.md` |
| REQ-SB-74-US-01-T04 | backend | New generic `vault_writer.move_okf_directory()` cross-parent archival-move primitive + `finalize_customer_archival(payload)` — moves the approved Customer folder to `Work/Archive/Customers/`, content byte-for-byte unchanged by construction | `app/data_access/vault_writer.py`, `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-74-US-01-T04-finalize-customer-archival.md` |
| REQ-SB-74-US-01-T05 | backend | Register `finalize_customer_backfill_routing`/`finalize_customer_archival` in `_APPROVAL_HANDLERS` under their own new `action_id`s + new `POST /poc/librarian-propose-customer-backfill` endpoint (orchestrates `propose_customer_backfill()` then `propose_customer_archival_candidates()` in one pass) — manually-triggered only, NOT wired into `run_housekeeping_pass()` | `app/api/pending_approvals_router.py`, `app/api/email_poc_router.py` | `../Tasks/REQ-SB-74-US-01-T05-approval-wiring-and-endpoint.md` |
| REQ-SB-74-US-01-T06 | backend | One-time backfill run against the real 137-Thread corpus via the real endpoint, at least one real approve round trip, then a re-run confirming an already-routed Thread is never re-proposed (Scenario 9) | `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-74-US-01-T06-backfill-run-and-idempotency-verification.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — manual mode still in effect, per `Implementation/Pipeline.md`
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Project-level routing** (Thread → Project beneath a Customer) — stays
  untouched; this requirement only reaches Customer, one level up.
- **Pipeline-stage or topic/content tags on Threads** — the deeper Thread
  taxonomy question stays open for a later, separate conversation.
- **Wiring `synthesize_customer`/`resync_project_from_thread`** into this
  write path or into live capture (`#128`, still parked) — a routed
  Thread's Customer `## Glimpse` stays exactly as empty as it is today.
- **Hand-classifying any of the 26 existing folders by name alone**
  (Columbus, Sindan, AZCON Holding, HR Avatar, etc.) — evidence-based only,
  per this pass's own design.
- **Wiring this Job into `run_housekeeping_pass()`'s recurring schedule** —
  manually-triggered one-time backfill only, per the standing `REQ-SB-70`/
  `71` "live/ongoing capture stays manual" constraint.
- **Any new `html-prototype/` screen** — `my-day-approvals.html`'s existing
  generic `.item-row` pattern covers both new proposal kinds with no new
  screen region.

## Notes

**Prototype parity** (`html-prototype/my-day-approvals.html`):

- `.item-row` title + `badge-warning` "Awaiting approval" — **Specced**,
  reused verbatim for both new proposal kinds this story adds (Customer-
  routing batch, archival candidate).
- `.item-row-meta` free-text description lines — **Specced**, already
  renders arbitrary description text (the page's own existing "Proposes:
  ..." convention); this story's own batch-size/Thread-list summary and
  archival-candidate reasoning render through this SAME already-generic
  mechanism. Exact wording (e.g. whether a large batch's meta line lists
  every Thread or shows a count) is a decomposer/coder detail, not a new UI
  element — see mechanism item 5 below.
- Approve/Decline `.item-row-actions` — **Specced**, reused verbatim.
- `.state-switcher` (populated/empty) — **Specced/unaffected**, already
  covers "nothing pending" generically.
- Header copy, sidebar nav, footer disclaimer text — **Unaffected**, no
  change.

**Mechanism-level questions left to `/plan-tasks`, not resolved by this pass
(the Gherkin above specifies the OUTCOME, not the mechanism — mirrors
`REQ-SB-73-US-01`'s own identical precedent):**

1. **The batched-per-Customer Pending Approval payload shape** (a list of
   Thread paths under one record) — the PRD's own text explicitly names
   this as "a genuinely new grouping shape for Pending Approvals, disclosed
   here as a design choice for `/plan-tasks` to size, not pre-decided by
   the operator." Scope is fully decided (one approval per proposed
   Customer, covering every Thread matched to it this pass); only the
   payload/registry-rendering mechanism is left open.
2. **The exact Customer-match detection call** — a new `compass_client`
   function, or a reuse/extension of `detect_mentioned_companies_for_
   thread`'s own existing shape (`REQ-SB-72-US-01-T05`) — left to the
   architect.
3. **The new "move a whole OKF-conformant directory to a different parent
   path" data_access primitive for archival** — no existing primitive
   covers this exactly: `rename_thread_directory` only handles a
   same-parent rename (old slug → new slug, same directory), and `move_
   note_and_attachments` only handles a single note + its sibling
   `attachments/` folder, not a 4-file OKF directory
   (`index.md`/`<slug>.md`/`log.md`/`captures.md`). Left to the architect,
   mirroring `rename_thread_directory`'s own atomic-move discipline.
4. **Exact new endpoint route name(s)** — follows the existing
   `/poc/librarian-*` convention already established by `REQ-SB-72-US-01-
   T08`; no specific route is asserted here.
5. **Whether a large batch's `.item-row-meta` line lists every Thread or
   summarizes with a count** — the existing free-text meta-line pattern
   supports either without a new UI element; left as a decomposer/coder
   wording detail.

**Why this does NOT trip trigger 1 (material assumption):** every open item
above is a MECHANISM question this project's own role boundaries assign to
the architect at `/plan-tasks` — the PRD's own text (confirmed live against
the real vault, 3 clarifying questions already answered by the operator this
same conversation) resolves every SCOPE-level question directly: what gets
proposed, how it's batched, what happens on approve/decline for both
proposal kinds, and the explicit deferrals. This pass adds no scope the PRD
did not already state.

**Why this does NOT trip trigger 2:** `REQ-SB-74` carries no `<!--
Draft -->` marker in the PRD — its own footnote confirms the noise-cleanup/
backfill-method/tag-scope questions were each individually put to the
operator and answered directly ("Archive noise, then backfill", "Propose,
then you approve", "Customer Backfill and Tag the Customer we will work
more on Threads Later").

**Why this does NOT trip trigger 3:** ADR creation/change is the
architect's own trigger, not this role's — this pass discloses the bounded
mechanism items above but does not itself create or edit
`Implementation/Architecture/ADR.md`.

**Why this does NOT trip trigger 4:** no `ESCALATIONS.md` entry was
written — nothing in this pass is a backward pipeline step or an
out-of-scope event.

**Why this does NOT trip trigger 5 (oversized):** 6 starting tasks —
comparable to `REQ-SB-73-US-01`'s own 4 and well under `REQ-SB-72-US-01`'s
proven 9-task ceiling for the SAME module — not oversized.

**Why this does NOT trip trigger 7:** no contradictory PRD inputs found —
direct reading of the real, already-shipped
`project_customer_synthesizer.py`/`pending_approval_registry.py`/
`customer_hub_linking.py`/`librarian_housekeeping.py`/`pending_approvals_
router.py` confirms every mechanism the PRD names (propose-then-approve
posture, `ensure_customer_hub_note`, Librarian Job pattern,
`_APPROVAL_HANDLERS` registry) already exists exactly as described, with no
discrepancy.

**Why this does NOT trip trigger 8:** the task brief itself raised whether
the batched-per-Customer grouping alone should trip this trigger — judged
NOT to, because the PRD's own text does not present multiple equally-valid
SCOPE interpretations or leave the requirement's intent unclear: it
explicitly decides the grouping granularity ("one approval decision covers
every Thread proposed for that same Customer") and explicitly frames the
remaining openness as a MECHANISM-sizing task for `/plan-tasks` — the exact
same disclosure shape `REQ-SB-73-US-01`'s own `## Notes` used for 4 separate
mechanism items (payload/registry shape, Job-chain placement,
section-ownership registration) without tripping gate. What's undecided
here is HOW the registry stores/renders a multi-target batch, not
WHETHER/WHAT to batch.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired (see the itemized
trigger-by-trigger reasoning above).

**What to do next:** eligible for `/plan-tasks REQ-SB-74-US-01` — the
architect resolves the 5 mechanism-level questions above (including the new
batched-approval payload shape and the new OKF-directory-move primitive),
then the decomposer locks ACs and writes tasks.

---

**Architect pass (`/plan-tasks` step 1, 2026-08-19):** all 5 mechanism-level
questions above resolved, one new ADR appended — [ADR-055](../Architecture/ADR.md)
(confirms, by direct reading, that the batched-per-Customer multi-target
Pending Approval payload needs ZERO change to `pending_approval_registry.py`
or `pending_approvals_router.py` — both were already fully payload-shape-
agnostic; adopted as this codebase's new canonical shape for any future
multi-target approval. Plus: a new `compass_client.detect_customer_for_
thread`, narrower sibling of `classify_task`; a new `vault_writer.list_
customer_folders()` enumeration, deliberately distinct from the existing
`list_known_customers()`; and a new generic `vault_writer.move_okf_
directory()` cross-parent archival-move primitive targeting the already-
provisioned `Work/Archive/Customers/`). Full mechanism detail: "The
Librarian — Customer Backfill" in `Implementation/Architecture/
architecture.md`.

**Architecture scope:** §"The Librarian — Customer Backfill
(`REQ-SB-74-US-01`, see ADR-055)" (all subsections — detection, the new
`list_customer_folders()` enumeration, the propose/finalize Job pair, the
batched-payload convention, `move_okf_directory()`, and the endpoint/
scheduling posture) in `Implementation/Architecture/architecture.md` — this
is the coder's own bound at `/implement-sprint`.

**Gate:** `flagged` — `trigger-3` (this pass created `ADR-055`). Per
`Implementation/Pipeline.md`, this does NOT halt the stage: the decomposer
still runs, so the human reviews the ADR and the resulting tasks together in
one pass. See `REVIEW-QUEUE.md` → `REQ-SB-74-US-01`.

---

## Decomposer pass (`/plan-tasks` step 2, 2026-08-19)

**All 9 Gherkin scenarios above are locked as `REQ-SB-74-US-01-AC-01`
through `AC-09`**, one-to-one against the analyst's own untagged scenarios —
wording kept essentially verbatim (already precise and buildable; no scope
change), each AC-ID tag appended immediately after its own scenario's
closing Gherkin fence, all locked by default (none marked `locked: false` —
every locked AC has a real, observable outcome: a real batched Pending
Approval record with a real payload, real `customer`/`tags` frontmatter
writes, a real folder move under `Work/Archive/Customers/`, a real
unchanged-on-decline/unchanged-on-no-match state — none found unverifiable).

**Task table above supersedes the analyst's own 6-task starting point**,
grounded directly in `ADR-055`'s own real mechanism text (the new
`compass_client.detect_customer_for_thread`/`vault_writer.list_customer_
folders()`/`vault_writer.move_okf_directory()` primitives, the batched-
payload convention, the one-orchestrating-endpoint posture) rather than the
analyst's own pre-architecture guess. Dependency graph:

- `T01` (`propose_customer_backfill()` + its own two new data_access
  primitives) — the shared detection/grouping root every other task
  consumes. `depends_on: []`.
- `T02` (`finalize_customer_backfill_routing`) — the deferred-write half of
  `T01`'s own proposal; needs `T01`'s payload shape (`{"customer",
  "is_new_customer", "thread_paths"}`) settled first. `depends_on: [T01]`.
- `T03` (`propose_customer_archival_candidates`) — consumes `T01`'s own
  `list_customer_folders()` primitive AND its own returned `matched_
  existing_customer_names` (the one-evidence-pass design, `ADR-055` Decision
  5 — never a second, independently-run Compass sweep). `depends_on: [T01]`.
- `T04` (`move_okf_directory` + `finalize_customer_archival`) — the
  deferred-write half of `T03`'s own proposal; needs `T03`'s payload shape
  (`{"customer", "source_directory"}`) settled first. `depends_on: [T03]`.
- `T05` (`_APPROVAL_HANDLERS` registration + the one orchestrating endpoint)
  — needs every propose/finalize pair to exist before it can register or
  route to any of them. `depends_on: [T01, T02, T03, T04]`.
- `T06` (the real, full-corpus backfill run + a real approve round trip +
  re-run/no-re-propose verification) — needs the whole wired system,
  reachable via the real endpoint, plus a real approval actually resolved
  before Scenario 9's own "already-routed" precondition can exist for real.
  `depends_on: [T01, T02, T03, T04, T05]`.

No cycles.

**AC → task mapping:** AC-01/AC-08 → `T01` (the propose Job's own grouping
and honest-leave-Unsorted behavior, both directly verifiable by calling
`propose_customer_backfill()` against the real vault without needing the
approval round trip wired yet); AC-02/AC-03 → `T02` (the finalize handler's
own deferred-write behavior, verified by calling it directly against a real
or hand-constructed payload — existing-folder and new-Customer branches
both exercised); AC-04 → `T03`; AC-05 → `T04`; AC-06/AC-07 → `T05` (the
decline half of both proposal kinds — a real, observable property of the
EXISTING, unmodified `decline_pending_approval` endpoint, which never calls
any `_APPROVAL_HANDLERS` entry at all per direct reading of `pending_
approvals_router.py` — genuinely only provable once `T05`'s own real
`propose_*`/`approve`/`decline` endpoints are all wired together for a real
round trip); AC-09 → `T06` (idempotency proven for real, at full-corpus
scale, after a real approval — this task's own explicit mandate; a
Scenario whose own precondition, "some batches are already approved,"
cannot be honestly satisfied before `T02`/`T05` exist). Every locked AC has
at least one AC-tagged manual verification step in exactly the task named
above; no locked AC is left without a tagged step (confirmed by direct
cross-check against all 6 task files' own `## Tests` blocks before
finalizing this pass).

**No cross-story dependency with `REQ-SB-73-US-01`, confirmed directly** —
both stories add Jobs to the same `librarian_housekeeping.py` module and
both touch `email_poc_router.py`, but this story's own new functions
(`propose_customer_backfill`/`finalize_customer_backfill_routing`/`propose_
customer_archival_candidates`/`finalize_customer_archival`) neither call nor
are called by `REQ-SB-73-US-01`'s own `link_thread_messages`/`rename_
threads` fan-out, and this story's own new endpoint is a standalone,
deliberately-unscheduled route, never inserted into `run_housekeeping_
pass()` (the one function `REQ-SB-73-US-01-T03` also edits) — a real,
disclosed shared-file overlap, never a functional dependency. No
`depends_on` edge is added between the two stories' task sets.

**Why this pass does NOT fire a NEW trigger, beyond the architect's own
already-standing `ADR-055` flag (which this role does not clear, per
`Implementation/Pipeline.md`):**
- **Trigger 1 (material assumption):** no gap-filling assumption made —
  every task-shaping choice above (the `T01`→`T02`, `T03`→`T04` propose/
  finalize pairings, the `T05` all-four-dependency wiring point) follows
  directly from `ADR-055`'s own Decision text; the one non-ADR-dictated
  choice (splitting propose from finalize into sibling tasks, rather than
  one task each) mirrors this codebase's own already-established `REQ-SB-
  72-US-01-T07`-style "propose Job, then its own finalize handler, as
  build-order-sequenced siblings" precedent, not a new pattern invented
  here.
- **Trigger 5 (oversized):** 6 tasks — comparable to `REQ-SB-73-US-01`'s own
  4 and well under this project's own proven ceilings for this SAME module
  (`REQ-SB-72-US-01`'s 9-task/L shape); not oversized.
- **Trigger 6 (unverifiable AC):** every locked AC has a concrete, real,
  observable verification path (a real Pending Approval payload, real
  frontmatter/tags writes, a real folder move, a real declined-record
  no-op) — none found unverifiable.
- **Trigger 7 (contradictory inputs):** none found — `ADR-055`'s own text is
  internally consistent with the story's own Gherkin and Constraints.
- **Trigger 8 (multiple equally-valid / unclear):** the task split above is
  grounded directly in `ADR-055`'s own real mechanism text (which new
  primitive belongs to which propose/finalize pair, where the orchestrating
  endpoint sits), not a coin-flip among equally-valid shapes.

**Status:** `Draft → Ready` — every AC is locked, every locked AC has a
tagged verification step in at least one task, and `depends_on` is acyclic
(confirmed above). `gate` stays `flagged` (`gate_reason` unchanged —
`trigger-3`, `ADR-055`) — the decomposer does not clear an architect's own
ADR flag; the human reviews `ADR-055` and this pass's own 6 tasks together,
per the architect's own Notes above and the existing `REVIEW-QUEUE.md`
pointer. All 6 new task files are written at `status: Ready` in lockstep
with this story's own transition, per `Implementation/Pipeline.md`'s "task
status moves in lockstep with the story" rule.

**What to do next:** this story is now `status: Ready` with a complete,
locked task graph, but `gate: flagged` — per `Implementation/Pipeline.md`'s
"Promotion of a flagged item" human gate, the human resolves the flag (reads
`ADR-055` at `REVIEW-QUEUE.md`, reviews this pass's own 6 tasks alongside
it) before `/plan-sprints` picks this story up.

---

## Product-owner pass (`/plan-sprints`, 2026-08-19)

Grouped into its own single-story sprint, `SPRINT-068` — kept separate from
the sibling `REQ-SB-73-US-01` (`SPRINT-067`, also `Ready`/ungrouped this
pass) since the decomposer confirmed no task-level dependency between them
and combining would exceed this project's own proven 9-task single-sprint
ceiling. Full grouping rationale: `Implementation/Sprints/SPRINT-068-
customer-backfill-thread-routing-and-noise-reconciliation.md` → `##
Grouping Rationale & Sizing` / `## Notes`. This story's own `gate: flagged`
(`ADR-055`) is unchanged — the product-owner does not clear an architect's
own ADR flag; `SPRINT-068` itself is `gate: clear`, `status: Ready` (its
own grouping decision was unambiguous), eligible for `/implement-sprint
SPRINT-068` once `ADR-055` is reviewed.

---

## Coder pass (`/implement-sprint SPRINT-068`, 2026-08-19)

All 6 tasks built and live-verified against the real, configured vault —
`T01`→`T06`, dependency order, no task blocked. Every locked AC (`AC-01`
through `AC-09`) verified via a real, direct outcome (a real batched
Pending Approval payload, real `customer`/`tags` frontmatter writes, a
real folder move under `Work/Archive/Customers/`, real declined-record
no-ops, real approve round trips through the actual HTTP surface, and a
real second-run idempotency check) — full detail in each task's own
Implementation Log.

**One genuine defect found live and fixed in scope (`T05`):**
`propose_customer_backfill()`'s own per-Thread loop had no failure
isolation against a transient `compass_client.CompassError` — a single
real Compass connection drop mid-pass (observed live) discarded every
other Thread's already-good classification and surfaced as an HTTP `500`.
Fixed additively (a new `"failed"` return key, mirrors `backfill_files`'s
own established honest-degradation pattern) — zero change to `ADR-055`
Decision 2's own "no retry loop" text, an orthogonal Job-level resilience
fix, not an ADR deviation. Full detail: `T05`'s own Implementation Log.

**Real, full-corpus backfill run completed** (`T06`): 133 real Threads,
10 genuinely routed on disk this session (`Aldar` × 3, `TAQA` × 7 — the
story's own headline TAQA example, confirmed end-to-end), 1 brand-new
real Customer folder created (`TAQA`), 2 real folders archived (`Twitter`,
`Google`), content byte-for-byte preserved both times. `AC-09`
(idempotency after approval) confirmed for real: the just-approved
`LinkedIn` Thread never reappeared in a real, immediately-following
second full-corpus run.

**A real, disclosed operational finding, not a defect against any locked
AC (flagged to `REVIEW-QUEUE.md` for a human decision, out of this
story's own scope to resolve):** `propose_customer_archival_candidates`
only ever consumes the SAME pass's own evidence (`ADR-055` Decision 5,
literally correct per Scenario 4's own "this pass" wording) — a Customer
already fully routed by an EARLIER pass shows zero matches on any LATER
pass (its Threads are no longer `"Unsorted"`, so a later pass never even
considers them), and gets wrongly re-proposed for archival. Observed for
real twice this session (`Aldar`, `LinkedIn` — both already-approved, real
active Customers); both declined, never approved, protecting real data.
A future story may want a "has real, currently-linked Threads" cross-pass
exclusion — not added here, out of this story's own locked scope.

**Real Pending Approvals outstanding at session end, never auto-approved:**
64 pending `propose_customer_backfill_routing` + 31 pending `propose_
customer_archival_candidate` records (substantial duplication across this
session's 3 real full-corpus trigger points — `ADR-055`'s own disclosed,
accepted "no idempotency guard on `trigger="direct"`" risk, restated in
the launching agent's own instructions not to mass-approve unattended).
Left for the operator's own real review per `ADR-055`'s own explicit
"normal operator discipline" posture — see `REVIEW-QUEUE.md`.

**Story-level Definition of Done:** all locked ACs pass, all Constraints
respected (never a silent write; `ensure_customer_hub_note`/`pending_
approval_registry` reused unmodified; archive-not-delete; manually-
triggered only, never wired into `run_housekeeping_pass()`;
`synthesize_customer`/`resync_project_from_thread` never called).
`MEMORY.md`/`CHANGELOG.md` updated (see repo root). `status: Done`. `gate`
stays `flagged` — the standing `ADR-055` architect-level review item is
not this role's to clear (mirrors the `REQ-SB-73-US-01`/`SPRINT-067`
precedent exactly); see `REVIEW-QUEUE.md`'s own "Coder update" note on
that existing line item.
