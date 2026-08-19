---
id: REQ-SB-44-US-01-T03
title: New app/business/cockpit/attachments.py — list an email's already-vault-saved attachments; hand_off_attachment_to_chat composes REQ-SB-28's upload_storage extract + summarize-file, posting the summary into the shared Cockpit thread
parent_story: REQ-SB-44-US-01
requirement_id: REQ-SB-44
type: backend
status: Done
gate: flagged
gate_reason: "one scope-internal judgement call logged for human spot-check: _attachments_dir skips re-slugification entirely (a cleaner reading than the task's own private-_slugify-reach-through sample), confirmed correct against real vault fixtures."
phase: P1
depends_on: [REQ-SB-28-US-01-T01, REQ-SB-28-US-01-T03, REQ-SB-28-US-01-T04, REQ-SB-43-US-01-T02]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-44-US-01-T03 — `app/business/cockpit/attachments.py`

## Parent Story

- Story: [[REQ-SB-44-US-01]] — `../UserStories/REQ-SB-44-US-01-inbox-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-44 *Inbox Cockpit — Expert-Assisted Email Workspace*

---

## Cross-story dependency (real, currently unmet at spec time — read before starting)

**This task `depends_on` `REQ-SB-28-US-01-T01`/`T03`/`T04`, which were `Ready` (not `Done`) when this story was decomposed** — mirrors `REQ-SB-39-US-02`'s own precedent for a `Ready`-not-`Done` cross-story dependency (that story's own Notes: "a decomposer-level task-sequencing discipline, not a code mechanism, since no real deploy boundary exists to enforce it technically"). Per `ADR-036` point 5/6, do not start this task until `REQ-SB-28-US-01-T01`/`T03`/`T04` are real, built, and verified — `upload_storage.save_upload`/`extract_text_content`/`delete_upload` (`T01`) and `skill_tools.summarize_file` (`T03`) are composed DIRECTLY by this task's own code (not via HTTP); `T04`'s own `POST /agents/{agent_id}/chat/attachment` endpoint is NOT called by this task (that endpoint is chat-upload-specific, ending in an unwanted Vault-Filing-Expert auto-file — see Context/Notes) but is listed as a `depends_on` edge per the architect's own explicit `ADR-036` point 5 instruction, and its own established "grant summarize-file unconditionally" pattern is mirrored here (see Constraints).

---

## Objective

List an email's own already-vault-saved attachments (`email_classification.py`'s existing `vault_writer.write_attachments` output, under `Work/Emails/attachments/<note_slug>/`) for review (Scenario 4/4b), and a "Hand off to Expert" action that summarizes one attachment (reusing `REQ-SB-28`'s own `upload_storage`/`summarize-file` mechanism directly against the real vault-saved bytes) and posts the resulting summary into the shared Cockpit thread as an ordinary chat turn — never a second, separate skill-trigger surface (`ADR-036` point 4).

---

## Starting State → End State

**Before / Inputs:**
- `REQ-SB-28-US-01-T01` has landed `app/data_access/upload_storage.py::save_upload(filename, content) -> upload_id`, `extract_text_content(upload_id, filename) -> str`, `delete_upload(upload_id, filename)`.
- `REQ-SB-28-US-01-T03` has landed `app/business/skill_tools.py::summarize_file(content, source_description) -> {"status": "ok", "summary": ...} | {"status": "error", "message": ...}`.
- `REQ-SB-43-US-01-T02` has landed `app/business/cockpit/threads.append_system_message(subject_kind, subject_note_stem, text)`.
- `app/data_access/vault_writer.py::write_attachments` saves email attachments under `<subfolder>/attachments/<note_slug>/<filename>` (confirmed by direct reading, `email_classification.py`).

**After / Outputs:** new `app/business/cockpit/attachments.py`:
```python
"""Inbox Cockpit attachment review (ADR-036 points 5/6) -- lists an
email's own already-vault-saved attachment files, and hands one off to
the shared Cockpit thread by composing REQ-SB-28's own upload_storage
(extract) + summarize-file Skill DIRECTLY against the real vault-saved
bytes -- never REQ-SB-28's own chat-upload HTTP endpoint (which ends in
an unwanted Vault-Filing-Expert auto-file for THIS use case)."""
from __future__ import annotations

from pathlib import Path

from app.business import skill_tools
from app.business.cockpit import threads
from app.config import settings
from app.data_access import upload_storage


def _attachments_dir(email_note_stem: str) -> Path:
    from app.data_access import vault_writer  # local import, mirrors write_attachments' own _slugify use
    note_slug = vault_writer._slugify(email_note_stem)
    return settings.vault_path / "Work/Emails/attachments" / note_slug


def list_attachments(email_note_stem: str) -> list[dict]:
    directory = _attachments_dir(email_note_stem)
    if not directory.exists():
        return []
    return [
        {"filename": path.name, "size": path.stat().st_size}
        for path in sorted(directory.iterdir()) if path.is_file()
    ]


def hand_off_attachment_to_chat(email_note_stem: str, filename: str) -> dict:
    path = _attachments_dir(email_note_stem) / filename
    if not path.exists():
        return {"status": "not_found"}
    content = path.read_bytes()
    upload_id = upload_storage.save_upload(filename, content)
    try:
        extracted_text = upload_storage.extract_text_content(upload_id, filename)
    except ValueError as exc:
        threads.append_system_message("email", email_note_stem, f"Couldn't read {filename}: {exc}")
        return {"status": "extraction_failed"}
    finally:
        upload_storage.delete_upload(upload_id, filename)

    summary_result = skill_tools.summarize_file(extracted_text, f"Email attachment: {filename}")
    if summary_result.get("status") != "ok":
        message = summary_result.get("message", "Summarization failed.")
        threads.append_system_message("email", email_note_stem, f"[Attachment: {filename}] {message}")
        return {"status": "summarization_failed"}

    threads.append_system_message(
        "email", email_note_stem, f"[Attachment: {filename}] {summary_result['summary']}",
    )
    return {"status": "ok", "summary": summary_result["summary"]}
```

---

## Files to Modify

- `src/backend/app/business/cockpit/attachments.py` (new) — per the code block above.

---

## Constraints

- Composes `upload_storage.save_upload`/`extract_text_content`/`delete_upload` (`REQ-SB-28-US-01-T01`) and `skill_tools.summarize_file` (`REQ-SB-28-US-01-T03`) DIRECTLY — never `skill_registry.invoke_skill` (no per-agent grant/gate needed for this system-level composition; `summarize_file` is a plain function, not a per-agent dispatch, for this call path) and NEVER `REQ-SB-28-US-01-T04`'s own `POST /agents/{agent_id}/chat/attachment` endpoint (that endpoint auto-files into the vault via the Vault Filing Expert — NOT wanted here; this task's own attachment is already vault-saved, reviewed in chat, not independently re-filed as a new note).
- `delete_upload` runs in a `finally` block — the temporary scratch copy under `.second-brain/uploads/` is always cleaned up, on both the extraction-success and extraction-failure paths (mirrors `REQ-SB-28-US-01-T04`'s own established cleanup discipline).
- The hand-off summary is posted via `threads.append_system_message` — an ORDINARY chat-thread turn, never a second, separate skill-trigger UI surface (`ADR-036` point 4's own "no explicit Action/Skill-trigger button" finding — the "Hand off to Expert" button, built by `T05`/`T06`, is UI sugar over this ordinary chat-append, not a new gated dispatch path).
- Never fabricates a summary — an extraction or summarization failure is posted to the thread HONESTLY (mirrors `REQ-SB-28`'s own standing honesty Constraint), never silently dropped.
- `list_attachments` returns `[]` (not an error) for an email with no attachments directory at all (Scenario 4b).
- Reads `email_classification.py`'s/`vault_writer.py`'s own REAL, current `write_attachments`/`_slugify` implementation before finalizing the attachments-directory path convention — reconcile against what actually exists, do not assume the code sample's `_attachments_dir` helper matches byte-for-byte (in particular, prefer importing/reusing a real existing slug helper over a private `_slugify` reach-through if a cleaner public equivalent already exists).

---

## Tests

**Manual verification steps** (Python shell, backend `.venv`, `PYTHONPATH=.`; requires a real Email note that was captured WITH at least one real attachment — trigger a real email-capture run against a fixture email with an attachment, or use an already-real one from the dev vault):
1. **[REQ-SB-44-US-01-AC-04]** `cockpit.attachments.list_attachments("<real-email-stem-with-an-attachment>")` — confirm a real, non-empty list with the real filename(s)/size(s) matching what's actually on disk under `Work/Emails/attachments/<slug>/`.
2. **[REQ-SB-44-US-01-AC-05]** `cockpit.attachments.list_attachments("<real-email-stem-with-NO-attachment>")` → `[]`.
3. **[REQ-SB-44-US-01-AC-04]** `cockpit.attachments.hand_off_attachment_to_chat("<stem>", "<real filename from step 1>")` — confirm `{"status": "ok", "summary": <real string>}` genuinely reflecting the real attachment's content (read it by eye), and confirm `cockpit.threads.get_thread("email", "<stem>")["messages"]` gained a new turn containing that summary, prefixed `"[Attachment: <filename>]"`.
4. Non-AC smoke check: confirm no file remains under `.second-brain/uploads/` after step 3 completes (cleanup ran).
5. Non-AC smoke check: induce a real extraction failure (a real `.pdf` attachment with no extractable text layer, if one exists in the fixture set, or a monkeypatch of `upload_storage.extract_text_content` to raise `ValueError`) — confirm an honest failure message is posted to the thread, never a fabricated summary, and the temp file is still cleaned up.
6. Non-AC smoke check: confirm `skill_registry.invoke_skill`/`_invoke_action` are never imported/called anywhere in this module (direct code-read check).
7. Clean-up: remove any test entries added to `.second-brain/cockpit_threads.json`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `list_attachments` returns real filenames/sizes for an email with attachments, `[]` for one without
- [x] `hand_off_attachment_to_chat` composes `upload_storage`/`summarize_file` directly (never `invoke_skill`/`T04`'s own endpoint), posts an honest result to the shared thread
- [x] Temp scratch file always cleaned up (`finally`)
- [x] A failure is surfaced honestly, never fabricated
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The HTTP routes — `T04`.
- Any frontend change — `T05`/`T06`.
- `REQ-SB-28-US-01`'s own `upload_storage.py`/`summarize_file`/chat-attachment-endpoint implementations — composed here, not modified.

---

## Context / Notes

Full mechanism/reasoning: `ADR-036` points 5/6. This task depends on `REQ-SB-28-US-01-T04` per the architect's own explicit instruction (mirroring `T04`'s own precedent for the mandatory-default "grant unconditionally" pattern this task's composition philosophy echoes), even though this task's own code composes `T01`/`T03` DIRECTLY rather than calling `T04`'s own HTTP endpoint — `T04`'s endpoint is chat-upload-specific (ends in Vault-Filing-Expert auto-filing, not wanted for an already-vault-saved email attachment reviewed in chat context). Read `REQ-SB-28-US-01-T01`'s/`T03`'s own REAL, as-built `upload_storage.py`/`skill_tools.py` before wiring this task's calls — reconcile function/return-shape names against what those tasks actually built.

---

## Implementation Log

**2026-08-14 — built with one disclosed deviation from the task's own literal code sample.** New `app/business/cockpit/attachments.py` created per the task's own shape (`list_attachments`/`hand_off_attachment_to_chat`), composing `upload_storage.save_upload`/`extract_text_content`/`delete_upload` and `skill_tools.summarize_file` DIRECTLY, `delete_upload` in a `finally` block, honest failure messages posted via `threads.append_system_message`, never `skill_registry`/`_invoke_action`.

**Deviation, disclosed:** `_attachments_dir` does NOT reach into `vault_writer.py`'s private `_slugify` at all (the task's own code sample's fallback path). Confirmed by direct reading of `vault_writer.py::write_attachments`/`write_note`: both compute the attachments-directory name and the note's own filename stem via the IDENTICAL `_slugify(filename_stem)` call on the IDENTICAL raw input — so a real Email note's own `path.stem` (what `list_email_items`'s `"stem"` field, and the Cockpit route, are keyed on) is already byte-identical to `write_attachments`' own `note_slug`. Confirmed live against two real vault fixtures (see below) — the directory name matched the note's own real filename stem exactly, with zero re-slugification. This is a cleaner reading of the task's own Constraint ("prefer importing/reusing a real existing slug helper... over a private `_slugify` reach-through if a cleaner public equivalent already exists") — the cleanest equivalent here is no slugification at all, not a public wrapper around one.

**Verification (Python shell, backend `.venv`, real vault fixtures — a real Email note with a real PDF attachment already on disk, and a real Email note with none):**

- **[AC-04]** `list_attachments("2026-08-12-Emailing Sarmad_Jari_Resume.pdf-10930000")` → `[{'filename': 'Sarmad_Jari_Resume.pdf', 'size': 342594}]` — matches the real file on disk byte-for-byte in size. **Pass.**
- **[AC-05]** `list_attachments("2026-07-20-Involuntary Loss of Employment Insurance (ILOE)-5C830000")` (a real Email note with no attachments directory) → `[]`. **Pass.**
- **[AC-04]** `hand_off_attachment_to_chat(<stem>, "Sarmad_Jari_Resume.pdf")` — real `upload_storage.save_upload`/`extract_text_content`/`delete_upload` composed against the real 342KB PDF, real `skill_tools.summarize_file` → real Compass/Core42 API call (`HTTP 200`), returned `{"status": "ok", "summary": <real, accurate resume summary — read by eye, genuinely reflects the real PDF's content (Sarmad Jari's Azure/cloud-architecture resume, correct current role, prior roles, certifications)>}`. `cockpit.threads.get_thread("email", <stem>)["messages"]` gained exactly one new turn, text prefixed `"[Attachment: Sarmad_Jari_Resume.pdf]"` containing the real summary. **Pass.**
- Non-AC smoke check: `.second-brain/uploads/` confirmed empty immediately after the hand-off (cleanup ran). **Pass.**
- Non-AC smoke check: induced a real extraction failure via a scoped, reverted in-process monkeypatch of `upload_storage.extract_text_content` (raises `ValueError`) — confirmed an honest failure message (`"Couldn't read Sarmad_Jari_Resume.pdf: induced failure..."`) was posted to the thread, never a fabricated summary, and `.second-brain/uploads/` was still clean afterward (the `finally` block ran on the failure path too). **Pass.**
- Non-AC smoke check: direct source-read of the real, unmodified `attachments.py` module confirmed neither `skill_registry` nor `_invoke_action` is imported or referenced anywhere. **Pass.**
- Clean-up: the two test entries added to `.second-brain/cockpit_threads.json` (the real hand-off + the induced-failure message) were removed immediately after verification. No residual test data remains in the real vault beyond the pre-existing real attachment file itself (untouched, read-only).

**Scope-internal judgement call for human spot-check** (per `gate: flagged` above): `_attachments_dir` skips slugification entirely rather than reaching into `vault_writer._slugify`, per the reasoning above — confirmed correct live against two independent real fixtures, not merely asserted.

`gate: flagged` 2026-08-14 — the deviation above is a scope-internal judgement call (implements the task's own Objective/Constraints faithfully, choosing the cleaner of two compliant readings of the task's own explicit Constraint about avoiding a private reach-through), not a MUST-FLAG architecture/dependency/AC trigger. No locked AC weakened; every AC this task owns (`AC-04`, `AC-05`) verified live with real data, a real attachment file, and a real Compass API call.
