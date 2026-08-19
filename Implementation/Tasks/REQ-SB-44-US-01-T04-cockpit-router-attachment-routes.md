---
id: REQ-SB-44-US-01-T04
title: Extend app/api/cockpit_router.py — GET /cockpit/email/{stem}/attachments, POST .../attachments/{filename}/hand-off
parent_story: REQ-SB-44-US-01
requirement_id: REQ-SB-44
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-44-US-01-T03, REQ-SB-43-US-01-T05]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-44-US-01-T04 — Attachment-review routes

## Parent Story

- Story: [[REQ-SB-44-US-01]] — `../UserStories/REQ-SB-44-US-01-inbox-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-44 *Inbox Cockpit — Expert-Assisted Email Workspace*

---

## Objective

Add two new, additive routes to `REQ-SB-43-US-01-T05`'s own `app/api/cockpit_router.py` file — listing an email's attachments and handing one off to the shared thread — composing `T03`'s `attachments.py`. This is the same shared router file both stories use (`ADR-036` point 2); this task extends it, never a second router.

---

## Starting State → End State

**Before / Inputs:** `REQ-SB-43-US-01-T05` has landed `app/api/cockpit_router.py`'s five generic-over-`subject_kind` routes. `T03` has landed `attachments.list_attachments`/`hand_off_attachment_to_chat`.

**After / Outputs:** two new routes appended to the SAME file:
```python
from app.business.cockpit import attachments  # additive import, alongside people/research/threads

@router.get("/email/{subject_note_stem}/attachments")
def list_email_attachments(subject_note_stem: str) -> list[dict]:
    return attachments.list_attachments(subject_note_stem)


@router.post("/email/{subject_note_stem}/attachments/{filename}/hand-off")
def hand_off_attachment(subject_note_stem: str, filename: str) -> dict:
    return attachments.hand_off_attachment_to_chat(subject_note_stem, filename)
```

---

## Files to Modify

- `src/backend/app/api/cockpit_router.py` — add the `attachments` import and the two new routes, additive only, at the end of the file (or grouped logically with the other routes — decomposer/coder's own call). Do not modify any of the five existing routes `REQ-SB-43-US-01-T05` built.

---

## Constraints

- These two routes are ONLY registered at `/cockpit/email/...` (not `/cockpit/{subject_kind}/...`) — attachments are an email-only concept, per the story's own scope; do not generalize this path to accept `"meeting"` (a Meeting Cockpit has no attachment concept — `REQ-SB-43-US-01`'s own Affected Screens confirm this).
- No change to `GET /cockpit/{subject_kind}/{subject_note_stem}`'s own existing response shape — attachments are fetched via their OWN separate route (`Cockpit.tsx`'s `attachmentsSlot` prop, supplied by `REQ-SB-44-US-01`'s own `T06`, calls it independently), not folded into the generic subject payload (keeps the shared endpoint truly generic, per `ADR-036` point 3).
- Read `REQ-SB-43-US-01-T05`'s own REAL, as-built `cockpit_router.py` before editing — reconcile the existing five routes' real shape, do not overwrite or reformat them.

---

## Tests

**Manual verification steps** (real dev server, backend `.venv`; requires a real Email note with a real attachment, per `T03`'s own Tests):
1. **[REQ-SB-44-US-01-AC-04]** `GET /cockpit/email/<real-stem>/attachments` — confirm `200`, a real list matching `T03`'s own `list_attachments` output.
2. **[REQ-SB-44-US-01-AC-05]** `GET /cockpit/email/<real-stem-with-no-attachments>/attachments` → `[]`.
3. **[REQ-SB-44-US-01-AC-04]** `POST /cockpit/email/<real-stem>/attachments/<real-filename>/hand-off` — confirm `200`, `{"status": "ok", "summary": ...}`; confirm `GET /cockpit/email/<real-stem>` (the existing route) now shows the hand-off summary in `thread.messages`.
4. Non-AC smoke check: `GET /cockpit/meeting/<real-meeting-stem>`'s own existing response shape is byte-for-byte unchanged by this task (no `attachments` key leaked into it).
5. Clean-up: as per `T03`'s own Tests.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `GET /cockpit/email/{stem}/attachments` and `POST .../hand-off` exist, composing `T03`
- [x] Neither route is reachable under `/cockpit/meeting/...`
- [x] The five existing routes `REQ-SB-43-US-01-T05` built are unmodified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend change — `T05`/`T06`.
- `T03`'s own `attachments.py` implementation — composed here, not modified.

---

## Context / Notes

Full mechanism: `ADR-036` points 2/5/6.

---

## Implementation Log

**2026-08-14 — built exactly per the task's own code block, no deviation.** `cockpit_router.py` gained an additive `attachments` import and two new routes (`GET /cockpit/email/{stem}/attachments`, `POST /cockpit/email/{stem}/attachments/{filename}/hand-off`), appended after the existing `research/save` route; the five existing routes `REQ-SB-43-US-01-T05` built were read first and left byte-for-byte unmodified.

**Verification (real dev server on port 8001, restarted fresh — non-`--reload` — after this edit, per this project's own established `--reload`-staleness-avoidance protocol):**

- **[AC-04]** `GET /cockpit/email/2026-08-12-Emailing%20Sarmad_Jari_Resume.pdf-10930000/attachments` → real `200`, `[{"filename":"Sarmad_Jari_Resume.pdf","size":342594}]`, matching `T03`'s own real `list_attachments` output exactly. **Pass.**
- **[AC-05]** `GET /cockpit/email/<real-stem-with-no-attachments>/attachments` → `200`, `[]`. **Pass.**
- **[AC-04]** `POST /cockpit/email/<real-stem>/attachments/Sarmad_Jari_Resume.pdf/hand-off` → real `200`, `{"status":"ok","summary":<real Compass-generated resume summary>}`. After a real `POST /vault-index/rebuild` (needed for this specific real Email note to be index-visible — an ordinary, already-documented `ADR-024` index-freshness characteristic, not a defect of this task), `GET /cockpit/email/<real-stem>` (the existing route) showed the real hand-off summary as the newest turn in `thread.messages`, prefixed `"[Attachment: Sarmad_Jari_Resume.pdf]"`. **Pass.**
- Non-AC smoke check: `GET /cockpit/meeting/HPC%20kickoff%20meeting-2026-08-11-62500000` — real response shape confirmed byte-for-byte unchanged by this task (`subject`/`people`/`thread`/`research_results` only, no `attachments` key leaked in). **Pass.**
- Clean-up: the real `.second-brain/cockpit_threads.json` test entry created by this verification pass was removed immediately after.

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired (no deviation from the task's own code sample; additive-only router change; all locked ACs this task owns verified live via real HTTP against real data).
