---
id: REQ-SB-56-US-01-T00
title: Live verification — does a real meeting/appointment COM item expose a usable ConversationID on this Outlook installation?
parent_story: REQ-SB-56-US-01
requirement_id: REQ-SB-56
type: verification
status: Done
gate: flagged
gate_reason: "Live probe executed and recorded (this task's own job) — trigger-7 fired because the recorded RESULT is negative (contradicts the referenced 100/100 figure on a material 40.5% of the real sample). T00 itself is Done (its job was to verify and record, which it did); T01 is set Blocked as this task's own Constraints require. See REVIEW-QUEUE.md / ESCALATIONS.md ESC-040."
phase: P1
depends_on: []
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-56-US-01-T00 — Live meeting-item ConversationID verification

## Parent Story

- Story: [[REQ-SB-56-US-01]] — `../UserStories/REQ-SB-56-US-01-meeting-capture-and-thread-linking.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-56 *Meeting Capture & Thread Linking*

---

## Objective

Perform a one-time, **read-only** COM probe of real Outlook calendar/appointment items to determine whether `ConversationID` is exposed and usable on this installation, and formally record the observed result in the parent story's own `## Notes` — before `T01` (which depends on this task) is built. Mirrors this codebase's own established "COM-assisted, one-time determination of a 'no safe default' config value" pattern (`MEMORY.md` → Patterns).

---

## Starting State → End State

**Before / Inputs:**
- `app/data_access/outlook_com.py::list_calendar_events` does NOT read `ConversationID` off the underlying `AppointmentItem` today (confirmed by direct reading) — a code gap, not yet a confirmed data-availability answer.
- `architecture.md`, `REVIEW-QUEUE.md`, and `BACKLOG.md`'s `REQ-SB-56` row all already reference an apparent prior finding — "a live, read-only sample of 100 real calendar items ... found ConversationID non-empty on 100/100" — attributed to the architect's own 2026-08-16 pass. **This figure has NOT been formally recorded inside this story's own `## Notes`**, which the story's own Definition of Done explicitly requires before `T01` is built. Per explicit operator instruction (2026-08-17): do not treat that referenced figure as authoritative until THIS task has independently run its own probe and recorded what it observed.

**After / Outputs:**
- A real, read-only COM probe has been run against a live Outlook session on this installation, using the same `GetDefaultFolder(9)` / `Restrict` window mechanics `list_calendar_events` already uses (so the sample matches the real capture window), reading `getattr(item, "ConversationID", None)` off each sampled item.
- The observed result (sample size, count non-empty, one real example value, and whether it looks stable/plausible as a join key) is appended to `REQ-SB-56-US-01`'s own `## Notes`, dated, below the existing "Operator confirmation, 2026-08-17" / "Additional standing constraint" section.
- `T01` may only proceed building the primary ConversationID-match strategy once this recorded result confirms ConversationID is usable; if it is not, `T01` stays blocked (see Constraints) — never silently reinterpreted.

---

## Files to Modify

- `Implementation/UserStories/REQ-SB-56-US-01-meeting-capture-and-thread-linking.md` — append the verification result to `## Notes` only; no other section of this file changes.

No `src/` file is modified by this task. `app/data_access/outlook_com.py` is **read-only** for `T00` (per this story's own task scoping) — the probe itself is a throwaway, uncommitted script/REPL session against the real, already-authenticated Outlook desktop session (mirrors this codebase's own established scratch-script verification convention, e.g. `REQ-SB-08-US-01-T01`'s own `self_email` COM probe), never committed to `src/`.

---

## Constraints

- Inherits from parent story.
- **Read-only, no side effects.** This probe must never modify, send, move, or delete any real Outlook item — only read `.ConversationID` / `.Subject` / `.Start` off a bounded sample. A handful of real items (at least 10; ideally matching or exceeding the architect's own referenced 100-item sample) is enough — no need to scan the entire calendar.
- **Do not assume the answer.** Even though `architecture.md` / `REVIEW-QUEUE.md` / `BACKLOG.md` already reference a "100/100 non-empty" figure from the architect's own 2026-08-16 pass, this task must independently execute its own probe this session and record what IT observes — do not copy the referenced figure into the story's `## Notes` without having actually run the check.
- **If ConversationID is confirmed usable** (non-empty, stable across the real sample): record this and state explicitly that `T01` may proceed unchanged as scoped.
- **If ConversationID is NOT usable** (empty/absent/unstable on a material fraction of real sampled items): do not silently narrow or reinterpret `T01`'s own scope. Write a `REVIEW-QUEUE.md` entry and an `ESCALATIONS.md` entry (trigger 7 — contradictory inputs: this story's own architecture section is grounded in a premise this task's own live check would have disproved) and stop. `T01` stays blocked until a human decides how to proceed (e.g., abandon the primary strategy, ship fallback-only). This is the one contingency this task's own Tests section below does not "pass" — do not force a pass to unblock `T01`.

---

## Tests

<!-- This is a technical prerequisite check, not itself a locked Gherkin
AC — AC-01's own tagged verification lives in T01, gated on this task's
recorded outcome. Steps below are NOT AC-tagged for that reason. -->

**Manual verification steps:**
1. Connect to the real, running Outlook desktop session via the same `win32com.client.Dispatch("Outlook.Application")` / `GetNamespace("MAPI")` mechanics `_connect_namespace()` already uses; open the Calendar default folder (`GetDefaultFolder(9)`); read a bounded sample of real items (e.g. the same `[Start]` window `list_calendar_events` already restricts to, or a smaller fixed sample) — for each, read `getattr(item, "ConversationID", None)`. Record: sample size, count non-empty, one real example value (subject-redacted if sensitive).
2. Append the observed result to `REQ-SB-56-US-01`'s own `## Notes`, dated, below the "Additional standing constraint" section — e.g. "`T00` live verification, <date>: N/N sampled real calendar items carried a non-empty `ConversationID`; example value `<redacted-or-real>`. Confirms/contradicts the architect's own referenced 100/100 figure. `T01` may [not] proceed as scoped."

**Automated tests:** `n/a — test tooling pending; this is inherently a live/manual check by nature (external COM dependency running against real Outlook state), not something a future automated suite can run in CI.`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Live, read-only COM probe executed against the real Outlook installation this session
- [x] Result (sample size / non-empty count / example) recorded verbatim in `REQ-SB-56-US-01`'s own `## Notes`
- [ ] If usable: explicit statement recorded that `T01` may proceed unchanged — **N/A, not usable (see below)**
- [x] If not usable: `REVIEW-QUEUE.md` + `ESCALATIONS.md` entries written; `T01` explicitly left blocked, not silently reinterpreted
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (e.g. confirming or correcting the architect's own referenced figure)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Adding `conversation_id` to `list_calendar_events`'s own returned dict — `T01`'s own scope, not this task's (this task is read-only against `outlook_com.py`).
- Any change to `meeting_classification.py` — `T01`/`T02`'s own scope.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Meeting → Thread Linking — ConversationID Primary Strategy, Attendee-Overlap/Date-Proximity Fallback", point 1. `MEMORY.md` → "COM-assisted, one-time determination of a 'no safe default' config value" pattern — closest established precedent (same read-only, one-time-probe-before-building shape, applied here to a feasibility question rather than a config value). `REVIEW-QUEUE.md` → `REQ-SB-56-US-01` entry already references an apparent prior 100/100 finding — this task's own job is to make that finding a REAL, task-executed, story-recorded fact, not to assume it.

---

## Implementation Log

**2026-08-17 — coder pass.** Ran a throwaway, read-only COM probe (not
committed to `src/`, per this task's own Files to Modify note — kept in
the coder's own scratchpad and discarded after this run) against the real,
running Outlook desktop session (`Get-Process OUTLOOK` confirmed a live
process before probing). The probe mirrored `list_calendar_events`'s own
exact connection/window mechanics: `Dispatch("Outlook.Application")` →
`GetNamespace("MAPI")` → `GetDefaultFolder(9)` → `Items.Sort("[Start]")`
→ `IncludeRecurrences = True` → the identical `[Start]` `Restrict()`
window with the function's own default `days_back=7, days_ahead=14`. For
each of the 37 real items landing in that live window, read
`getattr(item, "ConversationID", None)`, `Subject`, `Start`.

**Verification steps (this task's own `## Tests`, not AC-tagged — see
that section's own comment):**

1. **Step 1 (probe + record).** Executed. Result: **22/37 (59.5%)**
   real sampled items carried a genuine, non-empty, distinct
   `ConversationID` string; **15/37 (40.5%)** — every one an
   `IncludeRecurrences`-expanded recurring-occurrence item
   (`IsRecurring=True`, `RecurrenceState` 2 or 3) — returned a
   non-string bound-method object via the convenience property (raises
   `-2147352573 'Member not found.'` if invoked) and a `-2147352571
   'Type mismatch.'` COM error via the raw MAPI `PropertyAccessor`
   fallback (`PR_CONVERSATION_ID`, proptag `0x3013001F`). Full sample
   log, per-item breakdown, and the exact example values are recorded
   verbatim in `REQ-SB-56-US-01`'s own `## Notes` (dated 2026-08-17,
   below the "Product-owner pass" section).
2. **Step 2 (append to story Notes).** Done — see
   `Implementation/UserStories/
   REQ-SB-56-US-01-meeting-capture-and-thread-linking.md` → `## Notes`
   → "`T00` live verification, 2026-08-17 — NEGATIVE...".

**Outcome: NEGATIVE.** This independent, live, task-executed probe
**contradicts** the "100/100 non-empty" figure `architecture.md` /
`REVIEW-QUEUE.md` / `BACKLOG.md` had referenced from the architect's own
2026-08-16 pass — a real, material 40.5% of the live sample returns a
genuinely unusable value, concentrated entirely on recurring-occurrence
items (the exact expansion mechanism `list_calendar_events` already
relies on for correctness). Per this task's own Constraints, this is
**not** silently narrowed or reinterpreted into a smaller scope for
`T01` — a `REVIEW-QUEUE.md` entry and an `ESCALATIONS.md` entry
(`ESC-040`, category `other` — a live/factual finding, not an unclear
product requirement) have been written, and `REQ-SB-56-US-01-T01`'s own
`status:` has been set to `Blocked` with a pointer to this finding. `T01`
and `T02` are explicitly **not** attempted by this task — out of this
task's own scope regardless of the (negative) outcome, per this task's
own brief.

**MEMORY.md:** a new Pattern was recorded — this is the third
independent, live-confirmed instance on this same Outlook installation
of a per-item COM property being unreliable specifically on
`IncludeRecurrences`-expanded occurrence items (after `EntryID`,
`ESC-002`, and `GlobalAppointmentID`, `ESC-012`) — worth checking before
trusting any future new per-item Outlook COM property read against
expanded calendar occurrences.

**CHANGELOG.md:** entry appended under `## [Unreleased]`.

No `src/` file was modified by this task (read-only, per scope). No file
outside this task's own declared `## Files to Modify` was edited except
the standing coder Definition-of-Done surfaces (`CHANGELOG.md`,
`MEMORY.md`, `REVIEW-QUEUE.md`, `ESCALATIONS.md`) and
`REQ-SB-56-US-01-T01`'s own `status:`/gate frontmatter — the latter is
this task's own explicit, brief-directed escalation action ("mark T01
Blocked"), not scope creep into T01's actual build.
