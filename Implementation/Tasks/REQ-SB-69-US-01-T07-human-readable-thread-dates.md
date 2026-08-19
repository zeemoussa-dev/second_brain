---
id: REQ-SB-69-US-01-T07
title: Additive last_message_at_display frontmatter field; human-readable ## Transcript timestamps; last_message_at stays machine-parseable, unchanged
parent_story: REQ-SB-69-US-01
requirement_id: REQ-SB-69
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-69-US-01-T06]
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-69-US-01-T07 — Human-readable Thread dates

## Parent Story

- Story: [[REQ-SB-69-US-01]] — `../UserStories/REQ-SB-69-US-01-decoupled-email-pull-and-human-readable-thread-notes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-69 *Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes*

---

## Objective

Add a new, additive `last_message_at_display` frontmatter sibling field
(human-readable) and render `## Transcript` entry timestamps human-
readably at write time — while `last_message_at` itself stays byte-for-
byte unchanged (still machine-parseable), so `meeting_classification.py::
_date_proximity_gap_days`'s real, already-shipped
`last_message_at[:10]` parsing keeps working exactly as today.

---

## Starting State → End State

**Before / Inputs:**
- `thread_match_merge` writes `last_message_at` unconditionally via
  `vault_writer.upsert_frontmatter_key(path, "last_message_at",
  email["received"])` — a raw, COM-stringified timestamp (e.g.
  `"2026-08-16 13:02:57.246000+00:00"`).
- `## Transcript` entries are appended via `vault_writer.
  append_body_section_line(path, "## Transcript", f"- **{email[
  'received']}** — {sender}: {email['subject']}")` — the SAME raw
  timestamp string, rendered directly.
- `meeting_classification.py::_date_proximity_gap_days` (lines 86-103)
  parses `thread_last_message_at[:10]` via `datetime.strptime(...,
  "%Y-%m-%d")` — only ever reads the first 10 characters.

**After / Outputs:**
- `thread_match_merge` gains one additional `upsert_frontmatter_key`
  call: `vault_writer.upsert_frontmatter_key(path,
  "last_message_at_display", <human-readable rendering of email[
  "received"]>)`, written alongside (never instead of) the existing
  `last_message_at` write — `last_message_at` itself is written
  identically to today, unchanged.
- The `## Transcript` entry's own timestamp component renders human-
  readably (e.g. `"Aug 16, 2026, 1:02 PM"`) instead of the raw string,
  via the same formatting helper.
- A new `vault_writer.format_human_readable_datetime(raw: str) -> str`
  helper parses the raw, COM-stringified timestamp (`email["received"]`'s
  own real shape, e.g. `"2026-08-16 13:02:57.246000+00:00"`) and renders
  it in a human-readable form. Falls back to returning the raw string
  unchanged if parsing genuinely fails (never raises, never fabricates a
  guessed date) — mirrors this codebase's own honest-degradation
  posture for a display-only formatting concern.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add
  `format_human_readable_datetime(raw: str) -> str` as a new module-level
  helper, near the existing date-handling code (mirrors this module's own
  `datetime`/`timezone` imports, already present at the top of the file).
- `src/backend/app/business/email_classification.py`:
  - `thread_match_merge`: add the `last_message_at_display`
    `upsert_frontmatter_key` call, composing `vault_writer.
    format_human_readable_datetime(email["received"])`.
  - `thread_match_merge`'s own `## Transcript` `append_body_section_line`
    call: change the raw `{email['received']}` interpolation to
    `{vault_writer.format_human_readable_datetime(email['received'])}`.

---

## Constraints

- Inherits from parent story.
- **`last_message_at` stays byte-for-byte identical to today** — this
  task is purely additive; nothing about the existing
  `upsert_frontmatter_key(path, "last_message_at", email["received"])`
  call changes.
- **`format_human_readable_datetime` never raises** — a genuinely
  unparseable raw string falls back to returning it unchanged, never a
  fabricated/guessed date and never an uncaught exception that would
  abort the whole `thread_match_merge` call over a display-only
  formatting concern.
- **`meeting_classification.py` is NOT modified by this task** — the
  Constraint this task must satisfy is that its OWN, already-shipped
  `_date_proximity_gap_days` parsing keeps working against the
  unmodified `last_message_at` field; nothing in that file needs to
  change.
- No change to `T08`'s own scope (`## Related` wikilinks) in this task.

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-69-US-01-AC-08]` Run `thread_match_merge` for a real (or
   realistic synthetic) captured message. Open the resulting Thread
   note's frontmatter — confirm `last_message_at_display` is present and
   renders in a human-readable form (e.g. `"Aug 16, 2026, 1:02 PM"`), and
   confirm `last_message_at` itself is still the raw, machine-parseable
   form (unchanged in shape from before this task — a direct byte
   comparison against what today's code would have written). Confirm the
   `## Transcript` entry just appended for this message also renders its
   own timestamp human-readably, not as the raw string.
2. `[REQ-SB-69-US-01-AC-09]` Using a real Thread note and a real Meeting
   note whose dates are genuinely close (per `meeting_thread_link_config`'s
   own `date_proximity_days` window), run `_link_to_thread_by_fallback_
   heuristic` (or trigger the real Meeting-capture path that calls it)
   against them. Confirm it still correctly computes a real date-
   proximity gap and links the Meeting to the Thread exactly as it did
   before this task — a genuine, live-verified regression check, not
   inferred from reading the code alone.
3. Non-AC regression check: call `format_human_readable_datetime` with a
   deliberately malformed input string (e.g. `"not a real date"`).
   Confirm it returns the input unchanged rather than raising.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-69-US-01-AC-08` — `last_message_at_display` renders
      human-readable; `last_message_at` unchanged; `## Transcript`
      entries render human-readable
- [x] `REQ-SB-69-US-01-AC-09` — `_date_proximity_gap_days`/the
      Thread↔Meeting fallback linker keep working, verified live
- [x] `format_human_readable_datetime` never raises on malformed input
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `## Related` wikilinks — `T08`.
- Any change to `meeting_classification.py`.
- Backfilling already-captured Thread notes' dates — parent story's own
  Non-Goal, deferred.

---

## Context / Notes

`ADR-046` Decision 10 (`Implementation/Architecture/ADR.md`) is the full
architectural reasoning, including the direct repo-wide search
confirming nothing else programmatically parses an individual `##
Transcript` line (so its own timestamp formatting is a pure display
change with zero downstream parsing consequence). This task depends on
`T06` only to avoid a same-function conflicting edit to
`thread_match_merge` — it has no genuine content dependency on `T06`'s
own rename mechanism.

---

## Implementation Log

**What was changed:**

- `src/backend/app/data_access/vault_writer.py`: added
  `format_human_readable_datetime(raw: str) -> str`, placed directly after
  the Thread primitives block (`rename_thread_note`), before
  `_meeting_thread_link_config_path`. Parses `raw` via
  `datetime.fromisoformat` (handles the space-separated,
  microsecond-precision, UTC-offset-suffixed shape `email["received"]`
  already has, e.g. `"2026-08-16 13:02:57.246000+00:00"`), with a
  date-only `strptime("%Y-%m-%d")` fallback for a bare-date input; on a
  genuine parse failure (e.g. `"not a real date"`) returns `raw`
  unchanged — never raises. Renders `"<Mon> <day>, <year>, <hour>:<min>
  <AM/PM>"` with leading zeros stripped from the day and the 12-hour hour
  (e.g. `"Aug 16, 2026, 1:02 PM"`, `"Aug 6, 2026, 9:05 AM"`) — matches
  `ADR-046` Decision 10's own example exactly.
- `src/backend/app/business/email_classification.py`, `thread_match_merge`:
  - added one additional `vault_writer.upsert_frontmatter_key(path,
    "last_message_at_display",
    vault_writer.format_human_readable_datetime(email["received"]))`
    call, written immediately after (never instead of) the existing,
    byte-for-byte-unchanged `last_message_at` write.
  - the `## Transcript` `append_body_section_line` call's own
    `{email['received']}` interpolation changed to
    `{vault_writer.format_human_readable_datetime(email['received'])}` —
    the entry's sender/subject portions are unchanged.
  - the function's own docstring updated to describe both of the above
    (the human-readable sibling field and the human-readable Transcript
    dating), noting `last_message_at` itself stays unchanged and
    parseable by `meeting_classification.py`'s own
    `_date_proximity_gap_days`.

No deviation from the task's own `## Starting State → End State`/`##
Files to Modify` text — the exact field name, call composition, and
example format specified there and in `ADR-046` Decision 10 were
implemented as written. No scope-internal judgement calls beyond the
implementation's own internal formatting details (leading-zero stripping
on day/hour, not specified verbatim by the ADR beyond its one worked
example, but the only reading that reproduces that example exactly).

**Verification — manual mode, run live against the real, configured
vault (`VAULT_PATH = C:\myWorx\Moussa MD\Moussa Brain`), via two
disposable, self-cleaning Python scripts (mirroring `T06`'s own
`verify_t06.py` precedent), using only `T07VERIFY-*`-prefixed disposable
data, both cleaned up (disposable Thread notes deleted) and confirmed
zero residue afterward (`vault_writer.list_thread_notes()` shows only the
two real, pre-existing Threads before and after both runs). Real Compass
calls were made (live LLM synthesis for `## Summary`/opening-line
regeneration inside `thread_match_merge`), not mocked.**

- **`[REQ-SB-69-US-01-AC-08]`** — a disposable email
  (`conversation_id="T07VERIFY-CONV-0001"`, `received="2026-08-16
  13:02:57.246000+00:00"`) processed via `thread_match_merge`. Read the
  resulting Thread note's frontmatter directly off disk: `last_message_at
  == "2026-08-16 13:02:57.246000+00:00"` (byte-for-byte identical to what
  today's code would have written — a direct comparison, not inferred);
  `last_message_at_display == "Aug 16, 2026, 1:02 PM"` (human-readable,
  matches `ADR-046`'s own example exactly). `## Transcript`'s freshly
  appended entry read via `read_body_section`: contains `"Aug 16, 2026,
  1:02 PM"` and does NOT contain the raw ISO string
  `"2026-08-16 13:02:57.246000+00:00"`. **PASS (4/4 assertions).**
- **`[REQ-SB-69-US-01-AC-09]`** — a second disposable Thread
  (`conversation_id="T07VERIFY-CONV-0002"`, participant
  `t07verify.attendee@example.com`, `last_message_at="2026-08-10
  09:00:00.000000+00:00"`) created via `thread_match_merge`; confirmed its
  `last_message_at`/`last_message_at_display` frontmatter both correct. A
  disposable Meeting `event` dict (`start="2026-08-12 10:00:00+00:00"`,
  2 real calendar days later — within `meeting_thread_link_config`'s own
  default `date_proximity_days` window) with one overlapping attendee.
  Called `meeting_classification._date_proximity_gap_days(event["start"],
  frontmatter["last_message_at"])` directly against the real, unmodified
  `last_message_at` value written above — returned `2` (correct real gap,
  confirms `strptime(thread_last_message_at[:10], "%Y-%m-%d")` still
  parses `last_message_at` exactly as before this task). Then called the
  real, live `meeting_classification._link_to_thread_by_fallback_
  heuristic(event, self_excluded_attendees)` end-to-end — correctly
  returned `"T07VERIFY-CONV-0002"`, i.e. it linked the Meeting to the
  correct Thread. **PASS (3/3 assertions).**
- **Non-AC regression check (`format_human_readable_datetime` never
  raises)** — called directly with a deliberately malformed input,
  `"not a real date"`: returned `"not a real date"` unchanged, no
  exception raised. Also spot-checked additional real/edge shapes: a
  date-only string (`"2026-08-16"` → `"Aug 16, 2026, 12:00 AM"`, the
  honest fallback for a genuinely time-less input), a single-digit-day
  input (`"2026-08-06 09:05:00+00:00"` → `"Aug 6, 2026, 9:05 AM"`), and a
  noon boundary (`"2026-08-16 12:00:00+00:00"` → `"Aug 16, 2026, 12:00
  PM"`). **PASS.**

Both disposable Thread notes were deleted immediately after each script's
own assertions passed; `vault_writer.list_thread_notes()` re-checked
afterward shows zero residual `T07VERIFY*` notes, only the two real,
pre-existing Threads (`01D26A7530444A23803A002210620160.md`,
`0C41DC9411479C4BAC82EBDDDCA753E7.md`, both untouched by this task's
verification).

**MUST-FLAG check:** none of the triggers fired this pass — no new
dependency, no shared-interface change beyond what `ADR-046` Decision 10
already specifies verbatim, no ADR created/edited, no deviation from
`ADR-046`, no unanticipated file, no unclear/contradictory requirement
(the task's own text and `ADR-046` Decision 10 fully specified the exact
field name, call site, and example format). `gate: clear`.
