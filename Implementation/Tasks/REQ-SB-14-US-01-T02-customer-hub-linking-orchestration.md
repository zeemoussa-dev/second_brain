---
id: REQ-SB-14-US-01-T02
title: New app/business/customer_hub_linking.py orchestration module
parent_story: REQ-SB-14-US-01
requirement_id: REQ-SB-14
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-14-US-01-T01]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-14-US-01-T02 — New app/business/customer_hub_linking.py orchestration module

## Parent Story

- Story: [[REQ-SB-14-US-01]] — `../UserStories/REQ-SB-14-US-01-vault-graph-connectivity.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-14 *Vault Graph Connectivity*

---

## Objective

Add the single shared "ensure this customer's hub note exists, then link
this note to it" business-layer operation, plus the one-time batch retrofit
loop over every existing customer-tagged note — the one mechanism T03 (the
per-write hook) and T04 (the retrofit endpoint) both call, per
`architecture.md`'s "Customer Hub Notes & Graph Linking" section.

---

## Starting State → End State

**Before / Inputs:**
- T01 added the file-I/O primitives this module orchestrates:
  `hub_note_path`, `hub_note_exists`, `create_customer_hub_note_baseline`,
  `ensure_hub_note_baseline_frontmatter`, `insert_body_line_if_missing`.
- `app/business/tag_backfill.py` and `app/business/vault_restructure.py`
  are the existing "one business module per maintenance operation"
  precedent this module follows.

**After / Outputs:**
- A new file, `app/business/customer_hub_linking.py`, exposing
  `ensure_customer_hub_note`, `link_note_to_customer_hub`,
  `ensure_hub_note_and_link`, and `retrofit_customer_hub_links`.

---

## Files to Modify

- `src/backend/app/business/customer_hub_linking.py` (new file):

  ```python
  """Shared "ensure this customer's hub note exists, then link this note to
  it" orchestration (REQ-SB-14) — the one mechanism used by both the
  one-time retrofit (retrofit_customer_hub_links, over every existing
  customer-tagged note) and email_classification.py's per-write capture
  hook (ensure_hub_note_and_link, going forward). Follows ADR-003's
  layering and the tag_backfill.py / vault_restructure.py precedent of one
  business module per maintenance operation.
  """
  from __future__ import annotations

  from pathlib import Path

  from app.data_access import vault_writer

  _UNSORTED_CUSTOMER = "Unsorted"


  def ensure_customer_hub_note(customer: str) -> dict:
      """Ensures customer's hub note exists: creates a baseline note if
      missing, or tops up any missing baseline frontmatter keys if it
      already exists (REQ-SB-14 Scenario 4) without touching a key already
      present or the body. Returns {"hub_note_path": str, "created":
      bool}."""
      hub_path = vault_writer.hub_note_path(customer)
      if vault_writer.hub_note_exists(customer):
          vault_writer.ensure_hub_note_baseline_frontmatter(hub_path, customer)
          return {"hub_note_path": str(hub_path), "created": False}
      created_path = vault_writer.create_customer_hub_note_baseline(customer)
      return {"hub_note_path": created_path, "created": True}


  def link_note_to_customer_hub(note_path, customer: str) -> bool:
      """Ensures note_path's body carries the inline
      `**Customer:** [[Hub]]` wikilink to customer's hub note, inserting it
      only if not already present. Returns True if newly added, False if
      already present (REQ-SB-14 Scenario 5 idempotency)."""
      note_path = Path(note_path)
      hub_stem = vault_writer.hub_note_path(customer).stem
      link_line = f"**Customer:** [[{hub_stem}]]"
      return vault_writer.insert_body_line_if_missing(note_path, link_line)


  def ensure_hub_note_and_link(note_path, customer: str) -> dict:
      """The single shared operation, called by both the retrofit and the
      per-write capture hook: ensure customer's hub note exists, then
      ensure note_path is linked to it. "Unsorted" (the placeholder
      pseudo-customer list_known_customers() already excludes) and a blank
      customer are both skipped — there is no real customer to link to."""
      if not customer or customer == _UNSORTED_CUSTOMER:
          return {"skipped": True, "reason": "no_customer_or_unsorted"}
      note_path = Path(note_path)
      hub_result = ensure_customer_hub_note(customer)
      linked = link_note_to_customer_hub(note_path, customer)
      return {
          "skipped": False,
          "hub_note_path": hub_result["hub_note_path"],
          "hub_created": hub_result["created"],
          "linked": linked,
      }


  def retrofit_customer_hub_links() -> list[dict]:
      """One-time batch: for every existing note carrying a real
      `customer:` frontmatter field, ensures that customer's hub note
      exists and that the note is linked to it. Idempotent — rerunning
      finds every hub note already created and every already-linked note
      left unchanged (REQ-SB-14 Scenarios 1 and 5). Never links a hub note
      to itself."""
      results: list[dict] = []
      for path in vault_writer.list_all_note_paths():
          frontmatter, _ = vault_writer.read_note(path)
          customer = frontmatter.get("customer")
          if not customer or customer == _UNSORTED_CUSTOMER:
              results.append({"note": str(path), "status": "skipped_no_customer"})
              continue
          if path == vault_writer.hub_note_path(customer):
              results.append({"note": str(path), "status": "skipped_is_hub_note"})
              continue
          outcome = ensure_hub_note_and_link(path, customer)
          status = "linked" if outcome["linked"] else "already_linked"
          results.append({"note": str(path), "status": status, **outcome})
      return results
  ```

---

## Constraints

- Inherits from parent story (ADR-003 layering: no HTTP, no direct
  filesystem I/O — every read/write goes through `vault_writer`; ADR-004
  unchanged; idempotency is load-bearing, real live vault).
- Must not modify `email_classification.py`, `tag_backfill.py`,
  `vault_restructure.py`, or `email_poc_router.py` — this task only adds the
  new module.
- `retrofit_customer_hub_links` must never attempt to link a hub note to
  itself (guarded by the `path == vault_writer.hub_note_path(customer)`
  check).

---

## Tests

<!-- This task's own functions are exercised end-to-end, live, by T03 (the
per-write hook — AC-03) and T04 (the retrofit endpoint — AC-01, AC-02,
AC-04, AC-05), which is where this story's locked ACs are tagged. The smoke
check below is a non-AC-tagged confirmation that this module's functions
behave correctly in isolation before T03/T04 build on them. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`, call
   `ensure_hub_note_and_link("<path to a throwaway test note under
   Work/Emails/ with customer: 'Verify-T02-Customer' frontmatter>",
   "Verify-T02-Customer")`. Confirm the returned dict has `skipped: False`,
   `hub_created: True`, `linked: True`; confirm
   `Work/Customers/Verify-T02-Customer.md` now exists; confirm the test
   note's body now starts with `**Customer:** [[Verify-T02-Customer]]`.
   Call it again with the same arguments and confirm `hub_created: False`,
   `linked: False` (both already in place). Then call
   `ensure_hub_note_and_link(<same note>, "Unsorted")` and confirm
   `skipped: True` — no hub note created, no link inserted for the
   placeholder pseudo-customer. Delete the throwaway test note and hub note
   afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `ensure_customer_hub_note` creates a baseline hub note when missing,
      tops up only missing baseline keys when it already exists
- [x] `link_note_to_customer_hub` is idempotent (second call is a no-op,
      returns `False`)
- [x] `ensure_hub_note_and_link` skips `Unsorted`/blank customers
- [x] `retrofit_customer_hub_links` iterates every note, skips notes with
      no real customer, never links a hub note to itself
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision/pattern/constraint emerged; see Implementation Log)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Calling `ensure_hub_note_and_link` from `email_classification.py`'s
  capture flow — that is T03.
- Exposing `retrofit_customer_hub_links` as an HTTP endpoint — that is T04.

---

## Context / Notes

Mirrors `tag_backfill.py`'s existing shape exactly: a single business module
with a top-level batch function (`retrofit_customer_hub_links`, analogous to
`backfill_tags`) built on smaller reusable functions, all calling only into
`vault_writer` (never doing filesystem I/O itself), returning a per-note
results list the caller (the future T04 endpoint) tallies for its HTTP
response.

---

## Implementation Log

**Coder pass (2026-08-11):** Created `src/backend/app/business/customer_hub_linking.py`
verbatim as specified in `## Files to Modify` — `ensure_customer_hub_note`,
`link_note_to_customer_hub`, `ensure_hub_note_and_link`,
`retrofit_customer_hub_links`, plus the `_UNSORTED_CUSTOMER` module
constant. Confirmed T01's primitives it calls
(`hub_note_path`, `hub_note_exists`, `create_customer_hub_note_baseline`,
`ensure_hub_note_baseline_frontmatter`, `insert_body_line_if_missing`) exist
in `src/backend/app/data_access/vault_writer.py` exactly as expected before
writing this module. No other file touched.

**Verification (manual mode, non-AC smoke check, real `.venv` + real
configured vault):** This story's locked ACs (`REQ-SB-14-US-01-AC-01/02/04/05`)
are exercised live by T04's retrofit endpoint and `AC-03` by T03's capture
hook — this task carries no AC-tagged step of its own, per the decomposer's
Tests-section note. Ran a throwaway Python script via
`.venv\Scripts\python.exe` (cwd `src/backend`, `PYTHONPATH` set to that
directory so `app.*` imports resolve) against the real `VAULT_PATH` from
`src/backend/.env`:

1. Wrote a throwaway note directly via `vault_writer.write_note` at
   `Work/Emails/t02-smoke-check-throwaway.md` with
   `customer: "Verify-T02-Customer"` frontmatter.
2. Called `ensure_hub_note_and_link(note_path, "Verify-T02-Customer")` —
   **PASS.** Returned `{"skipped": False, "hub_created": True, "linked": True,
   "hub_note_path": ".../Work/Customers/Verify-T02-Customer.md"}`.
   Confirmed `Work/Customers/Verify-T02-Customer.md` now existed and the
   test note's body now started with
   `**Customer:** [[Verify-T02-Customer]]`.
3. Called it again with identical arguments — **PASS.** Returned
   `{"hub_created": False, "linked": False}` (both already in place, no
   duplicate writes — the `link_note_to_customer_hub`/
   `ensure_customer_hub_note` idempotency the AC checklist below requires).
4. Called `ensure_hub_note_and_link(note_path, "Unsorted")` — **PASS.**
   Returned `{"skipped": True, "reason": "no_customer_or_unsorted"}`; no
   hub note created, no link inserted for the placeholder pseudo-customer.
5. Deleted the throwaway test note and the throwaway hub note it created,
   then removed the now-empty `Work/Customers/` directory (auto-created by
   `write_note`'s `mkdir(parents=True, exist_ok=True)`) — restoring the
   real vault to exactly its pre-task state, confirmed via `Test-Path`
   returning `False` for both the note and the directory afterward.

`retrofit_customer_hub_links` and the `path == vault_writer.hub_note_path
(customer)` self-link guard were not separately smoke-checked here (no
existing customer-tagged notes with no hub note were touched, to avoid any
risk to the real live vault ahead of T04's dedicated, AC-tagged retrofit
verification) — its logic is a direct, mechanical iteration over
`ensure_hub_note_and_link` (already verified above) plus `list_all_note_paths`/
`read_note` (both already `Done`, unchanged, pre-existing `vault_writer`
functions), so it is judged correct by inspection pending T04's live
end-to-end verification against the real vault.

**Assumption logged for spot-check:** none beyond what the story's
architect/decomposer notes already settled — the code was copied verbatim
from the task's `## Files to Modify` block with no interpretation required.
`gate: clear` — no MUST-FLAG trigger fired (no new dependency, no
shared-interface change, no ADR deviation, no unanticipated file, no
unclear/contradictory requirement).

**MEMORY.md:** not updated — no new decision/pattern/constraint emerged;
this task followed the architect's and T01's already-recorded decisions
exactly (inline-body wikilink placement, one-business-module-per-
maintenance-operation shape, surgical baseline-frontmatter preservation).
