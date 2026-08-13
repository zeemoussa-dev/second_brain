---
id: SPRINT-013
title: My Day drill-downs and dashboard scoped to a rolling 7-day window
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro drafted — human to skim and harvest Learnings.md"
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~2 tasks, XS"    # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-11
started: "2026-08-11"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-11"            # YYYY-MM-DD when status → Done
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

# SPRINT-013 — My Day drill-downs and dashboard scoped to a rolling 7-day window

## Sprint Goal

Add query-time 7-day-window date filtering to My Day's Emails/Calendar drill-downs
and dashboard counts, so items 3 days before through 3 days after today show
automatically instead of the current unfiltered all-time list.

---

## Grouping Rationale & Sizing

- **Why grouped:** Single story, two tasks, one dependency edge (`T02` frontend
  depends on `T01` backend — the drill-down pages/dashboard consume the field and
  windowed result set `T01` adds). Both tasks are single-file, single-session
  changes entirely within the already-`Done`, already-`Accepted`
  `api → business → data_access` layering (no ADR, no new architecture). No other
  `Ready`, ungrouped story exists to combine or sequence against.
- **Sizing estimate:** ~2 tasks, XS — matches this project's smallest prior
  sizings (e.g. SPRINT-003, SPRINT-005 at ~2 tasks, XS), consistent with the
  story's own framing as an additive narrowing of an already-shipped read path,
  not a rebuild.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-013 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-22-US-01](../UserStories/REQ-SB-22-US-01-my-day-rolling-7-day-window.md) | My Day drill-downs and dashboard counts scoped to a rolling 7-day window | P1 | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None
- Story is a follow-on amendment to the already-`Done` `REQ-SB-12-US-02`
  (SPRINT-009) — not a not-yet-built story, so no `depends_on_sprints` edge is
  needed (SPRINT-009 is already `Done`).

---

## Out of Scope

- To-Do drill-down's populated state (still blocked on `REQ-SB-09`, per the
  story's own Non-Goals) — not touched by this sprint.
- Any new UI region, grouped-by-day layout, or day navigator — explicitly
  rejected by the story itself.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — no change needed; no new architectural fact this sprint (the architect's own `/plan-tasks` pass already recorded the amendment)
- [ ] Any new ADRs recorded in `ADR.md` with status `Accepted` — n/a, no ADR created this sprint
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

- **Estimated:** ~2 tasks, XS — **Actual:** 2 tasks, XS, landed exactly at
  estimate, zero rework, zero blocked tasks — **Takeaway:** the XS sizing
  calibration holds for a "narrow an already-shipped read path with a
  fixed-shape query filter, no new endpoint/component" story shape;
  confirms this project's smallest-sizing precedent (SPRINT-003/004/005)
  generalizes to backend-filter-plus-additive-field stories, not just
  pure-additive ones.

### What worked

- **The decomposer's task files already contained the exact, verbatim
  code to write.** Both `T01`/`T02`'s `## Files to Modify` sections
  specified complete, ready-to-paste function/component bodies (helpers,
  docstrings, and all) — implementation was a direct transcription with
  zero design decisions left to make at build time, and zero drift
  between what was planned and what shipped.
- **Backend-first live verification, frontend last, again.** `T01`'s
  `_compute_window()`/`_within_window()`/windowed list functions were
  smoke-checked directly in a Python shell against the real vault (179
  Email notes, 39 Meeting notes) *before* `T02` touched a single frontend
  file — by the time the browser-based pass started, the exact windowed
  counts (21/17) were already known-good, so the frontend verification
  was purely a rendering/wiring check, not a data-shape one.
- **The monkeypatch-and-revert technique translated cleanly from a
  client-side pattern to a server-side one.** `MEMORY.md`'s established
  "temporarily stub, verify, revert, re-confirm exact restoration"
  pattern (previously only used for `features/*/client.ts` fetch stubs)
  worked identically for `AC-04`'s harder problem — proving a
  `datetime.now()`-driven window recomputes without waiting a real day —
  by monkeypatching the module's own `datetime` reference in a live
  Python shell, then reverting and confirming byte-exact restoration of
  the real windowed result set.

### What didn't work

- **A background shell process launched with a trailing `&` inside a
  single `Bash` tool call did not reliably survive past that tool call's
  own completion** — the first backend-startup attempt
  (`uvicorn ... & sleep 3 && cat ...`) appeared to hang at "Waiting for
  application startup," and a second, separately-tracked
  `run_in_background: true` attempt was then also started against the
  same port, which failed with "address already in use" — because the
  *first* attempt's backgrounded process had, in fact, survived and bound
  the port after all. Root cause: don't chain a backgrounded long-running
  server process with `&` inside a compound command passed to a single
  `Bash` call; start it as its own dedicated `run_in_background: true`
  call so the harness tracks exactly one process per server, with no
  ambiguity about which attempt actually owns the port.
- **`npm`/`node` are not on the `Bash` tool's `PATH` in this environment**
  (Node is a portable zip under `tools/node/`, per `MEMORY.md`'s
  no-admin-rights constraint) — every `npm run dev`/`npm run build`
  invocation this sprint had to go through the `PowerShell` tool instead,
  with `tools/node` explicitly prepended to `$env:PATH` for that session.
  `Bash`-tool `npm` calls failed outright (`npm: command not found`)
  until this was corrected.
- **The frontend's committed `.env.local` (`VITE_API_BASE_URL=http://
  127.0.0.1:8001`) pointed at a port already occupied by a concurrent
  session**, and this task's own `## Files to Modify` didn't include
  `.env.local` — resolved by setting `VITE_API_BASE_URL` as a
  process-only PowerShell environment variable for the `npm run dev`
  invocation rather than editing the committed file, avoiding a scope
  violation while still pointing the dev frontend at the real backend
  port actually in use (`8002`) for this session.
- **A headless-Chrome CDP process died silently between verification
  passes** (confirmed via `ECONNREFUSED` on a later CDP call) partway
  through the `AC-06` stub-and-revert sequence — required relaunching a
  fresh headless Chrome instance mid-verification. No data was lost (the
  relaunch picked up cleanly against the still-running dev servers), but
  this is a real fragility in the current zero-dependency CDP-driver
  approach worth knowing about for future sprints using the same
  technique.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Server-side monkeypatch-and-revert for "prove it recomputes on every
  call" ACs** — when a locked AC requires proving a value is recomputed
  fresh (not cached) without waiting for real-world time to pass (e.g.
  "the window advances as days pass"), monkeypatch the specific dependency
  (e.g. a module's `datetime` reference) in a live shell, capture the
  shifted result, revert, and re-confirm byte-exact restoration of the
  original result — the same "stub, verify, revert" shape `MEMORY.md`
  already established for client-side fetch stubs, just applied one layer
  server-side. Reusable for any future "no manual refresh needed" AC.
- **Start each long-running dev-server process as its own dedicated
  `run_in_background: true` tool call, never chained with `&` inside a
  larger compound command** — chaining risks an ambiguous/duplicate
  process (see "What didn't work" above); one call, one tracked process,
  one clear PID to target for later cleanup.
- **Prefer a process-only environment-variable override over editing a
  committed local dev-config file when only the *current verification
  session's* port needs to differ** — e.g. `$env:VITE_API_BASE_URL =
  'http://127.0.0.1:<port>'` before `npm run dev`, rather than editing
  `.env.local` (which may not be in the task's own `## Files to Modify`
  and is itself a per-developer file, not spec-scoped). Zero risk of an
  accidental out-of-scope file edit, zero cleanup needed after the session
  ends.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Assuming `npm`/`node` are on the `Bash` tool's `PATH` in this
  environment** — they are not (portable Node install under
  `tools/node/`); use the `PowerShell` tool with `tools/node` explicitly
  prepended to `$env:PATH`, or invoke `tools/node/npm.cmd`/`node.exe` by
  full path, for every frontend command.
- **Trusting a headless-Chrome CDP session to stay alive indefinitely
  across a multi-step verification sequence without re-checking** — poll/
  re-verify the CDP port is still responding before a later step in a long
  verification sequence, rather than assuming the same browser instance
  launched several steps earlier is still there.

### Open follow-ups

- **CDP-driver process fragility** — the headless-Chrome instance died
  silently mid-sprint with no clear trigger identified; not a blocker this
  sprint (relaunching resolved it cleanly), but worth a future look if it
  recurs with higher frequency once a formal Playwright/Puppeteer
  test-stack ADR is on the table.
- **`.env.local`'s hardcoded `VITE_API_BASE_URL=http://127.0.0.1:8001`**
  remains a per-developer file outside any story's scope to fix; the same
  concurrent-port-conflict friction `SPRINT-009`'s/`SPRINT-010`'s retros
  already flagged for `CORSMiddleware`'s hardcoded origins list applies
  here too — both are real candidates for the same future env-var-driven
  configuration ADR already sitting in `REVIEW-QUEUE.md`.

---

## Notes

**Product-owner pass (2026-08-11, `/plan-sprints`):** REQ-SB-22-US-01 is the only
`Ready`, `sprint: ""` story found (checked all `Implementation/UserStories/*.md`;
the only other `status: Ready` story, REQ-SB-19-US-01, already carries
`sprint: "SPRINT-012"` and is excluded). Its 2 tasks form a single acyclic
dependency edge (`T02` → `T01`) entirely inside one story, so no partition
question arises. Phase is `P1` throughout — no phase-mixing risk. No ADR, no
oversized story, no blocked story, no cross-sprint dependency to introduce
(the story's own `Blocked by REQ-SB-12-US-02` is already `Done`), no ambiguity
in how to group a single, self-contained story. Advanced `Draft → Ready` with
`gate: clear`.

`gate: clear` 2026-08-11 — no MUST-FLAG trigger fired: single story, no
dependency conflict, no phase mix, not oversized, not blocked, no cross-sprint
edge introduced, only one valid partition (one story, one sprint). Ready for
`/implement-sprint`.

---

**Coder pass (`/implement-sprint`), 2026-08-11.** `REQ-SB-22-US-01` built
end-to-end: `T01` → `T02`, both `Done`, all 6 locked ACs verified live
against the real vault/real browser (backend smoke-checked directly via a
`.venv` Python shell, including a monkeypatch-and-revert for `AC-04`;
frontend verified via headless-Chrome CDP, backend on port `8002`,
frontend on port `5174` — ports `8000`/`8001`/`5173` were all already
occupied by concurrent sessions, a fresh instance of `MEMORY.md`'s
standing port-conflict constraint). `npm run build` ran clean, zero
TypeScript errors. Zero blocked tasks, zero `ESCALATIONS.md` entries.
Sprint `status: Ready -> Done`, `completed: 2026-08-11`. Story `status:
Ready -> Done`. `BACKLOG.md` updated (`REQ-SB-22-US-01`/`SPRINT-013` rows
-> `Done`). This sprint's `gate` set to `flagged` (retro drafted, awaiting
human `Learnings.md` harvest) per this role's own mandatory sprint-wrap
behaviour.
