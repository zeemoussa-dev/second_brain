---
id: REQ-SB-36-US-01-T03
title: provider_registry.py — "anthropic-claude" real-client id, "Anthropic Claude" auto-seed, new get_provider()
parent_story: REQ-SB-36-US-01
requirement_id: REQ-SB-36
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-022 created) — carried from the parent story; the human reviews ADR-022 alongside this task breakdown. No decomposer-owned trigger fired on this task itself; this task's own deliverables (get_provider, the Anthropic Claude seed) are unaffected by the later mid-build Provider-resolution correction (see T04's own Implementation Log) -- T04 now resolves credentials via get_agent_provider, a different, already-existing function this task did not need to touch."
phase: P1
depends_on: [REQ-SB-36-US-01-T01]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-36-US-01-T03 — `provider_registry.py` extension for `"anthropic-claude"`

## Parent Story

- Story: [[REQ-SB-36-US-01]] — `../UserStories/REQ-SB-36-US-01-web-research-skill.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-36 *Agent Knowledge Bootstrapping via Delegated Research*

---

## Objective

Extend the already-`Done` `provider_registry.py` (`REQ-SB-19-US-01`) with a genuinely new, real Provider: `_REAL_CLIENT_PROVIDER_IDS` gains `"anthropic-claude"`; `_seed_state()` additionally auto-seeds an `"Anthropic Claude"` entry from `Settings.anthropic_api_key`/`anthropic_model`; a new `get_provider(provider_id) -> dict | None` by-id lookup helper is added (`ADR-022` point 3).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `Settings.anthropic_api_key`/`anthropic_model`.
- `provider_registry._REAL_CLIENT_PROVIDER_IDS == {"compass"}`; `_seed_state()` seeds only `"Compass"`; no `get_provider` function exists (only `get_agent_provider(agent_id)`, a per-agent lookup).

**After / Outputs:**
- `_REAL_CLIENT_PROVIDER_IDS == {"compass", "anthropic-claude"}`.
- `_seed_state()` seeds both `"Compass"` and `"Anthropic Claude"` (`id: "anthropic-claude"`, `endpoint`: n/a or a documented placeholder since the Anthropic SDK doesn't take a base URL the same way, `credential: settings.anthropic_api_key`, `model: settings.anthropic_model`).
- New `get_provider(provider_id: str) -> dict | None` — a direct by-id lookup (mirrors `get_agent_provider`'s shape one level down), since the web-research skill resolves credentials by a *fixed* Provider id, not by whichever agent happens to invoke it.
- `list_providers()`'s existing output shape is unchanged (still includes `"Anthropic Claude"` automatically, the same generic loop over `state["providers"]` already used for `"Compass"` — no special-casing needed).

---

## Files to Modify

- `src/backend/app/business/provider_registry.py`:
  ```python
  _DEFAULT_PROVIDER_ID = "compass"
  _ANTHROPIC_PROVIDER_ID = "anthropic-claude"

  _REAL_CLIENT_PROVIDER_IDS = {"compass", "anthropic-claude"}


  def _seed_state() -> dict:
      compass = {
          "id": _DEFAULT_PROVIDER_ID,
          "name": "Compass",
          "endpoint": app_settings.compass_base_url,
          "credential": app_settings.compass_api_key,
          "model": app_settings.compass_model,
      }
      anthropic_claude = {
          "id": _ANTHROPIC_PROVIDER_ID,
          "name": "Anthropic Claude",
          "endpoint": "https://api.anthropic.com",  # informational only -- anthropic_client.py never reads this field, it constructs anthropic.Anthropic(api_key=...) directly
          "credential": app_settings.anthropic_api_key,
          "model": app_settings.anthropic_model,
      }
      state = {"providers": [compass, anthropic_claude], "assignments": {}}
      vault_writer.save_providers_state(state)
      return state


  def get_provider(provider_id: str) -> dict | None:
      state = _load_state()
      return next((p for p in state["providers"] if p["id"] == provider_id), None)
  ```
  (`create_provider`/`update_provider`/`remove_provider`/`list_providers`/`get_agent_provider`/`set_agent_provider`/`has_real_client` are all unchanged — this is a pure additive extension.)

---

## Constraints

- Inherits from parent story and `ADR-022` point 3.
- `agent_registry.py` and `compass_client.py` remain unmodified — this task only touches `provider_registry.py`.
- Auto-seed `"Anthropic Claude"` on first read, exactly mirroring `"Compass"`'s own existing self-seed shape — not a manual-creation-only entry.
- `get_provider` is a plain by-id lookup, distinct from `get_agent_provider`'s per-agent lookup — do not conflate the two or change `get_agent_provider`'s own existing behaviour.
- The pre-seeded `"Anthropic Claude"` entry is CRUD-editable via the existing Provider CRUD form but stays inert — editing its representation from Settings must never change the real, live Anthropic call path (`anthropic_client.py` keeps reading `Settings.anthropic_*` indirectly via `get_provider`'s own re-fetched `credential`/`model` values at call time, per `T04`'s own design — this mirrors `"Compass"`'s own precedent where the *seeded* values originate from `.env`, but unlike Compass, the web-research skill's own `T04` resolves credentials THROUGH `get_provider`, not by re-reading `Settings` directly a second time, so an edited "Anthropic Claude" Provider entry's `credential`/`model` DOES take effect on the next real call — a deliberate, real difference from Compass's own inert-edit precedent, worth confirming in Tests below rather than silently assuming the same posture applies).

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv` (real `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` configured, delete any stale `.second-brain/agent_providers.json` from a prior session's seed first). Call `provider_registry.list_providers()`. Confirm it now returns 2 entries — `"compass"` and `"anthropic-claude"` — the latter with `"has_real_client": True`, `"credential_set": True`.
2. Non-AC smoke check: call `provider_registry.get_provider("anthropic-claude")`. Confirm it returns the real seeded entry with `credential == settings.anthropic_api_key` and `model == settings.anthropic_model`. Call `provider_registry.get_provider("not-a-real-id")` — confirm `None`.
3. Non-AC smoke check: call `provider_registry.has_real_client("anthropic-claude")` — confirm `True`. Confirm `has_real_client("compass")` is still `True` (no regression).
4. Non-AC smoke check: edit the seeded `"Anthropic Claude"` entry's `credential` via `provider_registry.update_provider("anthropic-claude", credential="a-deliberately-different-throwaway-value")`. Confirm `get_provider("anthropic-claude")["credential"]` now reflects the edited value — recording plainly (per the Constraint above) that, unlike Compass's own inert-edit precedent, an edited "Anthropic Claude" entry's credential DOES flow into the real call path once `T04` resolves credentials through `get_provider`. Revert the edit back to the real `settings.anthropic_api_key` value afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `"anthropic-claude"` is a real-client Provider id, auto-seeded as `"Anthropic Claude"` mirroring `"Compass"`'s own shape
- [x] `get_provider(provider_id)` is a new, correct by-id lookup, distinct from `get_agent_provider`
- [x] Every existing `provider_registry.py` function's own behaviour (`Compass`'s own seed, `create_provider`/`update_provider`/`remove_provider`/`get_agent_provider`/`set_agent_provider`) is unchanged
- [x] `agent_registry.py`/`compass_client.py` not modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (the credential-edit-takes-effect behavioural difference from Compass's own precedent is worth recording)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Anthropic client itself — `T02`.
- The skill function that actually calls `get_provider`/`anthropic_client.web_search` — `T04`.
- Any UI — the existing Provider CRUD form already renders any Provider entry generically, per `REQ-SB-19-US-01`'s own precedent.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-022` created at `/plan-tasks` step 1) — the human reviews `ADR-022` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

This task carries no AC-tagged step of its own — `AC-01`/`AC-04` (real results / honest-unavailable) are verified one layer up in `T04`, once `skill_tools.web_research` actually composes this registry's `get_provider`/`has_real_client` with the real `anthropic_client.web_search` call, mirroring `REQ-SB-21-US-01-T02`'s own precedent for a foundational registry task with no AC-tagged step of its own.

---

## Implementation Log

Built exactly per spec — `_ANTHROPIC_PROVIDER_ID = "anthropic-claude"`,
`_REAL_CLIENT_PROVIDER_IDS` extended to `{"compass", "anthropic-claude"}`,
`_seed_state()` extended to also seed `"Anthropic Claude"`, new
`get_provider(provider_id) -> dict | None` by-id lookup added. Every
existing function (`create_provider`/`update_provider`/`remove_provider`/
`list_providers`/`get_agent_provider`/`set_agent_provider`/
`has_real_client`) left untouched.

**No AC-ID tagged to this task** (verified one layer up in `T04`, per its
own Tests note). All 4 manual verification steps performed live against
the real backend `.venv` and the real vault's own `.second-brain/
agent_providers.json` (deleted first to force a clean re-seed, per the
task's own step 1):

1. `list_providers()` returned exactly 2 entries — `"compass"` and
   `"anthropic-claude"`, the latter with `"has_real_client": True`,
   `"credential_set": True`.
2. `get_provider("anthropic-claude")` returned the real seeded entry with
   `credential`/`model` matching the configured `Settings` values;
   `get_provider("not-a-real-id")` returned `None`.
3. `has_real_client("anthropic-claude")` → `True`; `has_real_client("compass")`
   → still `True` (no regression).
4. `update_provider("anthropic-claude", credential="a-deliberately-different-throwaway-value")`
   then `get_provider("anthropic-claude")["credential"]` — confirmed the
   edited value took effect (`"a-deliberately-different-throwaway-value"`),
   proving — exactly as the task's own Constraint predicted — this is a
   real, deliberate difference from Compass's own inert-edit precedent
   (`REQ-SB-19-US-01`'s own `MEMORY.md` entry). Reverted the edit back to
   the real configured credential afterward; confirmed the revert took.

State cleaned up afterward: `.second-brain/agent_providers.json` deleted
once more and allowed to re-seed fresh (picking up the real, final
`.env`-sourced placeholder credential — see `T01`'s own Implementation Log
re: the credential gap) before this story's own later live HTTP
verification (`T05`) ran.

Unaffected by the later `T04`/`T05` Provider-resolution correction — this
task's own `get_provider`/seeding stay exactly as built; `T04` now
resolves credentials via the pre-existing `get_agent_provider(agent_id)`
function instead (a different, already-existing lookup this task did not
need to add or change).
