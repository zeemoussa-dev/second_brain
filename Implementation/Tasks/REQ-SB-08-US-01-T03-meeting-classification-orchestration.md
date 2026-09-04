---
id: REQ-SB-08-US-01-T03
title: New app/business/meeting_classification.py orchestration module + Settings.self_email
parent_story: REQ-SB-08-US-01
requirement_id: REQ-SB-08
type: backend
status: Done
gate: flagged
gate_reason: "other — ESC-002: live confirmation that EntryID is not stable/unique per recurring-occurrence expansion, the risk ADR-008 pre-flagged; see REVIEW-QUEUE.md"
phase: P1
depends_on: [REQ-SB-08-US-01-T01, REQ-SB-08-US-01-T02]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-08-US-01-T03 — New app/business/meeting_classification.py orchestration module + Settings.self_email

## Parent Story

- Story: [[REQ-SB-08-US-01]] — `../UserStories/REQ-SB-08-US-01-meeting-notes-from-calendar-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-08 *Meetings Capture Pipeline*

---

## Objective

Add the single shared "fetch calendar events → exclude the vault owner →
derive a customer via majority vote → write/top-up the Meeting note → link
the matched customer hub + every attendee's Person note" orchestration
(ADR-008), plus the new `Settings.self_email` config field Scenario 11's
exclusion depends on.

---

## Starting State → End State

**Before / Inputs:**
- T01 added `outlook_com.list_calendar_events`. T02 added the Meeting-note
  vault_writer primitives, including `upsert_attendee_links`.
- `app/business/people_extraction.py` already exposes
  `derive_company_from_email`, `find_matching_customer`, `ensure_person_note`
  (all reused as-is, per the story's Constraints).
- `app/business/customer_hub_linking.py` already exposes
  `ensure_customer_hub_note(customer)`/`link_note_to_customer_hub(note_path,
  customer)` (the granular primitives, reused as-is — never
  `ensure_hub_note_and_link`, per the same carve-out `people_extraction.py`
  established).
- `app/config.py`'s `Settings` has no `self_email` field yet.

**After / Outputs:**
- `app/config.py`'s `Settings` gains a required `self_email: str` field;
  `src/backend/.env.example` gains a matching `SELF_EMAIL=` line.
- A new file, `app/business/meeting_classification.py`, exposing
  `classify_recent_meetings`.

---

## Files to Modify

- `src/backend/app/config.py`:
  ```python
  from pathlib import Path

  from pydantic_settings import BaseSettings, SettingsConfigDict


  class Settings(BaseSettings):
      model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

      compass_base_url: str
      compass_api_key: str
      compass_model: str
      vault_path: Path
      self_email: str


  settings = Settings()
  ```
  (Only change: the new `self_email: str` field, added after `vault_path`.)

- `src/backend/.env.example`:
  ```
  COMPASS_BASE_URL=
  COMPASS_API_KEY=
  COMPASS_MODEL=
  VAULT_PATH=
  SELF_EMAIL=
  ```
  (Only change: the new `SELF_EMAIL=` line, appended after `VAULT_PATH=`.)

- `src/backend/app/business/meeting_classification.py` (new file):

  ```python
  """Orchestrates the Meetings-capture pipeline (REQ-SB-08): fetch calendar
  events in the sync window, exclude the vault owner's own email from the
  attendee list, derive a customer via majority vote among attendee
  companies, write/top-up the Meeting note, link the matched customer hub
  and every attendee's Person note. Mirrors email_classification.py's shape
  exactly (ADR-008) and reuses people_extraction.ensure_person_note /
  customer_hub_linking's granular primitives as-is — no changes to either
  module's existing public functions, per the story's Constraints.
  """
  from __future__ import annotations

  from collections import Counter
  from pathlib import Path

  from app.business import customer_hub_linking, people_extraction
  from app.config import settings
  from app.data_access import outlook_com, vault_writer


  def _exclude_self(attendees: list[dict]) -> list[dict]:
      """Filters settings.self_email (case-insensitive) out of the attendee
      list before any attendee reaches Person-note creation or customer
      derivation (Scenario 11) — the vault owner is never captured as a
      Person and their own company never participates in the majority
      vote below."""
      self_email = settings.self_email.lower()
      return [a for a in attendees if (a.get("email") or "").lower() != self_email]


  def _derive_meeting_customer(attendees: list[dict]) -> str | None:
      """Majority vote among each (post-exclusion) attendee's matched
      customer, via the unchanged derive_company_from_email/
      find_matching_customer; ties broken by whichever matched customer
      was first encountered in attendee order (To then Cc) — the
      architecture.md-recorded tie-break rule. No match among any
      attendee means no customer at all (Scenario 3)."""
      match_counts: Counter[str] = Counter()
      first_seen_order: list[str] = []
      for attendee in attendees:
          company = people_extraction.derive_company_from_email(attendee.get("email") or "")
          matched = people_extraction.find_matching_customer(company)
          if matched:
              if matched not in match_counts:
                  first_seen_order.append(matched)
              match_counts[matched] += 1
      if not match_counts:
          return None
      max_votes = max(match_counts.values())
      for customer in first_seen_order:
          if match_counts[customer] == max_votes:
              return customer
      return None  # unreachable — defensive fallback only


  def classify_recent_meetings(days_back: int = 7, days_ahead: int = 14, limit: int = 50) -> list[dict]:
      """The shared "ensure this calendar event's Meeting note exists and
      is up to date" operation — called once per fetched event, every run.
      Deliberately does not gate on load_processed_meeting_ids as a skip
      check (see this module's own module-level note below on why) —
      meeting_note_exists()'s deterministic-filename check is what
      prevents duplicate notes (Scenario 2, 7, 9); every in-window event
      still flows through the idempotent top-up path on every rerun
      (Scenario 2, 6). mark_meeting_processed is still called every run as
      an audit record."""
      events = outlook_com.list_calendar_events(days_back=days_back, days_ahead=days_ahead, limit=limit)
      results: list[dict] = []

      for event in events:
          attendees = _exclude_self(event["attendees"])
          customer = _derive_meeting_customer(attendees)

          note_path = Path(vault_writer.meeting_note_path(event["subject"], event["start"], event["id"]))
          if vault_writer.meeting_note_exists(event["subject"], event["start"], event["id"]):
              vault_writer.ensure_meeting_note_baseline_frontmatter(
                  note_path, event["subject"], customer, event["start"], event["end"],
                  event["location"], event["organizer"],
              )
              created = False
          else:
              vault_writer.create_meeting_note_baseline(
                  event["subject"], customer, event["start"], event["end"],
                  event["location"], event["organizer"], event["id"],
              )
              created = True

          vault_writer.mark_meeting_processed(event["id"])

          # Attendee links are upserted BEFORE the customer link — each
          # insert lands at the very top of the body, so calling Attendees
          # first and Customer second is what puts the Customer line
          # above the Attendees line, matching the resolved schema's
          # documented order (**Customer:** ... followed by
          # **Attendees:** ...).
          person_stems: list[str] = []
          for attendee in attendees:
              email = attendee.get("email") or ""
              if not email:
                  continue
              person_result = people_extraction.ensure_person_note(attendee.get("name") or email, email)
              person_stems.append(Path(person_result["note_path"]).stem)
          if person_stems:
              vault_writer.upsert_attendee_links(note_path, person_stems)

          linked = False
          if customer:
              customer_hub_linking.ensure_customer_hub_note(customer)
              linked = customer_hub_linking.link_note_to_customer_hub(note_path, customer)

          results.append({
              "subject": event["subject"],
              "note_path": str(note_path),
              "created": created,
              "customer": customer,
              "linked": linked,
              "attendees": len(person_stems),
          })

      return results
  ```

---

## Constraints

- Inherits from parent story (ADR-003 layering: no HTTP, no direct
  filesystem I/O — every read/write goes through `vault_writer`,
  `people_extraction`, or `customer_hub_linking`; idempotency is
  load-bearing, real live vault and real live Outlook calendar).
- Must NOT modify `people_extraction.py`, `customer_hub_linking.py`,
  `outlook_com.py`, or `email_classification.py` — this task only adds the
  new module and the two config files.
- Must call `customer_hub_linking.ensure_customer_hub_note` and
  `customer_hub_linking.link_note_to_customer_hub` directly — never
  `customer_hub_linking.ensure_hub_note_and_link` — and only after
  `_derive_meeting_customer` confirms a real match. Load-bearing carve-out
  from the parent story's Constraints.
- Every attendee (post-exclusion) must get the exact
  `people_extraction.ensure_person_note(name, email)` treatment, unchanged
  — no parallel/duplicate Person-note mechanism.
- `_exclude_self` must run before both Person-note creation and customer
  derivation — Scenario 11's ordering requirement.
- **Design note, not an escalation:** `classify_recent_meetings` does not
  early-`continue` on `load_processed_meeting_ids()` the way
  `classify_recent_emails` does on `load_processed_email_ids()`. Scenario
  2's own text ("the scheduled capture run processes the same calendar
  event again ... topping up any baseline fields it may still be missing")
  and Scenario 6 both describe an in-window event still flowing through
  the top-up path on rerun, not being hard-skipped — the actual
  no-duplicate guarantee for Meetings comes from the deterministic
  EntryID-suffixed filename plus `meeting_note_exists()`'s
  create-vs-top-up branch (the same "ensure" idempotency pattern already
  used for Person/Customer-hub notes), not from ID-based skipping.
  `processed_meeting_ids.json` is still written every run (an audit trail
  for future observability, REQ-SB-11) — this is a decomposer-level
  resolution of an underspecified mechanism question, not a deviation from
  ADR-008 (which specifies the file's *shape*, not that it must gate the
  loop) or from any Accepted requirement; do not "fix" this by adding a
  skip-check without checking with the human first, since doing so would
  break Scenario 2/6's literal top-up requirement.

---

## Tests

<!-- This task's own functions are exercised end-to-end, live, by T05 (the
manual /poc/classify-meetings endpoint — most of this story's locked ACs)
and T04 (the scheduler wiring — AC-10). The smoke checks below are
non-AC-tagged confirmations that this module's functions behave correctly
in isolation before T04/T05 build on them. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`, with
   `SELF_EMAIL` set in `.env` to your own real address, call
   `_exclude_self([{"name": "Me", "email": settings.self_email.upper()},
   {"name": "Real Attendee", "email": "someone@example.com"}])` (mixed
   casing deliberately) and confirm only the `"someone@example.com"` entry
   remains.
2. Non-AC smoke check: call `_derive_meeting_customer([{"name": "A",
   "email": "person1@core42.ai"}, {"name": "B", "email":
   "person2@core42.ai"}, {"name": "C", "email":
   "person3@some-unrelated-domain.com"}])` against the real vault (Core42
   should be a known customer per prior stories) and confirm it returns
   `"Core42"` (2 votes beats 1). Call it again with an attendee list where
   no company matches any known customer and confirm it returns `None`.
3. Non-AC smoke check: call `classify_recent_meetings(days_back=1,
   days_ahead=1, limit=5)` against the real live Outlook calendar and vault.
   Confirm it returns a list without raising, and that any Meeting note it
   created is well-formed (readable frontmatter, `type: "Meeting"`). Clean
   up any note this smoke check created against the real vault, or leave it
   in place as real production data if it corresponds to a genuine
   upcoming/past meeting (the same "real data is fine to keep" precedent
   `REQ-SB-10-US-01-T04` established) — note the choice in the
   Implementation Log either way.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `Settings.self_email` is a required, `.env`-sourced field;
      `.env.example` documents it
- [x] `_exclude_self` removes the vault owner's own email
      (case-insensitively) from an attendee list before it reaches
      Person-note creation or customer derivation
- [x] `_derive_meeting_customer` tallies matched-customer votes per
      attendee and returns the majority winner, tie-broken by first
      encountered order, or `None` when no attendee matches
- [x] `classify_recent_meetings` creates a baseline Meeting note when
      missing, tops up only missing baseline keys when it already exists,
      upserts attendee links, and only calls `customer_hub_linking`'s two
      granular primitives (never `ensure_hub_note_and_link`) after a
      confirmed customer match
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring `classify_recent_meetings` into the recurring scheduler tick —
  that is T04.
- Exposing it as a manual HTTP trigger — that is T05.

---

## Context / Notes

Mirrors `people_extraction.py`'s existing shape: a single business module
composing another business module (`customer_hub_linking`), calling only
into `vault_writer`/`people_extraction`/`outlook_com` (never doing
filesystem/COM I/O itself), returning a per-event results list the caller
(T05's endpoint) tallies for its HTTP response — the same permitted
business-to-business composition `architecture.md` already documents for
`people_extraction.py`.

**Call-order reminder (see the code's own inline comment):**
`insert_body_line_if_missing`/`upsert_attendee_links` always insert their
line at the very top of the body — the *last* call wins the top slot. To
get the resolved schema's documented order (Customer above Attendees), the
Attendees upsert must run before the Customer link, not after.

---

## Implementation Log

**2026-08-11, coder.** `Settings.self_email: str` added to `app/config.py`
(after `vault_path`); `SELF_EMAIL=` added to `.env.example`. New file
`app/business/meeting_classification.py` created exactly as specified
(`_exclude_self`, `_derive_meeting_customer`, `classify_recent_meetings`).
No changes to `people_extraction.py`, `customer_hub_linking.py`,
`outlook_com.py`, or `email_classification.py` (confirmed by diff).

**`self_email` value:** determined via a one-time, read-only Outlook COM
probe (`Namespace.CurrentUser` → `GetExchangeUser().PrimarySmtpAddress`) —
not guessed, not defaulted — yielding `<operator>@core42.ai`, set in the
local `.env` (gitignored). This does not deviate from ADR-008 (which
rejected a *dynamic runtime* lookup as the config's source, not a one-time
COM-assisted determination of the static value to put in `.env`).

**Non-AC smoke checks (manual verification steps 1-3):**
1. `_exclude_self` with a mixed-case `self_email` entry plus one real
   attendee — only the real attendee remained. PASS.
2. `_derive_meeting_customer` with 2 Core42-domain attendees + 1 unrelated —
   returned `"Core42"` (majority); with only an unrelated-domain attendee —
   returned `None`. PASS.
3. `classify_recent_meetings(days_back=1, days_ahead=1, limit=5)` against
   the real live Outlook calendar/vault — returned 5 well-formed results, 5
   real Meeting notes created (`type: "Meeting"`, correct customer
   derivation, e.g. `HPC kickoff meeting` → `ADNOC`, `Building the Infra
   Foundation for Masdar Data Lake` → `Masdar`). **Kept as real production
   data** (genuine calendar meetings), same "real data is fine to keep"
   precedent `REQ-SB-10-US-01-T04` established — not deleted.

**Scenario 11 confirmed live in this same run:** `HPC kickoff meeting`'s raw
attendee list (fetched separately via `list_calendar_events`) includes
`<operator>@core42.ai`; the written note's `**Attendees:**` line does
**not** include it — confirmed the self-exclusion filter works end-to-end,
not just at the unit level.

**Genuine finding, escalated as `ESC-002` (not a locked-AC failure, but
material new information bearing on ADR-008's own honestly-flagged risk):**
while investigating a real recurring meeting ("Weekly Forecast l Strategic
Clients", occurring 2026-08-10/17/24), all three distinct occurrences
returned by `list_calendar_events` (`IncludeRecurrences = True`) carry the
**exact same full `EntryID` string** — not just a coincidental 8-char-suffix
match, the entire ID is identical across occurrences. This directly
confirms the risk ADR-008's Consequences section named ("Outlook's
documented behaviour for EntryID stability across IncludeRecurrences=True
occurrence expansion is not something either codebase has had to stress-
test... grounds for a superseding ADR... not a silent workaround, if
observed"). **Today's live behavior is still correct** — each of the 3
occurrences got its own distinct Meeting note, because they fall on
different dates and the filename is `subject-date-entryid[-8:]`, so the
differing dates alone kept the filenames from colliding. But the
*underlying* per-occurrence dedup key ADR-008 specified (EntryID) is
empirically **not actually unique per occurrence** — only the combination
of (date, EntryID-suffix) happens to disambiguate today's real data. A
future recurring meeting with two occurrences landing on the exact same
calendar date (e.g. a twice-daily recurring meeting) would produce an
identical filename for both, and the second occurrence would be silently
treated as "already exists, top up only" — merging two distinct meetings
into one note. Per ADR-008's own explicit instruction, this is **not**
silently worked around (e.g. by unilaterally adding `GlobalAppointmentID`
myself) — logged in `ESCALATIONS.md` (`ESC-002`) and `REVIEW-QUEUE.md` for
a human decision on a superseding ADR.

**Result: PASS** for every literal AC in this task and for Scenario 11/
Scenario 9 as tested against real data — with the above finding flagged for
human review, not blocking this task's own completion.
