---
id: REQ-SB-69-US-01-T01
title: New app/data_access/email_staging.py — durable, vault-local, per-email staging store (stage_email/list_staged_emails/remove_staged_email)
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

# REQ-SB-69-US-01-T01 — Durable email staging primitives

## Parent Story

- Story: [[REQ-SB-69-US-01]] — `../UserStories/REQ-SB-69-US-01-decoupled-email-pull-and-human-readable-thread-notes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-69 *Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes*

---

## Objective

Build the new, dedicated `app/data_access/email_staging.py` module —
`ADR-046` Decision 1 — a durable, vault-local, incremental store for raw
pulled-but-not-yet-processed email content, one directory per email under
`.second-brain/email_staging/<entry_id>/`.

---

## Starting State → End State

**Before / Inputs:**
- No staging concept exists anywhere in this codebase. `outlook_com.
  list_recent_mail` returns a plain `list[dict]` in-memory only, consumed
  immediately by the caller.
- `app/data_access/upload_storage.py` (`ADR-034`) is the closest real
  precedent in this codebase for "structured metadata plus a real binary
  payload on disk under `.second-brain/`" — one file per upload, a
  generated id in the filename, deliberately not composing
  `vault_writer.py` (data_access siblings, not layered).

**After / Outputs:**
- A new `app/data_access/email_staging.py` module with three primitives:
  - `stage_email(email: dict) -> None` — writes one email's own directory.
    `email` is exactly the dict shape `outlook_com.list_recent_mail`
    already produces (`id`, `subject`, `sender_name`, `sender_email`,
    `received`, `body`, `conversation_id`, `recipients`, `attachments`).
    Writes `.second-brain/email_staging/<id>/email.json` — the full dict
    MINUS each attachment's own `"content"` bytes, PLUS each attachment's
    own `"relative_path"` into that same directory's `attachments/`
    subfolder; writes each attachment's real bytes to
    `.second-brain/email_staging/<id>/attachments/<filename>` directly
    (never base64-inflated into the JSON, mirroring `upload_storage.py`'s
    own blob-on-disk precedent, `ADR-034`). Idempotent — re-staging the
    same `id` overwrites its own directory cleanly (a Pull re-run against
    an overlapping recent-N window must not create a second, duplicate
    staged copy of the same email).
  - `list_staged_emails() -> list[dict]` — enumerates every staged
    directory under `.second-brain/email_staging/`, reconstructing each
    into the EXACT `list_recent_mail`-shaped dict (attachment bytes
    re-read from their own files back into each attachment's own
    `"content"` key) — every downstream Job (`classify_captured_email`,
    `thread_match_merge`, `summarize_attachment`, etc.) must see the
    identical shape it already consumes today, so none of their own
    function bodies need to change. Returns `[]` if the staging directory
    doesn't exist yet (mirrors this codebase's own "not-yet-created-
    folder is a valid, honest empty state" convention,
    `list_notes_in_kind_folder`).
  - `remove_staged_email(entry_id: str) -> None` — deletes a staged
    entry's own directory (metadata + attachments) once its own graph run
    has completed successfully. Idempotent — removing an already-absent
    `entry_id` is a no-op, never raises.

---

## Files to Modify

- `src/backend/app/data_access/email_staging.py` (**new file**) — the
  three primitives above. Compose `app.config.settings.vault_path`
  directly (never `vault_writer.py` — data_access siblings under
  `.second-brain/`, mirroring `upload_storage.py`'s own explicit
  "deliberately does not import vault_writer" precedent and docstring
  reasoning). Use `json.dumps(..., indent=2)`/`json.loads` for
  `email.json`, mirroring `vault_writer.py`'s own `_processed_emails_path`/
  `load_processed_email_ids` JSON-file shape. Use `pathlib.Path.mkdir(
  parents=True, exist_ok=True)` for directory creation and
  `shutil.rmtree(..., ignore_errors=True)` (or an equivalent idempotent
  recursive delete) for `remove_staged_email`.

---

## Constraints

- Inherits from parent story.
- **Never imports `vault_writer.py`** — a sibling data_access module for a
  structurally different storage concern (raw pre-note buffer, not a
  vault note), mirroring `upload_storage.py`'s own explicit boundary
  reasoning (`ADR-034`).
- **Never imports `outlook_com`** — this module only stores/reads plain
  dicts; it has no COM dependency of its own. (The one function that
  still imports `outlook_com` is `T02`'s `email_pull.py`.)
- **`stage_email`'s own returned/reconstructed dict shape from
  `list_staged_emails` must be byte-for-byte compatible with what
  `outlook_com.list_recent_mail` already returns** — every dict key
  present today (`id`, `subject`, `sender_name`, `sender_email`,
  `received`, `body`, `conversation_id`, `recipients`, `attachments`,
  and each attachment's `filename`/`content`/`size`) must round-trip
  through `stage_email` → `list_staged_emails` unchanged in meaning. This
  is what lets `T03` swap the pipeline's own input source with zero
  changes to any downstream Job's own function body.
- **Attachment bytes are written to their own file on disk, never
  base64-encoded into the JSON record** — mirrors `ADR-034`'s own
  precedent; the `recipients`/`attendees` JSON-encoded-STRING workaround
  (`ADR-042` point 3) is for small structured VALUES, not multi-megabyte
  binaries, and is explicitly rejected for this use in `ADR-046`'s own
  Alternatives Considered.
- **This is not a staging/promotion gate on vault content** (`MEMORY.md`'s
  standing constraint) — a staged email is not yet a note at all; do not
  add any approval/review step here. This module exists solely so an
  Outlook-COM stall can't lose already-fetched content.
- No change to any other file in this task.

---

## Tests

<!-- No locked AC maps directly to this task alone — this module's own
primitives are exercised end-to-end by T02/T03/T04's own AC-tagged
verification once wired in. This task's own Tests are plain, non-AC
sanity checks proving the primitives themselves are correct in
isolation, composable, and idempotent, before any caller depends on
them. -->

**Manual verification steps** (direct Python-shell calls against a real,
disposable subdirectory of the real configured vault — no HTTP server
needed):

1. Construct a synthetic email dict matching `list_recent_mail`'s own
   shape (including one small real attachment with real bytes). Call
   `stage_email(email)`. Confirm
   `.second-brain/email_staging/<id>/email.json` exists, its `body`/
   `subject`/etc. match the input, and its `attachments[0]` entry has NO
   `"content"` key but does have a `"relative_path"`/`filename` pointing
   at a real file under `attachments/` whose bytes match the original
   exactly.
2. Call `list_staged_emails()`. Confirm the returned list contains
   exactly one entry, and that entry's shape (including
   `attachments[0]["content"]`, re-read from disk) is deep-equal to the
   original synthetic email dict passed into `stage_email` in step 1.
3. Call `stage_email` a second time with the SAME `id` but a different
   `subject`. Confirm `list_staged_emails()` still returns exactly one
   entry (the directory was overwritten, not duplicated) and its
   `subject` reflects the second call — idempotent re-staging.
4. Call `remove_staged_email(id)`. Confirm
   `.second-brain/email_staging/<id>/` no longer exists and
   `list_staged_emails()` now returns `[]`. Call `remove_staged_email(id)`
   a second time — confirm it does not raise (idempotent no-op).
5. Confirm `list_staged_emails()` against a vault with no
   `.second-brain/email_staging/` directory at all returns `[]` without
   raising.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `stage_email`/`list_staged_emails`/`remove_staged_email` exist and
      behave exactly per `## Starting State → End State` above
- [x] Round-trip shape fidelity confirmed (Test step 2)
- [x] Idempotent re-stage and idempotent remove confirmed (Test steps 3, 4)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint — not
      warranted (see `## Implementation Log`): this task is a direct, mechanical
      build of `ADR-046` Decision 1, no new decision/pattern/constraint beyond what
      the ADR already recorded
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `on_item_fetched` callback on `outlook_com.list_recent_mail` and
  the new `email_pull.py` module that calls `stage_email` from a real
  live pull — `T02`.
- `email_capture_pipeline.py` reading from `list_staged_emails()` — `T03`.
- Independent dispatch/lock separation — `T04`.

---

## Context / Notes

`ADR-046` Decision 1 (`Implementation/Architecture/ADR.md`) is the full
architectural reasoning, including the rejected "single growing JSON
array file" and "base64-in-JSON" alternatives — read it before
implementing if any shape question isn't already answered above.

---

## Implementation Log

**Built as designed, no deviations.** New file
`src/backend/app/data_access/email_staging.py` — `stage_email(email:
dict) -> None`, `list_staged_emails() -> list[dict]`,
`remove_staged_email(entry_id: str) -> None`, exactly per `## Starting
State → End State`. Composes `app.config.settings.vault_path` directly,
mirrors `upload_storage.py`'s "deliberately does not import
`vault_writer`" boundary (docstring states this explicitly) and never
imports `outlook_com`. `.second-brain/email_staging/<entry_id>/`, with
`email.json` (the full input dict minus each attachment's `content`,
plus each attachment's `relative_path`) and `attachments/<filename>` for
the real bytes — `json.dumps(..., indent=2)` mirroring
`vault_writer.py::mark_email_processed`'s own JSON-file shape,
`Path.mkdir(parents=True, exist_ok=True)` for directory creation,
`shutil.rmtree(..., ignore_errors=True)` for idempotent
delete-then-recreate (`stage_email`'s own overwrite) and idempotent
removal (`remove_staged_email`). `list_staged_emails()` returns `[]` if
`.second-brain/email_staging/` doesn't exist yet, mirroring
`list_notes_in_kind_folder`'s own not-yet-created-folder convention.

**Scope-internal judgement call, logged for human spot-check (no locked
AC governs it directly — this is an edge case in `outlook_com.py`'s own
real attachment shape, not something the task's own Tests block names):**
`outlook_com._extract_attachments` already sets an attachment's own
`"content"` to `None` (never raises) when a real attachment exceeds
`_MAX_ATTACHMENT_BYTES` — there is no real byte payload to persist to
disk for that case. `stage_email` handles this by writing no file and
recording no `relative_path` for that one attachment (keeping every
OTHER attachment on the same email unaffected); `list_staged_emails`
reconstructs `"content": None` for it, so the round-trip shape stays
`list_recent_mail`-identical (a `None` content value round-trips as
`None`, exactly as it already does today for any downstream Job reading
`list_recent_mail`'s own direct output). Not independently tested this
pass (the task's own Test step 1 names "one small real attachment with
real bytes" specifically) — reasoned directly from `_extract_attachments`'s
own real, already-shipped behavior, not guessed.

Verification was run directly against the real, configured backend venv
(`src/backend/.venv`) and the real, configured vault
(`VAULT_PATH=<OPERATOR_VAULT_OLD>`) via a one-off Python
script driving `email_staging` directly — no HTTP server needed, no
locked AC maps to this task alone (per this task's own `## Tests`
preamble; `T02`/`T03`/`T04` exercise these primitives end-to-end against
their own locked ACs once wired in). A disposable, clearly-namespaced
`entry_id` (`TEST-T01-STAGING-VERIFY-0001`) was used and fully removed by
the test's own Step 4 — the real vault carries no leftover test state
after this run (confirmed: `.second-brain/email_staging/` exists but is
empty, the same "created, then legitimately emptied by normal use" state
this module would leave behind after any real stage→process→remove
cycle).

- **Test step 1** (`stage_email` writes correct on-disk shape) — PASS.
  Constructed a synthetic email dict matching `list_recent_mail`'s shape,
  with one real attachment (65 real bytes). Confirmed
  `.second-brain/email_staging/<id>/email.json` exists; `body`/
  `subject`/`sender_name`/`conversation_id` match the input exactly;
  `attachments[0]` has no `"content"` key but has both `"relative_path"`
  and `"filename"`; the referenced file under `attachments/` exists and
  its bytes are byte-for-byte identical to the original.
- **Test step 2** (round-trip shape fidelity) — PASS. `list_staged_emails()`
  returned exactly one entry; that entry (with `attachments[0]["content"]`
  re-read from disk) was deep-equal (`==`) to the original synthetic
  email dict passed into `stage_email`.
- **Test step 3** (idempotent re-stage) — PASS. Called `stage_email` a
  second time with the same `id` and a different `subject`.
  `list_staged_emails()` still returned exactly one entry, and its
  `subject` reflected the second call — the directory was overwritten,
  not duplicated.
- **Test step 4** (idempotent remove) — PASS. `remove_staged_email(id)`
  deleted `.second-brain/email_staging/<id>/`; `list_staged_emails()`
  then returned `[]`. A second `remove_staged_email(id)` call on the
  already-absent entry did not raise.
- **Test step 5** (empty-staging-directory honesty) — PASS. Confirmed,
  before Step 1 ran (the real vault had no
  `.second-brain/email_staging/` directory at all yet), that
  `list_staged_emails()` returned `[]` without raising.

Full raw pass/fail output (all 14 checks PASS, zero FAIL) captured
during this run; no re-run or fix cycle was needed.

gate: clear 2026-08-17 — no MUST-FLAG trigger fired: no material
assumption filling a genuine gap (the one attachment-`None` edge case
above is a direct, reasoned application of `outlook_com.py`'s own
already-shipped behavior, not a guess among equally-valid readings), no
ADR/architecture change, no `ESCALATIONS.md` entry, task not oversized,
every step in this task's own `## Tests` block verified directly and
passed.
