---
id: REQ-SB-87-US-02-T03
title: Migrate capture_attachments.py / capture_file_link.py / link_person_to_thread.py onto vault_manager.py
parent_story: REQ-SB-87-US-02
requirement_id: REQ-SB-87
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-02-T02]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-02-T03 — Migrate capture_attachments.py / capture_file_link.py / link_person_to_thread.py onto vault_manager.py

## Parent Story

- Story: [[REQ-SB-87-US-02]] — `../UserStories/REQ-SB-87-US-02-email-thread-capture-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Migrate the section-write half of `capture_attachments.py`,
`capture_file_link.py`, and `link_person_to_thread.py` onto
`vault_manager.py`'s `modify_section`, enforcing the Thread template's own
per-caller access declarations in place of `vault_lib.py`'s
`_CALLER_ALLOW_LISTS`/`_HUMAN_OWNED_HEADERS` guard.

---

## Starting State → End State

**Before / Inputs:**
- `link_person_to_thread.py` (read directly, 2026-09-01):
  `ensure_bare_person_note` (untouched), then
  `insert_body_section_if_missing`/`read_body_section`/
  `replace_body_section(..., "## Related", caller="link_person_to_thread.
  link_person_to_thread")` — idempotent (checks the wikilink isn't already
  present before appending).
- `capture_attachments.py`: resolves the Thread directory, then
  `vault_lib.write_file_companion(...)` (real byte-level file write — stays
  hand-written, a DIFFERENT mechanism than a note section) followed by
  `vault_lib.link_file_to_thread(directory, wikilink, caller="capture_
  attachments.capture_attachments")` to accumulate the companion's own
  wikilink into `## Files`.
- `capture_file_link.py` (not yet read in full — read the real current file
  directly before editing; expected, by its own module/caller-identity
  naming precedent, to mirror `capture_attachments.py`'s own `## Files`
  accumulation shape for a plain external link rather than a captured
  file's bytes).

**After / Outputs:**
- `link_person_to_thread.py`'s own `## Related` accumulation goes through
  `vault_manager.get_section_content`/`vault_manager.modify_section(...,
  section="## Related", mode="replace", caller="link_person_to_thread")` —
  the idempotent "already linked" check is preserved by reading the
  current content first, exactly as today.
- `capture_attachments.py`'s and `capture_file_link.py`'s own `## Files`
  accumulation goes through the SAME `modify_section` pattern, `caller=
  "capture_attachments"` / `caller="capture_file_link"` respectively —
  matching the Thread template's own declared `allowed_callers` for that
  section (`REQ-SB-87-US-01-T05`).
- `write_file_companion`/`write_file_link_companion` (real byte-level file
  writes) stay hand-written, unchanged — per the parent story's own
  Constraints, these are explicitly named as staying as-is.
- `ensure_bare_person_note` stays hand-written, unchanged.

---

## Files to Modify

- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/link_person_to_thread.py`
- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/capture_attachments.py`
- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/capture_file_link.py`

---

## Constraints

- Inherits from parent story.
- `write_file_companion`/`write_file_link_companion`,
  `ensure_bare_person_note`, `person_note_dedup_key`/
  `find_person_note_path` stay hand-written, byte-for-byte unchanged.
- Every existing caller-to-section write restriction still holds for THIS
  Skill's own five scripts: only `link_person_to_thread` may write
  `## Related`; only `capture_attachments`/`capture_file_link` may write
  `## Files`; `## Personal Notes` is refused to all five; `## Actions` is
  likewise refused to all five (the one narrow exception is a DIFFERENT
  Skill's own caller, `REQ-SB-87-US-05`, never one of these three scripts).
- Verify against the SAME scratch vault/100-email sample `T01`/`T02` used —
  never the live vault for this task.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`):**
1. `[REQ-SB-87-US-02-AC-04]` Run `link_person_to_thread.py` against a
   real Thread + sender from the scratch sample; confirm the sender's
   Person note is ensured (dedup-key/ignore-list/GAL fields unchanged) and
   its wikilink is accumulated into `## Related`. Run it again for the SAME
   sender/Thread; confirm the idempotent "already linked" no-op.
2. `[REQ-SB-87-US-02-AC-04]` Run `capture_attachments.py` (if the scratch
   sample has a real attachment) or `capture_file_link.py` against a real
   Thread; confirm the companion note/link is created and its wikilink is
   accumulated into `## Files`, with the underlying byte/link-write logic
   unchanged.
3. `[REQ-SB-87-US-02-AC-04]` Confirm each of the three scripts' own caller
   identity is exactly what the Thread template's `allowed_callers`
   expects (`link_person_to_thread`, `capture_attachments`,
   `capture_file_link`) — a write from the WRONG one of these three against
   the OTHER's own exclusive section (e.g. `link_person_to_thread` writing
   `## Files`) is refused.
4. `[REQ-SB-87-US-02-AC-07]` Attempt (via a disposable throwaway script,
   not a real Skill entry point) a `modify_section(..., section="##
   Personal Notes", caller="link_person_to_thread")` call through the
   migrated code path; confirm it is refused with a real, explicit
   `VaultManagerError` — never silently allowed.

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `## Related`/`## Files` accumulation for all three scripts goes
      through `vault_manager.modify_section`, correct caller identity each
- [ ] `write_file_companion`/`write_file_link_companion`/
      `ensure_bare_person_note` unchanged
- [ ] Per-caller restrictions enforced (only the declared caller may write
      its own section; `## Personal Notes`/`## Actions` refused to all
      three)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `ingest_email.py`/`rename_thread.py` — `T01`/`T02`.
- `run_full_capture.py`/`run_delta_capture.py` — `T04`.
- Any real-vault run or cutover — `T05`.

---

## Context / Notes

Read `capture_file_link.py`'s own real current content directly before
editing — this task file's own description of it is inferred from its
sibling `capture_attachments.py` and its own caller-identity naming
precedent (`vault_lib.py`'s `_CALLER_ALLOW_LISTS`), not yet independently
confirmed by a direct read at decomposition time.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
