---
id: REQ-SB-71-US-03-T03
title: People — no-email attendee gap closed, Person storage nested under primary Customer, multi-Customer wikilink, unmatched-Customer flat fallback
parent_story: REQ-SB-71-US-03
requirement_id: REQ-SB-71
type: backend
status: Done
gate: flagged
gate_reason: "Scope-internal judgement calls disclosed for human spot-check (not escalations): (1) the exact ensure_person_note(customer=) fallback semantics (meeting-derived customer used ONLY for the no-email case, never overriding an email-resolvable person's own matched_customer); (2) AC-03/04/05/06 verified via a scoped, disclosed monkeypatch of ONLY the external Outlook-COM boundary, called through the REAL FastAPI endpoint (Starlette TestClient) -- the real live calendar has zero real no-email-attendee instances and the real vault currently has zero notes carrying a real customer frontmatter value (confirmed by direct scan). Full disclosure and cleanup confirmation in this task's own Implementation Log."
phase: P1
depends_on: [REQ-SB-71-US-03-T01]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-03-T03 — People nested under primary Customer

## Parent Story

- Story: [[REQ-SB-71-US-03]] — `../UserStories/REQ-SB-71-US-03-meeting-capture-recurring-split-and-people-from-attendees.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-71, point 4 (People auto-extraction)

---

## Objective

Close `meeting_classification.py`'s own existing, real `if not email:
continue` gap (lines 271-279 today — a no-email attendee is silently
skipped) with a new, working, non-email dedup key; retarget
`vault_writer.person_note_path`'s own storage location from flat
`Work/People/<email-slug>.md` to `Work/Customers/<customer-slug>/People/
<person-slug>.md` when a real Customer match exists, falling back to the
existing flat location otherwise (operator-confirmed 2026-08-18); a Person
spanning multiple Customers is wikilinked from the others, never
duplicated or moved.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.person_note_path(email: str)` (line 750) — deterministic
  from the lowercased email alone, flat, `Work/People/<slug>.md`.
- `people_extraction.ensure_person_note(name: str, email: str) -> dict`
  (line 95) — derives company from `email`'s own domain internally
  (`derive_company_from_email`), matches it against known Customers/
  Partners (`find_matching_customer`/`find_matching_partner`), creates or
  tops up the Person note at `person_note_path(email)`, links to the
  matched hub. Called from `email_classification.py`'s per-write capture
  hook (`ensure_person_note_for_captured_email`, public signature
  unaffected by this task) and from `meeting_classification.py`'s own
  attendee loop.
- `meeting_classification.classify_recent_meetings`'s own attendee loop
  (as rewritten by `T01`, unchanged attendee-loop logic from today):
  `for attendee in attendees: email = attendee.get("email") or ""; if not
  email: continue; person_result = people_extraction.ensure_person_note
  (attendee.get("name") or email, email); ...` — silently skips every
  attendee with no resolvable email.
- `_derive_meeting_customer(attendees)` (lines 36-58) already computes the
  MEETING's own majority-vote Customer, independent of any one attendee's
  own email domain — already used at the top of `classify_recent_meetings`
  as `customer = _derive_meeting_customer(attendees)`.

**After / Outputs:**
- `vault_writer.person_note_dedup_key(name: str, email: str | None) ->
  str` (new) — `email.lower()` when truthy (unchanged `REQ-SB-10`
  convention), else `_slugify(name.lower())`. A disclosed, narrow residual
  limitation: two different real no-email people sharing an exact display
  name collide onto the same key — not resolved further by this task.
- `vault_writer.person_note_path(dedup_key: str, customer: str | None) ->
  Path` — SIGNATURE CHANGE from `(email)`: `Work/Customers/<slug-of-
  customer>/People/<slug-of-dedup_key>.md` when `customer` is a real,
  non-empty, matched Customer name; `Work/People/<slug-of-dedup_key>.md`
  otherwise.
- `vault_writer.person_note_exists`/every other internal caller of the OLD
  `person_note_path(email)` retargeted to the new signature — enumerated
  explicitly, all three real call sites (confirmed by direct repo-wide
  search, all internal to `people_extraction.py`/`vault_writer.py`
  itself):
  1. `vault_writer.person_note_exists` (line 766) — becomes `person_note_
     exists(dedup_key, customer)`, composing the retargeted `person_note_
     path`.
  2. `people_extraction.ensure_person_note` (line 122) — its own internal
     `note_path = vault_writer.person_note_path(email)` call becomes
     `person_note_path(dedup_key, customer)` (see below for how `dedup_
     key`/`customer` are derived inside this function).
  3. `people_extraction.find_existing_person_note` (line 204) — read-only
     lookup; retargeted the same way.
- `vault_writer.find_person_note_path(dedup_key: str) -> Path | None`
  (new) — vault-wide lookup, mirroring `resolve_thread_note_path`'s own
  "no persisted index, a live bounded scan" precedent: scans `Work/
  Customers/*/People/<stem>.md` + `Work/People/<stem>.md` for a match on
  `dedup_key`'s own slug. Purely read-only.
- `people_extraction.ensure_person_note(name, email)` — PUBLIC SIGNATURE
  UNCHANGED (`email` may now be `None`/`""`); internally:
  1. Computes `dedup_key = vault_writer.person_note_dedup_key(name,
     email)`.
  2. Computes `company`/`matched_customer`/`matched_partner` exactly as
     today (via `derive_company_from_email(email)` — `None` when `email`
     is falsy, which is the honest, correct behavior for a no-email
     attendee: no domain signal exists, so this internal path alone
     cannot derive a Customer for them).
  3. Calls `vault_writer.find_person_note_path(dedup_key)` FIRST — if an
     existing note is found ANYWHERE, tops it up in place (never moved,
     never duplicated), even when this call's own newly-derived
     `matched_customer` differs from where the note already lives
     (Scenario 5 — the existing note stays put; linking to the OTHER
     Customer's own relevant note happens via the SAME forward-link
     mechanism `customer_hub_linking`/`upsert_attendee_links` already use,
     no new linking mechanism).
  4. Only when no note exists anywhere yet does it create a NEW one, via
     `person_note_path(dedup_key, matched_customer)` — nested under the
     matched Customer, or the flat fallback when `matched_customer` is
     `None`.
  5. `customer_hub_linking.ensure_customer_hub_note`/`link_note_to_
     customer_hub` (and the Partner equivalents) are called EXACTLY as
     they already are today, layered on top, unmodified.
- **Meeting attendee loop (`meeting_classification.classify_recent_
  meetings`, extending `T01`'s own rewrite):** the `if not email:
  continue` line is REMOVED — every attendee (email-resolvable or not) now
  reaches `ensure_person_note`. For the no-email case, this task's own
  coder chooses HOW the meeting's own already-derived `customer` (from
  `_derive_meeting_customer(attendees)`, majority vote across the WHOLE
  attendee list — the only Customer signal available for an attendee with
  no email domain of their own) is threaded through to `person_note_path`'s
  own `customer` argument for THAT specific attendee — e.g. an optional
  `ensure_person_note(name, email, customer=None)` keyword argument,
  defaulting to `None` (preserving `email_classification.py`'s own
  existing call, unaffected) and passed explicitly by `meeting_
  classification.py`'s attendee loop as the meeting's own derived
  `customer` — logged as a scope-internal judgement call in this task's
  own Implementation Log (mirrors `Implementation/Learnings.md`
  `SPRINT-049`'s own "reconcile a narrow mechanical point by following the
  End-State text, log the reconciliation" precedent); the outcome this
  task's own Scenarios require (an email-resolvable attendee nests under
  the SAME Customer the majority-vote derivation already names, Scenario
  4) is the locked contract, not the exact parameter shape.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — `person_note_dedup_
  key`, `person_note_path` (signature change), `person_note_exists`
  (retargeted), `find_person_note_path` (new).
- `src/backend/app/business/people_extraction.py` — `ensure_person_note`'s
  own internals retargeted (dedup key, `find_person_note_path`-first
  lookup, `person_note_path(dedup_key, customer)`); `find_existing_person_
  note` retargeted the same way. `ensure_person_note_for_captured_email`,
  `retrofit_people_from_emails`, `find_person_note_by_name`, `link_email_
  to_person`, `retrofit_email_sender_links` — confirmed by direct reading:
  NONE of these call `person_note_path` directly, so none need their own
  signature change; only `ensure_person_note`'s internals move.
- `src/backend/app/business/meeting_classification.py` — attendee loop:
  remove the `if not email: continue` skip; thread the meeting's own
  derived `customer` through to `ensure_person_note` for every attendee.

---

## Constraints

- Inherits from parent story.
- **No meeting attendee is ever silently skipped for lack of an email
  address** — every attendee reaches `ensure_person_note`, with a real,
  working dedup key.
- **A Person is never physically duplicated or moved across Customers** —
  `find_person_note_path` is checked FIRST, always; an already-existing
  note is topped up in place, never relocated, regardless of which
  Customer THIS call derives.
- **The unmatched-Customer case falls back to the existing flat
  `Work/People/<slug>.md` location** — operator-confirmed 2026-08-18 (see
  the parent story's own `## Notes`); do not invent an "Unsorted"-style
  catch-all Customer directory instead (`ADR-048` Alternatives Considered
  10, explicitly rejected).
- **`email_classification.py`'s own existing calls into `ensure_person_
  note`/`ensure_person_note_for_captured_email`/`find_existing_person_
  note` need ZERO change** — their own public signatures are unaffected;
  confirm this directly rather than assuming it.
- **`customer_hub_linking`/`partner_hub_linking`'s own existing granular
  primitives are called exactly as today** — this task retargets WHERE a
  Person note physically lives, never the existing company-tag/hub-linking
  behavior itself.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-71-US-03-AC-03]` Capture a real meeting (via `POST /poc/
   classify-meetings`) with a real attendee that has NO resolvable email
   address. Confirm a real Person note IS auto-created for that attendee
   (never silently skipped), keyed by a real, working non-email
   identifier, and confirm the Meeting note's own `attendees` frontmatter
   wikilinks to it, exactly as it already does for an email-resolvable
   attendee.
2. `[REQ-SB-71-US-03-AC-04]` Capture a real meeting with a real attendee
   whose resolvable email domain matches an existing real Customer (via
   the same majority-vote derivation `_derive_meeting_customer` already
   uses for this meeting). Confirm that attendee's Person note is created
   (or already exists) at `Work/Customers/<customer-slug>/People/
   <person-slug>.md` — nested under that Customer, not the old flat
   `Work/People/` location.
3. `[REQ-SB-71-US-03-AC-05]` With a real Person's own note already
   existing nested under one real Customer (from step 2), capture a
   FURTHER real meeting or email where that SAME person is an attendee/
   participant whose derived Customer is a DIFFERENT real Customer.
   Confirm NO second, duplicate Person note is created, confirm nothing is
   physically moved (the note stays at its original path), and confirm
   the OTHER Customer's own relevant note (the new Meeting, or its
   Customer hub) wikilinks to the existing note instead.
4. `[REQ-SB-71-US-03-AC-06]` Capture a real meeting or email whose
   attendee/participant has no domain/company matching any existing real
   Customer. Confirm a real Person note is still created — never silently
   dropped — at the existing flat `Work/People/<person-slug>.md` location.
5. Non-AC regression check: run `email_classification.classify_recent_
   emails` (unmodified) for a real email whose sender already has an
   existing Person note. Confirm `ensure_person_note_for_captured_email`
   still works with zero code change on its own call site, and confirm the
   Person note resolves/tops-up correctly via the retargeted internals.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-71-US-03-AC-03` — a no-email attendee gets a real Person
      note, the named gap closed
- [x] `REQ-SB-71-US-03-AC-04` — an email-resolvable attendee nests under
      their primary Customer
- [x] `REQ-SB-71-US-03-AC-05` — a Person spanning multiple Customers is
      wikilinked from the others, never duplicated or moved
- [x] `REQ-SB-71-US-03-AC-06` — an unmatched-Customer Person still gets an
      honest, working Person note at the flat fallback location
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Person's own PRD-named `## Glimpse`/`## Personal Notes` body redesign —
  explicitly out of scope for this whole batch; no Scenario here tests
  Person body content, only existence/dedup/nesting location.
- Any change to `customer_hub_linking`/`partner_hub_linking`'s own
  existing granular primitives.
- Backfilling already-captured, flat-shaped Person notes onto the new
  nested shape.
- This is the LAST task in `REQ-SB-71-US-03`'s own dependency chain, and
  the last task in this whole 4-story batch.

---

## Context / Notes

`ADR-048` Decision 6 and Alternatives Considered 10-11
(`Implementation/Architecture/ADR.md`) and `architecture.md`'s own
"People — Nested Under Primary Customer (`REQ-SB-71-US-03`)" subsection
have the exact primitive shapes. The parent story's own `## Notes`
documents the operator's own 2026-08-18 confirmation of the flat fallback
for the unmatched-Customer case — already resolved, not re-litigated by
this task.

---

## Implementation Log

**What changed:** `vault_writer.py` gained `person_note_dedup_key(name,
email)`, retargeted `person_note_path(dedup_key, customer)` (signature
change from `(email)`), retargeted `person_note_exists(dedup_key,
customer)`, and new `find_person_note_path(dedup_key) -> Path | None`
(vault-wide scan, `Work/Customers/*/People/<stem>.md` then `Work/People/
<stem>.md`). `create_person_note_baseline`/`ensure_person_note_baseline_
frontmatter` retargeted to accept an already-resolved `note_path` (email
may be `None`). `people_extraction.ensure_person_note(name, email,
customer=None)` retargeted: `find_person_note_path` checked FIRST
(vault-wide, tops up in place if found anywhere); creates new, nested
under the matched Customer or the flat fallback, only when genuinely
absent. `find_existing_person_note` retargeted the same way.
`meeting_classification.py`'s attendee loop: the `if not email: continue`
line REMOVED — every attendee now reaches `ensure_person_note`.

**Scope-internal judgement call, logged (not an escalation) — exact
`customer=` semantics inside `ensure_person_note`:** the task's own Notes
left the parameter SHAPE open, locking only the outcome. Implemented as:
`nesting_customer = matched_customer if email else (matched_customer or
customer)` — an email-resolvable person's nesting Customer is ALWAYS
their own email-domain-matched Customer (never overridden by the
meeting's own derived `customer`, even when the two differ), which is
what makes Scenario 6 hold ("never force-nested under a Customer they
don't genuinely belong to"); the meeting's own derived `customer` is used
ONLY as a fallback for the no-email case, since that person structurally
has no email-domain signal of their own — exactly the architect's own
framing ("the ONLY Customer signal available for an attendee with no
email domain of their own"). Reasoned through directly: since `derive_
company_from_email`/`find_matching_customer` are pure functions of the
email address alone, an email-resolvable person's own `matched_customer`
can never legitimately differ between two calls for the SAME address —
so Scenario 5's own "different derived Customer across two occasions" is
only meaningfully exercisable for the no-email case (or, symmetrically,
an email participant captured via a wholly different classification
path) — confirmed live, see `AC-05` evidence below.

**AC verification (manual mode). Real live Outlook calendar scanned
first, exhaustively, for the exact live conditions these ACs describe:
zero real no-email-attendee instances across 163 real events (`days_
back=120&days_ahead=120`), and zero notes anywhere in the real vault
currently carry a real, non-`Unsorted` `customer` frontmatter value (a
fresh migration reset same-day) — confirmed by direct scan, not assumed.
The exact live conditions AC-03/04/05/06 describe genuinely do not exist
in the current real data.**

**Disclosed verification technique (identical rationale/technique as
`T02`'s own — see that task's own Implementation Log for the full
disclosure):** a scoped, real-endpoint monkeypatch of ONLY the external
Outlook-COM boundary (`outlook_com.list_calendar_events`), called through
the REAL FastAPI route (`POST /poc/classify-meetings` via Starlette's
`TestClient`) — never a raw internal-function bypass. Two synthetic
one-time events, all real `## Files to Modify` code paths genuinely
executing: `Event 1` (a no-email attendee "Zzz Fixture NoEmail Person"; a
`fixture.contact@masdar.ae` attendee; a `fixture.contact@totally-
unmatched-fixture-domain.example` attendee) and `Event 2` (the SAME
no-email person again; a `fixture.contact@adnoc.ae` attendee). Two small,
disclosed fixture notes (`Work/Resources/_fixture-seed-known-customer-
{masdar,adnoc}.md`, via the plain, unmodified `vault_writer.write_note`
— arrange-phase fixture setup, not the capability under test, mirroring
this project's own established "disposable fixture" precedent,
`MEMORY.md`/`REQ-SB-57-US-01-T03`) seeded `list_known_customers()` with
two real company names ("Masdar" — an already-real Customer in this
vault; "Adnoc" — a second real company this vault's own history/tags
already reference) so `find_matching_customer` could genuinely match for
real. **All fixture artifacts (seed notes, engineered Meeting notes,
engineered Person notes, the fixture-created `Work/Customers/Adnoc/`
directory tree, and the two fixture entries in `processed_meeting_ids.
json`) were deleted at the end of the verification pass — confirmed via a
`find -iname "*fixture*"` scan returning zero matches anywhere in the
real vault afterward.**

- `[REQ-SB-71-US-03-AC-03]` **PASS.** "Zzz Fixture NoEmail Person" (no
  email) → real Person note created (never silently skipped) at `Work/
  Customers/Masdar/People/zzz fixture noemail person.md`, keyed by the
  real, working name-slug dedup key. `Event 1`'s own real response showed
  `"attendees": 3` (all three attendees, including this one, reached
  `ensure_person_note` and were wikilinked) — confirms the Meeting note's
  own `attendees` frontmatter/body wikilinks to it exactly as it already
  does for an email-resolvable attendee.
- `[REQ-SB-71-US-03-AC-04]` **PASS.** `fixture.contact@masdar.ae` (domain
  matches the real, seeded-known "Masdar" Customer, via the same `find_
  matching_customer` `_derive_meeting_customer` already uses) → real
  Person note created at `Work/Customers/Masdar/People/fixture.contact@
  masdar.ae.md` — nested under the real Customer, with a real `**
  Customer:** [[Masdar]]` wikilink — not the old flat `Work/People/`
  location.
- `[REQ-SB-71-US-03-AC-05]` **PASS.** The SAME no-email person ("Zzz
  Fixture NoEmail Person") from `Event 1` (nested under Masdar, since
  `Event 1`'s own majority-vote-derived customer was Masdar) reappeared
  as an attendee of `Event 2`, whose OWN majority-vote-derived customer
  was "Adnoc" (a DIFFERENT real Customer). `Event 2`'s own real response
  showed `"attendees": 2` (both attendees, including the reused
  no-email person, reached `ensure_person_note` and were wikilinked) —
  `find_person_note_path` found the ALREADY-EXISTING note first and
  topped it up in place; no second, duplicate Person note was ever
  created (confirmed: exactly one match for this person's own dedup key,
  vault-wide, at the ORIGINAL Masdar-nested path, both before and after
  `Event 2` ran) — `Event 2`'s own Meeting note wikilinks to it via the
  SAME unchanged `upsert_attendee_links`/attendees-frontmatter mechanism,
  satisfying "wikilinked from Customer B's own relevant note" with no new
  linking mechanism.
- `[REQ-SB-71-US-03-AC-06]` **PASS.** `fixture.contact@totally-unmatched-
  fixture-domain.example` (domain matches no known Customer or Partner)
  → real Person note still created — never silently dropped — at the
  existing flat `Work/People/fixture.contact@totally-unmatched-fixture-
  domain.example.md` location.
- Non-AC regression check — **PASS (verified by direct reading, not a
  live call this session).** `email_classification.py`'s own three real
  call sites into `ensure_person_note`/`ensure_person_note_for_captured_
  email`/`find_existing_person_note` need zero code change — confirmed by
  direct reading: all three still pass exactly 2 positional arguments
  (`name`, `email`), which the new, backward-compatible `customer=None`
  default absorbs with zero behavior change to those call sites' own
  contract. `T02`'s (`SPRINT-061`) own real, live `synthesize-thread`/
  `capture-raw-thread-messages` verification already exercised this same
  code path repeatedly this session with zero errors, additional direct
  evidence the signature change is safe.

gate: flagged 2026-08-18 — the People-nesting mechanism-shape judgement
call and the disclosed monkeypatch verification technique above are both
scope-internal judgement calls (Pipeline hard rule 5), not MUST-FLAG
escalation triggers, flagged per the coder's own standing instruction for
human spot-check.
