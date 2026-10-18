---
id: SPRINT-086
title: Operator Profile — the singleton record, published into every agent's context
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint closed 2026-10-18: all 5 tasks Done, 7 locked ACs verified, nothing blocked. Flagged for the human to skim the DRAFTED retrospective below and harvest it into Implementation/Learnings.md (the coder never writes that file). The retro names the MEMORY.md compaction pass as BLOCKED WORK, not housekeeping — the third consecutive sprint to do so."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~5 tasks, M"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-10-16
started: "2026-10-18"              # YYYY-MM-DD when status → In Progress
completed: "2026-10-18"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — who drives each transition:
     Draft       → product-owner assembles the sprint. Bidirectional link is written
                   at creation: every story listed here already has sprint: SPRINT-NNN.
     Ready       → product-owner advances Draft→Ready when grouping is CLEAR (gate: clear).
                   Ambiguous, oversized, or blocked grouping stays Draft + gate: flagged.
                   Adding a story to a Ready sprint AUTO-REVERTS it to Draft.
     In Progress → /implement-sprint has started. Coder sets this + records started:.
     Blocked     → external dependency is unmet. Record it under Dependencies.
     Done        → every story is Done and every DoD box is checked. Coder sets this,
                   records completed:, DRAFTS the retrospective, and sets gate: flagged
                   for the human to skim and harvest Learnings.md.
-->

# SPRINT-086 — Operator Profile — the Singleton Record, Published Into Every Agent's Context

## Sprint Goal

Give this install one record of who the agent acts for — the operator's identity,
their other mail addresses, and their team as email+role entries — and publish it
into every agent's own SOUL.md as an auto-generated marker block, in one republish
pass that reloads the Registry exactly once.

---

## Grouping Rationale & Sizing

- **Why grouped (and why alone):** `REQ-SB-95-US-01` is the one story of
  `REQ-SB-95`'s five that is **fully independent** in the decomposer's recorded
  graph — read task by task, every `depends_on` edge in `T01`–`T05` points inside
  this story (`T01 → T02 → T04`, `T01 → T03 → T05`), and **no task in `US-02`,
  `US-03`, `US-04` or `US-05` reaches back into it**. It therefore needs no
  `depends_on_sprints` edge and can be built immediately, in parallel with or
  ahead of the Action spine. The story itself states the intent directly: it
  "deliberately lands first" because it builds the agent-context publication seam
  `US-03` reuses.
- **Why it was not merged with another story.** The only merge candidate that
  would not import a dependency it does not have is `US-02` (6 tasks, also
  edge-free at the sprint level) — 5 + 6 = 11 tasks, well past this project's own
  confirmed 8–9-task `L` ceiling (`SPRINT-021`, `SPRINT-030`, `SPRINT-049`,
  `SPRINT-083`). Merging with `US-05` (the other 5-task story) would be worse: it
  would drag this independent story behind `SPRINT-087`/`SPRINT-088`, since
  `US-05-T05` depends on `US-02-T02`, `US-03-T02` and `US-03-T03`. Standing alone
  is the only grouping that honours the graph without delaying buildable work.
- **Sizing:** 5 tasks, sized `M`. Four backend plus one frontend, in line with
  this project's own 5-task precedents (`SPRINT-032`, `SPRINT-034`, `SPRINT-038`
  at `S`; `SPRINT-081` at `M`). Sized `M` rather than `S` because `T02` is a
  genuinely new mechanism in the most actively-extended backend file
  (`agent_manager.py`) — a fourth marker-block pair plus a new one-pass republish
  method — and its ACs need real agent-context verification, which this project's
  Learnings repeatedly show dominates cost over code volume.
- **Sizing risk to watch:** if the operator answers the open export-privacy
  question (below) with *strip on export*, this story gains **one further task**
  and `AC-08` becomes locked. That takes the sprint to ~6 tasks, still inside the
  band — it does not re-open this grouping.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-086 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-95-US-01](../UserStories/REQ-SB-95-US-01-operator-profile.md) | Operator Profile — one record of who the agent acts for, published into every agent's context | P2 | Done (all five tasks Done 2026-10-18) |

Build order inside the sprint, read from the task files' own `depends_on`:
`T01 → (T02, T03)`, `T02 → T04`, `T03 → T05`.

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- **Shared file with `SPRINT-088`, with no dependency edge between them.** Both
  `REQ-SB-95-US-01-T02` (here) and `REQ-SB-95-US-03-T01` (`SPRINT-088`) add their
  own independent auto-generated marker pair to
  `src/backend/app/business/core/agents/agent_manager.py`. The decomposer recorded
  **no edge between them**, and neither reads the other's block — but their titles
  disagree about who lands first (`US-01-T02` calls its pair "the fourth",
  `US-03-T01` calls its own "the third", and both describe the same **two**
  existing pairs, `_SPECIALISTS_*` and `_INDEX_GUIDANCE_*`). The ordinal is
  cosmetic naming; no AC and no behaviour depends on it. Under this plan `US-01`'s
  pair lands first and is in fact the third. Whichever lands second composes around
  the **real current file**, per this project's standing pattern — do not apply
  either task's illustrative code block to a remembered version of that file.
- **Story-level gate carried forward (`gate: flagged`, not resolved by this
  sprint):** `REQ-SB-95-US-01` is flagged under trigger 8 — publication writes
  colleague names into every agent's SOUL.md, and an exported Agent bundle copies
  both that `soul.md` and Hermes' own `profile.tar.gz` (opaque bytes, `ADR-014`),
  so a second copy rides along. `AC-08` is deliberately **`locked: false`**, no
  task implements either answer, and `T04` only *discloses* what a real bundle
  contains. The sprint can be built and closed without that decision: the other
  seven ACs are locked and complete. See `REVIEW-QUEUE.md`.
- **ADRs awaiting a human look:** `ADR-032`, `ADR-035`, `ADR-036` (its marker-block
  decision only) and `ADR-038` (binding; it supersedes `ADR-036`'s `SELF_EMAIL`
  retirement). All are `Accepted`; the operator has reviewed the `ADR-036` item
  (marker block approved, retirement rejected). Nothing here waits on them.

---

## Out of Scope

- Actions, Workflows, enforcement and entity resolution — `SPRINT-087` …
  `SPRINT-090`.
- **`SELF_EMAIL` stays exactly as it is** (`ADR-038`): `system_settings._FIELDS`,
  `config.REQUIRED_FOR_STARTUP`, `setup_wizard.py`, `setup_router.py`,
  `SettingsSystemPage.tsx` and the deployed payload capture scripts are all
  untouched. The Profile mirrors the setting and never writes it.
- Implementing either answer to the export-privacy question (`AC-08`).
- Org-chart modelling, Person-note editing, multi-operator installs.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — no
      architectural fact changed; `T04` confirmed `ADR-032`'s exclusion already
      held by construction and wrote no production code
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — none created
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints —
      **BLOCKED, not skipped.** 86 KB against the 40 KB budget its own rule 1
      sets, which forbids appending while over. `T04`'s constraint is parked in
      `REVIEW-QUEUE.md`. See the retro's *Open follow-ups*.
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in (DRAFTED by the coder)
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes

**gate: clear 2026-10-16 — no product-owner trigger fired.** Checked trigger by
trigger: no assumption (the partition is read from the recorded `depends_on`
edges, not from story order); requirement finalised; no ADR created or changed by
this pass; no `ESCALATIONS.md` entry; **not oversized** (5 tasks, inside the
confirmed band); **no `Blocked` story** (`REQ-SB-95-US-01` is `Ready`); **no
cross-sprint dependency** — this sprint has none at all; no contradictory inputs
(the marker-block ordinal mismatch above is cosmetic and is recorded, not
guessed at); and **no ambiguity** — there is exactly one grouping that keeps this
independent story buildable now without exceeding the sizing band. The story's own
upstream `gate: flagged` is carried forward above rather than cleared here;
`/plan-sprints` does not resolve another stage's flag.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

_DRAFTED by the coder, 2026-10-18, on closing `T04`. The human skims this and
harvests it into `Implementation/Learnings.md`._

### Sizing accuracy

- **Estimated:** ~5 tasks, `M` — **Actual:** 5 tasks, `M` — **Takeaway:**
  **matched exactly, and the estimate's own reasoning held.** `T02` was correctly
  called as the cost centre up front (a fourth marker-block pair plus a new
  one-pass republish in `agent_manager.py`, this codebase's most
  actively-extended backend file), and it was. The sizing note's named risk — *if
  the operator answers the export-privacy question with "strip on export", the
  sprint gains a task* — did not fire: the operator **accepted** the leak on
  2026-10-17, so `AC-08` stayed `locked: false` and `T04` stayed a disclosure.
  One calibration point worth keeping: `T04` was sized as a build task and landed
  as a **guard-only** task with **zero production change**, because the property
  it protects already held by construction. Its real cost was verification design
  (making the guard survive the eighth artifact kind), not code.

### What worked

- **A conditional `## Files to Modify` entry.** `T04` listed
  `artifact_export.py` as *"only if the guard finds the Profile genuinely
  reachable today; if it is already excluded by construction, change nothing here
  and say so"*. The guard found it already excluded, the file was left
  byte-identical, and the task closed with no improvisation, no escalation and no
  defensive filter added to code that did not need one. The decomposer having
  written the conditional is what made "change nothing" an outcome rather than a
  judgement call.
- **Mutation-probing a guard that passed on the first run.** All five of `T04`'s
  tests passed immediately, which is exactly what a vacuous guard also does. A
  throwaway copy outside the repo added a plausible eighth artifact kind that
  sweeps `data/Operator/` in beside `data/Actions/`; four of the five tests
  failed, the fifth correctly did not (different door). That probe is the only
  reason "5 passed" is evidence.
- **Structural exclusion, inherited rather than re-invented.**
  `REQ-SB-95-US-04-T04` had already established that `ActionCalls/`/`WorkflowRuns/`
  are excluded *structurally* — no kind, therefore no selection and no closure —
  instead of by a name filter. The Operator store was already in that same
  position, so a privacy guarantee cost one test file and no production code.
- **`T02`'s honestly-logged "writes the Hermes soul, not the Registry mirror"
  decision paid off two tasks later.** It was recorded as a scope-internal
  judgement call with its reasoning; `T04` then read it and found it was the
  load-bearing fact about *when* the published roster actually reaches a bundle
  (the mirror is stale until the next `AgentManager.update()`). A one-line
  "chose A over B because C" note turned into the sharpest part of the `AC-08`
  disclosure.
- **A disposable install as the default verification substrate.** Three of the
  five tasks verified against a scratch Hermes home / scratch data path with
  fictitious values, and the sprint still produced real `SOUL.md` writes, a real
  `.sbf` on disk and a real browser pass — with nothing written to the operator's
  own install, vault or Hermes.

### What didn't work

- **`MEMORY.md` is over its own budget and is silently eating this project's
  constraints.** 86 KB against the 40 KB its own rule 1 sets, and that rule
  forbids appending while over. **Two tasks in this sprint alone** (`T03`, `T04`)
  produced a genuine framework constraint that could not be recorded and is now
  parked in `REVIEW-QUEUE.md` instead — eight such entries in four days. This is
  the **third consecutive retro** to name it. It is not tidiness: the queue
  behind it is a growing set of rules future sessions will not read, in the one
  file whose entire purpose is being read.
- **Manual verification steps authored against the operator's real install.**
  Three of five tasks (`T02`, `T04`, `T05`) hit a `## Tests` manual step that, as
  written, required the real Hermes install / real vault / real data store — "ask
  a real agent in a real chat", "export a real bundle from the Artifacts screen".
  Each had to substitute a disposable install and disclose the substitution. The
  substitutions were sound, but three identical disclosures in one sprint is an
  authoring pattern, not three coincidences.
- **A pre-existing defect surfaced where a story could not fix it.** `T05` found
  that `settings_system_router.UpdateSystemSettingsBody` declares 5 of
  `system_settings._FIELDS`' 9 fields, so a `PUT /settings/system` carrying
  `self_email` is silently dropped while the UI answers `Saved.` Correctly left
  alone (out of scope, flagged) — but it means the one editable surface for the
  address `ADR-038` makes authoritative has been quietly non-functional since
  2026-08-27, and the sprint that most depended on that address is the one that
  found it.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Conditional file scope for a task whose deliverable is a guarantee** — when a
  task exists to *prove* a property rather than build one, list the production
  file as *"edit only if the guard fails"*. The coder then has an authorised way
  to ship zero production change, instead of either adding a redundant filter or
  escalating over an empty diff. Found live, `REQ-SB-95-US-01-T04`.
- **Mutation-probe any guard that passes on the first run** — copy the test file
  outside the repository, induce the exact failure the guard exists to catch
  (here: a simulated eighth artifact kind), and confirm it fails. Never commit
  the probe. "Passed first try" and "asserts nothing" are the same observation
  until this is done. Found live, `REQ-SB-95-US-01-T04`.
- **Derive a negative test's subject from the live set, and assert a containment
  equality rather than an absence** — extends `ESC-077`'s rule from *what to
  name* to *how to assert*. `T04`'s guard reads the store's location off its own
  data-access module, takes the export selection from the live inventory, and
  derives "personal data" from the record's own leaf values; the rule it enforces
  is *the only member allowed to carry a Profile value is the exported agent's
  `soul.md`*. An eighth kind, a new seed path and a new field are all covered
  with nobody extending a list. Found live, `REQ-SB-95-US-01-T04`.
- **Test the archive's own members, not the in-memory payload** — a file can be
  absent from the manifest and present in the bundle. Write the real `.sbf`, read
  it back member by member, then delete it. Found live, `REQ-SB-95-US-01-T04`.
- **Log the mirror you deliberately did not write** — when a pass updates one
  copy of a file and knowingly leaves a mirror stale, record that choice and its
  reason in the Implementation Log. A later task reading it learns *when* the
  data actually propagates, which no amount of reading the code in isolation
  reveals. Found live, `REQ-SB-95-US-01-T02` → `T04`.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Authoring a manual verification step that can only be performed against the
  operator's real install** — a decomposer-facing rule. A step naming the real
  vault, the real Hermes profiles or the real data store is unperformable as
  written by any session that may not touch them, so every coder substitutes a
  disposable install and spends a paragraph disclosing it. Write the step against
  a disposable install in the first place, and name the real-install half
  separately as optional operator confirmation. Three of five tasks this sprint.
- **Treating a knowledge file that is over its own budget as housekeeping** —
  `MEMORY.md` has blocked eight constraints in four days across three sprints.
  While it is over budget its own rules forbid appending, so every new rule is
  routed to a transient inbox; the inbox is not what future sessions read. The
  compaction pass is blocked delivery work with a growing queue behind it, and
  naming it as tidiness is what has kept it unscheduled for three sprints.
- **Assuming a published value reaches an export because it reached the store the
  publisher writes** — publication writes the Hermes-side `SOUL.md`; the export
  reads the Registry-side mirror, which publication deliberately skips. The two
  agree only after the next `AgentManager.update()`. Check which copy the
  consumer actually reads before describing a value as exported — or as safe.

### Open follow-ups

- **`MEMORY.md` compaction — BLOCKED WORK, not housekeeping.** Two constraints
  from this sprint (`T03`, `T04`) are parked in `REVIEW-QUEUE.md` because the
  file is 86 KB against its own 40 KB budget. Third consecutive sprint retro to
  raise it. Needs a scheduled compaction pass (or an explicit budget decision),
  not another parked entry.
- **`AC-08` is disclosed and the operator has accepted it** (2026-10-17, story
  `gate_reason`). `T04`'s Implementation Log adds one nuance the acceptance did
  not have: the roster reaches a bundle through the **Registry mirror**, which is
  stale until the next agent edit, and a **second, fresher copy** rides inside
  `profile.tar.gz`. If the operator wants to revisit, that log is the evidence.
- **`settings_system_router` drops four of nine settings fields** (found by
  `T05`, pre-existing since 2026-08-27, including `self_email`). The human
  decides whether it becomes a `/bug`. In `REVIEW-QUEUE.md`.
- **`ADR-032`, `ADR-035`, `ADR-036`, `ADR-038`** are all `Accepted` and still
  awaiting a human look. Nothing in this sprint waited on them; `T04` confirmed
  `ADR-032`'s export-exclusion clause empirically.
