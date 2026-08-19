---
id: SPRINT-046
title: Cockpit @Mentions — inline @agent_id bring-in + @PersonName proposed Person-note edit
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "trigger-3 (ADR-038 created, carried from REQ-SB-49-US-02) — standing human-review breadcrumb; did not block the build, all tasks Done and all ACs verified live"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~7 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-14
started: "2026-08-14"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-14"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-046 — Cockpit @Mentions

## Sprint Goal

Build both halves of `REQ-SB-49` (Cockpit @Mentions) end to end: the
inline `@agent_id` bring-in shortcut (`REQ-SB-49-US-01`) and the
`@PersonName` person-directed-instruction proposed Person-note edit
(`REQ-SB-49-US-02`, gated per `ADR-038` through the existing working-mode
mechanism) — both sharing the same Cockpit chat-input/thread surface.

---

## Grouping Rationale & Sizing

- **Why grouped:** the two stories are literal siblings under the same
  requirement (`REQ-SB-49`), split at `/spec` time purely for independent
  shippability ("no independent value alone" test), not because they are
  unrelated — both parse the same human-facing `@` convention on the same
  real file (`Cockpit.tsx`'s chat input/thread), and each story's own
  Dependencies section explicitly names the other as sharing "the same
  chat-input parsing surface." Building them in the same sprint keeps that
  one real shared file's edits close together in one working session
  rather than split across two separately-sequenced sprints re-reading the
  same file cold.
- **Confirmed NOT a hard `depends_on` edge either direction** — the
  decomposer's own `REQ-SB-49-US-02` pass traced both real/planned call
  chains directly: `REQ-SB-49-US-01`'s mechanism is a deterministic,
  client-side regex parse at send time; `REQ-SB-49-US-02`'s mechanism is
  the model's own free-text tool-calling interpretation of the raw message
  text reaching the backend unmodified — zero shared code, two different
  layers. This sprint's own combination is therefore a cohesion choice
  (shared requirement + shared file), not a dependency-forced one; task
  execution order within the sprint (`REQ-SB-49-US-01-T01` before
  `REQ-SB-49-US-02`'s 6 tasks, or vice versa) has no correctness
  requirement either way.
- **Sizing estimate:** ~7 tasks, M (`REQ-SB-49-US-01`: 1 task;
  `REQ-SB-49-US-02`: 6 tasks) — within this project's own observed M band
  (6-8 tasks), below the L ceiling (≈9 tasks).
- **Story-level `gate: flagged` (on `REQ-SB-49-US-02` only) carried, not
  re-flagged by this sprint:** `REQ-SB-49-US-02` stays `gate: flagged`
  (`ADR-038` human review still outstanding, tracked in
  `REVIEW-QUEUE.md`); `REQ-SB-49-US-01` is `gate: clear`. Per
  `.claude/agents/product-owner.md`'s own closed list of 4 sprint-level
  flag triggers, none fired for this grouping decision — the combination
  is a deliberate, defensible cohesion call (same requirement, same file,
  no forced/ambiguous split), not oversized, not blocked, and introduces
  no cross-sprint dependency. `gate: clear`, advance to `Ready`.

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-49-US-01](../UserStories/REQ-SB-49-US-01-cockpit-inline-agent-mention-bring-in.md) | Cockpit Inline @agent_id Mention — Bring an Agent Into the Shared Thread | P1 | Done |
| [REQ-SB-49-US-02](../UserStories/REQ-SB-49-US-02-cockpit-person-mention-proposed-note-edit.md) | Cockpit Person-Directed Instruction (@PersonName) — Agent Proposes a Gated Person-Note Edit | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None
- **Outstanding, human-owned, not resolved by this pass:** `ADR-038`
  itself still needs human review before the coder builds
  `REQ-SB-49-US-02`'s tasks (tracked in `REVIEW-QUEUE.md`). Not resolved
  or duplicated here — already tracked at the story level.
- **Soft, same-source coordination note (not a hard `depends_on`), carried
  from `REQ-SB-49-US-01`'s own architect pass:** both this sprint's
  `REQ-SB-49-US-01` and `SPRINT-044`'s `REQ-SB-51-US-01` read the same
  `fetchAgentList()`-sourced candidate list for `@mention`
  matching/bring-in. Either build order works; whichever lands second may
  need a small, same-file follow-on edit to repoint its own source at the
  other's filtered variable. Not sequenced via `depends_on_sprints` here
  since neither build order is incorrect.

---

## Out of Scope

- Fuzzy/ranked `@agent_id` matching, or a new backend bring-in mechanism
  (`REQ-SB-49-US-01`'s own Non-Goals).
- Full NLU-driven, unbounded vault editing, or creating a new Person note
  from a bare `@mention` (`REQ-SB-49-US-02`'s own Non-Goals).
- Resolving `ADR-036`'s gate-bypass-vs.-this-requirement's-own-gating
  tension beyond what `ADR-038` already resolved.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, no architecture change this pass (both stories composed with already-recorded designs from the architect's own `/plan-tasks` pass)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, `ADR-038` was already `Accepted` before this sprint's build started; confirmed to hold up exactly as designed under live verification, no new ADR needed
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~7 tasks, M — **Actual:** 7 tasks, M — matched exactly.
  `REQ-SB-49-US-01-T01` (1 task) and `REQ-SB-49-US-02-T01`-`T06` (6 tasks)
  both built and verified in one working session with zero task
  splits/merges. `REQ-SB-49-US-02`'s own tasks were correctly the heavier
  half — not in code volume (each task's diff was small and additive) but
  in live-verification cost: two real, load-bearing integration bugs only
  surfaced once the whole chain was driven end-to-end through the real
  running frontend, not from any single task's own isolated smoke check.

### What worked

- **Both stories' own "no real dependency, shared file only" analysis
  held up exactly as the decomposer predicted** — `REQ-SB-49-US-01-T01`
  and `REQ-SB-49-US-02`'s six tasks were built in the same session with
  zero merge conflicts on `Cockpit.tsx`, confirming the decomposer's own
  reasoning that the two mechanisms operate at genuinely different layers
  (deterministic frontend regex vs. backend LLM tool-calling) with no
  shared code.
- **The `REQ-SB-51-US-01` soft-dependency instruction ("if it lands
  first, wire against its filtered `bringInCandidates`") resolved cleanly
  with zero ambiguity** — the real current `Cockpit.tsx` already had the
  filtered variable, so `T01` wired directly against it, exactly as the
  story's own Notes anticipated.
- **A from-scratch Node native-`fetch`/`WebSocket` CDP client (no
  Playwright/Puppeteer) against a headless Edge instance, launched on its
  own dedicated `--remote-debugging-port`/isolated `--user-data-dir`,
  proved every locked AC across both stories end-to-end** — real browser,
  real DOM, real network calls, real LLM replies, including the harder
  multi-step flow (mention → bring-in → reply; instruction → proposal →
  confirm/discard → real vault write) with zero mocking.
- **Verifying the Supervised gate path via direct `invoke_skill`/real
  Approve-endpoint calls (never the graph/LLM layer) and the Manual/
  Autonomous "propose" path via real live model calls was the right
  split** — `AC-02` (Supervised) doesn't need a real LLM call at all
  (deterministic dispatch), while `AC-01`/`AC-04`/`AC-05` (Manual/
  Autonomous) genuinely do (the model's own free-text interpretation is
  what triggers the tool) — matching exactly how the decomposer had
  already scoped each task's own `depends_on`/Tests.

### What didn't work

- **A task's own illustrative code sample can be stale even against a
  file that same sprint's sibling task is about to touch** — `T02`'s own
  `SKILLS` entry sample omitted the `"tool"` field a DIFFERENT,
  already-`Done` sprint (`REQ-SB-48-US-01`) had made mandatory for every
  entry; this only surfaced as a real `KeyError` on a live
  `PATCH /agents/{id}` call once `people-producer` was actually granted
  the new Skill — no isolated Python-shell smoke check would have caught
  it, since `list_agent_capabilities` is only reached via the HTTP
  `agents_router.py` layer.
- **A single-in-memory-object, save-once-at-the-end function
  (`send_user_message`) is silently unsafe the moment ANYTHING it calls
  mid-flight (here, a Skill dispatched from inside its own per-agent
  reply loop) does its own independent read-modify-write round trip on
  the SAME persisted record** — this is a structurally new hazard class
  this story introduced (the first time a Cockpit-originated Skill
  dispatch mutates the SAME thread record `send_user_message` itself is
  mid-way through building), and it only surfaced via a real end-to-end
  UI round trip, never a unit-level check of either function in
  isolation.
- **`uvicorn --reload`'s `WatchFiles` restart can get genuinely stuck
  (not just serve-stale-briefly) when the worker is continuously busy
  with a real, recurring background task** (this project's own autonomous
  capture scheduler tick) — reconfirms, and sharpens, `SPRINT-035`'s
  existing Learnings entry: "stuck," not just "briefly stale," is a real
  observed failure mode, costing several real minutes of polling before
  the documented kill-and-restart fix was applied.

### Patterns to carry forward

- **When a story's own mechanism composes with an already-`Done`,
  cross-cutting registry/gate (here, `skill_registry`'s `SKILLS` catalog
  and two-axis gate), verify the NEW entry against every real consumer of
  that catalog via at least one HTTP-layer call, not just the new Skill's
  own handler in isolation** — a purely business-layer smoke check would
  have missed the `"tool"`-field requirement entirely.
- **When a task threads a new optional parameter through an existing
  function that itself calls into a NEWLY-Skill-gated capability
  mid-body, explicitly ask "does anything this function calls now
  persist to the SAME record this function itself will also save" before
  trusting a single-save-at-the-end shape** — worth a standing question
  for any future task that adds a nested, self-persisting dispatch inside
  an already-established single-owner save function.

### Antipatterns to avoid

- **Trusting a task's own illustrative code sample's "already imports
  X" claim without grepping the real current file first** — cost one
  avoidable `ModuleNotFoundError`-class fix cycle (`Path` in
  `vault_writer.py`) that a 5-second grep would have caught before
  writing the diff.
- **Polling a stuck `WatchFiles` reload for more than ~30-45s without
  proactively checking whether the worker is continuously busy with an
  unrelated real background task** — should pivot to the documented
  kill-and-restart fix sooner rather than waiting to see if it resolves
  on its own.

### Open follow-ups

- **Disambiguating two real, identically-named Person notes for
  `find_person_note_by_name`** — not filed as a bug (no locked AC in this
  story asserts this behavior; the resolver correctly never fabricates a
  match), but worth a human decision on whether a future story should add
  email/company-scoped disambiguation if this vault-data condition
  (two "Mahmoud Moussa" Person notes) is more than a one-off.
- **`REQ-SB-49-US-02`'s `gate: flagged` (trigger-3, `ADR-038`) remains
  open for human review** — the architectural decision itself still
  needs the human's explicit sign-off per the standing `REVIEW-QUEUE.md`
  entry; this sprint's own build confirms `ADR-038` works exactly as
  designed, which is new evidence for that review, not a substitute for
  it.
