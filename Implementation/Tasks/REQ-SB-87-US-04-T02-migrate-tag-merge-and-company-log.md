---
id: REQ-SB-87-US-04-T02
title: Migrate tag-merge + company log-entry append/re-sort onto vault_manager.py
parent_story: REQ-SB-87-US-04
requirement_id: REQ-SB-87
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-04-T01]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-04-T02 — Migrate Tag-Merge + Company Log-Entry Append/Re-Sort Onto vault_manager.py

## Parent Story

- Story: [[REQ-SB-87-US-04]] — `../UserStories/REQ-SB-87-US-04-summarize-and-tag-threads-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Migrate `apply_thread_review.py`'s own `merge_tags` calls (Thread +
every RawMessage under it) onto `vault_manager.py`'s shared `merge_tags`
primitive, leaving company resolution, the never-tag-Person-notes rule,
and the company `-log.md` append/re-sort logic entirely hand-written and
unchanged.

---

## Starting State → End State

**Before / Inputs:**
- Real, current `apply_thread_review.py` (read directly, 2026-09-01):
  `build_company_index`/`resolve_companies` (scans `Work/Customers`/
  `Work/Partners` hub notes, matches on `name`/`aliases`, deduped by
  slug); `tags = [f"{kind}/{slug}" for ...]`; its own local `merge_tags(path,
  new_tags)` unions into `tags` frontmatter for the Thread AND every
  RawMessage under `messages/` (never Person notes — the 2026-08-21 bug
  fix, explicitly preserved); `append_log_entry(hub_md, date,
  short_summary, thread_wikilink)` appends one dated line to
  `<hub_md.stem>-log.md`, then re-sorts the WHOLE file's entries
  newest-to-oldest (dedup on exact `(date, line_text)` match).

**After / Outputs:**
- The script's own local `merge_tags` calls (for the Thread and each
  RawMessage) are replaced with `vault_manager.merge_tags` — the SAME
  real primitive `create_companies_partners.py` already uses, confirmed
  byte-compatible behavior (unions into `tags`, never removes, returns
  whether anything changed).
- `build_company_index`/`resolve_companies`/`append_log_entry` stay
  entirely hand-written — this task does not touch them, only the
  underlying tag-WRITE primitive each one's caller uses.
- The 2026-08-21 never-tag-Person-notes fix is preserved exactly — this
  task's own diff touches only the Thread/RawMessage tag-merge call sites,
  never introduces a Person-note write anywhere.

---

## Files to Modify

- `Hermes-Provisioning/skills/company-review/summarize-and-tag-threads/scripts/apply_thread_review.py`

---

## Constraints

- Inherits from parent story.
- `build_company_index`/`resolve_companies`, the never-tag-Person-notes
  rule, and `append_log_entry`'s own re-sort/dedup logic are untouched,
  byte-for-byte.
- Verify against a scratch vault, distinct `--vault-path`.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`, real
Thread content with at least one resolvable company name and one
genuinely unresolvable name):**
1. `[REQ-SB-87-US-04-AC-01]` Run the migrated `apply_thread_review.py`
   against a Thread whose agent-provided payload names one or more real,
   resolvable companies; confirm every resolved company still gets its
   `customer/<slug>`/`partner/<slug>` tag merged onto the Thread AND every
   message under it, and the script still prints `{tags_applied,
   companies_unresolved, messages_tagged, log_entries_added,
   last_message_at, last_summarized_at}` with the same meaning as today
   (combined with `T01`'s own `## Summary`/stamping confirmation, this
   closes out `AC-01` fully).
2. `[REQ-SB-87-US-04-AC-03]` Confirm each resolved company's own
   `<Name>-log.md` gets one dated log-entry line appended, and the whole
   file's entries are re-sorted newest-to-oldest, exactly as today —
   including a real case where a new entry's own date is NOT the newest
   (confirm it lands in the correct sorted position, not just appended at
   the end).
3. `[REQ-SB-87-US-04-AC-04]` Confirm no Person note is ever tagged as a
   side effect — inspect every Person note linked from the Thread's own
   messages (`participant_links`) before and after the run; confirm zero
   tag changes to any of them.
4. `[REQ-SB-87-US-04-AC-05]` Include a company name in the payload that
   does not match any real Customer/Partner/Affiliate hub note; confirm it
   is reported in `companies_unresolved` and no hub note is fabricated.

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Tag-merge for Thread + every RawMessage goes through
      `vault_manager.merge_tags`
- [x] Company log-entry append/re-sort logic byte-for-byte unchanged
- [x] Person notes never tagged
- [x] Unresolvable company name reported, never fabricated
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new hard rule, see Implementation Log)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `## Summary` write / stamping — `T01`.
- Retiring `_HUMAN_OWNED_HEADERS` — `T03`.
- Real-vault verification / cutover — `T04`.

---

## Context / Notes

Read the real current `apply_thread_review.py` directly before editing
(reproduced in Starting State above from a 2026-09-01 read).

---

## Implementation Log

**2026-09-01, coder.**

**What was changed (`apply_thread_review.py` only, per `## Files to
Modify`):**
- The Thread's own and every RawMessage's own tag-merge call sites (two:
  `merge_tags(thread_path, tags)`, `merge_tags(message_path, tags)`) now
  call `vm.merge_tags(...)` — `vault_manager.py`'s shared primitive
  (already deployed to this Skill's own `scripts/` folder by `T01`), the
  SAME one `create_companies_partners.py` already uses.
- This file's own local `merge_tags(path, new_tags)` function (the
  hand-rolled per-line frontmatter-preserving version) is REMOVED
  outright — once both call sites moved, it had zero remaining callers
  anywhere in the file (confirmed by reading the whole file, not
  assumed). Docstring updated with a short migration note explaining
  the removal.
- `build_company_index`/`resolve_companies` (company resolution),
  the never-tag-Person-notes rule, and `append_log_entry` (log-entry
  append/re-sort) are untouched, byte-for-byte — confirmed by diff-review
  of the final file against the pre-edit read.
- Corrected one now-stale sentence in the `T01` migration note (it said
  tag merging was "still using this file's own hand-rolled ... `merge_tags`
  ... primitives below -- `REQ-SB-87-US-04-T02`'s own scope", which read as
  a forward-looking TODO note before this task existed to resolve it — now
  reads accurately post-migration.

**Scope-internal judgment call (logged for human spot-check, not an
escalation):** whether the now-dead local `merge_tags` function should be
removed immediately (this task) or left "defined, unused" the way `T01`
left `_HUMAN_OWNED_HEADERS`/`insert_body_section_if_missing`/
`replace_body_section` for `T03` to retire. Resolved: those three stay
because they are STILL load-bearing for other, not-yet-migrated sections
(`## Personal Notes`/`## Actions`/`## Related`/`## Files`) — `T03`'s own
explicit scope. `merge_tags` has no such remaining consumer anywhere in
this file once this task's own two call sites move — keeping a fully dead
duplicate primitive around would directly contradict REQ-SB-87 point 7's
own binding principle ("never a second, bespoke write path"), so removal
is this task's own natural conclusion, not scope creep.

**Live verification (scratch vault, distinct `--vault-path`, seeded from
real Thread/Customer/Partner/Person template and content shapes read
directly from the real, live vault — synthetic company/person names used
for the scratch content itself, per the story's own scratch-vault-first
Constraint):** scratch vault built at a session-scoped temp directory:
real `thread`/`customer`/`partner` `Template.json` files copied
byte-identical from the real, live vault's own `.second-brain/data/
Templates/`; `Work/Customers/Acme/Acme.md` (name `"Acme Corp"`, alias
`"Acme"`, pre-existing `tags: ["customer/acme"]`) + `Acme-log.md`;
`Work/Partners/BetaPartner/BetaPartner.md` + `BetaPartner-log.md`; two
real-shaped `Work/People/*.md` Person notes (`jane.doe@acme-scratch.
example`, pre-existing `tags: ["kind/person", "customer/acme"]`;
`sam.internal@core42-scratch.example`, pre-existing `tags:
["kind/person"]`) linked via `participant_links` from the scratch
messages below; three scratch Threads, each with one RawMessage:
- **Thread A** (`2026-08-20 Acme Renewal Kickoff`, pre-existing Thread
  `tags: ["internal"]`, message dated 2026-08-20 09:00) — payload
  companies `["Acme Corp", "Ghost Company Not Real"]`.
- **Thread B** (`2026-08-10 Acme Contract Review`, NO pre-existing `tags`
  key at all, message dated 2026-08-10 14:30) — payload companies
  `["Acme", "Beta Partner"]`.
- **Thread C** (`2026-08-15 Acme Status Update`, pre-existing Thread
  `tags: ["urgent"]`, message dated 2026-08-15 10:00) — payload companies
  `["Acme Corp"]`. Run LAST, deliberately dated in the MIDDLE of A/B's
  dates, to test the out-of-order-arrival re-sort case.

Ran the real, migrated `apply_thread_review.py` (venv Python,
`src/backend/.venv/Scripts/python.exe` — stdlib-only script, any real
Python works) against all three, in order A → B → C, then re-ran A a
second time for an idempotence check:

- `[REQ-SB-87-US-04-AC-01]` **PASS (fully closes out, combined with
  `T01`'s own Summary-write confirmation).** Run A: `tags_applied:
  ["customer/acme"]`, `companies_unresolved: ["Ghost Company Not Real"]`,
  `messages_tagged: 1`. Confirmed on disk: Thread's own `tags` became
  `["internal", "customer/acme"]` — the pre-existing `"internal"` tag
  PRESERVED, not overwritten; the message's own `tags` (absent before)
  became `["customer/acme"]`. Run B: `tags_applied: ["customer/acme",
  "partner/betapartner"]` — both a `customer/` and a `partner/` tag
  applied from one payload; Thread's own `tags` key (didn't exist before)
  correctly created as `["customer/acme", "partner/betapartner"]`. Run C:
  `tags_applied: ["customer/acme"]`; Thread's own pre-existing `tags:
  ["urgent"]` became `["urgent", "customer/acme"]` — preserved again.
  Output JSON contract unchanged across all runs:
  `{tags_applied, companies_unresolved, messages_tagged,
  log_entries_added, last_message_at, last_summarized_at}` present with
  the same meaning every time.
- `[REQ-SB-87-US-04-AC-03]` **PASS.** After A → B → C, `Acme-log.md`
  read back:
  ```
  - 2026-08-20: Acme renewal kickoff -- scope alignment -- [[2026-08-20 Acme Renewal Kickoff]]
  - 2026-08-15: Acme status on track -- [[2026-08-15 Acme Status Update]]
  - 2026-08-10: Acme contract review with Beta Partner -- [[2026-08-10 Acme Contract Review]]
  ```
  Correctly newest-to-oldest, and the 08-15 entry (added LAST, in the
  THIRD run) landed in the correct MIDDLE position, not appended at the
  end — confirms the re-sort, not a plain append, is what's actually
  running. `BetaPartner-log.md` correctly got its own single entry from
  Run B. Re-running Thread A a second time: `Acme-log.md` still shows
  exactly the same 3 entries (no duplicate line for the 2026-08-20 date +
  identical text) — the `(date, line_text)` dedup holds through the
  migrated tag-merge path.
- `[REQ-SB-87-US-04-AC-04]` **PASS.** Both real Person notes
  (`jane.doe@...`, `sam.internal@...`) read back byte-identical to their
  pre-run snapshot (`tags: ["kind/person", "customer/acme"]` and `tags:
  ["kind/person"]` respectively) after all four runs (A, B, C, re-run A)
  — despite both being linked via `participant_links` from Threads/
  messages that DID get tagged. Zero tag changes to either Person note at
  any point.
- `[REQ-SB-87-US-04-AC-05]` **PASS.** `"Ghost Company Not Real"` (Run A's
  payload) reported in `companies_unresolved` every run; confirmed no
  `Ghost*` folder/note exists anywhere under `Work/Customers` or
  `Work/Partners` after the full run sequence (`Get-ChildItem -Recurse`
  scoped to both roots, zero matches).
- Re-run A's idempotence check also confirms `messages_tagged: 0` on the
  second run (the message already carried the tag, so `vm.merge_tags`
  correctly reports "nothing changed") — matches the original hand-rolled
  `merge_tags`'s own idempotence contract exactly, not just "returns
  True/False" in the abstract.
- `python -m py_compile` on the modified file — clean.
- `git status` confirms only `apply_thread_review.py` (this task's one
  `## Files to Modify` entry) was touched under this Skill's `scripts/`
  folder (plus this task file / CHANGELOG.md / story / BACKLOG / sprint
  status, per the coder's standing exception); `vault_manager.py` shows
  untracked only because `T01` deployed it and it hasn't been committed
  yet — not touched by this task.

**Deferred to later tasks (not this task's own scope, not silently
absorbed):** retiring `_HUMAN_OWNED_HEADERS`/`_CALLER`/
`insert_body_section_if_missing`/`replace_body_section` and converging
`## Personal Notes`/`## Actions`/`## Related`/`## Files` onto the
template's own section-access declarations is `T03`; real-vault
retrofit-safety and the live `job4` cron cutover (including deploying the
migrated script to the real, active Hermes profile location) is `T04`.

gate: clear 2026-09-01 — no MUST-FLAG trigger fired: no new dependency, no
shared-interface change beyond what the story's own Notes already named,
no ADR touched, no contradictory input, all four locked verification
points (`AC-01` fully, `AC-03`, `AC-04`, `AC-05`) passed live. The
dead-code-removal judgment call above is logged for human spot-check per
hard rule 5, not a flag trigger.
