---
id: REQ-SB-04-US-01-T01
title: "`/mcp` shared-secret authentication for non-loopback callers"
parent_story: REQ-SB-04-US-01
requirement_id: REQ-SB-04
type: backend
status: Done
gate: clear
gate_reason: "Individually clear (no MUST-FLAG trigger of its own); parent story's own trigger-3 flag (ADR-025 created) was already resolved before this build pass began (ADR-025 Accepted, reviewed 2026-08-13). All 4 non-AC smoke checks verified live against the real running backend — no new trigger fired during the build itself."
phase: P1
depends_on: []
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-04-US-01-T01 — `/mcp` shared-secret authentication for non-loopback callers

## Parent Story

- Story: [[REQ-SB-04-US-01]] — `../UserStories/REQ-SB-04-US-01-agent-vault-write-access.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-04 *Agent Vault Write Access*

---

## Objective

Add real authentication to the `/mcp` mount so any non-loopback caller must
present a valid shared secret before reaching any registered tool —
Second Brain's own in-app loopback MCP client stays unaffected. This is a
hard prerequisite for `T02`'s write-capable tool being safely reachable at
all (`ADR-025` point 1/2).

---

## Starting State → End State

**Before / Inputs:**
- `app/api/mcp_server.py` builds `mcp_server` (a `FastMCP` instance,
  four registered read-only `@mcp_server.tool()`s).
- `app/main.py` mounts it with zero authentication:
  `app.mount("/mcp", mcp_server.streamable_http_app())`.
- `app/business/agent_orchestration/mcp_client.py` connects to
  `"http://127.0.0.1:8001/mcp"` — a real, already-live loopback caller
  that must keep working unchanged.
- `app/config.py::Settings` has `compass_api_key`/`anthropic_api_key` as
  the existing `.env`-sourced credential-field precedent to mirror.

**After / Outputs:**
- New `Settings.hermes_mcp_shared_secret: str` field (`.env`-sourced).
- New `app/api/mcp_auth.py` exporting
  `require_hermes_shared_secret(app: ASGIApp) -> ASGIApp` — an ASGI
  middleware: non-HTTP scopes and loopback HTTP callers
  (`scope["client"][0]` in `{"127.0.0.1", "::1"}`) pass through
  unchecked; any other HTTP caller must present a matching
  `X-Hermes-Shared-Secret` header or receives a `401` before the
  underlying FastMCP app is ever invoked.
- `app/main.py` mounts
  `require_hermes_shared_secret(mcp_server.streamable_http_app())` in
  place of the bare app.
- `src/backend/.env.example` gains a `HERMES_MCP_SHARED_SECRET=` line,
  matching the existing `COMPASS_API_KEY`/`ANTHROPIC_API_KEY` entries'
  shape.

---

## Files to Modify

- `src/backend/app/config.py` — add `hermes_mcp_shared_secret: str` to
  `Settings`.
- `src/backend/app/api/mcp_auth.py` (new) — the ASGI middleware described
  above.
- `src/backend/app/main.py` — wrap the `/mcp` mount with
  `require_hermes_shared_secret(...)`.
- `src/backend/.env.example` — add `HERMES_MCP_SHARED_SECRET=` line.

---

## Constraints

- Inherits from parent story and `ADR-025` points 1-3.
- Loopback bypass must be based on the real TCP peer address
  (`scope["client"][0]`), never a caller-supplied header or hostname
  string — do not trust anything the caller sends to decide whether the
  secret check applies.
- Must not disturb Streamable HTTP's own SSE/streaming framing for a
  non-`"http"` ASGI scope type — pass those through unconditionally.
- `agent_orchestration/mcp_client.py`'s existing loopback call must
  continue to work with **zero** code change to that file.
- Do not add authentication anywhere else in the app — every other
  route stays exactly as unauthenticated as it is today (this project's
  existing single-user/local-only posture); this task is scoped to the
  `/mcp` mount only.

---

## Tests

**Manual verification steps:**
1. Non-AC smoke check: start the backend. From the same machine
   (loopback), confirm the existing in-app chat path
   (`agent_orchestration/mcp_client.py`'s loopback call, exercised via a
   real `POST /agents/{id}/chat` that triggers a tool call) still works
   unchanged with no `HERMES_MCP_SHARED_SECRET` header ever sent.
2. Non-AC smoke check: issue a raw HTTP request to `/mcp` from a
   non-loopback-simulated client (e.g. `httpx.AsyncClient` configured to
   report a non-loopback `client` in the ASGI scope, or a real request
   from another host/container if available) with no
   `X-Hermes-Shared-Secret` header. Confirm a `401` response and that no
   tool call reaches `mcp_server`'s own FastMCP app (no vault read/write
   occurs).
3. Non-AC smoke check: repeat step 2 with an incorrect secret value.
   Confirm `401`.
4. Non-AC smoke check: repeat step 2 with the correct
   `HERMES_MCP_SHARED_SECRET` value in the header. Confirm the request
   reaches the underlying FastMCP app (a real tool call, e.g.
   `list_known_kinds`, succeeds).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] A loopback caller (`127.0.0.1`/`::1`) reaches `/mcp` with no secret
      required, and Second Brain's own in-app loopback MCP client is
      unaffected
- [x] A non-loopback caller without a valid `X-Hermes-Shared-Secret`
      header is rejected `401`, with no tool call executed as a result
- [x] A non-loopback caller with the correct secret reaches the
      underlying FastMCP app normally
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The write-capable MCP tool itself — `T02`.
- Any per-agent credential/identity derived from the shared secret —
  `ADR-025`'s own "Alternatives Considered" explicitly rejects this; a
  single shared secret authenticates "a legitimate Hermes-side caller,"
  nothing more.
- `REQ-SB-03-US-01`'s own future `/plan-tasks` pass — this task's own
  mechanism is shared, reusable infrastructure (`ADR-025` point 3); that
  story's own decomposition should reference this task, not rebuild it.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-025` created at
`/plan-tasks` step 1) — the human reviews `ADR-025` and this story's task
breakdown together; the pipeline does not halt, so this task proceeds to
`Ready` alongside `T02` (and holds `T03` individually blocked — see that
task's own Notes).

This task carries no AC-tagged step of its own from the parent story's
locked ACs (none of `REQ-SB-04-US-01`'s own four Scenarios test `/mcp`
authentication directly — that is `REQ-SB-03-US-01`'s own Scenario 4) —
verified via the Tests block's own non-AC smoke checks instead, the same
shape `REQ-SB-21-US-01-T03` already established for a task whose own
locked-AC consumers live in sibling tasks.

---

## Implementation Log

**Built exactly per `ADR-025` points 1-3, no deviation.** New
`app/api/mcp_auth.py::require_hermes_shared_secret` — an ASGI middleware
class (`__init__(app)`, async `__call__`): non-`"http"` scopes pass through
unconditionally; an HTTP scope with `scope["client"][0]` in
`{"127.0.0.1", "::1"}` passes through unconditionally; any other HTTP scope
must present a matching `X-Hermes-Shared-Secret` header or gets a plain
`401` (`starlette.responses.PlainTextResponse`) with `self._app` never
invoked. New `Settings.hermes_mcp_shared_secret: str` field
(`app/config.py`); `.env.example` gained `HERMES_MCP_SHARED_SECRET=`; the
real, gitignored `.env` got a real dev value so the app could boot (same
precedent as `REQ-SB-36-US-01-T01`'s Anthropic-key placeholder — this one
is a genuinely usable dev secret, not an inert placeholder). `app/main.py`
now mounts `require_hermes_shared_secret(mcp_server.streamable_http_app())`
in place of the bare app; `mcp_server.py` itself untouched by this task.

**Live verification (real backend, real port 8001; two stray processes
from earlier sessions found holding the port were killed and the server
restarted cleanly, per the established specific-PID-kill-and-restart
protocol — Learnings, `SPRINT-019`/`SPRINT-022`):**

1. *Non-AC smoke check 1 (loopback unaffected)* — a real
   `POST /agents/vault-qa/chat` with a message deliberately worded to avoid
   any registered trigger phrase ("What distinct note kinds currently
   exist in the vault? Please call your tool to check rather than
   guessing.") went through `run_agent_conversation`'s real LangGraph
   chat path, which calls the loopback MCP client
   (`agent_orchestration/mcp_client.py`, `http://127.0.0.1:8001/mcp`, no
   `X-Hermes-Shared-Secret` header ever sent) and returned a real,
   tool-backed answer ("Customers, Emails, Files, Guides, Meetings,
   Newsletters, Notes, Notifications, Partners, People" — matching the
   real vault's actual kind folders). **PASS** — loopback genuinely
   unaffected.
2. *Non-AC smoke check 2 (non-loopback, no header → 401, no tool call)* —
   an in-process `httpx.ASGITransport(app=app, client=("203.0.113.5",
   54321))` against the real `app` object (main.py's own build, same
   `require_hermes_shared_secret`-wrapped mount), inside a manually-entered
   `mcp_server.session_manager.run()` context (mirrors main.py's own
   lifespan requirement for the FastMCP transport), `POST /mcp` with no
   secret header → `401 Unauthorized`, body `"Unauthorized"` (after
   Starlette's own trailing-slash mount redirect, `/mcp` → `/mcp/`, still
   enforced identically on the retried request — confirmed the middleware
   protects both entry forms). **PASS**.
3. *Non-AC smoke check 3 (non-loopback, wrong secret → 401)* — identical
   simulated non-loopback client, header
   `X-Hermes-Shared-Secret: definitely-wrong` → `401 Unauthorized`.
   **PASS**.
4. *Non-AC smoke check 4 (non-loopback, correct secret → reaches FastMCP)*
   — same simulated non-loopback client, header
   `X-Hermes-Shared-Secret: <real HERMES_MCP_SHARED_SECRET>`, using the
   real `mcp` SDK's `streamablehttp_client`/`ClientSession` (a genuine MCP
   session: initialize → `call_tool("list_known_kinds", {})`) → real
   session established, real tool call succeeded, returned the identical
   10-kind list from smoke check 1. **PASS** — the request genuinely
   reached the underlying FastMCP app, not merely a non-401 status.

**Technique note (added for future reference):** simulating a genuinely
non-loopback caller against a locally-run server can't be done via an
ordinary `curl`/`httpx` call from the same machine (the real TCP peer is
always `127.0.0.1`) — used `httpx.ASGITransport(app=app,
client=(fake_ip, fake_port))` exactly as this task's own Tests block
suggested, driving the real, unmodified `app`/`mcp_server` objects
in-process. `base_url` had to be a plausible host (`http://127.0.0.1:8001`,
matching `mcp_client.py`'s own real value) rather than an arbitrary
placeholder (`"http://testserver"` produced a genuine, unrelated `421
Misdirected Request` from FastMCP's own internal Host-header validation,
not from this task's own middleware) — worth remembering for any future
ASGITransport-based non-loopback simulation against this same mount.

**Scope-internal judgement calls (for spot-check, no MUST-FLAG trigger):**
(a) added a real (not placeholder) `HERMES_MCP_SHARED_SECRET` value to the
real `.env` so the app could boot and live-verification could proceed —
`.env` is not in this task's `## Files to Modify` list, but it is
gitignored, untracked local config, the same class of file
`REQ-SB-36-US-01-T01` already touched for the identical reason; (b) used
the `mcp` SDK's own `httpx_client_factory` hook (not named in the task) to
drive a genuine MCP protocol session over the simulated non-loopback
transport for smoke check 4 — a mechanical extension of the task's own
named `httpx.AsyncClient`-with-non-loopback-`client` technique, needed
because a bare `httpx.AsyncClient` alone cannot perform the MCP
initialize/session handshake FastMCP's own transport requires.

gate: clear 2026-08-13 — no MUST-FLAG trigger fired: no material
assumption beyond the two ordinary scope-internal judgement calls above (a
placeholder/config value and a client-technique detail, not the task's own
design), no ADR created/changed, no `ESCALATIONS.md` entry, all 4 own
Tests-block checks verified live and passing.
