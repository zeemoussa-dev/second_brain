---
id: REQ-SB-42-US-01-T03
title: Instrument the Hub-routed traveling pulse — knowledge_bootstrap.py's two hops call agent_presence.start_hub_routing/end_hub_routing
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

# REQ-SB-42-US-01-T03 — Hub-routed traveling-pulse instrumentation

## Parent Story

- Story: [[REQ-SB-42-US-01]] — `../UserStories/REQ-SB-42-US-01-real-time-agent-activity-pulses.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-42 *Real-Time Agent Activity Pulses (Agents Map)*

---

## Objective

Wrap each real caller of `graph.route_cross_section_request(...)` that goes on to actually invoke the matched agent — today, `knowledge_bootstrap.bootstrap_agent_knowledge`'s two hops — in `agent_presence.start_hub_routing(from_agent_id, to_agent_id)`/`end_hub_routing(token)`, spanning from the match to completion of the downstream call (`ADR-035` point 3d) — NOT inside `route_cross_section_request` itself, which only computes the match.

---

## Starting State → End State

**Before / Inputs:** `app/business/agent_orchestration/knowledge_bootstrap.py::bootstrap_agent_knowledge(agent_id, subject)` — Hop 1 (`agent_id` → `research_expert_id` via `route_cross_section_request`, then `skill_registry.invoke_skill(research_expert_id, "web-research", ...)`), Hop 2 (`research_expert_id` → `vault_filing_expert_id`, then `vault_filing_expert.determine_placement_and_file(...)`).

**After / Outputs:** each hop's own downstream call is bracketed:
```python
hop1 = graph.route_cross_section_request(agent_id, need_description=f"real web research about {subject}")
if not hop1["matched"]:
    ...
research_expert_id = hop1["agent_id"]
...
token1 = agent_presence.start_hub_routing(agent_id, research_expert_id)
try:
    research_result = skill_registry.invoke_skill(
        research_expert_id, "web-research", {"query": subject}, trigger="hub_routed"
    )
except Exception as exc:
    ...
finally:
    agent_presence.end_hub_routing(token1)
...
hop2 = graph.route_cross_section_request(research_expert_id, need_description="file this content into the vault")
...
vault_filing_expert_id = hop2["agent_id"]
token2 = agent_presence.start_hub_routing(research_expert_id, vault_filing_expert_id)
try:
    filing_result = vault_filing_expert.determine_placement_and_file(...)
finally:
    agent_presence.end_hub_routing(token2)
```

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/knowledge_bootstrap.py` — wrap both hops' downstream calls per the shape above; add `from app.business import agent_presence` import.

---

## Constraints

- The `start_hub_routing`/`end_hub_routing` pair wraps ONLY the downstream call (the `invoke_skill`/`determine_placement_and_file` call), not the `route_cross_section_request` match itself — `ADR-035` point 3d is explicit that the match function has no visibility into how long the downstream call takes.
- Uses `try/finally` so `end_hub_routing` runs even on the existing `except Exception` branch around Hop 1's `invoke_skill` call.
- Every existing early-return branch (`not hop1["matched"]`, `not autonomous`, `not research_result.get("found")`, `not hop2["matched"]`) is otherwise byte-for-byte unchanged — this task only adds the two `start_hub_routing`/`end_hub_routing` pairs around the two real downstream calls, nothing else in this function's control flow changes.
- Do not modify `graph.route_cross_section_request` itself.

---

## Tests

**Manual verification steps** (Python shell, backend `.venv`, `PYTHONPATH=.`):
1. **[REQ-SB-42-US-01-AC-03]** Set up a real routable pair (an agent whose Section Hub routes to a real Research Expert already in Autonomous mode — reuse whichever real Section/agent fixture `knowledge_bootstrap`'s own existing tests/verification used, e.g. the same pairing `REQ-SB-36-US-01`'s own verification used). Monkeypatch `skill_registry.invoke_skill` to, mid-call, assert `agent_presence.get_snapshot()["hub_routes"]` contains one entry with the real `from_agent_id`/`to_agent_id` pair for Hop 1, then delegate to the real function (or a stub returning a real-shaped `{"found": True, "summary": "..."}"`). Call `await knowledge_bootstrap.bootstrap_agent_knowledge(agent_id, "a real test subject")`. Confirm `agent_presence.get_snapshot()["hub_routes"]` is empty again after Hop 1's call returns (before Hop 2 starts) — proves the token is scoped to exactly that hop's own downstream call, not the whole function.
2. **[REQ-SB-42-US-01-AC-03]** Repeat, this time also monkeypatching `vault_filing_expert.determine_placement_and_file` to assert `agent_presence.get_snapshot()["hub_routes"]` contains Hop 2's own `from_agent_id`/`to_agent_id` pair (the Research Expert → Vault Filing Expert pairing) mid-call. Confirm it clears after.
3. Non-AC smoke check: induce Hop 1's own `except Exception` path (monkeypatch `skill_registry.invoke_skill` to raise) — confirm `agent_presence.get_snapshot()["hub_routes"]` is empty after the call returns (the `finally` ran even on the exception path) and the function's own existing honest-failure return (`{"status": "no_results", ...}`) is unchanged.
4. Clean-up: revert every monkeypatch.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Hop 1's downstream `invoke_skill` call is wrapped in `start_hub_routing(agent_id, research_expert_id)`/`end_hub_routing` via `try/finally`
- [ ] Hop 2's downstream `determine_placement_and_file` call is wrapped in `start_hub_routing(research_expert_id, vault_filing_expert_id)`/`end_hub_routing` via `try/finally`
- [ ] `route_cross_section_request` itself is never wrapped
- [ ] Every existing early-return branch's own logic is unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The single-agent capture/skill/chat instrumentation — `T02`.
- The pending-approval broadcast-only instrumentation — `T04`.
- Any change to `route_cross_section_request`'s own matching logic.

---

## Context / Notes

Full mechanism: `ADR-035` point 3d. This is currently the ONLY real caller that goes on to invoke the matched agent after a `route_cross_section_request` match (confirmed by the architect's own direct reading, `architecture.md` → "Real-Time Agent Activity Pulses"); if a future story adds a second such caller, it inherits this same instrumentation pattern, not built here.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
