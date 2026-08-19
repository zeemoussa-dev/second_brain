---
id: SPRINT-038
title: File upload on agent chat — Compass summarization + vault filing handoff
status: Done
gate: flagged
gate_reason: "retro-harvest + T05's own two scope-internal judgement calls, both non-blocking (see REVIEW-QUEUE.md)"
phase: P1
depends_on_sprints: [SPRINT-030]
sizing_estimate: "~5 tasks, S"
created: 2026-08-13
started: 2026-08-14
completed: 2026-08-14
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-038 — File upload on agent chat — Compass summarization + vault filing handoff

## Sprint Goal

Let a user attach a file on agent chat; summarize it via Compass, hand off
to the Vault Filing Expert, and file it into the vault with tags/wikilinks.

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-28-US-01` is the only story
  here. Its 5 tasks form one mostly-linear chain (`T01`/`T02` independent →
  `T03` depends on `T02` → `T04` depends on `T01`/`T03` → `T05` depends on
  `T04`), plus two real cross-story edges into the Skills foundation:
  `T03` and `T04` both `depends_on: [..., REQ-SB-39-US-01-T01/T02]`
  (respectively).
- **Why NOT bundled with `SPRINT-030` itself:** would grow that already
  `L`-sized (9-task) foundation sprint further past this project's own
  ceiling. **Why NOT bundled with `SPRINT-031`/`033`/`034` (the other
  `skill_registry.py`/`skill_tools.py`-touching sprints in this batch):** no
  task-level dependency links this story to any of them (its only real edges
  are into `SPRINT-030`) — bundling would be an unforced, ambiguous grouping
  with no basis in the actual dependency graph. Kept in its own sprint,
  ordered after `SPRINT-030` only.
- **Sizing estimate:** ~5 tasks, S.

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-28-US-01](../UserStories/REQ-SB-28-US-01-file-upload-attach-and-handoff.md) | File upload on agent chat — Compass summarization, handoff to the Vault Filing Expert, and vault filing with tags/wikilinks | P1 | Ready |

**Tasks in scope** (dependency order): `T01` (upload_storage.py module,
`depends_on: []`), `T02` (compass_client.py summarize_content, `depends_on:
[]`) → `T03` (summarize-file Skill, `depends_on: [T02, REQ-SB-39-US-01-T01,
REQ-SB-39-US-01-T02]`) → `T04` (chat attachment endpoint, `depends_on: [T01,
T03, REQ-SB-39-US-01-T02]`) → `T05` (frontend attach affordance,
`depends_on: [T04]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-030` (`REQ-SB-39-US-01`) — mirrors `T03`/
  `T04`'s own real cross-story `depends_on` edges.

---

## Out of Scope

- The Skills capability model itself (`SPRINT-030`).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (no new architectural fact — `/plan-tasks` already updated it; ADR-034 unchanged)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (ADR-034 already Accepted at `/plan-tasks`; no new ADR needed during build)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md`

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~5 tasks, S — **Actual:** 5 tasks, S — matched exactly.
  The straight, mostly-linear dependency chain (`T01`/`T02` parallel at
  the root → `T03` → `T04` → `T05`) held with zero rework/reordering;
  every task's own real-file-reconciliation note ("read `T0N`'s real
  output before wiring this task's code") was genuinely needed but
  never surfaced a mismatch — each prior task's own code sample landed
  verbatim, matching the sizing estimate's own implicit assumption that
  this sprint composes already-proven mechanisms rather than inventing
  new ones.

### What worked

- **Backend-layer-first, then frontend, live verification** — every
  locked AC was independently confirmed at the cheapest reachable layer
  first (`T01`/`T02` Python-shell, `T03` skill-registry-direct, `T04`
  real HTTP via `curl`/`ASGITransport`) before `T05`'s frontend task
  ever started; the frontend task then re-verified the UI-visible half
  of the same ACs through a real browser, never re-discovering a
  backend-layer bug at the UI layer. Reconfirmed, this project's own
  long-standing pattern.
- **`httpx.ASGITransport(app=app)` against the real, unmodified `app`
  object, combined with a scoped in-process monkeypatch, to induce a
  real failure for one specific HTTP call without a permanent code
  edit** — used for both `AC-09` (Compass failure) and `AC-10`
  (Vault-Filing-Expert-unavailable) at the router layer, genuinely
  driving the real app through a real HTTP request/response cycle, not
  a mock. Extends `SPRINT-029`'s own precedent (there used for an
  auth-middleware check) to a business-logic failure-induction use case.
- **A minimal, from-scratch Python `websockets`-based CDP driver**
  (no Playwright/Puppeteer installed in this repo) — `DOM.
  setFileInputFiles` for real file-input interaction (the correct CDP
  primitive for this exact need; a plain native-setter/dispatchEvent
  technique cannot set `.files` on a file input at all, browsers block
  it), combined with this project's own established Fiber-props
  `onClick`/`onSubmit` direct-invoke technique for reliably triggering
  React handlers headless. Real, not a mock — genuinely exercised the
  real `AgentDetailPanel.tsx`/`agentsApiClient.ts` code against a real
  running backend.
- **Directly importing and calling the real, served frontend module
  function from the browser's own JS context** (`await
  import('/src/features/agents-map/agentsApiClient.ts')`) to test a
  code path the UI's own client-side pre-check structurally prevents
  from ever being reached through ordinary interaction (`AC-07`'s
  "simulating a client that skipped pre-validation" server-honesty
  half) — genuinely exercises the real, unmodified module function
  against the real server, distinct from (and a useful complement to)
  the UI-level rendering confirmation `AC-08` provided for the
  identical `isError`-on-rejection code branch.

### What didn't work

- **A hand-built, minimal real PDF (no `reportlab`/`fpdf2` available)
  as the go-to real-`.pdf`-fixture technique when no PDF-authoring
  library is present in the environment** — worked correctly (`pypdf`
  genuinely extracted the real embedded text), but is a fragile,
  easy-to-get-wrong technique (a raw object/xref/trailer PDF structure
  built by hand) worth naming explicitly rather than reinventing next
  time a real PDF fixture is needed and no authoring library is
  installed.
- **Assuming a project's own default `VITE_API_BASE_URL`/CORS
  configuration would "just work" against a freshly-started dev-server
  instance on a non-default port** — cost one debug cycle: the backend's
  own `CORSMiddleware` (`ADR-010`) only allows `5173`/`5174`, silently
  blocking a frontend instance started on `5180` with no visible error
  beyond an empty "No agents connected yet." state. Worth checking a
  project's own CORS allow-list BEFORE picking a dedicated verification
  port, not after hitting a confusing empty-state symptom.

### Patterns to carry forward

- Both "What worked" entries above (ASGITransport + scoped monkeypatch
  for backend failure induction; the from-scratch CDP driver +
  `DOM.setFileInputFiles` for real file-input interaction; direct
  module-import-from-browser-console for a client-side-unreachable
  code path) are reusable, generalizable techniques for any future
  file-upload or induced-failure verification need in this codebase.
- **Locate a project-local Node/tool install via the actually-running
  process's own `ExecutablePath`** (`Get-CimInstance Win32_Process` →
  `ExecutablePath`) when `node`/`npm`/`npx` aren't on `PATH` — a third
  confirmed instance of this recurring environment issue
  (`SPRINT-027`/`028`), this time resolved via a project-local
  `tools/node/` install neither prior sprint's own registry-based
  fix would have found. Worth checking BOTH the registry AND any
  already-running project process's own image path going forward.

### Antipatterns to avoid

- **Assuming a dev-server's own default `VITE_API_BASE_URL`/backend
  origin is CORS-permitted without checking the backend's own real
  allow-list first** — see "What didn't work" above.
- **Windows console codepage (`cp1252`) silently mangling non-ASCII
  output** (em-dashes, emoji) from a Python verification script — cost
  a moment of false alarm (looked like data corruption) before
  confirming, via a UTF-8 file round-trip, that the underlying data was
  always correct and only the console *display* was lossy. Wrap
  `sys.stdout` in a UTF-8 `TextIOWrapper` (or write to a file) by
  default for any future verification script expected to print
  non-ASCII content, rather than debugging it reactively each time.

### Open follow-ups

- None — every locked AC across all 10 story-level scenarios and all
  5 tasks was verified live with a real positive result (no
  environment-blocked/deferred half, unlike several recent prior
  sprints). The only carry-forward items are the two `T05`
  scope-internal judgement calls already flagged in `REVIEW-QUEUE.md`
  for a human spot-check (non-blocking).

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).** This story was re-specced
2026-08-13 for the Compass-summary/Vault-Filing-Expert mechanism; that
re-spec's own blockers were resolved before `/plan-tasks` decomposed it.

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires: (1) no
material assumption — the one cross-sprint edge mirrors real task-level
`depends_on`; (2) `REQ-SB-28` is finalized PRD text; (3) product-owner does
not write ADRs; (4) no new `ESCALATIONS.md` entry; (5) not oversized (5
tasks, S); not a blocked story; the cross-sprint dependency recorded is a
pre-existing task edge, not introduced by this pass; (6) N/A; (7) no
contradictory inputs; (8) not ambiguous — the only real edges tie to
`SPRINT-030` alone, ruling out any equally-valid alternative bundling.
Advances `Draft → Ready`.
