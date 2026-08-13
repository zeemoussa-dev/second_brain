---
id: SPRINT-012
title: Global LLM Provider CRUD, per-agent Provider picker defaulting to Compass
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                        # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro drafted, pending human skim/harvest into Learnings.md; ADR-014's own human review (REVIEW-QUEUE.md) also still open, independent of this sprint's own completion"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-011]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~6 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-11
started: "2026-08-11"                        # YYYY-MM-DD when status → In Progress
completed: "2026-08-11"                      # YYYY-MM-DD when status → Done
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

# SPRINT-012 — Global LLM Provider CRUD, per-agent Provider picker defaulting to Compass

## Sprint Goal

Let the user configure one or more LLM Providers in Global Settings
(Compass pre-seeded as the default) and choose per agent which configured
Provider it uses, with an honest "not available" report — never a silent
fallback or a fabricated response — for any agent pointed at a
not-yet-built Provider; built as a diff on top of `SPRINT-011`'s
already-landed shared `PATCH /agents/{agent_id}` surface and shared
frontend files.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint. `REQ-SB-19-US-01` is the only story
  in this batch whose tasks it covers; its 6 tasks form one acyclic
  dependency graph (`T01 → T02 → T03`, `T04` depends on `T02`, `T05` depends
  on `T03`, `T06` depends on `T04`/`T05`) delivering one coherent,
  independently valuable capability — Provider CRUD + per-agent picker with
  the availability-honesty gate — per the story's own "no independent value
  alone" reasoning. Not splittable across sprints without cutting through
  the middle of a single dependency graph, which would contradict hard
  rule 7.
- **Why sequenced after `SPRINT-011` rather than combined into one sprint:**
  this story's `T04`, `T05`, and `T06` each carry an explicit cross-story
  `depends_on` edge naming a `REQ-SB-18-US-01` task in `SPRINT-011`
  (`T04`, `T07`, `T08` respectively) — the decomposer's own ground truth for
  how the two stories share `agents_router.py`'s `PATCH /agents/{agent_id}`,
  `AgentDetailPanel.tsx`, `agentsApiClient.ts`, `settingsApiClient.ts`, and
  `SettingsPage.tsx`: `REQ-SB-18-US-01` lands the shared surface first, this
  story builds its Provider-portion diff strictly on top, never racing to
  edit the same file in parallel. Honouring that graph (hard rule 7) permits
  either the same sprint or ordered sprints; ordered sprints was chosen
  because (a) combining would total 14 tasks (8 + 6), past this session's
  established ceiling (`SPRINT-010`'s 8 tasks is the largest single-story
  sprint to date; a 15-task combination was explicitly rejected on sizing
  grounds for `SPRINT-009`/`SPRINT-010`), and (b) half of this story's tasks
  are gated on `REQ-SB-18-US-01`'s own near-terminal tasks, meaning this
  story genuinely cannot make meaningful progress on the shared surface
  until `SPRINT-011` is almost entirely built — a real sprint boundary, not
  an invented one. `depends_on_sprints: [SPRINT-011]` records this
  precisely and lets `/implement-sprint` enforce it mechanically (hard
  rule 9) rather than relying on the coder to interleave two stories'
  tasks correctly by hand. Not a genuinely ambiguous partition — not
  flagged.
- **Sizing estimate:** ~6 tasks, M (medium) — matches the calibrated
  4-backend/2-frontend-minus-one shape of this story (3 backend tasks
  building on the shared registry pattern, `T04`'s availability-gate diff on
  `SPRINT-011`'s `agents_router.py` work, 2 frontend tasks extending
  `SPRINT-011`'s already-built `SettingsPage.tsx` composition and
  `AgentDetailPanel.tsx`), directly comparable to `SPRINT-007`'s 6-task M
  combined precedent and smaller than `SPRINT-011`'s 8-task L sibling since
  half this story's frontend/backend surface is a diff on already-landed
  code, not new-from-scratch.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-012 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-19-US-01](../UserStories/REQ-SB-19-US-01-per-agent-llm-provider-selection.md) | Global LLM Provider CRUD in Settings, with a per-agent Provider picker defaulting to Compass | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-011` — `REQ-SB-19-US-01-T04`/`T05`/`T06`
  each carry a task-level `depends_on` naming `REQ-SB-18-US-01-T04`/`T07`/
  `T08` respectively (shared `agents_router.py`, `AgentDetailPanel.tsx`,
  `agentsApiClient.ts`, `settingsApiClient.ts`, `SettingsPage.tsx`
  surface). This sprint cannot start until `SPRINT-011` is `Done`.
  `/implement-sprint` will refuse this sprint otherwise, per hard rule 9.
- The story's own `## Dependencies` confirm no other hard blocker:
  `REQ-SB-12-US-01` and `REQ-SB-13-US-01` (both `Done`) provide the Settings
  page shell and Agent Settings detail panel this story extends.
- `ADR-014` (shared with `REQ-SB-18-US-01`) is still under human review —
  see `REVIEW-QUEUE.md`'s `REQ-SB-18-US-01 / REQ-SB-19-US-01` entry. Per
  `Implementation/Pipeline.md`'s "an ADR-creation flag does not halt
  downstream stages" rule, this does not block sprint assembly; if the
  human's review changes `ADR-014`, the affected task/story `status:`
  should be reset and `/plan-tasks` re-run before this sprint starts.
- No new external-integration surface — this pass builds no real client for
  any Provider other than Compass, per the story's own scope limit.

---

## Out of Scope

- **Building real clients for any Provider other than Compass** — explicitly
  deferred, per the story's own Non-Goals.
- **Falling back to Compass when a selected Provider is unavailable** —
  explicitly rejected behaviour.
- **The Section concept, Section CRUD, or the Section picker** —
  `REQ-SB-18-US-01`/`SPRINT-011`'s scope, already `Done` by the time this
  sprint starts.
- **Removing or replacing Compass's existing `.env`-sourced configuration
  mechanism** — this story adds a Provider entry alongside it, per its own
  Non-Goals.
- **Provider-specific feature differences** (streaming, function-calling
  variance) — out of scope; this pass is about *selecting* a Provider only.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — already landed at the architect pass (2026-08-11); unchanged by this build pass
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-014` already `Accepted` at the architect pass (shared with `REQ-SB-18-US-01`/`SPRINT-011`)
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

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M, built in one
  uninterrupted pass (4 backend + 2 frontend, exactly as scoped; no task
  dropped, split, or added). **Takeaway:** the "diff on top of an
  already-landed shared surface" shape (half the frontend/backend work
  reusing `SPRINT-011`'s own new-file/new-registry/new-router scaffolding
  rather than building it from scratch) sized noticeably lighter in wall-
  clock effort than `SPRINT-011`'s own 8-task L, even though the task
  *count* delta (6 vs 8) undersells how much smaller the actual diff was —
  worth explicitly noting "N tasks, but M of them are diffs on an
  already-Done sibling story" as a sizing signal for future sequenced-pair
  stories, not just raw task count.

### What worked

- **Sequencing behind an already-Done sibling story with explicit
  cross-story `depends_on` edges eliminated all merge/race risk** — every
  shared file (`agents_router.py`, `AgentDetailPanel.tsx`,
  `agentsApiClient.ts`, `settingsApiClient.ts`, `SettingsPage.tsx`) was
  re-read fresh immediately before editing (per `SPRINT-011`'s own retro
  guard), and every one matched what the task files assumed exactly — zero
  surprises, zero escalations. Confirms the pattern is worth repeating for
  any future pair of stories the decomposer sequences this way.
- **Consolidating both trust-surface scenarios (`AC-07` no-regression,
  `AC-08` honest-unavailable) into two deliberate, individually-triggered
  real capture runs**, verified via the agent's own `/history` endpoint
  rather than guessing from the HTTP response alone — confirmed *no* real
  Outlook/Compass call happened for the `AC-08` trigger by checking the
  history's most recent entry was the honest-unavailable message, not a
  masked/silent failure.
- **Precise credential-substring checking (`"credential"` as a bare JSON
  key, not `credential_set`)** — a naive `grep -o "credential"` check
  against a raw response body false-positives on `credential_set`; scoping
  the check to the exact quoted key (`"credential"` with quotes) is what
  actually proves the trust-surface guarantee (`ADR-014` point 5) holds,
  not just that the word "credential" appears somewhere.

### What didn't work

- **A test driver's own `document.querySelector` scoped too broadly across
  two sibling cards on the same page** — `SectionsCard` and `ProvidersCard`
  both render a `form.item-row-actions` with a `button[type="submit"]`;
  an unscoped `document.querySelector('form.item-row-actions
  button[type="submit"]')` silently matched the *first* form in document
  order (Sections' "Create section"), not Providers' "Add provider" —
  producing a misleading "nothing happened" result rather than an error.
  Root cause: page-wide `querySelector` calls are unsafe once two
  structurally-identical card components coexist on one page; always scope
  to the specific card (e.g. by finding the ancestor whose own button text
  or heading disambiguates it) rather than trusting document-order luck.
- **A blocked-in-use Provider's Remove button is genuinely
  React-Fiber-`disabled`, re-triggering `SPRINT-011`'s already-documented
  finding** — a native `.click()` on it silently no-ops; required the same
  Fiber-props direct-invoke workaround `MEMORY.md` already records. Not new
  friction (the pattern was already known and applied immediately), but a
  second confirmation that this project's blocked-delete/blocked-remove UI
  convention (disabled + tooltip, not merely a soft warning) always needs
  this technique to exercise its own error path in live verification.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Scope DOM queries to the specific card/component, never
  `document`-wide, once a page composes two structurally-identical list
  components** (e.g. `SectionsCard` + `ProvidersCard`, both built from the
  same `.item-row`/`form.item-row-actions` shape) — an unscoped
  `document.querySelector` silently matches the wrong sibling's identical
  markup and produces a misleading "no effect" result instead of a clear
  error. Disambiguate via the nearest ancestor carrying a unique heading/
  button-text/data-attribute before querying inside it.
- **Verify a real side-effect's absence via the domain's own audit trail,
  not just the triggering call's response** — confirming `AC-08`'s
  "no real Outlook/Compass call happened" by reading
  `GET /agents/{id}/history` (checking the most recent entry is the honest-
  unavailable message, with no new success entry after it) is stronger
  evidence than trusting the HTTP response alone, since a response could in
  principle be honest while a side effect still silently occurred elsewhere.
- **Precise substring checks for a "field X must never appear in response
  Y" guarantee must match the literal key, not a prefix/superstring of
  it** — checking for the bare `"credential"` JSON key (with its quotes),
  not just the substring "credential" (which false-positives on
  `credential_set`), is what actually proves a credential-never-returned
  trust-surface guarantee (`ADR-014` point 5) rather than merely looking
  like it does.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **A decomposer's own literal code block can omit a sibling-registry
  guard the analogous already-landed module already has** — `T02`'s own
  literal `provider_registry.create_provider` has no same-slug-collision
  guard, unlike `section_registry.create_section`'s explicit "return the
  existing entry rather than duplicate." Found live during `T06`'s
  verification when a test script's own accidental double-POST produced
  two `Provider` entries sharing one `id`. Not a locked-AC failure (no
  scenario requires idempotent-on-name creation) and implemented exactly
  as specified — logged as a scope-internal observation, not fixed
  unilaterally — but worth the decomposer cross-checking a new registry
  module's CRUD shape against its most recent structurally-identical
  sibling (here, `section_registry.py`, built the same sprint) before
  finalizing a task's literal code, not just against the ADR's prose.

### Open follow-ups

- **`ADR-014`'s own human review** (`REVIEW-QUEUE.md` pointer, open since
  the architect pass 2026-08-11, shared with `REQ-SB-18-US-01`) remains
  open — independent of this sprint reaching `Done` (all 8 ACs pass
  against the ADR as currently written). If the human's review changes
  `ADR-014`, the affected task(s)' `status:` should be reset and rebuilt —
  for both stories, since they share the mechanism.
- **`provider_registry.create_provider`'s missing same-slug-collision
  guard** (see Antipatterns above) — worth a small follow-up fix (mirror
  `section_registry.create_section`'s existing-entry check) the next time
  this file is touched, or a standalone `BUGFIX-NN-US-01` if Provider
  creation is ever exposed to a retry-prone client path.
- **`REQ-SB-20-US-01`** (Section Hub Intelligence & Cross-Section Routing)
  now has one of its two blockers satisfied — `REQ-SB-18-US-01` was
  already `Done`; this sprint does not change `REQ-SB-20`'s own remaining
  `/design` blocker (see `REVIEW-QUEUE.md`).

---

## Notes

gate: clear 2026-08-11 — no MUST-FLAG trigger fired for this grouping
decision. This story's own dependency graph (`T01→T02→T03`, `T04`/`T05`/
`T06` per above) is honoured intact, not split across sprints. Not
oversized on its own (6 tasks matches the already-Done `SPRINT-007` 6-task
combined precedent). Not blocked — all 6 tasks and the story itself are
`status: Ready`; the one real upstream need is recorded as a genuine
`depends_on_sprints: [SPRINT-011]` edge, directly reflecting the
decomposer's own cross-story `depends_on` edges on `T04`/`T05`/`T06` — not
an artificial edge this role invented, so this does not trip the
"cross-sprint dependency you had to introduce" trigger (the same pattern
already established, gate: clear, by `SPRINT-009`/`SPRINT-010`'s own
`depends_on_sprints: [SPRINT-008]` edges). Single phase (P1). The choice to
sequence after `SPRINT-011` rather than merge is a reasoned sizing +
dependency-shape call (see `SPRINT-011`'s own Notes for the shared
reasoning), not a genuinely ambiguous partition — recorded above, not
flagged. Advanced `Draft → Ready`.

---

**Sprint assembled (2026-08-11):** 1 story, 6 tasks, `status: Ready`,
`gate: clear`. Eligible for `/implement-sprint` once `SPRINT-011` is `Done`.

**Sprint built (2026-08-11, `/implement-sprint` — coder):** All 6 tasks
built and verified live in dependency order (`T01→T02→T03→T04→T05→T06`),
strictly sequenced on top of `SPRINT-011`'s already-`Done` shared surface.
All 8 locked ACs (`REQ-SB-19-US-01-AC-01`…`AC-08`) confirmed passing
against the real backend and browser — see the story's own Notes and each
task's Implementation Log for full detail. `npm run build` (`tsc -b &&
vite build`) clean. Zero `ESCALATIONS.md` entries this pass; one
scope-internal observation logged (`T02` — see Retrospective). Story
advances `Ready → Done`; sprint advances `In Progress → Done`,
`completed: 2026-08-11`. `gate: flagged` — the retro above is drafted, not
yet human-skimmed/harvested into `Learnings.md`; `ADR-014`'s own human
review (`REVIEW-QUEUE.md`) is a separate, still-open item unaffected by
this sprint reaching `Done` (shared with `REQ-SB-18-US-01`/`SPRINT-011`).
