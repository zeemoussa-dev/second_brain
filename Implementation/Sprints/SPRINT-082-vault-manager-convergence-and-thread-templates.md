---
id: SPRINT-082
title: vault_manager.py convergence + Thread/RawMessage Template authoring
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "sprint retro drafted — human to skim and harvest Learnings.md; REQ-SB-87-US-01's own ADR-017 human-review flag also still open, see REVIEW-QUEUE.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-09-01
started: "2026-09-01"              # YYYY-MM-DD when status → In Progress
completed: "2026-09-01"            # YYYY-MM-DD when status → Done
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

# SPRINT-082 — vault_manager.py Convergence + Thread/RawMessage Template Authoring

## Sprint Goal

Reconcile all nine real deployed `vault_manager.py` copies onto one canonical,
extended (dynamic-children + per-caller-access) engine, and author the real
`thread`/`raw-message` `Template.json` definitions every downstream REQ-SB-87
story consumes.

---

## Grouping Rationale & Sizing

- **Why grouped as its own sprint:** `REQ-SB-87-US-01` is the shared
  foundation for all four remaining `REQ-SB-87` stories — every one of
  `US-02-T01`, `US-03` (transitively, via `US-02-T01`), and `US-04-T01`
  `depends_on: [REQ-SB-87-US-01-T05]` directly, confirmed from the
  decomposer's own task frontmatter, not re-derived from story prose. No
  other `REQ-SB-87` story can even begin its own build until this one's
  `T05` (the Thread/RawMessage templates) is `Done`. Beyond the pure
  dependency-graph argument, this is also a genuine sequencing-risk call:
  `US-01` is real engine work (a new `growth: dynamic` child-note
  primitive, a new `allowed_callers` per-caller access model — `ADR-017`)
  touching a canonical file with **nine** real, live deployment locations
  feeding multiple already-`Done` production Skills (`meeting-capture`,
  `create-companies-partners`). A failure or rework need here would block
  every downstream sprint regardless of how the remaining 4 stories'
  17 tasks get partitioned — isolating it in its own sprint means that risk
  is fully resolved and verified (`T06`'s own full regression pass across
  every already-`Done` template-driven note kind) before any downstream
  work is scheduled, rather than discovered mid-way through a larger,
  mixed sprint.
- **Sizing:** 6 tasks sits inside this project's own most-reliable sizing
  band (6-9 tasks/sprint, exact matches `SPRINT-020`/`022`/`028`/`048`/`080`),
  sized `M` per this project's own task-count-to-size convention. Even
  setting sequencing risk aside, `US-01` alone (6 tasks) combined with
  either sibling (`US-02`, 5 tasks → 11; `US-04`, 4 tasks → 10) would exceed
  this project's own largest confirmed-accurate ceiling (9 tasks/L,
  `SPRINT-021`/`030`), so standing alone is also the correct sizing call,
  not just the correct risk call.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-082 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-87-US-01](../UserStories/REQ-SB-87-US-01-vault-manager-resync-and-thread-templates.md) | vault_manager.py convergence + Thread/RawMessage Template authoring | P1 | Done (gate: flagged — `ADR-017` human review still pending, see REVIEW-QUEUE.md) |

---

## Dependencies / External Blockers

- **Depends on sprints:** None — this is the foundation sprint for
  `REQ-SB-87`.
- Internal task order (per the decomposer's own `depends_on`): `T01` → `T02`
  → `T03` → `T04`; `T02` → `T05` (parallel with `T03`/`T04`); `T06`
  (`depends_on: [T04, T05]`) closes the sprint with a full regression pass.

---

## Out of Scope

- `REQ-SB-87-US-02`/`US-03`/`US-04`/`US-05` — all four consume this
  sprint's own resynced engine + new templates; none of their own scripts
  are touched here (see `SPRINT-083`/`SPRINT-084`).
- Resolving `ADR-017`'s own human-review flag — that is a
  `REVIEW-QUEUE.md` item, not something this grouping pass clears (see
  Notes).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact
      (already done at `/plan-tasks`, `ADR-017` — no further architecture
      change surfaced during the build)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-017`,
      already `Accepted`)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
      (done incrementally by `T01`-`T05`; `T06` was verification-only and
      produced no new decision beyond what those five already recorded)
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes (product-owner, `/plan-sprints`, 2026-09-01)

- **This sprint's own `gate: clear` is scoped to the GROUPING decision
  only** — no product-owner-level MUST-FLAG trigger fired: no assumption
  was made partitioning `US-01` into its own sprint (the real `depends_on`
  edges were read directly from each task file's own frontmatter, never
  re-derived or guessed); `REQ-SB-87` is not `Draft`/unfinalised in the
  PRD; no ADR was created or changed by this pass (`ADR-017` was appended
  at `/plan-tasks`, not here); no `ESCALATIONS.md` entry was written by
  this pass; the sprint is not oversized (6 tasks, well inside the
  confirmed band); no cross-sprint dependency had to be introduced (this
  sprint has none); the partition is unambiguous given both the real
  dependency-fan-out (every downstream story needs `T05`) and the
  sizing-ceiling arithmetic above.
- **What this does NOT mean:** `REQ-SB-87-US-01` itself still carries
  `gate: flagged` at the story level (`ADR-017`, trigger-3) with its own
  open `REVIEW-QUEUE.md` entry. That flag is carried forward here for
  visibility, not silently dropped — see the `Stories in Scope` status
  column above. Per `Pipeline.md`, a flagged story gate does not block
  `/plan-sprints` or `/implement-sprint` from proceeding; the human
  resolves the story's own flag independently, on its own timeline —
  the same carry-forward shape already established for `SPRINT-078`
  (`REQ-SB-82-US-06`) and `SPRINT-080` (`REQ-SB-85-US-03`).
- No new `REVIEW-QUEUE.md` or `ESCALATIONS.md` entry was written by this
  pass — the existing `REQ-SB-87-US-01`/`ADR-017` entry already covers the
  open review; duplicating it here would only fragment the same open item
  across two places.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M — matched exactly,
  extending this project's own well-established 6-task/M precedent
  (`SPRINT-020`/`022`/`028`/`048`/`080`). No task was split, dropped, or
  merged. `T03` (the 82-copy resync) and `T05` (the Thread template,
  carrying most of the story's own locked ACs) were correctly the
  heaviest by live-verification effort, not code volume — `T06`'s own
  closing regression pass added real wall-clock cost (four separate
  scratch-vault scripts plus a live spot-check across six note kinds
  against the real vault) but zero code, exactly as a verification-only
  closing task should.

### What worked

- **Isolating a real, nine-copy, multi-production-Skill-touching engine
  change into its own single-story sprint, with the closing task as a
  mandatory full regression pass, paid off exactly as the product-owner's
  own grouping rationale predicted** — every one of `T01`-`T05`'s real,
  live-verified claims held up unchanged when re-checked independently at
  `T06`, and the one closing pass caught zero regressions across all ten
  already-`Done` note kinds plus both already-migrated production Skills.
- **Composing `T06`'s own scratch-vault regression scripts by directly
  importing the real, unmodified `ingest_meeting()`/`build()` functions
  (never a CLI subprocess, never a mock)** reused this codebase's own
  established "direct-import verification" precedent cleanly a further
  time, and made a thin call-site spy (recording each real `caller` kwarg)
  trivial to wire in without touching either script.
- **Re-resolving a note's current real path by id AFTER a later real
  mutation (here, `bump_folder_date` moving a series folder forward)
  instead of trusting an earlier call's own now-stale result-dict path**
  — caught a self-inflicted false negative in the verification script
  itself early, before it was ever mistaken for a real regression.
- **SHA-256 checksum re-verification, not a fresh eyeballed diff, to
  re-confirm a "should still be true" fact from an earlier task** — reused
  `T03`'s own exact hash and technique, turning "T04 didn't touch the
  engine copy" from a plausible claim into a directly re-confirmed one.

### What didn't work

- **Choosing test-data names for a live scratch-vault run without first
  considering `own_folder`'s own real title-truncation/collision-suffix
  behavior under a very long absolute scratch-path prefix** — an initial
  choice of two long, near-identical entity names (sharing a common
  prefix) collided into a real, correct-but-confusing time-suffixed
  folder name, costing one avoidable script-rewrite cycle before
  switching to short, genuinely distinct names. Worth naming explicitly:
  a deeply-nested scratch working directory (this project's own
  session-scratchpad convention) eats meaningfully into the same
  max-path budget a shorter, real-vault-rooted path would not.
- **Assuming a `type: "Note"` frontmatter match alone identifies a real,
  engine-created Note instance** — several real, hand-written notes
  (predating the `note` Template.json) share the exact same `type:
  "Note"` frontmatter value but carry none of the engine's own real
  `## Summary`/`## Body` section shape, and one whole cluster of them
  lives outside `Work/` (the engine's own real search root) entirely.
  Cost one false-negative investigation cycle before finding a genuine
  engine-created instance under `Work/Notes/`.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Re-resolve a mutated entity's current real path by identity AFTER
  every real mutation in a verification script, never trust an earlier
  call's own result-dict path once a later step in the same script could
  have moved/renamed it** (`bump_folder_date` here) — a self-inflicted
  false negative is otherwise easy to mistake for a real regression.
- **Pick short, genuinely distinct scratch-vault test-entity names, and
  budget for a deeply-nested scratch working directory eating into
  `own_folder`'s own real max-path truncation logic** — a long or
  near-identical test name that would never collide against a short,
  real-vault-rooted path can produce a confusing, correct-but-unexpected
  collision-suffixed folder purely as an artifact of an unusually long
  scratch-path prefix.
- **When a CLI subcommand's own surface is narrower than the real
  function it wraps (here, `get-section --id` only, vs.
  `get_section_content(path, section)` taking any resolved path), call
  the real function directly against a `find`-resolved path rather than
  treating the CLI's own narrower surface as a hard verification
  ceiling** — reused this codebase's own "direct-import verification"
  precedent one layer deeper.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Trusting a frontmatter `type:` value alone to identify a real,
  engine-created instance of a note kind, without also confirming the
  engine's own real declared section headers are present** — a
  same-named, hand-written note predating the engine's own template can
  share the exact same `type:` string while carrying a completely
  different body shape (or living entirely outside the engine's own real
  search-root scope), producing a false negative that looks like a
  missing capability rather than the real, disclosed finding it is
  (pre-existing content simply never passed through the engine).

### Open follow-ups

- **The real, disclosed raw-body-text gap `T05` found** (`create_dynamic_child()`
  has no way to write a flat, headerless raw body the way
  `create_raw_message_note` does today) is not this sprint's own scope to
  resolve — flagged for `REQ-SB-87-US-02` (`email-thread-capture`'s own
  write-mechanics migration, the first real consumer of the dynamic-child
  RawMessage shape) to pick up, per `T05`'s own `MEMORY.md` Constraint
  entry.
- **`REQ-SB-87-US-01`'s own `ADR-017` human-review flag remains open** —
  `REVIEW-QUEUE.md` still carries the unresolved 2026-09-01 entry asking
  for the ADR to be approved/rejected; resolving it is a human decision,
  not something this sprint's own closure clears.
