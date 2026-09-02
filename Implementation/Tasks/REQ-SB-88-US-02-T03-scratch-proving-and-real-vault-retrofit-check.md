---
id: REQ-SB-88-US-02-T03
title: Scratch-vault verification + real-vault retrofit check against an already-linked note
parent_story: REQ-SB-88-US-02
requirement_id: REQ-SB-88
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-88-US-02-T02]
created: 2026-09-02
updated: 2026-09-02
---

# REQ-SB-88-US-02-T03 — Scratch-Vault Verification + Real-Vault Retrofit Check Against an Already-Linked Note

## Parent Story

- Story: [[REQ-SB-88-US-02]] — `../UserStories/REQ-SB-88-US-02-track-opportunities-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-88 *Close the Remaining `vault_manager.py` Migration Gaps — Attachment Summarization + Opportunity Linking*

---

## Objective

Run a full regression pass of `T01`-`T02`'s own scenarios together against a
scratch vault, then prove the fully-migrated `link_opportunity.py` is
retrofit-safe against a real Thread or Meeting this Skill already linked to a
real Opportunity before this migration, and deploy the migrated script to the
real, active Hermes profile location.

---

## Starting State → End State

**Before / Inputs:**
- `T01`-`T02` complete and individually verified against a scratch vault.
- A real Thread or Meeting note this Skill already linked to a real
  Opportunity before this migration (per SKILL.md's own documented Job 3
  usage — genuinely exists in the live vault; identify it directly by
  reading real notes' own `opportunities` frontmatter, not assumed).

**After / Outputs:**
- A real, disclosed confirmation that the migrated script, run again
  against that real note/Opportunity pair, leaves the note's own
  `opportunities` frontmatter list and `## Related` section both
  byte-identical — no duplicate wikilink, no lost content.
- The migrated `link_opportunity.py` (+ `vault_manager.py`, if `T01`
  found and applied a resync) deployed to the real, active Hermes profile
  location this Skill actually runs from.

---

## Files to Modify

- None new — deployment of the already-migrated file(s) from `T01`-`T02`
  to the real, active Hermes profile location. No further code changes.

---

## Constraints

- Inherits from parent story.
- **This task must NOT run until `T01`-`T02` have both already passed
  against a scratch sample** — the real-vault check happens immediately
  before deployment, never instead of scratch-vault proving.
- Read-then-compare technique only against the real vault — snapshot
  before, run, diff after; never fabricate a new link for a real note/
  Opportunity pair this task doesn't already have a real prior link for.
- This Skill is manual-only, mid-chat-triggered — no cron/scheduled
  trigger exists or is introduced by this story.

---

## Tests

**Manual verification steps:**

1. (Unlabeled, supporting — full regression) Re-run `T01`'s own `AC-01`/
   `AC-03`/`AC-04` scenarios and `T02`'s own `AC-02` scenario together, in
   one continuous scratch-vault pass, against the FINAL, fully-migrated
   `link_opportunity.py` (both Thread and Meeting targets) — confirms no
   regression introduced by `T02`'s own changes to `T01`'s already-proven
   behavior.
2. `[REQ-SB-88-US-02-AC-05]` Pick a real Thread or Meeting note this Skill
   already linked to a real Opportunity before this migration (confirmed
   via its own `opportunities` frontmatter). Snapshot the note's own
   frontmatter and `## Related` section to the scratchpad before running
   anything. Run the newly-deployed, migrated `link_opportunity.py` again
   with the SAME note/Opportunity pair. Confirm on disk: `opportunities`
   frontmatter and `## Related` are both byte-identical before/after —
   `linked: false`, no duplicate wikilink, no lost content.
3. (Unlabeled, supporting) Confirm the deployed script (+ `vault_manager.py`,
   if resynced) at the real, active Hermes profile location is
   byte-identical to the fully-migrated repo copy (`Compare-Object`).
4. (Unlabeled, supporting) Confirm the real, live Thread Template.json's
   `## Related` `allowed_callers` includes `link_opportunity` alongside
   `link_person_to_thread` (this is `T02`'s own edit — confirm it's
   present at the real, live path).

**Automated tests:** `n/a — real-vault verification is not run against an
isolated fixture, by definition`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Full `T01`-`T02` regression pass confirmed clean against a scratch
      vault (both Thread and Meeting targets)
- [x] Real-vault retrofit-safety confirmed — a real, already-linked note's
      `opportunities` frontmatter and `## Related` section are both left
      byte-identical on a forced re-run with the same Opportunity
- [x] Migrated script deployed to the real, active Hermes profile location
- [x] Real, live Thread Template.json confirmed to carry `T02`'s own
      `## Related` `allowed_callers` edit
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any further code change.
- Any cron/scheduled provisioning — this Skill stays manual-only,
  mid-chat-triggered, per the story's own Constraint.

---

## Context / Notes

Mirrors `REQ-SB-87-US-04-T04`'s own real-vault retrofit-check shape
(read-then-compare, snapshot-before, bounded to already-known real
content), adapted here for `track-opportunities`' own no-cron, manual-only
usage — this task's "cutover" is deployment only, there is no schedule to
cut over.

---

## Implementation Log

**2026-09-02, coder.** Concurrency check performed before touching the
real vault (same check as `REQ-SB-88-US-01-T03`, re-run immediately
before this task's own real-vault touch so the two never overlap):
confirmed `REQ-SB-87-US-02-T05` still `Ready`, `email-delta-capture`
cron still `paused`, and zero matching capture/summarize/ingest
processes running. This task's own real-vault touch was sequenced AFTER
`REQ-SB-88-US-01-T03`'s, never concurrently with it.

**Full regression pass (Unlabeled, supporting):** re-ran `T01`'s own
`AC-01`/`AC-03`/`AC-04` scenarios and `T02`'s own `AC-02` scenario
together, in one continuous pass, against the scratch vault using the
FINAL, fully-migrated `link_opportunity.py` (a fresh scratch Thread C, to
isolate from earlier per-task test state): ambiguous-title refusal
(`AC-03`), resolution + real link with `--customer` (`AC-01`/`AC-03`),
idempotent re-run (`linked: false`, `AC-02`), and no-match refusal
(`AC-04`) all confirmed **PASS** against the final combined code. Final
Thread C state: `opportunities: ["[[Renewal 2026]]"]`, `## Related`
gained exactly one `- [[Renewal 2026]]` line, a fresh `id` minted — zero
regression from `T02`'s own changes onto `T01`'s already-proven behavior.

**Real-vault retrofit-safety check
(`[REQ-SB-88-US-02-AC-05]`):** searched the real vault directly (not
assumed) for a real Thread/Meeting already linked to a real, still-
existing Opportunity note (cross-checked every `opportunities:` wikilink
against the real Opportunity note it names, since PPT/deck note titles
can drift over time — one candidate Thread's own referenced Opportunity
title no longer matched any real Opportunity note, so it was excluded
rather than used). Found a clean match: `Work/Threads/2026-08-12 FW-
ADNOC - Amendement signature/2026-08-12 FW- ADNOC - Amendement
signature.md`, already linked to the real `ADNOC AVS→Azure Native
Landing Zone Amendment` Opportunity (`customer: "Adnoc"`) in both its
`opportunities` frontmatter AND its `## Related` section. Snapshotted the
Thread note to the scratchpad before running anything. Ran the newly-
deployed, migrated `link_opportunity.py` again with the SAME note/
Opportunity/`--customer` triple against the REAL vault. **PASS.**
Confirmed via direct `diff` against the snapshot: the Thread note is
byte-IDENTICAL, zero diff — `linked: false` (confirmed by calling
`link_opportunity()` directly in-process, see below), no duplicate
wikilink in either `opportunities` or `## Related`, no lost content.

**Disclosed, non-blocking finding (pre-existing, NOT introduced by this
migration):** the CLI's own `main()` → `print(json.dumps(...))` call
crashed with `UnicodeEncodeError` when the real Opportunity title
contains `→` (U+2192) and this shell's stdout uses the Windows `cp1252`
console codepage — this project's own already-documented
`SPRINT-038` antipattern ("Windows console codepage can silently mangle
non-ASCII script output"), now reconfirmed live for a REAL vault entity,
not just a test string. Confirmed this is unrelated to this migration:
`main()`'s `print()` line and `json.dumps()` call are byte-unchanged by
`T01`/`T02`, and the underlying `link_opportunity()` function itself ran
and returned correctly BEFORE the print crashed (confirmed by calling
`link_opportunity()` directly in-process with `python -X utf8`, bypassing
the crashing CLI print: `{"linked": false, "note_path": ..., 
"opportunity_path": "...ADNOC AVS→Azure Native Landing Zone
Amendment...")`}` — the real Opportunity write logic is correct; only the
CLI's own final stdout print is affected, and only under a `cp1252`
console). Out of this task's own `## Files to Modify` scope (fixing
`main()`'s stdout encoding isn't part of the write-mechanics migration),
so not silently fixed here — flagged to `REVIEW-QUEUE.md` instead, since
a REAL, currently-live Opportunity title (`ADNOC AVS→Azure Native Landing
Zone Amendment`) would hit this today if invoked for real by an agent
under a `cp1252` console.

**Deployment + Template.json confirmation:** copied the fully-migrated
`link_opportunity.py` to the real, active Hermes profile location
(`opp-manager/skills/company-review/track-opportunities/scripts/`);
`vault_manager.py` there was already byte-current (confirmed at `T01`,
re-confirmed here, no resync needed). `diff` confirmed both files
byte-identical to the repo copies post-deploy. Confirmed the real, live
`Templates/thread/Template.json`'s `## Related` `allowed_callers` array
is `["link_person_to_thread", "link_opportunity"]` at its real, live
path (this is `T02`'s own edit, live-confirmed here).

**Assumptions (scope-internal, for human spot-check):** none beyond the
disclosed finding above.

gate: clear 2026-09-02 — no MUST-FLAG trigger fired for the migration
itself (the one locked AC this task owns verified live with a real
positive result, no new dependency/interface change, no ADR touched,
the concurrent-write constraint was explicitly checked and respected
both times). The disclosed pre-existing console-encoding finding is
reported via `REVIEW-QUEUE.md` per this project's own established
disclosure pattern, not treated as a build-blocking defect of this
task's own scope.
