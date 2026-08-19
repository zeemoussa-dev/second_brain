---
id: BUGFIX-05-US-01-T02
title: Live-verify AC-02 (directory-shaped Thread never orphaned) via the real process_staged_email capability
parent_story: BUGFIX-05-US-01
requirement_id: BUG-026
type: backend
status: Done
gate: flagged
gate_reason: "Scope-internal judgement call, not an out-of-scope event: the coder discovered mid-task that the already-running backend server process predated T01's code changes (started without --reload), causing this task's FIRST verification attempt to run against the stale, pre-fix code path and briefly reproduce BUG-026's own orphaning failure live, for real, against the real vault. Immediately detected, contained (confirmed via direct filesystem check that exactly one real Thread was affected), and repaired byte-identical from a pre-test backup before any further action. Server restarted (confirmed running the corrected code) and the verification re-run cleanly to a genuine PASS. Full incident timeline in this task's own Implementation Log below. Flagged per Pipeline.md's own 'scope-internal judgement calls ... log them ... they make the task gate: flagged' convention, for human spot-check given this touched real, live vault data even though fully self-resolved."
depends_on: [BUGFIX-05-US-01-T01]
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-05-US-01-T02 — Live-verify AC-02 (directory-shaped Thread never orphaned) via the real process_staged_email capability

## Parent Story

- Story: [[BUGFIX-05-US-01]] — `../UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md`
- Requirement: `BUGS.md` → `BUG-026` (bugfix story; no PRD requirement anchor)

---

## Objective

Prove, live, against the real configured vault (`VAULT_PATH`) and the
real `process_staged_email` capability endpoint, that `T01`'s rewire
closes `AC-02`: a new message arriving for an already-migrated,
directory-shaped Thread with real `messages/`/`files/` content is
threaded into that SAME Thread, and its `messages/`/`files/` subfolders
are never left behind or disconnected from the concept file.

**This task does NOT verify `AC-01`** (the flat-shape duplication facet —
now locked, but verified separately in `T04`, since `T04` depends on
`T03`'s own `resolve_thread_directory` migration primitive, which this
task does not touch) **and does NOT flip `email-capture-pipeline`'s
working mode to `autonomous`** — `AC-02`'s own locked wording ties that
flip to "once this scenario AND Scenario 1 are both verified live," and
this task alone only ever verifies Scenario 2 (`AC-02`). Leave the
working mode `supervised`. The flip happens in `T04` (which depends on
this task), once `AC-01` is also confirmed PASS there. Do not improvise a
flip here — that is an explicit, disclosed hard boundary of this task,
not an oversight.

---

## Starting State → End State

**Before / Inputs:**
- `T01` is `Done` — `run_email_capture_pipeline()` now composes
  `capture_raw_thread_messages`/`synthesize_thread`, never invoking the
  old `StateGraph`/`thread_match_merge`.
- `email-capture-pipeline`'s working mode is currently `supervised`
  (`ESC-048`'s own protective measure, still in force).
- The real, configured vault (`VAULT_PATH`) has many real, already-
  migrated, directory-shaped Threads with real `messages/`/`files/`
  content — e.g. (confirmed present at decomposer time, 2026-08-19;
  re-confirm at verification time, since real capture continues to run
  in between): `Work/Threads/2026-08-16 FW- Presight Agent Academy Demo/`
  (`messages/` + `files/`), `Work/Threads/2026-07-28 Azerbaijan
  Engagement – Data Lake Opportunity & Core42 Participation/` (`messages/`
  + `files/`). Any real Thread with both a non-empty `messages/` and a
  non-empty `files/` subfolder is an equally valid candidate — pick
  whichever is real and current at verification time; do not assume the
  examples above still exist unchanged.

**After / Outputs:**
- One real, additional raw message note exists under the chosen Thread's
  own `messages/` directory.
- The chosen Thread's own concept file path, `messages/` directory
  (all pre-existing files), and `files/` directory (all pre-existing
  companions) are all confirmed unchanged in location — nothing moved,
  nothing disconnected.
- No second, duplicate Thread note exists anywhere in the vault for that
  same `conversation_id`.
- `[BUGFIX-05-US-01-AC-02]` recorded PASS or FAIL, with the real evidence,
  in this task's own Implementation Log.
- `email-capture-pipeline`'s working mode is STILL `supervised` (verify
  this explicitly as part of closing this task — it must not have
  changed).

---

## Files to Modify

None expected — this task calls the real, already-built `process_staged_
email` capability endpoint (`POST /agents/email-capture-pipeline/
schedules/process_staged_email/run-now`, `app/api/agent_schedules_
router.py`) and real, already-built read primitives only. If genuine
additional code is found to be needed live, that is an out-of-scope
escalation (`Implementation/Pipeline.md` hard rule 5) — do not improvise
a fix inside this verification-only task.

---

## Constraints

- Inherits from parent story (real, live vault — no fixture/test vault;
  no-data-loss is load-bearing, not a convenience).
- Must call the REAL capability endpoint (`POST /agents/email-capture-
  pipeline/schedules/process_staged_email/run-now`) to drive the actual
  processing under test — never a raw script that calls `synthesize_
  thread`/`run_email_capture_pipeline` directly and skips the real
  capability surface (the API-only verification constraint this story's
  own launch context named).
- Staging the precondition message MAY use the real, existing `email_
  staging.stage_email(email)` data-access primitive directly if no
  genuine new Outlook message for the chosen conversation arrives
  naturally within the verification window (disclosed substitute,
  mirroring `BUGFIX-03-US-01-T02`'s own established precedent) — this is
  legitimate because `stage_email` is the SAME real, production write
  primitive `pull_and_stage_emails` itself calls, writing the exact dict
  shape `outlook_com.list_recent_mail` produces; only the FETCH is
  substituted, never the PROCESSING under test. Any synthetic staged
  message must be clearly, visibly marked as verification content (e.g.
  subject prefixed `[BUGFIX-05-US-01-T02 verification]`) so it can never
  be mistaken for real correspondence if cleanup is somehow incomplete.
- Must NOT flip `email-capture-pipeline`'s working mode — verify it is
  still `supervised` both before and after this task's own real capture
  call.
- Must back up the chosen Thread's own concept-file content and a listing
  of its `messages/`/`files/` subfolders BEFORE inducing the real capture,
  and restore the concept file to its byte-identical pre-task content
  afterward (a real `## Summary` regeneration from `synthesize_thread` is
  an expected, legitimate side effect of a genuine new message — but any
  verification-induced change must be reverted once the AC is proven, not
  left as permanent noise in the user's real vault) — mirrors this
  project's own established "back up real production state, test, then
  restore" `Implementation/Learnings.md` pattern (`SPRINT-030`). The one
  exception: a genuinely new raw message note this task's own precondition
  legitimately creates is real Stage-1 output (write-once, per `raw_
  message_capture.py`'s own contract) — if it is synthetic verification
  content (not a real email), delete it as part of cleanup; if it is a
  real, naturally-arrived email, leave it (it is real user data, not
  verification noise).

---

## Tests

<!-- AC-02 is the only locked AC verified in this task. AC-01 is not
locked and has no verification step here or anywhere in this story's
current task set — see the story's own Notes / ESC-055. -->

**Manual verification steps (live against the real configured vault —
`VAULT_PATH`; real backend server running):**

1. **[BUGFIX-05-US-01-AC-02]** Confirm `email-capture-pipeline`'s current
   working mode is `supervised` (`GET /agents/email-capture-pipeline` or
   the agents list endpoint) — record this as the starting state.
   Identify a real, directory-shaped Thread in the vault with a real,
   non-empty `messages/` directory AND a real, non-empty `files/`
   directory (see `## Starting State` above for known-good candidates as
   of decomposer time; re-confirm freshly at verification time). Record
   its own `conversation_id` (from the concept file's own frontmatter),
   its concept-file path, and a full listing (filenames) of its
   `messages/` and `files/` subfolders — this is the backup/baseline.
2. Arrange a new staged message for that SAME `conversation_id` — prefer
   a real, newly-arrived Outlook message in that conversation if one
   exists within the verification window; otherwise use the disclosed
   `email_staging.stage_email(...)` substitute per this task's own
   Constraints (a real dict shape, same `conversation_id`, a clearly
   verification-marked subject, a real, distinct `id`/message id, a
   `received` timestamp later than every existing message in that
   Thread).
3. Call the REAL capability endpoint: `POST /agents/email-capture-
   pipeline/schedules/process_staged_email/run-now`. Confirm the response
   is a real, honest result (not an error) and that it reflects one
   thread updated for the chosen `conversation_id` (per `T01`'s own new
   per-Thread return shape).
4. **[BUGFIX-05-US-01-AC-02]** After the run completes, confirm directly:
   - the SAME concept file (identical path to step 1's baseline) now
     contains the new message's own content reflected in a regenerated
     `## Summary` — the Thread was UPDATED in place, not replaced;
   - the Thread's own `messages/` directory now contains exactly one
     additional raw message note beyond step 1's baseline listing, and
     every pre-existing message note from the baseline is still present,
     unchanged, at the SAME path;
   - the Thread's own `files/` directory is UNCHANGED from step 1's
     baseline listing — every pre-existing companion file/note still
     exists at the SAME path, none moved, none disconnected;
   - no second, duplicate Thread note exists anywhere under
     `Work/Threads/` for this same `conversation_id` (search the vault
     directly for the `conversation_id` string, mirroring `ESC-055`'s own
     verification technique).
5. Confirm `email-capture-pipeline`'s working mode is STILL `supervised`
   (re-check via the same endpoint as step 1) — this task must not have
   changed it.
6. Cleanup: if step 2 used the synthetic `stage_email` substitute, delete
   the resulting raw message note it produced and revert the concept
   file's own content/frontmatter to a byte-identical copy of step 1's
   backup (confirm via direct string/byte comparison, not just visual
   inspection) — restoring the real vault to its pre-task state, mirroring
   `BUGFIX-03-US-01-T02`'s own established real-vault cleanup precedent.
   If step 2 used a genuine, naturally-arrived real email, no reversion is
   needed (real content stays).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `[BUGFIX-05-US-01-AC-02]` verified live and passing
- [ ] `email-capture-pipeline`'s working mode confirmed unchanged
      (`supervised`) before and after this task
- [ ] The real vault is left in its pre-task state (any synthetic
      verification content cleaned up; real content, if any arrived
      naturally, is left as-is)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- `AC-01` (flat-shape duplication) — locked, but verified separately in
  `T04`, not here. See `ESCALATIONS.md` → `ESC-055` (now `Resolved`).
- Flipping `email-capture-pipeline`'s working mode to `autonomous` — only
  happens once BOTH `AC-01` and `AC-02` are verified, per the story's own
  `AC-02` wording and Constraints — done in `T04`, which depends on this
  task.
- Any code change — this is a verification-only task (see `## Files to
  Modify`).
- Repairing the already-live duplicate `ESC-055` found
  (`ED0954959F6F4A4C88F9E2ACA3D7113A`) — a separate, not-yet-scoped
  reconciliation, per the story's own Non-Goals.

---

## Context / Notes

Full reasoning for why `AC-01` and the working-mode flip are excluded
from this task: the story's own `## Notes` (Decomposer pass) and
`ESCALATIONS.md` → `ESC-055`. `BUGFIX-03-US-01-T02`'s own Implementation
Log is a close precedent for the backup/verify/cleanup live-verification
shape used here.

---

## Implementation Log

**2026-08-19, coder.**

**INCIDENT (self-detected, self-contained, self-repaired — full disclosure):**
this task's FIRST attempt ran the real capability endpoint against a
backend server process that had been started EARLIER (before `T01`'s code
changes) with `python -m uvicorn app.main:app --port 8000` — no
`--reload` flag. Since a running Python process never re-reads edited
source files, that server was still running the OLD, pre-`T01`
`thread_match_merge` code path despite the source files on disk already
being fixed. Target chosen: `Work/Threads/2026-08-16 FW- Presight Agent
Academy Demo/` (`conversation_id 01D26A7530444A23803A002210620160`, real
`messages/` [2 files] + `files/` [2 companions]) — backed up in full
(concept-file content, `messages/`/`files/` listings) before inducing
capture, per this task's own Constraints. Staged one synthetic,
clearly-marked verification message, called the real `POST /agents/
email-capture-pipeline/schedules/process_staged_email/run-now` endpoint,
approved the resulting Pending Approval (`email-capture-pipeline` is
`supervised`, so `run-now` always proposes first) — **this is exactly
where `BUG-026`'s own orphaning failure mode reproduced live, for real**:
the OLD `thread_match_merge` (still running in that stale process) found
the existing directory-shaped Thread via `resolve_thread_note_path`, then
computed a flat, hash-suffixed rename target via its own still-live legacy
`thread_note_path_for`/`rename_thread_note` and moved ONLY the concept
file to `Work/Threads/FW- Presight Agent Academy Demo-2026-08-19-
a5c82286.md`, leaving the real `messages/`/`files/` subfolders behind,
disconnected, in the now-headless original directory — precisely `BUG-026`
Scenario 2/`AC-02`'s own failure description.

**Detected immediately** (the returned run_event message read "Done — 1
email(s) filed," the OLD wording — `T01`'s own updated wording is "N
thread(s) updated" — the first tell). **Contained**: killed the stale
server process; confirmed via `find -newermt` across all of `Work/
Threads/*.md` (flat files) and all top-level directories that exactly ONE
real Thread was affected (the Presight one) — no other real Thread was
orphaned or duplicated. Two OTHER real Threads (`8939F134E8E14C998478E34
026921ADF`, `227EC9A9963D4D9DB407CEFFE5D08F98`) were reprocessed by the
same stale-code dispatch (their own real emails had been independently
re-staged by the live server's own "Missed-run catch-up" `pull_email`
schedule during this session) but directly inspected and confirmed
UNAFFECTED — both concept files remained correctly in place, content
clean, matching this coder's own prior legitimate `T01`-testing state; no
repair needed for either. **Repaired**: restored the Presight Thread's
concept file byte-identical from the pre-test backup, moved back into its
correct directory location (reversing the stale code's own orphaning
rename), deleted the now-redundant flat duplicate file — confirmed via
`diff` that the restored file is byte-identical to the pre-incident
backup, and that `messages/`/`files/` were never touched during the
incident (both stayed exactly as backed up throughout). Declined the one
stray Pending Approval referencing only the synthetic verification
content (`2162bb473394`); left two OTHER Pending Approvals generated by
this run untouched, since both are genuine, content-grounded real system
output unrelated to the synthetic testing content itself (a classification
retry on the Thread's own real, original first-message subject; a real
`propose_cross_cutting_update` for partner Core42 grounded in the Thread's
own real, regenerated Summary) — left for the human's own normal
supervised-mode review, not discarded.

**Server correctly restarted** — confirmed (unprompted, no external
intervention) a fresh `uvicorn` process pair came up automatically after
the kill (traced its ancestry to this same coding session's own earlier
background-bash lineage, not an unknown third party); confirmed via a
safe, zero-staged-email no-op dispatch (`"Done — 0 thread(s) updated."`)
that the fresh process is running the corrected, post-`T01` code before
re-attempting this task's own real verification.

**No out-of-scope event, no code fix required** — the incident is entirely
attributable to a stale already-running process predating this task's own
work, not a defect in `T01`'s own code (confirmed: the SECOND, clean
attempt against the freshly-restarted server passed cleanly, see below).
Logged here in full per this project's own "disclosed, not silently
buried" convention, and flagged (see frontmatter `gate_reason`) for human
awareness given real, live vault data was briefly, if fully-repairably,
affected.

---

**Live verification of `[BUGFIX-05-US-01-AC-02]` (second, clean attempt,
against the freshly-restarted, confirmed-correct server):**

1. Confirmed `email-capture-pipeline`'s working mode `supervised` (`GET
   /agents/email-capture-pipeline`). Target: `Work/Threads/2026-08-16 FW-
   Presight Agent Academy Demo/` (`conversation_id
   01D26A7530444A23803A002210620160`), real `messages/` (2 files: `2026-
   08-15-7fa3793a.md`, `2026-08-16-2724a8dd.md`) + real `files/` (2
   companions). Concept file baseline confirmed byte-identical to the
   pre-incident backup before proceeding (re-verified via `diff`).
2. Staged one new, clearly-marked synthetic message (`id:
   "T02-VERIFICATION-0002"`, subject prefixed `[BUGFIX-05-US-01-T02
   verification] ... (retry)`) via the real `email_staging.stage_email`
   primitive, same `conversation_id`, `received` timestamp later than
   every existing message.
3. Called `POST /agents/email-capture-pipeline/schedules/
   process_staged_email/run-now` → `{"status": "pending", ...}`; approved
   the resulting Pending Approval (`e0021c067382`) via `POST
   /pending-approvals/e0021c067382/approve` → `"status": "approved"`, a
   real, honest, non-error result.
4. **`[BUGFIX-05-US-01-AC-02]`** — after the run: the SAME concept file
   (identical path, `2026-08-16 FW- Presight Agent Academy Demo/2026-08-16
   FW- Presight Agent Academy Demo.md` — never moved/renamed) now contains
   a real, regenerated `## Summary` reflecting the Thread's own updated
   `last_message_at`; `messages/` now contains exactly 3 files — the 2
   original baseline files, byte-unchanged at their original paths, PLUS
   ONE new raw message note (`2026-08-19-b7b40574.md`); `files/` UNCHANGED
   — still exactly the 2 original companions, at the same paths, nothing
   moved/disconnected. Searched the full vault
   (`Work/Threads/**/*.md`) for `conversation_id
   01D26A7530444A23803A002210620160` — confirmed exactly ONE Thread note
   matches, at the correct directory-shaped path — no duplicate anywhere.
   **PASS.**
5. Confirmed `email-capture-pipeline`'s working mode STILL `supervised`
   (`GET /agents/email-capture-pipeline`) — unchanged by this task, as
   required.
6. Cleanup: deleted the synthetic raw message note
   (`messages/2026-08-19-b7b40574.md`); restored the concept file to a
   byte-identical copy of the pre-task backup (confirmed via `diff`, not
   visual inspection) — real vault left in its exact pre-task state.
   Declined the one stray classification-failure Pending Approval
   referencing the synthetic content; confirmed `email_staging` empty.

**Acceptance Criteria checklist:**
- [x] `[BUGFIX-05-US-01-AC-02]` verified live and passing (steps 3-4,
      second attempt — the first attempt's own failure was a stale-server
      artifact, not an `AC-02` failure; see incident report above)
- [x] `email-capture-pipeline`'s working mode confirmed unchanged
      (`supervised`) before and after this task (steps 1, 5)
- [x] The real vault is left in its pre-task state (step 6; the one
      real-data incident from the FIRST attempt is fully repaired,
      confirmed byte-identical to backup)
- [ ] `MEMORY.md` — see story-level `MEMORY.md` entry recorded once the
      full story reaches `Done`
- [x] `CHANGELOG.md` entry appended (this task's own commit)

Gate: flagged (see frontmatter `gate_reason`) — not blocking (AC-02 is
genuinely verified PASS and the incident is fully repaired and confirmed),
but surfaced for human awareness given real vault data was briefly
touched during this task's own verification process.
