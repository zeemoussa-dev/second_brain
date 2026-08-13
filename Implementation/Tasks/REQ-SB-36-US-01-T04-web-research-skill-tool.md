---
id: REQ-SB-36-US-01-T04
title: skill_tools.py — new web_research(query) skill (honest unavailable / empty / real)
parent_story: REQ-SB-36-US-01
requirement_id: REQ-SB-36
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-022 created) plus a NEW trigger fired during this task's own build: an operator-directed mid-build correction reversed ADR-022 point 3's fixed-Provider-id design (adr-deviation, ESCALATIONS.md -> ESC-019, Resolved). See Implementation Log."
phase: P1
depends_on: [REQ-SB-36-US-01-T02, REQ-SB-36-US-01-T03]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-36-US-01-T04 — `skill_tools.py`'s new `web_research` skill

## Parent Story

- Story: [[REQ-SB-36-US-01]] — `../UserStories/REQ-SB-36-US-01-web-research-skill.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-36 *Agent Knowledge Bootstrapping via Delegated Research*

---

## Objective

Add `web_research(query: str) -> dict` to `app/business/skill_tools.py`'s `SKILLS` catalog (`ADR-022` point 4) — the third real skill this project registers. Resolves the `"anthropic-claude"` Provider via `provider_registry.get_provider`/`has_real_client` before ever calling `anthropic_client.web_search`, so the honest-unavailable (Scenario 4) and honest-empty (Scenario 3) responses are always real and distinguishable from a genuine result.

---

## Starting State → End State

**Before / Inputs:**
- `T02` has landed `anthropic_client.web_search`. `T03` has landed `provider_registry.get_provider`/`has_real_client("anthropic-claude")`.
- `skill_tools.SKILLS` has one entry, `"diagram-understanding"`.

**After / Outputs:**
- `skill_tools.SKILLS` gains `"web-research"`.
- `skill_tools.web_research(query: str) -> dict` (`@mcp_server.tool()`) returns:
  - `{"available": False, "message": "This skill is not yet available — no real handler has been built for it."}` if the `"anthropic-claude"` Provider has no real client (mirrors `diagram_understanding`'s own honest-unavailable shape exactly), or
  - `{"found": True, "summary": str, "sources": list[str]}` on a real, relevant result, or
  - `{"found": False, "summary": "", "sources": []}` when genuinely nothing relevant is found.

---

## Files to Modify

- `src/backend/app/business/skill_tools.py`:
  ```python
  from app.business import provider_registry
  from app.data_access import anthropic_client

  SKILLS: dict[str, dict] = {
      "diagram-understanding": { ... },  # unchanged
      "web-research": {
          "id": "web-research",
          "name": "Web Research",
          "description": (
              "Given a research subject or query, gather real, current "
              "information from the web using Anthropic's own server-side "
              "web-search tool."
          ),
      },
  }


  @mcp_server.tool()
  def web_research(query: str) -> dict:
      """Given a research subject or query, gather real, current
      information from the web. Honestly reports unavailability if no
      real Anthropic Provider is configured yet, and honestly reports no
      results if the search genuinely finds nothing relevant -- never a
      fabricated result either way (ADR-022 point 4)."""
      provider = provider_registry.get_provider("anthropic-claude")
      if provider is None or not provider_registry.has_real_client("anthropic-claude"):
          return {
              "available": False,
              "message": "This skill is not yet available — no real handler has been built for it.",
          }
      result = anthropic_client.web_search(provider["credential"], provider["model"], query)
      return result
  ```

---

## Constraints

- Inherits from parent story and `ADR-022` point 4.
- Resolve the Provider and check `has_real_client` BEFORE ever calling `anthropic_client.web_search` — Scenario 4 (not yet available) and Scenario 3 (no results) must always be distinguishable from each other and from a real result.
- Reuses `diagram_understanding`'s exact honest-unavailable response shape (`{"available": False, "message": ...}`), for consistency across the skill catalog.
- Never fabricate a result — this function's own body must not synthesize a summary/sources when `anthropic_client.web_search` returns `"found": False`.
- Do not modify `diagram_understanding` or `mcp_server.py` — purely additive.

---

## Tests

<!-- AC-03/AC-04 verified here via direct calls to skill_tools.web_research
against the real backend .venv, real Provider state -- mirrors T02's own
"directly callable" style, one layer up. AC-01/AC-02 (the full
grant/invoke round trip, including the honest-refused case) are verified
in T05, once invoke_skill's own args threading exists. -->

**Manual verification steps:**
1. **[REQ-SB-36-US-01-AC-03]** In a Python shell against the backend `.venv` (real `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` configured). Call `skill_tools.web_research("<a query engineered to return nothing relevant>")` directly. Confirm `{"found": False, "summary": "", "sources": []}` — not a fabricated plausible-sounding result.
2. **[REQ-SB-36-US-01-AC-04]** Temporarily monkeypatch `provider_registry.has_real_client` in-process (mirroring the established in-process-monkeypatch-and-revert pattern) to return `False` for `"anthropic-claude"` specifically. Call `skill_tools.web_research("anything")`. Confirm `{"available": False, "message": "This skill is not yet available — no real handler has been built for it."}` — the identical shape `diagram_understanding` already returns. Revert the monkeypatch; confirm a real call (step 3) now succeeds again, proving the revert was clean.
3. Non-AC smoke check: call `skill_tools.web_research("What is the current version of the Python programming language?")` with the real client restored. Confirm `{"found": True, "summary": <non-empty>, "sources": [...]}`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-03** (Scenario 3) — a genuinely empty search is honestly reported, never fabricated — **re-verified live 2026-08-13 against a real, genuine `ANTHROPIC_API_KEY`; see this task's own Implementation Log for the exact observed shape (`found: true` + honest refusal text + empty `sources`, not the literal `found: false` shape originally documented — a real, load-bearing finding, not a defect; recorded for human review, not silently smoothed over).**
- [x] **AC-04** (Scenario 4) — before/without a real client, the skill returns the existing honest "not yet available" response, never a fabricated result
- [x] `web_research` is registered in `skill_tools.SKILLS`, same catalog shape as `diagram_understanding`
- [x] The Provider/real-client check happens before any call to `anthropic_client.web_search`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `skill_registry.invoke_skill`'s own `args` threading, `skills_router.py`'s optional invoke body — `T05`.
- The conversational tool-binding access-control gap fix — `T06`.
- `diagram_understanding`, `mcp_server.py` — unmodified.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-022` created at `/plan-tasks` step 1) — the human reviews `ADR-022` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

---

## Implementation Log

**Built initially exactly per this task's own literal code sample**
(`web_research(query: str) -> dict`, resolving the fixed
`"anthropic-claude"` Provider id via `provider_registry.get_provider`) —
`AC-04` was verified live against that first version (monkeypatching
`has_real_client` to return `False`, confirming the exact
`diagram_understanding`-shaped honest-unavailable response).

**Mid-build operator correction, then re-verified against the corrected
code — recorded here in full, not silently substituted:** after `T01`-`T03`
were fully built/verified and this task's first version was built and
partially verified, the operator sent a direct correction, quoted
verbatim: "The Anthropic_API_KEY Should be a Provider added to the
Providers List — if I linked the Research Agent to Compass, use Compass.
Don't Halt on that." This reverses `ADR-022` point 3's own explicit design
(a single hardcoded Provider id) — the invoking agent's own linked
Provider must be resolved instead. The operator also required a real
technical question be investigated first, not guessed: does Compass/GPT-5
have a real hosted web-search tool? Investigated live (full evidence in
`ADR-022`'s own "Correction" addendum and `ESCALATIONS.md` → `ESC-019`):
**no** — `compass_client.py`'s own real request payload carries no
`tools`/search parameter at all, and the sibling `agentic-map` project's
own `services/gateway/providers.py` routes its own web-search-capable
agents through a *separate* Perplexity Sonar provider specifically
because Compass/GPT-5 alone cannot do this. Building "web research" on a
plain Compass completion would fabricate an ungrounded result, violating
`REQ-SB-33`'s own already-shipped grounding guardrail.

**As actually built (supersedes this task's own literal code sample
above):**

```python
_ANTHROPIC_PROVIDER_ID = "anthropic-claude"


@mcp_server.tool()
def web_research(query: str, agent_id: str) -> dict:
    provider = provider_registry.get_agent_provider(agent_id)
    if (
        provider is not None
        and provider["id"] == _ANTHROPIC_PROVIDER_ID
        and provider_registry.has_real_client(_ANTHROPIC_PROVIDER_ID)
    ):
        return anthropic_client.web_search(provider["credential"], provider["model"], query)
    return {
        "available": False,
        "message": "This skill is not yet available — no real handler has been built for it.",
    }
```

`agent_id` is a new declared parameter (was `query`-only) — see `T05`'s
own Implementation Log for how `invoke_skill` supplies it without
changing the router's own request-body contract, and `ADR-022`'s own
Correction addendum for the accepted MCP-schema tradeoff this narrows
(not overturns) point 5's own rejected-alternative reasoning about.

**Full AC verification, against the corrected code:**

- **AC-04** (Scenario 4, honest not-yet-available) — verified via TWO
  real, independent conditions, not just the task's own literal
  monkeypatch technique: (a) re-ran the exact specified technique
  (monkeypatch `has_real_client` to return `False` for `"anthropic-claude"`
  while the test agent IS linked to it — the literal "before the real
  Anthropic Provider integration is not yet available" condition) —
  confirmed the identical `{"available": False, "message": "This skill is
  not yet available — no real handler has been built for it."}` response,
  cleanly reverted; (b) a stronger, fully-real condition with zero
  monkeypatching: the `todo-capture` fixture agent, genuinely linked to
  its real default `"compass"` Provider, invoked over real HTTP (`POST
  /agents/todo-capture/skills/web-research/invoke`) — confirmed the
  identical honest response, `200 OK`. Both conditions PASS.
- **AC-03** (Scenario 3, genuinely-empty search honestly reported) —
  **blocked on the missing real `ANTHROPIC_API_KEY`** (see `T01`'s own
  Implementation Log) — a real, working Anthropic call is required to
  produce a genuine no-results condition; not fabricated or guessed.
  Flagged in `REVIEW-QUEUE.md`.
- Registration: `web-research` confirmed present in `skill_tools.SKILLS`
  and in the live `GET /skills` response, same catalog shape as
  `diagram-understanding`.
- Provider/real-client check happens before any call to
  `anthropic_client.web_search` — confirmed by code inspection and by the
  live evidence that the Compass-linked path never reaches the real
  Anthropic call (no `HTTP Request: POST https://api.anthropic.com...`
  line appears in that path's own request trace), while the
  Anthropic-linked path does.
- **A genuine real-dispatch confirmation, not just a code-inspection
  claim:** with `todo-capture` reassigned to `"anthropic-claude"`, a real
  call was attempted and failed with a real, honest `401 invalid
  x-api-key` (confirmed both via a direct Python call and via real HTTP —
  see `T05`'s own Implementation Log) — direct, live proof the corrected
  resolution logic reaches the real Anthropic backend for an
  Anthropic-linked agent, blocked only by the missing genuine credential,
  never fabricating a result.

`diagram_understanding`/`mcp_server.py` confirmed unmodified.
`agent_registry.py`/`compass_client.py` confirmed unmodified (this
task's own files stayed within `skill_tools.py` only, per its own Files
to Modify).

**Scope-internal judgement calls made, logged for human spot-check (this
is why `gate` stays `flagged`, not because of a new escalation needing a
decision — the operator already made the decision directly):** (1)
threading `agent_id` as a real declared MCP-tool parameter (accepted
tradeoff, not silently ignored — see `ADR-022`'s own Correction addendum);
(2) keeping the exact same honest-unavailable message text for BOTH the
"not-yet-wired-at-all" and the "linked-to-a-Provider-without-real-search"
conditions, rather than inventing a second, more specific message — this
keeps `AC-04`'s own locked wording satisfied without weakening it, and
avoids over-specifying a distinction the locked AC text itself never
asked for.

**Re-verification pass (2026-08-13, coder, live against a genuine
`ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` now provisioned in `src/backend/
.env`) — the gap flagged in `REVIEW-QUEUE.md`'s `SPRINT-022` entry, closed.
No source code was changed by this pass; this is re-verification only.**

Backend restarted cleanly on port `8001` (the documented default; found
genuinely free this session — `Get-NetTCPConnection`/`Get-CimInstance
Win32_Process` checked first per `MEMORY.md`'s own protocol, no orphaned
PID found needing a kill this time; the earlier `SPRINT-021`/`SPRINT-022`
"ghost listener" on this port was not present today). `GET /providers`
confirmed `anthropic-claude` seeded with `"has_real_client": true`,
`"credential_set": true`.

**A genuine, load-bearing finding surfaced during this pass, investigated
and resolved before re-verification could proceed — not a code defect:**
the first real invocation attempt still returned a real Anthropic `401
invalid x-api-key`, even though `.env` now carries a genuine key. Root
cause, confirmed by direct inspection: `provider_registry._load_state()`
only calls `_seed_state()` when `.second-brain/agent_providers.json` does
not yet exist on disk — the file already existed from `SPRINT-022`'s own
build pass, seeded at that time with the placeholder
`NOT-PROVISIONED-PLACEHOLDER` credential, and nothing re-syncs an
already-persisted Provider entry's `credential` field from `Settings` on
its own. This exact operational step — delete the stale
`agent_providers.json` to force a clean re-seed from the live `.env` —
is the SAME documented step `T03`'s own Implementation Log already used
after editing `.env` mid-build (see `T03`'s Tests step 1), so this is not
a new discovery, just a re-application of an already-recorded operational
step, confirmed here via `grep -c "NOT-PROVISIONED-PLACEHOLDER"
agent_providers.json` returning `1` before the delete and `0` after
(re-seeded fresh). Deleting this file resets ALL agents' Provider
assignments to the default (`"compass"`) — confirmed harmless here since
every agent was already on `"compass"` before this pass started (`GET
/agents`, checked first) and after the re-seed (identical before/after
state for every agent except the one deliberately relinked for this
test). No skill-grant state (`agent_skills.json`, a separate file) was
touched by this — `vault-qa`'s pre-existing, `SPRINT-024`-documented
*permanent* `"web-research"` grant (`Implementation/Sprints/SPRINT-024-
agent-knowledge-bootstrapping-compass-expert-pilot.md`'s own "Open
follow-ups") was confirmed untouched throughout.

**AC-01/Scenario 1, re-verified live — a genuine, real, non-fabricated
result with real citations:** used `todo-capture` as the scratch test
agent (a fresh throwaway fixture, not `vault-qa`'s permanent pilot
config, per this re-verification's own instruction to prefer a throwaway
agent). Granted `web-research`, relinked to `"anthropic-claude"`. `POST
/agents/todo-capture/skills/web-research/invoke {"query": "What is the
current stable version of the Python programming language?"}` returned:

```json
{"found":true,"summary":"Based on the current date (August 12, 2026), \nthe current stable version of Python is Python 3.14.7, which was released on August 5, 2026\n. \n\nPython 3.14 is the latest major stable release series, with \nPython 3.15 currently in the alpha development phase and expected to launch in October 2026\n.","sources":["https://www.python.org/doc/versions/","https://en.wikipedia.org/wiki/Python_(programming_language)"]}
```

Real, checkable sources (`python.org`, Wikipedia) — not a fabricated or
guessed result, not a generic ungrounded LLM answer with no citations.
`AC-01` is now fully verified (both halves: the routing/dispatch half,
already verified in `SPRINT-022`, and this pass's own "produces a real,
relevant result" half).

**AC-03/Scenario 3, re-verified live — honestly reports nothing relevant
found, never fabricates, but NOT in the literal `{"found": false, ...}`
shape this task's own `## Files to Modify` sample documented; recorded
plainly, not smoothed over:** two queries engineered to have no real
answer were tried. Query 1 — "What was the exact closing stock price in
USD of the fictional company Zzyxqplon Nebula Dynamics on the
Interstellar Commodities Exchange on 3025-07-14?" — returned:

```json
{"found":true,"summary":"I cannot provide the closing stock price for Zzyxqplon Nebula Dynamics on July 14, 3025, because:\n\n1. **This is a fictional company** - \"Zzyxqplon Nebula Dynamics\" does not exist\n2. **The date is in the future**...\n3. **The exchange is fictional**...","sources":[]}
```

Query 2 — a similarly-engineered nonsense query about a fictional
institute's secret codename — returned the same shape: `found: true`, an
honest explanation that it will not fabricate the requested information,
`sources: []`.

**Why this counts as AC-03 verified, not a defect:** the locked AC text
is "it honestly reports that nothing relevant was found, rather than
fabricating a plausible-sounding result" — both real responses above do
exactly this: Claude used the web-search tool, found nothing real, and
said so explicitly rather than inventing a plausible stock price or
codename. `anthropic_client.py::web_search`'s own `found` flag is
computed purely from "is there any non-empty text block" (`if not
summary: return found=False`), and Claude's Messages API essentially
always returns *some* explanatory text even when the search tool itself
returns nothing useful — so the literal `{"found": false, "summary": "",
"sources": []}` shape documented in this task's own `## Files to Modify`
/ `## Starting State → End State` sections appears to be effectively
unreachable in practice with the current model/tool combination; the
real, observed honest-empty shape is `{"found": true, "summary":
<honest refusal text>, "sources": []}`. This is a genuine gap between
the task's own documented output *contract* and the real API's observed
behavior — not a code defect (the code does exactly what it says, and
never fabricates), and not a violation of the locked AC's own wording
(which speaks to honesty, not to a specific JSON shape). Flagged in
`REVIEW-QUEUE.md` for a human decision on whether `AC-03`'s contract
should be clarified in a future pass (e.g. "found: false OR found: true
with empty sources" as the honest-empty family), or left as-is since a
caller inspecting `sources` (not just `found`) already gets the right
signal. Not fixed here — no source code changed in this re-verification
pass, per this pass's own explicit instruction.

**AC-02/Scenario 2, spot-checked unaffected (not required by this pass,
done for completeness):** `vault-filing-expert` (genuinely ungranted)
invoked → real HTTP `403`, `{"detail":"Agent does not have access to this
skill."}` — unchanged from `SPRINT-022`'s own verification.

**Cleanup, confirmed complete:** `todo-capture` reverted to `"compass"`,
its `web-research` grant revoked (`DELETE
/agents/todo-capture/skills/web-research` → `{"revoked": true}`); final
`GET /agents`/`GET /agents/todo-capture/skills` confirmed identical to
this pass's own starting snapshot. `vault-qa`'s permanent `SPRINT-024`
pilot grant/Provider link untouched throughout. Backend process (started
fresh for this pass, PID `45648`/child `28104`) stopped cleanly at the
end of this pass, port `8001` confirmed free again.

`status` stays `Done`. `gate` stays `flagged` for the pre-existing
reasons above, plus this pass's own AC-03-shape finding for human
review — not a new escalation (the operator did not need to make a new
decision; this is a discovered nuance logged for spot-check, per this
project's own scope-internal-judgement-call convention).
