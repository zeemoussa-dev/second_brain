---
id: REQ-SB-42-US-01-T05
title: New app/api/agent_presence_router.py — GET /agent-presence/stream (Server-Sent Events), registered in main.py
parent_story: REQ-SB-42-US-01
requirement_id: REQ-SB-42
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-42-US-01-T01]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-42-US-01-T05 — `GET /agent-presence/stream` (SSE)

## Parent Story

- Story: [[REQ-SB-42-US-01]] — `../UserStories/REQ-SB-42-US-01-real-time-agent-activity-pulses.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-42 *Real-Time Agent Activity Pulses (Agents Map)*

---

## Objective

New `app/api/agent_presence_router.py`, `GET /agent-presence/stream` — a hand-rolled `StreamingResponse` (`text/event-stream`), no new package (`ADR-035` point 1). Subscribes a new `asyncio.Queue`, yields an initial `get_snapshot()` immediately on connect, then yields every subsequent broadcast as an SSE `data: <json>\n\n` event; unsubscribes on client disconnect.

---

## Starting State → End State

**Before / Inputs:** `T01` has landed `agent_presence.subscribe`/`unsubscribe`/`get_snapshot`. `app/main.py` registers every router via `app.include_router(...)`.

**After / Outputs:** new `app/api/agent_presence_router.py`:
```python
import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.business import agent_presence

router = APIRouter(prefix="/agent-presence")


async def _event_stream(request: Request):
    queue = agent_presence.subscribe()
    try:
        yield f"data: {json.dumps(agent_presence.get_snapshot())}\n\n"
        while True:
            if await request.is_disconnected():
                break
            try:
                snapshot = await asyncio.wait_for(queue.get(), timeout=15)
            except asyncio.TimeoutError:
                # Keep-alive comment line -- SSE clients (and some
                # intermediary proxies) treat a long silent connection as
                # stale; a periodic comment (ignored by EventSource's own
                # event parsing) keeps it visibly alive without emitting a
                # data event.
                yield ": keep-alive\n\n"
                continue
            yield f"data: {json.dumps(snapshot)}\n\n"
    finally:
        agent_presence.unsubscribe(queue)


@router.get("/stream")
async def stream(request: Request) -> StreamingResponse:
    return StreamingResponse(_event_stream(request), media_type="text/event-stream")
```
`app/main.py` gains:
```python
from app.api.agent_presence_router import router as agent_presence_router
...
app.include_router(agent_presence_router)
```

---

## Files to Modify

- `src/backend/app/api/agent_presence_router.py` (new) — per the code block above.
- `src/backend/app/main.py` — add the import and `app.include_router(agent_presence_router)` line, additive alongside the existing router registrations.

---

## Constraints

- No new package dependency (`ADR-035` point 1) — hand-rolled `StreamingResponse` only.
- The initial snapshot is yielded BEFORE entering the wait loop, so a client connecting after activity has already started sees correct state immediately (`ADR-035` point 4).
- `agent_presence.unsubscribe(queue)` runs in a `finally` block so a disconnected/cancelled client's queue is always removed from `_subscribers` — a leaked subscriber queue would silently accumulate memory across repeated page loads.
- Do not modify any other router or `main.py`'s existing `lifespan`/CORS/other router registrations.

---

## Tests

**Manual verification steps** (real dev server: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`, backend `.venv`):
1. Non-AC smoke check: `curl -N http://127.0.0.1:8001/agent-presence/stream` (or `Invoke-WebRequest` is unsuitable for a streaming body — use `curl.exe -N` or a small Python `httpx.stream("GET", ...)` script) — confirm the FIRST line received is `data: {...}` containing `"active"`/`"hub_routes"`/`"pending_approval_agent_ids"` keys, within a second or two of connecting (the initial snapshot).
2. **[REQ-SB-42-US-01-AC-07]** While the stream from step 1 is still open, in a separate Python shell against the SAME running process (or via a second real HTTP call that triggers a real broadcast, e.g. `POST /agents/email-capture/skills/summarize-file/invoke`-equivalent — simplest: a direct in-process call is not possible against a separate `uvicorn` process, so instead trigger a real state change via an HTTP call this codebase already exposes that ends up calling `agent_presence`, e.g. trigger a Supervised pending-approval creation via the existing `POST /agents/{agent_id}/trigger`-equivalent flow, or — simplest and most direct — temporarily add no code and instead call `POST /agents/{agent_id}/chat` against an agent, which per `T02` now wraps in `start_activity`/`end_activity`) — confirm a SECOND `data: {...}` line arrives on the still-open stream within ~1s of the real state change, without the client having made any new request (proves push, not poll — no second `GET` was issued).
3. Non-AC smoke check: close the client connection (Ctrl+C the `curl` process). Confirm (via a log line, or a quick Python-shell check of `len(agent_presence._subscribers)` in the running process if attachable, or simply re-run step 1 twice and confirm the subscriber count returns to what it was before either connection) that the server-side queue was unsubscribed — no unbounded growth of `_subscribers` across repeated connect/disconnect cycles.
4. Non-AC smoke check: leave a connection open for >15s with no activity — confirm a `: keep-alive` comment line arrives around the 15s mark and the connection stays open (not dropped).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `GET /agent-presence/stream` yields an initial snapshot immediately on connect
- [ ] A real `agent_presence.broadcast_snapshot()` call pushes a new `data:` event to every open connection without the client polling
- [ ] `agent_presence.unsubscribe` runs on disconnect (`finally`)
- [ ] Registered in `app/main.py` alongside the existing routers
- [ ] No other router or `main.py` behavior changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend change — `T06`-`T08`.
- Any real dispatch call-site instrumentation — `T02`-`T04`.

---

## Context / Notes

Full mechanism/alternatives (WebSocket, `sse-starlette`, polling — all rejected): `ADR-035`. This is the codebase's first real-time push surface — `ADR-035`'s own Consequences name this as a working precedent for any future story needing server-push.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
