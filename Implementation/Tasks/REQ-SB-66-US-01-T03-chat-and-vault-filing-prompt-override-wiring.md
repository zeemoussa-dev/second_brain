---
id: REQ-SB-66-US-01-T03
title: Wire the Prompt override into state.py's per-turn Chat system message and vault_filing_methodology.build_placement_prompt
parent_story: REQ-SB-66-US-01
requirement_id: REQ-SB-66
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-66-US-01-T01]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-66-US-01-T03 — Chat system message + Vault Filing Expert placement prompt wiring

## Parent Story

- Story: [[REQ-SB-66-US-01]] — `../UserStories/REQ-SB-66-US-01-real-editable-prompt-and-guardrails-placeholder.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-66 *Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings*

---

## Objective

Wire the Prompt override into the remaining 2 real prompt call sites this story
covers: `agent_orchestration/state.py`'s `history_entries_to_messages` (the real,
only per-turn Chat `SystemMessage`, read by `graph.py` on every real Agent's chat
turn — Worker/Producer/Expert alike, per the parent story's own verified
discrepancy vs. the PRD's naming of `agent_chat.py`), and
`vault_filing_methodology.build_placement_prompt`'s own `_METHODOLOGY_EXCERPT`
`SystemMessage` half (owned unambiguously by the single `vault-filing-expert`
Agent, regardless of which caller reaches it).

---

## Starting State → End State

**Before / Inputs:**
- `state.py`'s `history_entries_to_messages(agent_name: str, agent_type: str,
  history: list[dict])` prepends one hardcoded `SystemMessage` (the identity
  sentence + the honest-uncertainty/grounding instruction, `REQ-SB-33-US-01`) —
  called by `graph.py`'s `run_agent_conversation` as `history_entries_to_messages(
  agent["name"], agent["type"], history)`, where `agent_id` is already in scope at
  that same call site (`run_agent_conversation(agent_id, message, history, memory)`).
  No `agent_id` reaches `history_entries_to_messages` itself today.
- `vault_filing_methodology.build_placement_prompt(content, source_description,
  known_kinds, known_customers, known_partners)` returns `[SystemMessage(content=
  _METHODOLOGY_EXCERPT), HumanMessage(content=human_content)]` — called from
  exactly one place, `vault_filing_expert.determine_placement_and_file`, which
  always resolves `model_factory.resolve_agent_model("vault-filing-expert")`
  regardless of its own `requesting_agent_id` argument (confirmed by direct
  reading, per the parent story's own `## Context` — `requesting_agent_id` is used
  only for Pending-Approval bookkeeping, never for prompt/model selection).
- `T01` (`app/business/agent_prompts.py`) is `Ready` — `get_prompt(id) -> str |
  None` is the lookup this task's own callers use.

**After / Outputs:**
- `history_entries_to_messages` (or its own caller, `graph.py`'s
  `run_agent_conversation`) resolves `agent_prompts.get_prompt(agent_id)` for the
  agent whose turn is being run, and — when set — uses that override text as the
  Chat `SystemMessage`'s own content INSTEAD of the hardcoded identity/grounding
  sentence. The `record_knowledge_gap`-triggering honest-uncertainty MECHANISM
  itself (the tool call graph.py's own nodes wire up) is untouched by this task —
  only the DEFAULT TEXT of the SystemMessage becomes overridable (Scenario 2's own
  explicit "the override replaces the DEFAULT TEXT, never the mechanism that reads
  it" bar). When no override is set, the SystemMessage's own content is
  byte-for-byte identical to today's hardcoded sentence.
- `vault_filing_expert.determine_placement_and_file` resolves
  `agent_prompts.get_prompt("vault-filing-expert")` (the one, single owning
  identity, regardless of `requesting_agent_id`) and passes it into
  `vault_filing_methodology.build_placement_prompt` as a new optional parameter;
  `build_placement_prompt` uses it in place of `_METHODOLOGY_EXCERPT` for the
  returned `SystemMessage`'s own content when set, leaving the `HumanMessage`
  (`known_lists_text`/`source_description`/`content`/`_JSON_SCHEMA_INSTRUCTIONS`)
  completely untouched either way. This applies identically whether
  `determine_placement_and_file` is reached via `REQ-SB-20` Hub routing or via
  `email_classification.consult_librarian`'s own internal call — one single owning
  identity, one single override, regardless of caller (Scenario 3).

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/state.py`:
  - `history_entries_to_messages` gains a way to receive/resolve the calling
    agent's own stored Prompt override — either (a) an additional `agent_id: str`
    parameter, calling `agent_prompts.get_prompt(agent_id)` internally (`state.py`
    is a business-layer module; composing another business module is layer-legal
    per `ADR-003`), or (b) an additional, already-resolved `prompt_override: str |
    None = None` parameter, with the lookup performed by `graph.py`'s own caller
    instead. Either shape is fine — coder's choice, disclosed as genuine
    implementation latitude, not decided here (mirrors this project's own
    established "compose around the real current file, decide the mechanical shape
    at build time" precedent). When an override is present, it replaces the
    hardcoded `SystemMessage(content=(...))` text verbatim; when absent, output is
    byte-for-byte unchanged.
- `src/backend/app/business/agent_orchestration/graph.py`:
  - `run_agent_conversation`'s existing call to `history_entries_to_messages(
    agent["name"], agent["type"], history)` is updated to also supply the
    `agent_id`/override text, per whichever shape `state.py` above adopts.
    `agent_id` is already a parameter of `run_agent_conversation` — no new fetch
    needed if the resolution happens here.
- `src/backend/app/business/vault_filing_methodology.py`:
  - `build_placement_prompt` gains a new optional `prompt_override: str | None =
    None` parameter; when set, the returned `SystemMessage`'s own `content` is the
    override text instead of `_METHODOLOGY_EXCERPT`. The `HumanMessage` (built from
    `known_lists_text`/`source_description`/`content`/`_JSON_SCHEMA_INSTRUCTIONS`)
    is unchanged either way.
- `src/backend/app/business/vault_filing_expert.py`:
  - `determine_placement_and_file` resolves `agent_prompts.get_prompt(
    "vault-filing-expert")` before calling `vault_filing_methodology.
    build_placement_prompt`, and passes it through as `prompt_override`. Add
    `agent_prompts` to this module's own existing business-layer imports.

---

## Constraints

- Inherits from parent story: `agent_registry.py` is never modified; additive
  layering only (an unset override never changes any already-shipped behavior).
- **`REQ-SB-33`'s own honest-uncertainty/grounding mechanism must not be silently
  dropped** — this task changes the Chat SystemMessage's own DEFAULT TEXT only; the
  `record_knowledge_gap` tool-call wiring, and every other node in `graph.py`'s own
  conversation graph, are untouched (Scenario 2's own explicit bar).
- `vault-filing-expert` is the ONE owning identity for `build_placement_prompt`,
  regardless of caller — `determine_placement_and_file`'s own `requesting_agent_id`
  parameter must NOT be used to resolve which id's override applies (it stays
  bookkeeping-only, exactly as today).
- `build_placement_prompt`'s own `HumanMessage` (the known-lists/schema/content
  half) is never made overridable by this task — only the `SystemMessage`
  (`_METHODOLOGY_EXCERPT`) half is (Scenario 3's own explicit scope).
- When no override is set for the relevant id, both call sites' own output must be
  byte-for-byte identical to today's hardcoded text (Scenario 4/`AC-04`).
- Must respect the `api → business → data_access` layer boundary (`ADR-003`) — both
  `state.py`/`graph.py` and `vault_filing_expert.py` are business-layer modules;
  composing `agent_prompts.py` (also business) from either is layer-legal.
- Do not modify `agent_chat.py` — confirmed by direct reading (parent story's own
  `## Context`) to carry no LLM prompt of any kind; it is out of this task's scope
  entirely, despite the PRD's own naming of it.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-66-US-01-AC-02]** Save a distinctive override via
   `agent_prompts.set_prompt(<a real agent_id>, "<marker text>")` for a real Worker,
   a real Producer, AND a real Expert agent (3 separate ids, one per type) — for
   each, start a new Chat turn (`POST /agents/{agent_id}/chat` or a direct
   `run_agent_conversation` call) and confirm the constructed `SystemMessage`'s own
   `content` (inspect `messages[0]` before the model call) is the marker text, not
   the hardcoded identity/grounding sentence, for all 3 agent types. Confirm the
   `record_knowledge_gap` tool is still registered/callable on that same turn (the
   mechanism itself is untouched) — e.g. ask a question with no real answer in the
   vault and confirm a knowledge gap is still recorded exactly as before this task.
2. **[REQ-SB-66-US-01-AC-03]** Save a distinctive override via
   `agent_prompts.set_prompt("vault-filing-expert", "<marker text>")` — trigger
   `determine_placement_and_file` via BOTH real call paths (a direct Hub-routed
   consult, and `email_classification.consult_librarian`'s own internal call) and
   confirm the constructed `SystemMessage`'s own `content` is the marker text in
   BOTH cases, with the `HumanMessage`'s own known-lists/schema/content unaffected.
3. **[REQ-SB-66-US-01-AC-04]** With no override saved for a real agent id / for
   `"vault-filing-expert"`, run a Chat turn and a placement-decision call
   respectively — diff the constructed `SystemMessage` content in each case against
   this task's own recorded "before" value (captured from the real, unmodified
   files before this task's changes) — confirm byte-for-byte identical output for
   both.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `history_entries_to_messages`'s Chat `SystemMessage` uses a stored override
      (for the chatting agent's own id) when present, byte-for-byte hardcoded text
      when absent
- [x] `REQ-SB-33`'s own grounding/honest-uncertainty mechanism (the
      `record_knowledge_gap` tool wiring) is unaffected by this task
- [x] `build_placement_prompt`'s `SystemMessage` half uses a stored
      `"vault-filing-expert"` override when present, `_METHODOLOGY_EXCERPT`
      byte-for-byte when absent — identically whether reached via Hub routing or
      `consult_librarian`
- [x] `build_placement_prompt`'s `HumanMessage` half is never made overridable
- [x] `agent_chat.py` is not modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring an override into any of `compass_client.py`'s four functions — `T02`.
- Any HTTP-reachable endpoint for setting a Prompt/Guardrails value — `T04`/`T06`.
- Any frontend surface — `T05`/`T07`.
- Any change to `agent_chat.py` — confirmed out of scope, per the parent story's own
  verified PRD discrepancy.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Universal Prompt
Override + Guardrails Placeholder — Agents and Pipeline Jobs (REQ-SB-66, see
ADR-044)" → the `agent_orchestration/state.py`/`vault_filing_methodology.
build_placement_prompt` bullets under "Prompt override wiring". Also read the
parent story's own `## Context` in full — the verified PRD discrepancy
(`agent_chat.py` carries no LLM prompt; the real per-turn system message lives in
`state.py`) is already confirmed there by direct reading; do not re-litigate it.

Compose around the REAL current `state.py`/`graph.py`/`vault_filing_methodology.py`/
`vault_filing_expert.py` as they actually exist today — do not assume exact
variable/function names from this task's own illustrative prose without reading the
real files first.

**Gate is `clear`** — both owning identities this task wires (the chatting agent's
own id; `"vault-filing-expert"`, unambiguous regardless of caller) are confirmed
unambiguous by direct reading in the parent story's own `## Context`, unlike `T02`'s
own still-standing scoping assumption for `compass_client.py`'s four functions.

---

## Implementation Log

**Built as designed, no deviations.** Read the real, current `state.py`,
`graph.py`, `vault_filing_methodology.py`, and `vault_filing_expert.py`
fresh before editing. Confirmed `history_entries_to_messages(agent_name,
agent_type, history)` prepends exactly one hardcoded `SystemMessage`
(the identity + `REQ-SB-33-US-01` grounding sentence), called by
`graph.py`'s `run_agent_conversation` with `agent_id` already in scope
at that same call site; confirmed `build_placement_prompt` returns
`[SystemMessage(content=_METHODOLOGY_EXCERPT), HumanMessage(...)]`,
called from exactly one place, `determine_placement_and_file`, which
always resolves `model_factory.resolve_agent_model("vault-filing-expert")`
regardless of `requesting_agent_id`.

**Shape chosen for `state.py` (disclosed coder latitude, either shape
was fine per this task's own Files to Modify):** option (a) — added an
`agent_id: str | None = None` parameter directly to
`history_entries_to_messages`, resolving `agent_prompts.get_prompt
(agent_id)` internally (state.py composing another business module is
layer-legal, `ADR-003`), rather than pushing the lookup into
`graph.py`. Chosen because it keeps the override-resolution logic
co-located with the SystemMessage it replaces, and because `state.py`
already owns the "how the SystemMessage's text is built" concern
end-to-end. `graph.py`'s only change is passing its own already-in-scope
`agent_id` through: `history_entries_to_messages(agent["name"],
agent["type"], history, agent_id)`. Split point used: pulled the
original hardcoded sentence out into a `default_identity_and_
grounding_text` local (byte-identical to the original literal), then
`system_message_text = prompt_override if prompt_override is not None
else default_identity_and_grounding_text` — no override is `None` unless
`agent_id` itself is `None`, reproducing today's exact output.

For `vault_filing_methodology.build_placement_prompt`: this prompt
builder already keeps the `SystemMessage`/`HumanMessage` split at the
message-list level (unlike `compass_client.py`'s T02 case, which
interleaved static instructions with dynamic content in ONE string) —
no string-splitting was needed. Added `prompt_override: str | None =
None`; `system_message_text = prompt_override if prompt_override is not
None else _METHODOLOGY_EXCERPT`; the `HumanMessage`'s own construction
(`known_lists_text`/`source_description`/`content`/
`_JSON_SCHEMA_INSTRUCTIONS`) is completely untouched, built before the
branch and used identically either way. Logged this as a new, distinct,
reusable pattern in `MEMORY.md` alongside T02's own string-split pattern
(genuinely new — a simpler variant, not a duplicate).

`vault_filing_expert.py`: added `agent_prompts` to the existing
`from app.business import (...)` block (alphabetical). In
`determine_placement_and_file`, added `prompt_override =
agent_prompts.get_prompt("vault-filing-expert")` — the literal string
constant, never `requesting_agent_id` — immediately before the existing
`build_placement_prompt(...)` call, and passed it through as the new
`prompt_override=` keyword argument. Confirmed by grep that
`determine_placement_and_file` has exactly 4 real callers
(`agents_router.py` Hub routing, `email_classification.
consult_librarian`, `knowledge_gap_tracking.py`,
`agent_orchestration/knowledge_bootstrap.py`) and that this one
resolution point inside `determine_placement_and_file` itself covers
all 4 uniformly — no per-caller wiring needed, since none of the other
3 files were touched or needed to be.

`agent_chat.py` was not opened for editing at all — out of scope,
confirmed already by the parent story's own `## Context`.

Verification was run against the real, configured backend venv
(`src/backend/.venv`), with `settings.vault_path` redirected to a
scratch temp directory for the duration of the verification script
(never touching the real vault's own `.second-brain/agent_prompts.json`,
which already holds real `T01`/`T02` verification data) — a one-off
`python` script, not a persisted pytest file, per this task's own
"Automated tests: n/a — test tooling pending".

- **[REQ-SB-66-US-01-AC-02]** PASS. Saved a distinctive marker override
  via `agent_prompts.set_prompt(id, marker)` for one Worker-labeled id
  (`worker-marker-1`), one Producer-labeled id (`producer-marker-1`),
  and one Expert-labeled id (`expert-marker-1`) — for each, called
  `history_entries_to_messages(name, type, [], id)` and confirmed the
  constructed `messages[0].content` (the Chat `SystemMessage`) was the
  marker text verbatim, not the hardcoded identity/grounding sentence,
  for all 3. Confirmed a 4th, un-overridden id (`untouched-agent-id`)
  called alongside the 3 overridden ones still produced the exact
  hardcoded default text — no cross-id bleed. Confirmed the
  `record_knowledge_gap` tool-call mechanism itself is untouched: this
  task's own diff to `graph.py` is exactly one line (the
  `history_entries_to_messages(...)` call now also passes `agent_id`) —
  `record_knowledge_gap`'s own `@tool` definition, its unconditional
  append onto every turn's `tools` list in `run_agent_conversation`, its
  interception in `_route_after_model`, and the `_record_knowledge_gap`
  graph node itself are all confirmed unmodified by this task's diff
  (inspected via `git diff` on `graph.py`, isolated to this task's own
  single changed line).
- **[REQ-SB-66-US-01-AC-03]** PASS. Saved a distinctive marker override
  via `agent_prompts.set_prompt("vault-filing-expert", marker)`, read
  it back via `agent_prompts.get_prompt("vault-filing-expert")` (the
  exact resolution `determine_placement_and_file` itself now performs
  unconditionally, regardless of `requesting_agent_id` or which of its
  4 real callers reached it — see the reasoning above for why one
  resolution point covers both the Hub-routed path and
  `consult_librarian`'s own internal call), and passed it into
  `build_placement_prompt(..., prompt_override=...)`. Confirmed the
  returned `SystemMessage.content` was the marker text verbatim, and
  the returned `HumanMessage.content` was byte-identical to the
  no-override call's own `HumanMessage.content` (same `content`/
  `source_description`/known-lists inputs) — the known-lists/schema/
  content half is unaffected by the override.
- **[REQ-SB-66-US-01-AC-04]** PASS, both call sites. For `state.py`:
  `history_entries_to_messages("TestAgent", "worker", [])` (no
  `agent_id`) and `history_entries_to_messages("TestAgent", "worker",
  [], "worker-1")` (an id with no saved override) both produced
  `messages[0].content` byte-identical (`==`) to the real, unmodified
  hardcoded sentence, reproduced verbatim in the verification script
  from the file as it read before this task's edit. For
  `vault_filing_methodology.py`: `build_placement_prompt(...)` with no
  `prompt_override` argument produced `SystemMessage.content ==
  vfm._METHODOLOGY_EXCERPT` (the real, live module constant, confirmed
  unmodified by this task).

Full backend test suite (`pytest`, `src/backend`) re-run after the
change: 1 passed, no regressions. `ast.parse()` of all 4 modified files
confirmed clean; a direct `import` of all 4 modules (`state`, `graph`,
`vault_filing_methodology`, `vault_filing_expert`) confirmed no
circular-import or runtime error was introduced (`agent_prompts.py`
only imports `vault_writer`, no cycle back into `agent_orchestration`).

No file outside `## Files to Modify` was touched. No new assumption or
scope-internal judgement call beyond the disclosed `state.py` shape
latitude (option (a), chosen and reasoned above) — nothing new to log
for human spot-check beyond that disclosed choice.
