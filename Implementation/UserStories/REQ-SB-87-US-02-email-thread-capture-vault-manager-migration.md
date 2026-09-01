---
id: REQ-SB-87-US-02
title: Migrate email-thread-capture's write mechanics onto vault_manager.py
requirement_ids: [REQ-SB-87]
requirement_section: "REQ-SB-87: Email Thread Capture — a New, LLM-Driven Pipeline (Classify, Skip Noise, Summarize, Find Pending Actions)"
phase: P1
status: Ready
gate: clear
gate_reason: "Was flagged: live-pipeline migration/verification approach needed a human decision. Resolved 2026-09-01, operator, verbatim: \"Lets Build a small sample of 100 Emails to a new Pipeline we keep tweaking it when done we change the OutputDirectory and move on\" — a scratch-vault-path proving phase (real ~100-email sample, iterate against a distinct --vault-path) before the live cron job's own --vault-path is pointed at the real vault. See Constraints and Notes for the full resolution; original trigger reasoning preserved below, not erased."
sprint: "SPRINT-083"
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-02 — Migrate email-thread-capture's Write Mechanics onto vault_manager.py

## Story

**As the** operator whose live, daily `email-delta-capture` cron job (and the
one-time `run_full_capture.py` path) depends on `email-thread-capture`
**I want** `ingest_email.py`, `rename_thread.py`, `capture_attachments.py`,
`capture_file_link.py`, and `link_person_to_thread.py` to resolve/create/
update Thread and RawMessage notes through `vault_manager.py`'s template-
driven primitives instead of `vault_lib.py`'s own 614-line hand-rolled
implementation
**So that** Threads/RawMessages are maintained on the same, single,
already-twice-proven engine every other real capture pipeline now uses
(`meeting-capture`, `create-companies-partners`), without changing any of
`email-thread-capture`'s own real business logic (Person-note creation/dedup,
the section-ownership guard, attachment/file-link capture, Thread↔Person
linking) or breaking its live cron-facing contract.

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-87: Email Thread Capture — a New,
  LLM-Driven Pipeline (Classify, Skip Noise, Summarize, Find Pending Actions)*
- **Depends on** [[REQ-SB-87-US-01]] — the `thread`/`raw-message` templates
  and the resynced, canonical `vault_manager.py` must exist before this
  story's own scripts can call them.
- This Skill backs the LIVE `email-delta-capture` cron job the operator
  depends on daily (`SKILL.md`'s own "Recurring path (delta capture)"
  section) — real production risk, not a greenfield build. The PRD's own
  raised-context note: this requirement was raised the same day the real
  Hermes gateway process was found silently down all day, stalling
  `email-delta-capture` among other jobs — the operator's own "issues with
  the pipelines" framing is about RELIABILITY, not a claim that
  `email-thread-capture`'s own hand-written logic is broken; this story's real
  motivation is consolidating onto the one, already-proven engine, not fixing
  a defect.
- Precedent for a phased, low-risk cutover technique: `ingest_meeting.py`'s
  own migration (2026-08-25) initially wrote to a parallel, non-colliding
  location (`Notes/Meetings/...`, separate from the then-live
  `Work/Meetings/...` tree) before being proven and cut over — worth
  considering here too, though the exact verification technique is a
  `/plan-tasks`/coder-level decision, not locked by this story.
- Related: [[REQ-SB-87-US-01]] (upstream), `create_companies_partners.py`
  (the other real precedent — same-process `import vault_manager`, not a CLI
  subprocess).

## Acceptance Criteria

### Scenario 1: A first-seen email creates a Thread and its first RawMessage exactly as today
```gherkin
Given an email whose conversation_id has never been captured before
When ingest_email.py runs (now resolving/creating the Thread via
  vault_manager.py's find_by_id/create against the thread template, and
  creating the message note via the RawMessage mechanism REQ-SB-87-US-01
  delivers)
Then a new Thread concept note and its first RawMessage note are written with
  the exact same real frontmatter, body-section, and file/folder layout
  email-thread-capture produces today
  And the script still returns {thread_created, message_created, thread_path,
  message_path} with the same meaning as today
```
<!-- AC-ID: REQ-SB-87-US-02-AC-01 -->

### Scenario 2: Re-ingesting the same message is idempotent
```gherkin
Given a message_id that has already been captured
When ingest_email.py runs again for the same message
Then no duplicate Thread or RawMessage note is created
  And the Thread's own last_message_at frontmatter only ever advances, never
  regresses, matching today's real behavior
```
<!-- AC-ID: REQ-SB-87-US-02-AC-02 -->

### Scenario 3: Thread renaming, backlink updates, and same-day-subject collision handling are preserved
```gherkin
Given a Thread directory still slugged from its raw conversation_id, with
  existing messages and file companions
When rename_thread.py runs (now resolving/updating the Thread via
  vault_manager.py)
Then the Thread's directory and concept-note filename are relabeled to
  "<date> <subject>" exactly as today
  And every existing message note's own thread backlink, and every file
  companion's own source_thread field, are updated to match
  And two different conversation_ids that would clean to the identical
  "<date> <subject>" stem are still disambiguated the same way (a
  hash-of-conversation_id suffix), preserving the existing live-found
  collision fix
```
<!-- AC-ID: REQ-SB-87-US-02-AC-03 -->

### Scenario 4: Person-note creation, section-ownership, and Thread<->Person linking stay hand-written and behaviorally unchanged
```gherkin
Given link_person_to_thread.py, capture_attachments.py, and
  capture_file_link.py each still need to create/top up a bare Person note
  and accumulate a wikilink into the Thread's own ## Related / ## Files
  section
When these scripts are migrated to call vault_manager.py's create/
  modify_section/get_section_content instead of vault_lib.py's own
  hand-rolled read/replace-section primitives
Then ensure_bare_person_note's own dedup-key, ignore-list, and GAL-derived
  department/role/company logic stays exactly as it is today, entirely
  hand-written
  And every existing caller-to-section write restriction still holds for
  THIS Skill's own five scripts (only link_person_to_thread may write
  ## Related; only capture_attachments/capture_file_link may write ## Files;
  ## Personal Notes is never machine-writable by ANY of these five scripts;
  ## Actions is likewise refused to all five -- the one narrow exception
  REQ-SB-87-US-01/US-05 introduce is a DIFFERENT Skill's own caller
  [[REQ-SB-87-US-05]], never one of email-thread-capture's own scripts), now
  enforced via the Thread template's own section-access declarations rather
  than vault_lib.py's own _CALLER_ALLOW_LISTS
```
<!-- AC-ID: REQ-SB-87-US-02-AC-04 -->

### Scenario 5: The live cron-facing orchestration contract is unaffected
```gherkin
Given run_full_capture.py (one-time full history) and run_delta_capture.py
  (recurring, watermark-based, the process behind the live
  email-delta-capture cron job) each invoke the five per-email scripts above
  as separate subprocess calls, parsing each one's own printed JSON
When those five scripts are migrated onto vault_manager.py
Then both orchestrators' own external CLI contract (arguments accepted, JSON
  printed to stdout, exit codes, the watermark state file) is unchanged
  And the live email-delta-capture cron job keeps running against the same
  real, already-registered script paths, with no redeployment step beyond
  copying the updated file contents to those same real locations
```
<!-- AC-ID: REQ-SB-87-US-02-AC-05 -->

### Scenario 6: Migration is retrofit-safe against the real, already-populated vault
```gherkin
Given the real vault's own already-captured Threads, RawMessages, Person
  notes, and file companions from before this migration
When the migrated scripts run against that same real, live vault
Then every already-existing Thread/RawMessage/Person/File note is found and
  topped up correctly -- no duplicate created, no existing content lost or
  overwritten
```
<!-- AC-ID: REQ-SB-87-US-02-AC-06 -->

### Scenario 7: A disallowed section write is still refused
```gherkin
Given a caller that is not on a section's own allow-list (e.g. an attempt to
  machine-write ## Personal Notes)
When that write is attempted through the migrated code path
Then it is refused with the same kind of real, explicit error vault_lib.py's
  own SectionWriteNotAllowed produces today -- never silently allowed just
  because the underlying engine changed
```
<!-- AC-ID: REQ-SB-87-US-02-AC-07 -->

## Affected Screens

None — backend only (Hermes-Provisioning Skill scripts; no `src/frontend` or
`html-prototype/` surface).

## Dependencies

- **Blocked by:** [[REQ-SB-87-US-01]] — the `thread`/`raw-message` templates
  and the resynced `vault_manager.py` must exist first.
- **Blocks:** [[REQ-SB-87-US-03]] — the new Capture-time classification/
  noise-skip judgment step is layered onto this story's own already-migrated
  `ingest_email.py` flow, not built against the soon-to-be-retired
  `vault_lib.py` code path.
- **Related:** `link_meeting_to_thread.py` (meeting-capture's own precedent for
  what stays hand-written when linking across note kinds); `create-companies-
  partners`'s own `retag_threads_by_participant_company` (a later Enrich-pass
  consumer of Thread notes this migration must not disturb); [[REQ-SB-87-US-04]]
  / [[REQ-SB-87-US-05]] (the sibling Enrich-side mechanics migration + new
  capability, a different Skill's own scripts, no shared files with this
  story).
- **External:** none.

## Constraints

- Every existing hand-written business-logic function stays hand-written —
  only the underlying note read/create/find/section-write mechanics move to
  `vault_manager.py`: `ensure_bare_person_note` (dedup key, ignore list, GAL
  fields), the section-ownership guard's real per-caller allow-lists,
  `write_file_companion`/`write_file_link_companion`, `clean_subject`,
  `person_note_dedup_key`/`find_person_note_path`.
- `outlook_lib.py`, `list_recent_emails.py`, and `run_full_capture.py`/
  `run_delta_capture.py`'s own orchestration logic (paging, watermark,
  subprocess dispatch) are NOT part of this migration's own `## Files to
  Modify` — only the internals of the five write-mechanics scripts change;
  their own external CLI contract does not.
- This is a live, daily-use production pipeline (`email-delta-capture` cron)
  the operator depends on — verification must include a real run against the
  real, already-populated vault, not only a scratch vault, per this
  codebase's own established "retrofit-safe against real, pre-existing
  production data" precedent (`REQ-SB-73`/`74`/`79`/`86` series).
- Deploy the migrated scripts to the real, active Hermes profile location(s)
  this Skill is actually running from (not just the `Hermes-Provisioning/`
  repo copies), per this project's own standing manual-deploy pattern
  (`[[feedback_deploy_hermes_provisioning_manually]]`).
- Never run more than one capture job concurrently against the same vault
  during verification — `SKILL.md`'s own documented pitfall (a real Windows
  file-write race on attachment bytes, found live 2026-08-21).
- **Proving-phase rollout (operator, 2026-09-01, resolved MUST-FLAG trigger
  1/5 — see Notes):** the migrated scripts are the SAME code path
  regardless of target — no separate "test mode" branch. Iteration happens
  by pointing `--vault-path` at a scratch vault directory (a fresh copy,
  or a scratch vault seeded from a real ~100-email sample pulled via the
  already-real `list_recent_emails.py`/`run_full_capture.py` paging) and
  tweaking there until every Scenario above passes against that sample.
  Only once satisfied does the live `email-delta-capture` cron job's own
  `--vault-path` argument get pointed at the real vault — the cutover IS
  that one argument change, not a redeploy or a code branch. Scenario 6's
  own real-vault retrofit-safety check happens AFTER the scratch-sample
  proving phase, immediately before cutover, not instead of it.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-87-US-02-T01 | backend | Migrate `ingest_email.py` (Thread create/find + first-RawMessage) | `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/ingest_email.py`, `scripts/vault_manager.py` (new copy) | `REQ-SB-87-US-02-T01-migrate-ingest-email.md` |
| REQ-SB-87-US-02-T02 | backend | Migrate `rename_thread.py` (rename, backlinks, collision suffix) | `.../scripts/rename_thread.py` | `REQ-SB-87-US-02-T02-migrate-rename-thread.md` |
| REQ-SB-87-US-02-T03 | backend | Migrate `capture_attachments.py`/`capture_file_link.py`/`link_person_to_thread.py` | `.../scripts/capture_attachments.py`, `.../scripts/capture_file_link.py`, `.../scripts/link_person_to_thread.py` | `REQ-SB-87-US-02-T03-migrate-attachment-file-person-linking.md` |
| REQ-SB-87-US-02-T04 | backend | Verify orchestration contract unaffected (`run_full_capture.py`/`run_delta_capture.py`) | (verification only — no `## Files to Modify`) | `REQ-SB-87-US-02-T04-verify-orchestration-contract.md` |
| REQ-SB-87-US-02-T05 | backend | Real-vault retrofit-safety verification + live cron cutover | (verification + `--vault-path` cutover, no code changes) | `REQ-SB-87-US-02-T05-real-vault-verification-and-cutover.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- Any change to `summarize-and-tag-threads`'s own Enrich-phase logic
  (summarization, `last_summarized_at`, Customer/Partner company-matching) —
  a separate, later, deliberately untouched pass.
- Any change to `create-companies-partners`'s own `retag_threads_by_
  participant_company` — it reads/writes Thread notes from the outside;
  this story must not change what it can find or how it links, only how
  `email-thread-capture` itself writes.
- Resolving the growing-children architecture question — consumed as-built
  from [[REQ-SB-87-US-01]], not re-litigated here.
- Fixing `email-thread-capture`'s own EXISTING hand-written business logic
  (Person-note dedup, section-ownership mechanics, attachment/file-link
  capture) — scoping for this requirement found no evidence any of THAT is
  actually broken; this remains a mechanics migration, not a bug fix.
  **Revised 2026-09-01:** this bullet originally read as a blanket "no
  business-logic changes anywhere in this Skill" — no longer accurate.
  REQ-SB-87's own expansion adds a genuinely NEW Capture-time business-logic
  step (classify-or-skip judgment + noise definition) to this SAME Skill's
  own scripts, via [[REQ-SB-87-US-03]] — a real, deliberate ADDITION layered
  on top of this story's migrated code, not a "fix" to anything existing and
  not built by this story itself. This story's own five scripts still gain
  zero new business logic; [[REQ-SB-87-US-03]] is the one that does, and it
  is sequenced to depend on this story's own migration completing first.
- The new Capture-time classification/noise-skip judgment step — genuinely
  new business logic, [[REQ-SB-87-US-03]]'s own scope, not this story's.

## Notes

**Prototype parity:** not applicable — this story has no `html-prototype/`
surface (backend-only, no UI).

**MUST-FLAG triggers fired:**
- Trigger 1 (material assumption) — this story assumes a behavior-preserving,
  drop-in mechanics swap is achievable for all five scripts without a
  cron-job outage window; that assumption should be confirmed (or a phased
  parallel-write cutover, mirroring `ingest_meeting.py`'s own precedent,
  explicitly chosen instead) before `/plan-tasks` locks the task breakdown.
- Trigger 5 (real production risk, oversized-adjacent) — this migrates a
  LIVE, daily-use pipeline backing a cron job the operator depends on, with
  real prior incidents in this exact area (the 2026-08-21 concurrent-capture
  file-write race; the 2026-09-01 gateway-down incident that prompted this
  requirement). The human should weigh in on the migration/verification
  approach (parallel-path proof-then-cutover vs. direct in-place edit plus
  live real-vault verification) before tasks are locked.

**Resolved 2026-09-01 (operator, verbatim):** "Lets Build a small sample
of 100 Emails to a new Pipeline we keep tweaking it when done we change
the OutputDirectory and move on" — a phased, parallel-path rollout
(matching the recommended option), made concrete: prove the migrated
scripts against a real ~100-email sample in a scratch vault (distinct
`--vault-path`), iterate there, then cut over the live cron job's own
`--vault-path` to the real vault once satisfied. See the new Constraints
entry above for the full mechanism. `gate` set to `clear`; the original
trigger analysis above is preserved, not deleted.

gate: clear 2026-09-01 — resolved per the operator's own real rollout
decision, see Notes above.

**Revision breadcrumb (2026-09-01, analyst, same-day re-spec against REQ-SB-87's
own same-day scope expansion):** Scenario 4 and Non-Goals narrowed to be
precise about what "no business-logic changes" actually still means once the
requirement's own expanded scope adds real new Capture-time business logic to
this SAME Skill via a sibling story ([[REQ-SB-87-US-03]]) — this story's own
five scripts and their own ACs are otherwise UNCHANGED; nothing in the
originally-resolved rollout decision or Constraints needed to change. `gate`
stays `clear` — this revision resolves an internal-consistency staleness, it
does not introduce a new unresolved trigger.

**Architecture scope (2026-09-01, architect):** `architecture.md` → §Canonical
`vault_manager.py` Source & Deployment, §`vault_manager.py` Engine
Extensions — Dynamic Children & Per-Caller Access (`REQ-SB-87-US-01`,
`ADR-017`) — this story's own five scripts consume the resynced engine +
Thread/RawMessage templates as-built by `US-01`; no new architecture of
this story's own. `ADR-017`'s new per-caller-identity argument requirement
applies to every one of this story's own mutating calls (`create`/
`modify-section`), not just the new `email-thread-capture` copy — sized
into this story's own tasks at `/plan-tasks`.

gate: clear 2026-09-01 — no ADR touched by this story itself; no new
trigger fired at this architect pass.

**Decomposer pass (2026-09-01):** all 7 scenarios locked
(`REQ-SB-87-US-02-AC-01`..`AC-07`), 5 tasks created (`T01`..`T05`, a
straight chain: `T01 → T02 → T03 → T04 → T05`, `T01` depends on
`REQ-SB-87-US-01-T05`). Every task's own `## Tests` names the operator's
own real ~100-email scratch-vault proving-phase sample (distinct
`--vault-path`) explicitly, per the Constraints' rollout mechanism — `T05`
is the one and only task that performs Scenario 6's real-vault retrofit
check and the actual `--vault-path` cutover, and only after `T01`-`T04`
have already passed against the scratch sample. Every locked AC has at
least one AC-tagged verification step, `depends_on` is acyclic — `status`
advances `Draft → Ready`, all 5 tasks written at `status: Ready`. `gate`
left untouched (`clear`, already resolved by the operator).
