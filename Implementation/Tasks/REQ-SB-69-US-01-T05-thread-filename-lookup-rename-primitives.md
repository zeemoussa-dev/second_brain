---
id: REQ-SB-69-US-01-T05
title: vault_writer.py — thread_name baseline key, human-readable collision-safe Thread filename derivation, resolve_thread_note_path lookup, rename_thread_note
parent_story: REQ-SB-69-US-01
requirement_id: REQ-SB-69
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-69-US-01-T05 — Thread filename/lookup/rename primitives

## Parent Story

- Story: [[REQ-SB-69-US-01]] — `../UserStories/REQ-SB-69-US-01-decoupled-email-pull-and-human-readable-thread-notes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-69 *Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes*

---

## Objective

Build the new `vault_writer.py` primitives `ADR-046` Decisions 6/7
require: a human-readable, collision-safe Thread filename derivation
(mirroring `meeting_note_filename_stem`'s own shape exactly), a
frontmatter-scan lookup replacing `thread_note_path`'s now-broken
"deterministic from `conversation_id` alone" contract, and a rename
primitive — all as standalone, independently-testable functions, not yet
wired into `thread_match_merge` (that wiring is `T06`).

---

## Starting State → End State

**Before / Inputs:**
- `thread_note_path(conversation_id)` → `Work/Threads/<slug-of-
  conversation_id>.md`, a pure function of `conversation_id` alone
  (`ADR-042` point 5). `thread_note_exists(conversation_id)` checks that
  same path. `create_thread_note_baseline(conversation_id, tags=None)`
  writes baseline frontmatter `{"type": "Thread", "conversation_id":
  ..., "tags": ...}` with body `"## Summary\n\n## Transcript\n"`.
  `_THREAD_NOTE_BASELINE_KEYS = ("type", "conversation_id", "tags")`.
- `meeting_note_filename_stem(subject, start)` (lines 844-868) is the
  exact, already-shipped precedent to mirror: `f"{subject}-{date}-
  {suffix}"` where `date = start[:10]` and `suffix =
  hashlib.sha256(f"{subject}|{start}".encode("utf-8")).hexdigest()[:8]`.
- `list_thread_notes() -> list[Path]` (line 1156) already enumerates
  every real `Work/Threads/*.md` note (composes
  `list_notes_in_kind_folder("Threads")`) — built for `REQ-SB-56`'s
  fallback linker, directly reusable here.
- `move_note_and_attachments(note_path, target_dir)` (line 512) is the
  existing precedent for a real file-rename-with-refusal-to-overwrite
  primitive, but moves into a DIFFERENT directory — Thread's own rename
  stays within `Work/Threads/`, so a simpler `Path.rename` (or an
  adaptation of that primitive's own refuse-to-overwrite discipline) is
  what's actually needed here, not that function itself.

**After / Outputs:**
- `_THREAD_NOTE_BASELINE_KEYS` gains a 4th key, `"thread_name"`.
  `create_thread_note_baseline(conversation_id, thread_name: str,
  tags: list[str] | None = None) -> str` gains a required `thread_name`
  parameter, writing it into the baseline frontmatter dict alongside the
  existing three keys. `ensure_thread_note_baseline_frontmatter` gains
  the matching `thread_name` top-up parameter/baseline-value entry,
  mirroring its own existing three-key shape.
- New `thread_note_filename_stem(thread_name: str, date: str,
  conversation_id: str) -> str` — `f"{thread_name}-{date}-{suffix}"`
  where `suffix = hashlib.sha256(conversation_id.encode("utf-8")).
  hexdigest()[:8]` — deliberately hashing `conversation_id` ALONE (never
  `f"{thread_name}|{date}"`, unlike Meeting's own scheme), per `ADR-046`
  Decision 6: this keeps the disambiguator stable across renames even
  though the filename's own `date` component changes on every later
  message (Scenario 7).
- New `thread_note_path_for(thread_name: str, date: str,
  conversation_id: str)` — resolves the vault-absolute path this stem
  would live at (`Work/Threads/<slug-of-stem>.md`), mirroring
  `meeting_note_path`'s own "resolves without checking existence" shape,
  composing `thread_note_filename_stem` above.
- New `resolve_thread_note_path(conversation_id: str) -> Path | None` —
  scans every real path in `list_thread_notes()`, reads each one's own
  `conversation_id` frontmatter field (`read_note`), returns the first
  path whose `conversation_id` matches, or `None` if no match is found
  (a genuinely new conversation — the create-vs-update signal
  `thread_match_merge`, `T06`, needs). NEVER creates or writes anything —
  read-only.
- New `rename_thread_note(old_path, new_path) -> None` — physically
  renames the file in place (`old_path.rename(new_path)` after
  `new_path.parent.mkdir(parents=True, exist_ok=True)`), refusing to
  silently overwrite an existing different file at `new_path` (raise
  `FileExistsError` if `new_path` already exists and is not `old_path`
  itself — mirrors `move_note_and_attachments`'s own refuse-to-overwrite
  discipline). No-op (returns without renaming) if `old_path == new_path`
  — a Thread whose filename didn't actually change on this call.
- `thread_note_path`/`thread_note_exists` (the old deterministic-from-
  `conversation_id`-alone functions) are LEFT IN PLACE, unmodified,
  UNDELETED — `ADR-046`'s own Consequences explicitly defer their
  removal to a future, separately-scoped cleanup task, since any other
  real caller must be confirmed first (mirrors this project's own
  "confirming and retiring dead code is a task-scoping decision, not
  decided at the ADR level" precedent).

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  - Extend `_THREAD_NOTE_BASELINE_KEYS` to `("type", "conversation_id",
    "tags", "thread_name")`.
  - `create_thread_note_baseline`: add `thread_name: str` parameter,
    write it into the frontmatter dict.
  - `ensure_thread_note_baseline_frontmatter`: add a matching
    `thread_name: str` parameter and baseline-value entry.
  - Add `thread_note_filename_stem`, `thread_note_path_for`,
    `resolve_thread_note_path`, `rename_thread_note` as new module-level
    functions, placed near the existing Thread primitives (around line
    1083-1170).

---

## Constraints

- Inherits from parent story.
- **`thread_note_filename_stem`'s own hash suffix is derived from
  `conversation_id` ALONE, never combined with `thread_name`/`date`** —
  this is the one load-bearing correctness property that makes rename-
  on-update (`T06`, Scenario 7) stable; get this wrong and every rename
  would also change the hash suffix, defeating the whole point.
- **`resolve_thread_note_path` never creates, writes, or renames
  anything** — a pure read/scan. Composes `list_thread_notes()` (never a
  new, second `Work/Threads/*.md` glob mechanism) and `read_note`
  directly.
- **No new persisted index file** (e.g. a `thread_index.json`) — `ADR-046`
  explicitly rejects this (its own Alternatives Considered); the lookup
  is a live frontmatter scan, every call, deliberately.
- **`thread_note_path`/`thread_note_exists` are left completely
  unmodified and undeleted** — do not remove or edit them in this task.
- **`rename_thread_note` refuses to silently overwrite a different
  existing file at the destination** — mirrors this codebase's own
  standing filename-collision-safety precedent
  (`move_note_and_attachments`).
- This task does NOT wire any of these new primitives into
  `thread_match_merge`/`route_to_project` — that is `T06`'s own scope.
  This task only builds and unit-verifies the primitives themselves.

---

## Tests

<!-- No locked AC maps directly to this task alone (the primitives aren't
wired into the real create/update flow yet) — T06's own Tests carry
AC-05/06/07 once wiring lands. This task's own Tests are plain, non-AC
sanity checks proving each primitive is correct in isolation. -->

**Manual verification steps** (direct Python-shell calls against a real,
disposable subfolder of the real configured vault):

1. Call `thread_note_filename_stem("Project Kickoff", "2026-08-16",
   "01D26A7530444A23803A002210620160")`. Confirm the result matches the
   pattern `<slug-of-"Project Kickoff">-2026-08-16-<8 hex chars>` and
   confirm calling it AGAIN with the SAME `conversation_id` but a
   DIFFERENT `date` (e.g. `"2026-08-20"`) produces the SAME 8-hex-char
   suffix (conversation_id-only hashing, stable across date changes).
2. Confirm calling `thread_note_filename_stem` with the SAME
   `thread_name`+`date` but a DIFFERENT `conversation_id` produces a
   DIFFERENT suffix (disambiguation actually works — never a same-input-
   same-output collision across two distinct real conversations).
3. Write two real Thread notes directly (via `write_note`, bypassing
   `create_thread_note_baseline` if simpler) with distinct
   `conversation_id` frontmatter values. Call `resolve_thread_note_path`
   for each — confirm each resolves to its own correct path. Call it a
   third time with a `conversation_id` that matches neither — confirm it
   returns `None`.
4. Call `rename_thread_note(old_path, new_path)` where `old_path` is one
   of the two real notes from step 3 and `new_path` is a genuinely new
   filename in the same folder. Confirm the file now exists at
   `new_path` with its original content byte-for-byte preserved, and no
   longer exists at `old_path`. Call `rename_thread_note(new_path,
   new_path)` (same path twice) — confirm it is a safe no-op (no error,
   file still there). Call `rename_thread_note` targeting the OTHER
   real note's own existing path (a genuine collision) — confirm it
   raises `FileExistsError` rather than silently overwriting.
5. Confirm `create_thread_note_baseline`'s new `thread_name` parameter
   writes correctly (a fresh note's frontmatter includes `thread_name`)
   and confirm `_THREAD_NOTE_BASELINE_KEYS`/`ensure_thread_note_
   baseline_frontmatter`'s own top-up behavior tops up `thread_name`
   only when genuinely missing (mirrors the existing three-key
   top-up contract).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `thread_note_filename_stem` hashes `conversation_id` alone, stable
      across a `date` change, distinct across a `conversation_id` change
- [x] `resolve_thread_note_path` correctly resolves an existing Thread's
      real path and returns `None` for a genuinely new conversation
- [x] `rename_thread_note` preserves content, is a safe no-op for an
      unchanged path, and refuses to overwrite a genuine collision
- [x] `create_thread_note_baseline`/`ensure_thread_note_baseline_
      frontmatter` correctly carry the new `thread_name` key
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — not updated: this task is a direct, mechanical implementation of
      `ADR-046` Decisions 6/7 (already fully documented there and in
      `architecture.md`), producing no new decision/pattern/constraint of
      its own beyond what those artefacts already record.
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring these primitives into `thread_match_merge`'s own create-vs-
  update branch, and the stale Pending-Approval-payload fix — `T06`.
- Human-readable dates, `## Related` wikilinks — `T07`, `T08`.
- Deleting/retiring `thread_note_path`/`thread_note_exists` — a future,
  separately-scoped cleanup task, per `ADR-046`'s own Consequences.

---

## Context / Notes

`ADR-046` Decisions 6/7 (`Implementation/Architecture/ADR.md`) are the
full architectural reasoning, including the rejected persisted-index-file
alternative. This task can be built and fully verified independently of
`T01`-`T04` — it touches none of the same files and has no real
dependency on the staging/pull-decoupling half of this story.

---

## Implementation Log

**What was changed** (`src/backend/app/data_access/vault_writer.py` only,
exactly per `## Files to Modify`):

- `_THREAD_NOTE_BASELINE_KEYS` extended to `("type", "conversation_id",
  "tags", "thread_name")`.
- `create_thread_note_baseline(conversation_id, thread_name, tags=None)`
  — added the required `thread_name` parameter (positional, after
  `conversation_id`, before the existing `tags` keyword-defaulted
  parameter, matching the task's own End-State signature exactly), writes
  it into the baseline frontmatter dict.
- `ensure_thread_note_baseline_frontmatter(path, conversation_id,
  thread_name, tags=None)` — added the matching `thread_name` parameter
  and baseline-value entry, same top-up-only-if-missing contract as the
  existing three keys.
- New `thread_note_filename_stem(thread_name, date, conversation_id)`,
  `thread_note_path_for(thread_name, date, conversation_id)`,
  `resolve_thread_note_path(conversation_id) -> Path | None`,
  `rename_thread_note(old_path, new_path) -> None` — placed immediately
  after the existing `list_thread_notes()`, per the task's own placement
  note. `thread_note_path`/`thread_note_exists` left completely
  unmodified and undeleted.

**Scope-internal judgement calls (for human spot-check, not
escalations):**

1. **Parameter placement:** `thread_name` was placed as the 2nd
   positional parameter of `create_thread_note_baseline`/`ensure_thread_
   note_baseline_frontmatter` (before the existing `tags` keyword), since
   the task's own `## Starting State → End State` text spells out the
   exact signature `create_thread_note_baseline(conversation_id: str,
   thread_name: str, tags: list[str] | None = None)` — followed literally,
   no ambiguity to resolve.
2. **`rename_thread_note` never moves a sibling attachments folder**
   (unlike `move_note_and_attachments`, which it's told to mirror only for
   its refuse-to-overwrite discipline, not its full behavior) — confirmed
   by reading `email_classification.py`/`ADR-042`/`ADR-043` that Thread
   notes record Attachments inline in the note body (`## Attachments`
   section, `REQ-SB-55`), never in a sibling `attachments/<note_slug>/`
   folder the way Meeting/Email notes do — so there is nothing sibling to
   carry over on a Thread rename. Documented in the function's own
   docstring.
3. **A real, disclosed, EXPECTED transient consequence, not a defect or
   scope violation:** `create_thread_note_baseline`'s new required
   `thread_name` parameter means its one real existing caller —
   `email_classification.py::thread_match_merge`, line ~216,
   `vault_writer.create_thread_note_baseline(conversation_id,
   tags=message_tags)` (a file explicitly OUT of this task's own `##
   Files to Modify`, and explicitly `T06`'s own scope to wire) — will now
   raise `TypeError: missing 1 required positional argument: 'thread_name'`
   if a brand-new Thread is captured by a real, live pipeline run BEFORE
   `T06` lands and updates that call site. This is precisely why the
   decomposer recorded `T06 depends_on T05` (see the story's own Decomposer
   Pass task table) — `T05` and `T06` are sequenced back-to-back within
   the same sprint specifically so this window is real but short, not
   silently unaddressed. Not fixed here (would be editing a file outside
   this task's own scope, forbidden) and not escalated (the decomposer
   already anticipated and sequenced around exactly this consequence) —
   named here explicitly per this project's own "log scope-internal
   judgement calls for human spot-check" convention
   (`Implementation/Learnings.md`, `SPRINT-037`/`SPRINT-021` precedent).

**Verification — manual mode, run live against the real, configured
vault (`VAULT_PATH = C:\myWorx\Moussa MD\Moussa Brain`, confirmed 2 real
pre-existing Thread notes: `01D26A7530444A23803A002210620160.md`,
`0C41DC9411479C4BAC82EBDDDCA753E7.md`), via a disposable Python script
(`verify_t05.py`) that wrote/renamed/deleted only its own
`t05verify-*`/`T05VERIFY-CONV-*`-prefixed disposable notes, cleaned up
every one of them afterward, and confirmed both real pre-existing notes
were left untouched throughout. All 5 of the task's own manual Test steps
— 19 individual assertions total — passed:**

- **Test step 1** (`thread_note_filename_stem` stable across a `date`
  change, same `conversation_id`): `thread_note_filename_stem("Project
  Kickoff", "2026-08-16", "T05VERIFY-CONV-AAAA")` →
  `"Project Kickoff-2026-08-16-c00db819"` — matches the
  `<name>-<date>-<8hex>` pattern. Re-called with `date="2026-08-20"` →
  `"Project Kickoff-2026-08-20-c00db819"` — the 8-hex suffix (`c00db819`)
  is byte-identical across the date change. **PASS.**
- **Test step 2** (distinct `conversation_id` → distinct suffix, same
  `thread_name`+`date`): `thread_note_filename_stem("Project Kickoff",
  "2026-08-16", "T05VERIFY-CONV-BBBB")` →
  `"Project Kickoff-2026-08-16-37424786"` — suffix `37424786` differs from
  step 1's `c00db819`. **PASS.**
- **Test step 3** (`resolve_thread_note_path`): wrote two real disposable
  Thread notes directly via `write_note` with distinct `conversation_id`
  values (`T05VERIFY-CONV-AAAA`/`-BBBB`) into the real `Work/Threads/`.
  `resolve_thread_note_path(conv_a)`/`(conv_b)` each resolved to their own
  correct real path. `resolve_thread_note_path("T05VERIFY-CONV-DOES-NOT-EXIST")`
  returned `None`. **PASS (3/3 assertions).**
- **Test step 4** (`rename_thread_note`): renamed the disposable Alpha
  note to a new real filename in the same folder — new path existed with
  content preserved byte-for-byte, old path no longer existed. Re-called
  `rename_thread_note(new_path, new_path)` (same path twice) — safe no-op,
  file still present, content unchanged. Called `rename_thread_note`
  targeting the disposable Bravo note's own real existing path (a genuine
  collision) — raised `FileExistsError`, and Bravo's own content was
  confirmed still present/untouched afterward (not silently overwritten).
  **PASS (5/5 assertions).**
- **Test step 5** (`create_thread_note_baseline`/`ensure_thread_note_
  baseline_frontmatter` `thread_name` carriage): created a fresh
  disposable Thread note via `create_thread_note_baseline(conv_c,
  thread_name="T05VERIFY Charlie", tags=["kind/thread"])` — real written
  frontmatter included `thread_name: "T05VERIFY Charlie"`. Separately wrote
  a disposable Thread note missing `thread_name` (mirroring a
  pre-`REQ-SB-69` legacy note) and confirmed `ensure_thread_note_baseline_
  frontmatter` inserted ONLY `["thread_name"]` (not `type`/`conversation_id`/
  `tags`, all already present) and the value landed correctly. Re-ran it a
  second time on the now-complete note with a deliberately different
  `thread_name` argument (`"SHOULD NOT OVERWRITE"`) — inserted `[]` (no
  keys), and the real, already-present `thread_name` value
  (`"T05VERIFY Delta Topup"`) was confirmed unchanged — proving the
  top-up-only-if-missing contract holds for the new key exactly as it
  does for the existing three. **PASS (5/5 assertions).**

**Cleanup confirmed:** every disposable note this verification created
was deleted at the end of the script; a post-cleanup real directory
listing of `Work/Threads/` shows only the same 2 pre-existing real notes
that were there before this task's verification began — zero residue.

**Real code compiles/imports cleanly:** `python -c "import
app.data_access.vault_writer"` (project `.venv`) succeeded with no error
before live verification began.

**No locked AC owned by this task** (per its own `## Tests` block —
`T06`'s own Tests carry `AC-05`/`AC-06`/`AC-07` once the wiring lands);
all 4 of this task's own non-AC Acceptance Criteria items and both DoD
checklist items are satisfied, per the above.

**MUST-FLAG check:** no trigger fired. No material assumption filled a
genuine gap (the exact function names/signatures were spelled out
verbatim in the task's own `## Starting State → End State`); no ADR
created or changed by this coder pass; no `ESCALATIONS.md` entry written
(the transient-breakage consequence above is an already-anticipated,
already-sequenced-around consequence of the decomposer's own `depends_on`
graph, not a new out-of-scope event); this task owns no locked AC to fail
verification on; no new dependency, shared-interface change beyond what
`ADR-046`/this task's own spec already authorized, or unanticipated file
was needed. `gate: clear`.

gate: clear 2026-08-17 — no MUST-FLAG trigger fired (ADR-046 already
Accepted and unchanged by this pass; every function built matches the
task's own literal, decomposer-authored signatures; all verification
performed live against the real vault with a clean before/after state).
