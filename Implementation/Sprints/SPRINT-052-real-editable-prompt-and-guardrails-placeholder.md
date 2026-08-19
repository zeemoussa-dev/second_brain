---
id: SPRINT-052
title: Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Non-blocking standing breadcrumb, carried from REQ-SB-66-US-01's own gate_reason: (1) trigger-1 — the compass_client.py 'four functions, not two' call-site-scoping material assumption (T02 carries this flag). (2) trigger-3 — ADR-044 (a genuine, material narrowing of ADR-041/ADR-043 point 6, making a Job clickable and its Settings editable/persisted for the first time; T06/T07 carry this flag). Per this project's own established precedent (every ADR-creating story this session — REQ-SB-54/55/63-US-01 — plus REQ-SB-65-US-01/SPRINT-051), a flagged-but-Ready story is fully eligible for sprint planning and building; neither flag blocks this sprint. (3) Retro-harvest — this sprint's drafted Retrospective below awaits human propagation into Implementation/Learnings.md, plus the operator's own stated intent to personally live-browser-verify T07's Job-Settings shell (no browser tool was available to the coder this sprint; every AC was instead proven via TypeScript/lint clean-checks, direct JSX reading, and real HTTP round-trips against both an in-process TestClient and the live dev backend). See REVIEW-QUEUE.md."
phase: P1                          # single phase only — a sprint never mixes phases
depends_on_sprints: []             # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~7 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-16
started: "2026-08-16"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-17"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — see SPRINT-030 for the full comment block. -->

# SPRINT-052 — Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings

## Sprint Goal

Replace every hardcoded prompt-building call site (`compass_client.py`'s four
functions, the Chat system message, the Vault Filing Expert's placement prompt)
with a real, per-id, additive Prompt override backed by a new sibling
`agent_prompts.json` store, add a structure-only Guardrails field to the same
Settings surface for every real Agent Type and Job, and make a Pipeline Job
clickable on the Agents Map for the first time via a new, genuinely separate
Job-Settings-only endpoint and frontend shell (`ADR-044`).

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-66-US-01` is the only `Ready`,
  ungrouped story this pass found. Its 7 tasks are one strict dependency tree,
  all facets of the SAME single mechanism (an additive Prompt-override layer +
  a structure-only Guardrails field + the per-Type Settings extension + the
  narrow Job-Settings-view carve-out), never contradicting the decomposer's own
  recorded `depends_on` edges: `T01` (store, `depends_on: []`) is the shared
  root; `T02`/`T03`/`T04` each fan out from `T01` independently
  (`compass_client.py` wiring, Chat/Vault-Filing-Expert wiring, and the
  real-Agent Settings-router extension respectively); `T05` (frontend rows)
  depends on `T04`; `T06` (Job-Settings endpoint, `ADR-044`) depends on `T01`
  plus the already-`Done` `REQ-SB-65-US-01-T01`; `T07` (Job-Settings frontend
  shell, `ADR-044`) depends on `T06` plus the already-`Done`
  `REQ-SB-65-US-01-T02`. Confirmed acyclic by direct reading of every task
  file's own `depends_on:` frontmatter, not assumed. No reason to split one
  story's own single dependency tree across sprints, and no sibling `Ready`,
  ungrouped story exists to combine it with.
- **Cross-story `depends_on` edges confirmed, not assumed — no
  `depends_on_sprints` needed:** `T06`'s `depends_on: [REQ-SB-66-US-01-T01,
  REQ-SB-65-US-01-T01]` and `T07`'s `depends_on: [REQ-SB-66-US-01-T06,
  REQ-SB-65-US-01-T02]` are real, disclosed reliances on `REQ-SB-65-US-01`'s
  own tasks (`T06` validates a `job_id` against `email_capture_pipeline.
  get_job_tree()`, `T01`'s own function; `T07` reuses the SAME already-fetched
  `fetchAgentJobs(...)` list `T02`'s own `pipelineJobTreeAdapter.ts` already
  consumes) — read directly from both tasks' own frontmatter. Both referenced
  tasks are already `status: Done` (`SPRINT-051`, `status: Done`, closed
  2026-08-16) — a `depends_on_sprints` ordering edge is only needed when the
  referenced sprint is NOT YET `Done`; since `SPRINT-051` already is, this
  sprint records `depends_on_sprints: []` (no ordering constraint remains to
  express) and simply notes the reliance under `## Dependencies / External
  Blockers` below, mirroring `SPRINT-050`'s own identical "cross-story
  `depends_on` onto an already-`Done` sprint's tasks needs no ordering edge"
  precedent for `REQ-SB-63-US-01-T02` → `REQ-SB-55-US-01`.
- **`REQ-SB-64-US-01` deliberately excluded, confirmed directly from its own
  frontmatter, not assumed:** `status: Draft` (not `Ready`), `gate: flagged` —
  `gate_reason` names two genuinely unresolved operator open questions
  (whether it retrofits `REQ-SB-55`'s already-shipped `consult_librarian` call
  site, and the exact mechanical shape of Hub-mediation), neither answered as
  of this pass — see
  `Implementation/UserStories/REQ-SB-64-US-01-section-hub-kb-traffic-gateway.md`
  frontmatter and its own `REVIEW-QUEUE.md` entry. Not eligible for
  `/plan-sprints` regardless of any topical proximity to `REQ-SB-66-US-01`
  (both touch Agent/Job-level Settings-adjacent surfaces) — status is the
  single source of truth. No other `Ready`, `sprint: ""` story was found in
  `Implementation/UserStories/*.md` this pass.
- **Story-level `gate: flagged` (trigger-1 + trigger-3) is a standing
  breadcrumb, not a build blocker** — per this project's own established
  `REQ-SB-54-US-01`/`SPRINT-048`, `REQ-SB-55-US-01`/`SPRINT-049`,
  `REQ-SB-63-US-01`/`SPRINT-050`, and `REQ-SB-65-US-01`/`SPRINT-051` precedent
  (a `Ready`/`flagged` story is fully eligible for `/plan-sprints` and
  `/implement-sprint`; the flag awaits a human look at the ADR/assumption,
  independent of delivery progress). All 7 tasks are themselves `status:
  Ready` — nothing is `Blocked`.
- **Sizing estimate:** ~7 tasks, M — matches this project's own closest
  sizing analog for a 7-task story (`SPRINT-046`, "Estimated: ~7 tasks, M —
  Actual: 7 tasks, M — matched," `Implementation/Learnings.md`), and sits
  alongside this project's own repeated 6-task/M precedent (`SPRINT-020`,
  `SPRINT-022`, `SPRINT-028`, `SPRINT-048`, all "Estimated ~6 tasks, M —
  Actual: 6 tasks, M — matched exactly"). `T02` (four owning call sites
  across three files, carrying the story's own trigger-1 scoping assumption)
  and `T07` (the new Job-Settings frontend shell, `ADR-044`'s Decision 3,
  carrying trigger-3 plus the story's Scenario 7 click-to-open-detail proof)
  are expected to be the heaviest, by live-verification complexity rather
  than code volume — mirroring this project's own repeated finding that a
  frontend task's or a multi-call-site wiring task's real cost is
  verification, not lines changed.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-052 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-66-US-01](../UserStories/REQ-SB-66-US-01-real-editable-prompt-and-guardrails-placeholder.md) | Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings | P1 | Done |

**Tasks in scope** (dependency order): `T01` (`agent_prompts.json` sibling
store, `depends_on: []`) → `T02` (`compass_client.py` four-function wiring,
`depends_on: [T01]`), `T03` (Chat system message + Vault Filing Expert
placement-prompt wiring, `depends_on: [T01]`), `T04` (real-Agent
`GET`/`PATCH /agents/{agent_id}` Prompt+Guardrails fields, `depends_on:
[T01]`) — all three independently fan out from `T01` → `T05`
(`AgentDetailPanel.tsx` Settings-tab rows, `depends_on: [T04]`) → `T06`
(new `GET`/`PATCH /agents/{agent_id}/jobs/{job_id}/settings`, `ADR-044`,
`depends_on: [T01, REQ-SB-65-US-01-T01 (Done)]`) → `T07` (new standalone
Job-Settings frontend shell, `ADR-044`, `depends_on: [T06,
REQ-SB-65-US-01-T02 (Done)]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** None. `T06`'s and `T07`'s own cross-story
  `depends_on` edges onto `REQ-SB-65-US-01-T01`/`T02` (`SPRINT-051`, `Done`)
  are both already satisfied — confirmed directly from `SPRINT-051`'s own
  frontmatter (`status: Done`, `completed: 2026-08-16`), so no ordering edge
  is needed; the reliance is real (both tasks compose directly against
  `REQ-SB-65-US-01`'s own already-shipped `get_job_tree()`/
  `fetchAgentJobs`/`pipelineJobTreeAdapter.ts`) but does not block this
  sprint's start.
- `REQ-SB-64-US-01` — held out of this sprint per its own `Draft`/
  `gate: flagged` status (two unresolved operator open questions, see
  Grouping Rationale); not a dependency this sprint waits on.

---

## Out of Scope

- `REQ-SB-64-US-01` (Section Hub as KB Traffic Gateway) — `Draft`, two
  unresolved operator open questions; not eligible for `/plan-sprints` until
  the operator answers them and the story is re-run through `/plan-tasks`.
- `classify_recent_emails`'s own separate call to `compass_client.
  classify_email`, and `skill_tools.py`'s shared `summarize_file` MCP skill —
  both explicitly left unwired to any Prompt override by the story's own
  `## Non-Goals` (disclosed dual-ownership/second-caller scoping calls, not
  silently dropped).
- Resolving the "Job with no real LLM call site" gap for any Job beyond the
  2-item hand-maintained exclusion set (`thread_match_merge`,
  `detect_recurring_pattern`) — `ESC-039`, Resolved, is the decided
  mechanism this sprint implements; no generic introspection is built.
- Defining what Guardrails means or enforcing anything with it — the story's
  own explicit "structure only, not content-defined" framing; this sprint
  adds and persists the field, decides nothing about behavior.
- Any Pipeline other than Email Capture, or the demo taxonomy's own sample
  agents/pipelines — out of scope, mirroring `REQ-SB-65-US-01`'s own
  scope-narrowing precedent.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — done at `/plan-tasks` (architect pass), not touched further by the coder
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-044`, recorded at `/plan-tasks`
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~7 tasks, M — **Actual:** 7 tasks, M, no rebuilds, no
  blocked tasks — **Takeaway:** the task count and effort both matched
  exactly, reconfirming `SPRINT-046`'s own precedent for a 7-task/M story
  cited at planning time. Unlike `SPRINT-051`'s own retro finding (a
  cross-cutting contradiction only surfaced by live verification), every
  facet of this sprint's own dependency tree (`T01` store → `T02`/`T03`/`T04`
  fan-out → `T05`; `T06` → `T07`) built and verified cleanly on the first
  pass, including the two cross-story `depends_on` edges onto
  `REQ-SB-65-US-01`'s already-`Done` `T01`/`T02` — both composed against
  exactly as documented, with zero surprises.

### What worked

- **Reading the real, current file before touching it, every single time**
  (`T05`'s exact `handlePromptCommit`/`handleGuardrailsCommit`/
  `data-testid="settings-prompt-input"` pattern for `AgentDetailPanel.tsx`,
  reused near-verbatim for `T07`'s `JobSettingsPanel.tsx`; `T06`'s exact
  `{"id","name","prompt"?,"guardrails"}` response shape, reused verbatim in
  `agentsApiClient.ts`'s new `JobSettings` interface) meant `T07` needed zero
  guessing about field names, commit timing, or omission semantics — every
  contract was already proven real by the task it depended on.
- **In-process `TestClient(app)` verification, independent of the live dev
  server's own availability** (`T06`'s own precedent, reused directly by
  `T07`) proved decisive again this sprint: the live `127.0.0.1:8001` server
  was transiently unresponsive for several minutes early in `T07`'s
  verification pass (later confirmed to have recovered, with identical
  results) — `TestClient` gave a fast, real, network-independent way to
  prove the exact endpoint contract `JobSettingsPanel.tsx` depends on
  (key-presence, not `null`, for the 2 Prompt-omitted Jobs) without waiting
  on or diagnosing that transient backend condition.
- **The decomposer's own "user-observable ACs verify in the frontend task;
  the backend task gets non-AC smoke checks" split** (`T04`/`T06` carried no
  AC tags; `T05`/`T07` carried the corresponding user-facing ACs) kept each
  task's own verification scope honest and bounded — `T07` never had to
  re-derive what `T06` had already smoke-checked at the API layer, only
  prove the UI renders/commits against that already-proven contract.

### What didn't work

- **No browser/screenshot tool was available to the coder for this entire
  sprint** (`T05` and `T07` both disclosed this) — every frontend AC in this
  sprint was proven via TypeScript/lint clean-checks, direct JSX reading
  against a proven backend contract, and (for `T05`) the operator's own
  separate live-browser pass after the fact, rather than the coder's own
  in-session visual confirmation. This is a real, standing verification gap
  for every frontend-facing task in this project until a Layer-1 visual
  harness (`npm run visual` or equivalent) actually exists and is wired into
  the coder's own available tools — flagged again here, not newly found,
  since `T05`'s own retro-equivalent note already named it for this exact
  sprint.
- The live dev backend's transient unresponsiveness (several minutes of
  timed-out `Invoke-RestMethod`/`curl` calls against even the pre-existing,
  unrelated `/agents` endpoint) was never root-caused this sprint — most
  likely a `--reload` file-watcher restart window triggered by
  `agent_prompts.json` writes landing inside the watched tree, but this is
  an inference, not confirmed by reading `uvicorn`'s own reload logs. Left
  as an open follow-up rather than guessed at further, since diagnosing/
  fixing the dev server's own reload behavior is outside this sprint's own
  `## Files to Modify` scope entirely.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Key-presence checks for genuinely-optional response fields** — when a
  backend contract OMITS a JSON key entirely to represent "no real value
  exists here" (as opposed to `null`/`""` meaning "unset but valid"), the
  consuming frontend must check for the key's presence (`'field' in
  response`) rather than truthiness/emptiness of its value — collapsing
  "absent" and "empty-but-present" silently reintroduces the exact
  "present-but-inert field" outcome the backend's own omission was designed
  to avoid (`T06`/`T07`, `ADR-044`, `ESC-039`).
- **A genuinely separate, minimal component beats widening a large shared
  one when the shared one has no removal mechanism for what the new case
  doesn't need** — `ADR-044`'s own Decision 3 (confirmed correct by `T07`'s
  clean build): `AgentDetailPanel.tsx`'s `TABS` constant is fixed, additive
  only, with no tab-REMOVAL mechanism to reuse; building `JobSettingsPanel.tsx`
  as its own small component, reusing only the shared CSS vocabulary, avoided
  inventing that removal machinery inside an already-large component for a
  single, narrow new case.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Treating a transiently-unresponsive live dev server as a hard
  verification blocker** — when an in-process test harness (`TestClient`,
  Vite's `server.ssrLoadModule()`) can exercise the exact same real code
  against the exact same real config/data with zero network dependency, use
  it immediately rather than retrying the live network repeatedly; corroborate
  against the live server afterward if/when it recovers, but don't let a
  live-process hiccup stall verification of otherwise-provable AC contracts.

### Open follow-ups

- A Layer-1 visual harness (`npm run visual` or equivalent) still does not
  exist/is not wired into the coder's own available tools — every frontend
  task in this project continues to rely on the operator's own separate
  live-browser pass for actual visual confirmation. Not filed as a new
  ticket this sprint (no requirement asks for it yet); noted again here for
  visibility, consistent with `T05`'s own prior disclosure this same sprint.
- The live dev backend's transient unresponsiveness during `T07`'s
  verification pass was not root-caused (see "What didn't work" above) — if
  it recurs and blocks a future sprint's own verification, it may be worth a
  dedicated look at the `uvicorn --reload` watch-path configuration relative
  to `.second-brain/`'s own write-heavy files.

---

## Notes

**Sprint assembled 2026-08-16 (`/plan-sprints`).** `REQ-SB-66-US-01` enters
`/plan-sprints` at `status: Ready`, `gate: flagged` (trigger-1 — the
`compass_client.py` "four functions, not two" call-site-scoping material
assumption, standing breadcrumb on `T02`; trigger-3 — `ADR-044`, standing
breadcrumb on `T06`/`T07`) — a standing breadcrumb, not a blocker, per the
established `REQ-SB-54-US-01`/`SPRINT-048`, `REQ-SB-55-US-01`/`SPRINT-049`,
`REQ-SB-63-US-01`/`SPRINT-050`, `REQ-SB-65-US-01`/`SPRINT-051` precedent
explicitly reconfirmed for this pass. It is the only `Ready`, `sprint: ""`
story found — confirmed by scanning `Implementation/UserStories/*.md`
frontmatter directly. `REQ-SB-64-US-01` was checked specifically and
confirmed `Draft` (`gate: flagged`, two unresolved operator open questions) —
excluded, not batched, exactly as the prior two `/plan-sprints` passes this
session (`SPRINT-051`'s own Notes, and the pass before it) already confirmed.

**Gate: `gate: clear` 2026-08-16 for THIS product-owner pass** (the sprint's
own `gate: flagged` field carries forward the story's pre-existing,
non-blocking trigger-1/trigger-3 breadcrumbs — see `gate_reason` above — not
a new product-owner-level flag). No NEW MUST-FLAG trigger fires for this
partition decision itself: (1) no material assumption — the single-story
grouping and the full 7-task dependency order are both read directly off the
decomposer's own recorded `depends_on` edges in every task file's own
frontmatter (confirmed by direct reading, not guessed), and the two
cross-story edges' referenced tasks are confirmed `Done` by direct reading of
`SPRINT-051`'s own frontmatter; (2) `REQ-SB-66` is not
`<!-- Draft -->`/unfinalised in the PRD (the story's own Context states "this
requirement is real"); (3) product-owner does not write ADRs — none was
created or changed by this pass (`ADR-044` was already created at
`/plan-tasks`, prior to this pass); (4) no new `ESCALATIONS.md` entry written
by this pass; (5) not oversized (7 tasks, M, matching the `SPRINT-046`
7-task/M precedent) — not a blocked story — all 7 tasks are `status: Ready`;
no NEW cross-sprint dependency had to be introduced
(`depends_on_sprints: []`, genuinely none needed since both referenced
upstream tasks are already `Done`); (6) N/A (coder-only trigger); (7) no
contradictory inputs; (8) not genuinely ambiguous — a single story with one
strict dependency tree and no sibling `Ready` story to combine it with has
exactly one reasonable partition. Advances `Draft → Ready`.

**`BACKLOG.md` updated:** `REQ-SB-66` row's Story Status cell updated to
reflect `Ready`/carried flags, its Sprint column set to `SPRINT-052`, Sprint
Status cell set to `Ready`; a new `SPRINT-052` row appended to the Sprint
Status table.

**REVIEW-QUEUE.md:** no new entry written by this pass — the story's own
pre-existing standing flags (trigger-1 `compass_client.py` scoping
assumption; trigger-3 `ADR-044` human review) already have their own
`REVIEW-QUEUE.md` entries, unchanged and unresolved by this pass; see
`REVIEW-QUEUE.md` → the `REQ-SB-66-US-01`/`ADR-044` entries.

---

**Coder close-out, `T07`, 2026-08-17 — sprint `In Progress → Done`:**

- `T07` (the sprint's own final, last-remaining task) built and verified —
  all 7 tasks now `Done`, story `REQ-SB-66-US-01` marked `Done`, sprint
  `status: Done`, `completed: 2026-08-17`. `BACKLOG.md`'s `REQ-SB-66` row and
  `SPRINT-052`'s own Sprint Status row both updated to `Done`.
- No new `ESCALATIONS.md`/`REVIEW-QUEUE.md` entry written by this close-out
  pass — the two pre-existing standing flags (trigger-1, trigger-3) carry
  forward unchanged, plus this Retrospective itself (drafted, not yet
  human-harvested into `Learnings.md`) and the operator's own stated
  live-browser confirmation pass (no coder-side browser tool available this
  sprint). None of these block marking the sprint `Done` — a flagged gate is
  a standing human-review breadcrumb, not a completion blocker.
- `Retrospective` drafted above per this pipeline's own "coder drafts,
  human harvests" rule — `gate: flagged` set/kept specifically so the human
  skims it and propagates the two `Patterns to carry forward`/one
  `Antipattern to avoid` into `Implementation/Learnings.md`.
