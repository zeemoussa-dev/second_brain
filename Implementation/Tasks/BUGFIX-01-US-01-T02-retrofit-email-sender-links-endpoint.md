---
id: BUGFIX-01-US-01-T02
title: New retrofit_email_sender_links batch + POST /poc/retrofit-email-sender-links endpoint
parent_story: BUGFIX-01-US-01
requirement_id: BUG-001
type: backend
status: Done
gate: clear
gate_reason: ""
depends_on: [BUGFIX-01-US-01-T01]
created: 2026-08-11
updated: 2026-08-11
---

# BUGFIX-01-US-01-T02 — New retrofit_email_sender_links batch + POST /poc/retrofit-email-sender-links endpoint

## Parent Story

- Story: [[BUGFIX-01-US-01]] — `../UserStories/BUGFIX-01-US-01-email-notes-wikilink-to-sender-person-note.md`
- Requirement: `BUGS.md` → `BUG-001` (bugfix story; no PRD requirement anchor)

---

## Objective

Close the backfill half of `BUG-001`: give every already-captured Email note
its missing `[[PersonName]]` wikilink to its sender's Person note, via a
new one-time batch operation exposed as a one-off HTTP endpoint, matching
the three existing `/poc/retrofit-*` / `/poc/backfill-tags`
one-off-migration-endpoint precedents.

---

## Starting State → End State

**Before / Inputs:**
- T01 added `people_extraction.link_email_to_person(email_note_path,
  person_note_path) -> bool`.
- `people_extraction.ensure_person_note` (REQ-SB-10, Done) is already
  idempotent and safe to call again even if `retrofit_people_from_emails`
  already ran.
- `email_poc_router.py` has `/poc/classify-emails`, `/poc/backfill-tags`,
  `/poc/flatten-customer-folders`, `/poc/retrofit-customer-hub-links`,
  `/poc/retrofit-people-from-emails`, each a thin wrapper calling one
  business function and tallying its results list.

**After / Outputs:**
- `app/business/people_extraction.py` gains `retrofit_email_sender_links()`
  — a one-time batch over every already-captured Email note.
- A new `POST /poc/retrofit-email-sender-links` route, same thin shape as
  the five existing routes.

---

## Files to Modify

- `src/backend/app/business/people_extraction.py`:
  1. Append at the end of the file (after `link_email_to_person`, added by
     T01):

     ```python
     def retrofit_email_sender_links() -> list[dict]:
         """One-time batch: for every already-captured Email note carrying
         a real sender_email, ensures that sender's Person note exists and
         is up to date (safe and idempotent to call even if
         retrofit_people_from_emails already ran), then ensures the Email
         note's own body carries the [[PersonName]] wikilink back to it —
         the inbound Email→Person direction retrofit_people_from_emails
         never wrote (BUGFIX-01, closes BUG-001). Mirrors
         retrofit_customer_hub_links's and retrofit_people_from_emails's
         exact shape. Deliberately does not dedup by sender the way
         retrofit_people_from_emails does — every Email note from a given
         sender needs its own body link, not just the first one processed.
         A note with a blank/missing sender_email is skipped (status
         skipped_no_sender_email), never errored — Person and Customer hub
         notes are skipped by construction (neither carries a sender_email
         field)."""
         results: list[dict] = []
         for path in vault_writer.list_all_note_paths():
             frontmatter, _ = vault_writer.read_note(path)
             sender_email = frontmatter.get("sender_email")
             if not sender_email:
                 results.append({"note": str(path), "status": "skipped_no_sender_email"})
                 continue
             sender_name = frontmatter.get("sender") or sender_email
             person_result = ensure_person_note(sender_name, sender_email)
             linked = link_email_to_person(path, person_result["note_path"])
             status = "linked" if linked else "already_linked"
             results.append({"note": str(path), "status": status, **person_result})
         return results
     ```

- `src/backend/app/api/email_poc_router.py`:
  1. Replace this exact import line:

     ```python
     from app.business.people_extraction import retrofit_people_from_emails
     ```

     with:

     ```python
     from app.business.people_extraction import retrofit_email_sender_links, retrofit_people_from_emails
     ```

  2. Append the new route at the end of the file:

     ```python
     @router.post("/retrofit-email-sender-links")
     def retrofit_email_sender_links_endpoint() -> dict:
         results = retrofit_email_sender_links()
         linked = sum(1 for r in results if r["status"] == "linked")
         return {
             "notes_checked": len(results),
             "linked": linked,
             "results": results,
         }
     ```

---

## Constraints

- Inherits from parent story (ADR-003: `api/` calls into `business/` only,
  never `data_access/` directly; `business/` calling `data_access/` and
  another `business/` module's already-public functions only; idempotency
  is load-bearing, real live vault, no fixture vault).
- Must NOT modify the five existing routes, their imports, or
  `ensure_person_note`, `ensure_person_note_for_captured_email`,
  `retrofit_people_from_emails`, `link_email_to_person`'s own definition
  (added by T01, used as-is here), or anything in
  `email_classification.py`.
- No `data_access` change needed — `list_all_note_paths`, `read_note`, and
  (via `link_email_to_person`) `insert_body_line_if_missing` are all reused
  exactly as they already exist.
- Idempotent by construction — safe to call repeatedly against the real
  live vault; a rerun must never create a duplicate wikilink or otherwise
  disturb an Email note's existing body content.

---

## Tests

<!-- All three of this task's tagged ACs are exercised by the same
endpoint. Reuse real, already-captured senders from the live vault where a
natural example exists (e.g. the Person notes REQ-SB-10-US-01-T04 already
created for real senders); fall back to a throwaway Email note under
Work/Emails/ (via vault_writer.write_note directly, minimal frontmatter —
sender, sender_email, and whatever else read_note/write_note require) only
where the live vault has no natural example for a given case (most likely
AC-03's blank-sender_email case). Delete every throwaway note created,
restoring the vault to its pre-task state. -->

**Manual verification steps (run in this order, live against the real
configured vault — `VAULT_PATH` in `src/backend/.env`):**

1. Start the dev server: `.venv\Scripts\python.exe -m uvicorn app.main:app
   --reload` from `src/backend` (check port 8000 is free first per
   `MEMORY.md`'s standing constraint — an unrelated `agentic-map` process
   may already hold it; use `--port 8001` if so). This also fires one real
   email capture run on startup per ADR-005 — an unrelated, already-known
   side effect.
2. Identify an already-captured Email note under `Work/<Kind>/` whose
   sender already has (or will get) a Person note, and whose body does not
   yet contain a `**Sender:** [[...]]` line. Confirm that pre-state
   directly (open the note).
3. `Invoke-RestMethod -Method Post
   http://127.0.0.1:8000/poc/retrofit-email-sender-links` (adjust port if
   changed in step 1).
   - **[BUGFIX-01-US-01-AC-01]** (retrofit half) Confirm the results list
     contains an entry for the note from step 2 with `"status": "linked"`;
     re-open the note and confirm its body now contains
     `**Sender:** [[PersonStem]]` where `PersonStem` matches that sender's
     Person note's own filename stem under `Work/People/` exactly.
4. Call the same endpoint a second time.
   - **[BUGFIX-01-US-01-AC-02]** Confirm that same note's result entry now
     reads `"status": "already_linked"`; re-open the note and confirm its
     body still contains exactly one `**Sender:** [[PersonStem]]` line — no
     second, duplicate line was added.
5. Confirm the vault has (or create via a throwaway note under
   `Work/Emails/`) at least one Email note with a blank/missing
   `sender_email` field. Record its body content before the call. Call the
   endpoint once more (or reuse step 3/4's run if the throwaway note was
   already present for it).
   - **[BUGFIX-01-US-01-AC-03]** Confirm that note's result entry reads
     `"status": "skipped_no_sender_email"`, its body is byte-for-byte
     unchanged from the recorded pre-call content, and the run completed
     with a valid 200 response — no exception raised.
6. Clean up: delete any throwaway note created in step 5, and remove any
   now-empty directory it left behind, restoring the real vault to its
   pre-task state. Stop the dev server.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `POST /poc/retrofit-email-sender-links` adds a
      `**Sender:** [[PersonStem]]` wikilink to every already-captured Email
      note with a resolvable sender, matching that sender's Person note's
      own filename stem
- [x] A second run never adds a duplicate wikilink to a note already linked
- [x] An Email note with a blank/missing `sender_email` is skipped, its
      body left unchanged, and the run never errors on it
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `link_email_to_person` primitive itself and the going-forward capture
  hook wiring — that is T01 (a hard dependency: this task calls
  `link_email_to_person` as-is).
- Any change to `retrofit_people_from_emails`'s own dedup-by-sender
  behaviour — `retrofit_email_sender_links` is a separate function with
  its own (non-deduping) iteration, per its own docstring rationale.

---

## Context / Notes

Matches `/poc/retrofit-people-from-emails`'s and `/poc/retrofit-customer-hub-links`'s
exact shape: router imports one business function, calls it, tallies a
simple count from the results list, returns a dict. No new dependency, no
request body/query params needed. The real live vault's actual sender/
Email-note population is not known in advance — adapt using whatever real
notes already fit each scenario, falling back to a throwaway note only
where the live vault genuinely has no natural example (most likely AC-03),
the same substitution precedent `REQ-SB-14-US-01-T04` and
`REQ-SB-10-US-01-T04` both used. Log any such substitution in the
Implementation Log as a scope-internal judgement call, not a deviation from
AC intent.

---

## Implementation Log

**2026-08-11 — Coder.** Implemented exactly as specified in `## Files to
Modify`, no deviations:
- `app/business/people_extraction.py`: appended `retrofit_email_sender_links()`
  at the end of the file (after `link_email_to_person`, added by T01),
  verbatim per spec.
- `app/api/email_poc_router.py`: replaced the `retrofit_people_from_emails`
  import line to also import `retrofit_email_sender_links`; appended the
  `POST /retrofit-email-sender-links` route at the end of the file,
  verbatim per spec.

**Live verification session, 2026-08-11** (`VAULT_PATH` =
`<OPERATOR_VAULT_OLD>`, real configured vault, no fixture):

1. Confirmed port 8000 was occupied (`Get-NetTCPConnection -LocalPort 8000`
   showed an existing listener — the known `agentic-map` conflict per
   `MEMORY.md`) and started the dev server on `--port 8001` instead.
   Startup fired the known real capture-run side effect (ADR-005) —
   captured one genuinely new email (see T01's Implementation Log for
   that note's own AC-01 verification) and two new Person notes.
2. Pre-state check: identified a naturally-occurring, already-captured
   Email note with a real `sender_email` and no `**Sender:**` line yet —
   `Work/Emails/2026-07-20-Involuntary Loss of Employment Insurance
   (ILOE)-5C830000.md` (`sender_email: OnboardingTeam@core42.ai`), whose
   Person note (`Work/People/onboardingteam@core42.ai.md`) already existed
   from an earlier retrofit run in a prior sprint. Confirmed via `grep -c
   "Sender:"` = 0 before the call.
3. First call: `Invoke-RestMethod -Method Post
   http://127.0.0.1:8001/poc/retrofit-email-sender-links`. Result:
   `notes_checked: 334`, `linked: 249`, plus `skipped_no_sender_email: 84`
   and `already_linked: 1` (the one email the app-start capture had
   already linked via T01's forward hook — see T01's log). No errors.
   - **[BUGFIX-01-US-01-AC-01] (retrofit half) — PASS.** The step-2
     note's result entry read `"status": "linked"`. Re-opened the note:
     body now contains `**Sender:** [[onboardingteam@core42.ai]]`,
     matching the Person note's own filename stem exactly.
4. Second call, same endpoint, no changes in between. Result:
   `notes_checked: 334`, `linked: 0`, `already_linked: 250`.
   - **[BUGFIX-01-US-01-AC-02] — PASS.** The same note's result entry now
     read `"status": "already_linked"`. Re-opened the note: `grep -c
     "Sender:"` still = 1 — exactly one `**Sender:** [[...]]` line, no
     duplicate added on rerun.
5. Blank-`sender_email` case: rather than creating a throwaway note, found
   a genuinely natural example already in the live vault —
   `Work/Guides/Manual-Entry-Guide.md` (a hand-authored Guide note, no
   `sender_email` field at all). Read its full body before the first
   call as the recorded pre-state.
   - **[BUGFIX-01-US-01-AC-03] — PASS.** Its result entry in both runs
     read `"status": "skipped_no_sender_email"`; both endpoint calls
     returned valid 200 responses with no exception; re-reading the note
     after both runs showed it byte-for-byte unchanged from the recorded
     pre-state. Logged as a scope-internal judgement call, not a
     deviation: the story's own Context/Notes section explicitly permits
     substituting a natural real-vault example over a throwaway note
     where one already exists — `Manual-Entry-Guide.md` did, so no
     throwaway note was created and no cleanup was needed.
6. Stopped the dev server (confirmed port 8001 no longer bound
   afterward). No throwaway notes were created, so no vault cleanup was
   required beyond the intentional, idempotent link insertions the
   retrofit itself made (249 real Email notes gained their missing
   `**Sender:**` link — this is the actual bug-fix backfill, not
   incidental test pollution).

**Summary:** 334 notes checked (all of `Work/*/*.md` at call time,
including the one note the app-start capture added); 249 Email notes
newly linked by the retrofit; 84 notes skipped for having no
`sender_email` (Person notes, Customer hub notes, and the one Guide
note); 1 note already linked via the forward hook before the retrofit
even ran. Zero errors across both runs.

gate: clear 2026-08-11 — no triggers fired: no material assumption beyond
the one already-permitted natural-example substitution noted above (not
a MUST-FLAG trigger — the story's own Context/Notes explicitly allows
it); no new dependency, shared-interface change, or ADR deviation; all
three locked ACs verified live and passing.
