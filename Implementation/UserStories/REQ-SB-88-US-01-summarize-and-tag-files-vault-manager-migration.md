---
id: REQ-SB-88-US-01
title: Migrate summarize-and-tag-files' write mechanics (apply_file_review.py) onto vault_manager.py + give it a real cron job
requirement_ids: [REQ-SB-88]
requirement_section: "REQ-SB-88: Close the Remaining `vault_manager.py` Migration Gaps — Attachment Summarization + Opportunity Linking"
phase: P1
status: Done
gate: flagged
gate_reason: "T04's own AC-06 skip-rule sub-clause verified as unreliable under the real, scheduled job (4/15 real Files re-processed in its second run) -- job paused pending human decision, see REVIEW-QUEUE.md / Implementation Log of REQ-SB-88-US-01-T04"
sprint: SPRINT-085
created: 2026-09-02
updated: 2026-09-02
---

# REQ-SB-88-US-01 — Migrate summarize-and-tag-files' Write Mechanics onto vault_manager.py + Give It a Real Cron Job

## Story

**As** the operator whose captured email attachments never get summarized today
**I want** `apply_file_review.py`'s own hand-rolled read/write primitives (`read_note`,
`merge_tags`, `insert_body_section_if_missing`/`read_body_section`/
`replace_body_section`) replaced with calls through `vault_manager.py`'s shared,
already-proven engine, and a real recurring/batched cron job provisioned for this
Skill (none exists today)
**So that** File-note Summary/tag/Files-log writes go through the SAME one canonical
engine every other migrated Skill already uses — REQ-SB-87 point 7's own binding
principle, "never a second, bespoke write path" — and the real ~80-file captured
backlog actually gets summarized on a recurring basis instead of relying on someone
remembering to run this Skill manually, without changing any of its own already-
working real per-file judgment.

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-88*, Finding 1 + "Real scope" points 1-2.
- **Real diagnosis performed directly against the live code this session, not
  assumed:** `apply_file_review.py`
  (`Hermes-Provisioning/skills/company-review/summarize-and-tag-files/scripts/
  apply_file_review.py`, 396 lines) has its OWN, separate, fully duplicated
  `read_note`/`merge_tags`/`insert_body_section_if_missing`/`read_body_section`/
  `replace_body_section` primitives — near byte-identical in shape to
  `apply_thread_review.py`'s own pre-migration copy — and has **zero**
  `vault_manager.py` presence anywhere in its own `scripts/` folder (confirmed via
  `Glob`: only `apply_file_review.py` and `render_pptx_slide_win32.py` exist there).
  It never even had a copy deployed, unlike `track-opportunities` ([[REQ-SB-88-US-02]]).
- **Real cron gap confirmed live (per PRD's own audit) — no job of any kind (enabled,
  disabled, or otherwise) exists for this Skill**, unlike `job4-summarize-tag-threads`
  which exists disabled with a real repeat-budget history. The operator's own
  recollection ("at some point this was happening") plus SKILL.md's own stated scale
  ("209 Threads produced roughly 80 captured files total") ground this story's cron
  scenario in a real, bounded backlog size, not a hypothetical one.
- **Real functions confirmed by direct read, grounding what stays hand-written vs.
  what moves:**
  - `apply_file_review()` — the main entry: resolves companies, writes `## Summary`,
    merges tags, updates the parent Thread's `## Files` line. This is the mechanics
    this story migrates.
  - `build_company_index()`/`resolve_companies()` — identical contract to
    `apply_thread_review.py`'s own copy (matches a Customer/Partner hub note's
    `name`/`aliases`); this is real business logic and stays exactly as-is,
    hand-written, per [[REQ-SB-87-US-04]]'s own precedent for the sibling Skill.
  - `update_files_log_line()` — the idempotent "replace, never duplicate" line-write
    into the parent Thread's own `## Files` section (`- [[file-slug]] --
    <short_summary>`). Threads don't get their own Log/Captures companion files
    (`ADR-042`'s Customer/Partner-only scope-lock), so this line-replace IS this
    Skill's own log mechanism, per SKILL.md's own documented shape — must be
    preserved exactly.
  - `add_file_detail()` (the `--append` mode, 2026-08-22 addition, ported from
    `capture-files`' own `add_file_detail()`) — a deeper follow-up pass into
    `## Details`, with optional already-rendered diagram-image attachment via
    `_attach_images()`/`_unique_sibling_path()`. Uses the SAME hand-rolled section
    primitives as the main flow, so it is in scope for this same migration (one file,
    one set of duplicated primitives, all real write paths through it).
- **Precedent to follow closely:** [[REQ-SB-87-US-04]] (`Done`) migrated
  `apply_thread_review.py` onto `vault_manager.py` for the architecturally near-
  identical sibling Skill in the same company-review sequence — same
  "deploy a fresh `vault_manager.py` copy, migrate write-mechanics call sites one at
  a time, real-vault verify" shape, adapted here for Files instead of Threads. That
  story's own 4 tasks (`T01`-`T04`: migrate summary write + stamping, migrate
  tag-merge + log, converge on template access, scratch-proving + cutover) are the
  closest real template — this story's own tasks should mirror that shape, adapted
  for the absence of a `last_summarized_at` skip-timestamp (Files don't need one;
  SKILL.md's own documented skip rule is "already has a non-empty `## Summary`",
  simpler than Threads' timestamp-based rule) and the addition of the new cron job.
- **Depends on** [[REQ-SB-87-US-01]] (`Done`) — needs the canonical, byte-current
  `vault_manager.py` (`architecture.md`'s own nine-copy deployment inventory) to
  deploy as a brand-new tenth copy into `summarize-and-tag-files/scripts/` — it has
  never had one.
- **Lower production risk than [[REQ-SB-87-US-02]]/[[REQ-SB-87-US-04]]'s own already-
  resolved rollout trigger** — confirmed live this session: unlike `job4-summarize-
  tag-threads`, no cron job of ANY kind currently exists for this Skill, so there is
  no live, currently-firing schedule this migration could silently break. The
  scratch-vault-first verification discipline those stories established is still the
  right default (cheap, no reason to skip it), but the "must not disrupt an already-
  live daily job" urgency that justified those stories' own flagged rollout
  discussion does not apply here — there is nothing live yet to disrupt.
- **Confirmed not in scope** (per PRD's own audit): `files-manager` (a separate,
  live-triggered Agent for ad-hoc uploaded files, its own real use case, zero cron
  job, operator's own words: "We have 2 Jobs One for the file Uploads (Agent) and one
  for skills Emails and Companies" — this Skill is the latter, not `files-manager`).

## Acceptance Criteria

### Scenario 1: Summary write and tag merge continue to work exactly as today
```gherkin
Given a captured File note with an empty ## Summary, and an agent has already read
  its real content and decided on a summary, short_summary, and a list of company
  names it recognized
When apply_file_review.py runs (now writing the File's ## Summary and merging its
  customer/<slug>/partner/<slug> tags via vault_manager.py's write_note/merge_tags
  instead of its own hand-rolled replace_body_section/merge_tags)
Then the File's own ## Summary is written with the agent's real summary content,
  exactly as today
  And every resolved company still gets its customer/<slug> or partner/<slug> tag
  merged onto the File's own tags, exactly as today
  And the script still prints {tags_applied, companies_unresolved,
  files_log_updated} with the same meaning as today
```
<!-- AC-ID: REQ-SB-88-US-01-AC-01 -->

### Scenario 2: An unresolvable company name is reported, never fabricated
```gherkin
Given a company name in the agent's own payload that does not match any real
  Customer/Partner hub note's name or alias
When apply_file_review.py runs
Then that name is reported in companies_unresolved and no hub note is fabricated,
  exactly as today
```
<!-- AC-ID: REQ-SB-88-US-01-AC-02 -->

### Scenario 3: The parent Thread's ## Files line is replaced in place, never duplicated
```gherkin
Given a File note whose own source_thread frontmatter links to a real Thread, and
  that Thread's own ## Files section already has a bare `- [[file-slug]]` line for it
When apply_file_review.py runs and writes the File's summary
Then the Thread's own ## Files line for that file becomes
  `- [[file-slug]] -- <short_summary>`, replaced in place, exactly as today
  And re-running apply_file_review.py with the same short_summary leaves that line
  unchanged (idempotent, no duplicate line added)
```
<!-- AC-ID: REQ-SB-88-US-01-AC-03 -->

### Scenario 4: A deeper Details follow-up pass (with attached images) still works
```gherkin
Given a File already summarized once, with a genuinely new follow-up detail (and
  optionally one or more already-rendered diagram/slide images) to record
When apply_file_review.py --append runs
Then the new details are appended under the File's own ## Details section, never
  overwriting a prior pass, exactly as today
  And any given images are copied into the File's own folder and embedded via
  ![[...]], exactly as today
```
<!-- AC-ID: REQ-SB-88-US-01-AC-04 -->

### Scenario 5: Migration is retrofit-safe against already-summarized real files
```gherkin
Given a real, already-summarized captured File from before this migration
When the migrated apply_file_review.py runs again against it with the same summary/
  short_summary/companies it already carries
Then its own ## Summary, tags, and parent Thread's ## Files line are all left
  byte-identical -- no content lost, no duplicate tag, no duplicate log line
```
<!-- AC-ID: REQ-SB-88-US-01-AC-05 -->

### Scenario 6: A real, bounded cron job now processes the un-summarized backlog
```gherkin
Given roughly 80 real captured Files exist in the vault, most without a ## Summary
  yet, and no cron job of any kind -- enabled, disabled, or otherwise -- currently
  exists for summarize-and-tag-files
When a new cron job is provisioned for this Skill
Then it runs on a real, bounded schedule -- working through the real backlog over
  multiple runs rather than one single unbounded pass, mirroring
  job4-summarize-tag-threads' own real repeat-limited-backfill shape -- rather than
  simply not existing, as today
  And each run only processes Files whose ## Summary is still empty, skipping any
  File a prior run already summarized, exactly as SKILL.md's own documented skip
  rule already requires
```
<!-- AC-ID: REQ-SB-88-US-01-AC-06 -->

## Affected Screens

None — backend only (Hermes-Provisioning Skill scripts; no `src/frontend` or
`html-prototype/` surface).

## Dependencies

- **Blocked by:** [[REQ-SB-87-US-01]] (`Done`) — the canonical, byte-current
  `vault_manager.py` this story deploys as a brand-new copy.
- **Related:** [[REQ-SB-87-US-04]] — the closest real precedent (same migration
  shape, sibling Skill in the same company-review sequence, independent file scope,
  no shared files). [[REQ-SB-88-US-02]] — the sibling migration under the same
  requirement, genuinely independent (different note kind, different Skill folder,
  no shared files).
- **External:** none — no external credential/service is newly required; the cron
  job is provisioned the same way every other Hermes cron job in this vault already
  is.

## Constraints

- Every real per-file judgment (reading actual PDF/DOCX/PPTX/XLSX/image content,
  writing a real prose summary, recognizing companies) stays exactly as-is,
  hand-written, agent-driven — only the mechanical persistence moves to
  `vault_manager.py`.
- `build_company_index()`/`resolve_companies()` (company name/alias matching) stay
  hand-written, unchanged — identical contract to `apply_thread_review.py`'s own
  copy, not re-derived.
- Deploy a NEW `vault_manager.py` copy to `summarize-and-tag-files/scripts/` (it has
  never had one), sourced from the canonical, byte-current version
  ([[REQ-SB-87-US-01]]'s own nine-copy inventory) — not an eleventh diverged copy.
- The Thread's own `## Files` line-replace convention (idempotent, in-place, never a
  separate log file) must be preserved exactly — Threads stay Log/Captures-file-free
  per `ADR-042`'s own scope-lock.
- Verify the migrated script against a scratch-vault sample before either (a)
  running it against the real vault for the first time post-migration, or (b)
  pointing the new cron job's own `--vault-path` at the real vault — same standing
  proving-phase discipline [[REQ-SB-87-US-02]]/[[REQ-SB-87-US-04]] already
  established, applied fresh (no existing live cron to cut over from here).
- Never run this Skill concurrently with `capture-files`/`email-thread-capture`/
  `summarize-and-tag-threads` against the same vault — same documented
  concurrent-capture file-write-race pitfall those Skills' own SKILL.md files
  already warn about.
- The exact cron schedule/repeat-budget shape (how many batched runs, how large a
  batch, what triggers the next one) is a real `/plan-tasks` decision against the
  actual ~80-file backlog size, not decided here — Scenario 6 above states the
  outcome (bounded, backlog-processing, skip-rule-respecting) without prescribing
  the literal mechanism.
- Deploy the migrated script + new cron job definition to the real, active Hermes
  profile location this Skill actually runs from, per this project's own standing
  manual-deploy pattern.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-88-US-01-T01 | backend | Deploy vault_manager.py copy + migrate Summary write + tag-merge | `Hermes-Provisioning/skills/company-review/summarize-and-tag-files/scripts/apply_file_review.py`, `scripts/vault_manager.py` (new copy) | `REQ-SB-88-US-01-T01-deploy-vault-manager-migrate-summary-tag-merge.md` |
| REQ-SB-88-US-01-T02 | backend | Migrate Files-log-line update + Details/`--append` follow-up pass + Thread Template.json `## Files` `allowed_callers` edit | `.../scripts/apply_file_review.py`, `.second-brain/data/Templates/thread/Template.json` | `REQ-SB-88-US-01-T02-migrate-files-log-line-and-details-append.md` |
| REQ-SB-88-US-01-T03 | backend | Scratch-vault proving-phase verification + real-vault retrofit check | (verification only, no code changes) | `REQ-SB-88-US-01-T03-scratch-proving-and-real-vault-retrofit-check.md` |
| REQ-SB-88-US-01-T04 | backend | Provision + deploy the real cron job against the actual ~80-file backlog | Hermes cron config for `summarize-and-tag-files` | `REQ-SB-88-US-01-T04-provision-cron-job.md` |

## Definition of Done

- [~] All acceptance-criteria scenarios pass — AC-01 through AC-05 fully
      pass with a real, live positive result; AC-06 partially passes
      (bounded schedule + real batch processing both PASS; the skip-rule
      sub-clause is disclosed as unreliable under the real, scheduled
      job — see `REQ-SB-88-US-01-T04`'s own Implementation Log and
      `REVIEW-QUEUE.md`)
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, no pytest harness for this Skill yet; verified via scratch-vault + real-vault CLI/cron runs, per each task's own Tests block
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- Any change to `summarize-and-tag-files`' own real per-file judgment (which
  extraction skill to use, how to summarize, which companies it recognizes) — stays
  entirely hand-written/agent-driven, per PRD point 7's own binding principle.
- Fixing a defect in company resolution or the Files-log-line write — none was found;
  this is a mechanics migration + a genuinely new cron capability, not a bugfix.
- `files-manager`'s own separate, live-triggered Agent flow for ad-hoc uploaded
  files — confirmed out of scope by the PRD's own direct audit (a different real use
  case, zero cron job, operator's own explicit "2 Jobs" clarification).
- [[REQ-SB-88-US-02]]'s own `track-opportunities`/`link_opportunity.py` migration —
  a genuinely independent Skill, different note kind, no shared files, its own story.

## Notes

**Prototype parity:** not applicable — this story has no `html-prototype/` surface
(backend-only, no UI).

**Resolution record (2026-09-02, analyst):** two points that could otherwise read as
open were resolved directly, not guessed, so no flag fired:
1. **Whether the cron piece needs its own separate story:** the PRD's own text
   leaves this open explicitly for `/spec` to decide. Resolved by keeping it in the
   SAME story as the mechanics migration — the new cron job invokes the SAME
   migrated script, so splitting them would create an artificial dependency between
   two stories touching the same file, with no independent value in shipping one
   without the other. Mirrors [[REQ-SB-87-US-04]]'s own precedent shape (migration +
   real cutover/cron-facing verification landing in one story, not two).
2. **The exact cron schedule/batch shape:** genuinely left open by the PRD for
   `/plan-tasks` to resolve against the real backlog size — this is ordinary
   implementation latitude (like `vault_manager.py`'s own documented "exact CLI/JSON
   shape is decomposer/coder-level" precedent for `ADR-017`), not a requirement-
   intent ambiguity; Scenario 6 states the required OUTCOME without prescribing the
   mechanism, so no guess was made about what the story itself requires.

Neither point involved fabricating a fact, contradicted another PRD requirement, or
left the story's own acceptance criteria ambiguous — both are ordinary scoping calls
within the discretion the PRD's own text already grants at this stage.

gate: clear 2026-09-02 — no MUST-FLAG trigger fired (no live cron to disrupt, no
Draft/unfinalised requirement, no ADR touched, no contradictory inputs, both
open-ended PRD points resolved directly above rather than guessed).

**Architect pass (2026-09-02):** `architecture.md` §Files-Skill
`vault_manager.py` Migration + Cron Provisioning (`REQ-SB-88-US-01`) — read
`apply_file_review.py`, the deployed `file`/`thread` Template.json files, the
real `files-manager` profile's `cron/` folder (confirmed absent), and the live
`job4-summarize-tag-threads` `cron/jobs.json` entry directly before deciding.

**Architecture scope: §Files-Skill `vault_manager.py` Migration + Cron
Provisioning (`REQ-SB-88-US-01`)** (`Implementation/Architecture/
architecture.md`) — the coder is bounded to this section for both the
mechanics migration and the cron provisioning.

**No new ADR — confirmed, not assumed.** `apply_file_review.py`'s real shape
(`## Summary`/`## Details` writes, tag merge, the Thread's `## Files`
line-replace) is purely additive/consumptive of `ADR-017`'s already-built
`vm.modify_section`/`vm.merge_tags`/`allowed_callers` mechanism: the `file`
Template.json's `## Summary`/`## Details` sections are already open
`machine_write` (no `allowed_callers` key, zero edit needed); the Thread's
`## Files` section needs exactly one Template.json DATA edit (adding
`apply_file_review` alongside the two already-declared callers) — the exact
extension mechanism `ADR-017` already built for this purpose, not a new
engine capability. The new cron job is a first-time Hermes `cron/jobs.json`
entry (confirmed live: `files-manager`'s profile carries no `cron/` folder
today), operational provisioning of the same kind every other real job in
that file already is — not a Second-Brain architecture change.

**Open scoping question 1, resolved (confirm, not revise):** the cron job
stays its own separate TASK (`T04`) within this one story, not a separate
story — the analyst's own story-level resolution (kept together, since the
new cron job invokes the SAME migrated script) is correct, and at the
task-granularity level `T04` should stay distinct from `T01`-`T03` because
it is a genuinely different kind of action (Hermes `cron/jobs.json`
provisioning, not a Python file edit) with its own independent verification
(the real cron job's shape/budget), mirroring how `REQ-SB-87-US-04-T04` kept
its own cutover/cron-facing work as a distinct task from `T01`-`T03`'s code
migration.

**Real cron-shape finding for the decomposer:** `job4-summarize-tag-threads`'s
own live `cron/jobs.json` entry (`id: dd61ce1c8065`) is `schedule:
{"kind": "interval", "minutes": 20}`, `repeat: {"times": 8, "completed": 9}`,
now `enabled: false`/`state: "completed"` — a genuinely bounded,
repeat-limited batch job against a 209-Thread backlog, not an unbounded
recurring one. This Skill's real backlog (~80 Files, SKILL.md's own
documented scale) is smaller; the new job should follow the SAME bounded-
repeat shape (interval schedule + a finite `repeat.times` budget sized to
clear the real backlog with reasonable margin, then naturally stop), never
an indefinitely-recurring job — exact numbers are decomposer/coder-level
against the real backlog count at build time.

**Decomposer pass (2026-09-02):** all 6 scenarios locked as
`REQ-SB-88-US-01-AC-01`..`AC-06` (untagged Gherkin tightened for
buildability, wording otherwise preserved). Four tasks created,
`T01`→`T02`→`T03`→`T04`, each `depends_on` its immediate predecessor
(straight chain, mirroring `REQ-SB-87-US-04`'s own shape): `T01`
(Summary write + tag-merge), `T02` (Files-log-line + Details/`--append`,
carrying the architect-flagged Thread `Template.json` `## Files`
`allowed_callers` data edit as its own in-scope task item, not left
implicit), `T03` (scratch proving + real-vault retrofit check), `T04`
(cron provisioning, its own distinct task per the architect's own
confirmation). Every locked AC has at least one AC-tagged manual
verification step in its owning task's `## Tests`; `depends_on` is a
straight, acyclic chain. Story `status: Draft → Ready`; all four tasks
written at `status: Ready` in lockstep. `gate: clear` — no new MUST-FLAG
trigger fired at this stage (the architect's own "no new ADR" call
stands; the Template.json edit is ordinary data maintenance per
`ADR-017`'s own already-anticipated extension mechanism).

gate: clear 2026-09-02 (decomposer) — no MUST-FLAG trigger fired: no
material assumption made (both open scoping points were already resolved
by the analyst/architect), no Draft/unfinalised requirement, no ADR
touched, no `ESCALATIONS.md` entry, no oversized task (each of the 4
tasks is a bounded, single-session unit mirroring `REQ-SB-87-US-04`'s own
already-proven sizing), every locked AC has a verifiable, tagged step, no
contradictory inputs, and the task breakdown follows an already-
established precedent shape rather than being one of several equally
valid options.
