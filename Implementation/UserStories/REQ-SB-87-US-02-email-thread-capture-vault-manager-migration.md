---
id: REQ-SB-87-US-02
title: Migrate email-thread-capture's write mechanics onto vault_manager.py
requirement_ids: [REQ-SB-87]
requirement_section: "REQ-SB-87: Email Thread Capture — a New, LLM-Driven Pipeline (Classify, Skip Noise, Summarize, Find Pending Actions)"
phase: P1
status: Done
gate: flagged
gate_reason: "Was flagged: live-pipeline migration/verification approach needed a human decision. Resolved 2026-09-01, operator, verbatim: \"Lets Build a small sample of 100 Emails to a new Pipeline we keep tweaking it when done we change the OutputDirectory and move on\" — a scratch-vault-path proving phase (real ~100-email sample, iterate against a distinct --vault-path) before the live cron job's own --vault-path is pointed at the real vault. See Constraints and Notes for the full resolution; original trigger reasoning preserved below, not erased. RE-FLAGGED 2026-09-01: T01 was Blocked -- AC-01 couldn't be fully verified, vault_manager.py's create_dynamic_child() had no way to write a RawMessage's real flat, headerless body. RESOLVED same-day (ESC-061, direct fix): create_dynamic_child() extended with an additive body= flat-body mode, all 84 real deployed copies resynced, T01 completed and marked Done, both its locked ACs verified live. Story stays flagged: one disclosed scope-internal judgement call (RawMessage filename-convention divergence, see T01's own Implementation Log / REVIEW-QUEUE.md) needs human spot-check before T05's own future real-vault cutover. 2026-09-02: T02 (rename_thread.py) also completed and marked Done, AC-03 verified live -- two more disclosed, non-blocking scope-internal judgement calls added (a _slugify authority correctness fix, and a real vault_manager.update()-vs-upsert_frontmatter_key no-op-safety regression found and fixed live), see T02's own Implementation Log / REVIEW-QUEUE.md / MEMORY.md. 2026-09-02: T03 (link_person_to_thread.py/capture_attachments.py/capture_file_link.py) also completed and marked Done, AC-04 (and AC-07's ## Personal Notes half) verified live -- one more disclosed, non-blocking scope-internal judgement call added (a real, silent per-caller-access-control bypass caused by passing '## '-prefixed section names to modify_section, found and fixed live before shipping), see T03's own Implementation Log / REVIEW-QUEUE.md / MEMORY.md."
sprint: "SPRINT-083"
created: 2026-09-01
updated: 2026-09-02
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
- **Added 2026-09-02 (PRD REQ-SB-87 point 6 + its own "Second expanded-scope
  raised-context pass," operator-confirmed):** two real, silently-conflated
  signals need real, explicit fields, verified directly against the current
  `outlook_lib.py` (not assumed from the PRD's own restated version):
  - `_list_folder_mail` is called twice by `list_recent_mail` — once against
    `_OL_FOLDER_INBOX`, once against `_OL_FOLDER_SENT_MAIL` — then the two
    result lists are concatenated and re-sorted by `received`
    (`merged = sorted(inbox_results + sent_results, ...)`). Neither
    `_list_folder_mail`'s own per-item dict nor the merge step stamps which
    folder a message came from — confirmed live, no `direction` (or
    equivalent) key exists anywhere in the returned shape today.
  - `_resolve_attendees` filters `item.Recipients` via
    `recipient.Type not in (_OL_MEETING_RECIPIENT_REQUIRED,
    _OL_MEETING_RECIPIENT_OPTIONAL): continue` — these constants are named
    for Outlook's MEETING-attendee enum (`olMeetingRequired=1`/
    `olMeetingOptional=2`), reused for mail only because they happen to share
    integer values with mail's own `olTo=1`/`olCC=2`. The returned attendee
    dict (`{"name", "email", "department", "job_title", "company_name"}`)
    carries no marker for which of the two a given recipient actually was.
    (BCC — Outlook's `olBCC=3` — is already excluded by this same filter,
    unchanged behavior, not part of this story's own new scope.)
  - Both fields must be threaded from this real per-folder/per-recipient read
    all the way through `list_recent_emails.py` (a pure pass-through today —
    no field remapping, so no logic change there, only its own docstring's
    field-list documentation) to `ingest_email.py`'s own RawMessage
    frontmatter write. See Scenario 8/Scenario 9 below and the revised
    Constraints entry on `outlook_lib.py`'s own scope.

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

### Scenario 8: RawMessage notes carry a real direction field distinguishing sent from received (added 2026-09-02)
```gherkin
Given one email read from the Inbox folder and a separate email read from the
  Sent Mail folder, whether they belong to the same or different
  conversation_ids
When ingest_email.py creates or resolves the RawMessage note for each
Then the Inbox-sourced RawMessage's own frontmatter carries a real direction
  value of "received"
  And the Sent-Mail-sourced RawMessage's own frontmatter carries a real
  direction value of "sent"
  And this value is threaded through unchanged from outlook_lib.py's own
  per-folder read (the folder each message was actually queried from) —
  never inferred afterward from sender_email or participant matching
```
<!-- AC-ID: REQ-SB-87-US-02-AC-08 -->

### Scenario 9: RawMessage recipients carry a real type distinguishing To from CC (added 2026-09-02)
```gherkin
Given an email with at least one To recipient and at least one CC recipient
When ingest_email.py creates the RawMessage note and records its recipients
Then each recipient's own real recipient type (To or CC) is preserved and
  written into the RawMessage note's own real data, distinguishable per
  individual recipient — never flattened into one undifferentiated list with
  no way to tell them apart
  And this value comes from outlook_lib.py's own real per-recipient
  Type read at the Outlook COM layer, not a re-derived guess made downstream
```
<!-- AC-ID: REQ-SB-87-US-02-AC-09 -->

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
- **Blocked by (added 2026-09-02, real cross-story sequencing, PRD point 8):**
  [[REQ-SB-87-US-03]] — specifically, **this story's own `T05`** (the
  real-vault retrofit + live cron cutover) may not run until
  `REQ-SB-87-US-03`'s own classification-writing capability exists and is
  verified working. The operator's own instruction: the real 100-message
  retrofit `T05` performs must write a real classification value into every
  retrofitted message's frontmatter, even where the ultimate decision is
  "keep everything" — that capability is `REQ-SB-87-US-03`'s to build, not
  `T05`'s. This is a genuine new dependency edge, not just an ordering
  preference — `/plan-tasks` should record it as a real `depends_on` from
  `REQ-SB-87-US-02-T05` onto whichever `REQ-SB-87-US-03` task actually
  delivers working classification (not merely the noise-definition artifact
  or engine foundation). This does not affect `T01`-`T04` (already `Done`) or
  `T05`'s own pre-existing dependency on `T01`-`T04` completing first.
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
  **Revised 2026-09-02 (narrow carve-out for Scenario 8/Scenario 9 only):**
  `outlook_lib.py` now DOES enter this story's own real scope, narrowly — the
  real `direction` and recipient-type fields can only originate at the
  per-folder Outlook read itself (`_list_folder_mail`'s two separate
  Inbox/Sent-Mail calls; `_resolve_attendees`'s own `recipient.Type` read),
  confirmed by reading the real, current code directly (see Context above).
  This is an additive field-plumbing change only — no restructuring of
  `outlook_lib.py`'s own paging, restriction, or attachment logic.
  `list_recent_emails.py` needs no logic change (it already passes
  `list_recent_mail`'s dict straight through to JSON unmodified) — only its
  own module docstring's field-list documentation needs updating to match.
  `run_full_capture.py`/`run_delta_capture.py`'s own orchestration logic
  stays untouched, per the original constraint above. `ingest_email.py`
  (`T01`, already `Done`) will need a real, additive extension — not a
  rebuild — to persist these two new fields into the RawMessage's own real
  data; this reopens `T01`'s own file, not its already-verified `AC-01`/
  `AC-02` scope. Left to `/plan-tasks` whether this lands as an extension of
  the existing `T01` task or a new task.
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
| REQ-SB-87-US-02-T06 | backend | Thread `direction`/recipient-type fields through to RawMessage frontmatter | `.../scripts/outlook_lib.py` (additive per-folder/per-recipient stamps), `.../scripts/list_recent_emails.py` (docstring only), `.../scripts/ingest_email.py` (additive `frontmatter=` extension) | `REQ-SB-87-US-02-T06-raw-message-direction-and-recipient-type.md` |

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

**Coder pass, T01 (2026-09-01):** `T01` built and live-verified Thread
resolve/create + the `last_message_at` advances-only stamp against a real
~100-email scratch-vault sample — zero regressions vs. a same-sample
pre-migration baseline (byte-identical RawMessage/Person notes, matching
Thread frontmatter/section shape). RawMessage creation itself could NOT be
migrated: `vault_manager.py`'s `create_dynamic_child()` has no way to write
a flat, headerless real email body, and closing that gap needs a file
outside `T01`'s own `## Files to Modify` (the Thread `Template.json`, or
the canonical engine + all 82 deployed copies) — escalated (`ESC-061`,
`REVIEW-QUEUE.md`) rather than silently forked or routed around. `T01`
marked `Blocked`; `AC-01` not verified as fully passing, `AC-02` passes
live. `status`/`gate` on this story bumped to `In Progress`/`flagged` to
carry this forward — see `T01`'s own Implementation Log for full detail.

**Coder pass, T01 follow-up (2026-09-01, same day):** `ESC-061` resolved
as a direct fix (operator-directed, no new story, per this project's own
`BUG-041` precedent): `create_dynamic_child()` extended with an additive
`body=` flat-body mode (canonical `Hermes-Provisioning/shared/
vault_manager.py`, new automated tests), all 84 real deployed copies
resynced (11 repo + 73 live Hermes profile), `ingest_email.py`'s
RawMessage creation migrated. `T01` re-verified live against a fresh real
~100-email scratch-vault sample -- both locked ACs (`AC-01`, `AC-02`) now
pass with a real positive result (156/156 Person notes and 100/100
RawMessage bodies byte-for-byte identical to a true pre-migration
baseline; 0 real frontmatter mismatches beyond already-accepted additive
keys; idempotency and advances-only `last_message_at` reconfirmed).
`T01` marked `Done`. One disclosed, non-blocking scope-internal judgement
call carried forward for human spot-check: the RawMessage note's own
on-disk filename now follows `create_dynamic_child()`'s generic
ingestion-date-based naming, not `vault_lib`'s bespoke received-date-based
one (content and idempotency both unaffected) -- see `T01`'s own
Implementation Log and `REVIEW-QUEUE.md`. `T02`-`T05` remain `Ready`, not
started by this pass. Story `status` stays `In Progress`.

**Coder pass, T02 (2026-09-02):** `T02` (`rename_thread.py`) built and
live-verified against a fresh real scratch-vault sample (the prior sample
from `T01` no longer existed on disk; re-pulled fresh, same technique).
Thread resolution now `vault_manager.find_by_id`; `thread_name`/backlink/
`source_thread` updates now `vault_manager.update`; the physical directory
rename and `sha256(conversation_id)[:8]` collision-suffix disambiguation
stay hand-written, byte-for-byte unchanged. `AC-03` (this task's own one
locked AC) verified live: real-Thread relabel + backlink updates, an
engineered real same-stem collision (including a stem landing exactly at
the 80-char cutoff) correctly disambiguated, and the file-companion
`is_file()` guard preserved. **A real regression was found and fixed live
during verification**, within this task's own single file: `vault_manager.
update()` lacks `upsert_frontmatter_key()`'s own no-op safety on a
fence-less file, which the pre-existing `.md`-named-attachment
companion-directory collision case can trigger — fixed with an explicit
frontmatter-fence guard at the call site (generalized as a `MEMORY.md`
Constraint entry for `T03`'s own upcoming migration of
`capture_attachments.py`/`capture_file_link.py`, which write into this
same `files/` shape). `T02` marked `Done`, `gate: flagged` for two
disclosed, non-blocking scope-internal judgement calls (see `T02`'s own
Implementation Log / `REVIEW-QUEUE.md`). `T03`-`T05` remain `Ready`, not
started by this pass. Story `status` stays `In Progress`.

**Coder pass, T03 (2026-09-02, interrupted mid-task by a machine restart,
resumed same day):** `T03` (`link_person_to_thread.py`/`capture_
attachments.py`/`capture_file_link.py`) built and live-verified against a
fresh real scratch vault seeded with a real copy of the live `thread/
Template.json`, re-run for real after the restart per the coordinator's
explicit instruction not to trust any pre-restart partial state. Thread
resolution in all three now `vault_manager.find_by_id`; `## Related`
(`link_person_to_thread` only)/`## Files` (`capture_attachments`/
`capture_file_link` only) accumulation now `vault_manager.
get_section_content`/`modify_section(..., caller=...)`, replacing `vault_
lib.py`'s own `_CALLER_ALLOW_LISTS` guard with the Thread template's own
`allowed_callers` declarations. `ensure_bare_person_note`/`write_file_
companion`/`write_file_link_companion` stay hand-written, byte-for-byte
unchanged. `AC-04` (this task's own main locked AC) and the `## Personal
Notes` half of `AC-07` verified live: a real sender linked into `##
Related` (idempotent re-run confirmed); a real attachment captured into
`## Files` with byte-exact content; a URL-only file link captured into
`## Files` (idempotent re-run confirmed); every wrong-caller write against
the other script's own exclusive section (including `## Actions`) refused
with a real `VaultManagerError`, content unchanged; `## Personal Notes`
refused to all three callers and to no caller, unconditionally; a real CLI
smoke call confirmed the subprocess entry point still works. `T02`'s own
flagged frontmatter-fence-vs-raw-attachment-bytes risk explicitly
re-verified and confirmed NOT to reproduce here (an engineered `.md`-named
collision attachment stayed byte-for-byte unchanged across every
subsequent section write) — these three scripts never glob over `files/`,
unlike `rename_thread.py`'s own companion-backlink loop. **A real bug was
found and fixed live, before shipping:** an initial draft passed `"## "`-
prefixed section names to `modify_section`, which silently disabled its
own per-caller access check (a SILENT security hole — the write succeeded
with no error, defeating `ADR-017`'s whole per-caller restriction) rather
than raising; fixed to the bare form matching `apply_thread_review.py`'s
own convention, caught before the task reached `Done`. Generalized as a
`MEMORY.md` Constraint entry. `T03` marked `Done`, `gate: flagged` for this
one disclosed, non-blocking scope-internal judgement call (see `T03`'s own
Implementation Log / `REVIEW-QUEUE.md` / `MEMORY.md`). `T04`-`T05` remain
`Ready`, not started by this pass. Story `status` stays `In Progress`.

**Coder pass, T04 (2026-09-02):** `T04` (verify `run_full_capture.py`/
`run_delta_capture.py`'s own orchestration contract is unaffected) built
zero code — verification only, as scoped — and live-verified against a
fresh real scratch vault, real Outlook mail (707 real Inbox+Sent items).
`run_full_capture.py` run to genuine natural completion twice (10 pages/
499 emails/247 Threads first run; fully idempotent second run, `.md`
count unchanged at 1126, both real `exit 0` directly captured) — same
real CLI/JSON/exit-code contract as before this migration.
`run_delta_capture.py` run twice back-to-back: pass 1 bootstrapped its
documented 2-day lookback and wrote the real watermark state file for the
first time in its unchanged shape; pass 2 (immediately after) correctly
picked up zero new emails, watermark unchanged, real `exit 0` — direct,
positive proof of correct watermark-based incremental pickup with no
duplicate processing. `git diff` confirmed zero content changes to
either orchestrator file. `AC-05` (this task's own one locked AC)
verified live in full. One disclosed, non-blocking clarification (not a
defect): `run_full_capture.py` itself has never written the watermark
state file (only `run_delta_capture.py` does) — the task's own
Tests-step-1 prose read as if both do; confirmed pre-existing, unchanged
behavior, generalized as a `MEMORY.md` Constraint entry. `T04` marked
`Done`, `gate: clear` — no new trigger fired. `T05` remains `Ready`, not
started by this pass. Story `status` stays `In Progress`.

**Analyst pass (2026-09-02, real new scope added — PRD `REQ-SB-87` point 6 +
its own "Second expanded-scope raised-context pass," operator-confirmed
verbatim):** two new untagged Gherkin scenarios added (Scenario 8: real
`direction: "sent" | "received"` field; Scenario 9: real recipient
type/`is_cc` field distinguishing To vs. CC) — both verified directly against
the real, current `outlook_lib.py` (not assumed from the PRD's own restated
version; see Context above), not decomposer-locked (no `AC-ID` tags — that
remains the decomposer's job at the next `/plan-tasks` pass). Constraints
revised to bring `outlook_lib.py` narrowly into this story's own scope for
these two additive fields only (previously excluded entirely). Dependencies
updated with a new, real cross-story sequencing edge: this story's own `T05`
(real-vault retrofit + cutover) is now also blocked by
[[REQ-SB-87-US-03]]'s own classification-writing capability existing and
being verified first (PRD point 8) — a genuine new `depends_on` edge for
`/plan-tasks` to record at the task level, not merely an ordering preference.
This does not reopen `T01`-`T04`'s own already-locked/verified `AC-01`-`AC-06`
— those stay exactly as decomposed and verified; `T01`'s own file
(`ingest_email.py`) will need a real, additive extension (not a rebuild) once
`/plan-tasks` adds tasks for the two new scenarios. No new MUST-FLAG trigger
fired by this addition — these are concrete, already-resolved-by-the-operator
business rules (PRD's own verbatim quotes), not open interpretation
questions; `gate` stays `flagged` exactly as it already was (the two
pre-existing, unrelated disclosed scope-internal judgement calls from `T01`-
`T03` still await human spot-check before `T05`'s own cutover — unaffected
by this addition).

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

**Architect pass (2026-09-02, Scenario 8/Scenario 9 reviewed):** confirmed
directly against `vault_manager.py`'s real, current implementation — no
new ADR and no `Template.json` schema change are needed for the new
`direction`/recipient-type fields. Both `create()` (line ~964-965) and
`create_dynamic_child()` (line ~1125-1127) build `full_frontmatter` as
`dict(frontmatter_defaults)` then unconditionally `.update(frontmatter or
{})` with whatever the caller passes at call time — there is no allow-list
or schema restriction anywhere in the engine limiting frontmatter keys to
what a template's own `frontmatter_defaults` declares. The RawMessage
dynamic-child spec (`thread/Template.json`, confirmed read directly) only
declares `"frontmatter_defaults": {"type": "RawMessage"}` today, but that
is a DEFAULT, not a ceiling — `ingest_email.py`'s own already-planned
additive extension (flagged as needed in this story's own Constraints,
2026-09-02 revision) can pass `direction`/recipient-type straight through
in its `frontmatter=` argument with zero engine or template change. This
is a concrete, additive DATA-plumbing change (new keys threaded from
`outlook_lib.py` through to a `create_dynamic_child()` call's own
`frontmatter=` dict), exactly as the operator's own expectation framed it —
not a new structural/engine decision, and `ADR-017`'s already-Accepted
dynamic-child-primitive design is unaffected (it never claimed
`frontmatter_defaults` was an exhaustive key list). No `architecture.md`
edit made — nothing structural changed. Existing Architecture scope
(§Canonical `vault_manager.py` Source & Deployment, §`vault_manager.py`
Engine Extensions — Dynamic Children & Per-Caller Access, `ADR-017`) still
fully bounds this story, including its new Scenario 8/9.

gate: clear 2026-09-02 — this architect pass: no ADR touched, no
assumption made, no architecture.md edit needed for Scenario 8/9. The
story's own overall `gate: flagged` (three pre-existing, unrelated
disclosed scope-internal judgement calls from `T01`-`T03` awaiting human
spot-check before `T05`'s cutover) is untouched and unresolved by this
pass.

**Decomposer pass (2026-09-02, Scenario 8/Scenario 9 locked):** both new
scenarios locked (`REQ-SB-87-US-02-AC-08`, `REQ-SB-87-US-02-AC-09`), text
unchanged from the analyst's own already-precise wording (already verified
directly against the real `outlook_lib.py`, per the architect's own
confirmation no re-tightening was needed). Since `T01` (the task that owns
`ingest_email.py`'s RawMessage frontmatter write) is already `Done`, per
hard rule 1 (specs are append-only; a `Done` task's own scope is never
retroactively edited) this additive work is NOT folded into `T01` — a new
task, `T06`, was created instead, covering the real, additive plumbing:
`outlook_lib.py`'s per-folder `direction` stamp + per-recipient `type`
stamp (both additive, no restructuring of paging/attachment logic, per the
story's own narrow 2026-09-02 Constraints carve-out), `list_recent_emails.py`'s
docstring-only update (zero logic change — it already passes the dict
through unmodified), and `ingest_email.py`'s own additive `frontmatter=`
extension to `create_dynamic_child()` (zero engine/template change needed,
per the architect's own confirmation `create()`/`create_dynamic_child()`
already accept arbitrary extra frontmatter keys). `T06` depends only on
`T01` (documents that it extends `T01`'s own already-Done RawMessage
output file; `T01` being `Done` does not block `T06` from being built —
recorded for lineage/read-order clarity, not execution ordering).

**Real cross-story dependency edge recorded (2026-09-02):** per this
story's own already-disclosed 2026-09-02 Dependencies entry (PRD point 8,
analyst-added) — `T05` (the real-vault retrofit + live cron cutover) may
not run until `REQ-SB-87-US-03`'s own classification-writing capability
exists and is verified working. Reading `REQ-SB-87-US-03`'s own 5 task
files directly: `REQ-SB-87-US-03-T03` ("Wire the classify-or-skip relay
call into `ingest_email.py`") is the task that actually builds AND
individually, live-verifies the classification-WRITING mechanism (its own
`[REQ-SB-87-US-03-AC-02]` Tests step already confirms a real Thread's
frontmatter carries a real classification value) — `REQ-SB-87-US-03-T04`
only adds JSON-summary reporting (no writing capability of its own) and
`REQ-SB-87-US-03-T05` is a combined proving/retune pass, not where the
capability first exists. `T03` is therefore the more accurate target than
`T05` for "classification capability exists and is verified working."
`REQ-SB-87-US-02-T05`'s own `depends_on` frontmatter updated to
`[REQ-SB-87-US-02-T04, REQ-SB-87-US-02-T06, REQ-SB-87-US-03-T03]` — `T06`
added additionally (decomposer's own judgement call, not explicitly
requested but a real consequence of the same reasoning): `T05` deploys and
cuts over the SAME `ingest_email.py` file `T06` also edits, so the real
production cutover should not run ahead of `T06`'s own additive fields
landing in that same file. This is a genuine cross-sprint edge
(`SPRINT-083` → `SPRINT-084`, via the `REQ-SB-87-US-03-T03` leg) — already
disclosed as a real, expected dependency in both stories' own 2026-09-02
Dependencies sections (not a new discovery this pass); left to
`/plan-sprints`'s own `depends_on_sprints` handling, not re-flagged here.
`gate` left untouched (`flagged`, unchanged from the prior architect pass
— no new trigger fired by this addition).

**Coder pass, T06 (2026-09-02):** `T06` (`direction`/recipient-type fields
into RawMessage frontmatter) built and live-verified against a fresh real
scratch vault (`C:\scratch-sb87t06\`, seeded with a real copy of the live
`thread/Template.json`), a real ~20-email sample pulled via the unmodified
`list_recent_emails.py` against live Outlook. `outlook_lib.py`'s
`_list_folder_mail` now stamps a real `direction` (`"received"`/`"sent"`)
at the point of the real per-folder read; `_resolve_attendees` now stamps
a real per-recipient `type` (`"to"`/`"cc"`) read directly from
`recipient.Type` — both purely additive. `list_recent_emails.py`'s
docstring updated, zero logic change (`git diff` confirms). `AC-08`/`AC-09`
(this task's own two locked ACs) verified live in full: a real Inbox email
(mixed To/CC recipients) and a real Sent Mail email, ingested via the
migrated `ingest_email.py`, both produced correct on-disk RawMessage
frontmatter read back directly via `vault_manager.read_note`; re-running
both confirmed zero regression to `T01`'s own `AC-02` idempotency scope.
**A real bug was found and fixed live before shipping:** the task's own
illustrative one-list `recipients: [{"email", "type"}]` frontmatter shape
silently parsed back as an EMPTY list on read — `vault_manager.py`'s own
hand-rolled, non-YAML frontmatter writer only round-trips scalars and
homogeneous string lists, not a list of dicts. Resolved within `T06`'s own
`## Files to Modify` (`ingest_email.py` only): split into two flat
`to_recipients`/`cc_recipients` email-string lists, each recipient's own
type structurally distinguishable by which list it's in — confirmed
round-tripping correctly live. Generalized as a new `MEMORY.md` Constraint
entry. `T06` marked `Done`, `gate: flagged` for two disclosed, non-blocking
findings: (1) the frontmatter shape deviation above, and (2)
`run_full_capture.py`/`run_delta_capture.py` (out of `T06`'s own scope, not
touched) don't yet forward the new `direction` field in their own
`ingest_payload` construction — `recipients`/`type` already flows through
both unchanged, but `direction` needs a one-line addition to each
orchestrator before `T05`'s own live cutover — see `T06`'s own
Implementation Log / `REVIEW-QUEUE.md` / `MEMORY.md`. `T05` remains
blocked on `REQ-SB-87-US-03-T03` (a different sprint) as already recorded;
not started by this pass. Story `status` stays `In Progress`.

**Coder pass, T05 (2026-09-02, operator: "Run the retrofit now"):** `T05`
(real-vault retrofit-safety verification + live cron cutover) built and
verified. Confirmed `T04`/`T06`/`REQ-SB-87-US-03-T03` all `Done` first.
Closed the last disclosed pre-cutover gap (the orchestrator
`direction`-forwarding one-liner, `T06`'s own flagged finding). Found and
fixed TWO real bugs live, before/during the real retrofit, both within
`ingest_email.py`'s own already-open file scope: (1) a genuine
Thread-duplication risk — `find_by_id` cannot resolve ANY real,
pre-migration Thread (no `id` field on old content, and `thread/
Template.json`'s own `on_existing_title: "always_new"` gives `create()`
no title-collision safety net either); fixed with the same
"mint-and-backfill on first touch" pattern `REQ-SB-87-US-04-T01`
established, via the already-imported, unchanged `vault_lib.
resolve_thread_directory`; (2) a Unicode `UnicodeEncodeError` crash on
`main()`'s own final `print()` whenever a real subject/body carries a
character outside cp1252 (the SAME bug class `list_recent_emails.py`
already fixed for itself 2026-08-24) — fixed identically. Both verified
live (scratch vault first, then the real vault) before/during the real
work; see `MEMORY.md` for both. Deployed the five migrated scripts, both
orchestrators, and a fresh `vault_manager.py` copy to all 27 real active
Hermes profile locations (the one production/cron-facing location plus
all 26 per-profile copies), SHA-256-confirmed byte-identical.
`[REQ-SB-87-US-02-AC-06]` verified live against the REAL vault: two
known real Threads re-ingested idempotently (only the additive `id`
backfill changed, `diff`-confirmed); a real ~100-message sample
retrofitted — 94 already-existing (zero relay calls, zero duplicates,
Thread count +5 exactly matching the 5 genuinely-new non-noise
captures), 6 genuinely new (5 captured with real classification, 1
correctly skipped as noise), 0 Sent items incorrectly skipped.
`[REQ-SB-87-US-02-AC-05]` re-confirmed against the real vault (exit 0,
unchanged JSON/watermark contract). Cutover confirmed via a real,
manually-triggered `email-delta-capture` agentic cron run (not just a
direct script call) — real per-run output file confirms success on the
newly-deployed code. `T05` marked `Done`, `gate: flagged` for 3
disclosed scope-internal judgement calls (the two live bug fixes plus
the all-27-locations deploy scope), see `T05`'s own Implementation Log /
`REVIEW-QUEUE.md` / `MEMORY.md`. **All 6 tasks (`T01`-`T06`) now `Done`,
all 9 locked ACs (`AC-01`-`AC-09`) verified live with a real positive
result. Story `REQ-SB-87-US-02` moves `In Progress → Done`.**
