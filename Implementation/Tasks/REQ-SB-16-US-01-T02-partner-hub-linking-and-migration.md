---
id: REQ-SB-16-US-01-T02
title: New app/business/partner_hub_linking.py — hub-note orchestration plus the Customer-to-Partner migration
parent_story: REQ-SB-16-US-01
requirement_id: REQ-SB-16
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-16-US-01-T01]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-16-US-01-T02 — New app/business/partner_hub_linking.py — hub-note orchestration plus the Customer-to-Partner migration

## Parent Story

- Story: [[REQ-SB-16-US-01]] — `../UserStories/REQ-SB-16-US-01-partner-hub-notes-and-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-16 *Partner Hub Notes & Graph Connectivity*

---

## Objective

Create the new, dedicated `app/business/partner_hub_linking.py` module
(ADR-009 point 2 — a parallel sibling to `customer_hub_linking.py`, **not**
an extension of it): the two granular "ensure hub note / link note"
primitives T03 will call from `people_extraction.ensure_person_note`, plus
the one-time `migrate_customer_to_partner` operation T04 exposes over HTTP.

---

## Starting State → End State

**Before / Inputs:**
- T01 added the Partner baseline primitives and the four generic
  rename/remove/swap/replace primitives this module orchestrates.
- `app/business/customer_hub_linking.py` is the exact structural precedent
  for the two granular primitives (unchanged by this task, per ADR-009 and
  the story's own Non-Goals).

**After / Outputs:**
- A new file, `app/business/partner_hub_linking.py`, exposing
  `ensure_partner_hub_note`, `link_note_to_partner_hub`, and
  `migrate_customer_to_partner`.

---

## Files to Modify

- `src/backend/app/business/partner_hub_linking.py` (new file):

  ```python
  """Partner hub-note orchestration (REQ-SB-16, ADR-009) — a parallel
  sibling to customer_hub_linking.py, not an extension of it (full
  reasoning: ADR-009 — keeps the Done, mechanism-Accepted REQ-SB-14 module
  and its email_classification.py call site untouched). Structurally
  mirrors customer_hub_linking.py's two granular primitives
  (ensure_partner_hub_note, link_note_to_partner_hub) exactly, plus the
  one-time Customer->Partner migration (migrate_customer_to_partner) —
  see that function's own docstring for why one generic scan pass handles
  both the moved hub note's own frontmatter rewrite and every other
  mistagged note.
  """
  from __future__ import annotations

  from pathlib import Path

  from app.data_access import vault_writer


  def ensure_partner_hub_note(partner: str) -> dict:
      """Ensures partner's hub note exists: creates a baseline note if
      missing, or tops up any missing baseline frontmatter keys if it
      already exists, without touching a key already present or the body.
      Mirrors customer_hub_linking.ensure_customer_hub_note exactly, for
      Partner's shorter baseline-key set (no affiliate_of). Returns
      {"hub_note_path": str, "created": bool}."""
      hub_path = vault_writer.partner_hub_note_path(partner)
      if vault_writer.partner_hub_note_exists(partner):
          vault_writer.ensure_partner_hub_note_baseline_frontmatter(hub_path, partner)
          return {"hub_note_path": str(hub_path), "created": False}
      created_path = vault_writer.create_partner_hub_note_baseline(partner)
      return {"hub_note_path": created_path, "created": True}


  def link_note_to_partner_hub(note_path, partner: str) -> bool:
      """Ensures note_path's body carries the inline `**Partner:** [[Hub]]`
      wikilink to partner's hub note, inserting it only if not already
      present. Mirrors customer_hub_linking.link_note_to_customer_hub
      exactly. Returns True if newly added, False if already present
      (idempotent rerun)."""
      note_path = Path(note_path)
      hub_stem = vault_writer.partner_hub_note_path(partner).stem
      link_line = f"**Partner:** [[{hub_stem}]]"
      return vault_writer.insert_body_line_if_missing(note_path, link_line)


  def migrate_customer_to_partner(customer_name: str) -> dict:
      """One-time migration (ADR-009): moves customer_name's Customer hub
      note into the Partner namespace, then retags every vault note whose
      `customer` frontmatter equals customer_name — a **generic,
      vault-wide scan**, never a hardcoded note list (ADR-009's rejected
      alternative), so it correctly picks up every mistagged note
      regardless of kind (Person/Email/Newsletter/Notification alike).

      Step 1 moves Work/Customers/<name>.md to Work/Partners/<name>.md via
      vault_writer.move_note_and_attachments (already exists), guarded by
      an existence check so a rerun — finding the Customer hub note
      already gone — skips the move entirely (this step's own idempotency
      mechanism). Deliberately does NOT rewrite the moved note's
      frontmatter here: step 2's single generic scan picks up the
      just-moved note too (list_all_note_paths() finds it at its new
      Work/Partners/ path, still carrying its old customer/type: Customer/
      tags/affiliate_of frontmatter until the scan rewrites it) — so
      exactly one retag mechanism handles both the hub note and every
      other mistagged note, with no duplicated rewrite logic between the
      two steps.

      Step 2 iterates every vault note via list_all_note_paths()/
      read_note() (the same pattern retrofit_customer_hub_links/
      retrofit_people_from_emails already use) and, for every note whose
      `customer` frontmatter equals customer_name: swaps `type: Customer`
      -> `type: Partner` (a no-op for every non-hub note, since their
      `type` is never "Customer"), drops `affiliate_of` if present
      (present only on the hub note — Partner has no such key), renames
      `customer` -> `partner` (same value), swaps the `customer/<slug>`
      tag for `partner/<slug>` and `kind/customer` for `kind/partner` (the
      latter a no-op for every non-hub note, since only the hub note ever
      carries `kind/customer`), and — only where present — relabels an
      inline `**Customer:** [[<name>]]` body line to
      `**Partner:** [[<name>]]`. Every primitive this step calls is itself
      a no-op-if-absent, so a second full run makes zero further changes
      anywhere (idempotent by construction — no separate "already
      migrated" tracking needed; a note already migrated no longer has a
      `customer` field equal to customer_name at all, so the very first
      `if` below already excludes it on a rerun).

      Returns {"hub_note_moved": bool, "hub_note_path": str | None,
      "notes_retagged": list[dict]}.
      """
      old_hub_path = vault_writer.hub_note_path(customer_name)
      hub_note_moved = False
      new_hub_note_path: str | None = None
      if old_hub_path.exists():
          new_hub_dir = vault_writer.partner_hub_note_path(customer_name).parent
          new_hub_note_path = vault_writer.move_note_and_attachments(old_hub_path, new_hub_dir)
          hub_note_moved = True

      old_tag = f"customer/{vault_writer.tag_slug(customer_name)}"
      new_tag = f"partner/{vault_writer.tag_slug(customer_name)}"
      hub_stem = vault_writer.hub_note_path(customer_name).stem
      old_body_line = f"**Customer:** [[{hub_stem}]]"
      new_body_line = f"**Partner:** [[{hub_stem}]]"

      notes_retagged: list[dict] = []
      for path in vault_writer.list_all_note_paths():
          frontmatter, _ = vault_writer.read_note(path)
          if frontmatter.get("customer") != customer_name:
              continue
          changed: list[str] = []
          if frontmatter.get("type") == "Customer":
              if vault_writer.rename_frontmatter_key(path, "type", "type", new_value="Partner"):
                  changed.append("type")
          if vault_writer.remove_frontmatter_key_if_present(path, "affiliate_of"):
              changed.append("affiliate_of_dropped")
          if vault_writer.rename_frontmatter_key(path, "customer", "partner"):
              changed.append("customer_to_partner")
          if vault_writer.swap_tag(path, old_tag, new_tag):
              changed.append("tag_swapped")
          if vault_writer.swap_tag(path, "kind/customer", "kind/partner"):
              changed.append("kind_tag_swapped")
          if vault_writer.replace_body_line(path, old_body_line, new_body_line):
              changed.append("body_line_relabeled")
          notes_retagged.append({
              "note": str(path),
              "status": "retagged" if changed else "already_migrated",
              "changes": changed,
          })

      return {
          "hub_note_moved": hub_note_moved,
          "hub_note_path": new_hub_note_path,
          "notes_retagged": notes_retagged,
      }
  ```

---

## Constraints

- Inherits from parent story (ADR-003 layering: no HTTP, no direct
  filesystem I/O — every read/write goes through `vault_writer`; ADR-009's
  mutual-exclusivity and no-Affiliate-equivalent rules; idempotency is
  load-bearing, real live vault, real Microsoft migration data).
- Must NOT modify `customer_hub_linking.py`, `email_classification.py`,
  `meeting_classification.py`, or `email_poc_router.py` — this task only
  adds the new module, per the story's own Non-Goals (no per-write capture
  hook for Partner).
- `migrate_customer_to_partner` must be parameterised by `customer_name` —
  never hardcoded to `"Microsoft"`, even though Microsoft is the only real
  data today (architecture.md, ADR-009).
- The retag scan must never touch a note whose `customer` frontmatter does
  not equal `customer_name` exactly.

---

## Tests

<!-- This task's own functions are exercised end-to-end, live, by T03 (the
Person-note orchestration branch — AC-01/02/03/04/08) and T04 (the
migration endpoint — AC-05/06/07), which is where this story's locked ACs
are tagged. The smoke check below is a non-AC-tagged confirmation that this
module's functions behave correctly in isolation before T03/T04 build on
them. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`, call
   `ensure_partner_hub_note("Verify-T02-Partner")`. Confirm the returned
   dict has `created: True` and `Work/Partners/Verify-T02-Partner.md` now
   exists with the Partner schema (no `affiliate_of`). Call it again and
   confirm `created: False` (already exists, baseline topped up only if
   needed — nothing to top up here). Call `link_note_to_partner_hub(<a
   throwaway note path>, "Verify-T02-Partner")` — confirm it returns `True`
   and the note's body now starts with
   `**Partner:** [[Verify-T02-Partner]]`; call it again and confirm `False`
   (no duplicate line).
2. Non-AC smoke check: create a throwaway Customer hub note via
   `vault_writer.create_customer_hub_note_baseline("Verify-T02-Migrate")`,
   plus a throwaway Person note written directly via `vault_writer.
   create_person_note_baseline` with `customer: "Verify-T02-Migrate"`
   frontmatter added afterward (via `vault_writer.
   insert_frontmatter_key_if_missing`) and a
   `**Customer:** [[Verify-T02-Migrate]]` body line (via `vault_writer.
   insert_body_line_if_missing`) — reproducing the real Microsoft-shaped
   mistagged data at small scale. Call `migrate_customer_to_partner
   ("Verify-T02-Migrate")`. Confirm `hub_note_moved: True`,
   `Work/Partners/Verify-T02-Migrate.md` now exists (with `type: Partner`,
   `partner:`, `tags: [partner/verify-t02-migrate, kind/partner]`, no
   `affiliate_of`), `Work/Customers/Verify-T02-Migrate.md` no longer
   exists, and the throwaway Person note's `customer` frontmatter is now
   `partner:`, its tag is now `partner/verify-t02-migrate`, and its body
   line now reads `**Partner:** [[Verify-T02-Migrate]]`. Call
   `migrate_customer_to_partner("Verify-T02-Migrate")` again and confirm
   `hub_note_moved: False`, `notes_retagged` shows `already_migrated` (or
   empty — no note still carries `customer: "Verify-T02-Migrate"`), and no
   file changes. Delete all throwaway test files afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `ensure_partner_hub_note` creates a baseline hub note when missing,
      tops up only missing baseline keys when it already exists
- [x] `link_note_to_partner_hub` is idempotent (second call is a no-op,
      returns `False`)
- [x] `migrate_customer_to_partner` moves the hub note, retags every note
      whose `customer` equals the given name (frontmatter key, `type`
      value, tags, body line), and is idempotent on rerun
- [x] `migrate_customer_to_partner` is parameterised, never hardcoded to
      `"Microsoft"`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Deciding *when* Partner linking applies during Person-note orchestration
  (`find_matching_partner`, the Customer-checked-first ordering) — that is
  T03 (`people_extraction.py`).
- Exposing `migrate_customer_to_partner` as an HTTP endpoint — that is T04.
- Any per-write capture-pipeline hook — explicitly out of scope for the
  whole story (see the story's own Non-Goals).

---

## Context / Notes

Mirrors `customer_hub_linking.py`'s existing shape for the two granular
primitives exactly. `migrate_customer_to_partner`'s "one generic scan
handles the hub note's own rewrite too" design is a task-level
implementation choice consistent with — and not contradicting —
`architecture.md`'s two-numbered-step description (move, then generic
retag pass): the moved hub note is simply the first note the generic scan's
own `customer == customer_name` check happens to match, so no separate
hub-note-specific rewrite branch is needed.

---

## Implementation Log

**2026-08-11, coder.** Created `src/backend/app/business/partner_hub_linking.py`
verbatim per this task's `## Files to Modify` spec. Confirmed it imports
cleanly alongside `customer_hub_linking`/`people_extraction`/
`email_poc_router` (no circular-import or layering issue).

**Non-AC smoke checks (this task's own ACs are not story-locked; verified
per its own `## Tests`/`## Acceptance Criteria`, all against throwaway
data, all PASS):**
- `ensure_partner_hub_note("Verify-T02-Partner")` — first call `created:
  True`, hub note written with the correct schema; second call `created:
  False`, no duplicate.
- `link_note_to_partner_hub` on a throwaway note — first call `True`, body
  gained `**Partner:** [[Verify-T02-Partner]]`; second call `False`, no
  duplicate line.
- `migrate_customer_to_partner("Verify-T02-Migrate")` against a small,
  faithfully-reproduced Microsoft-shaped fixture (a throwaway Customer hub
  note + a throwaway Person note carrying `customer: Verify-T02-Migrate`
  frontmatter, a `customer/verify-t02-migrate` tag, and a
  `**Customer:** [[Verify-T02-Migrate]]` body line): first call moved the
  hub note to `Work/Partners/`, rewrote its frontmatter to the Partner
  schema (`type`/`partner`/`tags`, `affiliate_of` dropped), and correctly
  retagged the Person-note fixture (frontmatter key, tag, body line all
  swapped). Second call: `hub_note_moved: False`, `notes_retagged: []` — a
  true no-op, confirming idempotency by construction. All throwaway files
  deleted afterward.

**Note (not a deviation, logged for visibility):** this task's own smoke
check deliberately used a Person-note fixture carrying `customer:`
frontmatter directly (as instructed in this task's own `## Tests` step 2),
which is exactly how Email/Newsletter/Notification notes are actually
tagged in the real vault — but is **not** how real Person notes are tagged
(they never carry a `customer:` field, only `company/<slug>`). This
function behaves exactly as this task specifies against that fixture shape;
the mismatch between that fixture shape and the real Person notes' actual
schema is the live-data gap `REQ-SB-16-US-01-T04`'s own live verification
found and escalated (`ESCALATIONS.md` → `ESC-001`) — not a defect in this
task's own code relative to its own spec.

**Status:** `Done`. `gate: clear` — no new trigger fired by this task in
isolation.
