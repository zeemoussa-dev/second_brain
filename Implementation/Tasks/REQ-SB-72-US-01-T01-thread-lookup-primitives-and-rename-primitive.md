---
id: REQ-SB-72-US-01-T01
title: Thread lookup reverts to a frontmatter scan + new whole-directory rename primitive
parent_story: REQ-SB-72-US-01
requirement_id: REQ-SB-72
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-72-US-01-T01 — Thread lookup reverts to a frontmatter scan + new whole-directory rename primitive

## Parent Story

- Story: [[REQ-SB-72-US-01]] — `../UserStories/REQ-SB-72-US-01-librarian-section-first-housekeeping-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-72 *The Librarian Section — First Housekeeping Pipeline*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian Section — First Housekeeping Pipeline" (`ADR-049`), section "Thread lookup — frontmatter-based, again" + "Thread rename — a real, atomic whole-directory move"

---

## Objective

Land the two foundational `app/data_access/vault_writer.py` primitives every other task in this story composes: a new frontmatter-scan `resolve_thread_directory`, a signature-preserving retarget of `resolve_thread_note_path`/`raw_message_note_path` onto it, and a new `rename_thread_directory` whole-directory-move primitive. No business-layer caller is touched in this task (see `T02`).

---

## Starting State → End State

**Before / Inputs:**
- `resolve_thread_note_path(conversation_id)` is a pure deterministic existence check against `thread_directory_paths(conversation_id)["concept"]` (`ADR-048` Decision 7) — silently wrong the moment a Thread's own directory has been renamed.
- `raw_message_note_path(conversation_id, message_id, received)` composes `thread_directory_paths(conversation_id)["messages"]` directly, unconditionally.
- No whole-directory rename primitive exists — only the single-file `rename_thread_note` (`ADR-046`), which this task does NOT touch.

**After / Outputs:**
- `resolve_thread_directory(conversation_id) -> Path | None` — new, frontmatter-scan primitive, composing `list_thread_notes()` (never a second, independent Thread-enumeration mechanism), matching `frontmatter.get("conversation_id") == conversation_id`. Returns the Thread's own DIRECTORY (`path.parent`), or `None`.
- `resolve_thread_note_path(conversation_id)` — PUBLIC SIGNATURE UNCHANGED, retargeted to a thin wrapper: `directory / f"{directory.name}.md"` if `resolve_thread_directory` finds a match, else `None`. Every existing real caller (`_link_to_thread_by_conversation_id`, `_trigger_project_resynthesis`, `synthesize_thread`'s create-vs-update check at line 503, `meeting_classification.py` lines 85/225) keeps working with ZERO call-site change.
- `raw_message_note_path(conversation_id, message_id, received)` — retargeted to resolve-first, deterministic-fallback: composes `resolve_thread_directory` first; if found, the note path is under THAT directory's own `messages/`; only when the Thread genuinely does not exist yet does it fall back to the deterministic `thread_directory_paths(conversation_id)["messages"]` — mirrors `resolve_meeting_note_path`'s own established two-tier shape.
- `rename_thread_directory(old_directory: Path, new_directory: Path) -> Path` — new primitive: no-op if `old_directory == new_directory`; raises `FileExistsError` if `new_directory` already exists (never silently overwrites); otherwise `old_directory.rename(new_directory)` moves the whole tree (concept file, `messages/`, any `files/`) in one atomic filesystem op, then renames the concept file inside from `<old-slug>.md` to `<new-slug>.md`, preserving the `<slug>/<slug>.md` invariant `list_thread_notes()` depends on. Returns the new concept file path.
- `thread_directory_paths(conversation_id)` itself is UNCHANGED — still the deterministic path a brand-new Thread is first created at, and still valid for bulk/retrofit internal use.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add `resolve_thread_directory`; retarget `resolve_thread_note_path`; retarget `raw_message_note_path`; add `rename_thread_directory`.

---

## Constraints

- Inherits from parent story.
- `resolve_thread_note_path`'s PUBLIC signature (`Path | None`) must not change — zero call-site edits anywhere else in this task.
- `thread_directory_paths`, `list_thread_notes`, `create_thread_note_baseline`, and the OLD `rename_thread_note`/`thread_note_path_for`/`thread_note_filename_stem` primitives (`ADR-046`) stay completely untouched — still `thread_match_merge`'s own internal mechanism (see `ESC-050`, out of this story's scope).
- `resolve_thread_directory` composes `list_thread_notes()` — never a second, independent Thread-enumeration glob.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`) — this task stays entirely inside `data_access`.

---

## Tests

<!-- No locked AC is directly verified by this foundational task — its primitives
are consumed and AC-verified by T02 (AC-02) and T03 (AC-01). This task's own
Tests block is a component-level smoke check only, per this codebase's own
established "building-block task, AC verified downstream" precedent
(REQ-SB-63-US-01-T01/T02, REQ-SB-50). -->

**Manual verification steps:**
1. Direct Python-shell check (real vault, `VAULT_PATH`-configured): pick one real, already-captured `conversation_id` from `Work/Threads/`. Confirm `vault_writer.resolve_thread_directory(conversation_id)` returns that Thread's real directory, and `vault_writer.resolve_thread_note_path(conversation_id)` returns the identical `Path` it returned before this change (byte-for-byte, confirming the signature-preserving retarget).
2. In the same shell: pick a disposable/test Thread directory (never a real production Thread), call `vault_writer.rename_thread_directory(old, new)` and confirm the whole tree (`messages/`, any `files/`) moved intact and the concept file was renamed to `<new-slug>.md`; then call it a second time with `old == new` and confirm it is a genuine no-op; then call it again pointing at an already-existing `new_directory` and confirm it raises `FileExistsError` without touching either directory's contents.
3. Confirm `raw_message_note_path` for an ALREADY-RENAMED disposable Thread (from step 2) resolves under the renamed directory's own `messages/`, and for a genuinely brand-new `conversation_id` (no directory yet) falls back to the deterministic `thread_directory_paths(...)["messages"]` path.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `resolve_thread_directory` added, composing `list_thread_notes()` only
- [x] `resolve_thread_note_path` retargeted, zero call-site changes anywhere else
- [x] `raw_message_note_path` retargeted to resolve-first/deterministic-fallback
- [x] `rename_thread_directory` added with refuse-to-overwrite + no-op + atomic-move behavior
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any business-layer caller migration (`raw_message_capture.py`, `email_classification.synthesize_thread`, `meeting_classification.py`) — `T02`.
- The Rename Job itself (computing a Thread's `<date> <subject-without-Re->` stem and invoking `rename_thread_directory`) — `T03`.
- `thread_match_merge`/`email_capture_pipeline.py` — explicitly out of this story's `## Files to Modify` (see `ESC-050`).

---

## Context / Notes

`ADR-049` Decision 1's own reasoning for why a plain frontmatter scan (not a hybrid deterministic-then-scan fallback) is correct here: a hybrid's deterministic tier would miss every renamed Thread, forever — not a one-time transition artifact — so a single-tier scan is simpler and equally cheap at real steady-state volume (~10 emails/hour, ~127 real Thread directories). Full reasoning: `ADR-049` Decision 1 + Alternatives 1-3.

---

## Implementation Log

**2026-08-18, coder pass.** Implemented all four primitives in
`src/backend/app/data_access/vault_writer.py`: `resolve_thread_directory`
(new, frontmatter-scan over `list_thread_notes()`), `resolve_thread_note_path`
(retargeted, public signature unchanged, now a thin wrapper over
`resolve_thread_directory`), `raw_message_note_path` (retargeted to
resolve-first/deterministic-fallback), `rename_thread_directory` (new,
atomic whole-directory move, refuse-to-overwrite, no-op on `old==new`).

No locked AC is directly verified by this foundational task (per its own
Tests block) — component-level smoke checks performed directly against the
real vault (`VAULT_PATH`-configured, real backend running on `--reload`):

1. Picked a real `conversation_id` (`004771620DBD604FAE3D2CE2A3404608`) from
   the real vault. `resolve_thread_directory` returned the exact same
   directory `list_thread_notes()` already reports; `resolve_thread_note_path`
   returned the identical `Path` `thread_directory_paths(...)["concept"]`
   would have returned pre-change (byte-for-byte, confirming the
   signature-preserving retarget). PASS.
2. Built a disposable `TEST-LIBRARIAN-VERIFY-001` Thread directory (concept
   file + `messages/` + `files/`, never a real production Thread) under the
   real `Work/Threads/`. `rename_thread_directory` moved the whole tree
   intact — confirmed via SHA-256 hash comparison of every file's own bytes
   before/after, identical. A second call with `old == new` was a genuine
   no-op (no filesystem mutation). A third call against an already-existing
   `new_directory` raised `FileExistsError` without touching either
   directory's contents. All disposable fixtures cleaned up after
   verification (no residue left in the real vault). PASS.
3. `raw_message_note_path` for the already-renamed disposable Thread
   resolved under the renamed directory's own `messages/`; for a genuinely
   brand-new `conversation_id` (no directory yet), it fell back to the
   deterministic `thread_directory_paths(...)["messages"]` path exactly as
   specified. PASS.

**Assumption logged (scope-internal judgement call, not a MUST-FLAG
trigger):** none — this task's own mechanism was fully specified by
`ADR-049` Decision 1/2; no gap-filling was required.

`gate: clear 2026-08-18` — no MUST-FLAG trigger fired (no new dependency,
no shared-interface change beyond what `ADR-049` already authorized, no
ADR deviation, no unanticipated file, primitives match the ADR's own
illustrative text exactly).
