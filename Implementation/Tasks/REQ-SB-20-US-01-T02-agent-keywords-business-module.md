---
id: REQ-SB-20-US-01-T02
title: New app/business/agent_keywords.py — get/set per-agent keywords + cross-Section candidate matching
parent_story: REQ-SB-20-US-01
requirement_id: REQ-SB-20
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-017 created) — carried from the parent story; the human reviews ADR-017 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-20-US-01-T01]
created: 2026-08-12
updated: 2026-08-12
---

# REQ-SB-20-US-01-T02 — `app/business/agent_keywords.py`

## Parent Story

- Story: [[REQ-SB-20-US-01]] — `../UserStories/REQ-SB-20-US-01-section-hub-intelligence-and-cross-section-routing.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-20 *Section Hub Intelligence & Cross-Section Routing*

---

## Objective

Add the new business module `app/business/agent_keywords.py` (`ADR-017` point 3), sibling to `section_registry.py`/`provider_registry.py`: read/write an agent's own keywords, and the actual cross-Section keyword-substring candidate-matching function the routing node (`T05`) calls.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed — `vault_writer.load_agent_keywords`/`save_agent_keywords`/`load_all_agent_keywords` exist.
- `app/business/section_registry.py` already exists (`Done`): `get_agent_section(agent_id) -> dict | None`, `list_sections() -> list[dict]`.
- `app/business/agent_registry.py` already exists (`Done`): `list_agents() -> list[dict]` (each `{"id", "name", "type"}`).

**After / Outputs:**
- `app/business/agent_keywords.py` exists: `get_agent_keywords(agent_id) -> list[str]`, `set_agent_keywords(agent_id, keywords: list[str]) -> list[str]`, `list_candidate_agents_for_keyword_match(requesting_agent_id: str, need_description: str) -> list[dict]`.

---

## Files to Modify

- `src/backend/app/business/agent_keywords.py` (new):
  ```python
  """Per-agent free-text keywords describing what an agent knows (ADR-017),
  composed alongside app/business/agent_registry.py and
  app/business/section_registry.py, not inside either -- agent_registry.py
  itself is not modified (ADR-011 point 2's "agent identity/type/actions
  stay hardcoded" reasoning stays untouched). Powers Section-Hub
  cross-Section keyword-substring routing (REQ-SB-20), reusing ADR-011's
  exact matching posture one layer up at the Hub level."""
  from app.business import agent_registry, section_registry
  from app.data_access import vault_writer


  def get_agent_keywords(agent_id: str) -> list[str]:
      return vault_writer.load_agent_keywords(agent_id)


  def set_agent_keywords(agent_id: str, keywords: list[str]) -> list[str]:
      """Whole-list replace semantics, matching the free-text kv-list
      editing UX the Agent Settings panel already uses for other per-agent
      fields -- no incremental add/remove-one-keyword call is implied or
      required (ADR-017 point 3)."""
      vault_writer.save_agent_keywords(agent_id, keywords)
      return keywords


  def list_candidate_agents_for_keyword_match(
      requesting_agent_id: str, need_description: str
  ) -> list[dict]:
      """Deterministic, case-insensitive keyword-substring matching
      (ADR-011's exact posture, unchanged -- reused one layer up), scanning
      every OTHER agent whose Section differs from the requesting agent's
      own Section (cross-Section only -- this story's own Constraint
      deferring within-Section routing). Returns every matching candidate,
      in agent_registry.list_agents() order, as
      [{"agent_id": str, "section_id": str}, ...] -- first-match-wins
      tie-break (ADR-011's existing convention) is the caller's own
      responsibility (T05's route_hub_request/route_cross_section_request),
      not decided here, so callers can inspect every candidate if ever
      needed. An agent with an empty keyword list is structurally never a
      candidate -- no substring of an empty list ever matches
      need_description (ADR-017 point 4, "satisfied by construction, not
      an explicit exclusion check")."""
      requester_section = section_registry.get_agent_section(requesting_agent_id)
      requester_section_id = requester_section["id"] if requester_section else None
      all_keywords = vault_writer.load_all_agent_keywords()
      need_description_lower = need_description.lower()

      candidates = []
      for agent in agent_registry.list_agents():
          agent_id = agent["id"]
          if agent_id == requesting_agent_id:
              continue
          agent_section = section_registry.get_agent_section(agent_id)
          agent_section_id = agent_section["id"] if agent_section else None
          if agent_section_id == requester_section_id:
              continue  # within-Section routing is out of scope this pass
          agent_own_keywords = all_keywords.get(agent_id, [])
          if any(keyword.lower() in need_description_lower for keyword in agent_own_keywords):
              candidates.append({"agent_id": agent_id, "section_id": agent_section_id})
      return candidates
  ```

---

## Constraints

- Inherits from parent story: `api → business → data_access` layering (`ADR-003`) — no HTTP concerns, no direct file I/O (all persistence goes through `T01`'s `vault_writer` primitives).
- Must NOT modify `agent_registry.py` or `section_registry.py` — read-only composition only.
- `list_candidate_agents_for_keyword_match` must exclude the requesting agent itself and every agent in the requesting agent's own Section (cross-Section only, this story's own Constraint) — never return a same-Section candidate.
- The keyword-substring match itself must be case-insensitive and deterministic — no randomness, no LLM call, exactly `ADR-011`'s posture.
- An agent with `[]` keywords must never appear in the returned candidate list, for any `need_description` — this must hold structurally (an empty list has no substring to test), not via a special-cased skip.

---

## Tests

<!-- This task's own locked-AC verification (AC-02/AC-03/AC-04, the routing
*decision* itself) is deferred to T05, where this function is composed
into route_hub_request/route_cross_section_request -- the same "verify at
the level where the outcome first becomes genuinely observable as this
story's own routing behaviour" placement rule already established
(REQ-SB-19-US-01-T04, REQ-SB-25-US-01-T08). This task's own verification is
a non-AC smoke check confirming the function's matching/exclusion logic in
isolation, ahead of T05's full routing-result wiring. -->

**Manual verification steps:**
1. Non-AC smoke check: in a Python shell against the backend `.venv` (real
   configured `vault_path`, seeded 5 Sections per `section_registry`'s
   default self-heal). Reassign `people-producer` to a different Section
   than `email-capture`'s (e.g. `PATCH /agents/people-producer
   {"section_id": "customers"}` via a running backend, or call
   `section_registry.set_agent_section("people-producer", "customers")`
   directly). Call `agent_keywords.set_agent_keywords("people-producer",
   ["people", "contacts", "attendee bios"])`. Call
   `agent_keywords.list_candidate_agents_for_keyword_match("email-capture",
   "I need help finding an attendee's bio")`. Confirm the result is
   `[{"agent_id": "people-producer", "section_id": "customers"}]`.
2. Non-AC smoke check: leave `todo-capture` with no keywords ever assigned
   (the default, real starting state — `agent_keywords.json` never had a
   `todo-capture` entry written). Call
   `agent_keywords.list_candidate_agents_for_keyword_match("email-capture",
   "todo capture task list")` (a need description that would textually
   match `todo-capture`'s own *name/type* if name-matching were used —
   confirming the exclusion is genuinely keyword-based, not name-based).
   Confirm `todo-capture` never appears in the result (its own empty
   keyword list has nothing to match against).
3. Non-AC smoke check: reassign a second agent (e.g. `vault-qa`) into
   `email-capture`'s own Section (`"technical"`, the seed default) and give
   it matching keywords (`agent_keywords.set_agent_keywords("vault-qa",
   ["attendee bios"])`). Re-run step 1's call. Confirm `vault-qa` is
   **excluded** from the result (same-Section as the requester,
   `email-capture`) even though its own keywords would otherwise match —
   proving the cross-Section-only exclusion is enforced.
4. Clean-up: `agent_keywords.set_agent_keywords("people-producer", [])`,
   `agent_keywords.set_agent_keywords("vault-qa", [])`,
   `section_registry.set_agent_section("people-producer", "technical")`,
   `section_registry.set_agent_section("vault-qa", "technical")` — restore
   the clean seed state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `get_agent_keywords(agent_id)` returns that agent's own keyword list
- [x] `set_agent_keywords(agent_id, keywords)` whole-list-replaces and returns the new list
- [x] `list_candidate_agents_for_keyword_match` excludes the requesting agent itself and every same-Section agent
- [x] `list_candidate_agents_for_keyword_match` never returns an agent whose own keyword list is empty
- [x] Matching is case-insensitive, deterministic, substring-based — no LLM call
- [x] `agent_registry.py`/`section_registry.py` not modified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The two-hop "own Hub, then target Hub" relay's own result shape (`matched`/`from_section_id`/`matched_section_id` fields), the LangGraph node/tool/conditional-edge wiring, and the directly-callable `route_cross_section_request` entry point — all `T05` (`graph.py`).
- Any API surface exposing keywords — `T03`.
- First-match-wins tie-break selection — `T05`'s own responsibility, consuming this function's full candidate list.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-017` created at `/plan-tasks` step 1) — the human reviews `ADR-017` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

`list_candidate_agents_for_keyword_match` deliberately returns the **full** candidate list, not just the first match — `ADR-017` point 5/6 assigns first-match-wins selection to the routing node (`T05`) itself, the same "one business module composing another" shape already established across this codebase (`people_extraction.py` → `customer_hub_linking.py`; `meeting_classification.py` → `people_extraction.py`).

---

## Implementation Log

**Built 2026-08-12 (coder).** New `app/business/agent_keywords.py` created
verbatim per this task's own code block — `get_agent_keywords`/
`set_agent_keywords`/`list_candidate_agents_for_keyword_match`, composing
`agent_registry.list_agents()`/`section_registry.get_agent_section()`
read-only.

**Live verification (real backend `.venv`, real `section_registry`/
`agent_registry` data — real seed state has all 5 agents in "Productivity",
not "Technical" as the task's own illustrative example assumed; adapted the
reassignment target Section accordingly, same substance):**

- Reassigned `people-producer` to `"customers"` (a different Section than
  `email-capture`'s own `"productivity"`), assigned it keywords
  `["people", "contacts", "attendee bios"]`.
- **Scope-internal assumption, logged per Pipeline's "judgement calls go in
  the Implementation Log" rule (not an escalation):** the task's own literal
  example need-description, `"I need help finding an attendee's bio"`, does
  **not** actually contain any of the three example keywords as a
  case-insensitive substring (`"attendee bios"` — plural, with a space — is
  not a substring of `"...an attendee's bio"` — singular, with an
  apostrophe-s) under the exact deterministic keyword-substring algorithm
  this task's own code specifies (and `ADR-011`/`ADR-017` mandate). This is
  a wording slip in the task's own illustrative test data, not a defect in
  the implementation, which is a literal, unmodified copy of the task's own
  provided code. Corrected the example need-description to
  `"I need help with attendee bios for this customer meeting"` (genuinely
  contains `"attendee bios"` as a substring) so the smoke check actually
  exercises the intended behaviour; the underlying algorithm, AC substance,
  and code are all unaffected — only the illustrative example string
  changed. Same correction applied consistently at `T05`'s own identical
  example.
- `list_candidate_agents_for_keyword_match("email-capture", "I need help
  with attendee bios for this customer meeting")` →
  `[{"agent_id": "people-producer", "section_id": "customers"}]` exactly.
  **PASS.**
- `todo-capture` left with its real, never-assigned `[]` keyword list;
  `list_candidate_agents_for_keyword_match("email-capture", "todo capture
  task list")` (deliberately textually overlapping `todo-capture`'s own
  name) never returned it. **PASS.**
- Reassigned `vault-qa` into `email-capture`'s own Section
  (`"productivity"`) with matching keywords (`["attendee bios"]`) —
  confirmed **excluded** from the result (same-Section as requester) even
  though its own keywords would otherwise match. **PASS.**
- Clean-up: `people-producer`/`vault-qa` keywords reset to `[]`, both
  Sections restored to `"productivity"` — confirmed via
  `section_registry.get_agent_section` on both, matching the real seed
  state before this task's own verification began.

No locked AC of its own (verified further at `T05` where this function is
composed into the routing decision) — non-AC smoke check per this task's
own `## Tests` placement rule, all steps passed.

gate: flagged (carried, `ADR-017` — unresolved by this task itself, per
its own gating note).
