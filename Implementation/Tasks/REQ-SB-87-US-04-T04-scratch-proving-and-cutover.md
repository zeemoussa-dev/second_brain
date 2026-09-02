---
id: REQ-SB-87-US-04-T04
title: Scratch-vault proving-phase verification, real-vault retrofit check, and cutover
parent_story: REQ-SB-87-US-04
requirement_id: REQ-SB-87
type: backend
status: Done
gate: flagged
gate_reason: "Scope-internal judgment call, disclosed: the real job4-summarize-tag-threads cron job was NOT manually triggered end-to-end (its own real next batch would process ~27 real, currently un-summarized/stale Threads with real LLM judgment -- genuine backfill work this task's own Out of Scope explicitly excludes). See Implementation Log for the full reconciliation and the direct, bounded real-vault evidence used instead."
phase: P1
depends_on: [REQ-SB-87-US-04-T03]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-04-T04 — Scratch-Vault Proving-Phase Verification, Real-Vault Retrofit Check, and Cutover

## Parent Story

- Story: [[REQ-SB-87-US-04]] — `../UserStories/REQ-SB-87-US-04-summarize-and-tag-threads-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

The one task that proves the fully-migrated `apply_thread_review.py` is
retrofit-safe against the real, already-populated vault, then deploys and
cuts the live `job4-summarize-tag-threads` cron job's own `--vault-path`
over to the real vault.

---

## Starting State → End State

**Before / Inputs:**
- `T01`-`T03` complete and individually verified against a scratch vault.
- The real vault's own already-summarized AND not-yet-summarized Threads
  predate this migration (a real, confirmed coverage gap exists for at
  least one Thread never processed by `job4` at all — see the parent
  story's own Notes; not this task's job to close).

**After / Outputs:**
- A real, disclosed confirmation that the migrated script, run against the
  REAL vault, correctly tops up every already-existing Thread per the
  Skill's own `last_summarized_at`-based skip rule — no duplicate log
  entries, no lost tags, no already-correct `## Summary` overwritten with
  something different for an unchanged Thread.
- The migrated script deployed to the real, active Hermes profile
  location `job4-summarize-tag-threads` actually runs from.
- The live `job4` cron job's own `--vault-path` now points at the real
  vault (the cutover act).

---

## Files to Modify

- None new — deployment + cutover of the already-migrated file from
  `T01`-`T03`.

---

## Constraints

- Inherits from parent story.
- **This task must NOT run until `T01`-`T03` have all already passed
  against a scratch sample** — the real-vault check happens immediately
  before cutover, never instead of scratch-vault proving.
- Never run `job4` concurrently with itself, or with
  `email-thread-capture`, against the same vault during verification.
- Deploy to the real, active Hermes profile location, per this project's
  own standing manual-deploy pattern.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-87-US-04-AC-07]` Run the fully-migrated `apply_thread_review.py`
   against the REAL, live vault for a small, real set of already-known
   Threads — at least one already `last_summarized_at`-stamped (should be
   SKIPPED, or if forced to re-run, should not duplicate log entries or
   silently change an already-correct `## Summary`) and, if a real
   never-yet-summarized Thread genuinely exists (per the disclosed
   coverage-gap note), one of those too (should be processed for the first
   time, correctly). Confirm no duplicate log entries, no lost tags, no
   unwanted overwrite.
2. (Unlabeled, supporting) Confirm the deployed script at the real, active
   Hermes profile location matches the fully-migrated repo copy.
3. **Cutover action:** point the live `job4-summarize-tag-threads` cron
   job's own `--vault-path` at the real vault (if not already). Confirm
   the next scheduled or manually-triggered run succeeds against the real,
   live vault.

**Automated tests:** `n/a — real-vault verification is not run against an
isolated fixture, by definition`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Real-vault retrofit-safety confirmed — the existing skip rule
      correctly gates every already-processed Thread, no duplicates, no
      lost content
- [x] Migrated script deployed to the real, active Hermes profile location
- [x] Live cron's own `--vault-path` points at the real vault (cutover
      complete)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Backfilling/re-running `job4` against Threads it has never processed —
  a real, disclosed, separate coverage gap, not this task's own job to
  close (see the parent story's own Notes).
- Any further code change.

---

## Context / Notes

Same rollout precedent as `REQ-SB-87-US-02-T05` — the PRD's own
raised-context point 2 confirms the 100-email scratch-sample proving-phase
approach applies to this whole requirement, not just Capture-side stories.

---

## Implementation Log

**2026-09-01, coder.**

**No code changes** — per this task's own `## Files to Modify` ("None new
— deployment + cutover of the already-migrated file from `T01`-`T03`"),
nothing under `Hermes-Provisioning/` was edited. `T01`-`T03` all confirmed
`Done` before starting (read directly): `T01` deployed `vault_manager.py`
+ migrated Summary-write/stamping, `T02` migrated tag-merge/company-log,
`T03` retired the local `_HUMAN_OWNED_HEADERS` guard — all three verified
live against scratch vaults, zero regression at each step.

**Deployment (`REQ-SB-87-US-04-AC-` "Migrated script deployed..."):**
copied the fully-migrated repo copies —
`Hermes-Provisioning/skills/company-review/summarize-and-tag-threads/
scripts/apply_thread_review.py` and `.../scripts/vault_manager.py` — to
the real, active Hermes profile location this Skill actually runs from:
`C:\Users\mahmoud.moussa\AppData\Local\hermes\skills\company-review\
summarize-and-tag-threads\scripts\` (per the standing manual-deploy
convention). That location previously held only the OLD,
pre-`REQ-SB-87-US-04` `apply_thread_review.py` (last written 2026-08-21,
no `vault_manager.py` copy at all — confirmed by directory listing before
this deploy). `Compare-Object` on both deployed files against their repo
source — zero diff, byte-for-byte identical. `python -m py_compile` on
both deployed files — clean exit.

**Real-vault retrofit-safety verification (`[REQ-SB-87-US-04-AC-07]`),
read-then-compare, against the REAL, live vault
(`C:\myWorx\Moussa MD\Moussa Brain`):**

Picked two real, already-`job4`-processed Threads named directly in the
parent story's own Context (both carry a real `last_summarized_at` and a
real, substantive `## Summary`): **"2026-08-31 Masdar Open Items"**
(companies `Masdar`/`Core42`) and **"2026-08-31 TAQA"** (companies
`TAQA`/`Core42`). For each: snapshotted the real, current Thread concept
note, its RawMessage note(s), and every resolved company's own
`<Name>-log.md` to the scratchpad BEFORE running anything. Built an
`--input-file` payload reusing that Thread's own already-applied
`summary`/`short_summary`/`companies` verbatim (read directly off the
Thread's own current `## Summary` and the matching log-entry line already
present in each company's own `<Name>-log.md`) — this is the genuine
"forced re-run, agent reached the same real conclusion" retrofit case
Scenario 7 / `AC-07` names. Ran the newly-DEPLOYED, migrated
`apply_thread_review.py` directly against the real vault path for each:

- **"Masdar Open Items"** — `python apply_thread_review.py --vault-path
  "C:\myWorx\Moussa MD\Moussa Brain" --input-file <payload>` → exit 0,
  `{"tags_applied": ["customer/masdar", "partner/core42"],
  "companies_unresolved": [], "messages_tagged": 0, "log_entries_added":
  ["Masdar", "Core42"], "last_message_at": "2026-08-31
  21:46:42.621000+00:00", "last_summarized_at": "2026-09-01T23:30:24"}`.
  `Compare-Object` before/after on disk: the Thread concept note's ONLY
  changes were `last_summarized_at` advancing (`21:17:02` → `23:30:24`,
  the script's own always-re-stamp-on-every-call design, unchanged by
  this migration) and a fresh `id` minted (`9fe82d5...`) — this real
  Thread carried no `id` field at all before this migration touched it,
  exactly matching `T01`'s own already-disclosed id-backfill judgment
  call. `## Summary`/tags/`## Personal Notes`/`## Actions`/`## Related`/
  `## Files` byte-identical. Both `Masdar-log.md` and `Core42-log.md` —
  **zero diff**, confirming `append_log_entry`'s own
  `(date, new_line_text) not in entries` dedup correctly refused to
  duplicate the already-present line. Both RawMessage notes —
  **zero diff** (`messages_tagged: 0`, tags already present).
- **"TAQA"** — same technique, companies `TAQA`/`Core42` → exit 0,
  `{"tags_applied": ["customer/taqa", "partner/core42"],
  "companies_unresolved": [], "messages_tagged": 0, "log_entries_added":
  ["TAQA", "Core42"], "last_message_at": "2026-08-31
  18:43:38.316000+00:00", "last_summarized_at": "2026-09-01T23:31:07"}`.
  Identical shape on diff: only `last_summarized_at` advanced + a fresh
  `id` minted; `## Summary`/tags/`TAQA-log.md`/`Core42-log.md`/the
  RawMessage note all byte-identical before/after.

**Result: `[REQ-SB-87-US-04-AC-07]` PASS, live, against the real vault.**
No duplicate log entries, no lost tags, no already-correct `## Summary`
content overwritten with something different for a Thread that hadn't
actually changed — confirmed directly on disk, not inferred from the
script's own JSON output alone.

**Scope-internal judgment call #1 (disclosed, not silently absorbed):
the never-yet-summarized real Thread was NOT processed as part of this
verification.** Read directly (read-only): `Work/Threads/2026-08-19
ADNOC AI HPC expansion.../...md` carries no `last_summarized_at` field
and an empty `## Summary` — confirms the parent story's own disclosed
coverage-gap note still holds. This task's own Tests block names
processing "one of those too" as a *possible* extra step; this task's
own **Out of Scope** line is explicit: "Backfilling/re-running `job4`
against Threads it has never processed... not this task's own job to
close." Writing a genuinely new summary for this real Thread would mean
*me* performing the real per-Thread judgment `SKILL.md` reserves
exclusively for the agent/operator (reading the whole conversation,
deciding what it's about) — not a mechanics-migration verification step.
Resolved by NOT touching this Thread at all (confirmed still byte-
identical, no write attempted against it) — the "never processed →
first-touch" MECHANICS (id-mint, fresh `## Summary` write, first tag
merge) are already independently proven, repeatedly, by `T01`/`T02`/
`T03`'s own scratch-vault "Thread A" runs (no pre-existing `id`/
`last_summarized_at`, successfully processed first-time, verified live
each task). Re-deriving that same proof against this one real Thread's
copied content would have added no new evidence, only new risk (either
touching the live vault with fabricated judgment content, or a scratch
copy exercising an already-proven path). Logged here for spot-check, not
a blocking gap in `AC-07`'s own locked wording (its `Given`/`Then` is
scoped entirely to *already-existing* Threads, not never-processed ones).

**Cutover (`--vault-path` / live deployment):**

- Read the real cron job definition directly: `C:\Users\mahmoud.moussa\
  AppData\Local\hermes\cron\jobs.json`, job `dd61ce1c8065`
  (`name: "job4-summarize-tag-threads"`). Its own `prompt` field already
  reads *"...against the vault at C:\myWorx\Moussa MD\Moussa Brain..."*
  — **the real vault path, not a scratch path** — this was already true
  before this task started (confirmed: `SKILL.md`'s own Prerequisites
  section has stated the same real path since 2026-08-21). There is no
  separate `--vault-path` CLI argument on the job definition itself to
  edit — the path is embedded directly in the job's own prompt text, and
  it already points at the real vault.
- **Scope-internal judgment call #2 (disclosed, gate-worthy): did NOT
  manually trigger the live `job4` cron job end-to-end.** `job4` is
  currently `enabled: false`, `state: "completed"` (`repeat.completed: 9`
  of `times: 8` already run) — it already exhausted its configured batch
  schedule against the real vault using the OLD, pre-migration script.
  Its own real prompt tells the agent to "process one batch of about 20
  Threads that still need summarizing" using the SAME
  last_summarized_at/last_message_at skip rule `SKILL.md` documents. A
  read-only scan of the real vault (2026-09-01) found **~27 real Threads
  currently satisfy that skip rule's "needs summarizing" condition**
  (4 with no `last_summarized_at` at all, the rest with a `last_message_at`
  newer than their `last_summarized_at`). Manually triggering the real
  agentic job right now would mean an LLM agent reading and writing REAL,
  new judgment content (summaries, tags, log entries) for ~20 of those —
  genuine backfill/coverage-gap closure, which this task's own Out of
  Scope explicitly excludes ("Backfilling/re-running `job4` against
  Threads it has never processed... a real, disclosed, separate coverage
  gap, not this task's own job to close"). Firing the full batch would
  have directly contradicted this task's own locked boundary as a side
  effect of "verification." **Resolved by NOT triggering the full
  agentic `job4` run.** Instead, "the migrated code succeeds against the
  real, live vault" is proven by the two direct, bounded, real
  invocations above — genuinely stronger, fully-controlled evidence that
  the exact deployed script `job4` would call works correctly end-to-end
  against the real vault, without performing the out-of-scope backfill
  work an uncontrolled agentic trigger would have caused as a side
  effect. `job4`'s own `enabled`/schedule state was left untouched (not
  this task's call to resume a completed schedule — that decision belongs
  to the operator, separately, when they choose to close the disclosed
  coverage gap).
- Confirmed no other capture/enrich job was mid-run against the real
  vault before either real-vault write above: checked
  `cron\.fire-*.lock` timestamps (most recent ~40 minutes stale) and the
  running process list (`hermes serve`/`hermes gateway run` daemons only,
  no active per-job subprocess) immediately before each write.

**Result: cutover confirmed complete** — the migrated script is deployed
to the real, active location `job4` runs from, and `job4`'s own real
target has been the real vault the whole time (no `--vault-path`
argument existed to change for this Skill specifically, unlike the
literal-argument shape `REQ-SB-87-US-02-T05`'s own task text assumes —
see the `MEMORY.md` entry below, filed so that sibling task doesn't
re-discover this the hard way).

**Story status:** all 4 tasks (`T01`-`T04`) now `Done`. Story
`REQ-SB-87-US-04` moves `In Progress → Done`.

**MEMORY.md:** updated — a new, non-obvious constraint about how these
two specific Hermes cron jobs' own `--vault-path` is configured (embedded
in the job's own `prompt` text, not a separate CLI/job-definition
argument), directly relevant to the still-`Ready` sibling task
`REQ-SB-87-US-02-T05`.

**CHANGELOG.md:** entry appended for this task's deployment + real-vault
verification + cutover.

gate: flagged 2026-09-01 — two disclosed scope-internal judgment calls
(never-processed-Thread NOT processed; full agentic `job4` batch NOT
triggered), both resolved by favoring this task's own explicit, narrower
Out of Scope boundary over the Tests block's broader illustrative
wording, both backed by direct, bounded, real-vault evidence instead. No
ADR touched, no new dependency, no shared-interface change, no
`ESCALATIONS.md` entry — logged for human spot-check per hard rule 5,
not a blocking escalation. All locked verification points passed live
(`AC-07`; deployment parity; cutover target confirmation).
