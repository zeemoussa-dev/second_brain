---
id: SPRINT-067
title: Bidirectional Thread ↔ Message Linking (Retrofit + Rename-Safe)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "sprint-wrap retro drafted — human skim + Learnings.md propagation; ADR-054 review also still standing"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-19
started: "2026-08-19"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-19"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-067 — Bidirectional Thread ↔ Message Linking (Retrofit + Rename-Safe)

## Sprint Goal

Ship the Librarian's new `link_thread_messages()` Job — a real `## Messages`
rollup on every Thread and a real, self-healing `thread:` backlink on every
raw message, kept correct across Thread renames by extending
`rename_threads()` itself — then retrofit the whole real corpus (137
Threads / 257 messages).

---

## Grouping Rationale & Sizing

- **Single story, one sprint.** All 4 tasks belong to `REQ-SB-73-US-01`, one
  Definition of Done, one architecture scope (`architecture.md` → "The
  Librarian — Bidirectional Thread ↔ Message Linking", `ADR-054`). Graph
  read directly from each task file's own `depends_on:` frontmatter (per
  the decomposer's own recorded reasoning in the story's Decomposer pass):
  - `T01` (`link_thread_messages()` Job + `## Messages` header primitive +
    `section_ownership.py` entry + `vault_indexing.py` extension) —
    `depends_on: []`, root.
  - `T02` (`rename_threads()` fan-out extension) — `depends_on: []`,
    independent root — a different function, composing already-shipped
    primitives, zero shared new code with `T01`.
  - `T03` (Job-chain wiring + new endpoint) — `depends_on: [T01]`.
  - `T04` (full-corpus retrofit run + idempotency re-run) —
    `depends_on: [T01, T02, T03]` — needs the Job, the fan-out extension
    deployed alongside it (so the retrofit run exercises the same shipped
    state the story ships as one unit), and the real reachable endpoint.
  - Acyclic, all `phase: P1`.
- **Not split further** — `T01`/`T02` are independent roots, but both feed
  the same single-story assembly (`T03` → `T04`); splitting them into
  separate sprints would add a needless `depends_on_sprints` edge for zero
  real decoupling value (same antipattern already named in `SPRINT-063`'s
  own `## Notes`), since `T04`'s own idempotency proof needs BOTH `T01` and
  `T02` shipped together regardless of sprint boundaries.
- **Not bundled with `REQ-SB-74-US-01`** — see `## Notes` below for the
  full independence reasoning (both stories add Jobs to the same
  `librarian_housekeeping.py`/`email_poc_router.py` files, but the
  decomposer explicitly confirmed zero task-level `depends_on` edge in
  either direction between the two stories' task sets).
- **Sizing estimate: ~4 tasks, S.** Matches this project's own repeatedly-
  confirmed "~4 tasks, S" bucket (`SPRINT-008`, `SPRINT-019`, `SPRINT-025`,
  `SPRINT-027`, `SPRINT-036`, `SPRINT-042`) and sits well under the
  `librarian_housekeeping.py` module's own proven 9-task/L ceiling
  (`SPRINT-063`). Not oversized.

---

## Stories in Scope

<!-- Bidirectional link written at sprint creation: REQ-SB-73-US-01's own
frontmatter now carries sprint: "SPRINT-067". Order by implementation
dependency (dependency-first). -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-73-US-01](../UserStories/REQ-SB-73-US-01-bidirectional-thread-message-linking.md) | Bidirectional Thread ↔ Message Linking (Retrofit + Rename-Safe) | P1 | Done |

**Tasks in scope** (dependency order): `T01` and `T02` independent roots →
`T03` (needs `T01`) → `T04` (needs `T01`, `T02`, `T03`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. `REQ-SB-72-US-01` (`SPRINT-063`, Done),
  `REQ-SB-71-US-02` (`SPRINT-061`, Done), and `REQ-SB-71-US-01`
  (`SPRINT-060`, Done) are the story's own hard prerequisites — all already
  `Done`, so no NEW cross-sprint dependency is introduced by this sprint
  (confirmed directly: every one of this story's own 4 tasks' `depends_on`
  edges resolves to another task WITHIN this same story/sprint).
- **External:** none new — the real, already-configured vault this Job
  retrofits/extends (137 real Thread directories, 257 real raw message
  notes, confirmed live 2026-08-19).

---

## Out of Scope

- Stage 1 capture writing `thread:`/`## Messages` synchronously at capture
  time — explicitly deferred by the PRD; enrichment stays the Librarian's
  job, on its next scheduled/triggered pass.
- `REQ-SB-60` Conversation-level merging of related Threads — a separate,
  still-unspec'd P2 requirement.
- Backfilling any pre-`REQ-SB-71-US-02` flat-shape Thread notes, if any
  remain — the same disclosed carve-out `REQ-SB-72-US-01` already
  established (`ESC-048`), not reopened here.
- Any new screen or UI widget — the already-shipped, generic backlinks/
  graph-view machinery (`REQ-SB-14-US-01`) is the entire presentation
  layer this story needs.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (already done at the architect pass, `ADR-054`; no further change this stage)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-054`, already `Accepted` from the architect pass; unchanged by the coder)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints (none new emerged beyond `ADR-054`'s own already-recorded decision — see `## Retrospective` below)
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S, zero net code deviation from `ADR-054`'s own Decision text (no new `vault_writer.py` primitive turned out to be needed, confirming the architect's own premise) — **Takeaway:** exact match, extending this project's own repeatedly-confirmed "~4 tasks, S" bucket (`SPRINT-008`/`019`/`025`/`027`/`036`/`042`) one more time. The one real surprise was entirely on the VERIFICATION side, not the code side — see "What didn't work" below.

### What worked

- **Function-level proof before HTTP-level proof, applied consistently across all 4 tasks** — `T01`/`T02` verified entirely via direct Python-shell calls against the real vault before any endpoint existed (`T03`), mirroring `REQ-SB-72-US-01`'s own established technique; this let every locked AC on `T01`/`T02` be genuinely, immediately verified without waiting on wiring work.
- **The architect's own "reuse, don't invent" premise held exactly as designed** — `link_thread_messages()` and the `rename_threads()` fan-out really did compose entirely from `insert_body_section_if_missing`/`replace_body_section`/`upsert_frontmatter_key`/`list_thread_notes`, zero new `vault_writer.py` code, confirmed by the actual build, not just the ADR's own claim.
- **Real, live collisions during `T02` verification (5 genuine `<date> <subject>` stem collisions already present in the corpus) were caught and reported exactly as `rename_threads()`'s own pre-existing collision handling was designed to** — a real-world stress test the task's own Tests block anticipated but didn't manufacture, and it worked correctly on the first real encounter.
- **A tight-window, back-to-back before/afterA/afterB hash comparison (`T04`) fully isolated the true idempotency signal from unrelated concurrent activity** — once identified, narrowing the comparison window to two consecutive endpoint calls (rather than a longer before/first-run/second-run span) produced a clean, zero-diff, byte-for-byte proof across all 390 real files.

### What didn't work

- **Every fresh `uvicorn` instance started for endpoint verification (`T03`/`T04`) automatically fires the app's own already-shipped startup-scheduled jobs** (`run_capture_if_idle`, real Compass calls) as a side effect of merely starting the server for testing — not something either task's own Tests block called out, and it produced two confounding, real (but unrelated-to-this-story) file changes on the first `T04` hash comparison (a `## Files`/`**Customer:**` write from an already-shipped, out-of-scope Job) before the confound was identified and isolated. Root cause: this project's own dev-server startup behavior (`architecture.md`'s "Local Development" note already discloses the EMAIL capture leg of this; the Librarian's own 6-hour housekeeping schedule firing on startup too was not previously called out there).
- **Two concurrent coder sessions (this sprint and the sibling `REQ-SB-74-US-01`/`SPRINT-068`) editing the SAME `librarian_housekeeping.py`/`email_poc_router.py` files at the same time** required extra care on every `Edit` call to this task's own file scope (re-reading current state before each edit rather than trusting a stale mental model) — no real conflict occurred (the two stories' own insertion points never overlapped, as the decomposer had already confirmed), but it added real verification overhead this task's own estimate didn't explicitly account for.
- **An already-running shared dev server on the default port (owned by the concurrent session) meant this task's own endpoint verification needed its own dedicated, isolated port** — a small but real extra step neither task file anticipated.

### Patterns to carry forward

- **Isolate verification instances on a dedicated port when a shared dev server may already be running (concurrent sessions, or a stale process)** — apply whenever `/implement-sprint` needs to hit a real HTTP endpoint for verification and cannot assume exclusive ownership of the default port.
- **For any real byte-for-byte idempotency proof, minimize the time window between the two compared states (back-to-back calls), not just "before the first run" vs. "after the second run"** — a live, already-scheduled background process (this app's own scheduler, or a concurrent session) can otherwise write unrelated changes into the same window and produce a false-positive "not idempotent" reading that has nothing to do with the function actually under test.

### Antipatterns to avoid

- **Starting a fresh `uvicorn` instance purely for endpoint verification without first accounting for its own startup-scheduled side effects** — every start fires real, already-scheduled Jobs (email capture, and potentially the Librarian's own housekeeping schedule) against the real vault, which can contaminate a tightly-scoped verification window if not anticipated; wait for the startup burst to visibly settle (e.g. a stable count of outbound API calls in the server log) before capturing a "baseline" state for any before/after comparison.

### Open follow-ups

- **Document the Librarian's own housekeeping schedule firing on app startup in `architecture.md`'s "Local Development" note**, alongside the already-documented email-capture leg — a real gap found live this sprint, worth a small doc-only follow-up (not filed as a story; flagged here for the human to route as they see fit).

---

## Notes

**Grouping decision (product-owner, 2026-08-19):** Two `Ready`, ungrouped
stories existed this pass — `REQ-SB-73-US-01` (this sprint) and
`REQ-SB-74-US-01` (`SPRINT-068`). The decomposer's own task-level
`depends_on` graph confirms no edge exists between the two stories' task
sets in either direction (each story's own Decomposer pass states this
explicitly). Both are `phase: P1` and both add Jobs to the SAME
`librarian_housekeeping.py`/`email_poc_router.py` files, but that is a
disclosed shared-file overlap, never a functional dependency — neither
story's functions call, read, or depend on the other's.

**Why kept as two separate sprints, not one combined sprint:** combining
would total 4 + 6 = 10 tasks, one task ABOVE this project's own proven,
twice-exactly-matched single-story-sprint ceiling (9 tasks, L —
`SPRINT-021`, `SPRINT-030`, `SPRINT-063`, all exact estimate-vs-actual
matches per `Implementation/Learnings.md`). With zero real dependency
forcing them together, bundling would only add oversized-sprint risk for
no real decoupling benefit — the same class of judgement call
`SPRINT-063`'s own `## Notes` already reasoned through for a hypothetical
split of ITS OWN single story, applied here in reverse (two independent
stories kept apart, since nothing requires joining them). Each sprint
alone (`~4 tasks, S` here; `~6 tasks, M` for `SPRINT-068`) sits
comfortably within this project's own repeatedly-confirmed sizing buckets.

**Why no `depends_on_sprints` edge to `SPRINT-068`:** the decomposer
explicitly confirmed independence at `/plan-tasks` (both stories' own
Decomposer passes state it identically); building them in either order, or
concurrently across sessions, is safe — the shared-file overlap is
additive (different functions in the same file), not a call/data
dependency.

**Story-level ADR flag, not this role's to clear:** `REQ-SB-73-US-01`
carries `gate: flagged` (`trigger-3`, `ADR-054`) from the architect pass —
an already-open, separate `REVIEW-QUEUE.md` line item ("review `ADR-054`
... before the build starts"). Per the `SPRINT-060` precedent (built while
`ADR-048`'s own standing review flag was still open), this standing
architect-level flag does not, by itself, make THIS role's own grouping
decision ambiguous, oversized, blocked, or cross-sprint-dependent — the
partition itself is unambiguous. The sprint is therefore set `gate: clear`
at this stage; the ADR-054 review remains open under its own existing
`REQ-SB-73-US-01` line item in `REVIEW-QUEUE.md`, untouched by this pass.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired for this role's own
grouping decision: not oversized (4 tasks, S, well under the proven
ceiling); no blocked story; no NEW cross-sprint dependency (all 3 hard
prerequisite sprints are already `Done`); the split-vs-combine partition
was actively considered and resolved on real sizing/dependency grounds,
not left ambiguous. Advanced `Draft → Ready` — eligible for
`/implement-sprint SPRINT-067`.
