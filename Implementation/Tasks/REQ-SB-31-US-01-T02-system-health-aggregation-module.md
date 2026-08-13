---
id: REQ-SB-31-US-01-T02
title: New app/business/system_health.py — read-only aggregation of MCP reachability, Provider availability, disabled agents, and last capture run
parent_story: REQ-SB-31-US-01
requirement_id: REQ-SB-31
type: backend
status: Done
gate: flagged
gate_reason: "Live-discovered correction vs. the task's own literal code sample: mcp_mount_reachable() needed follow_redirects=True — see Implementation Log."
phase: P1
depends_on: []
sprint: "SPRINT-019"
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-31-US-01-T02 — New `app/business/system_health.py`

## Parent Story

- Story: [[REQ-SB-31-US-01]] — `../UserStories/REQ-SB-31-US-01-system-health-view.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-31 *System Health View*

---

## Objective

Add a new, read-only aggregation module that composes four already-
existing/already-computed signals into one `get_system_health()` payload
— no new persisted state, no new external round-trip beyond one local
`GET /mcp` loopback call.

---

## Starting State → End State

**Before / Inputs:**
- `app/business/provider_registry.py::list_providers()` (`Done`) already
  returns each Provider rolled up with `has_real_client`/`agent_ids`.
- `app/business/provider_registry.py::get_agent_provider(agent_id)` /
  `has_real_client(provider_id)` (`Done`).
- `app/business/agent_registry.py::list_agents()` (`Done`) returns
  `[{"id", "name", "type"}]`.
- `app/data_access/vault_writer.py::load_last_capture_run()` (`Done`)
  returns `{"finished_at": iso8601} | None`.
- `app/business/agent_orchestration/mcp_client.py` already calls the
  shared MCP mount at the hardcoded loopback `http://127.0.0.1:8001/mcp`.
- `httpx` is already a dependency (`requirements.txt`), already used
  synchronously by `app/data_access/compass_client.py`.

**After / Outputs:**
- `app/business/system_health.py` exists, exposing `get_system_health()
  -> dict` as its one public entry point.

---

## Files to Modify

- `src/backend/app/business/system_health.py` (new):
  ```python
  """Read-only aggregation of Second Brain's own operational signals for
  the System Health view (REQ-SB-31-US-01) -- writes no new persisted
  state at all, composes only already-existing/already-computed signals
  from provider_registry, agent_registry, and vault_writer, plus one
  local, in-process GET /mcp reachability check. Recompute fresh on every
  call -- no caching (Scenario 7)."""
  import httpx

  from app.business import agent_registry, provider_registry
  from app.data_access import vault_writer

  # Same hardcoded loopback host:port agent_orchestration/mcp_client.py
  # already calls -- this project's own documented port convention
  # (tools/run-backend.cmd --port 8001), not a new port-discovery
  # mechanism.
  _MCP_MOUNT_URL = "http://127.0.0.1:8001/mcp"


  def mcp_mount_reachable() -> bool:
      """True only on the mount's own proven "alive" signal (a bare GET
      correctly returns HTTP 406 Not Acceptable when the mount is alive --
      confirmed live 2026-08-12, see architecture.md). Any other status
      code, connection error, or timeout is honestly reported as
      unreachable -- never a fabricated True."""
      try:
          response = httpx.get(_MCP_MOUNT_URL, timeout=3.0)
      except httpx.HTTPError:
          return False
      return response.status_code == 406


  def list_disabled_agents() -> list[dict]:
      """Every agent whose selected Provider has no real client configured
      -- the System-Health-view-specific Disabled/Health-Issue override
      (scoped to this view only, per the story's own Constraints)."""
      disabled = []
      for agent in agent_registry.list_agents():
          provider = provider_registry.get_agent_provider(agent["id"])
          if provider is None or not provider_registry.has_real_client(provider["id"]):
              disabled.append({
                  "agent_id": agent["id"],
                  "agent_name": agent["name"],
                  "provider_name": provider["name"] if provider else None,
              })
      return disabled


  def _providers_with_agent_names() -> list[dict]:
      """provider_registry.list_providers() already rolls up each
      Provider's agent_ids -- this adds a display-only agent_names field
      (resolved via agent_registry.get_agent) alongside it, additive only,
      so the frontend never has to make a second round-trip or duplicate
      the id->name lookup itself. Does not modify provider_registry.py's
      own return contract."""
      providers = provider_registry.list_providers()
      for provider in providers:
          provider["agent_names"] = [
              agent_registry.get_agent(agent_id)["name"] for agent_id in provider["agent_ids"]
          ]
      return providers


  def get_system_health() -> dict:
      return {
          "mcp": {"reachable": mcp_mount_reachable()},
          "providers": _providers_with_agent_names(),
          "disabled_agents": list_disabled_agents(),
          "last_capture_run": vault_writer.load_last_capture_run(),
      }
  ```

---

## Constraints

- Inherits from parent story: `business/` layer only — no HTTP framework
  import (no FastAPI), no direct filesystem access of its own (reads
  `vault_writer.load_last_capture_run()`, never the file directly).
- **No new persisted state file** — this module writes nothing to
  `.second-brain/`.
- `mcp_mount_reachable()` must never raise past its own function — any
  `httpx` exception (connection refused, timeout, etc.) is caught and
  reported as `False`, never left to propagate and 500 the whole
  `/system-health` endpoint.
- `provider_registry.py`/`agent_registry.py` are **not modified** — this
  module composes their existing public functions only.
- `get_system_health()` must recompute fresh on every call — no
  module-level caching of any of the four signals.

---

## Tests

<!-- No locked AC of its own -- this module has no HTTP surface yet
(that's T03) and no screen renders it yet (that's T04). Every one of this
story's 7 view-observable ACs is genuinely observable only once T04 wires
a real page around T03's endpoint -- non-AC smoke check here, mirroring
REQ-SB-25-US-01-T07's / REQ-SB-12-US-02-T02's own identical split. -->

**Manual verification steps** (throwaway interpreter against
`src/backend`'s `.venv`, backend NOT required to be running for the
Provider/agent/capture-run checks, but required and reachable on `8001`
for the MCP check):

1. Non-AC smoke check: with the real backend running on port `8001`, call
   `system_health.get_system_health()` directly. Confirm `mcp.reachable
   is True`, `providers` matches `provider_registry.list_providers()`'s
   own live output, `disabled_agents` is `[]` if every agent's Provider
   currently has a real client (true for the real vault's default
   all-Compass assignment), `last_capture_run` matches
   `vault_writer.load_last_capture_run()`'s own live output.
2. Non-AC smoke check: stop the backend (or point `_MCP_MOUNT_URL` at an
   unreachable port temporarily), call `mcp_mount_reachable()` directly.
   Confirm `False`, no exception raised.
3. Non-AC smoke check: temporarily reassign one agent to a Provider with
   no real client (reuse the pattern `REQ-SB-25-US-01-T07`'s own
   verification already established), call `list_disabled_agents()`.
   Confirm it includes that agent's `{"agent_id", "agent_name",
   "provider_name"}`. Revert the reassignment afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `get_system_health()` returns `{"mcp", "providers",
      "disabled_agents", "last_capture_run"}`, recomputed fresh on every
      call; each entry in `providers` additionally carries a resolved
      `agent_names` list alongside its existing `agent_ids`
- [x] `mcp_mount_reachable()` returns `True` only on an HTTP 406 response
      from the loopback `/mcp` mount; any other outcome (including a
      connection error) returns `False`, never raises
- [x] `list_disabled_agents()` includes exactly the agents whose selected
      Provider has no real client configured
- [x] No new `.second-brain/` state file written by this module
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `app/api/system_health_router.py` — `T03`.
- Any frontend page/component — `T04`.
- The `run_agent_conversation` crash-gap fix — `T01`, no dependency
  either way.
- Active round-trip reachability probing of each configured Provider —
  the story's own Non-Goals.
- Any staleness/pass-fail judgment on `last_capture_run`'s timestamp.

---

## Context / Notes

`provider_registry.list_providers()` already returns each Provider rolled
up "per distinct Provider, from each agent's own selection" — exactly the
shape the story's Context calls for — so this module deliberately does
not re-derive Provider availability from `GET /agents` a second way.

---

## Implementation Log

**Build (2026-08-12).** `app/business/system_health.py` created exactly
per the task's own literal code sample, with one live-discovered
correction (below): `get_system_health()`, `mcp_mount_reachable()`,
`list_disabled_agents()`, `_providers_with_agent_names()`.

**Live-discovered correction vs. the task's own literal code sample
(gate: flagged for human spot-check, per the coder's "scope-internal
judgement call" rule):** the sample's `httpx.get(_MCP_MOUNT_URL,
timeout=3.0)` call, run against the real live backend, returned `307`
(redirecting `GET /mcp` → `GET /mcp/`), not the `406` the story's own
Context claims was "confirmed live 2026-08-12" — because `httpx.get()`'s
own default is `follow_redirects=False`, while the story's own live
confirmation was almost certainly performed with a client that follows
redirects automatically (a browser, or PowerShell's
`Invoke-WebRequest`/`curl`, both confirmed live in this task's own
verification to follow the redirect and land on `406`). As spec'd, the
real, live "everything healthy" case (Scenario 1) would have falsely
reported `mcp.reachable: false` even with a fully healthy MCP mount —
directly undermining Scenario 1/2's own locked-AC semantics (verified
downstream in `T04`). Fixed in-scope, within this task's own
`system_health.py` file: added `follow_redirects=True` to the one
`httpx.get()` call in `mcp_mount_reachable()`. No other file touched, no
new dependency, no interface change — `get_system_health()`'s own return
shape is unchanged.

**Verification — non-AC smoke checks (2026-08-12), against the real
running backend (started via `.claude/launch.json` →
`second-brain-backend`, restarted once via the standing specific-PID-
kill-and-restart protocol after the shared dev backend was found serving
stale code — see `MEMORY.md`/this story's own Notes for the pattern):**

1. **Everything-healthy smoke check:** `GET /system-health` (T03's own
   endpoint, exercising this module end-to-end) returned
   `mcp.reachable: true` (after the `follow_redirects` fix),
   `providers` = `[{"id": "compass", ..., "agent_names": ["Email
   Capture", "Meeting Capture", "To-Do Capture", "People Notes", "Vault
   Q&A"]}]` (matching `GET /providers`'s own live output plus the
   resolved names), `disabled_agents: []` (the real vault's default
   all-Compass assignment), `last_capture_run.finished_at` matching the
   real `.second-brain/last_capture_run.json` contents. **PASS.**
2. **MCP-unreachable smoke check:** temporarily pointed `_MCP_MOUNT_URL`
   at an intentionally unreachable loopback port (`18001`), confirmed
   `GET /system-health` → `mcp.reachable: false`, no exception raised, no
   500. Reverted immediately afterward and re-confirmed `mcp.reachable:
   true` on the very next call — no caching. **PASS.**
3. **Disabled-agent smoke check:** created a throwaway Provider with no
   real client (`POST /providers`, name "Verify No-Client Provider"),
   reassigned `people-producer` to it (`PATCH /agents/people-producer`),
   confirmed `disabled_agents` = `[{"agent_id": "people-producer",
   "agent_name": "People Notes", "provider_name": "Verify No-Client
   Provider"}]`. Reverted `people-producer` back to `compass` and deleted
   the throwaway Provider (`DELETE /providers/verify-no-client-provider`)
   immediately afterward; re-confirmed `disabled_agents: []` and `GET
   /providers` back to exactly the original single-Compass-entry state.
   **PASS.**

Full request/response transcripts and the `follow_redirects` root-cause
diagnosis (307 location header, before/after `httpx.get` comparison) are
in this sprint's own verification session; the corrected code is the
file itself.

`gate: flagged` 2026-08-12 — the `follow_redirects=True` correction is a
scope-internal judgement call (fixing the task's own literal sample to
match real, live-observed `httpx`/FastMCP-mount redirect behavior), not
an escalation: no new dependency, no shared-interface change, no ADR
deviation, no unanticipated file — flagged per the coder's own "log as
an assumption for human spot-check" rule, not `REVIEW-QUEUE.md`/
`ESCALATIONS.md`. `status: Done`.
