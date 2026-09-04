---
id: REQ-SB-59-US-01-T01
title: New app/business/vault_migration.py — wipe_legacy_email_notes() archives Work/Emails/ + stale .second-brain/ JSON stores
parent_story: REQ-SB-59-US-01
requirement_id: REQ-SB-59
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-59-US-01-T01 — `wipe_legacy_email_notes()` — archive `Work/Emails/` + stale `.second-brain/` JSON stores

## Parent Story

- Story: [[REQ-SB-59-US-01]] — `../UserStories/REQ-SB-59-US-01-full-vault-migration-to-new-knowledge-model.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-59 *Full Vault Migration to the New Knowledge Model*

---

## Objective

Build the new `app/business/vault_migration.py` module (fifth instance of this
codebase's one-off-migration-module shape) with its first public function,
`wipe_legacy_email_notes() -> dict`: archives (never deletes) every note under
`Work/Emails/` plus the two now-stale `.second-brain/` JSON stores
(`processed_email_ids.json`, `conversation_index.json`) into a new
`.second-brain/migration_backup/<run-timestamp>/` archive root, and expose it as
`POST /poc/wipe-legacy-email-notes`.

---

## Starting State → End State

**Before / Inputs:**
- No `app/business/vault_migration.py` file exists yet.
- `app/data_access/vault_writer.py::list_all_note_paths() -> list` (real,
  `Done`) returns every flat `Work/<kind>/*.md` note, including every note
  currently under `Work/Emails/`.
- `vault_writer.move_note_and_attachments(note_path, target_dir) -> str`
  (real, `Done`) moves a note and its sibling `attachments/<slug>/` folder
  (if any) into `target_dir`, preserving the note's own filename; raises
  `FileExistsError` rather than silently overwriting a collision.
- `vault_writer.remove_empty_dirs(root) -> None` (real, `Done`) removes any
  now-empty directory under `root`, and `root` itself if empty.
- `.second-brain/processed_email_ids.json` and
  `.second-brain/conversation_index.json` are private-constant-named paths
  inside `vault_writer.py` (`_STATE_DIR = ".second-brain"`,
  `_PROCESSED_EMAILS_FILE = "processed_email_ids.json"`,
  `_CONVERSATIONS_FILE = "conversation_index.json"`) — this task constructs
  their canonical paths directly as `settings.vault_path / ".second-brain" /
  "processed_email_ids.json"` (and the `conversation_index.json` sibling),
  mirroring `vault_restructure.py`'s own existing precedent of touching
  `settings.vault_path` directly for mechanical, non-Note filesystem
  bookkeeping, rather than importing either private name or adding a new
  `vault_writer` primitive for a one-time move of already-owned files.
- `app/api/email_poc_router.py` has no `/poc/wipe-legacy-email-notes` route
  yet; its existing `/poc/backfill-tags`/`/poc/flatten-customer-folders`
  routes are the naming/shape precedent to match.

**After / Outputs:**
- New file `app/business/vault_migration.py` with
  `wipe_legacy_email_notes() -> dict`, returning at minimum
  `{"run_timestamp": str, "emails_moved": list[dict], "state_files_archived":
  list[dict]}` (exact key names are this task's own implementation latitude;
  every result MUST report per-note/per-file `status`, mirroring
  `tag_backfill.backfill_tags`'s/`vault_restructure.flatten_customer_folders`'s
  own `results: list[dict]` reporting shape).
- After a real run: `Work/Emails/` contains zero `.md` notes; every
  pre-migration note (and any sibling `attachments/<slug>/` folder) now
  exists, byte-for-byte, under
  `.second-brain/migration_backup/<run-timestamp>/Emails/`.
- `processed_email_ids.json`/`conversation_index.json` no longer exist at
  their canonical `.second-brain/` paths; both now exist, byte-for-byte,
  under `.second-brain/migration_backup/<run-timestamp>/`.
- New `POST /poc/wipe-legacy-email-notes` endpoint in `email_poc_router.py`.

---

## Files to Modify

- `src/backend/app/business/vault_migration.py` (new file)
- `src/backend/app/api/email_poc_router.py` (add import +
  `POST /poc/wipe-legacy-email-notes` endpoint, matching the existing
  `/poc/backfill-tags`/`/poc/flatten-customer-folders` shape — a thin
  wrapper summarizing `wipe_legacy_email_notes()`'s own `results`, per that
  router's own established convention)

---

## Constraints

- Inherits from parent story:
  - **Archive, never delete** — every note/file this function removes from
    its canonical location moves via `vault_writer.move_note_and_attachments`
    (Notes) or a plain `Path.rename` (the two JSON stores), never
    `Path.unlink()`.
  - **Outlook itself is never touched by this task** — `wipe_legacy_email_notes`
    performs zero Outlook-COM calls; it only moves vault-local files.
  - **One-time, operator-triggered** — no scheduler wiring, no new UI.
  - Must respect the `api → business → data_access` layer boundary
    (`ADR-003`) — this module composes `vault_writer` (data_access) only;
    the two JSON-store moves are direct `pathlib`/`Path.rename` use inside
    `vault_migration.py` itself (business layer touching its own owned
    files), mirroring `vault_restructure.py`'s established precedent, not a
    new `vault_writer` primitive.
- **No new "already ran" state marker, no dry-run flag** — idempotency comes
  entirely from "nothing left under `Work/Emails/`/at the canonical JSON
  paths to move" on a rerun (`ADR-047` Alternative 5); do not invent one.
- Do not modify `vault_writer.py`, `email_pull.py`,
  `email_capture_pipeline.py`, or `meeting_classification.py` — every
  primitive this task composes already exists, unmodified. (`T02` composes
  the capture/meeting pipelines; out of this task's own scope.)
- Do not touch `Work/Meetings/` — per `ADR-047` Context point 2, Meeting
  notes need no wipe at all; `T02`'s own wide-window `classify_recent_meetings`
  re-run satisfies Scenario 5 on its own.

---

## Tests

<!-- AC-01 is the only locked AC this task carries — the wipe-and-archive
half of Scenario 1. -->

**Manual verification steps:**

1. [REQ-SB-59-US-01-AC-01] Before running, record the real, current count of
   `.md` notes under `Work/Emails/` (`N`) and whether
   `.second-brain/processed_email_ids.json` /
   `.second-brain/conversation_index.json` currently exist, capturing their
   byte content if so. Call `wipe_legacy_email_notes()` (directly, or via
   `POST /poc/wipe-legacy-email-notes`). Confirm the response reports `N`
   notes moved. Confirm `Work/Emails/` now contains zero `.md` notes (a
   fresh `list_all_note_paths()`/glob check). Confirm, for at least 2
   spot-checked notes (or all of them if `N <= 2`), the archived copy under
   `.second-brain/migration_backup/<run-timestamp>/Emails/` is byte-for-byte
   identical to the original content captured before the run, and that any
   sibling `attachments/<slug>/` folder moved with it.
2. [REQ-SB-59-US-01-AC-01] Confirm `processed_email_ids.json` and
   `conversation_index.json` no longer exist at their canonical
   `.second-brain/` paths after the run. Confirm both now exist, byte-for-byte
   identical to the content captured in step 1, under
   `.second-brain/migration_backup/<run-timestamp>/` — archived, not left
   dangling and not deleted.
3. Non-AC idempotency sanity check: call `wipe_legacy_email_notes()` a
   second time immediately after. Confirm the response reports zero notes
   moved and zero state files archived (nothing left to move), with no
   error — confirms `ADR-047`'s "nothing left to act on" idempotency
   mechanism holds for this function.
4. Non-AC safety check: confirm no note or attachment file that existed
   under `Work/Emails/` before step 1 is missing anywhere afterward — every
   one is either still present (should be none) or accounted for inside
   `.second-brain/migration_backup/<run-timestamp>/Emails/` — nothing was
   silently lost.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-59-US-01-AC-01` verified: `Work/Emails/` contains zero notes
      after a real run; every pre-migration note (and sibling attachments)
      is archived byte-for-byte under `migration_backup/<run-timestamp>/Emails/`
- [x] `REQ-SB-59-US-01-AC-01` verified: `processed_email_ids.json` and
      `conversation_index.json` are archived (not deleted, not left in
      place) out of their canonical paths
- [x] Idempotent rerun confirmed (zero-op on a clean second call)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Recapturing Outlook history — `T02`.
- Any Customer note work / `ESC-046` resolution — `T03`.
- Touching `Work/Meetings/` in any way — never in scope for this function
  (`ADR-047` Context point 2).

---

## Context / Notes

`Implementation/Architecture/architecture.md` → "Vault Migration — One-Time
Full Vault Migration to the New Knowledge Model (REQ-SB-59, see ADR-047)" is
the full architectural reasoning this task implements. `ADR-047` Decision 2
is the archive-not-delete mechanism; Context point 1 is why archiving
`processed_email_ids.json` is load-bearing, not merely tidy (leaving it in
place would make `T02`'s own recapture silently process zero emails, since
Outlook `EntryID`s are stable across a same-mailbox rerun and
`run_email_capture_pipeline`'s own `email["id"] in already_processed` check
is unchanged).

**`<run-timestamp>` is this function's own concern** — generate a single UTC
timestamp (e.g. `datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")`) once
per call and reuse it for every move inside that same call, so a single
invocation's own archived notes and archived JSON stores land under the
same `<run-timestamp>/` directory. A second, later call (e.g. `T03`'s own
`regenerate_customer_notes()`) generates its own, independent timestamp —
there is no shared "migration run" object across the three functions; each
is independently operator-triggered.

**No functional dependency on `T02`/`T03`** — this function only touches
`Work/Emails/` and the two named `.second-brain/` JSON stores, entirely
disjoint from `T02`'s Outlook reads/Thread-Meeting writes and `T03`'s
`Work/Customers/` scope. `T02` DOES depend on this task (see `T02`'s own
`depends_on`) because its recapture would silently no-op without this
task's own dedup-gate reset.

---

## Implementation Log

**2026-08-18 — Built and verified against the real, live vault
(`<OPERATOR_VAULT_OLD>`).**

Created `app/business/vault_migration.py` (new module) with
`wipe_legacy_email_notes() -> dict`, returning
`{"run_timestamp", "emails_moved": list[dict], "state_files_archived": list[dict]}`.
Added `POST /poc/wipe-legacy-email-notes` to `app/api/email_poc_router.py`,
matching the existing `/poc/backfill-tags` thin-wrapper shape (summarizes
`emails_checked`/`emails_archived` from the raw `results` list). No other
file touched; `vault_writer.py`/`email_pull.py`/`email_capture_pipeline.py`/
`meeting_classification.py` all left unmodified per Constraints.

**[REQ-SB-59-US-01-AC-01] — VERIFIED, pass.** Real run against the live
vault: baseline `N = 226` `.md` notes under `Work/Emails/` (confirmed via
`Get-ChildItem`), `processed_email_ids.json` (49836 bytes) and
`conversation_index.json` (30277 bytes) both present at their canonical
`.second-brain/` paths pre-run. Called `wipe_legacy_email_notes()` directly
(Python, in-process — equivalent to the endpoint, same function body).
Response: `run_timestamp="20260818T055046Z"`, `emails_moved` reports 226
entries, all `status: "archived"`, matching `N`. Post-run `Work/Emails/`
does not exist at all (folder itself removed once empty, via
`remove_empty_dirs`) — zero `.md` notes. Spot-checked 3 notes (2 arbitrary +
1 with a sibling `attachments/<slug>/` folder,
`2026-07-21-FW- Compass x E& Business Case Clarifications-92F40000.md`) via
SHA-256: every archived copy under
`.second-brain/migration_backup/20260818T055046Z/Emails/` is byte-for-byte
identical to its pre-run hash; the sibling attachment file
(`Product Exhibit 2 - Compass Core42 210726.docx`) moved intact alongside
its note. Full-count safety check: archived `.md` count = 226 (matches `N`),
archived `attachments/` subdirectory count = 23 (matches the pre-run
baseline count of attachment folders) — nothing lost.

**[REQ-SB-59-US-01-AC-01] — VERIFIED, pass.** `processed_email_ids.json`/
`conversation_index.json` confirmed absent from their canonical
`.second-brain/` paths post-run. Both now exist under
`.second-brain/migration_backup/20260818T055046Z/` with SHA-256 hashes
identical to their pre-run baseline (`C0998646...` /
`A10AB9CA...`) — archived, not left dangling, not deleted.

**Idempotency (non-AC sanity check) — pass.** Immediate second call:
`emails_moved` = `[]` (zero entries), both state files report
`status: "not_found"`, response returned cleanly with no exception —
`ADR-047`'s "nothing left to act on" idempotency mechanism confirmed live.

**Safety check (non-AC) — pass.** Every one of the 226 original notes and
all 23 attachment folders accounted for post-run, either under
`migration_backup/.../Emails/` (all of them) or nowhere else — none
silently lost.

**Assumption logged (scope-internal judgement call):** the task's own
`## Tests` step 1 called for "at least 2 spot-checked notes" — 3 were
spot-checked (2 arbitrary + the 1 known attachment-bearing note) for
stronger coverage of the attachments-move path; this is a superset of the
locked requirement, not a deviation from it.

No new dependency, no shared-interface change, no ADR deviation — matches
`ADR-047`/architecture.md exactly as scoped. `status: Ready -> Done`.
