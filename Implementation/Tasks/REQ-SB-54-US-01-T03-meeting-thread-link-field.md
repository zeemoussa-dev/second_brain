---
id: REQ-SB-54-US-01-T03
title: Meeting note schema extension — additive, empty `thread` field reserved for REQ-SB-56
parent_story: REQ-SB-54-US-01
requirement_id: REQ-SB-54
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-54-US-01-T03 — Meeting note schema extension: reserved `thread` field

## Parent Story

- Story: [[REQ-SB-54-US-01]] — `../UserStories/REQ-SB-54-US-01-vault-knowledge-model-redesign.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-54 *Vault Knowledge Model Redesign — Threads, Linked Meetings, Living Project & Customer Documents*

---

## Objective

Add one additive, currently-empty `thread` frontmatter field to the Meeting note baseline schema (`ADR-042` point 6) — reserved for `REQ-SB-56`'s own future Meeting→Thread linking, NOT populated by this story. This story only establishes that a Meeting note carries room for the relationship in its schema (story `## Context` point 2).

---

## Starting State → End State

**Before / Inputs:**
- `_MEETING_NOTE_BASELINE_KEYS = ("type", "customer", "subject", "start", "end", "location", "organizer", "tags")` (`vault_writer.py` line 556) — no `thread` key.
- `create_meeting_note_baseline`/`ensure_meeting_note_baseline_frontmatter` (lines 648, 682) write/top-up exactly those 8 keys.

**After / Outputs:**
- `_MEETING_NOTE_BASELINE_KEYS` gains a 9th entry, `"thread"`.
- Every newly-created Meeting note's frontmatter includes `thread: ""`.
- Every already-existing Meeting note gets `thread: ""` inserted on its next top-up pass, without touching any already-present key or the body — same baseline-preservation contract the other 8 keys already have.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — `_MEETING_NOTE_BASELINE_KEYS` (line 556), `create_meeting_note_baseline` (line 648), `ensure_meeting_note_baseline_frontmatter` (line 682).

---

## Constraints

- Inherits from parent story.
- Purely additive — do not change the signature of `create_meeting_note_baseline`/`ensure_meeting_note_baseline_frontmatter` (both already take no `thread` argument; the value is always the literal empty string `""` at this stage, unconditionally, mirroring how `customer` already defaults to `""` when none was derived). No caller (`meeting_classification.py`) needs to change.
- Do NOT implement any actual Meeting→Thread matching/linking logic — `REQ-SB-56`'s own separate, later scope. This task reserves the field only.
- Never touch an already-present `thread` value on top-up (same contract every other baseline key already has) — relevant once `REQ-SB-56` starts populating it for real.

---

## Tests

**Manual verification steps:**
1. Call `create_meeting_note_baseline(subject="Test Meeting", customer=None, start="2026-08-16T10:00:00", end="2026-08-16T10:30:00", location="", organizer="test@example.com")`. Read the resulting note's frontmatter — confirm it now includes `thread: ""` alongside the existing 8 keys, and that the note's body/other frontmatter are otherwise identical in shape to a Meeting note created before this task.
2. Construct (or reuse) an EXISTING Meeting note written before this task (no `thread` key). Call `ensure_meeting_note_baseline_frontmatter(path, subject=..., customer=..., start=..., end=..., location=..., organizer=...)` with the note's own real field values — confirm the returned "keys inserted" list contains exactly `["thread"]` (the other 8 already present, untouched), confirm the file's body and every other frontmatter value are byte-for-byte unchanged.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Every Meeting note (new or topped-up) carries a `thread: ""` frontmatter field.
- [x] No existing Meeting note's already-present frontmatter or body content is altered by this change.
- [x] `meeting_classification.py` (or any other real caller) needs zero changes.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint. (n/a — no new decision/pattern/constraint, see Implementation Log)
- [x] `CHANGELOG.md` entry appended.

---

## Out of Scope

- Actually matching/populating a real Meeting↔Thread relationship (`REQ-SB-56`).
- Any change to `meeting_classification.py` or any other capture-pipeline file.

---

## Context / Notes

No locked AC in this story directly names this field (this story's own Scenarios test Thread/Customer/Project, not Meeting) — this task exists because `ADR-042` point 6 and the story's own `## Context` point 2 explicitly scope it as part of this story's data-model work ("This story only establishes that a Meeting note carries room for that relationship in its schema"). Verification above is task-level, not AC-tagged.

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-042` point 6; `Implementation/Architecture/architecture.md` → "Vault Knowledge Model Redesign..." § Evidence layer, Meeting bullet.

---

## Implementation Log

**2026-08-16 — coder, implemented and verified.**

**What changed** (`src/backend/app/data_access/vault_writer.py` only, exactly
the three named locations):
- `_MEETING_NOTE_BASELINE_KEYS` extended from 8 to 9 entries, appending
  `"thread"` as the last key.
- `create_meeting_note_baseline`: `frontmatter` dict gains `"thread": ""`,
  written unconditionally on every new Meeting note (mirrors the existing
  `customer or ""` empty-default convention already used in the same dict).
- `ensure_meeting_note_baseline_frontmatter`: `baseline_values` dict gains
  `"thread": ""`; the existing `for key in _MEETING_NOTE_BASELINE_KEYS:
  insert_frontmatter_key_if_missing(...)` loop picks it up automatically
  with zero new branching — `insert_frontmatter_key_if_missing` already
  no-ops on an already-present key, so top-up preserves any value a future
  `REQ-SB-56` writes.
- Docstrings of both functions updated to mention the 9th key; no
  signature change on either function.

**No new decision/pattern/constraint** — this task applies the codebase's
already-established "append one key to the baseline tuple + baseline
values dict" pattern (same shape `_PERSON_NOTE_BASELINE_KEYS`/
`_MEETING_NOTE_BASELINE_KEYS` already use), so `MEMORY.md` was not
updated (would be a trivial/duplicate entry per `CLAUDE.md`'s "do NOT add
empty or trivial entries" rule).

**Verification (manual mode — matches `## Tests` above; no AC-IDs are
tagged for this task per its own `## Context / Notes` — task-level
verification only):**

- **Test step 1 — PASS.** Ran `vault_writer.create_meeting_note_baseline(
  subject="Test Meeting", customer=None, start="2026-08-16T10:00:00",
  end="2026-08-16T10:30:00", location="", organizer="test@example.com")`
  against a scratch vault directory. Read the resulting file. Frontmatter:
  ```
  type: "Meeting"
  customer: ""
  subject: "Test Meeting"
  start: "2026-08-16T10:00:00"
  end: "2026-08-16T10:30:00"
  location: ""
  organizer: "test@example.com"
  tags: ["kind/meeting"]
  thread: ""
  ```
  `thread: ""` present as the 9th key; the other 8 keys/values and the
  empty-body shape are identical to a pre-task Meeting note.
- **Test step 2 — PASS.** Constructed a simulated pre-task Meeting note
  (8 baseline keys only, no `thread`, plus a `**Attendees:**` body line)
  in the scratch vault. Called `ensure_meeting_note_baseline_frontmatter`
  with the note's own real field values. Returned keys-inserted list was
  exactly `["thread"]`. Byte-compared the file before/after: every line
  except the newly-inserted `thread: ""` line (all 8 original frontmatter
  lines, the closing `---`, and the `**Attendees:**` body line) was
  byte-for-byte identical — confirmed programmatically
  (`before_lines == after_lines_minus_thread_line` → `True`).
- **AC "`meeting_classification.py` needs zero changes" — PASS by
  inspection.** Read `src/backend/app/business/meeting_classification.py`
  lines ~71-88: both real call sites (`ensure_meeting_note_baseline_
  frontmatter` at an existing note, `create_meeting_note_baseline` at a
  new one) pass the same 6 positional arguments as before this task;
  neither function's signature changed, so no edit was needed or made to
  that file (confirmed no other caller exists via a repo-wide grep for
  both function names).
- Scratch vault used for verification was created under the session
  scratchpad temp directory and deleted after verification — no vault or
  repo file outside `## Files to Modify` was touched.

**Outcome:** all locked task-level items verified PASS. No escalation, no
`REVIEW-QUEUE.md`/`ESCALATIONS.md` entry needed. Task marked `Done`.
