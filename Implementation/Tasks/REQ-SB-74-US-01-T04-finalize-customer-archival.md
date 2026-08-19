---
id: REQ-SB-74-US-01-T04
title: vault_writer.move_okf_directory() + finalize_customer_archival(payload) — archive, never delete
parent_story: REQ-SB-74-US-01
requirement_id: REQ-SB-74
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-74-US-01-T03]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-74-US-01-T04 — `move_okf_directory()` + `finalize_customer_archival(payload)`

## Parent Story

- Story: [[REQ-SB-74-US-01]] — `../UserStories/REQ-SB-74-US-01-customer-backfill-thread-routing-and-noise-reconciliation.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-74 *Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Customer Backfill" → "`vault_writer.move_okf_directory()`" (`ADR-055` Decision 4)

---

## Objective

Build the new generic, cross-parent OKF-directory move primitive and the deferred-write handler that uses it: on approval of an archival-candidate proposal, move the whole Customer folder to `Work/Archive/Customers/`, content byte-for-byte unchanged, never deleted.

---

## Starting State → End State

**Before / Inputs:**
- No existing primitive moves a whole OKF-conformant directory to a DIFFERENT parent: `rename_thread_directory` only handles a same-parent slug rename (and additionally renames the concept file inside); `move_note_and_attachments` only moves a single flat note plus its sibling `attachments/<slug>/` folder, not a 4-file OKF directory (`index.md`/`<slug>.md`/`log.md`/`captures.md`).
- `Work/Archive/Customers/` already exists — `vault_provisioning.provision_vault_base` (`REQ-SB-70-US-01`) already idempotently creates `Work/Archive/{Opportunities,Customers,Resources}/` unconditionally. No new directory-provisioning code needed.

**After / Outputs:**
- New `vault_writer.move_okf_directory(source_directory: Path, target_parent_directory: Path) -> Path` — generic, not Customer-specific (named/placed alongside `okf_directory_paths`, shared across Customer/Project the same way that function already is): mirrors `rename_thread_directory`'s own atomic-move-plus-refuse-to-overwrite discipline, WIDENED to a different parent directory, NARROWED by NOT renaming the concept file inside — the directory's own name/slug is unchanged, only its location moves, so every file inside (plus any nested `People/` subdirectory) is moved byte-for-byte, untouched, in one atomic `Path.rename()`. Raises `FileExistsError` on a genuine collision at the target, never silently overwrites. Returns the new directory path.
- New `librarian_housekeeping.finalize_customer_archival(payload: dict) -> dict`: calls `vault_writer.move_okf_directory(Path(payload["source_directory"]), settings.vault_path / "Work/Archive/Customers")`. Returns `{"customer": str, "new_directory": str, "message": str}` (a `"message"` key, per the router's own fallback-`KeyError` risk if omitted — see `T02`'s own identical note).

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add `move_okf_directory`.
- `src/backend/app/business/pipelines/librarian_housekeeping.py` — add `finalize_customer_archival`.

---

## Constraints

- Inherits from parent story.
- Archive, never delete — the folder is moved, never removed; every file's content stays byte-for-byte unchanged (by construction, a directory `Path.rename()`, never a per-file copy).
- `move_okf_directory` must NOT rename the concept file or any file inside the directory — only its location (parent) changes.
- Raise `FileExistsError` on a genuine target collision, never silently overwrite — mirrors `rename_thread_directory`'s own discipline.
- `target_parent_directory` for this story's own use is `settings.vault_path / "Work/Archive/Customers"`, already provisioned — no new directory-provisioning code.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-74-US-01-AC-05]` Direct Python-shell check against the real vault: pick (or construct, disposably) a real Customer OKF folder with zero real Thread matches. Capture a content hash of every file inside it before the move. Hand-construct a payload `{"customer": <name>, "source_directory": <str>}` and call `finalize_customer_archival(payload)` directly. Confirm the whole folder now exists under `Work/Archive/Customers/<same-slug>/`, every one of its files present with IDENTICAL content hashes to their pre-move bytes, and confirm the original `Work/Customers/<slug>/` location no longer exists (moved, not copied) and nothing was deleted (the folder genuinely exists at the new location, inspectable).
2. Confirm the collision discipline: attempt `move_okf_directory` a second time with a target that already exists (e.g. re-run against the same source/target pair, or construct a genuine name collision); confirm a real `FileExistsError` is raised and nothing is overwritten.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `move_okf_directory` moves a whole OKF directory to a new parent, content byte-for-byte unchanged, concept file name unchanged
- [x] `move_okf_directory` raises `FileExistsError` on a genuine target collision, never silently overwrites
- [x] Approving an archival-candidate proposal moves the real folder to `Work/Archive/Customers/`, never deletes it
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `propose_customer_archival_candidates()` itself — `T03`.
- `_APPROVAL_HANDLERS` registration — `T05`.
- Declining an archival candidate (Scenario 7) — verified in `T05`, a property of the existing, unmodified decline endpoint (this handler is never called on decline).
- A future "un-archive/restore" operation — named by `ADR-055` as a natural future extension point, not built here.

---

## Context / Notes

Verified here by calling `finalize_customer_archival(payload)` directly against a real or hand-constructed payload — the real end-to-end approve round trip is exercised again in `T06`'s own full backfill run.

---

## Implementation Log

Built `vault_writer.move_okf_directory(source_directory, target_parent_
directory)` (new, `app/data_access/vault_writer.py`, placed beside
`okf_directory_paths`) and `librarian_housekeeping.finalize_customer_
archival(payload)` (new, `app/business/pipelines/librarian_housekeeping.
py`), exactly per `ADR-055` Decision 4.

**`[REQ-SB-74-US-01-AC-05]` PASS — real move.** Used `T03`'s own real
archival-candidate `"Twitter"` (`Work/Customers/Twitter/`, confirmed noise
per the story's own Context). Captured SHA-256 content hashes of all 4
real files (`captures.md`, `index.md`, `log.md`, `Twitter.md`) before the
move. Called `finalize_customer_archival(payload)` directly. Result: real
folder now exists at `Work/Archive/Customers/Twitter/`, same 4 filenames,
EVERY file's content hash identical before/after (programmatically
asserted, all matched). Confirmed the original `Work/Customers/Twitter/`
location no longer exists (`.exists()` → `False`) — a real move, not a
copy; nothing deleted (the folder genuinely exists, inspectable, at the
new location).

**Collision discipline verified separately** (disposable synthetic
fixtures, never real Customer data): created a throwaway OKF-shaped source
directory and a colliding directory already sitting at the computed target
location, called `move_okf_directory` — a real `FileExistsError` was
raised, source and the pre-existing target both confirmed untouched
afterward. Scratch fixtures cleaned up immediately after the assertion.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired; mechanism follows
`ADR-055`/architecture.md directly, no deviations.
