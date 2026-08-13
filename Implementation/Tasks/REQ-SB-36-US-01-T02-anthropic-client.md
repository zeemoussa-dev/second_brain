---
id: REQ-SB-36-US-01-T02
title: New app/data_access/anthropic_client.py — web_search(api_key, model, query)
parent_story: REQ-SB-36-US-01
requirement_id: REQ-SB-36
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-022 created) — carried from the parent story; the human reviews ADR-022 alongside this task breakdown. No decomposer-owned trigger fired on this task itself; unaffected by the later mid-build Provider-resolution correction (see T04's own Implementation Log)."
phase: P1
depends_on: [REQ-SB-36-US-01-T01]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-36-US-01-T02 — New `anthropic_client.py`

## Parent Story

- Story: [[REQ-SB-36-US-01]] — `../UserStories/REQ-SB-36-US-01-web-research-skill.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-36 *Agent Knowledge Bootstrapping via Delegated Research*

---

## Objective

Add `app/data_access/anthropic_client.py` (sibling to `compass_client.py`, `ADR-003` layering, `ADR-022` point 2) — a plain `anthropic` SDK client, `web_search(api_key, model, query) -> dict`, calling Anthropic's Messages API with its own server-side web-search tool included in the request, returning a normalized `{"found": bool, "summary": str, "sources": list[str]}`.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed the `anthropic` dependency.
- No `app/data_access/anthropic_client.py` exists.

**After / Outputs:**
- `app/data_access/anthropic_client.py` (new) exposes `web_search(api_key: str, model: str, query: str) -> dict`, returning `{"found": True, "summary": <non-empty str>, "sources": [<url>, ...]}` on a real, relevant result, or `{"found": False, "summary": "", "sources": []}` when the search genuinely returns nothing relevant — never a fabricated summary either way.

---

## Files to Modify

- `src/backend/app/data_access/anthropic_client.py` (new):
  ```python
  """Client for Anthropic's own Messages API, using its server-side
  web-search tool (ADR-022 point 2) — the operator-confirmed mechanism
  for real web research. A plain anthropic SDK client, mirroring
  compass_client.py's own "plain client, no framework wrapper" shape
  (ADR-003) for a fixed-purpose external call; NOT routed through
  model_factory.py/LangChain, since this call never touches
  run_agent_conversation's own graph (ADR-022's own Non-Goals)."""
  from __future__ import annotations

  import anthropic


  class AnthropicResearchError(Exception):
      """The Anthropic call failed or returned an unparseable response."""


  def web_search(api_key: str, model: str, query: str) -> dict:
      client = anthropic.Anthropic(api_key=api_key)
      try:
          response = client.messages.create(
              model=model,
              max_tokens=1024,
              # Exact current tool-type identifier / API version confirmed
              # against Anthropic's own current documentation at real
              # build time (this project's established
              # "pin-then-verify-at-real-install" precedent, ADR-015
              # point 6) -- adapt the literal "type" string below if it
              # has since changed, logging the deviation in the
              # Implementation Log, not grounds for escalation on its own.
              tools=[{"type": "web_search_20250305", "name": "web_search"}],
              messages=[{"role": "user", "content": query}],
          )
      except Exception as exc:  # noqa: BLE001 -- honest-failure-reporting funnel
          raise AnthropicResearchError(f"Anthropic web-search call failed: {exc}") from exc

      text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
      summary = "\n".join(text_blocks).strip()
      sources = _extract_sources(response)

      if not summary:
          return {"found": False, "summary": "", "sources": []}
      return {"found": True, "summary": summary, "sources": sources}


  def _extract_sources(response) -> list[str]:
      """Pulls citation/source URLs out of the response's own web-search
      tool-result content blocks -- the exact attribute path is confirmed
      against the real, installed anthropic SDK version at build time
      (see the module docstring's own caveat); returns [] rather than
      raising if no source metadata is present, never fabricating a URL."""
      sources: list[str] = []
      for block in getattr(response, "content", []):
          for citation in getattr(block, "citations", None) or []:
              url = getattr(citation, "url", None)
              if url:
                  sources.append(url)
      return sources
  ```

---

## Constraints

- Inherits from parent story and `ADR-022` point 2.
- A plain `anthropic` SDK client only — no LangChain wrapper, no `model_factory.py` involvement.
- Never fabricate `"found": True` with an empty/synthesized summary, and never fabricate a `"sources"` URL — both must come directly from the real API response.
- The exact web-search tool-type identifier/API version is confirmed against Anthropic's real, current documentation at build time — log any deviation from the literal string above as a scope-internal assumption, not a blocker.

---

## Tests

<!-- No AC is locked directly against this data_access-layer module on its
own -- AC-01/AC-03 (real results / honest no-results) are verified one
layer up, in T04, once skill_tools.web_research composes this client with
real Provider credentials. This task's own Tests are non-AC smoke checks
confirming the client itself works in isolation, catching any real-API
integration issue before T04 composes it. -->

**Manual verification steps:**
1. Non-AC smoke check: with a real, provisioned `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL`, call `anthropic_client.web_search(settings.anthropic_api_key, settings.anthropic_model, "What is the current version of the Python programming language?")` directly in a Python shell. Confirm `"found": True` and a non-empty, genuinely relevant `"summary"`.
2. Non-AC smoke check: call `anthropic_client.web_search(...)` with a query engineered to return nothing relevant (e.g. a nonsense string unlikely to have any real web presence). Confirm `"found": False`, `"summary": ""`, `"sources": []` — not a fabricated result.
3. Non-AC smoke check: call `anthropic_client.web_search(...)` with a deliberately invalid `api_key`. Confirm `AnthropicResearchError` is raised with a real, informative message from the underlying SDK exception — not silently swallowed.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [~] `web_search` returns a real, non-fabricated summary/sources on a genuine relevant result — **NOT verified this pass: blocked on a missing genuine `ANTHROPIC_API_KEY`; see this task's own Implementation Log and `REVIEW-QUEUE.md`.**
- [~] `web_search` returns `"found": False` honestly when nothing relevant is found — never a fabricated summary — **same credential blocker as above.**
- [x] A real API failure raises `AnthropicResearchError`, never silently swallowed
- [x] No LangChain/`model_factory.py` involvement anywhere in this module
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Provider-registry wiring (credential/model resolution by Provider id) — `T03`.
- The skill function itself (access-gating, honest-unavailable-before-real-client) — `T04`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-022` created at `/plan-tasks` step 1) — the human reviews `ADR-022` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

---

## Implementation Log

Built exactly per spec — `app/data_access/anthropic_client.py` (new),
`web_search(api_key, model, query) -> dict`, `AnthropicResearchError`.
Confirmed the literal tool-type identifier (`"type": "web_search_20250305"`,
`"name": "web_search"`) and the citation-extraction path
(`TextBlock.citations` → `CitationsWebSearchResultLocation.url`) are both
still current against the real, installed `anthropic==0.121.0` SDK by
directly reading its own `types/web_search_tool_20250305_param.py` and
`types/citations_web_search_result_location.py` source before writing this
file — no deviation from the task's own literal sample was needed.

**No AC-ID tagged to this task** (verified one layer up in `T04`, per its
own Tests note). Manual verification steps:

1/2. **Blocked on the missing real credential** (see `T01`'s own
Implementation Log) — a genuine relevant result and a genuine honest-empty
result both require a real, working `ANTHROPIC_API_KEY`, not available in
this environment. Not fabricated or guessed; recorded as an open
verification gap in `REVIEW-QUEUE.md`.
3. **Verified live**: called `web_search()` with a deliberately invalid
   `api_key`. Confirmed `AnthropicResearchError` raised with a real,
   informative message from the underlying SDK exception — `Anthropic
   web-search call failed: Error code: 401 - {'type': 'error', 'error':
   {'type': 'authentication_error', 'message': 'invalid x-api-key'}, ...}`
   — not silently swallowed. This is real, direct evidence the module's
   own HTTP call reaches Anthropic's real API and its own error-funnel
   works correctly.

No LangChain/`model_factory.py` involvement anywhere in this module —
confirmed by inspection (only `anthropic` is imported).

Unaffected by the later `T04`/`T05` Provider-resolution correction
(`ADR-022`'s own "Correction" addendum, `ESCALATIONS.md` → `ESC-019`) —
this module's own public contract (`web_search(api_key, model, query)`)
is unchanged; only which Provider's credential/model get passed into it
changed, one layer up.
