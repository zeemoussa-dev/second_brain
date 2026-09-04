---
id: REQ-SB-10-US-01-T04
title: New POST /poc/retrofit-people-from-emails endpoint
parent_story: REQ-SB-10-US-01
requirement_id: REQ-SB-10
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-10-US-01-T02]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-10-US-01-T04 — New POST /poc/retrofit-people-from-emails endpoint

## Parent Story

- Story: [[REQ-SB-10-US-01]] — `../UserStories/REQ-SB-10-US-01-people-notes-from-email-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-10 *People Living Documents*

---

## Objective

Expose T02's `retrofit_people_from_emails` batch operation as a new one-off
HTTP endpoint, matching the existing `/poc/backfill-tags`,
`/poc/flatten-customer-folders`, and `/poc/retrofit-customer-hub-links`
one-off-migration-endpoint precedent, so the operator can trigger the
one-time People backfill against the real vault.

---

## Starting State → End State

**Before / Inputs:**
- `email_poc_router.py` has `/poc/classify-emails`, `/poc/backfill-tags`,
  `/poc/flatten-customer-folders`, `/poc/retrofit-customer-hub-links`, each
  a thin wrapper calling one business function and tallying its results
  list.
- T02 added `app/business/people_extraction.retrofit_people_from_emails`.

**After / Outputs:**
- A new `POST /poc/retrofit-people-from-emails` route, same thin shape as
  the four existing routes.

---

## Files to Modify

- `src/backend/app/api/email_poc_router.py`:
  1. Add to the import block (alongside the existing
     `from app.business.customer_hub_linking import retrofit_customer_hub_links`):
     ```python
     from app.business.people_extraction import retrofit_people_from_emails
     ```
  2. Append the new route at the end of the file:
     ```python
     @router.post("/retrofit-people-from-emails")
     def retrofit_people_from_emails_endpoint() -> dict:
         results = retrofit_people_from_emails()
         created = sum(1 for r in results if r["status"] == "created")
         linked = sum(1 for r in results if r.get("linked"))
         return {
             "notes_checked": len(results),
             "created": created,
             "linked": linked,
             "results": results,
         }
     ```

---

## Constraints

- Inherits from parent story (ADR-003: `api/` calls into `business/` only,
  never `data_access/` directly).
- Must NOT modify the four existing routes or their imports.
- Idempotent by construction (delegates entirely to T02's
  `retrofit_people_from_emails`, already idempotent) — safe to call
  repeatedly against the real live vault.

---

## Tests

<!-- All 8 of this task's tagged ACs are exercised by the same endpoint —
retrofit_people_from_emails contains one code path; the ACs differ only in
which real (or, where the live vault has no natural example, throwaway)
sender data is fed through it. Create any throwaway note directly via
vault_writer.write_note under Work/Emails/ with the minimal frontmatter
needed (sender, sender_email, and any other fields write_note/read_note
require) when the real vault doesn't already contain a natural example for
a given scenario — the same fallback REQ-SB-14-US-01-T02's smoke check
used. Delete every throwaway note (and any Person/Customer note it caused
to be created) once verified, restoring the vault to its pre-task state. -->

**Manual verification steps (run in this order, live against the real
configured vault — `VAULT_PATH` in `src/backend/.env`):**

1. Start the dev server: `.venv\Scripts\python.exe -m uvicorn app.main:app
   --reload` from `src/backend` (this also fires one real email capture run
   on startup per ADR-005 — an unrelated, already-known side effect).
2. Scan the vault for an existing sender_email with two or more captured
   Email notes and no Person note yet (or create two throwaway Email notes
   sharing one `sender_email`/`sender` if none exists naturally).
3. Confirm the vault has (or create via a throwaway note) at least one
   Email note with a blank/missing `sender_email` field.
4. `Invoke-RestMethod -Method Post
   http://127.0.0.1:8000/poc/retrofit-people-from-emails`.
   - **[REQ-SB-10-US-01-AC-01]** Confirm a Person note now exists at
     `Work/People/<slug-of-lowercased-sender-email>.md` for the sender
     identified in step 2, with `name`/`email` populated from that sender's
     Email notes and the `kind/person` tag present; confirm exactly one
     Person note file exists for that sender despite multiple source
     emails.
   - **[REQ-SB-10-US-01-AC-09]** Confirm the results list contains a
     `skipped_no_sender_email` entry for the note from step 3, and that the
     run completed without raising an exception.
5. Identify (or create via a throwaway note) a sender_email whose domain
   matches an existing known customer's name (e.g. an internal person at a
   customer whose Customer hub note already exists, or any domain whose
   derived company name — `label[0].upper() + label[1:]` of the part before
   the first `.` after `@` — equals a real `list_known_customers()` entry).
   Re-run the endpoint.
   - **[REQ-SB-10-US-01-AC-03]** Confirm that Person note's tags include
     `company/<slug>` for the derived company, its body includes a
     `[[wikilink]]` to that customer's existing hub note, and no second
     Customer hub note was created for that customer (still exactly one
     file at `Work/Customers/<Customer>.md`).
6. Identify (or create via a throwaway note) a sender_email whose domain
   does not match any known customer (e.g. an internal Core42 colleague,
   or a third party like Microsoft) — a company is derivable, just not a
   known customer. Re-run the endpoint.
   - **[REQ-SB-10-US-01-AC-04]** Confirm that Person note's tags include
     `company/<slug>` for that company, its body has no `[[wikilink]]`
     added, and no new Customer hub note was created for that company.
7. Identify (or create via a throwaway note) a sender_email on a personal/
   free email domain (e.g. `gmail.com`). Re-run the endpoint.
   - **[REQ-SB-10-US-01-AC-05]** Confirm that Person note has `name`/`email`
     populated, carries only the `kind/person` tag (no `company/` tag), and
     has no `[[wikilink]]` in its body.
8. Manually add distinctive user content to the Person note from step 5 or
   6 (e.g. a filled-in `linkedin` value, a `role:`-style free-form line, or
   a personality-observation paragraph in the body) via the Edit tool.
   Re-run the endpoint.
   - **[REQ-SB-10-US-01-AC-06]** Confirm the manually-added content is
     unchanged; confirm any still-missing baseline fields (if any existed)
     were topped up, and no field the user already filled in was
     overwritten.
   - **[REQ-SB-10-US-01-AC-02]** Confirm no duplicate Person note file was
     created for that sender across this and prior runs (still exactly one
     file per distinct sender email address).
9. For the AC-04 company from step 6 (no known-customer match yet), create
   a Customer hub note for that same company — either by adding a
   throwaway note with `customer: "<that company>"` frontmatter and calling
   `POST /poc/retrofit-customer-hub-links`, or by calling
   `customer_hub_linking.ensure_customer_hub_note("<that company>")`
   directly. Then re-run `POST /poc/retrofit-people-from-emails` again.
   - **[REQ-SB-10-US-01-AC-08]** Confirm the wikilink to that company's
     now-existing hub note has been added to the AC-04 Person note's body,
     and that the rest of its content — including the manual addition from
     step 8, if made to this same note — is otherwise unchanged.
10. Clean up: delete every throwaway note/hub note this run created, and
    remove any now-empty directories under `Work/`, restoring the real
    vault to its pre-task state. Stop the dev server.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `POST /poc/retrofit-people-from-emails` creates a Person note for
      every distinct sender email address among captured Email notes, one
      per address even when multiple emails share it
- [x] A second run never creates a duplicate Person note; existing notes are
      topped up (missing baseline fields only), never overwritten
- [x] A known-customer company gets both the `company/<slug>` tag and the
      wikilink, with no duplicate Customer hub note
- [x] A derivable-but-unknown company gets the tag only, no wikilink, no new
      Customer hub note
- [x] A non-derivable (personal/free-provider or absent) domain gets neither
      tag nor wikilink
- [x] Manually-added Person-note content survives every rerun
- [x] A company that later becomes a known customer gets its wikilink added
      retroactively on the next run, without disturbing anything else
- [x] An Email note with a blank `sender_email` is skipped, never errors the
      run
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (yes — new environmental constraint: port 8000 may be occupied by an unrelated `agentic-map` process; see Implementation Log)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The retrofit logic itself (the loop, the per-note decision, company
  derivation, customer matching) — that is T02; this task only adds the
  HTTP wrapper.
- The per-write capture hook — that is T03 (verifies AC-07 separately).

---

## Context / Notes

Matches `/poc/retrofit-customer-hub-links`'s exact shape: router imports one
business function, calls it, tallies simple counts from the results list,
returns a dict. No new dependency, no request body/query params needed.

The real live vault's actual sender population is not known in advance —
per REQ-SB-14-US-01-T04's own precedent (the ADNOC→TAQA test-candidate
substitution), adapt step-by-step using whatever real senders already fit
each scenario, falling back to a throwaway note only where the real vault
genuinely has no natural example (most likely for AC-05's personal-domain
case and AC-09's blank-sender_email case). Log any such substitution in the
Implementation Log the same way T04 of REQ-SB-14-US-01 did — a
scope-internal judgement call, not a deviation from AC intent.

---

## Implementation Log

**Coder pass (2026-08-11):** Edited `src/backend/app/api/email_poc_router.py`
exactly as specified in `## Files to Modify` — no other line changed:
1. Added `from app.business.people_extraction import
   retrofit_people_from_emails` to the import block (alongside the four
   existing `from app.business...` imports).
2. Appended `retrofit_people_from_emails_endpoint` (`POST
   /poc/retrofit-people-from-emails`) at the end of the file, exact shape
   from the task spec — thin wrapper, tallies `created`/`linked` from the
   results list. The four existing routes and their imports are untouched.

**Environment note (scope-internal, not a deviation):** Port `8000` was
already bound by an unrelated `agentic-map` process (`services.control_plane`,
confirmed via `Get-NetTCPConnection`/`Get-CimInstance Win32_Process` — a
different project's process, not Second Brain's) at the time this task ran,
so the dev server was started on port `8001` instead
(`.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001`) and
every `Invoke-RestMethod` call below targets `http://127.0.0.1:8001`. Purely
an environmental port choice, no code/behavior implication.

**Verification setup (manual mode, real live vault, no automated test
tooling yet):** Started the dev server, which — per MEMORY.md's documented
constraint — fired one real scheduled capture run on startup (no new
already-unprocessed emails were found this time; vault state after startup
was unchanged from before: 35 Email notes, only the two pre-existing Person
notes from `REQ-SB-10-US-01-T03` — `ahmad.hamzeh@core42.ai.md`,
`shadi.shaat@core42.ai.md`).

**Pre-run scan of the real vault** (`Work/Emails/`, grouping by
`sender_email`) found a rich, naturally-occurring candidate for every
scenario except one:
- `mohamed.eltanany@core42.ai` — 7 Email notes, no Person note yet → AC-01
  (multi-email dedup) candidate.
- Company `Core42` already has an existing `Work/Customers/Core42.md` hub
  note → AC-03 (known-customer tag+link) candidate, via the same sender.
- `karimlouis@microsoft.com` — domain `microsoft.com`, a real, derivable
  company ("Microsoft") with no matching known customer → AC-04
  (tag-only) candidate, reused for AC-06 (manual-content preservation) and
  AC-08 (company later becomes known) since it needs no second sender.
- `<operator-email>` — `live.com` is in `people_extraction.py`'s
  `_PERSONAL_EMAIL_DOMAINS` set → AC-05 (no company) candidate.
- No naturally-occurring blank-`sender_email` Email note existed (the
  task's own Context/Notes correctly anticipated this as the most likely
  fallback case) — created one throwaway note directly via
  `vault_writer.write_note("Work/Emails", "REQ-SB-10-US-01-T04-verification-
  throwaway-blank-sender", {...sender_email: "", ...}, body="...")` for
  **AC-09**.

**Verification — REQ-SB-10-US-01-AC-01, AC-03, AC-04, AC-05, AC-09 (first
`POST /poc/retrofit-people-from-emails` call):**

Confirmed pre-call: no Person note existed yet for `mohamed.eltanany@core42.ai`,
`karimlouis@microsoft.com`, or `<operator-email>`; no
`Work/Customers/Microsoft.md`.

Called the endpoint → `{"notes_checked": 57, "created": 18, "linked": 11,
"results": [...]}` (`notes_checked` covers every note under `Work/*/*.md`,
not just `Work/Emails/`, since `retrofit_people_from_emails` iterates
`vault_writer.list_all_note_paths()` per T02's design — Customer/Person
notes and any note with no `sender_email` are cleanly skipped
`skipped_no_sender_email`, matching AC-09's own no-error contract).

- **AC-01:** `mohamed.eltanany@core42.ai`'s first-seen Email note
  (`2026-08-05-Re- ADNOC Account Plan Review...`) got
  `"status": "created", "note_path": ".../Work/People/
  mohamed.eltanany@core42.ai.md"`; its six other Email notes (2 in
  `Work/Emails/`, 2 in `Work/Files/`, plus duplicates) all got
  `"status": "skipped_duplicate_sender_this_run"`. Read the created note:
  `type: "Person"`, `name: "Mohamed Eltanany"`,
  `email: "mohamed.eltanany@core42.ai"`, `tags: ["company/core42",
  "kind/person"]` — `kind/person` present, exactly one file for this
  sender despite 7 source emails. **PASS.**
- **AC-03:** That same note's tags include `company/core42`; its body is
  `**Customer:** [[Core42]]` (the existing hub-note link mechanism T02
  already reuses); `Work/Customers/Core42.md` appears only in the
  `skipped_no_sender_email` list (untouched) — `Get-ChildItem` on
  `Work/Customers/` confirms still exactly one `Core42.md`. **PASS.**
- **AC-04:** `karimlouis@microsoft.com`'s Email note
  (`2026-08-06-FW- AI Spokesperson Avatar...`) got `"status": "created",
  "company": "Microsoft", "customer_matched": null, "linked": false`. Read
  the created note: `tags: ["company/microsoft", "kind/person"]`, empty
  body (no wikilink). Confirmed `Work/Customers/Microsoft.md` does not
  exist (`Test-Path` → `False`); `Work/Customers/` still lists exactly the
  same 9 pre-existing hub notes. **PASS.**
- **AC-05:** `<operator-email>`'s Email note got `"status":
  "created", "company": null, "customer_matched": null, "linked": false`.
  Read the created note: `name: "Mahmoud Moussa"`,
  `email: "<operator-email>"`, `tags: ["kind/person"]` only,
  empty body. **PASS.**
- **AC-09:** The throwaway blank-`sender_email` note's result entry:
  `{"status": "skipped_no_sender_email"}`; the run completed and returned
  a valid 200 response with no exception. **PASS.**

(Bonus real-vault confirmation, not independently AC-tagged: the same run
also correctly processed `Work/Notifications/`-kind notes carrying
`sender_email` — e.g. `security-noreply@linkedin.com` matched known
customer `LinkedIn` and got linked, `systemnotification@adnoc.ae` matched
`ADNOC` and got linked — confirming the retrofit's vault-wide scope works
uniformly across `Kind` folders, per T02's own design comment.)

**Verification — REQ-SB-10-US-01-AC-02, AC-06 (manual edit + second call):**

Manually added a distinctive `## Notes` line to
`Work/People/karimlouis@microsoft.com.md` via the Edit tool (simulating
user-added content, per this task's own step 8 wording), recorded its
SHA-256 hash, then called the endpoint again →
`{"notes_checked": 75, "created": 0, "linked": 0, ...}`. The
`mohamed.eltanany@core42.ai` and `karimlouis@microsoft.com` result entries
both read `"status": "already_existed", "created": false`.

- **AC-02:** No duplicate Person note file was created for either sender
  across the two runs — `Get-ChildItem Work/People/` stayed at exactly 20
  files both before and after the second call (18 newly created + 2
  pre-existing from T03). **PASS.**
- **AC-06:** Re-hashed `karimlouis@microsoft.com.md` after the second
  call — identical SHA-256
  (`C2542EEA63FD60BCCF2DD78DDC1C0040534450F37886D504B96083762A42F836`),
  confirming byte-for-byte unchanged (no baseline field was overwritten;
  there were no missing baseline fields left to top up either, all six
  were already present from creation). **PASS.**

**Verification — REQ-SB-10-US-01-AC-08 (company later becomes a known
customer):**

Called `customer_hub_linking.ensure_customer_hub_note("Microsoft")`
directly (the task's own step-9-authorized alternative to a throwaway
Email-note + `/poc/retrofit-customer-hub-links` round-trip) → created
`Work/Customers/Microsoft.md`. Called
`POST /poc/retrofit-people-from-emails` a third time →
`{"notes_checked": 76, "created": 0, "linked": 1, ...}`; the
`karimlouis@microsoft.com` entry now reads `"customer_matched":
"Microsoft", "linked": true`. Read the note: body now begins
`**Customer:** [[Microsoft]]`, followed by the still-unchanged `## Notes`
manual-addition line from the AC-06 step, and `tags:
["company/microsoft", "kind/person"]` unchanged (no duplicate tag entry).
**PASS** — wikilink added retroactively, rest of the note (including the
manual addition) otherwise unchanged.

**Cleanup:** Deleted `Work/Customers/Microsoft.md` (a throwaway hub note —
Microsoft is a real third party, not a genuine customer of this vault's
business, so its hub note existed only to exercise AC-08) and the
throwaway blank-`sender_email` Email note from the AC-09 setup. Since
deleting the throwaway hub note would otherwise leave a dangling
`[[Microsoft]]` wikilink in the real, production `karimlouis@microsoft.com`
Person note, removed that one inserted line via the Edit tool, restoring
the note to the accurate state a real (non-customer) contact should have —
tag only, no link — while deliberately leaving the AC-06 `## Notes` manual
verification marker in place (same choice `REQ-SB-14-US-01-T04` made for
its TAQA hub-note marker: content added directly to a real note via the
Edit tool is not itself a "throwaway note" the cleanup step requires
deleting). Re-ran the endpoint once more as a final consistency check:
`{"notes_checked": 74, "created": 0, "linked": 0, ...}`,
`karimlouis@microsoft.com`'s entry back to `"customer_matched": null,
"linked": false"` — stable, no error, `Work/Customers/` back to its
original 9 files, `Work/People/` still 20 files (no accidental deletion of
any real Person note). No empty directories were created by the throwaway
notes (both were single files in already-populated folders), so none
needed removing.

**Real production data created and deliberately kept (per this task's own
scope — the retrofit is meant to run for real against the live vault, the
same way `REQ-SB-10-US-01-T03` kept its two real Person notes):** this run
created 18 real Person notes for every distinct real sender/notification
address already present in the vault — `mohamed.eltanany@core42.ai`,
`naima.bikbi@core42.ai`, `hanish.arora@core42.ai`,
`adithya.srinivasan1@g42.ai`, `emma.cloney@core42.ai`,
`mohammed.retmi@core42.ai`, `<operator-email>`,
`maik.kurz@core42.ai`, `gurpreet.singh@simplai.ai`,
`sandeep.penumadu@core42.ai`, `imtiaz.ahmed@core42.ai`,
`parvaze.suleman@dge.gov.ae`, `karimlouis@microsoft.com`,
`arun.kalathil@core42.ai`, `no-reply@teams.mail.microsoft`, `omni@g42.ai`,
`security-noreply@linkedin.com`, `systemnotification@adnoc.ae`. None of
these are throwaway; all left in place.

**Assumptions logged for spot-check (scope-internal, same shape as
`REQ-SB-14-US-01-T04`'s ADNOC→TAQA substitution):**
1. Dev-server port changed 8000 → 8001 because an unrelated `agentic-map`
   process already held 8000 (verified via process command-line
   inspection before touching anything) — environment-driven, no code
   change.
2. Test-candidate selection: used `mohamed.eltanany@core42.ai` (not a
   task-suggested name) for AC-01/AC-03 and `karimlouis@microsoft.com`
   for AC-04/AC-06/AC-08, both real, naturally-occurring senders found by
   scanning the live vault — exactly the "adapt using whatever real
   senders already fit each scenario" fallback this task's own
   Context/Notes section pre-authorized.
3. AC-09 needed a throwaway Email note (no natural blank-`sender_email`
   example existed) — also pre-authorized by this task's own
   Context/Notes as the most likely fallback case; created and deleted
   per the Tests section's own instructions.
4. Post-AC-08 cleanup choice: removed the `[[Microsoft]]` wikilink from
   the real `karimlouis@microsoft.com` note (to avoid leaving a dangling
   link to a deleted throwaway hub note) while keeping the AC-06 manual
   `## Notes` marker (matching `REQ-SB-14-US-01-T04` precedent for
   content added to a real, non-throwaway note). A judgement call on how
   literally to apply "restoring the real vault to its pre-task state" to
   a real note touched only as a side effect of a throwaway fixture, not
   a deviation from any AC's intent.

No new dependency, no shared-interface change, no ADR deviation, no
unanticipated file, no unclear/contradictory requirement — none of these
four rises to an escalation; logged here for human spot-check per the
coder's role.

**Cleanup — dev server:** Stopped the uvicorn reloader and server
processes (`Stop-Process` on both `python.exe` PIDs whose command line
included `Second Brain`/`uvicorn app.main:app`, plus one orphaned
`multiprocessing`-spawned worker process left parented to the already-
stopped reloader). Confirmed via
`Get-CimInstance Win32_Process -Filter "Name = 'python.exe'"` that only
the two unrelated `agentic-map` (`services.control_plane`) processes
remain — neither touched.

**MEMORY.md:** updated — added one new `## Constraints` entry: port `8000`
is not reliably free on this development host (an unrelated `agentic-map`
process may already hold it), so future live-verification runs should
check first and use an alternate port rather than assuming a bind failure
means Second Brain's own server is already running. The endpoint code
itself is a pure thin-wrapper mirror of the four existing `/poc/*` routes,
exactly as the task and story's architect notes already specified — no
codebase decision/pattern emerged from the code change itself, only this
one environmental constraint.

**Story-level note:** this was the last task in `REQ-SB-10-US-01`
(`T01`/`T02`/`T03` already `Done`); all nine of the story's locked ACs
(`AC-01` through `AC-09`) are now verified — `AC-07` live in `T03`, the
remaining eight live here. Per this task's own scope, propagating the
parent story's `status:`/`BACKLOG.md` is left to the orchestrator, not
done by this task directly.

`gate: flagged` (`gate_reason: trigger-1`) — the four scope-internal
assumptions logged above (port choice, test-candidate substitution,
throwaway-note fallback for AC-09, and the wikilink-removal cleanup
judgement call), none of which is a new dependency, shared-interface
change, ADR deviation, unanticipated file, or unclear/contradictory
requirement. `REVIEW-QUEUE.md` pointer added.

---

**Orchestrator review (2026-08-11):** all four assumptions reviewed and
approved — port 8001 substitution (8000 held by an unrelated agentic-map
process, no code depends on the literal port), real-sender substitution
(matches T04-of-REQ-SB-14-US-01's precedent exactly), the AC-09 throwaway
note (cleaned up), and the AC-08 cleanup (removed the throwaway hub note
and its dangling wikilink while correctly preserving the AC-06 manual
content and all 18 real Person notes this run genuinely created).
`gate: flagged → clear`.
