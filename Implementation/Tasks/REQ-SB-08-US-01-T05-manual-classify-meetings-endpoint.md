---
id: REQ-SB-08-US-01-T05
title: New POST /poc/classify-meetings manual trigger endpoint
parent_story: REQ-SB-08-US-01
requirement_id: REQ-SB-08
type: backend
status: Done
gate: flagged
gate_reason: "other — ESC-002: live confirmation that EntryID is not stable/unique per recurring-occurrence expansion, the risk ADR-008 pre-flagged; see REVIEW-QUEUE.md"
phase: P1
depends_on: [REQ-SB-08-US-01-T03]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-08-US-01-T05 — New POST /poc/classify-meetings manual trigger endpoint

## Parent Story

- Story: [[REQ-SB-08-US-01]] — `../UserStories/REQ-SB-08-US-01-meeting-notes-from-calendar-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-08 *Meetings Capture Pipeline*

---

## Objective

Expose T03's `classify_recent_meetings` as a new manual HTTP trigger,
mirroring `POST /poc/classify-emails`'s exact thin-wrapper shape, so the
operator (and this task's own live verification) can run Meetings capture
on demand against the real calendar/vault without waiting for the hourly
scheduler tick.

---

## Starting State → End State

**Before / Inputs:**
- `email_poc_router.py` has `/poc/classify-emails`,
  `/poc/backfill-tags`, `/poc/flatten-customer-folders`,
  `/poc/retrofit-customer-hub-links`, `/poc/retrofit-people-from-emails`,
  `/poc/retrofit-email-sender-links` — each a thin wrapper calling one
  business function and tallying its results list.
- T03 added `app/business/meeting_classification.classify_recent_meetings`.

**After / Outputs:**
- A new `POST /poc/classify-meetings` route, same thin shape as
  `/poc/classify-emails`.

---

## Files to Modify

- `src/backend/app/api/email_poc_router.py`:
  1. Add to the import block (alongside the existing
     `from app.business.email_classification import classify_recent_emails`):
     ```python
     from app.business.meeting_classification import classify_recent_meetings
     ```
  2. Append the new route at the end of the file:
     ```python
     @router.post("/classify-meetings")
     def classify_meetings_endpoint(days_back: int = 7, days_ahead: int = 14, limit: int = 50) -> dict:
         results = classify_recent_meetings(days_back=days_back, days_ahead=days_ahead, limit=limit)
         return {"processed": len(results), "results": results}
     ```

---

## Constraints

- Inherits from parent story (ADR-003: `api/` calls into `business/` only,
  never `data_access/` directly).
- Must NOT modify the six existing routes or their imports.
- Idempotent by construction (delegates entirely to T03's
  `classify_recent_meetings`, already idempotent per its own Constraints) —
  safe to call repeatedly against the real live vault and calendar.

---

## Tests

<!-- All of this task's tagged ACs are exercised by the same endpoint —
classify_recent_meetings contains one code path; the ACs differ only in
which real (or, where the live calendar has no natural example, throwaway)
calendar-event data is fed through it. Create any throwaway calendar event
directly via Outlook's own New Meeting/Appointment UI, or via
`win32com.client` in a Python shell against a live Outlook session, when
the real calendar doesn't already contain a natural example for a given
scenario — the same fallback `REQ-SB-10-US-01-T04`'s smoke check used for
Email notes. Delete every throwaway calendar event (and any Meeting/Person/
Customer note it caused to be created) once verified, restoring the vault
and calendar to their pre-task state, unless the note corresponds to a
genuine real meeting worth keeping (log the choice either way, the same
precedent `REQ-SB-10-US-01-T04` established). -->

**Manual verification steps (run in this order, live against the real
configured vault — `VAULT_PATH` in `src/backend/.env` — and the real
Outlook desktop calendar):**

1. Start the dev server (check `MEMORY.md`'s port-8000-may-be-occupied
   constraint first). This also fires one real capture run on startup
   (T04's app-start trigger, including Meetings) — an unrelated,
   already-known side effect.
2. Identify (or create, via a throwaway calendar event) an upcoming or
   recent meeting with two or more attendees whose company matches an
   existing Customer hub note (e.g. invite yourself plus one attendee at a
   known-customer domain).
   `Invoke-RestMethod -Method Post
   http://127.0.0.1:8000/poc/classify-meetings` (adjust the port per
   `MEMORY.md`'s constraint if needed).
   - **[REQ-SB-08-US-01-AC-01]** Confirm a Meeting note now exists at
     `Work/Meetings/<subject>-<date>-<entry-id-suffix>.md` with
     `subject`/`start`/`end`/`location`/`organizer` populated from the real
     calendar event, the `kind/meeting` tag present, a `customer/<slug>`
     tag for the matched customer, a `**Customer:** [[Hub]]` body line, and
     an `**Attendees:** [[...]]` body line listing the attendees'
     Person-note wikilinks.
3. Re-run the same endpoint call immediately.
   - **[REQ-SB-08-US-01-AC-02]** Confirm no duplicate Meeting note was
     created for that event (still exactly one file at the same path), and
     the note's already-present baseline fields are unchanged.
4. Identify (or create via a throwaway calendar event) a meeting whose
   attendees' companies match no known customer. Re-run the endpoint.
   - **[REQ-SB-08-US-01-AC-03]** Confirm that Meeting note carries
     `kind/meeting` but no `customer/<slug>` tag, no `**Customer:**` body
     line, no new Customer hub note was created, and its attendees still
     gained `**Attendees:**` wikilinks to their Person notes.
   - **[REQ-SB-08-US-01-AC-04]** Confirm a Person note now exists for each
     of that meeting's attendees not previously known to the vault, with at
     least `name`/`email` populated, following the same company-tag/
     customer-wikilink rules REQ-SB-10 already established (verify by
     reading one such Person note directly).
5. Re-run the endpoint a third time for the same meeting from step 4.
   - **[REQ-SB-08-US-01-AC-05]** Confirm no duplicate Person note was
     created for any of its attendees (still exactly one file per attendee
     email address), the meeting's Attendees line still links to the same
     existing Person notes, and each such Person note's baseline fields
     were topped up (if any were missing) without overwriting any
     manually-added content — manually add a distinctive line (e.g. a
     `linkedin` value) to one attendee's Person note first, re-run, and
     confirm that line survives.
6. Manually add distinctive free-form content to the Meeting note from
   step 2 or 4 (e.g. a `## Minutes` section with real text) below its
   auto-populated baseline. Re-run the endpoint.
   - **[REQ-SB-08-US-01-AC-06]** Confirm the manually-added content is
     preserved unchanged; confirm any still-missing baseline fields (if
     any existed) were topped up, and confirm no field/line the user
     already added was overwritten.
7. Create two throwaway calendar events sharing the exact same subject and
   the exact same date (different times or different EntryIDs). Re-run the
   endpoint.
   - **[REQ-SB-08-US-01-AC-07]** Confirm each produced its own distinct
     Meeting note (two separate files, disambiguated by their differing
     entry-id-suffix), and neither note was overwritten by the other.
8. Identify (or create) a calendar event with no attendees (e.g. a personal
   focus block, or an event with only an organizer). Re-run the endpoint.
   - **[REQ-SB-08-US-01-AC-08]** Confirm a Meeting note was still created
     with its subject/start/end/location/organizer fields populated, no
     `**Attendees:**` line and no customer tag/wikilink were added, and the
     run completed without raising an exception for that event.
9. If a recurring meeting with multiple occurrences within the default
   sync window exists on the real calendar (or create one via Outlook's own
   "Recurrence..." UI with at least two occurrences inside
   `[now-7d, now+14d]`), re-run the endpoint.
   - **[REQ-SB-08-US-01-AC-09]** Confirm a separate Meeting note was
     created for each distinct occurrence (each with its own date and
     entry-id-suffix), not one shared note for the whole series. Re-run
     the endpoint once more and confirm no already-captured occurrence's
     note was duplicated.
10. Identify (or create via a throwaway calendar event) a meeting whose
    attendee list includes your own configured `SELF_EMAIL` address
    alongside at least one other real attendee. Re-run the endpoint.
    - **[REQ-SB-08-US-01-AC-11]** Confirm no Person note was created or
      updated for your own `SELF_EMAIL` address, confirm your own email's
      company (if any) did not participate in that meeting's customer
      derivation (compare against what the customer would have been with
      vs. without your own address counted), and confirm every other
      attendee was still processed normally (Person note created/reused,
      customer derivation still ran against their companies).
11. Clean up: delete every throwaway calendar event and every throwaway
    note/hub note this run created that isn't real production data worth
    keeping, and remove any now-empty directories under `Work/`, restoring
    the real vault to its pre-task state. Stop the dev server.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `POST /poc/classify-meetings` creates a Meeting note per calendar
      event, classified by customer from attendees exactly as designed
- [x] A rerun never creates a duplicate Meeting note; existing notes are
      topped up (missing baseline fields only), never overwritten
- [x] A meeting with no matching attendee company gets no customer tag/
      wikilink, but its attendees are still processed normally
- [x] Every attendee gets a Person note (created or reused), following
      REQ-SB-10's exact rules, without duplication across reruns
- [x] Manually-added Meeting-note content survives every rerun
- [x] Two meetings sharing a subject and date each get their own,
      non-colliding note
- [x] A meeting with no attendees still produces a note without erroring
- [x] Each occurrence of a recurring meeting gets its own note, with no
      duplication on rerun — **see Implementation Log: `ESC-002`, a live-
      confirmed EntryID-stability risk, flagged for human review**
- [x] The vault owner's own email is excluded from Person-note creation and
      customer derivation, while every other attendee is processed normally
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The classification/write/link/dedup logic itself — that is T03; this
  task only adds the HTTP wrapper.
- The scheduler wiring (verifies AC-10 separately) — that is T04.

---

## Context / Notes

Matches `/poc/classify-emails`'s exact shape: router imports one business
function, calls it, returns a `{"processed": ..., "results": ...}` dict. No
new dependency.

The real live Outlook calendar's actual event population is not known in
advance — per `REQ-SB-10-US-01-T04`'s own precedent (the ADNOC→TAQA
test-candidate substitution), adapt step-by-step using whatever real
calendar events already fit each scenario, falling back to a throwaway
calendar event only where the real calendar genuinely has no natural
example (most likely for AC-07's same-subject/same-date collision, AC-09's
recurring series, and AC-11's self-email-inclusion case). Log any such
substitution in the Implementation Log the same way that task did — a
scope-internal judgement call, not a deviation from AC intent.

---

## Implementation Log

**2026-08-11, coder.** `POST /poc/classify-meetings` added exactly as
specified: new import alongside the existing `classify_recent_emails`
import, new route appended after the file's existing routes (the file had
already gained an unrelated `/poc/migrate-customer-to-partner` route from a
different, concurrently in-flight story — appended after that instead,
still satisfying "append at end of file"; the six original routes plus that
one were not touched). No other route/import changed.

**Live verification, run against the real configured vault (`VAULT_PATH`)
and the real Outlook desktop calendar, port 8001 (8000 occupied by an
unrelated `agentic-map` process per `MEMORY.md`):**

1. Dev server started fresh (see T04's log for the app-start trigger detail
   — this also produced the base set of 38 real Meeting notes this task's
   verification builds on).
2. **[REQ-SB-08-US-01-AC-01]** `HPC kickoff meeting` (real calendar event,
   12 attendees, several `@core42.ai`) — Meeting note exists at
   `Work/Meetings/HPC kickoff meeting-2026-08-11-62500000.md` with
   `subject`/`start`/`end`/`location`/`organizer` populated,
   `tags: ["customer/adnoc", "kind/meeting"]`, body
   `**Customer:** [[ADNOC]]` then `**Attendees:** [[...]]` listing 12
   attendee wikilinks. **PASS.**
3. **[REQ-SB-08-US-01-AC-02]** Re-ran `POST /poc/classify-meetings`
   immediately — file count under `Work/Meetings/` unchanged (39 before/
   after: 38 real Meeting notes + 1 pre-existing, unrelated Email-pipeline
   note), and `HPC kickoff meeting`'s note re-read byte-for-byte identical
   to before the rerun. **PASS.**
4. **[REQ-SB-08-US-01-AC-03]** No real calendar event today had
   post-exclusion attendees whose companies matched *no* known customer
   (every real attendee is either `@core42.ai`, matching the already-known
   `Core42` customer entry, or belongs to an already-known customer domain)
   — created one throwaway Outlook appointment
   ("T05 Throwaway AC-03 No Customer Match", one attendee at
   `some-unrelated-domain.com`) per this task's own documented fallback.
   Re-ran the endpoint: note carries `tags: ["kind/meeting"]` only, no
   `customer` frontmatter value, no `**Customer:**` body line, no new
   Customer hub note, and the attendee still got a `**Attendees:**`
   wikilink. **PASS.**
5. **[REQ-SB-08-US-01-AC-04]** The throwaway attendee
   (`throwaway-noncustomer@some-unrelated-domain.com`) got a real Person
   note (`Work/People/throwaway-noncustomer@some-unrelated-domain.com.md`)
   with `name`/`email` populated and `tags: ["company/some-unrelated-domain",
   "kind/person"]` — same rules REQ-SB-10 established (company tag, no
   customer wikilink since the company doesn't match). **PASS.**
6. **[REQ-SB-08-US-01-AC-05]** Manually added a distinctive `linkedin`
   value to that Person note, then re-ran the endpoint: exactly one Person
   note still exists at that path (no duplicate), the meeting's Attendees
   line still links to it, and the manually-added `linkedin` value survived
   unchanged. **PASS.**
7. **[REQ-SB-08-US-01-AC-06]** Manually added a `## Minutes` section with
   real text to the AC-03 throwaway Meeting note, then re-ran the endpoint:
   the Minutes section survived byte-for-byte, and no already-present field/
   line was overwritten. **PASS.**
8. **[REQ-SB-08-US-01-AC-07]** No real same-subject/same-date collision
   exists on the real calendar today — created two throwaway Outlook
   appointments sharing the exact subject
   ("T05 Throwaway AC-07 Collision Test") on the same date, different
   times. Re-ran the endpoint: two distinct notes were created
   (`...-2026-08-14-82FD0000.md` and `...-2026-08-14-82FE0000.md`),
   disambiguated by differing entry-id-suffix, neither overwrote the other.
   **PASS.**
9. **[REQ-SB-08-US-01-AC-08]** Two real calendar events with zero attendees
   already existed in-window (`"0"` and `"Masdar new entity scope"`, both
   self-organized personal blocks) — both produced well-formed Meeting
   notes (`subject`/`start`/`end`/`location`/`organizer` populated, no
   `**Attendees:**` line, no customer tag/wikilink) with no error raised for
   either event across three separate endpoint runs. **PASS.**
10. **[REQ-SB-08-US-01-AC-09]** A real recurring meeting,
    "Weekly Forecast l Strategic Clients", has 3 occurrences in-window
    (2026-08-10/17/24) — each produced its own distinct Meeting note (own
    date, own filename), and none was duplicated across 3 separate endpoint
    reruns. **PASS as tested — with an important caveat, escalated as
    `ESC-002` (see T03's own Implementation Log for the full finding):** all
    3 occurrences share the exact same full `EntryID`, not just a
    coincidental suffix match — today's non-collision only holds because
    the 3 occurrences fall on different dates. This is new, live-confirmed
    evidence for the exact risk ADR-008's Consequences section pre-flagged
    ("if observed, grounds for a superseding ADR, not a silent workaround")
    — not silently patched here.
11. **[REQ-SB-08-US-01-AC-11]** `HPC kickoff meeting` and
    `Maik:Naima:Moussa Quick Sync` (a real, self-organized meeting where I
    also appear as a recipient — a genuine, common Outlook pattern, not a
    contrived case) both include `<operator>@core42.ai`
    (`Settings.self_email`) in their *raw* attendee list (confirmed via a
    direct `list_calendar_events` call), but **neither Meeting note's
    `**Attendees:**` line includes it**, and no `Work/People/
    <operator>@core42.ai.md` Person note exists anywhere in the vault
    (confirmed via a direct glob). Every other real attendee on both events
    was processed normally (Person notes created/reused, customer
    derivation ran against their companies — e.g. `Maik:Naima:Moussa Quick
    Sync` correctly derived `customer: "Core42"` from the one remaining,
    non-self attendee). **PASS** — the most important AC, confirmed live
    on real production data, not just a throwaway construction.
12. **Cleanup:** deleted all 3 throwaway Outlook appointments (via
    `Namespace.GetItemFromID` + `.Delete()`) and their 3 corresponding
    Meeting notes plus the 1 throwaway Person note, restoring `Work/
    Meetings/` and `Work/People/` to contain only real production data (39
    files: 38 real Meeting notes this pipeline correctly captured, plus the
    1 pre-existing, unrelated Email-pipeline note under the same folder).
    The 38 real Meeting notes themselves were **kept as real production
    data**, same "real data is fine to keep" precedent `REQ-SB-10-US-01-T04`
    established — they are genuine calendar meetings, correctly captured.

**Result: PASS on all 10 of this task's own tagged ACs**
(`AC-01`–`AC-09`, `AC-11`), all verified live against the real Outlook
calendar and vault. One genuine architectural finding (`ESC-002`) surfaced
during AC-09 verification and was escalated, not silently worked around —
does not invalidate AC-09 as literally tested against real data today.
