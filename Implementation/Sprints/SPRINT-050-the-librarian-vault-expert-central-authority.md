---
id: SPRINT-050
title: The Librarian — Vault Filing Expert generalized to a Pipeline-Job caller + cross-cutting-update detection
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro-harvest (sprint-wrap default — human should skim this Retrospective and propagate patterns into Implementation/Learnings.md) AND the still-open trigger-1 architect-designed-write-shape human review carried from the story's own gate (REQ-SB-63-US-01, the already_filed_path param/cross_cutting_implication tag shape) — unresolved by this sprint-wrap pass, see REVIEW-QUEUE.md for both."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-049]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~3 tasks, S"      # effort estimate; checked vs actual in retro
created: 2026-08-16
started: "2026-08-16"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-16"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-050 — The Librarian — Vault Expert as the Central Placement/Restructuring/Enrichment Authority

## Sprint Goal

Generalize the already-`Done` Vault Filing Expert (`ADR-021`) into the consulted
placement authority for `REQ-SB-55`'s Thread pipeline — an additive
`already_filed_path` parameter, a new `cross_cutting_implication` decision field
that proposes a Pending Approval when content also implies a KB update elsewhere,
and the one concrete `Consult-Librarian` integration point wired into the real,
running Email Capture & Threading pipeline.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-63-US-01` is the only story here.
  All 3 tasks (`T01`-`T03`) belong to one story and one architecture section
  (`architecture.md` → "The Librarian..."). `T01` (generalize
  `determine_placement_and_file` — both the `already_filed_path` param and the
  `cross_cutting_implication` detection/proposal, one cohesive unit, both evaluated
  in the same model completion) has no deps; `T02` (wire `Consult-Librarian` into
  the pipeline) and `T03` (`finalize_cross_cutting_update`) each depend on `T01`.
  No reason to split this single story's own 3-task chain across sprints.
- **Why sequenced behind `SPRINT-049`, not combined with it:** confirmed by direct
  reading of `T02`'s and `T03`'s own `depends_on` frontmatter that this story
  carries three REAL, decomposer-recorded cross-story edges into `REQ-SB-55-US-01`
  — `T02` depends on `REQ-SB-55-US-01-T03` (Thread-Match/Merge, supplies
  `thread_result`), `REQ-SB-55-US-01-T04` (Route-to-Project — Consult-Librarian
  must never gate it), and `REQ-SB-55-US-01-T07` (Pipeline assembly —
  `email_capture_pipeline.py` itself does not exist until that task lands, and
  `T02` adds its own 6th node into the graph `T07` compiles); `T03` depends on
  `REQ-SB-55-US-01-T01` (the unconditional frontmatter-key setter it reuses for the
  tag write). None of `REQ-SB-55-US-01`'s own tasks depend back on anything here —
  the edge runs strictly one-directional. `T02`'s own task file is explicit that
  this is not a soft or nice-to-have ordering: its own Tests block requires
  invoking the REAL, running pipeline (or a real `thread_result` produced by a real
  `thread_match_merge` call) to verify `AC-01`/`AC-02`/`AC-05`, and its own Context
  states plainly that reaching this task before `REQ-SB-55-US-01-T03`/`T04`/`T07`
  land means "treat it as genuinely blocked, not as license to improvise a
  divergent pipeline shape." Honouring this via a `depends_on_sprints: [SPRINT-049]`
  edge (ordered sprints) rather than same-sprint sequencing mirrors this project's
  own already-established `SPRINT-011`→`SPRINT-012` and `SPRINT-025`→`SPRINT-026`
  precedent exactly: both of those pairs record the real, decomposer-authored
  cross-story `depends_on` edge as a sprint-level `depends_on_sprints` edge on the
  DOWNSTREAM sprint, and both their own Notes state directly that this is "not an
  artificial edge this role invented" and therefore does not trip the "cross-sprint
  dependency you had to introduce" MUST-FLAG trigger — the edge is a faithful
  transcription of a real dependency graph the decomposer already recorded, not a
  new one this pass manufactured. Combined, the two stories would also total 11
  tasks — past this project's own largest-ever confirmed-accurate sprint
  (`SPRINT-021`/`SPRINT-030`, 9 tasks/L) — with no sizing precedent to calibrate an
  11-task single working context against. Two ordered sprints additionally give a
  cleaner retro/sizing signal per story (this project's single-story sprints —
  `SPRINT-020`/`022`/`023`/`028`/`048`, among others — have consistently matched
  their own estimates exactly at retro; a mixed 11-task retro would conflate two
  stories' own separate sizing signals). This is a reasoned sizing +
  dependency-shape call, not a genuinely ambiguous partition — not flagged (see
  `SPRINT-049`'s own Grouping Rationale for the mirrored reasoning on that side).
- **Sizing estimate:** ~3 tasks, S — directly matches two prior 3-task/S
  precedents that both matched their estimate exactly at retro (`SPRINT-023` —
  the original Vault Filing Expert build this story generalizes — and
  `SPRINT-024`). `T01` (the generalized entry point — both the additive param and
  the cross-cutting detection/proposal in one grounded model-completion decision)
  is expected to be the heaviest by live-verification effort, mirroring
  `SPRINT-023`'s own identical finding for the original `determine_placement_and_
  file` build.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-050 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-63-US-01](../UserStories/REQ-SB-63-US-01-the-librarian-vault-expert-central-authority.md) | The Librarian — generalize the Vault Filing Expert into the consulted placement authority for REQ-SB-55/56/57/58's pipeline Jobs, extended to detect and surface cross-cutting KB updates | P1 | Done |

**Tasks in scope** (dependency order): `T01` (Generalize
`determine_placement_and_file`, `depends_on: []`) → `T02` (Wire
`Consult-Librarian` into `REQ-SB-55`'s Thread pipeline, `depends_on:
[REQ-SB-63-US-01-T01, REQ-SB-55-US-01-T03, REQ-SB-55-US-01-T04,
REQ-SB-55-US-01-T07]`), `T03` (`finalize_cross_cutting_update`, `depends_on:
[REQ-SB-63-US-01-T01, REQ-SB-55-US-01-T01]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-049` (`REQ-SB-55-US-01`) — must be `Done`
  before this sprint can start (hard rule 9; `/implement-sprint` refuses
  otherwise). `T02` cannot be built OR verified until `SPRINT-049`'s `T03`/`T04`/
  `T07` are real, shipped code — its own Tests block requires the actual running
  pipeline. `T03` needs `SPRINT-049`'s `T01` (the frontmatter-key setter it
  reuses).
- Story-level `gate: flagged` (trigger-1, the architect's designed write-shape for
  the deferred cross-reference write) is a standing breadcrumb, not a build
  blocker — per this project's own established `REQ-SB-54-US-01`/`SPRINT-048`
  precedent (a `Ready`/`flagged` story is fully eligible for `/plan-sprints` and
  `/implement-sprint`; the flag awaits a human look at the architect's designed
  parameter/tag shape, independent of delivery progress).

---

## Out of Scope

- `REQ-SB-55-US-01` — this same `/plan-sprints` batch's other story; this sprint
  depends ON its output, sequenced via `SPRINT-049`.
- Wiring an equivalent Librarian consult call into `REQ-SB-56`/`57`/`58`'s own
  pipeline Jobs — each of those stories' own future addition, per this story's
  own Non-Goals.
- Retrofitting or bridging `REQ-SB-08`/`09`/`10`'s current classification modules
  — explicitly out of scope per the operator's own resolved decision ("no
  Retrofit... replace it with pipeline").
- The Pipeline Builder / DAG UI — unrelated, separately deferred work.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, no architectural fact changed by the coder pass (the architect's own pass at `/plan-tasks` already updated it; this sprint's own tasks composed that design as-is, no further architecture.md edit needed or made)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no new ADR (confirmed by both the architect and decomposer passes at `/plan-tasks`)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [x] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~3 tasks, S — **Actual:** 3 tasks, S. Exact match, the
  third consecutive time this exact "~3 tasks, S, generalize/extend an
  already-Done Expert module" shape has landed precisely on estimate
  (`SPRINT-023`, `SPRINT-024`, now `SPRINT-050`) — this shape is now a
  reliable sizing anchor for future single-Expert-generalization stories.
  `T01` was confirmed the heaviest by live-verification effort, exactly as
  predicted in this sprint's own Grouping Rationale (5 locked ACs, 2
  independent axes — the `already_filed_path` param and the
  `cross_cutting_implication` detection — evaluated together).

### What worked

- **Sequencing this sprint strictly behind `SPRINT-049` via `depends_on_
  sprints` (rather than combining into one 11-task sprint) paid off
  exactly as reasoned at `/plan-sprints`:** `T02`'s own Tests block
  required a REAL `thread_result` from a REAL `thread_match_merge` call
  and the REAL compiled `email_capture_pipeline.py` graph — neither
  existed until `SPRINT-049` shipped. Building this sprint only after that
  one closed meant `T02` never had to stub or improvise either dependency.
- **The decomposer's own `T01`/`T03` "propose/finalize split by file, not
  by concept" boundary (mirroring `ADR-021`'s own `_create_tier_2_
  proposal`/`finalize_new_top_level_area` precedent) held up cleanly
  end-to-end** — `T01` (propose) and `T03` (finalize) never needed to
  coordinate beyond the `propose_cross_cutting_update` `action_id`/payload
  shape `T01` defined and `T03` consumed as a given contract.
- **Reusing an already-established `StateGraph` wiring shape for a NEW
  requirement (`T02`'s own list-returning `_route_after_thread_match_
  merge`, mirroring `_route_after_classify`'s "always this, additionally
  that" pattern from `SPRINT-049`/`T07`) meant zero new LangGraph wiring
  concepts were introduced** — the "never gates" Constraint became a
  structural graph-topology property (two independent destinations, each
  with its own fixed edge to `END`) rather than something enforced only by
  code review or a runtime check.
- **`T01`'s own scoped, disclosed monkeypatch-of-`model_factory` technique
  (an engineered-JSON-reply stub) proved reusable verbatim by `T02`** for
  deterministically engineering Tier-1/Tier-2/unavailable Librarian
  outcomes without depending on a real model's own non-deterministic
  phrasing — this is now a proven, twice-used verification technique for
  any future `determine_placement_and_file` caller.

### What didn't work

- Nothing sprint-blocking. One real friction point, not a failure: `T02`'s
  own scratch-vault verification needed a `kind` value the tempfile
  scratch vault genuinely had (`"Threads"`, the only real top-level folder
  a fresh `thread_match_merge` call creates) rather than the task file's
  own illustrative `"Emails"` example — a reminder that a scratch vault's
  own `known_kinds`/`known_customers` are whatever the test itself seeds,
  never assumed from a task file's own illustrative prose.

### Patterns to carry forward

- **"Propose in the Expert's own module, finalize in the router's dispatch
  table" (`_create_X_proposal` + `finalize_X`, registered in
  `_APPROVAL_HANDLERS`) is this codebase's now-3x-confirmed canonical
  shape for any new Pending-Approval kind** (`ADR-021` original, `T01`'s
  own `propose_cross_cutting_update`, `SPRINT-049`'s own `route_thread_to_
  project`/`propose_recurring_pipeline`) — any future new approval kind
  should default to this shape without re-deriving it.
- **When adding an unconditional additional branch alongside an existing
  single-choice conditional edge from the same `StateGraph` source node,
  convert the routing function to return a list (`"always this" +
  conditionally "also that"`), mirroring `_route_after_classify`'s own
  shape — do not invent a second, parallel wiring mechanism for the same
  node.** Directly reusable for `REQ-SB-56`/`57`/`58`'s own future
  Librarian-consult wiring (this story's own explicitly named future
  work).
- **A Job-tier caller consulting an Agent-tier Expert (`consult_librarian`
  wrapping `determine_placement_and_file`) should ALWAYS wrap the call in
  its own `try/except`, even when the Expert itself already returns an
  honest `{"status": "unavailable", ...}` dict** — the wrapper's own job
  is to guarantee the PIPELINE never crashes on ANY exception the Expert
  might raise, not just the one failure mode the Expert already handles
  gracefully itself.

### Antipatterns to avoid

- Do not assume a task file's own illustrative example values (a `kind`
  name, a customer name) are literally present in a fresh scratch vault —
  verify what the scratch vault's own seeded state actually contains
  before engineering a test decision against it.

### Open follow-ups

- The story-level `gate: flagged` (trigger-1, architect's designed
  `already_filed_path`/`cross_cutting_implication`/tag-write shape) is
  STILL open — this sprint-wrap pass did not resolve it, only carried it
  forward; see `REVIEW-QUEUE.md`.
- Wiring an equivalent `Consult-Librarian` call into `REQ-SB-56`/`57`/
  `58`'s own future pipelines (this story's own Non-Goals, explicitly
  deferred) — the `_route_after_classify`-mirroring list-returning wiring
  pattern documented above is directly reusable when that work is scoped.
- `REQ-SB-57`'s own evidence-change discovery mechanism has not yet been
  extended to scan for the new `customer/<slug>`/`partner/<slug>` tag
  `finalize_cross_cutting_update` writes — a real, disclosed forward
  dependency (architect pass, `REQ-SB-63-US-01`'s own Notes), not a defect
  in this sprint's own Definition of Done.

---

## Notes

**Sprint assembled 2026-08-16 (`/plan-sprints`).** `REQ-SB-63-US-01` enters
`/plan-sprints` `status: Ready`, `gate: flagged` (trigger-1, material
assumption — the architect's designed write-shape; a standing breadcrumb, not
a blocker per the established `REQ-SB-54-US-01`/`SPRINT-048` precedent
explicitly reconfirmed for this pass).

**Gate: `gate: clear` 2026-08-16.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the standalone, single-story
grouping and the sequencing behind `SPRINT-049` are both read directly off the
decomposer's own recorded `depends_on` edges on `T02`/`T03` (confirmed by direct
reading, not guessed); (2) `REQ-SB-63` is not `<!-- Draft -->`/unfinalised;
(3) product-owner does not write ADRs — none was created or changed by this
pass; (4) no new `ESCALATIONS.md` entry; (5) not oversized (3 tasks, S, matching
two prior confirmed-accurate 3-task/S precedents, `SPRINT-023`/`SPRINT-024`);
not a blocked story — every task is `status: Ready`, the real upstream need is
recorded as a genuine `depends_on_sprints: [SPRINT-049]` edge, directly
reflecting the decomposer's own cross-story `depends_on` edges on `T02`/`T03` —
not an artificial edge this role invented, so this does NOT trip the
"cross-sprint dependency you had to introduce" trigger (the same pattern already
established, `gate: clear`, by `SPRINT-012`'s own `depends_on_sprints:
[SPRINT-011]` edge and `SPRINT-026`'s own `depends_on_sprints: [SPRINT-025]`
edge); (6) N/A (coder-only trigger); (7) no contradictory inputs; (8) not
genuinely ambiguous — the sizing-ceiling plus one-directional,
live-verification-gated dependency shape (documented in full on `SPRINT-049`'s
own Grouping Rationale) make two ordered sprints the reasoned call, not an
equally-valid toss-up with one combined 11-task sprint. Advances `Draft →
Ready`.

**BACKLOG.md updated:** `REQ-SB-63` row's Sprint column set to `SPRINT-050`.
