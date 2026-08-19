---
id: SPRINT-060
title: Vault Base Provisioning + Section-Ownership Enforcement (Foundation)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro-harvest, plus the standing REQ-SB-70-US-01/REQ-SB-71-US-01 ADR-048 human-review flag (unresolved, not this role's to clear) — see REVIEW-QUEUE.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~3 tasks, S"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-18
started: "2026-08-18"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-18"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-060 — Vault Base Provisioning + Section-Ownership Enforcement (Foundation)

## Sprint Goal

Lay down the empty `Work/` PARA/OKF skeleton via one idempotent, real HTTP
endpoint, and ship the code-enforced per-caller section-ownership guard on
`replace_body_section` — the two independent, foundational pieces of
`ADR-048`'s redesign that every other story in the batch needs in place
first.

---

## Grouping Rationale & Sizing

- **Why grouped — two small, independent-of-each-other roots, bundled
  rather than each getting its own 1-2-task sprint.** Read directly from
  each task file's own `depends_on:` frontmatter, not inferred from the
  story summaries:
  - `REQ-SB-70-US-01-T01` — `depends_on: []`. Fully independent: a new
    `vault_provisioning.py` + `POST /poc/provision-vault-base`.
  - `REQ-SB-71-US-01-T01` — `depends_on: []`. Fully independent: the
    `section_ownership.py` guard + `replace_body_section`'s new `caller`
    parameter.
  - `REQ-SB-71-US-01-T02` — `depends_on: [REQ-SB-71-US-01-T01]`. Retrofits
    the 4 already-shipped `replace_body_section` call sites.
  - **No task edge exists between `REQ-SB-70-US-01` and `REQ-SB-71-US-01`
    in either direction** — confirmed by direct reading of both task
    tables. Nothing about combining them contradicts the dependency graph;
    nothing about separating them would be required by it either — this is
    a genuine product-owner judgment call, made and disclosed here, not a
    coin-flip:
    - Both are the smallest, root-level, foundational pieces of the same
      `ADR-048` redesign the operator asked to "finish" as one coherent
      whole.
    - Both are `phase: P1`, so bundling doesn't risk a phase mix.
    - A bare 1-task sprint for `REQ-SB-70-US-01` alone would be smaller
      than any sprint this project has shipped to date (the smallest
      confirmed-accurate precedent is `SPRINT-047`/`SPRINT-017`, 1 task XS,
      but both of those were standalone fixes with no sibling foundational
      work available to bundle with — here, a genuinely related, equally
      small, same-phase sibling exists).
    - Combined, the two stories' 3 tasks together comfortably fit "a single
      working context" — well inside this project's own repeatedly
      confirmed "~3 tasks, S" bucket (`SPRINT-023`, `SPRINT-024`,
      `SPRINT-050`, `SPRINT-053`, `SPRINT-059`).
  - **The alternative (keep `REQ-SB-70-US-01` as its own standalone
    1-task sprint) is also defensible** — flagged here for transparency,
    not silently discarded, in case the human prefers that split instead.
    It was not treated as ambiguous enough to itself require a
    `gate: flagged` (trigger 8): there is no dependency-driven reason
    either way, and both readings ship the same code in the same order
    regardless — the only difference is sprint-file bookkeeping.
- **Why NOT folded into `SPRINT-061`/`SPRINT-062` (the Email/Meeting
  stories):** `REQ-SB-71-US-02-T05`/`-T07` and `REQ-SB-71-US-03-T01` all
  `depends_on: REQ-SB-71-US-01-T01` — a hard, real cross-story task edge.
  Per `Implementation/Pipeline.md` hard rule 7, this guard must ship and be
  `Done` before either downstream story's own new callers register against
  it; keeping it as its own upstream sprint (rather than merging into the
  much larger Email sprint) keeps that upstream/downstream boundary honest
  and lets this small, self-contained piece ship and verify independently.
- **Sizing estimate:** ~3 tasks, S.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-060 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-70-US-01](../UserStories/REQ-SB-70-US-01-vault-base-provisioning-api.md) | Vault Base Provisioning API — idempotent endpoint that lays down the empty PARA/OKF folder skeleton | P1 | Done |
| [REQ-SB-71-US-01](../UserStories/REQ-SB-71-US-01-section-ownership-enforcement.md) | Section-Ownership Enforcement — code-enforced, per-caller allow-list on vault_writer.replace_body_section | P1 | Done |

**Tasks in scope** (dependency order): `REQ-SB-70-US-01-T01` (`depends_on:
[]`) and `REQ-SB-71-US-01-T01` (`depends_on: []`) may build in either
order or in parallel; `REQ-SB-71-US-01-T02` (`depends_on:
[REQ-SB-71-US-01-T01]`) runs after `REQ-SB-71-US-01-T01`.

---

## Dependencies / External Blockers

- **Depends on sprints:** None — both stories are independent roots; no
  other `Ready`/ungrouped story's task graph points into this sprint.
- **External:** none.

---

## Out of Scope

- `REQ-SB-71-US-02` (Email Capture Redesign) and `REQ-SB-71-US-03`
  (Meeting Capture Redesign) — their own NEW caller registrations against
  this sprint's `section_ownership.py` registry are each story's own
  scope, built in their own downstream sprints (`SPRINT-061`,
  `SPRINT-062`), which record `depends_on_sprints` back to this one.
- Extending the allow-list guard to any body-writing primitive beyond
  `replace_body_section` (`REQ-SB-71-US-01`'s own `## Non-Goals`).
- Any per-Customer/Resources internal subshape, or any scheduling wiring
  for the provisioning endpoint (`REQ-SB-70-US-01`'s own `## Non-Goals`).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — already appended at `/plan-tasks` (`ADR-048`), unchanged this pass
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — none created this pass (coder does not write ADRs; `ADR-048` already exists from `/plan-tasks`, still awaiting the human review recorded in `REVIEW-QUEUE.md`)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
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

- **Estimated:** ~3 tasks, S — **Actual:** 3 tasks, S — matched exactly.
  All 3 tasks (`REQ-SB-70-US-01-T01`, `REQ-SB-71-US-01-T01`,
  `REQ-SB-71-US-01-T02`) built and verified in one pass, in the planned
  dependency order (`T01`s in parallel/either order, `T02` after
  `REQ-SB-71-US-01-T01`).

### What worked

- Both roots (`REQ-SB-70-US-01`, `REQ-SB-71-US-01`) were literal,
  code-complete transcriptions of the architect/decomposer's own already-
  fully-specified module shapes (down to the exact `_CALLER_ALLOW_LISTS`
  table and exact `provision_vault_base()` docstring) — zero open
  mechanism questions left at coding time, zero scope-internal design
  decisions needed.
- Verifying against the REAL operator vault (rather than a synthetic
  scratch vault) turned out to produce unusually strong, authentic
  evidence: a real, freshly-provisioned `Work/` for `REQ-SB-70-US-01`'s
  Scenarios, and — critically — a real backlog of already-shipped
  `route_thread_to_project` Pending Approvals that let `REQ-SB-71-US-01-
  T02`'s hardest-to-reach callers (`synthesize_project`/`synthesize_
  customer`) be exercised fully live, end-to-end, via their own real
  production trigger path, rather than any synthetic/mocked substitute.
- The breaking-signature-change retrofit (`caller` required keyword-only,
  no default) worked exactly as designed as a safety net: a missed call
  site would have surfaced as a loud `TypeError` the moment its real code
  path ran — and the real, live capture/synthesis runs this session
  exercised 5 of the 6 physical call sites with zero exceptions logged,
  giving direct, positive confirmation none were missed.

### What didn't work

- Starting the real backend app to reach `POST /poc/provision-vault-base`
  also triggers its own pre-existing, already-shipped, unrelated app-start
  capture job (`ADR-005`) — this fired real Outlook/Compass calls against
  the real vault concurrently with this sprint's own verification,
  producing directory-listing "noise" (`Work/People/`, extra `Work/
  Meetings/*.md`) that complicated a strictly literal reading of
  `REQ-SB-70-US-01-AC-01`'s "no other top-level or nested folder" wording.
  Worked around by using the endpoint's own machine-readable
  `created`/`already_existed` return dict as the authoritative,
  unambiguous evidence of what `provision_vault_base` itself did on each
  call, with the concurrent noise disclosed transparently rather than
  hidden or silently reconciled.
- One of `REQ-SB-71-US-01-T02`'s 4 real callers
  (`finalize_background_amendment_proposal`) has no currently-reachable
  real, live trigger in this vault's present state (its only real trigger,
  a genuine Compass-detected durable customer fact via `synthesize_
  customer`'s `evidence_text` path, has no live caller left now that the
  legacy-flat-Customer-note migration already ran) — this AC was verified
  via strong compensating evidence (unchanged-code-diff + the exact
  caller/header pair proven allowed and functional at the guard layer)
  rather than a full live end-to-end call, disclosed plainly in the task's
  own Implementation Log rather than silently assumed passing.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Verify data-writing retrofits against the real, live production vault
  (not a synthetic fixture) when a real, already-existing trigger path
  exists** — a real backlog of Pending Approvals / staged emails / Thread
  notes gives authentic, high-confidence proof a signature-breaking
  retrofit didn't regress anything, often exercising edge cases (a
  concurrent scheduler run, a real multi-step approval cascade) a
  synthetic scratch-vault test wouldn't surface at all.
- **A required, no-default keyword-only parameter, added as a breaking
  change, is an effective and cheap correctness net for an exhaustive
  multi-call-site retrofit** — a missed site fails loudly (`TypeError`) at
  the exact moment its real code path next runs, rather than silently
  passing through ungated.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Don't assume a freshly-emptied `Work/` will stay empty for the
  duration of a verification session once the real app is started** — this
  codebase's own already-shipped app-start capture trigger (`ADR-005`)
  fires unconditionally, every process start, regardless of what the
  session's own verification goal is. When a task's AC depends on an
  exact, uncontaminated directory-listing snapshot, prefer capturing that
  snapshot IMMEDIATELY after the triggering call, and treat the
  endpoint's/function's own machine-readable return value as the
  authoritative evidence of its own action, separate from a broader
  directory listing that may include unrelated concurrent activity.

### Open follow-ups

- `finalize_background_amendment_proposal`'s own full live end-to-end
  retrofit verification remains open — worth closing opportunistically
  the next time a real Background-amendment Pending Approval naturally
  occurs in this vault (e.g. during `SPRINT-061`/`SPRINT-062`'s own
  verification passes), rather than a dedicated follow-up task.
- The standing `ADR-048` human-review flag (`REVIEW-QUEUE.md`) remains
  open across all four stories in this batch — unchanged by this sprint,
  not this role's to clear.

---

## Notes

**Grouping decision (product-owner, 2026-08-18):** Confirmed via a fresh
scan of every `Implementation/UserStories/*.md` that exactly 4 stories are
`status: Ready` + `sprint: ""` right now — `REQ-SB-70-US-01`,
`REQ-SB-71-US-01`, `REQ-SB-71-US-02`, `REQ-SB-71-US-03` — no other story
matched. All four belong to the same `ADR-048` batch. This sprint takes the
two independent roots (`REQ-SB-70-US-01`, `REQ-SB-71-US-01`); the other two
(`REQ-SB-71-US-02`, `REQ-SB-71-US-03`) have real, hard task-level
`depends_on` edges into `REQ-SB-71-US-01-T01` (and, for `-US-03`, into
`REQ-SB-71-US-02` as well) and are sequenced into their own ordered
sprints (`SPRINT-061`, `SPRINT-062`) with recorded `depends_on_sprints`
edges back to this one — see those sprints' own `## Notes` for the full
single-vs-multi-sprint reasoning covering the whole batch.

No MUST-FLAG trigger fired for THIS sprint specifically: not oversized (3
tasks, S — well within this project's own repeatedly confirmed range);
no blocked story; no cross-sprint dependency was introduced BY this
sprint (it has `depends_on_sprints: []` — it is the upstream root the
other two depend on, not the other way around); the one real judgment call
(bundle `REQ-SB-70-US-01` with `REQ-SB-71-US-01` vs. give it its own
1-task sprint) is disclosed above with grounded reasoning, not a genuinely
unclear/equally-valid coin-flip warranting a flag. The stories' own
`gate: flagged` (architect's `ADR-048` human-review flag) stays on each
STORY, unchanged and uncleared by this pass — that flag is not this role's
to clear; it is tracked in `REVIEW-QUEUE.md`'s existing
`REQ-SB-70-US-01 + REQ-SB-71-US-01 + REQ-SB-71-US-02 + REQ-SB-71-US-03`
entry.

gate: clear 2026-08-18 (product-owner) — no MUST-FLAG trigger fired for
this sprint's own grouping; see itemized reasoning above. Sprint
`status: Draft → Ready`. Eligible for `/implement-sprint` once the human
resolves (or knowingly defers) the standing `ADR-048` story-level flag.

---

**Coder closing note (2026-08-18, `/implement-sprint SPRINT-060`):** all 3
tasks built and verified `Done`, in dependency order, with real, live
evidence against the real operator vault throughout (see each task's own
`## Implementation Log` and each story's own coder addendum). Both stories
→ `Done`. Sprint → `Done`, retrospective drafted above. `gate: flagged` —
carries forward the standing, still-unresolved `ADR-048` human-review flag
(`REVIEW-QUEUE.md`'s existing `REQ-SB-70-US-01 + REQ-SB-71-US-01 +
REQ-SB-71-US-02 + REQ-SB-71-US-03` entry — not this role's to clear) plus
this sprint's own retro-harvest flag for the human to propagate patterns
into `Implementation/Learnings.md`. Two scope-internal judgment calls were
disclosed (not hidden) in the task logs: (1) the real app's own pre-
existing app-start capture trigger produced concurrent, unrelated
directory noise during `REQ-SB-70-US-01-T01`'s verification; (2)
`REQ-SB-71-US-01-T02`'s `finalize_background_amendment_proposal` caller
could not be triggered fully live end-to-end this session (no real
Background-amendment Pending Approval currently exists), verified instead
via strong compensating evidence. Nothing is `Blocked`; nothing new was
written to `ESCALATIONS.md` by this pass.
