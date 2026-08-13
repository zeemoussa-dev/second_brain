---
id: REQ-SB-10-US-01-T02
title: New app/business/people_extraction.py orchestration module
parent_story: REQ-SB-10-US-01
requirement_id: REQ-SB-10
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-10-US-01-T01]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-10-US-01-T02 — New app/business/people_extraction.py orchestration module

## Parent Story

- Story: [[REQ-SB-10-US-01]] — `../UserStories/REQ-SB-10-US-01-people-notes-from-email-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-10 *People Living Documents*

---

## Objective

Add the single shared "ensure this email sender's Person note exists and is
up to date, linking it to their company's Customer hub note when that
company is a known customer" business-layer operation, the company-
derivation and company-to-known-customer-matching logic it depends on, and
the one-time batch retrofit loop over every already-captured Email note —
the one mechanism T03 (the per-write hook) and T04 (the retrofit endpoint)
both call, per `architecture.md`'s "Person Notes & Email-Sender Extraction"
section.

---

## Starting State → End State

**Before / Inputs:**
- T01 added the file-I/O primitives this module orchestrates:
  `person_note_path`, `person_note_exists`, `build_person_tags`,
  `create_person_note_baseline`, `ensure_person_note_baseline_frontmatter`,
  plus the newly-public `tag_slug`.
- `app/business/customer_hub_linking.py` (REQ-SB-14, Done) already exposes
  the two granular primitives this module composes:
  `ensure_customer_hub_note(customer)` and
  `link_note_to_customer_hub(note_path, customer)`.
- `app/business/tag_backfill.py`, `vault_restructure.py`, and
  `customer_hub_linking.py` are the existing "one business module per
  maintenance operation" precedent this module follows.

**After / Outputs:**
- A new file, `app/business/people_extraction.py`, exposing
  `derive_company_from_email`, `find_matching_customer`, `ensure_person_note`,
  `ensure_person_note_for_captured_email`, and `retrofit_people_from_emails`.

---

## Files to Modify

- `src/backend/app/business/people_extraction.py` (new file):

  ```python
  """Shared "ensure this email sender's Person note exists and is up to
  date, linking it to their company's Customer hub note when that company
  is a known customer" orchestration (REQ-SB-10) — the one mechanism used
  by both the one-time retrofit (retrofit_people_from_emails, over every
  already-captured Email note) and email_classification.py's per-write
  capture hook (ensure_person_note_for_captured_email, going forward).
  Follows ADR-003's layering and the tag_backfill.py / vault_restructure.py
  / customer_hub_linking.py precedent of one business module per
  maintenance operation — and is the first business module that composes
  another business module (customer_hub_linking.py's granular hub-note
  primitives) rather than only data_access; see architecture.md's explicit
  note that this is an intentional, permitted horizontal call within the
  business layer, not an ADR-003 boundary violation.
  """
  from __future__ import annotations

  from app.business import customer_hub_linking
  from app.data_access import vault_writer

  # Well-known personal/free email-provider domains — deliberately a fixed,
  # hardcoded set (unlike list_known_customers/list_known_kinds, which are
  # vault-derived): the universe of major personal email providers is a
  # small, externally-stable set with no relationship to this vault's own
  # content, so there is no vault signal that could ever grow or shrink it
  # the way real customer/kind values do (architecture.md). Extend this
  # constant directly if a real captured sender surfaces one that's missing.
  _PERSONAL_EMAIL_DOMAINS = frozenset({
      "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
      "msn.com", "yahoo.com", "ymail.com", "icloud.com", "me.com", "aol.com",
      "protonmail.com", "proton.me", "gmx.com", "mail.com", "yandex.com",
      "zoho.com",
  })


  def derive_company_from_email(sender_email: str) -> str | None:
      """Derives a display-name company from a sender's email domain — the
      only company signal available on a captured Email note (there is no
      separate "company" field anywhere in the existing schema). Takes the
      substring after "@", lowercases it, and checks it against
      _PERSONAL_EMAIL_DOMAINS; a match yields no company at all (Scenario 5
      — tag and link both absent). Otherwise the company display name is
      derived from the domain's first label — "core42.ai" -> "Core42"
      (label[0].upper() + label[1:]) — matching the resolved schema's own
      worked example verbatim. Returns None when sender_email is blank or
      has no "@" (Scenario 9's blank-sender_email case is actually filtered
      one layer up, before this function is ever called, but this guard
      keeps the function safe to call standalone)."""
      if not sender_email or "@" not in sender_email:
          return None
      domain = sender_email.rsplit("@", 1)[1].lower()
      if domain in _PERSONAL_EMAIL_DOMAINS:
          return None
      label = domain.split(".", 1)[0]
      if not label:
          return None
      return label[0].upper() + label[1:]


  def find_matching_customer(company: str | None) -> str | None:
      """Compares company against every name vault_writer.list_known_customers()
      returns, by tag-slug equality (e.g. "core42" vs "Core42" vs "CORE42"
      all match) rather than exact string equality — reuses the exact
      slugging rule tags already use (vault_writer.tag_slug) instead of
      inventing a second normalization scheme. Returns the matching known
      customer's original (non-slugified) name — the exact string
      customer_hub_linking's hub-note primitives expect — or None when
      company is blank or matches no known customer."""
      if not company:
          return None
      target_slug = vault_writer.tag_slug(company)
      for customer in vault_writer.list_known_customers():
          if vault_writer.tag_slug(customer) == target_slug:
              return customer
      return None


  def ensure_person_note(name: str, email: str) -> dict:
      """The shared "ensure this sender's Person note exists and is up to
      date" operation, called once as a one-time batch
      (retrofit_people_from_emails) and once as a per-write hook
      (ensure_person_note_for_captured_email). Creates a baseline note if
      missing, or tops up any missing baseline frontmatter keys if it
      already exists (Scenarios 2 and 6), without touching a key already
      present or the body. Derives the sender's company from their email
      domain and, only when that company matches an existing Customer hub
      note (find_matching_customer confirms a real match first), ensures
      the hub note exists and links this Person note to it — calling
      customer_hub_linking's two granular primitives directly
      (ensure_customer_hub_note, link_note_to_customer_hub), never the
      combined ensure_hub_note_and_link, since an arbitrary derived company
      is very often not a real customer (the story's load-bearing
      carve-out, architecture.md). A company with no match gets its
      company/<slug> tag and nothing else (Scenario 4); no company at all
      gets neither (Scenario 5). Re-checking find_matching_customer on
      every call (not just at creation) is what makes Scenario 8 work — a
      company that later becomes a known customer gets its wikilink added
      retroactively on the next call, without touching anything else.
      Returns {"note_path": str, "created": bool, "company": str | None,
      "customer_matched": str | None, "linked": bool}."""
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
      linked = False
      if matched_customer:
          customer_hub_linking.ensure_customer_hub_note(matched_customer)
          linked = customer_hub_linking.link_note_to_customer_hub(note_path, matched_customer)

      return {
          "note_path": str(note_path),
          "created": created,
          "company": company,
          "customer_matched": matched_customer,
          "linked": linked,
      }


  def ensure_person_note_for_captured_email(sender_name: str, sender_email: str) -> dict | None:
      """Per-write hook: called immediately after a new Email note is
      written, ensuring its sender's Person note exists and is up to date
      — the same ensure_person_note operation the retrofit uses, applied
      to one sender at a time going forward (Scenario 7). Skips (returns
      None), without erroring, when sender_email is blank (Scenario 9)."""
      if not sender_email:
          return None
      return ensure_person_note(sender_name or sender_email, sender_email)


  def retrofit_people_from_emails() -> list[dict]:
      """One-time batch: for every already-captured Email note carrying a
      real sender_email, ensures that sender's Person note exists and is up
      to date, deduped by email address (case-insensitively) so multiple
      Email notes from the same sender within this run produce exactly one
      Person note, not one per email (Scenario 1). Idempotent — rerunning
      finds every Person note already created and every already-linked note
      left unchanged (Scenario 2). Person and Customer hub notes are
      silently skipped by construction (neither carries a sender_email
      field). An Email note with no sender_email is skipped, not errored
      (Scenario 9)."""
      results: list[dict] = []
      seen_emails: set[str] = set()
      for path in vault_writer.list_all_note_paths():
          frontmatter, _ = vault_writer.read_note(path)
          sender_email = frontmatter.get("sender_email")
          if not sender_email:
              results.append({"note": str(path), "status": "skipped_no_sender_email"})
              continue
          dedup_key = sender_email.lower()
          if dedup_key in seen_emails:
              results.append({"note": str(path), "status": "skipped_duplicate_sender_this_run"})
              continue
          seen_emails.add(dedup_key)
          sender_name = frontmatter.get("sender") or sender_email
          outcome = ensure_person_note(sender_name, sender_email)
          status = "created" if outcome["created"] else "already_existed"
          results.append({"note": str(path), "status": status, **outcome})
      return results
  ```

---

## Constraints

- Inherits from parent story (ADR-003 layering: no HTTP, no direct
  filesystem I/O — every read/write goes through `vault_writer` or
  `customer_hub_linking`; People never nested under a `Company` folder;
  idempotency is load-bearing, real live vault).
- Must not modify `email_classification.py`, `customer_hub_linking.py`,
  `tag_backfill.py`, `vault_restructure.py`, or `email_poc_router.py` — this
  task only adds the new module.
- Must call `customer_hub_linking.ensure_customer_hub_note` and
  `customer_hub_linking.link_note_to_customer_hub` directly — never
  `customer_hub_linking.ensure_hub_note_and_link` — and only after
  `find_matching_customer` confirms a real match. This is the load-bearing
  carve-out the parent story's Constraints require (an arbitrary derived
  company is very often not a real customer).
- `_PERSONAL_EMAIL_DOMAINS` is a fixed constant, not vault-derived — do not
  change it to read from the vault.
- `retrofit_people_from_emails` must never error on a note with no
  `sender_email` (Scenario 9) or duplicate a Person note for a sender seen
  more than once in the same run (Scenario 1).

---

## Tests

<!-- This task's own functions are exercised end-to-end, live, by T04 (the
retrofit endpoint — AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-08, AC-09)
and T03 (the per-write hook — AC-07), which is where this story's locked
ACs are tagged. The smoke check below is a non-AC-tagged confirmation that
this module's functions behave correctly in isolation before T03/T04 build
on them. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv`, call
   `derive_company_from_email("person@core42.ai")` and confirm it returns
   `"Core42"`; call `derive_company_from_email("someone@gmail.com")` and
   confirm it returns `None`; call `derive_company_from_email("")` and
   confirm it returns `None` without raising.
2. Non-AC smoke check: call `find_matching_customer("Adnoc")` (mixed casing
   deliberately, to exercise the slug-equality comparison) against the real
   vault and confirm it returns the exact known-customer name
   `list_known_customers()` itself reports for ADNOC (e.g. `"ADNOC"`) if
   ADNOC is a known customer in the live vault; call
   `find_matching_customer("Some-Company-Nobody-Has-Heard-Of")` and confirm
   it returns `None`.
3. Non-AC smoke check: call `ensure_person_note("Verify T02 Person",
   "verify.t02@example.com")` against the real vault. Confirm the returned
   dict has `created: True`, `company: "Example"`, `customer_matched: None`
   (unless a real customer named "Example" happens to exist — unlikely),
   `linked: False`; confirm `Work/People/verify-t02-example-com.md` now
   exists. Call it again with identical arguments and confirm `created:
   False` (baseline top-up only, no duplicate). Delete the throwaway test
   note afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `derive_company_from_email` returns the domain-derived display name,
      `None` for a personal/free-provider domain, and `None` for a blank or
      malformed address
- [x] `find_matching_customer` matches by tag-slug equality, not exact
      string equality, and returns the known customer's original name
- [x] `ensure_person_note` creates a baseline note when missing, tops up
      only missing baseline keys when it already exists, and only calls
      `customer_hub_linking`'s two granular primitives (never
      `ensure_hub_note_and_link`) after a confirmed customer match
- [x] `ensure_person_note_for_captured_email` skips (returns `None`) without
      erroring when `sender_email` is blank
- [x] `retrofit_people_from_emails` iterates every note, skips notes with no
      `sender_email`, and produces exactly one Person note per distinct
      sender email address in a single run
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Calling `ensure_person_note_for_captured_email` from
  `email_classification.py`'s capture flow — that is T03.
- Exposing `retrofit_people_from_emails` as an HTTP endpoint — that is T04.

---

## Context / Notes

Mirrors `customer_hub_linking.py`'s existing shape exactly: a single
business module with a top-level batch function
(`retrofit_people_from_emails`, analogous to `retrofit_customer_hub_links`)
built on smaller reusable functions, calling only into `vault_writer` and
`customer_hub_linking` (never doing filesystem I/O itself), returning a
per-note results list the caller (T04's endpoint) tallies for its HTTP
response. This is the first business module that calls into another
business module — `architecture.md` records this explicitly as an
intentional, permitted shape (ADR-003 restricts `business/`'s I/O, not
business-to-business composition), not a new precedent to second-guess.

---

## Implementation Log

**2026-08-11 (coder):** Created `src/backend/app/business/people_extraction.py`
verbatim from this task's `## Files to Modify` spec — no deviation. Confirmed
T01's primitives (`person_note_path`, `person_note_exists`, `build_person_tags`,
`create_person_note_baseline`, `ensure_person_note_baseline_frontmatter`,
public `tag_slug`) exist in `app/data_access/vault_writer.py` exactly as
expected before writing this file. Read `app/business/customer_hub_linking.py`
and confirmed `ensure_customer_hub_note`/`link_note_to_customer_hub` are the
two granular primitives this module composes (never
`ensure_hub_note_and_link`, per the Constraints carve-out).

This task's own functions have no locked story AC tagged to them (this
story's 9 locked ACs — `AC-01`..`AC-09` — are exercised live by T03/AC-07
and T04/the rest, per the story and task's own framing). Recording the
three non-AC smoke checks this task's `## Tests` section specifies:

- **Smoke check 1** (`derive_company_from_email`) — PASS. Ran against the
  backend `.venv`:
  `derive_company_from_email("person@core42.ai")` → `'Core42'`;
  `derive_company_from_email("someone@gmail.com")` → `None`;
  `derive_company_from_email("")` → `None`, no exception. All three match
  the expected outcomes.
- **Smoke check 2** (`find_matching_customer`) — PASS. Against the real
  live vault, `list_known_customers()` returned `['ADNOC', 'Azerbaijan
  Ministry of Digital Development and Transport', 'Core42', 'Department
  of Government Enablement', 'LinkedIn', 'Masdar', 'TAQA']` (ADNOC is a
  known customer). `find_matching_customer("Adnoc")` → `'ADNOC'` (exact
  known-customer name, confirming slug-equality matching despite the
  mixed casing); `find_matching_customer("Some-Company-Nobody-Has-Heard-Of")`
  → `None`.
- **Smoke check 3** (`ensure_person_note`) — PASS. Against the real live
  vault: `ensure_person_note("Verify T02 Person", "verify.t02@example.com")`
  returned `{"note_path": ".../Work/People/verify.t02@example.com.md",
  "created": True, "company": "Example", "customer_matched": None,
  "linked": False}` — matches expected exactly ("Example" is not a real
  known customer in the live vault, confirming the no-match path). The
  note was written with the expected baseline frontmatter (`type:
  "Person"`, `name`, `email`, blank `phone`/`linkedin`,
  `tags: ["company/example", "kind/person"]`) and empty body. Note:
  the filename is `verify.t02@example.com.md` (dots/`@` preserved, not
  hyphenated) — expected per MEMORY.md's existing `_slugify()` vs
  `tag_slug()` distinction recorded during T01, not a new finding.
  Calling `ensure_person_note` again with identical arguments returned
  `created: False` (baseline top-up only — `ensure_person_note_baseline_
  frontmatter` found every key already present, so no write occurred),
  confirming idempotency. Deleted the throwaway note afterward
  (`Remove-Item` on `Work/People/verify.t02@example.com.md`); confirmed
  it no longer exists. `Work/People/` itself was left as found (already
  existed, empty, from T01's own verification) — no other vault state
  touched.

`ensure_person_note_for_captured_email` and `retrofit_people_from_emails`
were not separately smoke-tested here (this task's `## Tests` section
specifies only the three checks above) — both are thin wrappers around
`ensure_person_note`, already exercised by smoke check 3, and are
verified end-to-end live by T03 (the capture hook, AC-07) and T04 (the
retrofit endpoint, AC-01..AC-06/AC-08/AC-09) respectively, per this
task's own scope note. Code review against the task's verbatim spec
confirms both match: `ensure_person_note_for_captured_email` returns
`None` without calling `ensure_person_note` when `sender_email` is
falsy; `retrofit_people_from_emails` dedupes by lowercased
`sender_email` within one run and skips notes with no `sender_email`,
without raising.

No out-of-scope event, new dependency, shared-interface change, or ADR
deviation encountered. No assumption beyond what the task's own verbatim
code spec settles.

gate: clear 2026-08-11 — no MUST-FLAG trigger fired: code is verbatim
from the task's `## Files to Modify` spec (no material assumption), no
ADR created/changed, no ESCALATIONS.md entry, all three specified
smoke checks passed against the real live vault, no contradictory
inputs, task not oversized.

No new decision/pattern/constraint emerged beyond what T01 already
recorded in `MEMORY.md` (the `_slugify()`/`tag_slug()` distinction) —
`MEMORY.md` not updated by this task.
