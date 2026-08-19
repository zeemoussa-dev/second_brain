---
id: REQ-SB-40-US-01
title: Agent knowledge-gap tracking — record every honest "I don't know", let the user close it, surface a declining open-gap count as Expert readiness
requirement_ids: [REQ-SB-40]
requirement_section: "REQ-SB-40: Agent Knowledge-Gap Tracking & Expert Readiness"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-032 created, /plan-tasks architect pass 2026-08-13) — the operator relayed the detection/storage mechanism decisions and directed skipping /design for this batch; the architect resolved the remaining open placement question (the Knowledge Gaps tab lives on AgentDetailPanel.tsx, gated to Expert-type agents) and wrote ADR-032. Supersedes the prior gate_reason (unclear-requirement, ESC-030) — those mechanism questions are now resolved, not still open; the story stays flagged because an ADR was created, per Pipeline.md's ADR trigger, not because a question remains unanswered."
sprint: SPRINT-035
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-40-US-01 — Agent knowledge-gap tracking — record every honest "I don't know", let the user close it, surface a declining open-gap count as Expert readiness

## Story

**As a** Second Brain user
**I want** every honest "I don't know" an Expert agent gives to be recorded as
a trackable knowledge gap — one I can view, close by providing the missing
information myself or by directing the agent to research it, and watch the
open count decline over time
**So that** I have a real, observable signal of how close a newly-created,
initially-empty Expert agent is to being genuinely expert in its domain,
instead of honest uncertainty just disappearing into the chat transcript

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-40: Agent Knowledge-Gap Tracking &
  Expert Readiness*. **Acceptance:** "Every honest 'I don't know' an agent
  gives is recorded as an open knowledge gap, not just spoken and forgotten;
  the user can view an agent's open gaps; a gap can be closed either by the
  user directly providing the missing information or by directing the agent
  to research it; the count of open gaps for an agent is visible and
  decreases as gaps are closed."
- **PRD breadcrumb (2026-08-13, operator-directed), cited verbatim, not
  re-decided here** — answering "what makes an Expert agent actually
  ready/complete": "I guess we need both the wizard, and the Agent can say I
  don't know as a start, and a human input is needed to fill the gap — by
  time it will be Expert (the number of I don't know is how we close this
  Expert gap in future)." This builds directly on `REQ-SB-33` (Agent
  Grounding & Honest-Uncertainty Guardrail, `Done`, `SPRINT-018`) — that
  requirement made an agent say "I don't know" honestly instead of
  fabricating, but the reply itself is never captured anywhere beyond the
  chat transcript; this requirement is the natural next layer.
- **Real code read directly, not assumed, to ground this story in what
  actually exists today:**
  - `app/business/agent_orchestration/state.py::history_entries_to_messages`
    (`REQ-SB-33-US-01`, `Done`) confirms the honest-uncertainty behavior is
    **prompt-level only** — one prepended `SystemMessage` instructs the model
    to say "I don't know" rather than guess. There is **no structured
    signal** anywhere in the code today that distinguishes an honest
    "I don't know" reply from an ordinary answered reply — the model's raw
    `response.content` string is returned as `reply` either way, with
    nothing inspecting or flagging it. Detecting a gap therefore needs new
    machinery this story does not presume the shape of (see Constraints).
  - `app/business/agent_registry.py`'s static `AGENTS` catalog confirms
    "Expert" is already a real, structural agent-type marker today
    (`"type": "expert"`, carried by `vault-qa`, `vault-filing-expert`, and
    `compass-expert`) — not merely a role description with nothing to key
    off. This story's own "for an Expert agent" framing has a real field to
    anchor on, not a guess.
  - `app/business/agent_activity.py` (`REQ-SB-11-US-01`, `Done`) confirms
    its own `_ACTIVITY_KINDS = {"run_event", "run_error"}` scope is
    deliberately narrow — background-run outcomes only, explicitly
    excluding `"chat_user"`/`"chat_agent"`/`"proposal"` entries per that
    story's own Constraints. A knowledge gap (born from a *conversational*
    honest-uncertainty reply) does not fit this existing activity-log
    mechanism as-is; it is a new kind of trackable record, not an addition
    to `REQ-SB-11`'s existing log (see Constraints).
  - `app/business/skill_registry.py` / `app/business/agent_orchestration/
    knowledge_bootstrap.py` (`REQ-SB-36-US-01`/`-US-02`) confirm the
    delegated-research chain this story's own "directing the agent to
    research it" closing path composes with already exists and already
    honestly reports "nothing relevant found" rather than fabricating
    (`REQ-SB-36-US-01` Scenario 3) — this story's own Scenario 7 below
    reuses that honest-empty behavior directly, not a new one.
  - `app/business/vault_filing_expert.py` (`REQ-SB-35-US-01`, `Done`)
    confirms a real, working Tier-1/Tier-2 placement-and-write mechanism
    already exists for filing gathered content into the vault — the
    obvious candidate for however "the user directly provides the missing
    information" ends up landing in the vault, mirroring how `REQ-SB-23`'s
    My Day Intake Agent already files conversational input. The exact
    concrete shape (a chat reply routed through the Vault Filing Expert, vs.
    a dedicated gap-resolution UI) is the PRD breadcrumb's own named open
    question (2) below — not resolved here.
- **Genuinely open, not decided in the PRD, named explicitly in its own
  breadcrumb — left to `/spec`, and correctly left further to `/plan-tasks`
  where mechanism-level, not observable-behavior, per this session's own
  established convention (mirrors `REQ-SB-39-US-01`'s identical treatment):**
  1. The exact mechanism for detecting/recording an "I don't know" — a
     structured signal the model itself emits alongside its reply (more
     reliable, requires extending `REQ-SB-33`'s own system-prompt design),
     vs. a pattern-match over the reply text (cheaper, less reliable). This
     story's own Acceptance Criteria (below) describe the *observable*
     behavior only ("an honest 'I don't know' reply results in a recorded
     open gap") and do not presume which detection mechanism produces it.
  2. What "human input fills the gap" looks like concretely — a chat reply
     filed via the Vault Filing Expert the same way `REQ-SB-23`'s My Day
     Intake Agent already files conversational input, or a dedicated
     gap-resolution UI. Not resolved here.
  3. Where the gap count/readiness signal is surfaced. `REQ-SB-41` (Agent
     Overview) is named in the PRD breadcrumb as "the obvious fit, but not
     confirmed" — and direct inspection confirms `REQ-SB-41` itself has
     **no story yet** (PRD-only, `Left to /spec`) and **no
     `html-prototype/` coverage** (its own PRD breadcrumb says plainly "a
     `/design` pass is also needed (no prototype shows this)"). This
     story's own "the user can view an agent's open gaps" scenario (below)
     is therefore written at the observable-behavior level only — it does
     not presume the display surface is Agent Overview, a new standalone
     screen, or an addition to an existing panel.
  4. Whether a closed gap needs any verification that it was actually
     answered correctly, or whether any human-provided or research-derived
     content unconditionally counts as closing it. **Resolved directly here
     by direct, already-established project precedent, not a guess:**
     `MEMORY.md`'s own standing constraint (2026-08-10) — "No
     staging/promotion gate on ingested vault data – Second Brain indexes
     the user's own trusted Obsidian vault, not agent-written scratch data"
     — applies directly: once content is filed into the vault through the
     already-`Done`, already-trusted `REQ-SB-35-US-01` Vault Filing Expert
     mechanism (with its own existing Tier-1/Tier-2 split as the only gate
     that already exists), closing a gap needs no *additional*
     correctness-verification step layered on top. See Constraints.
- **Resolved directly from the requirement's own Acceptance text, not a
  guess — whether "declining rate" needs a threshold/window:** the PRD's
  own Acceptance text asks only that "the count of open gaps for an agent is
  visible and decreases as gaps are closed" — a simple, always-current open
  count, not a computed rate-over-time or a threshold at which an agent is
  formally declared "Expert." This story's own Scenario 5 (below) specs the
  count directly from that text; no threshold/window mechanism is introduced
  or needed this pass (see Constraints and Non-Goals).

## Acceptance Criteria

<!-- Tightened and locked at /plan-tasks step 2 (decomposer), 2026-08-13,
against ADR-032's real mechanism decisions (record_knowledge_gap tool,
knowledge_gap_tracking.py, the two composed closing-path endpoints, the
AgentDetailPanel.tsx Knowledge gaps tab). All 7 scenarios locked — no
material assumption was needed to tighten wording; every mechanism named
below is ADR-032's own Decision, not a decomposer guess. -->

### Scenario 1: An honest "I don't know" reply is recorded as an open knowledge gap

```gherkin
Given an Expert agent's model determines an honest "I don't know" is the
    right reply (REQ-SB-33's grounding/honest-uncertainty guardrail)
When the model calls the record_knowledge_gap(topic) tool before producing
    that reply, intercepted by graph.py's _record_knowledge_gap node
    (ADR-032 point 1, mirrors ADR-017's request_cross_section_help)
Then an open knowledge gap is recorded in agent_knowledge_gaps.json,
    capturing the turn's real originating HumanMessage as the gap's
    question — never the model's own paraphrased topic argument
  And the gap exists as its own trackable record (a unique id, "open"
    status), not just as text inside the chat transcript
  And the model's own honest decline reply is still produced normally to
    the user afterward, looped back through call_model
```
<!-- AC-ID: REQ-SB-40-US-01-AC-01 -->

### Scenario 2: The user can view an agent's accumulated open knowledge gaps

```gherkin
Given an Expert agent has one or more open knowledge gaps recorded
When the user opens that agent's detail panel and selects its
    conditionally-rendered "Knowledge gaps" tab (AgentDetailPanel.tsx,
    gated to agent.type === 'expert', ADR-032 point 5)
Then GET /agents/{agent_id}/knowledge-gaps returns the agent's open gaps
    and its current open_count
  And the tab renders each open gap's question/topic
  And the tab renders the current open-gap count
```
<!-- AC-ID: REQ-SB-40-US-01-AC-02 -->

### Scenario 3: A gap is closed by the user directly providing the missing information

```gherkin
Given an agent has an open knowledge gap
When the user submits an answer for that gap via POST
    /agents/{agent_id}/knowledge-gaps/{gap_id}/resolve
Then the answer is routed through
    vault_filing_expert.determine_placement_and_file unchanged (ADR-032
    point 3 — no additional correctness-verification step)
  And the gap's status becomes "closed" with resolution "human_provided"
    only once filing actually completes — immediately for a Tier-1 write,
    or at Tier-2 approval-finalization time, never before
  And the agent's open-gap count (knowledge_gap_tracking.count_open_gaps)
    decreases accordingly
```
<!-- AC-ID: REQ-SB-40-US-01-AC-03 -->

### Scenario 4: A gap is closed by directing the agent to research it

```gherkin
Given an agent has an open knowledge gap
When the user directs the agent to research that gap via POST
    /agents/{agent_id}/knowledge-gaps/{gap_id}/research
  And knowledge_bootstrap.bootstrap_agent_knowledge(agent_id,
    subject=<gap's question>) returns a real "written" or
    "pending_approval" outcome (ADR-032 point 4, REQ-SB-36's delegated
    web-research chain, unchanged)
Then the gap's status becomes "closed" with resolution "research"
  And the agent's open-gap count decreases accordingly
```
<!-- AC-ID: REQ-SB-40-US-01-AC-04 -->

### Scenario 5: The open-gap count is the visible signal of an Expert agent's readiness over time

```gherkin
Given a newly created Expert agent starts with zero recorded gaps,
    accumulating open knowledge gaps as it honestly encounters things it
    doesn't know (Scenario 1)
When gaps for that agent are closed over time (Scenario 3 and/or
    Scenario 4)
Then knowledge_gap_tracking.count_open_gaps(agent_id) visibly declines as
    each gap closes
  And the agent's Knowledge gaps tab always shows this same current
    open-gap count as the readiness signal — a simple current count, no
    computed decline-rate, time-window, or "now Expert" threshold
```
<!-- AC-ID: REQ-SB-40-US-01-AC-05 -->

### Scenario 6: A normally answered question does not create a spurious gap (regression guard)

```gherkin
Given an agent's tools return a real, relevant answer to the user's
    question (REQ-SB-33-US-01 Scenario 1) — the model does not call
    record_knowledge_gap this turn
When the agent replies
Then no knowledge gap is recorded for that reply
  And agent_knowledge_gaps.json's gap count for that agent is unchanged
```
<!-- AC-ID: REQ-SB-40-US-01-AC-06 -->

### Scenario 7: Research that itself comes back honestly empty does not silently close the gap

```gherkin
Given the user directs the agent to research an open gap via POST
    /agents/{agent_id}/knowledge-gaps/{gap_id}/research
  And knowledge_bootstrap.bootstrap_agent_knowledge returns status
    "no_results" (REQ-SB-36-US-01's own honest-no-results behavior)
When that research attempt completes
Then the gap remains "open" — close_gap is never called
  And the endpoint's own response honestly reflects that the research did
    not resolve the gap
```
<!-- AC-ID: REQ-SB-40-US-01-AC-07 -->

## Affected Screens

- **None approved yet — net-new design needed.** No `html-prototype/` screen
  shows a knowledge-gaps view, a gap count, or a gap-closing affordance
  anywhere today (confirmed by direct inspection — no "gap"/"readiness"/
  "don't know" text anywhere in `html-prototype/agents-map.html`). `REQ-SB-41`
  (Agent Overview), the PRD breadcrumb's own named "obvious fit" for where
  this surfaces, is itself unspecced (PRD-only, no story) with its own PRD
  breadcrumb stating plainly "a `/design` pass is also needed (no prototype
  shows this)." A `/design` pass against this story (and, ideally,
  coordinated with whenever `REQ-SB-41` is specced) is required before
  `/plan-tasks` can lock tasks against a UI shape no one has approved.

## Dependencies

- **Depends on:** `REQ-SB-33-US-01` (`Done`) — the honest-uncertainty
  behavior this story records; every gap this story tracks originates from
  that story's own honest "I don't know" reply path.
- **Related to, one of the two named closing paths:** `REQ-SB-36-US-01`
  (`Done`)/`REQ-SB-36-US-02` (`In Progress`) — the delegated web-research
  chain; Scenario 4/7 compose with its existing honest-result/honest-empty
  behavior, not a reimplementation.
- **Related to, likely filing mechanism for the other closing path:**
  `REQ-SB-35-US-01` (`Done`) — the Vault Filing Expert's existing
  Tier-1/Tier-2 placement-and-write mechanism is the obvious candidate for
  however "the user directly provides the missing information" ends up
  filed into the vault; the exact concrete shape is left open (Context,
  open question 2).
- **Related to, not overlapping:** `REQ-SB-31-US-01` (System Health View,
  `Done`) — current-snapshot infrastructure status, not per-agent knowledge
  completeness, a different kind of signal entirely.
- **Related to, not reused:** `REQ-SB-11-US-01` (Agent Activity & Error
  Observability, `Done`) — its own `_ACTIVITY_KINDS` scope
  (`run_event`/`run_error`) is deliberately narrow to background-run
  outcomes, confirmed by direct code inspection; a knowledge gap is a new
  kind of record this story introduces, not an addition to that log (see
  Constraints).
- **Related to, unspecced, no prototype:** `REQ-SB-41` (Agent Overview) —
  the PRD breadcrumb's own named likely display surface for this story's
  Scenario 2/5; itself has no story and no `html-prototype/` coverage yet
  (see `## Affected Screens`).
- **Related to, explicitly NOT a hard dependency in either direction:**
  `REQ-SB-37-US-01` (Agent Creation Wizard — Expert flow; corrected
  2026-08-13, `REQ-SB-37` was split into three per-type stories the same
  day this story landed) — its own PRD breadcrumb explicitly defers "the
  becoming an Expert part" to this requirement; that wizard's Expert flow
  is deliberately thin (define domain/scope only) because this story is
  where the gap-closing signal actually lives. `REQ-SB-37-US-01`'s own
  Context records the reverse judgment call explicitly: an Expert created
  by that wizard is fully functional (reachable, honestly uncertain per
  `REQ-SB-33`) without this story existing yet; this story adds
  gap-tracking observability on top, later.
- **External:** none new.

## Constraints

- **The exact detection mechanism for an honest "I don't know" reply is left
  to `/plan-tasks`** — a structured signal the model itself emits, vs. a
  pattern-match over the reply text. This story's Acceptance Criteria
  describe only the observable outcome (an honest "I don't know" results in
  a recorded open gap), not the mechanism that produces that outcome.
- **The exact concrete shape of "the user directly provides the missing
  information" is left open** — whether it is a chat reply routed through
  the existing Vault Filing Expert mechanism (`REQ-SB-35-US-01`), or a
  dedicated gap-resolution UI, is a `/plan-tasks`/`/design`-level decision,
  not resolved here.
- **Reuses, does not reimplement, `REQ-SB-36`'s existing delegated-research
  chain** for the "direct the agent to research it" closing path (Scenario
  4/7) — including its own existing honest-empty-result behavior.
- **Reuses, does not reimplement, `REQ-SB-35-US-01`'s existing Vault Filing
  Expert placement/write mechanism** (including its own Tier-1/Tier-2 split)
  for whatever filing step a gap-closing input requires.
- **No additional correctness-verification/approval step for a closed gap
  beyond what `REQ-SB-35-US-01`'s existing Tier-1/Tier-2 mechanism already
  applies** — mirrors this project's own standing "no staging/promotion
  gate" constraint (`MEMORY.md`, 2026-08-10): content filed through the
  already-trusted Vault Filing Expert mechanism unconditionally counts as
  closing the gap it addresses.
- **Readiness is a simple, always-current open-gap count** (per the
  requirement's own Acceptance text) — no computed decline-rate, no
  time-window, and no formal "now officially Expert" threshold/status is
  introduced this pass.
- **Does not extend or modify `REQ-SB-11-US-01`'s existing Agent Activity
  log** (`_ACTIVITY_KINDS`) — a knowledge gap is tracked as its own new kind
  of record, not folded into that log's existing `run_event`/`run_error`
  scope.
- **Does not modify `REQ-SB-33-US-01`'s own locked ACs or its existing
  system-prompt behavior** beyond whatever additive detection mechanism
  `/plan-tasks` designs — this story extends what happens *after* an honest
  "I don't know" reply is produced, not the guardrail that produces it.

## Implementation Tasks

| Task | Title | Depends on | ACs covered |
|---|---|---|---|
| [[REQ-SB-40-US-01-T01]] | `vault_writer.py` — `load_knowledge_gaps_state`/`save_knowledge_gaps_state` primitives | — | (supports AC-01/03/04/05/06/07) |
| [[REQ-SB-40-US-01-T02]] | `app/business/knowledge_gap_tracking.py` — `record_gap`/`close_gap`/`list_agent_gaps`/`count_open_gaps` | T01 | AC-05 |
| [[REQ-SB-40-US-01-T03]] | `state.py` — `AgentConversationState.gap_recorded` field + system-prompt instruction | — | (supports AC-01) |
| [[REQ-SB-40-US-01-T04]] | `graph.py` — `record_knowledge_gap` tool + `_record_knowledge_gap` node + routing branch | T02, T03 | AC-01, AC-06 |
| [[REQ-SB-40-US-01-T05]] | Human-answer closing path — `knowledge_gap_tracking.resolve_gap_with_human_answer` + `POST .../resolve` | T02 | AC-03 |
| [[REQ-SB-40-US-01-T06]] | Delegated-research closing path — `knowledge_gap_tracking.resolve_gap_via_research` + `POST .../research` | T02, T05 | AC-04, AC-07 |
| [[REQ-SB-40-US-01-T07]] | `agents_router.py` — `GET /agents/{agent_id}/knowledge-gaps` | T02 | AC-02 |
| [[REQ-SB-40-US-01-T08]] | `AgentDetailPanel.tsx` — conditional "Knowledge gaps" tab | T05, T06, T07 | AC-02, AC-05 |

Dependency graph: `T01 → T02 → {T04 (with T03), T05 → T06, T07} → T08`.
`T03` is independent of `T01`/`T02` (touches only `state.py`). `T06` additionally
depends on `T05` (reuses its shared, resolution-agnostic pending-approval
helpers — see `T05`/`T06`'s own Context/Notes). No cycles.

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **The exact detection mechanism** (structured model signal vs. text
  pattern-match) — left to `/plan-tasks` (see Constraints).
- **The exact "human input fills the gap" UI/flow shape** — left to
  `/plan-tasks`/a future `/design` pass (see Constraints).
- **Designing or building the concrete "view an agent's open gaps" screen**
  — flagged as net-new-design-needed (see `## Affected Screens`); this
  story's Acceptance Criteria are written at the observable-behavior level
  and do not presume a specific screen shape.
- **`REQ-SB-41`'s own Agent Overview surface itself** — separate, unspecced
  story; this story only composes with it once it exists, per its own PRD
  breadcrumb's "likely fit, not confirmed" framing.
- **Any correctness-verification/review step for a closed gap beyond
  `REQ-SB-35-US-01`'s existing Tier-1/Tier-2 mechanism** — resolved as
  unnecessary this pass (see Constraints).
- **A computed decline-rate, time-window, or a formal "now Expert"
  threshold/status** — resolved as a simple current open-gap count this
  pass (see Constraints).
- **`REQ-SB-37`'s own Expert-type Agent Creation wizard flow** — separate
  story; this story is the "becoming an Expert" half only, not the wizard
  itself.
- **Extending or modifying `REQ-SB-11-US-01`'s existing Agent Activity log**
  — a knowledge gap is its own new record kind (see Constraints).

## Notes

**Prototype parity (`html-prototype/agents-map.html`, the only screen this
requirement could plausibly touch today):**

- Agent detail side panel Settings/Chat/History tabs — **N/A, unaffected.**
  No existing region shows a knowledge-gaps view, a gap count, or a
  gap-closing affordance anywhere in the approved prototype.
- A "knowledge gaps" view/count for an agent — **Net-new design needed.**
  No approved prototype screen or region covers this at all; `REQ-SB-41`
  (Agent Overview), the PRD's own named likely display surface, is itself
  unspecced with no prototype coverage of its own. A `/design` pass is
  required before `/plan-tasks` can lock tasks against a UI shape no one has
  approved.

**Why this is flagged, not cleared (`ESCALATIONS.md` → `ESC-030`):**

1. **Mechanism-level questions left open by the PRD's own breadcrumb** — the
   detection mechanism for "I don't know" and the exact "human input fills
   the gap" shape are both explicitly named "genuinely open, not decided
   here... left to `/spec`" in the requirement's own breadcrumb, and are
   correctly further deferred to `/plan-tasks` per this session's own
   established convention (mirrors `REQ-SB-39-US-01`'s identical treatment)
   rather than guessed here.
2. **Net-new-design-needed** — no `html-prototype/` screen shows any
   knowledge-gaps view anywhere, and the PRD breadcrumb's own named likely
   display surface (`REQ-SB-41`, Agent Overview) is itself unspecced with no
   prototype coverage of its own — there is nothing yet to reconcile this
   story's Scenario 2/5 against.
3. **Not oversized, checked deliberately.** This story is comparable in
   shape to `REQ-SB-31-US-01` (System Health View) or `REQ-SB-11-US-01`
   (Agent Activity Observability) — a tracking/observability layer composing
   with several already-`Done` mechanisms (`REQ-SB-33`, `REQ-SB-35`,
   `REQ-SB-36`), not a re-architecture of any of them. Not split into
   multiple stories, unlike `REQ-SB-39` — there is no safety invariant here
   comparable to that requirement's "never observably ungated" concern that
   would force a sequenced split.
4. Two questions the PRD breadcrumb itself left open were resolved directly
   here, not guessed, and are not part of the flag: (a) whether "declining
   rate" needs a threshold/window — resolved directly from the requirement's
   own Acceptance text as a simple current count; (b) whether a closed gap
   needs additional correctness verification — resolved directly from this
   project's own standing `MEMORY.md` "no staging/promotion gate" constraint.

`ESCALATIONS.md` → `ESC-030` records the full detail. A `REVIEW-QUEUE.md`
entry recommends the concrete next steps.

**Architect pass (`/plan-tasks` step 1, 2026-08-13) — mechanism decisions
relayed and applied, ADR-032 written, `/design` skipped for this batch
(operator-directed):**

- **Detection:** a new bound tool, `record_knowledge_gap(topic: str)`,
  intercepted before generic tool execution exactly like `ADR-017`'s
  `request_cross_section_help` — a real, already-working precedent in
  this graph for a structured model-emitted signal, confirmed by direct
  read of `graph.py`/`_call_model` to be the only structured channel this
  graph has today (no `with_structured_output`/JSON-response-format
  mechanism exists anywhere in it). Not a text pattern-match.
- **Storage:** new `app/business/knowledge_gap_tracking.py` + new tenth
  `.second-brain/agent_knowledge_gaps.json`, mirroring
  `skill_registry.py`'s shape — confirmed NOT folded into
  `app/business/agent_activity.py` (its `_ACTIVITY_KINDS` scope stays
  background-run-only, per that `Done` story's own Constraints).
- **Display surface (the architect's own placement call, since
  `REQ-SB-41` remains unspecced):** a fourth, conditionally-rendered
  "Knowledge gaps" tab on the existing `AgentDetailPanel.tsx`
  (`src/frontend/src/features/agents-map/AgentDetailPanel.tsx`), gated to
  `agent.type === 'expert'`. Direct read corrected the task brief's own
  "Settings/Available-capabilities/Chat/Communication-History" framing —
  the panel carries exactly 3 tabs today (`chat`/`history`/`settings`);
  "Available actions" is a subsection inside `settings`, not a fourth
  tab.
- Full mechanism, every alternative considered, and every consequence:
  `Implementation/Architecture/ADR.md` → `ADR-032`. Full file-level
  shape: `Implementation/Architecture/architecture.md` → "Agent
  Knowledge-Gap Tracking & Expert Readiness" (under "In-App Agent
  Orchestration").

**Architecture scope: §In-App Agent Orchestration (LangGraph) & Shared
MCP Server → "Agent Knowledge-Gap Tracking & Expert Readiness" subsection
(ADR-032); §Frontend Application Architecture → `AgentDetailPanel.tsx`.**
The coder is bounded to these sections plus the already-`Done` sections
they compose with unchanged (Vault Filing Expert, Delegated
knowledge-bootstrap orchestration) — no other architecture.md section is
in scope for this story.

gate: flagged 2026-08-13, gate_reason: trigger-3 (ADR-032 created,
`/plan-tasks` architect pass) — supersedes the prior unclear-requirement
flag (`ESC-030`); those mechanism questions are now resolved (above), not
still open. `REQ-SB-40` itself is finalised PRD text (no `<!-- Draft -->`
marker) — the flag is standard ADR-creation review, not a requirement
finalization concern. Decomposer proceeds to lock ACs/tasks; the human
reviews `ADR-032` and the resulting tasks together in one pass, per
Pipeline.md's "do NOT halt the stage" rule.

**Decomposer pass (`/plan-tasks` step 2, 2026-08-13) — all 7 Gherkin
scenarios tightened and locked as `REQ-SB-40-US-01-AC-01`..`AC-07`
(`locked: true`, no non-locked exceptions), 8 tasks created (`T01`–`T08`,
flat root), `depends_on` wired acyclic (`T01 → T02 → {T04(+T03), T05, T06,
T07} → T08`), every locked AC has at least one AC-tagged manual
verification step across the task set. Story and all 8 tasks advance
`Draft → Ready` together, per Pipeline.md's "tasks move in lockstep with
the story" rule.**

**No new decomposer-owned MUST-FLAG trigger fired this pass** — every
mechanism this decomposition builds against is `ADR-032`'s own already-made
Decision (tool name/shape, node name, storage file/functions, endpoint
paths, tab gating), not a decomposer assumption; no locked AC is
unverifiable (every one maps to a real, inspectable outcome — a JSON file
entry, an HTTP response, a DOM tab); `depends_on` is acyclic; no task
exceeds one working session (each is a single file or a tightly-scoped
pair, comparable in shape to `REQ-SB-20-US-01`'s own 6-task breakdown for
an equivalent ADR-017 tool-interception mechanism). `gate` stays `flagged`
— trigger-3 (`ADR-032` created) is carried unchanged from the architect
pass, per this file's own rule "if the architect flagged the story this
run for an ADR change, leave it `gate: flagged`." No new `REVIEW-QUEUE.md`
entry needed — the architect's own entry (above, 2026-08-13) already asks
the human to "review `ADR-032` and the resulting tasks together," which
this pass's task files now make reviewable. No `ESCALATIONS.md` entry
written by this pass.

**Coder pass (`/implement-sprint`, `SPRINT-035`, 2026-08-14) — all 8 tasks
built and verified live, story `Done`.** All 7 locked ACs (`AC-01`..`AC-07`)
verified live against the real running app, real Compass/Anthropic
Providers, and the real vault — see each task's own Implementation Log for
full detail (`T01`..`T08`). Two scope-internal judgement calls logged for
human spot-check, neither a locked-AC gap: (1) `T06`'s `AC-04` induction
needed 3 temporary, real, already-reverted state changes (a skill grant, a
Provider swap, a Section reassignment) since the real vault's current agent
configuration has no pre-existing agent that is simultaneously a real
Hub-routing candidate for both hops; (2) `T08`'s "Research this" button
click was not independently re-exercised end-to-end in the browser (its own
backend endpoint already fully verified live at `T06`). No new
`ESCALATIONS.md`/`REVIEW-QUEUE.md` entry — no locked AC was unverifiable, no
out-of-scope event occurred. `BACKLOG.md` updated to reflect `Done`.
