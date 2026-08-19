---
id: SPRINT-033
title: Agent Creation Wizard — entry point + Expert-type flow
status: Done
gate: flagged
gate_reason: "retro-harvest — human skims the drafted retrospective below and propagates patterns/antipatterns into Implementation/Learnings.md."
phase: P1
depends_on_sprints: []
sizing_estimate: "~4 tasks, S"
created: 2026-08-13
started: 2026-08-14
completed: 2026-08-14
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-033 — Agent Creation Wizard — entry point + Expert-type flow

## Sprint Goal

Add a new-agent creation wizard reachable from Settings — type selection
(Worker/Producer shown disabled this pass) plus a complete Expert-type flow
(domain + Section, starts genuinely empty and honestly uncertain).

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-37-US-01` is the only story
  here. Its 4 tasks form one straight internal chain (`T01 → T02 → T03 →
  T04`); verified directly against every task file's real frontmatter that
  none carries a cross-story `depends_on` edge, despite this story sharing
  its feature family (and the `agents_router.py`/`agent_registry.py` files)
  with `REQ-SB-37-US-02`/`03`.
- **Why NOT bundled into one sprint with `REQ-SB-37-US-02`/`03` (the
  known file-overlap risk named for this pass):** the graph allows a genuine
  choice here — all three stories total 9 tasks, which would still fit this
  project's own `L` ceiling as one sprint. But `REQ-SB-37-US-01` alone has
  **zero** cross-story dependencies (unlike `US-02`/`US-03`, which both hard-
  depend on the Skills foundation, `SPRINT-030`/`031`, and `US-02` also on
  `SPRINT-032`), so bundling it in would force this entire sprint to wait on
  three upstream sprints for no real reason — `US-01` could otherwise start
  building immediately, in parallel. Splitting it into its own sprint also
  separates the *first* write to `agents_router.py`'s new `POST /agents`
  endpoint from the two later Worker/Producer-type extensions, directly
  reducing the same-sprint file-collision risk this pass was asked to
  minimize. Per this pass's own guidance, the smaller, dependency-ordered
  split is preferred over the single oversized bundle. `REQ-SB-37-US-02`/`03`
  are grouped together instead, in `SPRINT-034` (they DO have a direct,
  same-sprint-appropriate dependency on each other), ordered after this one.
- **Sizing estimate:** ~4 tasks, S.

---

## Stories in Scope

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-37-US-01](../UserStories/REQ-SB-37-US-01-agent-creation.md) | Agent Creation Wizard — entry point, type selection, and the Expert-type flow (domain + starts empty, honestly uncertain) | P1 | Done |

**Tasks in scope** (dependency order): `T01` (vault_writer.py
agents_registry.json primitives, `depends_on: []`) → `T02`
(agent_registry.py persisted overlay + create_agent(), `depends_on: [T01]`)
→ `T03` (agents_router.py new POST /agents endpoint, Expert only,
`depends_on: [T02]`) → `T04` (CreateAgentWizard.tsx type selector + Expert
step + Settings entry, `depends_on: [T03]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None.

---

## Out of Scope

- Worker-type flow and Producer-type flow (`REQ-SB-37-US-02`/`03` →
  `SPRINT-034`).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, no architectural fact changed beyond `ADR-030` itself (already recorded at `/plan-tasks`)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-030` already `Accepted` prior to this build
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md`

---

## Retrospective

### Sizing accuracy

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — matched exactly.
  `T04` (frontend wizard + Settings entry) was correctly the heaviest by
  real verification effort — not code volume, but standing up a real
  CDP-driven headless-browser session to drive React-controlled inputs
  and confirm exact network-call counts on both the happy path and the
  honest-rejection path.

### What worked

- **`ADR-030`'s own predicted mechanism held up exactly as designed on
  first try** — the concrete claim it made ("zero code changes needed in
  any of the five self-healing per-agent registries") was independently
  confirmed live, not just trusted: a freshly created agent picked up a
  default Section, Provider, and working mode, and became Skill-grantable,
  with genuinely zero edits to `section_registry.py`/`provider_registry.py`/
  `working_mode_registry.py`/`skill_registry.py`/`agent_keywords.py`.
- **Backend-layer-first verification, reused a further time** — `T03`
  proved 4 of the story's 8 locked ACs (AC-04/05/06/08) against the real
  `POST /agents` mechanism before the wizard UI existed at all, catching
  every downstream-surface question (Agents Map rendering, honest
  uncertainty, Provider/Skill configuration, Chat/History parity) at the
  cheapest layer, exactly as the decomposer's own task-to-AC mapping
  intended.
- **A real CDP-driven headless-browser session (own remote-debugging
  profile + WebSocket protocol driver, not just a static screenshot) let
  `T04`'s honest-rejection AC (`AC-07`) be proven precisely** — a
  `window.fetch` spy installed in-page confirmed **zero** network calls
  fired on the empty-submission path, and **exactly** the wizard's own
  two-call sequence (`POST` then `PATCH`, in order) on the real
  submission — stronger, more exact evidence than eyeballing the UI alone.
- **Going beyond the story's own locked ACs to run one additional,
  sprint-level end-to-end pass** (a fresh Expert agent's own real detail
  panel — Settings/Chat/History tabs — plus an independent
  before/after reconfirmation that all 7 static agents were byte-identical)
  caught nothing broken, but turned "the individual tasks' own ACs all
  passed" into a directly-observed "the whole feature genuinely works the
  way a user would experience it" confidence, cheaply, before closing the
  sprint.

### What didn't work

- **A task's own informal verification-step prose named a URL
  (`/agents-map`) that turned out not to be the real mounted route** — the
  Agents Map is actually served at `/` (root), per `App.tsx`'s own route
  table. Cheap to catch (one `grep` + a headless-Edge console message,
  "No routes matched location") and non-blocking (no locked AC's own
  wording depended on the literal URL), but cost one extra screenshot/DOM-
  dump round trip before the real route was found.

### Patterns to carry forward

- **When a task's own Tests block references a URL informally (not
  quoted from a locked AC's own Given/When/Then text), verify the real
  route from the router's own source file before trusting it** — cheaper
  than debugging a blank-page screenshot after the fact. Generalizes this
  sprint's own `/agents-map` → `/` correction to any future task whose
  Tests block names a path.
- **A CDP WebSocket driver script (own `Runtime.evaluate`/
  `Page.navigate`/`Runtime.exceptionThrown` listener, launched against a
  dedicated `--remote-debugging-port` + `--user-data-dir` headless Edge
  profile) is a viable, more precise alternative to a screenshot-only
  headless-browser pass** when a locked AC needs exact interaction
  sequencing/network-call-count proof (not just "does it look right") —
  reusable whenever `npx`/a dedicated visual-harness tool isn't resolvable
  in the session but a real browser engine is needed for more than a
  static screenshot.
- **Running one extra, sprint-level (not task-level) end-to-end pass
  before closing a sprint that introduces a genuinely new mechanism class**
  (here: the first-ever runtime-created agent) is worth the small extra
  cost — it directly exercises the "does this behave identically to
  what's already there" question a story's own per-task ACs don't always
  phrase as one single, holistic check.

### Antipatterns to avoid

- **Assuming a bash-emulated PID from a command this same task itself
  launched (`nohup ... &`, `echo $!`) will be a real, killable Windows
  PID** — reconfirmed a further time this session; resolve the real PID
  via `Get-NetTCPConnection`/`Get-CimInstance Win32_Process` before
  attempting `Stop-Process`/`taskkill`, every time, not just when a first
  attempt visibly fails.

### Open follow-ups

- None blocking. `REQ-SB-37-US-02`/`US-03` (Worker/Producer flows,
  `SPRINT-034`) extend this sprint's own wizard shell and `create_agent`
  call next, once `SPRINT-030`/`031`/`032`'s own dependency chain and this
  sprint are both `Done` (confirmed here).

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).** `ADR-030` (persisted-
registry mechanism, resolving this story's prior 2026-08-13 re-spec
blockers) is already `Accepted`.

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires for this
product-owner pass specifically: (1) no material assumption — the "split
`US-01` out" decision is grounded directly in real task-level `depends_on`
edges (zero cross-story deps for `US-01`) plus this pass's own explicit
sizing/file-overlap guidance, not a guess; (2) `REQ-SB-37` is finalized PRD
text; (3) product-owner does not write ADRs — `ADR-030` was already accepted
at `/plan-tasks`; (4) no new `ESCALATIONS.md` entry; (5) not oversized (4
tasks, S); not a blocked story; no cross-sprint dependency needed for this
sprint itself; (6) N/A; (7) no contradictory inputs; (8) the bundle-vs-split
choice was genuinely evaluated (see Grouping Rationale) and resolved on a
concrete, stated basis (zero deps + file-overlap minimization), not left as
an unresolved ambiguity. The story's own `gate: flagged` (trigger-3, ADR-030
creation) is a `/plan-tasks`-stage flag already recorded on the story file
itself and does not block scheduling per Pipeline.md. Advances `Draft →
Ready`.
