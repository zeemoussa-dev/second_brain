---
id: REQ-SB-36-US-02-T02
title: New agent_orchestration/knowledge_bootstrap.py — bootstrap_agent_knowledge(agent_id, subject)
parent_story: REQ-SB-36-US-02
requirement_id: REQ-SB-36
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-023 created) — carried from the parent story; the human reviews ADR-023 alongside this task breakdown. PLUS a real, coder-found scope-internal reconciliation this pass: a try/except added around skill_registry.invoke_skill to honestly catch a real external-API failure (bad/absent Anthropic credential) rather than crash — see Implementation Log."
phase: P1
depends_on: [REQ-SB-36-US-02-T01, REQ-SB-20-US-01-T05, REQ-SB-21-US-01-T02, REQ-SB-36-US-01-T05, REQ-SB-35-US-01-T02, REQ-SB-35-US-01-T03]
created: 2026-08-12
updated: 2026-08-13
---

# REQ-SB-36-US-02-T02 — `knowledge_bootstrap.py`'s `bootstrap_agent_knowledge`

## Parent Story

- Story: [[REQ-SB-36-US-02]] — `../UserStories/REQ-SB-36-US-02-agent-knowledge-bootstrapping-delegated-research-chain.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-36 *Agent Knowledge Bootstrapping via Delegated Research*

---

## Cross-story dependencies — real, not fabricated

This task composes five other stories' own real, `status: Ready` mechanisms, none of them yet `Done` as of this decomposition pass:
- `REQ-SB-20-US-01-T05` — `graph.route_cross_section_request(...)` (both Hub-routing hops).
- `REQ-SB-21-US-01-T02` — `working_mode_registry.get_agent_working_mode(...)` (the Autonomous-mode check).
- `REQ-SB-36-US-01-T05` — `skill_registry.invoke_skill(..., "web-research", {"query": ...})` (the research step).
- `REQ-SB-35-US-01-T02`/`T03` — `vault_filing_expert.determine_placement_and_file(...)` (Tier-1 write / Tier-2 pending-approval dispatch).

Do not start building this task until all six are `Done` — read each one's own real, landed code first, not this task's own sample below.

---

## Objective

Add new `app/business/agent_orchestration/knowledge_bootstrap.py`, exposing `async def bootstrap_agent_knowledge(agent_id: str, subject: str) -> dict` (`ADR-023` points 1–2) — a deterministic composition of the five mechanisms above, never a second layer of recursive, model-driven agent-to-agent conversation. Covers `AC-02` (Tier-2 pause), `AC-04` (honest no-match), `AC-05` (honest failure/uncertainty), `AC-06` (general capability, second subject).

---

## Starting State → End State

**Before / Inputs:** see Cross-story dependencies above — all six prerequisite functions exist and are directly callable.

**After / Outputs:**
- `bootstrap_agent_knowledge(agent_id, subject) -> dict` returns one of:
  - `{"status": "written", "path": str, "kind": str, "research_expert_id": str, "vault_filing_expert_id": str}` (Tier 1, full success),
  - `{"status": "pending_approval", "approval_id": str, "research_expert_id": str}` (Tier 2 — only the filing step paused, both Hub hops and research already completed),
  - `{"status": "no_match", "hop": "research" | "filing"}` (Scenario 4 — a Hub hop found no candidate),
  - `{"status": "no_results", "research_expert_id": str}` (Scenario 5 — the research step honestly found nothing),
  - `{"status": "not_autonomous", "matched_agent_id": str}` (a matched agent is not in Autonomous working mode — the chain does not proceed unattended for this flow, per the story's own Constraint).
- The whole outcome is recorded as one `run_event` history entry on `agent_id` via `vault_writer.append_agent_history_entry`.

---

## Files to Modify

- `src/backend/app/business/agent_orchestration/knowledge_bootstrap.py` (new):
  ```python
  """Delegated knowledge-bootstrap orchestration (ADR-023) -- composes
  already-real (or already-designed) entry points deterministically:
  Hub routing (ADR-017) to find who, then real invocation of the matched
  candidate's own capability (skill invocation, ADR-022; the Vault
  Filing Expert's placement function, ADR-021). This is the first code
  path in this project that actually ACTS on a Hub-routing match rather
  than only reporting it. Never a second, recursive
  run_agent_conversation call per hop -- a fixed, deterministic
  three-hop composition (ADR-023's own Alternatives Considered)."""
  from app.business import working_mode_registry, skill_registry, vault_filing_expert
  from app.business.agent_orchestration import graph
  from app.data_access import vault_writer


  async def bootstrap_agent_knowledge(agent_id: str, subject: str) -> dict:
      # Hop 1: this agent's own Section Hub -> a Research Expert candidate.
      hop1 = graph.route_cross_section_request(
          agent_id, need_description=f"real web research about {subject}"
      )
      if not hop1["matched"]:
          _record(agent_id, f"Could not find a Research Expert to help build knowledge about {subject}.")
          return {"status": "no_match", "hop": "research"}
      research_expert_id = hop1["agent_id"]

      if working_mode_registry.get_agent_working_mode(research_expert_id) != "autonomous":
          _record(agent_id, f"{research_expert_id} is not in Autonomous mode — cannot complete this flow unattended.")
          return {"status": "not_autonomous", "matched_agent_id": research_expert_id}

      # Research.
      research_result = skill_registry.invoke_skill(
          research_expert_id, "web-research", {"query": subject}
      )
      if not research_result.get("found"):
          _record(agent_id, f"{research_expert_id}'s web research about {subject} found nothing relevant.")
          return {"status": "no_results", "research_expert_id": research_expert_id}

      # Hop 2: the Research Expert's own Section Hub -> a Vault Filing Expert candidate.
      hop2 = graph.route_cross_section_request(
          research_expert_id, need_description="file this content into the vault"
      )
      if not hop2["matched"]:
          _record(agent_id, "Could not find a Vault Filing Expert to file the gathered research.")
          return {"status": "no_match", "hop": "filing"}
      vault_filing_expert_id = hop2["agent_id"]

      # Filing (Tier 1 writes immediately; Tier 2 creates a pending-approval record).
      filing_result = vault_filing_expert.determine_placement_and_file(
          content=research_result["summary"],
          source_description=f"Web research about {subject}",
          requesting_agent_id=agent_id,
      )
      if filing_result["status"] == "pending_approval":
          _record(agent_id, f"Research about {subject} gathered; filing paused pending approval of a new top-level vault area.")
          return {
              "status": "pending_approval",
              "approval_id": filing_result["approval_id"],
              "research_expert_id": research_expert_id,
          }
      if filing_result["status"] == "unavailable":
          _record(agent_id, f"Could not file the research about {subject} — {filing_result['message']}")
          return filing_result

      _record(agent_id, f"Built knowledge about {subject}: filed to {filing_result['path']}.")
      return {
          "status": "written",
          "path": filing_result["path"],
          "kind": filing_result["kind"],
          "research_expert_id": research_expert_id,
          "vault_filing_expert_id": vault_filing_expert_id,
      }


  def _record(agent_id: str, message: str) -> None:
      vault_writer.append_agent_history_entry(agent_id, "run_event", message)
  ```

---

## Constraints

- Inherits from parent story and `ADR-023` points 1–2, 4.
- Deterministic composition only — never a recursive `run_agent_conversation` call per hop.
- The Autonomous-mode check gates only the matched Research Expert (per the parent story's own worked Scenario 1 text: "every agent in the delegation chain is in Autonomous working mode") — this task does not additionally re-check `agent_id`'s (the requester's) own mode, since the trigger itself (`T03`) already goes through the ordinary `_invoke_action` gate for that agent.
- Every honest failure/no-match/no-results/not-autonomous branch must record a real `run_event` history entry and return before proceeding further — no step may fabricate a confident result to keep the chain moving (Scenario 5's own Constraint).
- Tier 2's own pause must be the ONLY step that pauses — every step before it (both Hub hops, research) must have already completed by the time the chain reaches the filing step, per Scenario 2's own "only that one step pauses... every other step has already completed" text.
- `bootstrap_agent_knowledge` must not reference `"compass"`/`"compass-expert"` anywhere in its own body — the mechanism must be entirely generic over `agent_id`/`subject`, satisfying Scenario 6 structurally.
- Must be genuinely `async def` end-to-end, per `MEMORY.md`'s own standing async-graph-node Constraint — `route_cross_section_request` itself is a synchronous, deterministic function (confirmed by direct reading of `REQ-SB-20-US-01-T05`), so no `await` is needed on those two calls specifically, but this function's own signature must stay `async def` since its caller (`T03`) invokes it from `agents_router.py`'s already-`async def` action-dispatch path.

---

## Tests

<!-- AC-02/AC-04/AC-05/AC-06 verified here via direct calls to
bootstrap_agent_knowledge against the real backend .venv -- mirrors
route_cross_section_request's/determine_placement_and_file's own
"directly callable, testable without a live trigger" precedent.
AC-01 (the full chat/direct-triggered round trip) is verified in T03. -->

**Manual verification steps:**
1. **[REQ-SB-36-US-02-AC-02]** In a Python shell against the backend `.venv` (real configured Sections/keywords/working-modes; every agent in the chain set to `"autonomous"`; a real Anthropic Provider configured). Reassign/keyword a real Research-Expert-candidate agent and a real Vault-Filing-Expert-candidate agent so both Hub hops match. Engineer the subject/content so the Vault Filing Expert's own placement decision resolves to a genuinely new top-level area (mirrors `REQ-SB-35-US-01-T03`'s own Tier-2 test). Call `await bootstrap_agent_knowledge("compass-expert", "<subject that forces Tier 2>")`. Confirm the result is `{"status": "pending_approval", "approval_id": <uuid>, ...}`, confirm via `pending_approval_registry`'s own list/get that a real record was created, and confirm — via each intermediate step's own observable state (the research result, the Hub-routing calls) — that both Hub hops and the research step had already genuinely completed before the pause (e.g. by temporarily adding a print/log, or by independently confirming `skill_registry.invoke_skill`'s own real result was non-empty).
2. **[REQ-SB-36-US-02-AC-04]** Temporarily clear the target Research-Expert-candidate's own keywords (`agent_keywords.set_agent_keywords(candidate_id, [])`), so Hop 1 cannot match anyone. Call `await bootstrap_agent_knowledge("compass-expert", "some subject")`. Confirm `{"status": "no_match", "hop": "research"}`, and confirm — via `GET /agents/compass-expert/history` — a real, honest `run_event` was recorded, not a fabricated research result. Restore the candidate's real keywords afterward.
3. **[REQ-SB-36-US-02-AC-05]** Engineer a query/subject likely to return no relevant web results (or temporarily monkeypatch `skill_registry.invoke_skill` in-process to return `{"found": False, ...}`, mirroring the established in-process-monkeypatch-and-revert pattern). Call `await bootstrap_agent_knowledge("compass-expert", "<subject>")`. Confirm `{"status": "no_results", ...}` and a real, honest `run_event` recorded — no fabricated content filed.
4. **[REQ-SB-36-US-02-AC-06]** Temporarily add a second, throwaway Expert agent entry to `agent_registry.AGENTS` in-process (in-memory dict mutation, not a file edit — mirrors the established in-process-monkeypatch pattern, reverted after), assign it real keywords/Section, and call `await bootstrap_agent_knowledge("<the throwaway agent id>", "<a different subject, e.g. a fictitious product name>")` through the full happy path (Tier 1). Confirm the identical chain (Hop 1 → research → Hop 2 → filing) runs correctly for it, unmodified — confirming this is a general capability, not code that special-cases `"compass-expert"`. Revert the in-memory `AGENTS` mutation afterward.
5. Non-AC smoke check (full happy path, Tier 1): with a subject/content that resolves to an existing vault category, call `await bootstrap_agent_knowledge("compass-expert", "<subject>")`. Confirm `{"status": "written", "path": <real path>, ...}`, the note exists on disk, and a real `run_event` history entry was recorded on `"compass-expert"`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-02** (Scenario 2) — only the Tier-2 filing step pauses; both Hub hops and research have already completed by then
- [x] **AC-04** (Scenario 4) — a Hub hop with no match honestly stops the chain, no fabricated result
- [x] **AC-05** (Scenario 5) — a no-results research step (or an uncertain filing step) honestly stops/reflects the failure, no fabricated confident result
- [x] **AC-06** (Scenario 6) — the mechanism is fully generic over `agent_id`/`subject`, confirmed with a second, non-Compass agent
- [x] Every branch records a real `run_event` history entry on the originating agent
- [x] The whole function is genuinely `async def`, no nested `asyncio.run()`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The `_ACTION_HANDLERS` dispatch entry and real chat/direct trigger — `T03` (also covers `AC-01`).
- Building/modifying `route_cross_section_request`, `determine_placement_and_file`, `invoke_skill`, or `working_mode_registry` themselves — all reused exactly as those stories build them.
- Scenario 3 ("draw on afterward") — `T04`, blocked on `REQ-SB-29-US-01`.

---

## Context / Notes

**Gating note:** this story is `gate: flagged` (`ADR-023` created at `/plan-tasks` step 1) — the human reviews `ADR-023` and this task breakdown together; the pipeline does not halt, so this task proceeds to `Ready` alongside the rest of the story.

**Do not start this task until all six cross-story prerequisites are actually `Done`** — every one of them is currently `Ready` but unbuilt as of this decomposition pass. `/implement-sprint` will not pick this task up before its `depends_on` are satisfied — this note is for the human/operator sequencing sprints, not the coder to route around.

---

## Implementation Log

**Built 2026-08-12/13 (`/implement-sprint`, `SPRINT-024`).** All six
cross-story prerequisites were confirmed `Done`, then read directly (not
trusted from this task's own sample): `graph.route_cross_section_request`,
`working_mode_registry.get_agent_working_mode`,
`skill_registry.invoke_skill`, `vault_filing_expert.
determine_placement_and_file`. New `app/business/agent_orchestration/
knowledge_bootstrap.py` created, composing all four deterministically,
per this task's own sample, with one real, load-bearing deviation found
by reading the REAL current dependency code (not the sample):

**Scope-internal finding, logged for human spot-check (this task was
already `gate: flagged`; this adds to that same flag, not a new
escalation):** direct reading of `app/data_access/anthropic_client.py::
web_search` shows it `raise`s `AnthropicResearchError` on any real
Anthropic API failure (bad/absent credential, network error) rather than
returning a result dict — this task's own sample called
`skill_registry.invoke_skill(...)` with no `try/except`, which would let
a real external-API failure crash the whole chain uncaught, directly
contradicting this task's own locked Constraint ("no step may fabricate
a confident result to keep the chain moving") and AC-05's own "honestly
reflects failure... rather than fabricating a result" wording (a crash is
neither an honest reflection nor a graceful stop). Added a `try/except`
around the `invoke_skill` call, converting any such exception into the
same declared `"no_results"` outcome (the closest of this task's own
5 enumerated statuses — no 6th status invented), with the recorded
message naming the real failure. Mirrors `graph.py::_call_model`'s own
identical honest-failure-funnel precedent for the same class of
real-Provider-call failure. **Verified this was load-bearing, not
theoretical** — see AC-05 below, where the real (unmocked) Anthropic
call genuinely raised this exact exception and was caught correctly.

A second, minor scope-internal reconciliation: `vault_filing_expert.
determine_placement_and_file` can return `{"status": "unavailable", ...}`
(its own Provider-unavailable branch, confirmed by direct reading) — not
named in this task's own "returns one of" Outputs enumeration but already
present in this task's own code sample's `if filing_result["status"] ==
"unavailable"` branch; kept exactly as sampled (a real, necessary branch,
not scope creep).

**Live verification (real backend `.venv`, real vault, real Compass
Provider; `vault-qa` configured as the real-config Research-Expert
candidate — keywords `["research", "web research"]`, granted
`"web-research"` skill access, Section `"productivity"` (real, cross-
Section from `compass-expert`'s own self-healed `"technical"`); a
`"vault"` keyword added to `vault-filing-expert`'s own real keyword list
so Hop 2's `need_description` genuinely matches it — all via the
already-built keyword/skill-grant endpoints, real configuration data, no
code change, per this task's own Tests instruction to "reassign/keyword a
real... candidate agent"):**

- **[AC-02]** (Tier-2 pause, both hops + research already completed).
  Real Hop 1/Hop 2 routing confirmed independently first
  (`route_cross_section_request("compass-expert", ...)` →
  `{"matched": True, "agent_id": "vault-qa", ...}`;
  `route_cross_section_request("vault-qa", "file this content into the
  vault")` → `{"matched": True, "agent_id": "vault-filing-expert", ...}`).
  Since no real `ANTHROPIC_API_KEY` exists (provably-inert placeholder,
  per `MEMORY.md`/`ESC-019`), the research step's own "found: True" branch
  is genuinely unreachable through any live external call this session —
  used the established, sanctioned in-process-monkeypatch-and-revert
  technique (`skill_registry.invoke_skill`, reverted immediately after)
  to substitute realistic research content, isolating the ONE externally-
  credential-gated step while running every other step for real. Content
  engineered to genuinely warrant a new top-level area (a structured,
  recurring personal home-brewing recipe log — mirrors
  `REQ-SB-35-US-01-T03`'s own "podcast-episode digest" precedent, adapted
  since `"Notes"` has since become a real, already-materialized catch-all
  kind in this vault, unlike at that task's own build time — a real,
  live-discovered environmental drift). Result:
  `{"status": "pending_approval", "approval_id": "98d6204ec364",
  "research_expert_id": "vault-qa"}`. Confirmed via
  `pending_approval_registry.get_pending_approval(...)`: a REAL record was
  created (`agent_id: "vault-filing-expert"`, `action_id:
  "propose_new_top_level_area"`, proposed `kind: "Recipes"`), confirmed
  `"Recipes"` was NOT in `list_known_kinds()` (no note written) before or
  after — the pause happened, and only that step. Declined afterward
  (`resolve_pending_approval(..., "declined")`) to avoid permanently
  creating a fabricated top-level vault area; `"Recipes"` confirmed still
  absent from `list_known_kinds()`. **PASS — the real Vault Filing Expert
  (a real Compass LLM placement call) was genuinely invoked and correctly
  created a real pending-approval record; both Hub hops and the research
  step had already genuinely completed by the time of the pause.**
- **[AC-04]** (no-match, honest). `vault-qa`'s real keywords temporarily
  cleared (`set_agent_keywords("vault-qa", [])`). Called
  `bootstrap_agent_knowledge("compass-expert", "Compass")`. Result:
  `{"status": "no_match", "hop": "research"}`; history grew by exactly one
  real `run_event`: "Could not find a Research Expert to help build
  knowledge about Compass." — no fabricated result. Real keywords
  restored and re-confirmed. **PASS.**
- **[AC-05]** (honest failure/uncertainty, no fabrication) — verified via
  **two independent real paths, not just one:**
  1. `vault-qa` left linked to its real `"compass"` Provider (no real
     web-search capability, per `ADR-022`'s own investigated finding).
     `skill_registry.invoke_skill` genuinely called `skill_tools.
     web_research`, which honestly returned `{"available": False,
     "message": "..."}`. Result: `{"status": "no_results",
     "research_expert_id": "vault-qa"}`, with an honest, accurate
     `run_event` (not a generic "found nothing" — includes the real
     unavailability message).
  2. `vault-qa` temporarily relinked to the real `"anthropic-claude"`
     Provider (the provably-inert placeholder credential). This made a
     REAL, live HTTP call to `https://api.anthropic.com/v1/messages`,
     which genuinely returned a real `401 Unauthorized`
     (`invalid x-api-key`) — confirming, live, the exact credential gap
     named in this sprint's own briefing. The new `try/except` (above)
     correctly caught the resulting `AnthropicResearchError` and returned
     the honest `{"status": "no_results", ...}` shape with a `run_event`
     naming the real error, instead of crashing. Provider reverted to
     `"compass"` afterward. **PASS — both an "unavailable" and a genuine
     external-failure path honestly stop the chain; neither fabricates a
     result.**
- **[AC-06]** (generic, second subject). A throwaway second pilot Expert
  agent (`"throwaway-second-pilot-expert"`, Section `"sales"`, no
  keywords) added to `agent_registry.AGENTS` in-process (mirrors this
  task's own sanctioned in-process-`AGENTS`-mutation Tests technique).
  Ran the full happy path (via the same monkeypatch technique as AC-02,
  since it also needs `"found": True` content) for subject "Fictitious
  Product Zephyr". Result: `{"status": "written", "path": ...,
  "research_expert_id": "vault-qa", "vault_filing_expert_id":
  "vault-filing-expert"}` — the identical chain (Hop 1 → mode check →
  research → Hop 2 → filing) ran correctly, unmodified, for a completely
  different `agent_id`/subject, confirming this module never references
  `"compass"`/`"compass-expert"` anywhere in its own body (also confirmed
  by direct code inspection — zero matches). `AGENTS` mutation reverted;
  the throwaway agent's own residual `.second-brain` state entries
  (sections/keywords/working-modes/providers/history — self-healed by
  those registries' own `_load_state()` calls while it briefly existed in
  `AGENTS`) and its one real vault note were removed afterward to avoid
  polluting the real vault/state with fabricated test residue. **PASS.**
- **Non-AC smoke check (real, unmocked full round trip):** with `vault-qa`
  linked to `"compass"` (its real, honest-unavailable Provider), a full
  real, unmocked call correctly produced `{"status": "no_results", ...}}`
  end to end, with the real Hub-routing hops, real mode check, and a real
  (honestly-unavailable) research attempt — confirming the whole
  deterministic chain runs correctly with zero mocking whenever no Tier-1/
  Tier-2-forcing content is needed.
- **Non-AC smoke check (`not_autonomous`).** `vault-qa`'s working mode
  temporarily set to `"supervised"`. Result: `{"status":
  "not_autonomous", "matched_agent_id": "vault-qa"}`, with an honest
  `run_event`. Restored to `"autonomous"` afterward.
- **Code inspection:** every composed call
  (`route_cross_section_request`, `get_agent_working_mode`,
  `invoke_skill`, `determine_placement_and_file`) is a real, synchronous
  function (confirmed by direct reading of each) — `bootstrap_agent_
  knowledge` itself is `async def` (this task's own Constraint,
  satisfied), with no `await`/`asyncio.run()` anywhere in its own body;
  every branch calls `_record()` (→
  `vault_writer.append_agent_history_entry`) before returning, confirmed
  live above for every branch actually reachable this session
  (`no_match` ×1 hop tested, `not_autonomous`, `no_results` ×2 real paths,
  `pending_approval`, `written`).

**Live-discovered vault-taxonomy drift, honestly recorded, not silently
adjusted around:** `REQ-SB-35-US-01-T03`'s own Implementation Log
recorded `"Notes"` as a genuinely new top-level area at that task's build
time; by this session, `"Notes"` is now a real, already-materialized
`list_known_kinds()` entry (this coder's own Tier-1 test wrote a second
real note into it), so the identical class of "generic, doesn't fit
elsewhere" content this task first tried for its own Tier-2 test now
resolves to the existing `"Notes"` catch-all instead of forcing a new
top-level area — content had to be reframed as an explicitly structured,
recurring, dedicated content type (see AC-02 above) to genuinely warrant
a new area under the real, current vault state. Not a defect — the
methodology-grounded model behaved correctly against the real, current
taxonomy; recorded here as a real environmental-drift finding, mirroring
this project's own standing practice for this class of finding.

No `ESCALATIONS.md` entry from this task itself — the `try/except`
addition and the Tier-2 content-engineering finding are both
scope-internal judgement calls within this task's own file/objective, not
a new dependency, shared-interface change, or ADR deviation. `gate:
flagged` carried from the parent story's `ADR-023` human-review flag,
plus this task's own two logged findings above for spot-check.
