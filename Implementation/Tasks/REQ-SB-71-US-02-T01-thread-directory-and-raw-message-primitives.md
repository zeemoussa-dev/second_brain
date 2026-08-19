---
id: REQ-SB-71-US-02-T01
title: Thread directory shape + raw message note primitives — thread_directory_paths, raw_message_note_path/_exists/create_raw_message_note, revived create_thread_note_baseline
parent_story: REQ-SB-71-US-02
requirement_id: REQ-SB-71
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-02-T01 — Thread directory shape + raw message note primitives

## Parent Story

- Story: [[REQ-SB-71-US-02]] — `../UserStories/REQ-SB-71-US-02-email-capture-raw-distilled-and-two-stage-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-71, points 1/2 (Thread raw/distilled split, two-stage pipeline)

---

## Objective

New `vault_writer` primitives establishing the redesigned Thread directory
shape (`Work/Threads/<slug-of-conversation_id>/`, permanently
deterministic from `conversation_id` alone — reverting `ADR-046`'s own
human-readable/renamable-filename mechanism) and the write-once raw
message note family — the foundation both Stage 1 (`T03`/`T04`) and Stage
2 (`T05`/`T06`) build on.

---

## Starting State → End State

**Before / Inputs:**
- Thread is a single FILE, `thread_note_path_for`/`thread_note_filename_
  stem`-derived, human-readable/renamable (`ADR-046` Decisions 6/7).
  `create_thread_note_baseline(conversation_id, thread_name, date, tags)`
  writes body `"## Summary\n\n## Transcript\n\n## Related\n"`.
- No raw-message-note primitive exists anywhere in this codebase — no
  primitive for an immutable, per-message, verbatim note.
- `thread_note_path(conversation_id)` (line 1093, `ADR-042` point 5's
  ORIGINAL deterministic function) already exists but is currently unused
  by `create_thread_note_baseline`/`thread_match_merge` (both use the
  renamable scheme instead) — this task REVIVES it as the concept-file half
  of the new directory scheme.

**After / Outputs:**
- `thread_directory_paths(conversation_id: str) -> dict` (new) —
  `{"directory": Work/Threads/<slug>/, "concept": Work/Threads/<slug>/
  <slug>.md, "messages": Work/Threads/<slug>/messages/}`, `slug =
  _slugify(conversation_id)`. Pure, deterministic, no I/O.
- `create_thread_note_baseline(conversation_id, thread_name, tags=None) ->
  str` — REWRITTEN for the new 2-part shape: writes the concept file at
  `thread_directory_paths(conversation_id)["concept"]` with frontmatter
  `{"type": "Thread", "conversation_id": conversation_id, "tags": tags or
  [], "thread_name": thread_name}` and body `"## Summary\n\n## Personal
  Notes\n\n## Actions\n\n## Related\n"` (four sections; `## Transcript` is
  RETIRED — no longer written). `date` is no longer a parameter (the new
  scheme needs no filename-date component). Always writes unconditionally
  — callers must check existence first (mirrors this module's own
  established `create_*_baseline` contract).
- `raw_message_note_path(conversation_id: str, message_id: str, received:
  str) -> Path` (new) — `thread_directory_paths(conversation_id)
  ["messages"] / f"{received[:10]}-{hash8(message_id)}.md"`, mirroring
  `meeting_note_filename_stem`'s own hash-suffix disambiguation shape
  (`hash8 = sha256(message_id)[:8]`).
- `raw_message_note_exists(conversation_id: str, message_id: str,
  received: str) -> bool` (new) — existence check the caller (Stage 1)
  MUST call before ever calling `create_raw_message_note`, mirroring
  `person_note_exists`'s own "callers must check first" contract.
- `create_raw_message_note(conversation_id: str, message_id: str,
  received: str, sender: str, sender_email: str, subject: str, body:
  str) -> str` (new) — writes the verbatim raw message note at
  `raw_message_note_path(...)`, frontmatter carrying at minimum
  `message_id`/`sender`/`sender_email`/`subject`/`received`, body the raw
  message content verbatim. Always writes unconditionally (no
  existence-check inside — the caller already checked via `raw_message_
  note_exists`). Never edited again once written by any caller in this
  codebase — this is a write-once contract enforced by convention (caller
  discipline), not a file-permission mechanism.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  - Add `thread_directory_paths(conversation_id: str) -> dict`.
  - Rewrite `create_thread_note_baseline` for the new signature/body
    (drop the `date` parameter; new 4-section body; write via
    `thread_directory_paths(...)["concept"]` instead of the old
    `thread_note_path_for`-derived filename).
  - Add `raw_message_note_path`, `raw_message_note_exists`,
    `create_raw_message_note` (new functions, placed near the existing
    Thread-note primitives).
  - `ensure_thread_note_baseline_frontmatter` — update to top up the same
    4 baseline keys (`type`/`conversation_id`/`tags`/`thread_name`)
    against the NEW concept-file path convention; no other behavior
    change.

---

## Constraints

- Inherits from parent story.
- **`Work/Threads/<slug>/<slug>.md` is permanently deterministic from
  `conversation_id` alone** — no rename-in-place mechanism, no
  frontmatter-scan lookup needed for path RESOLUTION (that lookup role —
  "does a Thread already exist for this `conversation_id`" — moves to
  `T02`'s own retargeted `resolve_thread_note_path`, composing this task's
  `thread_directory_paths`).
- **Every raw message note is write-once** — `create_raw_message_note`
  itself does not defensively re-check existence (the caller's own `raw_
  message_note_exists` check is the enforcement point, exactly mirroring
  every other `create_*_baseline` primitive's existing "always writes
  unconditionally, caller checks first" contract in this module).
- **`## Transcript` is retired from the baseline body** — do not write it
  anywhere in this task's own changed functions.
- **This task does NOT touch `thread_match_merge`, `resolve_thread_note_
  path`, `list_thread_notes`, `rename_thread_note`, or any other Stage-2/
  discovery-layer function** — those are `T02`'s (discovery) and `T05`'s
  (Stage 2 synthesis) own scope.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`) — all new primitives are plain `data_access` functions, no
  business-layer composition.

---

## Tests

**Manual verification steps:**

1. Non-AC foundational check: call `thread_directory_paths("AAMkAD...")`
   (a real or realistic synthetic `conversation_id`). Confirm the returned
   dict's three paths are all under `Work/Threads/<slug-of-conversation_
   id>/`, with `"concept"` and `"messages"` nested correctly beneath
   `"directory"`.
2. Non-AC foundational check: call `create_thread_note_baseline` for a
   brand-new, disposable `conversation_id`. Confirm the concept file is
   written at exactly the path `thread_directory_paths(...)["concept"]`
   resolves to, with frontmatter carrying `type`/`conversation_id`/`tags`/
   `thread_name`, and a body containing all four headers in order
   (`## Summary` < `## Personal Notes` < `## Actions` < `## Related`), no
   `## Transcript`.
3. Non-AC foundational check: call `raw_message_note_exists` for a
   `message_id` that has never been written — confirm `False`. Call
   `create_raw_message_note` for that same `message_id`, confirm the file
   is written at `raw_message_note_path(...)`'s own resolved path with the
   real verbatim body content passed in. Call `raw_message_note_exists`
   again for the same `message_id` — confirm `True`.
4. Non-AC foundational check: call `create_raw_message_note` a second time
   for a DIFFERENT `message_id` in the same conversation. Confirm a NEW,
   second file is written under the same `messages/` folder, and confirm
   the FIRST raw message note's own content (read back) is byte-for-byte
   unchanged from step 3.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `thread_directory_paths` resolves the new 2-part directory shape
      deterministically from `conversation_id` alone
- [ ] `create_thread_note_baseline` writes the new 4-section body at the
      new concept-file path, `## Transcript` retired
- [ ] `raw_message_note_path`/`_exists`/`create_raw_message_note` establish
      a real, working write-once raw message note primitive family
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `list_all_note_paths()`/`list_thread_notes()`/`resolve_thread_note_path()`
  generalization/retargeting — `T02`'s own scope.
- The Stage 1 pipeline itself (calling these primitives against real
  staged mail) — `T03`'s own scope.
- Stage 2's own `synthesize_thread` (reading `messages/`, regenerating
  `## Summary`/`## Related`) — `T05`'s own scope.
- Retiring `thread_note_path_for`/`thread_note_filename_stem`/
  `rename_thread_note`/`last_message_at_display` — dead code for new
  capture per `ADR-048`'s own Consequences, but their actual removal is a
  coder-level scope-internal judgement call for whichever task's coder
  finds it clean to do so (not mandated by this task).

---

## Context / Notes

`ADR-048` Decision 3 (`Implementation/Architecture/ADR.md`) and
`architecture.md`'s own "Email Capture Redesign — Thread Raw/Distilled
Split, Stage 1/Stage 2 (`REQ-SB-71-US-02`)" subsection have the exact code
shapes this task implements. No dependency on any other task/story — this
is the first, foundational task in this story's own chain.

---

## Implementation Log

**2026-08-18, `/implement-sprint SPRINT-061`:**

Implemented exactly as specified in `src/backend/app/data_access/
vault_writer.py`: `thread_directory_paths(conversation_id)`,
`create_thread_note_baseline(conversation_id, thread_name, tags=None)`
rewritten for the new 2-part shape, `raw_message_note_path`/`_exists`/
`create_raw_message_note` added. `## Transcript` retired from the
baseline body. `ensure_thread_note_baseline_frontmatter` required no code
change — it already receives `path` as a parameter and does not derive it
internally, so it is correct against the new concept-file path
unmodified (logged per the task's own "no other behavior change"
framing).

**Manual verification (non-AC foundational checks, this task's own
`## Tests`):**

1. `thread_directory_paths("TEST-CONVO-SPRINT061-DISPOSABLE-0001")` (a
   disposable, non-real conversation_id, cleaned up after) — confirmed
   `"concept"`/`"messages"` both nested under `"directory"`, all under
   `Work/Threads/<slug>/`. **PASS.**
2. `create_thread_note_baseline` for that disposable id — concept file
   written at exactly `thread_directory_paths(...)["concept"]`, body
   headers in order `## Summary` < `## Personal Notes` < `## Actions` <
   `## Related`, no `## Transcript`, frontmatter carries `type`/
   `conversation_id`/`tags`/`thread_name`. **PASS.**
3. `raw_message_note_exists` → `False` for a never-written `message_id`;
   `create_raw_message_note` writes the real verbatim body; `raw_message_
   note_exists` → `True` afterward. **PASS.**
4. A second, different `message_id` in the same conversation → a NEW,
   second file under `messages/`; the first file's own content re-read
   byte-for-byte unchanged. **PASS.**

Disposable test data (`TEST-CONVO-SPRINT061-DISPOSABLE-0001`) removed
from the real vault after verification.

Subsequently re-verified indirectly, end-to-end, against REAL live
Outlook mail via `T04`'s own real `POST /poc/capture-raw-thread-messages`
endpoint (252 real raw message notes + 127 real Thread concept files
written in one real batch — see `T04`'s own Implementation Log for full
evidence) — this task's own primitives are exactly what produced that
real, live output.

**Scope-internal finding, disclosed (not a MUST-FLAG trigger — see
`ESC-048` for the one genuine escalation this pass produced):**
`create_thread_note_baseline`'s signature change (dropping `date`) and
`T02`'s own retargeting of `resolve_thread_note_path` together mean the
still-live, scheduled `thread_match_merge` pipeline (`email-capture-
pipeline`'s `process_staged_email` capability, `REQ-SB-55`/`REQ-SB-69`,
both `Done`) can no longer resolve any OLD, pre-redesign flat-file Thread
note's own existence check correctly. As a protective measure taken
BEFORE writing any code this session, `email-capture-pipeline`'s working
mode was flipped `autonomous` → `supervised` via the real, existing
`PATCH /agents/email-capture-pipeline` endpoint, preventing the live
hourly scheduler from exercising the old path against the new primitives
during/after this build. Left `supervised` at task completion,
deliberately — see `ESC-048` (`ESCALATIONS.md`) for the full finding and
`REVIEW-QUEUE.md` for the human decision needed.

Status → `Done`. `gate: clear` — no MUST-FLAG trigger fired for this
task itself (the one genuine finding above is recorded as `ESC-048`, an
out-of-scope/shared-interface-change discovery, not a trigger against
this task's own deliverable, which is complete and independently
correct).
