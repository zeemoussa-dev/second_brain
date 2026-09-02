---
id: REQ-SB-87-US-02-T03
title: Migrate capture_attachments.py / capture_file_link.py / link_person_to_thread.py onto vault_manager.py
parent_story: REQ-SB-87-US-02
requirement_id: REQ-SB-87
type: backend
status: Done
gate: flagged
gate_reason: "One disclosed, non-blocking scope-internal judgement call needs human spot-check: a real bug was found and fixed live during verification, before shipping -- an initial draft passed '## '-prefixed section names to modify_section/get_section_content, which silently disabled modify_section's own per-caller access check (exact-match against Template.json's BARE section name) rather than raising. Fixed to the bare form, matching apply_thread_review.py's own convention. See Implementation Log and MEMORY.md Constraint entry (2026-09-02, second entry)."
phase: P1
depends_on: [REQ-SB-87-US-02-T02]
created: 2026-09-01
updated: 2026-09-02
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

- [x] `## Related`/`## Files` accumulation for all three scripts goes
      through `vault_manager.modify_section`, correct caller identity each
- [x] `write_file_companion`/`write_file_link_companion`/
      `ensure_bare_person_note` unchanged
- [x] Per-caller restrictions enforced (only the declared caller may write
      its own section; `## Personal Notes`/`## Actions` refused to all
      three)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

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

**What was built:** `link_person_to_thread.py`, `capture_attachments.py`,
and `capture_file_link.py` migrated per the task's End-State. Thread
resolution in all three now goes through `vault_manager.find_by_id(vault_path,
conversation_id, note_name="Threads")` instead of `vault_lib.
resolve_thread_directory`. `link_person_to_thread.py`'s own `## Related`
accumulation and `capture_attachments.py`'s/`capture_file_link.py`'s own
`## Files` accumulation now go through `vault_manager.get_section_content`
/`vault_manager.modify_section(..., caller=...)` instead of `vault_lib`'s
`insert_body_section_if_missing`/`read_body_section`/`replace_body_section`
(directly, for `link_person_to_thread.py`) / `link_file_to_thread` (for the
other two) — caller identity is one bare string per script
(`"link_person_to_thread"`, `"capture_attachments"`, `"capture_file_link"`),
matching the Thread template's own `allowed_callers` declarations
(`REQ-SB-87-US-01-T05`) and the established one-identity-per-script
convention (`REQ-SB-87-US-01-T04`). `ensure_bare_person_note`,
`write_file_companion`, and `write_file_link_companion` stay entirely
hand-written, byte-for-byte unchanged.

**Real bug found and fixed live, before shipping (never landed in a
"Done" state with the bug present):** an initial draft passed
`"## "`-prefixed section names (`section="## Related"`, `section="##
Files"`) to `modify_section`/`get_section_content` — copied directly from
the task's own decomposer-authored Tests prose and `REQ-SB-87-US-01-T05`'s
own illustrative Test steps, both of which use the prefixed form. Reading
`vault_manager.py`'s own source directly (not just its docstrings) showed
this is WRONG: `_require_machine_write`'s own `_section_access`/
`_section_allowed_callers` match the caller-supplied `section` argument
against `Template.json`'s `root.sections[].name` field via exact string
equality, and that field is the BARE name (confirmed against the real,
live `thread/Template.json`: `"name": "Related"`, `"name": "Files"`, no
`"## "` prefix) — `get_section_content`/`_set_section_content` are NOT
symmetric (they route through `_section_header()`, which tolerates
either form), so the bug was invisible on reads and only manifested as a
SILENT security hole on writes: the prefixed form finds no declared
entry, falls through to the undeclared-section default
(`access="machine_write"`, `allowed_callers=None` — open to ANY caller),
and the write still succeeds with no error. Caught live during
verification (the wrong-caller-refusal check did not actually raise on
the first pass); fixed by switching to the bare form
(`section="Related"`/`"Files"`), matching `apply_thread_review.py`'s own
already-`Done` real call-site convention and `test_vault_manager.py`'s
own established convention. Generalized as a `MEMORY.md` Constraint entry
(2026-09-02, second entry) so no future `modify_section`/`create` call
site repeats this. Not an escalation (stayed entirely within this task's
own three files, caught and fixed before the task's own first `Done`
state) — logged here and in `MEMORY.md` for human spot-check, per this
project's own established "log it, don't block, flag the task's gate"
pattern (`SPRINT-037`/`SPRINT-048`, and `T02`'s own identical-shape
precedent this same story).

**Interruption note:** this build was interrupted mid-task by a machine
restart after the code edits were already on disk but before live
verification/completion (task still showed `status: Ready`). Per the
coordinator's explicit instruction, the pre-restart partial verification
was NOT trusted — all three files were re-read fresh from disk and
confirmed complete/correct against the task's own End-State, any leftover
scratch-vault artefacts from the interrupted run were located and removed
(`C:\scratch-sb87t03\` and a leftover driver-script copy under the
session scratchpad), and the ENTIRE live verification below was re-run
from a freshly-rebuilt scratch vault, for real, after the restart.

**Live verification (real scratch vault, distinct `--vault-path`, never
the live vault — `C:\scratch-sb87t03\vault`, seeded with a real,
byte-identical copy of the live `thread/Template.json`, removed after
verification completed; a second small scratch vault,
`C:\scratch-sb87t03b\`, used for one supplementary check, also removed
afterward):** a real Thread + first RawMessage created via the
already-`Done`, unmodified `ingest_email.py` (the closest-to-real way a
Thread exists before these three scripts ever run against it), then the
three migrated scripts run directly (both via direct Python import of the
real, unmodified module AND, for `link_person_to_thread.py`, via its real
CLI entry point) against it.

- `[REQ-SB-87-US-02-AC-04]` **PASS** (Test 1 — `link_person_to_thread.py`):
  a real sender (`bob.related.rerun@example.com`) linked into `## Related`
  on the first call (`linked: true`); the SAME sender on a second call was
  a correct idempotent no-op (`linked: false, reason: "already linked"`),
  confirmed exactly one `## Related` line for that sender on disk after
  the re-run (no duplicate). `ensure_bare_person_note`'s own dedup-key/
  ignore-list/GAL-field business logic confirmed untouched (Person note's
  real on-disk shape matched exactly: `type`, `email`, `tags: ["kind/
  person"]`, blank department/role/company as supplied). A real CLI call
  (`python link_person_to_thread.py --vault-path ... --conversation-id
  ... --sender-name "Carol CLI" --sender-email carol.cli@example.com`)
  confirmed the subprocess entry point still works, printing the correct
  `{"linked": true, ...}` JSON.
- `[REQ-SB-87-US-02-AC-04]` **PASS** (Test 2 — `capture_attachments.py`):
  a real attachment (genuine byte payload, not a stub) captured via
  `capture_attachments.py`; `## Files` on disk gained the correct
  wikilink; the real attachment bytes under `files/<slug>/notes.txt`
  confirmed byte-for-byte identical to the original content; the temp
  file was removed after capture, matching today's real contract.
- `[REQ-SB-87-US-02-AC-04]` **PASS** (Test 2 — `capture_file_link.py`):
  a URL-only file link captured via `capture_file_link.py`; companion
  note created on disk containing the real URL; `## Files` gained a
  second, correct wikilink (now 3 entries total, alongside the two
  `capture_attachments.py` calls below); re-running with the identical
  label/URL was a correct idempotent no-op on `## Files` (no duplicate
  line).
- **Explicit re-verification of `REQ-SB-87-US-02-T02`'s own flagged
  frontmatter-fence-vs-raw-attachment-bytes risk**, the same way `T02`
  verified its own fix: an engineered collision case — a real attachment
  whose ORIGINAL filename ends in `.md` (`project-scaffold.md`, genuine
  markdown byte content, deliberately no frontmatter fence) — captured via
  `capture_attachments.py`. Confirmed the raw attachment bytes on disk
  matched the original content exactly immediately after capture (no
  synthetic frontmatter injected), confirmed the file still had no
  frontmatter fence, and confirmed the SEPARATE real companion note (ends
  `....md.md`, at the same directory level) DOES correctly carry a real
  frontmatter fence — i.e. `write_file_companion`'s own existing,
  unchanged dual-file behavior is intact. Then, after several FURTHER
  `## Related`/`## Files` writes against the Thread's own concept note
  (the sender link, the URL-only file link, and its idempotent re-run),
  re-confirmed the raw collision attachment bytes were STILL
  byte-for-byte unchanged — direct, positive proof this risk does not
  reproduce here: unlike `rename_thread.py`'s own companion-backlink
  loop (which globs `files/**/*.md` and can match the raw bytes file),
  none of these three scripts ever glob over `files/`; they only ever
  write the Thread's own single concept note (resolved by `id`) and the
  specific files `write_file_companion`/`write_file_link_companion`
  themselves explicitly name.
- `[REQ-SB-87-US-02-AC-04]` **PASS** (Test 3 — wrong-caller refusal):
  `caller="link_person_to_thread"` attempting to write `## Files`,
  `caller="capture_attachments"` and `caller="capture_file_link"` each
  attempting to write `## Related`, were all refused with a real, explicit
  `VaultManagerError` naming both the section and the refused caller;
  `## Related`/`## Files` content confirmed byte-for-byte unchanged after
  all three refused attempts (never a partial write). A positive control
  (the CORRECT caller, `link_person_to_thread`, writing `## Related`) was
  confirmed to still succeed immediately after, proving the refusals above
  are real access-control enforcement, not a broken engine. Supplementary
  check (not one of this task's own named Tests steps, but claimed by the
  Acceptance Criteria's own "`## Actions` refused to all three" wording):
  all three script caller identities individually attempting to write
  `## Actions` were also refused (`allowed_callers: ["apply_thread_
  review"]`, none of these three), content confirmed to stay empty.
- `[REQ-SB-87-US-02-AC-07]` **PASS** (Test 4 — `## Personal Notes`
  refusal): a disposable throwaway script (never a real Skill entry
  point) attempted `modify_section(..., section="Personal Notes", caller=
  ...)` for each of `link_person_to_thread`/`capture_attachments`/
  `capture_file_link`, and again with `caller=None` — every one refused
  with a real, explicit `VaultManagerError` (`"section 'Personal Notes'
  is 'human_only' ... no automated write is allowed here"`), unconditional
  regardless of caller identity; `## Personal Notes` confirmed to stay
  empty throughout.
- **Migration completeness self-check:** confirmed by direct source
  inspection (not just behavior) that none of the three migrated scripts'
  own function bodies call `vault_lib.resolve_thread_directory`,
  `vault_lib.insert_body_section_if_missing`, `vault_lib.
  read_body_section`, `vault_lib.replace_body_section`, or `vault_lib.
  link_file_to_thread` any more — the per-caller enforcement above is
  genuinely coming from the engine's own `Template.json`-driven
  `_require_machine_write`, not a leftover of `vault_lib.py`'s own retired
  `_CALLER_ALLOW_LISTS` guard (which these three scripts no longer import
  for that purpose at all).

**Scratch artefacts cleaned up:** `C:\scratch-sb87t03\` and
`C:\scratch-sb87t03b\` (both scratch vaults, driver scripts, temp
attachment files) removed after verification completed — nothing left
behind outside this repo. (A deep-scratchpad copy of the verification
driver, left behind by the interrupted pre-restart run, was also found
and removed.)

**Escalations / review-queue items written by this task:** none new — the
section-name bug above was caught and fixed entirely within this task's
own `## Files to Modify`, before the task ever reached a `Done` state
with the bug present, and did not require any file, dependency, or
interface outside this task's own scope. Logged here and in `MEMORY.md`
for human spot-check (not blocking), consistent with `T02`'s own
identical-shape precedent earlier in this same story. `REVIEW-QUEUE.md`
updated with a pointer to this task alongside the still-open
`REQ-SB-87-US-02-T01`/`T02` spot-check items.

**Task marked `Done`.** This task's own locked ACs (`AC-04` in full;
`AC-07`'s `## Personal Notes` half, the only part of `AC-07` this task's
own three scripts are responsible for) verified live with a real,
positive result, re-run for real after a mid-task machine-restart
interruption per the coordinator's explicit instruction not to trust any
pre-restart state. `gate: flagged` — one disclosed, non-blocking
scope-internal judgement call (the section-name bug, found and fixed
before shipping) needs human spot-check.
