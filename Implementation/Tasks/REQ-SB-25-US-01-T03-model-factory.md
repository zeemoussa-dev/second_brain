---
id: REQ-SB-25-US-01-T03
title: agent_orchestration/model_factory.py — resolve a per-agent ChatOpenAI or an honest unavailable signal
parent_story: REQ-SB-25-US-01
requirement_id: REQ-SB-25
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-25-US-01-T01]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-25-US-01-T03 — `agent_orchestration/model_factory.py`

## Parent Story

- Story: [[REQ-SB-25-US-01]] — `../UserStories/REQ-SB-25-US-01-real-conversational-agent-chat.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-25 *Real Conversational Agent Chat*

---

## Objective

Resolve a per-agent `langchain_openai.ChatOpenAI` instance from that
agent's selected Provider (`provider_registry`), returning an explicit
`None` — never a constructed-then-broken model, never a silent fallback —
when the Provider has no real client, mirroring
`agents_router.py::_invoke_action`'s existing honest-unavailability
funnel-gate one layer over for conversational replies (`ADR-015` point 3,
Scenario 4).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed — `langchain_openai` is installed and importable.
- `app/business/provider_registry.py` already exists (`Done`,
  `REQ-SB-19-US-01`): `get_agent_provider(agent_id) -> dict | None`
  (`{"id", "name", "endpoint", "credential", "model"}`),
  `has_real_client(provider_id) -> bool`.

**After / Outputs:**
- `app/business/agent_orchestration/model_factory.py` exists, exposing
  `resolve_agent_model(agent_id: str) -> ChatOpenAI | None`.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/model_factory.py` (new):
  ```python
  """Resolves a per-agent langchain_openai.ChatOpenAI instance from that
  agent's selected Provider (REQ-SB-19's provider_registry), the single
  source of LLM connection configuration for this new conversational
  surface too (ADR-015 point 4). Returns None -- an explicit "unavailable"
  signal -- before any model is constructed or called, when the Provider
  has no real client -- mirrors agents_router.py::_invoke_action's existing
  "declared but not yet backed by a real handler -> honest unavailability,
  no silent fallback, no fabricated response" funnel-gate shape (ADR-011
  point 3 / ADR-014 point 7), applied one layer over for conversational
  replies (ADR-015 point 3, REQ-SB-25 Scenario 4)."""
  from langchain_openai import ChatOpenAI

  from app.business import provider_registry


  def resolve_agent_model(agent_id: str) -> ChatOpenAI | None:
      provider = provider_registry.get_agent_provider(agent_id)
      if provider is None or not provider_registry.has_real_client(provider["id"]):
          return None
      return ChatOpenAI(
          base_url=provider["endpoint"],
          api_key=provider["credential"],
          model=provider["model"],
      )
  ```

---

## Constraints

- Inherits from parent story: `app/data_access/compass_client.py` and
  `app/config.py` are **not modified or imported** by this module — Compass
  connection configuration is sourced exclusively through
  `provider_registry.get_agent_provider`, per `ADR-015` point 4's own
  explicit "not an extension of `compass_client.py`" decision.
- Must not construct a `ChatOpenAI` instance, nor call it, when
  `has_real_client(provider["id"])` is `False` — the check happens first,
  unconditionally, before any model object is created.
- Must not compose the honest "unavailable" message text here — this
  module returns only `None`; the caller (`T07`'s `graph.py`) composes the
  user-facing message using the same `provider_registry` record, mirroring
  `_invoke_action`'s own inline message composition.

---

## Tests

<!-- This task has no locked AC of its own — model_factory.py is an
internal building block with no directly observable HTTP/user-facing
outcome by itself; REQ-SB-25-US-01-AC-04 (Scenario 4) is verified
end-to-end in T08, once agents_router.py::chat actually surfaces the
honest-unavailable reply this module's None return enables. Its own
verification here is a non-AC smoke check. -->

**Manual verification steps:**
1. Non-AC smoke check: in a throwaway interpreter against `src/backend`'s
   `.venv`, confirm `resolve_agent_model("email-capture")` (default
   `"compass"` Provider, a real client) returns a `ChatOpenAI` instance
   (not `None`), with its `base_url`/`model` attributes matching
   `provider_registry.get_agent_provider("email-capture")`'s `endpoint`/
   `model` values.
2. Non-AC smoke check: `POST /providers` a throwaway Provider with an id
   that is **not** in `provider_registry._REAL_CLIENT_PROVIDER_IDS` (e.g.
   any id other than `"compass"`), assign it to a test agent via `PATCH
   /agents/{agent_id}`, then confirm `resolve_agent_model(agent_id)`
   returns exactly `None`. Clean up the throwaway Provider/assignment
   afterward (restore the agent's Provider to `"compass"`,
   `DELETE /providers/<throwaway id>`).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `resolve_agent_model(agent_id)` returns a `ChatOpenAI` instance built
      from `provider_registry.get_agent_provider(agent_id)`'s `endpoint`/
      `credential`/`model` when that Provider has a real client
- [x] `resolve_agent_model(agent_id)` returns exactly `None` — no model
      constructed — when the agent has no Provider, or that Provider has
      no real client
- [x] `app/data_access/compass_client.py`, `app/config.py` not modified or
      imported by this module
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Composing the user-facing "Provider X is not available" message text —
  `T07` (`graph.py`).
- `state.py`, `mcp_client.py`, `graph.py` — `T02`, `T06`, `T07`.
- Any change to `provider_registry.py` itself — it is consumed, unmodified.

---

## Context / Notes

This is the exact "before any model is constructed or called" gate
`ADR-015` point 3 names — the honesty posture must hold even if a future
node is added to the graph that might otherwise be tempted to construct a
model speculatively.

---

## Implementation Log

**2026-08-12 — Done.** Created `model_factory.py` verbatim per the task's
own `## Files to Modify` code.

**Non-AC smoke checks (this task carries no locked AC of its own):**
1. `resolve_agent_model("email-capture")` (real `"compass"` Provider) →
   returned a `ChatOpenAI` instance whose `openai_api_base` matched
   `provider_registry.get_agent_provider("email-capture")["endpoint"]`
   (`https://api.core42.ai/v1/chat/completions`) and whose `model_name`
   matched `["model"]` (`gpt-5`). PASS.
2. Created a throwaway Provider (`create_provider("Verify Unavailable
   T03", "https://example.test", "x", "x")` → id `verify-unavailable-t03`,
   not in `_REAL_CLIENT_PROVIDER_IDS`), assigned it to `email-capture`,
   confirmed `resolve_agent_model("email-capture")` returned exactly
   `None`. PASS. Cleaned up: restored `email-capture` → `"compass"`,
   `remove_provider("verify-unavailable-t03")` → `{"deleted": True,
   "blocked_by_agent_ids": []}`; confirmed `get_agent_provider(
   "email-capture")["id"] == "compass"` afterward.

**Scope-internal judgement call, logged for spot-check:** the task's own
`## Tests` wording names the throwaway-Provider check as `POST
/providers`/`PATCH /agents/{agent_id}` HTTP calls; this was instead
performed via the equivalent direct `provider_registry` function calls
(`create_provider`/`set_agent_provider`/`remove_provider`) in a Python
shell against the real `.venv` and real `.second-brain/` state — the
identical underlying business-layer effect and identical proof (a Provider
absent from `_REAL_CLIENT_PROVIDER_IDS` makes `resolve_agent_model` return
`None`), without needing to start the full backend process (which fires a
real Outlook/Compass capture run on every start, per `MEMORY.md`'s
standing constraint) purely to exercise this internal, non-HTTP-reachable
module. `T08`'s own full end-to-end AC verification does exercise the real
HTTP `POST /providers`/`PATCH /agents/{id}` path.

No escalation. `gate: clear` 2026-08-12.
