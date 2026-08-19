---
id: BUGFIX-05-US-01-T04
title: Live-verify AC-01 (flat-shape Thread migrated, never duplicated) and flip email-capture-pipeline back to autonomous once both facets are verified
parent_story: BUGFIX-05-US-01
requirement_id: BUG-026
type: backend
status: Done
gate: flagged
gate_reason: "Two real-vault incidents occurred during this task's own second-attempt verification (a diagnostic call that side-effect-triggered a migration outside the real endpoint; a stale, pre-edit server process reproducing the pre-ADR-053 bug) -- both self-caught, fully repaired, and disclosed in full in this task's own Implementation Log, per this project's 'disclosed, not silently buried' convention (mirrors T02's own identical precedent). Not blocking: both AC-01 and AC-02's flip clause are genuinely verified PASS against the freshly-restarted, correct-code server, and the working-mode flip to autonomous is confirmed permanent."
depends_on: [BUGFIX-05-US-01-T01, BUGFIX-05-US-01-T02, BUGFIX-05-US-01-T03, BUGFIX-05-US-01-T05]
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-05-US-01-T04 — Live-verify AC-01 (flat-shape Thread migrated, never duplicated) and flip email-capture-pipeline back to autonomous once both facets are verified

## Parent Story

- Story: [[BUGFIX-05-US-01]] — `../UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md`
- Requirement: `BUGS.md` → `BUG-026` (bugfix story; no PRD requirement anchor)

---

## Objective

Prove, live, against the real configured vault (`VAULT_PATH`) and the
real `process_staged_email` capability endpoint, that `T01`'s composing
rewire, `T03`'s `resolve_thread_directory()` migration, and `T05`'s
`pre_migration_summary.md` sidecar mechanism together close `AC-01`'s own
re-locked wording (`ADR-053`): a new message arriving for a real,
pre-redesign, FLAT `Work/Threads/<name>.md` Thread note (with a real,
non-empty pre-migration `## Summary`) is migrated to the standard
directory shape, its regenerated `## Summary` genuinely reflects BOTH the
real pre-migration history AND the new message (never silently replaced
by a synopsis of the new message alone), the sidecar is archived to
`pre_migration_summary.consumed.md`, the new message is threaded into
that SAME Thread's history, and no second, duplicate Thread note is ever
created.

**Prior finding (superseded, not repeated):** this task's own first
attempt (2026-08-19, see `## Implementation Log` below, left untouched)
found `AC-01` genuinely FAILING under the pre-`ADR-053` design — the
migration itself worked, but the freshly-migrated Thread's real
pre-migration `## Summary` was silently lost the moment `synthesize_
thread` next ran on it. `ADR-053`'s sidecar mechanism (`T05`) exists
specifically to close that gap; this re-run re-verifies the SAME
scenario against the now-fixed design, not a new scenario.

Once `AC-01` is confirmed passing here AND `AC-02` is already confirmed
passing (`T02`, a real dependency of this task), this task ALSO performs
the working-mode flip `AC-02`'s own locked wording ties to "once this
scenario and Scenario 1 are both verified live" — flipping `email-capture-
pipeline`'s working mode from `supervised` to `autonomous`, undoing
`ESC-048`'s protective measure. This is the FIRST task in this story where
that flip is in scope — `T02` explicitly deferred it (only `AC-02` was
locked when `T02` was written); this task exists precisely because both
preconditions are now satisfiable.

---

## Starting State → End State

**Before / Inputs:**
- `T01` is `Done` — `run_email_capture_pipeline()` composes `capture_raw_
  thread_messages`/`synthesize_thread`, never the old `StateGraph`/
  `thread_match_merge`.
- `T02` is `Done` — `AC-02` (the orphaning facet) is already verified
  PASS live.
- `T03` is `Done` — `resolve_thread_directory()`'s second scan tier and
  `migrate_flat_thread_to_directory` exist and are verified against their
  own smoke checks.
- `T05` is `Done` — `migrate_flat_thread_to_directory` writes the
  `pre_migration_summary.md` sidecar; `synthesize_thread` folds it into
  its existing Compass call and archives it to
  `pre_migration_summary.consumed.md` on success.
- `email-capture-pipeline`'s working mode is currently `supervised`
  (`ESC-048`'s own protective measure, still in force).
- **Recommended verification target: reuse `conversation_id
  041969487D51E942B77F5CD4A13A6CC2` ("Compass Alert- Failed API Calls").**
  This task's own first attempt (below, left untouched) already used this
  SAME real flat Thread and, after finding `AC-01` failing, fully restored
  it byte-identical from a pre-test backup (`diff`-confirmed) — see that
  attempt's own Implementation Log for the restoration record. It is
  confirmed safe and genuinely back to its original flat, pre-redesign
  state, with its own known, real pre-migration `## Summary` text already
  recorded in this task's own Implementation Log below — which makes it an
  especially strong re-verification target, since the exact expected
  "reflects both the real pre-migration history and the new message"
  outcome is already known and can be directly compared. If, at
  verification time, this Thread is found to have been altered by
  unrelated real capture activity in the interim, fall back to any OTHER
  real flat note confirmed to have no directory-shaped duplicate for its
  own `conversation_id` yet, EXCLUDING `CF7FD118DD45F740ACAD6B93AB83BEB5`
  (`RITM0108464`, already migrated by `T03`) and whichever candidate `T05`
  itself consumed for its own smoke test (see `T05`'s own Implementation
  Log). **Do NOT use `conversation_id
  ED0954959F6F4A4C88F9E2ACA3D7113A`** (the Azure Forecast conversation) —
  it already has a real, diverged, directory-shaped duplicate that
  `ADR-052`'s own ordering rule deliberately, correctly no-ops on; using it
  would not actually exercise the new migration path and would not prove
  `AC-01`.

**After / Outputs:**
- The chosen flat Thread note is migrated in place to the standard
  `<slug>/<slug>.md` + `messages/` directory shape.
- The migrated Thread's regenerated `## Summary` genuinely reflects BOTH
  its own real pre-migration history AND the new staged message's own
  content — never silently replaced by a synopsis of the new message
  alone.
- The Thread directory's `pre_migration_summary.md` sidecar is renamed in
  place to `pre_migration_summary.consumed.md` (archived, never deleted).
- The new staged message is threaded into that SAME migrated Thread's
  history — reflected in the regenerated `## Summary` and a new raw
  message note under its own `messages/` directory.
- No second, duplicate Thread note exists anywhere in the vault for that
  same `conversation_id`.
- `[BUGFIX-05-US-01-AC-01]` recorded PASS or FAIL, with the real evidence,
  in this task's own Implementation Log.
- `email-capture-pipeline`'s working mode is flipped `supervised →
  autonomous` (only after both ACs are confirmed PASS) —
  `[BUGFIX-05-US-01-AC-02]` (the flip clause) recorded PASS in this task's
  own Implementation Log.
- The already-diverged `ED0954959F6F4A4C88F9E2ACA3D7113A` case is left
  completely untouched by this task.

---

## Files to Modify

None expected — this task calls the real, already-built `process_staged_
email` capability endpoint (`POST /agents/email-capture-pipeline/
schedules/process_staged_email/run-now`) and the real, already-built agent
working-mode endpoints (`GET /agents/email-capture-pipeline`, `PATCH
/agents/email-capture-pipeline` with `{"working_mode": "autonomous"}`,
`app/api/agents_router.py`) only. If genuine additional code is found to
be needed live, that is an out-of-scope escalation
(`Implementation/Pipeline.md` hard rule 5) — do not improvise a fix inside
this verification-only task.

---

## Constraints

- Inherits from parent story (real, live vault — no fixture/test vault;
  no-data-loss is load-bearing, not a convenience).
- Must call the REAL capability endpoint (`POST /agents/email-capture-
  pipeline/schedules/process_staged_email/run-now`) to drive the actual
  processing under test — never a raw script that calls `synthesize_
  thread`/`resolve_thread_directory` directly and skips the real
  capability surface.
- Staging the precondition message MAY use the real, existing `email_
  staging.stage_email(email)` data-access primitive directly if no
  genuine new Outlook message for the chosen conversation arrives
  naturally within the verification window (same disclosed substitute
  `T02` used, mirroring `BUGFIX-03-US-01-T02`'s own established
  precedent) — only the FETCH is substituted, never the PROCESSING under
  test. Any synthetic staged message must be clearly, visibly marked as
  verification content (e.g. subject prefixed `[BUGFIX-05-US-01-T04
  verification]`).
- Must NOT choose `conversation_id ED0954959F6F4A4C88F9E2ACA3D7113A` as
  the verification target (see `## Starting State` above for why).
- Must NOT attempt to fix, merge, or otherwise touch the already-diverged
  `ED0954959F6F4A4C88F9E2ACA3D7113A` case — out of this story's scope
  (deferred to a future Librarian-housekeeping backlog item, per the
  architect's own Decision 2).
- Must back up the chosen flat Thread note's own concept-file content
  (including its full pre-migration `## Summary` text) BEFORE inducing the
  real capture, and confirm the migrated concept file's own content is
  faithfully preserved (frontmatter byte-identical; `## Summary`
  regenerated to genuinely reflect BOTH that baseline text AND the genuine
  new message — never a bare replacement of one by the other) — mirrors
  `T02`'s/`BUGFIX-03-US-01-T02`'s own established "back up real production
  state, test, then restore where the state was synthetic"
  `Implementation/Learnings.md` pattern (`SPRINT-030`). The migration
  itself (flat file → directory shape) AND the sidecar's own successful
  archive-rename to `pre_migration_summary.consumed.md` are the intended,
  permanent, correct end state — do NOT revert either; only clean up any
  genuinely synthetic verification content (e.g. a `stage_email`
  substitute's own resulting raw message note) if used.
- The working-mode flip (`supervised → autonomous`) MUST NOT happen until
  BOTH `[BUGFIX-05-US-01-AC-01]` (this task) AND `[BUGFIX-05-US-01-AC-02]`
  (`T02`, already `Done`) are confirmed PASS — do not flip speculatively
  before `AC-01`'s own verification steps below complete successfully.

---

## Tests

<!-- AC-01 is the primary locked AC verified in this task. AC-02's own
third Gherkin clause (the working-mode flip, deliberately deferred by T02
since AC-01 was not yet locked when T02 was written) is ALSO verified
here, tagged AC-02 again — Pipeline.md requires at least one tagged step
per locked AC, not exactly one; AC-02's own Gherkin is only FULLY verified
once this flip-clause step, here, is added to T02's own two earlier
steps. -->

**Manual verification steps (live against the real configured vault —
`VAULT_PATH`; real backend server running):**

1. **[BUGFIX-05-US-01-AC-01]** Confirm `email-capture-pipeline`'s current
   working mode is `supervised` (`GET /agents/email-capture-pipeline`).
   Per `## Starting State` above, prefer reusing `conversation_id
   041969487D51E942B77F5CD4A13A6CC2` ("Compass Alert- Failed API Calls") —
   confirm directly it is still a genuine flat note at its own original
   path with no directory-shaped duplicate, and that its `## Summary` still
   reads as the real, substantive text this task's own prior attempt
   already recorded (below) — reuse it if so; otherwise, enumerate the
   real flat Thread notes still live (`Work/Threads/*.md`, one level deep)
   and, for each OTHER candidate, confirm no directory-shaped duplicate
   already exists for its own `conversation_id` (search `Work/Threads/*/
   *.md` for the same `conversation_id` string) — explicitly exclude
   `ED0954959F6F4A4C88F9E2ACA3D7113A`, `CF7FD118DD45F740ACAD6B93AB83BEB5`,
   and whichever candidate `T05` consumed for its own smoke test. Record
   the chosen candidate's own `conversation_id` (from its frontmatter), its
   flat file path, and its full concept-file content (frontmatter + body,
   including its real pre-migration `## Summary` text) — this is the
   backup/baseline.
2. Arrange a new staged message for that SAME `conversation_id` — prefer a
   real, newly-arrived Outlook message in that conversation if one exists
   within the verification window; otherwise use the disclosed `email_
   staging.stage_email(...)` substitute per this task's own Constraints (a
   real dict shape, same `conversation_id`, a clearly verification-marked
   subject, a real, distinct `id`/message id, a `received` timestamp later
   than the flat note's own last-known message).
3. Call the REAL capability endpoint: `POST /agents/email-capture-
   pipeline/schedules/process_staged_email/run-now`. Confirm the response
   is a real, honest result (not an error) and that it reflects one thread
   updated for the chosen `conversation_id`.
4. **[BUGFIX-05-US-01-AC-01]** After the run completes, confirm directly:
   - the flat note no longer exists at its own original path;
   - a new directory now exists at `Work/Threads/<slug-of-conversation_
     id>/`, containing `<slug>.md` (the migrated concept file — its
     frontmatter preserved from step 1's baseline) and a `messages/`
     subdirectory containing the new message's own raw note;
   - the migrated concept file's regenerated `## Summary` genuinely
     reflects content from BOTH step 1's own recorded baseline `## Summary`
     text AND the new message — read it directly and confirm both are
     represented (e.g. for the "Compass Alert" candidate, both the
     original Failed-API-Calls alert content AND the new message's own
     subject matter should be recognizable), never a synopsis of the new
     message alone;
   - the Thread directory's `pre_migration_summary.md` sidecar no longer
     exists; `pre_migration_summary.consumed.md` exists in its place, with
     text identical to step 1's own recorded baseline `## Summary` (archived
     verbatim, never deleted);
   - no second, duplicate Thread note exists anywhere under `Work/
     Threads/` for this same `conversation_id` (search the vault directly
     for the `conversation_id` string, mirroring `ESC-055`'s own
     verification technique).
5. **[BUGFIX-05-US-01-AC-02]** Confirm `T02`'s own Implementation Log
   already records `AC-02` PASS. Since `AC-01` (step 4, above) is now also
   confirmed PASS, flip `email-capture-pipeline`'s working mode:
   `PATCH /agents/email-capture-pipeline` with `{"working_mode":
   "autonomous"}`. Confirm via `GET /agents/email-capture-pipeline` that
   the working mode now reads `autonomous` — this is the intended,
   permanent end state; do NOT revert this flip.
6. Cleanup: if step 2 used the synthetic `stage_email` substitute, delete
   only the resulting raw message note it produced if it was purely
   verification content (a clearly-marked synthetic subject) — do NOT
   delete or revert the migration itself (the flat-to-directory shape
   change is the correct, permanent, intended real-world outcome of this
   fix, not verification noise). If step 2 used a genuine, naturally-
   arrived real email, no reversion of any kind is needed.
7. Confirm the already-diverged `ED0954959F6F4A4C88F9E2ACA3D7113A` case is
   completely untouched (still one flat 2026-07-27 note + one
   directory-shaped 2026-08-17 duplicate, unchanged from before this
   task) — this task must not have altered it.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `[BUGFIX-05-US-01-AC-01]` verified live and passing — including the
      regenerated `## Summary` genuinely reflecting BOTH the real
      pre-migration history and the new message, and the sidecar archived
      to `pre_migration_summary.consumed.md`
- [x] `[BUGFIX-05-US-01-AC-02]`'s own working-mode-flip clause verified
      live and passing
- [x] `email-capture-pipeline`'s working mode confirmed flipped to
      `autonomous` (permanent — not reverted)
- [x] The already-diverged `ED0954959F6F4A4C88F9E2ACA3D7113A` case is
      confirmed untouched
- [x] The real vault is left in its correct post-fix state (migration
      kept; any purely synthetic verification content cleaned up; real
      content, if any arrived naturally, is left as-is)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Fixing, merging, or otherwise reconciling the already-diverged
  `ED0954959F6F4A4C88F9E2ACA3D7113A` duplicate — deferred to a future
  Librarian-housekeeping backlog item, per the architect's own explicit
  Decision 2 and `ESC-055`'s resolution note.
- Any code change — this is a verification-only task (see `## Files to
  Modify`); the working-mode flip is a real, live state change via the
  existing agent-settings endpoint, not a code change.
- Any change to `pull_email`/`email_pull.py`.

---

## Context / Notes

Full reasoning for why `AC-01` was not locked until now, and the full
history of `ESC-055`/`ADR-052`: the story's own `## Notes` (all four
decomposer/architect passes) and `ESCALATIONS.md` → `ESC-055`/`ESC-056`
(both `Resolved`). `T02`'s own Implementation Log is the precedent for
`AC-02`'s own first two clauses; this task's own Implementation Log
records the third (flip) clause and `AC-01` together, since both are
only satisfiable once `T01`+`T02`+`T03`+`T05` are all `Done`.

**Decomposer re-lock pass, `/plan-tasks` step 2, 2026-08-19:** this
task's own first attempt (below) found `AC-01` genuinely failing —
`ADR-052`'s migration alone did not preserve a freshly-migrated flat
Thread's real pre-migration `## Summary` once `synthesize_thread` next
ran on it. The architect resolved this with `ADR-053` (a one-time,
self-consuming `pre_migration_summary.md` sidecar), implemented by the
new `T05`. `AC-01` is re-locked against `ADR-053`'s concrete design (see
the story's own `## Notes`, latest pass); this task's own `depends_on`
now includes `T05`, and its `## Objective`/`## Starting State`/`## Tests`
above are updated to verify the sidecar fold-in/archive alongside the
original migration/threading/no-duplicate outcomes. This task's own
prior FAIL attempt below is left completely untouched (append-only
historical record) — it is not repeated, only superseded by a fresh
re-run against the now-fixed design.

---

## Implementation Log

**2026-08-19, coder. `[BUGFIX-05-US-01-AC-01]` — FAIL. Task `Blocked`.**

**Preconditions confirmed:** `T01`, `T02`, `T03` all `Done`; server
confirmed running the freshly-restarted, corrected code (same server
process the `T02` incident's own repair already validated — see `T02`'s
own Implementation Log); `email-capture-pipeline` confirmed `supervised`.

**Verification steps run (against the real configured vault):**

1. Enumerated the real flat Thread notes still live under `Work/Threads/*.md`
   (one level deep): 6 remaining candidates (7 minus `Requested Item
   RITM0108464 has been updated`, already migrated by `T03`'s own smoke
   test). Cross-checked each against every real directory-shaped Thread's
   own `conversation_id` frontmatter — confirmed only
   `ED0954959F6F4A4C88F9E2ACA3D7113A` (Azure) has a known duplicate;
   excluded it per this task's own Constraints. Chose `Compass Alert-
   Failed API Calls-2026-07-27-61c91877.md` (`conversation_id
   041969487D51E942B77F5CD4A13A6CC2`). Backed up its full concept-file
   content (frontmatter + body, including its real, substantive
   pre-migration `## Summary`) before proceeding.
2. Staged one new, clearly-marked synthetic message (`id:
   "T04-VERIFICATION-0001"`) for the same `conversation_id` via `email_
   staging.stage_email`.
3. Called `POST /agents/email-capture-pipeline/schedules/
   process_staged_email/run-now` → pending → approved via `POST
   /pending-approvals/{id}/approve` → real, honest, non-error result.
4. **Migration facet — PASS on its own:** confirmed the flat note no
   longer exists at its original path; a new directory exists at
   `Work/Threads/041969487D51E942B77F5CD4A13A6CC2/` containing the
   concept file and a `messages/` subdirectory; no second, duplicate
   Thread note exists anywhere for this `conversation_id` (vault-wide
   search, one match). This part of `AC-01`'s own `Then` clause is
   correctly satisfied — `T03`'s own primitive works exactly as designed.
5. **Content-preservation facet — FAIL.** Directly read the migrated
   concept file's own `## Summary` section: it now reads "Single-message
   thread: a verification notice from 'BUGFIX-05-US-01-T04 verification'
   ... regarding AC-01 flat-thread migration check ..." — the ENTIRE
   original, real `## Summary` text (describing the actual Compass
   API-failure alert: "On Jul 27, 2026 at 5:01 PM, an automated status
   email ... reported a 'Failed API Calls' alert ... The per-minute
   failure rate hit 100.0% ...") is GONE — not merged, not referenced,
   silently replaced. Root cause (confirmed by direct reading, not
   assumed): `synthesize_thread` (unmodified by this story, per `T01`'s
   own Constraint) regenerates `## Summary` purely from raw message notes
   under the Thread's own `messages/` directory; `migrate_flat_thread_to_
   directory` (`T03`, per `ADR-052` Decision 1's own explicit "touches
   only filesystem SHAPE" design) creates that directory EMPTY — it never
   backfills a raw message capturing the flat note's own pre-migration
   history. This directly contradicts `AC-01`'s own locked wording
   ("preserving its own prior content"). Full write-up, root cause,
   evidence, and candidate fix options (none decided): `ESCALATIONS.md`
   → `ESC-056`.

**Immediate real-vault repair (before any further action):** restored
`Compass Alert- Failed API Calls-2026-07-27-61c91877.md` byte-identical
from the pre-test backup (`diff`-confirmed) — fully reversing BOTH the
migration and the lossy re-synthesis, since the story's own standing,
overriding Constraint ("no-data-loss is load-bearing, not a convenience")
takes precedence over this task's own narrower "do NOT revert the
migration" instruction, which assumed a successful, content-preserving
migration. The real vault is confirmed back in its exact pre-`T04` state.
Deleted the synthetic raw message note as part of the same reversal
(removed with the whole migrated directory). Declined the two stray
`acknowledge_classification_failure` Pending Approvals this test produced
(both reference only the synthetic verification subject). Confirmed
`email_staging` empty afterward.

**Working-mode flip: NOT performed.** `AC-02`'s own locked wording ties
the flip to "once this scenario AND Scenario 1 are both verified live" —
`AC-01` (Scenario 1) is not verified passing, so the flip's own
precondition is not met. `email-capture-pipeline`'s working mode is
confirmed still `supervised`.

**Acceptance Criteria checklist:**
- [ ] `[BUGFIX-05-US-01-AC-01]` verified live and passing — **FAIL**, see
      above; genuine architecture-level gap, not a coding defect in this
      task's own scope to fix (verification-only, `## Files to Modify`:
      none)
- [ ] `[BUGFIX-05-US-01-AC-02]`'s own working-mode-flip clause verified
      live and passing — **NOT ATTEMPTED**, correctly deferred since its
      own precondition (`AC-01` passing) is not met
- [ ] `email-capture-pipeline`'s working mode confirmed flipped to
      `autonomous` — **NOT DONE**, remains `supervised` (correct, per the
      above)
- [x] The already-diverged `ED0954959F6F4A4C88F9E2ACA3D7113A` case is
      confirmed untouched (excluded from candidate selection at step 1;
      never referenced by this run)
- [x] The real vault is left in its correct state — restored to its exact
      pre-task state (full reversal, since the "post-fix" state this task
      would otherwise have left permanently was itself the discovered
      defect)
- [ ] `MEMORY.md` — see story-level `MEMORY.md` entry (records this
      finding as a constraint for future architecture work)
- [x] `CHANGELOG.md` entry appended (this task's own commit)

**Blocked — not Done.** Per `Implementation/Pipeline.md` hard rule 4/trigger
6, a locked AC that fails live verification is a hard failure; this task
cannot be marked `Done`. Escalated: `ESCALATIONS.md` → `ESC-056`;
`REVIEW-QUEUE.md` entry written. The story (`BUGFIX-05-US-01`) stays `In
Progress` (not `Done`); `BUG-026` stays `In Sprint` (not `Closed`); the
sprint (`SPRINT-065`) stays `In Progress` (not `Done`) — see the sprint
file's own Retrospective/status notes for the full picture of what shipped
and what remains open.

---

**2026-08-19, coder. Second attempt — against `T05`'s now-`Done` `ADR-053`
sidecar mechanism. `[BUGFIX-05-US-01-AC-01]` — PASS. `[BUGFIX-05-US-01-AC-02]`
(flip clause) — PASS. Task `Done`.**

**Preconditions confirmed:** `T01`/`T02`/`T03`/`T05` all `Done`;
`email-capture-pipeline` confirmed `supervised`.

**Own real-vault incident during this attempt (disclosed, not silently
buried — mirrors `T02`'s own precedent for the same failure class):**
before the tracked verification run, a diagnostic call to `vault_writer.
resolve_thread_note_path` (made while re-confirming the reserved
candidate's own clean state) triggered `resolve_thread_directory`'s own
documented side-effecting second-scan tier and silently migrated
`Compass Alert- Failed API Calls-2026-07-27-61c91877.md` outside the real
capability endpoint — a genuine violation of this task's own "never a raw
script that calls resolve_thread_directory directly" Constraint, caught
immediately. No content was lost (`migrate_flat_thread_to_directory`'s own
contract is a pure rename plus the new sidecar; confirmed the relocated
concept file was byte-identical to the pre-touch content via direct string
comparison) — repaired immediately by renaming the concept file back to
its original flat path and removing the newly-created sidecar/directory,
confirmed via a direct `Read` that the restored file matched the two
earlier independent `Read` calls of the same file. **Second, separate
incident found immediately after, before any further action:** re-running
this task's own real verification through `POST .../process_staged_email/
run-now` against the STILL-RUNNING server process reproduced `ESC-056`'s
ORIGINAL pre-`ADR-053` failure exactly (no sidecar written at all, `##
Summary` silently replaced by only the new message's own content) —
diagnosed, not assumed: the running `uvicorn` process (PID 11536/41152, no
`--reload` flag, started before this session's own code edits to `vault_
writer.py`/`email_classification.py`) was running STALE code, the exact
same failure class `T02`'s own Implementation Log already documented and
repaired once this story. Restored the real Thread a second time
(reconstructed byte-for-byte from this task's own two independent `Read`
tool outputs of the file, taken before either incident — no other backup
existed; the vault itself is not under git). Killed the stale processes
cleanly (`Stop-Process -Force`, confirmed zero orphaned `python.exe`
processes), started a fresh `uvicorn` process, confirmed via `GET /agents/
email-capture-pipeline` that it responds and reports `supervised` before
re-attempting. No code fix required — both incidents are attributable to
this task's own script discipline and a stale pre-existing process, not a
defect in `T05`'s own implementation (confirmed: the fresh, correct-code
attempt below passed cleanly).

**Live verification of `[BUGFIX-05-US-01-AC-01]` (against the freshly
restarted, confirmed-correct server):**

1. Confirmed `email-capture-pipeline` `supervised`. Reused `conversation_id
   041969487D51E942B77F5CD4A13A6CC2` ("Compass Alert- Failed API Calls") —
   re-confirmed, freshly, its own flat file was back at its original path
   with content matching this task's own two independent baseline `Read`s
   (frontmatter + full body, including its real `## Summary`: "On Jul 27,
   2026 at 5:01 PM, an automated status email from status.notification@
   compass.core42.ai... reported a "Failed API Calls" alert... The
   per-minute failure rate hit 100.0%... no-reply notification.").
2. Staged one new, clearly-marked synthetic message (`id:
   "T04-VERIFICATION-0002"`, subject `[BUGFIX-05-US-01-T04 verification]
   RE: Compass Alert: Failed API Calls (retry)`) via `email_staging.
   stage_email`, same `conversation_id`, `received` later than the
   original message.
3. Called `POST /agents/email-capture-pipeline/schedules/
   process_staged_email/run-now` → `{"status": "pending", ...}`; approved
   via `POST /pending-approvals/379b61b119a7/approve` → `{"status":
   "approved", ...}`, a real, honest, non-error result.
4. **`[BUGFIX-05-US-01-AC-01]` — PASS, confirmed by direct reading:**
   - flat note no longer exists at its own original path;
   - `Work/Threads/041969487D51E942B77F5CD4A13A6CC2/` now exists,
     containing the migrated concept file and `messages/` (1 new raw
     message note);
   - the migrated concept file's own regenerated `## Summary` genuinely
     reflects content from BOTH the real Jul 27 alert (per-minute failure
     rate, 70.0% threshold, no-reply notice) AND the new Aug 19 synthetic
     message (references the retry/AC-01 re-verification, resolution after
     a service restart) — read directly, both clearly represented, never a
     bare replacement of one by the other;
   - `pre_migration_summary.md` no longer exists; `pre_migration_summary.
     consumed.md` exists in its place, text-identical (confirmed via
     direct comparison) to step 1's own recorded baseline `## Summary`;
   - vault-wide search (every `.md` file, not only `Work/Threads/`) for the
     literal string `041969487D51E942B77F5CD4A13A6CC2` returns exactly 2
     matches: the concept file and its own one raw message note (which
     legitimately carries the same `conversation_id` in its own
     frontmatter) — no second, duplicate Thread note anywhere.
5. **`[BUGFIX-05-US-01-AC-02]` (flip clause) — PASS:** confirmed `T02`'s
   own Implementation Log already records `AC-02`'s first two clauses
   PASS. With `AC-01` now also confirmed PASS, called `PATCH /agents/
   email-capture-pipeline` `{"working_mode": "autonomous"}` → response
   confirms `"working_mode":"autonomous"`. Re-confirmed via a SEPARATE,
   fresh `GET /agents/email-capture-pipeline` → `"working_mode":
   "autonomous"`. Permanent — not reverted.
6. Cleanup: deleted the synthetic raw message note (`messages/
   2026-08-19-5824a039.md`) — did NOT revert the migration or the
   sidecar's own successful archive-rename (this task's own Constraints:
   "the intended, permanent, correct end state"). Declined 4 stray
   `acknowledge_classification_failure` Pending Approvals produced across
   both incidents (`02d4c95dffa5`, `00bed2778acd`, `70ac1f223851`,
   `c6fc212201a1` — Compass's own separate first-message classification
   call, unrelated to `## Summary` synthesis, fails on the synthetic
   sender domain; pre-existing, unmodified behavior). Confirmed
   `email_staging` empty. **Disclosed scope-internal judgement call**
   (mirrors `T05`'s own identical disclosure): did not revert `participants`/
   `last_message_at`/`last_message_at_display` (now reflecting the real,
   permanent Aug 19 processing run) — this task's own Cleanup step names
   only "the resulting raw message note" for deletion, and the migration +
   sidecar-consumption (which these fields are a direct, designed
   consequence of, per `synthesize_thread`'s own pre-existing, unmodified
   per-message frontmatter-update behavior) are explicitly the intended
   permanent end state.
7. Confirmed `ED0954959F6F4A4C88F9E2ACA3D7113A` (Azure) completely
   untouched: still exactly 1 flat 2026-07-27 note + 1 directory-shaped
   2026-08-17 duplicate, unchanged.

**Acceptance Criteria checklist:**
- [x] `[BUGFIX-05-US-01-AC-01]` verified live and passing — including the
      regenerated `## Summary` genuinely reflecting BOTH the real
      pre-migration history and the new message, and the sidecar archived
      to `pre_migration_summary.consumed.md`
- [x] `[BUGFIX-05-US-01-AC-02]`'s own working-mode-flip clause verified
      live and passing
- [x] `email-capture-pipeline`'s working mode confirmed flipped to
      `autonomous` (permanent — not reverted)
- [x] The already-diverged `ED0954959F6F4A4C88F9E2ACA3D7113A` case is
      confirmed untouched
- [x] The real vault is left in its correct post-fix state (migration
      kept; synthetic raw message note cleaned up; two real-vault
      incidents from this session's own script discipline fully repaired
      and disclosed above)
- [x] `MEMORY.md` updated (see repo-root `MEMORY.md`)
- [x] `CHANGELOG.md` entry appended

gate: flagged — two real-vault incidents occurred during this task's own
verification process (disclosed in full above), both self-caught and
fully repaired before any permanent damage, neither caused by a defect in
`T05`'s own implementation. Flagged for human awareness per this
project's "disclosed, not silently buried" convention (mirrors `T02`'s
own identical precedent), not because anything remains unresolved — both
ACs are genuinely verified PASS and the working-mode flip is confirmed
permanent. **Task `Done`.**
