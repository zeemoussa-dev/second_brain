---
id: SPRINT-042
title: Skills Grouped-by-Tool Tree (AgentDetailPanel Capabilities) + Vault Scope Tag/Folder Autocomplete
status: Done                        # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "coder drafted retro below — human to skim and propagate Learnings; REQ-SB-48-US-01 also carries its own flagged items in REVIEW-QUEUE.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-14
started: "2026-08-14"               # YYYY-MM-DD when status → In Progress
completed: "2026-08-14"             # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-042 — Skills Grouped-by-Tool Tree + Vault Scope Autocomplete

## Sprint Goal

Ship two small, independent, `gate: clear` P1 enhancements to the agent
detail Settings surface: `REQ-SB-48-US-01`'s collapsible icon-bearing
multi-select Skills tree (grouped by Tool) replacing the flat Capabilities
list, and `REQ-SB-50-US-01`'s real, vault-derived tag/folder autocomplete
on the Vault Scope field.

---

## Grouping Rationale & Sizing

- **Why grouped:** both stories are small (2 tasks each), `gate: clear`,
  P1, and land on the exact same real screen/file
  (`AgentDetailPanel.tsx`'s Settings tab) without touching each other's
  own rows (Capabilities section vs. Vault Scope kv-row) or overlapping
  any `depends_on` edge — confirmed by reading both stories' own real task
  tables directly (`REQ-SB-48-US-01-T01→T02`; `REQ-SB-50-US-01-T01→T02`,
  no cross-story edge either direction). Combining two small, unrelated-
  but-adjacent, unambiguous stories into one sprint avoids two separate
  single-digit-task sprints, matching this project's own established
  "combine small independent same-phase clear-gate stories for efficient
  sizing" practice (distinct from forcing a dependency-linked pair
  together) — a cohesion-by-size rationale, not a shared-mechanism one.
- **Why `REQ-SB-48-US-01` is sequenced first within this sprint (not a
  hard requirement, but the sensible order):** `REQ-SB-46-US-01`'s own
  Step-3 task (`REQ-SB-46-US-01-T04`, sequenced into `SPRINT-043`) carries
  a real, locked `depends_on: REQ-SB-48-US-01-T02` edge — this codebase's
  first cross-story frontend task dependency (`ADR-039`). Landing
  `REQ-SB-48-US-01` in this earlier sprint, ordered before `SPRINT-043`,
  satisfies that edge per the task's own explicit instruction ("the
  product-owner is expected to sequence `REQ-SB-48-US-01` no later than
  the same sprint as, and ordered before, this task"). Chosen here over
  merging `REQ-SB-46-US-01` into this same sprint specifically to keep
  both sprints within this project's own proven sizing band — mirrors the
  identical, already-successful `SPRINT-040`→`SPRINT-041` precedent
  (`REQ-SB-44-US-01`'s cross-story edges onto `REQ-SB-43-US-01`, resolved
  via `depends_on_sprints` rather than one combined ~15-task sprint).
- **Sizing estimate:** ~4 tasks, S (`REQ-SB-48-US-01`: 2 tasks;
  `REQ-SB-50-US-01`: 2 tasks) — comfortably below this project's own
  observed sizing ceiling (L ≈ 9 tasks, `Implementation/Learnings.md`).

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-48-US-01](../UserStories/REQ-SB-48-US-01-skills-grouped-by-tool-collapsible-tree.md) | Skills Capabilities Tree — Collapsible, Icon-Bearing, Multi-Select Groups by Tool | P1 | Done (gate: flagged) |
| [REQ-SB-50-US-01](../UserStories/REQ-SB-50-US-01-tags-and-locations-autocomplete.md) | Tags and Locations Autocomplete — Vault Scope field | P1 | Done (gate: clear) |

---

## Dependencies / External Blockers

- **Depends on sprints:** None
- No external blockers. `REQ-SB-48-US-01`'s own `SkillsTree.tsx` shape is
  now locked at the task level (its `## Files to Modify` was amended
  2026-08-14 to mandate the exact mode-parameterized filename/prop shape
  `SPRINT-043`'s `REQ-SB-46-US-01-T04` depends on) — the coordination gap
  the decomposer originally flagged in `REVIEW-QUEUE.md` is already
  closed at the artefact level; only `ADR-039`'s own human review (tracked
  against `REQ-SB-46-US-01`/`SPRINT-043`) remains open.

---

## Out of Scope

- `REQ-SB-46-US-01`'s own Step-3 `mode="select"` consumption of
  `SkillsTree.tsx` — that is `SPRINT-043`'s scope, ordered after this one.
- `CreateAgentWizard.tsx`'s own Worker-step Vault Scope field — explicitly
  deferred by `REQ-SB-50-US-01`'s own Non-Goals to a future follow-on once
  `REQ-SB-46` ships.

---

## Definition of Done

- [ ] Every story in scope has status `Done`
- [ ] All story-level Definitions of Done satisfied
- [ ] `BACKLOG.md` updated — every affected row reflects current status
- [ ] `architecture.md` updated if the sprint changed an architectural fact
- [ ] Any new ADRs recorded in `ADR.md` with status `Accepted`
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended
- [ ] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — matched exactly.
  Task count and split (1 backend + 1 frontend per story) held with zero
  re-scoping. The frontend tasks were correctly the heavier of each pair,
  but not disproportionately so — both real UI tasks needed a genuinely
  non-trivial live-verification pass (a full CDP session, `window.fetch`
  spy, multiple real agents) to cover all their locked ACs, matching this
  project's own established "verification cost, not code volume, drives
  real effort" pattern.

### What worked

- **Building `SkillsTree.tsx` exactly to the task's amended, locked-down
  shape** (standalone file, `mode="manage" | "select"` discriminated
  union, a minimal-but-real `mode="select"` seam) removed all ambiguity
  about what `SPRINT-043`'s own `REQ-SB-46-US-01-T04` will find waiting
  for it — confirmed live and structurally, not just by reading the code.
- **A UI-free, direct Python-shell repro of a suspicious frontend
  observation** (a revoke that visually "stuck" then silently reverted)
  immediately separated "bug in this task's own new code" from "bug in an
  out-of-scope shared primitive," turning a confusing live-test anomaly
  into a confidently-diagnosed, correctly-scoped `BUGS.md` entry
  (`BUG-013`) in one extra step rather than several.
- **Choosing a non-migration-seeded Skill/agent pair to re-verify AC-06
  honestly, once `BUG-013` was found**, kept the locked AC's own real
  guarantee (a durable revoke) genuinely proven, rather than either
  reporting a false pass or blocking the task on an out-of-scope defect.
- **The project's own established Fiber-props direct-`onBlur`-invoke
  technique (`SPRINT-020`) generalized cleanly a further time** — a raw
  synthetic `blur` `dispatchEvent` again failed to reach React's
  delegated listener in this same CDP environment, on a completely
  different input/handler than the one that originally surfaced the
  antipattern.

### What didn't work

- **Trusting a `uvicorn --reload` restart had picked up a second,
  closely-timed file edit** (`vault_search_router.py`, edited moments
  after `vault_search.py`) — `WatchFiles` silently kept serving a stale
  worker returning `404` for the new route for several requests, exactly
  `SPRINT-035`'s own already-documented failure mode. Recovered via the
  same specific-PID-kill-and-restart protocol, this time switching to a
  non-`--reload` instance for the rest of the session.
- **Assuming a raw `dispatchEvent(new FocusEvent('blur', {bubbles:
  true}))` would reach a React `onBlur` handler** cost one avoidable
  round trip before switching to the Fiber-props direct-invoke technique
  — should have gone there first, given this project's own prior
  documented finding for the identical handler class.

### Patterns to carry forward

- **UI-free, direct-function-call repro as the fastest way to separate
  "my new code" from "a pre-existing shared dependency"** — whenever a
  live UI observation looks wrong, reproduce it one layer down (a plain
  backend/business-function call) before assuming the newly-written
  frontend code is at fault.
- **When a locked AC's own named example value doesn't exist in the real,
  current data** (a real folder name, a real Skill/agent pair), verify
  the AC's actual underlying guarantee against the closest real
  substitute and disclose the substitution explicitly, rather than either
  fabricating the named example or blocking the task.

### Antipatterns to avoid

- **Assuming two file edits made moments apart will both be picked up by
  the same `--reload` cycle** — reconfirmed a further time
  (`SPRINT-035`→`SPRINT-042`); smoke-check the newest edited route with a
  live request before trusting a reload-based dev server mid-session.
- **Dispatching a raw, non-bubbling-in-reality `blur`/`focus` DOM event
  and assuming it reaches a React `onBlur`/`onFocus` prop** — always use
  the Fiber-props direct-invoke technique for this handler class from the
  first attempt, not after a failed try.

### Open follow-ups

- `BUG-013` (`skill_registry._load_state` re-applies its migration seed
  on every state read, silently un-revoking 7 specific Skill/agent pairs)
  — filed in `BUGS.md`/`ESCALATIONS.md` (`ESC-035`), recommended for
  `/triage`. Not blocking — `AC-06` was independently re-verified against
  an unaffected Skill/agent pair.
- Two scope-internal judgement calls from `REQ-SB-48-US-01-T02` (the
  `mode="select"` seam's own minimal implementation; the `BUG-013`
  finding) parked in `REVIEW-QUEUE.md` for human spot-check before
  `SPRINT-043` starts building on `SkillsTree.tsx`.
