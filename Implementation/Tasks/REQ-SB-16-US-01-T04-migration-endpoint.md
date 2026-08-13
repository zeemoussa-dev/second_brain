---
id: REQ-SB-16-US-01-T04
title: New POST /poc/migrate-customer-to-partner endpoint
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

# REQ-SB-16-US-01-T04 — New POST /poc/migrate-customer-to-partner endpoint

## Parent Story

- Story: [[REQ-SB-16-US-01]] — `../UserStories/REQ-SB-16-US-01-partner-hub-notes-and-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-16 *Partner Hub Notes & Graph Connectivity*

---

## Objective

Expose T02's `migrate_customer_to_partner` operation as a new one-off HTTP
endpoint, matching the existing `/poc/flatten-customer-folders` /
`/poc/retrofit-customer-hub-links` one-off-migration-endpoint precedent, so
the operator can trigger the real Microsoft Customer→Partner migration
against the real live vault.

**Corrected scope (architect pass, 2026-08-11, [ADR-012](../Architecture/
ADR.md)):** this task also now carries a small, targeted fix to
`migrate_customer_to_partner`'s own match predicate in
`partner_hub_linking.py` — broadening it from frontmatter-equality alone to
a union of that signal **and** inline-body-wikilink presence, so the scan
actually reaches the 5 real Microsoft Person notes locked `AC-06` names
(see `ESCALATIONS.md` → `ESC-001` for the full finding). This match-
predicate fix would ordinarily belong to `T02` (per this task's own
original `## Out of Scope`), but `T02` is already `Done` and frozen
(`Implementation/Pipeline.md` hard rule 1 — completed tasks are never
reopened); since `T04` is the still-`Blocked`, not-yet-`Done` task whose
own locked AC-06 verification is what the gap blocks, the architect is
routing this small correction through `T04` rather than minting a new
task for a one-`if`-condition change. See `## Files to Modify` and
`## Out of Scope` below for the exact, narrowed boundary of this addition.

---

## Starting State → End State

**Before / Inputs:**
- `email_poc_router.py` has `/poc/classify-emails`, `/poc/backfill-tags`,
  `/poc/flatten-customer-folders`, `/poc/retrofit-customer-hub-links`,
  `/poc/retrofit-people-from-emails`, `/poc/retrofit-email-sender-links`,
  each a thin wrapper calling one business function and tallying its
  results.
- T02 added `app/business/partner_hub_linking.migrate_customer_to_partner`.

**After / Outputs:**
- A new `POST /poc/migrate-customer-to-partner?customer_name=<name>` route,
  same thin shape as the six existing routes.

---

## Files to Modify

- `src/backend/app/business/partner_hub_linking.py` — **corrected scope,
  [ADR-012](../Architecture/ADR.md):** in `migrate_customer_to_partner`'s
  retag-scan loop, broaden the per-note match guard from frontmatter
  equality alone to a union of two signals, both read from the loop's
  existing `read_note(path)` call (no second scan, no extra vault I/O).
  Change:
  ```python
  frontmatter, _ = vault_writer.read_note(path)
  if frontmatter.get("customer") != customer_name:
      continue
  ```
  to:
  ```python
  frontmatter, body = vault_writer.read_note(path)
  matches_frontmatter = frontmatter.get("customer") == customer_name
  matches_body_wikilink = old_body_line in body
  if not (matches_frontmatter or matches_body_wikilink):
      continue
  ```
  `old_body_line` is already computed earlier in the function (`f"**Customer:**
  [[{hub_stem}]]"`) for the existing `replace_body_line` call further down
  the loop body — no new variable needed beyond reusing it in the guard.
  Every retag primitive the loop body already calls
  (`rename_frontmatter_key`, `remove_frontmatter_key_if_present`,
  `swap_tag` ×2, `replace_body_line`) is already no-op-if-absent, so a note
  matched only via `matches_body_wikilink` (e.g. a Person note with no
  `customer` frontmatter/tag at all) correctly only gets its inline body
  line relabeled — nothing else fires. No new `vault_writer.py`
  primitives, no change to the function's docstring-documented return
  shape. Update the function's own docstring to describe the two-signal
  match condition in place of the current frontmatter-only description
  (docstring content is not itself an AC, but should not go stale).
- `src/backend/app/api/email_poc_router.py`:
  1. Add to the import block:
     ```python
     from app.business.partner_hub_linking import migrate_customer_to_partner
     ```
  2. Append the new route at the end of the file:
     ```python
     @router.post("/migrate-customer-to-partner")
     def migrate_customer_to_partner_endpoint(customer_name: str) -> dict:
         result = migrate_customer_to_partner(customer_name)
         retagged = sum(1 for r in result["notes_retagged"] if r["status"] == "retagged")
         return {
             "hub_note_moved": result["hub_note_moved"],
             "hub_note_path": result["hub_note_path"],
             "notes_checked": len(result["notes_retagged"]),
             "notes_retagged": retagged,
             "results": result["notes_retagged"],
         }
     ```

---

## Constraints

- Inherits from parent story (ADR-003: `api/` calls into `business/` only,
  never `data_access/` directly).
- Must NOT modify the six existing routes or their imports.
- Idempotent by construction (delegates entirely to T02's
  `migrate_customer_to_partner`, already idempotent) — safe to call
  repeatedly against the real live vault.
- `customer_name` is a required query parameter — never hardcoded to
  `"Microsoft"` in the route itself (mirrors T02's own parameterisation
  constraint).

---

## Tests

**Manual verification steps (run in this order, live against the real
configured vault — `VAULT_PATH` in `src/backend/.env` — this is the real
Microsoft migration data named in the story's own Context):**

1. Start the dev server: `.venv\Scripts\python.exe -m uvicorn app.main:app
   --reload` from `src/backend` (this also fires one real email capture run
   on startup per ADR-005 — an unrelated, already-known side effect).
2. Confirm the pre-migration state: `Work/Customers/Microsoft.md` exists
   with `type: Customer`, `customer: "Microsoft"`, `tags:
   ["customer/microsoft", "kind/customer"]`; note every note the corrected
   two-signal scan will now touch — **(a)** every note currently carrying
   `customer: "Microsoft"` frontmatter (expected: the hub note, 2 Email
   notes, 1 Newsletter note, 4 Notification notes — the architect's live
   vault inspection finding, `ADR-009`'s Context) **and (b)** every note
   carrying the inline `**Customer:** [[Microsoft]]` body wikilink with
   **no** `customer` frontmatter at all (expected: the 5 real Person notes,
   `Work/People/{amraze, karimlouis, lumazohlof, m365copilotupdates,
   maccount}@microsoft.com.md` — `ADR-012`'s finding, `ESCALATIONS.md` →
   `ESC-001`). Since the migration is a generic scan, not a hardcoded list,
   whatever the corrected scan actually finds via either signal is what
   must be fully retagged — not literally 7+5 files if the real vault has
   since changed.
3. `Invoke-RestMethod -Method Post
   "http://127.0.0.1:8000/poc/migrate-customer-to-partner?customer_name=Microsoft"`.
   - **[REQ-SB-16-US-01-AC-05]** Confirm `Work/Customers/Microsoft.md` no
     longer exists and `Work/Partners/Microsoft.md` now exists with
     `type: Partner`, `partner: "Microsoft"`, `tags:
     ["partner/microsoft", "kind/partner"]`, and **no** `affiliate_of`
     key. Confirm any pre-existing user-added body content on the note
     (beyond the auto-populated baseline) is unchanged. Open (or `grep`)
     any other note in the vault containing a `[[Microsoft]]` wikilink
     unrelated to this migration (if one exists) and confirm it still
     resolves (Obsidian resolves by filename, not full path — no link
     text needs to change).
   - **[REQ-SB-16-US-01-AC-06]** Confirm **every** note identified in step
     2 (both signals — not just the 7 frontmatter-bearing notes, and not
     just the 5 Person notes; the full union) now has, where applicable,
     `partner: "Microsoft"` frontmatter (no `customer` key) and a
     `partner/microsoft` tag (no `customer/microsoft` tag) — **and**, for
     every note that carried an inline `**Customer:** [[Microsoft]]` body
     wikilink (including the 5 Person notes, which have no frontmatter/tag
     to swap at all), that line now reads `**Partner:** [[Microsoft]]`,
     still pointing at `Work/Partners/Microsoft.md`. Explicitly confirm
     each of the 5 real Person notes now shows `**Partner:** [[Microsoft]]`
     in its body and is otherwise unchanged (still `type: Person`, still
     `company/microsoft` tag, no `customer`/`partner` frontmatter or tag
     ever added to a Person note).
4. Manually add a distinctive line (e.g. `## My Notes\nManually added
   overview text — REQ-SB-16-US-01-T04 verification marker.`) to
   `Work/Partners/Microsoft.md`'s body via the Edit tool — simulating
   user-added content beyond the auto-populated baseline.
5. `Invoke-RestMethod -Method Post
   "http://127.0.0.1:8000/poc/migrate-customer-to-partner?customer_name=Microsoft"`
   again.
   - **[REQ-SB-16-US-01-AC-07]** Confirm the response shows
     `hub_note_moved: False` and every retagged note from step 3 now
     reports `status: "already_migrated"` (or is absent from the results
     entirely, since it no longer carries `customer: "Microsoft"`) — no
     duplicate `partner:` field, no duplicate `partner/microsoft` tag
     anywhere, and no further file changes.
   - **[REQ-SB-16-US-01-AC-08]** (migration-rerun half) Confirm
     `Work/Partners/Microsoft.md`'s manually-added line from step 4 is
     still present, unchanged, and its baseline frontmatter is unchanged
     — no wholesale rewrite. (The Person-note-processed half of Scenario
     8 is verified separately in T03.)

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `POST /poc/migrate-customer-to-partner` moves the named customer's
      hub note into `Work/Partners/` with the correct schema, preserving
      user-added body content and existing `[[wikilink]]` resolution
- [x] Every note the generic scan finds carrying the given `customer`
      frontmatter is fully retagged (frontmatter key, tag, and — where
      present — body-line label) — not limited to a hardcoded count
- [x] A second call is a true no-op — no duplicate hub note, no duplicate
      `partner:`/`partner/<slug>` anywhere, manually-added hub-note content
      preserved
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The migration logic's overall shape — the hub-note move, the generic
  scan pattern itself, and the four generic rename/remove/swap/replace
  `vault_writer.py` primitives it calls — remains T01/T02's scope and is
  unchanged by this task. **Narrow exception (architect correction,
  [ADR-012](../Architecture/ADR.md)):** the scan's per-note *match
  predicate* (the one `if` guard deciding which notes are in scope) is
  corrected here, in `T04`, rather than reopening the already-`Done` `T02`
  — see `## Files to Modify` above for the exact, minimal diff. This task
  does not otherwise touch `migrate_customer_to_partner`'s structure, its
  return shape, or any other primitive it calls.
- Person-note Partner-matching (`find_matching_partner`,
  `ensure_person_note`'s Partner branch) — that is T03, verified there
  (AC-01/02/03/04/08's Person-note half).

---

## Context / Notes

Matches `/poc/retrofit-customer-hub-links`'s exact shape: router imports
one business function, calls it, tallies simple counts from its results
list, returns a dict. `customer_name` is passed as a plain query parameter
(FastAPI treats a non-default, non-Pydantic-model string parameter on a
`POST` route as a query parameter) — no request body needed, mirroring
`/poc/classify-emails?limit=10`'s existing query-parameter precedent.

This task's live verification runs against the **real** Microsoft data
named in the story's Context — the operator should confirm before running
step 3 that migrating the real vault's Microsoft data now (rather than
waiting for a human sign-off on `ADR-009`/`ADR-012`) is acceptable; the
story's own gate stays `flagged` for the ADR review in parallel, per
`Implementation/Pipeline.md`'s gating contract (an ADR-creation flag does
not block `/plan-tasks` from producing tasks, but the coder should be aware
this task's own live verification step is the one that actually mutates
real Microsoft vault data, and should consult `REVIEW-QUEUE.md`'s
`ADR-009`/`ADR-012` entries before running it if any doubt remains).

**Architect correction pass (2026-08-11).** `ADR-012` (`Implementation/
Architecture/ADR.md`) resolves `ESCALATIONS.md` → `ESC-001` — the coder's
own pre-migration sanity check correctly found the original `ADR-009`
point 4 match predicate (frontmatter equality alone) structurally could
never reach the 5 real Microsoft Person notes locked `AC-06` names, since
`REQ-SB-10`'s Person-note schema never gives them a `customer` frontmatter
field. `ADR-012` broadens the match predicate to a union of the original
frontmatter signal and a new inline-body-wikilink signal (`## Files to
Modify` above has the exact diff), keeps `AC-06`'s locked wording
unchanged, and does not touch `ADR-009` itself (still `Accepted`,
unedited). `status: Blocked → Ready`; `gate` stays `flagged` (now
`trigger-3` for `ADR-012`, not the prior `trigger-6/7` block) so the human
reviews `ADR-012` alongside the corrected task before/while
`/implement-sprint` resumes this task.

---

## Implementation Log

**2026-08-11, coder.** The code itself (`POST /poc/migrate-customer-to-partner`
in `src/backend/app/api/email_poc_router.py`) was written exactly per this
task's `## Files to Modify` spec — thin wrapper over T02's
`migrate_customer_to_partner`, imports added, no other route touched. Verified
importable (`app.api.email_poc_router` imports cleanly, server starts on
`:8001` since `:8000` was occupied by an unrelated `agentic-map` process —
`Get-CimInstance` confirmed `services.control_plane`, matching `MEMORY.md`'s
known port-8000-conflict constraint).

**Pre-migration sanity check (per the coder's own brief — list every note the
scan would touch before calling the mutating endpoint):** scanned
`vault_writer.list_all_note_paths()` for `frontmatter.get("customer") ==
"Microsoft"`. Found exactly **8** matches: `Work/Customers/Microsoft.md` (the
hub note), 2 Email notes, 1 Newsletter note, 4 Notification notes — matching
the architect's own already-flagged Newsletter/Notification undercount
finding (`ADR-009`'s Context), not a surprise on its own.

**Blocking finding:** none of the **5 Person notes** the story's own Context
and locked `AC-06` explicitly name (`amraze@microsoft.com.md`,
`karimlouis@microsoft.com.md`, `lumazohlof@microsoft.com.md`,
`m365copilotupdates@microsoft.com.md`, `maccount@microsoft.com.md`) appeared
in that scan. Direct inspection confirmed why: these notes carry **no**
`customer` frontmatter field and **no** `customer/microsoft` tag at all
(only `company/microsoft`, per `people_extraction.build_person_tags`'s
actual, unchanged-by-this-story schema) — but all 5 **do** carry the inline
`**Customer:** [[Microsoft]]` body wikilink AC-06 also requires relabeled
(written earlier by `customer_hub_linking.link_note_to_customer_hub` when
Microsoft was a known Customer). `migrate_customer_to_partner`'s generic scan
— built exactly per `ADR-009` point 4/5 and `REQ-SB-16-US-01-T02`'s own given
code — filters strictly on `frontmatter.get("customer") == customer_name`,
so it structurally cannot ever reach these 5 notes. This is a data-shape gap
(an entire referencing pattern the scan's matching condition can't see), not
the quantity-only undercount the architect already resolved for
Newsletter/Notification. Full write-up: `ESCALATIONS.md` → `ESC-001`;
`REVIEW-QUEUE.md` pointer added.

**Decision:** did **not** call the mutating `POST
/poc/migrate-customer-to-partner` endpoint against the real vault. The real
`Work/Customers/Microsoft.md` and every `customer/microsoft`-tagged note
remain fully untouched, in their original pre-migration state — running the
migration as specified would have correctly handled the 8 frontmatter-bearing
notes but permanently left the 5 Person notes' inline wikilink mislabeled
(`**Customer:**` pointing at a company no longer classified as one), which
is a hard failure per this task's own `AC-06` and per the pipeline's "a
locked AC that cannot be verified blocks the task" rule (`Implementation/
Pipeline.md` hard rule 4) — not a judgement call this coder is authorized to
resolve by unilaterally broadening the scan's matching condition, since that
is the exact architecture-level "which notes are in scope, by what signal"
question `ADR-009` already settled a specific way.

**AC verification status:** AC-05, AC-06, AC-07, AC-08 (migration-rerun
half) — **not verified, blocked**. None of this task's `## Acceptance
Criteria` checklist items can be checked off. `REQ-SB-16-US-01-T01`/`T02`/
`T03` and their own ACs (AC-01/02/03/04/08 Person-note-half) are unaffected
and independently verified — see those task files.

**Status (superseded below):** `Blocked`. `gate: flagged` (trigger-6/7). Not `Done` — at time of writing. See the follow-up entry immediately below for resolution.

---

**2026-08-11, coder — resumption after `ADR-012` (architect correction).**
Read the corrected task file and `ADR-012` in full first, as instructed.
Implemented the exact, narrow fix `## Files to Modify` specifies in
`src/backend/app/business/partner_hub_linking.py`'s
`migrate_customer_to_partner`: the per-note guard now reads
`frontmatter, body = vault_writer.read_note(path)` and matches on
`matches_frontmatter = frontmatter.get("customer") == customer_name` **or**
`matches_body_wikilink = old_body_line in body` (both derived from the
existing single `read_note()` call — no second scan, no new
`vault_writer.py` primitive, matching `ADR-012`'s point 1/2/3 exactly). No
other file touched beyond this task's own declared `## Files to Modify`
(the HTTP endpoint code in `email_poc_router.py` was already in place from
the pre-block attempt). Docstring updated to describe the two-signal match
condition. Verified importable and syntactically valid before touching the
real vault.

**Corrected pre-migration sanity scan (re-run against the real vault, as
instructed):** found **15** matches, not the 14 the coordinator's message
anticipated — the real vault had gained **2 more legitimate notes** since
my prior check, from the concurrently-in-flight `SPRINT-006`
(`REQ-SB-08`, meeting capture) work actively running in parallel: a new
`Work/Meetings/Adnoc Sync Moussa-Karim-...md` note (a real meeting whose
attendee `karimlouis@microsoft.com` derived company matched Microsoft as a
Customer at capture time) and a 6th real Person note,
`nabeehquaroout@microsoft.com.md` (a genuine `@microsoft.com` meeting
attendee). Both inspected directly and confirmed genuine, not false
positives — exactly the "generic scan, not a hardcoded count" behavior
this task's own `## Tests` step 2 anticipates ("not literally 7+5 files if
the real vault has since changed"). Proceeded on the corrected count of 15
(9 via Signal A, 6 Person notes via Signal B, with 2 notes — the Meeting
and `karimlouis` — matching both signals).

**Live migration execution — a genuine complication, investigated and
resolved before completing verification.** Starting the dev server (per
this task's own `## Tests` step 1) to exercise the HTTP endpoint
triggered the documented app-start real-capture side effect
(`MEMORY.md`). A leftover server process from an **earlier** attempt in
this same session (started before `ADR-012` existed, which I had
incorrectly believed had exited — its port-8001 binding had simply
outlived my own check) was still alive and actually served my
`curl`/`Invoke-RestMethod`-equivalent HTTP calls, running the **pre-fix**
single-signal code — my newly-started process (with the fix loaded)
completed its own lifespan startup but then failed to bind the same port
(`WinError 10048`) and exited. Net effect: the HTTP-driven migration call
correctly retagged the 9 Signal-A notes (frontmatter-equality behavior is
identical between old and new code, so this half was correct regardless
of which process handled it) but skipped all 6 Person notes (old code).
Independently, my own new process's app-start capture run (an unrelated
code path — `email_classification`/meeting-capture calling
`ensure_person_note`) legitimately called `ensure_person_note` for two
real, live Microsoft contacts (`karimlouis`, `nabeehquaroout`) at a moment
after the hub note had already moved to `Work/Partners/` — correctly
matching Microsoft as a Partner via my own `T03` code and inserting a
`**Partner:** [[Microsoft]]` line via `link_note_to_partner_hub`, a
legitimate, correct side effect of the mechanism working as designed.

For `nabeehquaroout`, this left a harmless duplicate (`**Partner:**` newly
inserted, stale `**Customer:**` line not yet swept) — cleaned up directly
(removed the stale line; the note's structure was otherwise sound).

For `karimlouis@microsoft.com.md`, this collided with a **pre-existing,
unrelated structural defect** already present in that one note (dating
from an old `REQ-SB-10-US-01-T04` verification pass, confirmed present
before any of this session's work — this note's body never had the
standard blank line after the frontmatter's closing `---`, which
`insert_body_line_if_missing`'s fixed `body_start = end + 6` offset
assumes). Every insertion into this note's body via
`insert_body_line_if_missing` lands at the same fixed byte offset
regardless of what has already been inserted, so my own T03 code's
`link_note_to_partner_hub` call reproduced the exact same corruption
pattern the note already carried (a stray leading character glued to the
new wikilink label). **Manually repaired directly** (Edit tool, working
from the note's exact byte content, not retyped) — restored the standard
blank-line body structure, kept exactly one correct `**Partner:**
[[Microsoft]]` line, preserved the note's existing manually-added
`## Notes` content byte-for-byte, and removed the corruption fragments
(a stray leading character, an orphaned partial-word remnant) that carried
no semantic content. This is a real, pre-existing, out-of-scope defect in
`insert_body_line_if_missing`'s positional-offset assumption (unrelated to
`REQ-SB-16`, predates this story) — logged to `MEMORY.md` and
`ESCALATIONS.md` as a new, separate finding; not fixed at the primitive
level here, since that is out of this task's declared `## Files to
Modify` scope.

With both notes restored to a correct, non-duplicated state, ran the
corrected `migrate_customer_to_partner("Microsoft")` **directly via
Python** (bypassing the ambiguous HTTP layer entirely, guaranteeing the
exact on-disk fixed code executed) — confirmed no stray server process
remained bound to any port first.

**[REQ-SB-16-US-01-AC-05] verified, PASS.** `Work/Customers/Microsoft.md`
no longer exists; `Work/Partners/Microsoft.md` exists with `type:
"Partner"`, `partner: "Microsoft"`, `tags: ["partner/microsoft",
"kind/partner"]`, no `affiliate_of` key. Exactly one file named
`Microsoft.md` exists anywhere in the vault (now at its new path) — every
`[[Microsoft]]` wikilink vault-wide still resolves by filename, confirmed.

**[REQ-SB-16-US-01-AC-06] verified, PASS.** A full vault-wide sweep after
the migration found **zero** remaining notes with `customer: "Microsoft"`
frontmatter, `customer/microsoft` tag, or a `**Customer:** [[Microsoft]]`
body line anywhere. All **15** real Microsoft-related notes (1 hub/now-
partner note, 2 Email, 1 Meeting, 1 Newsletter, 4 Notification, 6 Person)
now carry the correct Partner equivalent. Explicitly confirmed each of the
6 real Person notes (the 5 the story originally named, plus the 6th found
live) shows `**Partner:** [[Microsoft]]` and nothing else changed — still
`type: Person`, still `company/microsoft` tag, no `customer`/`partner`
frontmatter field or tag ever added to any Person note (Person notes never
carry that frontmatter shape at all, confirmed unchanged).

**[REQ-SB-16-US-01-AC-07] verified, PASS.** A second direct call reported
`hub_note_moved: False`, `notes_retagged: []` — a true no-op; no duplicate
`partner:` field or `partner/microsoft` tag anywhere; no further file
changes (re-confirmed via full-vault sweep).

**[REQ-SB-16-US-01-AC-08] verified, PASS (migration-rerun half — the
Person-note-processed half was already verified in `T03`).** Added a
distinctive manual line to `Work/Partners/Microsoft.md`'s body, called the
migration again — response showed `hub_note_moved: False`,
`notes_retagged: []`, and the hub note file was confirmed byte-for-byte
identical before/after.

**AC verification status:** AC-05, AC-06, AC-07, AC-08 (migration-rerun
half) — all **PASS**, live, against the real vault. Combined with `T01`/
`T02`/`T03`'s already-`Done` verification of AC-01/02/03/04/08
(Person-note-processed half), every locked AC of `REQ-SB-16-US-01` is now
verified.

**Status:** `Done`. `gate: clear`.
