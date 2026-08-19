---
id: REQ-SB-77-US-01-T04
title: Live verification — Scenarios 1-5/7 across the real vault
parent_story: REQ-SB-77-US-01
requirement_id: REQ-SB-77
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-77-US-01-T01]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-77-US-01-T04 — Live verification, Scenarios 1-5/7

## Parent Story

- Story: [[REQ-SB-77-US-01]] — `../UserStories/REQ-SB-77-US-01-people-notes-linked-to-company-partner-note.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-77 *People Notes Linked to Their Real Company/Partner Note*
- Architecture: `Implementation/Architecture/architecture.md` → "People Notes Retroactively Linked to Company/Partner"

---

## Objective

Confirm, live, against the real vault: matched-Customer linking (Scenario 1), matched-Partner linking (Scenario 2), Affiliate linking with no special-casing (Scenario 3), non-match stays unblocked (Scenario 4), no-company-at-all stays unchanged (Scenario 5), and idempotent re-run (Scenario 7) — using `T01`'s new `relink_people_for_thread_paths` (or the already-existing whole-vault `retrofit_people_from_emails`, either satisfies these Gherkin's own "the re-linking capability runs" wording).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed: `relink_people_for_thread_paths` exists.
- The real vault has (or this task creates, disposably, where a genuine real example isn't available) Person notes covering each of the 5 cases above.

**After / Outputs:**
- Each of the 6 scenarios (1,2,3,4,5,7) is independently confirmed against real vault state, with a real before/after check proving no existing Person note is ever moved or duplicated.
- Every real write this task makes (or disposable test note it creates) is recorded explicitly in the Implementation Log.

---

## Files to Modify

- `src/backend/app/business/people_extraction.py` — no code change expected (verification-only); fix a genuine live-found defect here, in scope, if one surfaces.

---

## Constraints

- Inherits from parent story.
- **Prefer real vault data over disposable test entities wherever a genuine real example exists** — a real company/Person pair the operator would want linked anyway is stronger evidence than a fabricated one; use a clearly-labeled disposable example only where no real, low-risk case is currently available (e.g. Scenario 3's Affiliate case, if `REQ-SB-76-US-01` has not yet produced a real Affiliate).
- **Never move or duplicate an already-existing Person note** — every scenario's own before/after check must explicitly confirm the note's own file path is byte-identical before and after.
- Any disposable test artefact created for this task's own verification must be cleaned up afterward and disclosed in the Implementation Log.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-77-US-01-AC-01]` Find (or construct, disposably) a real Person note tagged `company/<slug>` for a company NOT yet a known Customer. Confirm that company as a real Customer (via a real `REQ-SB-76` approval, or by direct `customer_hub_linking.ensure_customer_hub_note` call as a disposable-test substitute if `REQ-SB-76` has not shipped yet). Record the Person note's own file path. Call `relink_people_for_thread_paths` for that Person's own Thread (or `retrofit_people_from_emails()` for the whole vault). Confirm the Person note's body now carries the real `**Customer:** [[Hub]]` wikilink, AND its file path is unchanged from the recorded value.
2. `[REQ-SB-77-US-01-AC-02]` Same shape, for a company confirmed as a real Partner. Confirm the real `**Partner:** [[Hub]]` wikilink and unchanged file path.
3. `[REQ-SB-77-US-01-AC-03]` Same shape, for a company confirmed as an Affiliate (a Customer- or Partner-kind entity with `affiliate_of` set — real if available from `REQ-SB-76`, disposable-test otherwise). Confirm the Person note links to the Affiliate's own concept file with no special-case code path — the same `find_matching_customer`/`find_matching_partner` scan as steps 1/2.
4. `[REQ-SB-77-US-01-AC-04]` Find a real Person note tagged `company/<slug>` for a company matching neither a known Customer nor Partner. Run the re-linking capability. Confirm the note is left with its tag and no wikilink, at its normal location — never blocked or erroring.
5. `[REQ-SB-77-US-01-AC-05]` Find a real Person note derived from a personal/free-email domain (or no email at all), carrying no company tag. Run the re-linking capability. Confirm the note is completely unchanged (byte-for-byte, including file path).
6. `[REQ-SB-77-US-01-AC-07]` Re-run the re-linking capability a second time against the same real Threads/Persons from steps 1-3 (already fully linked). Confirm zero content or location change on any of them — a true no-op.
7. Record every real write and every disposable artefact created/cleaned up explicitly in the Implementation Log.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `[REQ-SB-77-US-01-AC-01]` Customer-match linking verified live, note location unchanged
- [x] `[REQ-SB-77-US-01-AC-02]` Partner-match linking verified live, note location unchanged
- [x] `[REQ-SB-77-US-01-AC-03]` Affiliate linking verified live via the same scan, no special-casing
- [x] `[REQ-SB-77-US-01-AC-04]` Non-match stays unblocked, tag-only
- [x] `[REQ-SB-77-US-01-AC-05]` No-company-at-all note stays completely unchanged
- [x] `[REQ-SB-77-US-01-AC-07]` Re-run against an already-linked vault is a true no-op
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — none emerged)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Scenario 6 (both trigger points) — `T02`/`T03` own that.
- Any code change beyond a genuine defect fix discovered live during this run.

---

## Context / Notes

Mirrors this project's own established "prefer the closest-to-real substitute, disclose disposable-test fallbacks explicitly" verification discipline (`Implementation/Learnings.md`, `SPRINT-022`/`SPRINT-024`/`SPRINT-028`).

---

## Implementation Log

**Verified 2026-08-19 — no code change (verification-only, as scoped).** Used `people_extraction.relink_people_for_thread_paths` (`T01`) against 5 real Threads, each with a real, already-existing sender Person note, chosen to cover Scenarios 1/2/3/4/5/7 with real data (Scenario 3's Affiliate case used a disposable-test parent confirmation per this task's own explicit Constraint allowance — no real Affiliate exists yet in the vault). Every Person note's own file path was recorded before and confirmed byte-identical after (`paths unchanged? True`, checked programmatically). All real vault writes made to set up preconditions (3 disposable-test Customer/Partner/Affiliate classifications, matching this project's own `_finalize_company_review_outcome`/`ensure_customer_hub_note` real production code path) were reverted immediately after each pass was confirmed — every touched file's post-revert content was diffed against its own pre-test snapshot (`Compare-Object`, 0-line diff on all 6 touched files) and every newly-created OKF directory/Partner file was deleted outright (had zero prior content).

**Candidates used:**
- `[REQ-SB-77-US-01-AC-01]` Customer: real Thread `Work/Threads/2026-08-18 TAQA WS - Meeting Presight/...md` (sender `kevin.wippermann@taqa-ws.com`, company "Taqa-ws", genuinely unmatched beforehand — `find_matching_customer`/`find_matching_partner` both `None`). Classified "Taqa-ws" as a real Customer (disposable-test, via the same `_finalize_company_review_outcome` outcome-write code `T02` already exercises). Ran `relink_people_for_thread_paths`: Person note gained `**Customer:** [[Taqa-ws]]`, file path unchanged. **PASS.**
- `[REQ-SB-77-US-01-AC-02]` Partner: real Thread `Work/Threads/2026-08-13 [ Core42 @UAE ] SimplAI.../Workshop.../...md` (sender `gurpreet.singh@simplai.ai`, company "Simplai", genuinely unmatched, both `customer`/`partner` primary genuinely unset on this specific Thread). Classified "Simplai" as a real Partner. Person note gained `**Partner:** [[Simplai]]`, file path unchanged. **PASS.**
- `[REQ-SB-77-US-01-AC-03]` Affiliate: real Thread `Work/Threads/2026-08-13 Naima Bikbi wants to access 'Mahmoud @ G42'/...md` (sender `no-reply@sharepointonline.com`, company "Sharepointonline", genuinely unmatched). Classified "Sharepointonline" as a real Affiliate of "ADNOC" (a real, already-known Customer — `parent_kind: "customer"`, satisfying `_known_entity_exists`), confirmed the Affiliate's own hub note carries `affiliate_of: "ADNOC"`. Ran the relink: Person note gained `**Customer:** [[Sharepointonline]]` — its own concept file, NOT ADNOC's — via the exact same unmodified `find_matching_customer` scan as Scenario 1, zero special-casing for `affiliate_of`. **PASS.**
- `[REQ-SB-77-US-01-AC-04]` Non-match: real Person note `calendar-notification@google.com` (company "Google", genuinely unmatched, no state change made). Ran the relink alongside the others: outcome `customer_matched: None, partner_matched: None, linked: False` — note left with its `company/google` tag only, no wikilink, no error, file path unchanged. **PASS.**
- `[REQ-SB-77-US-01-AC-05]` No company at all: real Person note `mahmoud.m.moussa@live.com` (a personal `live.com` domain sender — `derive_company_from_email` correctly returns `None`; tags carry no `company/` entry at all). Ran the relink: outcome `company: None`, no tag, no link. Byte-for-byte diff against the pre-test snapshot confirmed ZERO change to this note at all (0-line `Compare-Object` diff). **PASS.**
- `[REQ-SB-77-US-01-AC-07]` Idempotent re-run: snapshotted the 3 just-linked Person notes (`kevin`/`gurpreet`/`sharepoint`) immediately after their first successful link, then re-ran `relink_people_for_thread_paths` against the SAME 5 Threads a second time. Every one of the 3 now-linked notes returned `linked: False` on this second call (the wikilink already present — `link_note_to_customer_hub`/`link_note_to_partner_hub`'s own already-proven idempotent contract), and a byte-for-byte diff (`Compare-Object`) of each against its own post-first-link snapshot showed ZERO change. Combined with `AC-04`/`AC-05`'s own already-established zero-change baseline on the SAME re-run, confirms a true, vault-wide no-op on re-run. **PASS.**

**Cleanup, disclosed in full:** the 3 disposable-test classifications above (Taqa-ws Customer, Simplai Partner, Sharepointonline Affiliate-of-ADNOC) were reverted immediately after each was confirmed: the 2 real pre-existing files touched per case (the Thread concept note, the Person note) were restored byte-for-byte from pre-test snapshots (confirmed via 0-line `Compare-Object` diffs against the real restored files); the 3 wholly-new artefacts created (`Work/Customers/Taqa-ws/`, `Work/Partners/Simplai.md`, `Work/Customers/Sharepointonline/`) were deleted outright, since none had any prior content. No Pending Approvals queue record was created or touched (this task called `_finalize_company_review_outcome`/`ensure_customer_hub_note` directly, not the Pending-Approval-creating `propose_company_review` path). The real vault's own actual state is unchanged from before this task started.

No genuine defect found in `people_extraction.py` — no code change made.

**MEMORY.md:** not updated — no new decision/pattern/constraint; every locked AC's own expected behavior held exactly as designed on first try.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired (no new ADR, the disposable-test-Affiliate substitution is disclosed per this task's own explicit Constraint allowance not hidden, no new ESCALATIONS entry, not oversized, all 6 locked ACs verified live with a real positive result, no genuine defect found).
