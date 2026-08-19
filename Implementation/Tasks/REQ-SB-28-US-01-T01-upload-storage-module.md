---
id: REQ-SB-28-US-01-T01
title: requirements.txt (pypdf, python-multipart) + new app/data_access/upload_storage.py (validate/save/extract/delete) + .second-brain/uploads/ boundary
parent_story: REQ-SB-28-US-01
requirement_id: REQ-SB-28
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-28-US-01-T01 — New upload-storage module and `.second-brain/uploads/` boundary

## Parent Story

- Story: [[REQ-SB-28-US-01]] — `../UserStories/REQ-SB-28-US-01-file-upload-attach-and-handoff.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-28 *File Upload for Agents*

---

## Objective

Add `app/data_access/upload_storage.py` — the temporary, non-vault raw-byte
storage boundary `ADR-034` decided (`.second-brain/uploads/`, the
`.second-brain/` convention's first extension to raw bytes) — owning
validation (accepted extension + size cap), save, text extraction
(`.txt`/`.md` direct decode, `.pdf` via `pypdf`), and delete. Add `pypdf`
and `python-multipart` to `requirements.txt`.

---

## Starting State → End State

**Before / Inputs:**
- `app/data_access/vault_writer.py` owns the existing `.second-brain/`
  flat-file JSON state convention (`_STATE_DIR = ".second-brain"`,
  `load_skills_state`/`save_skills_state` as the closest existing
  precedent) — read for the directory-root convention only; not modified
  by this task.
- `app/config.py::settings.vault_path` — the vault root every
  `.second-brain/` path is built under.
- `requirements.txt` has no PDF-parsing library and no `python-multipart`
  today (confirmed by the architect's direct inspection, `ADR-034`).

**After / Outputs:**
- `requirements.txt` gains `pypdf` and `python-multipart` (additive, no
  existing line changed or reordered).
- `app/data_access/upload_storage.py` (new) exposes:
  ```python
  """Temporary, non-vault raw-byte upload storage (ADR-034) -- the first
  extension of the .second-brain/ flat-file state convention
  (app/data_access/vault_writer.py's own _STATE_DIR) to raw bytes rather
  than JSON. One file per upload, named with a generated id to avoid
  collisions (mirrors this project's own standing filename-uniqueness
  Constraint, MEMORY.md), deleted once summarized/handed off or on
  validation rejection. Deliberately does not import vault_writer -- this
  boundary is siblings with it (both under .second-brain/), not layered
  on top of it; vault_writer.py owns JSON state, this module owns binary
  blobs, both compute their own subdirectory under settings.vault_path.
  """
  from __future__ import annotations

  import uuid
  from pathlib import Path

  import pypdf

  from app.config import settings

  ACCEPTED_EXTENSIONS = {".pdf", ".txt", ".md"}
  MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB (REQ-SB-28-US-01 Constraints)

  _UPLOADS_DIR = ".second-brain/uploads"


  def _uploads_dir() -> Path:
      path = settings.vault_path / _UPLOADS_DIR
      path.mkdir(parents=True, exist_ok=True)
      return path


  def _upload_path(upload_id: str, filename: str) -> Path:
      ext = Path(filename).suffix.lower()
      return _uploads_dir() / f"{upload_id}{ext}"


  def validate_upload(filename: str, size_bytes: int) -> str | None:
      """Returns None if the upload is acceptable, else a clear, honest,
      user-facing rejection message -- distinguishes an unsupported file
      TYPE (Scenario 7/AC-07 -- e.g. an image) from exceeding the SIZE cap
      (Scenario 8/AC-08), never a single generic message conflating both."""
      ext = Path(filename).suffix.lower()
      if ext not in ACCEPTED_EXTENSIONS:
          return (
              f"'{ext or filename}' files aren't supported yet -- only PDF "
              "(.pdf), plain text (.txt), and Markdown (.md) files can be "
              "summarized today."
          )
      if size_bytes > MAX_UPLOAD_SIZE_BYTES:
          size_mb = size_bytes / (1024 * 1024)
          return f"That file is too large ({size_mb:.1f} MB) -- the limit is 20 MB."
      return None


  def save_upload(filename: str, content: bytes) -> str:
      """Stores content under a freshly generated upload_id + the original
      extension; returns the upload_id. Caller must have already confirmed
      validate_upload(filename, len(content)) is None -- this function does
      not re-validate."""
      upload_id = str(uuid.uuid4())
      _upload_path(upload_id, filename).write_bytes(content)
      return upload_id


  def extract_text_content(upload_id: str, filename: str) -> str:
      """Reads the stored upload back as plain text -- .txt/.md decoded
      directly, .pdf extracted page-by-page via pypdf. Raises ValueError if
      extraction produces no usable text (e.g. a scanned/image-only PDF
      with no embedded text layer) -- the caller (T04) surfaces this
      honestly, mirroring Scenario 9's "never a fabricated summary"
      posture; this function itself never fabricates placeholder text."""
      path = _upload_path(upload_id, filename)
      ext = Path(filename).suffix.lower()
      if ext == ".pdf":
          reader = pypdf.PdfReader(str(path))
          text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
      else:
          text = path.read_text(encoding="utf-8", errors="replace").strip()
      if not text:
          raise ValueError("No extractable text content found in this file.")
      return text


  def delete_upload(upload_id: str, filename: str) -> None:
      """Idempotent cleanup -- a no-op if the file is already gone."""
      _upload_path(upload_id, filename).unlink(missing_ok=True)
  ```

---

## Files to Modify

- `src/backend/requirements.txt` — add `pypdf` and `python-multipart`
  (additive lines; do not reorder or remove any existing entry).
- `src/backend/app/data_access/upload_storage.py` (new) — per the code
  block above.

---

## Constraints

- Inherits from parent story: never fabricate — `extract_text_content`
  raises rather than returning empty/placeholder text on an unusable file.
- `api → business → data_access` layering (`ADR-003`) — this module has no
  business-logic dependency (no import of `app.business.*`); it is a pure
  data_access boundary, mirroring `vault_writer.py`'s own layering.
- Must NOT modify `app/data_access/vault_writer.py` — siblings, not
  layered on top of it (see module docstring above).
- `MAX_UPLOAD_SIZE_BYTES`/`ACCEPTED_EXTENSIONS` are this story's own
  locked defaults (20 MB; `.pdf`/`.txt`/`.md`) — do not change without a
  story-level Constraint change.
- `save_upload`/`delete_upload` must use a generated id (not the raw
  original filename) to avoid filename collisions between concurrent
  uploads.

---

## Tests

<!-- Non-AC smoke checks plus this task's own share of locked ACs 05/07/08
(the parts verifiable at this module's own level, before the endpoint
exists) -- REQ-SB-28-US-01-T04 re-verifies the same ACs end-to-end through
the real HTTP endpoint. -->

**Manual verification steps** (Python shell, backend `.venv`; use a real
small `.pdf` with embedded text, a `.txt`, a `.md`, and a `.png` as fixtures):

1. Non-AC smoke check: `validate_upload("notes.txt", 1024)` → `None`.
   `validate_upload("book.pdf", 1024)` → `None`. `validate_upload("notes.md", 1024)` → `None`.
2. **[REQ-SB-28-US-01-AC-07]** `validate_upload("photo.png", 1024)` →
   a non-`None`, clearly worded message naming `.png` as an unsupported
   type (not the size-limit wording from step 3).
3. **[REQ-SB-28-US-01-AC-08]** `validate_upload("book.pdf", 21 * 1024 * 1024)`
   → a non-`None` message naming the 20 MB limit specifically (distinct
   wording from step 2's type-rejection message).
4. Non-AC smoke check: `save_upload("notes.txt", b"hello world")` returns
   a string `upload_id`; confirm `.second-brain/uploads/<upload_id>.txt`
   now exists on disk with that exact content.
5. **[REQ-SB-28-US-01-AC-02]** (extraction half) `extract_text_content`
   against: (a) the `.txt` saved in step 4 — returns `"hello world"`; (b)
   a real `.md` file saved via `save_upload` — returns its real text; (c)
   a real, small text-bearing `.pdf` saved via `save_upload` — returns
   its real extracted text (confirm it is the actual PDF content, not
   empty/placeholder).
6. Non-AC smoke check: `extract_text_content` against a saved upload whose
   underlying PDF has no extractable text (or an empty `.txt`) — confirm
   it raises `ValueError`, not an empty string.
7. **[REQ-SB-28-US-01-AC-05]** (cleanup half) `delete_upload(upload_id, "notes.txt")`
   from step 4 — confirm the file on disk is gone. Call it a second time
   — confirm no exception (idempotent).
8. Clean-up: delete any remaining files left under `.second-brain/uploads/`
   by this verification session.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `requirements.txt` gains `pypdf` and `python-multipart`, additive only
- [ ] `validate_upload` distinguishes an unsupported-type rejection from a
      size-limit rejection with different, clear wording (`AC-07`/`AC-08`)
- [ ] `save_upload` writes real bytes under `.second-brain/uploads/` keyed
      by a generated id, never the raw original filename alone
- [ ] `extract_text_content` returns real extracted text for `.txt`/`.md`/`.pdf`,
      and raises (never returns empty/placeholder text) when none exists
- [ ] `delete_upload` is idempotent
- [ ] `app/data_access/vault_writer.py` not modified
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Compass summarization call — `T02`.
- The `summarize-file` Skill registration — `T03`.
- The HTTP endpoint and end-to-end orchestration (calling `validate_upload`/
  `save_upload`/`extract_text_content`/`delete_upload` in sequence) — `T04`.
- Any frontend surface — `T05`.

---

## Context / Notes

This module's shape mirrors `vault_writer.py`'s `_STATE_DIR`/state-file
convention one layer over (raw bytes instead of JSON), per `ADR-034`
point 1 — read `vault_writer.py`'s `_STATE_DIR`/`load_skills_state`/
`save_skills_state` for the precedent, but do not import from or modify
that module; this is a new, sibling boundary.

`python-multipart` is a decomposer-added correction beyond `ADR-034`'s own
text (which named only `pypdf`) — FastAPI's `File`/`Form` request
parameters (needed for `T04`'s multipart endpoint, already decided by
`ADR-034` point 6) silently fail at request time without it installed.
This is a routine implementation necessity of an already-decided
architectural choice, not a new architectural decision.

---

## Implementation Log

**2026-08-14 — built exactly per the task's own code block, no deviation.**
`requirements.txt` gained `pypdf`/`python-multipart` as additive lines
(confirmed `python-multipart` was already present transitively via
FastAPI's own installed extras — `pip show` confirmed `0.0.32` already
installed — but the requirements.txt line is added regardless, per the
task's own explicit instruction, so the direct dependency is declared,
not just transitively present). `pypdf==6.16.0` installed fresh into
`.venv`. New `app/data_access/upload_storage.py` created verbatim per
the task's own code block.

**Verification (Python shell, backend `.venv`, real fixtures — a real
`.txt`, a real `.md`, a hand-constructed real `.pdf` with a genuine
embedded text-layer content stream confirmed independently readable via
`pypdf.PdfReader`, and a real 1x1 `.png`; `pdfplumber`/`reportlab`/
`fpdf2` were not available in this environment, so the fixture PDF was
constructed directly via minimal valid PDF object/xref/trailer syntax —
this is still a genuinely real, on-disk PDF file, not a mock):**

- Non-AC smoke check (step 1): `validate_upload` returned `None` for
  `.txt`/`.pdf`/`.md`. Confirmed.
- **AC-07** (step 2): `validate_upload("photo.png", 1024)` →
  `"'.png' files aren't supported yet -- only PDF (.pdf), plain text
  (.txt), and Markdown (.md) files can be summarized today."` — distinct
  wording from the size-limit message. **Pass.**
- **AC-08** (step 3): `validate_upload("book.pdf", 21*1024*1024)` →
  `"That file is too large (21.0 MB) -- the limit is 20 MB."` — distinct
  from step 2's wording. **Pass.**
- Non-AC smoke check (step 4): `save_upload` returned a real `upload_id`;
  confirmed `.second-brain/uploads/<id>.txt` existed on disk with the
  exact byte content `b"hello world"`.
- **AC-02** (extraction half, step 5): (a) `.txt` → `"hello world"`
  exactly; (b) `.md` (real fixture, an em-dash-bearing vendor-evaluation
  note) → the real file content, verified byte-exact by writing the
  extracted string to a UTF-8 file and re-reading it (console codepage
  display of the em-dash was misleading on first glance — independently
  confirmed correct, not corrupted); (c) `.pdf` → `"Harbor Point
  Renovation Summary: Phase two adds 40 residential units and a rooftop
  solar array, budgeted at 2.3 million dollars, completion targeted for
  March."` — the real embedded PDF text, not empty/placeholder. **Pass.**
- Non-AC smoke check (step 6): an empty `.txt` upload raised
  `ValueError("No extractable text content found in this file.")`, not
  an empty string. Confirmed.
- **AC-05** (cleanup half, step 7): `delete_upload` removed the file
  (confirmed `.exists()` → `False`); a second call raised no exception
  (idempotent). **Pass.**
- Clean-up (step 8): all files removed from `.second-brain/uploads/`;
  confirmed directory empty at end of session.

**Scope-internal judgement call for human spot-check:** the task's own
Tests block asked for real `.pdf`/`.png` fixtures without specifying how
to obtain them; no PDF-generation library (`reportlab`/`fpdf2`) was
available in this environment, so a minimal, syntactically valid real
PDF (hand-built object/xref/trailer structure with one embedded text
`Tj` operator) was constructed directly rather than sourced from an
existing document. `pypdf.PdfReader` genuinely parsed and extracted its
real text — a real dependency exercised against a real (if minimal) PDF
file, not a mock/monkeypatch.

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired (no new
dependency beyond what `ADR-034`/the decomposer's own
`python-multipart` note already named; no shared-interface change; no
ADR deviation; no unanticipated file; all 3 of this task's own locked
ACs verified live).
