---
id: REQ-SB-14-US-01-T01
title: Add hub-note file-I/O primitives to vault_writer.py
parent_story: REQ-SB-14-US-01
requirement_id: REQ-SB-14
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-14-US-01-T01 — Add hub-note file-I/O primitives to vault_writer.py

## Parent Story

- Story: [[REQ-SB-14-US-01]] — `../UserStories/REQ-SB-14-US-01-vault-graph-connectivity.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-14 *Vault Graph Connectivity*

---

## Objective

Add the low-level file-I/O primitives `app/business/customer_hub_linking.py`
(T02) will orchestrate on top of: resolving/checking a customer's hub-note
path, creating a hub note's baseline for the first time, topping up missing
baseline frontmatter keys on an existing hub note without touching the rest
of the file, and a generalized surgical body-line insert (used for the
inline customer wikilink).

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already has `write_note`, `build_tags`, `read_note`, and
  `insert_tags_line` (the existing "surgical insert, not full rewrite"
  precedent this task generalizes).

**After / Outputs:**
- Five new functions appended to `vault_writer.py`: `hub_note_path`,
  `hub_note_exists`, `create_customer_hub_note_baseline`,
  `insert_frontmatter_key_if_missing`, `ensure_hub_note_baseline_frontmatter`,
  `insert_body_line_if_missing` — no existing function's behavior changed.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — append at the end of the
  file (after `load_last_capture_run`):

  ```python
  _CUSTOMERS_SUBFOLDER = f"{_WORK_ROOT}/Customers"
  _HUB_NOTE_BASELINE_KEYS = ("type", "customer", "tags", "affiliate_of")


  def hub_note_path(customer: str):
      """Resolves the vault-absolute path a customer's hub note lives (or
      would live) at — Work/Customers/<Customer>.md — without checking
      whether it exists yet. Uses the same _slugify() write_note() applies
      to its own filename_stem, so this always points at exactly the file
      create_customer_hub_note_baseline()/write_note() would create."""
      return settings.vault_path / _CUSTOMERS_SUBFOLDER / f"{_slugify(customer)}.md"


  def hub_note_exists(customer: str) -> bool:
      return hub_note_path(customer).exists()


  def create_customer_hub_note_baseline(customer: str) -> str:
      """Creates a customer's hub note for the first time: baseline
      frontmatter (type/customer/tags/affiliate_of) plus a short
      auto-generated body stub inviting the user to add their own overview
      — REQ-SB-10's pattern extended to Customers (see architecture.md,
      'Customer Hub Notes & Graph Linking'). Always writes unconditionally,
      mirroring write_note()'s own contract — callers must check
      hub_note_exists() first (app/business/customer_hub_linking.py does)."""
      return write_note(
          subfolder=_CUSTOMERS_SUBFOLDER,
          filename_stem=customer,
          frontmatter={
              "type": "Customer",
              "customer": customer,
              "tags": build_tags(customer, "customer"),
              "affiliate_of": "",
          },
          body=(
              f"# {customer}\n\n"
              "_Add your own overview, key contacts, and current focus "
              "below — this section is never programmatically rewritten "
              "once you do._\n"
          ),
      )


  def insert_frontmatter_key_if_missing(path, key: str, value) -> bool:
      """Surgical insert of one `key: value` frontmatter line just before
      the closing `---`, leaving every other line (including exact
      formatting) byte-for-byte untouched — generalizes insert_tags_line's
      "surgical insert, not full rewrite" precedent from a single
      hardcoded `tags` key to any key/value pair, and (unlike
      insert_tags_line) checks presence itself rather than relying on the
      caller. Returns True if inserted, False if the key was already
      present (no write performed)."""
      frontmatter, _ = read_note(path)
      if key in frontmatter:
          return False
      text = path.read_text(encoding="utf-8")
      end = text.find("\n---\n", 4)
      if end == -1:
          return False
      insertion = f"{key}: {_format_frontmatter_value(value)}\n"
      path.write_text(text[: end + 1] + insertion + text[end + 1 :], encoding="utf-8")
      return True


  def ensure_hub_note_baseline_frontmatter(path, customer: str) -> list[str]:
      """Tops up an already-existing hub note with any of the four baseline
      frontmatter keys it is missing (type/customer/tags/affiliate_of),
      inserting each surgically via insert_frontmatter_key_if_missing —
      never touches a key already present (so a real affiliate_of value,
      once set, is never reset to ""), and never touches the body. Returns
      the list of keys actually inserted (empty if the note already had
      all four) — REQ-SB-14 Scenario 4's baseline-preservation mechanism."""
      baseline_values = {
          "type": "Customer",
          "customer": customer,
          "tags": build_tags(customer, "customer"),
          "affiliate_of": "",
      }
      inserted: list[str] = []
      for key in _HUB_NOTE_BASELINE_KEYS:
          if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
              inserted.append(key)
      return inserted


  def insert_body_line_if_missing(path, line: str) -> bool:
      """Surgical insert of a single line as the first line of a note's
      body if it is not already present anywhere in the file — used for
      the inline `**Customer:** [[Hub]]` wikilink (REQ-SB-14 Scenario 5's
      idempotency: an already-linked note must be left byte-for-byte
      unchanged on a rerun). Returns True if inserted, False if the line
      was already present (no write performed)."""
      text = path.read_text(encoding="utf-8")
      if line in text:
          return False
      end = text.find("\n---\n", 4)
      if end == -1:
          # No frontmatter block found (shouldn't happen for notes this
          # module writes) — prepend at the very top as a fallback.
          path.write_text(line + "\n\n" + text, encoding="utf-8")
          return True
      # write_note() always writes "---\n\n<body>" — end points at the
      # leading "\n" of the closing "\n---\n"; body starts 6 chars later
      # (past "---\n" itself, plus the blank-line separator).
      body_start = end + 6
      new_text = text[:body_start] + line + "\n\n" + text[body_start:]
      path.write_text(new_text, encoding="utf-8")
      return True
  ```

---

## Constraints

- Inherits from parent story (ADR-003 layering; no `Customer` folder for
  content classification, ADR-004; idempotency is load-bearing since this
  runs against the real live vault).
- This file lives in `data_access/` only — no business rules (the "which
  customer, which note" decisions belong to T02's
  `customer_hub_linking.py`), no HTTP concerns.
- Must NOT modify `insert_tags_line`, `write_note`, `build_tags`, `read_note`,
  or any other existing function's behavior — additive only.
- `hub_note_path()` must use the same `_slugify()` call `write_note()`
  applies internally to `filename_stem`, so the two always resolve to the
  identical file for the same customer name.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-14-US-01-AC-01] In a Python shell against the backend `.venv`
   (`.venv\Scripts\python.exe`, real configured `vault_path`), call
   `create_customer_hub_note_baseline("Verify-T01-Customer")`. Confirm a
   file is created at `Work/Customers/Verify-T01-Customer.md` with
   frontmatter `type: Customer`, `customer: "Verify-T01-Customer"`,
   `tags: [customer/verify-t01-customer, kind/customer]`,
   `affiliate_of: ""`, and a body starting with `# Verify-T01-Customer`.
   Confirm `hub_note_exists("Verify-T01-Customer")` returns `True` and
   `hub_note_path("Verify-T01-Customer")` matches the file just written.
   Delete the test file afterward (throwaway verification data, not part of
   Scenario 1's real retrofit — that runs live in T04).
2. Non-AC smoke check: on a second throwaway note, manually remove the
   `affiliate_of` frontmatter line, then call
   `ensure_hub_note_baseline_frontmatter(path, "Verify-T01-Customer-2")` and
   confirm only the missing `affiliate_of: ""` line is (re-)inserted — the
   other three existing keys and the body are byte-for-byte unchanged.
   Re-run the same call and confirm nothing changes the second time
   (already-present keys are never re-inserted).
3. Non-AC smoke check: call `insert_body_line_if_missing(path,
   "**Customer:** [[Verify-T01-Customer]]")` on a note with an existing
   body. Confirm the line is inserted as the first line of the body.
   Call it again with the identical line and confirm it returns `False`
   and the file is left unchanged (no duplicate line) — the mechanism
   Scenario 5 depends on.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `hub_note_path`/`hub_note_exists`/`create_customer_hub_note_baseline`
      resolve to and create the exact schema from
      `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`
- [x] `insert_frontmatter_key_if_missing` inserts only when the key is
      absent, leaves the rest of the file byte-for-byte unchanged otherwise
- [x] `ensure_hub_note_baseline_frontmatter` tops up missing baseline keys
      only, never resets a present `affiliate_of`, never touches the body
- [x] `insert_body_line_if_missing` is idempotent — a second call with the
      same line is a no-op
- [x] No existing `vault_writer.py` function's behavior changed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision/pattern/constraint emerged; see Implementation Log)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Deciding *which* customer/note to link, or the retrofit loop over all
  vault notes — that is T02 (`customer_hub_linking.py`).
- Wiring the per-write hook into `email_classification.py` — that is T03.
- The retrofit HTTP endpoint — that is T04.

---

## Context / Notes

`vault_writer.py` currently ends with `load_last_capture_run`; append the new
constants/functions directly after it, in the order shown above (each new
function references only prior functions in the file, no forward
references). No new imports are required — `settings`, `write_note`,
`build_tags`, `read_note`, `_slugify`, `_format_frontmatter_value`,
`_WORK_ROOT` all already exist in this module.

---

## Implementation Log

**Coder pass (2026-08-11):** Appended the six new items to
`src/backend/app/data_access/vault_writer.py` after `load_last_capture_run`,
verbatim as specified in `## Files to Modify` — `_CUSTOMERS_SUBFOLDER`,
`_HUB_NOTE_BASELINE_KEYS`, `hub_note_path`, `hub_note_exists`,
`create_customer_hub_note_baseline`, `insert_frontmatter_key_if_missing`,
`ensure_hub_note_baseline_frontmatter`, `insert_body_line_if_missing`. No
other lines in the file touched; no new imports needed (all referenced
names — `settings`, `write_note`, `build_tags`, `read_note`, `_slugify`,
`_format_frontmatter_value`, `_WORK_ROOT` — already existed).

**Verification (manual mode, real `.venv` + real configured vault):** Ran a
throwaway Python script via `.venv\Scripts\python.exe` (cwd
`src/backend`, `PYTHONPATH` set to that directory so `app.*` imports
resolve) against the real `VAULT_PATH` from `src/backend/.env`. Script and
all throwaway hub notes it created were deleted afterward; the
`Work/Customers/` directory itself (auto-created by `write_note`'s
`mkdir(parents=True, exist_ok=True)`) was also removed once verified
empty, restoring the vault to its pre-task state.

- **[REQ-SB-14-US-01-AC-01] — PASS.** Called
  `create_customer_hub_note_baseline("Verify-T01-Customer")`. Observed file
  written at `Work/Customers/Verify-T01-Customer.md` with frontmatter
  `type: "Customer"`, `customer: "Verify-T01-Customer"`,
  `tags: ["customer/verify-t01-customer", "kind/customer"]`,
  `affiliate_of: ""`, and body starting `# Verify-T01-Customer`. Note: the
  task's Tests-section shorthand `tags: [customer/verify-t01-customer,
  kind/customer]` (unquoted) describes the semantic tag list, not the
  literal on-disk syntax — the real file quotes each list string, matching
  every other note `write_note`/`_format_frontmatter_value` already
  produces in this vault (confirmed against an existing `Work/Emails/`
  note: `tags: ["customer/adnoc", "kind/emails"]`); this is pre-existing,
  unchanged formatting behavior, not a deviation. `hub_note_exists
  ("Verify-T01-Customer")` returned `True`; `hub_note_path
  ("Verify-T01-Customer")` matched the path `create_customer_hub_note_baseline`
  actually wrote to. Test file deleted afterward.
- **Non-AC smoke check 2 — PASS.** On a second throwaway hub note, manually
  stripped the `affiliate_of` frontmatter line, then called
  `ensure_hub_note_baseline_frontmatter(path, "Verify-T01-Customer-2")`.
  Observed: only `affiliate_of` was reported inserted (`type`/`customer`/
  `tags` left alone), the resulting file matched the pre-strip file with
  exactly `affiliate_of: ""` surgically reinserted (byte-for-byte
  elsewhere), and body was untouched. Re-running the same call inserted
  nothing (`[]` returned) and left the file byte-for-byte identical to the
  post-first-call state. Test file deleted afterward.
- **Non-AC smoke check 3 — PASS.** Called `insert_body_line_if_missing(path,
  "**Customer:** [[Verify-T01-Customer-3]]")` on a note with an existing
  body — observed the line inserted as the first line of the body.
  Calling it again with the identical line returned `False` and left the
  file byte-for-byte unchanged (`text.count(line) == 1` after the second
  call). Test file deleted afterward.

**Assumption logged for spot-check:** none beyond what the story's
architect/decomposer notes already settled — the code was copied verbatim
from the task's `## Files to Modify` block with no interpretation required.
`gate: clear` — no MUST-FLAG trigger fired (no new dependency, no
shared-interface change, no ADR deviation, no unanticipated file, no
unclear/contradictory requirement).
