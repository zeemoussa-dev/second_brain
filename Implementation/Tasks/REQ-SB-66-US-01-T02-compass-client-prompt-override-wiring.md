---
id: REQ-SB-66-US-01-T02
title: Wire the Prompt override into compass_client.py's four functions, at their own owning Job/Agent call sites
parent_story: REQ-SB-66-US-01
requirement_id: REQ-SB-66
type: backend
status: Done
gate: flagged
gate_reason: "trigger-1 (material assumption), carried from the parent story's own gate_reason: 'compass_client.py's various classify_* functions' is read expansively as all 4 of that file's hardcoded-prompt functions (classify_email, classify_task, guess_project_for_thread, summarize_content), not only the two literally named classify_*. This task's own Files to Modify also disclose 2 dual-ownership/second-caller scoping calls that are deliberately left UNWIRED (classify_recent_emails' own separate call to classify_email; skill_tools.summarize_file's own separate call to summarize_content) — neither has one unambiguous owning identity. See the parent story's own ## Context and ## Non-Goals. REVIEW-QUEUE.md carries the story-level pointer; this task's own flag is a breadcrumb, not a blocker."
phase: P1
depends_on: [REQ-SB-66-US-01-T01]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-66-US-01-T02 — compass_client.py Prompt override wiring

## Parent Story

- Story: [[REQ-SB-66-US-01]] — `../UserStories/REQ-SB-66-US-01-real-editable-prompt-and-guardrails-placeholder.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-66 *Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings*

---

## Objective

Give each of `compass_client.py`'s four hardcoded-prompt-building functions
(`classify_email`, `classify_task`, `guess_project_for_thread`,
`summarize_content`) an optional override, and wire that override in at each
function's own single, unambiguous owning call site: `classify_email` ↔ the
`classify` Job (`email_classification.classify_captured_email`); `classify_task` ↔
the `todo-capture` Agent (`todo_classification.classify_recent_todos`);
`guess_project_for_thread` ↔ the `route_to_project` Job
(`email_classification.route_to_project`); `summarize_content` ↔ the
`summarize_attachment` Job (`email_classification.summarize_attachment`).

---

## Starting State → End State

**Before / Inputs:**
- `compass_client.py`'s four functions each build ONE hardcoded prompt string
  (instructional text + the model's own JSON-response-schema ask, interleaved with
  the function's own dynamically-interpolated arguments — `subject`/`sender`/`body`,
  `known_customers`/`known_kinds` lists, `thread_summary`, `content`/
  `source_description`) and parse a JSON response expecting specific keys
  (`customer`/`kind`/`confidence`/`recurring_candidate`, `project`, `summary`).
- `T01` (`app/business/agent_prompts.py`) is `Ready` — `get_prompt(id) -> str | None`
  is the lookup this task's own business-layer callers use.
- `classify_captured_email` (`email_classification.py`), `classify_recent_todos`
  (`todo_classification.py`), `route_to_project`/`summarize_attachment`
  (`email_classification.py`) are each the ONE real, confirmed owning call site for
  their own compass_client function (see the parent story's own `## Context` for the
  full per-function ownership confirmation).
- 2 OTHER real, reachable calls into these same 4 functions exist and are
  DELIBERATELY left out of this task's own wiring (see `## Constraints`):
  `classify_recent_emails` (`email_classification.py`, its own separate,
  still-live `/poc/classify-emails` path) also calls `classify_email` directly;
  `skill_tools.summarize_file` also calls `summarize_content` directly, with no
  `agent_id` argument reaching that call site at all.

**After / Outputs:**
- Each of the 4 `compass_client.py` functions gains a new, optional
  `prompt_override: str | None = None` parameter (keyword-friendly, defaulting to
  `None`). When `None` (the default), each function's own prompt text is built
  byte-for-byte identically to today (Scenario 4/`AC-04` — the regression bar).
  When a non-`None` override is supplied, the override text is used in place of the
  function's own hardcoded static/instructional prompt content; the SAME real
  per-call dynamic data (subject/sender/body slices, known-customer/kind/project
  lists, thread summary, source content) the function already receives as its other
  arguments is still supplied to the model in some form — the exact split point
  (e.g. the override text followed by the same dynamic-content block this function
  already appends today, verbatim) is this task's own implementation choice; any
  shape is correct as long as (a) the override text is genuinely what's sent to the
  model in place of the hardcoded default whenever one is stored, and (b) the
  function's own real input data is not silently discarded.
- `classify_captured_email`, `classify_recent_todos`, `route_to_project`,
  `summarize_attachment` each look up their own owning id's stored override via
  `agent_prompts.get_prompt(owning_id)` (`"classify"`, `"todo-capture"`,
  `"route_to_project"`, `"summarize_attachment"` respectively) and pass it through
  as the new `prompt_override` argument to their own compass_client call.
- `classify_recent_emails` and `skill_tools.summarize_file`'s own calls into
  `classify_email`/`summarize_content` are UNCHANGED — they pass no
  `prompt_override` (or pass `None` explicitly), so their own behavior is
  byte-for-byte unaffected by this task.

---

## Files to Modify

- `src/backend/app/data_access/compass_client.py`:
  - `classify_email(..., prompt_override: str | None = None)`,
    `classify_task(..., prompt_override: str | None = None)`,
    `guess_project_for_thread(..., prompt_override: str | None = None)`,
    `summarize_content(..., prompt_override: str | None = None)` — each gains the
    new parameter and an `if prompt_override is not None:` branch that uses it in
    place of the function's own hardcoded static prompt text, per the "Starting
    State → End State" contract above. No other behavior in these 4 functions
    changes (the `httpx.post`/`CompassError`/JSON-parsing logic is untouched).
- `src/backend/app/business/email_classification.py`:
  - `classify_captured_email` — look up `agent_prompts.get_prompt("classify")`
    before calling `compass_client.classify_email`, pass it as `prompt_override`.
  - `route_to_project` — look up `agent_prompts.get_prompt("route_to_project")`
    before calling `compass_client.guess_project_for_thread`, pass it as
    `prompt_override`.
  - `summarize_attachment` — look up `agent_prompts.get_prompt("summarize_attachment")`
    before calling `compass_client.summarize_content`, pass it as `prompt_override`.
  - Add `agent_prompts` to the existing `from app.business import (...)` block
    (alphabetical, alongside `customer_hub_linking`/`meeting_classification`/etc.).
  - Do NOT change `classify_recent_emails`'s own call to `compass_client.
    classify_email` — leave it passing no `prompt_override` (disclosed scoping call,
    see `## Constraints`).
- `src/backend/app/business/todo_classification.py`:
  - `classify_recent_todos` — look up `agent_prompts.get_prompt("todo-capture")`
    before calling `compass_client.classify_task`, pass it as `prompt_override`.
    Add `agent_prompts` to the existing `from app.business import
    customer_hub_linking` import line.
- Do NOT modify `src/backend/app/business/skill_tools.py`'s `summarize_file` — its
  own call to `compass_client.summarize_content` stays exactly as it is today
  (disclosed scoping call, see `## Constraints`).

---

## Constraints

- Inherits from parent story: `agent_registry.py` is never modified; additive
  layering only (an unset override never changes any already-shipped behavior).
- Must respect the `api → business → data_access` layer boundary (`ADR-003`) —
  `compass_client.py` (data_access) never imports `agent_prompts.py` (business); the
  override lookup happens in the BUSINESS-layer callers
  (`email_classification.py`/`todo_classification.py`), which pass the already-
  resolved override text down into `compass_client.py` as a plain string parameter.
- **`classify_recent_emails`'s own separate call to `compass_client.classify_email`
  is explicitly NOT wired to any override** — the parent story's own `## Non-Goals`
  (the still-live, manual `/poc/classify-emails` path is a different call site from
  the real production `classify` Job).
- **`skill_tools.summarize_file`'s own separate call to `compass_client.
  summarize_content` is explicitly NOT wired to any override** — the parent story's
  own `## Non-Goals` (no single owning identity reaches that call site; it takes no
  `agent_id` argument at all).
- When `prompt_override` is `None` (the default, and the value every un-wired call
  site above always passes), each of the 4 `compass_client.py` functions must
  produce EXACTLY the same prompt text as before this task — byte-for-byte, not
  merely equivalent (Scenario 4/`AC-04`'s hard regression bar).
- The 4 functions' own JSON-response parsing/error-handling logic
  (`CompassError`, the `data["choices"][0]["message"]["content"]` shape) is
  untouched — this task only changes how the OUTGOING prompt text is assembled.
- No new dependency, no new HTTP client, no change to `settings.compass_model`/
  `settings.compass_base_url`/`settings.compass_api_key` usage.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-66-US-01-AC-01]** For each of the 4 owning call sites in turn
   (`classify_captured_email`/`"classify"`, `classify_recent_todos`/`"todo-capture"`,
   `route_to_project`/`"route_to_project"`, `summarize_attachment`/
   `"summarize_attachment"`): call `agent_prompts.set_prompt(owning_id, "<a
   distinctive marker string>")`, then invoke that owning function against real
   input data (or a direct call to the underlying `compass_client` function with
   the SAME `prompt_override` value it would resolve to) — confirm the outgoing
   prompt actually sent to Compass (inspect the constructed `payload["messages"]`
   content before the `httpx.post` call, e.g. via a debugger/print/mock) contains
   the marker string, not the function's own previously-hardcoded instructional
   text. Confirm a DIFFERENT owning id's own function (with no override saved) is
   unaffected — no other Agent's/Job's own prompt behavior changed as a result.
2. **[REQ-SB-66-US-01-AC-04]** With NO override saved for any of the 4 owning ids
   (a fresh/never-touched `agent_prompts.json`, or explicitly `agent_prompts.
   set_prompt(id, None)`-equivalent absence), call each of the 4 compass_client
   functions directly and diff the constructed prompt string against this task's
   own recorded "before" value (captured from the real, unmodified file before this
   task's changes) — confirm byte-for-byte identical output for all 4 functions.
3. Regression (not itself a locked AC): confirm `classify_recent_emails` and
   `skill_tools.summarize_file` are unmodified by this task (`git diff` shows no
   change to either function's own body) and that calling them still produces the
   same hardcoded-default prompt text as before, regardless of any override saved
   for `"classify"`/`"summarize_attachment"` — proving the 2 disclosed scoping
   calls are genuinely unaffected.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] All 4 `compass_client.py` functions gain an optional `prompt_override`
      parameter, defaulting to `None`, with byte-for-byte unchanged output when
      `None`
- [x] `classify_captured_email`/`classify_recent_todos`/`route_to_project`/
      `summarize_attachment` each resolve their own owning id's stored override via
      `agent_prompts.get_prompt` and pass it through
- [x] `classify_recent_emails` and `skill_tools.summarize_file` are unmodified —
      both disclosed scoping calls stay unwired
- [x] `api → business → data_access` layering respected — `compass_client.py` never
      imports `agent_prompts.py`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring an override into `state.py`'s Chat system message or
  `vault_filing_methodology.build_placement_prompt` — `T03`.
- Any HTTP-reachable endpoint for setting a Prompt/Guardrails value — `T04`/`T06`.
- Any frontend surface — `T05`/`T07`.
- Resolving `classify_recent_emails`'s or `skill_tools.summarize_file`'s own
  ownership ambiguity — explicitly deferred, per the parent story's own
  `## Non-Goals`.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Universal Prompt
Override + Guardrails Placeholder — Agents and Pipeline Jobs (REQ-SB-66, see
ADR-044)" → "Prompt override wiring — four owning call sites in compass_client.py"
bullet. Also read the parent story's own `## Context` in full — it directly reads
all four `compass_client.py` functions and both disclosed dual-ownership/
second-caller scoping calls before this task was written; do not re-litigate those
findings.

**Real, disclosed design tension, not silently resolved:** `compass_client.py`'s
four functions each build ONE combined prompt string mixing static instructions,
the model's own required JSON-response-schema ask, AND per-call dynamic content
(the real subject/sender/body, known lists, thread summary, or source content) —
unlike `state.py`'s Chat SystemMessage or `vault_filing_methodology`'s own
`_METHODOLOGY_EXCERPT`, which are each already a SEPARATE message from the dynamic
content (a HumanMessage carries the interpolated data instead). This task's own
"Starting State → End State" section above deliberately leaves the exact
override/dynamic-content split point as the coder's own implementation choice —
compose around the REAL current `compass_client.py` as it exists today, choosing
whichever concrete split (e.g. override text + an appended dynamic-content suffix
block, mirroring each function's own existing final paragraph) is simplest and most
faithful to Scenario 1's own "uses the newly stored Prompt value... instead of the
previously hardcoded default text" bar. An operator whose own override text drops
the JSON-response-format ask can break that function's own downstream parsing —
disclosed here as a real, accepted consequence of giving genuine prompt control (no
locked AC in this story asks for schema-preservation validation), not a defect this
task needs to guard against.

**Gate stays `flagged`, trigger-1** — carried from the parent story's own
`gate_reason` (the "four functions, not two" expansive reading, plus the two
disclosed, deliberately-unwired scoping calls this task's own Files to Modify
enumerate). A `REVIEW-QUEUE.md` entry exists at the story level; it does not block
this task's build.

---

## Implementation Log

**Built as designed, no deviations.** Read the real, current
`compass_client.py`, `email_classification.py`, and `todo_classification.py`
fresh before editing (per this task's own instruction) — confirmed each of the
4 `compass_client.py` functions builds ONE combined prompt string, static
instructions followed immediately by an f-string of per-call dynamic content
(`From:`/`Subject:`/body for `classify_email`, `Task subject:`/body for
`classify_task`, the bare `thread_summary` for `guess_project_for_thread`,
`Source:`/content for `summarize_content`), each already ending its static
portion with `"\n\n"` right before the dynamic f-string began.

Chose the split point the task's own "Starting State → End State" section left
open: pulled each function's static portion out into a `default_instructions`
local (byte-identical to the original literal, unchanged), computed the
existing dynamic f-string into a separate `dynamic_content` local (also
byte-identical), then branched — `prompt_override is None` → `default_instructions
+ dynamic_content` (exactly reproduces today's original single literal,
concatenation-equivalent since the two locals are literally the split halves of
the original string); `prompt_override is not None` → `f"{prompt_override}\n\n
{dynamic_content}"` (override text, then the same real per-call dynamic data,
verbatim, joined by the same `"\n\n"` separator the static portion already used).
No other line in any of the 4 functions changed — `httpx.post`/`CompassError`/
JSON-parsing logic is untouched, as required.

`email_classification.py`: added `agent_prompts` to the existing `from
app.business import (...)` block (alphabetically, before `customer_hub_linking`).
`classify_captured_email` now resolves `agent_prompts.get_prompt("classify")`
and passes it as `classify_email`'s new `prompt_override` kwarg.
`route_to_project` resolves `agent_prompts.get_prompt("route_to_project")` and
passes it into `guess_project_for_thread`. `summarize_attachment` resolves
`agent_prompts.get_prompt("summarize_attachment")` and passes it into
`summarize_content`. `classify_recent_emails`'s own separate call to
`compass_client.classify_email` (the still-live `/poc/classify-emails` path) was
left completely untouched — confirmed via a targeted `git diff` after the edit
that only the 3 intended call sites plus the import block changed in this file.

`todo_classification.py`: `from app.business import customer_hub_linking` became
`from app.business import agent_prompts, customer_hub_linking`.
`classify_recent_todos` now resolves `agent_prompts.get_prompt("todo-capture")`
and passes it into `classify_task`.

`skill_tools.py` was not opened for editing at all this task (not in `## Files
to Modify`); its own separate call to `compass_client.summarize_content` stays
exactly as it was.

Layering (`ADR-003`) verified by inspection: `compass_client.py`'s own import
block is unchanged (`from __future__ import annotations`, `json`, `httpx`,
`app.config.settings`) — no `agent_prompts` import was added there; the
override lookup happens only in the 2 business-layer callers, which pass the
already-resolved string down as a plain `prompt_override: str | None` parameter.

Verification was run against the real, configured backend venv
(`src/backend/.venv`) via a one-off script (not a persisted pytest file, per
this task's own "Automated tests: n/a — test tooling pending"), with
`httpx.post` monkeypatched to capture the constructed `payload["messages"][0]
["content"]` instead of making a real network call, and `settings.vault_path`
redirected to a scratch temp directory for the duration of the script so the
real vault's own `.second-brain/agent_prompts.json` (already touched by `T01`'s
own verification, holding a real `"vault-filing-expert"` prompt and `"classify"`
guardrails value) was never read from or written to by this task's marker-value
test writes.

- **[REQ-SB-66-US-01-AC-01]** PASS, all 4 owning call sites. For each of
  `"classify"`/`"todo-capture"`/`"route_to_project"`/`"summarize_attachment"`:
  called `agent_prompts.set_prompt(owning_id, "MARKER-XYZ-OVERRIDE-TEXT")`, then
  invoked the owning business-layer function against representative input data
  (`classify_captured_email`, and — since `classify_recent_todos`/
  `route_to_project` reach outward to `outlook_com`/`vault_writer` primitives not
  in this task's own Files to Modify — a direct `compass_client` call using the
  SAME `prompt_override` value the owning function would itself resolve via
  `agent_prompts.get_prompt`, per this AC's own step wording; `route_to_project`
  was exercised end-to-end with `vault_writer.list_customer_projects` and
  `pending_approval_registry.create_pending_approval` stubbed so only the real
  `guess_project_for_thread` call under test executed unstubbed). In every case
  the constructed `payload["messages"][0]["content"]` (inspected via the
  monkeypatched `httpx.post` capture, before any real HTTP call) contained the
  marker string and did NOT contain that function's own previously-hardcoded
  instructional opening line (`"Classify this inbox item"` /
  `"Classify which customer"` / `"Which currently-open Project"` /
  `"Summarize the following document"`). Confirmed a DIFFERENT, un-overridden id
  is unaffected: with `"classify"`/`"todo-capture"`/`"route_to_project"`/
  `"summarize_attachment"` all still holding their own marker overrides, a plain
  `compass_client.classify_email(...)` call with no `prompt_override` argument
  (mirroring `classify_recent_emails`'s own untouched call shape) produced its
  own real hardcoded default prompt text, unaffected by any of the 4 stored
  overrides.
- **[REQ-SB-66-US-01-AC-04]** PASS, all 4 functions. With `prompt_override`
  omitted (defaulting to `None`), called `classify_email`/`classify_task`/
  `guess_project_for_thread`/`summarize_content` directly and diffed the
  constructed prompt string (`==`) against each function's own real, unmodified
  "before" prompt text (captured from the file as it read before this task's
  edit, reproduced verbatim in the verification script) — byte-for-byte
  identical for all 4.
- **Regression (not itself a locked AC).** `classify_recent_emails`'s own call
  to `compass_client.classify_email` and `skill_tools.summarize_file`'s own call
  to `compass_client.summarize_content` were confirmed unmodified by `git diff`
  (neither function's own body appears in this task's diff) — both continue to
  pass no `prompt_override`, so both produce their own function's real hardcoded
  default prompt text regardless of any override saved for `"classify"`/
  `"summarize_attachment"`, per the isolation check under `AC-01` above.

Full backend test suite (`pytest`, `src/backend`) re-run after the change:
1 passed, no regressions. `ast.parse()` of all 3 modified files confirmed clean.

No file outside `## Files to Modify` was touched. No new assumption or
scope-internal judgement call beyond the one already disclosed and carried
forward in this task's own `gate_reason` (the "four functions, not two"
expansive reading and the two deliberately-unwired scoping calls) — nothing new
to log for human spot-check.
