---
id: REQ-SB-59-US-01-T02
title: vault_migration.recapture_outlook_history() — full re-run of Email/Meeting capture over Outlook history
parent_story: REQ-SB-59-US-01
requirement_id: REQ-SB-59
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-59-US-01-T01]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-59-US-01-T02 — `recapture_outlook_history()` — full re-run of Email/Meeting capture over Outlook history

## Parent Story

- Story: [[REQ-SB-59-US-01]] — `../UserStories/REQ-SB-59-US-01-full-vault-migration-to-new-knowledge-model.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-59 *Full Vault Migration to the New Knowledge Model*

---

## Objective

Add `recapture_outlook_history(email_limit: int, meeting_days_back: int) ->
dict` to `app/business/vault_migration.py`: re-runs the already-`Done`
Email/Meeting capture pipelines, once each, over a full-history window
supplied by the operator (never hardcoded), so every real historical Outlook
conversation and meeting lands in the vault through the new Thread/Meeting-
linking pipelines. Expose it as `POST /poc/recapture-outlook-history`. This
task carries this story's Scenario 3 (Thread consolidation), Scenario 4
(Outlook untouched), and Scenario 5 (Meeting notes/cross-links also cleaned
up) live verification.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has run (or is run immediately before this task's own live
  verification) — `.second-brain/processed_email_ids.json` is archived out
  of its canonical path, so `vault_writer.load_processed_email_ids()`'s own
  existing `if not path.exists(): return set()` branch resets the email
  dedup gate. **Without this, every real historical email is already marked
  processed by its own stable Outlook `EntryID`, and this function silently
  processes zero emails** (`ADR-047` Context point 1).
- `app/business/pipelines/email_pull.py::pull_and_stage_emails(limit: int =
  10) -> dict` (real, `Done`) — `outlook_com.list_recent_mail` iterates its
  own `Items` collection until EITHER `limit` is hit OR the collection is
  exhausted; an `email_limit` at/above the real Inbox item count fetches
  full history in one call.
- `app/business/pipelines/email_capture_pipeline.py::run_email_capture_pipeline(limit:
  int = 10) -> list[dict]` (real, `Done`) — its own current body already
  drains every currently-staged, not-yet-processed email in one call (its
  own `limit` parameter is retained only for call-site backward
  compatibility, per its own docstring).
- `app/business/meeting_classification.py::classify_recent_meetings(days_back:
  int = 7, days_ahead: int = 14, limit: int = 50) -> list[dict]` (real,
  `Done`) — `list_calendar_events` applies a real COM `Restrict()` date
  filter on `days_back`, reaching genuinely full calendar history for a
  large-enough value. `mark_meeting_processed`'s own docstring confirms its
  dedup marker is a non-gating, top-up-only audit trail — a Meeting note is
  topped up in place on every re-visit, never gated on "already processed."
  `REQ-SB-56`'s `Link-to-Thread` Job already runs unconditionally inside
  this same call, so a re-visited pre-migration Meeting note is also
  re-linked to its now-recaptured Thread with zero new code.
- Both underlying Outlook reads stay scoped to the default Inbox/Calendar
  folders only — pre-existing, unchanged behavior, not something this task
  extends.

**After / Outputs:**
- `app/business/vault_migration.py` gains
  `recapture_outlook_history(email_limit: int, meeting_days_back: int) ->
  dict`, returning at minimum `{"emails_staged": int, "emails_processed":
  list, "meetings_processed": list}` (exact key names are this task's own
  implementation latitude), composing the three functions above, each
  exactly once, in that order.
- New `POST /poc/recapture-outlook-history` endpoint in
  `email_poc_router.py`, accepting `email_limit`/`meeting_days_back` as
  required query/body parameters (never defaulted silently — `ADR-047`
  Decision 4/Consequences).
- After a real run: every real historical multi-message Outlook conversation
  exists as exactly one Thread note with a complete transcript; every
  pre-migration Meeting note is topped up/re-linked to its now-recaptured
  Thread; Outlook's own mailbox/calendar content is unchanged.

---

## Files to Modify

- `src/backend/app/business/vault_migration.py` (add
  `recapture_outlook_history`, alongside `T01`'s `wipe_legacy_email_notes`
  — read the REAL current file first, do not overwrite `T01`'s function)
- `src/backend/app/api/email_poc_router.py` (add import +
  `POST /poc/recapture-outlook-history` endpoint, required
  `email_limit`/`meeting_days_back` parameters, matching
  `/poc/classify-emails`'s own existing query-param convention)

---

## Constraints

- Inherits from parent story:
  - **No new Outlook-COM primitive** — reuses `pull_and_stage_emails`/
    `run_email_capture_pipeline`/`classify_recent_meetings` verbatim,
    unmodified.
  - **`email_limit`/`meeting_days_back` are required, operator-supplied
    parameters** — never a hardcoded magic number inside this function's
    own body (this project's standing "config, not constants" convention,
    `ADR-047` Decision 4).
  - **Outlook itself is never written to or deleted from** — every
    Outlook-COM call this function makes is a pre-existing, unchanged
    read-only call; this task adds no new Outlook write path.
  - **Never touches `Work/Meetings/`'s own notes destructively** — only
    `classify_recent_meetings`'s own existing, unchanged top-up/re-link
    write path runs against them.
- Do not modify `email_pull.py`, `email_capture_pipeline.py`,
  `meeting_classification.py`, `outlook_com.py`, or `vault_writer.py` — this
  task composes existing, unmodified functions only (`## Non-Goals`: "Any
  change to the capture pipelines themselves").
- Each of the three composed calls runs **exactly once** per invocation of
  `recapture_outlook_history` — no internal retry loop, no re-invocation.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

<!-- This task carries AC-03, AC-04, and AC-05 — every locked AC whose
Scenario needs a real, re-captured Thread/Meeting to exist. -->

**Manual verification steps:**

1. **Precondition:** confirm `T01`'s own `wipe_legacy_email_notes()` has
   already run against this same vault (its `Work/Emails/` is empty and
   `processed_email_ids.json`/`conversation_index.json` are archived, per
   `T01`'s own Tests). If not, run it first — `recapture_outlook_history`
   depends on this precondition to process any real email at all.
2. [REQ-SB-59-US-01-AC-04] Before running, via a direct, read-only call to
   `outlook_com.list_recent_mail(limit=<a large value>)` (or an equivalent
   direct COM read), record a baseline: the real Inbox item count and the
   set of real `EntryID`s returned. Do the same for
   `outlook_com.list_calendar_events(days_back=<meeting_days_back>,
   days_ahead=14)` — record the real event count and `EntryID`s/subjects.
   Call `recapture_outlook_history(email_limit=<>, meeting_days_back=<>)`
   (via `POST /poc/recapture-outlook-history`) and let it complete. Repeat
   the exact same two direct, read-only Outlook calls afterward. Confirm
   both the Inbox item count/`EntryID` set and the Calendar event
   count/`EntryID` set are byte-for-byte identical before and after — no
   Outlook item was created, modified, or deleted by this run.
3. [REQ-SB-59-US-01-AC-03] Before running, identify 3 real, previously-known
   multi-message Outlook conversations (2+ real messages each) that existed
   pre-migration — note each conversation's real message subjects/count.
   After `recapture_outlook_history(...)` completes, confirm each of the 3
   now corresponds to exactly ONE Thread note under the Thread folder (one
   file per conversation, not split across multiple), and that Thread
   note's own transcript contains every one of that conversation's real
   messages (spot-check the message count and subject lines against the
   real Outlook conversation recorded above).
4. [REQ-SB-59-US-01-AC-05] Before running, pick a real, previously-known
   pre-migration Meeting note (predating this migration) and record its
   current cross-link content (including any Thread link, which may be
   stale/dangling pre-run). After `recapture_outlook_history(...)`
   completes, confirm that same Meeting note was topped up in place (not
   duplicated into a second note) and its own Thread cross-link now
   resolves to the correct, now-recaptured Thread note for that meeting —
   not a stale or dangling reference. Confirm this is not scoped to Email
   notes alone — a real Meeting note genuinely changed as a result of this
   call.
5. Non-AC sanity check (load-bearing per `ADR-047` Context point 1): confirm
   the run's own reported `emails_processed`/similar count is a real,
   materially non-zero number matching real historical Inbox volume — NOT
   zero. A zero count here would mean `T01`'s dedup-gate reset silently
   failed to take effect, which would falsify AC-03 even if the 3
   spot-checked conversations happen to already exist from a prior run —
   treat a zero count as a build defect, not a pass.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `REQ-SB-59-US-01-AC-03` verified: 3 real spot-checked conversations
      each consolidate into exactly one complete Thread note
- [ ] `REQ-SB-59-US-01-AC-04` verified: Outlook's own real mailbox/calendar
      content is byte-for-byte unchanged before/after the run
- [ ] `REQ-SB-59-US-01-AC-05` verified: a real pre-migration Meeting note is
      topped up/re-linked to its recaptured Thread, not left stale
- [ ] `email_limit`/`meeting_days_back` are required parameters, never
      hardcoded
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiping `Work/Emails/` or the two `.second-brain/` JSON stores — `T01`.
- Any Customer note regeneration / `ESC-046` resolution — `T03`.
- Any change to `pull_and_stage_emails`/`run_email_capture_pipeline`/
  `classify_recent_meetings`'s own internal logic.

---

## Context / Notes

`Implementation/Architecture/architecture.md` → "Vault Migration..." section,
`recapture_outlook_history` bullet, and `ADR-047` Decision 3/4 are the full
architectural reasoning this task implements. `ADR-047` Context point 2 is
why no Meeting-note wipe is needed or wanted.

**Wall-clock expectation:** per `Implementation/Learnings.md`
(`SPRINT-021`/`SPRINT-027`/`SPRINT-031`), a real, on-demand, large-window
Outlook capture run is genuinely multi-minute-to-multi-hour depending on
real mailbox volume — background the verification call with unbuffered
output from the start and use CPU-accumulation/active-connection checks to
distinguish "still working" from a true hang, rather than assuming a fixed
timeout.

**No functional dependency on `T03`** — `regenerate_customer_notes()`
reads each legacy flat Customer note's own pre-migration body (not
anything this task recaptures) and rolls up existing Project state; it does
not need this task's own output to run correctly. See `T03`'s own Context
for the full reasoning.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
