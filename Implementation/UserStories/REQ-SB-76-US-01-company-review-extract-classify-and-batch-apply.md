---
id: REQ-SB-76-US-01
title: Company Review — Extract, Classify (Customer/Partner/Affiliate), and Batch-Apply
requirement_ids: [REQ-SB-76]
requirement_section: "REQ-SB-76: Company Review — Extract & Recommend, Customer/Partner/Affiliate Classification, Batch-Apply"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-057 created, plus ADR-009's own Status line narrowly updated to record point 3's partial supersession) — architect pass, /plan-tasks step 1; carried forward unchanged by the decomposer pass. Supersedes the earlier-resolved net-new-design-needed flag as this story's own current gate reason; the design-override resolution itself stands (see ## Notes, 'Gate cleared 2026-08-19 — operator override, design deferred') and is not reopened by this flag."
sprint: "SPRINT-072"
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-76-US-01 — Company Review — Extract, Classify (Customer/Partner/Affiliate), and Batch-Apply

## Story

**As a** Second Brain operator
**I want** every real company name a Thread's own content genuinely mentions —
never a name that only appears in email-client/device signature boilerplate —
extracted and put to me as one narrow question per company ("is this a real
Customer, a Partner, an Affiliate of one, a duplicate of an already-known one
to merge in, or nothing"), with my answer batch-applied to every real Thread
mentioning that company at once
**So that** the pre-existing Customer-folder noise (Apple/Google/Instagram/
Twitter/LinkedIn/etc., created by today's self-reinforcing direct-routing
prompt) stops recurring at its cheapest point, a company genuinely related to
an existing Customer/Partner can be tracked as its own real Affiliate, moving
a Customer to Partner actually works against the vault's current directory
shape, a company that already exists in the vault under a second,
differently-spelled name gets folded into its real canonical entity instead
of duplicating it, and a Thread that genuinely involves more than one
company gets that second company recorded — additively, without disturbing
its own already-set primary Customer

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-76: Company Review — Extract &
  Recommend, Customer/Partner/Affiliate Classification, Batch-Apply*. Raised
  2026-08-19, same conversation as `REQ-SB-74`'s own live data-quality
  findings. No `<!-- Draft -->` marker on this requirement — finalized text,
  the operator's own 6-point list triaged directly into this one requirement
  (points 1/2/5/3-partial) plus two deferred placeholders (`REQ-SB-77`,
  `REQ-SB-78`). The operator's own explicit framing: "I guess this can be a
  one go" — a single cohesive requirement, not several independent ones; this
  story is scoped as ONE story accordingly, per the launching agent's own
  same lean and confirmed here by direct PRD reading — nothing in the PRD's
  own text forces a split (every one of the five batch-apply outcomes —
  including Merge, added 2026-08-19 while this story was still `Draft`, see
  `## Notes` — reuses the SAME propose/finalize/batched-payload mechanism;
  the `migrate_customer_to_partner` fix and the multi-Customer additive-tag
  path are each small, additive, and share no independent design surface
  large enough to justify a separate story).
- **Root cause, confirmed live this session (restated directly in the PRD
  entry):** `compass_client.detect_customer_for_thread` (`REQ-SB-74-US-01`,
  `ADR-055` Decision 2) is grounded in a Thread's raw content — including
  real email-client/device signature boilerplate ("Sent from my iPhone,"
  "Get Outlook for Android" — 53 real messages in the vault carry one) — and
  is told to reuse an exact name from the existing known-customers list,
  which already contains that same noise, making it self-reinforcing. Direct
  reading of `detect_customer_for_thread`'s own current prompt (`app/data_
  access/compass_client.py`) confirms it says only "If you can't confidently
  tell, use 'Unsorted' rather than guessing" — no boilerplate-exclusion
  instruction exists today. This story replaces that function's own
  direct-routing prompt/outcome with a narrower two-step one: extract the
  real company name(s) genuinely relevant to a Thread's own substance
  (explicitly instructed to disregard signature/device boilerplate, mailing-
  list footers, and disclaimer text), then ask the Customer/Partner/
  Affiliate/nothing question — the exact mechanism (new `compass_client`
  call vs. an extended existing one, exact prompt wording) is left to
  `/plan-tasks` (see `## Notes`).
- **`REQ-SB-74-US-01` (`Done`, `SPRINT-068`) stays frozen, unedited** — specs
  are append-only (`Implementation/Pipeline.md` hard rule 1). This story does
  not reopen it; it supersedes its Job's own detection/proposal MECHANISM
  going forward (a new Job replaces `propose_customer_backfill`'s own
  direct-routing call), while reusing its batched-per-company Pending
  Approval SHAPE verbatim — confirmed by direct reading of `librarian_
  housekeeping.py`'s `propose_customer_backfill`/`finalize_customer_backfill_
  routing` and `ADR-055`'s own Decision 1 (`payload = {"customer", "is_new_
  customer", "thread_paths"}`, `trigger="direct"`, registered in
  `_APPROVAL_HANDLERS`) — the same "one approval covers every Thread
  proposing the same company" convention this story's own batch-apply
  scenarios below reuse, not reinvent.
- **The batched-per-company grouping precedent also already exists one layer
  over**, in the SAME module: `backfill_company_folders`/`_create_librarian_
  company_link_proposal` (`REQ-SB-72-US-01`, `ADR-049` Decision 5) already
  classifies a Thread's OTHER company mentions (via `compass_client.detect_
  mentioned_companies`/`detect_mentioned_companies_for_thread`) into
  `known`/`new_unambiguous`/`ambiguous` and routes the ambiguous case through
  a Pending Approval — a genuinely different question ("what else does this
  Thread mention," never batched per-company) from this story's own "what IS
  this Thread's own primary company, batched across every Thread mentioning
  it" (`detect_customer_for_thread`'s own question) — confirmed by direct
  reading; left to `/plan-tasks` to decide whether the new extract-only call
  is a new `compass_client` function or an extension of one of these two
  existing ones.
- **`affiliate_of` real prior art, confirmed by direct reading, not
  assumed:** `vault_writer.create_customer_hub_note_baseline`/`_HUB_NOTE_
  BASELINE_KEYS` (the LEGACY flat `Work/Customers/<name>.md` hub-note shape)
  already carries a real `affiliate_of` frontmatter key (defaults to `""`),
  but `vault_writer.build_customer_concept_frontmatter` (the CURRENT OKF
  directory shape `customer_hub_linking.ensure_customer_hub_note` actually
  writes, `ADR-042`/`REQ-SB-54`) carries no such key at all — this story
  restores it there. `vault_writer.create_partner_hub_note_baseline`/
  `_PARTNER_HUB_NOTE_BASELINE_KEYS` (`type`, `partner`, `tags` only) has NO
  `affiliate_of`-equivalent key at all today — its own docstring says so
  explicitly ("deliberately no affiliate_of, Partner has no Affiliate
  concept, ADR-009"). This story adds a real `affiliate_of` field to BOTH
  shapes (Customer's current OKF concept frontmatter, Partner's hub-note
  frontmatter), per the PRD's own explicit instruction that both Customer-
  kind and Partner-kind affiliates need it.
- **`ADR-009`'s "Partner has no Affiliate concept" sub-clause (Decision point
  3, and its "Alternatives Considered" rejection of Affiliate-for-Partner
  "for schema symmetry") is narrowly, additively revised by this
  requirement — not reversed.** `ADR-009`'s own real point (Customer/Partner
  mutual exclusivity, "a company is a Customer, a Partner, or neither, never
  both," Decision point 1) is a completely different axis from "can either
  one have a parent it's an Affiliate of" and stays untouched — the PRD's
  own text makes this same distinction explicitly. Per `Implementation/
  Pipeline.md`, ADR creation/editing is the architect's own trigger
  (trigger 3), not this role's — this story does not itself edit `ADR.md`.
  Whether this alone should still trip THIS role's own gate is addressed
  directly in `## Notes` below (judged: yes, but for a different, UI-shaped
  reason — see the gate_reason above — not for touching `ADR-009`'s scope by
  itself).
- **`partner_hub_linking.migrate_customer_to_partner`'s real gap, confirmed
  live by direct reading:** it moves `vault_writer.hub_note_path(customer_
  name)` — the OLD flat `Work/Customers/<name>.md` path — and its own
  vault-wide retag scan matches only `frontmatter.get("customer") ==
  customer_name` or the legacy inline `**Customer:** [[name]]` body
  wikilink. A real Customer created today lives under the OKF directory
  shape (`Work/Customers/<slug>/<slug>.md`, `customer_directory_paths`) —
  `hub_note_path(customer_name)` never resolves to that path, so `migrate_
  customer_to_partner` silently no-ops against every real Customer folder
  that exists in the vault today. Already disclosed as a known gap:
  `MEMORY.md` (`REQ-SB-54-US-01-T04` entry, 2026-08-16 — "a customer
  onboarded after this story ships won't have its OKF directory migrated to
  Partners on a Customer->Partner reclassification") and `REQ-SB-62`
  (2026-08-16, now superseded by this requirement — see below). This story
  fixes the real gap, not a rewritten migration mechanism from scratch —
  exact fix shape (extend the existing scan to also recognize the OKF
  directory shape, vs. a parallel new-shape-aware path) is left to
  `/plan-tasks`.
- **This requirement absorbs and supersedes `REQ-SB-62`** ("~~UI-Driven
  Customer → Partner Reclassification~~," `BACKLOG.md` row already marked
  "Superseded 2026-08-19, never built separately"). `REQ-SB-62` itself stays
  as an unbuilt, superseded placeholder — not re-specced or built on its
  own; this story's own `migrate_customer_to_partner` fix plus the new
  Pending-Approval decision control (a real UI-driven trigger point) are
  what close it.
- **Pending Approvals UI, confirmed live by direct reading:**
  `src/frontend/src/pages/MyDayApprovalsPage.tsx` renders every pending
  record with the SAME generic `.item-row` shape — title, description, and
  exactly two `.item-row-actions` buttons (`Approve` / `Decline`), calling
  `approvePendingApproval(id)`/`declinePendingApproval(id)`
  (`pendingApprovalsApiClient.ts`) — `POST /pending-approvals/{id}/approve`
  takes no body at all (`pending_approvals_router.py`'s `approve_pending_
  approval` dispatches purely on the record's already-stored `action_id`/
  `payload`, `_APPROVAL_HANDLERS[action_id](record["payload"])`). This
  requirement's own decision is NOT a binary approve/decline — it is a
  5-way choice (Customer / Partner / Affiliate-of-[an operator-picked
  known Customer or Partner] / Merge-into-[an operator-picked known
  Customer or Partner] / Decline), and for the Affiliate branch the
  operator additionally picks BOTH the real parent AND which kind (Customer
  or Partner) the new entity itself should be filed as. The Merge branch
  picks only the real canonical parent (no kind choice — the duplicate name
  is never itself created as an entity). No existing `html-prototype/`
  screen or component shows any version of this — see `## Notes` →
  Prototype parity.
- **`ensure_customer_hub_note`/`create_customer_directory_baseline`
  (`REQ-SB-54`, `BUG-028`'s header fix already applied) and `ensure_partner_
  hub_note`/`link_note_to_partner_hub` (`ADR-009`) are reused unmodified**
  for the Customer/Partner batch-apply outcomes — this story only adds the
  new `affiliate_of` field onto their respective baseline-frontmatter
  builders, never a new entity-creation mechanism.
- **Multi-Customer Threads — the operator's own direct correction after
  seeing the first PRD draft:** "One Gap is the Multi Customer thread its
  Important and I don't want to do a full write for that... All Emails will
  be updated based on the list... is this a Customer and we can Append Tags
  and Related to the email." `customer:` frontmatter stays single-value
  (whichever company is confirmed FIRST for a given Thread); any additional
  company confirmed later for the same Thread instead appends a `customer/
  <slug>` (or `partner/<slug>`) tag plus a `## Related` wikilink — zero
  change to the primary-field data model. `populate_thread_related_links`
  (`REQ-SB-72-US-01-T06`) already regenerates `## Related` wholesale from a
  Thread's current frontmatter each pass; whether this story's own additive
  link reuses that same regeneration path or is written directly by the new
  finalize handler is left to `/plan-tasks`.
- **Merge outcome — the operator's own real-time addition, caught while this
  story was already drafted (added 2026-08-19, before the story left
  `Draft`):** "sometimes you get the company Twice but with Different Name?
  (Mudala, Mubadala Investment Group) I need an option to move it as well."
  A 5th batch-apply outcome, Merge into an existing Customer or Partner,
  is added alongside Customer/Partner/Affiliate/Decline. The operator picks
  the real, already-known CANONICAL entity from the list; every real
  Thread named in the batch (the duplicate name) is routed directly to that
  canonical entity's own `customer`/`partner` frontmatter + tag — no new
  folder or entity is ever created for the duplicate name. If the duplicate
  name already has its own real OKF directory with real content (created
  before the duplication was recognized), that content is moved into the
  canonical entity and the duplicate's own now-empty folder is archived,
  never deleted. **This reuses two already-established mechanisms, not a
  new third one:** the move/retag itself reuses the exact same generic,
  vault-wide retag scan `migrate_customer_to_partner` already uses (this
  story's own Scenario 8/`T04` fix); the archival-not-delete step reuses
  `REQ-SB-74-US-01`'s own existing archival-candidate mechanism
  (`propose_customer_archival_candidates`/`finalize_customer_archival`/
  `vault_writer.move_okf_directory()`, targeting `Work/Archive/Customers/`).
  The PRD's own amended text is explicit on this point ("never a new,
  third move/retag primitive") — left to `/plan-tasks` only to decide the
  exact call sequencing (e.g. whether the finalize handler calls the retag
  scan then `move_okf_directory()` directly, or reuses the archival-
  candidate Job's own proposal step), never to invent a new mechanism.
- **Explicitly deferred, not this requirement's scope** (operator's own
  words, "log the Rest as REQ and we pick them next"): People notes linking
  to their real Company/Partner note (`REQ-SB-77`, placeholder); grouping/
  color-coding the Pending Approvals list by proposal type (`REQ-SB-78`,
  placeholder).

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A real company genuinely mentioned in a Thread's own substance is proposed as ONE batched Company Review decision, not a direct routing proposal

```gherkin
Given one or more real Unsorted Threads whose own content genuinely mentions
    the same real company name, relevant to those Threads' own substance
When the Company Review extraction pass runs
Then that company is proposed in exactly ONE Pending Approval offering five
    real outcomes — Customer, Partner, Affiliate of an existing Customer or
    Partner, Merge into an existing Customer or Partner, or Decline — never
    a direct "route to Customer X" proposal
  And that one Pending Approval's own payload names every real Thread this
    pass found genuinely mentioning that same company, not just one
  And no Thread's customer frontmatter or tags are written yet — this is a
    proposal, never a silent write
```
<!-- AC-ID: REQ-SB-76-US-01-AC-01 -->

### Scenario 2: A company name genuinely present only in email-signature or device boilerplate is never proposed as a Company Review candidate

```gherkin
Given a real Thread whose only mention of a company/device-adjacent name is
    email-client or device signature boilerplate text (e.g. "Sent from my
    iPhone," "Get Outlook for Android") — not a genuine reference to that
    company as part of the Thread's own substance
When the Company Review extraction pass runs
Then no Company Review proposal is created naming that boilerplate text as a
    candidate company
  And that Thread is not named in any Company Review batch on account of
    that boilerplate text
```
<!-- AC-ID: REQ-SB-76-US-01-AC-02 -->

### Scenario 3: Approving a company as Customer batch-applies to every real Thread in that company's batch, not just the one that triggered it

```gherkin
Given a pending Company Review batch naming two or more real Threads that
    genuinely mention the same company
When the operator classifies that company as Customer
Then that company's Customer OKF directory is created (or confirmed if it
    already exists), reusing ensure_customer_hub_note unmodified
  And every real Thread named in that batch — not only the Thread that
    originally triggered the proposal — receives real customer frontmatter
    set to that company's name and a real customer/<slug> tag
  And no Thread outside that batch is touched
```
<!-- AC-ID: REQ-SB-76-US-01-AC-03 -->

### Scenario 4: Approving a company as Partner batch-applies to every real Thread in that company's batch, not just the one that triggered it

```gherkin
Given a pending Company Review batch naming two or more real Threads that
    genuinely mention the same company
When the operator classifies that company as Partner
Then that company's Partner hub note is created (or confirmed if it already
    exists) under Work/Partners/, reusing ensure_partner_hub_note unmodified
  And every real Thread named in that batch — not only the Thread that
    originally triggered the proposal — is linked to that Partner hub note
    (reusing link_note_to_partner_hub) with a real partner/<slug> tag added
  And no Thread outside that batch is touched
```
<!-- AC-ID: REQ-SB-76-US-01-AC-04 -->

### Scenario 5: Approving a company as an Affiliate sets a real affiliate_of value pointing at the chosen existing Customer or Partner parent, for a Customer-kind affiliate

```gherkin
Given a pending Company Review batch for a company, and a real, already-known
    Customer the operator picks as that company's parent
When the operator classifies that company as an Affiliate of that Customer,
    choosing to file the new entity itself as a Customer
Then a new Customer OKF directory is created (or confirmed) for that company
    whose own concept frontmatter carries a real affiliate_of value equal to
    the parent Customer's real name
  And every real Thread named in that batch receives that new Customer's
    frontmatter and tag, exactly as Scenario 3's own plain Customer approval
  And no Thread outside that batch is touched
```
<!-- AC-ID: REQ-SB-76-US-01-AC-05 -->

### Scenario 6: Approving a company as an Affiliate sets a real affiliate_of value pointing at the chosen existing Customer or Partner parent, for a Partner-kind affiliate

```gherkin
Given a pending Company Review batch for a company, and a real, already-known
    Partner the operator picks as that company's parent
When the operator classifies that company as an Affiliate of that Partner,
    choosing to file the new entity itself as a Partner
Then a new Partner hub note is created (or confirmed) for that company whose
    own frontmatter carries a real affiliate_of value equal to the parent
    Partner's real name — a real value, where ADR-009's own Partner baseline
    previously carried no such key at all
  And every real Thread named in that batch is linked to that new Partner
    entry and tagged, exactly as Scenario 4's own plain Partner approval
  And no Thread outside that batch is touched
```
<!-- AC-ID: REQ-SB-76-US-01-AC-06 -->

### Scenario 7: Declining a Company Review batch leaves every Thread named in it completely unchanged

```gherkin
Given a pending Company Review batch naming one or more real Threads
When the operator declines that batch
Then none of the named Threads' customer/partner frontmatter, tags, or body
    content is modified in any way
  And no Customer or Partner entry is created for that company
  And every named Thread is exactly as it was before the proposal
```
<!-- AC-ID: REQ-SB-76-US-01-AC-07 -->

### Scenario 8: migrate_customer_to_partner correctly migrates a real Customer created under the current OKF directory shape, not just the legacy flat shape

```gherkin
Given a real Customer whose hub note exists under the current OKF directory
    shape (Work/Customers/<slug>/<slug>.md, plus its index.md/log.md/
    captures.md siblings) — not the legacy flat Work/Customers/<name>.md file
When migrate_customer_to_partner is invoked for that Customer
Then that Customer's real content is genuinely migrated into the Partner
    namespace — not a silent no-op — with every file's own content preserved
  And every other real vault note that referenced that Customer (by customer
    frontmatter, its customer/<slug> tag, or its inline **Customer:**
    wikilink) is correctly retagged into the Partner namespace
  And running the same migration again for that same company makes no
    further changes — idempotent by construction
```
<!-- AC-ID: REQ-SB-76-US-01-AC-08 -->

### Scenario 9: A second confirmed company on a Thread that already has a primary customer gets an additive tag and Related link, its original customer field untouched

```gherkin
Given a real Thread whose own customer frontmatter is already set to a real,
    previously-confirmed company (not "Unsorted")
When a second, different real company is confirmed for that same Thread
    through its own Company Review approval (Customer or Partner)
Then that Thread gains a real, additive customer/<slug> (or partner/<slug>)
    tag for the newly-confirmed company, alongside its existing tags
  And that Thread's ## Related section gains a real wikilink to the newly-
    confirmed company's own concept file
  And that Thread's original customer frontmatter value is left byte-for-
    byte unchanged by this write
```
<!-- AC-ID: REQ-SB-76-US-01-AC-09 -->

### Scenario 10: Approving a company as Merge routes every Thread in its batch to the canonical entity, and folds in any real content the duplicate name already had of its own — archived, never deleted

```gherkin
Given a pending Company Review batch for a duplicate-name company, and a
    real, already-known canonical Customer or Partner the operator picks as
    the entity that duplicate name actually refers to
When the operator classifies that company as a Merge into that canonical
    entity
Then every real Thread named in that batch receives the canonical entity's
    own customer/partner frontmatter value and tag — no new folder or
    entity is ever created for the duplicate name itself
  And if the duplicate name already had its own real OKF directory with
    real content, that content is moved into the canonical entity by
    reusing the exact same generic, vault-wide retag mechanism migrate_
    customer_to_partner already uses, and the duplicate's own now-empty
    folder is archived — never deleted — by reusing REQ-SB-74's own
    existing archival-candidate mechanism, not a new, third move/retag
    primitive
  And no Thread outside that batch is touched
```
<!-- AC-ID: REQ-SB-76-US-01-AC-10 -->

### Scenario 11 (decomposer-added, structural — screen/frontend rule): The Company Review proposal kind renders a distinct, real decision control, never the generic Approve/Decline pair

```gherkin
Given a pending Company Review proposal (action_id "propose_company_review")
    rendered in the Pending Approvals list, alongside other, unrelated
    pending items of other kinds
When that list renders
Then a distinct decision-control region renders in place of the generic
    Approve/Decline .item-row-actions pair, for that item only
  And it exposes five distinct real interactive controls — Customer,
    Partner, Affiliate, Merge, and Decline
  And selecting Affiliate reveals a real parent-entity picker (sourced from
    the live known-companies list) plus a real Customer-or-Partner kind
    choice for the new entity itself
  And selecting Merge reveals a real parent-entity picker only, with no
    kind choice
  And every OTHER pending item (any other action_id) still renders the
    existing, unchanged generic Approve/Decline pair
```
<!-- AC-ID: REQ-SB-76-US-01-AC-11 -->

## Affected Screens

- `html-prototype/my-day-approvals.html` — **needs a new UI region this
  requirement's own PRD text itself names as the ONLY new UI it requires**:
  a per-proposal-kind decision control for a Company Review record — offering
  Customer / Partner / Affiliate-of-[an operator-picked known Customer or
  Partner, plus a Customer-or-Partner kind choice for the new entity itself]
  / Merge-into-[an operator-picked known Customer or Partner, no kind
  choice] / Decline — replacing the generic Approve/Decline button pair for
  THIS proposal kind only (every other existing proposal kind keeps the
  current generic Approve/Decline `.item-row-actions` unchanged). No
  prototype screen shows any version of this control today. See
  `## Notes`.

## Dependencies

- **Blocked by (hard):** `REQ-SB-74-US-01` (Customer Backfill — Propose/
  Approve Thread Routing + Noise Reconciliation, `Done`, `SPRINT-068`) — this
  story reuses its batched-per-company Pending Approval shape (`ADR-055`)
  verbatim, supersedes its `detect_customer_for_thread`-driven proposal Job
  going forward, and (added with the Merge outcome, Scenario 10) reuses its
  own archival-candidate mechanism verbatim to archive a duplicate name's
  now-empty folder after a Merge; `REQ-SB-74-US-01` itself stays `Done`,
  unedited.
- **Blocked by (hard):** `REQ-SB-72-US-01` (The Librarian Section — First
  Housekeeping Pipeline, `Done`, `SPRINT-063`) — this story's own Job lives
  in the SAME `librarian_housekeeping.py` module/Section/Agent, and its
  nearest structural precedent for a batched company-mention proposal is
  `backfill_company_folders`/`_create_librarian_company_link_proposal`.
- **Blocked by (hard):** `REQ-SB-16-US-01` (Partner Hub Notes and Migration,
  `Done`) — `ensure_partner_hub_note`/`link_note_to_partner_hub`/`migrate_
  customer_to_partner`/`ADR-009` this story extends (new `affiliate_of`
  field) and fixes (OKF-shape migration gap).
- **Blocked by (hard):** `REQ-SB-54-US-01` (Vault Knowledge Model Redesign,
  `Done`) — the OKF directory shape (`build_customer_concept_frontmatter`,
  `customer_directory_paths`) this story adds `affiliate_of` onto, and whose
  own disclosed gap (`MEMORY.md`, 2026-08-16) against `migrate_customer_to_
  partner` this story closes.
- **Related to:** `REQ-SB-62` (superseded by this requirement — absorbed,
  never built separately).
- **Related to:** `REQ-SB-77` (People Notes Linked to Their Real Company/
  Partner Note, placeholder) — deferred out of this story's own scope.
- **Related to:** `REQ-SB-78` (Pending Approvals — Grouped, Color-Coded
  Review, placeholder) — deferred out of this story's own scope.
- **External:** a `/design REQ-SB-76` pass on the new Company Review decision
  control (see `## Notes`) before its frontend task can build against an
  approved screen.

## Constraints

- **Never a silent write** — every Customer/Partner/Affiliate classification
  and every multi-Customer additive tag goes through an explicit Company
  Review approval; no auto-create, auto-route, or auto-tag, even for a
  high-confidence extraction.
- **Batched per company, not per Thread** — reuses `ADR-055`'s own batched-
  payload Pending Approval convention verbatim; this story does not
  introduce a new registry/schema change without the architect confirming
  one is genuinely needed.
- **Customer/Partner mutual exclusivity (`ADR-009` point 1) is untouched** —
  only the "Partner has no Affiliate concept" sub-clause is revised,
  narrowly and additively; a company is still never both a Customer and a
  Partner at once.
- **`customer:` frontmatter stays single-value** — no list-type schema
  change; a second confirmed company on an already-routed Thread is always
  additive (tag + `## Related` link), never a second write to the primary
  `customer` field.
- **`ensure_customer_hub_note`/`create_customer_directory_baseline`,
  `ensure_partner_hub_note`/`link_note_to_partner_hub` are reused
  unmodified** for entity creation/linking — this story only adds a new
  `affiliate_of` field onto their respective baseline-frontmatter builders.
- **`migrate_customer_to_partner` is fixed, not rewritten from scratch** —
  the existing generic vault-wide retag scan (`ADR-009` point 4/`ADR-012`)
  is extended to also recognize the OKF directory shape; its own established
  idempotency-by-construction discipline is preserved.
- **The Merge outcome introduces NO new move/retag/archival primitive** —
  it reuses `migrate_customer_to_partner`'s own generic vault-wide retag
  scan (Scenario 8) to fold a duplicate name's own existing content into
  its canonical entity, and reuses `REQ-SB-74-US-01`'s own already-built
  archival-candidate mechanism (`propose_customer_archival_candidates`/
  `finalize_customer_archival`/`vault_writer.move_okf_directory()`) to
  archive the duplicate's now-empty folder — archive-not-delete, same as
  every other archival path in this project.
- **The only new UI this requirement needs is the approval decision control
  itself** — no other new screen or navigation change (operator's own
  explicit framing).
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

## Implementation Tasks

<!-- Decomposer's own table (/plan-tasks step 2, 2026-08-19) — supersedes the
analyst's own 7-task starting point above. See "## Decomposer pass" below for
the full dependency-graph reasoning and AC → task mapping. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-76-US-01-T01 | backend | Boilerplate-aware extraction call — `compass_client.extract_thread_companies_for_review` (new sibling, `detect_customer_for_thread` untouched) | `app/data_access/compass_client.py` | `../Tasks/REQ-SB-76-US-01-T01-extract-thread-companies-for-review.md` |
| REQ-SB-76-US-01-T02 | backend | Restores `affiliate_of` onto Customer's current OKF concept frontmatter; adds it to Partner's hub-note baseline frontmatter | `app/data_access/vault_writer.py` | `../Tasks/REQ-SB-76-US-01-T02-affiliate-of-on-current-shapes.md` |
| REQ-SB-76-US-01-T03 | backend | Fixes `migrate_customer_to_partner`'s real OKF-directory blind spot (Step 1); removes the now-wrong `affiliate_of`-drop line (Step 2); extracts the generalized `_retag_company_references`/public `retarget_company_references` primitive the Merge outcome reuses | `app/business/partner_hub_linking.py` | `../Tasks/REQ-SB-76-US-01-T03-migrate-customer-to-partner-okf-fix.md` |
| REQ-SB-76-US-01-T04 | backend | `propose_company_review()` Job — batched-per-company extraction pass over every real Thread, `dedupe_key`'d Pending Approvals, added alongside (not replacing) `propose_customer_backfill`; its own `POST /poc/librarian-propose-company-review` endpoint | `app/business/pipelines/librarian_housekeeping.py`, `app/api/email_poc_router.py` | `../Tasks/REQ-SB-76-US-01-T04-propose-company-review-job.md` |
| REQ-SB-76-US-01-T05 | backend | `_apply_company_to_threads` shared helper — primary-write vs. additive-tag-plus-`## Related` branching, read fresh at finalize time, used by all four write-producing outcomes | `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-76-US-01-T05-apply-company-to-threads.md` |
| REQ-SB-76-US-01-T06 | backend | `finalize_company_review()` dispatch — Customer/Partner/Affiliate/Merge branches, one handler branching on `payload["outcome"]` | `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-76-US-01-T06-finalize-company-review-outcomes.md` |
| REQ-SB-76-US-01-T07 | backend | Approve endpoint's additive `CompanyReviewDecisionBody`, merge-before-dispatch wiring, `_APPROVAL_HANDLERS` registration; new `GET /pending-approvals/known-companies` | `app/api/pending_approvals_router.py` | `../Tasks/REQ-SB-76-US-01-T07-approve-endpoint-and-known-companies.md` |
| REQ-SB-76-US-01-T08 | frontend | New Company Review decision control (Customer/Partner/Affiliate-of-[picker]/Merge-into-[picker]/Decline) — built directly, no `/design` pass (operator override, see `## Notes`) | `src/frontend/src/pages/MyDayApprovalsPage.tsx`, `src/frontend/src/features/agents-map/pendingApprovalsApiClient.ts` | `../Tasks/REQ-SB-76-US-01-T08-company-review-decision-control.md` |
| REQ-SB-76-US-01-T09 | backend | Real end-to-end verification run against the live vault — full-scale propose pass, at least one real resolution per outcome (including a real Merge with prior duplicate content), boilerplate-exclusion spot-check, a further real `migrate_customer_to_partner` call | `app/business/pipelines/librarian_housekeeping.py`, `app/business/partner_hub_linking.py` | `../Tasks/REQ-SB-76-US-01-T09-verification-run.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — manual mode still in effect, per `Implementation/Pipeline.md`
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **People notes linking to their real Company/Partner note** — deferred,
  see `REQ-SB-77` (placeholder, not yet specced).
- **Grouping/color-coding the Pending Approvals list by proposal type** —
  deferred, see `REQ-SB-78` (placeholder, not yet specced).
- **A `customer:`/`partner:` list-type schema change** — `customer:` stays
  single-value; multi-Customer support is additive tag + `## Related` only,
  per the operator's own explicit scoping.
- **Project-level routing (Thread → Project)** — untouched, one level below
  this requirement's own Customer/Partner/Affiliate scope.
- **Any change to Customer/Partner mutual exclusivity** — `ADR-009` point 1
  stays exactly as decided; a company is still never both at once.
- **Any other new Pending Approvals screen region** beyond the one decision
  control this requirement's own PRD text explicitly scopes to.

## Notes

**Gate cleared 2026-08-19 — operator override, design deferred:** this
story's `net-new-design-needed` flag (Scenarios 3-6/10's new decision
control has no `html-prototype/` reference) was resolved directly by the
operator when offered the same choice already made for `REQ-SB-75`/The
Vault: "No Straight No Designer we will handle the Design Later." The
coder builds the Customer/Partner/Affiliate-of-[picker]/Merge-into-
[picker]/Decline control directly, using the app's own existing form/
control vocabulary (same posture as every other Pending-Approval action
today) — a later, separate design pass may restyle it, but does not
block this story shipping. `REVIEW-QUEUE.md`'s corresponding entry
resolved in the same touch, naming this note as the resolving artefact.

**Amendment 2026-08-19 — Merge outcome added while this story was still
`Draft`, before it left the analyst's own stage:** the PRD's own `REQ-SB-76`
entry was amended, same day, to add a 5th batch-apply outcome — Merge into
an existing Customer or Partner — to point 3's own outcome list, and its
`<!-- Raised -->` comment and Acceptance paragraph were amended to match.
The operator's own real-time addition, quoted directly: "sometimes you get
the company Twice but with Different Name? (Mudala, Mubadala Investment
Group) I need an option to move it as well." This is an in-flight amendment
to an already-`Draft`, not-yet-built story — nothing has been implemented
against it yet, so this update edits the story directly rather than opening
a new one (`Implementation/Pipeline.md` hard rule 1's append-only rule
governs `Done` stories; this one is still `Draft`). What changed in this
pass: (1) a new Scenario 10 (Merge outcome) was added; (2) Scenario 1's own
outcome enumeration was corrected from four to five; (3) every place in this
story that names the decision control's own shape (`gate_reason`, Context's
Pending Approvals UI bullet, Affected Screens, the Prototype-parity bullet
below, the T01/T02/T06 task-table starting points) was updated to include
Merge-into-[picker]; (4) a new Context bullet and Constraints bullet make
explicit that the Merge outcome introduces NO new move/retag/archival
mechanism — it reuses `migrate_customer_to_partner`'s own generic retag
scan (this story's own Scenario 8/`T04` fix) and `REQ-SB-74-US-01`'s own
already-built archival-candidate mechanism verbatim, exactly as the PRD's
own amended text instructs ("never a new, third move/retag primitive") —
this is called out explicitly so the architect does not invent a redundant
mechanism at `/plan-tasks`. `gate: flagged` / `gate_reason: net-new-design-
needed` is left unchanged by this amendment — the same UI-design flag
already in place for Scenarios 3-6 now also covers Scenario 10's own
decision-control surface (Merge is one more branch of the SAME
not-yet-designed control, not a second, independent design gap).

**Prototype parity** (`html-prototype/my-day-approvals.html`):

- `.item-row` title + `badge-warning` "Awaiting approval" — **Specced**,
  reused verbatim.
- `.item-row-meta` free-text description lines — **Specced**, already
  renders arbitrary description text; this story's own batch/company
  summary text renders through this same already-generic mechanism.
- `.state-switcher` (populated/empty) — **Specced/unaffected**, already
  covers "nothing pending" generically.
- Approve/Decline `.item-row-actions` (generic binary) — **Superseded, for
  this proposal kind only.** Every OTHER existing proposal kind keeps this
  exact control unchanged (out of this story's scope to touch). This
  proposal kind alone needs a genuinely new 5-way decision control
  (Customer / Partner / Affiliate-of-[known-entity picker, plus a
  Customer-or-Partner kind choice for the new entity] / Merge-into-[known-
  entity picker, no kind choice] / Decline) — **no `html-prototype/` screen
  shows any version of this control today.** This is why this story sets
  `gate: flagged` / `gate_reason: net-new-design-needed` (see below) rather
  than `gate: clear`. (Merge was added to this control by the 2026-08-19
  amendment above — one more branch of the SAME not-yet-designed control,
  not a second design gap.)
- Header copy, sidebar nav, footer disclaimer text — **Unaffected**, no
  change.

**Why this story sets `gate: flagged` (MUST-FLAG trigger 8's own UI-shaped
instance, per the prototype-reconciliation rule):** the PRD's own text is
explicit that "the only new UI this requirement needs is the approval
decision itself" — meaning it EXPLICITLY calls for new UI, not merely a new
backend outcome rendered through an already-generic control. Direct reading
of `MyDayApprovalsPage.tsx`/`my-day-approvals.html` confirms today's control
is a plain Approve/Decline binary with no picker, no kind choice, and no
per-proposal-kind branching at all — a genuinely new interactive shape, not
a copy-edit of the existing one. Per this role's own mandatory "Prototype
parity" rule, a requirement whose UI is not yet covered by the approved
prototype is flagged `net-new-design-needed` and a human `/design REQ-SB-76`
pass is recommended before this story's own frontend task (`T06`) is built —
**this is judged to apply here even though the launching task's own framing
treated "the new UI component's own structure" as a mechanism-level
question for the architect's `## Notes`.** The two are not the same
question: the architect can size WHERE the control's state lives and HOW it
calls the approve endpoint (mechanism), but WHAT it looks like and HOW an
operator interacts with a multi-step picker (Customer vs. Partner vs.
Affiliate, then parent picker, then kind choice) is a real design decision
this project's own established `/design`-before-`/spec`-builds convention
(`Implementation/Pipeline.md` → "Design sign-off") puts in front of a human
in a browser, not left to either the architect or the coder to invent
silently. The backend Gherkin above (Scenarios 3-6) is written entirely at
the OUTCOME level (frontmatter/tag/entity results) precisely so it does not
presuppose the control's own visual shape — only `T06` (frontend) is
blocked on the `/design` pass; `T01`-`T05`/`T07` (all backend) are not.

**Mechanism-level questions left to `/plan-tasks`, not resolved by this pass
(the Gherkin above specifies the OUTCOME, not the mechanism, mirroring
`REQ-SB-74-US-01`'s own identical precedent):**

1. **The exact new extraction/classification call shape** — a genuinely new
   `compass_client` function (a boilerplate-aware sibling of `detect_
   customer_for_thread`), or an extension of the existing `detect_mentioned_
   companies`/`detect_mentioned_companies_for_thread` pair — left to the
   architect (see Context's own direct-reading comparison of both existing
   candidates).
2. **Whether `propose_customer_backfill`/`finalize_customer_backfill_
   routing` are replaced in place or a new sibling Job/pair is added
   alongside them** (with the old direct-routing path retired) — a real
   `librarian_housekeeping.py` structural choice, left to the architect.
3. **Exact new/changed endpoint shape(s)** — `POST /pending-approvals/
   {id}/approve` today takes no body; this story's own 5-way decision (plus
   the Affiliate branch's own parent + kind choice, and the Merge branch's
   own parent-only choice) needs the approve call to carry a real decision
   payload for this proposal kind specifically — left to the architect
   (e.g. a new request body field, a dedicated endpoint for this action_id,
   or a decision recorded via a separate call before Approve) — no specific
   shape is asserted here.
4. **Whether a Thread's own already-set-vs-unset primary `customer`/
   `partner` state is checked at proposal time or at finalize time**, before
   choosing the tag-append-only path (Scenario 9) over the frontmatter-write
   path (Scenarios 3-6) — left to the architect.
5. **Whether the multi-Customer additive `## Related` write (Scenario 9)
   reuses `populate_thread_related_links`'s own wholesale-regenerate pass or
   is written directly by the new finalize handler** — left to the
   architect.
6. **The new Company Review decision control's own visual/interaction
   structure** (button group vs. dropdown-plus-confirm, where the Affiliate
   parent-picker/kind-choice and the Merge parent-picker live, whether
   they're inline or a secondary step) — this is the `/design REQ-76`
   question itself, not a backend mechanism question; explicitly NOT
   resolved here (see above).
7. **The new Job's scheduling/triggering posture** — manually-triggered only
   via its own endpoint (mirroring `REQ-SB-74-US-01`'s own explicit "NOT
   wired into `run_housekeeping_pass()`" constraint), or eligible for the
   recurring chain — the PRD's own text does not repeat that constraint
   explicitly for this successor mechanism, so it is left open rather than
   assumed either way.

**Why this does NOT trip trigger 1 (material assumption):** every open item
above is a MECHANISM question this project's own role boundaries assign to
the architect (or, for item 6, to `/design`) — every SCOPE-level question
(what gets proposed, the five real outcomes including Merge, what batch-
applies where, the multi-Customer additive resolution, the `migrate_
customer_to_partner` fix's own target, and the Merge outcome's own reuse of
that SAME fix plus `REQ-SB-74-US-01`'s own archival mechanism rather than a
new primitive) is resolved directly by the PRD's own text, confirmed against
the real, current code throughout `## Context` above.

**Why this does NOT trip trigger 2:** `REQ-SB-76` carries no `<!--
Draft -->` marker in the PRD — its own footnote confirms the operator's
6-point list was triaged and each point either built here, superseded
(`REQ-SB-62`), or explicitly deferred with its own placeholder requirement
ID (`REQ-SB-77`, `REQ-SB-78`), none left ambiguous.

**Why this does NOT trip trigger 3 on its own (the `ADR-009` revision):**
ADR creation/editing is the architect's own trigger, not this role's — this
pass discloses the bounded, narrow, additive `ADR-009` revision (Context,
above) but does not itself create or edit `Implementation/Architecture/
ADR.md`. Judged NOT to additionally warrant an analyst-level flag on its own
merits either: the PRD's own text already fully reasons through why this is
additive, not a reversal (the mutual-exclusivity axis is untouched), the
same distinction `ADR-009`'s own real point already draws. This story's
`gate: flagged` status comes from the UI trigger above (documented
separately), not from the `ADR-009` revision itself — if the UI question
were somehow already resolved, this item alone would not have forced a flag.

**Why this does NOT trip trigger 4:** no `ESCALATIONS.md` entry was written
— nothing in this pass is a backward pipeline step or an out-of-scope
event; `REQ-SB-62`'s own supersession was already recorded directly in the
PRD/BACKLOG by the operator's own prior conversation, not by this pass.

**Why this does NOT trip trigger 5 (oversized):** still 7 starting tasks
after the Merge-outcome amendment — comparable to `REQ-SB-72-US-01`'s own
proven 9-task ceiling for the SAME module, and only one more than `REQ-SB-
74-US-01`'s own 6 for a requirement of genuinely comparable shape (same
batched-approval mechanism, five outcomes instead of two) — not oversized.
Merge did not add a new task of its own: it folds into `T01`/`T02`'s
already-existing proposal/finalize scope precisely because it reuses
already-built mechanisms rather than needing a new one. The operator's own
explicit "one go" framing is honored: one story, not split.

**Why this DOES trip trigger 8 (UI ambiguity/genuinely-new-design, see
gate_reason):** covered in full above — this is the sole reason this story
is `gate: flagged` rather than `gate: clear`.

**What to do next:** `/design REQ-SB-76` — a human designs and approves the
new Company Review decision control in the browser (extending `my-day-
approvals.html` or a focused variant of it) before `T06` (frontend) is
built; `T01`-`T05`/`T07` (backend) are not blocked by this and may proceed
through `/plan-tasks` once the human has reviewed this flag at
`REVIEW-QUEUE.md`. Per `Implementation/Pipeline.md`, a `gate: flagged` story
still allows `/plan-tasks` to run (the architect/decomposer pass is not
itself blocked by this flag) — only `T06`'s own build is gated on the
`/design` outcome.

**Superseded by the operator's own direct override, 2026-08-19 (see "Gate
cleared 2026-08-19" at the top of `## Notes`):** the `/design REQ-SB-76`
recommendation immediately above was overridden before this architect pass
ran — the coder builds the decision control directly, using the app's own
existing form/control vocabulary, no `/design` pass. Recorded once, at the
top of `## Notes`, as the resolution; this paragraph is not reopened.

---

**Architect pass, 2026-08-19 (`/plan-tasks` step 1):** all seven
mechanism-level questions left open above are now resolved. One new ADR,
[ADR-057](../Architecture/ADR.md), narrowly, additively revises `ADR-009`
point 3 only (points 1/2/4/5 untouched, `ADR-009`'s own `**Status:**` line
updated to record the partial supersession — the same cross-reference
convention `ADR-011`/`ADR-013`/`ADR-018` already use, never a rewrite of
`ADR-009`'s own Context/Decision/Alternatives/Consequences prose). Full
reasoning for every decision below: [ADR-057](../Architecture/ADR.md); full
mechanism detail: `architecture.md` → "The Librarian — Company Review."

Decisions, mapped 1:1 to the seven open items and this task's own asked
items:

1. **Extraction prompt** — a NEW sibling Compass call, `compass_client.
   extract_thread_companies_for_review` (multi-mention shape, explicit
   boilerplate/signature/footer/disclaimer exclusion instruction) — never
   an edit to the frozen, `Done` `detect_customer_for_thread` (hard rule 1).
2. **5-way batched approval mechanism** — ONE `action_id=
   "propose_company_review"` Pending Approval per company (`payload =
   {"company", "thread_paths"}`, `dedupe_key` per `ADR-056`'s own
   convention), resolved via a NEW additive, optional `CompanyReview
   DecisionBody` (`outcome`/`parent_name`/`parent_kind`) on the EXISTING
   `POST /pending-approvals/{id}/approve` endpoint — merged into the
   payload before dispatch, zero signature change to the other 8 registered
   handlers. `Decline` is untouched, reuses the existing endpoint verbatim.
3. **`affiliate_of` restoration + Partner extension** —
   `build_customer_concept_frontmatter` and `_PARTNER_HUB_NOTE_BASELINE_
   KEYS`/`create_partner_hub_note_baseline`/`ensure_partner_hub_note_
   baseline_frontmatter` each gain `"affiliate_of": ""`; a real value reuses
   the already-existing generic `upsert_frontmatter_key`. `ADR-009` point 3
   narrowly revised (`ADR-057` Decision 4).
4. **`migrate_customer_to_partner` OKF-shape fix** — Step 1 gains an
   OKF-directory-first branch (reuses `move_okf_directory` verbatim); Step 2
   already correctly discovers/retags the OKF concept file today (`list_
   all_note_paths()` is already a recursive scan) and needs exactly one
   correction — the now-incorrect `affiliate_of`-drop line is removed.
5. **Merge mechanism** — Step 2's per-note rewrite logic is extracted into
   a new, parameterized `_retag_company_references(old_name, old_kind,
   new_name, new_kind)`; `migrate_customer_to_partner` becomes a thin
   wrapper over it (zero external contract change); a new public sibling,
   `retarget_company_references`, is the Merge outcome's own entry point —
   no third move/retag primitive. Archival reuses `finalize_customer_
   archival`'s own exact call shape verbatim, matched to the duplicate's own
   real shape (`move_okf_directory` or `move_note_and_attachments`).
   Disclosed, not fixed: a Partner-shaped duplicate is retargeted but not
   archived (no `Work/Archive/Partners/` root exists yet).
6. **Multi-Customer additive path** — a new, shared `_apply_company_to_
   threads(thread_paths, target_name, target_kind)` helper (used by all
   four Customer/Partner/Affiliate/Merge outcomes) checks each Thread's
   CURRENT primary `customer`/`partner` state AT FINALIZE TIME (never
   proposal time) and branches primary-write vs. additive-tag-plus-`##
   Related`; the `## Related` write reuses `build_thread_related_
   wikilinks` directly (not `populate_thread_related_links`'s own
   whole-vault loop, which has no per-Thread entry point), under the SAME
   already-registered `section_ownership.py` caller id.
7. **Decision control shape** — five buttons (Customer/Partner/Affiliate/
   Merge/Decline); Affiliate reveals a parent picker (sourced from a new
   `GET /pending-approvals/known-companies`) plus a Customer-or-Partner kind
   choice; Merge reveals a parent picker only; Decline reuses the existing
   generic decline call verbatim. Built directly per the operator's own
   override above (no `/design` pass).

**Architecture scope:** §"The Librarian — Company Review"
(`REQ-SB-76-US-01`, includes the `extract_thread_companies_for_review`,
`propose_company_review`/`finalize_company_review`, `_apply_company_to_
threads`, `_retag_company_references`/`retarget_company_references`,
`affiliate_of`, Approve-endpoint, `known-companies`-endpoint, and frontend
sub-sections), §"The Librarian — Customer Backfill" (`REQ-SB-74-US-01`,
superseded-in-practice note only — read, not edited), §"Partner Hub Notes &
Mutually-Exclusive Company Taxonomy" (`REQ-SB-16`), §"Vault Knowledge Model
Redesign" (`REQ-SB-54`, the OKF directory shape this story's `affiliate_of`
and migration fix operate against) — bounds the coder to these sections at
`/implement-sprint`.

**Gate:** `flagged` — `gate_reason: trigger-3 (ADR-057 created)`. Per
`Implementation/Pipeline.md`, this does NOT halt the stage — the decomposer
still runs so the human reviews `ADR-057` and the resulting tasks together
in one pass. See `REVIEW-QUEUE.md`.

---

## Decomposer pass (`/plan-tasks` step 2, 2026-08-19)

**All 10 of the analyst's own Gherkin scenarios are locked as
`REQ-SB-76-US-01-AC-01` through `AC-10`**, one-to-one, wording kept
essentially verbatim (already precise and buildable — no scope change),
each AC-ID tag appended immediately after its own scenario's closing
Gherkin fence. **One additional scenario/AC, `AC-11`, is added by this
role** — per this role's own mandatory "structural ACs for screen/frontend
stories" rule: the new Company Review decision control (`T08`) is a real
screen change the analyst's own Gherkin deliberately left at the OUTCOME
level (see the story's own Notes, "the backend Gherkin above is written
entirely at the OUTCOME level... precisely so it does not presuppose the
control's own visual shape"), which is correct for the OUTCOME half but
leaves the DURABLE DESIGN LAYER (which region/control renders, that Affiliate/
Merge each reveal their own distinct picker shape) unlocked — a real,
DOM-verifiable structural property, never a visual/CSS one. `AC-11` locks
exactly that, nothing about styling. All 11 are locked by default (none
marked `locked: false` — every one has a real, observable outcome: a real
batched Pending Approval payload, real frontmatter/tag/`## Related` writes,
a real folder move, a real unchanged-on-decline state, a real DOM region —
none found unverifiable).

**Task table above supersedes the analyst's own 7-task starting point**,
grounded directly in `ADR-057`'s own real mechanism text and the real,
current shape of every file it touches (read directly, not assumed —
`compass_client.py`, `librarian_housekeeping.py`, `pending_approvals_
router.py`, `vault_writer.py`, `partner_hub_linking.py`, `customer_hub_
linking.py`, `email_classification.py`, `section_ownership.py`,
`MyDayApprovalsPage.tsx`, `pendingApprovalsApiClient.ts`). 9 tasks, not 7 —
the analyst's own single `T02` ("finalize handlers, all four outcomes") is
split into three real, independently-buildable/verifiable units
(`_apply_company_to_threads` as its own shared primitive, `finalize_company_
review`'s own dispatch, and the router's own decision-body wiring), and the
analyst's own single `T01` is split into the extraction call and the propose
Job (two genuinely different layers — data_access Compass call vs. business
Job orchestration, `ADR-003`'s own boundary), matching this codebase's own
"generic-primitive-first, kind-specific-wrapper-second" and "propose Job,
then its own finalize handler, as build-order-sequenced siblings"
precedents (`Implementation/Learnings.md`, `SPRINT-048`/`REQ-SB-72-US-01-T07`
style) rather than one oversized task per concern. Dependency graph:

- `T01` (`extract_thread_companies_for_review`) — the shared extraction
  primitive every downstream Job consumes; a pure data_access Compass call,
  no other new code depends on it existing beyond being importable.
  `depends_on: []`.
- `T02` (`affiliate_of` on both entity shapes) — a pure `vault_writer.py`
  frontmatter-shape addition, independent of extraction/propose/finalize
  entirely. `depends_on: []`.
- `T03` (`migrate_customer_to_partner` OKF fix + `_retag_company_
  references`/`retarget_company_references`) — Step 2's corrected
  `affiliate_of`-carry-forward behavior is only meaningful once Partner
  legitimately carries the key (`T02`). `depends_on: [T02]`.
- `T04` (`propose_company_review()` + its own endpoint) — calls `T01`'s
  extraction function directly. `depends_on: [T01]`.
- `T05` (`_apply_company_to_threads`) — composes only already-existing
  primitives (`vault_writer.replace_body_section`, `email_classification.
  build_thread_related_wikilinks`, `vault_writer.upsert_frontmatter_key`);
  no real dependency on `T01`-`T04`. `depends_on: []`.
- `T06` (`finalize_company_review` dispatch) — the Affiliate branch needs
  `T02`'s own `affiliate_of` key to exist on both shapes; the Merge branch
  needs `T03`'s own `retarget_company_references`; every branch needs `T05`'s
  own shared apply helper. `depends_on: [T02, T03, T05]`.
- `T07` (Approve-endpoint decision body + `known-companies`) — registers
  `T06`'s own `finalize_company_review` in `_APPROVAL_HANDLERS`, and its own
  `action_id` string must match the literal string `T04`'s `propose_company_
  review()` writes into every real record it creates. `depends_on: [T04,
  T06]`.
- `T08` (frontend decision control) — needs `T07`'s own real decision-body
  endpoint and `known-companies` endpoint to build and verify against (no
  stub/mock substitute per this codebase's own established real-backend-first
  discipline). `depends_on: [T07]`.
- `T09` (real end-to-end verification run) — needs the WHOLE wired system,
  every outcome reachable for real, plus the real frontend for `AC-11`'s own
  live re-confirmation. `depends_on: [T04, T06, T07, T08]` (transitively
  covers `T01`/`T02`/`T03`/`T05` too — every task feeds into this one).

No cycles.

**AC → task mapping:** `AC-01` (one batched proposal, five real outcomes,
no write at propose time) → `T04` (batching/payload/no-write half) + `T07`
(the "one `action_id`, five outcomes via a decision body, never per-outcome
`action_id`s" mechanism half) + `T09`; `AC-02` (boilerplate exclusion) →
`T01` + `T09`; `AC-03` (Customer batch-apply) → `T06` + `T08` (UI spot-check)
+ `T09`; `AC-04` (Partner batch-apply) → `T06` + `T09`; `AC-05` (Affiliate-
of-Customer) → `T02` (structural half) + `T06` + `T08` + `T09`; `AC-06`
(Affiliate-of-Partner) → `T02` (structural half) + `T06` + `T09`; `AC-07`
(Decline no-op) → `T07` + `T09`; `AC-08` (`migrate_customer_to_partner` OKF
fix + idempotency) → `T03` + `T09`; `AC-09` (multi-Customer additive tag +
`## Related`) → `T05` + `T09`; `AC-10` (Merge, both shapes) → `T03`
(retag primitive) + `T06` + `T08` (UI spot-check) + `T09`; `AC-11`
(decomposer-added structural frontend AC) → `T08` (primary — real DOM
verification) + `T09`. Every locked AC has at least one AC-tagged manual
verification step in the task(s) named above; no locked AC is left without a
tagged step (confirmed by direct cross-check against all 9 task files' own
`## Tests` blocks before finalizing this pass).

**Why this pass does NOT fire a NEW trigger, beyond the architect's own
already-standing `ADR-057` flag (which this role does not clear, per
`Implementation/Pipeline.md`):**

- **Trigger 1 (material assumption):** no gap-filling assumption made beyond
  one disclosed, narrow scope-internal judgement call — `AC-11`'s own
  addition (this role's own mandatory structural-AC rule for a screen-
  affecting story, not a guess about the analyst's intent) and the
  `T02`→`T03` build-order dependency (a same-file/related-shape sequencing
  choice, not a functional gap-fill). Every other task-shaping decision
  follows directly from `ADR-057`'s own Decision text.
- **Trigger 5 (oversized):** 9 tasks — matches this project's own proven
  9-task/L ceiling for genuinely large single-story sprints in this SAME
  module (`REQ-SB-72-US-01`, `Implementation/Learnings.md` `SPRINT-021`/
  `SPRINT-030`) and the story's own analyst-pass reasoning already anticipated
  this exact comparison; not oversized. `T09` is expected to be the heaviest
  by real-verification wall-clock cost, not code volume, mirroring `REQ-SB-
  74-US-01-T06`'s own precedent for the SAME kind of full-corpus real run.
- **Trigger 6 (unverifiable AC):** every locked AC (including the new `AC-11`)
  has a concrete, real, observable verification path (a real Pending
  Approval payload, real frontmatter/tag/`## Related` writes, a real
  `affiliate_of` value, a real folder move, a real declined-record no-op, a
  real DOM region) — none found unverifiable.
- **Trigger 7 (contradictory inputs):** none found — `ADR-057`'s own text is
  internally consistent with the story's own Gherkin, Constraints, and the
  real, current shape of every file it touches (confirmed by direct reading
  during this pass, not assumed).
- **Trigger 8 (multiple equally-valid / unclear):** the task split above is
  grounded directly in `ADR-057`'s own real mechanism text and this
  codebase's own established task-granularity precedents, not a coin-flip
  among equally-valid shapes. `T08`'s own exact picker-component structure
  (a single component vs. a small local sub-component split) is left to the
  coder's own judgement — a genuinely scope-internal implementation detail
  with no locked AC riding on which shape is chosen, named explicitly in
  `T08`'s own Files to Modify note.

**Status:** `Draft → Ready` — every AC is locked, every locked AC has a
tagged verification step in at least one task, and `depends_on` is acyclic
(confirmed above). `gate` stays `flagged` (`gate_reason` unchanged —
`trigger-3`, `ADR-057`) — the decomposer does not clear an architect's own
ADR flag; the human reviews `ADR-057` and this pass's own 9 tasks together,
per the architect's own Notes above and the existing `REVIEW-QUEUE.md` entry
(updated by this pass with a pointer to the finished task set, not
resolved/removed).

---

## Coder wrap-up (`/implement-sprint`, `SPRINT-072`, 2026-08-19/20)

All 9 tasks (`T01`-`T09`) `Done`. All 11 locked ACs independently verified
live against the real, fully-wired system — `AC-01`/`AC-02` (full 141-Thread
real corpus, two separate real passes), `AC-03` (Masdar, real Customer),
`AC-04` (Core42, real Partner, 43 real Threads), `AC-05` (Sindan, real
Affiliate of Mubadala — grounded in a real, explicit ">50% control Affiliate"
legal confirmation found in the Thread's own content), `AC-06` (G42, real
Affiliate of Core42), `AC-07` (LinkedIn, real Decline, confirmed no-op),
`AC-08` (`migrate_customer_to_partner` OKF fix + idempotency, `T03`; no
further real candidate found this session, honestly reported), `AC-09` (real
additive-tag-plus-`## Related` path, confirmed on the Aldar/Core42 Thread),
`AC-10` (Merge, both sub-cases — ADFEC→Masdar with no prior content,
Mubadala Investment Company→Mubadala with real prior OKF content, archived
not deleted), `AC-11` (live DOM re-confirmation at real scale — 39 decision
controls matching 39 real pending records exactly). Full detail, real
resolutions made, and two disclosed operational nuances (a Merge
re-proposal edge case and a multi-additive `## Related`-overwrite edge case,
neither a locked-AC violation) are in `T09`'s own Implementation Log and
`MEMORY.md`. No code defect required an in-scope fix. The Librarian's own
recurring schedule was confirmed still genuinely paused/absent and was NOT
touched — reserved for the operator's own return.
