---
id: SPRINT-048
title: Vault knowledge model redesign — Threads/Meetings/Manual Captures evidence layer, OKF-conformant Customer/Project synthesis directories
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: clear                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "All 6 tasks (T01-T06) Done, all 5 locked ACs (REQ-SB-54-US-01-AC-01..AC-05) verified live, manual mode. Retrospective drafted by the coder, reviewed by the operator 2026-08-16, one factual correction applied (the migrate_customer_to_partner REVIEW-QUEUE re-file), and its 3 Patterns + 1 Antipattern harvested into Implementation/Learnings.md the same day — the retro-harvest gate trigger is resolved. Two non-blocking REVIEW-QUEUE.md spot-check items remain open from T04/T05 (scope-internal judgement calls); neither blocks sprint completion."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"     # effort estimate; checked vs actual in retro
created: 2026-08-16
started: "2026-08-16"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-16"            # YYYY-MM-DD when status → Done
---

# SPRINT-048 — Vault knowledge model redesign — Threads/Meetings/Manual Captures evidence layer, OKF-conformant Customer/Project synthesis directories

## Sprint Goal

Ship `REQ-SB-54-US-01`'s full data-model redesign — the `replace_body_section`
regeneration primitive, the Thread note kind, the Meeting thread-link field, and
the OKF-conformant Customer/Project directory shape (`index.md`/`<slug>.md`/
`log.md`/`captures.md`) — as one cohesive unit under `ADR-042`.

---

## Grouping Rationale & Sizing

- **Why grouped:** All 6 tasks belong to a single story (`REQ-SB-54-US-01`) and a
  single architecture scope (`ADR-042`), so there is only one story to partition —
  the only real decision was whether to split its 6 tasks across ordered sprints.
  The dependency graph is one connected chain plus one independent leaf, all
  within the same story: `T01` (no deps) → `T02` (Thread note kind) and `T04`
  (OKF directory family + Customer) → `T05` (Project, reuses T04) → `T06`
  (`list_all_note_paths` recursion, needs both T04 and T05); `T03` (Meeting
  thread-link field) has no deps and is independent of the rest. Splitting this
  single story across two ordered sprints would force an artificial
  `depends_on_sprints` edge mid-story for no architectural benefit — the whole
  chain (`T01`→`T04`→`T05`→`T06`) has to land together for `AC-01`–`AC-05` to be
  verifiable as a unit anyway (e.g. `AC-02`/`AC-03` need both `T04` and `T05`
  conceptually consistent with each other). One sprint is the unambiguous
  partition.
- **Sizing estimate:** ~6 tasks, M — calibrated against `Implementation/
  Learnings.md`: three prior sprints of exactly 6 tasks (`SPRINT-020`,
  `SPRINT-022`, `SPRINT-028`) all sized `M` and matched their estimate exactly at
  retro, with the heaviest task in each case driven by live-verification
  complexity rather than raw code volume. This sprint's own chain depth (4:
  `T01`→`T04`→`T05`→`T06`) and its "regenerate, don't patch" + "manual Captures
  never rewritten" invariants (AC-02/AC-03/AC-04) point the same way — expect
  `T04` (the OKF directory family + `customer_hub_linking.py` restructure,
  preserving 5 real live call sites) to be the heaviest task by verification
  effort, consistent with the pattern.

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-54-US-01](../UserStories/REQ-SB-54-US-01-vault-knowledge-model-redesign.md) | Vault knowledge model redesign — Threads/Meetings/Manual Captures evidence layer, Project/Customer synthesis layer (Background/History/Glimpse/Captures) | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None
- No external blockers — `ConversationID` false-merge risk (point 9) verified
  live and resolved 2026-08-16; `ADR-042` reviewed and operator-approved
  2026-08-16, no changes requested.

---

## Out of Scope

- Building the Email or Meeting capture pipelines themselves (`REQ-SB-55`/
  `REQ-SB-56`'s own scope — this sprint only builds the data model they'll call).
- Actually linking a Meeting to a Thread (`REQ-SB-56`'s own scope — this sprint
  only reserves the schema field, `T03`).
- The Glimpse/History/Background synthesis mechanism itself — the regeneration
  triggers, ownership-enforcement, and exact History-line bar (`REQ-SB-57`'s own
  scope).
- Backfilling existing vault content into the new shape (`REQ-SB-59`'s own
  scope).

---

## Definition of Done

- [x] Every story in scope has status `Done` — `REQ-SB-54-US-01` is `Done`.
- [x] All story-level Definitions of Done satisfied — see the story's own `## Definition of Done`.
- [x] `BACKLOG.md` updated — every affected row reflects current status (`REQ-SB-54` row + `SPRINT-048` row in the Sprint Status table).
- [x] `architecture.md` updated if the sprint changed an architectural fact — done by the architect pass at `/plan-tasks` (out of the coder's own `T06` file scope; not touched by this task).
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-042` (architect pass, operator-reviewed and approved 2026-08-16).
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints — `T01`'s own entry (`replace_body_section` pattern) plus a new consolidated `[2026-08-16] REQ-SB-54-US-01` entry added on `T06`'s completion.
- [x] `CHANGELOG.md` entry appended.
- [x] Retrospective section below filled in.
- [x] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M — **Takeaway:** matched exactly, extending the same precedent `Implementation/Learnings.md` already noted for `SPRINT-020`/`SPRINT-022`/`SPRINT-028` (all exactly-6-task sprints sized `M` that matched at retro). `T04` (the OKF directory family + `customer_hub_linking.py` restructure) was, as predicted at sizing time, the heaviest task by verification effort — it live-verified 6 real Test steps and surfaced a genuine third architectural consequence (the `partner_hub_linking.py`/`migrate_customer_to_partner` blast radius) beyond the two `ADR-042` already named. `T06` (this task, closing the sprint) was the lightest — a direct, literal implementation of its own illustrative code with no deviation.

### What worked

- **One shared generic primitive family, reused three times without duplication.** `T01`'s `replace_body_section` is now the single "regenerate, don't patch" mechanism for both the Thread `## Summary` (`T02`) and the Customer/Project `## Glimpse`/`## Background` (`T04`/`T05`) — confirmed live, zero copies. `T04`'s generic `okf_directory_paths`/`create_okf_directory_baseline`/`ensure_okf_directory_baseline` family was then reused verbatim by `T05` for Project (five thin wrappers, zero duplicated 4-file-creation logic) — the dependency chain (`T01`→`T04`→`T05`→`T06`) paid off exactly as the sprint's own Grouping Rationale predicted: one sprint, one architecture scope, no artificial cross-sprint edge.
- **Reading the real current codebase before writing, every task.** `T04` found and disclosed a real, live dependency (`partner_hub_linking.migrate_customer_to_partner`) on the OLD flat-file Customer hub-note primitives that no task file had named — caught by direct reading, not assumed away, and resolved by a scoped decision (leave the OLD primitives untouched, restructure only `customer_hub_linking.ensure_customer_hub_note`'s internals) that preserved all 5 real call sites with zero behavior change.
- **A throwaway scratch vault (session scratchpad, `VAULT_PATH` env-overridden) as the standard manual-verification harness.** Used consistently across `T04`/`T05`/`T06` — real function calls, real filesystem state, real assertions, and the actual configured vault (`<operator vault>\<operator vault>`) never touched by any test run. Cheap to set up, cheap to discard, and catches real bugs a mocked/pure-unit test would miss (e.g. `T06`'s own regression check needed a real one-level-vs-multi-level glob comparison against real files on disk).
- **Disclosing scope-internal judgement calls immediately, inline, rather than silently choosing.** `T04` (slug casing) and `T05` (a small private helper) both flagged real, small, non-blocking decisions the moment they were made, each with a clear "what to do"/no-action-required framing — neither slowed down the next task (`T06` built on both without waiting for a resolution).

### What didn't work

- **The decomposer's own story-level note promised a `REVIEW-QUEUE.md` entry for the `partner_hub_linking.py`/`migrate_customer_to_partner` future-defect disclosure ("Flagged here and in `REVIEW-QUEUE.md`") that was never actually written as its own standalone item** — it appears to have been folded into the general `ADR-042` human-review entry, which was then removed once the operator approved the ADR, taking the more specific disclosure down with it. Root cause: a flagged item nested inside a broader entry doesn't survive that broader entry's own resolution/removal. Carried forward as an Open follow-up below rather than silently dropped.
- **Nothing else genuinely blocked or churned this sprint** — no rework, no reverted approach, no failed verification attempt across any of the 6 tasks.

### Patterns to carry forward

- **Generic-primitive-first, kind-specific-wrapper-second, for any future multi-kind structural feature** — build the shared mechanism once (`T01`'s `replace_body_section`, `T04`'s `okf_directory_*` family) against the FIRST concrete kind, then apply it to every subsequent kind as thin wrappers only (`T05`'s five one-line-bodied Project functions). Apply this whenever a story introduces 2+ structurally-identical note/entity kinds in sequence.
- **A one-level discovery glob is a real, structural blind spot the moment ANY note kind gains a directory shape — make the fix its own explicit task, not an assumed side effect of the kind-adding task.** `architecture.md`'s own Consequences section naming `list_all_note_paths()` as a flagged, not-yet-resolved gap (rather than letting `T04`/`T05` silently absorb it) is what turned it into a real, verified `T06` instead of a latent bug discovered later by `list_known_customers()`/search/indexing silently missing real data. Apply this pattern whenever any future story adds a note kind whose files don't all live at the SAME folder depth as every other kind.
- **When restructuring a function's internals that has multiple real external call sites, preserve the external contract exactly and verify every call site is unaffected, rather than touching the call sites too** — `T04`'s `customer_hub_linking.ensure_customer_hub_note` restructure (same `{"hub_note_path": str, "created": bool}` return shape) kept all 5 real callers (`email_classification.py`, `meeting_classification.py`, `people_extraction.py`, `todo_classification.py`, `vault_filing_expert.py`) working with zero changes to any of them — confirmed live-by-reasoning, not just asserted.

### Antipatterns to avoid

- **Nesting a real, specific disclosed risk inside a broader, more-easily-resolved `REVIEW-QUEUE.md` entry (e.g., "and also, separately, X").** When the broader entry is cleared, the nested disclosure disappears with it even though it was never itself resolved — this sprint's own `migrate_customer_to_partner` gap is the concrete example (see What didn't work above). Give any genuinely separate, future-relevant risk its OWN `REVIEW-QUEUE.md` line item, even when it surfaces mid-discussion of a larger one.

### Open follow-ups

- **`migrate_customer_to_partner`'s hub-note-move step will silently no-op for any Customer onboarded AFTER `REQ-SB-54` ships** (it's keyed off the OLD flat `hub_note_path`, which the NEW OKF-directory-shaped Customer never has) — a real, disclosed, deferred gap from `T04`'s own pass, not fixed by this sprint (`ADR-042`'s own scope explicitly excludes generalizing the directory shape to Partner). Re-filed as its own standalone `REVIEW-QUEUE.md` item during `T06` (see What didn't work above for why the first copy was lost) — now present and awaiting a follow-up bug/story once a real post-`REQ-SB-54` Customer→Partner reclassification is attempted.
- **Two open, non-blocking `REVIEW-QUEUE.md` spot-check items from `T04`/`T05`** (Customer/Project directory slug casing — `_slugify()` preserves case/spaces rather than lowercasing/hyphenating; a small private `_project_directory_root` helper factored out of `T05`'s illustrative inline-repetition shape) still await human confirmation — neither blocks any downstream story, both are pure judgement-call disclosures.
- **`REQ-SB-55`/`REQ-SB-56`/`REQ-SB-57`/`REQ-SB-58`/`REQ-SB-59`** are all directly unblocked by this sprint's completion (per `BACKLOG.md`'s own "blocked on `REQ-SB-54-US-01` shipping" notes) — `REQ-SB-56`/`REQ-SB-57` each still have their own separate, already-flagged `REVIEW-QUEUE.md` items (fallback-link thresholds; the History-line "conclusion" bar) awaiting operator confirmation before their own `T02`/`T03` can be built, unrelated to this sprint's own scope.
