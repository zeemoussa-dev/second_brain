---
id: REQ-SB-66-US-01-T01
title: New agent_prompts.json sibling store — get/set-by-id for Prompt + Guardrails, additive default-fallback
parent_story: REQ-SB-66-US-01
requirement_id: REQ-SB-66
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-66-US-01-T01 — New `agent_prompts.json` sibling store

## Parent Story

- Story: [[REQ-SB-66-US-01]] — `../UserStories/REQ-SB-66-US-01-real-editable-prompt-and-guardrails-placeholder.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-66 *Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings*

---

## Objective

Add a new `app/business/agent_prompts.py` business module, backed by a new sibling
`.second-brain/agent_prompts.json` file, exposing id-keyed get/set primitives for a
`prompt` (`str | None`, absent = no override) and a `guardrails` (`str`, absent = `""`)
value per id — the SAME flat id-keyed shape `agent_keywords.py`/
`working_mode_registry.py` already establish, covering a real Agent id (e.g.
`"vault-filing-expert"`) and a real Job id (e.g. `"classify"`) uniformly, with no
special-casing between the two.

---

## Starting State → End State

**Before / Inputs:**
- `app/data_access/vault_writer.py` already has 3 real, established sibling-store
  precedents to mirror exactly: `_agent_keywords_path()`/`_load_agent_keywords_index()`/
  `load_agent_keywords()`/`save_agent_keywords()`/`load_all_agent_keywords()` (a flat
  `{agent_id: list[str]}` shape); `_working_modes_state_path()`/
  `load_working_modes_state()`/`save_working_modes_state()` (a `{"assignments": {...}}`
  shape); `_agent_scopes_path()`/`load_agent_scope()`/`save_agent_scope()`/
  `load_all_agent_scopes()`. No `agent_prompts.json` primitive of any kind exists yet.
- `app/business/working_mode_registry.py`'s own `_load_state()`/`get_agent_working_mode()`
  is the established "self-healing default, never raises, never requires a prior save"
  shape this task's own default-fallback behavior mirrors (Decision 3 in the parent
  story — an unset override reads back as absent/empty, not an error).
- `agent_registry.py` is not modified by this task (or any task in this story) — the
  parent story's own Constraint (`ADR-011` point 2).

**After / Outputs:**
- `vault_writer.py` gains `_agent_prompts_path()` (mirrors `_agent_keywords_path()`
  exactly — same `_STATE_DIR`, a new `_AGENT_PROMPTS_FILE = "agent_prompts.json"`
  constant), `_load_agent_prompts_index() -> dict[str, dict]` (returns `{}` if the file
  doesn't exist yet, mirrors `_load_agent_keywords_index()`), and whole-record
  load/save primitives for one id's own `{"prompt": str | None, "guardrails": str}`
  entry (see Files to Modify for the exact suggested shape).
- `app/business/agent_prompts.py` (new) gains:
  - `get_prompt(id: str) -> str | None` — `None` when no override has ever been saved
    for `id` (the ordinary, expected starting state — mirrors `load_agent_keywords`'s
    own "no assignment yet" docstring reasoning, not `working_mode_registry`'s seeded
    default, since Prompt has no sensible universal default text of its own to seed).
  - `set_prompt(id: str, prompt: str) -> None` — whole-value replace for `id`'s own
    `prompt` entry.
  - `get_guardrails(id: str) -> str` — `""` when unset (Decision 3/ADR-044 point 2:
    Guardrails is always present, defaulting to an empty string, never absent/`None`).
  - `set_guardrails(id: str, guardrails: str) -> None` — whole-value replace for `id`'s
    own `guardrails` entry.
- `agent_prompts.json` (created on first write, under `.second-brain/`) — a flat,
  id-keyed JSON object, e.g. `{"vault-filing-expert": {"prompt": "...", "guardrails":
  ""}, "classify": {"prompt": null, "guardrails": "Do not..."}}`. A real Agent id and a
  real Job id share this one namespace with zero special-casing (Scenario 8/`AC-08`).

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  - Add `_AGENT_PROMPTS_FILE = "agent_prompts.json"` alongside the existing
    `_AGENT_KEYWORDS_FILE`/similar constants.
  - Add `_agent_prompts_path()`, mirroring `_agent_keywords_path()` exactly (same
    `_STATE_DIR`/`settings.vault_path` composition, same `mkdir(parents=True,
    exist_ok=True)`).
  - Add `_load_agent_prompts_index() -> dict[str, dict]`, mirroring
    `_load_agent_keywords_index()` (returns `{}` if the file doesn't exist; otherwise
    `json.loads(path.read_text(encoding="utf-8"))`).
  - Add `load_agent_prompt_record(id: str) -> dict` (returns `{"prompt": None,
    "guardrails": ""}` when `id` has no entry yet — self-healing default shape,
    mirrors `load_agent_keywords`'s own no-raise style) and
    `save_agent_prompt_record(id: str, record: dict) -> None` (whole-record replace
    for `id`'s own key, mirrors `save_agent_keywords`'s whole-list-replace style).
    Naming/shape latitude: the coder may split this into 4 narrower primitives
    (`load_agent_prompt`/`save_agent_prompt`/`load_agent_guardrails`/
    `save_agent_guardrails`) if that reads more naturally against the real file's
    existing conventions — either shape satisfies this task's own Acceptance
    Criteria; whichever is chosen, `agent_prompts.py` composes ONLY through
    `vault_writer.py`, never touching `.second-brain/agent_prompts.json` directly
    (`ADR-003`'s `api → business → data_access` layering).
- `src/backend/app/business/agent_prompts.py` (new):
  - `get_prompt(id: str) -> str | None`, `set_prompt(id: str, prompt: str) -> None`,
    `get_guardrails(id: str) -> str`, `set_guardrails(id: str, guardrails: str) ->
    None` — composed against the `vault_writer.py` primitives above, no direct file
    I/O in this module.

---

## Constraints

- Inherits from parent story: `agent_registry.py` is never modified — this store is
  composed alongside it, never inside it (`ADR-011` point 2).
- Must respect the `api → business → data_access` layer boundary (`ADR-003`) —
  `agent_prompts.py` (business) composes `vault_writer.py` (data_access) primitives
  only; it never reads/writes `.second-brain/agent_prompts.json` directly.
- An id with no saved Prompt override must read back `get_prompt(id) is None` — never
  `""`, never a raised exception, never a fabricated default string (that distinction
  is what lets `T02`/`T03`'s own call sites tell "no override" apart from "operator
  explicitly saved an empty string").
- An id with no saved Guardrails value must read back `get_guardrails(id) == ""` —
  never `None`, never raised (Decision 3/`ADR-044` point 2's "always present" bar).
- `set_prompt`/`set_guardrails` are whole-value replace semantics — no incremental
  append/merge primitive is implied or needed (mirrors `save_agent_keywords`'s own
  whole-list-replace convention, applied to a scalar value here instead of a list).
- No cross-id bleed: writing one id's own `prompt`/`guardrails` must never alter any
  OTHER id's own stored record (Scenario 9/`AC-09`).
- This task does not wire the override into any real runtime call site — that is
  `T02`/`T03`'s own scope. This task only builds the store and its get/set surface.
- This task does not add any HTTP-reachable endpoint — that is `T04`/`T06`'s own
  scope.

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-66-US-01-AC-08]** Call `set_prompt("vault-filing-expert", "Custom
   placement instructions.")` and `set_guardrails("classify", "Never file to
   Unsorted without a confidence note.")` — confirm `.second-brain/agent_prompts.json`
   now contains BOTH a `"vault-filing-expert"` key (a real Agent id) and a
   `"classify"` key (a real Job id) in the SAME flat top-level object, each holding
   its own `{"prompt", "guardrails"}` shape, with no distinguishing "kind" field or
   separate section between the two — confirming one identical storage/lookup
   mechanism serves both id kinds with no special-casing. Confirm
   `agent_registry.py`'s own source file is byte-for-byte unchanged (e.g. `git diff`
   shows no modification to it) after these writes.
2. **[REQ-SB-66-US-01-AC-09]** With both ids from step 1 already holding distinct
   stored values, call `set_prompt("classify", "A different override.")` — then
   re-read `get_prompt("vault-filing-expert")` and `get_guardrails("vault-filing-
   expert")` and confirm BOTH are completely unchanged from step 1's own values (no
   cross-id bleed in the stored JSON). Re-read `get_prompt("classify")` and confirm
   it reflects the new value.
3. Regression (not itself a locked AC): call `get_prompt("never-saved-id")` and
   `get_guardrails("never-saved-id")` for an id with no prior entry at all — confirm
   `get_prompt` returns `None` (not `""`, not a raised exception) and
   `get_guardrails` returns `""` (not `None`, not a raised exception).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `agent_prompts.py` + its `vault_writer.py` primitives mirror
      `agent_keywords.py`/`working_mode_registry.py`'s own established sibling-store
      shape — same `_STATE_DIR` composition, same self-healing-default, no-raise
      read style
- [x] `get_prompt`/`get_guardrails` return `None`/`""` respectively for any id with
      no saved value, never raising
- [x] `set_prompt`/`set_guardrails` are whole-value replace, with zero cross-id bleed
- [x] `agent_registry.py` is not modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring the override into any real prompt-building call site — `T02`/`T03`.
- Any HTTP-reachable endpoint exposing this store — `T04`/`T06`.
- Any frontend consumption — `T05`/`T07`.
- Any enforcement behavior for the stored Guardrails value — explicitly out of scope
  for the whole parent story (structure-only field).

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Universal Prompt
Override + Guardrails Placeholder — Agents and Pipeline Jobs (REQ-SB-66, see
ADR-044)" → "New sibling store, same shape this codebase already repeats" bullet.
Also read `Implementation/Architecture/ADR.md` → `ADR-011` point 2/`ADR-030` (the
already-`Accepted` "identity stays hardcoded, mutable state lives separately"
pattern this task mechanically applies a further time — no new ADR needed for this
part, per `ADR-044`'s own Consequences).

Compose around the REAL current `vault_writer.py`/`agent_keywords.py`/
`working_mode_registry.py` as they actually exist today — do not assume exact
variable/function names from this task's own illustrative prose without reading the
real files first (this codebase's own established "compose around the real current
file" precedent, `Learnings.md`).

**Naming latitude, disclosed:** whether Prompt/Guardrails are stored as one combined
per-id record (`{"prompt": ..., "guardrails": ...}`) or two separate per-id maps is a
task-level implementation choice, not decided here — either satisfies every locked
AC this task covers. The combined-record shape is suggested above because
`agent_prompts.json` is a SINGLE new file (per Decision 2 in the parent story), and a
combined record keeps one id's own two values co-located, but a two-map shape inside
the same file is equally valid if it reads more naturally against the real file.

---

## Implementation Log

**Built as designed, no deviations.** Compared the two disclosed naming/shape
options against the real current `vault_writer.py`/`agent_keywords.py` shape
and chose the combined-record option (`load_agent_prompt_record`/
`save_agent_prompt_record`, `{"prompt": str | None, "guardrails": str}` per
id) — it mirrors `_agent_keywords_path`/`_load_agent_keywords_index`/
`load_agent_keywords`/`save_agent_keywords`'s own exact structure one-for-one
(constant, `_<x>_path()`, `_load_<x>_index()`, then the public load/save
pair), keeping `agent_prompts.json` a single new sibling file with one id's
own Prompt and Guardrails co-located, per the task's own suggested shape.

`vault_writer.py` gained `_AGENT_PROMPTS_FILE = "agent_prompts.json"`
(alongside the existing `_AGENT_*_FILE` constants), `_agent_prompts_path()`
(same `_STATE_DIR`/`settings.vault_path` composition, same
`mkdir(parents=True, exist_ok=True)`), `_load_agent_prompts_index() ->
dict[str, dict]` (returns `{}` if the file doesn't exist), and
`load_agent_prompt_record(id)`/`save_agent_prompt_record(id, record)`
(self-healing default `{"prompt": None, "guardrails": ""}`, whole-record
replace) — placed directly after the `agent_scopes` primitives, grouping
every per-id agent-adjacent sibling store together.

`app/business/agent_prompts.py` (new) gained `get_prompt`/`set_prompt`/
`get_guardrails`/`set_guardrails`, composed ONLY against the
`vault_writer.py` primitives above — no direct file I/O, no import of
`agent_registry.py` (this store needs no agent-identity validation of its
own; `id` is accepted as any string, matching the "real Agent id and real
Job id share one namespace uniformly" requirement).

Verification was run directly against the real, configured backend venv
(`src/backend/.venv`) and the real, configured vault
(`VAULT_PATH=<OPERATOR_VAULT_OLD>`) — `python -c` one-off
scripts, not a persisted pytest file (repo has no test suite for this
module yet, per this task's own "Automated tests: n/a — test tooling
pending"). `.second-brain/agent_prompts.json` is a new internal state file
in the same trust tier as `agent_keywords.json`/`agent_scopes.json` (never
a vault note) — no scratch-vault isolation was needed, matching how the
sibling-store precedents this task mirrors are themselves exercised.

- **[REQ-SB-66-US-01-AC-08]** PASS. Called
  `agent_prompts.set_prompt("vault-filing-expert", "Custom placement
  instructions.")` and `agent_prompts.set_guardrails("classify", "Never
  file to Unsorted without a confidence note.")`. Read back the raw
  `.second-brain/agent_prompts.json` file directly: both
  `"vault-filing-expert"` (a real Agent id) and `"classify"` (a real Job
  id) are present as top-level keys in the SAME flat object, each holding
  exactly `{"prompt", "guardrails"}` — no "kind" field, no separate
  section between the two. `git status --porcelain -- src/backend/app/
  business/agent_registry.py` showed the identical pre-existing `M`
  status before and after these writes (the file's own last-write
  timestamp, `2026-08-16 18:46:06`, predates this task's script runs) —
  confirming these writes triggered zero new modification to
  `agent_registry.py`.
- **[REQ-SB-66-US-01-AC-09]** PASS. With both ids from `AC-08` already
  holding distinct values, called `agent_prompts.set_prompt("classify",
  "A different override.")`. Re-read `get_prompt("vault-filing-expert")`
  (`"Custom placement instructions."`, unchanged) and
  `get_guardrails("vault-filing-expert")` (`""`, unchanged) — both
  identical to their `AC-08` values, confirming zero cross-id bleed.
  Re-read `get_prompt("classify")` — correctly reflects `"A different
  override."`.
- **Regression (not itself a locked AC).** `get_prompt("never-saved-id")`
  returned `None` (not `""`, not raised); `get_guardrails
  ("never-saved-id")` returned `""` (not `None`, not raised).

Full backend test suite (`pytest`, `src/backend`) re-run after the change:
1 passed, no regressions. `ast.parse()` of both modified/new files
confirmed clean.

No file outside `## Files to Modify` was touched. No assumption or
scope-internal judgement call beyond the disclosed naming latitude (the
combined-record shape, chosen per the task's own explicit "either shape
satisfies this task's own Acceptance Criteria" latitude) — nothing new to
log for human spot-check.
