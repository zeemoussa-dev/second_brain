---
id: REQ-SB-66-US-01
title: Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings
requirement_ids: [REQ-SB-66]
requirement_section: "REQ-SB-66: Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings"
phase: P1
status: Done
gate: flagged
gate_reason: "Four distinct triggers were named; three are now RESOLVED, one is NEW. (1) trigger-1 (material assumption) — 'compass_client.py's various classify_* functions' is read expansively as all 4 of that file's hardcoded-prompt functions, plus two disclosed call-site-ownership scoping calls — see ## Notes. STILL STANDING, unresolved-but-disclosed. (2) RESOLVED 2026-08-16, operator-confirmed: Thread-Match/Merge and Detect-Recurring-Pattern (2 of the Email Capture Pipeline's 6 real Jobs) have NO real LLM/Compass call of their own — the Prompt field is OMITTED entirely for a Job with no real call site (never shown-but-inert); Guardrails still shows regardless. ESCALATIONS.md ESC-039 closed. Scenario 10/Constraints updated to match. (3) RESOLVED 2026-08-16, operator-directed: 'no more designer we will do it later build the needed ui we will fix it later' — the /design pass is explicitly, deliberately skipped for this story; implementation proceeds directly to /plan-tasks/coder using the codebase's own existing visual language (matching this project's established 'reuse existing generic UI, no fresh /design pass' precedent used for several other stories this session), not a silent omission. (4) RESOLVED 2026-08-16, /plan-tasks architect pass: the Job-Settings-detail-view data-source/endpoint shape is Option A — a new GET/PATCH /agents/{agent_id}/jobs/{job_id}/settings pair plus a genuinely separate, minimal frontend shell, never a widening of AgentDetailPanel.tsx's shared tab machinery (Option B rejected). (5) NEW, trigger-3 — this resolution required a new ADR, ADR-044: a genuine, material narrowing of ADR-041's own deferred 'whether/how a Job earns its own surface' Consequence and ADR-043 point 6 ('Jobs stay non-addressable in every respect'), unlike REQ-SB-65-US-01's own structurally similar, 'no new ADR' Option A/B precedent (that one was pure read, zero addressability change; this one makes a Job clickable and its Settings editable/persisted for the first time). See ## Notes and REVIEW-QUEUE.md — the decomposer still runs, this does not halt the stage. Decomposer pass, /plan-tasks step 2, 2026-08-16: all 10 scenarios locked (AC-01..AC-10), 7 tasks written (T01-T07), every locked AC has at least one tagged verification step, depends_on is acyclic (including 2 cross-story edges onto REQ-SB-65-US-01-T01/T02, both Done) — status advanced Draft to Ready per the gating contract. gate stays flagged as a standing breadcrumb for (1) trigger-1, the still-standing compass_client.py call-site-scoping material assumption (T02 carries this flag forward), and (2) trigger-3, ADR-044 human review (T06/T07 carry this flag forward) — neither blocks the build loop. See REVIEW-QUEUE.md."
sprint: "SPRINT-052"
created: 2026-08-16
updated: 2026-08-17
---

# REQ-SB-66-US-01 — Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings

## Story

**As a** Second Brain user (the operator)
**I want** every real Agent's and every real Job's own Settings surface to show
a real, persisted, editable Prompt — one that the real runtime call site already
running that Agent/Job actually reads, not a UI field that does nothing — plus a
Guardrails field reserved for future use with no defined behavior yet, and for a
Job's own Settings to be reachable by clicking it on the Agents Map
**So that** I can manage/tune what actually runs each Agent/Job today (today
every one of those prompts is buried, hardcoded, in Python I can't reach from
the app), and have a reserved interface slot to define guardrail behavior later
without a second requirement just to add the field

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-66: Real, Editable Per-Agent/Job Prompt
  + a Guardrails Placeholder in Settings*. Raised 2026-08-16, same day
  `REQ-SB-65` shipped, once the operator started thinking through "different
  views per agent type." Operator's own framing: "Jobs we don't need to chat
  with, I need to have the prompt that runs the agent to be in the Settings so
  I can manage it later, the guardrails — I want you to think what do we need
  to have per Agent Views and Settings." Asked directly what "guardrails"
  should cover: "I still don't know but we are building a placeholder" —
  confirmed explicitly as structure-only, not content-defined.
- **All three of the PRD's own named open questions are RESOLVED, same day,
  same follow-up discussion — treated here as locked inputs, not
  re-litigated:**
  1. **Per-type Settings differences:** NOT a separate screen per Type — one
     Settings tab, fields conditionally shown per Type, exactly like today's
     Domain-for-Expert/Purpose-for-Producer pattern. Prompt + Guardrails show
     for every Type including Jobs. A Job's own Settings ends up genuinely
     minimal — Prompt + Guardrails only (no Vault Scope/Working Mode/
     Schedule/Skills of its own).
  2. **Prompt storage shape:** a new sibling `.second-brain/agent_prompts.json`
     keyed by id, composed alongside `agent_registry.py` (never inside it) —
     mirrors this codebase's own repeated, already-real pattern
     (`agent_keywords.json`/`agent_scopes.json`/`agent_working_modes.json`,
     confirmed by direct reading of `app/data_access/vault_writer.py`'s own
     `load_agent_keywords`/`save_agent_keywords`/`_agent_keywords_path`
     shape, and `ADR-011`'s "identity stays hardcoded, mutable state lives
     separately" rule). The same id-keyed shape covers both real Agents and
     real Jobs uniformly — a Job has no `agent_registry.py` entry to attach
     to, but a sibling JSON file needs no such entry, just an id string.
  3. **Default-fallback behavior:** additive layering. An unset Prompt
     override falls back to today's existing hardcoded default, unchanged —
     confirmed by direct reading of `app/business/working_mode_registry.py`'s
     own self-healing-default `_load_state`/`get_agent_working_mode` shape,
     the exact pattern this story's own default-fallback mirrors.
- **The real, hardcoded prompt call sites this requirement targets — read
  directly, not assumed, with ONE verified discrepancy vs. the PRD's own
  prose:**
  - `app/data_access/compass_client.py` has **four** hardcoded-prompt-building
    functions, not the two literally named "classify_*": `classify_email`
    (owned by the `classify` Job, `email_classification.classify_captured_email`),
    `classify_task` (owned by the `todo-capture` Agent,
    `todo_classification.py`), `guess_project_for_thread` (owned by the
    `route_to_project` Job, `email_classification.route_to_project`), and
    `summarize_content` (owned by the `summarize_attachment` Job,
    `email_classification.summarize_attachment` — but see the disclosed
    dual-ownership scoping call below). This story reads "compass_client.py's
    various classify_* functions" expansively as shorthand for all four —
    narrowly matching only the two literally-named `classify_*` functions
    would arbitrarily leave `guess_project_for_thread`/`summarize_content`
    hardcoded despite being the exact same kind of gap the requirement's own
    motivating text names ("today every prompt in this codebase is hardcoded
    in Python"). Disclosed scoping call, not silently picked (trigger-1).
  - `app/business/vault_filing_methodology.py`'s `build_placement_prompt`
    (its `_METHODOLOGY_EXCERPT` `SystemMessage` half) — owned unambiguously
    by the `vault-filing-expert` Agent: `vault_filing_expert.
    determine_placement_and_file` always resolves
    `model_factory.resolve_agent_model("vault-filing-expert")` regardless of
    which agent is the `requesting_agent_id` (confirmed by direct reading —
    `requesting_agent_id` is used only for Pending-Approval bookkeeping, never
    for prompt/model selection), so there is exactly one owning identity, no
    ambiguity.
  - **Verified discrepancy vs. the PRD's own text:** the PRD names
    "`agent_chat.py`'s Expert system prompt." Direct reading of
    `app/business/agent_chat.py` found it carries **no LLM prompt of any
    kind** — it is `ADR-011`'s own exact-phrase/keyword-substring chat-trigger
    matcher, deliberately non-LLM. The real, only per-turn LLM system prompt
    lives in `app/business/agent_orchestration/state.py`'s
    `history_entries_to_messages` (the `SystemMessage` carrying the agent's
    identity sentence + the honest-uncertainty grounding instruction,
    `REQ-SB-33-US-01`) — read by `graph.py`'s `_retrieve_memory`/`_call_model`
    nodes on **every** real Agent's chat turn (Worker/Producer/Expert alike,
    via `run_agent_conversation`), not Expert-specific despite the PRD's own
    naming. This story wires the override into the REAL call site
    (`state.py`), owned unambiguously by whichever `agent_id` is chatting —
    mirrors `REQ-SB-65-US-01`'s own "verified discrepancy, found by reading
    the real code directly" precedent.
- **Disclosed dual-ownership scoping call, `summarize_content`:** this
  function has a SECOND real call site beyond the Summarize-Attachment Job —
  `app/business/skill_tools.py`'s `summarize_file`, a shared `@mcp_server.
  tool()` MCP skill invokable by **whichever agent's own model** calls it
  mid-chat (confirmed by direct reading: `summarize_file(content,
  source_description)` takes no `agent_id` argument at all, unlike
  `web_research`, which does). There is no single owning identity to key an
  override to at that call site. This story wires the override ONLY into the
  Summarize-Attachment Job's own direct call
  (`email_classification.summarize_attachment` →
  `compass_client.summarize_content`); `skill_tools.summarize_file`'s own call
  is explicitly left unwired — genuinely ambiguous shared ownership, not
  silently picked (see `## Non-Goals`).
- **Disclosed scoping call, `classify_email`'s second caller:**
  `email_classification.classify_recent_emails` also calls
  `compass_client.classify_email` directly — confirmed still-real, reachable
  code (its own docstring: "dead code for the email-capture-pipeline path...
  `app/api/email_poc_router.py` still calls this function directly as its own
  standalone, separate manual `/poc/classify-emails` endpoint"), not the real
  production path this requirement's Job-Prompt concept targets. This story
  wires the override only into the `classify` Job's own direct call
  (`classify_captured_email`); `classify_recent_emails`' own separate call is
  explicitly left unwired (see `## Non-Goals`).
- **The genuinely new, unresolved gap this pass found — not one of the PRD's
  own 3 already-resolved questions, logged as `ESCALATIONS.md` → `ESC-039`:**
  two of the Email Capture Pipeline's six real Jobs — `thread_match_merge`
  and `detect_recurring_pattern` (confirmed by direct reading of
  `app/business/email_classification.py`) — make **no Compass call and have
  no LLM prompt of their own at all**; both are purely deterministic Python.
  Decision 1's own blanket "Prompt shows for every Type including Jobs" rule
  therefore produces a Prompt Settings field for these two Jobs with **no
  real runtime call site to wire an override into** — directly tensioning
  with the requirement's own explicit "not just a UI field that does nothing"
  bar. None of the operator's 3 already-resolved decisions addresses this
  case (it was not visible until the real per-Job call sites were read
  directly). Flagged rather than guessed — see `## Notes` and `ESC-039`.
- **This deliberately reopens a decision `REQ-SB-65-US-01` made the same
  week.** That story's own `## Constraints` state: "Jobs stay non-addressable
  in every respect OTHER than their structural shape becoming visible...  no
  click-to-open-detail behavior distinct from what the rest of the Map
  already does for a non-clickable structural node." Direct reading of the
  real frontend confirms the CURRENT enforcement mechanism for that
  constraint is implicit, not an explicit click-guard: clicking any dot on
  the Agents Map (`AgentsMapCanvas.tsx`, `onSelect={onSelectAgent}` — applied
  uniformly, with no Job/Agent distinction in the click handler itself) opens
  `AgentDetailPanel`, which calls `fetchAgent(agentId)` →
  `GET /agents/{agent_id}` → `agent_registry.get_agent(agent_id)`. For a real
  Job id (e.g. `"classify"`, spliced onto the Map by
  `REQ-SB-65-US-01`'s own `pipelineJobTreeAdapter.ts`), that registry lookup
  returns `None` (Jobs have no `agent_registry.py` entry) → the backend
  404s → the panel's own `agent` state never populates → only the empty
  overlay/close-button shell renders, no title/tabs/body. This requirement
  asks that a Job click now open a real, populated Settings-only view
  instead — Chat/History/Working-Mode/Schedule/Visual stay excluded exactly
  as `REQ-SB-65-US-01`'s Constraints already established; only the
  Settings-view carve-out is new.
- **Existing, unrelated "Guardrails" surface — noted, not touched by this
  story:** `AgentDetailPanel.tsx`'s Overview tab already renders a hardcoded,
  non-editable `GUARDRAILS_STATEMENT` kv-row (`REQ-SB-33-US-01`'s own
  grounding-guardrail language: "Replies are grounded in what this agent's
  own tools actually find in the vault..."), identical text for every real
  Agent, never per-agent, never editable, never in `html-prototype/`. This
  requirement's new Guardrails field is a DIFFERENT thing — a new, per-id,
  editable, persisted, structure-only field in the SETTINGS tab, not the
  Overview tab's existing static sentence. The Overview row is left
  byte-for-byte unchanged by this story.
- **Prototype coverage — confirmed absent, not assumed:** a direct grep of
  `html-prototype/` for "Guardrails"/"Prompt" as a Settings-tab concept
  returns zero matches anywhere (`html-prototype/agents-map.html`'s own
  existing Settings kv-list sections show only the fields already shipped by
  prior stories — Section/Provider/Working mode/Background
  Agent/Keywords/Vault scope). Neither a Prompt field, a Guardrails field,
  nor a Job-only minimal Settings shell exists in the approved prototype
  anywhere. See `## Notes` → Prototype parity.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Every hardcoded prompt-building function in compass_client.py gains a real, per-owning-Agent/Job override

```gherkin
Given compass_client.py's four hardcoded prompt-building functions each have
    exactly one unambiguous owning identity in this story's scope
    (classify_email -> the "classify" Job; classify_task -> the
    "todo-capture" Agent; guess_project_for_thread -> the "route_to_project"
    Job; summarize_content -> the "summarize_attachment" Job, via its own
    direct call only)
When the operator sets a new Prompt value on one of these owning
    Agents'/Jobs' own Settings surface and saves it
Then a subsequent real run of that owning Agent's/Job's own real call site
    (e.g. the Classify Job's next real pipeline invocation) uses the newly
    stored Prompt value, not the previously hardcoded default text
  And no other Agent's/Job's own prompt behavior changes as a result
```
<!-- AC-ID: REQ-SB-66-US-01-AC-01 -->

### Scenario 2: A real Agent's own Chat system message becomes overridable, replacing the hardcoded identity/grounding text

```gherkin
Given a real Agent (Worker, Producer, or Expert) has a stored Prompt override
    set in its own Settings
When that Agent's Chat is used for a new turn
Then the per-turn system message the real conversation graph
    (agent_orchestration/state.py's history_entries_to_messages, read by
    graph.py on every turn) sends to the model uses the stored override
    instead of today's hardcoded identity/grounding sentence
  And the honest-uncertainty/grounding behavior this system message exists to
    enforce (REQ-SB-33) is not silently dropped just because the text
    changed -- the override replaces the DEFAULT TEXT, never the mechanism
    that reads it
```
<!-- AC-ID: REQ-SB-66-US-01-AC-02 -->

### Scenario 3: The Vault Filing Expert's own real placement-decision prompt becomes overridable

```gherkin
Given the "vault-filing-expert" Agent has a stored Prompt override set in its
    own Settings
When determine_placement_and_file next builds its placement prompt
    (vault_filing_methodology.build_placement_prompt)
Then the real call reads the stored override instead of the hardcoded
    _METHODOLOGY_EXCERPT text
  And this applies identically whether the Vault Filing Expert is reached via
    REQ-SB-20 Hub routing or via the Consult-Librarian Job's own internal
    call (email_classification.consult_librarian) -- one single owning
    identity, one single override, regardless of caller
```
<!-- AC-ID: REQ-SB-66-US-01-AC-03 -->

### Scenario 4: An Agent/Job with no stored Prompt override keeps using today's existing hardcoded default, unchanged

```gherkin
Given an Agent or Job that has never had a Prompt override saved for its own
    id
When its real runtime call site runs
Then it uses exactly the same hardcoded default prompt text this codebase
    already ships today -- byte-for-byte unchanged
  And no operator action is required for any already-shipped Agent's/Job's
    behavior to stay exactly as it is today
```
<!-- AC-ID: REQ-SB-66-US-01-AC-04 -->

### Scenario 5: A Guardrails field is present, editable, and persisted for every real Agent Type and every real Job -- with no enforcement behavior

```gherkin
Given any real Agent (Worker, Producer, or Expert) or any real Job (one of
    the Email Capture Pipeline's own six)
When its own Settings surface is viewed
Then a Guardrails field is present, showing whatever value (if any) is
    currently stored for that id
  And the operator can edit and save a new Guardrails value, which persists
    across a reload
  And no part of this story wires that stored value into any real enforcement
    behavior -- it reserves the interface slot only, exactly as the
    requirement's own "structure only, not content-defined" framing states
```
<!-- AC-ID: REQ-SB-66-US-01-AC-05 -->

### Scenario 6: Per-Type Settings stay one conditional tab, never a separate screen -- a Job's own Settings is genuinely minimal

```gherkin
Given the existing per-Type conditional-field convention (one Settings tab,
    fields shown/hidden per Type, e.g. Domain-for-Expert/Purpose-for-Producer)
When Prompt and Guardrails are added
Then they appear on that SAME existing Settings tab for every Type, never a
    new tab or a new screen
  And a real Job's own Settings shows ONLY Prompt and Guardrails -- no Vault
    Scope, no Working Mode, no Schedule, no Skills grant, matching its own
    genuinely minimal real capability set
```
<!-- AC-ID: REQ-SB-66-US-01-AC-06 -->

### Scenario 7: A Job becomes reachable via click-to-open-detail on the Agents Map, opening a Settings-only view

```gherkin
Given the Email Capture Pipeline's own real Jobs are rendered as tree nodes
    on the Agents Map (REQ-SB-65-US-01, Done)
When the operator clicks one of those Job nodes
Then a detail view opens showing that Job's own real name and its Settings
    (Prompt + Guardrails only) -- not the empty, unpopulated shell that
    opens today
  And no Chat tab, History tab, Working-Mode control, Schedule tab, or Visual
    tab is present for that Job -- REQ-SB-65-US-01's own "Jobs stay
    non-addressable in every OTHER respect" Constraint stays intact,
    narrowed only by this new Settings-view carve-out
```
<!-- AC-ID: REQ-SB-66-US-01-AC-07 -->

### Scenario 8: Prompt and Guardrails values are persisted in a new sibling store, keyed by id, covering Agents and Jobs uniformly

```gherkin
Given the new sibling `.second-brain/agent_prompts.json` store (composed
    alongside agent_registry.py, never inside it, mirroring
    agent_keywords.json's own established shape)
When a Prompt or Guardrails value is saved for any real Agent id or real Job
    id
Then it is written under that id's own key in agent_prompts.json
  And agent_registry.py's own file is not modified by this story
  And the identical storage/lookup mechanism serves both a real Agent id
    (e.g. "vault-filing-expert") and a real Job id (e.g. "classify") with no
    special-casing between the two
```
<!-- AC-ID: REQ-SB-66-US-01-AC-08 -->

### Scenario 9: Editing one Agent's/Job's own Prompt or Guardrails value never affects any other Agent's/Job's own stored value

```gherkin
Given two different real ids each already have their own distinct stored
    Prompt/Guardrails values
When the operator edits and saves a new value for only one of them
Then the other id's own stored value is read back completely unchanged
  And no cross-id bleed occurs in either the stored JSON or what any real
    call site reads at runtime
```
<!-- AC-ID: REQ-SB-66-US-01-AC-09 -->

### Scenario 10: A Job with no real LLM call site of its own omits the Prompt field entirely -- RESOLVED 2026-08-16, operator-confirmed

```gherkin
Given Thread-Match/Merge and Detect-Recurring-Pattern are two of the Email
    Capture Pipeline's six real Jobs, and neither makes any Compass call or
    has any LLM prompt of its own today (confirmed by direct reading of
    email_classification.py)
When the operator opens either Job's own Settings-only view
Then NO Prompt field is shown for that Job -- Decision 1's own blanket
    "Prompt shows for every Type including Jobs" rule is narrowed by this
    resolution: the Prompt field shows only for an Agent/Job with a real
    runtime call site to wire an override into
  And the Guardrails field is still shown (Guardrails is structure-only and
    applies uniformly regardless of whether a real LLM call exists)
  And no fabricated runtime call site is invented -- the field is honestly
    absent rather than present-but-inert (see ESCALATIONS.md ESC-039, Resolved)
```
<!-- AC-ID: REQ-SB-66-US-01-AC-10 -->

## Affected Screens

- `html-prototype/agents-map.html` — the Agent/Job Detail Panel's existing
  Settings-tab `kv-list` sections gain two new fields (Prompt, Guardrails) for
  every Type including Jobs, plus a new minimal Job-only Settings shell
  (no Chat/History/Schedule/Visual tabs). **None of this exists in the
  prototype today** — confirmed absent by direct grep (see `## Context`).
  **RESOLVED 2026-08-16, operator-directed:** "no more designer we will do
  it later build the needed ui we will fix it later" — the `/design` pass
  is deliberately skipped for this story. The coder builds the new
  Prompt/Guardrails fields and the Job-only Settings shell reusing the
  existing Settings `kv-list` visual language directly (the same
  "small, standard, vocabulary-reusing addition" precedent already used
  for several stories this session), not a fresh visual pass — a real,
  disclosed, non-blocking flag for later polish, not silently skipped.

## Dependencies

- **Blocked by:** `REQ-SB-65-US-01` (Pipeline Job Visualization, `Done`,
  `SPRINT-051`) — the real Job-tree data source
  (`email_capture_pipeline.get_job_tree()` /
  `GET /agents/{agent_id}/jobs`) this story's Job-Settings-view composes
  against for Job identity/existence; without it there is no real Job id
  list to key `agent_prompts.json` entries to, or to resolve a Job click
  against.
- **Related to:** `ADR-011` ("identity stays hardcoded, mutable state lives
  separately") and its own repeated precedent
  (`agent_keywords.json`/`agent_scopes.json`/`agent_working_modes.json`) —
  the exact storage-composition shape this story's `agent_prompts.json`
  mirrors a further time.
  `Implementation/UserStories/REQ-SB-29-US-01-agent-to-tag-folder-scoping.md`
  (Vault Scope) is the most recent sibling-store precedent of this kind.
- **Related to:** `ADR-015` (LangGraph + shared MCP server) — the
  conversation graph (`agent_orchestration/graph.py`/`state.py`) this
  story's Chat-prompt override (Scenario 2) reads from.
- **Related to:** `ADR-043` (Email Capture & Threading Pipeline) and
  `REQ-SB-63-US-01` (The Librarian, `Done`, `SPRINT-050`) — the real Job
  functions (`email_classification.py`) and the Vault Filing Expert call
  site (`vault_filing_expert.py`) this story wires overrides into.
- **Related to:** `REQ-SB-33-US-01` — the honest-uncertainty grounding
  instruction this story's Scenario 2 must not silently drop while making
  the surrounding text overridable.
- **External:** none.

## Constraints

- **`agent_registry.py` is never modified** — Prompt/Guardrails values live
  in a new sibling `.second-brain/agent_prompts.json`, composed alongside it
  (Decision 2; `ADR-011`'s "identity stays hardcoded, mutable state lives
  separately" rule).
- **Additive layering only** (Decision 3) — an unset override must never
  change any already-shipped Agent's/Job's own existing behavior. This is a
  hard regression bar (Scenario 4), not a convenience.
- **No separate screen per Type** (Decision 1) — Prompt and Guardrails land
  on the SAME existing Settings tab, conditionally shown per Type exactly
  like today's Domain-for-Expert/Purpose-for-Producer convention. Never a
  new tab, never a new top-level screen.
- **Jobs stay non-addressable in every OTHER respect** — `REQ-SB-65-US-01`'s
  own Constraints (no Chat, no History, no independent Working Mode, no
  Schedule, no Pending-Approval `agent_id`, no Skills grant) stay intact;
  this story's own click-to-open-detail carve-out is narrowly scoped to a
  Settings-only view, nothing more.
- **Guardrails carries zero enforcement behavior in this story** — a
  structural field only, per the requirement's own explicit "reserving the
  interface slot, not the mechanism" framing.
- **Scope stays bounded to the Email Capture Pipeline's own six real Jobs**
  (mirroring `REQ-SB-65-US-01`'s own scope-narrowing precedent) — no
  blanket "every Pipeline gets Job-level Settings" platform, no demo-taxonomy
  coverage.
- **No fabricated runtime wiring, and no inert fields** — where a real call
  site genuinely does not exist (Thread-Match/Merge, Detect-Recurring-Pattern),
  this story neither invents one nor shows a Prompt field with nothing to
  wire it to; the Prompt field itself is omitted for that Job (RESOLVED
  2026-08-16, operator-confirmed, Scenario 10). Guardrails still shows
  regardless, since it is structure-only and identity-agnostic.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

## Implementation Tasks

<!-- Locked by the decomposer, /plan-tasks step 2, 2026-08-16 — supersedes the
architect-pass provisional table. Task sizing note: 7 tasks (not the story's
own provisional 6) — the provisional single "frontend Settings fields" line
and single "Job-Settings endpoint" line each split into a backend-extension
task + a frontend-consumption task, mirroring this codebase's own established
"backend field/endpoint, then a separate frontend task consumes it"
precedent (REQ-SB-29-US-01-T03/T05, REQ-SB-65-US-01-T01/T02) — not
fragmentation, the same facet split this project already uses every time a
backend surface and its own UI consumption are each independently
verifiable. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-66-US-01-T01 | backend | New `agent_prompts.json` sibling store — get/set-by-id for Prompt + Guardrails, additive (unset → `None`/`""`), mirroring `agent_keywords.py`/`working_mode_registry.py`'s own shape | `app/business/agent_prompts.py` (new), `app/data_access/vault_writer.py` | `Implementation/Tasks/REQ-SB-66-US-01-T01-agent-prompts-sibling-store.md` |
| REQ-SB-66-US-01-T02 | backend | Wire the override into compass_client.py's four prompt functions' owning call sites (classify Job, todo-capture Agent, route_to_project Job, summarize_attachment Job) | `app/data_access/compass_client.py`, `app/business/email_classification.py`, `app/business/todo_classification.py` | `Implementation/Tasks/REQ-SB-66-US-01-T02-compass-client-prompt-override-wiring.md` |
| REQ-SB-66-US-01-T03 | backend | Wire the override into `state.py`'s per-turn Chat system message (every real Agent) and `vault_filing_methodology.build_placement_prompt` (vault-filing-expert) | `app/business/agent_orchestration/state.py`, `app/business/agent_orchestration/graph.py`, `app/business/vault_filing_methodology.py`, `app/business/vault_filing_expert.py` | `Implementation/Tasks/REQ-SB-66-US-01-T03-chat-and-vault-filing-prompt-override-wiring.md` |
| REQ-SB-66-US-01-T04 | backend | Extend `GET`/`PATCH /agents/{agent_id}` with Prompt + Guardrails fields for every real Agent | `app/api/agents_router.py` | `Implementation/Tasks/REQ-SB-66-US-01-T04-agents-router-prompt-guardrails-fields.md` |
| REQ-SB-66-US-01-T05 | frontend | Settings-tab Prompt + Guardrails `kv-list` rows for every real Agent Type | `src/frontend/src/features/agents-map/AgentDetailPanel.tsx`, `agentsApiClient.ts` | `Implementation/Tasks/REQ-SB-66-US-01-T05-agent-detail-panel-prompt-guardrails-rows.md` |
| REQ-SB-66-US-01-T06 | backend | New `GET`/`PATCH /agents/{agent_id}/jobs/{job_id}/settings` pair (`ADR-044`) | `app/api/agents_router.py` | `Implementation/Tasks/REQ-SB-66-US-01-T06-job-settings-endpoint.md` |
| REQ-SB-66-US-01-T07 | frontend | New standalone Job-Settings-only component + `AgentsMapPage.tsx` conditional-mount wiring (`ADR-044`) | `src/frontend/src/features/agents-map/` (new component), `src/frontend/src/pages/AgentsMapPage.tsx`, `agentsApiClient.ts` | `Implementation/Tasks/REQ-SB-66-US-01-T07-job-settings-frontend-shell.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) — n/a, test tooling still pending project-wide
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **`classify_recent_emails`'s own separate call to `compass_client.
  classify_email`** (the still-live, manual `/poc/classify-emails` path) —
  explicitly not wired to any Prompt override in this story; only the real
  production `classify` Job's own direct call is wired (disclosed scoping
  call, see `## Context`).
- **`skill_tools.py`'s shared, cross-agent `summarize_file` MCP skill** —
  explicitly not wired to any Prompt override in this story; it has no
  single owning identity (no `agent_id` argument reaches that call site at
  all). Only the Summarize-Attachment Job's own direct call to
  `compass_client.summarize_content` is wired (disclosed scoping call, see
  `## Context`).
- **Defining what Guardrails means or enforcing anything with it** —
  explicitly out of scope, per the requirement's own "structure only, not
  content-defined" framing. This story adds the field and persists it; it
  decides nothing about behavior.
- **The existing Overview-tab `GUARDRAILS_STATEMENT` row** (`REQ-SB-33-US-01`)
  — left byte-for-byte unchanged; this story's new Guardrails field lives in
  Settings, a different location and mechanism entirely.
- **Extending Prompt/Guardrails Settings to the demo taxonomy's sample
  agents/pipelines/Jobs, or to Meeting Capture/To-Do Capture's own
  (non-Pipeline-DAG) capture steps** — out of scope; only real Agents plus
  the Email Capture Pipeline's own six real Jobs are addressed, mirroring
  `REQ-SB-65-US-01`'s own scope-narrowing precedent.
- **A Job gaining Chat, History, independent Working Mode, Schedule, or a
  Pending-Approval `agent_id` of its own** — still explicitly excluded;
  `REQ-SB-65-US-01`'s own Constraints stay intact except for the narrow
  Settings-view click-through carve-out this story adds.
- **Resolving the "Job with no real LLM call site" gap** (Thread-Match/
  Merge, Detect-Recurring-Pattern) — explicitly left open, not guessed;
  tracked as `ESCALATIONS.md` → `ESC-039`, `Open`.
- **The exact Job-Settings-detail-view backend data-source/endpoint shape**
  — left to the architect at `/plan-tasks` (see `## Notes`); not designed
  here.

## Notes

**Open architecture question — genuinely open, NOT resolved by this pass
(one of the reasons for `gate: flagged`):**

`AgentDetail.type` (`agentsApiClient.ts`) today is exactly
`'worker' | 'producer' | 'expert'` — no `'job'` variant — and
`agent_registry.get_agent(job_id)` returns `None` for every real Job id
(Jobs have no registry entry, per `ADR-043` point 6, unchanged by this
story). Resolving a Job click into a real, populated Settings-only view
(Scenario 7) therefore needs a genuine design decision, structurally similar
to `REQ-SB-65-US-01`'s own Option A/B data-source choice. At least two shapes
look real and buildable, neither picked here:

- **Option A — a new, narrow endpoint** (e.g. `GET /jobs/{job_id}/settings`)
  returning only `{id, name, prompt, guardrails}`, paired with a frontend
  branch that renders a genuinely separate, minimal Settings-only shell for
  a Job id, bypassing `AgentDetailPanel`'s existing tab machinery entirely
  rather than trying to make it understand a non-Agent id.
- **Option B — widen the existing Agent-detail resolution** (without
  writing anything INTO `agent_registry.py` itself) to recognize a Job id via
  `email_capture_pipeline.get_job_tree()`, returning an `AgentDetail`-
  compatible shape with only Prompt/Guardrails meaningfully populated (every
  other field either omitted or a Job-appropriate constant), letting
  `AgentDetailPanel.tsx`'s existing tab-filtering logic hide Chat/History/
  Schedule/Visual for a Job-flagged detail the same way it already varies
  the tab set for `type === 'expert'` today.

Both are real, honest, non-fabricating options. Left for the architect to
confirm at `/plan-tasks`, exactly per `REQ-SB-65-US-01`'s own precedent for
this class of open question.

**RESOLVED 2026-08-16, `/plan-tasks` architect pass — Option A, with a new
ADR (`ADR-044`), not the "no new ADR" outcome `REQ-SB-65-US-01`'s own
precedent produced:**

- **Data source/endpoint shape: Option A.** New `GET`/`PATCH
  /agents/{agent_id}/jobs/{job_id}/settings` in `agents_router.py`
  (`agent_id` validates/scopes against `email_capture_pipeline.
  get_job_tree()`, never the storage key — `agent_prompts.json` is keyed
  by `job_id` alone). `GET` response: `{id, name, prompt: str | None,
  guardrails: str}` — `prompt` is the key OMITTED for `thread_match_merge`/
  `detect_recurring_pattern` (Scenario 10, `ESC-039` Resolved), a small,
  disclosed, hand-maintained 2-item exclusion set. `PATCH` body:
  `{prompt?: str, guardrails?: str}`. Frontend: a new, small, standalone
  Settings-only component, mounted by `AgentsMapPage.tsx` in place of
  `AgentDetailPanel` whenever `selectedAgentId` is a known Job id (reusing
  the SAME already-fetched `fetchAgentJobs(EMAIL_CAPTURE_PIPELINE_AGENT_ID)`
  list `pipelineJobTreeAdapter.ts` already consumes — no new fetch, no
  change to `AgentDetailPanel.tsx` itself for this piece).
- **Option B rejected**, for two confirmed reasons (the second one NEW,
  found by direct reading this pass, correcting this Note's own earlier
  framing): (1) it would blur the Agent/Job tier boundary across every
  `AgentDetail`-typed consumer, the same reasoning `REQ-SB-65-US-01`'s own
  Option B rejection already recorded for the Job Tree question; (2)
  `AgentDetailPanel.tsx`'s real, current `TABS` constant is FIXED for
  every real Agent Type — its only existing per-Type variance is ADDITIVE
  (`'gaps'` appended only for `type === 'expert'`). There is no existing
  tab-REMOVAL mechanism to reuse for a Job's own "Settings only" bar —
  confirmed by direct reading of the real file. This Note's own earlier
  "the same way it already varies tabs for `type === 'expert'` today"
  framing does not hold up against the real code; disclosed as a
  correction, not silently carried forward.
- **New ADR, `ADR-044`** (`Implementation/Architecture/ADR.md`) —
  `gate: flagged`, trigger-3. Unlike `REQ-SB-65-US-01`'s own structurally
  similar Option A/B choice (pure read, zero addressability change, "no
  new ADR"), this decision makes a Job clickable AND its own Settings
  editable/persisted for the first time — a genuine, material narrowing
  of `ADR-041`'s own deferred "whether/how a Job earns its own surface"
  Consequence and `ADR-043` point 6 ("Jobs stay non-addressable in every
  respect"), not an implementation-latitude composition within either
  ADR's already-settled boundaries. `ADR-044` narrows `ADR-043` point 6 to
  one explicit, bounded exception (Settings only — Prompt where a real
  call site exists, Guardrails always); every other facet (Chat, History,
  independent Working Mode, Schedule, Pending-Approval `agent_id`, Skills
  grant) stays exactly as `ADR-043` point 6 already established.
- **Architecture scope this story's coder is bounded by:**
  `Implementation/Architecture/architecture.md` → "Universal Prompt
  Override + Guardrails Placeholder — Agents and Pipeline Jobs (REQ-SB-66,
  see ADR-044)" (new section, covers the whole Prompt-override layer, the
  Guardrails field, the Settings-tab extension for real Agents, and the
  Job-Settings endpoint/frontend shape) plus, for context only (read, not
  modified by this story), "Pipeline Job Tree Visualization" (the real
  Job-id source, `email_capture_pipeline.get_job_tree()`/
  `GET /agents/{agent_id}/jobs`, `REQ-SB-65`).
- **Additive Prompt-override storage mechanism itself needs no separate
  new ADR** — it's a further, mechanical application of `ADR-011` point
  2/`ADR-030`'s already-`Accepted` "identity stays hardcoded, mutable
  state lives separately" pattern (`agent_keywords.json`'s own shape,
  once again). Only the Job-Settings-ADDRESSABILITY question needed
  `ADR-044`.

**Prototype parity:**

- **`/design` explicitly skipped, operator-directed 2026-08-16** — "no more
  designer we will do it later build the needed ui we will fix it later."
  None of the three items below get a fresh prototype pass; the coder
  builds them directly against the real app, reusing the existing Settings
  `kv-list` visual language verbatim, and revisits visual polish later if
  needed.
- The new Settings-tab Prompt field, for every Type including Jobs. Zero
  coverage anywhere in `html-prototype/agents-map.html` today (confirmed by
  direct grep) — built directly, not designed first.
- The new Settings-tab Guardrails field, for every Type including Jobs.
  Same zero-coverage finding — built directly, not designed first.
- The new Job-only minimal Settings shell (a detail view with no
  Chat/History/Schedule/Visual tabs, reachable by clicking a Job node). No
  such shell, or any Job-click-affordance at all, exists anywhere in the
  prototype today — built directly, not designed first.
- **Specced** — every OTHER existing Settings-tab kv-row (Section, Provider,
  Working mode, Background Agent, Keywords, Vault scope) and the existing
  per-Type tab set for real Agents — already covered by prior stories'
  approved prototype work; unaffected by this story, reused as-is for the
  fields that already exist.
- **Superseded** — none; this story adds new fields/a new view, it does not
  invalidate any existing approved prototype region.

**No other trigger fired beyond the four named in `gate_reason`:**
`REQ-SB-66` carries no `<!-- Draft -->` marker in the PRD (its own text
states "this requirement is real"); the story is not oversized purely by
file count — every touched call site is a facet of the SAME single
mechanism (an additive Prompt-override layer + a structure-only Guardrails
field + the per-Type Settings extension + the narrow Job-Settings-view
carve-out), mirroring `REQ-SB-65-US-01`'s own "kept as one story since both
are facets of the same... mechanism" precedent; no contradictory PRD
inputs beyond the newly-found Thread-Match/Merge/Detect-Recurring-Pattern
gap, already logged as `ESC-039` rather than silently resolved.

**What to do next — UPDATED 2026-08-16, architect pass:** `ESC-039` is
Resolved, `/design` is explicitly skipped (operator-directed), and the
Job-Settings-detail-view data-source shape is now RESOLVED (Option A,
`ADR-044`, above). Nothing remains open before the decomposer's own
`/plan-tasks` step 2 — `gate: flagged` carries forward on `ADR-044`
(trigger-3) plus the still-standing trigger-1 (the `classify_*`
call-site scoping assumption, unresolved-but-disclosed) — the decomposer
runs next regardless, per this pipeline's own "flag, don't halt" rule for
an ADR-change trigger. A `REVIEW-QUEUE.md` pointer was written for
`ADR-044`.

**Decomposer pass, `/plan-tasks` step 2, 2026-08-16 — AC locking + task
breakdown complete, story `Draft → Ready`:**

- All 10 untagged Gherkin scenarios locked as `REQ-SB-66-US-01-AC-01`
  through `AC-10` (sequential, one per Scenario, in order) — wording left
  essentially as the analyst/architect passes already tightened it; no
  further rewording was needed for buildability.
- **7 tasks written** (`T01`-`T07`), one more than the story's own
  provisional 6-line table — the provisional single "Settings-tab fields"
  line and single "Job-Settings endpoint" line each split into a
  backend-extension task + a separate frontend-consumption task, mirroring
  this codebase's own established "backend field/endpoint task, then a
  separate frontend task consumes it" precedent (`REQ-SB-29-US-01-T03`
  extends `GET`/`PATCH /agents/{agent_id}` with `scope`, `T05` is the
  separate `AgentDetailPanel.tsx` row that consumes it;
  `REQ-SB-65-US-01-T01` is the backend Job-tree endpoint, `T02` is the
  separate frontend splice) — not fragmentation, the same facet split this
  project already uses whenever a backend surface and its own UI
  consumption are each independently verifiable. Every OTHER grouping
  stayed as the story's own provisional table proposed it (`T01` store,
  `T02` compass_client wiring, `T03` Chat/Vault-Filing-Expert wiring).
- **AC → task mapping:** `AC-01`/`AC-04` (compass_client four functions +
  default-fallback for those four) → `T02`; `AC-02`/`AC-03`/`AC-04` (Chat
  system message + Vault Filing Expert placement prompt + their own
  default-fallback) → `T03`; `AC-08`/`AC-09` (storage shape, no cross-id
  bleed) → `T01`, verified directly at the store level (mirrors this
  project's own "test the mechanism where it's mechanically true" pattern,
  not duplicated at every consuming endpoint); `AC-05`/`AC-06` (Guardrails
  presence/persistence, per-Type Settings-tab shape) → `T05` (real Agents)
  AND `T07` (Jobs) — both genuinely needed, since the Job case is a wholly
  separate frontend surface; `AC-07` (Job click-to-open-detail) → `T07`;
  `AC-10` (Prompt field honestly absent for the 2 no-real-call-site Jobs)
  → `T07`, with a non-AC-tagged smoke check for the same omission at the
  API layer in `T06` (the user-observable outcome itself is the rendered
  Settings view, per this codebase's own established "user-observable ACs
  verify in the frontend task; the backend task gets non-AC smoke checks"
  rule — `REQ-SB-29-US-01-T03`'s own Tests-section precedent, cited there
  by name). `T04`/`T06` (the two backend Settings-surface extensions)
  therefore carry no AC tags of their own, by the same established rule —
  every locked AC still has at least one tagged step overall.
- **`depends_on` (acyclic, confirmed):** `T02`→`[T01]`; `T03`→`[T01]`;
  `T04`→`[T01]`; `T05`→`[T04]`; `T06`→`[T01, REQ-SB-65-US-01-T01]`;
  `T07`→`[T06, REQ-SB-65-US-01-T02]`. The two cross-story edges are real,
  not decorative — `T06`'s endpoint validates a `job_id` against
  `email_capture_pipeline.get_job_tree()` (`REQ-SB-65-US-01-T01`'s own
  function), and `T07`'s frontend shell reuses the SAME already-fetched
  `fetchAgentJobs(...)` list `REQ-SB-65-US-01-T02`'s own
  `pipelineJobTreeAdapter.ts` already consumes (per `ADR-044` Decision 3)
  — both targets are already `Done`, so neither edge blocks the build loop
  today; it documents a real reliance, mirroring `REQ-SB-63-US-01-T02`'s
  own cross-story `depends_on` precedent onto `REQ-SB-55-US-01`'s
  already-`Done` tasks.

**Coder pass, `T07`, 2026-08-17 — final task built, story `Ready → Done`:**

- `T07` (`JobSettingsPanel.tsx` + `AgentsMapPage.tsx` conditional-mount
  wiring, `ADR-044` Decision 3) built as specced, no deviations. All 7 tasks
  (`T01`-`T07`) now `Done`. `AC-05`/`AC-06`/`AC-07`/`AC-10` verified in
  `T07`'s real rendered Job-Settings UI (per this story's own AC→task
  mapping) via a combination of TypeScript/lint clean-checks, direct JSX
  reading, and real HTTP round-trips (both an in-process `TestClient` and
  the live `127.0.0.1:8001` dev server, both returning identical results)
  against `T06`'s real endpoint — full detail in `T07`'s own
  `## Implementation Log`.
- **Disclosed, not blocking:** no browser/screenshot tool was available to
  this coder's session, so the actual live-browser click-through (the
  literal `AC-07` manual step: click a Job dot, look at the panel) was not
  performed by the coder — the operator's own stated plan is to do this
  personally, exactly as for `T05`. Every AC is otherwise proven via the
  exact real backend contract plus direct component-code reading, not
  guessed.
- Every locked AC (`AC-01`-`AC-10`) now has a `Done`-task-verified outcome;
  no AC remains unverified or blocked. `status: Ready → Done`. `gate` stays
  `flagged` — the story-level `REVIEW-QUEUE.md` entry for `ADR-044` remains
  open for the operator's own architecture-decision + live-browser review;
  it does not block the story from being marked `Done` (a flagged gate is a
  standing human-review breadcrumb, not a completion blocker, per this
  pipeline's own "flag rather than guess, don't halt" rule).

- **Task-level gates, per this pipeline's own "carry the flag to every task
  that actually implements the flagged decision" rule
  (`REQ-SB-65-US-01-T01`/`T02` precedent):** `T02` is `gate: flagged`,
  trigger-1 (the still-standing `compass_client.py` call-site-scoping
  material assumption — the "four functions, not two" reading, plus the
  two disclosed, deliberately-unwired dual-ownership calls,
  `classify_recent_emails`/`skill_tools.summarize_file`, both landing
  inside this exact task's own Files to Modify). `T06`/`T07` are
  `gate: flagged`, trigger-3 (`ADR-044` — both tasks directly implement
  that ADR's Decision). `T01`/`T03`/`T04`/`T05` are `gate: clear` — `T03`'s
  own two owning identities are unambiguous by direct reading (no
  assumption); `T01`/`T04`/`T05` are mechanical applications of an
  already-`Accepted`, several-times-repeated pattern (`ADR-011`
  point 2/`ADR-030`), needing no new ADR per `architecture.md`'s own
  Consequences note.
- **Status:** every locked AC has ≥1 tagged verification step,
  `depends_on` is acyclic — story advanced `Draft → Ready`, every task
  written at `status: Ready` (not `Draft`) to match, per this pipeline's
  own "task status moves in lockstep with the story" rule. `gate` stays
  `flagged` (trigger-1 + trigger-3, both non-blocking breadcrumbs) — this
  story is eligible for `/plan-sprints` once the human review pass runs
  alongside it, exactly as `REQ-SB-54-US-01`/`REQ-SB-55-US-01`/
  `REQ-SB-63-US-01` were all left this session.

---

**Product-owner pass (`/plan-sprints`, 2026-08-16) — grouped into
`SPRINT-052`:** single-story sprint, the full 7-task dependency tree
(`T01` root → `T02`/`T03`/`T04` fan-out → `T05`; `T06` → `T07`, the latter
two also carrying real, already-satisfied cross-story `depends_on` edges
onto `REQ-SB-65-US-01-T01`/`T02`, both `Done` in `SPRINT-051` — no
`depends_on_sprints` ordering edge needed since the referenced sprint is
already `Done`), no sibling `Ready`, `sprint: ""` story existed to batch
alongside it (`REQ-SB-64-US-01` checked and confirmed `Draft`, excluded).
`gate: clear` for this partition decision itself — advances `Draft → Ready`
sprint status; the story's own trigger-1/trigger-3 flags stay as standing
breadcrumbs, unchanged. Full reasoning:
`Implementation/Sprints/SPRINT-052-real-editable-prompt-and-guardrails-placeholder.md`.
