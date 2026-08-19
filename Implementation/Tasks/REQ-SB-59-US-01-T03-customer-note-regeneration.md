---
id: REQ-SB-59-US-01-T03
title: vault_migration.regenerate_customer_notes() — regenerate legacy flat Customer notes onto the OKF shape, preserving durable content; resolves ESC-046
parent_story: REQ-SB-59-US-01
requirement_id: REQ-SB-59
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-59-US-01-T03 — `regenerate_customer_notes()` — regenerate legacy flat Customer notes onto the OKF shape; resolves `ESC-046`

## Parent Story

- Story: [[REQ-SB-59-US-01]] — `../UserStories/REQ-SB-59-US-01-full-vault-migration-to-new-knowledge-model.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-59 *Full Vault Migration to the New Knowledge Model*

---

## Objective

Add `regenerate_customer_notes() -> dict` to `app/business/vault_migration.py`:
for every real, pre-migration legacy flat `Work/Customers/<Name>.md` Customer
hub note, ensures its OKF concept-file directory exists, feeds its full body
into the existing, unmodified Customer Synthesizer
(`synthesize_customer(..., evidence_text=...)`) so any durable fact is routed
through the standing `detect_customer_durable_fact`/Pending-Approval gate
(never auto-written), then archives the flat file — which also resolves
`ESC-046`'s filename-stem collision. Expose it as
`POST /poc/regenerate-customer-notes`.

---

## Starting State → End State

**Before / Inputs:**
- `app/data_access/vault_writer.py::list_all_note_paths() -> list` (real,
  `Done`) returns both old-shape flat `Work/Customers/<Name>.md` hub notes
  AND new OKF concept files in the same flat list (its own docstring
  confirms this).
- `app/business/customer_hub_linking.py::ensure_customer_hub_note(customer:
  str) -> dict` (real, `Done`) — returns `{"hub_note_path": str, "created":
  bool}`; a no-op (tops up missing frontmatter keys only) if the concept
  file already exists, creates the full 4-file OKF baseline from scratch
  otherwise.
- `app/business/project_customer_synthesizer.py::synthesize_customer(customer:
  str, concluded_project: str | None = None, evidence_text: str = "") -> dict`
  (real, `Done`, `REQ-SB-57`) — regenerates `## Glimpse` (a mechanical
  rollup of the Customer's own currently active/on_hold Projects, via
  `vault_writer.list_customer_projects`, never a Thread/email read); when
  `evidence_text` is non-empty, reads the Customer's CURRENT `## Background`,
  calls `compass_client.detect_customer_durable_fact`, and — only on a real
  positive detection — proposes a `propose_background_amendment` Pending
  Approval (`action_id="propose_background_amendment"`, `agent_id=
  "project-customer-synthesizer"`, `payload={"customer": ..., "fact": ...}`)
  via `pending_approval_registry.create_pending_approval`. `## Background`
  itself is NEVER written by this call — only on later, separate operator
  approval (`finalize_background_amendment_proposal`).
- `vault_writer.move_note_and_attachments(note_path, target_dir) -> str`
  (real, `Done`, same primitive `T01` uses).
- `vault_writer.read_note(path) -> tuple[dict, str]` (real, `Done`) — returns
  `(frontmatter, body)`; this task uses the returned `body` as
  `evidence_text`.
- `ESC-046` (`ESCALATIONS.md`, `Open`, 2026-08-18): 14 of 17 real,
  already-migrated Customers still carry a stale legacy flat hub note at
  the identical filename stem as their real OKF concept file;
  `vault_indexing.rebuild_index()`'s stem-keyed index lets the
  later-visited legacy flat file silently win, so anything reading through
  `get_index()[stem]` resolves to the WRONG file for those 14.

**After / Outputs:**
- `app/business/vault_migration.py` gains `regenerate_customer_notes() ->
  dict`, returning at minimum `{"customers_processed": list[dict]}` (exact
  key names are this task's own implementation latitude; per-Customer
  entries report `status`, whether a hub note was created, whether a
  Pending Approval was proposed, and the archived-file path).
- New `POST /poc/regenerate-customer-notes` endpoint in
  `email_poc_router.py`.
- After a real run: every enumerated Customer's OKF concept file exists and
  carries the Background/History/Glimpse/Captures shape; any durable fact
  from the old flat note's body surfaces as a new Pending Approval; the old
  flat file is archived (never deleted) into
  `.second-brain/migration_backup/<run-timestamp>/Customers/`; the
  filename-stem collision `ESC-046` recorded is gone for every processed
  Customer, since only the OKF concept file remains at that stem.

---

## Files to Modify

- `src/backend/app/business/vault_migration.py` (add
  `regenerate_customer_notes`, alongside `T01`/`T02`'s own functions — read
  the REAL current file first, do not overwrite either)
- `src/backend/app/api/email_poc_router.py` (add import +
  `POST /poc/regenerate-customer-notes` endpoint, matching
  `/poc/migrate-customer-to-partner`'s own existing summarizing-wrapper
  shape)

---

## Constraints

- Inherits from parent story:
  - **Never a migration-only auto-write bypass** — durable pre-migration
    content is ALWAYS routed through `synthesize_customer`'s own existing
    `detect_customer_durable_fact`/Pending-Approval gate, exactly like the
    ongoing Synthesizer. Do not write directly to `## Background`.
  - **Archive, never delete** the flat legacy file, via
    `move_note_and_attachments`.
  - **A generic, vault-wide scan — never a hardcoded Customer name list**
    (mirrors `partner_hub_linking.migrate_customer_to_partner`'s own
    established precedent): enumerate every note `list_all_note_paths()`
    returns whose `frontmatter.get("type") == "Customer"` AND whose
    `path.parent.name == "Customers"` (the old flat shape — an OKF concept
    file's own parent directory is instead the slug, never literally
    `"Customers"`).
  - **Pending Approvals this function produces are NOT required to be
    approved for this task to be `Done`** — only that they are correctly
    *created*. Do not author or require a locked check that any resulting
    Pending Approval reaches `approved`.
- Do not modify `project_customer_synthesizer.py`,
  `customer_hub_linking.py`, `pending_approval_registry.py`, or
  `vault_indexing.py` — this task composes existing, unmodified functions
  only.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).
- **Out of scope, no evidence either currently exists — log, don't build,
  if found:** the Partner namespace (never an OKF directory by design,
  `ADR-009`) and any legacy flat Project-kind note. If the coder discovers
  either during implementation, log it as a scope-internal finding; do not
  silently extend this function to handle it.

---

## Tests

<!-- AC-02 is the only locked AC this task carries. -->

**Manual verification steps:**

1. [REQ-SB-59-US-01-AC-02] Before running, pick a real, pre-migration flat
   `Work/Customers/<Name>.md` note (predating this migration — one of the
   14 `ESC-046`-identified colliding Customers, or any other real flat note
   found by the same generic scan) whose body contains a genuine durable
   fact or concluded item. Record its full body text and its Customer name.
   Call `regenerate_customer_notes()` (via
   `POST /poc/regenerate-customer-notes`). Confirm: (a) that Customer's OKF
   concept file (`Work/Customers/<slug>/<slug>.md`) exists afterward and its
   body carries all four `## Background`, `## History`, `## Glimpse`, and
   `## Captures` headers; (b) a new pending approval exists in
   `pending_approval_registry.list_pending_approvals(status="pending")`
   with `action_id == "propose_background_amendment"` and
   `payload["customer"] == <that Customer's name>`, whose `payload["fact"]`
   reflects the durable fact recorded from the flat note's body — surfaced
   for review, not silently discarded and not auto-written into
   `## Background` directly.
2. [REQ-SB-59-US-01-AC-02] Confirm the flat legacy note no longer exists at
   its old `Work/Customers/<Name>.md` path afterward, and its full content
   is byte-for-byte identical (matching the body recorded in step 1) under
   `.second-brain/migration_backup/<run-timestamp>/Customers/`.
3. [REQ-SB-59-US-01-AC-02] Confirm the `ESC-046` collision is resolved for
   this specific Customer: `vault_indexing.rebuild_index()` then
   `get_index()[<stem>]["frontmatter"]["type"]` now resolves to `"customer"`
   (the real, current OKF concept file's own lower-case `type`), never the
   legacy flat shape's `"Customer"` — confirming only the OKF concept file
   remains at that stem once the flat file is archived.
4. Non-AC idempotency sanity check: call `regenerate_customer_notes()` a
   second time. Confirm it reports zero flat Customer notes left to
   process (the generic scan now finds none at `path.parent.name ==
   "Customers"` for any previously-processed Customer), and does not raise
   or create a duplicate Pending Approval for the same fact.
5. Non-AC completeness check: after a full real run, confirm the count of
   remaining flat `Work/Customers/<Name>.md` notes matches expectation —
   either zero, or only Customers that genuinely never had a legacy flat
   note to begin with (cross-check against `ESC-046`'s own recorded count
   of colliding Customers at the time it was filed, noting the real count
   may differ if vault state has changed since).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `REQ-SB-59-US-01-AC-02` verified: OKF Background/History/Glimpse/
      Captures shape exists for a real regenerated Customer
- [ ] `REQ-SB-59-US-01-AC-02` verified: a durable pre-migration fact
      produces a real Pending Approval, never a direct/auto `## Background`
      write
- [ ] `REQ-SB-59-US-01-AC-02` verified: the flat legacy note is archived
      (not deleted), byte-for-byte, resolving that Customer's `ESC-046`
      stem collision
- [ ] Generic, vault-wide scan confirmed — no hardcoded Customer name list
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiping `Work/Emails/`/the two `.second-brain/` JSON stores — `T01`.
- Recapturing Outlook history — `T02`.
- Requiring/forcing approval of any Pending Approval this function
  produces — ordinary, ongoing operator review, decoupled from this
  story's own Definition of Done.
- The Partner namespace and any legacy flat Project-kind note (see
  Constraints).

---

## Context / Notes

`Implementation/Architecture/architecture.md` → "Vault Migration..." section,
`regenerate_customer_notes` bullet, and `ADR-047` Decision 5/Alternative 3
are the full architectural reasoning this task implements — including why
auto-writing durable content directly (bypassing Pending Approval) was
explicitly rejected.

`ESCALATIONS.md` → `ESC-046` is the exact collision this task resolves as a
direct, in-scope consequence (`ADR-047` Decision 5/Alternative 4) — not a
separately deferred `BUGFIX-NN-US-01`. `REVIEW-QUEUE.md` carries the
human's pointer to confirm this resolution.

**No functional dependency on `T01`/`T02` (a deliberate decomposer
finding, not an assumption carried over from the story's own stub table):**
this function's own `evidence_text` is the flat legacy note's OWN
pre-migration body (read via `vault_writer.read_note`, never anything `T02`
recaptures), and `synthesize_customer`'s `## Glimpse` rollup
(`_build_customer_glimpse`) reads existing Project frontmatter under that
Customer's own directory — never a Thread/email note either. Neither
touches `Work/Emails/`, the two `.second-brain/` JSON stores `T01`
archives, or anything `T02`'s Outlook recapture writes. `depends_on: []`
reflects this directly-verified absence of a real code-level dependency —
see `T02`'s own Context for the same reasoning from the other side. This
does not mean run order is meaningless operationally (an operator would
still naturally trigger `T01` → `T02` → `T03` as one migration event), only
that no task's own correctness requires a prior task's own output.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
