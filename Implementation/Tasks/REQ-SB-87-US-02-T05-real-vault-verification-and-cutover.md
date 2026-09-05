---
id: REQ-SB-87-US-02-T05
title: Real-vault retrofit-safety verification and live cron cutover
parent_story: REQ-SB-87-US-02
requirement_id: REQ-SB-87
type: backend
status: Done
gate: flagged
gate_reason: "Two real bugs found and fixed live before real-vault work proceeded (a Thread retrofit-duplication risk; a Unicode print crash), plus the pre-authorized orchestrator direction-forwarding fix — all three are scope-internal judgement calls for human spot-check, see Implementation Log and REVIEW-QUEUE.md"
phase: P1
depends_on: [REQ-SB-87-US-02-T04, REQ-SB-87-US-02-T06, REQ-SB-87-US-03-T03]
created: 2026-09-01
updated: 2026-09-02
---

# REQ-SB-87-US-02-T05 — Real-Vault Retrofit-Safety Verification and Live Cron Cutover

## Parent Story

- Story: [[REQ-SB-87-US-02]] — `../UserStories/REQ-SB-87-US-02-email-thread-capture-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

The one and only task that (a) proves the fully-migrated `email-thread-capture`
Skill is retrofit-safe against the real, already-populated vault, and (b)
performs the actual production cutover — pointing the live
`email-delta-capture` cron job's own `--vault-path` at the real vault — per
the operator's own already-locked rollout decision.

---

## Starting State → End State

**Before / Inputs:**
- `T01`-`T04` have all passed against the scratch vault / real ~100-email
  sample. The migrated scripts are the SAME code path regardless of
  target — no separate "test mode" branch; the cutover IS the
  `--vault-path` argument change, not a redeploy or a code branch (parent
  story's own Constraints).
- The real vault's own already-captured Threads, RawMessages, Person notes,
  and file companions predate this migration.

**After / Outputs:**
- A real, disclosed confirmation that the migrated scripts, run against the
  REAL vault, find and correctly top up every already-existing note — no
  duplicate created, no existing content lost or overwritten.
- The live `email-delta-capture` cron job's own `--vault-path` argument
  now points at the real vault (the actual cutover act).
- The migrated scripts are deployed to the real, active Hermes profile
  location(s) this Skill is actually running from (not only the
  `Hermes-Provisioning/` repo copies).

---

## Files to Modify

- None new — this task deploys the already-migrated files (from `T01`-`T03`)
  to the real, active Hermes profile location, and updates the live cron's
  own `--vault-path` argument (a scheduler/task-definition change, not a
  script-source edit).

---

## Constraints

- Inherits from parent story.
- **This task must NOT run until `T01`-`T04` and `T06` have all already
  passed against the scratch sample** — Scenario 6's own real-vault check
  happens AFTER the scratch-sample proving phase, immediately before
  cutover, never instead of it. `T06` (the real `direction`/recipient-type
  fields) added 2026-09-02 — its changes land in the SAME `ingest_email.py`
  file this task deploys/cuts over, so cutover must not run ahead of it.
- **Added 2026-09-02 (real cross-story sequencing, PRD point 8, both
  stories' own Dependencies sections):** this task must also NOT run until
  `REQ-SB-87-US-03-T03` (the task that wires the classify-or-skip relay call
  into `ingest_email.py` and individually, live-verifies that a real
  classification value is stamped onto a Thread's frontmatter) has passed —
  the real 100-message retrofit this task performs must write a real
  classification value into every retrofitted message's frontmatter, even
  where the ultimate decision is "keep everything," per the operator's own
  instruction. This is a genuine cross-sprint dependency edge
  (`SPRINT-083` → `SPRINT-084`), left to `/plan-sprints`'s own
  `depends_on_sprints` handling.
- Never run more than one capture job concurrently against the real vault
  during this verification.
- Deploy to the real, active Hermes profile location(s), per this
  project's own standing manual-deploy pattern.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-87-US-02-AC-06]` Run the fully-migrated `ingest_email.py`
   (and, as applicable, `rename_thread.py`/`capture_attachments.py`/
   `capture_file_link.py`/`link_person_to_thread.py`) against the REAL,
   live vault for a small, real, already-known set of Threads/messages
   (re-ingesting already-captured `message_id`s is safe, per Scenario 2's
   idempotency). Confirm every already-existing Thread/RawMessage/Person/
   File note is found and topped up correctly — no duplicate created, no
   existing content lost or overwritten. Spot-check at least one Thread
   that has an existing `## Related` entry, one with a file companion, and
   one whose directory is already renamed to `"<date> <subject>"`.
2. (Unlabeled, supporting) Confirm the deployed scripts at the real, active
   Hermes profile location match the fully-migrated repo copies exactly
   (byte-for-byte, or functionally — coder's disclosed choice).
3. `[REQ-SB-87-US-02-AC-05]` Re-confirm (one final time, against the REAL
   vault, not just the scratch sample) that `run_delta_capture.py`'s own
   external contract (arguments, JSON, exit code, watermark file) is
   unaffected.
4. **Cutover action:** update the live `email-delta-capture` cron job's own
   `--vault-path` argument to point at the real vault (if it does not
   already, e.g. if this Skill was previously being run manually against a
   scratch path during the proving phase). Confirm the next scheduled or
   manually-triggered run succeeds against the real, live vault.

**Automated tests:** `n/a — real-vault verification, by definition, is not
run against an isolated test fixture`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Real-vault retrofit-safety confirmed — no duplicate, no lost/
      overwritten content
- [x] Migrated scripts deployed to the real, active Hermes profile location
- [x] Live cron's own `--vault-path` points at the real vault (cutover
      complete)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any further code change — this task is verification + deployment +
  cutover only, building on `T01`-`T04`'s already-complete migration.

---

## Context / Notes

Operator's own real rollout decision (verbatim, `REQ-SB-87-US-02`'s own
Notes): *"Lets Build a small sample of 100 Emails to a new Pipeline we keep
tweaking it when done we change the OutputDirectory and move on."* This
task is that "change the OutputDirectory and move on" step.

**Added 2026-09-02 (decomposer pass, Scenario 8/9 + cross-story edge):**
this task's own cutover deploys `ingest_email.py` in whatever state it is
in AFTER `T06` (real `direction`/recipient-type fields) and after
`REQ-SB-87-US-03-T03` (the classify-or-skip relay + classification stamp,
a different story's own task, layered onto the SAME file) have both landed
— confirm before cutover that both are present in the deployed code, not
just that each individually passed its own scratch-vault checks in
isolation.

---

## Implementation Log

**2026-09-02, coder pass — real-vault verification, retrofit, deployment,
and live cron cutover, per the operator's explicit "Run the retrofit
now" authorization.**

**Pre-flight:** confirmed `T04`/`T06`/`REQ-SB-87-US-03-T03` all `Done`
directly (read each task file). Confirmed no other real capture/enrich
job was mid-run: `job4-summarize-tag-threads` was `enabled: false,
state: "completed"` (not mid-run); no `meeting-capture-recurring` job
exists in the real `cron/jobs.json` at all; no fresh `.fire-*.lock` for
`email-delta-capture` at session start. **Paused** the live
`email-delta-capture` cron job (`hermes cron pause afbc0d78d611`) for
the duration of deployment + real-vault verification, resumed only at
the very end (see Cutover below).

**1. Orchestrator `direction`-forwarding fix (pre-authorized).** Confirmed
still open by direct read (not assumed): `run_full_capture.py` line
~239 and `run_delta_capture.py` line ~194 build `ingest_payload` from a
fixed, explicit key list that omitted `"direction"` — `recipients`
already flowed through unchanged (both forward the whole list object),
but `direction` did not. Added `"direction": e.get("direction") or "",`
to both, matching every other already-forwarded field's own shape.
Compiled clean (`py -m py_compile`).

**2. Real, live retrofit-duplication bug found and fixed BEFORE any
real-vault write (scope-internal judgement call, disclosed).** Before
touching the real vault, statically verified (via a direct, isolated
`vault_manager.find_by_id`/`_find_by_title` check against a real
scratch copy of a real pre-existing Thread) whether the migrated
`ingest_email.py` would actually recognize an already-existing,
pre-migration Thread. It would NOT: `find_by_id` requires a real `id`
frontmatter field, which `vault_lib.py`'s old implementation never
wrote; `thread/Template.json`'s own `on_existing_title: "always_new"`
means `create()`'s fallback title-lookup path never even runs for this
template. Left unfixed, retrofitting the real vault would have created
a genuine DUPLICATE Thread for every pre-existing conversation
touched — the exact failure this task's own `AC-06` exists to catch.
Fixed in `ingest_email.py` (the only file this required): on a
`find_by_id` miss, fall back to the already-imported, unchanged
`vault_lib.resolve_thread_directory(vault_path, conversation_id)`
(the SAME hand-written lookup `update_thread_last_message_at` already
relies on, correctly scoped to Thread root notes only) — if found,
backfill `id=conversation_id` via `vault_manager.update()` and treat it
as already-existing (no classify-or-skip relay call), mirroring
`REQ-SB-87-US-04-T01`'s own already-established "mint-and-backfill on
first touch" pattern for the identical problem. Verified live on a
throwaway scratch copy of a real Thread (never the live vault) across
three cases: (a) re-ingesting an already-captured message on the legacy
Thread — `thread_created: false, message_created: false`, `id`
correctly backfilled, zero duplicate directory; (b) a genuinely new
top-up message on the same legacy Thread — `thread_created: false,
message_created: true`, no relay call made; (c) a genuinely new
conversation with no legacy Thread at all — unaffected, still goes
through classify-or-skip + `create()` exactly as before (`classification:
"customer"` stamped correctly). See `MEMORY.md`.

**3. Deployment — migrated scripts to every real, active Hermes profile
location.** Deployed `ingest_email.py`, `rename_thread.py`,
`capture_attachments.py`, `capture_file_link.py`,
`link_person_to_thread.py`, `outlook_lib.py`, `list_recent_emails.py`,
`run_full_capture.py`, `run_delta_capture.py`, and a fresh
`vault_manager.py` copy (canonical `Hermes-Provisioning/shared/
vault_manager.py`, already byte-identical to this Skill's own repo
copy) to: (a) the ONE real, active location the live
`email-delta-capture` cron job's own `SKILL.md`-documented absolute
path actually calls (`C:\Users\<operator>\AppData\Local\hermes\
skills\vault-rebuild\email-thread-capture\scripts\` — confirmed still
on the OLD, pre-migration code, `vault_lib.py`-only, no
`vault_manager.py`, before this deploy); (b) all 26 real, active
per-profile deployed copies of this same Skill (`%LOCALAPPDATA%\hermes\
profiles\<profile>\skills\vault-rebuild\email-thread-capture\scripts\`,
none under a `_disabled-skills*` folder), for consistency with this
project's own established "resync every real deployed copy, not just
one" discipline (`vault_manager.py`'s own 82-copy resync precedent,
2026-09-01). **`vault_lib.py` deliberately NOT redeployed** — confirmed
via `git log` it was never touched by any `T01`-`T06` task; its own
repo-vs-deployed diff is a pre-existing line-ending-only artifact
(confirmed via a CRLF-normalized content comparison, byte-identical
otherwise), matching `T04`'s own already-documented finding for the
orchestrator files. All 27 locations SHA-256-confirmed byte-identical
to the migrated repo source after deploy; `py -m py_compile` clean at
the production location.

**4. Real, live Unicode print-crash bug found and fixed live, during
the retrofit itself (scope-internal judgement call, disclosed).**
2 of the real 100 retrofitted messages (subjects containing 🚀,
U+1F680) crashed `ingest_email.py`'s own `main()` with
`UnicodeEncodeError` on its FINAL `print(json.dumps(result, ...))` —
the SAME class of bug `list_recent_emails.py` already fixed for itself
on 2026-08-24 (its own module docstring), never applied to
`ingest_email.py`. The underlying vault write had already succeeded by
the time of the crash (confirmed: re-running both afterward returned
`message_created: false`, i.e. already captured) — no data was lost,
but the script exited non-zero with no JSON, which a real orchestrator
would silently log-and-continue on. Fixed identically to
`list_recent_emails.py`'s own established pattern:
`sys.stdout.reconfigure(encoding="utf-8")` at the top of `main()` (plus
the `import sys` this needed). Verified live on a scratch vault with an
engineered emoji-subject payload (no crash); re-deployed the fixed file
to all 27 real active locations (SHA-256-reconfirmed); re-ran the 2
originally-failed real messages directly against the real vault — both
now return `returncode: 0`, `message_created: false` (correctly found
already-captured). See `MEMORY.md`.

**`[REQ-SB-87-US-02-AC-06]` Real-vault retrofit-safety — PASS.**
Snapshotted two real, already-known Threads before touching them:
**"2026-07-16 You now have Audio Conferencing for Microsoft Teams..."**
(a real `## Related` entry populated, no file companion) and
**"2026-07-27 Masdar Data"** (4 real file companions under `files/`,
already renamed to `"<date> <subject>"` form — both Threads also
satisfy the "already renamed" spot-check). Re-ingested each one's own
already-captured message (same real `conversation_id`/`message_id`)
via the newly-DEPLOYED, migrated `ingest_email.py` directly against the
REAL, live vault: both returned `thread_created: false, message_created:
false`. `diff` before/after on both Thread concept notes: the ONLY
change on either was the additive `id: "<conversation_id>"` backfill
line — `## Summary`/`## Personal Notes`/`## Actions`/`## Related`/
`## Files`, tags, `last_message_at`, `last_summarized_at`, `thread_name`
all byte-identical; `messages/`/`files/` subtrees on both Threads
showed zero diff (recursive `diff -rq`). No duplicate directory
created.

**Real ~100-message retrofit (last 100 real Inbox+Sent items, pulled
via the deployed `list_recent_emails.py --limit 100`, 88 received/12
sent):** ran the deployed, migrated `ingest_email.py` directly against
the REAL vault for all 100, in order (matching the orchestrators' own
per-email dispatch shape), forwarding the same fields the fixed
orchestrators now forward. Result: **94 already-existing conversations**
(topped up with ZERO classify-or-skip relay calls, ZERO Thread
duplication — confirmed both by each individual response
`thread_created: false` and by the real vault's own Thread-directory
count growing by EXACTLY 5, not 94+5); **6 genuinely-new conversations**
(never previously captured, confirmed via a direct `find_by_id`/
`resolve_thread_directory` check performed BEFORE each `ingest_email`
call) — **5 captured with a real, valid classification value**
(`customer`/`partner`/`internal`, none fabricated/`null`) and **1
correctly skipped as noise** (a ServiceNow "Requested Item...has been
updated" automated ticket-status notification, zero vault trace,
confirmed via `find_by_id` still returning `None` afterward); **0 Sent
items were skipped as noise** (the Sent-guard from `REQ-SB-87-US-03-T03`
held for all 12 real Sent items in the sample, all of which were
already-existing conversations in this particular sample). Real
Thread-directory count: 251 → 256 (+5, exactly matching the 5
genuinely-new non-noise captures); real total `.md` count: 2213 → 2236
(+23 = 5 new Thread notes + 14 new RawMessage notes [messages_created
aggregated across the batch] + 4 new Person notes for previously-unseen
participants — all expected, correct side effects of genuine new
content, not an anomaly). Two items (idx 29, 65) hit the Unicode
print-crash bug (fixed above) on first pass; confirmed via re-run that
their underlying vault write had already succeeded on the FIRST pass
(idempotent re-run found them already captured) — zero data actually
lost, only a reporting-layer failure, now fixed for future runs too.

**Note on already-migrated-looking real data found mid-session:** one
Thread ("2026-09-02 Data Driven Process", real `id`/renamed shape)
was found already present in the real vault, created earlier the same
day (before this task's own deployment) — traced to a REAL, regular
`email-delta-capture` cron run at 12:07 local time (confirmed via its
own real per-run output file, `cron\output\afbc0d78d611\
2026-09-02_12-07-13.md`). Not investigated further (out of this task's
own scope to root-cause a prior session's own real cron activity); it
did not affect this task's own before/after baselines (the 251-Thread
count used as this task's own baseline was taken AFTER that run, at
the start of THIS task's own real-vault work).

**`[REQ-SB-87-US-02-AC-05]` Re-confirmed against the REAL vault — PASS.**
Ran the deployed, migrated `run_delta_capture.py` directly against the
real vault: `exit 0`, real JSON summary in the unchanged shape (now
including the `skipped_as_noise` field per `REQ-SB-87-US-03-T04`),
watermark correctly unchanged (`total_new_emails: 0` — the retrofit
above had already captured everything up to the watermark).

**Cutover — deployment + live cron trigger.** Per the same real,
already-documented Constraint this migration's own sibling task
established (`REQ-SB-87-US-04-T04`, 2026-09-01 `MEMORY.md` entry):
`email-delta-capture`'s own real cron job definition
(`cron\jobs.json`, `afbc0d78d611`) has NO separate `--vault-path`
field — the real vault path (`<OPERATOR_VAULT_OLD>`) is
embedded directly in the job's own prompt text and has been since the
job was created; there was no literal argument to edit. The real
cutover act is therefore the CODE deployment above. Resumed the
paused job (`hermes cron resume afbc0d78d611`) and manually triggered a
REAL agentic run (`hermes cron run afbc0d78d611`, not just a direct
script call) — the strongest available confirmation, mirroring
`US-04-T04`'s own cutover check: the real Hermes agent read `SKILL.md`
and called the exact, newly-deployed `run_delta_capture.py` at its own
documented absolute path. Confirmed via the job's own real per-run
output file (`cron\output\afbc0d78d611\2026-09-02_13-50-51.md`):
`{"status": "complete", ..., "skipped_as_noise": 0, ...}`, real
`last_status: "ok"` in `jobs.json` afterward. The live cron job now
runs the fully-migrated, retrofit-confirmed code on its normal 30-minute
schedule.

**Scope-internal judgement calls (assumptions), logged for human
spot-check per Pipeline.md hard rule 5:**
1. Fixed 2 real bugs found live during required verification
   (retrofit-duplication risk; Unicode print crash) directly within
   `ingest_email.py`, beyond this task's own literal `## Files to
   Modify` ("None new"), rather than blocking the task or silently
   proceeding — both are narrow, mechanical, fully-precedented fixes
   (the SAME patterns already established by `REQ-SB-87-US-04-T01` and
   `list_recent_emails.py` respectively), disclosed in full above and in
   `MEMORY.md`.
2. Deployed to all 26 real per-profile copies of this Skill, not just
   the one production/cron-facing location — a disclosed judgement call
   extending the task's own "location(s)" wording, matching this
   project's own established multi-copy-resync discipline.
3. Carried forward, unresolved by this task (not this task's own job to
   resolve): the pre-existing disclosed scope-internal judgement calls
   from `T01`/`T02`/`T03` (RawMessage filename-convention divergence;
   two `rename_thread.py` judgement calls; the `link_person_to_thread.py`
   section-name bug fix) and `T06`'s own SOUL.md wording mismatch — all
   already in `REVIEW-QUEUE.md`, all independently confirmed non-blocking
   for this task's own real-vault work.

No `ESCALATIONS.md` entry required — both real bugs found were resolved
directly within already-open file scope using already-established,
precedented patterns, not new dependencies/shared-interface changes/ADR
deviations/unanticipated files. `gate: flagged` for the three
scope-internal judgement calls above — see the new `REVIEW-QUEUE.md`
entry.

`MEMORY.md`: 2 new Constraint entries added (the retrofit-duplication
fix; the Unicode print-crash fix). `CHANGELOG.md`: entry appended.

**Task marked `Done`** — both locked ACs (`AC-05`, `AC-06`) verified
live with a real, positive result against the REAL, live vault; the
deployment + cutover confirmed real and complete. Story
`REQ-SB-87-US-02` moves `In Progress → Done` (all 6 tasks `Done`, all 9
locked ACs verified). `SPRINT-083` moves `In Progress → Done` (both its
stories, `REQ-SB-87-US-02` and `REQ-SB-87-US-04`, now `Done`) — a
retrospective is drafted below, `gate: flagged` for human harvest into
`Implementation/Learnings.md`. `BACKLOG.md`'s `REQ-SB-87` row and Sprint
Status table updated.
