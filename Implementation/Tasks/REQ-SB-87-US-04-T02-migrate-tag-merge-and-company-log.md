---
id: REQ-SB-87-US-04-T02
title: Migrate tag-merge + company log-entry append/re-sort onto vault_manager.py
parent_story: REQ-SB-87-US-04
requirement_id: REQ-SB-87
type: backend
status: Ready
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

- [ ] Tag-merge for Thread + every RawMessage goes through
      `vault_manager.merge_tags`
- [ ] Company log-entry append/re-sort logic byte-for-byte unchanged
- [ ] Person notes never tagged
- [ ] Unresolvable company name reported, never fabricated
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

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

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
