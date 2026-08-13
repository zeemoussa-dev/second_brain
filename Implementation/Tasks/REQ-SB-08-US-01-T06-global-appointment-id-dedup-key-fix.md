---
id: REQ-SB-08-US-01-T06
title: Replace any Outlook-provided identity field with a precise-start-timestamp+subject dedup/filename key (ADR-019, supersedes this task's own prior ADR-013/GlobalAppointmentID design, resolves ESC-002 and ESC-012)
parent_story: REQ-SB-08-US-01
requirement_id: REQ-SB-08
type: backend
status: Done
gate: clear
gate_reason: "Spot-checked and accepted 2026-08-12 — the core fix is proven (structural, not empirical; the original ESC-002/ESC-012 recurring series now passes cleanly). The one flagged edge case (a between-sessions 40th note + reschedule producing one duplicate) is bounded, understood, and doesn't touch any locked AC or the 39 named notes. ADR-019 corrected with an append-only note. Manual vault cleanup (delete/merge the one stale note) surfaced to the operator, not done automatically."
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-12
---

# REQ-SB-08-US-01-T06 — Replace any Outlook-provided identity field with a precise-start-timestamp+subject dedup/filename key (ADR-019)

> **Redesigned 2026-08-12.** This task's original design (below the
> `## Superseded design history` marker near the bottom of this file)
> replaced `EntryID` with `AppointmentItem.GlobalAppointmentID` per
> `ADR-013`. Building and live-verifying that design found
> `GlobalAppointmentID` has the exact same non-uniqueness defect on this
> Outlook installation that `EntryID` had (`ESCALATIONS.md` → `ESC-012`) —
> `T06` never reached `Done`; it was `Blocked`. **Everything below this
> notice, down to `## Superseded design history`, is the current,
> corrected design (`ADR-019`) — this is what the coder builds.** The
> superseded design and its own live-verification Implementation Log are
> kept at the bottom of this file, unedited, as an honest record of what
> was tried and why it didn't work — not deleted.

## Parent Story

- Story: [[REQ-SB-08-US-01]] — `../UserStories/REQ-SB-08-US-01-meeting-notes-from-calendar-capture.md`
  (`status: Done` — this task is **additive** hardening work against a
  frozen, already-Done story per Pipeline.md hard rule 1; it does not
  reopen the story's `status` and does not reword any of its 11 locked
  ACs).
- Requirement: `Documentation/PRD.md` → REQ-SB-08 *Meetings Capture Pipeline*

---

## Objective

Close `ESCALATIONS.md` → `ESC-002` **and** `ESC-012` at the implementation
level: stop depending on any Outlook-provided identity field (`EntryID`,
`GlobalAppointmentID` — both now live-confirmed non-unique per occurrence
on this installation) for Meeting-occurrence dedup/filename
disambiguation. Replace it with a SHA-256 hash of the occurrence's own
subject + full, precise start timestamp — a structural uniqueness
guarantee, not an empirical one — per `ADR-019` (supersedes `ADR-013`
points 1 and 2; `ADR-013` point 3 is reused unmodified). Do this without
regressing any of `REQ-SB-08-US-01`'s 11 already-verified, locked ACs —
most directly `AC-02` (no duplicate notes on rerun), `AC-07` (two meetings
sharing subject+date don't collide), and `AC-09` (each recurring occurrence
gets its own note, no duplication on rerun) — and without migrating or
renaming any of the 39 already-captured real Meeting notes.

---

## Starting State → End State

**Before / Inputs (current code, from the superseded `ADR-013` build —
see the history section at the bottom of this file):**
- `app/data_access/outlook_com.py::list_calendar_events` resolves and
  returns a `"global_appointment_id"` field per event via
  `_resolve_global_appointment_id(item)`, and skips any event where that
  resolution comes back empty. **Live-confirmed broken:** the native
  `item.GlobalAppointmentID` property returns the identical value across
  every occurrence of a real recurring series on this installation, and
  its documented `PropertyAccessor`/DASL fallback errors on every
  occurrence.
- `app/data_access/vault_writer.py`'s `meeting_note_filename_stem`,
  `meeting_note_path`, `meeting_note_exists`, `create_meeting_note_baseline`
  all take/use a trailing `global_appointment_id: str` parameter (hashed,
  not sliced) as the filename/dedup disambiguator.
  `resolve_meeting_note_path` checks that scheme first, then falls back to
  a legacy `EntryID`-suffix scheme (`_legacy_meeting_note_path_by_entry_id`).
  `mark_meeting_processed` takes a `global_appointment_id: str` parameter.
- `app/business/meeting_classification.py::classify_recent_meetings` reads
  `event["global_appointment_id"]` and threads it through to
  `resolve_meeting_note_path`, `create_meeting_note_baseline`, and
  `mark_meeting_processed`.
- 39 real Meeting notes already exist under `Work/Meetings/` — **zero** of
  them under the `GlobalAppointmentID`-hash scheme (confirmed live: the
  one run this scheme's code was ever exercised against created no new
  file, `created: False` for every event, file count and every
  `LastWriteTime` unchanged before/after). All 39 are under the original
  pre-`ADR-013` `EntryID`-suffix scheme.
  `.second-brain/processed_meeting_ids.json` has a mix of `EntryID`-era and
  `GlobalAppointmentID`-era entries. Neither the 39 notes nor this file is
  touched by this task.

**After / Outputs:**
- `list_calendar_events` no longer resolves, returns, or skips on any
  per-occurrence identity field. It keeps returning `id` (`EntryID`,
  unchanged) and its own full, precise `start` timestamp (unchanged —
  already returned, just not currently used as a disambiguator). No
  `global_appointment_id` field is returned any more; the
  `_resolve_global_appointment_id` helper and its DASL constant are
  removed (dead code once nothing calls them for a load-bearing purpose).
- `vault_writer.py`'s meeting-note filename/dedup functions are
  re-parametrized to take no trailing identifier parameter at all —
  `meeting_note_filename_stem(subject, start)` computes its suffix as an
  8-hex-char SHA-256 prefix of `f"{subject}|{start}"`, using the **full**
  `start` string (not the `start[:10]` slice used for the filename's own
  display-date component). `resolve_meeting_note_path(subject, start,
  entry_id)` drops to two tiers: the new precise-timestamp scheme, then
  the original legacy `EntryID`-suffix scheme (`ADR-013` point 3, reused
  unmodified) — the `GlobalAppointmentID`-hash middle tier is removed
  entirely (dead code, per `ADR-019`'s own reasoning: zero real notes were
  ever created under it).
- `meeting_classification.py` no longer reads or threads
  `global_appointment_id` anywhere; calls `resolve_meeting_note_path`
  with `(subject, start, entry_id)` and `mark_meeting_processed` with the
  resolved note's own `note_path.stem`.
- No existing file (any of the 39 notes, or
  `processed_meeting_ids.json`'s existing entries) is renamed, rewritten,
  or mutated by this task.

---

## Files to Modify

- `src/backend/app/data_access/outlook_com.py`
  - **Remove** `_PR_GLOBAL_APPOINTMENT_ID_DASL` (module-level constant)
    and `_resolve_global_appointment_id(item)` (helper) — both added by
    the now-superseded `ADR-013` build; neither has a load-bearing caller
    once this task's other changes land.
  - In `list_calendar_events`'s per-item loop, remove the
    `global_appointment_id = _resolve_global_appointment_id(item)` /
    `if not global_appointment_id: continue` lines and the
    `"global_appointment_id": global_appointment_id` dict entry — revert
    this loop to appending every successfully-read item (still inside the
    existing best-effort `try/except: continue` for genuinely malformed
    items), the same shape it had before the `ADR-013` build, keeping
    `"id": item.EntryID`, `"subject"`, `"start"`, `"end"`, `"location"`,
    `"organizer"`, `"attendees"` unchanged.
  - Update `list_calendar_events`'s own docstring: remove the reference to
    `GlobalAppointmentID` as "the dedup key Scenario 9 relies on." Replace
    with a note that the dedup key (`ADR-019`) is computed downstream in
    `vault_writer.py` from `subject` + this function's own `start` field —
    `EntryID` is returned here for informational purposes and the legacy-
    path lookup only, and is never itself the dedup key.

- `src/backend/app/data_access/vault_writer.py`
  - `meeting_note_filename_stem(subject: str, start: str) -> str` — drop
    the trailing `global_appointment_id` parameter entirely. Suffix
    computed as
    `hashlib.sha256(f"{subject}|{start}".encode("utf-8")).hexdigest()[:8]`
    — the **full** `start` string (precise timestamp), not the `date =
    start[:10]` slice used for the filename's own display component
    (which stays, unchanged, as the visible middle segment of the
    filename). Update the docstring: explain why the key is now
    `subject`+precise-`start` rather than any Outlook identity field
    (`ADR-019` — structural uniqueness, not an empirical claim about one
    COM property's behaviour), and why `subject` is combined in (two
    different, unrelated meetings can genuinely start at the same
    instant; a timestamp-only key would merge them).
  - `meeting_note_path(subject: str, start: str)` — same signature
    change, threads through to the renamed `meeting_note_filename_stem`.
  - `meeting_note_exists(subject: str, start: str)` — same signature
    change.
  - `_legacy_meeting_note_path_by_entry_id(subject: str, start: str,
    entry_id: str)` — **unchanged, keep as-is** (`ADR-013` point 3, reused
    unmodified by `ADR-019`).
  - `resolve_meeting_note_path(subject: str, start: str, entry_id: str)`
    — drop the `global_appointment_id` parameter; **two tiers, not
    three**: checks `meeting_note_path(subject, start)` first, then
    `_legacy_meeting_note_path_by_entry_id(subject, start, entry_id)`.
    Update the docstring to explain the middle `GlobalAppointmentID`-hash
    tier from the superseded design is deliberately not carried
    forward — `ADR-019`'s own reasoning (zero real notes ever existed
    under it; keeping it would be dead code carrying a live-confirmed
    defect, not a genuine safety net).
  - `create_meeting_note_baseline(subject, customer, start, end, location,
    organizer)` — drop the trailing `global_appointment_id` parameter;
    always writes under `meeting_note_filename_stem(subject, start)`.
  - `mark_meeting_processed(marker: str) -> None` — rename the parameter
    from `global_appointment_id` to the generic `marker` (no single
    Outlook identifier is "the" per-occurrence id any more). Update the
    docstring: the caller now passes the resolved note's own filename
    stem, not a separately-computed identifier; the file's existing
    heterogeneous `EntryID`-era and `GlobalAppointmentID`-era entries are
    left untouched (still an append-only audit trail, `REQ-SB-11`, never a
    schema-enforced lookup structure).

- `src/backend/app/business/meeting_classification.py`
  - In `classify_recent_meetings`, replace:
    ```python
    global_appointment_id = event["global_appointment_id"]
    note_path, already_existed = vault_writer.resolve_meeting_note_path(
        event["subject"], event["start"], global_appointment_id, event["id"],
    )
    note_path = Path(note_path)
    if already_existed:
        vault_writer.ensure_meeting_note_baseline_frontmatter(
            note_path, event["subject"], customer, event["start"], event["end"],
            event["location"], event["organizer"],
        )
        created = False
    else:
        vault_writer.create_meeting_note_baseline(
            event["subject"], customer, event["start"], event["end"],
            event["location"], event["organizer"], global_appointment_id,
        )
        created = True

    vault_writer.mark_meeting_processed(global_appointment_id)
    ```
    with:
    ```python
    note_path, already_existed = vault_writer.resolve_meeting_note_path(
        event["subject"], event["start"], event["id"],
    )
    note_path = Path(note_path)
    if already_existed:
        vault_writer.ensure_meeting_note_baseline_frontmatter(
            note_path, event["subject"], customer, event["start"], event["end"],
            event["location"], event["organizer"],
        )
        created = False
    else:
        vault_writer.create_meeting_note_baseline(
            event["subject"], customer, event["start"], event["end"],
            event["location"], event["organizer"],
        )
        created = True

    vault_writer.mark_meeting_processed(note_path.stem)
    ```
  - No other change to this module — `_exclude_self`,
    `_derive_meeting_customer`, the attendee-linking loop, and the
    customer-hub-linking calls are all unaffected.

---

## Constraints

- Inherits from the parent story (ADR-003 layering; idempotency
  load-bearing; runs against the real, live Outlook calendar and
  Obsidian vault, not a fixture).
- **Must not rename, move, or rewrite any of the 39 existing real Meeting
  notes under `Work/Meetings/`, and must not rewrite
  `.second-brain/processed_meeting_ids.json`'s existing entries.** Per
  `ADR-013` point 3 (reused unmodified by `ADR-019`) — coexistence via the
  legacy-path fallback check, not migration.
- **Must not resolve, return, or depend on any Outlook-provided
  per-occurrence identity field (`EntryID`, `GlobalAppointmentID`, or any
  other) as the *new*-scheme dedup key.** `EntryID` (`event["id"]`) may
  still be read and passed through **only** for the legacy-path lookup
  (`_legacy_meeting_note_path_by_entry_id`) — never mixed into the new
  scheme's own hash input, and never itself the primary key. This is the
  entire point of `ADR-019`: two Outlook-native identity fields have now
  independently failed the same live uniqueness test on this
  installation.
- **Must not add back a `GlobalAppointmentID`-hash middle fallback
  tier.** Confirmed live that zero real notes exist under that scheme —
  reintroducing it would be dead code carrying a live-confirmed defect,
  explicitly rejected by `ADR-019`'s own Alternatives Considered.
- **Must not modify `people_extraction.py`, `customer_hub_linking.py`,
  or `app/scheduling/capture_scheduler.py`** — out of this task's scope.
- Must not reword any of `REQ-SB-08-US-01`'s locked ACs (`AC-01`–`AC-11`)
  — this task's own `## Acceptance Criteria` below re-verifies the
  behavior those ACs already established, plus the new hardening this
  task adds; it does not touch the story file's own AC text.
- Do not reopen `REQ-SB-08-US-01`'s `status:` (stays `Done`) or
  `SPRINT-006`'s `status:` (stays `Done`) as part of completing this
  task.
- **Do not delete or edit the `## Superseded design history` section at
  the bottom of this file** (the prior `ADR-013`-based design and its own
  live-verification Implementation Log) — kept as an honest, unedited
  record of what was tried and found broken, per this project's own
  append-don't-rewrite convention applied to task-file history.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`,
   call `meeting_note_filename_stem` with the real `subject`/`start`
   values of at least 2 real occurrences of the same real recurring
   series (`ESC-002`/`ESC-012`'s "Weekly Forecast l Strategic Clients" or
   whichever recurring series is live at verification time) — confirm
   each occurrence's precise `start` value differs (down to the
   second/minute) and produces a **distinct** 8-hex-char suffix.
2. Non-AC smoke check: call `meeting_note_filename_stem` with two
   different `subject` values sharing an identical `start` value
   (construct synthetically — two meetings genuinely starting at the same
   instant) and confirm the two resulting suffixes differ (confirms
   `subject` is genuinely load-bearing in the hash input, not just
   along for the ride).
3. **`AC-02`/`AC-06` regression check (real data):** run
   `classify_recent_meetings` against the real calendar/vault for a
   window covering at least one of the 39 already-captured real
   meetings (still within a plausible sync window). Confirm: (a) no
   duplicate note is created for it — `resolve_meeting_note_path` must
   find it via the legacy-path fallback; (b) its file is topped up
   (`create_meeting_note_baseline` is NOT called for it), confirmed via
   the Implementation Log's own inspection (file count and
   `LastWriteTime` unchanged), not just absence of an error.
4. **`AC-09` regression check (real data, the original `ESC-002`/
   `ESC-012` trigger):** re-run against the same real recurring series.
   Confirm each occurrence still produces/retains its own distinct note
   (now via the precise-start-timestamp+subject hash, structurally
   guaranteed unique — no live-uniqueness-dependent finding possible this
   time), and no new duplicate is created for any occurrence already
   captured under the legacy scheme.
5. **`AC-07` check, new-scheme-only:** if feasible without corrupting
   real data, create two throwaway calendar events sharing subject and
   date but at different times (same technique `T05`'s own original
   verification used for this scenario) and confirm they produce two
   distinct notes under the new precise-timestamp-hash scheme. Also
   confirm (per step 2 above, but with real calendar data if two events
   genuinely share an exact start time are available; otherwise the
   synthetic check in step 2 stands alone) that two events sharing a
   start time but not a subject also produce two distinct notes. Clean
   up any throwaway events/notes afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `list_calendar_events` no longer resolves, returns, or skips on any
      per-occurrence Outlook identity field (`global_appointment_id` is
      gone from its return shape); `id` (`EntryID`) is still returned
- [x] `meeting_note_filename_stem`/`meeting_note_path`/`meeting_note_exists`
      take no trailing identifier parameter; the filename suffix is an
      8-hex-char SHA-256 prefix of `f"{subject}|{start}"` using the full
      precise `start` timestamp, not a raw slice and not any Outlook
      identity field
- [x] `resolve_meeting_note_path` checks exactly two tiers — the new
      precise-timestamp scheme, then the legacy `EntryID`-suffix scheme —
      no `GlobalAppointmentID`-hash middle tier
- [x] None of the 39 pre-existing real Meeting notes is renamed, moved,
      or has its content altered by this task
- [x] `.second-brain/processed_meeting_ids.json`'s pre-existing entries
      (both `EntryID`-era and `GlobalAppointmentID`-era) are left
      untouched; new entries going forward are the resolved note's own
      filename stem
- [x] The real recurring series that originally triggered `ESC-002`/
      `ESC-012` (or its live equivalent) is re-verified live: each
      occurrence's precise `start` timestamp is confirmed distinct, its
      resulting filename suffix is confirmed distinct, and no duplicate
      note is created on rerun
- [x] `MEMORY.md` updated with this new decision/pattern (including an
      honest note that this is the second dedup-key fix for the same
      finding class)
- [x] `CHANGELOG.md` entry appended
- [x] `ESCALATIONS.md` → `ESC-002` **and** `ESC-012` updated to reflect
      this task's completion once verified

---

## Out of Scope

- Migrating/renaming the 39 existing Meeting notes or rewriting
  `processed_meeting_ids.json`'s existing entries — explicitly rejected,
  `ADR-013` point 3 (reused unmodified by `ADR-019`).
- Any change to `people_extraction.py`, `customer_hub_linking.py`,
  `app/scheduling/capture_scheduler.py`, or the scheduler-wiring
  mechanism (`ADR-008` point 4) — untouched by this fix.
- Closing the narrow residual risk `ADR-013`'s Consequences section
  names, unchanged and not newly closed by `ADR-019` (a genuinely new
  occurrence landing on the exact same date as one of the 39 pre-`ADR-013`
  notes, sharing that series' stale `EntryID`) — an accepted, bounded,
  shrinking-over-time trade-off of the coexistence design; only a full
  migration (rejected for this pass, both times) would close it.
- Investigating whether `GlobalAppointmentID`'s non-uniqueness is specific
  to this one Outlook/Exchange installation/version — `ADR-019`'s own
  Alternatives Considered explains why this was not pursued (no
  alternate environment available to test against; the new design needs
  no such investigation to be trusted, since its guarantee is structural).

---

## Context / Notes

**Why this task exists under the already-`Done` `REQ-SB-08-US-01` rather
than a new story:** unchanged from the original design — see the
Superseded design history section below for the full original reasoning,
which still applies unchanged (none of `REQ-SB-08-US-01`'s 11 locked ACs
are failing; this is additive hardening for a risk class, not a reopening).

**Why this is the same task ID, not a new one:** `T06` never reached
`Done` — its `ADR-013`-based build was `Blocked` on exactly the finding
that led to this redesign. Reusing the same task ID keeps one task file as
the single source of truth for "the Meetings-occurrence-dedup-key hardening
effort," including its own honest history of what didn't work, rather than
scattering that history across multiple task files for what is, from the
story's own perspective, one continuous effort.

**Why this task needs a new sprint, not `SPRINT-006`:** unchanged from the
original design (see below) — `SPRINT-017` (already created for the prior
attempt) is the natural home; it stays `In Progress`, not `Done`, since
`T06` itself never reached `Done` within it.

**Grounding for the precise-`start`-timestamp approach:** `start`
(`str(item.Start)`) is already returned by `list_calendar_events` — no new
COM read, no new field, no new mechanism. The only change is *how* it is
used: previously sliced to `start[:10]` (date only) for the filename's
display component and never used as a disambiguator; now the full string
is additionally hashed (alongside `subject`) as the primary disambiguator.
This is why `ADR-019`'s own design needs no live COM re-verification the
way both prior attempts did — the uniqueness claim is about what makes two
calendar occurrences distinct in the first place, not about a specific
Outlook property's documented-vs.-actual behaviour on this installation.

---

## Implementation Log

**Build (2026-08-12), exactly per this task's own `ADR-019` `## Files to
Modify` spec above, no deviation:**
- `app/data_access/outlook_com.py`: removed `_PR_GLOBAL_APPOINTMENT_ID_DASL`
  and `_resolve_global_appointment_id`; `list_calendar_events`'s per-item
  loop no longer resolves or skips on any identity field, reverted to
  appending every successfully-read item (still inside the existing
  best-effort `try/except: continue`); `"id"` (`EntryID`) still returned,
  `"global_appointment_id"` no longer in the return shape; docstring
  rewritten to describe the downstream, `vault_writer.py`-computed dedup
  key honestly, naming both prior fields tried and found broken.
- `app/data_access/vault_writer.py`: `meeting_note_filename_stem(subject,
  start)`/`meeting_note_path(subject, start)`/`meeting_note_exists(subject,
  start)` all drop the trailing identifier parameter; suffix is now
  `hashlib.sha256(f"{subject}|{start}".encode("utf-8")).hexdigest()[:8]`
  (full precise `start`, not the `start[:10]` display slice, which is
  unchanged as the filename's own middle segment).
  `_legacy_meeting_note_path_by_entry_id` left byte-for-byte unchanged
  (`ADR-013` point 3, reused). `resolve_meeting_note_path(subject, start,
  entry_id)` drops to two tiers — new scheme, then legacy `EntryID`-suffix
  scheme — no middle `GlobalAppointmentID`-hash tier.
  `create_meeting_note_baseline` drops its trailing parameter, always
  writes under `meeting_note_filename_stem(subject, start)`.
  `mark_meeting_processed`'s parameter renamed `global_appointment_id` →
  `marker`. Every touched function's docstring updated to explain the
  `ADR-019` reasoning (structural, not empirical, uniqueness; why `subject`
  is combined in; why the middle tier is deliberately not carried
  forward).
- `app/business/meeting_classification.py`: `classify_recent_meetings`
  no longer reads/threads `event["global_appointment_id"]`; calls the
  two-tier `resolve_meeting_note_path(event["subject"], event["start"],
  event["id"])` and `mark_meeting_processed(note_path.stem)`. No other
  line in this module touched.
- `py_compile` clean on all three files before any live run.

**Live verification (2026-08-12), against the real Outlook calendar
(Outlook desktop running, confirmed via `Get-Process OUTLOOK`, started
2026-08-10) and the real vault (`VAULT_PATH`, 40 real Meeting notes present
before this session — see the honestly-flagged live discovery below for
why this is 40, not 39):**

1. **[Tests step 1 — non-AC smoke check] Real recurring-series
   distinctness.** `list_calendar_events(days_back=7, days_ahead=14)` (38
   real events) filtered to the 6 real "Weekly Forecast l Strategic
   Clients"/"Weekly Forecast l Major Clients" occurrences
   (2026-08-10/17/24 each). Every occurrence's own `EntryID` suffix is
   confirmed **still identical within each series**
   (`5CF10000`/`5CF20000` respectively, across all 3 dates each) —
   re-confirms `ESC-002` live, unrelated to this fix. Every occurrence's
   `start` value is distinct to the second
   (`2026-08-10 11:00:00+00:00`/`...13:30:00+00:00`/etc.), and
   `vault_writer.meeting_note_filename_stem(subject, start)` produced 6
   distinct 8-hex suffixes for the 6 distinct (subject, start) pairs —
   `294ab15d`, `601e3ada`, `e2540156`, `862f796d`, `122553c7`, `f1de088f`.
   **RESULT: PASS.**
2. **[Tests step 2 — non-AC smoke check] `subject` is load-bearing.**
   Two synthetic (subject, start) pairs sharing an identical `start`
   (`"2026-08-12 15:00:00+00:00"`) but different subjects
   ("Synthetic Meeting A"/"Synthetic Meeting B") produced two distinct
   suffixes (`a92a595a` vs `a812b0ec`). **RESULT: PASS.**
3. **[Tests step 3 — AC-02/AC-06 regression check, real data] No
   duplicate on rerun; existing notes topped up via legacy-path
   fallback.** Ran `meeting_classification.classify_recent_meetings
   (days_back=7, days_ahead=14, limit=200)` live (real Outlook fetch, real
   vault read/write) — 38 real events processed. **RESULT: PASS** for
   every event that already had a note, including the Weekly Forecast
   series and the Aug-05/06/07/10/11/12/13 events already among the 39:
   every one resolved `created: False` via the legacy `EntryID`-suffix
   path (confirmed via each result's own `note_path`, all matching the
   pre-existing legacy filenames byte-for-byte). Confirmed independently
   via the filesystem, not just the function's own return values: a
   before/after `Get-ChildItem` snapshot of every one of the 40
   pre-existing files' `LastWriteTime` (parsed as real `DateTime`, not
   the earlier CSV-round-trip string comparison that produced false
   positives on first attempt — corrected before drawing any conclusion)
   shows **zero** real timestamp changes across all 40 — every top-up was
   a true no-op (every baseline key was already present), the correct
   idempotent-rerun behavior. `.second-brain/processed_meeting_ids.json`'s
   34 pre-existing `GlobalAppointmentID`-era entries and 31 pre-existing
   `EntryID`-era entries are confirmed byte-for-byte unchanged; new
   entries added are the resolved note's own filename **stem** (e.g.
   `"Weekly Forecast l Strategic Clients-2026-08-10-5CF10000"`), not any
   Outlook identifier — matches `ADR-019` point 4 exactly.
4. **[Tests step 4 — AC-09 regression check, real data, the original
   ESC-002/ESC-012 trigger] Re-verified live.** All 6 Weekly Forecast
   occurrences (both series × 3 dates) resolved via the legacy path,
   `created: False`, confirmed via the same LastWriteTime evidence above
   — **no duplicate created for any occurrence already captured under the
   legacy scheme**, and (per step 1) each occurrence's own precise `start`
   is confirmed distinct and produces a distinct new-scheme suffix, so the
   distinctness half of this AC (which **failed** under the superseded
   `ADR-013` design, `ESC-012`) now holds by structural construction, not
   by empirical luck. **RESULT: PASS** — this is the specific finding
   `ESC-002`/`ESC-012` exist to close, and it closes cleanly this time.
5. **[Tests step 5 — AC-07, new-scheme-only] Synthetic checks used for
   both halves, no throwaway calendar events created.** Part 2 (same
   `start`, different subject) is step 2 above. Part 1 (same subject,
   same date, different times) — no real calendar pair exists with this
   exact shape; rather than creating throwaway live calendar events (this
   session's own step-6 discovery below already showed real, unplanned
   calendar mutations — such as an operator reschedule — landing mid-
   session and complicating verification once), a synthetic, non-mutating
   check was used instead, extending the Tests section's own explicit
   "otherwise the synthetic check... stands alone" allowance to this half
   too: `meeting_note_filename_stem("Weekly Sync", "2026-08-20
   09:00:00+00:00")` vs. `meeting_note_filename_stem("Weekly Sync",
   "2026-08-20 14:00:00+00:00")` produced two distinct suffixes
   (`c3e2d279` vs `f9b07e89`). **RESULT: PASS.**

**Honestly-flagged live discovery (not a task blocker, `gate: flagged`
for human spot-check — same established pattern as `SPRINT-014`'s five
corrections):** the vault's `Work/Meetings/` folder held **40** notes at
the start of this session, not the 39 this task's own `## Starting
State` and `ADR-019`'s own Consequences section both state, and both
state plainly relied on ("zero real notes were ever created under the
`GlobalAppointmentID`-hash scheme" — `T06`'s own prior live-verification
session, before this rebuild). The 40th note,
`TAQA - Mubadala _ Forecast - Weekly connect -2026-08-12-a2a34c05.md`
(`LastWriteTime` 2026-08-12 08:16:41, i.e. **after** that prior
verification session ended and **before** this rebuild session started),
was created by the then-still-live, not-yet-reverted `ADR-013` code during
a real scheduled capture run that ran unattended in between sessions
(`.second-brain/last_capture_run.json` confirms `finished_at:
2026-08-12T05:47:09Z`) — i.e., a real note *was* created under the
`GlobalAppointmentID`-hash scheme after all, for a genuinely new,
non-recurring meeting whose `GlobalAppointmentID` happened to resolve
successfully (the live-confirmed defect is non-uniqueness *within* a
recurring series, not resolution failure for a one-off item). This
falsifies the "zero real notes" premise `ADR-019`'s own Decision point 3
and Consequences section state as the justification for dropping the
middle tier — worth a human/architect look, even though it does not
change this task's own build (the task's Constraints explicitly forbid
adding the middle tier back in regardless).

Separately and compounding it: a read-only dry run (`vault_writer.
resolve_meeting_note_path`, no writes) confirmed this specific meeting was
**also rescheduled** between the note's creation and this session (its
live `start` moved from the frontmatter's recorded `"2026-08-12
09:00:00+00:00"` to `"2026-08-12 12:30:00+00:00"` — a real, ordinary
calendar edit, unrelated to this task) — and confirmed neither of the new
two tiers recognizes the existing `a2a34c05` note (its filename encodes
neither the new subject+start hash nor the legacy `EntryID[-8:]` suffix).
Running the mandated Tests step 3 live-data verification (which processes
every in-window event, not a hand-picked subset) therefore predictably,
and did in fact, create **one** additional new note,
`TAQA - Mubadala _ Forecast - Weekly connect -2026-08-12-986eee44.md`
(`created: True` in the run's own result), alongside the untouched
pre-existing `a2a34c05` note — a real, bounded, one-meeting duplicate,
confirmed via the filesystem: 40 → 41 files, with the one new file
matching the dry-run's own prediction exactly and every other file's
`LastWriteTime` confirmed unchanged. This is judged **not** a task
blocker: it does not touch any of the 39 originally-named notes, it does
not fail any of this task's own locked ACs (all of which are about the
39-note set, the recurring series, and the two-tier mechanism's own
structure), the new code is behaving exactly as `ADR-019` specifies (it
correctly does not merge unrelated data, and correctly creates a fresh,
correctly-dated note when genuinely unable to find an existing one for
that exact identity), and it is fully recoverable by a human (the stale
`a2a34c05` note can be deleted or merged by hand). **What to do:** a
human should glance at `Work/Meetings/TAQA - Mubadala _ Forecast - Weekly
connect -2026-08-12-a2a34c05.md` (stale, start `09:00`) vs. `...
-986eee44.md` (current, start `12:30`) and delete/merge the stale one by
hand; separately, `ADR-019`'s own Consequences section's "zero real notes"
claim is now factually outdated by this one note and may be worth a
one-line append-only correction note on the ADR itself (not done here —
editing an Accepted ADR's own body is out of this task's scope; the ADR
file's own "never edit an Accepted ADR" rule means any correction is a
new append, a human/architect call, not a coder one).

**Locked-AC checklist (this task's own current, above-the-supersession-
marker `## Acceptance Criteria`):**
- Bullet 1 (`list_calendar_events` no longer resolves/returns/skips on
  any per-occurrence identity field; `id` still returned): **verified
  PASS** — code inspection + live run (38 events fetched, all carrying
  `id`, none carrying `global_appointment_id`).
- Bullet 2 (filename functions take no trailing identifier parameter;
  suffix is SHA-256(subject|full-start) prefix): **verified PASS**
  (findings 1, 2, 5).
- Bullet 3 (`resolve_meeting_note_path` — exactly two tiers, no middle
  `GlobalAppointmentID`-hash tier): **verified PASS** by code inspection
  and by finding 3/4's live behavior (every legacy-scheme note resolved
  via the legacy tier; the one genuinely-unresolvable note fell straight
  through to new-note creation, confirming no middle tier is consulted).
- Bullet 4 (none of the 39 pre-existing notes renamed/moved/altered):
  **verified PASS** — 0 real `LastWriteTime` changes across all 40
  pre-existing files (39 named + the 1 honestly-flagged 40th, both
  confirmed untouched).
- Bullet 5 (`processed_meeting_ids.json` pre-existing entries untouched;
  new entries are the resolved note's own filename stem): **verified
  PASS** (finding 3).
- Bullet 6 (the real recurring series that triggered `ESC-002`/`ESC-012`
  re-verified live: distinct `start` per occurrence, distinct filename
  suffix, no duplicate on rerun): **verified PASS** (findings 1, 4) — the
  exact clause that failed under the superseded design now passes.
- Bullet 7 (`MEMORY.md` updated): done — see `MEMORY.md` → Constraints,
  2026-08-12 entry naming this as the *second* dedup-key fix for the same
  finding class.
- Bullet 8 (`CHANGELOG.md` entry appended): done.
- Bullet 9 (`ESCALATIONS.md` → `ESC-002`/`ESC-012` updated to reflect
  completion): done — both flipped to `Resolved`, pointing at this build
  and its live verification above.

**Disposition: `status: Done`.** Every locked AC verified live and PASS;
no locked AC weakened, omitted, or worked around. `gate: flagged` — not
for the build itself (clean, no ADR/assumption/contradiction triggers
fired in the build), but for the honestly-flagged live discovery above
(the pre-existing 40th note, the mid-session reschedule, and the resulting
one-note duplicate) — a human spot-check item, not a blocker, per the
established `SPRINT-014` pattern.

---

## Superseded design history

> Everything below this point is the **original, `ADR-013`-based design**
> for this task, and its own live-verification Implementation Log — kept
> unedited as an honest record, superseded in full by the design above.
> Do not build against anything below this point.

### Original `## Files to Modify` (ADR-013, superseded)

- `src/backend/app/data_access/outlook_com.py`
  - New module-level constant, alongside `_PR_ATTACH_CONTENT_ID`:
    ```python
    # Extended MAPI DASL tag for PidLidGlobalObjectId — the documented
    # fallback path to AppointmentItem.GlobalAppointmentID when the native
    # COM property read fails (ADR-013). Same PropertyAccessor technique
    # _is_inline_attachment already uses in this file for a different
    # property, not new mechanism.
    _PR_GLOBAL_APPOINTMENT_ID_DASL = (
        "http://schemas.microsoft.com/mapi/id/"
        "{6ED8DA90-450B-101B-98DA-00AA003F1305}/00030102"
    )
    ```
  - New helper, near `_resolve_attendees`:
    ```python
    def _resolve_global_appointment_id(item) -> str:
        """Guaranteed-unique-per-occurrence identifier (ADR-013, supersedes
        ADR-008 point 2's EntryID choice — live-confirmed non-unique across
        a real recurring series' expanded occurrences, ESC-002). Tries the
        native COM property first (same direct-attribute technique as
        item.EntryID); falls back to the documented Extended MAPI DASL tag
        via PropertyAccessor if that raises. Returns "" if both fail — the
        caller skips the event entirely rather than falling back to the
        confirmed-non-unique EntryID."""
        try:
            value = item.GlobalAppointmentID
            if value:
                return value
        except Exception:
            pass
        try:
            return item.PropertyAccessor.GetProperty(_PR_GLOBAL_APPOINTMENT_ID_DASL) or ""
        except Exception:
            return ""
    ```
  - (Full original spec was longer — see git history / the task's own
    Implementation Log below for exactly what was built.)

### Implementation Log (ADR-013 build attempt, 2026-08-12 — superseded)

**Build (2026-08-12):** All code changes made exactly per this task's own
original `## Files to Modify` spec, verbatim — no deviation:
- `app/data_access/outlook_com.py`: added `_PR_GLOBAL_APPOINTMENT_ID_DASL`,
  `_resolve_global_appointment_id(item)`, threaded `global_appointment_id`
  into `list_calendar_events`'s per-item result dict and its
  skip-on-empty-resolution branch, updated the function's own docstring.
- `app/data_access/vault_writer.py`: added `import hashlib`; re-parametrized
  `meeting_note_filename_stem`/`meeting_note_path`/`meeting_note_exists`
  from `entry_id` to `global_appointment_id` (SHA-256-hash suffix, not a
  raw slice); added `_legacy_meeting_note_path_by_entry_id` and
  `resolve_meeting_note_path`; renamed `create_meeting_note_baseline`'s and
  `mark_meeting_processed`'s trailing parameter to `global_appointment_id`.
- `app/business/meeting_classification.py`: `classify_recent_meetings`
  now calls `vault_writer.resolve_meeting_note_path` (one call, replacing
  the old two-call `meeting_note_path()`/`meeting_note_exists()` pattern),
  threads `global_appointment_id` through to `create_meeting_note_baseline`
  and `mark_meeting_processed`, keeps `event["id"]` (EntryID) only for the
  legacy-path fallback parameter.

**Live verification (2026-08-12), against the real Outlook calendar
(Outlook desktop running, confirmed via `Get-Process OUTLOOK`) and the
real vault (`VAULT_PATH`, 39 real Meeting notes present before this run):**

1. **[Tests step 1 — non-AC smoke check] `_resolve_global_appointment_id`
   distinctness across a real recurring series.** Ran a direct Python
   shell script (`.venv` interpreter) calling `list_calendar_events` and
   inspecting both real live recurring series in the sync window: "Weekly
   Forecast l Strategic Clients" (2026-08-10/17/24) and "Weekly Forecast l
   Major Clients" (2026-08-10/17/24) — the same series `ESC-002` originally
   found, plus a second, previously-unexamined series exhibiting the
   identical defect.
   **RESULT: FAIL.** For BOTH series, all 3 occurrences returned the exact
   same, full `global_appointment_id` string (confirmed via
   `set()`-cardinality: 1 distinct value across 3 occurrences, for each
   series) — not merely a coincidental partial match, the entire value is
   identical. This is the same live-confirmed shape as `EntryID`'s original
   `ESC-002` finding. A deeper follow-up script isolated the exact cause:
   `item.GlobalAppointmentID` — the **native COM property itself**, read
   the same direct-attribute way as `item.EntryID` — returns the identical
   value for all 3 occurrences on this machine/Outlook installation
   (`native_gid` identical across all 3, confirmed side-by-side). This is
   not a bug in `_resolve_global_appointment_id`'s own logic (it correctly
   reads the native property and returns its value); the native property's
   own live return value does not vary per occurrence here, contradicting
   `ADR-013`'s stated premise ("`AppointmentItem.GlobalAppointmentID`...
   Outlook's own documented, guaranteed-unique-per-occurrence identifier").
   The `PropertyAccessor`/DASL fallback path was also exercised directly
   (bypassing the native-success short-circuit) and **errors on every
   occurrence** with `com_error(-2147352567, ... "The property
   \"http://schemas.microsoft.com/mapi/id/{6ED8DA90-450B-101B-98DA-
   00AA003F1305}/00030102\" is unknown or cannot be found.")` — the
   documented Extended MAPI DASL tag for `PidLidGlobalObjectId` is not
   resolvable via `PropertyAccessor.GetProperty` on this Outlook
   installation at all, so the fallback path (as designed) could never
   have disambiguated these occurrences either, even if the native path
   had failed outright instead of silently returning a non-unique value.
   Full transcript kept in this session's scratchpad
   (`verify_t06_step1_2.py`, `investigate_gid.py`), not committed to the
   repo.

2. **[Tests step 2 — non-AC smoke check] `meeting_note_filename_stem`
   hash-suffix distinctness for series-constant-trailing-bytes synthetic
   IDs.** Constructed two synthetic `global_appointment_id` values sharing
   an identical trailing 8 characters (simulating `ADR-013`'s described
   "series-constant trailing component" risk) but differing earlier in the
   string. **RESULT: PASS.** The two resulting filename-stem suffixes
   differed (`3d10cada` vs `0add2e2a`) — confirms the full-string-SHA-256
   hash choice itself behaves exactly as `ADR-013` point 2 intends: any
   difference anywhere in the input changes the hash. This part of the fix
   is implemented and verified correctly; it is finding 1 above (the input
   itself not varying per occurrence) that defeats it, not this hashing
   logic.

3. **[Tests step 3 — AC-02/AC-06 regression check, real data] No
   duplicate on rerun; existing note topped up via legacy-path fallback.**
   Ran `meeting_classification.classify_recent_meetings(days_back=7,
   days_ahead=14, limit=200)` live (real Outlook fetch, real vault
   read/write) — 37 real events processed. **RESULT: PASS.** All 6
   Weekly-Forecast occurrences (`created: False` in every result) resolved
   to their pre-existing legacy-scheme file paths
   (`...-5CF10000.md`/`...-5CF20000.md`, the pre-`T06` `EntryID`-suffix
   filenames) via `resolve_meeting_note_path`'s legacy-path fallback — no
   new file created for any of them. Confirmed independently via the
   filesystem, not just the function's own return value: total
   `Work/Meetings/` file count unchanged (39 before and after), and every
   file's `LastWriteTime` unchanged by this run (most-recent timestamp
   across the whole folder remained 2026-08-11, predating this session) —
   `ensure_meeting_note_baseline_frontmatter` correctly no-op'd because
   every baseline key was already present, so "topped up" here means
   "correctly recognized as already-existing and left untouched," which is
   itself the correct idempotent-rerun behavior. `.second-brain/
   processed_meeting_ids.json` gained new `global_appointment_id` entries
   (confirmed: the Strategic-series GID is now present) while its
   pre-existing legacy `EntryID` entries (confirmed: the same series'
   pre-fix `EntryID` value is still present) were left untouched — matches
   `ADR-013` point 3's coexistence design exactly. **This is the concrete
   evidence `ADR-019`'s Decision point 3 cites for dropping the
   `GlobalAppointmentID`-hash tier entirely: it was never reached to
   create a new file in this or any other run, since it was `Blocked`
   before any further capture cycle ran.**

4. **[Tests step 4 — AC-09 regression check, real data, the original
   ESC-002 trigger] Re-verify the real recurring series live.** Combines
   findings 1 and 3 above: the coexistence/no-duplicate mechanism itself
   works correctly (step 3, PASS), but the AC's own conjunctive text ("each
   occurrence's global_appointment_id is confirmed distinct, AND no
   duplicate note is created on rerun") **FAILS as a whole** because the
   distinctness clause is false (finding 1). Practically: today's 39
   existing notes remain correct only because the filename still separately
   incorporates the event's *date* (unchanged from the pre-`T06` scheme) —
   exactly the same accidental protection `ESC-002` originally described
   for `EntryID`. The specific risk `ADR-013` was built to close — two
   occurrences of the same recurring series landing on the **same calendar
   date** — is **not closed** by this fix as implemented: since
   `global_appointment_id` does not vary per occurrence at all on this
   Outlook environment, two same-date occurrences would still produce an
   identical filename and still silently merge, exactly as `ESC-002`
   originally found for `EntryID`.

5. **[Tests step 5 — AC-07, new-scheme-only] Not performed.** Given finding
   1 (the core per-occurrence-uniqueness premise already falsified for the
   real trigger case), constructing throwaway same-subject/same-date
   calendar events to test the new scheme's collision behavior would not
   add new information — the new scheme's dedup suffix is only genuinely
   safe when `global_appointment_id` itself varies, which this environment
   has now shown it may not. Skipped rather than creating and cleaning up
   unnecessary live calendar-mutating test data pending an architect
   decision on how to proceed.

**Locked-AC-equivalent checklist (this task's own original `##
Acceptance Criteria`, undated/untagged bullets, addressed in order):**
- Bullet 1 (`global_appointment_id` field, native+DASL fallback, skip on
  double-failure): code correctly implements this exactly as specified;
  the native path succeeded (non-empty) for all 37 live events fetched, so
  the double-failure skip branch was not naturally exercised live this
  pass — not falsified, just not organically triggered.
- Bullet 2 (hash-based suffix, not raw slice): **verified PASS** (finding 2).
- Bullet 3 (`resolve_meeting_note_path` new-then-legacy lookup): **verified
  PASS** (finding 3).
- Bullet 4 (none of the pre-existing notes renamed/moved/altered):
  **verified PASS** (finding 3 — file count and `LastWriteTime` unchanged).
- Bullet 5 (`processed_meeting_ids.json` legacy entries untouched, new
  entries are `GlobalAppointmentID` values): **verified PASS** (finding 3).
- Bullet 6 (the real recurring series re-verified: distinct
  `global_appointment_id` per occurrence + no duplicate on rerun): **FAILS**
  (findings 1 and 4) — the distinctness half is false, live, for the exact
  series this task exists to fix.
- Bullet 7 (`MEMORY.md` updated): done — see `MEMORY.md` → Constraints.
- Bullet 8 (`CHANGELOG.md` entry appended): done.
- Bullet 9 (`ESCALATIONS.md` → `ESC-002` updated to reflect completion):
  done, but **not** flipped to `Resolved` — `ESC-002`'s own named risk is
  not actually closed by this build; see `ESCALATIONS.md` → `ESC-002`'s
  2026-08-12 update and the `ESC-012` entry it points to.

**Disposition at the time: `status: Blocked`, not `Done`.** Superseded
2026-08-12 by the `ADR-019` redesign at the top of this file — this task
is now `status: Ready` against the new design, not `Blocked` against this
one. The built `ADR-013`-era code described in this log is being replaced
by this same task's own new build, not reverted-and-abandoned separately —
the "left in place, not reverted" disposition below described the state
*before* this redesign; the redesign itself is what now supersedes that
code.

**Original assumption logged for human spot-check (scope-internal
judgement call, not an escalation on its own):** ran the live regression
check (finding 3/step 3) against the real, already-populated vault rather
than a fixture, per this task's own Tests section instruction and
`MEMORY.md`'s existing precedent for this story. This is a real,
additive-only write pass (confirmed no file touched by `LastWriteTime`),
consistent with every other live-verification pass this story's own
`T03`/`T05` already performed.
