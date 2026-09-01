---
id: REQ-SB-87-US-04
title: Migrate summarize-and-tag-threads' write mechanics (apply_thread_review.py) onto vault_manager.py
requirement_ids: [REQ-SB-87]
requirement_section: "REQ-SB-87: Email Thread Capture — a New, LLM-Driven Pipeline (Classify, Skip Noise, Summarize, Find Pending Actions)"
phase: P1
status: Ready
gate: clear
gate_reason: "Production-risk trigger resolved by applying the operator's own already-locked rollout decision (REQ-SB-87-US-02's 100-email scratch-sample proving phase — PRD raised-context point 2 confirms this applies to the whole requirement's scope, not just that one story). The 'is Summary actually broken' question is resolved by direct diagnosis in Context, not left open. No other trigger fired."
sprint: "SPRINT-083"
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-04 — Migrate summarize-and-tag-threads' Write Mechanics onto vault_manager.py

## Story

**As** the operator whose live, recurring `job4-summarize-tag-threads` cron job
depends on `apply_thread_review.py` to write real Summary/tag/log content onto
Threads
**I want** `apply_thread_review.py`'s own hand-rolled read/write primitives
(`read_note`, `merge_tags`, `upsert_frontmatter_key`, `replace_body_section`, its own
separate `_HUMAN_OWNED_HEADERS` guard) replaced with calls through
`vault_manager.py`'s shared, template-driven engine
**So that** Summary/tag/action writes for a Thread all go through the SAME one
canonical engine — REQ-SB-87 point 7's own binding principle, "never a second,
bespoke write path" — instead of `apply_thread_review.py` remaining a third,
independently hand-maintained writer alongside the now-converged `vault_manager.py`
copies, without changing any of its own already-working real judgment-application
behavior.

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-87*, point 7 (verbatim binding principle:
  "Minmize the amount of code think prompts that code, You Have the Vault Manager
  That can be used for writes... never a second, bespoke write path").
- **Real diagnosis performed directly against the live vault (2026-09-01), not
  assumed:** the PRD's own "confirmed live... `## Summary` and `## Actions` are BOTH
  genuinely empty" observation does NOT hold for Threads `job4` has actually
  processed. Read directly: `Work/Threads/2026-08-31 Masdar Open Items/...md`,
  `2026-08-31 TAQA/...md`, `2026-08-31 Updates on Energy AI for Adnoc/...md`,
  `2026-08-31 Masdar Forecasted BoQ for Data Platform/...md`, `2026-08-31 Discuss
  with Mousa/...md` — every one of these carries a real `last_summarized_at`
  timestamp AND a real, substantive `## Summary` (multi-sentence, genuinely
  reflecting that Thread's own content, not a placeholder). **`apply_thread_review.
  py`'s own summary-writing mechanism is NOT broken — it works exactly as its own
  docstring intends, when it actually runs.** A Thread never yet processed by `job4`
  (`Work/Threads/2026-08-19 ADNOC AI HPC expansion.../...md` — no
  `last_summarized_at` field at all, an older, pre-2026-08-21-rewrite tags shape)
  still shows an empty `## Summary`, consistent with "never yet run through the
  current pipeline," not "the pipeline is broken." **`## Actions`, by contrast, is
  empty on every single Thread checked, including the freshly-processed ones —
  confirming it is a genuine, currently 100%-absent capability, not a defect** —
  matching `apply_thread_review.py`'s own real payload shape (`{thread_path,
  summary, short_summary, companies}` — no `actions` key exists anywhere in it
  today). This reframes what "fix" means here: no code defect to repair in the
  Summary path; a real mechanics migration (this story) plus a genuinely NEW
  capability (pending-action extraction, [[REQ-SB-87-US-05]]) — not a bugfix.
- **Real, confirmed gap found reading `apply_thread_review.py` directly:** it does
  not import `vault_manager.py` at all — it is its OWN, separate, smaller module
  with its own duplicated `read_note`/`merge_tags`/`upsert_frontmatter_key`/
  `replace_body_section`/`_HUMAN_OWNED_HEADERS`/`_CALLER` primitives, entirely
  independent of the three already-converging `vault_manager.py` copies
  [[REQ-SB-87-US-01]] resyncs, and has never had a `vault_manager.py` copy deployed
  to its own `scripts/` folder.
- **Depends on** [[REQ-SB-87-US-01]] — needs the resynced, canonical
  `vault_manager.py` AND the Thread template's own section-access declarations
  (this story's own migrated caller needs its existing `## Summary` write access
  preserved).
- This Skill backs the LIVE, recurring `job4-summarize-tag-threads` cron job — real
  production risk, matching [[REQ-SB-87-US-02]]'s own already-resolved risk profile
  exactly (same operator, same day, same PRD).
- **Rollout approach — resolved, not re-litigated.** The PRD's own raised-context
  point 2 states the operator's 100-email scratch-sample proving-phase rollout
  (already locked on [[REQ-SB-87-US-02]]'s own Constraints) is "this requirement's
  own implementation" rollout approach generally, not scoped to that one story alone.
  Applied here: prove the migrated `apply_thread_review.py` against a real
  scratch-vault sample (`--vault-path` pointed at a scratch copy, iterated there)
  before pointing the live `job4` cron's own `--vault-path` at the real vault.
- Related: `create_companies_partners.py`'s own `retag_threads_by_participant_
  company` — a separate, later Enrich-pass consumer of Thread notes this migration
  must not disturb, mirroring the same boundary [[REQ-SB-87-US-02]] already respects
  for its own migration.

## Acceptance Criteria

### Scenario 1: Summary and tag writes for an already-resolved company continue to work exactly as today
```gherkin
Given a Thread whose messages an agent has already read and reasoned about, with a
  real summary, short_summary, and a list of company names it recognized
When apply_thread_review.py runs (now resolving/writing the Thread via
  vault_manager.py's find_by_id/modify_section/merge_tags instead of its own
  hand-rolled read_note/replace_body_section/merge_tags)
Then the Thread's own ## Summary is written with the agent's real summary content,
  exactly as today
  And every resolved company still gets its customer/<slug> or partner/<slug> tag
  merged onto the Thread and every message under it, exactly as today
  And the script still prints {tags_applied, companies_unresolved, messages_tagged,
  log_entries_added, last_message_at, last_summarized_at} with the same meaning as
  today
```
<!-- AC-ID: REQ-SB-87-US-04-AC-01 -->

### Scenario 2: last_message_at / last_summarized_at stamping is preserved
```gherkin
Given a Thread with one or more RawMessage notes under its own messages/ folder
When apply_thread_review.py runs against it
Then last_message_at is stamped from that Thread's own latest message's real
  received value, and last_summarized_at is stamped to the current time, exactly as
  today — this is what lets a recurring job4 run tell "already summarized, nothing
  new since" apart from "needs a summary" (the Skill's own documented skip rule)
```
<!-- AC-ID: REQ-SB-87-US-04-AC-02 -->

### Scenario 3: Company log entries are appended and re-sorted exactly as today
```gherkin
Given one or more companies resolved for a Thread
When apply_thread_review.py runs
Then each resolved company's own <Name>-log.md gets one dated log-entry line
  appended, and the whole file's entries are re-sorted newest-to-oldest, exactly as
  today
```
<!-- AC-ID: REQ-SB-87-US-04-AC-03 -->

### Scenario 4: Person notes are still never tagged by this path
```gherkin
Given a Thread whose messages carry participant_links to real Person notes
When apply_thread_review.py runs and tags the Thread + its messages with resolved
  company tags
Then no Person note is ever tagged as a side effect — the 2026-08-21 bug-fixed
  behavior (person tagging is exclusively domain-based, a separate mechanism) is
  preserved exactly
```
<!-- AC-ID: REQ-SB-87-US-04-AC-04 -->

### Scenario 5: An unresolvable company name is reported, never fabricated
```gherkin
Given a company name in the agent's own payload that does not match any real
  Customer/Partner/Affiliate hub note
When apply_thread_review.py runs
Then that name is reported in companies_unresolved and no hub note is fabricated,
  exactly as today
```
<!-- AC-ID: REQ-SB-87-US-04-AC-05 -->

### Scenario 6: The migrated script converges onto the Thread template's own section-access declarations
```gherkin
Given the Thread template ([[REQ-SB-87-US-01]]) declares ## Summary as
  machine-writable by this script's own caller identity, and ## Personal Notes as
  never machine-writable
When apply_thread_review.py attempts to write either section through the migrated
  code path
Then ## Summary is written successfully, and any attempt to write ## Personal Notes
  is refused with a real, explicit error
  And this refusal is enforced by vault_manager.py's own template-declared access
  control, not by apply_thread_review.py's own separate, now-retired
  _HUMAN_OWNED_HEADERS constant
```
<!-- AC-ID: REQ-SB-87-US-04-AC-06 -->

### Scenario 7: Migration is retrofit-safe against the real, already-populated vault
```gherkin
Given the real vault's own already-summarized and not-yet-summarized Threads from
  before this migration
When the migrated apply_thread_review.py runs against that same real, live vault
Then every already-existing Thread is found and topped up correctly by the same
  last_summarized_at-based skip rule the Skill's own SKILL.md already documents —
  no duplicate log entries, no lost tags, no already-correct ## Summary content
  overwritten with something different for a Thread that hasn't actually changed
```
<!-- AC-ID: REQ-SB-87-US-04-AC-07 -->

## Affected Screens

None — backend only (Hermes-Provisioning Skill scripts; no `src/frontend` or
`html-prototype/` surface).

## Dependencies

- **Blocked by:** [[REQ-SB-87-US-01]] — resynced `vault_manager.py` + Thread
  template section-access declarations.
- **Blocks:** [[REQ-SB-87-US-05]] — pending-action extraction builds its own new
  `## Actions` write on top of this story's own migrated engine call, not on the
  old, retiring bespoke primitives.
- **Related:** [[REQ-SB-87-US-02]] — the sibling Capture-side migration; same
  rollout precedent, independent file scope, no shared files.
- **External:** none.

## Constraints

- Every existing hand-written business-logic function/decision stays hand-written
  and behaviorally unchanged — only the underlying note read/write mechanics move to
  `vault_manager.py`: company resolution (`build_company_index`/`resolve_companies`),
  the "never tag Person notes" rule, the log-entry re-sort logic.
- Deploy a NEW `vault_manager.py` copy to `summarize-and-tag-threads/scripts/` (it
  has never had one), sourced from [[REQ-SB-87-US-01]]'s own canonical resynced
  version — not a further-diverged fifth copy.
- Same production-risk posture as [[REQ-SB-87-US-02]]: verify first against a
  scratch-vault sample, only then cut the live `job4` cron's own `--vault-path` over
  to the real vault (see Context's rollout-approach resolution).
- Never run `job4` concurrently with itself, or with `email-thread-capture`, against
  the same vault during verification — mirrors the Skill's own documented
  concurrent-capture file-write-race pitfall (`SKILL.md`, 2026-08-21).
- Deploy the migrated script to the real, active Hermes profile location(s) it is
  actually running from, per this project's own standing manual-deploy pattern.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-87-US-04-T01 | backend | Deploy vault_manager.py copy + migrate Thread-resolution/`## Summary` write + stamping | `Hermes-Provisioning/skills/company-review/summarize-and-tag-threads/scripts/apply_thread_review.py`, `scripts/vault_manager.py` (new copy) | `REQ-SB-87-US-04-T01-migrate-summary-write-and-stamping.md` |
| REQ-SB-87-US-04-T02 | backend | Migrate tag-merge + company log-entry append/re-sort | `.../scripts/apply_thread_review.py` | `REQ-SB-87-US-04-T02-migrate-tag-merge-and-company-log.md` |
| REQ-SB-87-US-04-T03 | backend | Converge onto Thread template's own section-access declarations (retire `_HUMAN_OWNED_HEADERS`) | `.../scripts/apply_thread_review.py` | `REQ-SB-87-US-04-T03-converge-on-template-access.md` |
| REQ-SB-87-US-04-T04 | backend | Scratch-vault proving-phase verification + real-vault retrofit check + cutover | (verification + `--vault-path` cutover, no code changes) | `REQ-SB-87-US-04-T04-scratch-proving-and-cutover.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Fixing a Summary-writing defect** — none was found; see Context's own direct
  diagnosis against real, live Thread notes. This is a mechanics migration +
  convergence onto the shared engine, not a bugfix.
- Any change to `summarize-and-tag-threads`' own real per-Thread judgment (what the
  agent reads, how it writes a summary, which companies it recognizes) — stays
  entirely hand-written/agent-driven, per PRD point 7.
- Pending-action extraction — genuinely new capability, [[REQ-SB-87-US-05]].
- The new coarse Internal/Partner/Customer classification — written at Capture time,
  [[REQ-SB-87-US-03]], not touched here.
- Backfilling/re-running `job4` against Threads it has never processed (the older,
  pre-2026-08-21 Threads still showing an empty Summary) — a real, disclosed,
  separate coverage gap, not this migration's own job to close (see Notes).
- Fixing `BUG-042` (company-name resolution mis-tagging some real Threads as generic
  `"internal"`) — a separate, already-tracked Open bug, not silently absorbed here.

## Notes

**Prototype parity:** not applicable — this story has no `html-prototype/` surface
(backend-only, no UI).

**Diagnosis finding, disclosed rather than silently acted on:** a real
coverage/backlog gap exists — at least one confirmed real Thread (2026-08-19 ADNOC
AI HPC expansion) has never been processed by any `job4` pass at all, independent of
anything this migration changes; there are likely more among the vault's 209+
Threads (`SKILL.md`'s own stated scale). Closing that backlog (a bulk/backfill
`job4` run) is a real, legitimate follow-up, but is NOT the same problem as "the
summary mechanism is broken," and is not this story's own scope — noted here so it
isn't lost, not silently absorbed into a "fix" framing the direct diagnosis above
does not support.

**Resolution record (2026-09-01, analyst):** the two conditions that would otherwise
require a flag here are both resolved directly, not guessed:
1. **Production-risk (mirrors [[REQ-SB-87-US-02]]'s own originally-flagged
   trigger 5):** resolved by applying the operator's own already-made rollout
   decision — the PRD's own raised-context point 2 states the 100-email
   scratch-sample proving-phase approach is "this requirement's own implementation"
   rollout, not scoped to `REQ-SB-87-US-02` alone. Applying an already-decided
   precedent to a structurally identical later trigger (same operator, same day, same
   requirement, same kind of live-cron production risk) is legitimate autonomous
   pipeline execution, not a fresh guess.
2. **"Is Summary actually broken" (would otherwise be trigger 1/8, an unclear
   requirement premise):** resolved by direct, live evidence against five real
   Thread notes (see Context) — no code defect found, so no ambiguity remains to
   flag.

gate: clear 2026-09-01 — no unresolved trigger; see the resolution record above.

**Architecture scope (2026-09-01, architect):** `architecture.md` →
§Canonical `vault_manager.py` Source & Deployment, §`vault_manager.py`
Engine Extensions — Dynamic Children & Per-Caller Access
(`REQ-SB-87-US-01`, `ADR-017`), §Enrich-Stage Mechanics Migration &
Pending-Action Extraction (`REQ-SB-87-US-04`/`US-05`) — this story deploys
a NEW `vault_manager.py` copy (per `ADR-017`'s deployment inventory) and
consumes the Thread template's own `## Summary`/`## Actions` per-caller
access declarations (`apply_thread_review` is the one caller identity for
both sections). No new architecture of this story's own; no ADR touched by
this story itself.

**Decomposer pass (2026-09-01):** all 7 scenarios locked
(`REQ-SB-87-US-04-AC-01`..`AC-07`), 4 tasks created (`T01`..`T04`, chain
`T01 → T02 → T03 → T04`, `T01` depends on `REQ-SB-87-US-01-T05`). `T04`'s
own `## Tests` names the real ~100-email scratch-vault proving-phase
sample explicitly and is the one task that performs the real-vault
retrofit check + cutover. Every locked AC has at least one AC-tagged
verification step, `depends_on` is acyclic — `status` advances `Draft →
Ready`, all 4 tasks written at `status: Ready`. `gate` left untouched
(`clear`, already resolved by direct diagnosis).
