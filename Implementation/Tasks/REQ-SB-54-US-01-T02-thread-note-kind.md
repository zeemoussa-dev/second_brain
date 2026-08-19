---
id: REQ-SB-54-US-01-T02
title: Thread note kind — deterministic path, baseline create/top-up, Summary/Transcript body shape
parent_story: REQ-SB-54-US-01
requirement_id: REQ-SB-54
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-54-US-01-T01]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-54-US-01-T02 — Thread note kind

## Parent Story

- Story: [[REQ-SB-54-US-01]] — `../UserStories/REQ-SB-54-US-01-vault-knowledge-model-redesign.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-54 *Vault Knowledge Model Redesign — Threads, Linked Meetings, Living Project & Customer Documents*

---

## Objective

Add the Thread note kind to `app/data_access/vault_writer.py`: a deterministic path resolver keyed on Outlook `conversation_id` alone (`ADR-042` point 5), baseline creation/top-up, and the `## Summary` (fully regenerated, via `T01`'s `replace_body_section`) + `## Transcript` (append-only, growing) body shape — mirroring `hub_note_path`/`meeting_note_path`'s existing "deterministic path from a stable key, no separate lookup index" precedent.

---

## Starting State → End State

**Before / Inputs:**
- No Thread note kind exists. `conversation_id` is already captured by Outlook COM (`app/data_access/outlook_com.py::list_recent_mail`) but only used for a loose `find_related_note_stems()` lookup (`conversation_index.json`), never to merge notes into one Thread — that module and file stay untouched by this task (`ADR-042` Alternatives: still owned by `email_classification.py` until `REQ-SB-55` replaces it).
- `T01`'s `replace_body_section` exists and is the mechanism this task's own Summary regeneration uses.
- `hub_note_path`/`meeting_note_path` (lines 341, 593) are the real precedent for a deterministic-path-from-a-stable-key note kind, and `write_note` (line 160) for baseline creation.

**After / Outputs:**
- `thread_note_path(conversation_id)`, `thread_note_exists(conversation_id)`, `create_thread_note_baseline(conversation_id, tags=None)`, `ensure_thread_note_baseline_frontmatter(path, conversation_id, tags=None)` exist in `vault_writer.py`.
- `Work/Threads/<slug-of-conversation-id>.md` is the deterministic path. `Work/Threads/` is a new, dynamically-discovered `kind` folder — `list_known_kinds()` needs no code change to find it.
- A newly-created Thread note's body is exactly `## Summary` (empty) + `## Transcript` (empty) — ready for a future caller (`REQ-SB-55`) to regenerate/append via `T01`'s `replace_body_section` and the existing `append_person_note_update_line`.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add `_THREADS_SUBFOLDER`, `_THREAD_NOTE_BASELINE_KEYS`, `thread_note_path`, `thread_note_exists`, `create_thread_note_baseline`, `ensure_thread_note_baseline_frontmatter`, placed alongside the Meeting-note-kind block (near line 555) as the next note-kind family.

---

## Constraints

- Inherits from parent story: Thread's `## Summary` is regenerated via `T01`'s `replace_body_section` ONLY — never any other write mechanism, never incrementally patched.
- `## Transcript` growth reuses the EXISTING generic append primitive (`append_person_note_update_line`) — do not add a new append primitive (`ADR-042` point 1). Renaming it to reflect its now-multi-purpose role is optional/coder's judgement call, not required by this task.
- `thread_note_path` must be a pure, deterministic function of `conversation_id` alone (no separate lookup index) — mirrors `hub_note_path`/`meeting_note_path` exactly.
- Do NOT modify `conversation_index.json`/`find_related_note_stems`/`record_conversation_note` — still owned by `email_classification.py` until `REQ-SB-55` (`ADR-042` Alternatives).
- Do NOT modify `email_classification.py` or any capture-pipeline file — this story defines the data shape only (`REQ-SB-55` builds the pipeline that calls these primitives).
- Tag accumulation/union logic across updates (architecture.md: "Tags accumulate, unioned, never pruned") is explicitly OUT of this task's scope — the caller that updates an existing Thread note's tags on a later message is `REQ-SB-55`'s own job; this task only needs `create_thread_note_baseline`/`ensure_thread_note_baseline_frontmatter` to accept an initial `tags` list.
- `Work/Threads/` needs no `list_known_kinds()` change — confirm this live (folder is dynamically discovered by directory name already).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-54-US-01-AC-01] Pick a throwaway `conversation_id` (e.g. `"test-conv-001"`). Call `thread_note_exists("test-conv-001")` — expect `False`. Call `create_thread_note_baseline("test-conv-001", tags=["kind/thread"])`. Confirm a note now exists at `thread_note_path("test-conv-001")` (`Work/Threads/test-conv-001.md`), with frontmatter `type: "Thread"`, `conversation_id: "test-conv-001"`, `tags: ["kind/thread"]`, and a body containing an (empty) `## Summary` section followed by an (empty) `## Transcript` section — this is the "first message creates one Thread note" half of the scenario.
2. [REQ-SB-54-US-01-AC-01] Simulating "a later message in the same conversation": call `thread_note_path("test-conv-001")` again — confirm it resolves to the exact SAME path as step 1 (no new file, no second note). Call `replace_body_section(path, "## Summary", "Regenerated summary covering 2 messages.")` (`T01`) and separately `append_person_note_update_line(path, "2026-08-16: second message body text")`. Read the note back — confirm `## Summary` now shows ONLY the new regenerated text (no trace of the empty placeholder), confirm `## Transcript` now contains the appended line (growing, not replaced), confirm the frontmatter block is byte-for-byte unchanged from step 1.
3. Call `ensure_thread_note_baseline_frontmatter(path, "test-conv-001", tags=["kind/thread"])` on the SAME already-existing note — confirm it inserts no new keys (all four baseline keys already present) and touches neither the body nor any already-set frontmatter value (idempotent no-op).
4. Confirm live that `list_known_kinds()` now includes `"Threads"` with zero code changes, once the test note above exists.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `thread_note_path(conversation_id)` is a pure, deterministic function of `conversation_id` alone.
- [x] `create_thread_note_baseline` creates exactly one note per `conversation_id`, with `## Summary`/`## Transcript` sections present.
- [x] A second creation attempt for the same `conversation_id` never produces a second file — the caller (future `REQ-SB-55`) checks `thread_note_exists` first, same contract as every other note kind in this codebase.
- [x] `## Summary` regeneration goes ONLY through `replace_body_section`; `## Transcript` growth goes ONLY through the existing generic append primitive.
- [x] `list_known_kinds()` discovers `Threads` with zero code change.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint. (No new entry — see Implementation Log; this task is a direct mirror of an already-documented pattern, nothing new to preserve.)
- [x] `CHANGELOG.md` entry appended.

---

## Out of Scope

- Actually wiring these primitives into a real capture pipeline (`REQ-SB-55`).
- Tag union/accumulation logic across updates (`REQ-SB-55`'s job).
- Meeting→Thread linking (`T03` only reserves the field; `REQ-SB-56` populates it).

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-042` point 5; `Implementation/Architecture/architecture.md` → "Vault Knowledge Model Redesign..." § Evidence layer, Thread bullet. Real precedent to mirror: `meeting_note_path`/`create_meeting_note_baseline`/`ensure_meeting_note_baseline_frontmatter` (lines 593-713).

Illustrative shape (reconcile against the real current file — line numbers may have shifted since `T01` lands):

```python
_THREADS_SUBFOLDER = f"{_WORK_ROOT}/Threads"
_THREAD_NOTE_BASELINE_KEYS = ("type", "conversation_id", "tags")

def thread_note_path(conversation_id: str):
    return settings.vault_path / _THREADS_SUBFOLDER / f"{_slugify(conversation_id)}.md"

def thread_note_exists(conversation_id: str) -> bool:
    return thread_note_path(conversation_id).exists()

def create_thread_note_baseline(conversation_id: str, tags: list[str] | None = None) -> str:
    return write_note(
        subfolder=_THREADS_SUBFOLDER,
        filename_stem=conversation_id,
        frontmatter={"type": "Thread", "conversation_id": conversation_id, "tags": tags or []},
        body="## Summary\n\n## Transcript\n",
    )

def ensure_thread_note_baseline_frontmatter(path, conversation_id: str, tags: list[str] | None = None) -> list[str]:
    baseline_values = {"type": "Thread", "conversation_id": conversation_id, "tags": tags or []}
    inserted: list[str] = []
    for key in _THREAD_NOTE_BASELINE_KEYS:
        if insert_frontmatter_key_if_missing(path, key, baseline_values[key]):
            inserted.append(key)
    return inserted
```

Callers regenerate `## Summary` and grow `## Transcript` directly via `replace_body_section(path, "## Summary", ...)` / `append_person_note_update_line(path, ...)` — no wrapper function needed, per `ADR-042`'s "one shared mechanism" principle.

---

## Implementation Log

**Coder pass (2026-08-16).**

- Added the Thread note-kind block to `src/backend/app/data_access/
  vault_writer.py`, placed directly after `upsert_attendee_links` (end of
  the Meeting-note-kind block) and before `_PARTNERS_SUBFOLDER` — the next
  note-kind family in file order, matching the task's own "alongside the
  Meeting-note-kind block, as the next note-kind family" placement
  instruction (real location shifted slightly from the task's own
  illustrative "near line 555" estimate, since that line is
  `_MEETINGS_SUBFOLDER` itself, i.e. the START of the Meeting block — the
  actual insertion point used is the END of that same block, ~line 805,
  which is the correct "next note-kind family" position; purely a
  location clarification, no scope change). Added `_THREADS_SUBFOLDER`,
  `_THREAD_NOTE_BASELINE_KEYS`, `thread_note_path`, `thread_note_exists`,
  `create_thread_note_baseline`, `ensure_thread_note_baseline_frontmatter`
  — signatures and behavior match the task's own illustrative shape
  exactly (pure deterministic path via `_slugify(conversation_id)`,
  `write_note`-based unconditional baseline creation, `insert_frontmatter_
  key_if_missing`-based surgical top-up), mirroring `meeting_note_path`/
  `create_meeting_note_baseline`/`ensure_meeting_note_baseline_
  frontmatter`'s own established contract. No new append/regeneration
  primitive added — callers use `T01`'s `replace_body_section` for
  `## Summary` and the existing `append_person_note_update_line` for
  `## Transcript` directly, per the task's own Constraints and `ADR-042`'s
  "one shared mechanism" principle. Confirmed by direct reading that
  `conversation_index.json`/`find_related_note_stems`/
  `record_conversation_note`/`email_classification.py` are byte-for-byte
  untouched, and that `list_known_kinds()` (dynamic `Work/*` directory
  scan) needed zero code change to discover a new `Work/Threads/` folder.
  `T01`'s `replace_body_section`/`_BODY_SECTION_HEADER_PATTERN` and `T03`'s
  `_MEETING_NOTE_BASELINE_KEYS`/`create_meeting_note_baseline`/
  `ensure_meeting_note_baseline_frontmatter` changes (both already
  committed to this same file before this task started) are unmodified —
  confirmed by direct reading before and after this edit.

**Verification (manual mode — automated test tooling still pending, per
this task's own `Tests` section).** Ran a throwaway script via the real
backend venv (`src/backend/.venv/Scripts/python.exe`), importing the real
`app.data_access.vault_writer` module unmodified, `settings.vault_path`
pointed at a `tempfile.mkdtemp()` scratch directory (not the real vault).

- **[REQ-SB-54-US-01-AC-01], Test step 1:** `thread_note_exists(
  "test-conv-001")` returned `False` before creation. Called
  `create_thread_note_baseline("test-conv-001", tags=["kind/thread"])`.
  Observed: a note now exists at `thread_note_path("test-conv-001")`,
  which resolved to exactly `Work/Threads/test-conv-001.md` under the
  scratch vault; `read_note()` showed frontmatter `{'type': 'Thread',
  'conversation_id': 'test-conv-001', 'tags': ['kind/thread']}` and a body
  containing `## Summary` immediately followed by an empty region then
  `## Transcript` (also empty) — `## Summary` ordered before
  `## Transcript`. **PASS.**
- **[REQ-SB-54-US-01-AC-01], Test step 2:** Called `thread_note_path(
  "test-conv-001")` again — resolved to the exact same `Path` object value
  as step 1 (no new file). Captured the frontmatter block's raw bytes
  before mutating. Called `replace_body_section(path, "## Summary",
  "Regenerated summary covering 2 messages.")` (returned `True`) and
  separately `append_person_note_update_line(path, "2026-08-16: second
  message body text")`. Read the note back: `## Summary` now shows ONLY
  `Regenerated summary covering 2 messages.` (exactly one occurrence, no
  trace of the empty placeholder), `## Transcript` now contains the
  appended line after its own header (growing, not replaced — file
  content `'\n## Summary\n\nRegenerated summary covering 2
  messages.\n\n## Transcript\n2026-08-16: second message body text\n'`),
  and a before/after byte comparison of the frontmatter block confirmed
  it is byte-for-byte unchanged. **PASS.**
- **Test step 3 (idempotent top-up):** Captured the full file text before
  calling `ensure_thread_note_baseline_frontmatter(path, "test-conv-001",
  tags=["kind/thread"])` on the same already-existing, already-complete
  note. Observed: `inserted == []` (no keys inserted — all three baseline
  keys already present) and a full-file before/after byte comparison
  confirmed the file (body AND frontmatter) is completely unchanged.
  **PASS.**
- **Test step 4 (`list_known_kinds()` discovery):** Called
  `list_known_kinds()` against the same scratch vault after the note
  above was created — result included `"Threads"`, with zero
  `vault_writer.py` code change needed beyond this task's own additions
  (`list_known_kinds()` itself, line ~189, is unmodified — it already
  dynamically scans `Work/*` subdirectory names). **PASS.**
- Regression check: `ast.parse()` against the full `vault_writer.py`
  confirmed no syntax error was introduced; direct reading confirmed
  every pre-existing function/constant in the file (including `T01`'s
  `replace_body_section`/`_BODY_SECTION_HEADER_PATTERN` and `T03`'s
  Meeting-note changes) is unmodified.

**Scope-internal judgement call, not an escalation:** the task's own AC
checklist item "`MEMORY.md` updated if this task produced a new decision /
pattern / constraint" is conditional. This task applies an
already-established pattern (`hub_note_path`/`meeting_note_path`'s
deterministic-path-from-a-stable-key precedent, `ADR-042` point 5, and
`T01`'s own already-`MEMORY.md`-recorded `replace_body_section`
convention) without introducing anything new to preserve — no `MEMORY.md`
entry was added, per CLAUDE.md's "do NOT add empty or trivial entries"
instruction.

No `ESCALATIONS.md`/`REVIEW-QUEUE.md` entries — no out-of-scope event, no
ambiguous requirement, all locked-AC-tagged manual steps verified with an
observed `PASS` outcome. `CHANGELOG.md` updated per project convention
(see its own `[Unreleased]` entry dated 2026-08-16 for this task).
