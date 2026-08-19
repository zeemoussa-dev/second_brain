---
id: REQ-SB-55-US-01-T05
title: Summarize-Attachment branch Job — per-attachment dated summarized sub-entry
parent_story: REQ-SB-55-US-01
requirement_id: REQ-SB-55
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-043 created) — carried from the parent story; the human reviews ADR-043 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-55-US-01-T01, REQ-SB-55-US-01-T03]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-55-US-01-T05 — `Summarize-Attachment` branch Job

## Parent Story

- Story: [[REQ-SB-55-US-01]] — `../UserStories/REQ-SB-55-US-01-email-capture-and-threading-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-55 *Email Capture & Threading Pipeline*

---

## Objective

Add `summarize_attachment(attachment, conversation_id, received) -> dict` to `email_classification.py` — this Pipeline's `Summarize-Attachment` branch Job: for ONE real attachment, saves it (reusing `vault_writer.write_attachments`, unchanged) and produces its own dated, summarized sub-entry string (reusing `compass_client.summarize_content`, unchanged — the same primitive `REQ-SB-28`'s `summarize-file` Skill already uses) — never compressing the attachment's own content into the Thread's separately-regenerated top-level `## Summary`.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.write_attachments(subfolder, note_stem, attachments) -> list[dict]` — real, already-shipped, saves real attachment bytes, returns `{"filename", "size", "saved", "relative_link"}` per attachment (or `"saved": False` for an oversized one).
- `compass_client.summarize_content(content, source_description) -> {"summary": str}` — real, already-shipped (`REQ-SB-28-US-01`), raises `CompassError` on failure.
- Today's `classify_recent_emails` calls `write_attachments` once per email (a batch call) and links each saved attachment as a plain `- [filename](link)` body line — no summarization, no dated sub-entry.

**After / Outputs:**
- `summarize_attachment(attachment: dict, conversation_id: str, received: str) -> dict` exists: saves the ONE attachment under the Thread's own subfolder/stem (`Work/Threads/attachments/<slug-of-conversation_id>/`), and — if saved and the attachment has extractable text content — calls `compass_client.summarize_content` on it, producing a dated sub-entry string of the shape `f"{received[:10]} — {filename}: {summary}"`. Returns `{"filename", "saved", "relative_link" (if saved), "dated_entry" (if summarized), "summary_error" (if summarization failed)}` — an honest, non-fabricating result on every path.
- The Pipeline calls this once per real attachment on an email (fan-out), collects the resulting `dated_entry` strings, and threads them into `Thread-Match/Merge`'s own `attachment_entries` parameter (`T07`'s own graph wiring) — this task's own function never calls `thread_match_merge` itself.

---

## Files to Modify

- `src/backend/app/business/email_classification.py` — add `summarize_attachment`, placed near `thread_match_merge`.

---

## Constraints

- Inherits from parent story: an attachment's own summarized content must never be folded into the Thread's regenerated top-level `## Summary` — this function only ever produces a SEPARATE, dated sub-entry string; it must never call `replace_body_section` or touch `## Summary` itself.
- Must compose `vault_writer.write_attachments`/`compass_client.summarize_content` DIRECTLY, unchanged — no new attachment-saving or summarization mechanism invented (mirrors `REQ-SB-44-US-01`'s own "compose `upload_storage`/`summarize_file` directly" precedent, `MEMORY.md`).
- An oversized/unsaved attachment (`write_attachments`'s own existing `"saved": False` outcome) must be honestly reported (e.g. a `dated_entry` noting it wasn't saved, or an equivalent honest signal) — never silently dropped, never fabricated as summarized.
- A `compass_client.CompassError` during summarization must be caught and honestly reported (`summary_error`) — never allowed to crash the whole pipeline run for one email over one bad attachment, mirroring `classify_recent_emails`'s own existing per-item `try/except`+continue posture applied at the attachment level.
- Must remain a plain, LangGraph-ignorant function — ordinary Python data in/out, no graph-state dict parameter, independently callable/testable.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-55-US-01-AC-02]** Against a throwaway scratch vault, call `summarize_attachment(attachment, "test-conv-attach-1", "2026-08-16T10:00:00Z")` with a real, small text-bearing attachment (a `.txt` or a real, hand-built `.pdf`, mirroring `REQ-SB-28-US-01`'s own established real-file-verification technique — no fabricated/mocked summary). Confirm the file is actually saved under the Thread's own attachments subfolder, and confirm the returned `dated_entry` genuinely reflects the attachment's own real content (not a generic placeholder) and includes the received date.
2. Call `summarize_attachment` with a deliberately oversized attachment (exceeding `write_attachments`'s own existing size cap) — confirm the honest "not saved" outcome is returned, with no `dated_entry` implying a summary that never happened.
3. Induce a real `CompassError` (e.g. a scoped, in-process monkeypatch of `compass_client.summarize_content` for this one call, reverted immediately after, mirroring this project's own established in-process-monkeypatch failure-induction technique) — confirm `summarize_attachment` returns an honest `summary_error` result rather than raising uncaught or fabricating a summary.
4. Confirm (by direct reading) `summarize_attachment` never calls `replace_body_section` or any `## Summary`-touching primitive.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-02** (Scenario 2, the summarization half) — a real attachment produces its own genuine, dated summarized sub-entry, kept structurally separate from `## Summary`.
- [x] An oversized/unsaved attachment and a real Compass failure are both reported honestly, never fabricated, never crash the caller.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Writing the sub-entry into the Thread note's own `## Attachments` region — `T03`'s `thread_match_merge` (via `T01`'s append primitive) does that, consuming this function's own output.
- Fan-out/parallel invocation across multiple attachments on one email — `T07`'s own graph-wiring job.
- Non-text-bearing attachment types (images, etc.) — mirrors `REQ-SB-28-US-01`'s own already-disclosed, still-standing scope limit (neither Compass nor `diagram-understanding` produces usable text today); an honest "not summarizable" outcome for such a type is acceptable, not a locked-AC gap.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-043` point 3; `Implementation/Architecture/architecture.md` → "Email Capture & Threading Pipeline — First Concrete Pipeline". Real precedent to mirror: `REQ-SB-28-US-01`'s own `summarize-file` Skill (the same `compass_client.summarize_content` composition, the same honest-error-envelope shape); `REQ-SB-44-US-01`'s own "compose the existing attachment-review primitives directly, never through a Skill/chat surface" precedent (`MEMORY.md`).

---

## Implementation Log

**2026-08-16, coder pass.**

Read `T03`'s real, current `thread_match_merge` (already accepts
`attachment_entries: list[str] | None`, folds each entry into `##
Attachments` via `append_body_section_line`, confirming this task runs
before/alongside `Thread-Match/Merge`, never after it) and `T04`'s real
`route_to_project`/`finalize_thread_project_routing` before writing any
code, per this task's own Context note — confirmed current file state
matches the sprint's own summary exactly, no drift.

Added `summarize_attachment(attachment, conversation_id, received) -> dict`
to `app/business/email_classification.py`, placed immediately after
`thread_match_merge` and before `route_to_project` (near, as the task
specifies). Composes exactly two existing primitives, unchanged, no new
mechanism:

- `vault_writer.write_attachments(subfolder="Work/Threads",
  note_stem=conversation_id, attachments=[attachment])` — saves the ONE
  attachment under `Work/Threads/attachments/<slug-of-conversation_id>/`,
  reusing its own existing `"saved": False` outcome for an
  oversized/unsaved attachment rather than a second size check (Outlook's
  own upstream size cap already sets `attachment["content"]` to `None`
  before this function ever sees it, confirmed by direct reading of
  `outlook_com.py::_extract_attachments`).
- Text extraction reuses `REQ-SB-28-US-01`'s own
  `upload_storage.save_upload`/`extract_text_content`/`delete_upload`
  DIRECTLY against the attachment's own real, already-in-memory bytes —
  the identical temporary-save-then-extract-then-delete technique
  `REQ-SB-44-US-01`'s own `app/business/cockpit/attachments.py` already
  established for a vault-saved email attachment (confirmed by direct
  reading of that file before writing this task's own code).
- Summarization calls `compass_client.summarize_content(extracted_text,
  f"Email attachment: {filename}")` DIRECTLY — the same primitive
  `REQ-SB-28`'s own `summarize-file` Skill (`skill_tools.summarize_file`)
  composes, per this task's own Objective wording — never through
  `skill_registry`/`invoke_skill` dispatch, keeping this function a
  plain, LangGraph-ignorant, independently callable/testable function
  with no graph-state parameter (this task's own Constraint).

Return contract exactly as specced: `{"filename", "saved",
"relative_link" (only when saved), "dated_entry" (only when a real
summary was produced), "summary_error" (when saved but no usable summary
could be produced — unsaved/oversized, non-text-bearing, or a real
`CompassError`)}`. An unsaved/oversized attachment reports via
`summary_error` (the Constraint's own "or an equivalent honest signal"
alternative to a `dated_entry`) rather than a `dated_entry` implying a
summary happened — matches Test step 2's own literal wording ("no
`dated_entry` implying a summary that never happened") exactly. Never
raises for ordinary control flow — `ValueError` (non-text-bearing/no
extractable content) and `compass_client.CompassError` (a real Compass
failure) are both caught locally and folded into `summary_error`, never
propagated, mirroring `classify_recent_emails`' own per-item
try/except+continue posture applied at the attachment level. Never calls
`replace_body_section`, `thread_match_merge`, or any other `##
Summary`-touching primitive — confirmed by direct reading of the
function's own full body (grep-isolated, zero matches).

**Manual verification (scratch vault, `VAULT_PATH` env-overridden to a
`tempfile.mkdtemp()` directory, real configured vault never touched, real
Compass Provider — script kept in this session's own scratchpad, not
committed):**

- **Step 1 (`REQ-SB-55-US-01-AC-02`):** called `summarize_attachment`
  with a real, small `.txt` attachment (a genuine, hand-written
  quarterly-consumption paragraph — "4,820 units", "week 6... onboarding
  cohort", "tiered pricing plan") against `conversation_id=
  "test-conv-attach-1"`, `received="2026-08-16T10:00:00Z"`. Observed: the
  file is genuinely saved on disk at `Work/Threads/attachments/
  test-conv-attach-1/consumption-report.txt` with byte-identical content;
  the returned `dated_entry` is `"2026-08-16 — consumption-report.txt:
  Acme Corp quarterly consumption: 4,820 units. Notable spike in week 6
  due to new onboarding cohort ramp-up. Recommends reviewing the tiered
  pricing plan before next renewal."` — a genuine, real-Compass-produced
  reflection of the attachment's own actual content (not a generic
  placeholder — it names the exact real figures/details from the source
  text), correctly prefixed with the received date (`2026-08-16`). PASS.
- **Step 2:** called `summarize_attachment` with a deliberately oversized
  attachment (`content=None`, `size=25 MB` — the real shape Outlook's own
  upstream size cap already produces for an oversized attachment).
  Observed: `{"saved": False, "summary_error": "Attachment not saved --
  exceeds the size cap."}` — no `dated_entry` key present at all, no
  fabricated summary. PASS.
- **Step 3:** induced a real `CompassError` via a scoped, in-process
  monkeypatch of `compass_client.summarize_content` for this one call
  only (reverted immediately in a `finally` block, mirroring this
  project's own established in-process-monkeypatch failure-induction
  technique). Observed: the attachment was still genuinely saved
  (`"saved": True`, real `relative_link`), no `dated_entry` present, and
  `summary_error` honestly reported the induced failure text — never
  raised uncaught, never fabricated a summary. Confirmed the monkeypatch
  was truly reverted immediately after: a following real call with a
  fresh real attachment produced a genuine `dated_entry` again (real
  Compass call working normally). PASS.
- **Step 4:** confirmed by direct reading of `summarize_attachment`'s own
  full function body (isolated via a multiline grep bounded to the next
  `def`) that it contains zero calls to `replace_body_section` or any
  other `## Summary`-touching primitive, and never calls
  `thread_match_merge` itself. PASS.

`ast.parse()` of the full `email_classification.py` file after this edit
succeeded with no syntax error. No file outside `## Files to Modify` was
edited — `vault_writer.py`, `compass_client.py`, and
`upload_storage.py` were only read, composed unchanged. No locked AC was
weakened, omitted, or deleted.

No `ESCALATIONS.md`/`REVIEW-QUEUE.md` entry from this task's own pass —
nothing here contradicts `ADR-043`, the PRD, or a `MEMORY.md` constraint;
the story's own already-flagged `gate: flagged` (trigger-3, `ADR-043`)
already carries this task into the existing human-review pass.
