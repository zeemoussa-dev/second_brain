---
id: REQ-SB-16-US-01-T03
title: Extend people_extraction.py with a Partner-matching branch (find_matching_partner, ensure_person_note)
parent_story: REQ-SB-16-US-01
requirement_id: REQ-SB-16
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-16-US-01-T02]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-16-US-01-T03 — Extend people_extraction.py with a Partner-matching branch (find_matching_partner, ensure_person_note)

## Parent Story

- Story: [[REQ-SB-16-US-01]] — `../UserStories/REQ-SB-16-US-01-partner-hub-notes-and-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-16 *Partner Hub Notes & Graph Connectivity*

---

## Objective

Add `find_matching_partner` (mirroring `find_matching_customer` exactly)
and extend `ensure_person_note` with a second, mutually-exclusive branch:
Customer is checked first (unchanged); Partner is checked only when no
Customer match was found. This is the actual "Person-note orchestration"
mechanism Scenarios 1–4 and 8 exercise — REQ-SB-16 scopes Partner linking
specifically to this Person-note path, not a new capture-pipeline hook (see
the story's own Non-Goals).

---

## Starting State → End State

**Before / Inputs:**
- `people_extraction.ensure_person_note` currently calls
  `find_matching_customer(company)` only, and its return dict has
  `customer_matched`/`linked` but no `partner_matched`.
- T02 added `partner_hub_linking.ensure_partner_hub_note`/
  `link_note_to_partner_hub` this task calls, on a confirmed Partner match
  only (never unconditionally — the same "granular primitives only, after
  a confirmed match" carve-out already established for Customer).

**After / Outputs:**
- `people_extraction.py` gains `find_matching_partner`; `ensure_person_note`
  checks Customer first, Partner second, and its return dict gains
  `partner_matched` (additive — existing callers reading only
  `customer_matched`/`linked` are unaffected).

---

## Files to Modify

- `src/backend/app/business/people_extraction.py`:

  1. Add to the import block (alongside the existing
     `from app.business import customer_hub_linking`):
     ```python
     from app.business import customer_hub_linking, partner_hub_linking
     ```

  2. Add `find_matching_partner` immediately after the existing
     `find_matching_customer` function:
     ```python
     def find_matching_partner(company: str | None) -> str | None:
         """Mirrors find_matching_customer exactly, against
         vault_writer.list_known_partners() instead of
         vault_writer.list_known_customers() (ADR-009). Returns the
         matching known partner's original (non-slugified) name, or None
         when company is blank or matches no known partner."""
         if not company:
             return None
         target_slug = vault_writer.tag_slug(company)
         for partner in vault_writer.list_known_partners():
             if vault_writer.tag_slug(partner) == target_slug:
                 return partner
         return None
     ```

  3. Replace `ensure_person_note`'s body (keep the function signature,
     replace everything from `company = derive_company_from_email(email)`
     through the final `return {...}`) with:
     ```python
     def ensure_person_note(name: str, email: str) -> dict:
         """The shared "ensure this sender's Person note exists and is up
         to date" operation, called once as a one-time batch
         (retrofit_people_from_emails) and once as a per-write hook
         (ensure_person_note_for_captured_email). Creates a baseline note
         if missing, or tops up any missing baseline frontmatter keys if
         it already exists (Scenarios 2 and 6), without touching a key
         already present or the body. Derives the sender's company from
         their email domain and checks it against known Customers first
         (unchanged) — only when no Customer match is found does it check
         known Partners (ADR-009: customer/<slug> and partner/<slug> are
         mutually exclusive, so at most one of customer_matched/
         partner_matched is ever non-None). On a confirmed match (either
         kind), ensures that company's hub note exists and links this
         Person note to it, calling the matching module's two granular
         primitives directly (never a combined unconditional-creation
         entry point), since an arbitrary derived company is very often
         not a real customer or partner. A company matching neither gets
         its company/<slug> tag and nothing else; no company at all gets
         neither. Re-checking both matches on every call (not just at
         creation) is what makes Scenario 8 work — a company that later
         becomes a known customer or partner gets its wikilink added
         retroactively on the next call, without touching anything else.
         Returns {"note_path": str, "created": bool, "company": str |
         None, "customer_matched": str | None, "partner_matched": str |
         None, "linked": bool}."""
         company = derive_company_from_email(email)
         tags = vault_writer.build_person_tags(company)
         note_path = vault_writer.person_note_path(email)

         if vault_writer.person_note_exists(email):
             vault_writer.ensure_person_note_baseline_frontmatter(note_path, name, email, tags)
             created = False
         else:
             vault_writer.create_person_note_baseline(name, email, tags)
             created = True

         matched_customer = find_matching_customer(company)
         matched_partner = None
         linked = False
         if matched_customer:
             customer_hub_linking.ensure_customer_hub_note(matched_customer)
             linked = customer_hub_linking.link_note_to_customer_hub(note_path, matched_customer)
         else:
             matched_partner = find_matching_partner(company)
             if matched_partner:
                 partner_hub_linking.ensure_partner_hub_note(matched_partner)
                 linked = partner_hub_linking.link_note_to_partner_hub(note_path, matched_partner)

         return {
             "note_path": str(note_path),
             "created": created,
             "company": company,
             "customer_matched": matched_customer,
             "partner_matched": matched_partner,
             "linked": linked,
         }
     ```

---

## Constraints

- Inherits from parent story (ADR-003 layering; ADR-009 mutual exclusivity
  — Partner checked only when Customer finds no match).
- Must NOT modify `derive_company_from_email`,
  `ensure_person_note_for_captured_email`, `retrofit_people_from_emails`,
  `link_email_to_person`, or `retrofit_email_sender_links` — this task only
  touches the import block, adds `find_matching_partner`, and replaces
  `ensure_person_note`'s body (its signature and its callers' contract
  otherwise unchanged — the new `partner_matched` key is additive).
- Must NOT call `partner_hub_linking.ensure_partner_hub_note`/
  `link_note_to_partner_hub` unconditionally — only after a confirmed
  Partner match, mirroring the existing Customer carve-out exactly.
- Must NOT add any call site in `email_classification.py` or
  `meeting_classification.py` — per the story's own Non-Goals, Partner
  linking is reached only through `ensure_person_note`, never a new
  per-write hook.

---

## Tests

**Manual verification steps (Python shell against the backend `.venv`, real
configured vault — use throwaway partner/customer names and a throwaway
`Work/Emails/` note so this task's verification never touches real
Microsoft/ADNOC data; delete every throwaway file created below
afterward):**

1. [REQ-SB-16-US-01-AC-01] Create a throwaway Partner via
   `partner_hub_linking.ensure_partner_hub_note("Verifyt03partner")`
   — do **not** create a hub note for it directly; instead confirm
   `vault_writer.list_known_partners()` includes it. Call
   `ensure_person_note("Test Person", "person@verifyt03partner.com")`
   (this domain's derived company, per `derive_company_from_email`, is
   `"Verifyt03partner"`, matching the partner above by tag-slug). Confirm
   the returned dict has `customer_matched: None`,
   `partner_matched: "Verifyt03partner"`, `linked: True`; confirm the new
   Person note's body starts with `**Partner:** [[Verifyt03partner]]`.
2. [REQ-SB-16-US-01-AC-02] Call `ensure_person_note("Test Person",
   "person@verifyt03partner.com")` again with identical arguments. Confirm
   `linked: False` (the wikilink was already present — no duplicate line)
   and that no second Partner hub note was created for
   `"Verifyt03partner"` (`Work/Partners/` still has exactly one file for
   it).
3. [REQ-SB-16-US-01-AC-03] Create a throwaway Customer hub note via
   `customer_hub_linking.ensure_customer_hub_note("Verifyt03both")` **and**
   a throwaway Partner hub note via
   `partner_hub_linking.ensure_partner_hub_note("Verifyt03both")` (same
   name, both namespaces — a contrived edge case to prove the
   Customer-checked-first ordering even when both could technically
   match). Call `ensure_person_note("Test Person",
   "person@verifyt03both.com")`. Confirm `customer_matched:
   "Verifyt03both"`, `partner_matched: None` — the Partner branch is never
   attempted once Customer already matched — and the Person note's body
   carries `**Customer:** [[Verifyt03both]]`, not a `**Partner:**` line.
4. [REQ-SB-16-US-01-AC-04] Call `ensure_person_note("Test Person",
   "person@verifyt03none.com")` — a domain matching no known Customer or
   Partner. Confirm `customer_matched: None`, `partner_matched: None`,
   `linked: False`; confirm the Person note's `tags` are exactly
   `["company/verifyt03none", "kind/person"]`; confirm no new hub note was
   created in either `Work/Customers/` or `Work/Partners/` for
   `"Verifyt03none"`.
5. [REQ-SB-16-US-01-AC-08] On the `"Verifyt03partner"` hub note from step
   1, manually append a distinctive line beyond its auto-populated
   baseline (e.g. `## My Notes\nManually added overview text.`) via the
   Edit tool. Call `ensure_person_note("Test Person",
   "person@verifyt03partner.com")` again. Confirm the manually-added line
   is still present, unchanged, and the hub note's baseline frontmatter
   (`type`/`partner`/`tags`) is unchanged — no wholesale rewrite.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `find_matching_partner` mirrors `find_matching_customer` exactly
      (tag-slug comparison, returns the known partner's original name or
      `None`)
- [x] `ensure_person_note` checks Customer first; Partner is only ever
      checked/matched when no Customer match was found
- [x] `ensure_person_note`'s return dict gains `partner_matched`,
      additive — existing keys unchanged in meaning
- [x] A company matching neither gets its `company/<slug>` tag alone, no
      hub note created, no link added
- [x] Rerunning is idempotent — no duplicate hub note, no duplicate
      wikilink
- [x] Manually-added Partner hub-note content survives `ensure_person_note`
      being called again for that same partner
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Partner hub-note primitives themselves — that is T01/T02.
- The Customer→Partner migration and its endpoint — that is T02/T04.
- Any per-write capture-pipeline hook for Partner — explicitly out of
  scope for the whole story.

---

## Context / Notes

This is the only call site REQ-SB-16 adds Partner-matching to — the exact
"Person-note orchestration" Scenarios 1–4 and 8 describe. Since
`ensure_person_note` is already reached by both
`ensure_person_note_for_captured_email` (the existing per-write hook,
unchanged) and `retrofit_people_from_emails`/`retrofit_email_sender_links`
(the existing retrofit endpoints, unchanged), Partner-matching becomes live
across the whole existing capture surface automatically, with no new call
site needed — exactly the story's own scoping intent.

---

## Implementation Log

**2026-08-11, coder.** Edited `src/backend/app/business/people_extraction.py`
exactly per this task's `## Files to Modify` spec: import block extended,
`find_matching_partner` added immediately after `find_matching_customer`,
`ensure_person_note`'s body replaced verbatim (signature unchanged). All
throwaway verification used deliberately made-up partner/customer names and
domains (`Verifyt03partner`, `Verifyt03both`, `Verifyt03none`) plus throwaway
`Work/People/` notes — real Microsoft/ADNOC data was never touched by this
task, as instructed.

**[REQ-SB-16-US-01-AC-01] verified live, PASS.** Created throwaway partner
`Verifyt03partner` via `partner_hub_linking.ensure_partner_hub_note` (so
`list_known_partners()` picks it up); called `ensure_person_note("Test
Person", "person@verifyt03partner.com")`. Result: `customer_matched: None`,
`partner_matched: "Verifyt03partner"`, `linked: True`; Person note body
starts with `**Partner:** [[Verifyt03partner]]`.

**[REQ-SB-16-US-01-AC-02] verified live, PASS.** Called `ensure_person_note`
again with identical arguments — `linked: False` (line already present);
`Work/Partners/` had exactly one file for `Verifyt03partner` (no duplicate
hub note).

**[REQ-SB-16-US-01-AC-03] verified live, PASS.** Created both a throwaway
Customer hub note and a throwaway Partner hub note under the same name
(`Verifyt03both`) — the contrived both-could-match edge case. Called
`ensure_person_note("Test Person", "person@verifyt03both.com")`. Result:
`customer_matched: "Verifyt03both"`, `partner_matched: None` — Partner branch
never attempted once Customer matched. Person note body carries
`**Customer:** [[Verifyt03both]]`, no `**Partner:**` line.

**[REQ-SB-16-US-01-AC-04] verified live, PASS.** Called `ensure_person_note`
for `person@verifyt03none.com` (matches neither). Result: `customer_matched:
None`, `partner_matched: None`, `linked: False`; tags exactly
`["company/verifyt03none", "kind/person"]`; no new hub note created in
either `Work/Customers/` or `Work/Partners/`.

**[REQ-SB-16-US-01-AC-08] verified live, PASS (Person-note-processed half —
the migration-rerun half is T04's, blocked; see that task's own log).**
Manually appended a `## My Notes` line beyond `Verifyt03partner`'s
auto-populated baseline, then called `ensure_person_note` again for the same
partner — the manually-added line and the baseline frontmatter were both
byte-for-byte unchanged afterward.

All throwaway files (`Work/Partners/Verifyt03partner.md`,
`Work/Customers/Verifyt03both.md`, `Work/Partners/Verifyt03both.md`,
`Work/People/person@verifyt03{partner,both,none}.com.md`) deleted after
verification — no residue left in the real vault; real Microsoft/ADNOC data
was never read or written by this task.

**Status:** `Done`. `gate: clear` — no new trigger fired by this task in
isolation. (This task's own scope and verification are entirely independent
of the `REQ-SB-16-US-01-T04` blocker — see `ESCALATIONS.md` → `ESC-001` —
which concerns the migration's coverage of already-existing real Person
notes, not this task's forward-going `ensure_person_note` mechanism, which
is fully correct and fully verified.)
