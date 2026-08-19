---
id: REQ-SB-56-US-01-T01
title: Link-to-Thread Job — primary ConversationID-match strategy
parent_story: REQ-SB-56-US-01
requirement_id: REQ-SB-56
type: backend
status: Done
gate: clear
gate_reason: "Built and verified 2026-08-17 under the operator's provisional Option (a) resolution of ESC-040 (see the banner below and this story's own ## Notes). No new MUST-FLAG trigger fired on this coder pass: no new material assumption beyond what was already resolved upstream; no ADR touched; no ESCALATIONS.md entry needed (nothing new out-of-scope); every locked AC (AC-01) plus the new untagged ConversationID-safety check verified via real code against a real live Outlook installation + a VAULT_PATH-scratch vault (see ## Implementation Log). The STORY-level provisional-resolution spot-check on ESC-040 itself (whether Option (a) was the right call vs. investigating Option (b) later) remains independently open in REVIEW-QUEUE.md — unaffected by, and not blocking, this task's own completion."
phase: P1
depends_on: [REQ-SB-56-US-01-T00]
created: 2026-08-17
updated: 2026-08-17
---

> **UNBLOCKED, 2026-08-17 — provisional operator resolution, flagged for
> morning spot-check.** `T00`'s own live, independent COM verification
> found `ConversationID` unusable (a non-string, inaccessible bound-method
> object) on 15/37 (40.5%) of real sampled calendar items — every one an
> `IncludeRecurrences`-expanded recurring-occurrence item (`ESC-040`).
> Resolved under the operator's own standing overnight instruction ("find
> the best guess" when no urgent human decision is available) as
> **Option (a)** from `ESC-040`'s own listed options: a non-string or
> COM-inaccessible `ConversationID` is treated exactly the same as an
> absent one — this meeting is simply not primary-strategy-linkable, no
> exception is raised, no garbage value is ever written, and the meeting
> falls through to `T02`'s own fallback strategy untouched (identical
> code path to a meeting whose `ConversationID` was empty to begin with).
> The primary strategy still fully works for the 59.5% single-occurrence
> majority. **NOT attempted:** ESC-040's Option (b) (reading the
> recurring series' own master item to recover a usable id for the other
> 40.5%) — a genuine investigation/scope question, deliberately left for
> the operator's own morning review rather than guessed. This task's own
> scope below is amended with one explicit new requirement (see
> Constraints/Tests) to implement Option (a) correctly — read
> `ESC-040`/`REQ-SB-56-US-01`'s own `## Notes` (2026-08-17 entries) for
> full reasoning before starting.

# REQ-SB-56-US-01-T01 — `Link-to-Thread` Job: primary ConversationID-match strategy

## Parent Story

- Story: [[REQ-SB-56-US-01]] — `../UserStories/REQ-SB-56-US-01-meeting-capture-and-thread-linking.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-56 *Meeting Capture & Thread Linking*

---

## Objective

Add a `Link-to-Thread` Job onto the existing, unmodified `meeting-capture` Worker (`classify_recent_meetings`) that links a captured Meeting note to its Thread note via the primary `conversation_id`-match strategy — including the one code-gap fix (`list_calendar_events` doesn't read `ConversationID` today) — once `T00` has confirmed the meeting item's `ConversationID` is usable on this installation.

---

## Starting State → End State

**Before / Inputs:**
- `T00`'s live verification result, recorded in the parent story's own `## Notes`, confirming (or not) that a real meeting/appointment COM item exposes a usable `ConversationID`.
- `list_calendar_events` (`app/data_access/outlook_com.py`) returns `id`/`subject`/`start`/`end`/`location`/`organizer`/`attendees` only — no `conversation_id` field. `list_recent_mail` already returns `"conversation_id": getattr(item, "ConversationID", None) or ""` for mail items — the exact field/shape to mirror.
- `classify_recent_meetings` (`app/business/meeting_classification.py`) already resolves/creates each Meeting note and links customer/attendees, but never touches its `thread` frontmatter field — reserved as an unconditional empty string by `create_meeting_note_baseline`/`ensure_meeting_note_baseline_frontmatter` (`REQ-SB-54-US-01`/T03), explicitly documented there as "REQ-SB-56 is the sole future writer of a real value."
- `vault_writer.thread_note_path(conversation_id)` / `thread_note_exists(conversation_id)` (`REQ-SB-54-US-01`/T02) and `vault_writer.upsert_frontmatter_key(path, key, value)` (defined in `vault_writer.py`, used by `email_classification.py`'s `thread_match_merge`) are the two existing primitives this task composes — no new `vault_writer.py` primitive is needed for `T01`.

**After / Outputs:**
- `list_calendar_events` additionally returns `"conversation_id": getattr(item, "ConversationID", None) or ""` per event.
- A new function in `meeting_classification.py` (e.g. `_link_to_thread_by_conversation_id(event, note_path) -> bool`), called from `classify_recent_meetings` additively, after the existing note create/top-up + attendee/customer linking logic, that: if `event["conversation_id"]` is non-empty AND `vault_writer.thread_note_exists(conversation_id)`, writes that `conversation_id` into the Meeting note's own `thread` frontmatter field via `vault_writer.upsert_frontmatter_key`, and returns whether a link was made.
- `classify_recent_meetings`'s own per-event result dict gains a `"thread_linked": bool` field reporting the outcome (mirrors the existing `"linked"` (customer) field's own shape).
- Every existing meeting-capture behavior (fetch/classify/customer-derivation/attendee-linking/note write) is completely unmodified — this is a purely additive call, not a replacement of any existing line.

---

## Files to Modify

- `src/backend/app/data_access/outlook_com.py` — `list_calendar_events`: add the one new `"conversation_id"` key to its returned dict (mirrors `list_recent_mail`'s own identical field exactly).
- `src/backend/app/business/meeting_classification.py` — add the new primary-strategy linking function and call it from `classify_recent_meetings`.

---

## Constraints

- Inherits from parent story: **false-positive links are worse than no link** — the PRIMARY strategy only ever links on an exact `conversation_id` match against an EXISTING Thread note; it never creates a Thread, never guesses.
- Do not modify `thread_note_path` / `thread_note_exists` / `upsert_frontmatter_key` — compose them as-is.
- Do not touch any of `classify_recent_meetings`'s existing lines — this is an additive call only, placed after the existing customer/attendee linking logic (mirrors this story's own Scenario 4 "purely additive Job" constraint).
- **This task's own build is gated on `T00`'s recorded result.** `T00` found `ConversationID` is NOT usable on a material fraction of items (recurring occurrences) — per the operator's own `ESC-040` Option (a) resolution above, this task must NOT use `list_recent_mail`'s naive `getattr(item, "ConversationID", None) or ""` pattern verbatim (that pattern would silently pass the broken bound-method object through as if it were a real, truthy id). `list_calendar_events`'s own new `"conversation_id"` field must safely resolve to `""` for BOTH an absent property AND a present-but-inaccessible/non-string one — wrap the property access in a narrow `try/except` (or an `isinstance(value, str)` guard after the `getattr`) so a `COMError`/`Type mismatch` on a recurring-occurrence item degrades to `""`, never raises and never propagates the garbage value. This is the one concrete code requirement Option (a) implies.
- Must respect `api → business → data_access` layering (`ADR-003`) — `meeting_classification.py` calls `vault_writer` / `outlook_com`, never the reverse.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-56-US-01-AC-01]** Confirm `T00`'s recorded result in the parent story's `## Notes` shows `ConversationID` is usable. Against a throwaway scratch vault (`VAULT_PATH` env-overridden, real vault untouched — this codebase's own established protocol), construct a synthetic calendar-event dict whose `conversation_id` matches an already-existing Thread note's own `conversation_id` (create one first via `vault_writer.create_thread_note_baseline`). Run the new linking function against it. Confirm the resulting Meeting note's `thread` frontmatter field now holds that exact `conversation_id` (not empty), and confirm the function's own return value reports a link was made.
2. Confirm a synthetic event whose `conversation_id` is non-empty but does NOT match any existing Thread note's own path leaves the Meeting note's `thread` field at its reserved empty string — no false Thread creation, no false link.
3. Confirm a synthetic event whose `conversation_id` is empty/absent (structurally can't primary-match) leaves `thread` empty and does not raise.
3b. **[ESC-040 Option (a)]** Against a real, live recurring-occurrence calendar item on this Outlook installation (one of the ones `T00` found broken — see its recorded sample), confirm `list_calendar_events`'s new `conversation_id` field resolves to `""` (not an exception, not a truthy non-string object) for that item, and confirm the resulting Meeting note's `thread` field is left empty by the primary strategy (falls through cleanly, no crash, no garbage value ever reaches `upsert_frontmatter_key`).
4. Partial regression check (finalized together with `T02`'s own full pass — see `T02`'s Tests step tagged `[REQ-SB-56-US-01-AC-04]`): confirm `classify_recent_meetings`'s existing customer derivation / attendee Person-note linking / customer hub linking / Meeting note create-or-top-up behavior for these same synthetic events is unaffected by this task's own addition — same `customer` / `linked` / `attendees` result-dict fields and values as before this task's change.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1) — a meeting whose `conversation_id` matches an existing Thread note links via the primary strategy
- [x] `list_calendar_events` returns a real, non-hardcoded `conversation_id` per event, mirroring `list_recent_mail`
- [x] No Thread note is ever created by this task — the primary strategy links only against an ALREADY-existing Thread note
- [x] A non-string/COM-inaccessible `ConversationID` (recurring-occurrence items, `ESC-040`) resolves to `""`, never raises, never gets written as a garbage `thread` value
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The fallback attendee-overlap/date-proximity strategy — `T02`'s own scope.
- Any change to `email_classification.py`'s own `thread_match_merge` — already `Done`, unmodified.
- Scenario 4's own FULL regression confirmation — finalized once `T02` also lands (see `T02`'s own Tests step).
- **`ESC-040` Option (b)** (investigating whether reading a recurring series' own master item, rather than each expanded occurrence proxy, recovers a usable `ConversationID` for the 40.5% broken fraction) — deliberately NOT attempted here; the operator's own overnight resolution took the safe Option (a) path only and left (b) as a genuine future optimization for morning review, not something to explore mid-task.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Meeting → Thread Linking — ConversationID Primary Strategy, Attendee-Overlap/Date-Proximity Fallback", point 1. `REQ-SB-54-US-01`/T03 reserved the Meeting `thread` field empty specifically for this story to write — this task is its first real writer.

---

## Implementation Log

**Build, 2026-08-17.**

- `app/data_access/outlook_com.py`: added `_resolve_conversation_id(item)` —
  reads `item.ConversationID` inside a narrow `try/except`, then requires
  `isinstance(value, str)` before returning it, else `""`. Deliberately NOT
  `list_recent_mail`'s own `getattr(item, "ConversationID", None) or ""`
  pattern, per this task's own amended Constraint — that pattern's `or ""`
  only filters a falsy value, and the real broken value (a bound-method
  object) is truthy. `list_calendar_events`'s returned dict now includes
  `"conversation_id": _resolve_conversation_id(item)`. No other line in
  either function touched.
- `app/business/meeting_classification.py`: added
  `_link_to_thread_by_conversation_id(event, note_path) -> bool` — non-empty
  `event["conversation_id"]` AND `vault_writer.thread_note_exists(...)` is
  the only path that calls `vault_writer.upsert_frontmatter_key(note_path,
  "thread", conversation_id)`; every other case (empty, absent, or
  non-matching) returns `False` without writing anything or creating a
  Thread note. Called from `classify_recent_meetings` additively, after the
  existing customer/attendee linking logic, and its result is added to the
  per-event result dict as the new `"thread_linked"` key. No existing line
  in `classify_recent_meetings` was changed.

**Verification (manual mode — no automated test runner exists yet, per
`## Tests`'s own `n/a — test tooling pending`).** All runs used a
`VAULT_PATH`-env-overridden throwaway scratch vault under this session's own
scratchpad directory — the real vault was never touched.

- **[REQ-SB-56-US-01-AC-01] / Test step 1 — PASS.** Created a real Thread
  note via `vault_writer.create_thread_note_baseline("MATCHING-CID-0001")`,
  a real Meeting note via `vault_writer.create_meeting_note_baseline(...)`,
  then called `_link_to_thread_by_conversation_id({"conversation_id":
  "MATCHING-CID-0001"}, note_path)` directly (as the Tests step instructs).
  Observed: function returned `True`; the Meeting note's own `thread`
  frontmatter field read back as exactly `"MATCHING-CID-0001"` (not empty).
- **Test step 2 — PASS.** Same setup with a `conversation_id` that does NOT
  match any existing Thread note. Observed: function returned `False`; the
  Meeting note's `thread` field stayed at its reserved `""`; confirmed no
  Thread note was ever created at that non-matching id's own path (`
  thread_note_exists` still `False` afterward) — no false-positive link,
  no false Thread creation.
- **Test step 3 — PASS.** Same setup with `conversation_id` both explicitly
  `""` and the key absent entirely from the event dict. Observed: neither
  call raised; both returned `False`; `thread` field stayed `""`.
- **[ESC-040 Option (a)] / Test step 3b — PASS, verified against BOTH a real
  live item and a synthetic double.** (1) **Real live check:** ran
  `outlook_com.list_calendar_events(days_back=7, days_ahead=14)` against
  this session's real, live Outlook desktop session (the same installation
  `T00` probed) — 37 real calendar items in window, 16 resolved to an empty
  `conversation_id` (`""`, confirmed `type: str`, not a truthy non-string
  object), 21 resolved to a genuine non-empty id string, and the run raised
  no exception. The 5 subjects in the empty set match `T00`'s own recorded
  broken-recurring-series sample exactly ("Weekly Forecast l Strategic
  Clients", "Weekly Forecast l Major Clients", "Discuss with Mousa", "Kimi 3
  - Foundry PoC - Integration CORE42-Weekly Checkpoints", "Standup - AZDL
  Readiness") plus 11 further individual occurrences of those same 5 (and
  1 more) recurring series in this wider window — i.e. this is a live,
  read-only spot-check against the actual real items `T00` found broken, not
  a copy of `T00`'s own figures. (2) **Synthetic double**, additionally, to
  pin the exact ESC-040 failure shape (attribute access returns a callable
  rather than raising, and only raises `COMError` if actually invoked): a
  fake item whose `ConversationID` attribute is a bound-method-shaped
  callable object that raises if called was passed through
  `outlook_com._resolve_conversation_id` directly — resolved to `""` (`str`,
  not the callable), then through `_link_to_thread_by_conversation_id` — 
  returned `False`, no exception, Meeting note `thread` field stayed `""`,
  `upsert_frontmatter_key` was never reached (short-circuited on the empty
  `conversation_id` check before any write).
- **Test step 4 (partial regression) — PASS, via a mocked-event run
  (assumption logged below).** `classify_recent_meetings` was run end-to-end
  against `outlook_com.list_calendar_events` monkeypatched to return one
  synthetic event (non-matching `conversation_id`) instead of live Outlook
  data. Observed: `created=True`, `customer`/`linked`/`attendees` fields all
  present with their pre-existing shapes/values, the Meeting note's body
  still carries a correct `**Attendees:**` line, `thread` frontmatter stayed
  `""`, and the new `thread_linked=False` key was present alongside the
  unchanged existing keys — confirms this task's own addition is purely
  additive, matching Scenario 4's intent for this task's own partial slice
  (full regression finalizes at `T02` per this task's own Tests step 4).
  **Assumption (scope-internal judgement call, logged per
  `Pipeline.md` rule 5):** an end-to-end run against REAL live Outlook data
  (not mocked) was also attempted and surfaced a pre-existing, unrelated bug
  — one real attendee's resolved address is an EX-style legacyExchangeDN
  string that `vault_writer.create_person_note_baseline`'s own filename
  slugify turns into an invalid Windows path
  (`Work/People/-o=exchangelabs-ou=...-cn=recipients.md`), raising
  `FileNotFoundError` inside `people_extraction.ensure_person_note` — code
  this task's own `## Files to Modify` does not include and did not change.
  Not fixed here (out of this task's scope); worked around for this
  verification by mocking the calendar-event source instead, which is
  sufficient to prove this task's own purely-additive claim. Flagged in this
  session's closing report for the human to `/bug` it separately — not an
  `ESCALATIONS.md`/`REVIEW-QUEUE.md` item for `T01` itself, since it neither
  originates in nor blocks this task's own scope or ACs.
- Confirmed by direct reading: no other line of `classify_recent_meetings`,
  `list_calendar_events`, `thread_note_path`/`thread_note_exists`/
  `upsert_frontmatter_key`, or any other existing function was modified.

**MEMORY.md / CHANGELOG.md:** both updated — see repo-root files. The
COM-safety pattern (never trust a bound-method/non-string COM property
return as truthy; guard with `isinstance(value, str)`, not `or ""`) is
recorded as a new `MEMORY.md` Pattern, given this is the third independent
live-confirmed instance of this exact class of finding on this installation
(`EntryID` — `ESC-002`; `GlobalAppointmentID` — `ESC-012`; `ConversationID`
— `ESC-040`).

**Out of Scope confirmed untouched:** the fallback attendee-overlap/
date-proximity strategy (`T02`); `email_classification.py`'s own
`thread_match_merge`; `ESC-040` Option (b) (recurring-series master-item
investigation) — not attempted, per this task's own explicit instruction.

gate: clear 2026-08-17 — no coder-owned MUST-FLAG trigger fired on this
pass (see `gate_reason` above for full reasoning).
