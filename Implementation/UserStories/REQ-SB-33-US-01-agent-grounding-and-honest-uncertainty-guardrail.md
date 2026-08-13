---
id: REQ-SB-33-US-01
title: Agent grounding & honest-uncertainty guardrail — system-prompt instruction, applied to every agent's real conversational reply
requirement_ids: [REQ-SB-33]
requirement_section: "REQ-SB-33: Agent Grounding & Honest-Uncertainty Guardrail"
phase: P1
status: Done
gate: clear
gate_reason: "Resolved 2026-08-12 — mechanism resolved by direction, matching this project's own established 'proportionate first, escalate only if proven insufficient' reasoning pattern (ADR-011); global-baseline-vs-per-agent-configurable resolved directly from the PRD Story text's own 'Every agent's' wording. Architect (2026-08-12) independently confirmed the same code and concurred: no ADR needed. Decomposer (2026-08-12) locked all 4 ACs and created REQ-SB-33-US-01-T01. No new UI, no ADR, no contradictory inputs. See Notes for the full resolution trail."
sprint: "SPRINT-018"
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-33-US-01 — Agent grounding & honest-uncertainty guardrail

## Story

**As a** Second Brain user
**I want** every agent's conversational replies to be grounded in what its
own tools actually retrieved, and to honestly say "I don't know" instead
of guessing when its tools don't surface a real answer
**So that** I can trust an agent's answer is a real vault fact, not a
plausible-sounding fabrication from the model's general training
knowledge

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-33: Agent Grounding &
  Honest-Uncertainty Guardrail* — "Every agent's real conversational
  replies (REQ-SB-25) are grounded in what it actually retrieved via its
  own tools — never the model's general training knowledge presented as a
  vault fact — and an agent honestly says it doesn't know, rather than
  guessing or fabricating, whenever its tools don't return an answer or
  the question falls outside its assigned scope (REQ-SB-29)." Acceptance:
  "An agent's conversational reply never states a vault fact that didn't
  come from a real tool result; when its tools return no relevant answer
  (in-scope or not), the agent says so honestly instead of producing a
  plausible-sounding guess."
- **PRD breadcrumb (2026-08-12, operator-authored, cited verbatim, NOT
  re-decided here):** raised alongside `REQ-SB-29` and `REQ-SB-31` as
  three related facets of "making an agent trustworthy, not just
  responsive" — operator's own framing: "avoid Hallucination as much as
  possible... if they don't know I can Get Don't know as an Answer...
  part of Agents Declaration should be the scope, Rail Guides." Distinct
  from `REQ-SB-29`'s own existing Scenario 4/5 honesty behavior (the
  question is outside the agent's assigned scope) — this requirement
  covers the harder, separate case: the question is legitimately in
  scope, but the agent's own tool calls didn't actually surface a real
  answer, and the model must not paper over that gap with a
  plausible-sounding guess.
- **This story's scope is deliberately narrower than "everything the
  breadcrumb's own operator quote gestures at."** The operator quote
  bundles hallucination-avoidance, honest "don't know," AND scope-based
  "Rail Guides" together in one sentence — but the requirement's own
  Acceptance text (quoted above) and its own distinguishing note both
  scope this specific requirement to the grounding/honest-uncertainty
  half; the scope/"Rail Guides" half is `REQ-SB-29`'s own, separately
  specced territory (see Dependencies). This story does not re-spec
  `REQ-SB-29`'s Scenario 4/5 (out-of-scope honesty) or its scope-
  assignment mechanism.
- **Real code read directly, not assumed, to ground this story in what
  actually exists today (all `REQ-SB-25`, `Done`):**
  - `app/business/agent_orchestration/state.py::history_entries_to_
    messages` prepends exactly one `SystemMessage` to every conversation:
    `"You are the {agent_name} agent for the user's personal Second Brain
    knowledge base."` — no grounding, honesty, or anti-fabrication
    instruction of any kind exists in the prompt today.
  - `app/business/agent_orchestration/graph.py::_call_model` binds the
    agent's tools (`model.bind_tools(tools)` whenever `tools` is
    non-empty) and invokes the model directly against the full message
    list. If the model's response carries `tool_calls`, `_execute_tools`
    runs them and routes back to `_call_model`; otherwise the model's raw
    `response.content` is returned as the final `reply` with **no
    verification step of any kind** — nothing today checks whether that
    reply's claims are actually traceable to a real tool result before
    it is returned to the user.
  - This confirms the PRD's own framing is accurate: today, a tool-bound
    model is free to answer a vault-fact question directly from its own
    general training knowledge, with nothing in the graph or the prompt
    telling it not to, and nothing catching it if it does.
- **Mechanism resolved here, by direction, matching this project's own
  already-established "proportionate first, escalate only if proven
  insufficient" reasoning pattern (not a guess) — this is the PRD
  breadcrumb's own open question (1):** a stronger system-prompt
  instruction added to `history_entries_to_messages`'s existing prepended
  `SystemMessage` (or a second `SystemMessage`, mirroring `REQ-SB-26`'s
  own `retrieve_memory` precedent of inserting an additional
  `SystemMessage`), instructing the model to answer only from its own
  tool results and to honestly say it doesn't know rather than guess —
  **not** a separate verification/citation step that checks the reply is
  actually traceable to a real tool result before returning it. This
  mirrors `ADR-011`'s own decision reasoning exactly (point 1: "exact-
  phrase/keyword substring matching... not an NLU/LLM pipeline...
  proportionate to what actually exists in this project today... building
  [more machinery] for a [small surface] would be pure speculative
  machinery this project's own discipline discourages") — a prompt-level
  instruction is the cheap, immediately buildable option; a
  verification/citation step is real added latency/complexity with no
  proof yet that the cheaper option is insufficient. **Honest limitation,
  recorded, not hidden:** a system-prompt instruction is not a hard
  technical guarantee — an LLM can still fail to follow an instruction.
  This story's Constraints call this out explicitly rather than
  overclaiming enforcement; escalating to a verification/citation step is
  legitimate future follow-on work if this proves insufficient in real
  use (not built here).
- **Global-vs-per-agent-configurable resolved directly from the PRD
  Story text's own wording (not a guess) — this is the PRD breadcrumb's
  own open questions (2) and (3):** the requirement's own Story
  description states "**Every agent's** real conversational replies...
  are grounded" — unqualified, no per-agent exception named anywhere in
  the requirement or its Acceptance text. This story specs the guardrail
  as a **global, mandatory baseline applied to every agent's reply path**
  (the one shared `history_entries_to_messages`/`_call_model` code path
  every agent's conversation already runs through, per `REQ-SB-25`) —
  **not** a per-agent opt-in/opt-out toggle, and **not** a new field on
  the Agent Settings surface. This directly resolves question (3) as
  well: since there is no per-agent configurability this pass, there is
  no new "Agent Declaration" UI surface to design — the breadcrumb's own
  named "always-on baseline behavior with nothing to configure" option is
  the one the requirement's own text supports. A future per-agent
  opt-out (e.g. an agent explicitly meant to answer general-knowledge
  questions too) is legitimate follow-on scope, not built here.
- **No new `html-prototype/` screen or region is needed.** The chat
  reply is rendered in the existing `.chat-message.chat-message--agent`
  element inside each agent's `chat-thread` (already approved,
  `REQ-SB-13`) — this story changes the *content* an agent's reply is
  allowed to state, not any visual structure. Confirmed by direct
  inspection of `html-prototype/agents-map.html`'s five agent panels
  (Email/Meeting/To-Do Capture, People Notes, Vault Q&A) — each already
  has an unmodified `chat-thread`/`chat-message` region.

## Acceptance Criteria

<!-- Locked by the decomposer at /plan-tasks, 2026-08-12. Each scenario below
carries its assigned AC-ID as a trailing tag comment; wording lightly tightened
for buildability, no scenario intent changed. Scenarios below deliberately do
not re-spec REQ-SB-29's own Scenario 4/5 (out-of-scope honesty) — see Context
and Dependencies. -->

### Scenario 1: A real question with a real tool-backed answer still works normally (regression guard)

```gherkin
Given an agent's tools return real, relevant vault content for the user's
    question
When the user asks that question in the agent's chat
Then the agent's reply is grounded in the real tool result content
  And the reply is returned normally, exactly as REQ-SB-25's existing
    conversational reply behavior already works
```
<!-- AC-ID: REQ-SB-33-US-01-AC-01 -->

### Scenario 2: A legitimately in-scope question whose tools return no relevant result gets an honest "I don't know"

```gherkin
Given the user asks an agent a question that its tools are capable of
    answering in principle
  And the agent's tool calls return no relevant result for that question
When the agent produces its reply
Then the reply honestly states that it doesn't know / couldn't find an
    answer
  And the reply does not state a plausible-sounding guess as if it were a
    real vault fact
```
<!-- AC-ID: REQ-SB-33-US-01-AC-02 -->

### Scenario 3: A tool call failure does not get papered over with a fabricated answer

```gherkin
Given the user asks an agent a question that triggers a tool call
  And that tool call fails or errors rather than returning a usable result
When the agent produces its reply
Then the reply honestly reflects that it could not retrieve an answer
  And the reply does not substitute a fabricated answer from the model's
    own general training knowledge in place of the failed tool result
```
<!-- AC-ID: REQ-SB-33-US-01-AC-03 -->

### Scenario 4: The reply never states as fact anything not traceable to an actual tool result

```gherkin
Given an agent is asked about something not actually present anywhere in
    the vault (a fact the model might otherwise "know" from its own
    general training knowledge, but which no tool call for this
    conversation actually returned)
When the agent produces its reply
Then the reply does not present that general-training-knowledge fact as
    if it were a real vault fact
  And the reply honestly indicates it has no vault-grounded answer to
    give
```
<!-- AC-ID: REQ-SB-33-US-01-AC-04 -->

## Affected Screens

- None — backend/prompt-behavior only. The existing `chat-thread`/
  `chat-message` rendering in each agent panel of
  `html-prototype/agents-map.html` (Email Capture, Meeting Capture,
  To-Do Capture, People Notes, Vault Q&A) is unchanged; only the content
  an agent's reply is allowed to state changes. No new field is added to
  any agent's Settings `kv-list`.

## Dependencies

- **Depends on:** `REQ-SB-25-US-01` (`Done`) — the real conversational
  reply path (`history_entries_to_messages`, `_call_model`) this story
  guards; this story is a behavioral extension of that already-shipped
  graph, not a new graph or a new entry point.
- **Related to, not overlapping:** `REQ-SB-29` (Agent-to-Tag/Folder
  Scoping, `REQ-SB-29-US-01`, `Draft`) — REQ-SB-29's own Scenario 4/5
  already cover the "the question is outside my assigned scope" honesty
  case; this story is the separate, harder case of an in-scope question
  whose tool calls simply didn't surface an answer. This story does not
  depend on REQ-SB-29 being built — it applies to every agent's reply
  path today, independent of whether that agent has any tag/folder scope
  assigned.
- **Related to:** `REQ-SB-31` (System Health View, `REQ-SB-31-US-01`,
  `Draft`, flagged) — that story's own PRD breadcrumb and Context note
  this guardrail is expected to eventually surface, per-agent, as part of
  that story's own health/readiness signal. This story does not build any
  such surfacing itself — a future health-view story reading whether this
  guardrail's system-prompt instruction is present for a given agent is
  that story's own scope, not re-specced here.
- **Related to:** `REQ-SB-26-US-01` (Agent Memory, `Done`) — its own
  Scenario 3 already established the same "honest, not fabricated"
  posture one layer over for recalled facts ("an agent asked to recall
  something never actually shared honestly says so rather than
  fabricating an answer"); this story applies the equivalent posture to
  tool-grounded vault-fact answers, and the same live-prompting
  verification approach that scenario used is expected to carry over.
- **External:** none new.

## Constraints

- **Mechanism: a system-prompt instruction only, this pass — not a
  verification/citation step.** Extend the existing prepended
  `SystemMessage` in `history_entries_to_messages` (or add a second
  `SystemMessage`, mirroring `REQ-SB-26`'s `retrieve_memory` precedent)
  with an explicit grounding/honest-uncertainty instruction. Do not build
  a reply-verification/citation mechanism that checks the model's output
  against real tool results before returning it — that is real added
  latency/complexity with no proof yet that the cheaper prompt-level
  option is insufficient; it is legitimate future escalation, not this
  story's scope.
- **Global, mandatory baseline — applies to every agent's reply path,
  with no per-agent opt-out or configuration this pass.** Do not add any
  new field to the Agent Settings `kv-list` or any other "Agent
  Declaration" UI surface for this guardrail.
- **Honest limitation, not hidden:** a system-prompt instruction gives no
  hard technical guarantee the model will always comply — this story
  specs and verifies the intended behavior via real prompting (mirroring
  `REQ-SB-26-US-01`'s own honesty-scenario verification approach), not a
  mechanical enforcement check.
- Do not touch `_execute_tools`, `_retrieve_memory`, `_extract_memory`,
  or any other existing node's own logic beyond `_call_model`'s prompt
  input — this story is scoped to the model-facing instruction, not a
  restructuring of the graph.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-33-US-01-T01 | backend | Extend `history_entries_to_messages`'s existing identity `SystemMessage` with a grounding/honest-uncertainty instruction; verify against all 4 locked ACs via real prompting | `app/business/agent_orchestration/state.py` | `../Tasks/REQ-SB-33-US-01-T01-grounding-honest-uncertainty-system-prompt.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **REQ-SB-29's own out-of-scope honesty behavior (its Scenario 4/5)** —
  a different, already-specced case; not re-specced here.
- **A reply-verification/citation mechanism** that checks a reply's
  claims against real tool results before returning it — deferred; the
  breadcrumb's own named stronger alternative, not built this pass (see
  Constraints).
- **Per-agent configurability** (an opt-out letting a specific agent
  answer general-knowledge questions too) — the requirement's own "Every
  agent's" text resolves this pass as a global baseline; a future
  per-agent toggle is legitimate follow-on scope, not built here.
- **Any new Agent Settings / "Agent Declaration" UI surface** — resolved
  as unnecessary this pass, since there is no per-agent configuration to
  expose.
- **REQ-SB-31's own System Health surfacing** of whether this guardrail
  is active for a given agent — related, not this story's scope.
- **Non-vault, general-knowledge questions unrelated to any tool call**
  (e.g. a question the agent could answer without needing a vault-query
  tool at all) — this requirement's Acceptance text scopes specifically
  to "a vault fact"; broader policy on whether an agent may answer
  general-knowledge questions at all is not addressed by this story.

## Notes

**Prototype parity (agents-map.html, all five agent panels):**

- Settings `kv-list` — **N/A**, not touched (no new field; resolved as a
  global baseline, no per-agent configuration this pass — see Context).
- Chat `chat-thread`/`chat-message` region — **Specced.** Existing
  region, unmodified visually; this story changes only the content an
  agent's reply is allowed to state (Scenarios 1-4).
- Available Actions / Communication History blocks — **N/A**, not
  touched by this story.

**Resolution trail (both PRD-breadcrumb open questions resolved, neither
guessed):**

1. *Mechanism* (system-prompt instruction vs. verification/citation
   step) — resolved by direction, applying this project's own
   already-established `ADR-011` reasoning pattern ("proportionate to
   what actually exists... building [more machinery] would be pure
   speculative machinery this project's own discipline discourages") to
   this new case. Not identical to an ADR-worthy decision (no new tool,
   framework, or structural boundary — a prompt-content change to an
   already-shipped graph node), so no ADR is created here; the architect
   may still weigh in at `/plan-tasks` if the prompt-only approach proves
   structurally insufficient once tasked out.
2. *Global baseline vs. per-agent configurable, and the UI surface
   question* — resolved directly from the requirement's own Story text
   ("Every agent's real conversational replies... are grounded"), which
   states this as unqualified and universal with no per-agent exception
   named anywhere in the requirement. This also resolves the "how is
   this exposed as part of Agent Declaration" question: since there is
   no per-agent configuration this pass, there is nothing to expose —
   the breadcrumb's own named "always-on baseline behavior with nothing
   to configure" option is the one the text supports.

Neither resolution required an ESCALATIONS.md entry: neither is a
material assumption filling a genuine PRD gap (item 1 is a delegated,
precedent-grounded implementation-mechanism choice; item 2 is a direct
reading of the requirement's own text), no PRD inputs are contradictory,
the story is not oversized, and no net-new design surface exists to flag.

gate: clear 2026-08-12 — no MUST-FLAG triggers fired. REQ-SB-33 itself is
finalised PRD text (no `<!-- Draft -->` marker); no material assumption
was needed beyond the precedent-grounded/text-grounded resolutions
recorded above; no ADR was created or changed; no ESCALATIONS.md entry
was written; the story is not oversized (one prompt-content change, one
existing graph node touched); no contradictory PRD inputs exist; and no
multiple-equally-valid/genuinely-unclear question remains open after the
resolution trail above. Ready for `/plan-tasks`.

**Architect pass (2026-08-12) — independently confirmed, not merely
accepted on faith:** read `app/business/agent_orchestration/state.py`
(`history_entries_to_messages`) and `graph.py` (`_call_model`,
`_execute_tools`, `_route_after_model`) directly. Confirmed the analyst's
own Context summary is accurate: exactly one `SystemMessage` is prepended
today, no grounding/honesty instruction exists anywhere in the prompt or
graph, and `_call_model` returns `response.content` as the final `reply`
with no verification step against real tool results. Concur this is a
prompt-content change to an already-`Accepted`, already-shipped graph
node (`ADR-015`) — no new tool, framework, node, state file, or
structural boundary — so **no ADR is created or changed** this pass. Full
mechanism recorded in `architecture.md` → "In-App Agent Orchestration
(LangGraph) & Shared MCP Server" → new "Addendum (REQ-SB-33-US-01 agent
grounding & honest-uncertainty guardrail, 2026-08-12)" subsection:
extends `history_entries_to_messages`'s existing single identity
`SystemMessage`'s own content string with an additional grounding/
honest-uncertainty instruction — deliberately **not** a second
`SystemMessage` (distinguished from `ADR-016`'s `_retrieve_memory`
precedent, which inserts a second message for a genuinely separate,
per-conversation-varying concern; this instruction is static and
agent-generic, the same category as the existing identity sentence).

**Architecture scope:** §"In-App Agent Orchestration (LangGraph) &
Shared MCP Server" (`REQ-SB-20, REQ-SB-25, REQ-SB-26, REQ-SB-27, see
ADR-015`) — specifically its "LangGraph — where it lives, what it
composes with" subsection (for `agent_orchestration/state.py`'s existing
shape) and this pass's own new "Addendum (REQ-SB-33-US-01 agent grounding
& honest-uncertainty guardrail, 2026-08-12)" subsection. The decomposer's
task(s) and the eventual coder are bounded to `app/business/
agent_orchestration/state.py::history_entries_to_messages` only —
`graph.py` (`_call_model`, `_execute_tools`, `_retrieve_memory`,
`_extract_memory`) is explicitly out of file scope, per this story's own
Constraints ("do not touch `_execute_tools`, `_retrieve_memory`,
`_extract_memory`, or any other existing node's own logic beyond
`_call_model`'s prompt input" — and `_call_model` itself needs no edit,
since the prompt input it receives is already fully assembled by
`history_entries_to_messages` before `_call_model` ever runs).

**Gate:** `gate: clear` 2026-08-12 (architect pass) — no ADR created or
changed (`ADR-015` already `Accepted` and already covers this story in
full), no material assumption beyond the ordinary mechanism-filling
detail above, no contradiction with any `Accepted` ADR, the PRD, or a
`MEMORY.md` constraint (no staging/promotion gate — not implicated; the
Hermes external-integration-point constraint — not implicated), and no
other MUST-FLAG trigger fired. Handing off to the decomposer.

**Decomposer pass (2026-08-12):** all 4 scenarios locked as-is (wording
lightly tightened, no intent change) — `REQ-SB-33-US-01-AC-01` through
`AC-04`, tagged directly under each scenario's Gherkin fence in
`## Acceptance Criteria`. One task, `REQ-SB-33-US-01-T01`
(`../Tasks/REQ-SB-33-US-01-T01-grounding-honest-uncertainty-system-prompt.md`),
scoped to `app/business/agent_orchestration/state.py::
history_entries_to_messages` only, per the architect's own file-scope
note above — not split further, since the entire change is one prompt-
content edit to one function, and all 4 ACs are observable from the one
shared code path it feeds (`_call_model`'s existing message-consumption,
unmodified). `depends_on: []` — the underlying `REQ-SB-25-US-01` graph
this story extends is already `Done`. All 4 locked ACs have a matching
AC-tagged manual verification step in `T01`'s `## Tests` (real prompting,
mirroring `REQ-SB-26-US-01`'s own honesty-scenario verification
approach — test tooling still pending project-wide). No MUST-FLAG trigger
fired at this step: no new material assumption, `REQ-SB-33` is finalised
PRD text, no ESCALATIONS.md entry, one small task (not oversized), no
contradictory inputs, no genuinely unclear/multiple-equally-valid
breakdown question (the story's own Constraints already fix the single
file/function scope). `gate: clear` stands (the architect step above
found nothing to flag either — no ADR was touched). `status: Draft →
Ready`; `T01` written at `status: Ready` to match. Ready for
`/plan-sprints`.
