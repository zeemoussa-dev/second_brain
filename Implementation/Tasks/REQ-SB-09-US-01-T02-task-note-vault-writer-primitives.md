---
id: REQ-SB-09-US-01-T02
title: Add Task-note file-I/O primitives (baseline create/top-up, upsert_frontmatter_key, task_note_index.json dedup) to vault_writer.py
parent_story: REQ-SB-09-US-01
requirement_id: REQ-SB-09
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-09-US-01-T02 — Add Task-note file-I/O primitives to vault_writer.py

## Parent Story

- Story: [[REQ-SB-09-US-01]] — `../UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-09 *To-Do Task Capture Pipeline*

---

## Objective

Add the low-level file-I/O primitives `T03` (`todo_classification.py`)
will orchestrate on top of: the load-bearing `task_note_index.json`
EntryID-keyed dedup/top-up lookup (`ADR-027` point 3 — consulted BEFORE
any path is computed from current Outlook fields, a genuine divergence
from Meeting's own recompute-and-`exists()`-check mechanism), Task-note
baseline create/top-up, and a new generic `upsert_frontmatter_key`
primitive the `due`/`status` fields need that no existing primitive in
this module provides.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.py` already has `write_note`, `read_note`, `tag_slug`,
  `insert_frontmatter_key_if_missing`, `insert_body_line_if_missing`,
  `rename_frontmatter_key` (Meeting/Partner/Customer precedent), and the
  `conversation_index.json` shape (`find_related_note_stems`/
  `record_conversation_note`) — the real key→value(s) index precedent this
  task's own `task_note_index.json` generalizes to a genuinely load-bearing
  (not merely audit) lookup.
- No Task-note primitives, no `upsert_frontmatter_key`, and no
  `task_note_index.json` exist yet.

**After / Outputs:**
- New items appended to `vault_writer.py`: `_TASKS_SUBFOLDER`,
  `_TASK_NOTE_INDEX_FILE`, `upsert_frontmatter_key`,
  `task_note_filename_stem`, `task_note_path_for_stem`,
  `task_note_exists_for_stem`, `build_task_tags`,
  `create_task_note_baseline`, `ensure_task_note_baseline_frontmatter`,
  `_task_note_index_path`, `load_task_note_index`,
  `lookup_task_note_stem`, `record_task_note`. No existing function's
  behavior changed.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:

  Append at the end of the file (after `save_pending_approvals_state`,
  the module's current last function):

  ```python
  def upsert_frontmatter_key(path, key: str, value) -> bool:
      """Ensures key: value is present with EXACTLY this value -- inserts
      if missing (mirroring insert_frontmatter_key_if_missing), or
      overwrites in place if already present but holding a different
      value (unlike insert_frontmatter_key_if_missing, which never
      touches an already-present key). Used for Task notes' due/status
      fields only (REQ-SB-09 Scenario 5/6) -- the one baseline-field pair
      this pipeline's own ACs require to reflect Outlook's CURRENT value
      on every top-up, not just fill a gap, unlike every other baseline
      key in this codebase so far (Customer/Person/Meeting all use strict
      insert-if-missing). Returns True if the file was written (inserted
      OR changed), False if the key was already present with an
      identical value (a true no-op)."""
      frontmatter, _ = read_note(path)
      if key not in frontmatter:
          return insert_frontmatter_key_if_missing(path, key, value)
      if frontmatter[key] == value:
          return False
      return rename_frontmatter_key(path, key, key, new_value=value)


  _TASKS_SUBFOLDER = f"{_WORK_ROOT}/Tasks"
  _TASK_NOTE_INDEX_FILE = "task_note_index.json"


  def task_note_filename_stem(subject: str, capture_date: str, entry_id: str) -> str:
      """<subject>-<capture-date>-<entry-id-suffix>. capture_date is the
      date this note was FIRST written -- the caller (T03) passes today's
      date only when creating a note for the first time, never
      recomputed from Outlook's own (mutable) due field on a later run
      (ADR-027 point 3) -- this is the load-bearing reason a due-date
      edit between runs still resolves to the SAME note (Scenario 6),
      unlike Meeting's own recompute-from-start scheme. capture_date is
      expected as a 'YYYY-MM-DD' string, mirroring
      meeting_note_filename_stem's [:10]-sliced start convention applied
      one layer up by the caller instead."""
      return f"{subject}-{capture_date}-{entry_id[-8:]}"


  def task_note_path_for_stem(stem: str):
      """Resolves the vault-absolute path for an ALREADY-KNOWN filename
      stem, looked up via task_note_index (lookup_task_note_stem, below)
      -- NOT a recompute-from-current-fields path resolver the way
      meeting_note_path works, since Task's own dedup key is the index
      entry itself, not a deterministic function of current field
      values (ADR-027 point 3). Uses the same _slugify() write_note()
      applies internally, so this always points at exactly the file
      create_task_note_baseline() would have created for that stem."""
      return settings.vault_path / _TASKS_SUBFOLDER / f"{_slugify(stem)}.md"


  def task_note_exists_for_stem(stem: str) -> bool:
      return task_note_path_for_stem(stem).exists()


  def build_task_tags(customer: str | None) -> list[str]:
      """Mirrors build_meeting_tags's shape for Tasks. Returns
      ["kind/task"] alone when no customer was derived (Scenario 3), or
      ["customer/<slug>", "kind/task"] when one was (Scenario 1)."""
      if not customer:
          return ["kind/task"]
      return [f"customer/{tag_slug(customer)}", "kind/task"]


  def create_task_note_baseline(
      subject: str,
      customer: str | None,
      due: str | None,
      status: str,
      entry_id: str,
      capture_date: str,
  ) -> str:
      """Creates a Task note for the first time. Unlike Meeting's
      create_meeting_note_baseline (which always writes a customer key,
      "" when none), Task's resolved schema requires customer/due to be
      ABSENT from frontmatter entirely when not applicable (Scenario 3;
      "absent otherwise" per the story's own ## Context), not written as
      empty placeholders -- both keys are conditionally included in the
      frontmatter dict below, never written unconditionally. The
      **Customer:**/[[wikilink]] body line is never written here -- it is
      inserted separately by the orchestration layer (T03), the same way
      link_note_to_customer_hub layers on top of ensure_customer_hub_note
      for every other captured note type. Always writes unconditionally,
      mirroring write_note()'s own contract -- callers must consult
      lookup_task_note_stem() first (T03 does) to decide create vs.
      top-up."""
      frontmatter: dict = {
          "type": "Task",
      }
      if customer:
          frontmatter["customer"] = customer
      frontmatter["subject"] = subject
      if due:
          frontmatter["due"] = due
      frontmatter["status"] = status
      frontmatter["tags"] = build_task_tags(customer)
      frontmatter["source"] = "outlook-task"
      frontmatter["outlook_entry_id"] = entry_id
      return write_note(
          subfolder=_TASKS_SUBFOLDER,
          filename_stem=task_note_filename_stem(subject, capture_date, entry_id),
          frontmatter=frontmatter,
          body="",
      )


  def ensure_task_note_baseline_frontmatter(
      path,
      subject: str,
      customer: str | None,
      due: str | None,
      status: str,
      entry_id: str,
  ) -> list[str]:
      """Tops up an already-existing Task note. type/subject/tags/source/
      outlook_entry_id/customer follow the established insert-only-if-
      missing contract (never overwritten once set, matching every other
      captured note type in this codebase) -- customer is only ever
      inserted, never re-derived-and-overwritten on a later run, the same
      accepted behavior Meeting's own ensure_meeting_note_baseline_
      frontmatter already established for its own customer field.
      due/status are the ONE deliberate exception (REQ-SB-09 Scenario
      5/6): upserted via upsert_frontmatter_key, so a status change (Not
      Started -> Completed) or a due-date edit in Outlook is reflected on
      the next capture run, not just filled in the first time a value
      exists. due is only touched when Outlook currently reports one
      (due is not None) -- a due date cleared in Outlook after being set
      is not a case any locked AC covers; the existing value is left
      untouched rather than guessing whether to remove it. Never touches
      the body -- the user's own manually-added content survives
      untouched regardless of which frontmatter keys change. Returns the
      list of keys actually inserted or changed (empty if nothing
      changed) -- Scenario 2/6's baseline-preservation mechanism."""
      changed: list[str] = []
      stable_values = {
          "type": "Task",
          "subject": subject,
          "tags": build_task_tags(customer),
          "source": "outlook-task",
          "outlook_entry_id": entry_id,
      }
      for key, value in stable_values.items():
          if insert_frontmatter_key_if_missing(path, key, value):
              changed.append(key)
      if customer and insert_frontmatter_key_if_missing(path, "customer", customer):
          changed.append("customer")
      if due is not None and upsert_frontmatter_key(path, "due", due):
          changed.append("due")
      if upsert_frontmatter_key(path, "status", status):
          changed.append("status")
      return changed


  def _task_note_index_path():
      state_dir = settings.vault_path / _STATE_DIR
      state_dir.mkdir(parents=True, exist_ok=True)
      return state_dir / _TASK_NOTE_INDEX_FILE


  def load_task_note_index() -> dict[str, str]:
      path = _task_note_index_path()
      if not path.exists():
          return {}
      return json.loads(path.read_text(encoding="utf-8"))


  def lookup_task_note_stem(entry_id: str) -> str | None:
      """The dedup/top-up lookup itself (ADR-027 point 3): consulted
      BEFORE any path is computed from current Outlook fields, not a
      recomputed-and-exists()-checked path the way Meeting's
      resolve_meeting_note_path works. Returns the note's own filename
      stem if entry_id has been seen before (regardless of what
      subject/due/status now read as in Outlook), or None if this is
      genuinely a new item never captured before."""
      return load_task_note_index().get(entry_id)


  def record_task_note(entry_id: str, stem: str) -> None:
      """Records entry_id -> stem the first (and, by this pipeline's own
      contract, ONLY the first) time a Task note is created for it -- a
      real, load-bearing key->value lookup (unlike processed_meeting_
      ids.json's flat audit-only set), mirroring conversation_index.
      json's own real-lookup shape (find_related_note_stems/
      record_conversation_note), generalized from key -> list[value] to
      key -> value. The caller (T03) only calls this on first creation,
      never on top-up -- a stem is never reassigned once recorded."""
      path = _task_note_index_path()
      index = load_task_note_index()
      index[entry_id] = stem
      path.write_text(json.dumps(index, indent=2), encoding="utf-8")
  ```

---

## Constraints

- Inherits from parent story (ADR-003 layering; Tasks never nested under a
  `Customer` folder — a direct extension of `ADR-004`'s folder-vs-tag
  reasoning; idempotency is load-bearing since this runs against the real
  live vault).
- This file lives in `data_access/` only — no business rules (customer
  classification, the create-vs-top-up decision) belong to `T03`'s
  `todo_classification.py`, no HTTP concerns.
- Must NOT modify any existing function's behavior — additive only.
  `upsert_frontmatter_key` is a genuinely NEW primitive (not a variant of
  `insert_frontmatter_key_if_missing`, which must keep its own
  insert-only-if-missing contract for every existing caller).
- `create_task_note_baseline`/`ensure_task_note_baseline_frontmatter` must
  write/consider `customer`/`due` as ABSENT keys (not empty-string
  placeholders) when not applicable — a deliberate divergence from
  Meeting's own `customer: ""` convention, per the resolved schema's own
  "absent otherwise" text (`## Context`, `REQ-SB-09-US-01`).
- `task_note_path_for_stem()`/`create_task_note_baseline()` must use the
  same `task_note_filename_stem()` helper, so path resolution and file
  creation always agree on the same file for the same stem.
- `lookup_task_note_stem`/`record_task_note` are generic state primitives
  only — this task does not decide when T03 calls them (only on
  create, never on top-up); see the docstrings above and `T03`'s own
  `## Context / Notes`.

---

## Tests

<!-- This task's own functions are exercised end-to-end, live, by T03
(todo_classification.py) -- this story's own locked ACs are tagged there,
not here. The smoke checks below are non-AC-tagged confirmations that
this module's new primitives behave correctly in isolation before T03
builds on them, mirroring REQ-SB-08-US-01-T02's own precedent for
Meeting's own vault_writer primitives. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`, call
   `create_task_note_baseline("Verify T02 Task", "Verify Customer",
   "2026-08-20", "Not Started", "abcdef1234567890", "2026-08-13")`.
   Confirm a file is created under `Work/Tasks/` whose name incorporates
   the subject, the `2026-08-13` capture date, and the entry-id suffix
   `34567890`, with frontmatter `type: "Task"`, `customer: "Verify
   Customer"`, `subject`/`due`/`status` populated, `tags:
   ["customer/verify-customer", "kind/task"]`, `source: "outlook-task"`,
   `outlook_entry_id`, and an empty body. Confirm
   `task_note_exists_for_stem(task_note_filename_stem("Verify T02 Task",
   "2026-08-13", "abcdef1234567890"))` returns `True`.
2. Non-AC smoke check: on a second throwaway note created WITHOUT a
   customer or due date (`create_task_note_baseline("Verify T02 No
   Customer", None, None, "Not Started", "fedcba0987654321",
   "2026-08-13")`), confirm the written frontmatter has NO `customer` key
   and NO `due` key at all (not empty strings) — confirms the
   resolved schema's "absent otherwise" contract, distinct from Meeting's
   own `customer: ""` convention.
3. Non-AC smoke check: on the first throwaway note, manually remove the
   `status` frontmatter line, then call
   `ensure_task_note_baseline_frontmatter(path, "Verify T02 Task",
   "Verify Customer", "2026-08-20", "In Progress", "abcdef1234567890")`
   and confirm `status` is (re-)inserted as `"In Progress"` and `"status"`
   appears in the returned changed-keys list — the other seven keys and
   the (empty) body are byte-for-byte unchanged.
4. Non-AC smoke check, the load-bearing upsert behavior (Scenario 5/6):
   call `ensure_task_note_baseline_frontmatter(path, "Verify T02 Task",
   "Verify Customer", "2026-08-25", "Completed", "abcdef1234567890")`
   again on the same note (now `due: "2026-08-20"`, `status: "In
   Progress"`). Confirm `due` is UPDATED to `"2026-08-25"` and `status` is
   UPDATED to `"Completed"` (both appear in the returned changed-keys
   list) — unlike every other baseline key in this codebase, these two
   are overwritten, not merely filled-if-missing. Call it a third time
   with the identical arguments and confirm the returned changed-keys
   list is empty (true no-op, file byte-for-byte unchanged).
5. Non-AC smoke check: call `record_task_note("abcdef1234567890",
   "verify-t02-task-2026-08-13-34567890")` then `load_task_note_index()`
   and confirm the mapping is present; call `lookup_task_note_stem
   ("abcdef1234567890")` and confirm it returns the same stem; call
   `lookup_task_note_stem("never-seen-entry-id")` and confirm it returns
   `None`. Delete both throwaway notes afterward and, if now empty, the
   `Work/Tasks/` directory and the `.second-brain/task_note_index.json`
   file this check created, restoring the vault to its pre-task state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `create_task_note_baseline` writes the exact schema from
      `REQ-SB-09-US-01`'s own `## Context`, keyed by
      `task_note_filename_stem`, with `customer`/`due` conditionally
      included (absent, not empty, when not applicable)
- [ ] `build_task_tags` returns `["kind/task"]` alone when `customer` is
      falsy, or `["customer/<slug>", "kind/task"]` otherwise
- [ ] `ensure_task_note_baseline_frontmatter` tops up `type`/`subject`/
      `tags`/`source`/`outlook_entry_id`/`customer` only if missing
      (never resets a present value), but UPDATES `due`/`status` to
      Outlook's current values whenever they differ, and never touches
      the body
- [ ] `upsert_frontmatter_key` inserts when the key is absent, overwrites
      when present with a different value, and is a true no-op (no write)
      when the value is already identical
- [ ] `load_task_note_index`/`lookup_task_note_stem`/`record_task_note`
      correctly persist and look up `entry_id -> stem` mappings
- [ ] No existing `vault_writer.py` function's behavior changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Deciding customer classification, or which task to create/update — that
  is `T03`.
- Wiring the per-write hook into the capture pipeline — that is `T04`.
- The live `EntryID`-stability empirical check against a real Outlook
  mailbox — carried by `T01` (isolated) and `T03` (end-to-end, `AC-06`),
  not here: this task's own primitives are vault-side only and have no
  live Outlook dependency of their own to test that specific claim
  against. Deliberate placement, not an oversight — see this task's own
  `## Context / Notes`.

---

## Context / Notes

`vault_writer.py` currently ends with `save_pending_approvals_state`;
append the new Task-note primitives directly after it. No new imports are
required — `settings`, `write_note`, `read_note`,
`insert_frontmatter_key_if_missing`, `rename_frontmatter_key`, `tag_slug`,
`_slugify`, `_WORK_ROOT`, `_STATE_DIR`, `json` all already exist in this
module.

**Why `upsert_frontmatter_key` reuses `rename_frontmatter_key` rather than
reimplementing surgical text editing:** `rename_frontmatter_key(path, key,
key, new_value=value)` — calling it with `old_key == new_key` already
does exactly "replace this key's line with a new value, leaving every
other line untouched," since that function's own contract only special-
cases the key NAME, not whether it changes. This keeps the new primitive
to a few lines rather than duplicating the surgical-frontmatter-line-
replace logic a third time in this module.

**Why the live `EntryID`-stability check is NOT in this task's own
`## Tests`:** `ADR-027`'s Consequences section names "the coder building
`T01`/`T02`" for that verification, using the story's own pre-sketched
task numbering (outlook read / vault writer primitives) as shorthand for
"the tasks that build this mechanism" — not a literal instruction that
both task files must independently repeat the same live check. This
task's own functions have no live-Outlook dependency to test that
specific claim against (they only read/write vault files); the check
itself lives in `T01` (isolated, using only `list_outlook_tasks`) and is
reinforced end-to-end in `T03` (`AC-06`, the full capture-then-rerun-
after-edit cycle exercising this task's own index primitives against real
data). See the parent story's own decomposer Notes for the full
reasoning.

---

## Implementation Log

**Built 2026-08-13.** `upsert_frontmatter_key`, `_TASKS_SUBFOLDER`,
`_TASK_NOTE_INDEX_FILE`, `task_note_filename_stem`,
`task_note_path_for_stem`, `task_note_exists_for_stem`, `build_task_tags`,
`create_task_note_baseline`, `ensure_task_note_baseline_frontmatter`,
`_task_note_index_path`, `load_task_note_index`, `lookup_task_note_stem`,
`record_task_note` appended to `vault_writer.py` exactly as specified,
additive-only after `save_pending_approvals_state` (confirmed: no
existing function's body changed).

**Manual verification — all 5 non-AC smoke checks run against the real
vault (`.venv\Scripts\python.exe`, cwd `src/backend`), throwaway notes
cleaned up afterward:**

1. `create_task_note_baseline("Verify T02 Task", "Verify Customer",
   "2026-08-20", "Not Started", "abcdef1234567890", "2026-08-13")` —
   file created under `Work/Tasks/`, name incorporates subject/capture
   date/entry-id suffix `34567890`; frontmatter exactly
   `{type: "Task", customer: "Verify Customer", subject, due, status,
   tags: ["customer/verify-customer", "kind/task"], source:
   "outlook-task", outlook_entry_id}`, empty body.
   `task_note_exists_for_stem(...)` returns `True`. PASS.
2. `create_task_note_baseline("Verify T02 No Customer", None, None, ...)`
   — frontmatter has NO `customer` key and NO `due` key at all (not
   empty strings) — confirms the "absent otherwise" schema contract.
   PASS.
3. Removed the `status` line manually, called
   `ensure_task_note_baseline_frontmatter(...)` — `status` re-inserted
   as `"In Progress"`, `"status"` in the returned changed-keys list, the
   other 7 keys + empty body byte-for-byte unchanged. PASS.
4. **Load-bearing upsert behavior (Scenario 5/6):** called
   `ensure_task_note_baseline_frontmatter(...)` again with new
   `due="2026-08-25"`/`status="Completed"` — both UPDATED (in the
   changed-keys list), unlike every other baseline key. Called a third
   time with identical arguments — changed-keys list empty, file
   byte-for-byte unchanged (true no-op). PASS.
5. `record_task_note`/`load_task_note_index`/`lookup_task_note_stem`
   round-tripped correctly; an unseen `entry_id` correctly returns
   `None`. PASS. Throwaway notes, the `Work/Tasks/` directory (now
   empty), and `task_note_index.json` all removed afterward, restoring
   the vault to its pre-task state.

No existing `vault_writer.py` function's behavior changed (confirmed by
direct diff review — only additive appends).

`gate: clear` 2026-08-13 — no MUST-FLAG trigger fired: no assumption,
no ADR change, all 5 non-AC checks passed exactly as specced.
