---
id: SPRINT-072
title: Company Review — Extract, Classify (Customer/Partner/Affiliate), and Batch-Apply
status: Done                        # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro-harvest — normal at sprint close, see ## Retrospective"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~9 tasks, L"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-19
started: 2026-08-19                # YYYY-MM-DD when status → In Progress
completed: "2026-08-19"             # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-072 — Company Review — Extract, Classify, and Batch-Apply

## Sprint Goal

Ship the Company Review pipeline — boilerplate-aware company extraction, a
5-way batched Customer/Partner/Affiliate/Merge/Decline Pending Approval, and
the `migrate_customer_to_partner` OKF-shape fix — as one cohesive addition to
the existing Librarian Section.

---

## Grouping Rationale & Sizing

- **Why grouped — single story, one sprint.** All 9 tasks belong to
  `REQ-SB-76-US-01`, one Definition of Done, one architecture scope
  (`architecture.md` → "The Librarian — Company Review", `ADR-057`). Graph
  read directly from each of the 9 task files' own `depends_on:`
  frontmatter (not from the story's own prose summary):
  - `T01` (`extract_thread_companies_for_review`) — `depends_on: []`, root.
  - `T02` (`affiliate_of` on both Customer/Partner shapes) — `depends_on: []`, root.
  - `T05` (`_apply_company_to_threads` shared helper) — `depends_on: []`, root.
  - `T03` (`migrate_customer_to_partner` OKF fix + `_retag_company_
    references`/`retarget_company_references`) — `depends_on: [T02]`.
  - `T04` (`propose_company_review()` Job + endpoint) — `depends_on: [T01]`.
  - `T06` (`finalize_company_review()` dispatch) — `depends_on: [T02, T03, T05]`.
  - `T07` (approve-endpoint decision body + `known-companies`) —
    `depends_on: [T04, T06]`.
  - `T08` (frontend decision control) — `depends_on: [T07]`.
  - `T09` (real end-to-end verification run) — `depends_on: [T04, T06, T07, T08]`.
  - **Acyclic** — a valid topological order exists (`T01`, `T02`, `T05` →
    `T03` → `T04` → `T06` → `T07` → `T08` → `T09`); confirmed by walking
    every edge above, no back-reference found. All 9 tasks carry `phase: P1`
    (matching the parent story) — no phase mixing.
- **Single sprint, not split.** No fault line decouples cleanly: `T06`
  (finalize dispatch) alone depends on three of the other roots/near-roots
  (`T02`, `T03`, `T05`) simultaneously, and `T09` transitively needs every
  other task's own output for a real full-system verification pass. Splitting
  along any plausible seam (e.g. "extraction/propose" vs. "finalize/apply"
  vs. "frontend") would still require the earlier group(s) fully `Done`
  before the next could start — no different in outcome from one sprint
  building all 9 in dependency order, just with extra sprint files and
  `depends_on_sprints` edges adding zero real decoupling value. Directly
  analogous to `SPRINT-063`'s own identical reasoning for the prior story in
  this SAME module (`REQ-SB-72-US-01`, also 9 tasks, also rejected a split
  on the same grounds).
- **Sizing estimate: ~9 tasks, L.** Matches this project's own proven,
  repeatedly-confirmed single-story/single-sprint ceiling
  (`SPRINT-021` 9 tasks/L, `SPRINT-030` 9 tasks/L, `SPRINT-063` 9 tasks/L —
  all three exact matches at retro per `Implementation/Learnings.md`) — not
  oversized. Every task is real, distinct, non-duplicative work (a new
  extraction call, a frontmatter-shape addition, a migration-fix + retag
  primitive, a propose Job, a shared apply helper, a finalize dispatcher, an
  endpoint/decision-body wiring, a frontend control, and a real full-corpus
  verification pass) — no MUST-FLAG oversized trigger fired for this
  grouping decision.
- **Standing story-level flag, not a grouping ambiguity.** The story itself
  carries `gate: flagged` / `gate_reason: trigger-3 (ADR-057 created)` from
  the architect pass — a standing human-review item for `ADR-057` (and
  `ADR-009`'s narrow, additive point-3 revision), already logged in
  `REVIEW-QUEUE.md` (`REQ-SB-76-US-01` entry, 2026-08-19). Per
  `Implementation/Pipeline.md`, this does not halt `/plan-sprints` — the
  product-owner does not clear an architect's own ADR flag, and the
  grouping decision above is itself unambiguous (single story, proven
  9-task/L shape, acyclic graph, all hard prerequisites already `Done`).
  This sprint's own `gate: clear` covers ONLY the grouping/partition
  decision; the story's own standing `ADR-057` review remains open in
  `REVIEW-QUEUE.md` and is unaffected by this sprint reaching `Ready`.

---

## Stories in Scope

<!-- Bidirectional link written at sprint creation: REQ-SB-76-US-01's own
frontmatter now carries sprint: "SPRINT-072". Order by implementation
dependency (dependency-first). -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-76-US-01](../UserStories/REQ-SB-76-US-01-company-review-extract-classify-and-batch-apply.md) | Company Review — Extract, Classify (Customer/Partner/Affiliate), and Batch-Apply | P1 | Ready |

**Tasks in scope** (dependency order): `T01`/`T02`/`T05` (independent roots)
→ `T03` (needs `T02`) → `T04` (needs `T01`) → `T06` (needs `T02`, `T03`, `T05`)
→ `T07` (needs `T04`, `T06`) → `T08` (needs `T07`) → `T09` (needs `T04`,
`T06`, `T07`, `T08`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. The story's four hard-blocking prerequisite
  stories are all already `Done` — `REQ-SB-74-US-01` (`SPRINT-068`),
  `REQ-SB-72-US-01` (`SPRINT-063`), `REQ-SB-16-US-01` (`SPRINT-007`),
  `REQ-SB-54-US-01` (`SPRINT-048`) — confirmed directly: every one of this
  story's 9 tasks' `depends_on` edges resolves to another task WITHIN this
  same story/sprint; none names a task ID from any other sprint.
- **External:** none new — the real, already-configured vault this pipeline
  extends. The story's own standing `ADR-057` human-review item
  (`REVIEW-QUEUE.md`, 2026-08-19) does not block `/implement-sprint` per
  `Implementation/Pipeline.md`'s "flagged doesn't halt the stage" rule, but
  remains open for the human's own sign-off independent of this sprint's
  own readiness.

---

## Out of Scope

- People notes linking to their real Company/Partner note — `REQ-SB-77`,
  placeholder, deferred by the story's own scope.
- Grouping/color-coding the Pending Approvals list by proposal type —
  `REQ-SB-78`, placeholder, deferred by the story's own scope.
- Any change to `ADR-009`'s Customer/Partner mutual-exclusivity axis (point
  1) — untouched; only point 3 (Partner's own Affiliate concept) is
  narrowly, additively revised by `ADR-057`.
- Project-level (Thread → Project) routing — one level below this
  requirement's own Customer/Partner/Affiliate scope.

---

## Definition of Done

- [ ] Every story in scope has status `Done`
- [ ] All story-level Definitions of Done satisfied
- [ ] `BACKLOG.md` updated — every affected row reflects current status
- [ ] `architecture.md` updated if the sprint changed an architectural fact (no change expected — already updated at `/plan-tasks` under "The Librarian — Company Review")
- [ ] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-057`, recorded at `/plan-tasks`, pending the standing human-review item above)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended
- [ ] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~9 tasks, L — **Actual:** 9 tasks, L — exact match. **Takeaway:**
  the estimate held even though the real build spanned two separate coder
  sessions across an infra stall (see "What didn't work") — the underlying
  scope itself was correctly sized at `/plan-tasks` time; the interruption
  was operational, not a scoping miss.

### What worked

- The propose/finalize split (`ADR-055`/`ADR-057`) made the mid-sprint stall
  recoverable with zero data risk: T09's resumed session found a genuine
  half-finished write (Masdar's `ensure_customer_hub_note` had run but its
  Thread tags hadn't) and could safely re-drive it to completion because
  every primitive involved was already idempotent by construction — no
  special-cased recovery logic was needed.
- Verifying against REAL vault data (not synthetic fixtures) surfaced real,
  substantive business decisions (Core42→Partner, Sindan→Affiliate-of-
  Mubadala grounded in an actual legal-affiliate confirmation quote,
  ADFEC→Merge-into-Masdar grounded in the Thread's own body naming ADFEC as
  Masdar's former name) that a synthetic test could never have produced —
  this is the same "real-data verification finds real gaps" pattern this
  project has repeatedly confirmed all session.

### What didn't work

- **Two separate coder-session stalls** ("Agent stalled: no progress for
  600s") interrupted this sprint's own T09 — an infra/stream-watchdog
  issue, not a code or data defect (confirmed both times: no orphaned
  processes, both backend ports healthy). Recovery worked because task/
  story frontmatter `status:` was checked directly before resuming rather
  than assumed, avoiding duplicate work both times.
- The operator's own briefing that "the Pending Approvals queue is
  intentionally near-empty" was stale by the time T09 actually ran — the
  FIRST (stalled) session had already run a real, unbounded propose pass
  before stalling, leaving 47 real pending records the resumed session had
  to discover and reconcile against, rather than a clean slate. Worth a
  general pattern: a resumed session should always re-verify real current
  state rather than trust a briefing written before an unknown-duration
  gap.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Idempotent primitives make mid-flight infra stalls safe** — every
  Company Review write this sprint (`ensure_customer_hub_note`,
  `_apply_company_to_threads`, `finalize_company_review`) was built
  idempotent from `/plan-tasks` onward, which is what let a real half-
  finished write survive an unplanned session stall and resume cleanly
  with zero manual repair. Apply this bar to any future propose/finalize-
  shaped mechanism as a default, not an afterthought.
- **Real-data verification over synthetic fixtures for classification-
  shaped mechanisms** — this sprint's own AC evidence (Partner/Affiliate/
  Merge decisions grounded in actual Thread content) would have been
  impossible to produce credibly against fixture data. When a task's own
  outcome is inherently judgment-shaped (is X a real Customer/Partner/
  Affiliate), verify against the real corpus, not invented examples.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting a stale "the queue is empty/clean" briefing across a session
  gap of unknown duration.** A resumed session must re-check real current
  state before acting on inherited assumptions, even ones stated
  confidently and recently — a prior session can make real, unlogged
  progress (or damage) in the gap.

### Open follow-ups

- **The per-mention idempotency floor doesn't track Merge-source names** —
  a Thread merged away from a duplicate name (e.g. "ADFEC" → Masdar) gets
  re-proposed under the ORIGINAL duplicate name on the next full pass,
  since only the canonical entity's tag is written, never a marker for the
  now-retired name. Real, disclosed, non-blocking (re-declining is a safe
  no-op) — filed in `MEMORY.md`, not yet its own story.
- **`## Related` regeneration doesn't accumulate across 3+ separate Company
  Review resolutions on the same Thread** — each additive resolution
  correctly ADDS its own tag, but regenerates `## Related` from only the
  current call's own target, silently dropping earlier resolutions' own
  links from that section (tags stay correct; only the `## Related` prose
  list under-represents history). Real design decision needed (accumulate
  from current `tags` vs. persist a list) — out of any single task's
  scope, filed in `MEMORY.md` for a future story that touches `## Related`
  regeneration again.
- **39 real `propose_company_review` records intentionally left pending**
  for the operator's own direct review (ADNOC, TAQA, FAB, Aldar, DGE,
  Microsoft, Google, and 32 more) — not a defect, the correct behavior of
  a propose-then-approve mechanism; noted here so the retro accurately
  reflects that real operator work remains before the corpus is fully
  classified.

---

## Notes

**Grouping decision (product-owner, 2026-08-19):** Single sprint, no split,
no `depends_on_sprints` edge. Verified the 9 task files' own `depends_on:`
frontmatter directly (not the story's own prose summary) — matches exactly,
acyclic, all `phase: P1`. This sprint's grouping is unambiguous: one story,
one proven 9-task/L shape (third exact match of this project's own
established ceiling, after `SPRINT-021`/`SPRINT-030`/`SPRINT-063`), all hard
prerequisite stories already `Done`, no cross-sprint dependency needed.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired for this role's own
grouping decision: not oversized (at, not beyond, an already-thrice-proven
ceiling); no blocked story (all hard prerequisites `Done`); no NEW
cross-sprint dependency introduced; the single-sprint-vs-split question was
actively checked against the real task graph, not left ambiguous. The
story's own standing `gate: flagged` (`ADR-057`, architect trigger-3) is a
separate, already-logged `REVIEW-QUEUE.md` item this role does not clear and
which does not block this sprint reaching `Ready`. Advanced `Draft → Ready`
— eligible for `/implement-sprint SPRINT-072`.
