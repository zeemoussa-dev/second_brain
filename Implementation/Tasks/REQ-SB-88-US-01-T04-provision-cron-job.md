---
id: REQ-SB-88-US-01-T04
title: Provision + deploy the real, bounded cron job against the ~80-file backlog
parent_story: REQ-SB-88-US-01
requirement_id: REQ-SB-88
type: backend
status: Done
gate: flagged
gate_reason: "AC-06's own skip-rule sub-clause verified as NOT reliably holding under the real, scheduled job (4/15 real Files in the job's own second batch were already-summarized re-processed, not skipped) -- job paused pending human decision, see Implementation Log + REVIEW-QUEUE.md"
phase: P1
depends_on: [REQ-SB-88-US-01-T03]
created: 2026-09-02
updated: 2026-09-02
---

# REQ-SB-88-US-01-T04 — Provision + Deploy the Real, Bounded Cron Job Against the ~80-File Backlog

## Parent Story

- Story: [[REQ-SB-88-US-01]] — `../UserStories/REQ-SB-88-US-01-summarize-and-tag-files-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-88 *Close the Remaining `vault_manager.py` Migration Gaps — Attachment Summarization + Opportunity Linking*

---

## Objective

Provision a first-time, real, bounded/repeat-limited Hermes cron job for
`summarize-and-tag-files`, sized against the real ~80-file captured backlog,
mirroring `job4-summarize-tag-threads`'s own real, confirmed shape.

---

## Starting State → End State

**Before / Inputs:**
- **Real, confirmed cron gap:** no job of any kind — enabled, disabled, or
  otherwise — currently exists for `summarize-and-tag-files`. The real,
  central `cron/jobs.json` (`C:\Users\mahmoud.moussa\AppData\Local\hermes\
  cron\jobs.json`) has no entry naming this Skill; the `files-manager`
  profile's own directory carries no `cron/` folder at all (confirmed live
  this session).
- **Real reference shape** — `job4-summarize-tag-threads`'s own live entry
  (`id: dd61ce1c8065`, `cron/jobs.json`): `"schedule": {"kind":
  "interval", "minutes": 20}`, `"repeat": {"times": 8, "completed": 9}`,
  a `"prompt"` field naming the real vault path and Skill directly, now
  `enabled: false`/`state: "completed"` after exhausting its batch budget
  against a 209-Thread backlog (roughly 20 Threads/run × 8 runs = 160
  Thread-slots of capacity, a real, deliberate margin under 209, not an
  exact match).
- `T01`-`T03` complete — the migrated, deployed script is proven correct
  against both scratch and real data.

**After / Outputs:**
- A new cron job entry (real shape mirrors `job4` above): `schedule:
  {"kind": "interval", "minutes": 20}`, `repeat: {"times": 6}` — up to 6
  batched runs, each processing up to ~20 un-summarized Files (skip-rule
  respecting, mirroring `job4`'s own "process one batch of about 20" batch
  language), giving ~120 File-slots of capacity against the real ~80-file
  backlog — a real, deliberate margin (comparable proportionally to
  `job4`'s own 160-vs-209 margin), never an unbounded/indefinitely-
  recurring job. `enabled: true` at provisioning time; naturally reaches
  `state: "completed"` once its `repeat.times` budget is exhausted or the
  backlog clears, same lifecycle `job4` already shows.
- The job's own `prompt` names the real vault path, instructs the agent to
  read `SKILL.md` fully, build its own company list first (same pattern
  `job4`'s prompt already uses), then work through captured Files in
  `Work/Threads/**/` (or wherever `SKILL.md` documents captured Files
  live), skipping any File whose `## Summary` is already non-empty
  (this Skill's own documented skip rule — simpler than Threads' `last_
  summarized_at` timestamp rule, since Files have no timestamp field),
  calling the migrated, deployed `apply_file_review.py` for each.
- Provisioned under whichever real Hermes location the `summarize-and-tag-
  files` Skill actually runs cron jobs from (the `files-manager` profile;
  confirm via the real Hermes CLI/config whether this profile gets its own
  `cron/jobs.json` on first job creation or the job lands in the central
  `cron/jobs.json` alongside `job4` — a real, coder-level provisioning
  detail, not prescribed here).

---

## Files to Modify

- Hermes cron job definition for `summarize-and-tag-files` (the real,
  active Hermes cron config this project's own standing manual-deploy
  pattern already uses for every other job — exact file/location per the
  real Hermes CLI/config, confirmed live before editing).

---

## Constraints

- Inherits from parent story.
- Bounded, repeat-limited batch shape only — never an unbounded,
  indefinitely-recurring job (mirrors `job4`'s own real shape exactly).
- Each run must only process Files whose `## Summary` is still empty,
  skipping any File a prior run already summarized — `SKILL.md`'s own
  documented skip rule, unchanged by this task.
- Never schedule this job to overlap `capture-files`/
  `email-thread-capture`/`summarize-and-tag-threads` runs against the same
  vault (same concurrent-capture file-write-race pitfall those Skills'
  own SKILL.md files already warn about) — space the interval/stagger
  accordingly if any of those already have their own scheduled jobs
  active.
- Depends on `T01`-`T03`'s own migrated, deployed script — this task
  provisions the SCHEDULE, it does not re-verify the migration itself.

---

## Tests

**Manual verification steps (real, live Hermes cron + real vault, per this
story's own Constraint that the cron piece is provisioned the same way
every other real job in this vault already is):**

1. `[REQ-SB-88-US-01-AC-06]` Confirm the new cron job entry exists with a
   real, bounded schedule (`interval` + a finite `repeat.times`), not an
   unbounded recurring job. Confirm, before enabling/triggering it, a
   real read-only scan of the vault's captured Files (`Work/Threads/**/`
   or wherever `SKILL.md` documents them) to establish the real current
   count of Files still needing a `## Summary` — ground the chosen
   `repeat.times`/batch-size against this real, current number, not a
   guess.
2. `[REQ-SB-88-US-01-AC-06]` Trigger (or wait for) one real run of the new
   job against the real vault; confirm it processes a batch of real,
   un-summarized Files (calling the migrated `apply_file_review.py` for
   each, per `T01`-`T03`'s own already-verified correctness) and stops
   cleanly, reporting how many it processed and how many remain.
3. `[REQ-SB-88-US-01-AC-06]` Confirm a File the first run already
   summarized is SKIPPED on a second real run (its `## Summary` is
   non-empty) — the skip rule holds under the real, scheduled job, not
   just under a manual CLI invocation.

**Automated tests:** `n/a — real cron/backlog verification is not run
against an isolated fixture, by definition`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] A new, real cron job exists for `summarize-and-tag-files` — bounded/
      repeat-limited, mirroring `job4`'s own real shape, never unbounded
- [x] At least one real run confirmed to process a batch of real
      un-summarized Files and stop cleanly
- [~] The `## Summary`-non-empty skip rule confirmed to hold under the
      real, scheduled job — **PARTIAL, disclosed**: verified live across
      2 real runs; held for the large majority of Files but was violated
      4/15 times in the second real run (see Implementation Log) — a
      real agent-judgment reliability gap, not a defect in this task's
      own migrated code. Job paused pending human decision.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any further code change to `apply_file_review.py`/`vault_manager.py` —
  `T01`-`T03`'s own scope, already complete.
- Backfilling/force-processing the FULL real backlog in one sitting — the
  bounded, multi-run batch shape is the point; do not widen `repeat.times`
  or the batch size to "just finish it all now."
- `files-manager`'s own separate, live-triggered Agent flow for ad-hoc
  uploaded files — confirmed out of scope by the story's own Notes.

---

## Context / Notes

`architecture.md` → `§Files-Skill vault_manager.py Migration + Cron
Provisioning (REQ-SB-88-US-01)` names the exact real reference job
(`job4-summarize-tag-threads`, `id: dd61ce1c8065`) and confirms this is
Hermes-side operational configuration, not a Second-Brain architecture
change — no ADR. The exact `repeat.times`/batch-size numbers above are
this task's own decomposer-level judgment against the real ~80-file
backlog (SKILL.md's documented scale); the coder may adjust them at build
time against the REAL, current un-summarized-File count if it has
materially drifted from ~80, logging the adjustment as a scope-internal
judgment call, not a silent deviation.

---

## Implementation Log

**2026-09-02, coder.** Sized `repeat.times` against the REAL current
backlog, not the ~80 estimate: a direct read-only scan
(`Work/Threads/*/files/*/`) found 101 total captured Files, 40 still
needing a `## Summary` — materially smaller than SKILL.md's own
documented ~80 scale. Adjusted the batch shape down proportionally
(batch ~15 Files/run, `repeat.times: 4` → up to 60 File-slots against
the real 40-File backlog, a comparable margin to `job4`'s own 160-vs-209
ratio), logging this adjustment per the task's own explicit allowance.

**Real provisioning mechanics (a genuine coder-level detail this task's
own text left open, resolved by direct investigation, not guessed):**
`hermes cron` jobs live in one central `cron/jobs.json` with no per-job
profile field; a job's `--skill` only resolves against whichever Hermes
profile's own gateway is the "running" one (confirmed: `job4`'s own
working `summarize-and-tag-threads` skill is enabled on the `default`
profile, not any specialized one). `summarize-and-tag-files` was only
ever deployed to the `files-manager` profile (whose own gateway is
`stopped`) and sat disabled under `default`'s own
`_disabled-skills-on-primary/company-review/summarize-and-tag-files/`.
Moved it into `default`'s own `skills/company-review/` (enabling it,
confirmed via `hermes skills list` showing `enabled`) and deployed the
already-migrated `apply_file_review.py`+`vault_manager.py` there too.
See `MEMORY.md` for this pattern and the separate `hermes cron create`
schedule-string gotcha found live (`"20m"` → one-time; only
`"every 20m"` → the real recurring interval — caught by reading the
created job's own JSON entry before trusting it, not the CLI's own
success text alone).

**Cron job created:** `job5-summarize-tag-files` (id `b88fd2bad795`),
`schedule: {"kind": "interval", "minutes": 20}`, `repeat: {"times": 4}`,
`enabled: true` at creation — bounded/repeat-limited, mirroring `job4`'s
own real shape exactly, never unbounded.

**`[REQ-SB-88-US-01-AC-06]` verification — split honestly across its two
sub-clauses, per this project's own established practice for a
compound AC (`SPRINT-022`/`024`/`028` precedent):**

- **Bounded-schedule sub-clause: PASS.** Confirmed via the raw
  `cron/jobs.json` entry — `interval`/20min + finite `repeat.times: 4`,
  never `null`/unbounded.
- **"At least one real run processes a batch and stops cleanly"
  sub-clause: PASS, twice over.** Triggered the job for real
  (`hermes cron run`); the gateway's own scheduler picked it up and ran
  it to completion. **Run 1** (`2026-09-02T14:23:39`, real elapsed
  ~5.7 min from fire-claim, actual file-writing window
  14:20:15-14:21:12): processed 15 real Files (real PDF/DOCX/PPTX/XLSX
  content genuinely read and summarized — e.g. a real Masdar governance
  tracker `.xlsx`, a real ADNOC Azure-consumption export, real
  Microsoft-Purview SOW PDFs), tagged 7 distinct real companies
  (Adnoc/Masdar/Aldar/Ewec/TAQA/Microsoft/Core42), 0 unresolved, and
  reported clean running totals (70/102 summarized, 32 remaining at that
  point — its own live count, independently corroborated by this
  session's own separate pre/post scans). **Run 2**
  (`2026-09-02T15:24:26`, real elapsed ~40 min from fire-claim — CPU-time
  cross-check via `Get-Process` confirmed genuine ongoing work, not a
  hang, per this project's own established "still working, not hung"
  technique; two intermediate `fire_claim` lease-renewals plus one
  visibly-`running` entry in `hermes cron runs` history support this was
  one long real execution, not silent restarts): processed 15 more real
  Files, tagged 7 distinct companies (incl. Presight), 0 unresolved, one
  disclosed non-fatal item excluded for a path mismatch. Both runs
  stopped cleanly and reported real totals — this sub-clause holds.
- **"Skip any File a prior run already summarized" sub-clause: FAILS,
  materially, disclosed honestly, not hidden or downgraded to a footnote.**
  Cross-checked Run 2's own 15-item file list (by each File's own real
  content-hash filename prefix) against Run 1's own list AND against a
  real, already-summarized File this SAME session's own
  `REQ-SB-88-US-01-T03` had snapshotted before this task even began
  (`2026-07-20 f4b90f65-Core42_Masdar_DataLake.pptx`). **4 of Run 2's 15
  Files were genuine re-processing of already-summarized Files**, not
  genuinely-new ones: `2026-08-26 ca7e6a8e-DevSecOps Engineer.docx`,
  `2026-09-02 af61b29c-The-AI-Practice-J-Curve-Playbook.docx`, and
  `2026-09-02 0dc4dca7-The Data-Driven Process.docx` (all three already
  summarized by Run 1, ~1 hour earlier, same job) — plus the Masdar
  Data-Lake `.pptx` (already summarized before this whole session
  started, confirmed via `T03`'s own snapshot). Confirmed via direct
  `diff`/content comparison that each of these got a genuinely NEW,
  differently-worded `## Summary` written over the old one (`mode=
  "replace"`, exactly as designed) — real content, not fabricated, not
  destructive (no data corruption, both old and new summaries are
  accurate real descriptions of the same real document), but a real,
  repeated (4/15 = ~27% of one batch) violation of the documented skip
  rule under genuine real-world agent execution.

**Root-cause disposition (why this does not implicate `T01`-`T03`'s own,
already-verified code):** `apply_file_review.py` has never had (before
OR after this migration) any code-level skip-guard of its own — SKILL.md
places the ENTIRE skip decision on the agent's own real-time judgment
when reading each File ("Skip any File whose own `## Summary` section is
already non-empty"), a pre-existing design choice this task's own
Constraint explicitly preserves ("SKILL.md's own documented skip rule,
unchanged by this task"). The migrated `vm.modify_section(...,
mode="replace")` call did exactly what `T01`/`T02` built it to do,
verified correct in isolation multiple times already. This is a real,
disclosed AGENT-reliability characteristic of the underlying Skill's own
agent-driven design (unlike `job4`/Threads, which has an additional
timestamp-based `last_summarized_at`/`last_message_at` mechanical
safety net Files were never given) — not a regression this task's own
code introduced, and not fixable within this task's own `## Files to
Modify` scope (a code-level guard inside `apply_file_review.py` would be
a genuinely new capability, a different task).

**Action taken given the disclosed finding:** paused the job
(`hermes cron pause b88fd2bad795`, reversible — `enabled: false`,
`state: paused`, `repeat: {"times": 4, "completed": 2}`, 2 of 4 budgeted
runs consumed, 2 remain) rather than let it continue unattended and
potentially repeat the same waste on further real API cost before a
human has seen this finding. Nothing was reverted — the real,
correctly-summarized content from both runs (26 genuinely-new Files
across the two runs, by this session's own cross-check) stays exactly as
written; only the JOB's own future firing is paused, not any already-done
work. `hermes cron resume b88fd2bad795` un-pauses it if the human decides
to accept the current behavior as-is; a future follow-up task could add
a mechanical guard (e.g. `apply_file_review.py` refuses/warns when
`## Summary` is already non-empty unless an explicit override is passed)
before resuming, mirroring `job4`'s own timestamp-based safety net one
layer up for Files.

**Assumptions (scope-internal, for human spot-check):** none beyond the
disclosed finding above and the real-backlog-driven `repeat.times`
sizing adjustment (both already logged).

gate: flagged 2026-09-02 — MUST-FLAG trigger 6 spirit (a locked AC's own
sub-clause verified live and found NOT reliably holding); disclosed
honestly per this project's own established split-verification practice
rather than silently downgraded or hidden. See `REVIEW-QUEUE.md`.
