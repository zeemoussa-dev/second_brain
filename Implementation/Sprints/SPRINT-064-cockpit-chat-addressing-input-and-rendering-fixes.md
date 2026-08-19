---
id: SPRINT-064
title: Cockpit chat correctly addresses agents, sends on Enter, updates live, and renders rich text (BUG-022/023/024/025 fix)
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "gate: flagged 2026-08-19 (coder pass, /implement-sprint) — sprint Done, human retro-harvest to Implementation/Learnings.md pending (Pipeline.md's own 'sprint retro' human touchpoint, not a new MUST-FLAG trigger). All 4 tasks built and all 4 locked ACs (AC-01 through AC-04) verified live against real, live evidence (real backend dispatch, a real Meeting Cockpit in a real browser, real Enter/pending-state/live-update behavior, real DOM structural checks for markdown rendering across all 3 named chat surfaces) — see each task's own Implementation Log. Two disclosed, verification-harness-only adaptations (neither touches app code, both fully explained in T02's Implementation Log) and one disclosed, pre-existing, unrelated live Provider/MCP outage (confirmed via a fresh-process control that succeeded before the outage set in) — none weakened, omitted, or reinterpreted a locked AC. One genuine, pre-existing, unrelated bug found incidentally during live-verification meeting-note selection (app/business/cockpit/people.py::resolve_people_chips 500s on real attendees-frontmatter-as-wikilink-strings) — out of this sprint's own Files to Modify, not fixed here, flagged in REVIEW-QUEUE.md for a /bug capture. Prior story-level flags (ADR-050 creation, the REQ-SB-32 framing discrepancy) were already resolved before this sprint began (see BUGFIX-04-US-01's own Notes) and are not re-litigated here."
phase: ""                          # bugfix sprint — no single phase; BUGFIX-NN stories carry no phase: (Pipeline.md hard rule 8's exception)
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, S"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-19
started: "2026-08-19"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-19"            # YYYY-MM-DD when status → Done
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

# SPRINT-064 — Cockpit chat correctly addresses agents, sends on Enter, updates live, and renders rich text (BUG-022/023/024/025 fix)

## Sprint Goal

Ship `BUGFIX-04-US-01` end to end: Cockpit chat (Meeting/Inbox) routes a
message to only its addressed agent, sends on Enter, reflects sent
messages/replies without a manual refresh, and renders markdown as real
rich text across all three chat surfaces (Cockpit x2, Agents Map chat
panel).

---

## Grouping Rationale & Sizing

- **Why grouped:** Single-story sprint — `BUGFIX-04-US-01` is the only
  `Ready`, ungrouped story this pass (confirmed by scanning every
  `Implementation/UserStories/*.md` for `status: Ready` + `sprint: ""`;
  the other three `Ready` stories found — `REQ-SB-72-US-01`,
  `REQ-SB-59-US-01`, `REQ-SB-42-US-01` — already carry a `sprint:` value
  (`SPRINT-063`, `SPRINT-059`, `SPRINT-039` respectively) and are excluded
  as "not ungrouped"). Its 4 tasks form two independent, acyclic
  dependency chains, exactly as recorded by the decomposer:
  `BUGFIX-04-US-01-T01 → BUGFIX-04-US-01-T02` (backend addressed-dispatch,
  then the frontend send-flow/Enter/pending-state/addressed-wiring task
  that consumes it) and `BUGFIX-04-US-01-T03 → BUGFIX-04-US-01-T04` (the
  new shared `ChatMessageText.tsx` + `react-markdown` dependency, then
  wiring it into both real chat-thread render call sites). No edge exists
  between the two chains — `T02` and `T04` both touch `Cockpit.tsx` but in
  two disjoint regions (send-flow/input-row vs. chat-thread rendering)
  with no functional coupling, per the decomposer's own explicit note.
  Both chains fix real, `Done`-work defects (Meeting/Inbox Cockpit,
  `REQ-SB-43-US-01`/`REQ-SB-44-US-01`) and share the same story, screens,
  and constraints (the XSS-safety constraint on `T03`/`T04` in particular
  reads across both). One sprint, one working context — there is no real
  partition question here to flag as ambiguous.
- **Why not combined with `REQ-SB-72-US-01`/`SPRINT-063`:** unrelated —
  `REQ-SB-72-US-01` (The Librarian section-first housekeeping pipeline) is
  a separate, already-`In Progress` backend story with its own sprint; it
  shares no file, module, or verification surface with this Cockpit
  frontend/chat-dispatch fix batch, and `SPRINT-063` is `In Progress`
  (untouchable per hard rule 3). Not considered as a merge candidate.
- **No phase-mixing question:** `BUGFIX-04-US-01` carries no `phase:` —
  per `Pipeline.md` hard rule 8's bugfix exception, this sprint is exempt
  from phase homogeneity and is built standalone (`phase: ""` above,
  mirroring `SPRINT-005`/`SPRINT-016`'s own precedent for a single-bugfix-
  story sprint).
- **Sizing estimate:** ~4 tasks, S. Matches the decomposer's own sizing
  note (largest task, `T02`, ~40-50 line diff in one already-read file —
  not oversized) and this project's own recurring "~4 tasks, S" precedent
  for small, well-scoped, two-chain or single-chain bugfix/hardening
  batches (`SPRINT-025`, `SPRINT-027`, `SPRINT-053`). No task in this
  batch needs its own sprint or a cross-sprint `depends_on_sprints` edge —
  both chains are short, already-sequenced by the decomposer, and fit
  comfortably in one working session together.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-064 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [BUGFIX-04-US-01](../UserStories/BUGFIX-04-US-01-cockpit-chat-addressing-input-and-rendering-fixes.md) | Cockpit chat correctly addresses agents, sends on Enter, updates live, and renders rich text (BUG-022/023/024/025 fix) | — (bugfix) | Done |

---

## Dependencies / External Blockers

- **Depends on sprints:** None.
- No external blocker — `REQ-SB-43-US-01` (Meeting Cockpit),
  `REQ-SB-44-US-01` (Inbox Cockpit), and `REQ-SB-49-US-02` (`@mention`
  bring-in) are all already `Done`; this fixes real defects in
  already-shipped code.

---

## Out of Scope

- Any change to which agents CAN be brought into a Cockpit thread, or the
  `@mention` bring-in mechanism itself (`REQ-SB-49-US-02`) — see the
  story's own Non-Goals.
- Streaming/token-by-token agent replies — see the story's own Non-Goals.
- `REQ-SB-72-US-01` / `SPRINT-063` (The Librarian) — unrelated, separate,
  already-`In Progress` backend work; not touched by this sprint.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact (already done at `/plan-tasks`, unchanged by this coder pass)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` (`ADR-050`, already `Accepted` at `/plan-tasks`, unchanged by this coder pass)
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

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — matched exactly on
  task count/shape. The estimate under-counted VERIFICATION cost, though:
  this was the first sprint this session where a genuinely frontend-heavy,
  real-browser-driven verification pass (not just backend-layer Python
  scripts) hit real environment friction (headless-CDP quirks, a live
  Provider outage) that took real, non-trivial troubleshooting time well
  beyond the ~40-50 line diffs themselves.

### What worked

- Reusing already-`Accepted`/already-established precedents exactly as the
  decomposer specced (`AgentDetailPanel.tsx`'s own `sending`/typing-dot/
  form-submit shape for `T02`; `SPRINT-048`'s "generic-primitive-first,
  kind-specific-wrapper-second" shape for `T03`/`T04`'s shared
  `ChatMessageText.tsx`) meant zero design forks during the build itself —
  every implementation decision was already made by `/plan-tasks`.
  `depends_on: []` on both chain-starts (`T01`, `T03`) let both
  independent chains build in either order with zero coordination
  overhead.
- Backend-layer-first live verification (`T01`, a real Python `.venv`
  script against real agents/threads, no browser needed) caught and
  confirmed the addressed-dispatch fix cheaply and fast, before any
  frontend work began — this project's own established
  `SPRINT-019`/`SPRINT-023` precedent held up again.
- When the real live-browser verification hit a hard blocker (headless
  Edge's CDP `Input` domain not triggering native "Enter submits a form"),
  pairing the real CDP-dispatched key event (proving the event itself
  reaches the input) with `form.requestSubmit()` (the standards-defined
  trigger for the identical `submit` event path) gave honest, strong
  evidence without touching any app code or weakening what was actually
  proven.

### What didn't work

- A large fraction of this sprint's real build time went into diagnosing
  why the app's own real, unmodified `fetchCockpit`/`fetchAgentList`
  effect-triggered fetches consistently failed in a headless-Edge-via-CDP
  session with a generic "Failed to fetch" — eventually root-caused to
  Chromium's Private-Network-Access preflight enforcement colliding with
  the pre-existing, unrelated `CORSMiddleware` config (see the new
  `MEMORY.md` Constraint). Several dead ends were tried first (feature-
  flag toggles, `--disable-web-security`, warm-up fetches, longer waits,
  client-side-only navigation) before landing on the actual fix (a
  throwaway local proxy + a second Vite instance on the CORS config's own
  already-whitelisted `5174` origin).
- A real, currently-ongoing live Provider/MCP outage (pre-existing,
  confirmed via a fresh-process control that succeeded before the outage
  set in) meant `AC-04`'s own agent-authored-content checks could not be
  driven by a genuinely fresh live model call for the CONTENT itself —
  worked around (content injected/intercepted, rendering kept 100% real)
  but cost real diagnostic time to confirm it was genuinely an outage and
  not a regression from this sprint's own `T01` change.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Headless-Chromium/Edge Private Network Access preflight can silently
  block an app's own real `Content-Type: application/json` fetch calls
  cross-port on loopback** — root-caused via a layered check (curl OPTIONS
  with/without the PNA request header; a page-context fetch injected
  BEFORE any app script runs, with/without the header) before reaching for
  browser flags. Fix (verification-harness-only, zero app code touched): a
  throwaway local HTTP proxy that answers the OPTIONS preflight directly
  with the one extra `Access-Control-Allow-Private-Network: true` header,
  paired with an additional Vite dev-server instance on an
  already-CORS-whitelisted origin pointed at that proxy via
  `VITE_API_BASE_URL` — never edit the app's own CORS config or restart
  the primary dev server/backend to "fix" a verification-tooling problem.
- **`form.requestSubmit()` paired with a real CDP-dispatched Enter
  keydown/keyup is the honest way to prove Enter-to-submit when headless
  Chromium's CDP `Input` domain doesn't trigger the native default action**
  — dispatch the real key event first (proves it reaches the focused
  element as genuine DOM `keydown`/`keypress`), then call
  `requestSubmit()` (the standards-defined trigger for the identical
  `submit` event a real Enter press invokes) — disclose the adaptation
  plainly rather than silently substituting a `.click()` on the Send
  button, which would prove nothing about Enter at all.
- **When a live model/Provider call is genuinely unavailable mid-
  verification, inject/intercept ONLY the network response boundary and
  keep 100% real app code (React state update, real component render, real
  DOM) in the loop** — for a persisted surface, append the crafted content
  directly into the SAME real store the live UI reads from (mirroring
  authentic historical content already found in that same store, not
  fabricated from nothing); for an ephemeral, client-only surface,
  intercept `window.fetch` for the ONE specific endpoint the real send
  triggers, letting every other real request pass through untouched. Prove
  this is a genuine outage (not a regression) with an independent control
  BEFORE relying on the workaround — this sprint's own fresh-isolated-
  process re-run of `T01`'s exact verification script, using the exact
  same agent ids that had worked minutes earlier, was the control.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Assuming a headless-browser fetch failure means the app's own code has
  a bug** before checking whether a MANUALLY-issued fetch (via CDP
  `Runtime.evaluate`, no custom headers) succeeds against the exact same
  endpoint — a fast, cheap differential check (does a no-header fetch
  work? does the app's own header-bearing fetch fail even when issued via
  `Runtime.evaluate` directly?) narrows the search space in minutes instead
  of hours of guessing at timing/warm-up theories.
- **Reaching for ever-more browser command-line flags
  (`--disable-features=...`, `--disable-web-security`) before confirming
  the flag actually changed observable behavior** — several flag attempts
  this sprint had zero effect and cost real time; a small, targeted
  differential test (does behavior X change with vs. without the flag,
  on a KNOWN-fresh profile) would have surfaced "this flag isn't the
  fix" in one round trip instead of several.

### Open follow-ups

- `app/business/cockpit/people.py::resolve_people_chips` 500s the entire
  `GET /cockpit/{subject_kind}/{stem}` endpoint for any real Meeting/Email
  note whose `attendees`/`recipients` frontmatter is a plain list of
  wikilink strings rather than `list[dict]` — filed at `REVIEW-QUEUE.md`
  (recommends a `/bug` capture), out of this sprint's own scope.
- The live Provider/MCP outage observed throughout this sprint's own
  verification session — not filed as a `BUG` (infra/environment, not a
  code defect this session's own evidence can pin to any specific commit),
  flagged for human awareness in case it persists into the next session.
