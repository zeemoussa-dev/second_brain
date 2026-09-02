---
id: REQ-SB-87-US-02-T04
title: Verify run_full_capture.py / run_delta_capture.py orchestration contract is unaffected
parent_story: REQ-SB-87-US-02
requirement_id: REQ-SB-87
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-02-T03]
created: 2026-09-01
updated: 2026-09-02
---

# REQ-SB-87-US-02-T04 — Verify run_full_capture.py / run_delta_capture.py Orchestration Contract Is Unaffected

## Parent Story

- Story: [[REQ-SB-87-US-02]] — `../UserStories/REQ-SB-87-US-02-email-thread-capture-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Confirm, with real evidence, that `run_full_capture.py`/
`run_delta_capture.py`'s own external CLI contract (arguments, printed
JSON, exit codes, watermark state file) is completely unaffected by
`T01`-`T03`'s migration of the five per-email scripts they orchestrate —
this task makes NO code changes of its own.

---

## Starting State → End State

**Before / Inputs:**
- `run_full_capture.py`/`run_delta_capture.py` invoke `ingest_email.py`,
  `rename_thread.py`, `capture_attachments.py`, `capture_file_link.py`,
  `link_person_to_thread.py` as separate subprocess calls, parsing each
  one's own printed JSON — untouched by `T01`-`T03`, which only edited the
  INTERNALS of those five scripts, never their own CLI arg/stdout/exit-code
  shape.

**After / Outputs:**
- A real, disclosed confirmation that both orchestrators still run
  end-to-end against the migrated per-email scripts, with the exact same
  external contract as before this migration — no code change required or
  made.

---

## Files to Modify

- None — verification only. `run_full_capture.py`/`run_delta_capture.py`'s
  own orchestration logic (paging, watermark, subprocess dispatch) is
  explicitly NOT part of this migration's own `## Files to Modify`, per the
  parent story's own Constraints.

---

## Constraints

- Inherits from parent story.
- Zero code edits in this task.
- Verify against the SAME scratch vault/100-email sample `T01`-`T03` used —
  never the live vault for this task.
- Never run more than one capture job concurrently against the same vault
  during verification.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`):**
1. `[REQ-SB-87-US-02-AC-05]` Run `run_full_capture.py` end-to-end against
   the scratch vault's own real ~100-email sample (or a representative
   subset); confirm it still accepts the same real CLI arguments, still
   prints the same real JSON summary shape, still exits 0 on success, and
   the watermark state file is written/updated in its same real location
   and shape.
2. `[REQ-SB-87-US-02-AC-05]` Run `run_delta_capture.py` once more (a
   second, incremental pass) against the same scratch vault; confirm its
   own watermark-based delta logic still correctly picks up only the
   genuinely new/changed items since the prior run, with the same real
   external contract.
3. (Unlabeled, supporting) Confirm neither orchestrator's own source file
   required any edit to make steps 1-2 pass — a real, observed zero-diff
   confirmation, not just an assumption.

**Automated tests:** `n/a — orchestration verified via real scratch-vault
CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `run_full_capture.py` external contract confirmed unchanged
- [x] `run_delta_capture.py` external contract confirmed unchanged,
      including watermark-based delta correctness
- [x] Zero code edits made in this task
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any code change to either orchestrator.
- Real-vault cutover — `T05`.

---

## Context / Notes

This task exists specifically to give Scenario 5 ("the live cron-facing
orchestration contract is unaffected") its own dedicated, disclosed
verification pass, separate from the per-script migration tasks, since the
orchestrators themselves are deliberately untouched.

---

## Implementation Log

**What was built:** Nothing — verification only, as scoped. Zero edits made
to `run_full_capture.py`, `run_delta_capture.py`, or any of the five
per-email scripts they orchestrate.

**Setup:** A fresh real scratch vault (`C:\scratch-sb87t04\vault`, distinct
`--vault-path`, never the live vault), seeded with a real, byte-identical
copy of the live `thread/Template.json` under
`.second-brain/data/Templates/thread/Template.json` (the same setup shape
`T01`-`T03` used). `SECOND_BRAIN_VAULT_PATH` env var pointed at this
scratch path for every invocation of either orchestrator (both read the
vault path exclusively from this env var, no CLI arg — confirmed by direct
source read, unchanged). `pywin32` installed for the real interpreter this
session's shells actually resolve (`py`, `C:\Users\mahmoud.moussa\
AppData\Local\Python\pythoncore-3.14-64\python.exe` — `python`/`python3`
were not resolvable at all in this session's shells, a fresh instance of
this project's own documented `npx`/`node` PATH-resolution antipattern,
now confirmed for `python` too; resolved via the `py` launcher). A
disposable, read-only Outlook COM count (never touching the vault)
confirmed the real target mailbox is modestly sized (Inbox 572 + Sent Mail
135 = 707 raw items), well within reach of a genuine, natural full-history
completion in this session — not the multi-hour scale `SPRINT-031`
documented for a much larger real backlog, so run_full_capture.py was run
to REAL completion rather than a deliberately-bounded representative
subset.

**`[REQ-SB-87-US-02-AC-05]` Step 1 — `run_full_capture.py`:** Run to real,
natural completion against the scratch vault (Outlook genuinely returned
an empty page, not a deliberate early stop): 10 pages, 499 real emails
processed, 247 Threads created, 499 messages created, 111 attachments
captured, `CAPTURE COMPLETE` printed with the exact same JSON summary
shape as before this migration (`status`/`pages`/`total_emails`/
`threads_created`/`messages_created`/`attachments_captured`/`date_range`/
`progress`), real `$LASTEXITCODE` captured directly (not inferred) = `0`.
Same real CLI contract confirmed: no arguments accepted or required
(vault path via `SECOND_BRAIN_VAULT_PATH` only, unchanged). A second,
immediate, real re-run against the SAME scratch vault confirmed genuine
idempotency at the vault-content level: `threads_created: 0`,
`messages_created: 0` in the second run's own JSON, and the real on-disk
`.md` file count under `Work/` unchanged at 1126 before vs. after the
second run (independently counted via `Path.rglob`-equivalent, not just
trusted from the printed summary) — zero duplicate Thread/RawMessage
notes from a real re-run. Second run's own real `exit 0` also directly
captured. One honest, non-blocking observation: `attachments_captured`
differed by 1 between the two runs (111 then 110) even though the
on-disk file count under every Thread's own `files/` folder was IDENTICAL
before/after the second run (226 files both times) — i.e. no actual
duplicate or lost file, just a minor discrepancy in `capture_attachments.
py`'s own returned "captured" count on a re-run. `write_file_companion`/
`capture_attachments.py`'s own re-run accounting is explicitly
hand-written, pre-existing, untouched by `T01`-`T03`'s migration (per the
parent story's own Constraints) — not investigated further as genuinely
out of this task's own scope (verifying the ORCHESTRATORS' contract, not
auditing the five scripts' own internal counters a second time), logged
here for visibility, not as a defect (real file counts prove no actual
duplication or corruption occurred).

**Honest, disclosed clarification (not a defect) — watermark file scope:**
this step's own Tests-prose ("...the watermark state file is written/
updated in its same real location and shape") reads as if
`run_full_capture.py` itself also touches the watermark file. Confirmed
live and via direct source read: it does NOT, before or after this
migration — `run_full_capture.py` has no watermark concept at all (it
pages back until Outlook returns empty); only `run_delta_capture.py` owns
`.second-brain/email_capture_state.json`. After BOTH full-capture runs
above, `.second-brain/` on the scratch vault contained only the seeded
`Templates/thread/Template.json` — zero watermark file — confirmed
correct, unchanged, pre-existing behavior, not a regression. Generalized
as a `MEMORY.md` Constraint entry so a future task's own prose doesn't
misattribute this file to the wrong orchestrator again. The watermark
file's own real contract is verified below, against `run_delta_capture.py`
specifically, where it actually belongs.

**`[REQ-SB-87-US-02-AC-05]` Step 2 — `run_delta_capture.py` (two
back-to-back real passes, same scratch vault):**
- **Pass 1** (fresh scratch vault, no prior watermark): bootstrapped the
  documented 2-day lookback (`load_watermark()`'s own fallback, confirmed
  live via the printed `watermark_before`), paged once (`pages: 1`),
  found 36 of the page's 50 seen emails newer than the bootstrap
  watermark, processed them (idempotently — `threads_created: 0`,
  `messages_created: 0`, since all 36 were already captured by the full
  run above), wrote `.second-brain/email_capture_state.json` for the
  FIRST time, in its real, unchanged shape (`{"last_captured_at":
  "2026-09-02 09:33:03.597000+00:00"}`, confirmed by direct file read —
  the exact same shape `save_watermark()`'s own source produces),
  `DELTA CAPTURE COMPLETE` printed with the same real JSON summary shape
  as before this migration, real `$LASTEXITCODE` = `0` directly captured.
  Real on-disk `.md` count confirmed unchanged (1126) after this pass —
  no duplicates from the idempotent re-processing.
- **Pass 2** (immediately after, same scratch vault, same watermark file
  now present): `watermark_before` correctly read back the value Pass 1
  had just saved; found ZERO of the page's 50 seen emails newer than the
  watermark (`new_emails: 0`, `processed: 0`), `total_new_emails: 0`,
  `threads_created: 0`, `messages_created: 0`, `attachments_captured: 0`,
  `watermark_after == watermark_before` (correctly did NOT regress or
  churn the file when nothing new was found), real `exit 0` directly
  captured. Real on-disk `.md` count confirmed unchanged (1126) after
  this pass too. This is the direct, positive proof the Test step asks
  for: the watermark-based delta logic correctly picks up only genuinely
  new/changed items and performs zero duplicate processing of
  already-captured messages, exercised via two REAL back-to-back runs
  rather than a synthetic new-mail injection (no genuinely new mail
  arrived in the real mailbox during this session's short window, so the
  strongest honest proof available was "immediately-after correctly finds
  nothing new," not "later, new mail correctly gets picked up" — both are
  real instances of the same watermark-comparison code path;
  `new_emails = [e for e in emails if received > watermark]` is exercised
  identically either way).

**(Unlabeled, supporting) Step 3 — zero code edits, confirmed not just
assumed:** `git status`/`git diff` against both orchestrator files
performed AFTER all verification runs above. Both files show a
pre-existing `M` status that already existed at the very start of this
task (present in the session's own opening `git status`, before this
task read or ran anything) — `git diff` against `HEAD` for both files
returns EMPTY (zero content difference), confirming this task made no
content edits of its own; the pre-existing dirty flag (likely a
line-ending/whitespace artifact from an earlier, unrelated session) is
untouched, out of this task's own scope to investigate or fix.

**Scratch artefacts cleaned up:** `C:\scratch-sb87t04\` (scratch vault,
stdout/stderr logs, PID file) removed after verification completed —
nothing left behind outside this repo. The disposable Outlook-count
script lived only in the session scratchpad, never in the repo.

**Escalations / review-queue items written by this task:** none. No new
dependency, shared-interface change, ADR deviation, or unanticipated file
was needed — both orchestrators' own external contract held completely
unchanged, confirmed live, exactly as the parent story's Constraints
anticipated. The one disclosed item above (the watermark-file scope
clarification) is a Tests-prose imprecision about an ALREADY-correct,
pre-existing behavior, not a build defect or a blocked AC — logged in
`MEMORY.md` for future task authors, not escalated.

**Task marked `Done`.** This task's own one locked AC (`AC-05`) verified
live in full, for both halves (`run_full_capture.py` and
`run_delta_capture.py`), including watermark-based delta correctness
(two real back-to-back delta passes) and idempotency (two real
back-to-back full-capture passes) beyond what the Tests block's own three
steps strictly required, for extra confidence given this backs a live,
daily-use cron job. `gate: clear` — no MUST-FLAG trigger fired (no
assumption beyond the honest, disclosed Tests-prose clarification above;
no ADR touched; no escalation; no contradictory input; the verification
technique itself, not the AC's own wording, was the only judgement call,
and it stayed well inside this task's own scope).
